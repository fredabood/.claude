"""
Content Loader.

Loads content items from the vibey/content/ directory.
Handles frontmatter parsing and content type detection.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import yaml

from vibey.content import (
    get_content_root,
    get_agents_dir,
    get_workflows_dir,
    get_templates_dir,
    get_schemas_dir,
    get_examples_dir,
    get_config_dir,
)
from .models import ContentType, ContentMetadata, ContentItem

logger = logging.getLogger(__name__)


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Extract YAML frontmatter from markdown content.

    Args:
        content: Raw file content

    Returns:
        Tuple of (frontmatter dict or None, body text)
    """
    if not content.strip().startswith("---"):
        return None, content

    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        return None, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]
        return frontmatter, body
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse frontmatter: {e}")
        return None, content


def compose_content(frontmatter: Dict[str, Any], body: str) -> str:
    """
    Compose content from frontmatter and body.

    Args:
        frontmatter: Dict to serialize as YAML
        body: Body text

    Returns:
        Complete markdown content with frontmatter
    """
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return f"---\n{yaml_str}---\n{body}"


class ContentLoader:
    """
    Load content items from the filesystem.

    Provides methods to load individual items or list all content
    of a specific type.
    """

    def __init__(self, content_root: Optional[Path] = None):
        """
        Initialize content loader.

        Args:
            content_root: Root path to content directory (defaults to package content)
        """
        self.content_root = content_root or get_content_root()

    def get_type_directory(self, content_type: ContentType) -> Path:
        """Get the directory for a content type."""
        if self.content_root == get_content_root():
            # Use accessor functions for package-aware paths
            mapping = {
                ContentType.AGENT: get_agents_dir(),
                ContentType.WORKFLOW: get_workflows_dir(),
                ContentType.TEMPLATE: get_templates_dir(),
                ContentType.HANDOFF: get_templates_dir() / "handoffs",
                ContentType.SCHEMA: get_schemas_dir(),
                ContentType.EXAMPLE: get_examples_dir(),
                ContentType.CONFIG: get_config_dir(),
            }
            return mapping.get(content_type, self.content_root)
        else:
            # Custom root - use relative paths
            return self.content_root / content_type.directory_name

    def load_file(self, filepath: Path) -> Optional[ContentItem]:
        """
        Load a single content file.

        Args:
            filepath: Path to the content file

        Returns:
            ContentItem or None if file cannot be loaded
        """
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None

        try:
            raw_content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return None

        # Determine content type from path
        content_type = ContentType.from_path(filepath)
        if content_type is None:
            logger.warning(f"Cannot determine content type for: {filepath}")
            return None

        # Parse frontmatter
        frontmatter, body = extract_frontmatter(raw_content)
        if frontmatter is None:
            # For non-markdown files (yaml), treat entire content as metadata
            if filepath.suffix in (".yaml", ".yml"):
                try:
                    frontmatter = yaml.safe_load(raw_content)
                    body = ""
                except yaml.YAMLError:
                    logger.warning(f"Failed to parse YAML: {filepath}")
                    return None
            else:
                logger.warning(f"No frontmatter found in: {filepath}")
                return None

        # Create metadata
        metadata = ContentMetadata.from_frontmatter(frontmatter)

        # Generate ID from filename if not in frontmatter
        if not metadata.id:
            metadata.id = filepath.stem

        # Generate name from filename if not in frontmatter
        if not metadata.name:
            metadata.name = filepath.stem.replace("-", " ").replace("_", " ").title()

        return ContentItem(
            content_type=content_type,
            metadata=metadata,
            body=body,
            filepath=filepath,
            _raw_frontmatter=frontmatter,
        )

    def load_by_id(
        self,
        content_id: str,
        content_type: Optional[ContentType] = None
    ) -> Optional[ContentItem]:
        """
        Load content by ID.

        Args:
            content_id: Content ID to find
            content_type: Optionally limit search to specific type

        Returns:
            ContentItem or None if not found
        """
        types_to_search = [content_type] if content_type else list(ContentType)

        for ctype in types_to_search:
            search_dir = self.get_type_directory(ctype)
            if not search_dir.exists():
                continue

            # Search for matching file
            for filepath in search_dir.rglob("*"):
                if filepath.is_dir() or filepath.name.lower() == "readme.md":
                    continue

                # Check if filename matches ID
                if filepath.stem == content_id:
                    return self.load_file(filepath)

                # Load and check frontmatter ID
                item = self.load_file(filepath)
                if item and item.id == content_id:
                    return item

        return None

    def list_content(
        self,
        content_type: Optional[ContentType] = None,
        category: Optional[str] = None,
    ) -> List[ContentItem]:
        """
        List all content items.

        Args:
            content_type: Optionally filter by content type
            category: Optionally filter by category (subdirectory)

        Returns:
            List of ContentItem objects
        """
        types_to_search = [content_type] if content_type else list(ContentType)
        items: List[ContentItem] = []

        for ctype in types_to_search:
            search_dir = self.get_type_directory(ctype)
            if not search_dir.exists():
                continue

            # Get all content files
            patterns = ["*.md", "*.yaml", "*.yml"]
            for pattern in patterns:
                for filepath in search_dir.rglob(pattern):
                    if filepath.is_dir():
                        continue
                    if filepath.name.lower() == "readme.md":
                        continue

                    item = self.load_file(filepath)
                    if item is None:
                        continue

                    # Filter by category if specified
                    if category and item.category != category:
                        continue

                    items.append(item)

        return items

    def get_categories(self, content_type: ContentType) -> List[str]:
        """
        Get all categories (subdirectories) for a content type.

        Args:
            content_type: Content type to check

        Returns:
            List of category names
        """
        search_dir = self.get_type_directory(content_type)
        if not search_dir.exists():
            return []

        categories = []
        for path in search_dir.iterdir():
            if path.is_dir() and not path.name.startswith((".", "_")):
                categories.append(path.name)

        return sorted(categories)


# Module-level convenience functions
_default_loader: Optional[ContentLoader] = None


def get_loader() -> ContentLoader:
    """Get the default content loader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = ContentLoader()
    return _default_loader


def load_content(content_id: str, content_type: Optional[ContentType] = None) -> Optional[ContentItem]:
    """Load content by ID."""
    return get_loader().load_by_id(content_id, content_type)


def list_content(
    content_type: Optional[ContentType] = None,
    category: Optional[str] = None
) -> List[ContentItem]:
    """List all content items."""
    return get_loader().list_content(content_type, category)
