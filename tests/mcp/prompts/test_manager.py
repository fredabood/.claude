"""Tests for PromptManager."""

import pytest
from vibey.mcp.prompts.manager import PromptManager
from vibey.mcp.prompts.exceptions import PromptNotFoundError


class TestPromptManager:
    """Tests for PromptManager class."""

    def test_initialization(self, content_root, roadmap_root):
        """Test that PromptManager initializes correctly."""
        manager = PromptManager(content_root, roadmap_root)
        assert manager is not None
        assert manager.content_root == content_root

    def test_lazy_initialization(self, content_root, roadmap_root):
        """Test that providers are registered lazily."""
        manager = PromptManager(content_root, roadmap_root)
        # Providers shouldn't be registered until first access
        assert manager._initialized is False
        # Access triggers initialization
        manager.list_prompts()
        assert manager._initialized is True

    def test_list_prompts(self, prompt_manager):
        """Test listing all prompts."""
        prompts = prompt_manager.list_prompts()
        assert len(prompts) >= 4
        # Should have quality gate prompts
        names = [p.name for p in prompts]
        assert "vibey_quality_gate_check" in names
        assert "vibey_security_scan" in names

    def test_list_prompts_dict(self, prompt_manager):
        """Test listing prompts as dictionaries."""
        prompts = prompt_manager.list_prompts_dict()
        assert isinstance(prompts, list)
        assert len(prompts) >= 4
        assert all(isinstance(p, dict) for p in prompts)
        assert all("name" in p for p in prompts)

    def test_get_provider_for_prompt(self, prompt_manager):
        """Test getting provider for a prompt."""
        provider = prompt_manager.get_provider_for_prompt("vibey_quality_gate_check")
        assert provider is not None
        provider_none = prompt_manager.get_provider_for_prompt("unknown_prompt")
        assert provider_none is None

    @pytest.mark.asyncio
    async def test_get_prompt(self, prompt_manager):
        """Test getting a specific prompt."""
        result = await prompt_manager.get_prompt(
            "vibey_quality_gate_check",
            {"gate_type": "security"}
        )
        assert result is not None
        assert result.messages is not None
        assert len(result.messages) >= 2

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self, prompt_manager):
        """Test getting a non-existent prompt."""
        with pytest.raises(PromptNotFoundError):
            await prompt_manager.get_prompt("unknown_prompt", {})

    @pytest.mark.asyncio
    async def test_get_prompt_dict(self, prompt_manager):
        """Test getting prompt as dictionary."""
        result = await prompt_manager.get_prompt_dict(
            "vibey_quality_gate_check",
            {"gate_type": "testing"}
        )
        assert isinstance(result, dict)
        assert "messages" in result

    def test_register_provider(self, content_root, roadmap_root):
        """Test registering a custom provider."""
        from vibey.mcp.prompts.quality_gates import QualityGatePromptProvider

        manager = PromptManager(content_root, roadmap_root)
        custom_provider = QualityGatePromptProvider(content_root)
        manager.register_provider("custom-gates", custom_provider)
        assert "custom-gates" in manager.providers

    def test_get_stats(self, prompt_manager):
        """Test getting manager statistics."""
        stats = prompt_manager.get_stats()
        assert "provider_count" in stats
        assert "providers" in stats
        assert "prompt_count" in stats
        assert stats["provider_count"] >= 1
        assert stats["prompt_count"] >= 4

    def test_prompts_have_arguments(self, prompt_manager):
        """Test that prompts have argument definitions."""
        prompts = prompt_manager.list_prompts()
        for prompt in prompts:
            assert hasattr(prompt, "arguments")
            # Each prompt should have at least one argument
            assert len(prompt.arguments) >= 1

    def test_prompts_have_descriptions(self, prompt_manager):
        """Test that prompts have descriptions."""
        prompts = prompt_manager.list_prompts()
        for prompt in prompts:
            assert hasattr(prompt, "description")
            assert prompt.description is not None
            assert len(prompt.description) > 0

    @pytest.mark.asyncio
    async def test_all_prompts_callable(self, prompt_manager):
        """Test that all registered prompts can be called with minimal args."""
        prompts = prompt_manager.list_prompts()
        for prompt in prompts:
            # Build minimal arguments from required fields
            args = {}
            for arg in prompt.arguments:
                if arg.required:
                    # Provide a test value
                    args[arg.name] = "test_value"

            result = await prompt_manager.get_prompt(prompt.name, args)
            assert result is not None
            assert result.messages is not None
