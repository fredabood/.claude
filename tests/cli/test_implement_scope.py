"""
Tests for explicit scope requirements in implementation mode.

Sprint 12, Task 08: Add tests for explicit scope requirements
Track: Implementation Mode (Autonomous Execution)

Tests cover:
1. Bare command shows help (no execution without explicit scope)
2. --all-tickets enables full execution
3. --ticket filters correctly by hierarchy
4. Completion detection works for parent tickets
5. Deprecated options still work with warnings
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from vibey.cli.implement import implement


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


class TestBareCommandShowsHelp:
    """Test that bare command shows help instead of executing."""

    def test_bare_command_shows_scope_required_help(self, cli_runner):
        """Bare 'vibey implement' should show help about scope requirements."""
        result = cli_runner.invoke(implement, [])

        # Should exit cleanly (not error)
        assert result.exit_code == 0

        # Should show scope requirement message
        assert "SCOPE OPTIONS" in result.output or "scope" in result.output.lower()

    def test_bare_command_does_not_execute(self, cli_runner):
        """Bare command should not start execution."""
        with patch('vibey.cli.implement.run_implementation_cmd') as mock_run:
            result = cli_runner.invoke(implement, [])

            # run_implementation_cmd should NOT be called
            mock_run.assert_not_called()


class TestAllTicketsFlag:
    """Test --all-tickets flag for full roadmap execution."""

    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_all_tickets_triggers_execution(self, mock_run, cli_runner):
        """--all-tickets should trigger execution with confirmation."""
        mock_run.return_value = 0

        result = cli_runner.invoke(implement, ['--all-tickets', '--yes'])

        # Should call run_implementation_cmd with all_tickets=True
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('all_tickets') is True

    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_all_tickets_passes_scope_ulid_none(self, mock_run, cli_runner):
        """--all-tickets should pass scope_ulid=None (full roadmap)."""
        mock_run.return_value = 0

        result = cli_runner.invoke(implement, ['--all-tickets', '--yes'])

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('scope_ulid') is None


class TestTicketFilter:
    """Test --ticket filters correctly by hierarchy."""

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_ticket_passes_ulid(self, mock_run, mock_service_class, cli_runner):
        """--ticket should pass the ULID to execution."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Ticket"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        test_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        result = cli_runner.invoke(implement, ['--ticket', test_ulid, '--yes'])

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('scope_ulid') == test_ulid

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_ticket_validates_ulid_exists(self, mock_run, mock_service_class, cli_runner):
        """--ticket should validate that the ULID exists."""
        from vibey.services.ticket_service import TicketNotFoundError

        mock_service = MagicMock()
        mock_service.get_ticket.side_effect = TicketNotFoundError("Not found")
        mock_service_class.return_value = mock_service

        result = cli_runner.invoke(implement, ['--ticket', 'INVALID_ULID', '--yes'])

        # Should exit with error
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestDeprecatedOptionsWithWarnings:
    """Test deprecated --track and --sprint options still work with warnings."""

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_track_shows_deprecation_warning(self, mock_run, mock_service_class, cli_runner):
        """--track should show deprecation warning."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Track"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        test_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        result = cli_runner.invoke(implement, ['--track', test_ulid, '--yes'])

        # Should show deprecation warning
        assert "deprecated" in result.output.lower()
        assert "--ticket" in result.output

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_sprint_shows_deprecation_warning(self, mock_run, mock_service_class, cli_runner):
        """--sprint should show deprecation warning."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Sprint"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        test_ulid = "01KC2D0JKVT80AFQ6C1PA8CKJD"
        result = cli_runner.invoke(implement, ['--sprint', test_ulid, '--yes'])

        # Should show deprecation warning
        assert "deprecated" in result.output.lower()
        assert "--ticket" in result.output

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_deprecated_track_still_works(self, mock_run, mock_service_class, cli_runner):
        """--track should still work for backward compatibility."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Track"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        test_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        result = cli_runner.invoke(implement, ['--track', test_ulid, '--yes'])

        # Should still call run_implementation_cmd with the ULID
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('scope_ulid') == test_ulid

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_deprecated_sprint_still_works(self, mock_run, mock_service_class, cli_runner):
        """--sprint should still work for backward compatibility."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Sprint"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        test_ulid = "01KC2D0JKVT80AFQ6C1PA8CKJD"
        result = cli_runner.invoke(implement, ['--sprint', test_ulid, '--yes'])

        # Should still call run_implementation_cmd with the ULID
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('scope_ulid') == test_ulid


class TestCompletionDetection:
    """Test completion detection for parent tickets."""

    def test_scope_completion_checker_import(self):
        """ScopeCompletionChecker should be importable."""
        from vibey.services.implementation.completion import ScopeCompletionChecker

        checker = ScopeCompletionChecker()
        assert checker is not None

    def test_load_scope_ticket_import(self):
        """load_scope_ticket should be importable."""
        from vibey.services.implementation.completion import load_scope_ticket

        assert callable(load_scope_ticket)

    def test_check_scope_complete_import(self):
        """check_scope_complete should be importable."""
        from vibey.services.implementation.completion import check_scope_complete

        assert callable(check_scope_complete)

    def test_scope_completion_checker_methods(self):
        """ScopeCompletionChecker should have required methods."""
        from vibey.services.implementation.completion import ScopeCompletionChecker

        checker = ScopeCompletionChecker()

        assert hasattr(checker, 'check_scope_completion')
        assert hasattr(checker, 'get_completion_progress')
        assert hasattr(checker, 'is_scope_complete')


class TestTicketPrecedence:
    """Test that --ticket takes precedence over deprecated options."""

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_ticket_overrides_track(self, mock_run, mock_service_class, cli_runner):
        """--ticket should take precedence over --track."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Ticket"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        ticket_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        track_ulid = "01KC2D0JKVT80AFQ6C1PA8CKJD"

        result = cli_runner.invoke(implement, [
            '--ticket', ticket_ulid,
            '--track', track_ulid,
            '--yes'
        ])

        # Should use --ticket value, not --track
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('scope_ulid') == ticket_ulid

    @patch('vibey.services.ticket_service.TicketService')
    @patch('vibey.cli.implement.run_implementation_cmd')
    def test_ticket_overrides_sprint(self, mock_run, mock_service_class, cli_runner):
        """--ticket should take precedence over --sprint."""
        mock_run.return_value = 0
        mock_service = MagicMock()
        mock_ticket = MagicMock()
        mock_ticket.name = "Test Ticket"
        mock_service.get_ticket.return_value = mock_ticket
        mock_service_class.return_value = mock_service

        ticket_ulid = "01KC2D0JK9JKQXGQW6MQEB0JZP"
        sprint_ulid = "01KC2D0JKVT80AFQ6C1PA8CKJD"

        result = cli_runner.invoke(implement, [
            '--ticket', ticket_ulid,
            '--sprint', sprint_ulid,
            '--yes'
        ])

        # Should use --ticket value, not --sprint
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get('scope_ulid') == ticket_ulid
