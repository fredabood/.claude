"""
PM Adapter Registry - Discovery and management of PM tool adapters.

This module provides the registry pattern for discovering, registering,
and managing PM tool adapters. It mirrors the existing AdapterRegistry
in vibey/adapters/registry.py.

Features:
- Register adapters with @pm_adapter decorator
- Get adapters by name
- Set and get default adapter
- List available adapters
- Lazy loading of adapter classes

Usage:
    from vibey.adapters.pm.registry import PMAdapterRegistry, pm_adapter

    # Register an adapter
    @pm_adapter("jira")
    class JiraAdapter(TicketAdapter):
        ...

    # Get an adapter
    adapter = PMAdapterRegistry.get("jira")

    # Get the default adapter (usually "vibey")
    default = PMAdapterRegistry.get_default()

    # List all registered adapters
    adapters = PMAdapterRegistry.list_adapters()

Reference: UNIFIED_ADAPTER_ARCHITECTURE.md Part 3.4
"""

from typing import Callable, Dict, List, Optional, Type

from vibey.adapters.pm.base import TicketAdapter
from vibey.adapters.pm.types import AdapterInfo, PMCapabilities


class AdapterNotFoundError(Exception):
    """Raised when a requested adapter is not registered."""

    def __init__(self, adapter_name: str, available: List[str]):
        self.adapter_name = adapter_name
        self.available = available
        super().__init__(
            f"Adapter '{adapter_name}' not found. "
            f"Available adapters: {', '.join(available) if available else 'none'}"
        )


class AdapterRegistrationError(Exception):
    """Raised when adapter registration fails."""

    pass


