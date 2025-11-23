"""Tests for GeminiCommandGenerator."""

import pytest
from pathlib import Path
from datetime import datetime

from vibey.adapters.gemini.command_generator import (
    GeminiCommandGenerator,
    GeneratedCommand,
    CommandGenerationResult,
)


class TestGeminiCommandGenerator:
    """Test suite for GeminiCommandGenerator."""

    @pytest.fixture
    def generator(self):
        """Create generator with project root."""
        return GeminiCommandGenerator(Path.cwd())

    def test_generate_returns_result(self, generator):
        """Test that generate() returns a CommandGenerationResult."""
        result = generator.generate()

        assert isinstance(result, CommandGenerationResult)
        assert isinstance(result.commands, list)
        assert isinstance(result.checksum, str)
        assert isinstance(result.generated_at, datetime)
        assert isinstance(result.manifest, dict)

    def test_generate_creates_workflow_commands(self, generator):
        """Test that workflow commands are generated."""
        result = generator.generate()

        # Should have workflow commands
        workflow_cmds = [c for c in result.commands if not c.id.startswith("agent-")]
        assert len(workflow_cmds) > 0

    def test_generate_creates_agent_commands(self, generator):
        """Test that agent shortcut commands are generated."""
        result = generator.generate()

        # Should have agent commands
        agent_cmds = [c for c in result.commands if c.id.startswith("agent-")]
        assert len(agent_cmds) > 0
        assert len(agent_cmds) >= 10  # At least 10 agents

    def test_generate_creates_utility_commands(self, generator):
        """Test that utility commands are generated."""
        result = generator.generate()

        # Should have utility commands
        utility_ids = {"status", "sprint", "task"}
        found_utilities = {c.id for c in result.commands if c.id in utility_ids}
        assert found_utilities == utility_ids

    def test_command_has_toml_format(self, generator):
        """Test that commands are in TOML format."""
        result = generator.generate()

        for cmd in result.commands:
            assert 'description = "' in cmd.content
            assert 'prompt = """' in cmd.content
            assert '"""' in cmd.content  # Ends with triple quotes (may have trailing newline)

    def test_command_has_do_not_edit_marker(self, generator):
        """Test that commands have do-not-edit marker."""
        result = generator.generate()

        for cmd in result.commands:
            assert "DO NOT EDIT" in cmd.content
            assert "vibey export gemini" in cmd.content

    def test_checksum_is_stable(self, generator):
        """Test that checksum is stable across regenerations."""
        result1 = generator.generate()
        result2 = generator.generate()

        assert result1.checksum == result2.checksum

    def test_checksum_is_16_chars(self, generator):
        """Test that checksum is truncated to 16 characters."""
        result = generator.generate()

        assert len(result.checksum) == 16

    def test_manifest_has_expected_fields(self, generator):
        """Test that manifest has expected fields."""
        result = generator.generate()
        manifest = result.manifest

        assert "version" in manifest
        assert "generated_at" in manifest
        assert "commands_count" in manifest
        assert "workflows_count" in manifest
        assert "agents_count" in manifest
        assert "commands" in manifest

    def test_manifest_commands_count_matches(self, generator):
        """Test that manifest command count matches actual count."""
        result = generator.generate()

        assert result.manifest["commands_count"] == len(result.commands)

    def test_write_to_directory(self, generator, tmp_path):
        """Test writing commands to directory."""
        output_dir = tmp_path / "commands"

        result = generator.write_to_directory(output_dir)

        # Check namespace directory created
        assert (output_dir / "vibey").exists()

        # Check commands written
        for cmd in result.commands:
            cmd_path = output_dir / "vibey" / cmd.filename
            assert cmd_path.exists()
            assert cmd_path.read_text() == cmd.content

        # Check manifest written
        manifest_path = output_dir / "vibey" / "_manifest.json"
        assert manifest_path.exists()

    def test_command_filename_format(self, generator):
        """Test that command filenames follow expected format."""
        result = generator.generate()

        for cmd in result.commands:
            assert cmd.filename.endswith(".toml")
            assert "-" in cmd.filename or cmd.filename in ["status.toml", "sprint.toml", "task.toml"]


class TestGeneratedCommand:
    """Test GeneratedCommand dataclass."""

    def test_dataclass_fields(self):
        """Test GeneratedCommand has expected fields."""
        cmd = GeneratedCommand(
            id="test-cmd",
            filename="test-cmd.toml",
            content='description = "test"',
            source_workflow="test.md",
        )

        assert cmd.id == "test-cmd"
        assert cmd.filename == "test-cmd.toml"
        assert cmd.content == 'description = "test"'
        assert cmd.source_workflow == "test.md"


class TestCommandGenerationResult:
    """Test CommandGenerationResult dataclass."""

    def test_dataclass_fields(self):
        """Test CommandGenerationResult has expected fields."""
        result = CommandGenerationResult(
            commands=[],
            checksum="abc123",
            generated_at=datetime.now(),
            manifest={"version": "1.0.0"},
        )

        assert result.commands == []
        assert result.checksum == "abc123"
        assert isinstance(result.generated_at, datetime)
        assert result.manifest == {"version": "1.0.0"}
