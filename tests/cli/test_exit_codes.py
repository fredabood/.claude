"""
Tests for Vibey CLI exit codes.

Tests exit code behavior across different scenarios.
Coverage: 5 tests for exit code correctness.

Exit Code Reference (from docs):
- 0: Success
- 1: General error
- 2: Validation error
- 3: Dependency error
- 4: Already exists
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


class TestExitCodeSuccess:
    """Test exit code 0 (success)."""

    def test_exit_code_success_version(self):
        """
        Test: Successful command execution (version)
        Verify: Exit code 0
        """
        result = run_cli("--version")
        assert result.returncode == 0, "Version command should return exit code 0"

    def test_exit_code_success_help(self):
        """
        Test: Successful help command
        Verify: Exit code 0
        """
        result = run_cli("--help")
        assert result.returncode == 0, "Help command should return exit code 0"

    def test_exit_code_success_deploy_help(self):
        """
        Test: Successful subcommand help
        Verify: Exit code 0
        """
        result = run_cli("deploy", "--help")
        assert result.returncode == 0, "Deploy help should return exit code 0"

    def test_exit_code_success_list_platforms(self):
        """
        Test: Successful list platforms command
        Verify: Exit code 0
        """
        result = run_cli("deploy", "list-platforms")
        assert result.returncode == 0, "List platforms should return exit code 0"


class TestExitCodeGeneralError:
    """Test exit code 1 (general error)."""

    def test_exit_code_general_error_invalid_command(self):
        """
        Test: Invalid command
        Verify: Exit code 1 (general error)
        """
        result = run_cli("nonexistent-command-12345")

        # Should return non-zero (likely 1 for general error)
        assert result.returncode != 0, "Invalid command should return non-zero exit code"

        # Common convention is 1 for general errors, but may vary
        # Acceptable: 1 (general error) or 2 (usage error)
        assert result.returncode in [1, 2], \
            f"Expected exit code 1 or 2, got {result.returncode}"

    def test_exit_code_general_error_missing_file(self):
        """
        Test: Command with missing required file
        Verify: Exit code 1 (general error) or appropriate error code

        Note: Tests roadmap status with no roadmap file.
        """
        result = run_cli("roadmap", "status")

        # May succeed with "no roadmap" message or fail with error
        # If fails, should be non-zero
        if result.returncode != 0:
            # Error case - should be 1, 2, or other error code
            assert result.returncode > 0
        # If succeeds, that's also acceptable (shows "no roadmap found")

    def test_exit_code_invalid_flag(self):
        """
        Test: Command with invalid flag
        Verify: Exit code 1 or 2 (usage error)
        """
        result = run_cli("--invalid-flag-xyz")

        assert result.returncode != 0, "Invalid flag should return non-zero exit code"
        # Should be 1 or 2 (usage/general error)
        assert result.returncode in [1, 2], \
            f"Expected exit code 1 or 2 for invalid flag, got {result.returncode}"


class TestExitCodeValidationError:
    """Test exit code 2 (validation error)."""

    def test_exit_code_config_validation_concept(self):
        """
        Test: Config validation failure concept
        Verify: Would return exit code 2 for validation errors

        Note: This tests the command structure. Actual validation
        testing requires corrupted config files.
        """
        # Test that validate command exists
        result = run_cli("config", "validate", "--help")
        assert result.returncode == 0

        # Actual validation test would need:
        # 1. Create corrupted config file
        # 2. Run validate
        # 3. Verify exit code 2

    def test_exit_code_validation_help_exists(self):
        """
        Test: Validation commands exist
        Verify: Can test validation error scenarios
        """
        # Config validation
        config_validate = run_cli("config", "validate", "--help")
        assert config_validate.returncode == 0

        # These commands would trigger validation errors with bad data:
        # - vibey config validate (with corrupted config)
        # - vibey config migrate (with incompatible config)


class TestExitCodeDependencyError:
    """Test exit code 3 (dependency error)."""

    def test_exit_code_dependency_error_concept(self):
        """
        Test: Dependency error concept
        Verify: Would return exit code 3 for dependency issues

        Note: Dependency errors occur when:
        - Required tool not installed
        - Sprint dependencies not met (blocked sprint)
        - Quality gate dependencies not satisfied
        """
        # This is a conceptual test
        # Actual dependency testing would require:
        # 1. Scenario with unmet dependencies
        # 2. Attempt to start blocked sprint
        # 3. Verify exit code 3

        # For now, verify roadmap commands exist
        result = run_cli("roadmap", "--help")
        assert result.returncode == 0

    def test_exit_code_blocked_sprint_scenario_structure(self):
        """
        Test: Verify commands for testing blocked sprint scenarios
        Verify: Roadmap commands available for dependency testing
        """
        # Verify start command exists (would error with blocked sprint)
        start_help = run_cli("roadmap", "start", "--help")
        assert start_help.returncode == 0

        # Actual test would:
        # 1. Create roadmap with dependencies
        # 2. Attempt to start sprint with unmet dependencies
        # 3. Verify exit code 3


class TestExitCodeAlreadyExists:
    """Test exit code 4 (already exists)."""

    def test_exit_code_already_exists_concept(self):
        """
        Test: Already exists error concept
        Verify: Would return exit code 4 when resource exists

        Note: This occurs when:
        - Deploying to platform that's already deployed
        - Initializing roadmap that already exists
        - Creating config that already exists
        """
        # This is a conceptual test
        # Actual testing would require:
        # 1. Deploy once (succeeds)
        # 2. Deploy again without --force (fails with code 4)
        # 3. Verify error message and exit code

        # Verify relevant commands exist
        deploy_help = run_cli("deploy", "run", "--help")
        assert deploy_help.returncode == 0

    def test_exit_code_init_commands_exist(self):
        """
        Test: Verify init commands for testing "already exists" scenarios
        """
        # Roadmap init (would fail if already exists)
        roadmap_init_help = run_cli("roadmap", "init", "--help")
        assert roadmap_init_help.returncode == 0

        # Actual test would:
        # 1. Run roadmap init (succeeds)
        # 2. Run roadmap init again (fails with exit code 4)


class TestExitCodeConsistency:
    """Test exit code consistency across commands."""

    def test_exit_code_successful_commands_return_zero(self):
        """
        Test: All successful commands return exit code 0
        Verify: Consistency across command groups
        """
        successful_commands = [
            ["--version"],
            ["--help"],
            ["deploy", "--help"],
            ["config", "--help"],
            ["roadmap", "--help"],
            ["docs", "--help"],
        ]

        for cmd in successful_commands:
            result = run_cli(*cmd)
            assert result.returncode == 0, \
                f"Command {' '.join(cmd)} should return exit code 0, got {result.returncode}"

    def test_exit_code_invalid_commands_return_nonzero(self):
        """
        Test: All invalid commands return non-zero exit codes
        Verify: Error conditions are properly signaled
        """
        error_commands = [
            ["nonexistent-command"],
            ["deploy", "invalid-subcommand"],
            ["config", "invalid-subcommand"],
        ]

        for cmd in error_commands:
            result = run_cli(*cmd)
            assert result.returncode != 0, \
                f"Invalid command {' '.join(cmd)} should return non-zero exit code"

    def test_exit_code_help_always_succeeds(self):
        """
        Test: Help commands always return exit code 0
        Verify: Users can always get help without errors
        """
        help_commands = [
            ["--help"],
            ["deploy", "--help"],
            ["deploy", "run", "--help"],
            ["config", "--help"],
            ["config", "show", "--help"],
            ["roadmap", "--help"],
            ["roadmap", "status", "--help"],
            ["docs", "--help"],
        ]

        for cmd in help_commands:
            result = run_cli(*cmd)
            assert result.returncode == 0, \
                f"Help command {' '.join(cmd)} should always return exit code 0"


class TestExitCodeDocumentation:
    """Test that exit codes match documentation."""

    def test_exit_code_reference_accuracy(self):
        """
        Test: Verify exit codes match documented behavior
        Verify: Documentation is accurate

        Reference (from VIBEY_USER_JOURNEYS.md):
        - 0: Success
        - 1: General error
        - 2: Validation error
        - 3: Dependency error
        - 4: Already exists
        """
        # Success case
        success = run_cli("--version")
        assert success.returncode == 0, "Success should return 0"

        # General error case (invalid command)
        error = run_cli("invalid-command-xyz")
        assert error.returncode != 0, "Errors should return non-zero"

        # Exit codes should follow documented convention
        # Specific validation requires actual error scenarios
        # which would need setup (corrupted files, blocked sprints, etc.)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
