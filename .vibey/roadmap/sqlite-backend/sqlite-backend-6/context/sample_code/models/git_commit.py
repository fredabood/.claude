class GitCommit(BaseModel):
    """A git commit with platform, completion, and file tracking metadata."""

    sha: str  # Full 40-char SHA
    message: str
    date: datetime
    author: str

    # Platform tracking
    platform: str  # claude-code, goose, cursor, etc.
    submitted_at: datetime

    # Extracted from message (parsed on load)
    completes_tickets: List[str] = Field(default_factory=list)

    # File changes (from git diff-tree)
    files_added: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    files_deleted: List[str] = Field(default_factory=list)

    # Artifact links (computed by matching paths to registered artifacts)
    creates_artifacts: List[str] = Field(default_factory=list)    # Artifact IDs
    modifies_artifacts: List[str] = Field(default_factory=list)   # Artifact IDs
    deletes_artifacts: List[str] = Field(default_factory=list)    # Artifact IDs

    @property
    def all_changed_files(self) -> List[str]:
        """All files touched by this commit."""
        return self.files_added + self.files_modified + self.files_deleted

    @property
    def all_affected_artifacts(self) -> List[str]:
        """All artifacts affected by this commit."""
        return self.creates_artifacts + self.modifies_artifacts + self.deletes_artifacts

    @classmethod
    def from_git(cls, sha: str, repo_path: Path, platform: str) -> "GitCommit":
        """Parse git commit and extract all metadata."""
        # Get commit metadata
        result = subprocess.run(
            ["git", "show", "-s", "--format=%H%n%s%n%b%n%aI%n%an", sha],
            cwd=repo_path, capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        full_sha, subject, *body_lines, date_str, author = lines
        body = '\n'.join(body_lines)

        # Extract "Completes: ticket-id" markers
        completes = []
        for line in body.split('\n'):
            if line.startswith('Completes:'):
                ticket_id = line.replace('Completes:', '').strip()
                completes.append(ticket_id)

        # Get file changes (A=added, M=modified, D=deleted)
        diff_result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", sha],
            cwd=repo_path, capture_output=True, text=True
        )

        added, modified, deleted = [], [], []
        for line in diff_result.stdout.strip().split('\n'):
            if not line:
                continue
            status, *path_parts = line.split('\t')
            path = path_parts[0] if path_parts else ""
            if status == 'A':
                added.append(path)
            elif status == 'M':
                modified.append(path)
            elif status == 'D':
                deleted.append(path)

        return cls(
            sha=full_sha,
            message=f"{subject}\n\n{body}".strip(),
            date=datetime.fromisoformat(date_str),
            author=author,
            platform=platform,
            submitted_at=datetime.now(timezone.utc),
            completes_tickets=completes,
            files_added=added,
            files_modified=modified,
            files_deleted=deleted,
            # Artifact links computed separately via link_to_artifacts()
        )

    def link_to_artifacts(self, artifact_registry: Dict[str, "Artifact"]) -> None:
        """
        Match file changes to registered artifacts.

        Called after from_git() with the artifact registry to establish links.
        """
        creates, modifies, deletes = [], [], []

        for artifact_id, artifact in artifact_registry.items():
            artifact_paths = set(artifact.paths)

            # Check if any added files match this artifact
            if artifact_paths & set(self.files_added):
                creates.append(artifact_id)

            # Check if any modified files match this artifact
            elif artifact_paths & set(self.files_modified):
                modifies.append(artifact_id)

            # Check if any deleted files match this artifact
            elif artifact_paths & set(self.files_deleted):
                deletes.append(artifact_id)

        self.creates_artifacts = creates
        self.modifies_artifacts = modifies
        self.deletes_artifacts = deletes
