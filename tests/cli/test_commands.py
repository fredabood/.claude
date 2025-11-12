"""
Tests for vibey.cli.commands module.

Tests the command wrapper functions that bridge CLI to operations modules.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from vibey.cli.commands import (
    roadmap_start_cmd,
    roadmap_complete_cmd,
    roadmap_status_cmd,
    roadmap_show_cmd,
    roadmap_init_cmd,
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
