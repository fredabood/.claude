"""
Sprint/Task compatibility analysis for Vibey.

Checks if tasks fit within the current platform's context window
and provides recommendations for recalculation if needed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

from vibey.platform import (
    PlatformInfo,
    get_effective_platform,
    get_context_window,
    format_token_count,
)


class CompatibilityStatus(str, Enum):
    """Compatibility check result status."""
    COMPATIBLE = "compatible"
    OVERSIZED = "oversized"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class TaskCompatibility:
    """Compatibility result for a single task."""
    task_id: str
    task_name: str
    status: str  # Task status (completed, in_progress, not_started)
    estimated_tokens: int
    context_window: int
    compatibility: CompatibilityStatus
    overflow_tokens: int = 0
    utilization_percent: float = 0.0
    is_completed: bool = False
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "estimated_tokens": self.estimated_tokens,
            "context_window": self.context_window,
            "compatibility": self.compatibility.value,
            "overflow_tokens": self.overflow_tokens,
            "utilization_percent": self.utilization_percent,
            "is_completed": self.is_completed,
            "message": self.message,
        }


@dataclass
class SprintCompatibility:
    """Compatibility result for a sprint."""
    sprint_id: str
    sprint_name: str
    platform: PlatformInfo
    total_tasks: int
    completed_tasks: int
    incomplete_tasks: int
    compatible_tasks: int
    oversized_tasks: int
    warning_tasks: int
    unknown_tasks: int
    overall_status: CompatibilityStatus
    task_results: List[TaskCompatibility]
    recommendations: List[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def needs_recalculation(self) -> bool:
        """Check if sprint needs recalculation."""
        return self.oversized_tasks > 0

    @property
    def can_proceed(self) -> bool:
        """Check if sprint can proceed without recalculation."""
        return self.oversized_tasks == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_id": self.sprint_id,
            "sprint_name": self.sprint_name,
            "platform": self.platform.to_dict(),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "incomplete_tasks": self.incomplete_tasks,
            "compatible_tasks": self.compatible_tasks,
            "oversized_tasks": self.oversized_tasks,
            "warning_tasks": self.warning_tasks,
            "unknown_tasks": self.unknown_tasks,
            "overall_status": self.overall_status.value,
            "needs_recalculation": self.needs_recalculation,
            "can_proceed": self.can_proceed,
            "task_results": [t.to_dict() for t in self.task_results],
            "recommendations": self.recommendations,
            "checked_at": self.checked_at,
        }


def is_task_completed(task_status: str) -> bool:
    """Check if a task is considered completed."""
    return task_status.lower() in ("completed", "done", "finished", "shipped")


def check_task_compatibility(
    task_data: Dict[str, Any],
    context_window: int,
    buffer_percent: float = 0.1,
) -> TaskCompatibility:
    """
    Check if a single task fits within the context window.

    Args:
        task_data: Task dictionary from YAML.
        context_window: Platform context window in tokens.
        buffer_percent: Buffer to leave for response (default 10%).

    Returns:
        TaskCompatibility result.
    """
    task = task_data.get("task", task_data)
    task_id = task.get("id", "unknown")
    task_name = task.get("name", task.get("title", "Unnamed Task"))
    task_status = task.get("status", "unknown")
    estimated_tokens = task.get("estimated_tokens", 0)

    is_completed = is_task_completed(task_status)

    # Skip completed tasks - they don't need compatibility checking
    if is_completed:
        return TaskCompatibility(
            task_id=task_id,
            task_name=task_name,
            status=task_status,
            estimated_tokens=estimated_tokens,
            context_window=context_window,
            compatibility=CompatibilityStatus.COMPATIBLE,
            is_completed=True,
            message="Task already completed",
        )

    # Unknown token count
    if estimated_tokens == 0:
        return TaskCompatibility(
            task_id=task_id,
            task_name=task_name,
            status=task_status,
            estimated_tokens=0,
            context_window=context_window,
            compatibility=CompatibilityStatus.UNKNOWN,
            message="No token estimate available",
        )

    # Calculate usable context (with buffer)
    usable_context = int(context_window * (1 - buffer_percent))
    utilization = (estimated_tokens / context_window) * 100

    if estimated_tokens > context_window:
        # Definitely oversized
        overflow = estimated_tokens - context_window
        return TaskCompatibility(
            task_id=task_id,
            task_name=task_name,
            status=task_status,
            estimated_tokens=estimated_tokens,
            context_window=context_window,
            compatibility=CompatibilityStatus.OVERSIZED,
            overflow_tokens=overflow,
            utilization_percent=utilization,
            message=f"Exceeds context by {format_token_count(overflow)} tokens",
        )
    elif estimated_tokens > usable_context:
        # Fits but no buffer for response
        overflow = estimated_tokens - usable_context
        return TaskCompatibility(
            task_id=task_id,
            task_name=task_name,
            status=task_status,
            estimated_tokens=estimated_tokens,
            context_window=context_window,
            compatibility=CompatibilityStatus.WARNING,
            overflow_tokens=overflow,
            utilization_percent=utilization,
            message=f"May not leave room for response ({utilization:.0f}% utilization)",
        )
    else:
        # Compatible
        return TaskCompatibility(
            task_id=task_id,
            task_name=task_name,
            status=task_status,
            estimated_tokens=estimated_tokens,
            context_window=context_window,
            compatibility=CompatibilityStatus.COMPATIBLE,
            utilization_percent=utilization,
            message=f"Fits within context ({utilization:.0f}% utilization)",
        )


def load_sprint_tasks(sprint_id: str, project_root: Optional[Path] = None) -> Tuple[Dict, List[Dict]]:
    """
    Load sprint and its tasks from the roadmap.

    Args:
        sprint_id: Sprint identifier.
        project_root: Project root directory.

    Returns:
        Tuple of (sprint_data, list of task_data).
    """
    if project_root is None:
        project_root = Path.cwd()

    roadmap_root = project_root / ".vibey" / "roadmap"

    # Find the sprint file - need to search in track directories
    sprint_file = None
    sprint_dir = None

    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir():
            continue
        potential_sprint_dir = track_dir / sprint_id
        if potential_sprint_dir.exists():
            sprint_file = potential_sprint_dir / "sprint.yaml"
            sprint_dir = potential_sprint_dir
            break

    if not sprint_file or not sprint_file.exists():
        raise FileNotFoundError(f"Sprint not found: {sprint_id}")

    # Load sprint data
    with open(sprint_file) as f:
        sprint_data = yaml.safe_load(f)

    # Load task files
    tasks = []
    if sprint_dir:
        for task_dir in sorted(sprint_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_file = task_dir / "task.yaml"
            if task_file.exists():
                with open(task_file) as f:
                    task_data = yaml.safe_load(f)
                    tasks.append(task_data)

    return sprint_data, tasks


def check_sprint_compatibility(
    sprint_id: str,
    project_root: Optional[Path] = None,
    platform: Optional[str] = None,
    context_window: Optional[int] = None,
    include_completed: bool = False,
) -> SprintCompatibility:
    """
    Check sprint compatibility with current platform.

    Args:
        sprint_id: Sprint identifier.
        project_root: Project root directory.
        platform: Override platform (auto-detect if None).
        context_window: Override context window.
        include_completed: Include completed tasks in analysis.

    Returns:
        SprintCompatibility with detailed results.
    """
    if project_root is None:
        project_root = Path.cwd()

    # Get platform info
    platform_info = get_effective_platform(project_root)
    if platform:
        from vibey.platform import get_platform_info
        platform_info = get_platform_info(platform)
    if context_window:
        platform_info.context_window = context_window

    ctx_window = platform_info.context_window

    # Load sprint and tasks
    sprint_data, tasks = load_sprint_tasks(sprint_id, project_root)
    sprint = sprint_data.get("sprint", sprint_data)
    sprint_name = sprint.get("name", sprint_id)

    # Check each task
    task_results = []
    for task_data in tasks:
        result = check_task_compatibility(task_data, ctx_window)
        task_results.append(result)

    # Filter results
    if not include_completed:
        incomplete_results = [t for t in task_results if not t.is_completed]
    else:
        incomplete_results = task_results

    # Count by status
    total = len(task_results)
    completed = sum(1 for t in task_results if t.is_completed)
    incomplete = total - completed

    compatible = sum(1 for t in incomplete_results if t.compatibility == CompatibilityStatus.COMPATIBLE)
    oversized = sum(1 for t in incomplete_results if t.compatibility == CompatibilityStatus.OVERSIZED)
    warning = sum(1 for t in incomplete_results if t.compatibility == CompatibilityStatus.WARNING)
    unknown = sum(1 for t in incomplete_results if t.compatibility == CompatibilityStatus.UNKNOWN)

    # Determine overall status
    if oversized > 0:
        overall = CompatibilityStatus.OVERSIZED
    elif warning > 0:
        overall = CompatibilityStatus.WARNING
    elif unknown > 0 and compatible == 0:
        overall = CompatibilityStatus.UNKNOWN
    else:
        overall = CompatibilityStatus.COMPATIBLE

    # Generate recommendations
    recommendations = []
    if oversized > 0:
        recommendations.append(
            f"Recalculate sprint for {platform_info.display_name} ({format_token_count(ctx_window)} context)"
        )
        recommendations.append(
            f"{oversized} task(s) exceed your platform's context window"
        )
    if warning > 0:
        recommendations.append(
            f"{warning} task(s) may not leave room for AI responses"
        )
    if unknown > 0:
        recommendations.append(
            f"{unknown} task(s) have no token estimates - consider adding estimates"
        )

    return SprintCompatibility(
        sprint_id=sprint_id,
        sprint_name=sprint_name,
        platform=platform_info,
        total_tasks=total,
        completed_tasks=completed,
        incomplete_tasks=incomplete,
        compatible_tasks=compatible,
        oversized_tasks=oversized,
        warning_tasks=warning,
        unknown_tasks=unknown,
        overall_status=overall,
        task_results=task_results if include_completed else incomplete_results,
        recommendations=recommendations,
    )


def format_compatibility_result(result: SprintCompatibility, verbose: bool = False) -> str:
    """
    Format compatibility result for CLI display.

    Args:
        result: SprintCompatibility to format.
        verbose: Show all tasks (not just problematic ones).

    Returns:
        Formatted string for display.
    """
    lines = []

    # Header
    lines.append(f"\nSprint Compatibility Check: {result.sprint_id}")
    lines.append("=" * 70)

    # Platform info
    lines.append(f"\nPlatform: {result.platform.display_name}")
    lines.append(f"Context Window: {format_token_count(result.platform.context_window)} tokens")

    # Summary
    lines.append(f"\nTask Summary:")
    lines.append(f"  Total Tasks:     {result.total_tasks}")
    lines.append(f"  Completed:       {result.completed_tasks}")
    lines.append(f"  Incomplete:      {result.incomplete_tasks}")

    if result.incomplete_tasks > 0:
        lines.append(f"\nIncomplete Task Compatibility:")
        lines.append(f"  ✅ Compatible:   {result.compatible_tasks}")
        lines.append(f"  ⚠️  Warning:      {result.warning_tasks}")
        lines.append(f"  ❌ Oversized:    {result.oversized_tasks}")
        lines.append(f"  ❓ Unknown:      {result.unknown_tasks}")

    # Overall status
    status_icons = {
        CompatibilityStatus.COMPATIBLE: "✅",
        CompatibilityStatus.WARNING: "⚠️",
        CompatibilityStatus.OVERSIZED: "❌",
        CompatibilityStatus.UNKNOWN: "❓",
    }
    lines.append(f"\nOverall Status: {status_icons[result.overall_status]} {result.overall_status.value.upper()}")

    # Problem tasks
    problem_tasks = [t for t in result.task_results
                     if t.compatibility in (CompatibilityStatus.OVERSIZED, CompatibilityStatus.WARNING)]

    if problem_tasks:
        lines.append(f"\nProblematic Tasks:")
        lines.append("-" * 70)
        for task in problem_tasks:
            icon = "❌" if task.compatibility == CompatibilityStatus.OVERSIZED else "⚠️"
            lines.append(f"  {icon} {task.task_id}")
            lines.append(f"     {task.task_name}")
            lines.append(f"     Tokens: {format_token_count(task.estimated_tokens)} ({task.utilization_percent:.0f}% of context)")
            lines.append(f"     {task.message}")
            lines.append("")

    # Verbose: show all tasks
    if verbose and result.task_results:
        lines.append(f"\nAll Tasks:")
        lines.append("-" * 70)
        for task in result.task_results:
            icon = {
                CompatibilityStatus.COMPATIBLE: "✅",
                CompatibilityStatus.WARNING: "⚠️",
                CompatibilityStatus.OVERSIZED: "❌",
                CompatibilityStatus.UNKNOWN: "❓",
            }[task.compatibility]
            status = "[DONE]" if task.is_completed else f"[{task.status}]"
            tokens = format_token_count(task.estimated_tokens) if task.estimated_tokens else "?"
            lines.append(f"  {icon} {task.task_id} {status}")
            lines.append(f"     {task.task_name}")
            lines.append(f"     Tokens: {tokens}")
            lines.append("")

    # Recommendations
    if result.recommendations:
        lines.append("Recommendations:")
        for rec in result.recommendations:
            lines.append(f"  → {rec}")

    # Action guidance
    if result.needs_recalculation:
        lines.append(f"\n💡 Run 'vibey roadmap recalculate {result.sprint_id}' to split oversized tasks")
    elif result.can_proceed:
        lines.append(f"\n✅ Sprint is compatible with your platform - ready to proceed")

    return "\n".join(lines)
