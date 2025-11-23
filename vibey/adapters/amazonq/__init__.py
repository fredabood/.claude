"""
Amazon Q Developer Platform Adapter.

Exports Vibey framework to Amazon Q Developer configuration format:
- .amazonq/mcp.json for MCP server configuration
- AMAZONQ.md context file

Amazon Q Developer has full MCP support (GA April 2025),
enabling integration with Vibey's 46 MCP tools across
CLI and IDE plugins (VS Code, JetBrains).
"""

from .adapter import AmazonQAdapter

__all__ = ["AmazonQAdapter"]
