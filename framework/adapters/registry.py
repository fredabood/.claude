"""
Adapter Registry for managing platform adapters.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from .base import BaseAdapter, CompositeAdapter
from .types import ExportResult, AdapterInfo

logger = logging.getLogger(__name__)

AdapterType = Union[BaseAdapter, CompositeAdapter]


class AdapterRegistry:
    """
    Central registry for discovering and managing platform adapters.

    The registry maintains a collection of adapters and provides methods
    for listing, retrieving, and bulk exporting to all platforms.

    Example:
        >>> registry = AdapterRegistry()
        >>> registry.register(MCPAdapter(asset_registry))
        >>> registry.register(GooseAdapter(mcp_adapter, asset_registry))
        >>>
        >>> # List platforms
        >>> print(registry.list_platforms())
        ['mcp', 'goose']
        >>>
        >>> # Export to specific platform
        >>> result = registry.export('goose', Path('./output'))
        >>>
        >>> # Export to all platforms
        >>> results = registry.export_all(Path('./output'))
    """

    def __init__(self):
        """Initialize empty adapter registry."""
        self._adapters: Dict[str, AdapterType] = {}

    def register(self, adapter: AdapterType) -> None:
        """
        Register a platform adapter.

        Args:
            adapter: BaseAdapter or CompositeAdapter instance

        Raises:
            ValueError: If adapter with same platform_name already registered
        """
        name = adapter.platform_name
        if name in self._adapters:
            raise ValueError(f"Adapter already registered: {name}")

        self._adapters[name] = adapter
        logger.info(f"Registered adapter: {name} ({adapter.display_name})")

    def unregister(self, platform: str) -> bool:
        """
        Unregister a platform adapter.

        Args:
            platform: Platform name to unregister

        Returns:
            True if adapter was removed, False if not found
        """
        if platform in self._adapters:
            del self._adapters[platform]
            logger.info(f"Unregistered adapter: {platform}")
            return True
        return False

    def get(self, platform: str) -> Optional[AdapterType]:
        """
        Get adapter by platform name.

        Args:
            platform: Platform name (e.g., 'mcp', 'goose')

        Returns:
            Adapter instance or None if not found
        """
        return self._adapters.get(platform)

    def get_required(self, platform: str) -> AdapterType:
        """
        Get adapter by platform name, raising if not found.

        Args:
            platform: Platform name

        Returns:
            Adapter instance

        Raises:
            KeyError: If platform not found
        """
        adapter = self.get(platform)
        if adapter is None:
            available = ", ".join(self.list_platforms())
            raise KeyError(
                f"Platform '{platform}' not found. Available: {available}"
            )
        return adapter

    def list_platforms(self) -> List[str]:
        """
        List all registered platform names.

        Returns:
            List of platform names
        """
        return list(self._adapters.keys())

    def list_adapters(self) -> List[AdapterInfo]:
        """
        List information about all registered adapters.

        Returns:
            List of AdapterInfo objects
        """
        return [adapter.get_info() for adapter in self._adapters.values()]

    def export(self, platform: str, output_dir: Path) -> ExportResult:
        """
        Export to a specific platform.

        Args:
            platform: Platform name
            output_dir: Directory to write exported files

        Returns:
            ExportResult with list of created files

        Raises:
            KeyError: If platform not found
        """
        adapter = self.get_required(platform)
        output_dir.mkdir(parents=True, exist_ok=True)
        return adapter.export(output_dir)

    def export_all(self, output_dir: Path) -> Dict[str, ExportResult]:
        """
        Export to all registered platforms.

        Creates a subdirectory for each platform under output_dir.

        Args:
            output_dir: Base directory for exports

        Returns:
            Dict mapping platform name to ExportResult
        """
        results = {}
        for name, adapter in self._adapters.items():
            platform_dir = output_dir / name
            platform_dir.mkdir(parents=True, exist_ok=True)
            try:
                results[name] = adapter.export(platform_dir)
                logger.info(
                    f"Exported {results[name].file_count} files to {platform_dir}"
                )
            except Exception as e:
                logger.error(f"Export failed for {name}: {e}")
                results[name] = ExportResult(
                    platform=name,
                    errors=[str(e)]
                )
        return results

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all registered adapters.

        Returns:
            Dict mapping platform name to list of validation errors
        """
        results = {}
        for name, adapter in self._adapters.items():
            errors = adapter.validate()
            if errors:
                results[name] = errors
        return results

    def __len__(self) -> int:
        """Number of registered adapters."""
        return len(self._adapters)

    def __contains__(self, platform: str) -> bool:
        """Check if platform is registered."""
        return platform in self._adapters

    def __iter__(self):
        """Iterate over registered adapters."""
        return iter(self._adapters.values())
