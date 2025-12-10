class ArtifactProvenance(BaseModel):
    """
    How an artifact came to exist.

    Provenance enables:
    - Distinguishing ticket-created vs pre-existing files
    - Tracking generated documentation sources
    - Identifying framework components
    """

    provenance_type: ProvenanceType

    # ═══════════════════════════════════════════════════════════════
    # FOR TICKET_CREATED
    # ═══════════════════════════════════════════════════════════════
    created_by_ticket_id: Optional[str] = None
    created_by_criterion_id: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # FOR PRE_EXISTING
    # ═══════════════════════════════════════════════════════════════
    discovered_at: Optional[datetime] = None
    discovered_by: Optional[str] = None  # User, scan process, or "filesystem_scan"

    # ═══════════════════════════════════════════════════════════════
    # FOR GENERATED
    # ═══════════════════════════════════════════════════════════════
    generator_type: Optional[str] = None  # "sphinx", "pdoc", "typedoc", "mkdocs"
    generator_config: Optional[Dict[str, Any]] = None
    source_artifact_ids: Optional[List[str]] = None  # Artifacts used to generate this

    # ═══════════════════════════════════════════════════════════════
    # FOR EXTERNAL
    # ═══════════════════════════════════════════════════════════════
    external_source: Optional[str] = None  # URL, package name, etc.
    external_version: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════
    # FOR FRAMEWORK
    # ═══════════════════════════════════════════════════════════════
    framework_component_type: Optional[str] = None  # "agent", "workflow", "template"


class ProvenanceType(str, Enum):
    """How an artifact came to exist."""

    TICKET_CREATED = "ticket_created"  # Created by a ticket's work
    PRE_EXISTING = "pre_existing"      # Existed before roadmap system
    GENERATED = "generated"            # Auto-generated from other artifacts
    EXTERNAL = "external"              # From external source (vendored, fetched)
    FRAMEWORK = "framework"            # Vibey framework component
