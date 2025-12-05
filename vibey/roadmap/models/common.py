"""
Common types and enums used across all roadmap models.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def safe_datetime_compare(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[int]:
    """
    Safely compare two datetimes, handling mixed timezone-aware and naive datetimes.

    Args:
        dt1: First datetime (can be None, naive, or aware)
        dt2: Second datetime (can be None, naive, or aware)

    Returns:
        -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2, None if either is None
    """
    if dt1 is None or dt2 is None:
        return None

    # Normalize both to timezone-aware (assume UTC for naive datetimes)
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)

    if dt1 < dt2:
        return -1
    elif dt1 > dt2:
        return 1
    return 0


class Status(str, Enum):
    """Status enum for roadmap objects."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETION_GATE_CHECK = "completion_gate_check"
    COMPLETED = "completed"
    PRODUCTION_GATE_CHECK = "production_gate_check"
    PRODUCTION_READY = "production_ready"
    DEPLOYED = "deployed"
    SUPERSEDED = "superseded"  # Track/sprint has been superseded/merged into another
    WONT_DO = "wont_do"


class TaskStatus(str, Enum):
    """Status enum for tasks (restricted set - no production statuses)."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETION_GATE_CHECK = "completion_gate_check"
    COMPLETED = "completed"
    WONT_DO = "wont_do"


class Priority(str, Enum):
    """Priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    """Task type classification."""

    DEVELOPMENT = "development"
    COMPLETION_GATE = "completion_gate"
    PRODUCTION_GATE = "production_gate"


class GateStatus(str, Enum):
    """Quality gate execution status."""

    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SUPERSEDED = "superseded"  # Gate requirements have been superseded by other gates


class DependencyType(str, Enum):
    """Types of dependencies."""

    TASK = "task"
    SPRINT = "sprint"
    TRACK = "track"
    EXTERNAL = "external"


