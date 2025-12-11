"""
MCP Resource Provider base class.

Defines the abstract interface that all resource providers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import re

from .types import Resource, ResourceContent, ResourceTemplate
from .exceptions import InvalidResourceUriError

logger = logging.getLogger(__name__)


class ResourceProvider(ABC):
    """
    Abstract base class for MCP resource providers.

    Each provider handles a specific category of resources (workflows,
    handoffs, agents, etc.) and implements methods to discover and
    read those resources.

    Subclasses must implement:
        - get_templates(): Return URI templates this provider supports
        - list_resources(): List concrete resources for a template
        - read_resource(): Read resource content by URI

    Example:
        >>> class MyResourceProvider(ResourceProvider):
        ...     def get_templates(self) -> List[ResourceTemplate]:
        ...         return [ResourceTemplate(
        ...             uriTemplate="vibey://myresource/{id}",
        ...             name="My Resource"
        ...         )]
        ...
        ...     def list_resources(self, uri_template: str) -> List[Resource]:
        ...         return [Resource(uri="vibey://myresource/1", name="Resource 1")]
        ...
        ...     async def read_resource(self, uri: str) -> ResourceContent:
        ...         return ResourceContent(uri=uri, mimeType="text/plain", text="content")
    """

    # URI scheme this provider handles
    URI_SCHEME = "vibey"

    # Category prefix for URIs (e.g., "workflows", "handoffs")
    URI_CATEGORY: str = ""

    def __init__(self, content_root: Path):
        """
        Initialize the resource provider.

        Args:
            content_root: Root path for content discovery
        """
        self.content_root = Path(content_root)

    @abstractmethod
    def get_templates(self) -> List[ResourceTemplate]:
        """
        Return resource templates this provider supports.

        Templates define URI patterns that clients can use to discover
        resources. Each template should have a unique uriTemplate.

        Returns:
            List of ResourceTemplate definitions
        """
        pass

    @abstractmethod
    def list_resources(self, uri_template: str) -> List[Resource]:
        """
        List all resources matching a template.

        Called when clients request resource discovery. Should return
        all concrete resources that match the given template pattern.

        Args:
            uri_template: URI template pattern to match

        Returns:
            List of Resource objects matching the template
        """
        pass

    @abstractmethod
    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Read resource content by URI.

        Called when clients request a specific resource. Should return
        the full content of the resource.

        Args:
            uri: Resource URI to read

        Returns:
            ResourceContent with the resource data

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceReadError: If resource can't be read
        """
        pass

    def supports_uri(self, uri: str) -> bool:
        """
        Check if this provider handles the given URI.

        Default implementation checks if URI starts with the provider's
        scheme and category prefix.

        Args:
            uri: URI to check

        Returns:
            True if this provider handles the URI
        """
        expected_prefix = f"{self.URI_SCHEME}://{self.URI_CATEGORY}"
        return uri.startswith(expected_prefix)

    def parse_uri(self, uri: str) -> Dict[str, str]:
        """
        Parse a resource URI into components.

        Args:
            uri: Resource URI (e.g., "vibey://workflows/sprint-planning/steps")

        Returns:
            Dict with parsed components:
                - scheme: URI scheme (e.g., "vibey")
                - category: Resource category (e.g., "workflows")
                - id: Resource identifier (e.g., "sprint-planning")
                - subresource: Optional sub-resource (e.g., "steps")

        Raises:
            InvalidResourceUriError: If URI format is invalid
        """
        # Pattern: scheme://category/id[/subresource]
        pattern = r"^(\w+)://([^/]+)/([^/]+)(?:/(.+))?$"
        match = re.match(pattern, uri)

        if not match:
            raise InvalidResourceUriError(uri, "URI must match pattern: scheme://category/id[/subresource]")

        scheme, category, resource_id, subresource = match.groups()

        if scheme != self.URI_SCHEME:
            raise InvalidResourceUriError(uri, f"Expected scheme '{self.URI_SCHEME}', got '{scheme}'")

        return {
            "scheme": scheme,
            "category": category,
            "id": resource_id,
            "subresource": subresource,
        }

    def build_uri(self, resource_id: str, subresource: Optional[str] = None) -> str:
        """
        Build a resource URI from components.

        Args:
            resource_id: Resource identifier
            subresource: Optional sub-resource path

        Returns:
            Complete resource URI
        """
        uri = f"{self.URI_SCHEME}://{self.URI_CATEGORY}/{resource_id}"
        if subresource:
            uri += f"/{subresource}"
        return uri

    def invalidate_cache(self):
        """
        Invalidate any cached data.

        Subclasses should override this to clear their caches.
        Default implementation does nothing.
        """
        pass
