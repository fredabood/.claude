"""
Artifact Entity for the Unified Ticket Architecture.

This module defines the Artifact entity as a first-class entity independent
of tickets. Artifacts represent any file-based component in the project.

Design Reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.3
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
import hashlib

from pydantic import BaseModel, Field

from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactType,
    ProvenanceType,
)


# =============================================================================
# ARTIFACT REGISTRY PROTOCOL
# =============================================================================


class ArtifactRegistry(Protocol):
    """
    Protocol for artifact lookup.

    Used by staleness detection to find related artifacts.
    """

    def get(self, artifact_id: str) -> Optional["Artifact"]:
        """Get an artifact by ID."""
        ...

    def get_referencing_criteria(self, artifact_id: str) -> List[str]:
        """Get criterion IDs that reference this artifact."""
        ...


# =============================================================================
# ARTIFACT PROVENANCE
# =============================================================================


class ArtifactProvenance(BaseModel):
    """
    How an artifact came to exist.

    Provenance enables:
    - Distinguishing ticket-created vs pre-existing files
    - Tracking generated documentation sources
    - Identifying framework components

    Design Reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.4
    """

    provenance_type: ProvenanceType

    # For TICKET_CREATED
    created_by_ticket_id: Optional[str] = None
    created_by_criterion_id: Optional[str] = None

    # For PRE_EXISTING
    discovered_at: Optional[datetime] = None
    discovered_by: Optional[str] = None  # User, scan process, or "filesystem_scan"

    # For GENERATED
    generator_type: Optional[str] = None  # "sphinx", "pdoc", "typedoc", "mkdocs"
    generator_config: Optional[Dict[str, Any]] = None
    source_artifact_ids: Optional[List[str]] = None  # Artifacts used to generate this

    # For EXTERNAL
    external_source: Optional[str] = None  # URL, package name, etc.
    external_version: Optional[str] = None

    # For FRAMEWORK
    framework_component_type: Optional[str] = None  # "agent", "workflow", "template"

    @classmethod
    def ticket_created(
        cls,
        ticket_id: str,
        criterion_id: Optional[str] = None,
    ) -> "ArtifactProvenance":
        """Create provenance for an artifact created by a ticket."""
        return cls(
            provenance_type=ProvenanceType.TICKET_CREATED,
            created_by_ticket_id=ticket_id,
            created_by_criterion_id=criterion_id,
        )

    @classmethod
    def pre_existing(
        cls,
        discovered_by: str = "filesystem_scan",
    ) -> "ArtifactProvenance":
        """Create provenance for a pre-existing artifact."""
        return cls(
            provenance_type=ProvenanceType.PRE_EXISTING,
            discovered_at=datetime.now(timezone.utc),
            discovered_by=discovered_by,
        )

    @classmethod
    def generated(
        cls,
        generator_type: str,
        source_artifact_ids: Optional[List[str]] = None,
        generator_config: Optional[Dict[str, Any]] = None,
    ) -> "ArtifactProvenance":
        """Create provenance for a generated artifact."""
        return cls(
            provenance_type=ProvenanceType.GENERATED,
            generator_type=generator_type,
            source_artifact_ids=source_artifact_ids or [],
            generator_config=generator_config,
        )

    @classmethod
    def external(
        cls,
        source: str,
        version: Optional[str] = None,
    ) -> "ArtifactProvenance":
        """Create provenance for an external artifact."""
        return cls(
            provenance_type=ProvenanceType.EXTERNAL,
            external_source=source,
            external_version=version,
        )

    @classmethod
    def framework(
        cls,
        component_type: str,
    ) -> "ArtifactProvenance":
        """Create provenance for a framework component."""
        return cls(
            provenance_type=ProvenanceType.FRAMEWORK,
            framework_component_type=component_type,
        )


# =============================================================================
# ARTIFACT ENTITY
# =============================================================================


class Artifact(BaseModel):
    """
    A first-class entity representing any file-based artifact in the project.

    Artifacts exist independently of tickets. They may be:
    - Created by a ticket (provenance.type = TICKET_CREATED)
    - Pre-existing (provenance.type = PRE_EXISTING)
    - Generated from other artifacts (provenance.type = GENERATED)
    - From external sources (provenance.type = EXTERNAL)
    - Vibey framework components (provenance.type = FRAMEWORK)

    Design Reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.3
    """

    # =========================================================================
    # IDENTITY
    # =========================================================================
    id: str  # ULID
    name: str
    description: Optional[str] = None

    # =========================================================================
    # FILE LOCATION
    # =========================================================================
    paths: List[str]  # One artifact may span multiple files
    content_hash: Optional[str] = None  # SHA256 of concatenated file contents
    last_verified: Optional[datetime] = None  # When files were last checked

    # =========================================================================
    # CLASSIFICATION
    # =========================================================================
    artifact_type: ArtifactType
    artifact_subtype: Optional[str] = None  # More specific classification

    # =========================================================================
    # PROVENANCE
    # =========================================================================
    provenance: ArtifactProvenance

    # =========================================================================
    # RELATIONSHIPS
    # =========================================================================
    # Documentation relationship: what does this artifact document?
    documents_artifact_id: Optional[str] = None

    # Dependency relationships: what artifacts does this depend on?
    depends_on_artifact_ids: List[str] = Field(default_factory=list)

    # =========================================================================
    # STATE
    # =========================================================================
    exists: bool = True  # False if files were deleted
    is_stale: bool = False  # For docs: source artifact changed since last update

    # =========================================================================
    # TIMESTAMPS
    # =========================================================================
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # =========================================================================
    # PRIVATE STATE (for staleness tracking)
    # =========================================================================
    _documented_source_hash: Optional[str] = None

    # Internal registry reference for computed properties
    _registry: Optional[ArtifactRegistry] = None

    model_config = {
        "arbitrary_types_allowed": True,
    }

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def is_documentation(self) -> bool:
        """True if this artifact documents another artifact."""
        return self.documents_artifact_id is not None

    @property
    def is_orphan(self) -> bool:
        """
        True if no criteria reference this artifact.

        Note: This requires a registry to be set. Returns False if no registry.
        """
        if self._registry is None:
            return False
        return len(self._registry.get_referencing_criteria(self.id)) == 0

    @property
    def referencing_criteria(self) -> List[str]:
        """
        Criterion IDs that reference this artifact.

        Note: This requires a registry to be set. Returns empty list if no registry.
        """
        if self._registry is None:
            return []
        return self._registry.get_referencing_criteria(self.id)

    # =========================================================================
    # STALENESS DETECTION
    # =========================================================================

    def check_staleness(self, registry: ArtifactRegistry) -> bool:
        """
        Check if this documentation artifact is stale.

        Returns True if the documented artifact has changed since this
        artifact was last updated.

        Args:
            registry: Registry to look up the documented artifact

        Returns:
            True if stale, False otherwise
        """
        if not self.documents_artifact_id:
            return False  # Not documentation, can't be stale

        source = registry.get(self.documents_artifact_id)
        if not source:
            self.is_stale = True
            return True  # Source doesn't exist - definitely stale

        # Compare source's current hash to what we documented
        if source.content_hash != self._documented_source_hash:
            self.is_stale = True
            return True

        self.is_stale = False
        return False

    def mark_updated(self, registry: ArtifactRegistry) -> None:
        """
        Mark this documentation as updated (no longer stale).

        Captures the current hash of the documented artifact.

        Args:
            registry: Registry to look up the documented artifact
        """
        if self.documents_artifact_id:
            source = registry.get(self.documents_artifact_id)
            if source:
                self._documented_source_hash = source.content_hash

        self.is_stale = False
        self.updated_at = datetime.now(timezone.utc)

    # =========================================================================
    # CONTENT HASH
    # =========================================================================

    def compute_content_hash(self, base_path: Optional[Path] = None) -> str:
        """
        Compute SHA256 hash of all files in paths[].

        Files are sorted and concatenated before hashing for determinism.

        Args:
            base_path: Optional base path to resolve relative paths

        Returns:
            SHA256 hex digest of concatenated file contents

        Raises:
            FileNotFoundError: If any file in paths doesn't exist
        """
        hasher = hashlib.sha256()

        # Sort paths for deterministic ordering
        sorted_paths = sorted(self.paths)

        for path_str in sorted_paths:
            path = Path(path_str)
            if base_path:
                path = base_path / path

            if not path.exists():
                raise FileNotFoundError(f"Artifact file not found: {path}")

            if path.is_file():
                with open(path, "rb") as f:
                    # Hash in chunks for memory efficiency
                    for chunk in iter(lambda: f.read(8192), b""):
                        hasher.update(chunk)

        return hasher.hexdigest()

    def refresh_content_hash(self, base_path: Optional[Path] = None) -> bool:
        """
        Refresh the content hash and update last_verified.

        Args:
            base_path: Optional base path to resolve relative paths

        Returns:
            True if hash changed, False if unchanged
        """
        try:
            new_hash = self.compute_content_hash(base_path)
            changed = new_hash != self.content_hash
            self.content_hash = new_hash
            self.last_verified = datetime.now(timezone.utc)
            self.exists = True
            return changed
        except FileNotFoundError:
            self.exists = False
            return True  # Changed (from existing to not existing)

    # =========================================================================
    # FILE EXISTENCE VERIFICATION
    # =========================================================================

    def verify_exists(self, base_path: Optional[Path] = None) -> bool:
        """
        Check if all files in paths[] exist on filesystem.

        Args:
            base_path: Optional base path to resolve relative paths

        Returns:
            True if all files exist, False otherwise
        """
        for path_str in self.paths:
            path = Path(path_str)
            if base_path:
                path = base_path / path

            if not path.exists():
                self.exists = False
                return False

        self.exists = True
        self.last_verified = datetime.now(timezone.utc)
        return True

    def get_missing_paths(self, base_path: Optional[Path] = None) -> List[str]:
        """
        Get list of paths that don't exist.

        Args:
            base_path: Optional base path to resolve relative paths

        Returns:
            List of missing path strings
        """
        missing = []
        for path_str in self.paths:
            path = Path(path_str)
            if base_path:
                path = base_path / path

            if not path.exists():
                missing.append(path_str)

        return missing

    # =========================================================================
    # REGISTRY BINDING
    # =========================================================================

    def bind_registry(self, registry: ArtifactRegistry) -> None:
        """
        Bind a registry for computed property lookups.

        Args:
            registry: The artifact registry to use for lookups
        """
        object.__setattr__(self, "_registry", registry)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ArtifactRegistry",
    "ArtifactProvenance",
    "Artifact",
]
