"""
Tests for session CLI commands.

Sprint 3.2 Task 8: Integration Testing
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from vibey.cli.main import cli
from vibey.roadmap.models.session import (
    Session,
    SessionStatus,
    SessionEvent,
    SessionEventType,
)
from datetime import datetime, timezone


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_roadmap():
    """Create a temporary roadmap directory."""
    temp_dir = Path(tempfile.mkdtemp())
    roadmap_path = temp_dir / ".vibey" / "roadmap"
    roadmap_path.mkdir(parents=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    now = datetime.now(timezone.utc)
    return Session(
        id="01KCTEST12345678901234567",
        name="Test Session",
        status=SessionStatus.ACTIVE,
        created=now,
        started=now,
        roadmap_id="test-roadmap",
        track_id="test-track",
        sprint_id="test-sprint",
        goals=["Goal 1", "Goal 2"],
        events=[
            SessionEvent(
                id="01KCEVENT123456789012345",
                session_id="01KCTEST12345678901234567",
                timestamp=now,
                event_type=SessionEventType.SESSION_START,
                data={"name": "Test Session"},
            ),
        ],
    )


class TestSessionStartCommand:
    """Tests for session start command."""

    def test_start_help(self, runner):
        """Test start command help."""
        result = runner.invoke(cli, ['session', 'start', '--help'])
        assert result.exit_code == 0
        assert 'Start a new' in result.output or 'name' in result.output.lower()

    @patch('vibey.cli.commands.session_start_cmd')
    def test_start_with_name(self, mock_cmd, runner):
        """Test starting session with name."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, ['session', 'start', 'My Session'])

        # Command should be called
        mock_cmd.assert_called_once()
        # Verify the name was passed (either as positional or keyword arg)
        call_args = mock_cmd.call_args
        name_passed = (
            (call_args.args and call_args.args[0] == 'My Session') or
            (call_args.kwargs.get('name') == 'My Session') or
            'My Session' in str(call_args)
        )
        assert name_passed

    @patch('vibey.cli.commands.session_start_cmd')
    def test_start_with_goals(self, mock_cmd, runner):
        """Test starting session with goals."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'start', 'My Session',
            '--goal', 'Goal 1',
            '--goal', 'Goal 2',
        ])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_start_cmd')
    def test_start_with_track(self, mock_cmd, runner):
        """Test starting session with track association."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'start', 'My Session',
            '--track', 'test-track',
        ])

        mock_cmd.assert_called_once()


class TestSessionEndCommand:
    """Tests for session end command."""

    def test_end_help(self, runner):
        """Test end command help."""
        result = runner.invoke(cli, ['session', 'end', '--help'])
        assert result.exit_code == 0
        assert 'End' in result.output or 'session' in result.output.lower()

    @patch('vibey.cli.commands.session_end_cmd')
    def test_end_default(self, mock_cmd, runner):
        """Test ending session with defaults."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, ['session', 'end'])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_end_cmd')
    def test_end_with_summary(self, mock_cmd, runner):
        """Test ending session with summary."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'end',
            '--summary', 'Completed all tasks',
        ])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_end_cmd')
    def test_end_as_abandoned(self, mock_cmd, runner):
        """Test ending session as abandoned."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'end',
            '--status', 'abandoned',
        ])

        mock_cmd.assert_called_once()


class TestSessionStatusCommand:
    """Tests for session status command."""

    def test_status_help(self, runner):
        """Test status command help."""
        result = runner.invoke(cli, ['session', 'status', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_status_cmd')
    def test_status(self, mock_cmd, runner):
        """Test getting session status."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, ['session', 'status'])

        mock_cmd.assert_called_once()


class TestSessionListCommand:
    """Tests for session list command."""

    def test_list_help(self, runner):
        """Test list command help."""
        result = runner.invoke(cli, ['session', 'list', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_list_cmd')
    def test_list_all(self, mock_cmd, runner):
        """Test listing all sessions."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, ['session', 'list'])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_list_cmd')
    def test_list_with_status_filter(self, mock_cmd, runner):
        """Test listing sessions with status filter."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'list',
            '--status', 'completed',
        ])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_list_cmd')
    def test_list_with_limit(self, mock_cmd, runner):
        """Test listing sessions with limit."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'list',
            '--limit', '5',
        ])

        mock_cmd.assert_called_once()


class TestSessionShowCommand:
    """Tests for session show command."""

    def test_show_help(self, runner):
        """Test show command help."""
        result = runner.invoke(cli, ['session', 'show', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_show_cmd')
    def test_show_session(self, mock_cmd, runner):
        """Test showing session details."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'show', '01KCTEST12345678901234567'
        ])

        mock_cmd.assert_called_once()


