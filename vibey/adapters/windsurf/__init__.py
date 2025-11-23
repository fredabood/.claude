"""
Windsurf Platform Adapter.

Exports Vibey framework to Windsurf's configuration format:
- MCP configuration (same format as Claude Desktop)
- WINDSURF.md context file

Windsurf has native MCP support with the same config schema
as Claude Desktop, enabling direct reuse of the Vibey MCP server.
"""

from .adapter import WindsurfAdapter

__all__ = ["WindsurfAdapter"]
