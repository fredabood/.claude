"""
MCP Resource Provider for Handoffs.

Provides MCP Resources for vibey handoff templates, enabling:
- Listing available handoff templates
- Accessing template metadata (variables, agents)
- Reading template content
- Variable schema extraction for tool generation
- Template rendering with sample data
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .provider import ResourceProvider
from .types import (
    Resource,
    ResourceContent,
    ResourceTemplate,
    RESOURCE_CATEGORY_HANDOFFS,
    MIME_TYPE_MARKDOWN,
    MIME_TYPE_JSON,
    MIME_TYPE_JINJA2_MARKDOWN,
)
from .exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class HandoffVariable:
    """Variable definition from handoff template."""

    name: str
    type: str
    required: bool
    description: Optional[str] = None
    default: Optional[Any] = None


@dataclass
class HandoffDefinition:
    """Parsed handoff template definition."""

    id: str
    name: str
    version: str
    from_agent: str
    to_agents: List[str]
    purpose: str
    description: Optional[str]
    variables: List[HandoffVariable]
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


class HandoffResourceProvider(ResourceProvider):
    """
    Provides MCP Resources for handoff templates.

    Exposes vibey handoff templates as MCP Resources with support for:
    - Full template content (markdown with Jinja2)
    - Variable schema (JSON Schema format)
    - Template metadata (JSON)
    - Rendered template with sample data (markdown)

    Example:
        >>> provider = HandoffResourceProvider(Path("/path/to/vibey"))
        >>> templates = provider.get_templates()
        >>> resources = provider.list_resources("vibey://handoffs/{handoff_id}")
        >>> content = await provider.read_resource("vibey://handoffs/diagram-handoff")
    """

    URI_CATEGORY = RESOURCE_CATEGORY_HANDOFFS

    def __init__(self, content_root: Path):
        """
        Initialize handoff resource provider.

        Args:
            content_root: Root directory for content discovery
        """
        super().__init__(content_root)
        self._handoffs_dir = self._resolve_handoffs_dir()
        self._cache: Optional[List[HandoffDefinition]] = None

    def _resolve_handoffs_dir(self) -> Path:
        """Resolve the handoffs directory path."""
        possible_paths = [
            self.content_root / "vibey" / "content" / "templates" / "handoffs",
            self.content_root / "content" / "templates" / "handoffs",
            self.content_root / "framework" / "templates" / "handoffs",
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return possible_paths[0]  # Default

    def get_templates(self) -> List[ResourceTemplate]:
        """
        Return handoff resource templates.

        Returns:
            List of ResourceTemplate definitions for handoff resources
        """
        return [
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}",
                name="Handoff Template",
                description="Full handoff template with Jinja2 content",
                mimeType=MIME_TYPE_JINJA2_MARKDOWN,
            ),
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}/variables",
                name="Handoff Variables",
                description="Variable schema for the handoff template (JSON Schema)",
                mimeType=MIME_TYPE_JSON,
            ),
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}/metadata",
                name="Handoff Metadata",
                description="Handoff template metadata (agents, purpose)",
                mimeType=MIME_TYPE_JSON,
            ),
            ResourceTemplate(
                uriTemplate="vibey://handoffs/{handoff_id}/rendered",
                name="Rendered Handoff",
                description="Handoff template rendered with sample data",
                mimeType=MIME_TYPE_MARKDOWN,
            ),
        ]

    def list_resources(self, uri_template: str) -> List[Resource]:
        """
        List all handoffs as resources for a given template.

        Args:
            uri_template: URI template pattern to match

        Returns:
            List of Resource objects matching the template
        """
        handoffs = self._discover_handoffs()
        resources = []

        for hf in handoffs:
            if "variables" in uri_template:
                resources.append(
                    Resource(
                        uri=f"vibey://handoffs/{hf.id}/variables",
                        name=f"{hf.name} - Variables",
                        description=f"{len(hf.variables)} variables defined",
                        mimeType=MIME_TYPE_JSON,
                        metadata={
                            "variable_count": len(hf.variables),
                            "required_count": sum(
                                1 for v in hf.variables if v.required
                            ),
                        },
                    )
                )
            elif "metadata" in uri_template:
                resources.append(
                    Resource(
                        uri=f"vibey://handoffs/{hf.id}/metadata",
                        name=f"{hf.name} - Metadata",
                        description=hf.purpose,
                        mimeType=MIME_TYPE_JSON,
                        metadata={
                            "from_agent": hf.from_agent,
                            "to_agents": hf.to_agents,
                        },
                    )
                )
            elif "rendered" in uri_template:
                resources.append(
                    Resource(
                        uri=f"vibey://handoffs/{hf.id}/rendered",
                        name=f"{hf.name} - Rendered",
                        description="Template rendered with sample values",
                        mimeType=MIME_TYPE_MARKDOWN,
                    )
                )
            else:
                # Full template resource
                resources.append(
                    Resource(
                        uri=f"vibey://handoffs/{hf.id}",
                        name=hf.name,
                        description=hf.purpose,
                        mimeType=MIME_TYPE_JINJA2_MARKDOWN,
                        metadata={
                            "version": hf.version,
                            "from_agent": hf.from_agent,
                            "to_agents": hf.to_agents,
                            "variables": len(hf.variables),
                        },
                    )
                )

        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Read handoff resource content by URI.

        Args:
            uri: Resource URI (e.g., "vibey://handoffs/diagram-handoff")

        Returns:
            ResourceContent with the handoff data

        Raises:
            ResourceNotFoundError: If handoff doesn't exist
        """
        parsed = self.parse_uri(uri)
        handoff_id = parsed["id"]
        subresource = parsed.get("subresource")

        handoff = self._find_handoff(handoff_id)
        if not handoff:
            raise ResourceNotFoundError(uri, f"Handoff not found: {handoff_id}")

        if subresource == "variables":
            return await self._read_variables(handoff, uri)
        elif subresource == "metadata":
            return await self._read_metadata(handoff, uri)
        elif subresource == "rendered":
            return await self._read_rendered(handoff, uri)
        else:
            return await self._read_full_template(handoff, uri)

    async def _read_full_template(
        self, hf: HandoffDefinition, uri: str
    ) -> ResourceContent:
        """
        Read full handoff template content.

        Args:
            hf: HandoffDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with template text
        """
        if hf.filepath and hf.filepath.exists():
            content = hf.filepath.read_text()
        else:
            content = f"# {hf.name}\n\nTemplate file not found."

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_JINJA2_MARKDOWN,
            text=content,
        )

    async def _read_variables(
        self, hf: HandoffDefinition, uri: str
    ) -> ResourceContent:
        """
        Read handoff variables as JSON Schema.

        Args:
            hf: HandoffDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with JSON Schema for variables
        """
        schema: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": f"{hf.name} Variables",
            "description": f"Variable schema for {hf.name} handoff template",
            "handoff_id": hf.id,
            "handoff_name": hf.name,
            "properties": {},
            "required": [],
        }

        for var in hf.variables:
            prop: Dict[str, Any] = {
                "type": var.type if var.type != "array" else "array",
                "description": var.description or f"Variable: {var.name}",
            }
            if var.default is not None:
                prop["default"] = var.default
            schema["properties"][var.name] = prop
            if var.required:
                schema["required"].append(var.name)

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_JSON,
            text=json.dumps(schema, indent=2),
        )

    async def _read_metadata(
        self, hf: HandoffDefinition, uri: str
    ) -> ResourceContent:
        """
        Read handoff metadata as JSON.

        Args:
            hf: HandoffDefinition to read
            uri: Original request URI

        Returns:
            ResourceContent with JSON metadata
        """
        metadata = {
            "id": hf.id,
            "name": hf.name,
            "version": hf.version,
            "from_agent": hf.from_agent,
            "to_agents": hf.to_agents,
            "purpose": hf.purpose,
            "description": hf.description,
            "variable_count": len(hf.variables),
            "required_variables": [v.name for v in hf.variables if v.required],
        }

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_JSON,
            text=json.dumps(metadata, indent=2),
        )

    async def _read_rendered(
        self, hf: HandoffDefinition, uri: str
    ) -> ResourceContent:
        """
        Render handoff template with sample data.

        Args:
            hf: HandoffDefinition to render
            uri: Original request URI

        Returns:
            ResourceContent with rendered markdown
        """
        if not hf.filepath or not hf.filepath.exists():
            return ResourceContent(
                uri=uri,
                mimeType=MIME_TYPE_MARKDOWN,
                text="# Template Not Found",
            )

        # Read template content and remove frontmatter
        raw_content = hf.filepath.read_text()
        template_content = self._strip_frontmatter(raw_content)

        # Generate sample data for variables
        sample_data = self._generate_sample_data(hf)

        # Render template
        try:
            from jinja2 import BaseLoader, Environment

            env = Environment(loader=BaseLoader())
            template = env.from_string(template_content)
            rendered = template.render(**sample_data)
        except Exception as e:
            rendered = (
                f"# Rendering Error\n\n"
                f"Error: {str(e)}\n\n"
                f"## Raw Template\n\n{template_content}"
            )

        return ResourceContent(
            uri=uri,
            mimeType=MIME_TYPE_MARKDOWN,
            text=rendered,
        )

    def _strip_frontmatter(self, content: str) -> str:
        """
        Strip YAML frontmatter from content.

        Args:
            content: Full file content with potential frontmatter

        Returns:
            Content with frontmatter removed
        """
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

    def _generate_sample_data(self, hf: HandoffDefinition) -> Dict[str, Any]:
        """
        Generate sample data for template rendering.

        Args:
            hf: HandoffDefinition with variable definitions

        Returns:
            Dict with sample values for all variables
        """
        sample: Dict[str, Any] = {
            "config": {"roles": {}},
            "handoff_title": f"Sample {hf.name}",
            "handoff_date": "2025-01-01",
        }

        for var in hf.variables:
            if var.default is not None:
                sample[var.name] = var.default
            elif var.type == "string":
                sample[var.name] = f"[{var.name}]"
            elif var.type == "number":
                sample[var.name] = 0
            elif var.type == "boolean":
                sample[var.name] = True
            elif var.type == "array":
                sample[var.name] = []
            else:
                sample[var.name] = f"<{var.name}>"

        return sample

    def _discover_handoffs(self) -> List[HandoffDefinition]:
        """
        Discover all handoff templates.

        Returns:
            List of HandoffDefinition objects
        """
        if self._cache is not None:
            return self._cache

        handoffs = []
        if not self._handoffs_dir.exists():
            logger.warning(f"Handoffs directory not found: {self._handoffs_dir}")
            return handoffs

        for filepath in self._handoffs_dir.glob("*.md"):
            # Skip README
            if filepath.name.lower() == "readme.md":
                continue

            try:
                content = filepath.read_text()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        if frontmatter:
                            handoff = HandoffDefinition.from_frontmatter(
                                frontmatter, filepath
                            )
                            handoffs.append(handoff)
                            logger.debug(f"Discovered handoff: {handoff.id}")
            except Exception as e:
                logger.error(f"Error parsing handoff {filepath}: {e}")

        logger.info(f"Discovered {len(handoffs)} handoff templates")
        self._cache = handoffs
        return handoffs

    def _find_handoff(self, handoff_id: str) -> Optional[HandoffDefinition]:
        """
        Find handoff by ID.

        Args:
            handoff_id: Handoff ID to find

        Returns:
            HandoffDefinition or None if not found
        """
        for hf in self._discover_handoffs():
            if hf.id == handoff_id:
                return hf
        return None

    def get_handoffs_from_agent(self, agent_id: str) -> List[HandoffDefinition]:
        """
        Get all handoffs originating from a specific agent.

        Args:
            agent_id: Agent ID to filter by

        Returns:
            List of handoffs from that agent
        """
        return [
            hf for hf in self._discover_handoffs() if hf.from_agent == agent_id
        ]

    def get_handoffs_to_agent(self, agent_id: str) -> List[HandoffDefinition]:
        """
        Get all handoffs targeting a specific agent.

        Args:
            agent_id: Agent ID to filter by

        Returns:
            List of handoffs to that agent
        """
        return [
            hf for hf in self._discover_handoffs() if agent_id in hf.to_agents
        ]

    def invalidate_cache(self) -> None:
        """Invalidate handoff cache."""
        self._cache = None
        logger.debug("Handoff resource cache invalidated")
