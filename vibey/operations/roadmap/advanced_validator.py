"""
Advanced Roadmap Validation Module

Detects complex edge cases and integrity issues:
- Circular dependencies
- Orphaned tasks
- Broken references
- Auto-repair capabilities

Implements deferred functionality from Sprint 1 Task 005.

Author: Vibey Framework
Created: 2025-11-21
Sprint: Post-Sprint 1 Enhancement
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from difflib import get_close_matches


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CircularDependency:
    """Represents a circular dependency cycle."""
    cycle: List[str]  # Task IDs in the cycle
    cycle_length: int
    description: str

    def __str__(self) -> str:
        cycle_str = " → ".join(self.cycle)
        return f"Circular dependency ({self.cycle_length} tasks): {cycle_str}"


@dataclass
class OrphanedTask:
    """Represents a task with missing sprint reference."""
    task_id: str
    task_file: str
    missing_sprint_id: str
    suggested_sprints: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Orphaned task {self.task_id} references non-existent sprint: {self.missing_sprint_id}"


@dataclass
class BrokenReference:
    """Represents a broken task reference."""
    task_id: str
    task_file: str
    field: str  # 'blocks', 'depends_on', 'depended_on_by', etc.
    missing_id: str
    suggested_ids: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Task {self.task_id} references non-existent task in {self.field}: {self.missing_id}"


@dataclass
class ProgressMismatch:
    """Represents inconsistent progress counters."""
    entity_type: str  # 'sprint' or 'track'
    entity_id: str
    entity_file: str
    claimed_completed: int
    actual_completed: int
    claimed_total: int
    actual_total: int
    can_auto_fix: bool = True

    def __str__(self) -> str:
        return (f"{self.entity_type.capitalize()} {self.entity_id}: "
                f"claimed {self.claimed_completed}/{self.claimed_total} but "
                f"actual {self.actual_completed}/{self.actual_total}")


@dataclass
class AdvancedValidationReport:
    """Report of advanced validation results."""
    total_tasks: int = 0
    total_sprints: int = 0
    total_tracks: int = 0

    circular_dependencies: List[CircularDependency] = field(default_factory=list)
    orphaned_tasks: List[OrphanedTask] = field(default_factory=list)
    broken_references: List[BrokenReference] = field(default_factory=list)
    progress_mismatches: List[ProgressMismatch] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return (len(self.circular_dependencies) > 0 or
                len(self.orphaned_tasks) > 0 or
                len(self.broken_references) > 0 or
                len(self.progress_mismatches) > 0)

    @property
    def issue_count(self) -> int:
        """Total number of issues found."""
        return (len(self.circular_dependencies) +
                len(self.orphaned_tasks) +
                len(self.broken_references) +
                len(self.progress_mismatches))


# ============================================================================
# Circular Dependency Detection
# ============================================================================

def detect_circular_dependencies(
    tasks: Dict[str, Dict[str, Any]]
) -> List[CircularDependency]:
    """
    Detect circular dependency chains using depth-first search.

    Args:
        tasks: Dictionary mapping task_id to task data

    Returns:
        List of CircularDependency objects
    """
    visited = set()
    rec_stack = set()
    cycles = []

    def get_dependencies(task_id: str) -> List[str]:
        """Get all task IDs this task depends on."""
        task = tasks.get(task_id, {})
        deps = []

        # Get depends_on list
        depends_on = task.get('depends_on', [])
        if isinstance(depends_on, list):
            for item in depends_on:
                if isinstance(item, str):
                    deps.append(item)
                elif isinstance(item, dict) and 'target_id' in item:
                    deps.append(item['target_id'])

        # Get blocked_by list
        blocked_by = task.get('blocked_by', [])
        if isinstance(blocked_by, list):
            for item in blocked_by:
                if isinstance(item, str):
                    deps.append(item)
                elif isinstance(item, dict) and 'target_id' in item:
                    deps.append(item['target_id'])

        return deps

    def dfs(task_id: str, path: List[str]):
        """Depth-first search to find cycles."""
        visited.add(task_id)
        rec_stack.add(task_id)
        path.append(task_id)

        # Check all dependencies
        for dep_id in get_dependencies(task_id):
            if dep_id not in visited:
                dfs(dep_id, path.copy())
            elif dep_id in rec_stack:
                # Found a cycle!
                try:
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:] + [dep_id]

                    # Create cycle description
                    cycle_desc = f"Circular dependency detected: {' → '.join(cycle)}"

                    cycles.append(CircularDependency(
                        cycle=cycle,
                        cycle_length=len(cycle) - 1,  # Don't count duplicate
                        description=cycle_desc
                    ))
                except ValueError:
                    pass  # dep_id not in path (shouldn't happen)

        rec_stack.remove(task_id)

    # Run DFS from each unvisited task
    for task_id in tasks.keys():
        if task_id not in visited:
            dfs(task_id, [])

    # Remove duplicate cycles (same cycle detected from different entry points)
    unique_cycles = []
    seen_cycles = set()

    for cycle in cycles:
        # Normalize cycle by sorting the task IDs
        normalized = tuple(sorted(cycle.cycle[:-1]))  # Exclude duplicate last element
        if normalized not in seen_cycles:
            seen_cycles.add(normalized)
            unique_cycles.append(cycle)

    return unique_cycles


# ============================================================================
# Orphaned Task Detection
# ============================================================================

def find_orphaned_tasks(
    roadmap_dir: Path
) -> List[OrphanedTask]:
    """
    Find tasks referencing non-existent sprints.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        List of OrphanedTask objects
    """
    # Load all sprint IDs
    sprint_ids = set()
    sprint_files = {}

    for sprint_file in roadmap_dir.glob("*/*/sprint.yaml"):
        try:
            with open(sprint_file) as f:
                data = yaml.safe_load(f)

            if data and 'sprint' in data:
                sprint_id = data['sprint'].get('id')
                if sprint_id:
                    sprint_ids.add(sprint_id)
                    sprint_files[sprint_id] = str(sprint_file)
        except Exception:
            continue

    # Check all tasks
    orphaned = []

    for task_file in roadmap_dir.glob("*/*/*/task.yaml"):
        try:
            with open(task_file) as f:
                data = yaml.safe_load(f)

            if not data or 'task' not in data:
                continue

            task = data['task']
            task_id = task.get('id')
            sprint_id = task.get('sprint_id')

            if not task_id or not sprint_id:
                continue

            # Check if sprint exists
            if sprint_id not in sprint_ids:
                # Find similar sprint IDs
                suggested = get_close_matches(sprint_id, sprint_ids, n=3, cutoff=0.6)

                orphaned.append(OrphanedTask(
                    task_id=task_id,
                    task_file=str(task_file),
                    missing_sprint_id=sprint_id,
                    suggested_sprints=suggested
                ))

        except Exception:
            continue

    return orphaned


# ============================================================================
# Broken Reference Detection
# ============================================================================

def find_broken_references(
    roadmap_dir: Path
) -> List[BrokenReference]:
    """
    Find broken task ID references.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        List of BrokenReference objects
    """
    # Load all task IDs
    all_task_ids = set()
    task_files = {}
    task_data_map = {}

    for task_file in roadmap_dir.glob("*/*/*/task.yaml"):
        try:
            with open(task_file) as f:
                data = yaml.safe_load(f)

            if data and 'task' in data:
                task = data['task']
                task_id = task.get('id')
                if task_id:
                    all_task_ids.add(task_id)
                    task_files[task_id] = str(task_file)
                    task_data_map[task_id] = task
        except Exception:
            continue

    # Check all references
    broken = []

    for task_id, task in task_data_map.items():
        task_file = task_files[task_id]

        # Check 'blocks' references
        blocks = task.get('blocks', [])
        if isinstance(blocks, list):
            for block_entry in blocks:
                if isinstance(block_entry, dict):
                    target_id = block_entry.get('target_id')
                    if target_id and target_id not in all_task_ids:
                        suggested = get_close_matches(target_id, all_task_ids, n=3, cutoff=0.6)
                        broken.append(BrokenReference(
                            task_id=task_id,
                            task_file=task_file,
                            field='blocks',
                            missing_id=target_id,
                            suggested_ids=suggested
                        ))

        # Check 'depends_on' references
        depends_on = task.get('depends_on', [])
        if isinstance(depends_on, list):
            for dep_id in depends_on:
                if isinstance(dep_id, str) and dep_id not in all_task_ids:
                    suggested = get_close_matches(dep_id, all_task_ids, n=3, cutoff=0.6)
                    broken.append(BrokenReference(
                        task_id=task_id,
                        task_file=task_file,
                        field='depends_on',
                        missing_id=dep_id,
                        suggested_ids=suggested
                    ))

        # Check 'blocked_by' references
        blocked_by = task.get('blocked_by', [])
        if isinstance(blocked_by, list):
            for blocker_id in blocked_by:
                if isinstance(blocker_id, str) and blocker_id not in all_task_ids:
                    suggested = get_close_matches(blocker_id, all_task_ids, n=3, cutoff=0.6)
                    broken.append(BrokenReference(
                        task_id=task_id,
                        task_file=task_file,
                        field='blocked_by',
                        missing_id=blocker_id,
                        suggested_ids=suggested
                    ))

        # Check 'depended_on_by' references
        depended_on_by = task.get('depended_on_by', [])
        if isinstance(depended_on_by, list):
            for dependent_id in depended_on_by:
                if isinstance(dependent_id, str) and dependent_id not in all_task_ids:
                    suggested = get_close_matches(dependent_id, all_task_ids, n=3, cutoff=0.6)
                    broken.append(BrokenReference(
                        task_id=task_id,
                        task_file=task_file,
                        field='depended_on_by',
                        missing_id=dependent_id,
                        suggested_ids=suggested
                    ))

    return broken


# ============================================================================
# Progress Counter Validation
# ============================================================================

def validate_progress_counters(
    roadmap_dir: Path
) -> List[ProgressMismatch]:
    """
    Validate progress counters match actual task states.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        List of ProgressMismatch objects
    """
    mismatches = []

    # Validate sprint progress
    for sprint_file in roadmap_dir.glob("*/*/sprint.yaml"):
        try:
            with open(sprint_file) as f:
                data = yaml.safe_load(f)

            if not data or 'sprint' not in data:
                continue

            sprint = data['sprint']
            sprint_id = sprint.get('id')
            progress = sprint.get('progress', {})

            claimed_completed = progress.get('tasks_completed', 0)
            claimed_total = progress.get('tasks_total', 0)

            # Count actual tasks
            sprint_dir = sprint_file.parent
            task_files = list(sprint_dir.glob("*/task.yaml"))
            actual_total = len(task_files)

            actual_completed = 0
            for task_file in task_files:
                try:
                    with open(task_file) as f:
                        task_data = yaml.safe_load(f)
                    if task_data and 'task' in task_data:
                        if task_data['task'].get('status') == 'completed':
                            actual_completed += 1
                except Exception:
                    continue

            # Check for mismatch
            if (claimed_completed != actual_completed or
                claimed_total != actual_total):
                mismatches.append(ProgressMismatch(
                    entity_type='sprint',
                    entity_id=sprint_id,
                    entity_file=str(sprint_file),
                    claimed_completed=claimed_completed,
                    actual_completed=actual_completed,
                    claimed_total=claimed_total,
                    actual_total=actual_total,
                    can_auto_fix=True
                ))

        except Exception:
            continue

    # Validate track progress
    for track_file in roadmap_dir.glob("*/track.yaml"):
        try:
            with open(track_file) as f:
                data = yaml.safe_load(f)

            if not data or 'track' not in data:
                continue

            track = data['track']
            track_id = track.get('id')
            progress = track.get('progress', {})

            claimed_completed = progress.get('sprints_completed', 0)
            claimed_total = progress.get('sprints_total', 0)

            # Count actual sprints
            track_dir = track_file.parent
            sprint_files = list(track_dir.glob("*/sprint.yaml"))
            actual_total = len(sprint_files)

            actual_completed = 0
            for sprint_file in sprint_files:
                try:
                    with open(sprint_file) as f:
                        sprint_data = yaml.safe_load(f)
                    if sprint_data and 'sprint' in sprint_data:
                        if sprint_data['sprint'].get('status') == 'completed':
                            actual_completed += 1
                except Exception:
                    continue

            # Check for mismatch
            if (claimed_completed != actual_completed or
                claimed_total != actual_total):
                mismatches.append(ProgressMismatch(
                    entity_type='track',
                    entity_id=track_id,
                    entity_file=str(track_file),
                    claimed_completed=claimed_completed,
                    actual_completed=actual_completed,
                    claimed_total=claimed_total,
                    actual_total=actual_total,
                    can_auto_fix=True
                ))

        except Exception:
            continue

    return mismatches


# ============================================================================
# Advanced Validator Class
# ============================================================================

class AdvancedValidator:
    """
    Comprehensive validator for complex roadmap integrity issues.
    """

    def __init__(self, root_dir: Path):
        """
        Initialize advanced validator.

        Args:
            root_dir: Repository root directory
        """
        self.root_dir = root_dir
        self.roadmap_dir = root_dir / ".vibey" / "roadmap"

    def validate(self) -> AdvancedValidationReport:
        """
        Run all advanced validation checks.

        Returns:
            AdvancedValidationReport with all detected issues
        """
        report = AdvancedValidationReport()

        if not self.roadmap_dir.exists():
            return report

        # Load all tasks for circular dependency detection
        tasks = self._load_all_tasks()
        report.total_tasks = len(tasks)

        # Detect circular dependencies
        report.circular_dependencies = detect_circular_dependencies(tasks)

        # Find orphaned tasks
        report.orphaned_tasks = find_orphaned_tasks(self.roadmap_dir)

        # Find broken references
        report.broken_references = find_broken_references(self.roadmap_dir)

        # Validate progress counters
        report.progress_mismatches = validate_progress_counters(self.roadmap_dir)

        # Count sprints and tracks
        report.total_sprints = len(list(self.roadmap_dir.glob("*/*/sprint.yaml")))
        report.total_tracks = len(list(self.roadmap_dir.glob("*/track.yaml")))

        return report

    def _load_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Load all task data for dependency analysis."""
        tasks = {}

        for task_file in self.roadmap_dir.glob("*/*/*/task.yaml"):
            try:
                with open(task_file) as f:
                    data = yaml.safe_load(f)

                if data and 'task' in data:
                    task = data['task']
                    task_id = task.get('id')
                    if task_id:
                        tasks[task_id] = task
            except Exception:
                continue

        return tasks


