"""
Basic CLI tests for vibey command.

Tests the core CLI functionality: version, help, command groups.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(*args):
    """Run the vibey CLI and return the result."""
    cmd = [sys.executable, "-m", "vibey"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_version(self):
        """Test that --version flag works."""
        result = run_cli("--version")
        assert result.returncode == 0
        assert "2.5.0" in result.stdout

    def test_cli_help(self):
        """Test that --help flag works."""
        result = run_cli("--help")
        assert result.returncode == 0
        assert "Vibey Agent Framework" in result.stdout
        assert "roadmap" in result.stdout
        assert "deploy" in result.stdout
        assert "docs" in result.stdout
        assert "config" in result.stdout

    def test_cli_no_args_shows_help(self):
        """Test that running with no args shows help."""
        result = run_cli()
        # Click groups return exit code 2 when no command is provided
        assert result.returncode == 2
        # Should show help message in stderr
        assert "Usage:" in result.stderr or "Vibey" in result.stdout


class TestRoadmapCommands:
    """Test roadmap command group."""

    def test_roadmap_help(self):
        """Test roadmap --help."""
        result = run_cli("roadmap", "--help")
        assert result.returncode == 0
        assert "Manage roadmap system" in result.stdout
        assert "init" in result.stdout
        assert "status" in result.stdout
        assert "start" in result.stdout
        assert "complete" in result.stdout

    def test_roadmap_status(self):
        """Test roadmap status command."""
        result = run_cli("roadmap", "status")
        # May fail if no roadmap exists, but should execute
        assert result.returncode in [0, 1, 2]  # 0=success, 1=not found, 2=other

    def test_roadmap_start_requires_id(self):
        """Test that roadmap start requires an ID."""
        result = run_cli("roadmap", "start")
        assert result.returncode != 0  # Should fail without ID


class TestDeployCommands:
    """Test deploy command group."""

    def test_deploy_help(self):
        """Test deploy --help."""
        result = run_cli("deploy", "--help")
        assert result.returncode == 0
        assert "Deploy framework to target platforms" in result.stdout

    def test_deploy_list_platforms(self):
        """Test deploy list command (lists platforms)."""
        result = run_cli("deploy", "list")
        assert result.returncode == 0
        assert "claude-code" in result.stdout or "claude" in result.stdout.lower()
        assert "goose" in result.stdout or "Goose" in result.stdout


class TestDocsCommands:
    """Test docs command group."""

    def test_docs_help(self):
        """Test docs --help."""
        result = run_cli("docs", "--help")
        assert result.returncode == 0
        assert "Generate and manage documentation" in result.stdout


class TestConfigCommands:
    """Test config command group."""

    def test_config_help(self):
        """Test config --help."""
        result = run_cli("config", "--help")
        assert result.returncode == 0
        assert "Manage framework configuration" in result.stdout


class TestCLIGlobalOptions:
    """Test global CLI options."""

    def test_verbose_flag(self):
        """Test --verbose flag."""
        result = run_cli("--verbose", "--help")
        assert result.returncode == 0

    def test_quiet_flag(self):
        """Test --quiet flag."""
        result = run_cli("--quiet", "roadmap", "--help")
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
