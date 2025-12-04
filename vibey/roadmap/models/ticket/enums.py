"""
Enum types for the Unified Ticket Architecture.

This module defines all enum types used by the unified completion model.
It serves as the single source of truth for type values - all enums are
defined here and imported elsewhere.

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from enum import Enum


# =============================================================================
# TICKET LIFECYCLE ENUMS
# =============================================================================


class TicketStatus(str, Enum):
    """
    Lifecycle status for tickets (Completable entities).

    Status progression:
        NOT_STARTED → IN_PROGRESS → PAUSED → COMPLETION_GATE_CHECK →
        COMPLETED → PRODUCTION_GATE_CHECK → PRODUCTION_READY → DEPLOYED

    Terminal states: WONT_DO, SUPERSEDED
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETION_GATE_CHECK = "completion_gate_check"
    COMPLETED = "completed"
    PRODUCTION_GATE_CHECK = "production_gate_check"
    PRODUCTION_READY = "production_ready"
    DEPLOYED = "deployed"
    WONT_DO = "wont_do"
    SUPERSEDED = "superseded"

    @classmethod
    def progression_order(cls) -> list["TicketStatus"]:
        """Return statuses in progression order (for comparison)."""
        return [
            cls.NOT_STARTED,
            cls.IN_PROGRESS,
            cls.PAUSED,
            cls.COMPLETION_GATE_CHECK,
            cls.COMPLETED,
            cls.PRODUCTION_GATE_CHECK,
            cls.PRODUCTION_READY,
            cls.DEPLOYED,
        ]

    @classmethod
    def terminal_statuses(cls) -> list["TicketStatus"]:
        """Return terminal statuses that cannot progress further."""
        return [cls.WONT_DO, cls.SUPERSEDED]

    def is_terminal(self) -> bool:
        """Check if this status is terminal."""
        return self in self.terminal_statuses()

    def can_progress_to(self, target: "TicketStatus") -> bool:
        """Check if this status can progress to target status."""
        if self.is_terminal() or target.is_terminal():
            return False
        order = self.progression_order()
        try:
            return order.index(target) > order.index(self)
        except ValueError:
            return False


class TicketType(str, Enum):
    """
    Hierarchy level discriminator for tickets.

    Defines the four levels of the Vibey roadmap hierarchy:
        ROADMAP → TRACK → SPRINT → TASK
    """

    ROADMAP = "roadmap"
    TRACK = "track"
    SPRINT = "sprint"
    TASK = "task"

    @classmethod
    def hierarchy_order(cls) -> list["TicketType"]:
        """Return types in hierarchy order (parent to child)."""
        return [cls.ROADMAP, cls.TRACK, cls.SPRINT, cls.TASK]

    def parent_type(self) -> "TicketType | None":
        """Return the parent type in the hierarchy."""
        order = self.hierarchy_order()
        idx = order.index(self)
        return order[idx - 1] if idx > 0 else None

    def child_type(self) -> "TicketType | None":
        """Return the child type in the hierarchy."""
        order = self.hierarchy_order()
        idx = order.index(self)
        return order[idx + 1] if idx < len(order) - 1 else None


# =============================================================================
# TASK CLASSIFICATION ENUMS
# =============================================================================


class TaskType(str, Enum):
    """
    Semantic classification of task work type.

    Used to categorize the nature of work being performed.
    """

    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    INFRASTRUCTURE = "infrastructure"
    GATE = "gate"  # Quality gate task


class Complexity(str, Enum):
    """
    Work complexity estimate for tasks.

    Used for effort estimation and capacity planning.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Extremely complex, high-risk


class Priority(str, Enum):
    """
    Priority levels for tickets.

    Used to determine execution order and resource allocation.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def priority_order(cls) -> list["Priority"]:
        """Return priorities in order (highest to lowest)."""
        return [cls.CRITICAL, cls.HIGH, cls.MEDIUM, cls.LOW]

    def __lt__(self, other: "Priority") -> bool:
        """Compare priorities (CRITICAL > HIGH > MEDIUM > LOW)."""
        if not isinstance(other, Priority):
            return NotImplemented
        order = self.priority_order()
        return order.index(self) > order.index(other)

    def __le__(self, other: "Priority") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Priority") -> bool:
        if not isinstance(other, Priority):
            return NotImplemented
        return other < self

    def __ge__(self, other: "Priority") -> bool:
        return self == other or self > other


# =============================================================================
# CRITERION TARGET ENUMS
# =============================================================================


class CriterionTargetType(str, Enum):
    """
    Polymorphic target type discriminator for criteria.

    Determines how a criterion's satisfaction is evaluated.
    Each type corresponds to a different CriterionTarget subclass.
    """

    # Core types (Sprint 6)
    COMPLETABLE = "completable"  # Another Completable must reach status
    FILE_EXISTS = "file_exists"  # File(s) must exist at path(s)
    TEST_PASSES = "test_passes"  # Test command must pass
    TEST_COVERAGE = "test_coverage"  # Test coverage must meet threshold
    THRESHOLD = "threshold"  # Metric must meet threshold
    MANUAL = "manual"  # Human assessment required
    EXTERNAL = "external"  # External system check

    # Artifact types (Sprint 7)
    # ARTIFACT = "artifact"  # Artifact entity must exist and be valid

    # Code verification types (Sprint 10)
    # SYMBOL_EXISTS = "symbol_exists"  # Code symbol must exist
    # COMMAND_EXISTS = "command_exists"  # CLI command must exist
    # MCP_TOOL_EXISTS = "mcp_tool_exists"  # MCP tool must exist


