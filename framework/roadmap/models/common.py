"""
Common types and enums used across all roadmap models.
"""

from enum import Enum


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
    ROADMAP_INITIALIZED = "roadmap_initialized"


class VersionBumpTrigger(str, Enum):
    """Version bump triggers."""

    ROADMAP_MILESTONE = "roadmap_milestone"
    TRACK_COMPLETION = "track_completion"
    SPRINT_PRODUCTION_READY = "sprint_production_ready"
    MANUAL = "manual"
