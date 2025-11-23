"""
Agent Discovery Module.

Scans the framework/agents/ directory for agent markdown files
and extracts their frontmatter for MCP tool generation.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from .parser import FrontmatterParser

logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Parsed agent definition from frontmatter."""

    id: str
    name: str
    type: str
    version: str
    description: str = ""
    triggers: Dict[str, Any] = field(default_factory=dict)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    filepath: Optional[Path] = None

    @classmethod
    def from_frontmatter(
        cls,
        frontmatter: Dict[str, Any],
        filepath: Optional[Path] = None
    ) -> "AgentDefinition":
        """Create AgentDefinition from parsed frontmatter."""
        return cls(
            id=frontmatter.get('id', ''),
            name=frontmatter.get('name', ''),
            type=frontmatter.get('type', 'development'),
            version=frontmatter.get('version', '1.0.0'),
            description=frontmatter.get('description', ''),
            triggers=frontmatter.get('triggers', {}),
            inputs=frontmatter.get('inputs', []),
            outputs=frontmatter.get('outputs', []),
            aliases=frontmatter.get('aliases', []),
            filepath=filepath,
        )


class AgentDiscovery:
    """
    Discover agents from framework/agents/ directory.

    Scans all markdown files, extracts frontmatter, and returns
    AgentDefinition objects for MCP tool generation.

    Example:
        >>> discovery = AgentDiscovery(Path("/path/to/vibey"))
        >>> agents = discovery.discover()
        >>> for agent in agents:
        ...     print(f"{agent.id}: {agent.name}")
    """

    REQUIRED_FIELDS = ['id', 'name', 'type', 'version']

    def __init__(self, root_dir: Path):
        """
        Initialize agent discovery.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.agents_dir = self.root_dir / 'framework' / 'agents'
        self.parser = FrontmatterParser()

    def discover(self) -> List[AgentDefinition]:
        """
        Discover all agents in the agents directory.

        Returns:
            List of AgentDefinition objects
        """
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return []

        agents = []
        for filepath in self.agents_dir.rglob('*.md'):
            # Skip README files
            if filepath.name.lower() == 'readme.md':
                continue

            agent = self._parse_agent_file(filepath)
            if agent:
                agents.append(agent)
                logger.debug(f"Discovered agent: {agent.id}")

        logger.info(f"Discovered {len(agents)} agents")
        return agents

    def _parse_agent_file(self, filepath: Path) -> Optional[AgentDefinition]:
        """Parse a single agent file."""
        try:
            frontmatter, _ = self.parser.parse_file(filepath)

            if frontmatter is None:
                logger.warning(f"No frontmatter in agent file: {filepath}")
                return None

            # Validate required fields
            is_valid, errors = self.parser.validate_frontmatter(
                frontmatter,
                self.REQUIRED_FIELDS
            )

            if not is_valid:
                logger.warning(f"Invalid agent {filepath}: {errors}")
                return None

            return AgentDefinition.from_frontmatter(frontmatter, filepath)

        except Exception as e:
            logger.error(f"Error parsing agent {filepath}: {e}")
            return None

    def get_agent_by_id(self, agent_id: str) -> Optional[AgentDefinition]:
        """
        Get a specific agent by ID.

        Args:
            agent_id: Agent ID to find

        Returns:
            AgentDefinition or None if not found
        """
        agents = self.discover()
        for agent in agents:
            if agent.id == agent_id:
                return agent
            # Check aliases
            if agent_id in agent.aliases:
                return agent
        return None

    def get_agents_by_type(self, agent_type: str) -> List[AgentDefinition]:
        """
        Get all agents of a specific type.

        Args:
            agent_type: Type to filter by (core, planning, development, etc.)

        Returns:
            List of matching AgentDefinition objects
        """
        agents = self.discover()
        return [a for a in agents if a.type == agent_type]
