"""
Core content versioning infrastructure for task implementation.

This module provides the fundamental versioning system for tracking
content changes across the implementation lifecycle (plan, execution, post-mortem).

Key Components:
- ContentVersion: Immutable version of content at a point in time
- VersionStage: Enum for lifecycle stages
- ContentVersioner: Service for creating and managing versions

Storage Structure:
    .vibey/roadmap/versions/
    └── {ticket_id}/
        ├── plan/
        │   ├── {version_id}.yaml
        │   └── current.yaml -> {latest_version_id}.yaml
        ├── execution/
        │   └── ...
        └── post_mortem/
            └── ...

Design Reference:
- Implementation Mode Track Sprint
- Task: Implement ContentVersioner core versioning system
"""

import hashlib
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from ulid import ULID

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class VersionStage(str, Enum):
    """
    Stage in the implementation lifecycle.

    Values:
        PLAN: Planning and design phase
        EXECUTION: Active implementation phase
        POST_MORTEM: Review and learning phase
    """

    PLAN = "plan"
    EXECUTION = "execution"
    POST_MORTEM = "post_mortem"


# =============================================================================
# CONTENT VERSION
# =============================================================================


@dataclass
class ContentVersion:
    """
    Immutable version of content at a point in time.

    Represents a snapshot of content (plan, execution state, post-mortem)
    at a specific moment, with full provenance tracking.

    Attributes:
        version_id: Unique identifier for this version (ULID)
        ticket_id: ID of the ticket this version belongs to
        stage: Which stage of implementation (plan, execution, post_mortem)
        content_hash: SHA256 hash of the content for change detection
        content: Full content snapshot
        timestamp: When this version was created
        author: Agent ID or user who created this version
        parent_version: Previous version ID (None for first version)
        change_summary: Human-readable summary of what changed
        metadata: Additional context-specific metadata

    Example:
        >>> version = ContentVersion(
        ...     version_id=str(ULID()),
        ...     ticket_id="01KCZF73PX9YNKWXKYVARY89N3",
        ...     stage=VersionStage.PLAN,
        ...     content_hash="abc123...",
        ...     content="Plan content here...",
        ...     timestamp=datetime.now(timezone.utc),
        ...     author="claude-code",
        ... )
    """

    version_id: str
    ticket_id: str
    stage: VersionStage
    content_hash: str
    content: str
    timestamp: datetime
    author: str
    parent_version: Optional[str] = None
    change_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for YAML serialization.
        """
        return {
            "version_id": self.version_id,
            "ticket_id": self.ticket_id,
            "stage": self.stage.value,
            "content_hash": self.content_hash,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author,
            "parent_version": self.parent_version,
            "change_summary": self.change_summary,
            "metadata": self.metadata,
        }

    def to_yaml(self) -> str:
        """
        Serialize version to YAML.

        Returns:
            YAML string representation of this version.
        """
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentVersion":
        """
        Create ContentVersion from dictionary.

        Args:
            data: Dictionary with version data.

        Returns:
            ContentVersion instance.
        """
        # Parse timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Parse stage
        stage_str = data.get("stage", "plan")
        try:
            stage = VersionStage(stage_str)
        except ValueError:
            stage = VersionStage.PLAN

        return cls(
            version_id=data.get("version_id", str(ULID())),
            ticket_id=data.get("ticket_id", ""),
            stage=stage,
            content_hash=data.get("content_hash", ""),
            content=data.get("content", ""),
            timestamp=timestamp,
            author=data.get("author", "unknown"),
            parent_version=data.get("parent_version"),
            change_summary=data.get("change_summary"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ContentVersion":
        """
        Deserialize from YAML.

        Args:
            yaml_str: YAML string representation.

        Returns:
            ContentVersion instance.
        """
        data = yaml.safe_load(yaml_str)
        if data is None:
            data = {}
        return cls.from_dict(data)

    @property
    def is_first_version(self) -> bool:
        """Check if this is the first version (no parent)."""
        return self.parent_version is None


# =============================================================================
# CONTENT VERSIONER
# =============================================================================


class ContentVersioner:
    """
    Service for creating and managing content versions.

    ContentVersioner provides the core versioning infrastructure for
    tracking changes to content across the implementation lifecycle.

    Attributes:
        versions_root: Root directory for storing versions

    Example:
        >>> versioner = ContentVersioner(Path(".vibey/roadmap/versions"))
        >>> version = versioner.create_version(
        ...     ticket_id="01KCZF73PX9YNKWXKYVARY89N3",
        ...     stage=VersionStage.PLAN,
        ...     content="Plan content...",
        ...     author="claude-code",
        ... )
    """

    def __init__(self, versions_root: Path):
        """
        Initialize ContentVersioner.

        Args:
            versions_root: Root directory for version storage.
        """
        self.versions_root = versions_root

    def _get_stage_dir(self, ticket_id: str, stage: VersionStage) -> Path:
        """Get the directory for a ticket's stage versions."""
        return self.versions_root / ticket_id / stage.value

    def _get_version_path(
        self, ticket_id: str, stage: VersionStage, version_id: str
    ) -> Path:
        """Get the path for a specific version file."""
        return self._get_stage_dir(ticket_id, stage) / f"{version_id}.yaml"

    def _get_current_link_path(self, ticket_id: str, stage: VersionStage) -> Path:
        """Get the path for the current version link/file."""
        return self._get_stage_dir(ticket_id, stage) / "current.yaml"

    def create_version(
        self,
        ticket_id: str,
        stage: VersionStage,
        content: str,
        author: str,
        change_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContentVersion:
        """
        Create new version of content.

        Process:
        1. Compute content hash
        2. Get parent version (current)
        3. Create version record
        4. Save to version directory
        5. Update current symlink

        Args:
            ticket_id: ID of the ticket this version belongs to
            stage: Which stage of implementation
            content: Full content to version
            author: Agent ID or user creating this version
            change_summary: Optional summary of what changed
            metadata: Optional additional metadata

        Returns:
            The created ContentVersion.
        """
        # Ensure directory exists
        stage_dir = self._get_stage_dir(ticket_id, stage)
        stage_dir.mkdir(parents=True, exist_ok=True)

        # Compute content hash
        content_hash = self.compute_hash(content)

        # Get current version as parent
        current = self.get_current(ticket_id, stage)
        parent_version = current.version_id if current else None

        # Create version
        version = ContentVersion(
            version_id=str(ULID()),
            ticket_id=ticket_id,
            stage=stage,
            content_hash=content_hash,
            content=content,
            timestamp=datetime.now(timezone.utc),
            author=author,
            parent_version=parent_version,
            change_summary=change_summary,
            metadata=metadata or {},
        )

        # Save version file
        self._save_version(version)

        # Update current link (using a YAML file for consistency and cross-platform support)
        self._update_current_link(ticket_id, stage, version.version_id)

        return version

    def get_current(
        self, ticket_id: str, stage: VersionStage
    ) -> Optional[ContentVersion]:
        """
        Get current (latest) version for stage.

        Args:
            ticket_id: ID of the ticket
            stage: Which stage to get current version for

        Returns:
            Current ContentVersion, or None if no versions exist.
        """
        current_path = self._get_current_link_path(ticket_id, stage)

        if not current_path.exists():
            return None

        try:
            # Read current.yaml which contains reference to latest version
            current_data = yaml.safe_load(current_path.read_text(encoding="utf-8"))
            if current_data is None:
                return None

            current_version_id = current_data.get("current_version_id")
            if not current_version_id:
                return None

            return self.get_version(ticket_id, stage, current_version_id)
        except Exception as e:
            logger.warning(f"Failed to read current version link: {e}")
            return None

    def get_version(
        self, ticket_id: str, stage: VersionStage, version_id: str
    ) -> Optional[ContentVersion]:
        """
        Get specific version by ID.

        Args:
            ticket_id: ID of the ticket
            stage: Which stage the version belongs to
            version_id: ID of the version to retrieve

        Returns:
            ContentVersion if found, None otherwise.
        """
        version_path = self._get_version_path(ticket_id, stage, version_id)

        if not version_path.exists():
            return None

        yaml_content = version_path.read_text(encoding="utf-8")
        return ContentVersion.from_yaml(yaml_content)

    def get_history(
        self,
        ticket_id: str,
        stage: Optional[VersionStage] = None,
    ) -> List[ContentVersion]:
        """
        Get version history for ticket, optionally filtered by stage.

        Args:
            ticket_id: ID of the ticket
            stage: Optional stage to filter by (None = all stages)

        Returns:
            List of ContentVersions, sorted by timestamp (oldest first).
        """
        versions: List[ContentVersion] = []

        # Determine which stages to check
        stages = [stage] if stage else list(VersionStage)

        for s in stages:
            stage_dir = self._get_stage_dir(ticket_id, s)
            if not stage_dir.exists():
                continue

            for version_file in stage_dir.glob("*.yaml"):
                # Skip the current pointer file
                if version_file.name == "current.yaml":
                    continue

                try:
                    yaml_content = version_file.read_text(encoding="utf-8")
                    version = ContentVersion.from_yaml(yaml_content)
                    versions.append(version)
                except Exception as e:
                    logger.warning(f"Failed to load version from {version_file}: {e}")

        # Sort by timestamp
        versions.sort(key=lambda v: v.timestamp)

        return versions

    def compute_hash(self, content: str) -> str:
        """
        Compute SHA256 hash of content.

        Args:
            content: Content to hash

        Returns:
            Hexadecimal SHA256 hash string.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def has_changed(
        self, ticket_id: str, stage: VersionStage, content: str
    ) -> bool:
        """
        Check if content differs from current version.

        Args:
            ticket_id: ID of the ticket
            stage: Which stage to check
            content: Content to compare against current version

        Returns:
            True if content is different from current version,
            False if same or no current version exists.
        """
        current = self.get_current(ticket_id, stage)
        if current is None:
            return True  # No current version means content is "new"

        new_hash = self.compute_hash(content)
        return new_hash != current.content_hash

    def get_version_by_id(self, version_id: str) -> Optional[ContentVersion]:
        """
        Get a version by ID, searching across all tickets and stages.

        This is a slower operation that searches all version files.
        Use get_version() when you know the ticket_id and stage.

        Args:
            version_id: ID of the version to find

        Returns:
            ContentVersion if found, None otherwise.
        """
        if not self.versions_root.exists():
            return None

        # Search all ticket directories
        for ticket_dir in self.versions_root.iterdir():
            if not ticket_dir.is_dir():
                continue

            # Search all stages
            for stage in VersionStage:
                stage_dir = ticket_dir / stage.value
                if not stage_dir.exists():
                    continue

                version_path = stage_dir / f"{version_id}.yaml"
                if version_path.exists():
                    yaml_content = version_path.read_text(encoding="utf-8")
                    return ContentVersion.from_yaml(yaml_content)

        return None

    def _get_version_dir(self, ticket_id: str, stage: VersionStage) -> Path:
        """
        Get directory for version storage.

        This is an alias for _get_stage_dir for API consistency
        with the task specification.

        Args:
            ticket_id: ID of the ticket
            stage: Which stage

        Returns:
            Path to the stage directory for the ticket.
        """
        return self._get_stage_dir(ticket_id, stage)

    def _save_version(self, version: ContentVersion) -> None:
        """
        Save version to filesystem.

        Creates necessary directories and writes the version YAML file.

        Args:
            version: ContentVersion to save
        """
        stage_dir = self._get_stage_dir(version.ticket_id, version.stage)
        stage_dir.mkdir(parents=True, exist_ok=True)

        version_path = self._get_version_path(
            version.ticket_id, version.stage, version.version_id
        )
        version_path.write_text(version.to_yaml(), encoding="utf-8")
        logger.debug(f"Saved version {version.version_id} to {version_path}")

    def _update_current_link(
        self, ticket_id: str, stage: VersionStage, version_id: str
    ) -> None:
        """
        Update current.yaml to point to the latest version.

        Uses a YAML file with version reference for cross-platform compatibility
        (avoiding symlinks which don't work well on Windows).

        Args:
            ticket_id: ID of the ticket
            stage: Which stage
            version_id: ID of the version to set as current
        """
        stage_dir = self._get_stage_dir(ticket_id, stage)
        stage_dir.mkdir(parents=True, exist_ok=True)

        current_path = self._get_current_link_path(ticket_id, stage)

        # Write YAML file with reference to current version
        current_data = {
            "current_version_id": version_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        yaml_content = yaml.dump(
            current_data,
            default_flow_style=False,
            sort_keys=False,
        )
        current_path.write_text(yaml_content, encoding="utf-8")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ContentVersion",
    "ContentVersioner",
    "VersionStage",
]
