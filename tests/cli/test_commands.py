"""
Tests for vibey.cli.commands module.

Tests the command wrapper functions that bridge CLI to scripts.
"""

import pytest
from unittest.mock import patch, MagicMock

from vibey.cli.commands import (
    run_script,
    roadmap_start_cmd,
    roadmap_complete_cmd,
    roadmap_status_cmd,
    roadmap_show_cmd,
)


class TestRunScript:
    """Test the run_script helper function."""

    @patch('vibey.cli.commands.Path.exists')
    @patch('vibey.cli.commands.subprocess.run')
    def test_run_script_with_py_extension(self, mock_run, mock_exists):
        """Test running a script with .py extension."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        exit_code = run_script('test-script.py', ['arg1', 'arg2'])

        assert exit_code == 0
        assert mock_run.called

    @patch('vibey.cli.commands.Path.exists')
    @patch('vibey.cli.commands.subprocess.run')
    def test_run_script_without_py_extension(self, mock_run, mock_exists):
        """Test running a script without .py extension."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        exit_code = run_script('test-script', ['arg1'])

        assert exit_code == 0
        assert mock_run.called

    def test_run_script_not_found(self):
        """Test running a script that doesn't exist."""
        exit_code = run_script('nonexistent-script.py', [])

        assert exit_code == 1


class TestRoadmapCommands:
    """Test roadmap command wrappers."""

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_start_task(self, mock_run):
        """Test starting a task."""
        mock_run.return_value = 0

        exit_code = roadmap_start_cmd('directory-migration-1-task-001')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-update.py',
            ['--start-task', 'directory-migration-1-task-001']
        )

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_start_sprint(self, mock_run):
        """Test starting a sprint."""
        mock_run.return_value = 0

        exit_code = roadmap_start_cmd('directory-migration-1')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-update.py',
            ['--start-sprint', 'directory-migration-1']
        )

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_complete_task(self, mock_run):
        """Test completing a task."""
        mock_run.return_value = 0

        exit_code = roadmap_complete_cmd('directory-migration-1-task-001')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-update.py',
            ['--complete-task', 'directory-migration-1-task-001']
        )

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_status_no_filters(self, mock_run):
        """Test roadmap status without filters."""
        mock_run.return_value = 0

        exit_code = roadmap_status_cmd()

        assert exit_code == 0
        mock_run.assert_called_once_with('roadmap-query.py', [])

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_status_with_track(self, mock_run):
        """Test roadmap status with track filter."""
        mock_run.return_value = 0

        exit_code = roadmap_status_cmd(track='directory-migration')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-query.py',
            ['--track', 'directory-migration']
        )

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_show_task(self, mock_run):
        """Test showing task details."""
        mock_run.return_value = 0

        exit_code = roadmap_show_cmd('directory-migration-1-task-001')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-query.py',
            ['--task', 'directory-migration-1-task-001']
        )

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_show_sprint(self, mock_run):
        """Test showing sprint details."""
        mock_run.return_value = 0

        exit_code = roadmap_show_cmd('directory-migration-1')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-query.py',
            ['--sprint', 'directory-migration-1']
        )

    @patch('vibey.cli.commands.run_script')
    def test_roadmap_show_track(self, mock_run):
        """Test showing track details."""
        mock_run.return_value = 0

        exit_code = roadmap_show_cmd('directory-migration')

        assert exit_code == 0
        mock_run.assert_called_once_with(
            'roadmap-query.py',
            ['--track', 'directory-migration']
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
