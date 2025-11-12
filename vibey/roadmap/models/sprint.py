"""
Sprint data model.

A Sprint is a logical unit of work pushable to production.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .common import Status, TaskType, DependencyType, DependencyStatus
from .task import TaskCompletionCommit
from .standard import Standard


@dataclass
class SprintProgress:
    """Sprint progress tracking."""

    development_tasks_total: int
    development_tasks_completed: int
    completion_gate_tasks_total: int
    completion_gate_tasks_completed: int
    production_gate_tasks_total: int
    production_gate_tasks_completed: int
    tasks_total: int
    tasks_completed: int
    completion_percent: int

    def __post_init__(self):
        """Validate progress values."""
        # Validate counts
        if self.development_tasks_completed > self.development_tasks_total:
            raise ValueError("Completed dev tasks cannot exceed total")
        if self.completion_gate_tasks_completed > self.completion_gate_tasks_total:
            raise ValueError("Completed completion gate tasks cannot exceed total")
        if self.production_gate_tasks_completed > self.production_gate_tasks_total:
            raise ValueError("Completed production gate tasks cannot exceed total")

        # Validate totals match
        expected_total = (
            self.development_tasks_total
            + self.completion_gate_tasks_total
            + self.production_gate_tasks_total
        )
        if self.tasks_total != expected_total:
            raise ValueError(f"Tasks total ({self.tasks_total}) must equal sum of task types ({expected_total})")

        expected_completed = (
            self.development_tasks_completed
            + self.completion_gate_tasks_completed
            + self.production_gate_tasks_completed
        )
        if self.tasks_completed != expected_completed:
            raise ValueError(f"Tasks completed ({self.tasks_completed}) must equal sum of completed task types ({expected_completed})")

        # Validate percentage
        if not 0 <= self.completion_percent <= 100:
            raise ValueError("Completion percent must be between 0 and 100")


@dataclass
class TaskSummary:
    """Summary of a task in the sprint."""

    id: str
    title: str
    status: Status
    task_type: TaskType
    gate_info: Optional[dict] = None


@dataclass
class DevelopmentGate:
    """External dependency for a sprint."""

    type: DependencyType
    target_id: str
    target_status: str
    reason: str


@dataclass
class SprintBlocker:
    """Current blocker for a sprint."""

    dependency_id: str
    dependency_type: str
    current_status: str
    required_status: str
    blocking_since: datetime
    estimated_resolution: Optional[datetime] = None


@dataclass
class SprintMetadata:
    """Sprint metadata."""

    last_updated: datetime
    estimated_duration: Optional[str] = None
    actual_duration: Optional[str] = None
    estimated_tokens: Optional[int] = None
    actual_tokens: Optional[int] = None
    agents_used: Optional[List[str]] = None


@dataclass
class Sprint:
    """
    Sprint object - a logical unit of work pushable to production.

    Key characteristics:
    - Production-deployable unit
    - Contains development tasks AND quality gate tasks
    - Has completion_gate_check and production_gate_check statuses
    - Can reach production_ready and deployed statuses
    """

    # Identity
    id: str
    name: str
    track_id: str
    roadmap_id: str

    # Status
    status: Status
    blocked: bool

    # Timing
    created: datetime
    progress: SprintProgress
    tasks: List[TaskSummary]
    development_gates: List[DevelopmentGate]  # Source of truth (static config)
    blocks: List[DevelopmentGate]  # What this sprint blocks (forward index)
    blocked_by: List[SprintBlocker]  # Computed blockers (DEPRECATED - use depends_on)

    # NEW: Cached dependency tracking for fast updates
    depends_on: List[DependencyStatus]  # Cached status of dependencies (for blocking check)
    depended_on_by: List[str]  # IDs of objects that depend on this (reverse index)

    metadata: SprintMetadata

    # Optional timing
    started: Optional[datetime] = None
    completion_gate_check_at: Optional[datetime] = None
    completed: Optional[datetime] = None
    production_gate_check_at: Optional[datetime] = None
    production_ready_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None

    # Documentation
    plan_file: Optional[str] = None
    deliverables: List[str] = field(default_factory=list)

    # Commit tracking - records commits that completed tasks in this sprint
    commits: List[TaskCompletionCommit] = field(default_factory=list)

    # Quality standards (apply to tasks in this sprint, inherits from roadmap/track)
    standards: List[Standard] = field(default_factory=list)

    def __post_init__(self):
        """Validate sprint data."""
        # Validate sprint ID is track-scoped
        if not self.id.startswith(f"{self.track_id}-"):
            raise ValueError(f"Sprint ID {self.id} must start with track ID {self.track_id}")

        # Validate dates
        if self.started and self.started < self.created:
            raise ValueError("Start date must be after or equal to creation date")

        # Validate blocked status matches depends_on
        has_unsatisfied_deps = any(not dep.is_satisfied() for dep in self.depends_on)
        if self.blocked != has_unsatisfied_deps:
            raise ValueError(f"Blocked flag ({self.blocked}) must match unsatisfied dependencies ({has_unsatisfied_deps})")

        # Validate status transitions
        if self.status == Status.IN_PROGRESS and not self.started:
            raise ValueError("In-progress sprints must have a start date")

        if self.status == Status.COMPLETED and not self.completed:
            raise ValueError("Completed sprints must have a completion date")

        if self.status == Status.PRODUCTION_READY and not self.production_ready_at:
            raise ValueError("Production-ready sprints must have production_ready_at date")

        # Validate task IDs are sprint-scoped
        for task in self.tasks:
            if not task.id.startswith(f"{self.id}-"):
                raise ValueError(f"Task ID {task.id} must start with sprint ID {self.id}")

        # Validate gate tasks have gate_info
        for task in self.tasks:
            if task.task_type in [TaskType.COMPLETION_GATE, TaskType.PRODUCTION_GATE]:
                if not task.gate_info:
                    raise ValueError(f"Gate task {task.id} must have gate_info")
            else:
                if task.gate_info:
                    raise ValueError(f"Development task {task.id} cannot have gate_info")

    def get_task_summary(self, task_id: str) -> Optional[TaskSummary]:
        """Get summary for a specific task."""
        return next((t for t in self.tasks if t.id == task_id), None)

    def is_blocked(self) -> bool:
        """Check if sprint is blocked using depends_on."""
        return any(not dep.is_satisfied() for dep in self.depends_on)

    def compute_blocked_status(self) -> bool:
        """Compute blocked status from depends_on array."""
        return any(not dep.is_satisfied() for dep in self.depends_on)

    def get_unsatisfied_dependencies(self) -> List[DependencyStatus]:
        """Get list of dependencies that are not satisfied."""
        return [dep for dep in self.depends_on if not dep.is_satisfied()]

    def get_completion_percentage(self) -> int:
        """Get completion percentage."""
        return self.progress.completion_percent

    def get_development_tasks(self) -> List[TaskSummary]:
        """Get development tasks only."""
        return [t for t in self.tasks if t.task_type == TaskType.DEVELOPMENT]

    def get_completion_gate_tasks(self) -> List[TaskSummary]:
        """Get completion gate tasks only."""
        return [t for t in self.tasks if t.task_type == TaskType.COMPLETION_GATE]

    def get_production_gate_tasks(self) -> List[TaskSummary]:
        """Get production gate tasks only."""
        return [t for t in self.tasks if t.task_type == TaskType.PRODUCTION_GATE]

    def all_development_tasks_completed(self) -> bool:
        """Check if all development tasks are completed."""
        # Use progress metrics instead of tasks list (which may be empty)
        if self.progress.development_tasks_total == 0:
            return True  # No dev tasks means they're all "done"
        return self.progress.development_tasks_completed == self.progress.development_tasks_total

    def all_completion_gates_passed(self) -> bool:
        """Check if all completion gate tasks are completed."""
        # Use progress metrics instead of tasks list (which may be empty)
        if self.progress.completion_gate_tasks_total == 0:
            return True  # No gates means they're all "passed"
        return self.progress.completion_gate_tasks_completed == self.progress.completion_gate_tasks_total

    def all_production_gates_passed(self) -> bool:
        """Check if all production gate tasks are completed."""
        # Use progress metrics instead of tasks list (which may be empty)
        if self.progress.production_gate_tasks_total == 0:
            return True  # No gates means they're all "passed"
        return self.progress.production_gate_tasks_completed == self.progress.production_gate_tasks_total

    def can_enter_completion_gate_check(self) -> bool:
        """Check if sprint can enter completion gate check status."""
        return self.all_development_tasks_completed()

    def can_complete(self) -> bool:
        """Check if sprint can be completed."""
        return self.all_development_tasks_completed() and self.all_completion_gates_passed()

    def can_enter_production_gate_check(self) -> bool:
        """Check if sprint can enter production gate check status."""
        return self.can_complete()

    def can_be_production_ready(self) -> bool:
        """Check if sprint can be production ready."""
        return self.can_complete() and self.all_production_gates_passed()

    def get_standard(self, standard_id: str) -> Optional[Standard]:
        """Get a specific standard by ID."""
        return next((s for s in self.standards if s.id == standard_id), None)

    def add_standard(self, standard: Standard):
        """Add a standard to the sprint."""
        # Check for duplicate IDs
        if any(s.id == standard.id for s in self.standards):
            raise ValueError(f"Standard with ID '{standard.id}' already exists")
        self.standards.append(standard)
        self.metadata.last_updated = datetime.now(timezone.utc)

    def remove_standard(self, standard_id: str) -> bool:
        """Remove a standard by ID. Returns True if removed, False if not found."""
        initial_count = len(self.standards)
        self.standards = [s for s in self.standards if s.id != standard_id]
        if len(self.standards) < initial_count:
            self.metadata.last_updated = datetime.now(timezone.utc)
            return True
        return False

    def get_active_standards(self) -> List[Standard]:
        """Get all enabled standards."""
        return [s for s in self.standards if s.is_active()]

    def get_blocking_standards(self) -> List[Standard]:
        """Get all blocking standards."""
        return [s for s in self.standards if s.is_blocking() and s.is_active()]
