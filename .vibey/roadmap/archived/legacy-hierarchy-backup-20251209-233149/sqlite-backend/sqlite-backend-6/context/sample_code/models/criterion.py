class Criterion(BaseModel):
    """A single requirement for state transition."""

    # Identity
    id: str
    description: str

    # THE key field for unified blocking
    blocks_transition_to: TicketStatus = TicketStatus.COMPLETED

    # What satisfies this criterion (polymorphic)
    target: CriterionTarget

    # Optionality
    required: bool = True

    # Computed
    @property
    def is_met(self) -> bool:
        """Criterion is met when target is satisfied."""
        if not self.required:
            return True
        return self.target.is_satisfied()
