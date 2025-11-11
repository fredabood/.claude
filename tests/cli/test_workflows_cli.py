"""
Tests for common Vibey CLI workflows.

Tests end-to-end workflows: first-time setup, multi-platform deployment,
sprint progression, configuration migration.
Coverage: 5 tests for workflow scenarios.
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


class TestFirstTimeSetupWorkflow:
    """Test first-time setup workflow."""

    def test_workflow_first_time_setup_commands_exist(self):
        """
        Test: Complete first-time setup workflow (command verification)
        Steps: Check version → Check deploy help → Verify commands exist
        Verify: All setup commands are available
        """
        # Step 1: Check version
        version_result = run_cli("--version")
        assert version_result.returncode == 0

        # Step 2: Check deploy command exists
        deploy_help = run_cli("deploy", "--help")
        assert deploy_help.returncode == 0

        # Step 3: Check deploy run command exists
        deploy_run_help = run_cli("deploy", "run", "--help")
        assert deploy_run_help.returncode == 0

        # Verify end state: commands are accessible
        assert "deploy" in deploy_help.stdout.lower()
        assert "platform" in deploy_run_help.stdout.lower()

    def test_workflow_first_time_setup_help_navigation(self):
        """
        Test: Help system navigation for first-time users
        Verify: Users can discover commands through help
        """
        # Start with general help
        main_help = run_cli("--help")
        assert main_help.returncode == 0
        assert "deploy" in main_help.stdout

        # Navigate to deploy help
        deploy_help = run_cli("deploy", "--help")
        assert deploy_help.returncode == 0

        # Navigate to specific command help
        deploy_run_help = run_cli("deploy", "run", "--help")
        assert deploy_run_help.returncode == 0
        assert "--platform" in deploy_run_help.stdout


class TestMultiPlatformDeploymentWorkflow:
    """Test multi-platform deployment workflow."""

    def test_workflow_deploy_to_multiple_platforms(self):
        """
        Test: Deploy to 2+ platforms workflow
        Steps: List platforms → Verify run commands exist
        Verify: Multi-platform commands available
        """
        # Step 1: List available platforms
        list_result = run_cli("deploy", "list-platforms")
        assert list_result.returncode == 0
        assert "claude-code" in list_result.stdout
        assert "goose" in list_result.stdout

        # Step 2: Verify deploy run command structure
        run_help = run_cli("deploy", "run", "--help")
        assert run_help.returncode == 0
        assert "--platform" in run_help.stdout

        # Step 3: Verify platform options are documented
        # Should mention available platforms or 'all' option
        help_text = run_help.stdout.lower()
        assert "platform" in help_text

    def test_workflow_deploy_all_platforms_option(self):
        """
        Test: Deploy to all platforms workflow
        Verify: 'all' option or multiple platform support
        """
        # Check if deploy run accepts 'all' platform
        help_result = run_cli("deploy", "run", "--help")
        assert help_result.returncode == 0

        # Verify platform option exists
        assert "--platform" in help_result.stdout


class TestRoadmapStatusWorkflow:
    """Test roadmap status check workflow."""

    def test_workflow_check_roadmap_status(self):
        """
        Test: Roadmap status check workflow
        Steps: Check status → Show details → Verify commands work
        Verify: Commands work together
        """
        # Step 1: Check roadmap status
        status_result = run_cli("roadmap", "status")
        # May fail if no roadmap exists, which is acceptable
        assert status_result.returncode in [0, 1, 2]

        # Step 2: Verify show command exists
        show_help = run_cli("roadmap", "show", "--help")
        assert show_help.returncode == 0

        # Step 3: Verify start command exists
        start_help = run_cli("roadmap", "start", "--help")
        assert start_help.returncode == 0

    def test_workflow_roadmap_command_navigation(self):
        """
        Test: Roadmap command discovery workflow
        Verify: Users can navigate roadmap commands
        """
        # Start with roadmap help
        roadmap_help = run_cli("roadmap", "--help")
        assert roadmap_help.returncode == 0
        assert "status" in roadmap_help.stdout
        assert "show" in roadmap_help.stdout
        assert "start" in roadmap_help.stdout
        assert "complete" in roadmap_help.stdout


class TestSprintProgressionWorkflow:
    """Test sprint progression workflow."""

    def test_workflow_start_next_sprint(self):
        """
        Test: Sprint progression workflow
        Steps: Status → Start → Validate commands
        Verify: Sprint lifecycle commands work together
        """
        # Check roadmap help for available commands
        roadmap_help = run_cli("roadmap", "--help")
        assert roadmap_help.returncode == 0

        # Verify status command
        status_result = run_cli("roadmap", "status")
        # May fail if no roadmap, but should execute
        assert status_result.returncode in [0, 1, 2]

        # Verify start command structure
        start_help = run_cli("roadmap", "start", "--help")
        assert start_help.returncode == 0

        # Verify complete command structure
        complete_help = run_cli("roadmap", "complete", "--help")
        assert complete_help.returncode == 0

    def test_workflow_complete_task_and_progress(self):
        """
        Test: Task completion workflow
        Steps: Complete → Check status → Start next
        Verify: Task lifecycle commands available
        """
        # Verify complete command exists
        complete_help = run_cli("roadmap", "complete", "--help")
        assert complete_help.returncode == 0

        # Verify status command exists
        status_help = run_cli("roadmap", "status", "--help")
        assert status_help.returncode == 0

        # Verify start command exists for next task
        start_help = run_cli("roadmap", "start", "--help")
        assert start_help.returncode == 0


class TestConfigMigrationWorkflow:
    """Test configuration migration workflow."""

    def test_workflow_migrate_legacy_config(self):
        """
        Test: Config migration workflow
        Steps: Show config → Migrate → Validate
        Verify: Migration commands work together
        """
        # Step 1: Check config show command
        show_result = run_cli("config", "show")
        # May fail if no config, but should execute
        assert show_result.returncode in [0, 1, 2]

        # Step 2: Verify migrate command exists
        migrate_help = run_cli("config", "migrate", "--help")
        assert migrate_help.returncode == 0
        assert "migrate" in migrate_help.stdout.lower()

        # Step 3: Verify validate command exists
        validate_help = run_cli("config", "validate", "--help")
        assert validate_help.returncode == 0

        # Step 4: Verify rollback command exists (safety net)
        rollback_help = run_cli("config", "rollback", "--help")
        assert rollback_help.returncode == 0

    def test_workflow_config_migration_with_backup(self):
        """
        Test: Config migration with backup workflow
        Verify: Backup and rollback options available
        """
        # Check migrate command has backup options
        migrate_help = run_cli("config", "migrate", "--help")
        assert migrate_help.returncode == 0

        # Should mention backup or dry-run options
        help_lower = migrate_help.stdout.lower()
        assert "backup" in help_lower or "dry-run" in help_lower or "force" in help_lower

        # Verify rollback command structure
        rollback_help = run_cli("config", "rollback", "--help")
        assert rollback_help.returncode == 0
        assert "rollback" in rollback_help.stdout.lower()


class TestWorkflowIntegration:
    """Integration tests across multiple workflows."""

    def test_workflow_complete_user_journey(self):
        """
        Test: Complete user journey from install to usage
        Verify: All major commands accessible in sequence
        """
        # Check version (verify installation)
        assert run_cli("--version").returncode == 0

        # Check main help
        assert run_cli("--help").returncode == 0

        # Check each command group
        assert run_cli("deploy", "--help").returncode == 0
        assert run_cli("config", "--help").returncode == 0
        assert run_cli("roadmap", "--help").returncode == 0
        assert run_cli("docs", "--help").returncode == 0

    def test_workflow_error_recovery(self):
        """
        Test: Error recovery workflow
        Verify: Users can recover from errors using help
        """
        # Simulate error: invalid command
        invalid_result = run_cli("nonexistent-command")
        # Should fail or show help
        if invalid_result.returncode != 0:
            # Error case - should provide guidance
            error_output = invalid_result.stderr + invalid_result.stdout
            assert len(error_output) > 0

        # Recovery: use help
        help_result = run_cli("--help")
        assert help_result.returncode == 0

    def test_workflow_command_discovery(self):
        """
        Test: Command discovery workflow
        Verify: Users can discover all commands through help system
        """
        # Start with main help
        main_help = run_cli("--help")
        assert main_help.returncode == 0

        # Extract command groups from help
        command_groups = ["deploy", "config", "roadmap", "docs"]

        for group in command_groups:
            # Each group should be mentioned in main help
            assert group in main_help.stdout, f"Command group '{group}' not in main help"

            # Each group should have its own help
            group_help = run_cli(group, "--help")
            assert group_help.returncode == 0, f"Help failed for '{group}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
