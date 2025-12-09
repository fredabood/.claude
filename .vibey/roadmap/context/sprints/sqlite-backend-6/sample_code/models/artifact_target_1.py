class ArtifactTarget(CriterionTarget):
    artifact_id: str                     # References Artifact.id
    verification: ArtifactVerification = ArtifactVerification.EXISTS

    # Cached state (denormalized from Artifact)
    artifact_exists: bool = False
    artifact_hash: Optional[str]
    artifact_is_stale: bool = False
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
