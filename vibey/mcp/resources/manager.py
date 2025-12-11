"""
MCP Resource Manager.

Orchestrates resource providers and handles MCP resource protocol operations.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .types import Resource, ResourceContent, ResourceTemplate
from .exceptions import ProviderNotFoundError, ResourceNotFoundError
from .provider import ResourceProvider

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages all resource providers and handles MCP resource operations.

    The ResourceManager is the central coordinator for resource discovery
    and access. It maintains a registry of providers and routes resource
    requests to the appropriate provider.

    Example:
        >>> manager = ResourceManager(Path("/path/to/content"))
        >>> templates = manager.get_all_templates()
        >>> resources = manager.list_all_resources()
        >>> content = await manager.read_resource("vibey://workflows/sprint-planning")
    """

    def __init__(self, content_root: Path):
        """
        Initialize the resource manager.

        Args:
            content_root: Root directory for content discovery
        """
        self.content_root = Path(content_root)
        self.providers: Dict[str, ResourceProvider] = {}
        self._initialized = False

    def register_provider(self, name: str, provider: ResourceProvider) -> None:
        """
        Register a resource provider.

        Args:
            name: Provider name/category (e.g., "workflows", "handoffs")
            provider: ResourceProvider instance
        """
        self.providers[name] = provider
        logger.debug(f"Registered resource provider: {name}")

    def _ensure_initialized(self) -> None:
        """
        Ensure providers are registered.

        This is called lazily to allow providers to be registered
        after manager creation. Subclasses can override _register_providers
        to add default providers.
        """
        if not self._initialized:
            self._register_providers()
            self._initialized = True

    def _register_providers(self) -> None:
        """
        Register default resource providers.

        Override this method to register providers for specific content types.
        This is called lazily on first access.
        """
        from .workflows import WorkflowResourceProvider
        from .handoffs import HandoffResourceProvider

        # Register workflow provider
        self.providers['workflows'] = WorkflowResourceProvider(self.content_root)
        logger.debug("Registered workflows resource provider")

        # Register handoff provider
        self.providers['handoffs'] = HandoffResourceProvider(self.content_root)
        logger.debug("Registered handoffs resource provider")

        # Future providers will be registered here as they are implemented:
        # self.providers['agents'] = AgentResourceProvider(self.content_root)
        # self.providers['quality-gates'] = QualityGateResourceProvider(self.content_root)

    def get_all_templates(self) -> List[ResourceTemplate]:
        """
        Get all resource templates from all providers.

        Returns:
            List of all ResourceTemplate definitions
        """
        self._ensure_initialized()
        templates = []
        for provider in self.providers.values():
            try:
                templates.extend(provider.get_templates())
            except Exception as e:
                logger.error(f"Error getting templates from provider: {e}")
        return templates

    def get_all_templates_dict(self) -> List[Dict[str, Any]]:
        """
        Get all resource templates as dictionaries.

        Convenience method for MCP protocol responses.

        Returns:
            List of template dictionaries
        """
        return [asdict(t) for t in self.get_all_templates()]

    def list_all_resources(self) -> List[Resource]:
        """
        List all available resources from all providers.

        Returns:
            List of all Resource definitions
        """
        self._ensure_initialized()
        resources = []
        for provider in self.providers.values():
            try:
                for template in provider.get_templates():
                    resources.extend(provider.list_resources(template.uriTemplate))
            except Exception as e:
                logger.error(f"Error listing resources from provider: {e}")
        return resources

    def list_all_resources_dict(self) -> List[Dict[str, Any]]:
        """
        List all resources as dictionaries.

        Convenience method for MCP protocol responses.

        Returns:
            List of resource dictionaries
        """
        return [asdict(r) for r in self.list_all_resources()]

    def list_resources_by_category(self, category: str) -> List[Resource]:
        """
        List resources for a specific category.

        Args:
            category: Resource category (e.g., "workflows", "handoffs")

        Returns:
            List of resources in that category
        """
        self._ensure_initialized()
        provider = self.providers.get(category)
        if not provider:
            return []

        resources = []
        for template in provider.get_templates():
            resources.extend(provider.list_resources(template.uriTemplate))
        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Read resource content by URI.

        Args:
            uri: Resource URI to read

        Returns:
            ResourceContent with the resource data

        Raises:
            ProviderNotFoundError: If no provider handles the URI
            ResourceNotFoundError: If resource doesn't exist
        """
        self._ensure_initialized()

        # Find provider that handles this URI
        for provider in self.providers.values():
            if provider.supports_uri(uri):
                return await provider.read_resource(uri)

        raise ProviderNotFoundError(uri)

    async def read_resource_dict(self, uri: str) -> Dict[str, Any]:
        """
        Read resource content as dictionary.

        Convenience method for MCP protocol responses.

        Args:
            uri: Resource URI to read

        Returns:
            Resource content as dictionary
        """
        content = await self.read_resource(uri)
        result = asdict(content)
        # Remove None values for cleaner response
        return {k: v for k, v in result.items() if v is not None}

    def get_provider_for_uri(self, uri: str) -> Optional[ResourceProvider]:
        """
        Get the provider that handles a given URI.

        Args:
            uri: Resource URI

        Returns:
            ResourceProvider or None if no provider handles the URI
        """
        self._ensure_initialized()
        for provider in self.providers.values():
            if provider.supports_uri(uri):
                return provider
        return None

    def invalidate_all_caches(self) -> None:
        """
        Invalidate caches in all providers.

        Called when content may have changed and providers should
        refresh their cached data.
        """
        self._ensure_initialized()
        for provider in self.providers.values():
            try:
                provider.invalidate_cache()
            except Exception as e:
                logger.error(f"Error invalidating provider cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered providers and resources.

        Returns:
            Dict with provider and resource counts
        """
        self._ensure_initialized()
        stats = {
            "provider_count": len(self.providers),
            "providers": list(self.providers.keys()),
            "template_count": len(self.get_all_templates()),
            "resource_count": len(self.list_all_resources()),
        }
        return stats
