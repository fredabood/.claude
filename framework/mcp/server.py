"""
Vibey MCP Server.

Main MCP server implementation that exposes Vibey roadmap operations
as MCP tools, resources, and prompts.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Note: MCP Python SDK is required (pip install mcp)
# This is a placeholder implementation showing the structure
# The actual MCP SDK may have a different API

from .adapters.roadmap_adapter import RoadmapAdapter
from .tools.task_tools import get_task_tools, handle_task_tool
from .tools.sprint_tools import get_sprint_tools, handle_sprint_tool
from .tools.query_tools import get_query_tools, handle_query_tool
from .utils.errors import VibeyMCPError

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

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize Vibey MCP server.

        Args:
            roadmap_root: Path to roadmap root directory
        """
        self.roadmap_root = Path(roadmap_root)
        self.adapter = RoadmapAdapter(str(self.roadmap_root))
        logger.info(f"Initialized Vibey MCP Server (roadmap_root: {roadmap_root})")

    async def run(self):
        """
        Run the MCP server.

        This is a placeholder for the actual MCP server implementation.
        Once the MCP Python SDK is installed, this will use the SDK's
        server class and stdio transport.

        Example implementation structure:
            from mcp import Server
            from mcp.server.stdio import stdio_server

            server = Server("vibey-roadmap")

            @server.list_tools()
            async def handle_list_tools():
                return self.get_tools()

            @server.call_tool()
            async def handle_call_tool(name: str, arguments: dict):
                return await self.handle_tool_call(name, arguments)

            async with stdio_server() as streams:
                await server.run(streams[0], streams[1])
        """
        logger.info("MCP Server starting...")

        # TODO: Implement actual MCP server once SDK is available
        # For now, this is a placeholder that demonstrates the structure

        print("Vibey MCP Server - Placeholder Implementation", file=sys.stderr)
        print("", file=sys.stderr)
        print("To complete the implementation:", file=sys.stderr)
        print("1. Install MCP Python SDK: pip install mcp", file=sys.stderr)
        print("2. Implement server using SDK's Server class", file=sys.stderr)
        print("3. Set up stdio or HTTP+SSE transport", file=sys.stderr)
        print("", file=sys.stderr)
        print("Server structure ready. Tools available:", file=sys.stderr)

        tools = self.get_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)

        print("", file=sys.stderr)
        print("Waiting for MCP SDK installation...", file=sys.stderr)

        # Keep server alive
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Server shutting down...")

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

    def get_tools(self) -> list[Dict[str, Any]]:
        """
        Get all available tools.

        Returns:
            List of tool definitions
        """
        tools = []

        # Task management tools (Sprint 1)
        tools.extend(get_task_tools())

        # Sprint management tools (Sprint 2)
        tools.extend(get_sprint_tools())

        # Query tools (Sprint 2)
        tools.extend(get_query_tools())

        # More tools will be added in future sprints:
        # - Sprint 2: Documentation sync tools (remaining)
        # - Sprint 3: Resources and prompts

        return tools

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
            if tool_name.startswith("vibey_") and ("query" in tool_name or "list" in tool_name or "status" in tool_name):
                return await handle_query_tool(tool_name, arguments, self.adapter)

            # More tool routing will be added in future sprints

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
