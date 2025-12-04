def verify_completion_claims(commit_message: str, root_dir: Path) -> List[str]:
    """
    Verify that claimed completions meet all criteria.

    Called by pre-commit hook when commit contains "Completes:" lines.
    Returns list of errors (empty = OK to commit).
    """
    errors = []

    # Extract claimed completions
    claimed = []
    for line in commit_message.split('\n'):
        if line.startswith('Completes:'):
            ticket_id = line.replace('Completes:', '').strip()
            claimed.append(ticket_id)

    for ticket_id in claimed:
        ticket = load_ticket(ticket_id, root_dir)
        if not ticket:
            errors.append(f"Unknown ticket: {ticket_id}")
            continue

        can, reasons = ticket.can_transition_to(TicketStatus.COMPLETED)

        if not can:
            errors.append(
                f"Cannot complete {ticket_id} - criteria not met:\n" +
                "\n".join(f"  - {r}" for r in reasons)
            )

    return errors
