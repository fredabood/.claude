"""
GitHub Copilot Platform Adapter.

Exports Vibey framework to GitHub Copilot's configuration format:
- .github/copilot-instructions.md for repository instructions
- .github/agents/*.md for custom agent profiles
- MCP configuration for Copilot CLI

GitHub Copilot supports MCP via the Copilot CLI and VS Code Copilot,
enabling integration with Vibey's 46 MCP tools.
"""

from .adapter import CopilotAdapter

__all__ = ["CopilotAdapter"]
