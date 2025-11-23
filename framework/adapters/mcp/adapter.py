"""
MCP Adapter - Generates MCP tools from Vibey assets.

This is the canonical source for MCP tool generation. Other MCP-based
adapters (Goose, JetBrains) should compose this adapter rather than
duplicating tool generation logic.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from ..base import BaseAdapter
from ..types import ExportResult, PlatformCapabilities
from framework.mcp.discovery import (
    ToolDiscovery,
    AgentDefinition,
    WorkflowDefinition,
)

logger = logging.getLogger(__name__)


# Map types to JSON Schema types
TYPE_MAP = {
    'string': 'string',
    'integer': 'integer',
    'boolean': 'boolean',
    'array': 'array',
    'object': 'object',
    'number': 'number',
}


class MCPAdapter(BaseAdapter):
    """
    MCP (Model Context Protocol) adapter.

    Generates MCP tool definitions from Vibey agents and workflows.
    This is the canonical source for all MCP tool generation.

    Example:
        >>> adapter = MCPAdapter(root_dir=Path('.'))
        >>> tools = adapter.get_tools()
        >>> print(f"Generated {len(tools)} MCP tools")

        >>> # Export to directory
        >>> result = adapter.export(Path('./mcp-export'))
    """

    platform_name = "mcp"
    display_name = "Model Context Protocol"
    description = "MCP tools for AI assistants (Claude Code, Goose, JetBrains)"

    def __init__(
        self,
        root_dir: Path,
        tool_prefix: str = "vibey",
        cache_ttl: int = 60
    ):
        """
        Initialize MCP adapter.

        Args:
            root_dir: Root directory of Vibey repository
            tool_prefix: Prefix for tool names (default: "vibey")
            cache_ttl: Cache time-to-live in seconds (default: 60)
        """
        self.root_dir = Path(root_dir)
        self.tool_prefix = tool_prefix

        # Use existing discovery system
        self._discovery = ToolDiscovery(
            root_dir=self.root_dir,
            cache_ttl=cache_ttl,
            tool_prefix=tool_prefix
        )

    @property
    def capabilities(self) -> PlatformCapabilities:
        """MCP capabilities."""
        return PlatformCapabilities(
            agents=True,
            workflows=True,
            handoffs=False,
            real_time_discovery=True,  # Cache with TTL
            recipes=False,
            extension_manifest=False,
        )

    def get_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all MCP tools.

        Uses cached discovery for efficiency.

        Args:
            force_refresh: Force cache refresh

        Returns:
            List of MCP tool definitions
        """
        return self._discovery.get_all_tools(force_refresh)

    def get_agent_tools(self) -> List[Dict[str, Any]]:
        """Get only agent tools."""
        return self._discovery.get_agent_tools()

    def get_workflow_tools(self) -> List[Dict[str, Any]]:
        """Get only workflow tools."""
        return self._discovery.get_workflow_tools()

    def get_tool_by_name(self, name: str) -> Dict[str, Any]:
        """Get a specific tool by name."""
        return self._discovery.get_tool_by_name(name)

    def get_agents(self) -> List[AgentDefinition]:
        """Get all discovered agents."""
        return self._discovery.get_agents()

    def get_workflows(self) -> List[WorkflowDefinition]:
        """Get all discovered workflows."""
        return self._discovery.get_workflows()

    def translate_agent(self, agent: AgentDefinition) -> Dict[str, Any]:
        """
        Convert agent to MCP tool schema.

        Args:
            agent: AgentDefinition from discovery

        Returns:
            MCP tool definition dict
        """
        tool_name = f"{self.tool_prefix}_{agent.id.replace('-', '_')}"

        # Build input schema from agent inputs
        properties = {}
        required = []

        for inp in agent.inputs:
            prop_name = inp.get('name', '')
            if not prop_name:
                continue

            prop_type = TYPE_MAP.get(inp.get('type', 'string'), 'string')
            prop_def = {
                'type': prop_type,
                'description': inp.get('description', ''),
            }

            if 'default' in inp:
                prop_def['default'] = inp['default']

            properties[prop_name] = prop_def

            if inp.get('required', False):
                required.append(prop_name)

        # Build description including triggers for context
        description = agent.description or f"{agent.name} agent"
        if agent.triggers.get('keywords'):
            keywords = agent.triggers['keywords'][:5]
            description += f" (triggers: {', '.join(keywords)})"

        return {
            'name': tool_name,
            'title': agent.name,
            'description': description,
            'inputSchema': {
                'type': 'object',
                'properties': properties,
                'required': required,
            },
            '_metadata': {
                'asset_type': 'agent',
                'asset_id': agent.id,
                'agent_type': agent.type,
                'triggers': agent.triggers,
                'aliases': agent.aliases,
            }
        }

    def translate_workflow(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """
        Convert workflow to MCP tool schema.

        Args:
            workflow: WorkflowDefinition from discovery

        Returns:
            MCP tool definition dict
        """
        tool_name = f"{self.tool_prefix}_workflow_{workflow.id.replace('-', '_')}"

        # Build input schema from workflow inputs
        properties = {}
        required = []

        for inp in workflow.inputs:
            prop_name = inp.get('name', '')
            if not prop_name:
                continue

            prop_type = TYPE_MAP.get(inp.get('type', 'string'), 'string')
            prop_def = {
                'type': prop_type,
                'description': inp.get('description', ''),
            }

            if 'default' in inp:
                prop_def['default'] = inp['default']

            properties[prop_name] = prop_def

            if inp.get('required', False):
                required.append(prop_name)

        # Build description including steps summary
        description = workflow.description or f"{workflow.name} workflow"
        if workflow.steps:
            step_count = len(workflow.steps)
            description += f" ({step_count} steps"
            if workflow.duration:
                description += f", {workflow.duration}"
            description += ")"

        return {
            'name': tool_name,
            'title': f"Workflow: {workflow.name}",
            'description': description,
            'inputSchema': {
                'type': 'object',
                'properties': properties,
                'required': required,
            },
            '_metadata': {
                'asset_type': 'workflow',
                'asset_id': workflow.id,
                'workflow_type': workflow.type,
                'steps': [
                    {'order': s.order, 'name': s.name, 'agent': s.agent}
                    for s in workflow.steps
                ],
                'quality_gates': [
                    {'name': g.name, 'type': g.type, 'threshold': g.threshold}
                    for g in workflow.quality_gates
                ],
            }
        }

    def export(self, output_dir: Path) -> ExportResult:
        """
        Export MCP tools to directory.

        Creates:
        - tools.json: List of all tool definitions
        - server-config.json: MCP server configuration

        Args:
            output_dir: Directory to write files

        Returns:
            ExportResult with created files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        files = []
        errors = []

        try:
            # Export tools
            tools = self.get_tools()
            tools_path = output_dir / "tools.json"
            tools_path.write_text(json.dumps(tools, indent=2))
            files.append(tools_path)

            # Export server config
            config = self._generate_server_config(tools)
            config_path = output_dir / "server-config.json"
            config_path.write_text(json.dumps(config, indent=2))
            files.append(config_path)

            logger.info(f"Exported {len(tools)} MCP tools to {output_dir}")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            errors.append(str(e))

        return ExportResult(
            platform=self.platform_name,
            files=files,
            errors=errors
        )

    def _generate_server_config(self, tools: List[Dict]) -> Dict[str, Any]:
        """Generate MCP server configuration."""
        agent_tools = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'agent']
        workflow_tools = [t for t in tools if t.get('_metadata', {}).get('asset_type') == 'workflow']

        return {
            "name": "vibey",
            "version": "1.0.0",
            "description": "Vibey Agent Framework MCP Server",
            "command": "python -m framework.mcp.server",
            "args": ["--roadmap-root", ".vibey/roadmap"],
            "capabilities": {
                "tools": len(tools),
                "agents": len(agent_tools),
                "workflows": len(workflow_tools),
            },
            "tool_prefix": self.tool_prefix,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return self._discovery.get_stats()

    def invalidate_cache(self) -> None:
        """Invalidate the tool cache."""
        self._discovery.invalidate_cache()
