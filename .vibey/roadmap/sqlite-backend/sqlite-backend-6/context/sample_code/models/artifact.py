class Artifact(BaseModel):
    """
    A first-class entity representing any file-based artifact in the project.

    Artifacts exist independently of tickets. They may be:
    - Created by a ticket (provenance.type = TICKET_CREATED)
    - Pre-existing (provenance.type = PRE_EXISTING)
    - Generated from other artifacts (provenance.type = GENERATED)
    - From external sources (provenance.type = EXTERNAL)
    - Vibey framework components (provenance.type = FRAMEWORK)
    """

    # ═══════════════════════════════════════════════════════════════
    # IDENTITY
    # ═══════════════════════════════════════════════════════════════
    id: str  # ULID
    name: str
    description: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # FILE LOCATION
    # ═══════════════════════════════════════════════════════════════
    paths: List[str]  # One artifact may span multiple files
    content_hash: Optional[str] = None  # SHA256 of concatenated file contents
    last_verified: Optional[datetime] = None  # When files were last checked

    # ═══════════════════════════════════════════════════════════════
    # CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════
    artifact_type: ArtifactType
    artifact_subtype: Optional[str] = None  # More specific classification

    # ═══════════════════════════════════════════════════════════════
    # PROVENANCE
    # ═══════════════════════════════════════════════════════════════
    provenance: ArtifactProvenance

    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════

    # Documentation relationship: what does this artifact document?
    documents_artifact_id: Optional[str] = None

    # Dependency relationships: what artifacts does this depend on?
    depends_on_artifact_ids: List[str] = Field(default_factory=list)

    # ═══════════════════════════════════════════════════════════════
    # STATE
    # ═══════════════════════════════════════════════════════════════
    exists: bool = True  # False if files were deleted
    is_stale: bool = False  # For docs: source artifact changed since last update

    # ═══════════════════════════════════════════════════════════════
    # GIT COMMIT TRACKING
    # ═══════════════════════════════════════════════════════════════
    created_by_commit: Optional[str] = None      # SHA of commit that created file(s)
    last_modified_by_commit: Optional[str] = None  # SHA of most recent modifying commit
    deleted_by_commit: Optional[str] = None      # SHA of commit that deleted file(s)
    commit_history: List[str] = Field(default_factory=list)  # All commit SHAs that touched this

    # For documentation artifacts: track what version of source was documented
    documented_source_hash: Optional[str] = None  # Hash of source when docs were written

    # ═══════════════════════════════════════════════════════════════
    # TIMESTAMPS
    # ═══════════════════════════════════════════════════════════════
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ═══════════════════════════════════════════════════════════════
    # COMPUTED PROPERTIES
    # ═══════════════════════════════════════════════════════════════

    @computed_field
    def is_orphan(self) -> bool:
        """True if no criteria reference this artifact."""
        # Computed via database query in repository
        return self._check_orphan_status()

    @computed_field
    def referencing_criteria(self) -> List[str]:
        """Criterion IDs that reference this artifact."""
        # Computed via database query in repository
        return self._get_referencing_criteria()

    @computed_field
    def is_documentation(self) -> bool:
        """True if this artifact documents another artifact."""
        return self.documents_artifact_id is not None

    # ═══════════════════════════════════════════════════════════════
    # STALENESS DETECTION
    # ═══════════════════════════════════════════════════════════════

    def check_staleness(self, artifact_registry: "ArtifactRegistry") -> bool:
        """
        Check if this documentation artifact is stale.

        Returns True if the documented artifact has changed since this
        artifact was last updated.
        """
        if not self.documents_artifact_id:
            return False  # Not documentation, can't be stale

        source = artifact_registry.get(self.documents_artifact_id)
        if not source:
            return True  # Source doesn't exist - definitely stale

        # Compare source's current hash to what we documented
        if source.content_hash != self.documented_source_hash:
            self.is_stale = True
            return True

        self.is_stale = False
        return False

    def mark_updated(self, artifact_registry: "ArtifactRegistry") -> None:
        """
        Mark this documentation as updated (no longer stale).

        Captures the current hash of the documented artifact.
        """
        if self.documents_artifact_id:
            source = artifact_registry.get(self.documents_artifact_id)
            if source:
                self.documented_source_hash = source.content_hash

        self.is_stale = False
        self.updated_at = datetime.now(timezone.utc)

    def record_commit(self, commit_sha: str, action: str) -> None:
        """
        Record a commit that affected this artifact.

        Args:
            commit_sha: The git commit SHA
            action: One of 'create', 'modify', 'delete'
        """
        if action == 'create':
            self.created_by_commit = commit_sha
            self.exists = True
        elif action == 'modify':
            self.last_modified_by_commit = commit_sha
        elif action == 'delete':
            self.deleted_by_commit = commit_sha
            self.exists = False

        if commit_sha not in self.commit_history:
            self.commit_history.append(commit_sha)

        self.updated_at = datetime.now(timezone.utc)
