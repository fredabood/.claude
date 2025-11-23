"""
VS Code Platform Adapter.

Exports Vibey framework to VS Code's native MCP configuration:
- .vscode/mcp.json for MCP server configuration
- VSCODE.md context file

VS Code has full native MCP support (GA July 2025) with support for
tools, resources, prompts, sampling, and authentication.
"""

from .adapter import VSCodeAdapter

__all__ = ["VSCodeAdapter"]
