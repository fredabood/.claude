"""
Intelligent sprint recalculation engine for Vibey.

Recalculates sprints to fit different platform context windows by:
- Splitting oversized tasks into smaller subtasks
- Preserving and re-mapping dependencies
- Distributing success criteria across subtasks
- Preserving agent assignments where appropriate
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml
import copy

from vibey.platform import (
    PlatformInfo,
    get_effective_platform,
    format_token_count,
)
from vibey.roadmap.compatibility import (
    check_sprint_compatibility,
    is_task_completed,
    load_sprint_tasks,
    CompatibilityStatus,
)


@dataclass
class SubTask:
    """A subtask created from splitting an oversized task."""
    id: str
    name: str
    description: str
    estimated_tokens: int
    dependencies: List[str]
    success_criteria: List[str]
    assigned_agent: Optional[str]
    parent_task_id: str
    subtask_index: int
    total_subtasks: int


@dataclass
class RecalculationPlan:
    """Plan for recalculating a sprint."""
    sprint_id: str
    platform: PlatformInfo
    original_context: int
    target_context: int
    tasks_to_split: List[str]
    tasks_unchanged: List[str]
    subtasks: List[SubTask]
    dependency_map: Dict[str, str]  # old_task_id -> new_task_id (last subtask)
    warnings: List[str]

    @property
    def total_new_tasks(self) -> int:
        return len(self.tasks_unchanged) + len(self.subtasks)


@dataclass
class RecalculationResult:
    """Result of recalculating a sprint."""
    success: bool
    sprint_id: str
    plan: RecalculationPlan
    files_modified: List[str]
    message: str
    errors: List[str] = field(default_factory=list)


def calculate_split_count(task_tokens: int, max_context: int, buffer: float = 0.1) -> int:
    """
    Calculate how many subtasks are needed.

    Args:
        task_tokens: Estimated tokens for the task.
        max_context: Maximum context window.
        buffer: Buffer percentage (default 10%).

    Returns:
        Number of subtasks needed.
    """
    usable_context = int(max_context * (1 - buffer))
    return max(1, ceil(task_tokens / usable_context))


def split_success_criteria(criteria: List[str], num_splits: int, task_name: str) -> List[List[str]]:
    """
    Distribute success criteria across subtasks.

    Args:
        criteria: Original success criteria.
        num_splits: Number of subtasks.
        task_name: Task name for context.

    Returns:
        List of criteria lists, one per subtask.
    """
    if not criteria:
        # Generate placeholder criteria
        return [[f"Complete part {i+1} of {task_name}"] for i in range(num_splits)]

    # Distribute criteria evenly
    result = [[] for _ in range(num_splits)]
    for i, c in enumerate(criteria):
        result[i % num_splits].append(c)

    # Ensure each subtask has at least one criterion
    for i, r in enumerate(result):
        if not r:
            result[i].append(f"Continue work on {task_name} (part {i+1}/{num_splits})")

    return result


def split_task(
    task_data: Dict[str, Any],
    target_context: int,
    sprint_id: str,
    existing_task_ids: List[str],
) -> List[SubTask]:
    """
    Split an oversized task into subtasks.

    Args:
        task_data: Original task YAML data.
        target_context: Target context window.
        sprint_id: Sprint ID for new task IDs.
        existing_task_ids: Existing task IDs to avoid conflicts.

    Returns:
        List of SubTask objects.
    """
    task = task_data.get("task", task_data)
    task_id = task.get("id", "unknown")
    task_name = task.get("name", "Unnamed Task")
    estimated_tokens = task.get("estimated_tokens", 0)
    description = task.get("description", "")
    dependencies = task.get("dependencies", [])
    success_criteria = task.get("success_criteria", [])
    assigned_agent = task.get("assigned_agent")

    # Calculate split count
    num_splits = calculate_split_count(estimated_tokens, target_context)

    if num_splits <= 1:
        return []  # No split needed

    # Calculate tokens per subtask
    tokens_per_subtask = estimated_tokens // num_splits

    # Distribute success criteria
    criteria_per_subtask = split_success_criteria(success_criteria, num_splits, task_name)

    # Generate subtask IDs
    base_id = task_id.replace("-task-", "-subtask-")

    subtasks = []
    for i in range(num_splits):
        subtask_id = f"{base_id}-{i+1:02d}"

        # First subtask inherits external dependencies
        if i == 0:
            subtask_deps = dependencies.copy()
        else:
            # Later subtasks depend on previous subtask
            subtask_deps = [subtasks[-1].id]

        subtask = SubTask(
            id=subtask_id,
            name=f"{task_name} (Part {i+1}/{num_splits})",
            description=f"Part {i+1} of {num_splits}: {description[:200]}..." if len(description) > 200 else description,
            estimated_tokens=tokens_per_subtask,
            dependencies=subtask_deps,
            success_criteria=criteria_per_subtask[i],
            assigned_agent=assigned_agent,
            parent_task_id=task_id,
            subtask_index=i,
            total_subtasks=num_splits,
        )
        subtasks.append(subtask)

    return subtasks


def create_recalculation_plan(
    sprint_id: str,
    project_root: Optional[Path] = None,
    target_platform: Optional[str] = None,
    target_context: Optional[int] = None,
) -> RecalculationPlan:
    """
    Create a plan for recalculating a sprint.

    Args:
        sprint_id: Sprint to recalculate.
        project_root: Project root directory.
        target_platform: Target platform (auto-detect if None).
        target_context: Target context window.

    Returns:
        RecalculationPlan with details.
    """
    if project_root is None:
        project_root = Path.cwd()

    # Get target platform
    platform = get_effective_platform(project_root)
    if target_platform:
        from vibey.platform import get_platform_info
        platform = get_platform_info(target_platform)
    if target_context:
        platform.context_window = target_context

    ctx_window = platform.context_window

    # Load sprint and tasks
    sprint_data, tasks = load_sprint_tasks(sprint_id, project_root)

    # Separate completed vs incomplete
    tasks_to_split = []
    tasks_unchanged = []
    all_subtasks = []
    existing_ids = [t.get("task", t).get("id", "") for t in tasks]
    warnings = []

    for task_data in tasks:
        task = task_data.get("task", task_data)
        task_id = task.get("id", "")
        task_status = task.get("status", "")
        estimated_tokens = task.get("estimated_tokens", 0)

        # Skip completed tasks
        if is_task_completed(task_status):
            tasks_unchanged.append(task_id)
            continue

        # Check if needs splitting
        if estimated_tokens > ctx_window:
            subtasks = split_task(task_data, ctx_window, sprint_id, existing_ids)
            if subtasks:
                tasks_to_split.append(task_id)
                all_subtasks.extend(subtasks)
                existing_ids.extend([s.id for s in subtasks])
            else:
                tasks_unchanged.append(task_id)
        else:
            tasks_unchanged.append(task_id)

    # Build dependency map (old task -> last subtask)
    dependency_map = {}
    for task_id in tasks_to_split:
        related_subtasks = [s for s in all_subtasks if s.parent_task_id == task_id]
        if related_subtasks:
            dependency_map[task_id] = related_subtasks[-1].id

    # Update dependencies in remaining tasks to point to subtasks
    # (This would require modifying the unchanged tasks)
    if dependency_map:
        warnings.append(f"Tasks depending on split tasks will need dependency updates")

    return RecalculationPlan(
        sprint_id=sprint_id,
        platform=platform,
        original_context=200_000,  # Assumed original
        target_context=ctx_window,
        tasks_to_split=tasks_to_split,
        tasks_unchanged=tasks_unchanged,
        subtasks=all_subtasks,
        dependency_map=dependency_map,
        warnings=warnings,
    )


def apply_recalculation(
    plan: RecalculationPlan,
    project_root: Optional[Path] = None,
    dry_run: bool = False,
) -> RecalculationResult:
    """
    Apply a recalculation plan to the sprint.

    Args:
        plan: RecalculationPlan to apply.
        project_root: Project root directory.
        dry_run: If True, don't write files.

    Returns:
        RecalculationResult with details.
    """
    if project_root is None:
        project_root = Path.cwd()

    files_modified = []
    errors = []

    # Find sprint directory
    roadmap_root = project_root / ".vibey" / "roadmap"
    sprint_dir = None

    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir():
            continue
        potential = track_dir / plan.sprint_id
        if potential.exists():
            sprint_dir = potential
            break

    if not sprint_dir:
        return RecalculationResult(
            success=False,
            sprint_id=plan.sprint_id,
            plan=plan,
            files_modified=[],
            message=f"Sprint directory not found: {plan.sprint_id}",
            errors=[f"Directory not found"],
        )

    now = datetime.now(timezone.utc).isoformat()

    # Create subtask files
    for subtask in plan.subtasks:
        task_dir = sprint_dir / subtask.id
        task_file = task_dir / "task.yaml"

        task_data = {
            "task": {
                "id": subtask.id,
                "name": subtask.name,
                "sprint_id": plan.sprint_id,
                "track_id": sprint_dir.parent.name,
                "roadmap_id": "vibey-framework-v2",
                "status": "not_started",
                "blocked": False,
                "created": now,
                "started": None,
                "completed": None,
                "estimated_tokens": subtask.estimated_tokens,
                "description": subtask.description,
                "success_criteria": subtask.success_criteria,
                "dependencies": subtask.dependencies,
                "blocked_by": [],
                "assigned_agent": subtask.assigned_agent,
                "commits": [],
                "metadata": {
                    "parent_task": subtask.parent_task_id,
                    "subtask_index": subtask.subtask_index,
                    "total_subtasks": subtask.total_subtasks,
                    "created_by_recalculation": True,
                    "recalculated_at": now,
                    "target_platform": plan.platform.name,
                    "target_context": plan.target_context,
                },
            }
        }

        if not dry_run:
            task_dir.mkdir(parents=True, exist_ok=True)
            with open(task_file, "w") as f:
                yaml.dump(task_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        files_modified.append(str(task_file))

    # Update sprint metadata
    sprint_file = sprint_dir / "sprint.yaml"
    if sprint_file.exists():
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint = sprint_data.get("sprint", sprint_data)

        # Add recalculation metadata
        if "metadata" not in sprint:
            sprint["metadata"] = {}

        sprint["metadata"]["recalculated_at"] = now
        sprint["metadata"]["recalculated_for_platform"] = plan.platform.name
        sprint["metadata"]["recalculated_context_window"] = plan.target_context
        sprint["metadata"]["tasks_split"] = plan.tasks_to_split
        sprint["metadata"]["subtasks_created"] = [s.id for s in plan.subtasks]

        # Update task count
        new_task_count = len(plan.tasks_unchanged) + len(plan.subtasks)
        sprint["progress"]["tasks_total"] = new_task_count

        if not dry_run:
            with open(sprint_file, "w") as f:
                yaml.dump({"sprint": sprint}, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        files_modified.append(str(sprint_file))

    return RecalculationResult(
        success=True,
        sprint_id=plan.sprint_id,
        plan=plan,
        files_modified=files_modified,
        message=f"Recalculated {len(plan.tasks_to_split)} tasks into {len(plan.subtasks)} subtasks",
        errors=errors,
    )


def format_recalculation_plan(plan: RecalculationPlan, verbose: bool = False) -> str:
    """Format recalculation plan for display."""
    lines = []

    lines.append(f"\nRecalculation Plan: {plan.sprint_id}")
    lines.append("=" * 70)

    lines.append(f"\nTarget Platform: {plan.platform.display_name}")
    lines.append(f"Target Context: {format_token_count(plan.target_context)} tokens")

    lines.append(f"\nTasks to Split: {len(plan.tasks_to_split)}")
    for task_id in plan.tasks_to_split:
        lines.append(f"  • {task_id}")

    lines.append(f"\nSubtasks to Create: {len(plan.subtasks)}")
    for subtask in plan.subtasks:
        lines.append(f"  • {subtask.id}")
        lines.append(f"    {subtask.name}")
        lines.append(f"    Tokens: {format_token_count(subtask.estimated_tokens)}")
        if verbose:
            lines.append(f"    Dependencies: {subtask.dependencies}")

    lines.append(f"\nTasks Unchanged: {len(plan.tasks_unchanged)}")

    if plan.warnings:
        lines.append(f"\nWarnings:")
        for w in plan.warnings:
            lines.append(f"  ⚠️  {w}")

    lines.append(f"\nTotal tasks after recalculation: {plan.total_new_tasks}")

    return "\n".join(lines)
