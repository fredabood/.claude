"""
IndependentTaskIdentifier - Identify tasks that can execute in parallel.

This module provides parallel execution grouping for implementation mode,
enabling multiple tasks to be executed concurrently when they have no
dependencies or file conflicts.

Key Features:
- Build parallel execution groups (waves) from task lists
- Check direct and transitive dependencies between tasks
- Detect file conflicts based on task plans and descriptions
- Calculate maximum parallelism for a set of tasks
- Suggest optimal execution order with parallelism

Usage:
    from vibey.services.implementation import (
        IndependentTaskIdentifier,
        ParallelGroup,
    )
    from pathlib import Path

    # Build dependency graph
    graph = CriterionDependencyGraph(roadmap_root=Path(".vibey/roadmap"))
    graph.build()

    # Create identifier
    identifier = IndependentTaskIdentifier(graph)

    # Find parallel groups
    groups = identifier.find_parallel_groups(tasks)

    # Get execution waves
    waves = identifier.suggest_execution_order(tasks)
    for i, wave in enumerate(waves):
        print(f"Wave {i}: {[t.id for t in wave]}")

Design Reference:
- Implementation Mode Track: Parallel Execution
- ADR-0002: Flat Directory Structure
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.dependency_graph import CriterionDependencyGraph

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class ParallelGroup:
    """
    A group of tasks that can execute in parallel.

    Represents a set of tasks with no mutual dependencies or file conflicts
    that can safely execute concurrently within a single "wave" of execution.

    Attributes:
        tasks: List of HierarchicalTicket objects in this group
        wave_number: The wave index (0-indexed) for execution ordering
        max_concurrent: Maximum concurrent tasks allowed in this group
        estimated_duration: Optional estimate for longest task duration
        file_coverage: Set of file paths that tasks in this group will modify

    Example:
        >>> group = ParallelGroup(
        ...     tasks=[task1, task2],
        ...     wave_number=0,
        ...     max_concurrent=2,
        ...     file_coverage={Path("src/foo.py"), Path("src/bar.py")},
        ... )
        >>> group.has_conflict_with(other_group)
        False
    """

    tasks: List["HierarchicalTicket"]
    wave_number: int
    max_concurrent: int
    estimated_duration: Optional[timedelta] = None
    file_coverage: Set[Path] = field(default_factory=set)

    def has_conflict_with(self, other: "ParallelGroup") -> bool:
        """
        Check if this group conflicts with another based on file coverage.

        Two groups conflict if they both modify any of the same files,
        which would create race conditions during parallel execution.

        Args:
            other: Another ParallelGroup to check for conflicts

        Returns:
            True if there are overlapping files, False otherwise

        Example:
            >>> group1 = ParallelGroup(tasks=[], wave_number=0, max_concurrent=2,
            ...                        file_coverage={Path("src/foo.py")})
            >>> group2 = ParallelGroup(tasks=[], wave_number=1, max_concurrent=2,
            ...                        file_coverage={Path("src/bar.py")})
            >>> group1.has_conflict_with(group2)
            False
        """
        return bool(self.file_coverage & other.file_coverage)

    @property
    def task_ids(self) -> List[str]:
        """Get list of task IDs in this group."""
        return [task.id for task in self.tasks]

    @property
    def task_count(self) -> int:
        """Get number of tasks in this group."""
        return len(self.tasks)

    def __repr__(self) -> str:
        return (
            f"ParallelGroup(wave={self.wave_number}, "
            f"tasks={self.task_count}, "
            f"files={len(self.file_coverage)})"
        )


# =============================================================================
# INDEPENDENT TASK IDENTIFIER
# =============================================================================


class IndependentTaskIdentifier:
    """
    Identifies tasks that can execute in parallel.

    Uses the CriterionDependencyGraph to analyze task dependencies and
    file coverage to determine which tasks can safely execute concurrently.

    Tasks are independent if:
    1. No direct dependency between them
    2. No transitive dependency
    3. No file conflicts (modifying same files)
    4. No criterion conflicts

    Attributes:
        graph: CriterionDependencyGraph for dependency analysis
        _file_map: Cache of task_id -> set of file paths

    Example:
        >>> graph = CriterionDependencyGraph(Path(".vibey/roadmap")).build()
        >>> identifier = IndependentTaskIdentifier(graph)
        >>> groups = identifier.find_parallel_groups(tasks)
        >>> print(f"Found {len(groups)} parallel groups")
    """

    def __init__(self, dependency_graph: "CriterionDependencyGraph"):
        """
        Initialize IndependentTaskIdentifier.

        Args:
            dependency_graph: Built CriterionDependencyGraph for dependency analysis

        Example:
            >>> graph = CriterionDependencyGraph(Path(".vibey/roadmap")).build()
            >>> identifier = IndependentTaskIdentifier(graph)
        """
        self.graph = dependency_graph
        self._file_map: Dict[str, Set[Path]] = {}

    def find_parallel_groups(
        self,
        tasks: List["HierarchicalTicket"],
        max_concurrent: int = 4,
    ) -> List[ParallelGroup]:
        """
        Identify groups of tasks that can execute in parallel.

        Tasks are independent if:
        1. No direct dependency between them
        2. No transitive dependency
        3. No file conflicts (modifying same files)
        4. No criterion conflicts

        Groups tasks into parallel execution waves, where all tasks in
        a wave can run concurrently without conflicts.

        Args:
            tasks: List of HierarchicalTicket objects to group
            max_concurrent: Maximum tasks per parallel group (default 4)

        Returns:
            List of ParallelGroup objects representing execution waves

        Example:
            >>> groups = identifier.find_parallel_groups(tasks, max_concurrent=4)
            >>> for group in groups:
            ...     print(f"Wave {group.wave_number}: {group.task_ids}")
        """
        if not tasks:
            return []

        # Pre-compute file coverage for all tasks
        for task in tasks:
            self._compute_file_coverage(task)

        # Get execution order from dependency graph
        waves = self._build_execution_waves(tasks, max_concurrent)

        # Convert waves to ParallelGroup objects
        groups: List[ParallelGroup] = []
        for wave_num, wave_tasks in enumerate(waves):
            # Compute file coverage for the entire wave
            wave_files: Set[Path] = set()
            for task in wave_tasks:
                wave_files.update(self._file_map.get(task.id, set()))

            # Estimate duration based on tokens (rough heuristic)
            estimated_duration = self._estimate_wave_duration(wave_tasks)

            group = ParallelGroup(
                tasks=list(wave_tasks),
                wave_number=wave_num,
                max_concurrent=min(max_concurrent, len(wave_tasks)),
                estimated_duration=estimated_duration,
                file_coverage=wave_files,
            )
            groups.append(group)

        logger.info(
            f"Created {len(groups)} parallel groups from {len(tasks)} tasks"
        )
        return groups

    def has_dependency(self, task_a: str, task_b: str) -> bool:
        """
        Check if task_a depends on task_b or vice versa.

        Uses the dependency graph to check for both direct and transitive
        dependencies in either direction.

        Args:
            task_a: First task ID
            task_b: Second task ID

        Returns:
            True if there is any dependency relationship between the tasks

        Example:
            >>> if identifier.has_dependency(task1.id, task2.id):
            ...     print("Tasks must run sequentially")
        """
        # Check direct dependency in either direction
        if self.graph.graph.has_edge(task_a, task_b):
            return True
        if self.graph.graph.has_edge(task_b, task_a):
            return True

        # Check transitive dependency using transitive closure
        closure_a = self.graph.get_transitive_closure(task_a)
        if task_b in closure_a:
            return True

        closure_b = self.graph.get_transitive_closure(task_b)
        if task_a in closure_b:
            return True

        return False

    def has_file_conflict(self, task_a: str, task_b: str) -> bool:
        """
        Check if tasks modify overlapping files.

        Two tasks have a file conflict if they both plan to modify
        any of the same files, which would create race conditions
        during parallel execution.

        Args:
            task_a: First task ID
            task_b: Second task ID

        Returns:
            True if tasks modify overlapping files

        Example:
            >>> if identifier.has_file_conflict(task1.id, task2.id):
            ...     print("Tasks modify same files - cannot parallelize")
        """
        files_a = self._file_map.get(task_a, set())
        files_b = self._file_map.get(task_b, set())
        return bool(files_a & files_b)

    def get_max_parallelism(self, tasks: List["HierarchicalTicket"]) -> int:
        """
        Get maximum number of tasks that can run in parallel.

        Analyzes dependencies and file conflicts to determine the
        theoretical maximum parallelism for the given task set.

        Args:
            tasks: List of HierarchicalTicket objects to analyze

        Returns:
            Maximum number of tasks that can execute concurrently

        Example:
            >>> max_parallel = identifier.get_max_parallelism(tasks)
            >>> print(f"Can run up to {max_parallel} tasks at once")
        """
        if not tasks:
            return 0

        # Pre-compute file coverage
        for task in tasks:
            self._compute_file_coverage(task)

        # Build waves to find maximum wave size
        waves = self._build_execution_waves(tasks, max_concurrent=len(tasks))

        if not waves:
            return 0

        # Maximum parallelism is the largest wave
        return max(len(wave) for wave in waves)

    def suggest_execution_order(
        self,
        tasks: List["HierarchicalTicket"],
        max_concurrent: int = 4,
    ) -> List[List["HierarchicalTicket"]]:
        """
        Suggest optimal execution order with parallelism.

        Returns list of "waves" where each wave can run in parallel.
        Waves are ordered such that all dependencies in earlier waves
        complete before later waves begin.

        Args:
            tasks: List of HierarchicalTicket objects to order
            max_concurrent: Maximum tasks per parallel wave (default 4)

        Returns:
            List of waves, where each wave is a list of tasks that
            can execute in parallel

        Example:
            >>> waves = identifier.suggest_execution_order(tasks)
            >>> for i, wave in enumerate(waves):
            ...     print(f"Wave {i}: Execute these in parallel:")
            ...     for task in wave:
            ...         print(f"  - {task.name}")
        """
        if not tasks:
            return []

        # Pre-compute file coverage
        for task in tasks:
            self._compute_file_coverage(task)

        return self._build_execution_waves(tasks, max_concurrent)

    def are_tasks_independent(
        self,
        task_a: "HierarchicalTicket",
        task_b: "HierarchicalTicket",
    ) -> Tuple[bool, List[str]]:
        """
        Check if two tasks are independent (can run in parallel).

        Returns a tuple of (is_independent, reasons) where reasons
        lists any conflicts that prevent parallel execution.

        Args:
            task_a: First task
            task_b: Second task

        Returns:
            Tuple of (is_independent: bool, conflict_reasons: List[str])

        Example:
            >>> independent, reasons = identifier.are_tasks_independent(t1, t2)
            >>> if not independent:
            ...     print(f"Cannot parallelize: {reasons}")
        """
        reasons: List[str] = []

        # Check dependency
        if self.has_dependency(task_a.id, task_b.id):
            # Determine direction
            if self.graph.graph.has_edge(task_a.id, task_b.id):
                reasons.append(f"{task_a.id} depends on {task_b.id}")
            elif self.graph.graph.has_edge(task_b.id, task_a.id):
                reasons.append(f"{task_b.id} depends on {task_a.id}")
            else:
                reasons.append("Transitive dependency exists")

        # Check file conflict
        self._compute_file_coverage(task_a)
        self._compute_file_coverage(task_b)

        if self.has_file_conflict(task_a.id, task_b.id):
            overlap = self._file_map[task_a.id] & self._file_map[task_b.id]
            overlap_str = ", ".join(str(p) for p in list(overlap)[:3])
            if len(overlap) > 3:
                overlap_str += f" (and {len(overlap) - 3} more)"
            reasons.append(f"File conflict: {overlap_str}")

        return (len(reasons) == 0, reasons)

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _compute_file_coverage(self, task: "HierarchicalTicket") -> Set[Path]:
        """
        Compute and cache file paths that a task will modify.

        Parses the task description and plan to identify files that
        will be modified during task implementation.

        Args:
            task: The HierarchicalTicket to analyze

        Returns:
            Set of file paths the task will modify
        """
        if task.id in self._file_map:
            return self._file_map[task.id]

        files: Set[Path] = set()

        # Extract from task description
        if task.description:
            files.update(self._extract_file_paths(task.description))

        # Extract from task plan if available
        plan_content = self._load_task_plan(task)
        if plan_content:
            files.update(self._extract_file_paths(plan_content))

        # Extract from criteria targets
        for criterion in task.criteria:
            target = criterion.target
            # Check for FileExistsTarget
            if hasattr(target, 'paths'):
                for path_str in target.paths:
                    files.add(Path(path_str))
            # Check for file references in description
            if criterion.description:
                files.update(self._extract_file_paths(criterion.description))

        self._file_map[task.id] = files
        return files

    def _load_task_plan(self, task: "HierarchicalTicket") -> Optional[str]:
        """
        Load task plan content if available.

        Args:
            task: The HierarchicalTicket to load plan for

        Returns:
            Plan content as string, or None if not available
        """
        # Check for plan in context directory
        plan_paths = [
            self.graph.root / "context" / "tasks" / task.id / "plan.md",
            self.graph.root / "context" / "tasks" / task.id / "PLAN.md",
            self.graph.root / "context" / "tasks" / task.id / "implementation.md",
        ]

        for plan_path in plan_paths:
            if plan_path.exists():
                try:
                    return plan_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.debug(f"Failed to read plan at {plan_path}: {e}")

        return None

    def _extract_file_paths(self, text: str) -> Set[Path]:
        """
        Extract file paths from text using pattern matching.

        Looks for common file path patterns in task descriptions and plans.

        Args:
            text: Text to search for file paths

        Returns:
            Set of extracted Path objects
        """
        paths: Set[Path] = set()

        # Pattern for file paths with extensions
        # Matches: vibey/cli/main.py, ./src/file.ts, path/to/file.yaml
        file_pattern = r'(?:^|[\s\`\"\'<>])([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]{1,10})(?:[\s\`\"\'<>]|$)'

        matches = re.findall(file_pattern, text)

        for match in matches:
            path = match.strip()

            # Skip URLs
            if path.startswith('http') or path.startswith('www.'):
                continue

            # Skip version numbers like 3.9, 2.5.0
            if re.match(r'^\d+\.\d+', path):
                continue

            # Skip common non-file patterns
            if path in ('e.g.', 'i.e.', 'etc.'):
                continue

            # Normalize path
            if path.startswith('./'):
                path = path[2:]

            paths.add(Path(path))

        return paths

    def _build_execution_waves(
        self,
        tasks: List["HierarchicalTicket"],
        max_concurrent: int,
    ) -> List[List["HierarchicalTicket"]]:
        """
        Build execution waves respecting dependencies and file conflicts.

        Uses a modified Kahn's algorithm for topological sorting that
        groups independent tasks into parallel waves.

        Args:
            tasks: List of tasks to organize into waves
            max_concurrent: Maximum tasks per wave

        Returns:
            List of waves, each containing tasks that can run in parallel
        """
        if not tasks:
            return []

        # Build task ID set and mapping
        task_map: Dict[str, "HierarchicalTicket"] = {t.id: t for t in tasks}
        task_ids = set(task_map.keys())

        # Compute in-degrees (dependencies within our task set)
        in_degree: Dict[str, int] = {tid: 0 for tid in task_ids}

        # Build dependency graph subset for our tasks
        for task_id in task_ids:
            if task_id in self.graph.graph:
                for successor in self.graph.graph.successors(task_id):
                    if successor in task_ids:
                        in_degree[task_id] += 1

        # Initialize ready queue with tasks that have no dependencies
        ready: List[str] = [tid for tid, deg in in_degree.items() if deg == 0]
        waves: List[List["HierarchicalTicket"]] = []
        processed: Set[str] = set()

        while ready:
            # Build current wave from ready tasks
            current_wave: List["HierarchicalTicket"] = []
            wave_files: Set[Path] = set()
            next_ready: List[str] = []

            for task_id in ready:
                if len(current_wave) >= max_concurrent:
                    # Wave is full, defer to next iteration
                    next_ready.append(task_id)
                    continue

                task = task_map[task_id]
                task_files = self._file_map.get(task_id, set())

                # Check for file conflicts with current wave
                if wave_files & task_files:
                    # File conflict, defer to next wave
                    next_ready.append(task_id)
                    continue

                # Add to current wave
                current_wave.append(task)
                wave_files.update(task_files)
                processed.add(task_id)

            if current_wave:
                waves.append(current_wave)

            # Update ready queue
            ready = list(next_ready)

            # Add newly ready tasks (dependencies completed)
            for completed_id in list(processed):
                if completed_id in self.graph.graph:
                    for predecessor in self.graph.graph.predecessors(completed_id):
                        if predecessor in task_ids and predecessor not in processed:
                            # Check if all dependencies are completed
                            all_deps_done = True
                            for dep in self.graph.graph.successors(predecessor):
                                if dep in task_ids and dep not in processed:
                                    all_deps_done = False
                                    break

                            if all_deps_done and predecessor not in ready:
                                ready.append(predecessor)

            # Handle orphaned tasks (not in graph but in our list)
            for task_id in task_ids:
                if task_id not in processed and task_id not in ready:
                    # Check if it has any unprocessed dependencies
                    has_deps = False
                    if task_id in self.graph.graph:
                        for successor in self.graph.graph.successors(task_id):
                            if successor in task_ids and successor not in processed:
                                has_deps = True
                                break

                    if not has_deps:
                        ready.append(task_id)

            # Safety check to prevent infinite loops
            if not current_wave and ready:
                # Force process remaining tasks if we're stuck
                logger.warning("Potential cycle detected, forcing task processing")
                remaining = [task_map[tid] for tid in ready if tid not in processed]
                if remaining:
                    waves.append(remaining[:max_concurrent])
                    for task in remaining[:max_concurrent]:
                        processed.add(task.id)
                    ready = [tid for tid in ready if tid not in processed]

            if not ready and len(processed) < len(task_ids):
                # Add any remaining unprocessed tasks
                remaining_ids = task_ids - processed
                ready = list(remaining_ids)

        return waves

    def _estimate_wave_duration(
        self,
        tasks: List["HierarchicalTicket"],
    ) -> Optional[timedelta]:
        """
        Estimate duration for a wave based on token estimates.

        Uses a rough heuristic based on estimated tokens to predict
        how long the longest task in the wave will take.

        Args:
            tasks: Tasks in the wave

        Returns:
            Estimated timedelta, or None if no estimates available
        """
        if not tasks:
            return None

        max_tokens = 0
        for task in tasks:
            if hasattr(task, 'computed_tokens'):
                max_tokens = max(max_tokens, task.computed_tokens)
            elif hasattr(task, 'estimated_tokens'):
                est = getattr(task, 'estimated_tokens', 0) or 0
                max_tokens = max(max_tokens, est)

        if max_tokens == 0:
            return None

        # Rough heuristic: assume ~1000 tokens per minute
        # This is very approximate and will vary by model/task complexity
        minutes = max_tokens / 1000
        return timedelta(minutes=minutes)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ParallelGroup",
    "IndependentTaskIdentifier",
]
