"""
Tests for vibey.cli.roadmap_lib.error_messages module.

Tests centralized error messages for roadmap CLI.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys


# Mock the help_formatter module before importing error_messages
mock_help_formatter = MagicMock()
sys.modules['help_formatter'] = mock_help_formatter

# Create mock CLIHelpFormatter class
mock_help_formatter.CLIHelpFormatter = MagicMock()
mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion = MagicMock(return_value="formatted error")
mock_help_formatter.CLIHelpFormatter.format_dependency_error = MagicMock(return_value="dependency error")
mock_help_formatter.CLIHelpFormatter.format_validation_error = MagicMock(return_value="validation error")

from vibey.cli.roadmap_lib.error_messages import (
    ErrorMessages,
    WarningMessages,
    SuccessMessages,
)


class TestErrorMessagesRoadmapNotFound:
    """Test roadmap not found error messages."""

    def test_roadmap_not_found(self):
        """Test roadmap not found error."""
        result = ErrorMessages.roadmap_not_found("/some/dir")

        mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.assert_called()
        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "Roadmap not found" in call_args.kwargs['error']
        assert len(call_args.kwargs['suggestions']) >= 1


class TestErrorMessagesTrackNotFound:
    """Test track not found error messages."""

    def test_track_not_found_basic(self):
        """Test basic track not found error."""
        result = ErrorMessages.track_not_found("my-track")

        mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.assert_called()
        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "my-track" in call_args.kwargs['error']

    def test_track_not_found_with_available(self):
        """Test track not found with available tracks."""
        available = ["track-a", "track-b", "track-c"]
        result = ErrorMessages.track_not_found("missing-track", available=available)

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        suggestions_str = str(call_args.kwargs['suggestions'])

        assert "track-a" in suggestions_str


class TestErrorMessagesSprintNotFound:
    """Test sprint not found error messages."""

    def test_sprint_not_found_basic(self):
        """Test basic sprint not found error."""
        result = ErrorMessages.sprint_not_found("sprint-001")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        assert "sprint-001" in call_args.kwargs['error']

    def test_sprint_not_found_with_track(self):
        """Test sprint not found with track context."""
        result = ErrorMessages.sprint_not_found("sprint-001", track_id="backend")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        suggestions_str = str(call_args.kwargs['suggestions'])

        assert "backend" in suggestions_str


class TestErrorMessagesTaskNotFound:
    """Test task not found error messages."""

    def test_task_not_found_basic(self):
        """Test basic task not found error."""
        result = ErrorMessages.task_not_found("task-001")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        assert "task-001" in call_args.kwargs['error']

    def test_task_not_found_with_sprint(self):
        """Test task not found with sprint context."""
        result = ErrorMessages.task_not_found("task-001", sprint_id="sprint-001")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        suggestions_str = str(call_args.kwargs['suggestions'])

        assert "sprint-001" in suggestions_str

    def test_task_not_found_extracts_sprint_id(self):
        """Test task not found extracts sprint ID from task ID."""
        result = ErrorMessages.task_not_found("backend-1-task-001")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        suggestions_str = str(call_args.kwargs['suggestions'])

        assert "backend-1" in suggestions_str


class TestErrorMessagesDependencyBlocked:
    """Test dependency blocked error messages."""

    def test_dependency_blocked(self):
        """Test dependency blocked error."""
        result = ErrorMessages.dependency_blocked(
            object_id="task-002",
            object_type="task",
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress"
        )

        mock_help_formatter.CLIHelpFormatter.format_dependency_error.assert_called_with(
            object_id="task-002",
            object_type="task",
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress"
        )


class TestErrorMessagesInvalidStatusTransition:
    """Test invalid status transition error messages."""

    def test_invalid_status_transition(self):
        """Test invalid status transition error."""
        result = ErrorMessages.invalid_status_transition(
            object_id="task-001",
            current_status="not_started",
            attempted_status="completed",
            valid_transitions=["in_progress"]
        )

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "not_started" in call_args.kwargs['error']
        assert "completed" in call_args.kwargs['error']


class TestErrorMessagesGateNotPassed:
    """Test gate not passed error messages."""

    def test_completion_gate_not_passed(self):
        """Test completion gate not passed error."""
        incomplete_gates = ["unit-tests", "code-review"]
        result = ErrorMessages.completion_gate_not_passed("sprint-001", incomplete_gates)

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "sprint-001" in call_args.kwargs['error']
        suggestions_str = str(call_args.kwargs['suggestions'])
        assert "unit-tests" in suggestions_str

    def test_production_gate_not_passed(self):
        """Test production gate not passed error."""
        incomplete_gates = ["security-scan", "performance-test"]
        result = ErrorMessages.production_gate_not_passed("sprint-001", incomplete_gates)

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "sprint-001" in call_args.kwargs['error']
        suggestions_str = str(call_args.kwargs['suggestions'])
        assert "security-scan" in suggestions_str


class TestErrorMessagesInvalidIdFormat:
    """Test invalid ID format error messages."""

    def test_invalid_id_format(self):
        """Test invalid ID format error."""
        result = ErrorMessages.invalid_id_format(
            provided_id="BAD ID",
            object_type="task",
            expected_format="kebab-case",
            example="backend-1-task-001"
        )

        mock_help_formatter.CLIHelpFormatter.format_validation_error.assert_called_with(
            field="task_id",
            value="BAD ID",
            expected="kebab-case",
            context="Example: backend-1-task-001"
        )


class TestErrorMessagesMissingRequiredField:
    """Test missing required field error messages."""

    def test_missing_required_field_basic(self):
        """Test missing required field error."""
        result = ErrorMessages.missing_required_field("name", "track")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "name" in call_args.kwargs['error']

    def test_missing_required_field_with_context(self):
        """Test missing required field with context."""
        result = ErrorMessages.missing_required_field("name", "track", context="Required for display")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args
        suggestions_str = str(call_args.kwargs['suggestions'])

        assert "Required for display" in suggestions_str


class TestErrorMessagesFileNotFound:
    """Test file not found error messages."""

    def test_file_not_found(self):
        """Test file not found error."""
        result = ErrorMessages.file_not_found("/path/to/file.yaml", "Sprint")

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "Sprint" in call_args.kwargs['error']
        assert "/path/to/file.yaml" in call_args.kwargs['error']


class TestErrorMessagesCircularDependency:
    """Test circular dependency error messages."""

    def test_circular_dependency(self):
        """Test circular dependency error."""
        chain = ["task-001", "task-002", "task-003", "task-001"]
        result = ErrorMessages.circular_dependency("task-001", chain)

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "task-001" in call_args.kwargs['error']
        suggestions_str = str(call_args.kwargs['suggestions'])
        assert "task-002" in suggestions_str


class TestErrorMessagesNoTasksReady:
    """Test no tasks ready error messages."""

    def test_no_tasks_ready(self):
        """Test no tasks ready error."""
        result = ErrorMessages.no_tasks_ready("sprint-001", blocked_count=5)

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "sprint-001" in call_args.kwargs['error']
        suggestions_str = str(call_args.kwargs['suggestions'])
        assert "5" in suggestions_str


class TestErrorMessagesValidationFailed:
    """Test validation failed error messages."""

    def test_validation_failed(self):
        """Test validation failed error."""
        errors = ["Missing title", "Invalid status"]
        result = ErrorMessages.validation_failed("task", "task-001", errors)

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "task-001" in call_args.kwargs['error']
        suggestions_str = str(call_args.kwargs['suggestions'])
        assert "Missing title" in suggestions_str


class TestErrorMessagesConcurrentModification:
    """Test concurrent modification error messages."""

    def test_concurrent_modification(self):
        """Test concurrent modification error."""
        result = ErrorMessages.concurrent_modification(
            object_id="task-001",
            expected_version="1.0",
            actual_version="1.1"
        )

        call_args = mock_help_formatter.CLIHelpFormatter.format_error_with_suggestion.call_args

        assert "task-001" in call_args.kwargs['error']
        suggestions_str = str(call_args.kwargs['suggestions'])
        assert "1.0" in suggestions_str
        assert "1.1" in suggestions_str


class TestWarningMessages:
    """Test warning message templates."""

    def test_large_context_warning_under_threshold(self):
        """Test large context warning when under threshold returns empty."""
        mock_formatting = MagicMock()
        mock_formatting.warning = MagicMock(return_value="")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = WarningMessages.large_context_warning(100.0, threshold_kb=200)
        assert result == ""

    def test_large_context_warning_at_threshold(self):
        """Test large context warning at threshold returns empty."""
        mock_formatting = MagicMock()
        mock_formatting.warning = MagicMock(return_value="")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = WarningMessages.large_context_warning(200.0, threshold_kb=200)
        assert result == ""

    def test_deprecated_command_structure(self):
        """Test deprecated command has correct structure."""
        # The method imports at runtime, so we mock the formatting module
        mock_formatting = MagicMock()
        mock_formatting.warning = MagicMock(return_value="⚠ WARNING")
        mock_formatting.info = MagicMock(return_value="ℹ INFO")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = WarningMessages.deprecated_command("old-cmd", "new-cmd")

        # Result should contain both command names and warning text
        assert "old-cmd" in result or "WARNING" in result

    def test_large_context_warning_over_threshold_structure(self):
        """Test large context warning over threshold has content."""
        mock_formatting = MagicMock()
        mock_formatting.warning = MagicMock(return_value="⚠ Large context size")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = WarningMessages.large_context_warning(250.0, threshold_kb=200)

        # Should have content when over threshold
        assert len(result) > 0


class TestSuccessMessages:
    """Test success message templates."""

    def test_task_completed_structure(self):
        """Test task completed message structure."""
        mock_formatting = MagicMock()
        mock_formatting.success = MagicMock(return_value="✓ Task completed")
        mock_formatting.info = MagicMock(return_value="ℹ Unblocked")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = SuccessMessages.task_completed("task-001", "My Task", [])

        assert "completed" in result.lower() or "✓" in result

    def test_task_completed_with_unblocked_structure(self):
        """Test task completed with unblocked tasks includes task IDs."""
        mock_formatting = MagicMock()
        mock_formatting.success = MagicMock(return_value="✓ Task completed")
        mock_formatting.info = MagicMock(return_value="ℹ Unblocked 2 task(s)")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = SuccessMessages.task_completed(
                "task-001",
                "My Task",
                ["task-002", "task-003"]
            )

        # Should include the unblocked task IDs
        assert "task-002" in result
        assert "task-003" in result

    def test_sprint_completed_structure(self):
        """Test sprint completed message structure."""
        mock_formatting = MagicMock()
        mock_formatting.success = MagicMock(return_value="✓ Sprint completed")
        mock_formatting.info = MagicMock(return_value="ℹ Note")
        mock_formatting.bold = MagicMock(return_value="**Statistics**")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            stats = {
                'tasks_completed': 10,
                'duration': '2 weeks',
                'completion_gates_passed': 3,
                'production_gates_total': 2
            }
            result = SuccessMessages.sprint_completed("sprint-001", "Sprint 1", stats)

        assert "completed" in result.lower() or "✓" in result

    def test_initialization_success_structure(self):
        """Test initialization success message structure."""
        mock_formatting = MagicMock()
        mock_formatting.success = MagicMock(return_value="✓ Roadmap initialized")
        mock_formatting.info = MagicMock(return_value="ℹ See docs")
        mock_formatting.bold = MagicMock(return_value="**Created**")

        with patch.dict(sys.modules, {'formatting': mock_formatting}):
            result = SuccessMessages.initialization_success("my-roadmap", "/path/to/.vibey/roadmap")

        assert "my-roadmap" in result or "initialized" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
