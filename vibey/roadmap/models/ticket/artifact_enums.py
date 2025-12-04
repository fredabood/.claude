"""
Artifact System Enums for the Unified Ticket Architecture.

This module defines enum types for the artifact system, which provides
first-class representation of files tracked by the roadmap system.

Design Reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13, Appendix E
"""

from enum import Enum


# =============================================================================
# ARTIFACT TYPE ENUMS
# =============================================================================


class ArtifactType(str, Enum):
    """
    Primary classification of artifacts.

    Categorizes files by their semantic purpose in the codebase.

    Properties:
        is_documentation_type: True for DOCUMENTATION, CONTEXT
        is_code_type: True for CODE, TEST, CONFIG
        is_framework_type: True for AGENT, WORKFLOW, TEMPLATE
    """

    CODE = "code"  # Source code (.py, .js, .ts, etc.)
    TEST = "test"  # Test files
    CONFIG = "config"  # Configuration files (.yaml, .json, .toml)
    DOCUMENTATION = "documentation"  # Project docs (describes current state)
    CONTEXT = "context"  # Ticket context (planning, notes, retros)
    AGENT = "agent"  # Vibey agent definition
    WORKFLOW = "workflow"  # Vibey workflow definition
    TEMPLATE = "template"  # Handoff or rendering template
    DATA = "data"  # Data files, fixtures, samples
    ASSET = "asset"  # Images, diagrams, media
    SCHEMA = "schema"  # API schemas, database schemas
    OTHER = "other"  # Catch-all for uncategorized files

    @property
    def is_documentation_type(self) -> bool:
        """Check if this artifact type is documentation-related."""
        return self in (self.DOCUMENTATION, self.CONTEXT)

    @property
    def is_code_type(self) -> bool:
        """Check if this artifact type is code-related."""
        return self in (self.CODE, self.TEST, self.CONFIG)

    @property
    def is_framework_type(self) -> bool:
        """Check if this artifact type is a Vibey framework component."""
        return self in (self.AGENT, self.WORKFLOW, self.TEMPLATE)

    @classmethod
    def from_extension(cls, extension: str) -> "ArtifactType":
        """
        Infer artifact type from file extension.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            Best-guess ArtifactType based on extension
        """
        ext = extension.lower().lstrip(".")

        # Code files
        if ext in ("py", "js", "ts", "jsx", "tsx", "go", "rs", "java", "cpp", "c", "h"):
            return cls.CODE

        # Test files (detected by filename, not extension - this is a fallback)
        if ext in ("test.py", "spec.js", "test.ts"):
            return cls.TEST

        # Config files
        if ext in ("yaml", "yml", "json", "toml", "ini", "cfg", "conf"):
            return cls.CONFIG

        # Documentation
        if ext in ("md", "rst", "txt", "adoc"):
            return cls.DOCUMENTATION

        # Schema files
        if ext in ("xsd", "graphql", "proto", "avsc"):
            return cls.SCHEMA

        # Asset files
        if ext in ("png", "jpg", "jpeg", "gif", "svg", "ico", "webp", "pdf"):
            return cls.ASSET

        # Data files
        if ext in ("csv", "tsv", "parquet", "sqlite", "db"):
            return cls.DATA

        return cls.OTHER


class ProvenanceType(str, Enum):
    """
    How an artifact came to exist.

    Tracks the origin/creation context of an artifact.
    """

    TICKET_CREATED = "ticket_created"  # Created by a ticket's work
    PRE_EXISTING = "pre_existing"  # Existed before roadmap system
    GENERATED = "generated"  # Auto-generated from other artifacts
    EXTERNAL = "external"  # From external source (vendored, fetched)
    FRAMEWORK = "framework"  # Vibey framework component

    @property
    def is_tracked(self) -> bool:
        """Check if this provenance type indicates ticket-tracked work."""
        return self == self.TICKET_CREATED

    @property
    def is_auto_generated(self) -> bool:
        """Check if artifact was auto-generated."""
        return self == self.GENERATED


