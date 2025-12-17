"""
Output formatters for unified commands.

Formatters handle converting CommandResult to interface-specific output.
"""

from .base import (
    CommandResult,
    DefaultFormatter,
    OutputFormatter,
    DEFAULT_FORMATTER,
)

__all__ = [
    "CommandResult",
    "DefaultFormatter",
    "OutputFormatter",
    "DEFAULT_FORMATTER",
]
