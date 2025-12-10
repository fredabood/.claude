class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    # ... existing accessors from Part 3 ...

    # ═══════════════════════════════════════════════════════════════
    # ARTIFACT AGGREGATION
    # ═══════════════════════════════════════════════════════════════

    @property
    def all_referenced_artifacts(self) -> List[str]:
        """
        All artifact IDs referenced by this ticket and descendants.

        Aggregation: Parents see all descendant artifacts.
        """
        if self.is_ultimate_child:
            return self.referenced_artifact_ids

        all_ids = list(self.referenced_artifact_ids)
        for child in self._load_children():
            all_ids.extend(child.all_referenced_artifacts)

        return list(set(all_ids))  # Deduplicate

    @property
    def stale_documentation_artifacts(self) -> List[str]:
        """
        Artifact IDs for stale documentation in this subtree.

        Aggregation: Parents see all stale docs in descendants.
        """
        stale = []

        for criterion in self.artifact_criteria:
            if (criterion.target.verification == ArtifactVerification.NOT_STALE
                and criterion.target.artifact_is_stale):
                stale.append(criterion.target.artifact_id)

        if not self.is_ultimate_child:
            for child in self._load_children():
                stale.extend(child.stale_documentation_artifacts)

        return list(set(stale))

    @property
    def has_stale_documentation(self) -> bool:
        """True if any documentation in this subtree is stale."""
        return len(self.stale_documentation_artifacts) > 0

    @property
    def documentation_health(self) -> "DocumentationHealth":
        """
        Aggregate documentation health status.
        """
        stale_count = len(self.stale_documentation_artifacts)

        if stale_count == 0:
            return DocumentationHealth.HEALTHY

        # Check if any stale docs block completion
        for criterion in self.artifact_criteria:
            if (criterion.target.artifact_is_stale
                and criterion.blocks_transition_to == TicketStatus.COMPLETED
                and criterion.required):
                return DocumentationHealth.CRITICAL

        return DocumentationHealth.DEGRADED


class DocumentationHealth(str, Enum):
    """Documentation health status."""
    HEALTHY = "healthy"      # All docs current
    DEGRADED = "degraded"    # Some docs stale (non-blocking)
    CRITICAL = "critical"    # Stale docs blocking completion
