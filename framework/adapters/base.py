"""
Base classes for platform adapters.

Two adapter types:
- BaseAdapter: Translates directly from assets (MCP, Cursor, Aider)
- CompositeAdapter: Builds on other adapters (Goose uses MCP)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .types import ExportResult, PlatformCapabilities, AdapterInfo

if TYPE_CHECKING:
    from framework.mcp.discovery import AgentDefinition, WorkflowDefinition


class BaseAdapter(ABC):
    """
    Base class for adapters that translate directly from assets.

    Base adapters read from the Asset Registry and produce platform-specific
    output without depending on other adapters.

    Examples: MCPAdapter, CursorAdapter, AiderAdapter, ClaudeCodeAdapter

    Usage:
        >>> adapter = MCPAdapter(registry)
        >>> tools = adapter.get_tools()
        >>> result = adapter.export(Path("./output"))
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        Unique platform identifier.

        Used for CLI commands and file paths.
        Example: "mcp", "cursor", "aider"
        """

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable platform name.

        Example: "Model Context Protocol", "Cursor", "Aider"
        """

    @property
    def description(self) -> str:
        """Platform description."""
        return f"{self.display_name} adapter"

    @property
    def capabilities(self) -> PlatformCapabilities:
        """Capabilities supported by this adapter."""
        return PlatformCapabilities()

    def get_info(self) -> AdapterInfo:
        """Get adapter information."""
        return AdapterInfo(
            platform_name=self.platform_name,
            display_name=self.display_name,
            description=self.description,
            adapter_type="base",
            capabilities=self.capabilities,
        )

    @abstractmethod
    def translate_agent(self, agent: "AgentDefinition") -> Any:
        """
        Convert agent to platform-native format.

        Args:
            agent: AgentDefinition from asset registry

        Returns:
            Platform-specific representation
        """

    @abstractmethod
    def translate_workflow(self, workflow: "WorkflowDefinition") -> Any:
        """
        Convert workflow to platform-native format.

        Args:
            workflow: WorkflowDefinition from asset registry

        Returns:
            Platform-specific representation
        """

    @abstractmethod
    def export(self, output_dir: Path) -> ExportResult:
        """
        Export all assets to platform format.

        Args:
            output_dir: Directory to write exported files

        Returns:
            ExportResult with list of created files
        """

    def validate(self) -> List[str]:
        """
        Validate adapter configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        return []


class CompositeAdapter(ABC):
    """
    Base class for adapters that compose other adapters.

    Composite adapters build on top of base adapters, adding platform-specific
    features without duplicating translation logic.

    Examples: GooseAdapter (uses MCPAdapter), JetBrainsAdapter (uses MCPAdapter)

    Usage:
        >>> mcp = MCPAdapter(registry)
        >>> goose = GooseAdapter(mcp, registry)
        >>> tools = goose.get_tools()  # Delegates to MCPAdapter
        >>> recipes = goose.get_recipes()  # Goose-specific
    """

    def __init__(self, base_adapter: BaseAdapter):
        """
        Initialize composite adapter.

        Args:
            base_adapter: The base adapter to compose
        """
        self._base = base_adapter

    @property
    def base(self) -> BaseAdapter:
        """The base adapter this composite uses."""
        return self._base

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        Unique platform identifier.

        Example: "goose", "jetbrains"
        """

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable platform name.

        Example: "Goose (Block)", "JetBrains AI Assistant"
        """

    @property
    def description(self) -> str:
        """Platform description."""
        return f"{self.display_name} adapter (uses {self.base.display_name})"

    @property
    def base_platform(self) -> str:
        """The platform name of the base adapter."""
        return self._base.platform_name

    @property
    def capabilities(self) -> PlatformCapabilities:
        """Capabilities supported by this adapter."""
        # Start with base capabilities
        caps = self._base.capabilities
        return caps

    def get_info(self) -> AdapterInfo:
        """Get adapter information."""
        return AdapterInfo(
            platform_name=self.platform_name,
            display_name=self.display_name,
            description=self.description,
            adapter_type="composite",
            base_platform=self.base_platform,
            capabilities=self.capabilities,
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Delegate tool generation to base adapter.

        This ensures no duplication of translation logic.

        Returns:
            List of tools from base adapter
        """
        if hasattr(self._base, 'get_tools'):
            return self._base.get_tools()
        raise NotImplementedError(
            f"Base adapter {self._base.platform_name} doesn't support get_tools()"
        )

    @abstractmethod
    def export(self, output_dir: Path) -> ExportResult:
        """
        Export all assets to platform format.

        Args:
            output_dir: Directory to write exported files

        Returns:
            ExportResult with list of created files
        """

    def validate(self) -> List[str]:
        """
        Validate adapter configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        # Validate base adapter
        errors.extend(self._base.validate())
        return errors
