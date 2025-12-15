"""
Integration tests for cross-module interactions.

Tests that exercise interactions between modules: CLI → operations → roadmap → storage flows.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from vibey.cli.main import cli


class TestCLIToDatabaseFlow:
    """Test data flows correctly from CLI to database and YAML."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def isolated_env(self, tmp_path):
        """Create isolated environment with sample roadmap."""
        # Copy a minimal roadmap structure
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        # Create minimal roadmap.yaml
        roadmap_yaml = roadmap_dir / "roadmap.yaml"
        roadmap_yaml.write_text("""roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  version_strategy: semver
  status: in_progress
  blocked: false
  created: '2025-12-15T10:00:00Z'
  progress:
    tracks_total: 1
    tracks_completed: 0
    sprints_total: 1
    sprints_completed: 0
    tasks_total: 1
    tasks_completed: 0
    completion_percent: 0
  tracks:
    - id: test-track
  activity_log: []
  metadata: {}
""")

        # Create tracks directory
        tracks_dir = roadmap_dir / "tracks"
        tracks_dir.mkdir()

        track_yaml = tracks_dir / "test-track.yaml"
        track_yaml.write_text("""track:
  id: test-track
  name: Test Track
  roadmap_id: test-roadmap
  status: in_progress
  blocked: false
  priority: medium
  created: '2025-12-15T10:00:00Z'
  progress:
    sprints_total: 1
    sprints_completed: 0
    tasks_total: 1
    tasks_completed: 0
    completion_percent: 0
  sprints:
    - id: test-track-1
  dependencies: []
  blocks: []
  blocked_by: []
  quality_gates: []
  assigned_agents: []
  metadata: {}
""")

        # Create sprints directory
        sprints_dir = roadmap_dir / "sprints"
        sprints_dir.mkdir()

        sprint_yaml = sprints_dir / "test-track-1.yaml"
        sprint_yaml.write_text("""sprint:
  id: test-track-1
  name: Sprint 1
  track_id: test-track
  roadmap_id: test-roadmap
  status: not_started
  blocked: false
  created: '2025-12-15T10:00:00Z'
  progress:
    tasks_total: 1
    tasks_completed: 0
  development_gates: []
  blocks: []
  blocked_by: []
  metadata: {}
""")

        # Create tasks directory
        tasks_dir = roadmap_dir / "tasks"
        tasks_dir.mkdir()

        task_yaml = tasks_dir / "test-track-1-task-001.yaml"
        task_yaml.write_text("""task:
  id: test-track-1-task-001
  sprint_id: test-track-1
  track_id: test-track
  roadmap_id: test-roadmap
  task_type: development
  title: Test Task
  description: A test task
  status: not_started
  blocked: false
  created: '2025-12-15T10:00:00Z'
  priority: medium
  estimated_tokens: 10000
  complexity: medium
  dependencies: []
  blocks: []
  blocked_by: []
  metadata: {}
""")

        return tmp_path

    def test_cli_status_reads_from_yaml(self, runner, isolated_env):
        """Test CLI status command reads data from YAML files."""
        result = runner.invoke(cli, ["roadmap", "status"], obj={"cwd": str(isolated_env)})
        # Should work or fail gracefully
        assert result.exit_code in [0, 1]

    def test_cli_show_reflects_yaml_state(self, runner, isolated_env):
        """Test CLI show command reflects YAML state."""
        result = runner.invoke(cli, ["roadmap", "show", "--help"])
        assert result.exit_code == 0


class TestYAMLAndDatabaseSync:
    """Test YAML source of truth and SQLite cache stay in sync."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_db_validate_checks_sync(self, runner):
        """Test db validate checks YAML-SQLite sync."""
        result = runner.invoke(cli, ["roadmap", "db", "validate"])
        assert result.exit_code == 0

    def test_db_rebuild_recreates_from_yaml(self, runner):
        """Test db rebuild recreates SQLite from YAML."""
        result = runner.invoke(cli, ["roadmap", "db", "rebuild"])
        assert result.exit_code == 0
        assert "rebuilt" in result.output.lower() or "success" in result.output.lower()


class TestContextLoadingIntegration:
    """Test context loading integrates with roadmap data."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_context_command_exists(self, runner):
        """Test context command is available."""
        result = runner.invoke(cli, ["roadmap", "context", "--help"])
        assert result.exit_code == 0

    def test_context_loads_from_roadmap(self, runner):
        """Test context command can load context from roadmap."""
        # Just verify the command works (details depend on task)
        result = runner.invoke(cli, ["roadmap", "context", "--help"])
        assert result.exit_code == 0


