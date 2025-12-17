"""
MCP Prompt Manager.

Orchestrates prompt providers and handles MCP prompt protocol operations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .types import PromptDefinition, PromptResult
from .exceptions import PromptNotFoundError
from .provider import PromptProvider
from .quality_gates import QualityGatePromptProvider

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Manages all prompt providers and handles MCP prompt operations.

    The PromptManager is the central coordinator for prompt discovery
    and generation. It maintains a registry of providers and routes
    prompt requests to the appropriate provider.

    Example:
        >>> manager = PromptManager(Path("/path/to/content"))
        >>> prompts = manager.list_prompts()
        >>> result = await manager.get_prompt("vibey_quality_gate", {"gate_type": "security"})
    """

    def __init__(self, content_root: Path, roadmap_root: Optional[Path] = None):
        """
        Initialize the prompt manager.

        Args:
            content_root: Root directory for content discovery
            roadmap_root: Optional roadmap directory (defaults to content_root/.vibey)
        """
        self.content_root = Path(content_root)
        self.roadmap_root = Path(roadmap_root) if roadmap_root else self.content_root / ".vibey"
        self.providers: Dict[str, PromptProvider] = {}
        self._initialized = False

    def register_provider(self, name: str, provider: PromptProvider) -> None:
        """
        Register a prompt provider.

        Args:
            name: Provider name/category (e.g., "quality-gates", "workflows")
            provider: PromptProvider instance
        """
        self.providers[name] = provider
        logger.debug(f"Registered prompt provider: {name}")

    def _ensure_initialized(self) -> None:
        """
        Ensure providers are registered.

        This is called lazily to allow providers to be registered
        after manager creation. Subclasses can override _register_providers
        to add default providers.
        """
        if not self._initialized:
            self._register_providers()
            self._initialized = True

    def _register_providers(self) -> None:
        """
        Register default prompt providers.

        Override this method to register providers for specific prompt types.
        This is called lazily on first access.
        """
        # Quality gates provider
        self.providers['quality-gates'] = QualityGatePromptProvider(self.content_root)

        # Future providers:
        # self.providers['workflows'] = WorkflowPromptProvider(self.content_root)
        # self.providers['reviews'] = ReviewPromptProvider(self.content_root)
        # self.providers['planning'] = PlanningPromptProvider(self.roadmap_root)

    def list_prompts(self) -> List[PromptDefinition]:
        """
        List all available prompts from all providers.

        Returns:
            List of all PromptDefinition objects
        """
        self._ensure_initialized()
        prompts = []
        for provider in self.providers.values():
            try:
                prompts.extend(provider.get_prompts())
            except Exception as e:
                logger.error(f"Error getting prompts from provider: {e}")
        return prompts

    def list_prompts_dict(self) -> List[Dict[str, Any]]:
        """
        List all prompts as dictionaries.

        Convenience method for MCP protocol responses.

        Returns:
            List of prompt dictionaries
        """
        prompts = []
        for prompt in self.list_prompts():
            prompts.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": [
                    {
                        "name": arg.name,
                        "description": arg.description,
                        "required": arg.required,
                    }
                    for arg in prompt.arguments
                ],
            })
        return prompts

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None,
    ) -> PromptResult:
        """
        Get prompt messages by name.

        Args:
            name: Prompt name to get
            arguments: Optional arguments to parameterize the prompt

        Returns:
            PromptResult with the generated messages

        Raises:
            PromptNotFoundError: If no provider handles the prompt
        """
        self._ensure_initialized()

        # Find provider that handles this prompt
        for provider in self.providers.values():
            if provider.supports_prompt(name):
                return await provider.get_prompt(name, arguments)

        raise PromptNotFoundError(name)

    async def get_prompt_dict(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Get prompt messages as dictionary.

        Convenience method for MCP protocol responses.

        Args:
            name: Prompt name to get
            arguments: Optional arguments

        Returns:
            Prompt result as dictionary
        """
        result = await self.get_prompt(name, arguments)
        return {
            "description": result.description,
            "messages": [
                {
                    "role": msg.role,
                    "content": {"type": "text", "text": msg.content},
                }
                for msg in result.messages
            ],
        }

    def get_provider_for_prompt(self, name: str) -> Optional[PromptProvider]:
        """
        Get the provider that handles a given prompt.

        Args:
            name: Prompt name

        Returns:
            PromptProvider or None if no provider handles the prompt
        """
        self._ensure_initialized()
        for provider in self.providers.values():
            if provider.supports_prompt(name):
                return provider
        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered providers and prompts.

        Returns:
            Dict with provider and prompt counts
        """
        self._ensure_initialized()
        stats = {
            "provider_count": len(self.providers),
            "providers": list(self.providers.keys()),
            "prompt_count": len(self.list_prompts()),
        }
        return stats
