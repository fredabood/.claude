"""
Task data model.

A Task is a context-window sized work unit - the smallest unit of work.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .common import TaskStatus, Priority, TaskType, Complexity, SizeCategory, DeliverableType, DependencyType, DependencyStatus


@dataclass
class GateInfo:
    """Information for quality gate tasks."""

    blocks_status: str  # "completed" or "production_ready"
    threshold: int  # 0-100
    is_blocking: bool
    score: Optional[int] = None  # 0-100

    def __post_init__(self):
        """Validate gate info."""
        if self.blocks_status not in ["completed", "production_ready"]:
            raise ValueError("blocks_status must be 'completed' or 'production_ready'")
        if not 0 <= self.threshold <= 100:
            raise ValueError("Threshold must be between 0 and 100")
        if self.score is not None and not 0 <= self.score <= 100:
            raise ValueError("Score must be between 0 and 100")

    def has_passed(self) -> bool:
        """Check if gate has passed."""
        return self.score is not None and self.score >= self.threshold


@dataclass
class AuditResults:
    """Results from quality gate execution."""

    issues_found: int
    issues_fixed: int
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate audit results."""
        if self.issues_found < 0:
            raise ValueError("Issues found cannot be negative")
        if self.issues_fixed < 0:
            raise ValueError("Issues fixed cannot be negative")
        if self.issues_fixed > self.issues_found:
            raise ValueError("Issues fixed cannot exceed issues found")


@dataclass
class TaskDependency:
    """Dependency for a task."""

    type: DependencyType
    target_id: str
    target_status: str
    reason: str


@dataclass
class TaskBlocker:
    """Current blocker for a task."""

    dependency_id: str
    dependency_type: str
    current_status: str
    required_status: str
    blocking_since: datetime
    estimated_resolution: Optional[datetime] = None


@dataclass
class Deliverable:
    """Task deliverable."""

    type: DeliverableType
    paths: List[str]


@dataclass
class GitCommit:
    """Git commit associated with task.

    Platform tracking is REQUIRED for all new commits to support multi-platform development.
    Timestamps use Unix time (seconds since epoch) to avoid timezone issues.
    """

    sha: str
    message: str
    date: datetime  # Git commit date (from git log)
    author: str

    # Platform tracking (REQUIRED)
    platform: str  # e.g., "claude-code", "goose", "cursor"
    submitted_at: int  # Unix timestamp (seconds since epoch) when commit was submitted via platform

    def __post_init__(self):
        """Validate commit."""
        if not (7 <= len(self.sha) <= 40):
            raise ValueError("SHA must be 7-40 characters")
        # Basic hex validation
        try:
            int(self.sha, 16)
        except ValueError:
            raise ValueError(f"SHA must be hexadecimal: {self.sha}")

        # Validate platform
        if not self.platform or not self.platform.strip():
            raise ValueError("Platform is required and cannot be empty")

        # Validate submitted_at is a valid Unix timestamp
        if not isinstance(self.submitted_at, int):
            raise ValueError("submitted_at must be a Unix timestamp (integer)")
        if self.submitted_at < 0:
            raise ValueError("submitted_at must be a positive Unix timestamp")


@dataclass
class TaskCompletionCommit:
    """Commit that completed a task (used in sprint tracking)."""

    task_id: str  # Which task was completed
    sha: str
    message: str
    date: datetime
    author: str

    def __post_init__(self):
        """Validate commit."""
        if not (7 <= len(self.sha) <= 40):
            raise ValueError("SHA must be 7-40 characters")
        # Basic hex validation
        try:
            int(self.sha, 16)
        except ValueError:
            raise ValueError(f"SHA must be hexadecimal: {self.sha}")


@dataclass
class SprintCompletionCommit:
    """Commit that completed a sprint (used in track tracking)."""

    sprint_id: str  # Which sprint was completed
    sha: str
    message: str
    date: datetime
    author: str

    def __post_init__(self):
        """Validate commit."""
        if not (7 <= len(self.sha) <= 40):
            raise ValueError("SHA must be 7-40 characters")
        # Basic hex validation
        try:
            int(self.sha, 16)
        except ValueError:
            raise ValueError(f"SHA must be hexadecimal: {self.sha}")


