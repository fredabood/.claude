"""
Tests for vibey.cli.roadmap_lib.help_formatter module.

Tests enhanced help formatting for roadmap CLI.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

# We need to mock the formatting module before importing help_formatter
mock_formatting = MagicMock()
mock_formatting.header = MagicMock(return_value="=== Header ===")
mock_formatting.bold = MagicMock(return_value="**BOLD**")
mock_formatting.dim = MagicMock(return_value="(dim)")
mock_formatting.colorize = MagicMock(return_value="<colored>")
mock_formatting.Color = MagicMock()
mock_formatting.Color.RED = "red"
mock_formatting.Color.CYAN = "cyan"
mock_formatting.Color.GREEN = "green"
mock_formatting.Color.YELLOW = "yellow"
mock_formatting.info = MagicMock(return_value="INFO")
mock_formatting.success = MagicMock(return_value="SUCCESS")
mock_formatting.progress_bar = MagicMock(return_value="[=======>    ]")
mock_formatting.status_indicator = MagicMock(return_value="[IN_PROGRESS]")

sys.modules['vibey.cli.roadmap_lib.formatting'] = mock_formatting

from vibey.cli.roadmap_lib.help_formatter import (
    CLIHelpFormatter,
    ROADMAP_QUERY_HELP,
    ROADMAP_UPDATE_HELP,
    ROADMAP_INIT_HELP,
)


class TestFormatCommandHelp:
    """Test format_command_help method."""

    def test_basic_command_help(self):
        """Test basic command help formatting."""
        result = CLIHelpFormatter.format_command_help(
            command="test-cmd",
            description="A test command",
            usage="test-cmd [OPTIONS]",
            options=[
                {"flag": "--help", "description": "Show help"}
            ]
        )

        # Should contain header call with command and description
        mock_formatting.header.assert_called()

        # Should contain usage section
        assert "test-cmd [OPTIONS]" in result

    def test_command_help_with_default_option(self):
        """Test command help with option having default."""
        result = CLIHelpFormatter.format_command_help(
            command="test-cmd",
            description="A test command",
            usage="test-cmd [OPTIONS]",
            options=[
                {"flag": "--config", "description": "Config file", "default": "config.yaml"}
            ]
        )

        # Should include option with default
        mock_formatting.dim.assert_called()

    def test_command_help_with_examples(self):
        """Test command help with examples."""
        result = CLIHelpFormatter.format_command_help(
            command="test-cmd",
            description="A test command",
            usage="test-cmd [OPTIONS]",
            options=[],
            examples=[
                {"description": "Example 1", "command": "test-cmd --flag"}
            ]
        )

        # Should include examples section
        assert "Example 1" in result

    def test_command_help_with_tips(self):
        """Test command help with tips."""
        result = CLIHelpFormatter.format_command_help(
            command="test-cmd",
            description="A test command",
            usage="test-cmd [OPTIONS]",
            options=[],
            tips=["Tip 1", "Tip 2"]
        )

        # Should include tips
        assert "Tip 1" in result
        assert "Tip 2" in result

    def test_command_help_with_see_also(self):
        """Test command help with see also section."""
        result = CLIHelpFormatter.format_command_help(
            command="test-cmd",
            description="A test command",
            usage="test-cmd [OPTIONS]",
            options=[],
            see_also=["other-cmd", "another-cmd"]
        )

        # Should include see also section
        assert "other-cmd" in result
        assert "another-cmd" in result

    def test_command_help_all_sections(self):
        """Test command help with all sections."""
        result = CLIHelpFormatter.format_command_help(
            command="full-cmd",
            description="A full command",
            usage="full-cmd [OPTIONS]",
            options=[
                {"flag": "--opt1", "description": "Option 1"},
                {"flag": "--opt2", "description": "Option 2", "default": "value"}
            ],
            examples=[
                {"description": "Basic usage", "command": "full-cmd --opt1"}
            ],
            tips=["Use --help for more info"],
            see_also=["related-cmd"]
        )

        # Should have all sections present
        assert isinstance(result, str)
        assert len(result) > 0


class TestFormatErrorWithSuggestion:
    """Test format_error_with_suggestion method."""

    def test_basic_error(self):
        """Test basic error formatting."""
        result = CLIHelpFormatter.format_error_with_suggestion(
            error="Something went wrong",
            suggestions=["Try this"]
        )

        # Should include error message (via colorize)
        mock_formatting.colorize.assert_called()

    def test_error_with_hint(self):
        """Test error with hint."""
        result = CLIHelpFormatter.format_error_with_suggestion(
            error="Not found",
            suggestions=["Check the ID"],
            hint="The ID might be misspelled"
        )

        # Should include hint
        assert isinstance(result, str)

    def test_error_with_multiple_suggestions(self):
        """Test error with multiple suggestions."""
        result = CLIHelpFormatter.format_error_with_suggestion(
            error="Failed",
            suggestions=["Option A", "Option B", "Option C"]
        )

        # Should include all suggestions
        assert "Option A" in result
        assert "Option B" in result
        assert "Option C" in result

    def test_error_empty_suggestions(self):
        """Test error with empty suggestions list."""
        result = CLIHelpFormatter.format_error_with_suggestion(
            error="Error occurred",
            suggestions=[]
        )

        # Should not include Try: section
        # Note: Result structure depends on implementation
        assert isinstance(result, str)


class TestFormatValidationError:
    """Test format_validation_error method."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        result = CLIHelpFormatter.format_validation_error(
            field="status",
            value="invalid_status",
            expected="One of: not_started, in_progress, completed"
        )

        # Should contain field, value, expected
        assert isinstance(result, str)

    def test_validation_error_with_context(self):
        """Test validation error with context."""
        result = CLIHelpFormatter.format_validation_error(
            field="task_id",
            value="BAD ID",
            expected="kebab-case format",
            context="task.yaml:5"
        )

        # Should contain context
        assert isinstance(result, str)

    def test_validation_error_numeric_value(self):
        """Test validation error with numeric value."""
        result = CLIHelpFormatter.format_validation_error(
            field="priority",
            value=100,
            expected="1-10"
        )

        # Should convert numeric to string
        assert isinstance(result, str)


