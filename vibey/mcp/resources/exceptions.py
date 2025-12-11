"""
MCP Resource exceptions.

Custom exceptions for resource operations.
"""

from typing import Optional


class ResourceError(Exception):
    """Base exception for resource operations."""

    def __init__(self, message: str, uri: Optional[str] = None):
        self.message = message
        self.uri = uri
        super().__init__(message)


class ResourceNotFoundError(ResourceError):
    """Resource not found at the specified URI."""

    def __init__(self, uri: str, message: Optional[str] = None):
        msg = message or f"Resource not found: {uri}"
        super().__init__(msg, uri)


class ResourceReadError(ResourceError):
    """Error reading resource content."""

    def __init__(self, uri: str, reason: str):
        msg = f"Error reading resource {uri}: {reason}"
        super().__init__(msg, uri)
        self.reason = reason


class InvalidResourceUriError(ResourceError):
    """Invalid resource URI format."""

    def __init__(self, uri: str, reason: Optional[str] = None):
        msg = f"Invalid resource URI: {uri}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg, uri)


class ProviderNotFoundError(ResourceError):
    """No provider found for the resource URI."""

    def __init__(self, uri: str):
        msg = f"No provider found for URI: {uri}"
        super().__init__(msg, uri)


class ResourceTemplateError(ResourceError):
    """Error with resource template definition."""

    def __init__(self, template: str, reason: str):
        msg = f"Invalid resource template '{template}': {reason}"
        super().__init__(msg, None)
        self.template = template
        self.reason = reason
