"""
Content Writer.

Handles writing content with validation, backups, and atomic writes.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from vibey.content import get_content_root
from .models import (
    ContentType,
    ContentItem,
    ContentMetadata,
    ContentValidationResult,
    ContentOperationResult,
)
from .loader import ContentLoader, compose_content, extract_frontmatter
from .backup import ContentBackup, get_backup_manager

logger = logging.getLogger(__name__)


# Required fields by content type
REQUIRED_FIELDS = {
    ContentType.AGENT: ["id", "name", "type", "version"],
    ContentType.WORKFLOW: ["id", "name", "type", "version"],
    ContentType.TEMPLATE: ["id", "name", "version"],
    ContentType.HANDOFF: ["id", "name", "version"],
    ContentType.SCHEMA: ["id", "name"],
    ContentType.EXAMPLE: ["id", "name"],
    ContentType.CONFIG: [],
}

# Valid enum values
VALID_AGENT_TYPES = ["core", "planning", "development", "quality", "documentation", "architecture"]
VALID_WORKFLOW_TYPES = ["planning", "development", "quality", "documentation", "deployment"]


class ContentValidator:
    """Validates content before writing."""

    def validate(
        self,
        content_type: ContentType,
        frontmatter: Dict[str, Any],
        body: str = ""
    ) -> ContentValidationResult:
        """
        Validate content before writing.

        Args:
            content_type: Type of content
            frontmatter: Frontmatter dict to validate
            body: Body text (optional)

        Returns:
            ContentValidationResult with any errors/warnings
        """
        result = ContentValidationResult(is_valid=True)

        # Check required fields
        required = REQUIRED_FIELDS.get(content_type, [])
        for field in required:
            if field not in frontmatter or not frontmatter[field]:
                result.add_error(f"Missing required field: {field}")

        # Type-specific validation
        if content_type == ContentType.AGENT:
            self._validate_agent(frontmatter, result)
        elif content_type == ContentType.WORKFLOW:
            self._validate_workflow(frontmatter, result)

        # Validate ID format
        if "id" in frontmatter:
            id_val = frontmatter["id"]
            if not isinstance(id_val, str):
                result.add_error("ID must be a string")
            elif not id_val.replace("-", "").replace("_", "").isalnum():
                result.add_warning("ID should contain only alphanumeric characters, hyphens, and underscores")

        return result

    def _validate_agent(
        self,
        frontmatter: Dict[str, Any],
        result: ContentValidationResult
    ) -> None:
        """Validate agent-specific fields."""
        if "type" in frontmatter and frontmatter["type"] not in VALID_AGENT_TYPES:
            result.add_error(
                f"Invalid agent type: {frontmatter['type']} "
                f"(valid: {', '.join(VALID_AGENT_TYPES)})"
            )

        # Check inputs have required fields
        if "inputs" in frontmatter:
            for i, inp in enumerate(frontmatter["inputs"]):
                if not isinstance(inp, dict):
                    result.add_error(f"Input {i} must be a dict")
                elif "name" not in inp:
                    result.add_error(f"Input {i} missing 'name' field")

        # Check outputs have required fields
        if "outputs" in frontmatter:
            for i, out in enumerate(frontmatter["outputs"]):
                if not isinstance(out, dict):
                    result.add_error(f"Output {i} must be a dict")
                elif "name" not in out:
                    result.add_error(f"Output {i} missing 'name' field")

    def _validate_workflow(
        self,
        frontmatter: Dict[str, Any],
        result: ContentValidationResult
    ) -> None:
        """Validate workflow-specific fields."""
        if "type" in frontmatter and frontmatter["type"] not in VALID_WORKFLOW_TYPES:
            result.add_error(
                f"Invalid workflow type: {frontmatter['type']} "
                f"(valid: {', '.join(VALID_WORKFLOW_TYPES)})"
            )

        # Check steps have required fields
        if "steps" in frontmatter:
            for i, step in enumerate(frontmatter["steps"]):
                if not isinstance(step, dict):
                    result.add_error(f"Step {i} must be a dict")
                else:
                    if "order" not in step:
                        result.add_error(f"Step {i} missing 'order' field")
                    if "name" not in step:
                        result.add_error(f"Step {i} missing 'name' field")


class ContentWriter:
    """
    Write content with validation and safety.

    Features:
    - Validates content before writing
    - Creates backups before modifications
    - Atomic writes (temp file + rename)
    - Maintains file permissions
    """

    def __init__(
        self,
        content_root: Optional[Path] = None,
        backup_manager: Optional[ContentBackup] = None
    ):
        """
        Initialize content writer.

        Args:
            content_root: Root path to content directory
            backup_manager: Backup manager instance
        """
        self.content_root = content_root or get_content_root()
        self.backup = backup_manager or get_backup_manager()
        self.validator = ContentValidator()
        self.loader = ContentLoader(self.content_root)

    def create(
        self,
        content_type: ContentType,
        frontmatter: Dict[str, Any],
        body: str = "",
        category: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> ContentOperationResult:
        """
        Create new content.

        Args:
            content_type: Type of content to create
            frontmatter: Frontmatter dict
            body: Body text (for markdown files)
            category: Subdirectory (e.g., "core" for agents)
            filename: Filename (defaults to ID)

        Returns:
            ContentOperationResult
        """
        # Validate
        validation = self.validator.validate(content_type, frontmatter, body)
        if not validation.is_valid:
            return ContentOperationResult.error(
                "Validation failed",
                errors=validation.errors
            )

        # Determine filepath
        content_id = frontmatter.get("id", "")
        if not filename:
            filename = f"{content_id}{content_type.file_extension}"

        type_dir = self.loader.get_type_directory(content_type)
        if category:
            filepath = type_dir / category / filename
        else:
            filepath = type_dir / filename

        # Check if already exists
        if filepath.exists():
            return ContentOperationResult.error(
                f"Content already exists: {filepath}"
            )

        # Write file
        return self._write_file(filepath, content_type, frontmatter, body)

    def update(
        self,
        content_id: str,
        updates: Dict[str, Any],
        content_type: Optional[ContentType] = None,
        update_body: Optional[str] = None,
    ) -> ContentOperationResult:
        """
        Update existing content.

        Args:
            content_id: ID of content to update
            updates: Dict of field updates (merged into existing frontmatter)
            content_type: Content type (optional, will search if not provided)
            update_body: New body text (optional)

        Returns:
            ContentOperationResult
        """
        # Load existing content
        item = self.loader.load_by_id(content_id, content_type)
        if item is None:
            return ContentOperationResult.error(f"Content not found: {content_id}")

        # Merge updates into existing frontmatter
        new_frontmatter = item._raw_frontmatter.copy()
        new_frontmatter.update(updates)

        # Use new body or keep existing
        new_body = update_body if update_body is not None else item.body

        # Validate updated content
        validation = self.validator.validate(item.content_type, new_frontmatter, new_body)
        if not validation.is_valid:
            return ContentOperationResult.error(
                "Validation failed",
                errors=validation.errors
            )

        # Create backup
        backup_path = self.backup.create_backup(item.filepath, operation="update")

        # Write updated file
        result = self._write_file(
            item.filepath,
            item.content_type,
            new_frontmatter,
            new_body,
            overwrite=True
        )
        result.backup_path = backup_path

        return result

    def delete(
        self,
        content_id: str,
        content_type: Optional[ContentType] = None,
        force: bool = False,
    ) -> ContentOperationResult:
        """
        Delete content (moves to trash).

        Args:
            content_id: ID of content to delete
            content_type: Content type (optional)
            force: Skip reference check if True

        Returns:
            ContentOperationResult
        """
        # Load content to delete
        item = self.loader.load_by_id(content_id, content_type)
        if item is None:
            return ContentOperationResult.error(f"Content not found: {content_id}")

        # Check for references (unless force)
        if not force:
            references = self._find_references(content_id)
            if references:
                return ContentOperationResult.error(
                    f"Content is referenced by: {', '.join(references)}. Use --force to delete anyway."
                )

        # Move to trash (soft delete)
        trash_path = self.backup.move_to_trash(item.filepath)
        if trash_path is None:
            return ContentOperationResult.error(f"Failed to delete: {item.filepath}")

        return ContentOperationResult.ok(
            f"Deleted {content_id} (moved to trash)",
            backup_path=trash_path
        )

    def _write_file(
        self,
        filepath: Path,
        content_type: ContentType,
        frontmatter: Dict[str, Any],
        body: str,
        overwrite: bool = False,
    ) -> ContentOperationResult:
        """
        Write content file atomically.

        Uses temp file + rename for atomic write.
        """
        if filepath.exists() and not overwrite:
            return ContentOperationResult.error(f"File exists: {filepath}")

        # Compose content
        if content_type.file_extension == ".md":
            content = compose_content(frontmatter, body)
        else:
            # YAML files
            content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: temp file + rename
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix=filepath.suffix,
                dir=filepath.parent
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)

                # Rename (atomic on most filesystems)
                os.replace(temp_path, filepath)
            except Exception:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return ContentOperationResult.error(f"Write failed: {e}")

        # Load and return the written content
        item = self.loader.load_file(filepath)

        return ContentOperationResult.ok(
            f"Created {filepath.name}",
            content=item
        )

    def _find_references(self, content_id: str) -> List[str]:
        """
        Find content that references the given ID.

        Searches for mentions of the ID in other content files.
        """
        references = []

        for item in self.loader.list_content():
            if item.id == content_id:
                continue

            # Check if ID is referenced in frontmatter or body
            frontmatter_str = str(item._raw_frontmatter)
            if content_id in frontmatter_str or content_id in item.body:
                references.append(item.id)

        return references


# Module-level convenience functions
_default_writer: Optional[ContentWriter] = None


def get_writer() -> ContentWriter:
    """Get the default content writer."""
    global _default_writer
    if _default_writer is None:
        _default_writer = ContentWriter()
    return _default_writer


def create_content(
    content_type: ContentType,
    frontmatter: Dict[str, Any],
    body: str = "",
    category: Optional[str] = None,
) -> ContentOperationResult:
    """Create new content."""
    return get_writer().create(content_type, frontmatter, body, category)


def update_content(
    content_id: str,
    updates: Dict[str, Any],
    content_type: Optional[ContentType] = None,
) -> ContentOperationResult:
    """Update existing content."""
    return get_writer().update(content_id, updates, content_type)


def delete_content(
    content_id: str,
    content_type: Optional[ContentType] = None,
    force: bool = False,
) -> ContentOperationResult:
    """Delete content."""
    return get_writer().delete(content_id, content_type, force)
