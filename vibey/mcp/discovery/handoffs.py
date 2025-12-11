"""
Handoff Discovery Module.

Discovers handoff templates from markdown files and provides structured
HandoffDefinition objects for tool generation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class HandoffVariable:
    """Variable definition from handoff template."""

    name: str
    type: str = "string"
    required: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None


@dataclass
class HandoffDefinition:
    """
    Parsed handoff template definition.

    Contains all metadata about a handoff template including:
    - Routing information (from/to agents)
    - Variable definitions for template rendering
    - Purpose and description
    """

    id: str
    name: str
    version: str
    from_agent: str
    to_agents: List[str]
    purpose: str
    description: Optional[str] = None
    variables: List[HandoffVariable] = field(default_factory=list)
    filepath: Optional[Path] = None

    @classmethod
    def from_frontmatter(
        cls, frontmatter: Dict[str, Any], filepath: Path
    ) -> "HandoffDefinition":
        """
        Parse handoff from YAML frontmatter.

        Args:
            frontmatter: Parsed YAML frontmatter dict
            filepath: Path to the template file

        Returns:
            HandoffDefinition instance
        """
        variables = [
            HandoffVariable(
                name=v.get("name", ""),
                type=v.get("type", "string"),
                required=v.get("required", False),
                description=v.get("description"),
                default=v.get("default"),
            )
            for v in frontmatter.get("variables", [])
        ]

        return cls(
            id=frontmatter.get("id", filepath.stem),
            name=frontmatter.get("name", filepath.stem),
            version=frontmatter.get("version", "1.0.0"),
            from_agent=frontmatter.get("from_agent", "unknown"),
            to_agents=frontmatter.get("to_agents", []),
            purpose=frontmatter.get("purpose", ""),
            description=frontmatter.get("description"),
            variables=variables,
            filepath=filepath,
        )


class HandoffDiscovery:
    """
    Discovers handoff templates from markdown files.

    Scans the templates/handoffs directory, parses YAML frontmatter,
    and builds HandoffDefinition objects for tool generation.

    Example:
        >>> discovery = HandoffDiscovery(Path("/path/to/vibey"))
        >>> handoffs = discovery.discover()
        >>> print(f"Found {len(handoffs)} handoffs")
    """

    def __init__(self, root_dir: Path):
        """
        Initialize handoff discovery.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.handoffs_dir = self._resolve_handoffs_dir()
        self._cache: Optional[List[HandoffDefinition]] = None

    def _resolve_handoffs_dir(self) -> Path:
        """Resolve the handoffs directory path."""
        possible_paths = [
            self.root_dir / "vibey" / "content" / "templates" / "handoffs",
            self.root_dir / "content" / "templates" / "handoffs",
            self.root_dir / "framework" / "templates" / "handoffs",
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return possible_paths[0]

    def discover(self, force_refresh: bool = False) -> List[HandoffDefinition]:
        """
        Discover all handoff templates.

        Args:
            force_refresh: Force re-scan of templates

        Returns:
            List of HandoffDefinition objects
        """
        if self._cache is not None and not force_refresh:
            return self._cache

        handoffs = []

        if not self.handoffs_dir.exists():
            logger.warning(f"Handoffs directory not found: {self.handoffs_dir}")
            return handoffs

        for filepath in self.handoffs_dir.glob("*.md"):
            # Skip README files
            if filepath.name.lower() == "readme.md":
                continue

            try:
                handoff = self._parse_handoff_file(filepath)
                if handoff:
                    handoffs.append(handoff)
                    logger.debug(f"Discovered handoff: {handoff.id}")
            except Exception as e:
                logger.error(f"Error parsing handoff {filepath}: {e}")

        self._cache = handoffs
        logger.info(f"Discovered {len(handoffs)} handoff templates")
        return handoffs

    def _parse_handoff_file(self, filepath: Path) -> Optional[HandoffDefinition]:
        """
        Parse a single handoff template file.

        Args:
            filepath: Path to the markdown file

        Returns:
            HandoffDefinition or None if parsing fails
        """
        content = filepath.read_text()

        # Extract frontmatter
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {filepath}: {e}")
            return None

        if not frontmatter:
            return None

        return HandoffDefinition.from_frontmatter(frontmatter, filepath)

    def get_handoff_by_id(self, handoff_id: str) -> Optional[HandoffDefinition]:
        """
        Get a specific handoff by ID.

        Args:
            handoff_id: Handoff ID to find

        Returns:
            HandoffDefinition or None if not found
        """
        for handoff in self.discover():
            if handoff.id == handoff_id:
                return handoff
        return None

    def get_handoffs_from_agent(self, agent_id: str) -> List[HandoffDefinition]:
        """
        Get all handoffs originating from an agent.

        Args:
            agent_id: Agent ID to filter by

        Returns:
            List of handoffs from that agent
        """
        return [h for h in self.discover() if h.from_agent == agent_id]

    def get_handoffs_to_agent(self, agent_id: str) -> List[HandoffDefinition]:
        """
        Get all handoffs targeting an agent.

        Args:
            agent_id: Agent ID to filter by

        Returns:
            List of handoffs to that agent
        """
        return [h for h in self.discover() if agent_id in h.to_agents]

    def invalidate_cache(self) -> None:
        """Invalidate the discovery cache."""
        self._cache = None
        logger.debug("Handoff discovery cache invalidated")
