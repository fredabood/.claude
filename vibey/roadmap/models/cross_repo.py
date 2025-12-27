"""
Cross-repo relationship data models.

This module defines models for managing relationships between parent and
submodule roadmaps, including push modes, external blockers, and linked
task pairs.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: All cross-repo data lives in the PARENT repo only.
Submodules have NO knowledge of being submodules.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .submodule import SubmoduleReference


class PushMode(str, Enum):
    """
    Push mode for creating tasks in submodules.

    Controls how tasks are distributed between parent and submodule repos.
    Per design decision in SUBMODULE_ISOLATION_AND_PUSHDOWN.md.
    """

    LINKED = "linked"
    """Create tasks in BOTH repos with link tracking.

    - Creates task in parent repo
    - Creates standalone copy in submodule repo
    - Records link in linked_task_pairs table
    - Progress syncs from submodule to parent
    """

    PARENT_ONLY = "parent_only"
    """Keep task in parent repo only.

    - Task exists only in parent
    - Submodule has no knowledge of this task
    - Use when work is done by parent team
    """

    SUBMODULE_ONLY = "submodule_only"
    """Push task to submodule only, remove from parent.

    - Task created in submodule as standalone task
    - No task remains in parent
    - Parent tracks via external_blockers if needed
    - Use when work is fully delegated
    """


class ExternalBlockerType(str, Enum):
    """Types of external blockers for cross-repo dependencies."""

    EXTERNAL_PROJECT = "external_project"  # Dependency on external project
    SUBMODULE_TASK = "submodule_task"  # Dependency on task in submodule
    EXTERNAL_API = "external_api"  # External API or service
    MANUAL_APPROVAL = "manual_approval"  # Human approval required


@dataclass
class ExternalBlockerInfo:
    """
    Extended blocker info for cross-repo dependencies.

    This extends the basic DependencyStatus with submodule-specific
    fields for tracking dependencies on tasks in submodule repos.

    Stored in the parent repo's external_blockers SQLite table.
    """

    # Identification
    blocker_id: str  # Human-readable ID (e.g., "libs/repo-a:auth-v2")
    blocker_type: ExternalBlockerType = ExternalBlockerType.SUBMODULE_TASK

    # Resolution (populated when linked to actual task)
    resolved_to: Optional[str] = None  # Submodule task ULID when linked
    required_status: str = "completed"  # Status needed to unblock

    # Submodule context
    submodule_path: Optional[str] = None  # Path to submodule directory

    # Synced status from submodule
    current_status: Optional[str] = None  # Synced from submodule task
    is_satisfied: bool = False

    # Sync tracking
    last_synced: Optional[datetime] = None

    # Description
    description: Optional[str] = None

    def check_satisfied(self) -> bool:
        """
        Check if this external blocker is satisfied.

        Uses status progression order to determine if current_status
        meets or exceeds required_status.
        """
        if self.current_status is None:
            return False

        status_order = [
            "not_started", "in_progress", "paused",
            "completion_gate_check", "completed",
            "production_gate_check", "production_ready", "deployed"
        ]

        try:
            current_idx = status_order.index(self.current_status)
            required_idx = status_order.index(self.required_status)
            self.is_satisfied = current_idx >= required_idx
            return self.is_satisfied
        except ValueError:
            # Status not in list - check exact match
            self.is_satisfied = self.current_status == self.required_status
            return self.is_satisfied

    def to_blocker_id_format(self) -> str:
        """
        Format as standard blocker_id string.

        Format: {submodule_path}:{task_ref}

        Examples:
            - "libs/repo-a:auth-v2"
            - "shared/utils:01KXYZ..."
        """
        if self.submodule_path and self.resolved_to:
            return f"{self.submodule_path}:{self.resolved_to}"
        return self.blocker_id


@dataclass
class SubmoduleConfig:
    """
    Configuration for submodule integration.

    Stored in parent repo's .vibey/config/submodules.yaml.
    """

    # Registered submodules
    submodules: list[SubmoduleReference] = field(default_factory=list)

    # Default push settings
    default_push_mode: PushMode = PushMode.LINKED

    # Aggregation settings
    aggregate_on_status: bool = True  # Auto-aggregate when running `vibey roadmap status`
    stale_threshold_minutes: int = 60  # Warn if not synced within threshold

    def get_submodule(self, path: str) -> Optional[SubmoduleReference]:
        """Get submodule reference by path."""
        path = path.replace("\\", "/").strip("/")
        for sub in self.submodules:
            if sub.path == path:
                return sub
        return None

    def add_submodule(self, submodule: SubmoduleReference) -> None:
        """Add a submodule reference, replacing if exists."""
        existing = self.get_submodule(submodule.path)
        if existing:
            self.submodules.remove(existing)
        self.submodules.append(submodule)

    def remove_submodule(self, path: str) -> bool:
        """Remove a submodule reference. Returns True if removed."""
        submodule = self.get_submodule(path)
        if submodule:
            self.submodules.remove(submodule)
            return True
        return False


@dataclass
class LinkedTaskPair:
    """
    Tracks the relationship between a parent task and its submodule counterpart.

    Created when a task is pushed with 'linked' mode.
    Stored in linked_task_pairs SQLite table.
    """

    # Parent side
    parent_task_id: str  # ULID in parent repo

    # Submodule side
    submodule_path: str  # Path to submodule
    submodule_task_id: str  # ULID in submodule repo

    # Push configuration
    push_mode: PushMode = PushMode.LINKED

    # Audit
    created: Optional[datetime] = None
    id: Optional[str] = None  # Link ULID (generated on save)

    def __post_init__(self):
        """Validate linked task pair."""
        if not self.parent_task_id:
            raise ValueError("parent_task_id is required")
        if not self.submodule_path:
            raise ValueError("submodule_path is required")
        if not self.submodule_task_id:
            raise ValueError("submodule_task_id is required")

        # Normalize path
        self.submodule_path = self.submodule_path.replace("\\", "/").strip("/")

        # Set created timestamp if not provided
        if self.created is None:
            self.created = datetime.now(timezone.utc)


@dataclass
class PushResult:
    """
    Result of pushing a task to a submodule.

    Returned by TaskPusher.push_task() operations.
    """

    success: bool
    push_mode: PushMode

    # Created entities
    parent_task_id: Optional[str] = None
    submodule_task_id: Optional[str] = None
    link_id: Optional[str] = None  # LinkedTaskPair ID if created

    # Error handling
    error: Optional[str] = None
    error_type: Optional[str] = None

    # Metadata
    submodule_path: Optional[str] = None
    pushed_at: Optional[datetime] = None

    def __post_init__(self):
        """Set pushed_at if not provided."""
        if self.success and self.pushed_at is None:
            self.pushed_at = datetime.now(timezone.utc)


@dataclass
class SyncResult:
    """
    Result of syncing status from a submodule.

    Returned by ProgressAggregator.sync_blocked_by_status() operations.
    """

    success: bool
    submodule_path: str

    # Sync details
    tasks_synced: int = 0
    blockers_updated: int = 0
    blockers_resolved: int = 0

    # Error handling
    error: Optional[str] = None

    # Timing
    synced_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    def __post_init__(self):
        """Set synced_at if not provided."""
        if self.success and self.synced_at is None:
            self.synced_at = datetime.now(timezone.utc)
