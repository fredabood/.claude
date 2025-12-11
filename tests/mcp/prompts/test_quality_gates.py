"""Tests for QualityGatePromptProvider."""

import pytest
from vibey.mcp.prompts.quality_gates import QualityGatePromptProvider
from vibey.mcp.prompts.exceptions import PromptNotFoundError


class TestQualityGatePromptProvider:
    """Tests for QualityGatePromptProvider."""

    def test_get_prompts(self, quality_gate_provider):
        """Test that all prompts are returned."""
        prompts = quality_gate_provider.get_prompts()
        assert len(prompts) == 4
        names = [p.name for p in prompts]
        assert "vibey_quality_gate_check" in names
        assert "vibey_security_scan" in names
        assert "vibey_test_coverage" in names
        assert "vibey_doc_check" in names

    def test_prompt_definitions_have_arguments(self, quality_gate_provider):
        """Test that prompts have proper argument definitions."""
        prompts = quality_gate_provider.get_prompts()
        for prompt in prompts:
            assert len(prompt.arguments) >= 1
            # Check at least one required argument
            has_required = any(arg.required for arg in prompt.arguments)
            assert has_required, f"Prompt {prompt.name} should have required args"

    def test_supports_prompt(self, quality_gate_provider):
        """Test supports_prompt method."""
        assert quality_gate_provider.supports_prompt("vibey_quality_gate_check")
        assert quality_gate_provider.supports_prompt("vibey_security_scan")
        assert not quality_gate_provider.supports_prompt("unknown_prompt")

    @pytest.mark.asyncio
    async def test_quality_gate_check_all_types(self, quality_gate_provider):
        """Test quality gate check for all gate types."""
        for gate_type in ["security", "testing", "logging", "documentation", "performance"]:
            result = await quality_gate_provider.get_prompt(
                "vibey_quality_gate_check",
                {"gate_type": gate_type}
            )
            assert result is not None
            assert result.messages is not None
            assert len(result.messages) >= 2
            user_msg = result.messages[0].content
            assert gate_type in user_msg.lower()

    @pytest.mark.asyncio
    async def test_quality_gate_check_with_threshold(self, quality_gate_provider):
        """Test quality gate check with custom threshold."""
        result = await quality_gate_provider.get_prompt(
            "vibey_quality_gate_check",
            {"gate_type": "security", "threshold": "95"}
        )
        assert result is not None
        user_msg = result.messages[0].content
        assert "95" in user_msg

    @pytest.mark.asyncio
    async def test_security_scan_prompt(self, quality_gate_provider):
        """Test security scan prompt."""
        result = await quality_gate_provider.get_prompt(
            "vibey_security_scan",
            {"target": "src/auth.py", "focus": "injection"}
        )
        assert result is not None
        assert len(result.messages) >= 2
        user_msg = result.messages[0].content
        assert "src/auth.py" in user_msg
        assert "injection" in user_msg.lower()

    @pytest.mark.asyncio
    async def test_test_coverage_prompt(self, quality_gate_provider):
        """Test coverage analysis prompt."""
        result = await quality_gate_provider.get_prompt(
            "vibey_test_coverage",
            {"target": "vibey.mcp", "coverage_type": "line"}
        )
        assert result is not None
        user_msg = result.messages[0].content
        assert "vibey.mcp" in user_msg

    @pytest.mark.asyncio
    async def test_doc_check_prompt(self, quality_gate_provider):
        """Test documentation check prompt."""
        result = await quality_gate_provider.get_prompt(
            "vibey_doc_check",
            {"target": "vibey/mcp/server.py", "doc_type": "docstrings"}
        )
        assert result is not None
        user_msg = result.messages[0].content
        assert "vibey/mcp/server.py" in user_msg

    @pytest.mark.asyncio
    async def test_unknown_prompt_raises_error(self, quality_gate_provider):
        """Test that unknown prompt raises PromptNotFoundError."""
        with pytest.raises(PromptNotFoundError):
            await quality_gate_provider.get_prompt("unknown_prompt", {})

    def test_get_checklist_all_types(self, quality_gate_provider):
        """Test _get_checklist for all gate types."""
        for gate_type in ["security", "testing", "logging", "documentation", "performance"]:
            checklist = quality_gate_provider._get_checklist(gate_type)
            assert checklist is not None
            assert len(checklist) > 0
            assert "[ ]" in checklist  # Should have checkbox items

    def test_get_checklist_all_combines_all(self, quality_gate_provider):
        """Test _get_checklist with 'all' combines all checklists."""
        all_checklist = quality_gate_provider._get_checklist("all")
        for gate_type in ["security", "testing", "logging", "documentation", "performance"]:
            type_checklist = quality_gate_provider._get_checklist(gate_type)
            # Each type's checklist should be contained in 'all'
            assert type_checklist in all_checklist or type_checklist.strip() in all_checklist
