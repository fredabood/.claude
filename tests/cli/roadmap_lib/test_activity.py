"""
Tests for vibey.cli.roadmap_lib.activity module.

Tests activity logging utilities for roadmap state.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from vibey.roadmap.models import ActivityType
from vibey.cli.roadmap_lib.activity import (
    ActivityLogger,
    log_activity,
)


class TestActivityLoggerInit:
    """Test ActivityLogger initialization."""

    @patch('vibey.cli.roadmap_lib.activity.FileSystemManager')
    def test_init_default_root(self, mock_fs):
        """Test initialization with default root."""
        logger = ActivityLogger()

        mock_fs.assert_called_once_with(None)

    @patch('vibey.cli.roadmap_lib.activity.FileSystemManager')
    def test_init_custom_root(self, mock_fs):
        """Test initialization with custom root."""
        custom_path = Path("/custom/path")
        logger = ActivityLogger(root_dir=custom_path)

        mock_fs.assert_called_once_with(custom_path)


class TestLogActivity:
    """Test activity logging."""

    @pytest.fixture
    def logger(self):
        """Create ActivityLogger with mocked filesystem."""
        with patch('vibey.cli.roadmap_lib.activity.FileSystemManager') as mock_fs:
            mock_fs_instance = MagicMock()
            mock_fs.return_value = mock_fs_instance
            lgr = ActivityLogger()
            lgr.fs = mock_fs_instance
            return lgr

    def test_log_activity_roadmap_not_found(self, logger):
        """Test logging when roadmap doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        logger.fs.get_roadmap_path.return_value = mock_path

        result = logger.log_activity(
            ActivityType.TASK_COMPLETED,
            "Test description"
        )

        assert result is False

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_activity_success(self, mock_save, mock_load, logger):
        """Test successful activity logging."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        result = logger.log_activity(
            ActivityType.TASK_COMPLETED,
            "Task completed"
        )

        assert result is True
        mock_roadmap.add_activity.assert_called_once()
        mock_save.assert_called_once()

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_activity_with_context(self, mock_save, mock_load, logger):
        """Test logging with context dictionary."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        context = {"task_id": "task-001", "old_status": "pending", "new_status": "completed"}

        result = logger.log_activity(
            ActivityType.TASK_COMPLETED,
            "Task completed",
            context
        )

        assert result is True
        call_args = mock_roadmap.add_activity.call_args
        assert call_args[0][0] == ActivityType.TASK_COMPLETED
        assert call_args[0][1] == "Task completed"
        assert call_args[0][2] == context

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    def test_log_activity_load_error(self, mock_load, logger):
        """Test logging when load fails."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_load.side_effect = Exception("Load failed")

        result = logger.log_activity(
            ActivityType.TASK_COMPLETED,
            "Test description"
        )

        assert result is False

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_activity_save_error(self, mock_save, mock_load, logger):
        """Test logging when save fails."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap
        mock_save.side_effect = Exception("Save failed")

        result = logger.log_activity(
            ActivityType.TASK_COMPLETED,
            "Test description"
        )

        assert result is False


class TestLogActivityFunction:
    """Test module-level convenience function."""

    @patch('vibey.cli.roadmap_lib.activity.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_activity_function_success(self, mock_save, mock_load, mock_fs):
        """Test log_activity convenience function."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        result = log_activity(
            ActivityType.TASK_STARTED,
            "New task created"
        )

        assert result is True

    @patch('vibey.cli.roadmap_lib.activity.FileSystemManager')
    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_activity_function_with_root_dir(self, mock_save, mock_load, mock_fs):
        """Test log_activity with custom root_dir."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        custom_root = Path("/custom/root")
        result = log_activity(
            ActivityType.SPRINT_STARTED,
            "Sprint started",
            root_dir=custom_root
        )

        mock_fs.assert_called_with(custom_root)

    @patch('vibey.cli.roadmap_lib.activity.FileSystemManager')
    def test_log_activity_function_roadmap_not_found(self, mock_fs):
        """Test log_activity when roadmap not found."""
        mock_fs_instance = MagicMock()
        mock_fs.return_value = mock_fs_instance

        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_fs_instance.get_roadmap_path.return_value = mock_path

        result = log_activity(
            ActivityType.TASK_COMPLETED,
            "Test"
        )

        assert result is False


class TestActivityTypes:
    """Test with various activity types."""

    @pytest.fixture
    def logger(self):
        """Create ActivityLogger with mocked filesystem."""
        with patch('vibey.cli.roadmap_lib.activity.FileSystemManager') as mock_fs:
            mock_fs_instance = MagicMock()
            mock_fs.return_value = mock_fs_instance
            lgr = ActivityLogger()
            lgr.fs = mock_fs_instance
            return lgr

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_task_created(self, mock_save, mock_load, logger):
        """Test logging task created activity."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        result = logger.log_activity(
            ActivityType.TASK_STARTED,
            "Created task task-001",
            {"task_id": "task-001"}
        )

        assert result is True
        call_args = mock_roadmap.add_activity.call_args
        assert call_args[0][0] == ActivityType.TASK_STARTED

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_sprint_started(self, mock_save, mock_load, logger):
        """Test logging sprint started activity."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        result = logger.log_activity(
            ActivityType.SPRINT_STARTED,
            "Started sprint sprint-1",
            {"sprint_id": "sprint-1"}
        )

        assert result is True
        call_args = mock_roadmap.add_activity.call_args
        assert call_args[0][0] == ActivityType.SPRINT_STARTED

    @patch('vibey.cli.roadmap_lib.activity.load_roadmap')
    @patch('vibey.cli.roadmap_lib.activity.save_roadmap')
    def test_log_status_changed(self, mock_save, mock_load, logger):
        """Test logging status changed activity."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        logger.fs.get_roadmap_path.return_value = mock_path

        mock_roadmap = MagicMock()
        mock_load.return_value = mock_roadmap

        result = logger.log_activity(
            ActivityType.TASK_COMPLETED,
            "Task status changed",
            {"old_status": "pending", "new_status": "completed"}
        )

        assert result is True
        call_args = mock_roadmap.add_activity.call_args
        assert call_args[0][0] == ActivityType.TASK_COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