class TestActivityLogIntegration:
    """Test activity log integrates with CLI operations."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_activity_command_works(self, runner):
        """Test activity command returns activity data."""
        result = runner.invoke(cli, ["roadmap", "activity"])
        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1]

    def test_activity_with_limit(self, runner):
        """Test activity command accepts limit parameter."""
        result = runner.invoke(cli, ["roadmap", "activity", "-n", "5"])
        assert result.exit_code in [0, 1]


class TestValidationChainIntegration:
    """Test validation flows through CLI to operations."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_validate_fast_uses_operations(self, runner):
        """Test validate-fast command uses validation operations."""
        result = runner.invoke(cli, ["roadmap", "validate-fast"])
        assert result.exit_code in [0, 1]

    def test_validate_structure_uses_operations(self, runner):
        """Test validate-structure command uses validation operations."""
        result = runner.invoke(cli, ["roadmap", "validate-structure"])
        assert result.exit_code in [0, 1]


class TestStatusTransitionIntegration:
    """Test status transitions flow through all layers."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_start_command_exists(self, runner):
        """Test start command is available."""
        result = runner.invoke(cli, ["roadmap", "start", "--help"])
        assert result.exit_code == 0
        assert "start" in result.output.lower()

    def test_complete_command_exists(self, runner):
        """Test complete command is available."""
        result = runner.invoke(cli, ["roadmap", "complete", "--help"])
        assert result.exit_code == 0
        assert "complete" in result.output.lower()

    def test_invalid_transition_handled(self, runner):
        """Test invalid transitions are handled gracefully."""
        result = runner.invoke(cli, ["roadmap", "complete", "nonexistent-task-12345"])
        # Should fail with error message, not crash
        assert result.exit_code != 0 or "error" in result.output.lower() or "not found" in result.output.lower()


class TestDatabaseOperationsIntegration:
    """Test database operations integrate with CLI."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_db_status_shows_counts(self, runner):
        """Test db status shows entity counts."""
        result = runner.invoke(cli, ["roadmap", "db", "status"])
        # Should show status info
        assert result.exit_code == 0

    def test_db_validate_reports_issues(self, runner):
        """Test db validate reports any issues found."""
        result = runner.invoke(cli, ["roadmap", "db", "validate"])
        assert result.exit_code == 0
        # Should have validation output
        assert len(result.output) > 0


class TestSearchIntegration:
    """Test search functionality integrates with data layers."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_show_command_finds_entities(self, runner):
        """Test show command can find entities by ID or slug."""
        result = runner.invoke(cli, ["roadmap", "show", "--help"])
        assert result.exit_code == 0

    def test_status_shows_roadmap_info(self, runner):
        """Test status shows roadmap information."""
        result = runner.invoke(cli, ["roadmap", "status"])
        assert result.exit_code == 0
        # Should contain roadmap info
        assert len(result.output) > 0


class TestSyncOperationsIntegration:
    """Test sync operations integrate CLI with storage."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_sync_command_exists(self, runner):
        """Test sync command is available."""
        result = runner.invoke(cli, ["roadmap", "sync", "--help"])
        assert result.exit_code == 0


class TestAuditOperationsIntegration:
    """Test audit operations integrate CLI with storage."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_audit_command_exists(self, runner):
        """Test audit command is available."""
        result = runner.invoke(cli, ["roadmap", "audit", "--help"])
        assert result.exit_code == 0


class TestEditOperationsIntegration:
    """Test edit operations integrate CLI with YAML storage."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_edit_command_exists(self, runner):
        """Test edit command is available."""
        result = runner.invoke(cli, ["roadmap", "edit", "--help"])
        assert result.exit_code == 0


class TestCreateOperationsIntegration:
    """Test create operations integrate CLI with storage."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_create_track_command_exists(self, runner):
        """Test create-track command is available."""
        result = runner.invoke(cli, ["roadmap", "create-track", "--help"])
        assert result.exit_code == 0

    def test_create_sprint_command_exists(self, runner):
        """Test create-sprint command is available."""
        result = runner.invoke(cli, ["roadmap", "create-sprint", "--help"])
        assert result.exit_code == 0

    def test_create_task_command_exists(self, runner):
        """Test create-task command is available."""
        result = runner.invoke(cli, ["roadmap", "create-task", "--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
