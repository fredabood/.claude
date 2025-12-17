"""
Unified command definitions.

Commands defined here are automatically registered to both CLI and MCP
interfaces via the @unified_command decorator.

Import command modules here to register them in the COMMAND_REGISTRY.
"""

# Import command modules to register them
from . import roadmap
from . import deploy
from . import docs

__all__ = ["roadmap", "deploy", "docs"]
