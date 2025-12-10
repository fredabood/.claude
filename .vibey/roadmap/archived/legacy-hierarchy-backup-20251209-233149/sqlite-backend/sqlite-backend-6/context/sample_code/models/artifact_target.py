class ArtifactTarget(CriterionTarget):
    """
    Criterion target that references a first-class Artifact.

    This replaces FileExistsTarget for artifact-based criteria.
    FileExistsTarget is retained for cases where you want to check
    file existence without creating an Artifact entity.
    """

    artifact_id: str  # References Artifact.id

    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION MODE
    # ═══════════════════════════════════════════════════════════════
    verification: ArtifactVerification = ArtifactVerification.EXISTS

    # ═══════════════════════════════════════════════════════════════
    # CACHED STATE (denormalized from Artifact for performance)
    # ═══════════════════════════════════════════════════════════════
    artifact_exists: bool = False
    artifact_hash: Optional[str] = None
    artifact_is_stale: bool = False
    last_checked: Optional[datetime] = None

    @property
    def is_automatic(self) -> bool:
        return True

    def is_satisfied(self) -> bool:
        """Check if criterion is satisfied based on verification mode."""
        if self.verification == ArtifactVerification.EXISTS:
            return self.artifact_exists

        elif self.verification == ArtifactVerification.NOT_STALE:
            return self.artifact_exists and not self.artifact_is_stale

        elif self.verification == ArtifactVerification.HASH_UNCHANGED:
            # For checking that artifact content hasn't changed
            artifact = self._load_artifact()
            return (
                self.artifact_exists and
                artifact and
                artifact.content_hash == self.artifact_hash
            )

        return False

    def refresh(self, context: "RefreshContext") -> None:
        """Refresh cached state from artifact registry."""
        artifact = context.artifact_registry.get(self.artifact_id)

        if artifact:
            self.artifact_exists = artifact.exists
            self.artifact_hash = artifact.content_hash
            self.artifact_is_stale = artifact.is_stale
        else:
            self.artifact_exists = False
            self.artifact_hash = None
            self.artifact_is_stale = False

        self.last_checked = datetime.now(timezone.utc)


class ArtifactVerification(str, Enum):
    """How to verify an artifact criterion is satisfied."""

    EXISTS = "exists"              # Files exist (default)
    NOT_STALE = "not_stale"        # Exists AND not stale (for documentation)
    HASH_UNCHANGED = "hash_unchanged"  # Content hasn't changed since criterion created
