"""
MCP Prompts.

Prompt templates for MCP protocol prompt operations.
Implements the MCP Prompt protocol for providing structured
prompts to AI assistants (quality gates, workflows, reviews, planning).
"""

from .types import (
    PromptArgument,
    PromptDefinition,
    PromptMessage,
    PromptResult,
    PROMPT_CATEGORY_QUALITY_GATES,
    PROMPT_CATEGORY_WORKFLOWS,
    PROMPT_CATEGORY_REVIEWS,
    PROMPT_CATEGORY_PLANNING,
    PROMPT_PREFIX,
)

from .exceptions import (
    PromptError,
    PromptNotFoundError,
    PromptArgumentError,
    PromptGenerationError,
    PromptProviderError,
)

from .provider import PromptProvider
from .manager import PromptManager

__all__ = [
    # Types
    "PromptArgument",
    "PromptDefinition",
    "PromptMessage",
    "PromptResult",
    # Constants
    "PROMPT_CATEGORY_QUALITY_GATES",
    "PROMPT_CATEGORY_WORKFLOWS",
    "PROMPT_CATEGORY_REVIEWS",
    "PROMPT_CATEGORY_PLANNING",
    "PROMPT_PREFIX",
    # Exceptions
    "PromptError",
    "PromptNotFoundError",
    "PromptArgumentError",
    "PromptGenerationError",
    "PromptProviderError",
    # Core classes
    "PromptProvider",
    "PromptManager",
]
