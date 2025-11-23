"""
Cursor Platform Adapter.

Exports Vibey framework to Cursor's configuration format:
- .cursor/mcp.json for MCP server configuration
- .cursorrules for project-specific AI rules
- CURSOR.md context file

Cursor has native MCP support (since Nov 2024) with the same config
schema as Claude Desktop, enabling direct reuse of the Vibey MCP server.
"""

from .adapter import CursorAdapter

__all__ = ["CursorAdapter"]
