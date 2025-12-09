class Ticket(Completable):
    # === LIFECYCLE ===
    status: TicketStatus = TicketStatus.NOT_STARTED
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime

    # === WORK TRACKING ===
    commits_local: List[GitCommit] = []
    assigned_agents_local: List[str] = []

    # === HIERARCHY ===
    parent_ref: Optional[str]

    # === REQUIREMENTS ===
    requirements_local: List[Requirement] = []

    # === NEW FIELDS (from gap analysis) ===
    priority: Optional[Priority]
    deferred: bool = False
    estimated_duration_local: Optional[str]
    actual_duration_local: Optional[str]

    # === STATE TRANSITIONS ===
    def start(self) -> tuple[bool, List[str]]:
        """Start work - checks can_transition_to(IN_PROGRESS)."""
        ...

    def complete(self) -> tuple[bool, List[str]]:
        """Complete work - checks can_transition_to(COMPLETED)."""
        ...

    # === COMPUTED HIERARCHY ===
    @computed_field
    def is_parent(self) -> bool: ...

    @computed_field
    def is_child(self) -> bool: ...

    @computed_field
    def is_ultimate_parent(self) -> bool: ...

    @computed_field
    def is_ultimate_child(self) -> bool: ...

    @computed_field
    def is_intermediate(self) -> bool: ...
