def get_dependents(self, ticket_id: str) -> List[str]:
    """Get tickets that depend on this ticket (reverse lookup)."""
    return self._db.execute("""
        SELECT blocking_ticket_id
        FROM v_reverse_dependencies
        WHERE blocked_ticket_id = ?
    """, (ticket_id,)).fetchall()