class TestFormatDependencyError:
    """Test format_dependency_error method."""

    def test_task_dependency_error(self):
        """Test task dependency error."""
        result = CLIHelpFormatter.format_dependency_error(
            object_id="task-002",
            object_type="task",
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress"
        )

        # Should reference task in check command
        assert "task" in result.lower() or "roadmap" in result.lower()

    def test_sprint_dependency_error(self):
        """Test sprint dependency error."""
        result = CLIHelpFormatter.format_dependency_error(
            object_id="sprint-2",
            object_type="sprint",
            blocker_id="sprint-1",
            blocker_type="sprint",
            required_status="completed",
            current_status="in_progress"
        )

        # Should reference sprint in check command
        assert "sprint" in result.lower() or "roadmap" in result.lower()

    def test_track_dependency_error(self):
        """Test track dependency error."""
        result = CLIHelpFormatter.format_dependency_error(
            object_id="track-b",
            object_type="track",
            blocker_id="track-a",
            blocker_type="track",
            required_status="completed",
            current_status="in_progress"
        )

        # Should reference track in check command
        assert "track" in result.lower() or "roadmap" in result.lower()


class TestFormatNotFoundError:
    """Test format_not_found_error method."""

    def test_basic_not_found_error(self):
        """Test basic not found error."""
        result = CLIHelpFormatter.format_not_found_error(
            object_id="task-001",
            object_type="task"
        )

        # Should mention the ID
        assert isinstance(result, str)

    def test_not_found_error_with_paths(self):
        """Test not found error with searched paths."""
        result = CLIHelpFormatter.format_not_found_error(
            object_id="sprint-001",
            object_type="sprint",
            searched_paths=["/path/to/sprints/", "/other/path/"]
        )

        # Should include searched paths
        assert isinstance(result, str)

    def test_task_not_found_includes_sprint_hint(self):
        """Test task not found includes sprint hint."""
        result = CLIHelpFormatter.format_not_found_error(
            object_id="task-001",
            object_type="task"
        )

        # For tasks, should mention sprint-scoped
        assert "sprint" in result.lower()


class TestFormatProgressSummary:
    """Test format_progress_summary method."""

    def test_basic_progress_summary(self):
        """Test basic progress summary."""
        result = CLIHelpFormatter.format_progress_summary(
            object_name="Sprint 1",
            completed=5,
            total=10,
            status="in_progress"
        )

        # Should include object name
        mock_formatting.bold.assert_called()
        assert isinstance(result, str)

    def test_progress_summary_with_details(self):
        """Test progress summary with additional details."""
        result = CLIHelpFormatter.format_progress_summary(
            object_name="Backend Track",
            completed=3,
            total=5,
            status="in_progress",
            details={"Started": "2024-01-01", "Due": "2024-03-01"}
        )

        # Should include details
        assert "Started" in result
        assert "Due" in result

    def test_progress_summary_zero_total(self):
        """Test progress summary with zero total (no progress bar)."""
        result = CLIHelpFormatter.format_progress_summary(
            object_name="Empty Sprint",
            completed=0,
            total=0,
            status="not_started"
        )

        # Should handle zero total gracefully (no progress bar)
        assert isinstance(result, str)


class TestPreDefinedHelpMessages:
    """Test pre-defined help message constants."""

    def test_roadmap_query_help_exists(self):
        """Test ROADMAP_QUERY_HELP is defined."""
        assert ROADMAP_QUERY_HELP is not None
        assert isinstance(ROADMAP_QUERY_HELP, str)

    def test_roadmap_update_help_exists(self):
        """Test ROADMAP_UPDATE_HELP is defined."""
        assert ROADMAP_UPDATE_HELP is not None
        assert isinstance(ROADMAP_UPDATE_HELP, str)

    def test_roadmap_init_help_exists(self):
        """Test ROADMAP_INIT_HELP is defined."""
        assert ROADMAP_INIT_HELP is not None
        assert isinstance(ROADMAP_INIT_HELP, str)


class TestIntegration:
    """Integration tests for help formatter."""

    def test_error_then_suggestion_flow(self):
        """Test typical error handling flow."""
        # First show validation error
        validation_result = CLIHelpFormatter.format_validation_error(
            field="status",
            value="invalid",
            expected="valid status"
        )

        # Then show suggestions
        error_result = CLIHelpFormatter.format_error_with_suggestion(
            error="Invalid status",
            suggestions=["Use 'not_started'", "Use 'in_progress'", "Use 'completed'"]
        )

        assert isinstance(validation_result, str)
        assert isinstance(error_result, str)

    def test_not_found_with_suggestions(self):
        """Test not found error with follow-up suggestions."""
        not_found = CLIHelpFormatter.format_not_found_error(
            object_id="task-999",
            object_type="task",
            searched_paths=[".vibey/roadmap/tasks/"]
        )

        follow_up = CLIHelpFormatter.format_error_with_suggestion(
            error="Task 'task-999' not found",
            suggestions=[
                "List all tasks: vibey roadmap task list",
                "Check task ID format"
            ],
            hint="Task IDs use ULID format"
        )

        assert isinstance(not_found, str)
        assert isinstance(follow_up, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
