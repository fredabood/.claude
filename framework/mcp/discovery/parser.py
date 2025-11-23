"""
Frontmatter Parser for Vibey assets.

Extracts YAML frontmatter from markdown files containing
agent, workflow, and handoff definitions.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class FrontmatterParser:
    """
    Parse YAML frontmatter from Vibey markdown files.

    Example:
        >>> parser = FrontmatterParser()
        >>> frontmatter, body = parser.parse_file(Path("agents/test-engineer.md"))
        >>> print(frontmatter['id'])
        'test-engineer'
    """

    # Regex to match YAML frontmatter block
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.DOTALL
    )

    def parse_file(self, filepath: Path) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Parse a markdown file and extract frontmatter.

        Args:
            filepath: Path to the markdown file

        Returns:
            Tuple of (frontmatter dict or None, body content)

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If frontmatter is invalid YAML
        """
        content = filepath.read_text(encoding='utf-8')
        return self.parse_content(content, filepath)

    def parse_content(
        self,
        content: str,
        source: Optional[Path] = None
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Parse content string and extract frontmatter.

        Args:
            content: Markdown content string
            source: Optional source path for error messages

        Returns:
            Tuple of (frontmatter dict or None, body content)
        """
        if not content.strip().startswith('---'):
            logger.debug(f"No frontmatter in {source or 'content'}")
            return None, content

        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            logger.warning(f"Malformed frontmatter in {source or 'content'}")
            return None, content

        yaml_content = match.group(1)
        body = content[match.end():]

        try:
            frontmatter = yaml.safe_load(yaml_content)
            if not isinstance(frontmatter, dict):
                logger.warning(f"Frontmatter is not a dict in {source or 'content'}")
                return None, content
            return frontmatter, body
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {source or 'content'}: {e}")
            raise

    def has_frontmatter(self, content: str) -> bool:
        """Check if content has valid frontmatter."""
        if not content.strip().startswith('---'):
            return False
        return bool(self.FRONTMATTER_PATTERN.match(content))

    def validate_frontmatter(
        self,
        frontmatter: Dict[str, Any],
        required_fields: list[str]
    ) -> Tuple[bool, list[str]]:
        """
        Validate frontmatter has required fields.

        Args:
            frontmatter: Parsed frontmatter dict
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        for field in required_fields:
            if field not in frontmatter:
                errors.append(f"Missing required field: {field}")
            elif frontmatter[field] is None:
                errors.append(f"Field '{field}' is null")
            elif isinstance(frontmatter[field], str) and not frontmatter[field].strip():
                errors.append(f"Field '{field}' is empty")

        return len(errors) == 0, errors