class Complexity(str, Enum):
    """Task complexity rating."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class SizeCategory(str, Enum):
    """Token-based size categories for effort estimation.

    Size categories provide a standardized way to estimate and track
    token consumption for AI-assisted development tasks.

    Token ranges (based on Claude Code context usage):
    - SMALL: <10K tokens - Quick fixes, simple changes
    - MEDIUM: 10K-30K tokens - Feature additions, moderate refactors
    - LARGE: 30K-75K tokens - Complex features, significant changes
    - X_LARGE: 75K-150K tokens - Major features, architectural changes
    - XX_LARGE: 150K+ tokens - Should be split into multiple tasks
    """

    SMALL = "S"       # <10K tokens
    MEDIUM = "M"      # 10K-30K tokens
    LARGE = "L"       # 30K-75K tokens
    X_LARGE = "XL"    # 75K-150K tokens
    XX_LARGE = "XXL"  # 150K+ tokens (recommend splitting)

    @classmethod
    def from_tokens(cls, tokens: int) -> "SizeCategory":
        """Determine size category from token count."""
        if tokens < 10_000:
            return cls.SMALL
        elif tokens < 30_000:
            return cls.MEDIUM
        elif tokens < 75_000:
            return cls.LARGE
        elif tokens < 150_000:
            return cls.X_LARGE
        else:
            return cls.XX_LARGE

    def get_token_range(self) -> tuple[int, int]:
        """Get the token range for this category (min, max)."""
        ranges = {
            self.SMALL: (0, 10_000),
            self.MEDIUM: (10_000, 30_000),
            self.LARGE: (30_000, 75_000),
            self.X_LARGE: (75_000, 150_000),
            self.XX_LARGE: (150_000, 500_000),
        }
        return ranges[self]

    def get_midpoint(self) -> int:
        """Get the midpoint token estimate for this category."""
        min_tokens, max_tokens = self.get_token_range()
        return (min_tokens + max_tokens) // 2


class DeliverableType(str, Enum):
    """Types of task deliverables."""

    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    OTHER = "other"


class ActivityType(str, Enum):
    """Types of activity log entries."""

    ROADMAP_STARTED = "roadmap_started"
    ROADMAP_COMPLETED = "roadmap_completed"
    ROADMAP_DEPLOYED = "roadmap_deployed"
    ROADMAP_INITIALIZED = "roadmap_initialized"
    TRACK_ADDED = "track_added"
    TRACK_STARTED = "track_started"
    TRACK_COMPLETED = "track_completed"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    SPRINT_PRODUCTION_READY = "sprint_production_ready"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    QUALITY_GATE = "quality_gate"
    VERSION_BUMP = "version_bump"
    BLOCKER_ADDED = "blocker_added"
    BLOCKER_RESOLVED = "blocker_resolved"
    DESIGN_COMPLETED = "design_completed"
    PLANNING_COMPLETED = "planning_completed"


class VersionBumpTrigger(str, Enum):
    """Version bump triggers."""

    ROADMAP_MILESTONE = "roadmap_milestone"
    TRACK_COMPLETION = "track_completion"
    SPRINT_PRODUCTION_READY = "sprint_production_ready"
    MANUAL = "manual"


@dataclass
class DependencyStatus:
    """
    Cached dependency status for fast blocking computation.

    This is a denormalized cache of a dependency's current state,
    allowing O(1) blocking checks without loading dependency files.

    Used by Task, Sprint, and Track models.
    """

    blocker_id: str          # The dependency's ID (e.g., "backend-1-task-005")
    blocker_type: str        # Type: task/sprint/track/external
    required_status: str     # Status needed to unblock (e.g., "completed")
    current_status: str      # Cached current status of blocker
    blocks_transition_to: str  # What status transition this blocks (e.g., "in_progress", "completed")
    last_checked: datetime   # When status was last synced

    def is_satisfied(self) -> bool:
        """
        Check if this dependency is satisfied.

        Uses status progression order:
        not_started < in_progress < paused < completion_gate_check <
        completed < production_gate_check < production_ready < deployed
        """
        status_order = [
            "not_started", "in_progress", "paused",
            "completion_gate_check", "completed",
            "production_gate_check", "production_ready", "deployed"
        ]

        try:
            current_idx = status_order.index(self.current_status)
            required_idx = status_order.index(self.required_status)
            return current_idx >= required_idx
        except ValueError:
            # Status not in list - check exact match
            return self.current_status == self.required_status

    def blocks_transition(self, target_status: str) -> bool:
        """
        Check if this dependency blocks a specific status transition.

        Args:
            target_status: The status trying to transition to

        Returns:
            True if this dependency blocks that transition

        Examples:
            # Can start work if blocker allows in_progress
            if not dep.blocks_transition("in_progress"):
                task.status = "in_progress"

            # Can complete if blocker allows completed
            if not dep.blocks_transition("completed"):
                task.status = "completed"
        """
        status_order = [
            "not_started", "in_progress", "paused",
            "completion_gate_check", "completed",
            "production_gate_check", "production_ready", "deployed"
        ]

        try:
            target_idx = status_order.index(target_status)
            blocks_idx = status_order.index(self.blocks_transition_to)

            # This dependency blocks if target >= blocks_transition_to
            # AND dependency is not satisfied
            if target_idx >= blocks_idx and not self.is_satisfied():
                return True
            return False
        except ValueError:
            # If not in order, check exact match
            return target_status == self.blocks_transition_to and not self.is_satisfied()


@dataclass
class PlatformDeployment:
    """
    Record of a platform deployment for a roadmap.

    Tracks which AI platforms (claude-code, goose, cursor, etc.) Vibey has been
    deployed for in this project, along with their context windows and deployment metadata.
    """

    platform: str  # Platform name (e.g., "claude-code", "goose", "cursor")
    context_window: int  # Token context window for this platform
    deployed_at: int  # Unix timestamp when platform was deployed
    deployed_by: str  # Who deployed it (email or username)
    primary: bool = False  # Is this the primary platform for the project?

    def __post_init__(self):
        """Validate platform deployment."""
        if not self.platform or not self.platform.strip():
            raise ValueError("Platform name is required and cannot be empty")

        if self.context_window <= 0:
            raise ValueError("Context window must be positive")

        if not isinstance(self.deployed_at, int):
            raise ValueError("deployed_at must be a Unix timestamp (integer)")
        if self.deployed_at < 0:
            raise ValueError("deployed_at must be a positive Unix timestamp")

        if not self.deployed_by or not self.deployed_by.strip():
            raise ValueError("deployed_by is required and cannot be empty")
