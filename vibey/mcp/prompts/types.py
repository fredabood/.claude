"""
MCP Prompt type definitions.

Defines dataclasses for MCP Prompt protocol types following the
Model Context Protocol specification.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PromptArgument:
    """
    MCP Prompt argument definition.

    Arguments allow prompts to be parameterized. Each argument has a name,
    optional description, and required flag.

    Example:
        >>> arg = PromptArgument(
        ...     name="gate_type",
        ...     description="Type of quality gate to run",
        ...     required=True
        ... )
    """

    name: str
    description: Optional[str] = None
    required: bool = False


@dataclass
class PromptDefinition:
    """
    MCP Prompt definition.

    Represents a prompt that can be invoked by clients.
    Prompts are discovered via list and invoked by name.

    Example:
        >>> prompt = PromptDefinition(
        ...     name="vibey_quality_gate",
        ...     description="Run a quality gate check",
        ...     arguments=[
        ...         PromptArgument(name="gate_type", required=True),
        ...         PromptArgument(name="threshold", required=False)
        ...     ]
        ... )
    """

    name: str
    description: Optional[str] = None
    arguments: List[PromptArgument] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptMessage:
    """
    Message in a prompt response.

    Prompts return a sequence of messages that guide the AI assistant.
    Each message has a role (user or assistant) and content.

    Attributes:
        role: Message role ("user" or "assistant")
        content: Text content of the message

    Example:
        >>> msg = PromptMessage(
        ...     role="user",
        ...     content="Please review this code for security issues."
        ... )
    """

    role: str  # "user" or "assistant"
    content: str


@dataclass
class PromptResult:
    """
    Result of getting a prompt.

    Contains the generated messages and optional description.

    Attributes:
        description: Optional description of the prompt result
        messages: List of messages to send to the AI

    Example:
        >>> result = PromptResult(
        ...     description="Security review checklist",
        ...     messages=[
        ...         PromptMessage(role="user", content="Review for vulnerabilities"),
        ...         PromptMessage(role="assistant", content="I'll check for common issues...")
        ...     ]
        ... )
    """

    description: Optional[str] = None
    messages: List[PromptMessage] = field(default_factory=list)


# Prompt category constants
PROMPT_CATEGORY_QUALITY_GATES = "quality-gates"
PROMPT_CATEGORY_WORKFLOWS = "workflows"
PROMPT_CATEGORY_REVIEWS = "reviews"
PROMPT_CATEGORY_PLANNING = "planning"

# Prompt name prefixes
PROMPT_PREFIX = "vibey_"
