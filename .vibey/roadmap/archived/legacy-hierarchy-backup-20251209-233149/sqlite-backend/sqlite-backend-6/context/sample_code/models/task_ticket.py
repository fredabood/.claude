class TaskTicket(HierarchicalTicket):
    """Task-specific semantic fields."""
    task_type: TaskType
    estimated_tokens: int  # Required for tasks
    actual_tokens: Optional[int] = None
    complexity: Complexity = Complexity.MEDIUM
    phase_label: Optional[str] = None


class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    @computed_field
    def computed_tokens(self) -> int:
        """
        Token estimate for this ticket.

        - Ultimate children (tasks): return estimated_tokens
        - Parents: aggregate from children's computed_tokens
        """
        if self.is_ultimate_child:
            # TaskTicket has estimated_tokens
            return getattr(self, 'estimated_tokens', 0)

        # Aggregate from children
        return sum(
            child.computed_tokens
            for child in self._load_children()
        )
