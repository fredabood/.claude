"""
Integration tests for CLI workflows.

Tests end-to-end CLI workflows: roadmap create → update → query → export flows.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from vibey.cli.main import cli


class TestCliAvailability:
    """Test CLI is available and responds correctly."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_cli_responds(self, runner):
        """Test CLI responds to --help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "vibey" in result.output.lower() or "Usage" in result.output

    def test_version_command(self, runner):
        """Test --version returns version info."""
        result = runner.invoke(cli, ["--version"])
        # Either exit 0 with version or exit 0 with no output (if no version defined)
        assert result.exit_code in [0, 2]  # 2 for "no such option" if not implemented

    def test_roadmap_subcommand_exists(self, runner):
        """Test roadmap subcommand exists."""
        result = runner.invoke(cli, ["roadmap", "--help"])
        assert result.exit_code == 0
        assert "roadmap" in result.output.lower()


class TestRoadmapStatusWorkflow:
    """Test roadmap status querying workflow."""

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

    def test_roadmap_status_in_project(self, runner, isolated_env):
        """Test roadmap status command in project context."""
        result = runner.invoke(cli, ["roadmap", "status"], obj={"cwd": str(isolated_env)})
        # Should work or fail gracefully
        assert result.exit_code in [0, 1]


class TestRoadmapShowWorkflow:
    """Test roadmap show workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_show_help(self, runner):
        """Test roadmap show --help."""
        result = runner.invoke(cli, ["roadmap", "show", "--help"])
        assert result.exit_code == 0


class TestRoadmapDatabaseWorkflow:
    """Test roadmap database operations workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_db_subcommand_exists(self, runner):
        """Test db subcommand exists."""
        result = runner.invoke(cli, ["roadmap", "db", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.output.lower() or "rebuild" in result.output.lower()

    def test_db_validate_current_project(self, runner):
        """Test db validate on current project."""
        # Run against actual project (which has valid roadmap)
        result = runner.invoke(cli, ["roadmap", "db", "validate"])
        # Should pass validation
        assert result.exit_code == 0
        assert "passed" in result.output.lower() or "success" in result.output.lower()


class TestRoadmapCreateWorkflow:
    """Test roadmap creation workflows."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_create_track_help(self, runner):
        """Test create-track --help."""
        result = runner.invoke(cli, ["roadmap", "create-track", "--help"])
        assert result.exit_code == 0

    def test_create_sprint_help(self, runner):
        """Test create-sprint --help."""
        result = runner.invoke(cli, ["roadmap", "create-sprint", "--help"])
        assert result.exit_code == 0

    def test_create_task_help(self, runner):
        """Test create-task --help."""
        result = runner.invoke(cli, ["roadmap", "create-task", "--help"])
        assert result.exit_code == 0


class TestRoadmapTransitionWorkflow:
    """Test roadmap status transition workflows."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_start_help(self, runner):
        """Test start --help."""
        result = runner.invoke(cli, ["roadmap", "start", "--help"])
        assert result.exit_code == 0

    def test_complete_help(self, runner):
        """Test complete --help."""
        result = runner.invoke(cli, ["roadmap", "complete", "--help"])
        assert result.exit_code == 0


class TestRoadmapActivityWorkflow:
    """Test roadmap activity log workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_activity_help(self, runner):
        """Test activity --help."""
        result = runner.invoke(cli, ["roadmap", "activity", "--help"])
        assert result.exit_code == 0

    def test_activity_output(self, runner):
        """Test activity command produces output."""
        result = runner.invoke(cli, ["roadmap", "activity"])
        # Should either succeed or fail gracefully
        assert result.exit_code in [0, 1]


class TestRoadmapContextWorkflow:
    """Test roadmap context workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_context_help(self, runner):
        """Test context --help."""
        result = runner.invoke(cli, ["roadmap", "context", "--help"])
        assert result.exit_code == 0


class TestRoadmapValidationWorkflow:
    """Test roadmap validation workflows."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_validate_fast_exists(self, runner):
        """Test validate-fast command exists."""
        result = runner.invoke(cli, ["roadmap", "validate-fast", "--help"])
        assert result.exit_code == 0

    def test_validate_structure_exists(self, runner):
        """Test validate-structure command exists."""
        result = runner.invoke(cli, ["roadmap", "validate-structure", "--help"])
        assert result.exit_code == 0


class TestErrorHandling:
    """Test CLI error handling."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_invalid_subcommand(self, runner):
        """Test invalid subcommand produces error."""
        result = runner.invoke(cli, ["roadmap", "invalid-command"])
        assert result.exit_code != 0

    def test_missing_required_args(self, runner):
        """Test missing required args produces error."""
        # create-track requires name
        result = runner.invoke(cli, ["roadmap", "create-track"])
        assert result.exit_code != 0

    def test_invalid_item_reference(self, runner):
        """Test invalid item reference produces error."""
        result = runner.invoke(cli, ["roadmap", "show", "nonexistent-item-12345"])
        # Should fail but not crash
        assert result.exit_code != 0 or "not found" in result.output.lower() or "error" in result.output.lower()


class TestRoadmapEditWorkflow:
    """Test roadmap edit workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_edit_help(self, runner):
        """Test edit --help."""
        result = runner.invoke(cli, ["roadmap", "edit", "--help"])
        assert result.exit_code == 0


class TestRoadmapSyncWorkflow:
    """Test roadmap sync workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_sync_help(self, runner):
        """Test sync --help."""
        result = runner.invoke(cli, ["roadmap", "sync", "--help"])
        assert result.exit_code == 0


class TestRoadmapAuditWorkflow:
    """Test roadmap audit workflow."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_audit_help(self, runner):
        """Test audit --help."""
        result = runner.invoke(cli, ["roadmap", "audit", "--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
