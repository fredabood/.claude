"""
Tests for reference documentation generators.

Tests the CLI and MCP reference Markdown generators.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.operations.docs.cli_introspector import (
    CLIStructure,
    CommandInfo,
    ParamInfo,
    ExampleInfo,
    ParamKind,
)

from vibey.operations.docs.cli_reference_generator import (
    GeneratorConfig,
    CLIReferenceGenerator,
    generate_cli_reference,
    write_cli_reference,
)


class TestGeneratorConfig:
    """Test GeneratorConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GeneratorConfig()
        assert config.include_toc is True
        assert config.include_index is True
        assert config.include_hidden is False
        assert config.include_deprecated is True
        assert config.max_heading_depth == 4
        assert config.include_timestamp is True
        assert config.base_command == "vibey"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = GeneratorConfig(
            include_toc=False,
            include_hidden=True,
            max_heading_depth=3,
            base_command="./vibey",
        )
        assert config.include_toc is False
        assert config.include_hidden is True
        assert config.max_heading_depth == 3
        assert config.base_command == "./vibey"


class TestCLIReferenceGenerator:
    """Test CLIReferenceGenerator class."""

    @pytest.fixture
    def simple_structure(self):
        """Create a simple CLI structure for testing."""
        status_cmd = CommandInfo(
            name="status",
            path="vibey status",
            help="Show overall status",
            short_help="Show status",
            params=[
                ParamInfo(
                    name="verbose",
                    kind=ParamKind.OPTION,
                    type_str="BOOL",
                    required=False,
                    is_flag=True,
                    opts=["-v", "--verbose"],
                    help="Show verbose output",
                ),
            ],
        )
        roadmap_cmd = CommandInfo(
            name="roadmap",
            path="vibey roadmap",
            help="Roadmap management commands",
            short_help="Roadmap commands",
            is_group=True,
            subcommands=[
                CommandInfo(
                    name="status",
                    path="vibey roadmap status",
                    help="Show roadmap status",
                    short_help="Show status",
                ),
            ],
        )
        root = CommandInfo(
            name="vibey",
            path="vibey",
            help="Vibey CLI",
            is_group=True,
            subcommands=[status_cmd, roadmap_cmd],
        )
        return CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=4,
            max_depth=2,
            generated_at="2024-01-01T00:00:00Z",
        )

    def test_init_with_defaults(self, simple_structure):
        """Test generator initialization with defaults."""
        generator = CLIReferenceGenerator(simple_structure)
        assert generator.structure == simple_structure
        assert generator.config.include_toc is True

    def test_init_with_config(self, simple_structure):
        """Test generator initialization with custom config."""
        config = GeneratorConfig(include_toc=False)
        generator = CLIReferenceGenerator(simple_structure, config)
        assert generator.config.include_toc is False

    def test_generate_returns_string(self, simple_structure):
        """Test generate returns a string."""
        generator = CLIReferenceGenerator(simple_structure)
        result = generator.generate()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_includes_header(self, simple_structure):
        """Test generated output includes header."""
        generator = CLIReferenceGenerator(simple_structure)
        result = generator.generate()
        assert "# CLI Reference" in result
        assert "Version:" in result
        assert "Total Commands:" in result

    def test_generate_includes_quick_start(self, simple_structure):
        """Test generated output includes quick start."""
        generator = CLIReferenceGenerator(simple_structure)
        result = generator.generate()
        assert "Quick Start" in result
        assert "vibey init" in result

    def test_generate_includes_toc(self, simple_structure):
        """Test generated output includes TOC when enabled."""
        config = GeneratorConfig(include_toc=True)
        generator = CLIReferenceGenerator(simple_structure, config)
        result = generator.generate()
        assert "Table of Contents" in result

    def test_generate_excludes_toc(self, simple_structure):
        """Test generated output excludes TOC when disabled."""
        config = GeneratorConfig(include_toc=False)
        generator = CLIReferenceGenerator(simple_structure, config)
        result = generator.generate()
        assert "Table of Contents" not in result

    def test_generate_includes_command_index(self, simple_structure):
        """Test generated output includes command index."""
        config = GeneratorConfig(include_index=True)
        generator = CLIReferenceGenerator(simple_structure, config)
        result = generator.generate()
        assert "Command Index" in result

    def test_generate_includes_command_reference(self, simple_structure):
        """Test generated output includes command reference."""
        generator = CLIReferenceGenerator(simple_structure)
        result = generator.generate()
        assert "Command Reference" in result
        assert "`vibey status`" in result

    def test_generate_includes_common_errors(self, simple_structure):
        """Test generated output includes common errors."""
        generator = CLIReferenceGenerator(simple_structure)
        result = generator.generate()
        assert "Common Errors" in result
        assert "Database Errors" in result

    def test_generate_includes_footer(self, simple_structure):
        """Test generated output includes footer."""
        generator = CLIReferenceGenerator(simple_structure)
        result = generator.generate()
        assert "auto-generated" in result.lower()

    def test_make_anchor(self, simple_structure):
        """Test anchor generation."""
        generator = CLIReferenceGenerator(simple_structure)
        assert generator._make_anchor("Hello World") == "hello-world"
        assert generator._make_anchor("vibey-roadmap-status") == "vibey-roadmap-status"
        assert generator._make_anchor("Test!@#$") == "test"

    def test_build_usage_simple_command(self, simple_structure):
        """Test usage string for simple command."""
        generator = CLIReferenceGenerator(simple_structure)
        cmd = CommandInfo(
            name="status",
            path="vibey status",
        )
        usage = generator._build_usage(cmd)
        assert usage == "vibey status"

    def test_build_usage_with_options(self, simple_structure):
        """Test usage string with options."""
        generator = CLIReferenceGenerator(simple_structure)
        cmd = CommandInfo(
            name="status",
            path="vibey status",
            params=[
                ParamInfo("verbose", ParamKind.OPTION, "BOOL", False),
            ],
        )
        usage = generator._build_usage(cmd)
        assert "[OPTIONS]" in usage

    def test_build_usage_with_arguments(self, simple_structure):
        """Test usage string with arguments."""
        generator = CLIReferenceGenerator(simple_structure)
        cmd = CommandInfo(
            name="show",
            path="vibey show",
            params=[
                ParamInfo("task_id", ParamKind.ARGUMENT, "STRING", True),
            ],
        )
        usage = generator._build_usage(cmd)
        assert "<TASK_ID>" in usage

    def test_build_usage_with_group(self, simple_structure):
        """Test usage string for command group."""
        generator = CLIReferenceGenerator(simple_structure)
        cmd = CommandInfo(
            name="roadmap",
            path="vibey roadmap",
            is_group=True,
        )
        usage = generator._build_usage(cmd)
        assert "COMMAND" in usage


