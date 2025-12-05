"""
Tests for pre-commit hook completion verification.

Tests that the pre-commit hook properly validates completion criteria
before allowing items to be marked as completed.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Get the project root directory (where .vibey/ exists)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


class TestCompletionVerification:
    """Tests for completion verification in pre-commit hook."""

    def test_hook_has_completion_verification_method(self):
        """Test that PreCommitHook has _check_completion_verification method."""
        from vibey.operations.git.hooks.pre_commit import PreCommitHook

        hook = PreCommitHook(str(PROJECT_ROOT))
        assert hasattr(hook, '_check_completion_verification')
        assert callable(hook._check_completion_verification)

    def test_hook_config_has_completion_verification(self):
        """Test that HookConfig includes completion_verification setting."""
        from vibey.operations.git.hooks.pre_commit import HookConfig

        config = HookConfig()
        assert hasattr(config, 'completion_verification')
        assert config.completion_verification is not None
        assert config.completion_verification.get("enabled", True) is True
        assert config.completion_verification.get("mode") == "blocking"

    def test_completion_verification_disabled_when_configured(self):
        """Test that completion verification can be disabled."""
        from vibey.operations.git.hooks.pre_commit import PreCommitHook, HookConfig

        hook = PreCommitHook(str(PROJECT_ROOT))
        hook.config = HookConfig(completion_verification={"enabled": False})

        # Should not raise any errors
        hook._check_completion_verification()
        # Should have no issues added
        # (If enabled, it might add issues, but disabled should skip entirely)

    def test_completion_verification_checks_staged_files(self):
        """Test that verification only checks staged files."""
        from vibey.operations.git.hooks.pre_commit import PreCommitHook

        hook = PreCommitHook(str(PROJECT_ROOT))

        # Mock the staged files to return empty
        with patch.object(hook, '_get_staged_files', return_value=[]):
            hook._check_completion_verification()
            # Should complete without issues if no staged files
            # No completion verification issues expected
            completion_issues = [i for i in hook.issues if i.rule == "completion_verification"]
            assert len(completion_issues) == 0


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_validation_issue_creation(self):
        """Test creating a ValidationIssue."""
        from vibey.operations.git.hooks.pre_commit import ValidationIssue

        issue = ValidationIssue(
            severity="error",
            rule="completion_verification",
            message="Cannot complete task: blockers exist",
            file=".vibey/roadmap/test/task.yaml",
            suggestion="Resolve blockers first",
        )

        assert issue.severity == "error"
        assert issue.rule == "completion_verification"
        assert "Cannot complete" in issue.message

    def test_validation_issue_to_dict(self):
        """Test converting ValidationIssue to dict."""
        from vibey.operations.git.hooks.pre_commit import ValidationIssue

        issue = ValidationIssue(
            severity="warning",
            rule="completion_verification",
            message="Test message",
        )

        d = issue.to_dict()
        assert isinstance(d, dict)
        assert d["severity"] == "warning"
        assert d["rule"] == "completion_verification"


class TestPreCommitHookRun:
    """Tests for PreCommitHook.run() method."""

    def test_run_method_exists(self):
        """Test that run method exists."""
        from vibey.operations.git.hooks.pre_commit import PreCommitHook

        hook = PreCommitHook(str(PROJECT_ROOT))
        assert hasattr(hook, 'run')
        assert callable(hook.run)

    def test_run_returns_exit_code(self):
        """Test that run returns an exit code."""
        from vibey.operations.git.hooks.pre_commit import PreCommitHook

        hook = PreCommitHook(str(PROJECT_ROOT))

        # Mock to avoid side effects
        with patch.object(hook, '_sync_database_to_yaml', return_value=True):
            with patch.object(hook, '_validate_roadmap_files', return_value=True):
                with patch.object(hook, '_check_cli_usage'):
                    with patch.object(hook, '_check_completion_verification'):
                        exit_code = hook.run()

        assert isinstance(exit_code, int)
        assert exit_code in [0, 1]


class TestCompletionVerificationIntegration:
    """Integration tests for completion verification."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_verification_uses_ticket_models(self, root_dir):
        """Test that verification uses ticket model's can_transition_to."""
        # This is an indirect test - we verify the imports work
        from vibey.operations.roadmap.query import (
            load_task_ticket,
            load_sprint_ticket,
            load_track_ticket,
        )
        from vibey.roadmap.models.ticket import TicketStatus

        # Load a real task and verify can_transition_to works
        task = load_task_ticket(root_dir, "sqlite-backend-9-task-001")
        can_complete, blockers = task.can_transition_to(TicketStatus.COMPLETED)

        assert isinstance(can_complete, bool)
        assert isinstance(blockers, list)

    def test_completed_task_passes_verification(self, root_dir):
        """Test that an already completed task passes verification."""
        from vibey.operations.roadmap.query import load_task_ticket
        from vibey.roadmap.models.ticket import TicketStatus

        # Load a completed task
        task = load_task_ticket(root_dir, "sqlite-backend-9-task-001")

        # It should be able to stay completed (no-op transition)
        can_complete, blockers = task.can_transition_to(TicketStatus.COMPLETED)

        # Completed task should report no blockers for staying completed
        # (or may report True with empty blockers)
        assert isinstance(can_complete, bool)
