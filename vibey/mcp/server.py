"""
Vibey MCP Server.

Main MCP server implementation that exposes Vibey roadmap operations
as MCP tools, resources, and prompts.

Now includes dynamic tool discovery for agents and workflows via
YAML frontmatter parsing.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Note: MCP Python SDK is required (pip install mcp)
# This is a placeholder implementation showing the structure
# The actual MCP SDK may have a different API

from .adapters.roadmap_adapter import RoadmapAdapter
from .tools.task_tools import get_task_tools, handle_task_tool
from .tools.sprint_tools import get_sprint_tools, handle_sprint_tool
from .tools.query_tools import get_query_tools, handle_query_tool
from .tools.content_tools import get_content_tools, handle_content_tool
from .utils.errors import VibeyMCPError
from .discovery import ToolDiscovery

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr to not interfere with stdio protocol
)
logger = logging.getLogger("vibey-mcp-server")


class VibeyMCPServer:
    """
    Vibey MCP Server.

    Exposes Vibey roadmap operations through the Model Context Protocol.

    Example:
        >>> server = VibeyMCPServer()
        >>> await server.run()
    """

    def __init__(
        self,
        roadmap_root: str = ".vibey/roadmap",
        framework_root: Optional[str] = None
    ):
        """
        Initialize Vibey MCP server.

        Args:
            roadmap_root: Path to roadmap root directory
            framework_root: Path to framework root (for agent/workflow discovery)
                           Defaults to current working directory
        """
        self.roadmap_root = Path(roadmap_root)
        self.framework_root = Path(framework_root) if framework_root else Path.cwd()
        self.adapter = RoadmapAdapter(str(self.roadmap_root))

        # Initialize dynamic tool discovery
        self.tool_discovery = ToolDiscovery(
            root_dir=self.framework_root,
            cache_ttl=60,  # Refresh cache every 60 seconds
            tool_prefix="vibey"
        )

        logger.info(f"Initialized Vibey MCP Server")
        logger.info(f"  Roadmap root: {roadmap_root}")
        logger.info(f"  Framework root: {self.framework_root}")

    async def run(self):
        """
        Run the MCP server using stdio transport.

        This implements the MCP protocol using the official Python SDK.
        """
        from mcp.server.fastmcp import FastMCP

        logger.info("MCP Server starting...")

        # Create MCP server using FastMCP
        mcp = FastMCP("vibey-roadmap")

        # Get tools and register them
        tools = self.get_tools()
        logger.info(f"Registering {len(tools)} tools...")

        # Create a wrapper for each tool
        for tool_def in tools:
            tool_name = tool_def['name']
            tool_desc = tool_def.get('description', '')

            # Create closure to capture tool_name
            async def make_handler(name):
                async def handler(**kwargs):
                    result = await self.handle_tool_call(name, kwargs)
                    content = result.get('content', [])
                    if content and isinstance(content, list):
                        return content[0].get('text', str(result))
                    return str(result)
                return handler

            # Register tool with FastMCP
            handler = await make_handler(tool_name)
            mcp.tool(name=tool_name, description=tool_desc)(handler)

        logger.info("Starting MCP server on stdio...")
        await mcp.run_stdio_async()

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities for MCP initialize response.

        Returns:
            Capabilities dict following MCP spec
        """
        return {
            "tools": {
                "listChanged": True  # We support tool list change notifications
            },
            "resources": {
                "subscribe": False  # Resources not implemented in Sprint 1
            },
            "prompts": {
                "listChanged": False  # Prompts not implemented in Sprint 1
            }
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available tools.

        Includes:
        - Static roadmap tools (task, sprint, query)
        - Dynamic agent tools (from frontmatter discovery)
        - Dynamic workflow tools (from frontmatter discovery)

        Returns:
            List of tool definitions
        """
        tools = []

        # Static roadmap management tools
        tools.extend(get_task_tools())
        tools.extend(get_sprint_tools())
        tools.extend(get_query_tools())

        # Content management tools
        tools.extend(get_content_tools())

        # Dynamic agent and workflow tools (from frontmatter discovery)
        try:
            discovered_tools = self.tool_discovery.get_all_tools()
            tools.extend(discovered_tools)
            logger.debug(f"Added {len(discovered_tools)} discovered tools")
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            # Continue with static tools even if discovery fails

        return tools

    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get statistics about discovered tools."""
        return self.tool_discovery.get_stats()

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle tool invocation.

        Routes tool calls to appropriate handlers.

        Args:
            tool_name: Name of tool to invoke
            arguments: Tool input arguments

        Returns:
            Tool response with content and isError flag
        """
        logger.info(f"Tool call: {tool_name} with args: {arguments}")

        try:
            # Route to task tools
            if tool_name.startswith("vibey_") and "task" in tool_name:
                return await handle_task_tool(tool_name, arguments, self.adapter)

            # Route to sprint tools
            if tool_name.startswith("vibey_") and ("sprint" in tool_name or "refresh" in tool_name):
                return await handle_sprint_tool(tool_name, arguments, self.adapter)

            # Route to query tools
            if tool_name.startswith("vibey_") and ("query" in tool_name or "roadmap" in tool_name):
                return await handle_query_tool(tool_name, arguments, self.adapter)

            # Route to content tools
            if tool_name.startswith("vibey_content_"):
                return await handle_content_tool(tool_name, arguments)

            # Route to dynamic agent/workflow tools
            if tool_name.startswith("vibey_"):
                tool_def = self.tool_discovery.get_tool_by_name(tool_name)
                if tool_def:
                    return await self._handle_dynamic_tool(tool_name, arguments, tool_def)

            # Unknown tool
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Unknown tool: {tool_name}"
                    }
                ],
                "isError": True
            }

        except VibeyMCPError as e:
            logger.error(f"Vibey error in {tool_name}: {e.message}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error: {e.message}"
                    }
                ],
                "isError": True
            }
        except Exception as e:
            logger.error(f"Unexpected error in {tool_name}: {str(e)}", exc_info=True)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Unexpected error: {str(e)}"
                    }
                ],
                "isError": True
            }


    async def _handle_dynamic_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle invocation of a dynamically discovered tool.

        For agents: Returns the agent's instructions and context
        For workflows: Returns the workflow steps and configuration

        Args:
            tool_name: Name of the tool
            arguments: Tool input arguments
            tool_def: Tool definition from discovery

        Returns:
            Tool response with content
        """
        metadata = tool_def.get('_metadata', {})
        asset_type = metadata.get('asset_type')
        asset_id = metadata.get('asset_id')

        if asset_type == 'agent':
            return await self._execute_agent_tool(asset_id, arguments, metadata)
        elif asset_type == 'workflow':
            return await self._execute_workflow_tool(asset_id, arguments, metadata)
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Unknown asset type: {asset_type}"
                    }
                ],
                "isError": True
            }

    async def _execute_agent_tool(
        self,
        agent_id: str,
        arguments: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an agent tool.

        Returns the agent's instructions and any relevant context
        for the AI assistant to follow.

        Args:
            agent_id: Agent identifier
            arguments: Input arguments from tool call
            metadata: Agent metadata from discovery

        Returns:
            Tool response with agent instructions
        """
        # Get the full agent definition
        agent = self.tool_discovery.agent_discovery.get_agent_by_id(agent_id)

        if not agent:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Agent not found: {agent_id}"
                    }
                ],
                "isError": True
            }

        # Read the agent's full markdown content
        agent_content = ""
        if agent.filepath and agent.filepath.exists():
            try:
                agent_content = agent.filepath.read_text()
                # Remove frontmatter for cleaner output
                if agent_content.startswith('---'):
                    parts = agent_content.split('---', 2)
                    if len(parts) >= 3:
                        agent_content = parts[2].strip()
            except Exception as e:
                logger.warning(f"Could not read agent file: {e}")

        # Build response with agent context
        response_parts = [
            f"# Agent: {agent.name}",
            f"**Type:** {agent.type}",
            f"**ID:** {agent.id}",
            "",
        ]

        if agent.description:
            response_parts.extend([
                f"**Description:** {agent.description}",
                "",
            ])

        # Include input arguments
        if arguments:
            response_parts.extend([
                "## Inputs Provided",
                "",
            ])
            for key, value in arguments.items():
                response_parts.append(f"- **{key}:** {value}")
            response_parts.append("")

        # Include agent instructions
        if agent_content:
            response_parts.extend([
                "## Agent Instructions",
                "",
                agent_content,
            ])

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(response_parts)
                }
            ],
            "isError": False
        }

    async def _execute_workflow_tool(
        self,
        workflow_id: str,
        arguments: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow tool.

        Returns the workflow steps and configuration for the
        AI assistant to orchestrate.

        Args:
            workflow_id: Workflow identifier
            arguments: Input arguments from tool call
            metadata: Workflow metadata from discovery

        Returns:
            Tool response with workflow steps
        """
        # Get the full workflow definition
        workflow = self.tool_discovery.workflow_discovery.get_workflow_by_id(workflow_id)

        if not workflow:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Workflow not found: {workflow_id}"
                    }
                ],
                "isError": True
            }

        # Read the workflow's full markdown content
        workflow_content = ""
        if workflow.filepath and workflow.filepath.exists():
            try:
                workflow_content = workflow.filepath.read_text()
                # Remove frontmatter for cleaner output
                if workflow_content.startswith('---'):
                    parts = workflow_content.split('---', 2)
                    if len(parts) >= 3:
                        workflow_content = parts[2].strip()
            except Exception as e:
                logger.warning(f"Could not read workflow file: {e}")

        # Build response with workflow context
        response_parts = [
            f"# Workflow: {workflow.name}",
            f"**Type:** {workflow.type}",
            f"**ID:** {workflow.id}",
            f"**Complexity:** {workflow.complexity}",
        ]

        if workflow.duration:
            response_parts.append(f"**Estimated Duration:** {workflow.duration}")

        response_parts.append("")

        if workflow.description:
            response_parts.extend([
                f"**Description:** {workflow.description}",
                "",
            ])

        # Include input arguments
        if arguments:
            response_parts.extend([
                "## Inputs Provided",
                "",
            ])
            for key, value in arguments.items():
                response_parts.append(f"- **{key}:** {value}")
            response_parts.append("")

        # Include workflow steps summary
        if workflow.steps:
            response_parts.extend([
                "## Workflow Steps",
                "",
            ])
            for step in workflow.steps:
                step_line = f"{step.order}. **{step.name}**"
                if step.agent:
                    step_line += f" (Agent: {step.agent})"
                if step.duration:
                    step_line += f" - {step.duration}"
                response_parts.append(step_line)
            response_parts.append("")

        # Include quality gates
        if workflow.quality_gates:
            response_parts.extend([
                "## Quality Gates",
                "",
            ])
            for gate in workflow.quality_gates:
                gate_line = f"- **{gate.name}** ({gate.type})"
                if gate.threshold:
                    gate_line += f" - Threshold: {gate.threshold}%"
                if gate.blocking:
                    gate_line += " [BLOCKING]"
                response_parts.append(gate_line)
            response_parts.append("")

        # Include full workflow instructions
        if workflow_content:
            response_parts.extend([
                "## Full Workflow Instructions",
                "",
                workflow_content,
            ])

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(response_parts)
                }
            ],
            "isError": False
        }


def main():
    """Main entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Vibey MCP Server - Roadmap management via MCP protocol"
    )
    parser.add_argument(
        "--roadmap-root",
        default=".vibey/roadmap",
        help="Path to roadmap root directory (default: .vibey/roadmap)"
    )
    args = parser.parse_args()

    # Create and run server
    server = VibeyMCPServer(roadmap_root=args.roadmap_root)

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
