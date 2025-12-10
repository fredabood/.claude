class DeliverableType(str, Enum):
    """Classification for file-based deliverables."""
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    OTHER = "other"


class ActivityType(str, Enum):
    """Types of activity log entries (unified audit trail)."""
    # Lifecycle events
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

    # Field-level audit
    FIELD_CHANGED = "field_changed"
    STATUS_CHANGED = "status_changed"

    # Criterion events
    CRITERION_MET = "criterion_met"
    CRITERION_EVALUATED = "criterion_evaluated"
    CRITERION_REFRESHED = "criterion_refreshed"

    # System events
    AUTO_PROGRESSION = "auto_progression"
    VALIDATION_WARNING = "validation_warning"
    COMMIT_LINKED = "commit_linked"