# ============================================================================
# Report Printing
# ============================================================================

def print_advanced_report(report: AdvancedValidationReport, verbose: bool = False):
    """
    Print advanced validation report.

    Args:
        report: AdvancedValidationReport to print
        verbose: Show detailed information
    """
    print(f"\n{'='*80}")
    print("Advanced Roadmap Validation Report")
    print(f"{'='*80}\n")

    # Summary
    print(f"Roadmap entities:")
    print(f"  Tasks: {report.total_tasks}")
    print(f"  Sprints: {report.total_sprints}")
    print(f"  Tracks: {report.total_tracks}\n")

    # Issues found
    if not report.has_issues:
        print("✅ No issues detected!\n")
        print(f"{'='*80}\n")
        return

    print(f"⚠️  Issues detected: {report.issue_count}\n")

    # Circular dependencies
    if report.circular_dependencies:
        print(f"{'─'*80}")
        print(f"🔄 Circular Dependencies: {len(report.circular_dependencies)}")
        print(f"{'─'*80}\n")

        for i, cycle in enumerate(report.circular_dependencies, 1):
            print(f"{i}. {cycle}")
            if verbose:
                print(f"   Length: {cycle.cycle_length} tasks")
                print(f"   Suggestion: Break dependency between any two tasks in cycle")
            print()

    # Orphaned tasks
    if report.orphaned_tasks:
        print(f"{'─'*80}")
        print(f"👻 Orphaned Tasks: {len(report.orphaned_tasks)}")
        print(f"{'─'*80}\n")

        for i, orphan in enumerate(report.orphaned_tasks, 1):
            print(f"{i}. {orphan}")
            if orphan.suggested_sprints:
                print(f"   Suggested sprints: {', '.join(orphan.suggested_sprints)}")
            if verbose:
                print(f"   File: {orphan.task_file}")
            print()

    # Broken references
    if report.broken_references:
        print(f"{'─'*80}")
        print(f"🔗 Broken References: {len(report.broken_references)}")
        print(f"{'─'*80}\n")

        for i, ref in enumerate(report.broken_references, 1):
            print(f"{i}. {ref}")
            if ref.suggested_ids:
                print(f"   Did you mean: {', '.join(ref.suggested_ids)}")
            if verbose:
                print(f"   File: {ref.task_file}")
            print()

    # Progress mismatches
    if report.progress_mismatches:
        print(f"{'─'*80}")
        print(f"📊 Progress Counter Mismatches: {len(report.progress_mismatches)}")
        print(f"{'─'*80}\n")

        for i, mismatch in enumerate(report.progress_mismatches, 1):
            print(f"{i}. {mismatch}")
            if mismatch.can_auto_fix:
                print(f"   ✅ Can be auto-fixed")
            if verbose:
                print(f"   File: {mismatch.entity_file}")
            print()

    # Status
    print(f"{'='*80}")
    print("❌ Advanced validation FAILED")
    print(f"{'='*80}\n")
