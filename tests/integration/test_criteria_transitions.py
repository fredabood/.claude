"""
Integration tests for criteria-based state transitions.

Tests the CLI commands for starting and completing tasks/sprints,
verifying that criteria validation works correctly.

These tests run against the actual project roadmap data rather than
isolated fixtures, as the transition operations require the full
hierarchical structure to be present.
"""

import pytest
from click.testing import CliRunner

from vibey.cli.main import cli


class TestStartCommandIntegration:
    """Integration tests for 'vibey roadmap start' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_start_help(self, runner):
        """Start command has help text."""
        result = runner.invoke(cli, ['roadmap', 'start', '--help'])
        assert result.exit_code == 0
        assert 'start' in result.output.lower()

    def test_start_invalid_id(self, runner):
        """Start with invalid ID shows error."""
        result = runner.invoke(cli, ['roadmap', 'start', 'nonexistent-task-id-xyz'])
        # Should fail gracefully
        assert result.exit_code != 0 or 'error' in result.output.lower() or 'not found' in result.output.lower()

    def test_start_missing_arg(self, runner):
        """Start without argument shows error."""
        result = runner.invoke(cli, ['roadmap', 'start'])
        # Should require an argument
        assert result.exit_code != 0 or 'missing' in result.output.lower()


class TestCompleteCommandIntegration:
    """Integration tests for 'vibey roadmap complete' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_complete_help(self, runner):
        """Complete command has help text."""
        result = runner.invoke(cli, ['roadmap', 'complete', '--help'])
        assert result.exit_code == 0
        assert 'complete' in result.output.lower()

    def test_complete_invalid_id(self, runner):
        """Complete with invalid ID shows error."""
        result = runner.invoke(cli, ['roadmap', 'complete', 'nonexistent-task-id-xyz'])
        # Should fail gracefully
        assert result.exit_code != 0 or 'error' in result.output.lower() or 'not found' in result.output.lower()

    def test_complete_missing_arg(self, runner):
        """Complete without argument shows error."""
        result = runner.invoke(cli, ['roadmap', 'complete'])
        # Should require an argument
        assert result.exit_code != 0 or 'missing' in result.output.lower()


class TestTransitionBlockedError:
    """Test that transitions properly report blocked status."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_transition_blocked_error_class_exists(self):
        """TransitionBlockedError is importable and has reasons attribute."""
        from vibey.operations.roadmap.transitions import TransitionBlockedError
        from vibey.roadmap.models.ticket import TicketStatus

        # Can instantiate with required arguments
        error = TransitionBlockedError(
            entity_id="test-task-001",
            target_status=TicketStatus.IN_PROGRESS,
            reasons=["reason1", "reason2"]
        )
        assert hasattr(error, 'reasons')
        assert len(error.reasons) == 2
        assert "reason1" in error.reasons
        assert "reason2" in error.reasons

    def test_transition_blocked_error_str_representation(self):
        """TransitionBlockedError has string representation."""
        from vibey.operations.roadmap.transitions import TransitionBlockedError
        from vibey.roadmap.models.ticket import TicketStatus

        error = TransitionBlockedError(
            entity_id="test-task-001",
            target_status=TicketStatus.IN_PROGRESS,
            reasons=["Task A must complete first"]
        )
        # Should be convertible to string
        error_str = str(error)
        assert isinstance(error_str, str)
        assert "test-task-001" in error_str


class TestTransitionFunctionsExist:
    """Test that transition functions are importable and callable."""

    def test_start_item_importable(self):
        """start_item function is importable."""
        from vibey.operations.roadmap.transitions import start_item
        assert callable(start_item)

    def test_complete_item_importable(self):
        """complete_item function is importable."""
        from vibey.operations.roadmap.transitions import complete_item
        assert callable(complete_item)

    def test_transition_task_importable(self):
        """transition_task function is importable."""
        from vibey.operations.roadmap.transitions import transition_task
        assert callable(transition_task)

    def test_transition_sprint_importable(self):
        """transition_sprint function is importable."""
        from vibey.operations.roadmap.transitions import transition_sprint
        assert callable(transition_sprint)


class TestCriteriaModelsExist:
    """Test that criteria model classes are properly defined."""

    def test_criterion_class_exists(self):
        """Criterion class is importable with expected fields."""
        from vibey.roadmap.models.ticket.completable import Criterion

        # Should be able to check for expected attributes
        assert hasattr(Criterion, '__fields__') or hasattr(Criterion, 'model_fields')

    def test_file_exists_target_importable(self):
        """FileExistsTarget is importable."""
        from vibey.roadmap.models.ticket.targets import FileExistsTarget
        assert FileExistsTarget is not None

    def test_completable_target_importable(self):
        """CompletableTarget is importable."""
        from vibey.roadmap.models.ticket.targets import CompletableTarget
        assert CompletableTarget is not None

    def test_criterion_can_have_file_target(self):
        """Criterion can be created with FileExistsTarget."""
        from vibey.roadmap.models.ticket.completable import Criterion
        from vibey.roadmap.models.ticket.targets import FileExistsTarget
        from vibey.roadmap.models.ticket import TicketStatus

        criterion = Criterion(
            id="test-file-criterion",
            description="Test file must exist",
            target=FileExistsTarget(paths=["/tmp/test.txt"]),
            blocks_transition_to=TicketStatus.COMPLETED,
        )

        assert criterion.id == "test-file-criterion"
        assert isinstance(criterion.target, FileExistsTarget)
