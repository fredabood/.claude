"""
Impact analyzer for documentation staleness detection.

This module provides the ImpactAnalyzer class that detects when code changes
affect documentation and identifies cascading updates needed.

Design reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.10
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Protocol

from pydantic import BaseModel, Field

from vibey.roadmap.models.ticket.artifact_enums import ArtifactType


# =============================================================================
# PROTOCOLS
# =============================================================================


class ArtifactRegistry(Protocol):
    """Protocol for artifact registry access."""

    def get(self, artifact_id: str) -> Optional["ArtifactLike"]:
        """Get an artifact by ID."""
        ...

    def get_all(self) -> List["ArtifactLike"]:
        """Get all artifacts."""
        ...


class ArtifactLike(Protocol):
    """Protocol for artifact-like objects."""

    id: str
    name: str
    artifact_type: ArtifactType
    paths: List[str]
    documents_artifact_id: Optional[str]
    is_stale: bool
    content_hash: Optional[str]

    def compute_content_hash(self, base_path: Optional[Path] = None) -> str:
        """Compute content hash from files."""
        ...


class Database(Protocol):
    """Protocol for database access."""

    def execute(self, query: str, params: tuple = ()) -> "CursorLike":
        """Execute a query."""
        ...


class CursorLike(Protocol):
    """Protocol for database cursor."""

    def fetchall(self) -> List[tuple]:
        ...

    def fetchone(self) -> Optional[tuple]:
        ...


# =============================================================================
# SUPPORTING MODELS
# =============================================================================


class ArtifactSummary(BaseModel):
    """Summary of an artifact for impact reports."""

    id: str
    name: str
    artifact_type: ArtifactType
    paths: List[str]

    @classmethod
    def from_artifact(cls, artifact: ArtifactLike) -> "ArtifactSummary":
        """Create from an artifact-like object."""
        return cls(
            id=artifact.id,
            name=artifact.name,
            artifact_type=artifact.artifact_type,
            paths=list(artifact.paths),
        )


class TicketImpact(BaseModel):
    """Impact of staleness on a ticket."""

    ticket_id: str
    ticket_name: str
    impact_type: str = Field(
        description="Type of impact: 'stale_doc_blocks_completion', 'stale_doc_warning'"
    )
    criterion_id: str
    artifact_id: str


class RecommendedAction(BaseModel):
    """Recommended action to resolve staleness."""

    action_type: str = Field(
        description="Type of action: 'update_documentation', 'refresh_hash', 'review'"
    )
    target_artifact_id: str
    description: str
    priority: str = Field(description="Priority: 'high', 'medium', 'low'")


class ImpactReport(BaseModel):
    """Report of impact from file changes."""

    # Input
    changed_files: List[str]
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Direct impacts
    directly_impacted_artifacts: List[ArtifactSummary] = Field(default_factory=list)

    # Documentation impacts
    stale_documentation: List[ArtifactSummary] = Field(default_factory=list)

    # Ticket impacts
    affected_tickets: List[TicketImpact] = Field(default_factory=list)

    # Recommendations
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)

    @property
    def total_artifacts_affected(self) -> int:
        """Total number of artifacts affected (direct + docs)."""
        return len(self.directly_impacted_artifacts) + len(self.stale_documentation)

    @property
    def total_tickets_affected(self) -> int:
        """Total number of unique tickets affected."""
        return len(set(t.ticket_id for t in self.affected_tickets))

    @property
    def has_blocking_impacts(self) -> bool:
        """Check if any impacts are blocking (would prevent completion)."""
        return any(
            t.impact_type == "stale_doc_blocks_completion"
            for t in self.affected_tickets
        )

    @property
    def has_any_impacts(self) -> bool:
        """Check if there are any impacts at all."""
        return (
            len(self.directly_impacted_artifacts) > 0
            or len(self.stale_documentation) > 0
            or len(self.affected_tickets) > 0
        )


# =============================================================================
# IMPACT ANALYZER
# =============================================================================


class ImpactAnalyzer:
    """
    Analyzes impact of file changes on artifacts and documentation.

    This class detects when code changes affect documentation and identifies
    cascading updates needed throughout the artifact graph.

    Usage:
        analyzer = ImpactAnalyzer(artifact_registry, db)
        report = analyzer.analyze_file_changes(["src/main.py", "src/utils.py"])

        if report.has_blocking_impacts:
            print("WARNING: Documentation may be stale")
            for action in report.recommended_actions:
                print(f"  - {action.description}")
    """

    def __init__(
        self,
        artifact_registry: ArtifactRegistry,
        db: Optional[Database] = None,
        base_path: Optional[Path] = None,
    ):
        """
        Initialize the ImpactAnalyzer.

        Args:
            artifact_registry: Registry providing access to artifacts
            db: Optional database for ticket queries
            base_path: Base path for resolving relative file paths
        """
        self._registry = artifact_registry
        self._db = db
        self._base_path = base_path

    def analyze_file_changes(self, changed_files: List[str]) -> ImpactReport:
        """
        Analyze impact of file changes.

        Args:
            changed_files: List of file paths that changed

        Returns:
            ImpactReport with affected artifacts and required updates
        """
        if not changed_files:
            return ImpactReport(changed_files=[])

        # Normalize file paths
        normalized_files = [self._normalize_path(f) for f in changed_files]

        # 1. Find artifacts containing changed files
        directly_impacted = self._find_artifacts_by_files(normalized_files)

        # 2. Find documentation that documents impacted artifacts
        stale_documentation = []
        for artifact in directly_impacted:
            docs = self._find_documenting_artifacts(artifact.id)
            stale_documentation.extend(docs)

        # Deduplicate stale docs
        seen_ids = set()
        unique_stale_docs = []
        for doc in stale_documentation:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                unique_stale_docs.append(doc)
        stale_documentation = unique_stale_docs

        # 3. Find tickets with criteria referencing stale documentation
        affected_tickets = self._find_affected_tickets(stale_documentation)

        # 4. Generate recommendations
        recommendations = self._generate_recommendations(
            directly_impacted, stale_documentation, affected_tickets
        )

        return ImpactReport(
            changed_files=changed_files,
            directly_impacted_artifacts=[
                ArtifactSummary.from_artifact(a) for a in directly_impacted
            ],
            stale_documentation=[
                ArtifactSummary.from_artifact(a) for a in stale_documentation
            ],
            affected_tickets=affected_tickets,
            recommended_actions=recommendations,
        )

    def mark_documentation_stale(self, artifact_ids: List[str]) -> int:
        """
        Mark documentation artifacts as stale.

        Args:
            artifact_ids: List of artifact IDs to mark stale

        Returns:
            Count of artifacts updated
        """
        count = 0
        for artifact_id in artifact_ids:
            artifact = self._registry.get(artifact_id)
            if artifact is not None:
                # Try to set is_stale if the artifact supports it
                if hasattr(artifact, "is_stale"):
                    artifact.is_stale = True
                    count += 1
        return count

    def refresh_artifact_hashes(
        self, artifact_ids: List[str], base_path: Optional[Path] = None
    ) -> int:
        """
        Recompute content hashes for artifacts.

        Args:
            artifact_ids: List of artifact IDs to refresh
            base_path: Base path for resolving file paths

        Returns:
            Count of artifacts updated
        """
        effective_base = base_path or self._base_path
        count = 0

        for artifact_id in artifact_ids:
            artifact = self._registry.get(artifact_id)
            if artifact is not None and hasattr(artifact, "compute_content_hash"):
                try:
                    artifact.compute_content_hash(effective_base)
                    count += 1
                except Exception:
                    # Skip artifacts that can't compute hash (e.g., missing files)
                    pass

        return count

    def _normalize_path(self, path: str) -> str:
        """Normalize a file path for comparison."""
        # Remove leading ./ if present
        if path.startswith("./"):
            path = path[2:]
        # Remove leading / if present
        if path.startswith("/") and self._base_path:
            # Try to make it relative to base_path
            try:
                p = Path(path)
                rel = p.relative_to(self._base_path)
                path = str(rel)
            except ValueError:
                pass
        return path

    def _find_artifacts_by_files(
        self, files: List[str]
    ) -> List[ArtifactLike]:
        """
        Find artifacts whose paths contain any of the given files.

        Args:
            files: Normalized file paths to search for

        Returns:
            List of artifacts containing the files
        """
        matching_artifacts = []
        file_set = set(files)

        for artifact in self._registry.get_all():
            # Check if any of the artifact's paths match
            artifact_paths = set(self._normalize_path(p) for p in artifact.paths)
            if artifact_paths & file_set:
                matching_artifacts.append(artifact)

        return matching_artifacts

    def _find_documenting_artifacts(self, artifact_id: str) -> List[ArtifactLike]:
        """
        Find artifacts that document the given artifact.

        Args:
            artifact_id: ID of the source artifact

        Returns:
            List of documentation artifacts
        """
        documenting = []

        for artifact in self._registry.get_all():
            if artifact.documents_artifact_id == artifact_id:
                documenting.append(artifact)

        return documenting

    def _find_affected_tickets(
        self, stale_artifacts: List[ArtifactLike]
    ) -> List[TicketImpact]:
        """
        Find tickets with criteria referencing stale artifacts.

        Args:
            stale_artifacts: List of stale documentation artifacts

        Returns:
            List of affected ticket impacts
        """
        if self._db is None or not stale_artifacts:
            return []

        affected = []
        artifact_ids = [a.id for a in stale_artifacts]

        # Query for criteria referencing these artifacts
        # This assumes a criteria table with target_type and target_data columns
        try:
            placeholders = ",".join("?" * len(artifact_ids))
            query = f"""
                SELECT
                    c.id AS criterion_id,
                    c.ticket_id,
                    t.title AS ticket_name,
                    json_extract(c.target_data, '$.artifact_id') AS artifact_id,
                    c.blocks_transition_to
                FROM criteria c
                JOIN tasks t ON c.ticket_id = t.id
                WHERE c.target_type = 'artifact'
                  AND json_extract(c.target_data, '$.artifact_id') IN ({placeholders})
            """
            cursor = self._db.execute(query, tuple(artifact_ids))
            rows = cursor.fetchall()

            for row in rows:
                criterion_id, ticket_id, ticket_name, artifact_id, blocks_transition = row
                impact_type = (
                    "stale_doc_blocks_completion"
                    if blocks_transition
                    else "stale_doc_warning"
                )
                affected.append(
                    TicketImpact(
                        ticket_id=ticket_id,
                        ticket_name=ticket_name or "Unknown",
                        impact_type=impact_type,
                        criterion_id=criterion_id,
                        artifact_id=artifact_id,
                    )
                )
        except Exception:
            # Database query failed - return empty list
            pass

        return affected

    def _generate_recommendations(
        self,
        directly_impacted: List[ArtifactLike],
        stale_docs: List[ArtifactLike],
        affected_tickets: List[TicketImpact],
    ) -> List[RecommendedAction]:
        """
        Generate recommended actions based on impacts.

        Args:
            directly_impacted: Artifacts directly affected by file changes
            stale_docs: Documentation artifacts that may be stale
            affected_tickets: Tickets affected by staleness

        Returns:
            List of recommended actions
        """
        recommendations = []

        # Recommend refreshing hashes for directly impacted artifacts
        for artifact in directly_impacted:
            recommendations.append(
                RecommendedAction(
                    action_type="refresh_hash",
                    target_artifact_id=artifact.id,
                    description=f"Refresh content hash for '{artifact.name}'",
                    priority="medium",
                )
            )

        # Recommend updating stale documentation
        # Higher priority if it blocks ticket completion
        blocking_artifact_ids = set(t.artifact_id for t in affected_tickets if t.impact_type == "stale_doc_blocks_completion")

        for doc in stale_docs:
            priority = "high" if doc.id in blocking_artifact_ids else "medium"
            recommendations.append(
                RecommendedAction(
                    action_type="update_documentation",
                    target_artifact_id=doc.id,
                    description=f"Update documentation '{doc.name}' to reflect source changes",
                    priority=priority,
                )
            )

        # Recommend review for affected tickets
        reviewed_tickets = set()
        for impact in affected_tickets:
            if impact.ticket_id not in reviewed_tickets:
                reviewed_tickets.add(impact.ticket_id)
                recommendations.append(
                    RecommendedAction(
                        action_type="review",
                        target_artifact_id=impact.artifact_id,
                        description=f"Review ticket '{impact.ticket_name}' - completion criteria may be affected",
                        priority="low" if impact.impact_type == "stale_doc_warning" else "high",
                    )
                )

        return recommendations


# =============================================================================
# GIT HOOK HELPERS
# =============================================================================


def analyze_staged_files(
    artifact_registry: ArtifactRegistry,
    db: Optional[Database] = None,
    base_path: Optional[Path] = None,
) -> ImpactReport:
    """
    Analyze impact of currently staged git files.

    This is a convenience function for use in pre-commit hooks.

    Args:
        artifact_registry: Registry providing access to artifacts
        db: Optional database for ticket queries
        base_path: Base path of the git repository

    Returns:
        ImpactReport with affected artifacts

    Example usage in pre-commit hook:
        from vibey.roadmap.operations import analyze_staged_files

        report = analyze_staged_files(registry, db, Path("."))
        if report.has_blocking_impacts:
            print("WARNING: Documentation may be stale")
            sys.exit(1)
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(base_path) if base_path else None,
        )
        staged_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        staged_files = []

    analyzer = ImpactAnalyzer(artifact_registry, db, base_path)
    return analyzer.analyze_file_changes(staged_files)


