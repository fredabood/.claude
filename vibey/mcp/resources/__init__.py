"""
MCP Resources.

Resource definitions for MCP protocol content access.
Implements the MCP Resource protocol for exposing vibey content
(workflows, handoffs, agents, quality gates) to AI assistants.
"""

from .types import (
    Resource,
    ResourceContent,
    ResourceTemplate,
    ResourceSubscription,
    ResourceListChanged,
    VIBEY_URI_SCHEME,
    RESOURCE_CATEGORY_WORKFLOWS,
    RESOURCE_CATEGORY_HANDOFFS,
    RESOURCE_CATEGORY_AGENTS,
    RESOURCE_CATEGORY_QUALITY_GATES,
    MIME_TYPE_MARKDOWN,
    MIME_TYPE_JSON,
    MIME_TYPE_JINJA2_MARKDOWN,
)

from .exceptions import (
    ResourceError,
    ResourceNotFoundError,
    ResourceReadError,
    InvalidResourceUriError,
    ProviderNotFoundError,
    ResourceTemplateError,
)

from .provider import ResourceProvider
from .manager import ResourceManager
from .workflows import WorkflowResourceProvider

__all__ = [
    # Types
    "Resource",
    "ResourceContent",
    "ResourceTemplate",
    "ResourceSubscription",
    "ResourceListChanged",
    # Constants
    "VIBEY_URI_SCHEME",
    "RESOURCE_CATEGORY_WORKFLOWS",
    "RESOURCE_CATEGORY_HANDOFFS",
    "RESOURCE_CATEGORY_AGENTS",
    "RESOURCE_CATEGORY_QUALITY_GATES",
    "MIME_TYPE_MARKDOWN",
    "MIME_TYPE_JSON",
    "MIME_TYPE_JINJA2_MARKDOWN",
    # Exceptions
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceReadError",
    "InvalidResourceUriError",
    "ProviderNotFoundError",
    "ResourceTemplateError",
    # Core classes
    "ResourceProvider",
    "ResourceManager",
    # Providers
    "WorkflowResourceProvider",
]
