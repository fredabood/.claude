"""
Platform Adapter Registry

Factory pattern for managing and instantiating platform adapters.

Usage:
    from framework.platform_adapters.registry import AdapterRegistry

    # Get adapter by name
    adapter = AdapterRegistry.get_adapter('claude-code')
    adapter.deploy()

    # List all available adapters
    platforms = AdapterRegistry.list_platforms()

Created: 2025-11-09
Sprint: core-framework-2, Task 7
"""

from pathlib import Path
from typing import Dict, List, Optional, Type
from .base import PlatformAdapter


class AdapterRegistry:
    """
    Registry for platform adapters.

    Manages registration and instantiation of platform adapters
    using the factory pattern.
    """

    _adapters: Dict[str, Type[PlatformAdapter]] = {}

    @classmethod
    def register(cls, platform_name: str, adapter_class: Type[PlatformAdapter]) -> None:
        """
        Register a platform adapter.

        Args:
            platform_name: Platform identifier (e.g., 'claude-code')
            adapter_class: Adapter class (must extend PlatformAdapter)

        Raises:
            TypeError: If adapter_class doesn't extend PlatformAdapter
        """
        if not issubclass(adapter_class, PlatformAdapter):
            raise TypeError(
                f"{adapter_class.__name__} must extend PlatformAdapter"
            )

        cls._adapters[platform_name] = adapter_class

    @classmethod
    def unregister(cls, platform_name: str) -> None:
        """
        Unregister a platform adapter.

        Args:
            platform_name: Platform identifier
        """
        if platform_name in cls._adapters:
            del cls._adapters[platform_name]

    @classmethod
    def get_adapter(
        cls,
        platform_name: str,
        vibey_dir: Optional[Path] = None
    ) -> PlatformAdapter:
        """
        Get adapter instance for platform.

        Args:
            platform_name: Platform identifier (e.g., 'claude-code')
            vibey_dir: Path to .vibey directory (auto-detected if not provided)

        Returns:
            Instantiated platform adapter

        Raises:
            ValueError: If platform not registered
        """
        if platform_name not in cls._adapters:
            available = ', '.join(cls.list_platforms())
            raise ValueError(
                f"Platform '{platform_name}' not registered. "
                f"Available platforms: {available}"
            )

        adapter_class = cls._adapters[platform_name]
        return adapter_class(vibey_dir=vibey_dir)

    @classmethod
    def list_platforms(cls) -> List[str]:
        """
        List all registered platforms.

        Returns:
            List of platform identifiers
        """
        return sorted(cls._adapters.keys())

    @classmethod
    def is_registered(cls, platform_name: str) -> bool:
        """
        Check if platform is registered.

        Args:
            platform_name: Platform identifier

        Returns:
            True if registered, False otherwise
        """
        return platform_name in cls._adapters

    @classmethod
    def get_adapter_info(cls, platform_name: str) -> Dict[str, str]:
        """
        Get information about a registered adapter.

        Args:
            platform_name: Platform identifier

        Returns:
            Dict with adapter information

        Raises:
            ValueError: If platform not registered
        """
        if platform_name not in cls._adapters:
            raise ValueError(f"Platform '{platform_name}' not registered")

        adapter_class = cls._adapters[platform_name]

        # Create temporary instance to get info
        try:
            adapter = adapter_class()
            return {
                'platform_name': platform_name,
                'class_name': adapter_class.__name__,
                'deployment_dir': str(adapter.get_deployment_dir().name),
                'instructions_file': adapter.get_instructions_filename(),
            }
        except FileNotFoundError:
            # If .vibey not found, return basic info
            return {
                'platform_name': platform_name,
                'class_name': adapter_class.__name__,
                'deployment_dir': 'N/A (no .vibey found)',
                'instructions_file': 'N/A',
            }


# Auto-register built-in adapters
def _register_builtin_adapters():
    """Register all built-in platform adapters."""
    try:
        from .claude_adapter import ClaudeAdapter
        AdapterRegistry.register('claude-code', ClaudeAdapter)
    except ImportError:
        pass

    # Future adapters will be registered here:
    # try:
    #     from .goose_adapter import GooseAdapter
    #     AdapterRegistry.register('goose', GooseAdapter)
    # except ImportError:
    #     pass
    #
    # try:
    #     from .cursor_adapter import CursorAdapter
    #     AdapterRegistry.register('cursor', CursorAdapter)
    # except ImportError:
    #     pass


# Register adapters on module import
_register_builtin_adapters()


def main():
    """Demo the adapter registry."""
    print("🏭 Platform Adapter Registry\n")
    print("=" * 60)

    # List registered platforms
    platforms = AdapterRegistry.list_platforms()
    print(f"\nRegistered Platforms ({len(platforms)}):")
    for platform in platforms:
        print(f"  - {platform}")

    # Show adapter info
    print("\n" + "=" * 60)
    print("\nAdapter Information:")
    for platform in platforms:
        try:
            info = AdapterRegistry.get_adapter_info(platform)
            print(f"\n{platform}:")
            print(f"  Class: {info['class_name']}")
            print(f"  Deployment Dir: {info['deployment_dir']}")
            print(f"  Instructions File: {info['instructions_file']}")
        except Exception as e:
            print(f"\n{platform}: Error - {e}")

    # Test instantiation
    print("\n" + "=" * 60)
    print("\nTesting Instantiation:")
    for platform in platforms:
        try:
            adapter = AdapterRegistry.get_adapter(platform)
            print(f"  ✅ {platform}: {type(adapter).__name__} instance created")
        except FileNotFoundError as e:
            print(f"  ⚠️  {platform}: {e}")
        except Exception as e:
            print(f"  ❌ {platform}: {e}")

    print("\n" + "=" * 60)
    print("✅ Registry test complete!")


if __name__ == "__main__":
    main()
