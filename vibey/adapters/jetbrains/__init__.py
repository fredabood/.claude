"""
JetBrains AI Assistant Platform Adapter.

Exports Vibey framework to JetBrains IDEs configuration format:
- .idea/ai/mcp-servers.json for MCP server configuration
- JETBRAINS.md context file

JetBrains AI Assistant supports MCP via the IDE AI settings,
enabling integration with Vibey's 46 MCP tools across all
JetBrains IDEs (IntelliJ, PyCharm, WebStorm, GoLand, etc.).
"""

from .adapter import JetBrainsAdapter

__all__ = ["JetBrainsAdapter"]
