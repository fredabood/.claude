"""
Submodule integration data models.

This module defines models for tracking git submodules that have vibey roadmaps,
aggregating their progress, and managing submodule blockers.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: Submodules have NO knowledge of parent repos. All cross-repo
coordination data lives in the PARENT repo only.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DetectionSource(str, Enum):
    """How a submodule was detected."""

    GITMODULES = "gitmodules"  # Parsed from .gitmodules file
    GIT_COMMAND = "git_command"  # From `git submodule status`
    DIRECTORY_SCAN = "directory_scan"  # Found .vibey/ directory in subdir
    MANUAL = "manual"  # Manually added via CLI


class SyncStatus(str, Enum):
    """Sync status between parent and submodule."""

    SYNCED = "synced"  # Recently synced, data is fresh
    STALE = "stale"  # Data is older than threshold
    NEVER_SYNCED = "never_synced"  # No sync has been performed
    ERROR = "error"  # Sync failed due to error


class BlockerSeverity(str, Enum):
    """Severity of a submodule blocker."""

    CRITICAL = "critical"  # Blocks all progress
    HIGH = "high"  # Blocks major work streams
    MEDIUM = "medium"  # Affects some work
    LOW = "low"  # Minor impact


class CollectionMethod(str, Enum):
    """How progress is collected from submodules."""

    POLLING = "polling"  # Regular interval polling
    ON_DEMAND = "on_demand"  # Only when explicitly requested
    GIT_HOOK = "git_hook"  # Triggered by git operations


@dataclass
class SubmoduleReference:
    """
    Reference to a git submodule with a vibey roadmap.

    This represents a link from the parent repo to a submodule's roadmap.
    Stored in the parent repo's .vibey/config/submodules.yaml.
    """

    path: str  # Relative path to submodule (e.g., 'libs/repo-a')
    roadmap_id: Optional[str] = None  # Submodule's roadmap identifier (from its roadmap.yaml)
    aggregate: bool = True  # Include in parent's progress rollup
    track_filter: list[str] = field(default_factory=list)  # Empty = all tracks
    detection_source: DetectionSource = DetectionSource.GITMODULES
    last_synced: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.NEVER_SYNCED

    def __post_init__(self):
        """Validate submodule reference."""
        if not self.path or not self.path.strip():
            raise ValueError("Submodule path is required")
        # Normalize path separators
        self.path = self.path.replace("\\", "/").strip("/")


@dataclass
class SubmoduleProgress:
    """
    Progress summary from a single submodule.

    Collected from the submodule's roadmap and cached in parent.
    """

    submodule_path: str  # Path to submodule
    roadmap_id: str  # Submodule's roadmap ID

    # Track counts
    tracks_total: int = 0
    tracks_completed: int = 0
    tracks_in_progress: int = 0

    # Sprint counts
    sprints_total: int = 0
    sprints_completed: int = 0
    sprints_in_progress: int = 0

    # Task counts
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0

    # Computed
    completion_percent: float = 0.0

    # Sync metadata
    collected_at: Optional[datetime] = None
    collection_method: CollectionMethod = CollectionMethod.ON_DEMAND

    def calculate_completion(self) -> float:
        """Calculate overall completion percentage."""
        if self.tasks_total == 0:
            return 0.0
        self.completion_percent = (self.tasks_completed / self.tasks_total) * 100.0
        return self.completion_percent


@dataclass
class SubmoduleBlocker:
    """
    A blocker originating from a submodule that affects the parent.

    These are issues in submodules that block parent roadmap progress.
    """

    submodule_path: str  # Path to submodule
    blocker_id: str  # ID in submodule (e.g., task ULID)
    title: str  # Human-readable title
    severity: BlockerSeverity = BlockerSeverity.MEDIUM
    description: Optional[str] = None

    # What it affects in parent
    blocks_tasks: list[str] = field(default_factory=list)  # Parent task ULIDs
    blocks_sprints: list[str] = field(default_factory=list)  # Parent sprint ULIDs

    # Status
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None


@dataclass
class AggregatedProgress:
    """
    Rolled-up progress from all submodules.

    Combines SubmoduleProgress from all registered submodules into
    a single summary for the parent roadmap.
    """

    # Per-submodule breakdown
    submodule_progress: list[SubmoduleProgress] = field(default_factory=list)

    # Aggregated totals
    total_tracks: int = 0
    completed_tracks: int = 0
    total_sprints: int = 0
    completed_sprints: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0

    # Overall
    overall_completion_percent: float = 0.0

    # Blockers
    active_blockers: list[SubmoduleBlocker] = field(default_factory=list)
    critical_blocker_count: int = 0

    # Sync metadata
    last_aggregated: Optional[datetime] = None
    submodules_synced: int = 0
    submodules_stale: int = 0
    submodules_error: int = 0

    def aggregate(self) -> None:
        """Recalculate aggregated totals from submodule progress."""
        self.total_tracks = sum(p.tracks_total for p in self.submodule_progress)
        self.completed_tracks = sum(p.tracks_completed for p in self.submodule_progress)
        self.total_sprints = sum(p.sprints_total for p in self.submodule_progress)
        self.completed_sprints = sum(p.sprints_completed for p in self.submodule_progress)
        self.total_tasks = sum(p.tasks_total for p in self.submodule_progress)
        self.completed_tasks = sum(p.tasks_completed for p in self.submodule_progress)

        if self.total_tasks > 0:
            self.overall_completion_percent = (self.completed_tasks / self.total_tasks) * 100.0
        else:
            self.overall_completion_percent = 0.0

        self.critical_blocker_count = sum(
            1 for b in self.active_blockers if b.severity == BlockerSeverity.CRITICAL
        )
        self.last_aggregated = datetime.now(timezone.utc)
