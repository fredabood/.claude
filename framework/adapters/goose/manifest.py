"""
Goose Extension Manifest Generator.

Generates the goose-extension.yaml that registers Vibey as a Goose extension.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """
    Generate Goose extension manifest.

    The manifest registers the Vibey MCP server as a Goose extension,
    making all Vibey tools available to Goose.

    Example:
        >>> generator = ManifestGenerator()
        >>> manifest = generator.generate(
        ...     tools_count=35,
        ...     agent_count=19,
        ...     workflow_count=16
        ... )
    """

    DEFAULT_VERSION = "1.0.0"
    DEFAULT_NAME = "vibey"

    def __init__(
        self,
        name: str = DEFAULT_NAME,
        version: str = DEFAULT_VERSION,
    ):
        """
        Initialize manifest generator.

        Args:
            name: Extension name (default: "vibey")
            version: Extension version (default: "1.0.0")
        """
        self.name = name
        self.version = version

    def generate(
        self,
        tools_count: int = 0,
        agent_count: int = 0,
        workflow_count: int = 0,
        recipe_count: int = 0,
        custom_command: Optional[str] = None,
        custom_args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate Goose extension manifest.

        Args:
            tools_count: Total number of MCP tools
            agent_count: Number of agent tools
            workflow_count: Number of workflow tools
            recipe_count: Number of generated recipes
            custom_command: Custom MCP server command
            custom_args: Custom MCP server arguments

        Returns:
            Extension manifest dict
        """
        manifest = {
            "name": self.name,
            "version": self.version,
            "type": "mcp",
            "description": self._generate_description(
                tools_count, agent_count, workflow_count
            ),
        }

        # MCP server configuration
        manifest["mcp"] = {
            "command": custom_command or "python",
            "args": custom_args or [
                "-m", "framework.mcp.server",
                "--roadmap-root", ".vibey/roadmap"
            ],
        }

        # Capabilities summary
        manifest["capabilities"] = {
            "tools": tools_count,
            "agents": agent_count,
            "workflows": workflow_count,
            "recipes": recipe_count,
            "dynamic_discovery": True,
        }

        # Categories for Goose extension registry
        manifest["categories"] = self._generate_categories()

        # Metadata
        manifest["metadata"] = {
            "homepage": "https://github.com/vibey/vibey-framework",
            "documentation": "https://vibey.dev/docs",
            "license": "MIT",
        }

        return manifest

    def _generate_description(
        self,
        tools_count: int,
        agent_count: int,
        workflow_count: int
    ) -> str:
        """Generate extension description."""
        parts = [
            "Vibey Agent Framework - Intelligent agent orchestration for AI coding assistants.",
        ]

        if tools_count:
            parts.append(
                f"Provides {tools_count} tools ({agent_count} agents, {workflow_count} workflows) "
                "covering planning, development, quality, and documentation."
            )

        parts.append(
            "Features dynamic tool discovery from YAML frontmatter for zero-drift operation."
        )

        return " ".join(parts)

    def _generate_categories(self) -> List[str]:
        """Generate extension categories."""
        return [
            "development",
            "planning",
            "quality",
            "documentation",
            "orchestration",
        ]

    def to_yaml(self, manifest: Dict[str, Any]) -> str:
        """
        Convert manifest to YAML string.

        Args:
            manifest: Manifest dict

        Returns:
            YAML-formatted string
        """
        import yaml
        return yaml.dump(manifest, default_flow_style=False, sort_keys=False)
