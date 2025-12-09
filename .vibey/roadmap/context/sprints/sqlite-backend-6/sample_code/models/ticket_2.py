class Ticket(Completable):
    """Layer 1: Base ticket with work semantics."""

    # ... existing fields from Part 3 ...

    # ═══════════════════════════════════════════════════════════════
    # ARTIFACT ACCESSORS (computed via criteria)
    # ═══════════════════════════════════════════════════════════════

    @property
    def artifact_criteria(self) -> List[Criterion]:
        """Criteria that reference artifacts."""
        return [
            c for c in self.criteria
            if isinstance(c.target, ArtifactTarget)
        ]

    @property
    def referenced_artifact_ids(self) -> List[str]:
        """IDs of artifacts referenced by this ticket's criteria."""
        return [
            c.target.artifact_id
            for c in self.artifact_criteria
        ]

    # ═══════════════════════════════════════════════════════════════
    # LIFECYCLE UPDATES FOR ARTIFACTS
    # ═══════════════════════════════════════════════════════════════

    def complete(self) -> tuple[bool, List[str]]:
        """Complete this ticket, capturing artifact state."""
        can, reasons = self.can_transition_to(TicketStatus.COMPLETED)

        # Additional check: all documentation artifacts must be current
        for criterion in self.artifact_criteria:
            if criterion.target.verification == ArtifactVerification.NOT_STALE:
                if criterion.target.artifact_is_stale:
                    reasons.append(
                        f"Documentation artifact is stale: {criterion.description}"
                    )
                    can = False

        if can:
            self.status = TicketStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)

            # Capture artifact hashes for future impact analysis
            self._capture_artifact_state()

        return (can, reasons)
