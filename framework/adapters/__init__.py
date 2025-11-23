"""
Platform Adapters for Vibey Framework.

Provides extensible translation of Vibey assets (agents, workflows, handoffs)
to platform-specific formats with zero drift.

Architecture:
- BaseAdapter: Direct translation from assets (MCP, Cursor, Aider)
- CompositeAdapter: Builds on base adapters (Goose uses MCP)

Example:
    >>> from framework.adapters import AdapterRegistry, MCPAdapter, GooseAdapter
    >>>
    >>> # Create adapters
    >>> mcp = MCPAdapter(root_dir=Path('.'))
    >>> goose = GooseAdapter(mcp)
    >>>
    >>> # Register adapters
    >>> registry = AdapterRegistry()
    >>> registry.register(mcp)
    >>> registry.register(goose)
    >>>
    >>> # Export to all platforms
    >>> results = registry.export_all(Path('./exports'))
"""

from .base import BaseAdapter, CompositeAdapter
from .registry import AdapterRegistry
from .types import ExportResult, PlatformCapabilities, AdapterInfo
from .mcp import MCPAdapter
from .goose import GooseAdapter, RecipeGenerator, ManifestGenerator

__all__ = [
    # Base classes
    "BaseAdapter",
    "CompositeAdapter",
    # Registry
    "AdapterRegistry",
    # Types
    "ExportResult",
    "PlatformCapabilities",
    "AdapterInfo",
    # Adapters
    "MCPAdapter",
    "GooseAdapter",
    # Generators
    "RecipeGenerator",
    "ManifestGenerator",
]


def create_default_registry(root_dir=None) -> AdapterRegistry:
    """
    Create a registry with default adapters.

    Args:
        root_dir: Root directory for asset discovery (default: current dir)

    Returns:
        AdapterRegistry with MCP and Goose adapters registered
    """
    from pathlib import Path

    root_dir = Path(root_dir) if root_dir else Path.cwd()

    # Create adapters
    mcp_adapter = MCPAdapter(root_dir=root_dir)
    goose_adapter = GooseAdapter(mcp_adapter)

    # Register
    registry = AdapterRegistry()
    registry.register(mcp_adapter)
    registry.register(goose_adapter)

    return registry
