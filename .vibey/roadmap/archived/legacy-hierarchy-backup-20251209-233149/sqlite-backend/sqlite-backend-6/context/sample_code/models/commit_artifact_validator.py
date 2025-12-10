class CommitArtifactValidator:
    """
    Validate consistency between commits, criteria, and artifacts.

    Ensures that:
    1. Completion claims are backed by criteria satisfaction
    2. Incidental artifact changes are flagged for awareness
    3. Missing criterion-artifact links are surfaced
    """

    def __init__(self, artifact_registry: Dict[str, Artifact], ticket_registry: Dict[str, Ticket]):
        self.artifacts = artifact_registry
        self.tickets = ticket_registry

    def validate_commit(self, commit: GitCommit) -> CommitValidationResult:
        """
        Validate a commit against the ticket/artifact system.

        Returns warnings and errors for review.
        """
        warnings = []
        errors = []
        info = []

        # Get all artifacts touched by this commit
        touched_artifacts = set(commit.all_affected_artifacts)

        # For each ticket this commit claims to complete
        for ticket_id in commit.completes_tickets:
            ticket = self.tickets.get(ticket_id)
            if not ticket:
                errors.append(f"Unknown ticket in Completes: {ticket_id}")
                continue

            # Get artifacts required by this ticket's criteria
            required_artifacts = self._get_required_artifacts(ticket)

            # Check for incidental changes
            incidental = touched_artifacts - required_artifacts
            if incidental:
                artifact_names = [self.artifacts[a].name for a in incidental if a in self.artifacts]
                warnings.append(
                    f"Commit touches artifacts not in {ticket_id} criteria: {artifact_names}"
                )

            # Check which required artifacts this commit provides
            provided = touched_artifacts & required_artifacts
            if provided:
                info.append(
                    f"Commit provides {len(provided)}/{len(required_artifacts)} "
                    f"required artifacts for {ticket_id}"
                )

        # Check for orphan artifact modifications (no ticket claims this commit)
        if not commit.completes_tickets and touched_artifacts:
            # Find which tickets have criteria for these artifacts
            potential_tickets = self._find_tickets_for_artifacts(touched_artifacts)
            if potential_tickets:
                warnings.append(
                    f"Commit modifies artifacts that are criteria for: {potential_tickets}. "
                    f"Consider adding 'Completes:' if work is done."
                )

        return CommitValidationResult(
            commit_sha=commit.sha,
            errors=errors,
            warnings=warnings,
            info=info,
            is_valid=len(errors) == 0
        )

    def validate_ticket_completion(self, ticket: Ticket) -> TicketValidationResult:
        """
        Validate that a ticket's completion is properly tracked.

        Checks that all required artifacts have commit provenance.
        """
        warnings = []
        info = []

        required_artifacts = self._get_required_artifacts(ticket)

        for artifact_id in required_artifacts:
            artifact = self.artifacts.get(artifact_id)
            if not artifact:
                warnings.append(f"Required artifact not found: {artifact_id}")
                continue

            # Check if artifact has commit provenance
            if not artifact.created_by_commit and not artifact.last_modified_by_commit:
                if artifact.provenance.type == ArtifactProvenance.PRE_EXISTING:
                    info.append(f"Artifact {artifact_id} is pre-existing (no commit expected)")
                else:
                    warnings.append(
                        f"Artifact {artifact_id} has no commit provenance. "
                        f"Was it created outside the tracked workflow?"
                    )

            # Check if any commit on this ticket touched this artifact
            ticket_commits = {c.sha for c in ticket.commits_local}
            artifact_commits = set(artifact.commit_history)
            if not (ticket_commits & artifact_commits):
                warnings.append(
                    f"Artifact {artifact_id} not touched by any commit on this ticket"
                )

        return TicketValidationResult(
            ticket_id=ticket.id,
            warnings=warnings,
            info=info,
            required_artifacts=list(required_artifacts),
            has_full_provenance=len(warnings) == 0
        )

    def _get_required_artifacts(self, ticket: Ticket) -> Set[str]:
        """Get artifact IDs required by ticket's criteria."""
        required = set()
        for criterion in ticket.criteria:
            if isinstance(criterion.target, CompletableTarget):
                completable_id = criterion.target.completable_id
                if completable_id in self.artifacts:
                    required.add(completable_id)
        return required

    def _find_tickets_for_artifacts(self, artifact_ids: Set[str]) -> List[str]:
        """Find tickets that have criteria for given artifacts."""
        tickets = []
        for ticket_id, ticket in self.tickets.items():
            required = self._get_required_artifacts(ticket)
            if required & artifact_ids:
                tickets.append(ticket_id)
        return tickets


@dataclass
class CommitValidationResult:
    """Result of validating a commit."""
    commit_sha: str
    errors: List[str]
    warnings: List[str]
    info: List[str]
    is_valid: bool

    def __str__(self) -> str:
        lines = [f"Commit {self.commit_sha[:8]}:"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        for i in self.info:
            lines.append(f"  INFO: {i}")
        return "\n".join(lines)


@dataclass
class TicketValidationResult:
    """Result of validating ticket completion."""
    ticket_id: str
    warnings: List[str]
    info: List[str]
    required_artifacts: List[str]
    has_full_provenance: bool

    def __str__(self) -> str:
        lines = [f"Ticket {self.ticket_id}:"]
        lines.append(f"  Required artifacts: {len(self.required_artifacts)}")
        lines.append(f"  Full provenance: {self.has_full_provenance}")
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        for i in self.info:
            lines.append(f"  INFO: {i}")
        return "\n".join(lines)
