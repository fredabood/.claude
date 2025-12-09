class ActivityLogEntry(BaseModel):
    timestamp: datetime
    type: ActivityType
    description: str

    # Entity tracking
    entity_type: Optional[str]           # roadmap, track, sprint, task, criterion
    entity_id: Optional[str]

    # Field change tracking
    field: Optional[str]
    old_value: Optional[Any]
    new_value: Optional[Any]

    # Attribution
    changed_by: Optional[str]
    commit_sha: Optional[str]

    # Additional context
    context: Optional[Dict[str, Any]]
