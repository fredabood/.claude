"""
Track data model.

A Track is a parallelization boundary containing related sprints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .common import Status, Priority, DependencyType, GateStatus


@dataclass
class TrackProgress:
    """Track progress tracking."""

    sprints_total: int
    sprints_completed: int
    tasks_total: int
    tasks_completed: int
    completion_percent: int

    def __post_init__(self):
        """Validate progress values."""
        if self.sprints_completed > self.sprints_total:
            raise ValueError("Completed sprints cannot exceed total sprints")
        if self.tasks_completed > self.tasks_total:
            raise ValueError("Completed tasks cannot exceed total tasks")
        if not 0 <= self.completion_percent <= 100:
            raise ValueError("Completion percent must be between 0 and 100")


@dataclass
class SprintSummary:
    """Summary of a sprint in the track."""

    id: str
    name: str
    status: Status
    estimated_duration: Optional[str] = None
    tasks_count: Optional[int] = None
    started: Optional[datetime] = None


@dataclass
class TrackDependency:
    """Dependency for a track."""

    type: DependencyType
    target_id: str
    target_status: str
    reason: str
    optional: bool = False


@dataclass
class TrackBlocker:
    """Current blocker for a track."""

    dependency_id: str
    dependency_type: str
    current_status: str
    required_status: str
    blocking_since: datetime
    estimated_resolution: Optional[datetime] = None


@dataclass
class QualityGate:
    """Track-level quality gate."""

    name: str
    threshold: int
    blocking: bool
    status: GateStatus
    description: Optional[str] = None
    score: Optional[int] = None

    def __post_init__(self):
        """Validate quality gate."""
        if not 0 <= self.threshold <= 100:
            raise ValueError("Threshold must be between 0 and 100")
        if self.score is not None and not 0 <= self.score <= 100:
            raise ValueError("Score must be between 0 and 100")


@dataclass
class TrackMetadata:
    """Track metadata."""

    created_by: str
    last_updated: datetime
    design_doc: Optional[str] = None
    implementation_plan: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Track:
    """
    Track object - a parallelization boundary.

    Tracks with no dependencies can run in parallel.
    Each track contains related sprints with track-scoped IDs.
    """

    # Identity
    id: str
    name: str
    roadmap_id: str

    # Status
    status: Status
    blocked: bool
    priority: Priority

    # Timing
    created: datetime
    progress: TrackProgress
    sprints: List[SprintSummary]
    dependencies: List[TrackDependency]
    blocks: List[TrackDependency]  # What this track blocks
    blocked_by: List[TrackBlocker]
    quality_gates: List[QualityGate]
    assigned_agents: List[str]
    metadata: TrackMetadata

    # Optional timing
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    estimated_duration: Optional[str] = None

    # Deliverables and strategic value
    deliverables: List[str] = field(default_factory=list)
    strategic_value: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate track data."""
        # Validate dates
        if self.started and self.started < self.created:
            raise ValueError("Start date must be after or equal to creation date")

        if self.completed and self.started and self.completed < self.started:
            raise ValueError("Completion date must be after or equal to start date")

        # Validate blocked status
        has_blockers = len(self.blocked_by) > 0
        if self.blocked != has_blockers:
            raise ValueError(f"Blocked flag ({self.blocked}) must match blocker list (has_blockers={has_blockers})")

        # Validate status transitions
        if self.status == Status.IN_PROGRESS and not self.started:
            raise ValueError("In-progress tracks must have a start date")

        if self.status == Status.COMPLETED and not self.completed:
            raise ValueError("Completed tracks must have a completion date")

        # Validate sprint IDs are track-scoped
        for sprint in self.sprints:
            if not sprint.id.startswith(f"{self.id}-"):
                raise ValueError(f"Sprint ID {sprint.id} must start with track ID {self.id}")

        # Validate progress
        if len(self.sprints) != self.progress.sprints_total:
            raise ValueError(f"Sprint count ({len(self.sprints)}) must match sprints_total ({self.progress.sprints_total})")

    def get_sprint_summary(self, sprint_id: str) -> Optional[SprintSummary]:
        """Get summary for a specific sprint."""
        return next((s for s in self.sprints if s.id == sprint_id), None)

    def is_blocked(self) -> bool:
        """Check if track is blocked."""
        return len(self.blocked_by) > 0

    def get_completion_percentage(self) -> int:
        """Get completion percentage."""
        return self.progress.completion_percent

    def get_active_sprints(self) -> List[SprintSummary]:
        """Get sprints that are in progress."""
        return [s for s in self.sprints if s.status == Status.IN_PROGRESS]

    def get_pending_sprints(self) -> List[SprintSummary]:
        """Get sprints that haven't started."""
        return [s for s in self.sprints if s.status == Status.NOT_STARTED]

    def get_completed_sprints(self) -> List[SprintSummary]:
        """Get sprints that are completed."""
        return [s for s in self.sprints if s.status == Status.COMPLETED]

    def get_blocking_quality_gates(self) -> List[QualityGate]:
        """Get quality gates that are blocking and not passed."""
        return [
            gate
            for gate in self.quality_gates
            if gate.blocking and gate.status != GateStatus.PASSED
        ]

    def all_quality_gates_passed(self) -> bool:
        """Check if all blocking quality gates have passed."""
        return len(self.get_blocking_quality_gates()) == 0
