# Task 006: Add Integration Tests for Create Commands

**Task ID:** dogfooding-bugs-05-task-006
**Bug Addressed:** #15 (No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

After implementing the create track/sprint/task commands (Tasks 001-004), comprehensive integration tests are needed to:

1. Verify commands work end-to-end
2. Test flat ULID structure creation
3. Verify progress counters update correctly
4. Test dependency handling
5. Prevent regression in future changes

---

## Test Categories

### 1. Create Track Command Tests

```python
# tests/cli/test_create_track.py

import pytest
from pathlib import Path
from click.testing import CliRunner
from vibey.cli.main import cli
from vibey.roadmap.serialization import load_track, load_roadmap


@pytest.fixture
def flat_roadmap_env(tmp_path):
    """Create flat ULID-based roadmap environment."""
    vibey_dir = tmp_path / ".vibey"
    roadmap_dir = vibey_dir / "roadmap"

    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir()
    (roadmap_dir / "tasks").mkdir()

    # Create minimal roadmap.yaml
    (roadmap_dir / "roadmap.yaml").write_text('''
roadmap:
  id: test-roadmap
  name: Test Roadmap
  status: not_started
  progress:
    tracks_total: 0
    tracks_completed: 0
    tasks_total: 0
    tasks_completed: 0
  tracks: []
''')

    # Change to tmp directory
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    yield tmp_path

    os.chdir(original_cwd)


class TestCreateTrackCommand:
    """Integration tests for create-track command."""

    def test_create_track_minimal(self, flat_roadmap_env):
        """Create track with just name."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'Authentication System',
        ])

        assert result.exit_code == 0
        assert 'Created track' in result.output
        assert 'Authentication System' in result.output

        # Verify file created with ULID
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_files = list(tracks_dir.glob("track_*.yaml"))
        assert len(track_files) == 1

        # Verify ULID format
        track_id = track_files[0].stem
        assert track_id.startswith("track_")
        assert len(track_id) == 32  # track_ (6) + ULID (26)

    def test_create_track_with_all_options(self, flat_roadmap_env):
        """Create track with all options."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'Performance Optimization',
            '--slug', 'perf-opt',
            '--description', 'Improve application performance',
            '--priority', 'high',
            '--start',
        ])

        assert result.exit_code == 0
        assert 'in_progress' in result.output

        # Load and verify track
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_file = list(tracks_dir.glob("track_*.yaml"))[0]
        track = load_track(track_file)

        assert track.name == 'Performance Optimization'
        assert track.slug == 'perf-opt'
        assert track.description == 'Improve application performance'
        assert track.priority.value == 'high'
        assert track.status.value == 'in_progress'
        assert track.started is not None

    def test_create_track_updates_roadmap(self, flat_roadmap_env):
        """Track added to roadmap.yaml."""
        runner = CliRunner()
        runner.invoke(cli, [
            'roadmap', 'create-track',
            '--name', 'New Feature',
        ])

        # Verify roadmap updated
        roadmap_path = flat_roadmap_env / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        assert roadmap.progress.tracks_total == 1
        assert len(roadmap.tracks) == 1
        assert roadmap.tracks[0].name == 'New Feature'

    def test_create_multiple_tracks(self, flat_roadmap_env):
        """Create multiple tracks."""
        runner = CliRunner()

        for i in range(3):
            result = runner.invoke(cli, [
                'roadmap', 'create-track',
                '-n', f'Track {i+1}',
            ])
            assert result.exit_code == 0

        # Verify all tracks created
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_files = list(tracks_dir.glob("track_*.yaml"))
        assert len(track_files) == 3

        # Verify unique ULIDs
        track_ids = [f.stem for f in track_files]
        assert len(set(track_ids)) == 3

    def test_create_track_auto_slug(self, flat_roadmap_env):
        """Slug auto-generated from name."""
        runner = CliRunner()
        runner.invoke(cli, [
            'roadmap', 'create-track',
            '-n', 'User Authentication System',
        ])

        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_file = list(tracks_dir.glob("track_*.yaml"))[0]
        track = load_track(track_file)

        assert track.slug == 'user-authentication-system'


class TestCreateSprintCommand:
    """Integration tests for create-sprint command."""

    def test_create_sprint_minimal(self, flat_roadmap_env):
        """Create sprint with just track and name."""
        runner = CliRunner()

        # Create track first
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])

        # Create sprint
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '--track', 'test-track',
            '--name', 'Sprint 1',
        ])

        assert result.exit_code == 0
        assert 'Created sprint' in result.output

        # Verify file created
        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_files = list(sprints_dir.glob("sprint_*.yaml"))
        assert len(sprint_files) == 1

    def test_create_sprint_by_track_ulid(self, flat_roadmap_env):
        """Create sprint using track ULID."""
        runner = CliRunner()

        # Create track
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])

        # Get track ULID
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_file = list(tracks_dir.glob("track_*.yaml"))[0]
        track_id = track_file.stem

        # Create sprint by ULID
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '--track', track_id,
            '--name', 'Sprint 1',
        ])

        assert result.exit_code == 0

    def test_create_sprint_updates_track(self, flat_roadmap_env):
        """Sprint added to track's sprint list."""
        runner = CliRunner()

        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
        runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '-t', 'test-track',
            '-n', 'Sprint 1',
        ])

        # Load track and verify
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_file = list(tracks_dir.glob("track_*.yaml"))[0]
        track = load_track(track_file)

        assert track.progress.sprints_total == 1
        assert len(track.sprints) == 1
        assert track.sprints[0].name == 'Sprint 1'

    def test_create_sprint_with_dependency(self, flat_roadmap_env):
        """Create sprint with dependency."""
        runner = CliRunner()

        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

        # Get sprint 1 ID
        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint1_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
        sprint1_id = sprint1_file.stem

        # Create sprint 2 depending on sprint 1
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '-t', 'test-track',
            '-n', 'Sprint 2',
            '--depends-on', sprint1_id,
        ])

        assert result.exit_code == 0

        # Load sprint 2 and verify dependency
        sprint2_file = [f for f in sprints_dir.glob("sprint_*.yaml") if f.stem != sprint1_id][0]
        sprint2 = load_sprint(sprint2_file)

        assert sprint1_id in sprint2.depends_on

    def test_create_sprint_invalid_track(self, flat_roadmap_env):
        """Error on non-existent track."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '-t', 'nonexistent-track',
            '-n', 'Sprint 1',
        ])

        assert result.exit_code != 0
        assert 'not found' in result.output


class TestCreateTaskCommand:
    """Integration tests for create-task command."""

    def test_create_task_minimal(self, flat_roadmap_env):
        """Create task with just sprint and title."""
        runner = CliRunner()

        # Setup
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_id = list(sprints_dir.glob("sprint_*.yaml"))[0].stem

        # Create task
        result = runner.invoke(cli, [
            'roadmap', 'create-task',
            '--sprint', sprint_id,
            '--title', 'Implement login',
        ])

        assert result.exit_code == 0
        assert 'Created task' in result.output

        # Verify file created
        tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"
        task_files = list(tasks_dir.glob("task_*.yaml"))
        assert len(task_files) == 1

    def test_create_task_updates_sprint_progress(self, flat_roadmap_env):
        """Task creation updates sprint progress."""
        runner = CliRunner()

        # Setup
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
        sprint_id = sprint_file.stem

        # Create 3 tasks
        for i in range(3):
            runner.invoke(cli, [
                'roadmap', 'create-task',
                '-s', sprint_id,
                '-t', f'Task {i+1}',
            ])

        # Verify progress
        sprint = load_sprint(sprint_file)
        assert sprint.progress.tasks_total == 3
        assert sprint.progress.development_tasks_total == 3
        assert len(sprint.tasks) == 3

    def test_create_task_different_types(self, flat_roadmap_env):
        """Task types correctly categorized."""
        runner = CliRunner()

        # Setup
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
        sprint_id = sprint_file.stem

        # Create different task types
        runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Dev', '--type', 'development'])
        runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Gate', '--type', 'completion_gate'])
        runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Prod', '--type', 'production_gate'])

        # Verify counters
        sprint = load_sprint(sprint_file)
        assert sprint.progress.development_tasks_total == 1
        assert sprint.progress.completion_gate_tasks_total == 1
        assert sprint.progress.production_gate_tasks_total == 1

    def test_create_task_updates_track_progress(self, flat_roadmap_env):
        """Task creation updates track progress."""
        runner = CliRunner()

        # Setup
        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_id = list(sprints_dir.glob("sprint_*.yaml"))[0].stem

        # Create task
        runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Task 1'])

        # Verify track progress
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        track_file = list(tracks_dir.glob("track_*.yaml"))[0]
        track = load_track(track_file)

        assert track.progress.tasks_total == 1


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_full_hierarchy_creation(self, flat_roadmap_env):
        """Create complete track/sprint/task hierarchy."""
        runner = CliRunner()

        # Create track
        result = runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Feature X'])
        assert result.exit_code == 0

        # Create 2 sprints
        for i in range(2):
            result = runner.invoke(cli, [
                'roadmap', 'create-sprint',
                '-t', 'feature-x',
                '-n', f'Sprint {i+1}',
            ])
            assert result.exit_code == 0

        # Create tasks in each sprint
        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        for sprint_file in sprints_dir.glob("sprint_*.yaml"):
            sprint_id = sprint_file.stem
            for j in range(3):
                result = runner.invoke(cli, [
                    'roadmap', 'create-task',
                    '-s', sprint_id,
                    '-t', f'Task {j+1}',
                ])
                assert result.exit_code == 0

        # Verify structure
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"

        assert len(list(tracks_dir.glob("track_*.yaml"))) == 1
        assert len(list(sprints_dir.glob("sprint_*.yaml"))) == 2
        assert len(list(tasks_dir.glob("task_*.yaml"))) == 6

        # Verify progress rollup
        track = load_track(list(tracks_dir.glob("track_*.yaml"))[0])
        assert track.progress.sprints_total == 2
        assert track.progress.tasks_total == 6

    def test_ids_are_ulid_format(self, flat_roadmap_env):
        """All generated IDs use ULID format."""
        from vibey.roadmap.id_generator import is_ulid_format

        runner = CliRunner()

        runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test'])
        runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test', '-n', 'S1'])

        sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
        sprint_id = list(sprints_dir.glob("sprint_*.yaml"))[0].stem

        runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'T1'])

        # Verify all IDs are ULID format
        tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
        tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"

        for track_file in tracks_dir.glob("track_*.yaml"):
            assert is_ulid_format(track_file.stem)

        for sprint_file in sprints_dir.glob("sprint_*.yaml"):
            assert is_ulid_format(sprint_file.stem)

        for task_file in tasks_dir.glob("task_*.yaml"):
            assert is_ulid_format(task_file.stem)
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/cli/test_create_track.py` | Track creation tests |
| `tests/cli/test_create_sprint.py` | Sprint creation tests |
| `tests/cli/test_create_task.py` | Task creation tests |
| `tests/cli/test_create_from_plan.py` | create-from-plan tests |
| `tests/cli/conftest.py` | Shared fixtures |

---

## Success Criteria

- [ ] All create track command tests pass
- [ ] All create sprint command tests pass
- [ ] All create task command tests pass
- [ ] All create-from-plan tests pass
- [ ] End-to-end workflow tests pass
- [ ] ULID format validation tests pass
- [ ] Progress counter tests pass
- [ ] Dependency handling tests pass
- [ ] Error handling tests pass
- [ ] Tests run in CI pipeline

---

## Dependencies

- Tasks 001-004 (implementation complete)
- Task 005 (ULIDManager verification)

---

## Notes

These tests serve as:
1. **Verification** that Bug #15 is fixed
2. **Regression prevention** for future changes
3. **Documentation** of expected behavior
4. **Specification** for how create commands should work

Key testing principles:
- Use temporary directories for isolation
- Verify file system state after each operation
- Test both happy path and error cases
- Validate ULID format compliance
- Test progress counter accuracy