class ThresholdComparison(str, Enum):
    """
    Comparison operators for threshold-based criteria.

    Used by ThresholdTarget to define how values are compared.
    """

    GTE = "gte"  # >= (at least)
    GT = "gt"  # > (more than)
    EQ = "eq"  # == (exactly)
    LTE = "lte"  # <= (at most)
    LT = "lt"  # < (less than)

    def compare(self, actual: float, threshold: float) -> bool:
        """Evaluate comparison between actual and threshold values."""
        comparisons = {
            self.GTE: actual >= threshold,
            self.GT: actual > threshold,
            self.EQ: actual == threshold,
            self.LTE: actual <= threshold,
            self.LT: actual < threshold,
        }
        return comparisons[self]

    def description(self, threshold: float) -> str:
        """Return human-readable description of the threshold."""
        descriptions = {
            self.GTE: f"at least {threshold}",
            self.GT: f"more than {threshold}",
            self.EQ: f"exactly {threshold}",
            self.LTE: f"at most {threshold}",
            self.LT: f"less than {threshold}",
        }
        return descriptions[self]


# =============================================================================
# REQUIREMENT SYSTEM ENUMS
# =============================================================================


class InheritMode(str, Enum):
    """
    Inheritance behavior for requirements.

    Controls how requirements are resolved when both local and
    ancestor requirements exist.
    """

    INHERIT = "inherit"  # Use stricter of local vs ancestor
    OVERRIDE = "override"  # Replace ancestor entirely
    SKIP = "skip"  # Explicitly not applicable


class EnforcementMode(str, Enum):
    """
    How strictly a requirement is enforced.

    Controls the consequence of an unmet requirement.
    """

    BLOCKING = "blocking"  # Prevents status transition
    WARNING = "warning"  # Shows warning, allows transition
    AUDIT = "audit"  # Logs only, no user feedback


class RequirementType(str, Enum):
    """
    Categories of requirements that can be applied to tickets.

    Used to group and filter requirements by their purpose.
    """

    TEST_COVERAGE = "test_coverage"
    CODE_STYLE = "code_style"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    REVIEW = "review"
    CUSTOM = "custom"


# =============================================================================
# GATE STATUS ENUMS
# =============================================================================


class GateStatus(str, Enum):
    """
    Status of development gates (sprint-specific blocking conditions).

    Gates are used to track sprint-level quality checkpoints.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"

    def is_resolved(self) -> bool:
        """Check if this gate is resolved (passed or failed)."""
        return self in (self.PASSED, self.FAILED)

    def is_blocking(self) -> bool:
        """Check if this gate status is blocking."""
        return self in (self.NOT_STARTED, self.IN_PROGRESS, self.BLOCKED, self.FAILED)


# =============================================================================
# DEPENDENCY ENUMS
# =============================================================================


class DependencyRelation(str, Enum):
    """
    Sibling relationship types between tickets.

    Note: In the unified model, dependencies are criteria with
    CompletableTarget. This enum is for semantic labeling of
    the relationship type.
    """

    BLOCKS = "blocks"  # This ticket blocks another
    DEPENDS_ON = "depends_on"  # This ticket depends on another
    RELATED = "related"  # Informational link only


# =============================================================================
# DELIVERABLE ENUMS
# =============================================================================


class DeliverableType(str, Enum):
    """
    Types of task deliverables.

    Used to categorize outputs produced by task completion.
    """

    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    DESIGN = "design"
    OTHER = "other"


# =============================================================================
# ACTIVITY LOG ENUMS
# =============================================================================


class ActivityType(str, Enum):
    """
    Types of activity log entries.

    Used to categorize events in the audit trail.
    """

    # Roadmap events
    ROADMAP_INITIALIZED = "roadmap_initialized"
    ROADMAP_STARTED = "roadmap_started"
    ROADMAP_COMPLETED = "roadmap_completed"
    ROADMAP_DEPLOYED = "roadmap_deployed"

    # Track events
    TRACK_ADDED = "track_added"
    TRACK_STARTED = "track_started"
    TRACK_COMPLETED = "track_completed"

    # Sprint events
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    SPRINT_PRODUCTION_READY = "sprint_production_ready"

    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"

    # Quality events
    QUALITY_GATE = "quality_gate"
    CRITERION_MET = "criterion_met"
    CRITERION_FAILED = "criterion_failed"

    # Blocking events
    BLOCKER_ADDED = "blocker_added"
    BLOCKER_RESOLVED = "blocker_resolved"

    # Planning events
    DESIGN_COMPLETED = "design_completed"
    PLANNING_COMPLETED = "planning_completed"

    # Version events
    VERSION_BUMP = "version_bump"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Ticket lifecycle
    "TicketStatus",
    "TicketType",
    # Task classification
    "TaskType",
    "Complexity",
    "Priority",
    # Criterion targets
    "CriterionTargetType",
    "ThresholdComparison",
    # Requirement system
    "InheritMode",
    "EnforcementMode",
    "RequirementType",
    # Gate status
    "GateStatus",
    # Dependencies
    "DependencyRelation",
    # Deliverables
    "DeliverableType",
    # Activity log
    "ActivityType",
]
