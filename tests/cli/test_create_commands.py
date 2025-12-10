"""
Integration tests for create-track, create-sprint, create-task CLI commands.

Tests Bug #15: No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure
"""

import os
import pytest
from pathlib import Path
from click.testing import CliRunner


@pytest.fixture
def flat_roadmap_env(tmp_path):
    """Create flat ULID-based roadmap environment for testing."""
    vibey_dir = tmp_path / ".vibey"
    roadmap_dir = vibey_dir / "roadmap"

    # Create directory structure
    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir()
    (roadmap_dir / "tasks").mkdir()

    # Create .id files for slug->ULID mapping
    (roadmap_dir / "tracks" / ".id").write_text("")
    (roadmap_dir / "sprints" / ".id").write_text("")
    (roadmap_dir / "tasks" / ".id").write_text("")

    # Create minimal roadmap.yaml
    from datetime import datetime, timezone
    roadmap_yaml = f"""
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  status: not_started
  blocked: false
  created: '{datetime.now(timezone.utc).isoformat()}'
  version_strategy:
    major_on: roadmap_milestone
    minor_on: track_completion
    patch_on: sprint_production_ready
  progress:
    tracks_total: 0
    tracks_completed: 0
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0
  tracks: []
  activity_log: []
  metadata:
    created_by: test
    framework_version: 2.5.0
    schema_version: '2.1'
  standards: []
  standards_config:
    inheritance: cascade
    override_policy: strict
"""
    (roadmap_dir / "roadmap.yaml").write_text(roadmap_yaml)

    # Save original cwd and change to tmp directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    yield tmp_path

    # Restore original cwd
    os.chdir(original_cwd)


class TestCreateTrackCommand:
    """Test create-track CLI command."""

    def test_create_track_help(self):
        """Verify help displays correctly."""
        from vibey.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'create-track', '--help'])

        assert result.exit_code == 0
        assert 'Create a new track' in result.output
        assert '--name' in result.output
        assert '--slug' in result.output
        assert '--priority' in result.output

    def test_create_track_minimal(self, flat_roadmap_env):
        """Create track with minimal options."""
        from vibey.cli.main import cli
        runner = CliRunner()

        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'Test Track',
        ])

        assert result.exit_code == 0
        assert 'Created track' in result.output or 'Test Track' in result.output

        # Verify file created
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_files = [f for f in tracks_dir.glob("*.yaml") if f.name != ".id"]
        assert len(track_files) == 1

        # Verify ULID format (26 chars, alphanumeric)
        track_id = track_files[0].stem
        assert len(track_id) == 26
        assert track_id.isalnum()

    def test_create_track_with_slug(self, flat_roadmap_env):
        """Create track with custom slug."""
        from vibey.cli.main import cli
        runner = CliRunner()

        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'My Feature',
            '--slug', 'my-feature',
        ])

        assert result.exit_code == 0

        # Verify .id mapping created
        id_file = flat_roadmap_env / ".vibey" / "roadmap" / "tracks" / ".id"
        id_content = id_file.read_text()
        assert 'my-feature=' in id_content


class TestCreateSprintCommand:
    """Test create-sprint CLI command."""

    def test_create_sprint_help(self):
        """Verify help displays correctly."""
        from vibey.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'create-sprint', '--help'])

        assert result.exit_code == 0
        assert 'Create a new sprint' in result.output
        assert '--track' in result.output
        assert '--name' in result.output

    def test_create_sprint_after_track(self, flat_roadmap_env):
        """Create sprint in an existing track."""
        from vibey.cli.main import cli
        runner = CliRunner()

        # First create a track
        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'Parent Track',
            '--slug', 'parent-track',
        ])
        assert result.exit_code == 0, f"Track creation failed: {result.output}"

        # Then create a sprint
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '--track', 'parent-track',
            '--name', 'Sprint 1',
        ])

        assert result.exit_code == 0, f"Sprint creation failed: {result.output}"
        assert 'Created sprint' in result.output or 'Sprint 1' in result.output

        # Verify sprint file created
        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_files = [f for f in sprints_dir.glob("*.yaml") if f.name != ".id"]
        assert len(sprint_files) == 1


class TestCreateTaskCommand:
    """Test create-task CLI command."""

    def test_create_task_help(self):
        """Verify help displays correctly."""
        from vibey.cli.main import cli
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'create-task', '--help'])

        assert result.exit_code == 0
        assert 'Create a new task' in result.output
        assert '--sprint' in result.output
        assert '--title' in result.output
        assert '--type' in result.output

    def test_create_task_in_sprint(self, flat_roadmap_env):
        """Create task in an existing sprint."""
        from vibey.cli.main import cli
        runner = CliRunner()

        # Create track first
        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'Test Track',
            '--slug', 'test-track',
        ])
        assert result.exit_code == 0

        # Create sprint
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '--track', 'test-track',
            '--name', 'Sprint 1',
        ])
        assert result.exit_code == 0

        # Get sprint slug from .id file
        id_file = flat_roadmap_env / ".vibey" / "roadmap" / "sprints" / ".id"
        id_content = id_file.read_text()
        sprint_slug = id_content.strip().split("=")[0]

        # Create task
        result = runner.invoke(cli, [
            'roadmap', 'create-task',
            '--sprint', sprint_slug,
            '--title', 'Implement feature',
        ])

        assert result.exit_code == 0, f"Task creation failed: {result.output}"
        assert 'Created task' in result.output or 'Implement feature' in result.output

        # Verify task file created
        tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"
        task_files = [f for f in tasks_dir.glob("*.yaml") if f.name != ".id"]
        assert len(task_files) == 1


class TestULIDFormat:
    """Test that all IDs use proper ULID format."""

    def test_ulid_format_validation(self, flat_roadmap_env):
        """All generated IDs should be valid ULIDs."""
        from vibey.cli.main import cli
        runner = CliRunner()

        # Create full hierarchy
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test', '-s', 'test'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test', '-n', 'Sprint 1'])

        # Get sprint slug
        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        id_file = sprints_dir / ".id"
        sprint_slug = id_file.read_text().strip().split("=")[0]

        runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_slug, '-t', 'Task 1'])

        # Verify all IDs are 26-char alphanumeric (ULID format)
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"

        for yaml_file in tracks_dir.glob("*.yaml"):
            if yaml_file.name != ".id":
                ulid = yaml_file.stem
                assert len(ulid) == 26, f"Track ID {ulid} not 26 chars"
                assert ulid.isalnum(), f"Track ID {ulid} not alphanumeric"

        for yaml_file in sprints_dir.glob("*.yaml"):
            if yaml_file.name != ".id":
                ulid = yaml_file.stem
                assert len(ulid) == 26, f"Sprint ID {ulid} not 26 chars"
                assert ulid.isalnum(), f"Sprint ID {ulid} not alphanumeric"

        for yaml_file in tasks_dir.glob("*.yaml"):
            if yaml_file.name != ".id":
                ulid = yaml_file.stem
                assert len(ulid) == 26, f"Task ID {ulid} not 26 chars"
                assert ulid.isalnum(), f"Task ID {ulid} not alphanumeric"
