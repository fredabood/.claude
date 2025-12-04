class Completable(BaseModel):
    # Identity (ULID-based, immutable)
    id: str                              # Format: {type}_{ulid}
    name: str                            # Display name (mutable)
    description: Optional[str]

    # THE source of truth for ALL blocking
    criteria: List[Criterion] = []

    # Computed Properties
    @computed_field
    def children(self) -> List[str]:
        """Derived from CompletableTarget criteria."""
        ...

    # Core Methods
    def can_transition_to(self, status: TicketStatus) -> tuple[bool, List[str]]:
        """THE unified interface for checking state transitions."""
        ...

    def progress_for_transition(self, status: TicketStatus) -> Progress:
        """Progress computed per transition type."""
        ...

    @property
    def progress(self) -> Progress:
        """Default: progress toward COMPLETED."""
        ...
