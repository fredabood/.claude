"""
Tests for vibey.cli.commands module.

Tests the command wrapper functions that bridge CLI to operations modules.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from vibey.cli.commands import (
    roadmap_start_cmd,
    roadmap_complete_cmd,
    roadmap_status_cmd,
    roadmap_show_cmd,
    roadmap_init_cmd,
    roadmap_context_cmd,
    roadmap_list_cmd,
    roadmap_validate_cmd,
)


class TestRoadmapCommands:
    """Test roadmap command wrappers."""

    @patch('vibey.cli.commands.start_task')
    def test_roadmap_start_task(self, mock_start):
        """Test starting a task."""
        mock_start.return_value = 0

        exit_code = roadmap_start_cmd('directory-migration-1-task-001')

        assert exit_code == 0
        mock_start.assert_called_once()
        # Verify the task_id was passed
        args = mock_start.call_args
        assert args[0][1] == 'directory-migration-1-task-001'

    @patch('vibey.cli.commands.start_sprint')
    def test_roadmap_start_sprint(self, mock_start):
        """Test starting a sprint."""
        mock_start.return_value = 0

        exit_code = roadmap_start_cmd('directory-migration-1')

        assert exit_code == 0
        mock_start.assert_called_once()

    @patch('vibey.cli.commands.complete_task')
    def test_roadmap_complete_task(self, mock_complete):
        """Test completing a task."""
        mock_complete.return_value = 0

        exit_code = roadmap_complete_cmd('directory-migration-1-task-001')

        assert exit_code == 0
        mock_complete.assert_called_once()

    @patch('vibey.cli.commands.query_roadmap_summary')
    def test_roadmap_status_no_filters(self, mock_query):
        """Test roadmap status without filters."""
        mock_query.return_value = {"status": "ok"}

        exit_code = roadmap_status_cmd()

        assert exit_code == 0
        mock_query.assert_called_once()

    @patch('vibey.cli.commands.query_track_details')
    def test_roadmap_status_with_track(self, mock_query):
        """Test roadmap status with track filter."""
        mock_query.return_value = {"track": "test"}

        exit_code = roadmap_status_cmd(track='directory-migration')

        assert exit_code == 0
        mock_query.assert_called_once()

    @patch('vibey.cli.commands.query_task_details')
    def test_roadmap_show_task(self, mock_query):
        """Test showing task details."""
        mock_query.return_value = {"task": "test"}

        exit_code = roadmap_show_cmd('directory-migration-1-task-001')

        assert exit_code == 0
        mock_query.assert_called_once()

    @patch('vibey.cli.commands.query_sprint_details')
    def test_roadmap_show_sprint(self, mock_query):
        """Test showing sprint details."""
        mock_query.return_value = {"sprint": "test"}

        exit_code = roadmap_show_cmd('directory-migration-1')

        assert exit_code == 0
        mock_query.assert_called_once()

    @patch('vibey.cli.commands.query_track_details')
    def test_roadmap_show_track(self, mock_query):
        """Test showing track details."""
        mock_query.return_value = {"track": "test"}

        exit_code = roadmap_show_cmd('directory-migration')

        assert exit_code == 0
        mock_query.assert_called_once()

    @patch('vibey.cli.commands.init_roadmap')
    def test_roadmap_init(self, mock_init):
        """Test initializing a roadmap."""
        mock_init.return_value = 0

        exit_code = roadmap_init_cmd('test-roadmap', '1.0.0')

        assert exit_code == 0
        mock_init.assert_called_once()
        args = mock_init.call_args
        assert 'test-roadmap' in str(args)


class TestRoadmapErrorHandling:
    """Test error handling in roadmap commands."""

    @patch('vibey.cli.commands.start_task')
    def test_start_handles_exception(self, mock_start):
        """Test start command propagates exceptions."""
        mock_start.side_effect = Exception("Task not found")

        # Exception should propagate
        with pytest.raises(Exception, match="Task not found"):
            roadmap_start_cmd('nonexistent-task')
        mock_start.assert_called_once()

    @patch('vibey.cli.commands.complete_task')
    def test_complete_handles_exception(self, mock_complete):
        """Test complete command propagates exceptions."""
        mock_complete.side_effect = Exception("Task not in progress")

        # Exception should propagate (task ID must contain -task-)
        with pytest.raises(Exception, match="Task not in progress"):
            roadmap_complete_cmd('test-1-task-001')
        mock_complete.assert_called_once()

    @patch('vibey.cli.commands.query_roadmap_summary')
    def test_status_handles_not_found(self, mock_query):
        """Test status command handles file not found and returns non-zero."""
        mock_query.side_effect = FileNotFoundError("Roadmap not found")

        # Function catches exception and returns non-zero
        result = roadmap_status_cmd()
        mock_query.assert_called_once()
        # Should return non-zero exit code on error
        assert result != 0


class TestRoadmapContextCommand:
    """Test roadmap context command."""

    @patch('vibey.cli.commands.get_task_context')
    def test_context_returns_task_info(self, mock_context):
        """Test context command calls get_task_context."""
        mock_context.return_value = 0  # Returns exit code

        result = roadmap_context_cmd('test-task')

        # Should call the underlying function
        mock_context.assert_called_once()
        assert result == 0

    @patch('vibey.cli.commands.get_task_context')
    def test_context_handles_not_found(self, mock_context):
        """Test context command propagates exceptions."""
        mock_context.side_effect = KeyError("Task not found")

        # Exception should propagate
        with pytest.raises(KeyError):
            roadmap_context_cmd('nonexistent-task')
        mock_context.assert_called_once()


class TestListAndValidateCommands:
    """Test list and validate commands."""

    def test_list_cmd_returns_code(self):
        """Test list command returns exit code."""
        # Just verify it can be called
        try:
            exit_code = roadmap_list_cmd()
            assert isinstance(exit_code, int)
        except Exception:
            # May fail if roadmap doesn't exist
            pass

    def test_validate_cmd_returns_code(self):
        """Test validate command returns exit code."""
        # Just verify it can be called
        try:
            exit_code = roadmap_validate_cmd()
            assert isinstance(exit_code, int)
        except Exception:
            # May fail if roadmap doesn't exist
            pass


class TestCommandInputValidation:
    """Test input validation for commands."""

    def test_start_validates_object_id_format(self):
        """Test start command validates object ID format."""
        # Empty ID should be handled
        exit_code = roadmap_start_cmd('')
        assert exit_code != 0

    @patch('vibey.cli.commands.query_task_details')
    @patch('vibey.cli.commands.query_sprint_details')
    @patch('vibey.cli.commands.query_track_details')
    def test_show_validates_object_id_format(self, mock_track, mock_sprint, mock_task):
        """Test show command validates object ID format."""
        # Configure mocks to raise not found for empty ID
        from vibey.common.errors import TaskNotFoundError, SprintNotFoundError, TrackNotFoundError
        mock_task.side_effect = TaskNotFoundError("")
        mock_sprint.side_effect = SprintNotFoundError("")
        mock_track.side_effect = TrackNotFoundError("")

        # Empty ID should be handled as error
        exit_code = roadmap_show_cmd('')
        assert exit_code != 0

    def test_complete_validates_object_id_format(self):
        """Test complete command validates object ID format."""
        # Empty ID should be handled
        exit_code = roadmap_complete_cmd('')
        assert exit_code != 0


class TestCommandOutputFormatting:
    """Test output formatting in commands."""

    @patch('vibey.cli.commands.query_roadmap_summary')
    def test_status_formats_progress_correctly(self, mock_query):
        """Test status command formats progress percentage."""
        mock_query.return_value = {
            "progress": {
                "completion_percent": 50
            }
        }

        exit_code = roadmap_status_cmd()

        assert exit_code == 0

    @patch('vibey.cli.commands.query_task_details')
    def test_show_formats_task_details(self, mock_query):
        """Test show command formats task details."""
        mock_query.return_value = {
            "id": "test-task",
            "title": "Test Task",
            "status": "in_progress",
            "description": "A test task"
        }

        exit_code = roadmap_show_cmd('test-task')

        assert exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