class TestGenerateCLIReference:
    """Test generate_cli_reference convenience function."""

    def test_with_mock_structure(self):
        """Test with mocked CLI structure."""
        root = CommandInfo(
            name="vibey",
            path="vibey",
            is_group=True,
            subcommands=[
                CommandInfo(name="status", path="vibey status"),
            ],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=2,
            max_depth=1,
            generated_at="2024-01-01",
        )

        result = generate_cli_reference(structure=structure)
        assert isinstance(result, str)
        assert "CLI Reference" in result

    def test_with_custom_config(self):
        """Test with custom configuration."""
        root = CommandInfo(
            name="vibey",
            path="vibey",
            is_group=True,
            subcommands=[],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01",
        )

        config = GeneratorConfig(include_toc=False, include_index=False)
        result = generate_cli_reference(config=config, structure=structure)

        assert "Table of Contents" not in result
        assert "Command Index" not in result


class TestWriteCLIReference:
    """Test write_cli_reference convenience function."""

    def test_writes_to_file(self, tmp_path):
        """Test that file is written correctly."""
        output_path = tmp_path / "CLI_REFERENCE.md"

        # Mock introspect_cli to avoid import issues
        root = CommandInfo(
            name="vibey",
            path="vibey",
            is_group=True,
            subcommands=[],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01",
        )

        with patch(
            'vibey.operations.docs.cli_reference_generator.introspect_cli',
            return_value=structure
        ):
            result = write_cli_reference(str(output_path))

        assert result == output_path
        assert output_path.exists()
        content = output_path.read_text()
        assert "CLI Reference" in content

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        output_path = tmp_path / "nested" / "dir" / "CLI_REFERENCE.md"

        root = CommandInfo(
            name="vibey",
            path="vibey",
            is_group=True,
            subcommands=[],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01",
        )

        with patch(
            'vibey.operations.docs.cli_reference_generator.introspect_cli',
            return_value=structure
        ):
            result = write_cli_reference(str(output_path))

        assert output_path.exists()


class TestIntegration:
    """Integration tests with real CLI (if available)."""

    def test_generate_real_cli_reference(self):
        """Test generating reference from actual CLI."""
        try:
            markdown = generate_cli_reference()
            assert isinstance(markdown, str)
            assert len(markdown) > 1000  # Should be substantial
            assert "CLI Reference" in markdown
            assert "vibey" in markdown
        except ImportError:
            pytest.skip("vibey.cli.main not available")

    def test_generated_content_is_valid_markdown(self):
        """Test that generated content is valid markdown."""
        try:
            markdown = generate_cli_reference()

            # Basic markdown validation
            lines = markdown.split("\n")

            # Should have headings
            headings = [l for l in lines if l.startswith("#")]
            assert len(headings) > 0

            # Should have code blocks
            assert "```" in markdown

            # Should have tables
            assert "|" in markdown

        except ImportError:
            pytest.skip("vibey.cli.main not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
