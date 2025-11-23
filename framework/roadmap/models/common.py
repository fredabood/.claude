"""
Common types and enums used across all roadmap models.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime


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
    WONT_DO = "won't_do"
    SUPERSEDED = "superseded"
    PENDING = "pending"


class TaskStatus(str, Enum):
    """Status enum for tasks (restricted set - no production statuses)."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETION_GATE_CHECK = "completion_gate_check"
    COMPLETED = "completed"
    WONT_DO = "won't_do"


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
