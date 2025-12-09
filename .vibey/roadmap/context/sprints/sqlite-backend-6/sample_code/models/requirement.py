class Requirement(BaseModel):
    """A criterion template that cascades down the hierarchy."""

    id: str
    name: str
    description: str

    # What type of criterion this generates
    criterion_template: CriterionTemplate

    # When does this apply?
    applicability: ApplicabilityRules

    # Inheritance behavior (child's choice)
    inherit_mode: InheritMode  # INHERIT, OVERRIDE, SKIP

    # Enforcement (ancestor's constraint)
    enforceable: bool = False  # If True, descendants cannot OVERRIDE or SKIP
    skip_justification: Optional[str] = None  # Required when inherit_mode=SKIP


class CriterionTemplate(BaseModel):
    """Template for generating criteria."""

    target_type: CriterionTargetType
    target_config: Dict[str, Any]
    blocks_transition_to: TicketStatus = TicketStatus.COMPLETED

    def instantiate(self, ticket: Ticket) -> Criterion:
        """Generate a criterion for a specific ticket."""
        target = create_target(self.target_type, self.target_config, ticket)
        return Criterion(
            id=f"{self.id}-{ticket.id}",
            description=self.description,
            target=target,
            blocks_transition_to=self.blocks_transition_to
        )


class ApplicabilityRules(BaseModel):
    """Rules for when a requirement applies."""

    ticket_types: Optional[List[str]] = None
    task_types: Optional[List[TaskType]] = None
    has_criterion_types: Optional[List[CriterionTargetType]] = None

    def matches(self, ticket: Ticket) -> bool:
        """Check if this requirement applies to a ticket."""
        # Implementation checks each rule
        ...


class InheritMode(str, Enum):
    """How a requirement interacts with inherited requirements."""
    INHERIT = "inherit"      # Use stricter of local vs ancestor
    OVERRIDE = "override"    # Replace ancestor requirement entirely
    SKIP = "skip"            # Explicitly not applicable (with justification)
