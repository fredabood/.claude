def start(self, platform_context_window: Optional[int] = None) -> tuple[bool, List[str]]:
    """Start work on this ticket with optional platform validation."""
    can, reasons = self.can_transition_to(TicketStatus.IN_PROGRESS)

    # Platform fit check (warning, not blocker)
    if platform_context_window and self.computed_tokens > platform_context_window:
        warning = (
            f"Ticket requires ~{self.computed_tokens} tokens but platform "
            f"context window is {platform_context_window}. Consider splitting."
        )
        reasons.append(warning)
        logger.warning(warning)
        # Note: This is a WARNING, not a blocker - can still proceed

    if can:
        self.status = TicketStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    return (can, reasons)
