"""
Continue.dev Platform Adapter.

Exports Vibey framework to Continue.dev's configuration format:
- .continuerc.yaml (workspace config)
- MCP server configuration
- Custom prompts from agent frontmatter

Continue.dev has native MCP support, enabling direct reuse
of the Vibey MCP server (46 tools).
"""

from .adapter import ContinueAdapter
from .context_generator import ContinueContextGenerator
from .settings_generator import ContinueSettingsGenerator

__all__ = [
    "ContinueAdapter",
    "ContinueContextGenerator",
    "ContinueSettingsGenerator",
]
