class ApplicabilityRules(BaseModel):
    ticket_types: Optional[List[str]]
    task_types: Optional[List[TaskType]]
    has_criterion_types: Optional[List[CriterionTargetType]]

    def matches(self, ticket: Ticket) -> bool: ...
