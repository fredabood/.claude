"""
Roadmap data model.

The Roadmap is the top-level object with unified state management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from .common import Status, Priority, VersionBumpTrigger, ActivityType, PlatformDeployment


@dataclass
class VersionStrategy:
    """Version bump strategy configuration."""

    major_on: VersionBumpTrigger
    minor_on: VersionBumpTrigger
    patch_on: VersionBumpTrigger


@dataclass
class Progress:
    """Aggregate progress tracking."""

    tracks_total: int
    tracks_completed: int
    sprints_total: int
    sprints_completed: int
    tasks_total: int
    tasks_completed: int
    completion_percent: int

    def __post_init__(self):
        """Validate progress values."""
        if self.tracks_completed > self.tracks_total:
            raise ValueError("Completed tracks cannot exceed total tracks")
        if self.sprints_completed > self.sprints_total:
            raise ValueError("Completed sprints cannot exceed total sprints")
        if self.tasks_completed > self.tasks_total:
            raise ValueError("Completed tasks cannot exceed total tasks")
        if not 0 <= self.completion_percent <= 100:
            raise ValueError("Completion percent must be between 0 and 100")


@dataclass
class TrackSummary:
    """Summary of a track in the roadmap."""

    id: str
    name: str
    status: Status
    priority: Priority


@dataclass
class Dependency:
    """External dependency (e.g., AWS account, external system)."""

    type: str  # "external"
    name: str
    status: str
    required_for: Optional[str] = None


@dataclass
class Blocker:
    """Current blocker preventing progress."""

    dependency_id: str
    dependency_type: str
    current_status: str
    required_status: str
    blocking_since: datetime
    estimated_resolution: Optional[datetime] = None


@dataclass
class VersionHistoryEntry:
    """Historical version entry."""

    version: str
    date: datetime
    milestone: str
    git_tag: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ActivityLogEntry:
    """Activity log entry."""

    timestamp: datetime
    type: ActivityType
    description: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class Metadata:
    """Roadmap metadata."""

    created_by: str
    framework_version: str
    schema_version: str
    last_updated: datetime
    purpose: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Roadmap:
    """
    Top-level roadmap object.

    The Roadmap contains unified activity log, version management,
    aggregate progress tracking, and track definitions.
    """

    # Identity
    id: str
    name: str

    # Version Management
    version: str
    version_strategy: VersionStrategy

    # Status
    status: Status
    blocked: bool

    # Timing
    created: datetime
    progress: Progress
    tracks: List[TrackSummary]
    activity_log: List[ActivityLogEntry]
    metadata: Metadata

    # Optional timing
    started: Optional[datetime] = None
    target_completion: Optional[datetime] = None
    completed: Optional[datetime] = None
    deployed: Optional[datetime] = None

    # Dependencies and blockers
    dependencies: List[Dependency] = field(default_factory=list)
    blocked_by: List[Blocker] = field(default_factory=list)

    # Version history
    version_history: List[VersionHistoryEntry] = field(default_factory=list)

    # Platform deployments
    deployed_platforms: List[PlatformDeployment] = field(default_factory=list)

    def __post_init__(self):
        """Validate roadmap data."""
        # Validate dates
        if self.started and self.started < self.created:
            raise ValueError("Start date must be after or equal to creation date")

        if self.completed and self.started and self.completed < self.started:
            raise ValueError("Completion date must be after or equal to start date")

        # Validate blocked status matches blocker list
        has_blockers = len(self.blocked_by) > 0
        if self.blocked != has_blockers:
            raise ValueError(f"Blocked flag ({self.blocked}) must match blocker list (has_blockers={has_blockers})")

        # Validate status transitions
        if self.status == Status.IN_PROGRESS and not self.started:
            raise ValueError("In-progress roadmaps must have a start date")

        if self.status == Status.COMPLETED and not self.completed:
            raise ValueError("Completed roadmaps must have a completion date")

    def get_track_summary(self, track_id: str) -> Optional[TrackSummary]:
        """Get summary for a specific track."""
        return next((t for t in self.tracks if t.id == track_id), None)

    def add_activity(self, activity_type: ActivityType, description: str, context: Optional[Dict[str, Any]] = None):
        """Add an activity log entry."""
        entry = ActivityLogEntry(
            timestamp=datetime.now(timezone.utc),
            type=activity_type,
            description=description,
            context=context,
        )
        self.activity_log.append(entry)
        self.metadata.last_updated = datetime.now(timezone.utc)

    def is_blocked(self) -> bool:
        """Check if roadmap is blocked."""
        return len(self.blocked_by) > 0

    def is_platform_deployed(self, platform: str) -> bool:
        """Check if a platform is deployed for this roadmap."""
        return any(p.platform == platform for p in self.deployed_platforms)

    def get_platform_deployment(self, platform: str) -> Optional[PlatformDeployment]:
        """Get deployment info for a specific platform."""
        return next((p for p in self.deployed_platforms if p.platform == platform), None)

    def get_deployed_platform_names(self) -> List[str]:
        """Get list of all deployed platform names."""
        return [p.platform for p in self.deployed_platforms]

    def get_primary_platform(self) -> Optional[PlatformDeployment]:
        """Get the primary platform deployment."""
        return next((p for p in self.deployed_platforms if p.primary), None)

    def get_completion_percentage(self) -> int:
        """Get completion percentage."""
        return self.progress.completion_percent

    def get_active_tracks(self) -> List[TrackSummary]:
        """Get tracks that are in progress."""
        return [t for t in self.tracks if t.status == Status.IN_PROGRESS]

    def get_completed_tracks(self) -> List[TrackSummary]:
        """Get tracks that are completed."""
        return [t for t in self.tracks if t.status == Status.COMPLETED]

    def get_recent_activity(self, limit: int = 10) -> List[ActivityLogEntry]:
        """Get recent activity log entries."""
        return sorted(self.activity_log, key=lambda x: x.timestamp, reverse=True)[:limit]
