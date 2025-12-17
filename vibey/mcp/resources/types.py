"""
MCP Resource type definitions.

Defines dataclasses for MCP Resource protocol types following the
Model Context Protocol specification.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ResourceTemplate:
    """
    MCP Resource template definition.

    Templates define URI patterns that can be used to discover resources.
    The uriTemplate uses RFC 6570 URI Template syntax.

    Example:
        >>> template = ResourceTemplate(
        ...     uriTemplate="vibey://workflows/{workflow_id}",
        ...     name="Workflow Definition",
        ...     description="Full workflow content",
        ...     mimeType="text/markdown"
        ... )
    """

    uriTemplate: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


@dataclass
class Resource:
    """
    MCP Resource definition.

    Represents a concrete resource that can be read by clients.
    Resources are discovered via templates and accessed by URI.

    Example:
        >>> resource = Resource(
        ...     uri="vibey://workflows/sprint-planning",
        ...     name="Sprint Planning Workflow",
        ...     description="Workflow for planning development sprints",
        ...     mimeType="text/markdown",
        ...     metadata={"type": "planning", "complexity": "medium"}
        ... )
    """

    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResourceContent:
    """
    Resource content response.

    Contains the actual content of a resource. Either text or blob
    should be set, but not both.

    Attributes:
        uri: The resource URI that was read
        mimeType: MIME type of the content
        text: Text content (for text/* MIME types)
        blob: Binary content as bytes (for binary MIME types)

    Example:
        >>> content = ResourceContent(
        ...     uri="vibey://workflows/sprint-planning",
        ...     mimeType="text/markdown",
        ...     text="# Sprint Planning\\n\\nWorkflow steps..."
        ... )
    """

    uri: str
    mimeType: str
    text: Optional[str] = None
    blob: Optional[bytes] = None

    def __post_init__(self):
        """Validate that either text or blob is set, not both."""
        if self.text is not None and self.blob is not None:
            raise ValueError("ResourceContent cannot have both text and blob")


@dataclass
class ResourceSubscription:
    """
    Resource subscription for live updates.

    Clients can subscribe to resources to receive notifications
    when the resource content changes.

    Attributes:
        uri: The resource URI to subscribe to
        callback_id: Client-provided callback identifier
    """

    uri: str
    callback_id: str


@dataclass
class ResourceListChanged:
    """
    Notification that the resource list has changed.

    Sent to clients when resources are added, removed, or modified.
    """

    pass


# URI scheme constants
VIBEY_URI_SCHEME = "vibey"

# Resource categories
RESOURCE_CATEGORY_WORKFLOWS = "workflows"
RESOURCE_CATEGORY_HANDOFFS = "handoffs"
RESOURCE_CATEGORY_AGENTS = "agents"
RESOURCE_CATEGORY_QUALITY_GATES = "quality-gates"

# MIME types
MIME_TYPE_MARKDOWN = "text/markdown"
MIME_TYPE_JSON = "application/json"
MIME_TYPE_JINJA2_MARKDOWN = "text/markdown+jinja2"