class ArtifactVerification(str, Enum):
    """
    How to verify an artifact criterion is satisfied.

    Controls the verification strategy for artifact-based criteria.
    """

    EXISTS = "exists"  # Files exist (default)
    NOT_STALE = "not_stale"  # Exists AND not stale (for documentation)
    HASH_UNCHANGED = "hash_unchanged"  # Content hasn't changed since criterion created

    @classmethod
    def default(cls) -> "ArtifactVerification":
        """Return the default verification mode."""
        return cls.EXISTS

    @property
    def checks_staleness(self) -> bool:
        """Check if this verification mode considers staleness."""
        return self == self.NOT_STALE

    @property
    def is_content_aware(self) -> bool:
        """Check if this verification mode considers file content."""
        return self in (self.NOT_STALE, self.HASH_UNCHANGED)


# =============================================================================
# ARTIFACT SUBTYPE ENUMS
# =============================================================================


class ContextArtifactSubtype(str, Enum):
    """
    Subtypes for CONTEXT artifacts.

    Provides finer classification of ticket context files.
    """

    PLANNING_DOC = "planning_doc"  # Pre-work planning (design doc, RFC)
    IMPLEMENTATION_NOTES = "impl_notes"  # During-work notes
    DECISION_RECORD = "decision_record"  # ADR, design decisions
    AUDIT_REPORT = "audit_report"  # Validation/audit results
    RETROSPECTIVE = "retrospective"  # Post-work reflection

    @property
    def is_pre_work(self) -> bool:
        """Check if this is pre-implementation context."""
        return self in (self.PLANNING_DOC, self.DECISION_RECORD)

    @property
    def is_during_work(self) -> bool:
        """Check if this is during-implementation context."""
        return self == self.IMPLEMENTATION_NOTES

    @property
    def is_post_work(self) -> bool:
        """Check if this is post-implementation context."""
        return self in (self.AUDIT_REPORT, self.RETROSPECTIVE)


class DocumentationSubtype(str, Enum):
    """
    Subtypes for DOCUMENTATION artifacts.

    Provides finer classification of project documentation files.
    """

    README = "readme"  # README files
    API_REFERENCE = "api_reference"  # API documentation
    USER_GUIDE = "user_guide"  # How-to guides
    ARCHITECTURE = "architecture"  # Architecture documentation
    CHANGELOG = "changelog"  # Version history
    TUTORIAL = "tutorial"  # Step-by-step tutorials

    @property
    def is_reference(self) -> bool:
        """Check if this is reference documentation."""
        return self in (self.API_REFERENCE, self.README)

    @property
    def is_guide(self) -> bool:
        """Check if this is guide-style documentation."""
        return self in (self.USER_GUIDE, self.TUTORIAL)


# =============================================================================
# DOCUMENTATION HEALTH ENUMS
# =============================================================================


class DocumentationHealth(str, Enum):
    """
    Aggregate documentation health status.

    Represents the overall state of documentation for a ticket.
    """

    HEALTHY = "healthy"  # All docs current
    DEGRADED = "degraded"  # Some docs stale (non-blocking)
    CRITICAL = "critical"  # Stale docs blocking completion

    @property
    def is_healthy(self) -> bool:
        """Check if documentation is fully healthy."""
        return self == self.HEALTHY

    @property
    def is_blocking(self) -> bool:
        """Check if documentation status is blocking."""
        return self == self.CRITICAL

    @classmethod
    def from_stale_count(cls, stale: int, blocking: int) -> "DocumentationHealth":
        """
        Determine health from staleness counts.

        Args:
            stale: Number of stale documentation artifacts
            blocking: Number of stale artifacts that are blocking

        Returns:
            Appropriate DocumentationHealth status
        """
        if blocking > 0:
            return cls.CRITICAL
        elif stale > 0:
            return cls.DEGRADED
        return cls.HEALTHY


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Primary classification
    "ArtifactType",
    # Provenance
    "ProvenanceType",
    # Verification
    "ArtifactVerification",
    # Subtypes
    "ContextArtifactSubtype",
    "DocumentationSubtype",
    # Health
    "DocumentationHealth",
]
