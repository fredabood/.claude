def auto_progress(self, context: "RefreshContext") -> List[str]:
    """
    Refresh automatic criteria and progress status if possible.

    Returns list of transitions made.
    """
    transitions = []

    # Step 1: Refresh all automatic criteria
    for criterion in self.criteria:
        if criterion.target.is_automatic:
            criterion.target.refresh(context)

    # Step 2: Check each possible transition in order
    status_order = [
        TicketStatus.IN_PROGRESS,
        TicketStatus.COMPLETION_GATE_CHECK,
        TicketStatus.COMPLETED,
        TicketStatus.PRODUCTION_GATE_CHECK,
        TicketStatus.PRODUCTION_READY,
    ]

    for target_status in status_order:
        if self.status.precedes(target_status):
            can, reasons = self.can_transition_to(target_status)
            if can:
                old_status = self.status
                self._transition_to(target_status)
                transitions.append(f"{self.id}: {old_status} → {target_status}")

                # Log the auto-progression
                context.activity_log.append(ActivityLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    type=ActivityType.AUTO_PROGRESSION,
                    description=f"Auto-progressed from {old_status} to {target_status}",
                    entity_type=self.ticket_type,
                    entity_id=self.id,
                    field="status",
                    old_value=old_status.value,
                    new_value=target_status.value
                ))

    return transitions
