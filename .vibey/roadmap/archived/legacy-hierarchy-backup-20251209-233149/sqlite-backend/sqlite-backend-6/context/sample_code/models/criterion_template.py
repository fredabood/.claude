class CriterionTemplate(BaseModel):
    target_type: CriterionTargetType
    target_config: Dict[str, Any]
    blocks_transition_to: TicketStatus = TicketStatus.COMPLETED

    def instantiate(self, ticket: Ticket) -> Criterion: ...
