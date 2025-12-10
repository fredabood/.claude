class Artifact(BaseModel):
    # Identity
    id: str                              # ULID format
    name: str
    description: Optional[str]

    # File Location
    paths: List[str]                     # One artifact may span multiple files
    content_hash: Optional[str]          # SHA256 of concatenated contents
    last_verified: Optional[datetime]

    # Classification
    artifact_type: ArtifactType
    artifact_subtype: Optional[str]

    # Provenance
    provenance: ArtifactProvenance

    # Relationships
    documents_artifact_id: Optional[str] # What this artifact documents
    depends_on_artifact_ids: List[str]

    # State
    exists: bool = True
    is_stale: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Computed Properties
    @computed_field
    def is_orphan(self) -> bool: ...

    @computed_field
    def referencing_criteria(self) -> List[str]: ...

    @computed_field
    def is_documentation(self) -> bool: ...

    # Methods
    def check_staleness(self, registry) -> bool: ...
    def mark_updated(self, registry) -> None: ...
