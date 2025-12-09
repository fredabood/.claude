class Completable(BaseModel):
    """Base class for anything that can be completed."""

    # ═══════════════════════════════════════════════════════════════
    # IDENTITY (ULID-based, immutable)
    # ═══════════════════════════════════════════════════════════════
    id: str  # ULID format: {type}_{ulid} e.g., "task_01JB3QVE5NTSK2BPFQR8LVXABC"
    name: str  # Display name (mutable, not used for references)
    description: Optional[str] = None

    # THE source of truth for ALL blocking
    criteria: List[Criterion] = Field(default_factory=list)

    # Computed properties
    @computed_field
    def children(self) -> List[str]:
        """Children are derived from CompletableTarget criteria."""
        return [
            c.target.completable_id
            for c in self.criteria
            if isinstance(c.target, CompletableTarget)
        ]

    def can_transition_to(self, status: TicketStatus) -> tuple[bool, List[str]]:
        """
        THE unified interface for checking state transitions.

        Returns (can_transition, blocking_reasons).
        """
        blocking = [
            c.description
            for c in self.criteria
            if c.blocks_transition_to == status and not c.is_met
        ]
        return (len(blocking) == 0, blocking)

    def progress_for_transition(self, status: TicketStatus) -> Progress:
        """Progress computed per transition type."""
        relevant = [c for c in self.criteria if c.blocks_transition_to == status]
        total = len(relevant)
        met = sum(1 for c in relevant if c.is_met)
        return Progress(
            total=total,
            completed=met,
            completion_percent=(met / total * 100) if total > 0 else 100.0
        )

    @property
    def progress(self) -> Progress:
        """Default progress = progress toward COMPLETED."""
        return self.progress_for_transition(TicketStatus.COMPLETED)