class TestSessionPauseCommand:
    """Tests for session pause command."""

    def test_pause_help(self, runner):
        """Test pause command help."""
        result = runner.invoke(cli, ['session', 'pause', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_pause_cmd')
    def test_pause(self, mock_cmd, runner):
        """Test pausing session."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, ['session', 'pause'])

        mock_cmd.assert_called_once()


class TestSessionResumeCommand:
    """Tests for session resume command."""

    def test_resume_help(self, runner):
        """Test resume command help."""
        result = runner.invoke(cli, ['session', 'resume', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_resume_cmd')
    def test_resume(self, mock_cmd, runner):
        """Test resuming session."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'resume', '01KCTEST12345678901234567'
        ])

        mock_cmd.assert_called_once()


class TestSessionReportCommand:
    """Tests for session report command."""

    def test_report_help(self, runner):
        """Test report command help."""
        result = runner.invoke(cli, ['session', 'report', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_report_cmd')
    def test_report(self, mock_cmd, runner):
        """Test generating session report."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'report', '01KCTEST12345678901234567'
        ])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_report_cmd')
    def test_report_text_format(self, mock_cmd, runner):
        """Test generating report in text format."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'report', '01KCTEST12345678901234567',
            '--format', 'text',
        ])

        mock_cmd.assert_called_once()


class TestSessionTimelineCommand:
    """Tests for session timeline command."""

    def test_timeline_help(self, runner):
        """Test timeline command help."""
        result = runner.invoke(cli, ['session', 'timeline', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_timeline_cmd')
    def test_timeline(self, mock_cmd, runner):
        """Test showing session timeline."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'timeline', '01KCTEST12345678901234567'
        ])

        mock_cmd.assert_called_once()


class TestSessionExportCommand:
    """Tests for session export command."""

    def test_export_help(self, runner):
        """Test export command help."""
        result = runner.invoke(cli, ['session', 'export', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_export_cmd')
    def test_export(self, mock_cmd, runner):
        """Test exporting session."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'export', '01KCTEST12345678901234567'
        ])

        mock_cmd.assert_called_once()

    @patch('vibey.cli.commands.session_export_cmd')
    def test_export_to_file(self, mock_cmd, runner):
        """Test exporting session to file."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'export', '01KCTEST12345678901234567',
            '--output', '/tmp/export.json',
        ])

        mock_cmd.assert_called_once()


class TestSessionDecisionsCommand:
    """Tests for session decisions command."""

    def test_decisions_help(self, runner):
        """Test decisions command help."""
        result = runner.invoke(cli, ['session', 'decisions', '--help'])
        assert result.exit_code == 0

    @patch('vibey.cli.commands.session_decisions_cmd')
    def test_decisions(self, mock_cmd, runner):
        """Test showing session decisions."""
        mock_cmd.return_value = 0

        result = runner.invoke(cli, [
            'session', 'decisions', '01KCTEST12345678901234567'
        ])

        mock_cmd.assert_called_once()


class TestSessionGroupExists:
    """Tests for session command group existence."""

    def test_session_group_exists(self, runner):
        """Test session command group is registered."""
        result = runner.invoke(cli, ['session', '--help'])
        assert result.exit_code == 0
        assert 'session' in result.output.lower() or 'commands' in result.output.lower()

    def test_subcommands_exist(self, runner):
        """Test all subcommands are available."""
        result = runner.invoke(cli, ['session', '--help'])
        assert result.exit_code == 0

        # Check for expected subcommands
        expected_commands = ['start', 'end', 'status', 'list', 'show', 'pause', 'resume']
        for cmd in expected_commands:
            assert cmd in result.output.lower(), f"Missing subcommand: {cmd}"


class TestErrorHandling:
    """Tests for CLI error handling."""

    @patch('vibey.cli.commands.session_start_cmd')
    def test_start_error_handling(self, mock_cmd, runner):
        """Test error handling in start command."""
        mock_cmd.return_value = 1  # Error exit code

        result = runner.invoke(cli, ['session', 'start', 'Test'])

        assert result.exit_code == 1

    @patch('vibey.cli.commands.session_end_cmd')
    def test_end_error_handling(self, mock_cmd, runner):
        """Test error handling in end command."""
        mock_cmd.return_value = 1

        result = runner.invoke(cli, ['session', 'end'])

        assert result.exit_code == 1

    @patch('vibey.cli.commands.session_show_cmd')
    def test_show_error_handling(self, mock_cmd, runner):
        """Test error handling in show command."""
        mock_cmd.return_value = 1

        result = runner.invoke(cli, ['session', 'show', 'invalid'])

        assert result.exit_code == 1
