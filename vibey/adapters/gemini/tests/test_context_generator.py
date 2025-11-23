"""Tests for GeminiContextGenerator."""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from vibey.adapters.gemini.context_generator import (
    GeminiContextGenerator,
    GeneratedContext,
)


class TestGeminiContextGenerator:
    """Test suite for GeminiContextGenerator."""

    @pytest.fixture
    def generator(self):
        """Create generator with project root."""
        return GeminiContextGenerator(Path.cwd())

    def test_generate_returns_context(self, generator):
        """Test that generate() returns a GeneratedContext."""
        result = generator.generate()

        assert isinstance(result, GeneratedContext)
        assert isinstance(result.content, str)
        assert isinstance(result.checksum, str)
        assert isinstance(result.generated_at, datetime)

    def test_generate_discovers_agents(self, generator):
        """Test that agents are discovered from frontmatter."""
        result = generator.generate()

        # Should find agents (we have 19 in the framework)
        assert result.agents_count > 0
        assert result.agents_count >= 10  # At least 10 agents expected

    def test_generate_discovers_workflows(self, generator):
        """Test that workflows are discovered from frontmatter."""
        result = generator.generate()

        # Should find workflows (we have 16 in the framework)
        assert result.workflows_count > 0
        assert result.workflows_count >= 10  # At least 10 workflows expected

    def test_content_includes_header(self, generator):
        """Test that generated content includes Vibey header."""
        result = generator.generate()

        assert "# Vibey Agent Framework" in result.content
        assert "Quick Start" in result.content

    def test_content_includes_agents_section(self, generator):
        """Test that generated content includes agents section."""
        result = generator.generate()

        assert "## Available Agents" in result.content
        assert "MCP Tool:" in result.content

    def test_content_includes_workflows_section(self, generator):
        """Test that generated content includes workflows section."""
        result = generator.generate(include_workflows=True)

        assert "## Available Workflows" in result.content
        assert "/vibey:" in result.content

    def test_content_includes_mcp_section(self, generator):
        """Test that generated content includes MCP instructions."""
        result = generator.generate(include_mcp_instructions=True)

        assert "## MCP Integration" in result.content
        assert "vibey_" in result.content

    def test_content_includes_footer(self, generator):
        """Test that generated content includes footer with marker."""
        result = generator.generate()

        assert "VIBEY_GEMINI_GENERATED" in result.content
        assert "Do not edit manually" in result.content

    def test_checksum_is_stable(self, generator):
        """Test that checksum is stable across regenerations."""
        result1 = generator.generate()
        result2 = generator.generate()

        # Checksums should match (timestamp is excluded)
        assert result1.checksum == result2.checksum

    def test_checksum_is_16_chars(self, generator):
        """Test that checksum is truncated to 16 characters."""
        result = generator.generate()

        assert len(result.checksum) == 16

    def test_exclude_workflows(self, generator):
        """Test that workflows can be excluded."""
        result = generator.generate(include_workflows=False)

        # Should still have agents
        assert result.agents_count > 0
        # Workflows count should be 0
        assert result.workflows_count == 0

    def test_exclude_mcp_instructions(self, generator):
        """Test that MCP instructions can be excluded."""
        result = generator.generate(include_mcp_instructions=False)

        # Should not have MCP section
        assert "## MCP Integration" not in result.content

    def test_write_to_file(self, generator, tmp_path):
        """Test writing generated content to file."""
        output_path = tmp_path / "GEMINI.md"

        result = generator.write_to_file(output_path)

        assert output_path.exists()
        assert output_path.read_text() == result.content
        assert result.agents_count > 0

    def test_agents_grouped_by_type(self, generator):
        """Test that agents are grouped by type in output."""
        result = generator.generate()

        # Should have type headers
        assert "### " in result.content
        # Common agent types
        type_headers = ["Development", "Quality", "Planning", "Core"]
        found_headers = [h for h in type_headers if f"### {h}" in result.content]
        assert len(found_headers) >= 2  # At least 2 type groups


class TestGeneratedContext:
    """Test GeneratedContext dataclass."""

    def test_dataclass_fields(self):
        """Test GeneratedContext has expected fields."""
        ctx = GeneratedContext(
            content="test content",
            checksum="abc123",
            agents_count=5,
            workflows_count=3,
            generated_at=datetime.now(timezone.utc),
        )

        assert ctx.content == "test content"
        assert ctx.checksum == "abc123"
        assert ctx.agents_count == 5
        assert ctx.workflows_count == 3
        assert isinstance(ctx.generated_at, datetime)
