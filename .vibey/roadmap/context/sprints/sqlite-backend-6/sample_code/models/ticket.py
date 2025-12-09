class Ticket(Completable):
    """Layer 1: Base ticket with work semantics."""

    # === IDENTITY (from Completable) ===
    # id, name, description, criteria

    # === LIFECYCLE ===
    status: TicketStatus = TicketStatus.NOT_STARTED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # === WORK TRACKING ===
    commits_local: List[GitCommit] = Field(default_factory=list)
    assigned_agents_local: List[str] = Field(default_factory=list)

    # === HIERARCHY (denormalized for lookup) ===
    parent_ref: Optional[str] = None

    # === REQUIREMENTS (criterion templates for children) ===
    requirements_local: List[Requirement] = Field(default_factory=list)

    # === DETERMINISTIC STATE TRANSITIONS ===
    def start(self) -> tuple[bool, List[str]]:
        """Start work on this ticket."""
        can, reasons = self.can_transition_to(TicketStatus.IN_PROGRESS)
        if can:
            self.status = TicketStatus.IN_PROGRESS
            self.started_at = datetime.now(timezone.utc)
        return (can, reasons)

    def complete(self) -> tuple[bool, List[str]]:
        """Complete this ticket."""
        can, reasons = self.can_transition_to(TicketStatus.COMPLETED)
        if can:
            self.status = TicketStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
        return (can, reasons)

    # === COMPUTED HIERARCHY ATTRIBUTES ===
    @computed_field
    def is_parent(self) -> bool:
        return len(self.children) > 0

    @computed_field
    def is_child(self) -> bool:
        return self.parent_ref is not None

    @computed_field
    def is_ultimate_parent(self) -> bool:
        return self.is_parent and not self.is_child

    @computed_field
    def is_ultimate_child(self) -> bool:
        return self.is_child and not self.is_parent

    @computed_field
    def is_intermediate(self) -> bool:
        return self.is_parent and self.is_child