def format_impact_report(report: ImpactReport, verbose: bool = False) -> str:
    """
    Format an impact report for console output.

    Args:
        report: The impact report to format
        verbose: Whether to include detailed recommendations

    Returns:
        Formatted string for console output
    """
    lines = []

    if not report.has_any_impacts:
        return "No documentation impacts detected."

    lines.append(f"Impact Analysis ({len(report.changed_files)} files changed)")
    lines.append("=" * 50)

    if report.directly_impacted_artifacts:
        lines.append(f"\nDirectly Impacted Artifacts ({len(report.directly_impacted_artifacts)}):")
        for artifact in report.directly_impacted_artifacts:
            lines.append(f"  - {artifact.name} ({artifact.artifact_type.value})")

    if report.stale_documentation:
        lines.append(f"\nPotentially Stale Documentation ({len(report.stale_documentation)}):")
        for doc in report.stale_documentation:
            lines.append(f"  - {doc.name}")

    if report.affected_tickets:
        lines.append(f"\nAffected Tickets ({report.total_tickets_affected}):")
        for impact in report.affected_tickets:
            status = "BLOCKING" if impact.impact_type == "stale_doc_blocks_completion" else "warning"
            lines.append(f"  - [{status}] {impact.ticket_name}")

    if verbose and report.recommended_actions:
        lines.append(f"\nRecommended Actions ({len(report.recommended_actions)}):")
        for action in report.recommended_actions:
            lines.append(f"  [{action.priority.upper()}] {action.description}")

    if report.has_blocking_impacts:
        lines.append("\n⚠️  WARNING: Some impacts may block ticket completion!")

    return "\n".join(lines)
