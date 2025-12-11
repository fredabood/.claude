"""
MCP Prompt Provider base class.

Defines the abstract interface that all prompt providers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .types import PromptDefinition, PromptResult
from .exceptions import PromptArgumentError

logger = logging.getLogger(__name__)


class PromptProvider(ABC):
    """
    Abstract base class for MCP prompt providers.

    Each provider handles a specific category of prompts (quality gates,
    workflows, reviews, planning, etc.) and implements methods to list
    available prompts and generate prompt messages.

    Subclasses must implement:
        - get_prompts(): Return prompts this provider offers
        - get_prompt(): Generate prompt messages for a given prompt name

    Example:
        >>> class MyPromptProvider(PromptProvider):
        ...     def get_prompts(self) -> List[PromptDefinition]:
        ...         return [PromptDefinition(
        ...             name="my_prompt",
        ...             description="A custom prompt"
        ...         )]
        ...
        ...     async def get_prompt(self, name: str, arguments: Dict) -> PromptResult:
        ...         return PromptResult(
        ...             messages=[PromptMessage(role="user", content="Hello")]
        ...         )
    """

    # Category name for this provider
    CATEGORY: str = ""

    def __init__(self, content_root: Path):
        """
        Initialize the prompt provider.

        Args:
            content_root: Root path for content access
        """
        self.content_root = Path(content_root)

    @abstractmethod
    def get_prompts(self) -> List[PromptDefinition]:
        """
        Return all prompts this provider offers.

        Returns:
            List of PromptDefinition objects
        """
        pass

    @abstractmethod
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None,
    ) -> PromptResult:
        """
        Generate prompt messages for the given prompt name.

        Args:
            name: Prompt name to generate
            arguments: Optional arguments to parameterize the prompt

        Returns:
            PromptResult with generated messages

        Raises:
            PromptNotFoundError: If prompt name not supported
            PromptArgumentError: If required arguments missing
        """
        pass

    def supports_prompt(self, name: str) -> bool:
        """
        Check if this provider handles the given prompt.

        Args:
            name: Prompt name to check

        Returns:
            True if this provider handles the prompt
        """
        return any(p.name == name for p in self.get_prompts())

    def validate_arguments(
        self,
        prompt: PromptDefinition,
        arguments: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Validate and normalize prompt arguments.

        Checks that all required arguments are present and returns
        a normalized arguments dict.

        Args:
            prompt: PromptDefinition to validate against
            arguments: Arguments to validate

        Returns:
            Validated and normalized arguments dict

        Raises:
            PromptArgumentError: If required argument is missing
        """
        args = arguments or {}
        validated = {}

        for arg_def in prompt.arguments:
            if arg_def.name in args:
                validated[arg_def.name] = args[arg_def.name]
            elif arg_def.required:
                raise PromptArgumentError(
                    prompt.name,
                    arg_def.name,
                    "Required argument not provided",
                )

        return validated

    def get_prompt_by_name(self, name: str) -> Optional[PromptDefinition]:
        """
        Find a prompt by name.

        Args:
            name: Prompt name to find

        Returns:
            PromptDefinition or None if not found
        """
        for prompt in self.get_prompts():
            if prompt.name == name:
                return prompt
        return None