class PMAdapterRegistry:
    """
    Registry for PM tool adapters.

    Provides a central location for registering, discovering, and
    managing PM tool adapters. Supports lazy loading and a default
    adapter for operations that don't specify which adapter to use.

    Class-level registry (singleton pattern via class variables).
    """

    # Class variables (shared across all instances)
    _adapters: Dict[str, Type[TicketAdapter]] = {}
    _instances: Dict[str, TicketAdapter] = {}
    _default_adapter: Optional[str] = None

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    @classmethod
    def register(
        cls,
        name: str,
        adapter_class: Type[TicketAdapter],
        set_default: bool = False,
    ) -> None:
        """
        Register an adapter class.

        Args:
            name: Unique adapter name (lowercase, no spaces)
            adapter_class: The adapter class (must inherit from TicketAdapter)
            set_default: If True, set this as the default adapter

        Raises:
            AdapterRegistrationError: If name is already registered or invalid
        """
        if not name or not name.isidentifier():
            raise AdapterRegistrationError(
                f"Invalid adapter name: '{name}'. "
                "Must be a valid Python identifier (lowercase, no spaces)."
            )

        if not issubclass(adapter_class, TicketAdapter):
            raise AdapterRegistrationError(
                f"Adapter class must inherit from TicketAdapter, "
                f"got {adapter_class.__name__}"
            )

        if name in cls._adapters and cls._adapters[name] != adapter_class:
            raise AdapterRegistrationError(
                f"Adapter '{name}' is already registered with a different class. "
                f"Use unregister() first to replace it."
            )

        cls._adapters[name] = adapter_class

        if set_default or cls._default_adapter is None:
            cls._default_adapter = name

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister an adapter.

        Args:
            name: Name of adapter to unregister

        Returns:
            True if adapter was unregistered, False if not found
        """
        if name in cls._adapters:
            del cls._adapters[name]

            # Clear instance cache
            if name in cls._instances:
                del cls._instances[name]

            # Clear default if this was it
            if cls._default_adapter == name:
                cls._default_adapter = next(iter(cls._adapters), None)

            return True
        return False

    # =========================================================================
    # RETRIEVAL
    # =========================================================================

    @classmethod
    def get(cls, name: str, use_cache: bool = True) -> TicketAdapter:
        """
        Get an adapter instance by name.

        Args:
            name: Adapter name
            use_cache: If True, return cached instance if available

        Returns:
            TicketAdapter instance

        Raises:
            AdapterNotFoundError: If adapter is not registered
        """
        if name not in cls._adapters:
            raise AdapterNotFoundError(name, list(cls._adapters.keys()))

        if use_cache and name in cls._instances:
            return cls._instances[name]

        # Create new instance
        adapter_class = cls._adapters[name]
        instance = adapter_class()
        cls._instances[name] = instance
        return instance

    @classmethod
    def get_default(cls) -> TicketAdapter:
        """
        Get the default adapter.

        Returns:
            Default TicketAdapter instance

        Raises:
            AdapterNotFoundError: If no adapters are registered
        """
        if cls._default_adapter is None:
            raise AdapterNotFoundError("default", list(cls._adapters.keys()))

        return cls.get(cls._default_adapter)

    @classmethod
    def set_default(cls, name: str) -> None:
        """
        Set the default adapter.

        Args:
            name: Name of adapter to set as default

        Raises:
            AdapterNotFoundError: If adapter is not registered
        """
        if name not in cls._adapters:
            raise AdapterNotFoundError(name, list(cls._adapters.keys()))

        cls._default_adapter = name

    @classmethod
    def get_default_name(cls) -> Optional[str]:
        """Get the name of the default adapter."""
        return cls._default_adapter

    # =========================================================================
    # DISCOVERY
    # =========================================================================

    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        List all registered adapter names.

        Returns:
            List of adapter names (sorted alphabetically)
        """
        return sorted(cls._adapters.keys())

    @classmethod
    def get_adapter_info(cls, name: str) -> AdapterInfo:
        """
        Get information about an adapter.

        Args:
            name: Adapter name

        Returns:
            AdapterInfo with adapter details

        Raises:
            AdapterNotFoundError: If adapter is not registered
        """
        adapter = cls.get(name)

        # Check availability
        try:
            is_available = adapter.is_available()
            errors = adapter.validate_config()
            error_message = errors[0] if errors else None
        except Exception as e:
            is_available = False
            error_message = str(e)

        return AdapterInfo(
            name=adapter.adapter_name,
            display_name=adapter.display_name,
            capabilities=adapter.capabilities,
            is_available=is_available,
            error_message=error_message,
        )

    @classmethod
    def list_adapter_info(cls) -> List[AdapterInfo]:
        """
        Get information about all registered adapters.

        Returns:
            List of AdapterInfo objects
        """
        return [cls.get_adapter_info(name) for name in cls.list_adapters()]

    @classmethod
    def get_capabilities(cls, name: str) -> PMCapabilities:
        """
        Get capabilities of an adapter.

        Args:
            name: Adapter name

        Returns:
            PMCapabilities for the adapter

        Raises:
            AdapterNotFoundError: If adapter is not registered
        """
        return cls.get(name).capabilities

    # =========================================================================
    # UTILITY
    # =========================================================================

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered adapters.

        Primarily for testing purposes.
        """
        cls._adapters.clear()
        cls._instances.clear()
        cls._default_adapter = None

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an adapter is registered."""
        return name in cls._adapters


def pm_adapter(
    name: str,
    set_default: bool = False,
) -> Callable[[Type[TicketAdapter]], Type[TicketAdapter]]:
    """
    Decorator for auto-registering PM adapters.

    Usage:
        @pm_adapter("jira")
        class JiraAdapter(TicketAdapter):
            ...

        @pm_adapter("vibey", set_default=True)
        class VibeyAdapter(TicketAdapter):
            ...

    Args:
        name: Unique adapter name
        set_default: If True, set this adapter as the default

    Returns:
        Decorator function
    """

    def decorator(cls: Type[TicketAdapter]) -> Type[TicketAdapter]:
        PMAdapterRegistry.register(name, cls, set_default=set_default)
        return cls

    return decorator