@dataclass
class TaskMetadata:
    """Task metadata."""

    last_updated: Optional[datetime] = None
    token_efficiency: Optional[float] = None
    duration_hours: Optional[float] = None

    def __post_init__(self):
        """Validate metadata."""
        if self.token_efficiency is not None and self.token_efficiency < 0:
            raise ValueError("Token efficiency cannot be negative")
        if self.duration_hours is not None and self.duration_hours < 0:
            raise ValueError("Duration hours cannot be negative")


@dataclass
class Task:
    """
    Task object - a context-window sized work unit.

    Key characteristics:
    - Sized to fit within model's context window
    - No production concerns (no production_ready or deployed statuses)
    - Can be a development task OR a quality gate task
    """

    # Identity
    id: str
    sprint_id: str
    track_id: str
    roadmap_id: str

    # Task Type
    task_type: TaskType

    # Description
    title: str
    description: str

    # Status (restricted set - no production statuses)
    status: TaskStatus
    blocked: bool

    # Timing
    created: datetime

    # Assignment
    assigned_agent: str
    priority: Priority

    # Complexity & Size
    estimated_tokens: int
    complexity: Complexity

    # Dependencies and blockers
    dependencies: List[TaskDependency]      # Source of truth (static config)
    blocks: List[TaskDependency]            # What this task blocks (forward index)
    blocked_by: List[TaskBlocker]           # Computed blockers (DEPRECATED - use depends_on)

    # NEW: Cached dependency tracking for fast updates
    depends_on: List[DependencyStatus]      # Cached status of dependencies (for blocking check)
    depended_on_by: List[str]               # IDs of objects that depend on this (reverse index)

    metadata: TaskMetadata

    # Optional fields
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    phase_label: Optional[str] = None
    actual_tokens: Optional[int] = None
    size_category: Optional[SizeCategory] = None  # Auto-computed from estimated_tokens if not set

    # Gate-specific (only for quality gate tasks)
    gate_info: Optional[GateInfo] = None
    audit_results: Optional[AuditResults] = None

    # Deliverables and commits
    deliverables: List[Deliverable] = field(default_factory=list)
    commits: List[GitCommit] = field(default_factory=list)

    def __post_init__(self):
        """Validate task data."""
        # Check if task ID is a ULID (26 chars, alphanumeric, uppercase)
        is_ulid = len(self.id) == 26 and self.id.isalnum() and self.id.isupper()

        # Validate task ID is sprint-scoped (skip for ULID task IDs)
        if not is_ulid and not self.id.startswith(f"{self.sprint_id}-"):
            raise ValueError(f"Task ID {self.id} must start with sprint ID {self.sprint_id}")

        # Validate task type and gate_info consistency
        if self.task_type == TaskType.DEVELOPMENT:
            if self.gate_info is not None:
                raise ValueError("Development tasks cannot have gate_info")
        else:  # completion_gate or production_gate
            if self.gate_info is None:
                raise ValueError("Quality gate tasks must have gate_info")

            # Validate gate type matches blocks_status
            if self.task_type == TaskType.COMPLETION_GATE:
                if self.gate_info.blocks_status != "completed":
                    raise ValueError("Completion gates must block 'completed' status")
            elif self.task_type == TaskType.PRODUCTION_GATE:
                if self.gate_info.blocks_status != "production_ready":
                    raise ValueError("Production gates must block 'production_ready' status")

        # Validate dates (use safe comparison for mixed timezone-aware/naive datetimes)
        from vibey.roadmap.models.common import safe_datetime_compare
        if safe_datetime_compare(self.started, self.created) == -1:
            raise ValueError("Start date must be after or equal to creation date")

        if safe_datetime_compare(self.completed, self.started) == -1:
            raise ValueError("Completion date must be after or equal to start date")

        # Validate blocked status matches depends_on (primary) or blocked_by (deprecated)
        # blocked should be True if ANY dependency in depends_on is not satisfied
        has_unsatisfied_deps = any(not dep.is_satisfied() for dep in self.depends_on)
        if self.blocked != has_unsatisfied_deps:
            raise ValueError(f"Blocked flag ({self.blocked}) must match unsatisfied dependencies ({has_unsatisfied_deps})")

        # Validate status transitions
        if self.status == TaskStatus.IN_PROGRESS and not self.started:
            raise ValueError("In-progress tasks must have a start date")

        if self.status == TaskStatus.COMPLETED and not self.completed:
            raise ValueError("Completed tasks must have a completion date")

        # Validate tokens
        if self.estimated_tokens <= 0:
            raise ValueError("Estimated tokens must be positive")

        if self.actual_tokens is not None and self.actual_tokens < 0:
            raise ValueError("Actual tokens cannot be negative")

        # Calculate token efficiency if both values present
        if self.actual_tokens is not None and self.metadata.token_efficiency is None:
            self.metadata.token_efficiency = self.actual_tokens / self.estimated_tokens

        # Auto-compute size_category from estimated_tokens if not set
        if self.size_category is None:
            self.size_category = SizeCategory.from_tokens(self.estimated_tokens)

    def is_blocked(self) -> bool:
        """
        Check if task is blocked.

        Uses depends_on to check if any dependencies are unsatisfied.
        """
        return any(not dep.is_satisfied() for dep in self.depends_on)

    def compute_blocked_status(self) -> bool:
        """
        Compute blocked status from depends_on array.

        Returns True if ANY dependency is not satisfied.
        """
        return any(not dep.is_satisfied() for dep in self.depends_on)

    def get_unsatisfied_dependencies(self) -> List[DependencyStatus]:
        """Get list of dependencies that are not satisfied."""
        return [dep for dep in self.depends_on if not dep.is_satisfied()]

    def get_satisfied_dependencies(self) -> List[DependencyStatus]:
        """Get list of dependencies that are satisfied."""
        return [dep for dep in self.depends_on if dep.is_satisfied()]

    def can_transition_to(self, target_status: str) -> bool:
        """
        Check if task can transition to a specific status.

        Args:
            target_status: Target status (e.g., "in_progress", "completed")

        Returns:
            True if no dependencies block this transition

        Examples:
            if task.can_transition_to("in_progress"):
                task.status = TaskStatus.IN_PROGRESS

            if task.can_transition_to("completed"):
                task.status = TaskStatus.COMPLETED
        """
        return not any(dep.blocks_transition(target_status) for dep in self.depends_on)

    def get_blocking_dependencies_for(self, target_status: str) -> List[DependencyStatus]:
        """
        Get dependencies that block a specific transition.

        Args:
            target_status: Target status to check

        Returns:
            List of dependencies blocking that transition
        """
        return [dep for dep in self.depends_on if dep.blocks_transition(target_status)]

    def is_development_task(self) -> bool:
        """Check if this is a development task."""
        return self.task_type == TaskType.DEVELOPMENT

    def is_quality_gate(self) -> bool:
        """Check if this is a quality gate task."""
        return self.task_type in [TaskType.COMPLETION_GATE, TaskType.PRODUCTION_GATE]

    def is_completion_gate(self) -> bool:
        """Check if this is a completion gate."""
        return self.task_type == TaskType.COMPLETION_GATE

    def is_production_gate(self) -> bool:
        """Check if this is a production gate."""
        return self.task_type == TaskType.PRODUCTION_GATE

    def has_passed_gate(self) -> bool:
        """Check if quality gate has passed (only for gate tasks)."""
        if not self.is_quality_gate() or not self.gate_info:
            return False
        return self.gate_info.has_passed()

    def get_token_efficiency(self) -> Optional[float]:
        """Get token efficiency ratio."""
        if self.actual_tokens is None:
            return None
        return self.actual_tokens / self.estimated_tokens

    def add_commit(
        self,
        sha: str,
        message: str,
        author: str,
        platform: str,
        date: Optional[datetime] = None,
        submitted_at: Optional[int] = None,
    ):
        """Add a git commit to this task.

        Args:
            sha: Git commit SHA (7-40 characters)
            message: Commit message
            author: Commit author
            platform: Platform used to submit commit (REQUIRED: e.g., "claude-code", "goose")
            date: Git commit date (from git log), defaults to now
            submitted_at: Unix timestamp when commit was submitted via platform, defaults to now
        """
        if date is None:
            date = datetime.now(timezone.utc)
        if submitted_at is None:
            # Use current time as Unix timestamp
            submitted_at = int(datetime.now(timezone.utc).timestamp())

        commit = GitCommit(
            sha=sha,
            message=message,
            date=date,
            author=author,
            platform=platform,
            submitted_at=submitted_at,
        )
        self.commits.append(commit)
        self.metadata.last_updated = datetime.now(timezone.utc)

    def add_deliverable(self, deliverable_type: DeliverableType, paths: List[str]):
        """Add a deliverable to this task."""
        deliverable = Deliverable(type=deliverable_type, paths=paths)
        self.deliverables.append(deliverable)
        self.metadata.last_updated = datetime.now(timezone.utc)
