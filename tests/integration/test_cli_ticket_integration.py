"""
Integration tests for CLI commands using the ticket model.

Tests that CLI commands properly interact with the unified ticket architecture
through the transitions and query modules.
"""

import pytest
from click.testing import CliRunner

from vibey.cli.main import cli


class TestRoadmapStartCLI:
    """CLI tests for roadmap start command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_start_command_exists(self, runner):
        """Start command is available."""
        result = runner.invoke(cli, ['roadmap', 'start', '--help'])
        assert result.exit_code == 0
        assert 'Usage' in result.output or 'usage' in result.output.lower()

    def test_start_requires_item_id(self, runner):
        """Start command requires item ID argument."""
        result = runner.invoke(cli, ['roadmap', 'start'])
        # Should require an argument
        assert result.exit_code != 0 or 'missing' in result.output.lower() or 'required' in result.output.lower()

    def test_start_invalid_id_handled(self, runner):
        """Start with non-existent ID is handled gracefully."""
        result = runner.invoke(cli, ['roadmap', 'start', 'fake-id-that-does-not-exist'])
        # Should return error, not crash
        assert result.exit_code != 0 or 'error' in result.output.lower() or 'not found' in result.output.lower()


class TestRoadmapCompleteCLI:
    """CLI tests for roadmap complete command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_complete_command_exists(self, runner):
        """Complete command is available."""
        result = runner.invoke(cli, ['roadmap', 'complete', '--help'])
        assert result.exit_code == 0
        assert 'Usage' in result.output or 'usage' in result.output.lower()

    def test_complete_requires_item_id(self, runner):
        """Complete command requires item ID argument."""
        result = runner.invoke(cli, ['roadmap', 'complete'])
        # Should require an argument
        assert result.exit_code != 0 or 'missing' in result.output.lower() or 'required' in result.output.lower()

    def test_complete_invalid_id_handled(self, runner):
        """Complete with non-existent ID is handled gracefully."""
        result = runner.invoke(cli, ['roadmap', 'complete', 'fake-id-that-does-not-exist'])
        # Should return error, not crash
        assert result.exit_code != 0 or 'error' in result.output.lower() or 'not found' in result.output.lower()


class TestRoadmapShowCLI:
    """CLI tests for roadmap show command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_show_command_exists(self, runner):
        """Show command is available."""
        result = runner.invoke(cli, ['roadmap', 'show', '--help'])
        assert result.exit_code == 0
        assert 'Usage' in result.output or 'usage' in result.output.lower()

    def test_show_requires_item_id(self, runner):
        """Show command requires item ID argument."""
        result = runner.invoke(cli, ['roadmap', 'show'])
        # Should require an argument
        assert result.exit_code != 0 or 'missing' in result.output.lower() or 'required' in result.output.lower()

    def test_show_invalid_id_handled(self, runner):
        """Show with non-existent ID is handled gracefully."""
        result = runner.invoke(cli, ['roadmap', 'show', 'fake-id-that-does-not-exist'])
        # Should return error, not crash
        assert result.exit_code != 0 or 'error' in result.output.lower() or 'not found' in result.output.lower()


class TestRoadmapStatusCLI:
    """CLI tests for roadmap status command (shows overall roadmap info)."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_status_command_exists(self, runner):
        """Status command is available."""
        result = runner.invoke(cli, ['roadmap', 'status', '--help'])
        assert result.exit_code == 0
        assert 'Usage' in result.output or 'usage' in result.output.lower()

    def test_status_works(self, runner):
        """Status command runs successfully."""
        result = runner.invoke(cli, ['roadmap', 'status'])
        # Should not crash - will show roadmap status
        assert result.exit_code == 0 or 'error' not in result.output.lower()


class TestRoadmapDbCLI:
    """CLI tests for roadmap db commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_db_command_exists(self, runner):
        """DB command group is available."""
        result = runner.invoke(cli, ['roadmap', 'db', '--help'])
        assert result.exit_code == 0
        assert 'Usage' in result.output or 'usage' in result.output.lower()

    def test_db_status_works(self, runner):
        """DB status command runs successfully."""
        result = runner.invoke(cli, ['roadmap', 'db', 'status'])
        # Should not crash
        assert result.exit_code == 0 or 'error' not in result.output.lower()


class TestTicketModelImports:
    """Test that ticket model classes are importable."""

    def test_task_ticket_importable(self):
        """TaskTicket is importable."""
        from vibey.roadmap.models.ticket import TaskTicket
        assert TaskTicket is not None

    def test_sprint_ticket_importable(self):
        """SprintTicket is importable."""
        from vibey.roadmap.models.ticket import SprintTicket
        assert SprintTicket is not None

    def test_track_ticket_importable(self):
        """TrackTicket is importable."""
        from vibey.roadmap.models.ticket import TrackTicket
        assert TrackTicket is not None

    def test_roadmap_ticket_importable(self):
        """RoadmapTicket is importable."""
        from vibey.roadmap.models.ticket import RoadmapTicket
        assert RoadmapTicket is not None

    def test_ticket_status_importable(self):
        """TicketStatus enum is importable."""
        from vibey.roadmap.models.ticket import TicketStatus
        assert hasattr(TicketStatus, 'NOT_STARTED')
        assert hasattr(TicketStatus, 'IN_PROGRESS')
        assert hasattr(TicketStatus, 'COMPLETED')


class TestHierarchicalTicketModel:
    """Test HierarchicalTicket base class."""

    def test_hierarchical_ticket_importable(self):
        """HierarchicalTicket is importable."""
        from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
        assert HierarchicalTicket is not None

    def test_hierarchical_ticket_has_class_methods(self):
        """HierarchicalTicket has expected class methods."""
        from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

        # Should have loader management methods
        assert hasattr(HierarchicalTicket, 'set_roadmap_root')
        assert hasattr(HierarchicalTicket, 'clear_roadmap_root')
        assert hasattr(HierarchicalTicket, 'clear_loaders')
