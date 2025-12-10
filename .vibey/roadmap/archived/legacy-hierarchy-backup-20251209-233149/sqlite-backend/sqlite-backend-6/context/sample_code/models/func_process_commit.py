def process_commit(sha: str, repo_path: Path, platform: str) -> ProcessCommitResult:
    """
    Process a git commit: parse, link to artifacts, update staleness.

    Called by post-commit hook to integrate commit into the system.

    Returns:
        ProcessCommitResult with commit, affected artifacts, and any warnings
    """
    # Parse the commit
    commit = GitCommit.from_git(sha, repo_path, platform)

    # Load artifact registry
    artifact_registry = load_artifact_registry(repo_path)

    # Link commit to artifacts
    commit.link_to_artifacts(artifact_registry)

    # Update artifact states based on file changes
    warnings = []

    # Handle created artifacts
    for artifact_id in commit.creates_artifacts:
        artifact = artifact_registry[artifact_id]
        artifact.created_by_commit = commit.sha
        artifact.content_hash = compute_hash(artifact.paths, repo_path)
        # Artifact transitions from NOT_STARTED to IN_PROGRESS (file now exists)

    # Handle modified artifacts
    for artifact_id in commit.modifies_artifacts:
        artifact = artifact_registry[artifact_id]
        old_hash = artifact.content_hash
        artifact.content_hash = compute_hash(artifact.paths, repo_path)
        artifact.last_modified_by_commit = commit.sha

        # Check if this artifact documents another artifact
        if artifact.documents_artifact_id:
            source = artifact_registry.get(artifact.documents_artifact_id)
            if source and source.content_hash != source.last_documented_hash:
                warnings.append(
                    f"Documentation artifact {artifact_id} may be stale: "
                    f"source {artifact.documents_artifact_id} was modified"
                )

    # Handle deleted artifacts
    for artifact_id in commit.deletes_artifacts:
        artifact = artifact_registry[artifact_id]
        artifact.deleted_by_commit = commit.sha
        # Artifact transitions back to NOT_STARTED (file no longer exists)
        warnings.append(f"Artifact {artifact_id} was deleted by commit {sha[:8]}")

    # Check for orphaned documentation
    for artifact_id in commit.modifies_artifacts:
        artifact = artifact_registry[artifact_id]
        # Find documentation that references this artifact
        docs = find_documentation_for(artifact_id, artifact_registry)
        for doc in docs:
            if doc.content_hash == doc.last_checked_hash:
                # Documentation hasn't been updated since source changed
                warnings.append(
                    f"Documentation {doc.id} may need update: "
                    f"source {artifact_id} was modified"
                )

    # Link commit to tickets
    for ticket_id in commit.completes_tickets:
        ticket = load_ticket(ticket_id, repo_path)
        if ticket:
            ticket.commits_local.append(commit)
            save_ticket(ticket, repo_path)

    # Run validation
    validator = CommitArtifactValidator(artifact_registry, ticket_registry)
    validation_result = validator.validate_commit(commit)

    # Merge validation warnings
    warnings.extend(validation_result.warnings)

    return ProcessCommitResult(
        commit=commit,
        artifacts_created=commit.creates_artifacts,
        artifacts_modified=commit.modifies_artifacts,
        artifacts_deleted=commit.deletes_artifacts,
        warnings=warnings,
        validation=validation_result
    )


@dataclass
class ProcessCommitResult:
    """Result of processing a commit."""
    commit: GitCommit
    artifacts_created: List[str]
    artifacts_modified: List[str]
    artifacts_deleted: List[str]
    warnings: List[str]
    validation: Optional[CommitValidationResult] = None

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def summary(self) -> str:
        """Human-readable summary of commit processing."""
        lines = [f"Processed commit {self.commit.sha[:8]}"]

        if self.artifacts_created:
            lines.append(f"  Created: {len(self.artifacts_created)} artifacts")
        if self.artifacts_modified:
            lines.append(f"  Modified: {len(self.artifacts_modified)} artifacts")
        if self.artifacts_deleted:
            lines.append(f"  Deleted: {len(self.artifacts_deleted)} artifacts")

        if self.commit.completes_tickets:
            lines.append(f"  Completes: {self.commit.completes_tickets}")

        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings:
                lines.append(f"    - {w}")

        return "\n".join(lines)
