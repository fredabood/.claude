class ActivityLogEntry(BaseModel):
    """Unified activity/audit entry for all changes."""

    # Core fields
    timestamp: datetime
    type: ActivityType
    description: str

    # Entity tracking (for any entity, not just roadmap)
    entity_type: Optional[str] = None  # roadmap, track, sprint, task, criterion
    entity_id: Optional[str] = None

    # Field change tracking (when type is FIELD_CHANGED or STATUS_CHANGED)
    field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    # Attribution
    changed_by: Optional[str] = None
    commit_sha: Optional[str] = None

    # Additional context
    context: Optional[Dict[str, Any]] = None


class ActivityType(str, Enum):
    # High-level lifecycle events
    ROADMAP_STARTED = "roadmap_started"
    ROADMAP_COMPLETED = "roadmap_completed"
    TRACK_STARTED = "track_started"
    TRACK_COMPLETED = "track_completed"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"

    # Field-level audit events
    FIELD_CHANGED = "field_changed"
    STATUS_CHANGED = "status_changed"

    # Criterion events
    CRITERION_MET = "criterion_met"
    CRITERION_EVALUATED = "criterion_evaluated"  # For non-required
    CRITERION_REFRESHED = "criterion_refreshed"

    # System events
    AUTO_PROGRESSION = "auto_progression"
    VALIDATION_WARNING = "validation_warning"
