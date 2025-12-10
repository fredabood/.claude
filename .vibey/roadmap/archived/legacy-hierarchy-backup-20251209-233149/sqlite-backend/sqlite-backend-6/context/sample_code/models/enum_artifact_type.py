class ArtifactType(str, Enum):
    """Primary classification of artifacts."""

    # ═══════════════════════════════════════════════════════════════
    # CODE ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    CODE = "code"          # Source code (.py, .js, .ts, etc.)
    TEST = "test"          # Test files
    CONFIG = "config"      # Configuration files (.yaml, .json, .toml)

    # ═══════════════════════════════════════════════════════════════
    # DOCUMENTATION ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    DOCUMENTATION = "documentation"  # Project docs (describes current state)
    CONTEXT = "context"              # Ticket context (planning, notes, retros)

    # ═══════════════════════════════════════════════════════════════
    # FRAMEWORK ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    AGENT = "agent"        # Vibey agent definition
    WORKFLOW = "workflow"  # Vibey workflow definition
    TEMPLATE = "template"  # Handoff or rendering template

    # ═══════════════════════════════════════════════════════════════
    # OTHER ARTIFACTS
    # ═══════════════════════════════════════════════════════════════
    DATA = "data"          # Data files, fixtures, samples
    ASSET = "asset"        # Images, diagrams, media
    SCHEMA = "schema"      # API schemas, database schemas
    OTHER = "other"

    @property
    def is_documentation_type(self) -> bool:
        """True if this type represents documentation."""
        return self in {self.DOCUMENTATION, self.CONTEXT}

    @property
    def is_code_type(self) -> bool:
        """True if this type represents code."""
        return self in {self.CODE, self.TEST, self.CONFIG}

    @property
    def is_framework_type(self) -> bool:
        """True if this is a Vibey framework component."""
        return self in {self.AGENT, self.WORKFLOW, self.TEMPLATE}


class ContextArtifactSubtype(str, Enum):
    """Subtypes for CONTEXT artifacts (ticket planning/execution support)."""

    PLANNING_DOC = "planning_doc"           # Pre-work planning (design doc, RFC)
    IMPLEMENTATION_NOTES = "impl_notes"     # During-work notes
    DECISION_RECORD = "decision_record"     # ADR, design decisions
    AUDIT_REPORT = "audit_report"           # Validation/audit results
    RETROSPECTIVE = "retrospective"         # Post-work reflection


class DocumentationSubtype(str, Enum):
    """Subtypes for DOCUMENTATION artifacts (project docs)."""

    README = "readme"                # README files
    API_REFERENCE = "api_reference"  # API documentation
    USER_GUIDE = "user_guide"        # How-to guides
    ARCHITECTURE = "architecture"    # Architecture documentation
    CHANGELOG = "changelog"          # Version history
    TUTORIAL = "tutorial"            # Step-by-step tutorials
