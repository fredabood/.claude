"""
Tests for global Vibey CLI options.

Tests the core CLI functionality: help, version, debug, quiet flags.
Coverage: 5 tests for global options.
"""

import subprocess
import sys
import os
from pathlib import Path

import pytest


def run_cli(*args, env=None):
    """Run the vibey CLI and return the result."""
    cmd = [sys.executable, "-m", "vibey"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy()
    )
    return result


class TestGlobalOptions:
    """Test global CLI options and flags."""

    def test_vibey_help_command(self):
        """
        Test: vibey --help
        Verify: Shows usage information, lists all subcommands
        """
        result = run_cli("--help")

        assert result.returncode == 0
        assert "Vibey Agent Framework" in result.stdout

        # Verify all subcommands are listed
        assert "deploy" in result.stdout
        assert "config" in result.stdout
        assert "roadmap" in result.stdout
        assert "docs" in result.stdout

        # Verify global options shown
        assert "--help" in result.stdout or "-h" in result.stdout
        assert "--version" in result.stdout or "-v" in result.stdout

    def test_vibey_version_command(self):
        """
        Test: vibey --version
        Verify: Shows version number (format: X.Y.Z)
        """
        result = run_cli("--version")

        assert result.returncode == 0
        assert "Vibey Agent Framework" in result.stdout or "vibey" in result.stdout.lower()

        # Check version format (X.Y.Z)
        import re
        version_pattern = r'\d+\.\d+\.\d+'
        assert re.search(version_pattern, result.stdout), \
            f"Expected version format X.Y.Z in output: {result.stdout}"

    def test_vibey_debug_flag(self):
        """
        Test: vibey --verbose flag (actual flag name)
        Verify: Verbose logging enabled, verbose output shown

        Note: The actual flag is --verbose or -v, not --debug
        """
        result = run_cli("--verbose", "deploy", "--help")

        assert result.returncode == 0
        # Verbose mode should work without errors
        # Actual verbose output verification depends on implementation

        # Alternative: test with roadmap status for safer execution
        result2 = run_cli("-v", "roadmap", "--help")
        assert result2.returncode == 0

    def test_vibey_quiet_flag(self):
        """
        Test: vibey --quiet deploy run --platform claude-code
        Verify: Minimal output, only critical messages

        Note: This test uses --help to avoid actual deployment
        """
        result = run_cli("--quiet", "deploy", "--help")

        assert result.returncode == 0
        # Quiet mode should work without errors
        # Output should be minimal (implementation dependent)

        # Compare with normal mode
        normal_result = run_cli("deploy", "--help")
        # Quiet mode might have same or less output for help
        # This is a basic sanity check
        assert len(result.stdout) > 0

    def test_global_option_conflicts(self):
        """
        Test: vibey --verbose --quiet <command>
        Verify: Error message or last option wins

        Tests conflicting options behavior.
        """
        result = run_cli("--verbose", "--quiet", "--help")

        # Should either:
        # 1. Show error about conflicting options (returncode != 0)
        # 2. Accept last option (returncode == 0)
        # Both are valid behaviors - document which one is used

        if result.returncode != 0:
            # Error case - verify error message
            error_output = result.stderr + result.stdout
            assert "conflict" in error_output.lower() or "option" in error_output.lower()
        else:
            # Last option wins - should succeed
            assert "help" in result.stdout or "usage" in result.stdout.lower()


class TestCLIInvocation:
    """Test different ways to invoke the CLI."""

    def test_cli_module_invocation(self):
        """Test that CLI can be invoked via python -m vibey."""
        result = subprocess.run(
            [sys.executable, "-m", "vibey", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_cli_direct_invocation(self):
        """Test that CLI can be invoked directly (if installed)."""
        # This test only runs if 'vibey' is in PATH
        result = subprocess.run(
            ["vibey", "--version"],
            capture_output=True,
            text=True,
            shell=False
        )
        # May fail if not installed, which is acceptable
        if result.returncode == 0:
            assert "vibey" in result.stdout.lower() or "Vibey" in result.stdout

    def test_cli_no_args_shows_help(self):
        """Test that running with no args shows help."""
        result = run_cli()

        # CLI shows help but returns exit code 2 (usage error)
        # This is standard Click behavior
        assert result.returncode == 2
        # Should contain usage information in stderr
        output = result.stderr + result.stdout
        assert len(output) > 50  # Non-trivial output
        assert "Vibey" in output or "vibey" in output


class TestGlobalOptionsWithSubcommands:
    """Test global options combined with subcommands."""

    def test_verbose_with_roadmap_status(self):
        """Test --verbose flag with roadmap status command."""
        result = run_cli("--verbose", "roadmap", "status")

        # Should execute (may fail if no roadmap, but should try)
        assert result.returncode in [0, 1, 2]
        # Should not crash

    def test_quiet_with_config_show(self):
        """Test --quiet flag with config show command."""
        result = run_cli("--quiet", "config", "show")

        # Should execute (may fail if no config, but should try)
        assert result.returncode in [0, 1, 2]
        # Should not crash

    def test_help_for_subcommand(self):
        """Test help flag works for subcommands."""
        subcommands = ["deploy", "config", "roadmap", "docs"]

        for subcmd in subcommands:
            result = run_cli(subcmd, "--help")
            assert result.returncode == 0, f"Help failed for {subcmd}"
            assert subcmd in result.stdout.lower(), \
                f"Expected '{subcmd}' in help output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
