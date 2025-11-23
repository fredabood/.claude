"""
Continue.dev Settings Generator.

Generates .continuerc.yaml configuration files with MCP server settings.
This ensures zero-drift: the generated config always matches the source.

Continue Configuration:
- .continuerc.yaml for workspace-level config
- ~/.continue/config.yaml for global config
- mcpServers section for MCP server configuration
- prompts section for custom agent prompts
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml

from vibey.mcp.discovery.agents import AgentDefinition, AgentDiscovery
from vibey.mcp.discovery.workflows import WorkflowDefinition, WorkflowDiscovery

logger = logging.getLogger(__name__)


@dataclass
class GeneratedSettings:
    """Result of settings generation."""
    content: str
    checksum: str
    mcp_servers: int
    prompts_count: int
    generated_at: datetime


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


class ContinueSettingsGenerator:
    """
    Generate Continue.dev configuration from Vibey frontmatter.

    Zero-Drift Guarantee:
    - MCP server config generated from standard settings
    - Prompts generated from agent frontmatter
    - Checksums enable drift detection

    Example:
        >>> generator = ContinueSettingsGenerator(Path("/path/to/vibey"))
        >>> result = generator.generate()
        >>> Path(".continuerc.yaml").write_text(result.content)
    """

    def __init__(self, root_dir: Path):
        """
        Initialize settings generator.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.agent_discovery = AgentDiscovery(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)

    def generate(
        self,
        mcp_command: str = "python",
        mcp_args: Optional[List[str]] = None,
        include_prompts: bool = True,
        include_rules: bool = True,
    ) -> GeneratedSettings:
        """
        Generate Continue configuration.

        Args:
            mcp_command: Python command for MCP server
            mcp_args: Arguments for MCP server (default: [-m, vibey.mcp.server])
            include_prompts: Generate prompts from agent frontmatter
            include_rules: Include project rules section

        Returns:
            GeneratedSettings with content and metadata
        """
        if mcp_args is None:
            mcp_args = ["-m", "vibey.mcp.server"]

        agents = self.agent_discovery.discover()
        workflows = self.workflow_discovery.discover()

        config = self._build_config(
            agents=agents,
            workflows=workflows,
            mcp_command=mcp_command,
            mcp_args=mcp_args,
            include_prompts=include_prompts,
            include_rules=include_rules,
        )

        # Use safe YAML dump
        content = yaml.dump(
            config,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        # Add header comment
        header = self._build_header()
        full_content = header + content

        checksum = self._calculate_checksum(full_content)

        return GeneratedSettings(
            content=full_content,
            checksum=checksum,
            mcp_servers=1,  # Vibey MCP server
            prompts_count=len(agents) if include_prompts else 0,
            generated_at=datetime.now(timezone.utc),
        )

    def _build_config(
        self,
        agents: List[AgentDefinition],
        workflows: List[WorkflowDefinition],
        mcp_command: str,
        mcp_args: List[str],
        include_prompts: bool,
        include_rules: bool,
    ) -> Dict[str, Any]:
        """Build the configuration dictionary."""
        config: Dict[str, Any] = {
            "name": "vibey-assistant",
            "version": "1.0.0",
            "schema": "v1",
        }

        # MCP Servers
        config["mcpServers"] = [
            {
                "name": "Vibey Framework",
                "command": mcp_command,
                "args": mcp_args,
            }
        ]

        # Context providers
        config["context"] = [
            {"provider": "code"},
            {"provider": "docs"},
            {"provider": "diff"},
            {"provider": "terminal"},
        ]

        # Prompts from agent frontmatter
        if include_prompts and agents:
            config["prompts"] = self._build_prompts(agents)

        # Rules section
        if include_rules:
            config["rules"] = self._build_rules()

        return config

    def _build_prompts(self, agents: List[AgentDefinition]) -> List[Dict[str, str]]:
        """Build prompts from agent frontmatter."""
        prompts = []

        for agent in agents:
            tool_name = agent.id.replace('-', '_')
            prompt = {
                "name": f"vibey-{tool_name}",
                "description": agent.description or f"{agent.name} agent",
                "prompt": self._build_agent_prompt(agent),
            }
            prompts.append(prompt)

        return prompts

    def _build_agent_prompt(self, agent: AgentDefinition) -> str:
        """Build prompt content for an agent."""
        tool_name = agent.id.replace('-', '_')
        lines = [
            f"You are the {agent.name}.",
            "",
        ]

        if agent.description:
            lines.append(agent.description)
            lines.append("")

        lines.extend([
            "## Instructions",
            "",
            f"Act as a specialized {agent.name.lower()} assistant.",
            "",
            "## Available Tools",
            "",
            f"Use the `vibey_{tool_name}` MCP tool for specialized tasks.",
            "Use other Vibey MCP tools as needed for roadmap and workflow management.",
        ])

        return "\n".join(lines)

    def _build_rules(self) -> List[str]:
        """Build project rules."""
        return [
            "Use Vibey MCP tools (prefixed with vibey_) for framework operations",
            "Follow structured workflows for multi-step tasks",
            "Validate quality gates before marking tasks complete",
            "Use agent specialization - each agent has domain expertise",
            "Reference roadmap status before starting new work",
        ]

    def _build_header(self) -> str:
        """Build YAML header comment."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"""# Continue.dev Configuration for Vibey Framework
# Generated: {timestamp}
# Generator: vibey-continue-adapter
# DO NOT EDIT: This file is generated from Vibey frontmatter
# Regenerate with: vibey deploy --platform continue

"""

    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for drift detection."""
        # Remove timestamp line for stable checksum
        lines = content.split("\n")
        stable_lines = [l for l in lines if "Generated:" not in l]
        stable_content = "\n".join(stable_lines)
        return hashlib.sha256(stable_content.encode()).hexdigest()[:16]

    def write_to_file(self, output_path: Path) -> GeneratedSettings:
        """
        Generate and write settings to file.

        Args:
            output_path: Path to write .continuerc.yaml

        Returns:
            GeneratedSettings with metadata
        """
        result = self.generate()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.content, encoding='utf-8')
        logger.info(
            f"Wrote {output_path}: {result.mcp_servers} MCP servers, "
            f"{result.prompts_count} prompts"
        )
        return result

    def generate_mcp_only(
        self,
        mcp_command: str = "python",
        mcp_args: Optional[List[str]] = None,
    ) -> str:
        """
        Generate minimal config with just MCP server.

        Useful for adding to existing Continue configuration.

        Args:
            mcp_command: Python command
            mcp_args: MCP server arguments

        Returns:
            YAML string with mcpServers section only
        """
        if mcp_args is None:
            mcp_args = ["-m", "vibey.mcp.server"]

        config = {
            "mcpServers": [
                {
                    "name": "Vibey Framework",
                    "command": mcp_command,
                    "args": mcp_args,
                }
            ]
        }

        return yaml.dump(config, default_flow_style=False, sort_keys=False)
