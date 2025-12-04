class Criterion(BaseModel):
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
        ...

    def evaluate(self, activity_log: List[ActivityLogEntry]) -> bool:
        """Evaluate with logging for non-required criteria."""
        ...
