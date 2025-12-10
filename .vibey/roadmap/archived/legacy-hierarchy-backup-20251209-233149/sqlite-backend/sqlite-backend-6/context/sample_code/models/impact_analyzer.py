class ImpactAnalyzer:
    """Analyzes impact of changes across the artifact graph."""

    def __init__(self, artifact_registry: "ArtifactRegistry", db: "Database"):
        self._artifacts = artifact_registry
        self._db = db

    def analyze_file_changes(self, changed_files: List[str]) -> "ImpactReport":
        """
        Analyze which artifacts are impacted by file changes.

        Called by:
        - Pre-commit hooks
        - Post-commit processing
        - Manual impact checks
        """
        # Find artifacts containing changed files
        directly_impacted = self._find_artifacts_by_files(changed_files)

        # Find documentation that documents impacted artifacts
        stale_documentation = []
        for artifact in directly_impacted:
            docs = self._find_documenting_artifacts(artifact.id)
            stale_documentation.extend(docs)

        # Find tickets affected by stale documentation
        affected_tickets = self._find_affected_tickets(stale_documentation)

        return ImpactReport(
            changed_files=changed_files,
            directly_impacted_artifacts=directly_impacted,
            stale_documentation=stale_documentation,
            affected_tickets=affected_tickets
        )

    def _find_artifacts_by_files(self, files: List[str]) -> List[Artifact]:
        """Find artifacts whose paths include any of the given files."""
        results = []
        for artifact in self._artifacts.all():
            if any(f in artifact.paths for f in files):
                results.append(artifact)
        return results

    def _find_documenting_artifacts(self, artifact_id: str) -> List[Artifact]:
        """Find documentation artifacts that document the given artifact."""
        return self._db.query("""
            SELECT * FROM artifacts
            WHERE documents_artifact_id = ?
        """, (artifact_id,))

    def _find_affected_tickets(self, stale_docs: List[Artifact]) -> List[str]:
        """Find tickets with criteria referencing stale documentation."""
        ticket_ids = set()
        for doc in stale_docs:
            criteria = self._db.query("""
                SELECT ticket_id FROM criteria WHERE artifact_id = ?
            """, (doc.id,))
            ticket_ids.update(c.ticket_id for c in criteria)
        return list(ticket_ids)


@dataclass
class ImpactReport:
    """Report of impact from file changes."""

    changed_files: List[str]
    directly_impacted_artifacts: List[Artifact]
    stale_documentation: List[Artifact]
    affected_tickets: List[str]

    @property
    def has_documentation_impact(self) -> bool:
        return len(self.stale_documentation) > 0

    def to_warning_message(self) -> str:
        """Generate warning message for pre-commit hook."""
        if not self.has_documentation_impact:
            return ""

        lines = ["⚠️  Documentation may need updating:"]
        for doc in self.stale_documentation:
            lines.append(f"  - {doc.name} ({', '.join(doc.paths)})")

        if self.affected_tickets:
            lines.append(f"\nAffected tickets: {', '.join(self.affected_tickets)}")

        return "\n".join(lines)
