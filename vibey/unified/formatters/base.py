"""
Base output formatter for unified commands.

Formatters handle the difference between CLI output (terminal text)
and MCP output (structured responses).
"""

from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass
class CommandResult:
    """
    Standard result from a unified command.

    Provides a consistent return type that formatters can convert
    to interface-specific output formats.

    Attributes:
        success: Whether the operation succeeded
        data: The result data (can be any type)
        message: Human-readable success message
        error: Error message if operation failed
    """

    success: bool
    data: Any = None
    message: str = ""
    error: str = ""

    @classmethod
    def ok(cls, data: Any = None, message: str = "") -> "CommandResult":
        """Create a successful result."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, error: str, data: Any = None) -> "CommandResult":
        """Create a failed result."""
        return cls(success=False, data=data, error=error)


class OutputFormatter(Protocol):
    """
    Protocol for output formatters.

    Implement this protocol to create custom formatters for specific
    commands that need special output handling.
    """

    def format_cli(self, result: CommandResult) -> str:
        """
        Format result for CLI output.

        Args:
            result: The command result

        Returns:
            String to print to terminal
        """
        ...

    def format_mcp(self, result: CommandResult) -> str:
        """
        Format result for MCP response.

        Args:
            result: The command result

        Returns:
            String for MCP text content
        """
        ...


class DefaultFormatter:
    """
    Default formatter for command results.

    Provides basic formatting suitable for most commands.
    """

    def format_cli(self, result: CommandResult) -> str:
        """Format result for CLI output."""
        if not result.success:
            return f"Error: {result.error}"
        if result.message:
            return result.message
        if result.data is not None:
            return str(result.data)
        return ""

    def format_mcp(self, result: CommandResult) -> str:
        """Format result for MCP response."""
        if not result.success:
            return f"Error: {result.error}"
        if result.message:
            return result.message
        if result.data is not None:
            # MCP can handle more structured output
            if isinstance(result.data, dict):
                import json
                return json.dumps(result.data, indent=2, default=str)
            return str(result.data)
        return "Operation completed successfully."


# Default formatter instance
DEFAULT_FORMATTER = DefaultFormatter()
