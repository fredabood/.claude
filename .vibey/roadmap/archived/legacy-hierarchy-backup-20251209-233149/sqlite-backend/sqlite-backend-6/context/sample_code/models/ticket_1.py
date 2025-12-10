class Ticket(Completable):
    """Layer 1: Base ticket with work semantics."""

    # ... existing fields ...

    # Priority (optional - used by Track and Task)
    priority: Optional[Priority] = None

    # Deferral flag - marks ticket as optional for production
    deferred: bool = False

    # Duration tracking (optional, stored on any level)
    estimated_duration_local: Optional[str] = None
    actual_duration_local: Optional[str] = None


class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    @property
    def effective_priority(self) -> Priority:
        """Priority with inheritance from parent."""
        if self.priority is not None:
            return self.priority
        parent = self._load_parent()
        if parent and hasattr(parent, 'effective_priority'):
            return parent.effective_priority
        return Priority.MEDIUM

    @property
    def estimated_duration(self) -> Optional[str]:
        """Duration with parent aggregation from children."""
        if self.estimated_duration_local:
            return self.estimated_duration_local
        if self.is_parent:
            return self._aggregate_duration_from_children()
        return None

    @property
    def required_children(self) -> List[str]:
        """Children that are not deferred."""
        return [
            c.target.completable_id
            for c in self.criteria
            if isinstance(c.target, CompletableTarget)
            and not self._is_child_deferred(c.target.completable_id)
        ]
