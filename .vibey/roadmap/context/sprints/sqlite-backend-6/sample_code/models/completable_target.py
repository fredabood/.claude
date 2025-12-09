class CompletableTarget(CriterionTarget):
    completable_id: str
    required_status: TicketStatus = TicketStatus.COMPLETED

    # Cached state
    current_status: Optional[TicketStatus]
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
