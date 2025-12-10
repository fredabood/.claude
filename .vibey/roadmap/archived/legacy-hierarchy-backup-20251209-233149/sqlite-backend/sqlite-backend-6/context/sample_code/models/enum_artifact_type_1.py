class ArtifactType(str, Enum):
    """Primary classification of artifacts."""
    CODE = "code"
    TEST = "test"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    CONTEXT = "context"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    DATA = "data"
    ASSET = "asset"
    SCHEMA = "schema"
    OTHER = "other"


class ContextArtifactSubtype(str, Enum):
    """Subtypes for CONTEXT artifacts."""
    PLANNING_DOC = "planning_doc"
    IMPLEMENTATION_NOTES = "impl_notes"
    DECISION_RECORD = "decision_record"
    AUDIT_REPORT = "audit_report"
    RETROSPECTIVE = "retrospective"


class DocumentationSubtype(str, Enum):
    """Subtypes for DOCUMENTATION artifacts."""
    README = "readme"
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    ARCHITECTURE = "architecture"
    CHANGELOG = "changelog"
    TUTORIAL = "tutorial"


class ProvenanceType(str, Enum):
    """How an artifact came to exist."""
    TICKET_CREATED = "ticket_created"
    PRE_EXISTING = "pre_existing"
    GENERATED = "generated"
    EXTERNAL = "external"
    FRAMEWORK = "framework"


class ArtifactVerification(str, Enum):
    """How to verify an artifact criterion is satisfied."""
    EXISTS = "exists"
    NOT_STALE = "not_stale"
    HASH_UNCHANGED = "hash_unchanged"


class DocumentationHealth(str, Enum):
    """Documentation health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
