"""
Content Operations Models.

Defines the core data models for content management:
- ContentType: Enum of content types (agent, workflow, template, etc.)
- ContentMetadata: Structured frontmatter data
- ContentItem: Full content representation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContentType(str, Enum):
    """Types of content in the Vibey framework."""

    AGENT = "agent"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    HANDOFF = "handoff"
    SCHEMA = "schema"
    EXAMPLE = "example"
    CONFIG = "config"

    @classmethod
    def from_path(cls, path: Path) -> Optional["ContentType"]:
        """Infer content type from file path."""
        path_str = str(path).lower()

        if "/agents/" in path_str:
            return cls.AGENT
        elif "/workflows/" in path_str:
            return cls.WORKFLOW
        elif "/templates/" in path_str:
            return cls.TEMPLATE
        elif "/handoffs/" in path_str:
            return cls.HANDOFF
        elif "/schemas/" in path_str:
            return cls.SCHEMA
        elif "/examples/" in path_str:
            return cls.EXAMPLE
        elif "/config/" in path_str:
            return cls.CONFIG
        return None

    @property
    def directory_name(self) -> str:
        """Get the directory name for this content type."""
        return {
            ContentType.AGENT: "agents",
            ContentType.WORKFLOW: "workflows",
            ContentType.TEMPLATE: "templates",
            ContentType.HANDOFF: "handoffs",
            ContentType.SCHEMA: "schemas",
            ContentType.EXAMPLE: "examples",
            ContentType.CONFIG: "config",
        }[self]

    @property
    def file_extension(self) -> str:
        """Get the typical file extension for this content type."""
        if self in (ContentType.AGENT, ContentType.WORKFLOW, ContentType.TEMPLATE, ContentType.HANDOFF):
            return ".md"
        elif self in (ContentType.SCHEMA, ContentType.EXAMPLE, ContentType.CONFIG):
            return ".yaml"
        return ".md"


@dataclass
class ContentMetadata:
    """
    Structured metadata from content frontmatter.

    Common fields across all content types. Type-specific
    fields are stored in `extra`.
    """

    id: str
    name: str
    version: str = "1.0.0"
    type: Optional[str] = None  # Subtype within content type (e.g., agent type: "core", "planning")
    description: str = ""
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_frontmatter(cls, frontmatter: Dict[str, Any]) -> "ContentMetadata":
        """Create ContentMetadata from parsed frontmatter dict."""
        # Extract known fields
        known_fields = {"id", "name", "version", "type", "description", "tags"}
        extra = {k: v for k, v in frontmatter.items() if k not in known_fields}

        return cls(
            id=frontmatter.get("id", ""),
            name=frontmatter.get("name", ""),
            version=frontmatter.get("version", "1.0.0"),
            type=frontmatter.get("type"),
            description=frontmatter.get("description", ""),
            tags=frontmatter.get("tags", []),
            extra=extra,
        )

    def to_frontmatter(self) -> Dict[str, Any]:
        """Convert back to frontmatter dict."""
        result: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
        }
        if self.type:
            result["type"] = self.type
        if self.description:
            result["description"] = self.description
        if self.tags:
            result["tags"] = self.tags
        # Merge extra fields
        result.update(self.extra)
        return result


@dataclass
class ContentItem:
    """
    Full representation of a content item.

    Contains both metadata (frontmatter) and body content,
    along with file path and computed properties.
    """

    content_type: ContentType
    metadata: ContentMetadata
    body: str
    filepath: Path

    # Computed/cached properties
    _raw_frontmatter: Dict[str, Any] = field(default_factory=dict, repr=False)
    _modified_time: Optional[datetime] = None

    @property
    def id(self) -> str:
        """Content ID from metadata."""
        return self.metadata.id

    @property
    def name(self) -> str:
        """Content name from metadata."""
        return self.metadata.name

    @property
    def relative_path(self) -> str:
        """Get path relative to content root."""
        parts = self.filepath.parts
        try:
            content_idx = parts.index("content")
            return "/".join(parts[content_idx + 1:])
        except ValueError:
            return str(self.filepath.name)

    @property
    def category(self) -> Optional[str]:
        """Get category (subdirectory) if applicable."""
        # For agents/workflows, category is the subdirectory
        # e.g., agents/core/coordinator.md -> "core"
        parts = self.filepath.parts
        try:
            type_dir = self.content_type.directory_name
            type_idx = None
            for i, part in enumerate(parts):
                if part == type_dir:
                    type_idx = i
                    break
            if type_idx is not None and type_idx + 1 < len(parts) - 1:
                return parts[type_idx + 1]
        except (ValueError, IndexError):
            pass
        return None

    @property
    def modified_time(self) -> Optional[datetime]:
        """Get file modification time."""
        if self._modified_time is None and self.filepath.exists():
            stat = self.filepath.stat()
            self._modified_time = datetime.fromtimestamp(stat.st_mtime)
        return self._modified_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "content_type": self.content_type.value,
            "category": self.category,
            "filepath": str(self.filepath),
            "relative_path": self.relative_path,
            "metadata": self.metadata.to_frontmatter(),
            "body_preview": self.body[:200] + "..." if len(self.body) > 200 else self.body,
        }


@dataclass
class ContentValidationResult:
    """Result of validating content."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


@dataclass
class ContentOperationResult:
    """Result of a content operation (create, update, delete)."""

    success: bool
    message: str
    content: Optional[ContentItem] = None
    backup_path: Optional[Path] = None
    errors: List[str] = field(default_factory=list)

    @classmethod
    def ok(
        cls,
        message: str,
        content: Optional[ContentItem] = None,
        backup_path: Optional[Path] = None
    ) -> "ContentOperationResult":
        """Create a successful result."""
        return cls(success=True, message=message, content=content, backup_path=backup_path)

    @classmethod
    def error(cls, message: str, errors: Optional[List[str]] = None) -> "ContentOperationResult":
        """Create an error result."""
        return cls(success=False, message=message, errors=errors or [message])
