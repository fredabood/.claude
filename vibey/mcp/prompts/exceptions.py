"""
MCP Prompt exceptions.

Custom exceptions for prompt operations.
"""

from typing import Optional


class PromptError(Exception):
    """Base exception for prompt operations."""

    def __init__(self, message: str, prompt_name: Optional[str] = None):
        self.message = message
        self.prompt_name = prompt_name
        super().__init__(message)


class PromptNotFoundError(PromptError):
    """Prompt not found by name."""

    def __init__(self, prompt_name: str, message: Optional[str] = None):
        msg = message or f"Prompt not found: {prompt_name}"
        super().__init__(msg, prompt_name)


class PromptArgumentError(PromptError):
    """Invalid or missing prompt argument."""

    def __init__(
        self,
        prompt_name: str,
        argument_name: str,
        reason: str,
    ):
        msg = f"Invalid argument '{argument_name}' for prompt '{prompt_name}': {reason}"
        super().__init__(msg, prompt_name)
        self.argument_name = argument_name
        self.reason = reason


class PromptGenerationError(PromptError):
    """Error generating prompt messages."""

    def __init__(self, prompt_name: str, reason: str):
        msg = f"Error generating prompt '{prompt_name}': {reason}"
        super().__init__(msg, prompt_name)
        self.reason = reason


class PromptProviderError(PromptError):
    """Error with prompt provider."""

    def __init__(self, provider_name: str, reason: str):
        msg = f"Prompt provider error '{provider_name}': {reason}"
        super().__init__(msg, None)
        self.provider_name = provider_name
        self.reason = reason
