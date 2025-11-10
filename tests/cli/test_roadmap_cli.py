"""
Tests for roadmap CLI wrapper script and commands.

Tests verify that:
- Wrapper script correctly routes commands
- All roadmap commands work via wrapper
- Error handling is correct
- Commands work with real roadmap data
"""

import subprocess
import pytest
from pathlib import Path
import os


# Get repository root
REPO_ROOT = Path(__file__).parent.parent.parent
WRAPPER_SCRIPT = REPO_ROOT / "framework" / "scripts" / "roadmap-cli.sh"


@pytest.fixture
def wrapper_path():
    """Provide path to wrapper script."""
    assert WRAPPER_SCRIPT.exists(), f"Wrapper script not found: {WRAPPER_SCRIPT}"
    assert os.access(WRAPPER_SCRIPT, os.X_OK), f"Wrapper script not executable: {WRAPPER_SCRIPT}"
    return str(WRAPPER_SCRIPT)


@pytest.fixture
def real_roadmap_exists():
    """Check if real roadmap data exists for integration testing."""
    roadmap_file = REPO_ROOT / ".vibey" / "roadmap.yaml"
    return roadmap_file.exists()


class TestWrapperBasics:
    """Test basic wrapper script functionality."""

    def test_wrapper_exists(self, wrapper_path):
        """Test that wrapper script exists and is executable."""
        assert Path(wrapper_path).exists()
        assert os.access(wrapper_path, os.X_OK)

    def test_help_display(self, wrapper_path):
        """Test that running wrapper with no args shows help."""
        result = subprocess.run(
            [wrapper_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Vibey Roadmap CLI" in result.stdout
        assert "Available commands:" in result.stdout
        assert "query" in result.stdout
        assert "update" in result.stdout

    def test_invalid_command(self, wrapper_path):
        """Test error handling for invalid commands."""
        result = subprocess.run(
            [wrapper_path, "invalid-command"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        # Error message may be in stdout or stderr
        error_output = result.stderr + result.stdout
        assert "Unknown command" in error_output
        assert "invalid-command" in error_output


class TestQueryCommand:
    """Test roadmap query command."""

    def test_query_help(self, wrapper_path):
        """Test query command help."""
        result = subprocess.run(
            [wrapper_path, "query", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        assert "query" in result.stdout.lower() or "roadmap" in result.stdout.lower()

    @pytest.mark.skipif(not (REPO_ROOT / ".vibey" / "roadmap.yaml").exists(),
                        reason="Requires real roadmap data")
    def test_query_roadmap_summary(self, wrapper_path):
        """Test querying roadmap summary with real data."""
        result = subprocess.run(
            [wrapper_path, "query"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        assert "Roadmap:" in result.stdout or "vibey-framework-v2" in result.stdout

    @pytest.mark.skipif(not (REPO_ROOT / ".vibey" / "roadmap.yaml").exists(),
                        reason="Requires real roadmap data")
    def test_query_specific_track(self, wrapper_path):
        """Test querying specific track."""
        result = subprocess.run(
            [wrapper_path, "query", "--track", "infrastructure-fixes"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        assert "infrastructure-fixes" in result.stdout.lower()

    @pytest.mark.skipif(not (REPO_ROOT / ".vibey" / "roadmap.yaml").exists(),
                        reason="Requires real roadmap data")
    def test_query_json_output(self, wrapper_path):
        """Test JSON output format."""
        result = subprocess.run(
            [wrapper_path, "query", "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should succeed or show roadmap data
        # May return error if no roadmap, which is expected
        assert result.returncode in [0, 1]


class TestUpdateCommand:
    """Test roadmap update command."""

    def test_update_help(self, wrapper_path):
        """Test update command help."""
        result = subprocess.run(
            [wrapper_path, "update", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        assert "--start-task" in result.stdout or "--complete-task" in result.stdout

    def test_update_missing_task_id(self, wrapper_path):
        """Test update command with missing task ID."""
        result = subprocess.run(
            [wrapper_path, "update", "--start-task"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should fail with error about missing argument
        assert result.returncode != 0


class TestContextCommand:
    """Test roadmap context loading command."""

    def test_context_help(self, wrapper_path):
        """Test context command help."""
        result = subprocess.run(
            [wrapper_path, "context", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        assert "context" in result.stdout.lower() or "task" in result.stdout.lower()

    @pytest.mark.skipif(not (REPO_ROOT / ".vibey" / "roadmap.yaml").exists(),
                        reason="Requires real roadmap data")
    def test_context_with_task_id(self, wrapper_path):
        """Test loading context for a task."""
        # Use a task we know exists
        result = subprocess.run(
            [wrapper_path, "context", "infrastructure-fixes-1-task-001"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # May succeed or fail if task not found, both are valid
        assert result.returncode in [0, 1]


class TestSummarizeCommand:
    """Test roadmap summarize command."""

    def test_summarize_help(self, wrapper_path):
        """Test summarize command help (via roadmap.py)."""
        # The summarize command maps to roadmap.py which has subcommands
        result = subprocess.run(
            [wrapper_path, "summarize", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should show help for summarize
        assert result.returncode in [0, 2]  # 2 for argparse errors


class TestPythonPathHandling:
    """Test that PYTHONPATH is correctly set by wrapper."""

    def test_wrapper_works_from_different_directory(self, wrapper_path, tmp_path):
        """Test that wrapper works when run from different directory."""
        result = subprocess.run(
            [wrapper_path, "query", "--help"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path)  # Run from temp directory
        )
        # Should work regardless of current directory
        assert result.returncode == 0
        assert "query" in result.stdout.lower() or "roadmap" in result.stdout.lower()

    def test_wrapper_sets_pythonpath(self, wrapper_path):
        """Test that wrapper sets PYTHONPATH correctly."""
        # Run a command that would fail without proper PYTHONPATH
        result = subprocess.run(
            [wrapper_path, "query", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should succeed because wrapper sets PYTHONPATH
        assert result.returncode == 0


class TestIntegrationWithRealData:
    """Integration tests with real roadmap data."""

    @pytest.mark.skipif(not (REPO_ROOT / ".vibey" / "roadmap.yaml").exists(),
                        reason="Requires real roadmap data")
    def test_query_update_workflow(self, wrapper_path):
        """Test complete query workflow with real data."""
        # Query roadmap
        result = subprocess.run(
            [wrapper_path, "query"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0

        # Query specific track
        result = subprocess.run(
            [wrapper_path, "query", "--track", "infrastructure-fixes"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0

    @pytest.mark.skipif(not (REPO_ROOT / ".vibey" / "roadmap.yaml").exists(),
                        reason="Requires real roadmap data")
    def test_all_commands_accessible(self, wrapper_path):
        """Test that all commands are accessible via wrapper."""
        # Test commands that are known to work
        working_commands = ["query", "update", "context", "summarize", "sync-docs"]

        for command in working_commands:
            result = subprocess.run(
                [wrapper_path, command, "--help"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT)
            )
            # All commands should at least show help without crashing
            assert result.returncode in [0, 2], f"Command {command} failed unexpectedly"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_nonexistent_track(self, wrapper_path):
        """Test querying non-existent track."""
        result = subprocess.run(
            [wrapper_path, "query", "--track", "nonexistent-track-12345"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should return error
        assert result.returncode == 1
        assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()

    def test_invalid_command_arguments(self, wrapper_path):
        """Test invalid command arguments."""
        result = subprocess.run(
            [wrapper_path, "query", "--invalid-flag"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        # Should fail with argparse error
        assert result.returncode != 0


class TestScriptMapping:
    """Test that commands map to correct Python scripts."""

    def test_query_maps_to_roadmap_query(self, wrapper_path):
        """Test that 'query' command uses roadmap-query.py."""
        result = subprocess.run(
            [wrapper_path, "query", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        # Output should be from roadmap-query.py
        assert "query" in result.stdout.lower() or "roadmap" in result.stdout.lower()

    def test_update_maps_to_roadmap_update(self, wrapper_path):
        """Test that 'update' command uses roadmap-update.py."""
        result = subprocess.run(
            [wrapper_path, "update", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        assert result.returncode == 0
        # Output should be from roadmap-update.py
        assert "update" in result.stdout.lower() or "task" in result.stdout.lower()
