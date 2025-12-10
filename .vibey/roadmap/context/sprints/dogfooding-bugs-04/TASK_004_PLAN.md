# Task 004: Add Unit Tests for Progress Propagation

**Task ID:** dogfooding-bugs-04-task-004
**Bug Addressed:** #1 (Track and Sprint Progress Not Auto-Updated After Task Completion)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

After implementing the progress propagation fixes (Tasks 002-003), comprehensive unit tests are needed to:

1. Verify progress propagates correctly in flat structure
2. Verify backward compatibility with nested structure
3. Test edge cases and error conditions
4. Prevent regression in future changes

---

## Test Categories

### 1. Progress Calculation Tests

```python
# tests/operations/roadmap/test_progress.py

import pytest
from pathlib import Path
from vibey.operations.roadmap.update import (
    _update_sprint_progress,
    _update_track_progress,
    _update_roadmap_progress,
)
from vibey.roadmap.serialization import load_sprint, load_track, load_roadmap


class TestSprintProgressCalculation:
    """Test sprint progress calculation."""

    def test_sprint_progress_from_tasks(self, flat_roadmap_env):
        """Sprint progress calculated from task completion."""
        fs = FileSystemManager(flat_roadmap_env)

        # Complete 3 of 5 tasks
        complete_task(flat_roadmap_env, "task-001")
        complete_task(flat_roadmap_env, "task-002")
        complete_task(flat_roadmap_env, "task-003")

        sprint = load_sprint(sprint_path)

        assert sprint.progress.tasks_total == 5
        assert sprint.progress.tasks_completed == 3
        assert sprint.progress.completion_percent == 60

    def test_sprint_progress_by_task_type(self, flat_roadmap_env):
        """Sprint tracks progress by task type."""
        fs = FileSystemManager(flat_roadmap_env)

        # Create tasks of different types
        create_task(flat_roadmap_env, "dev-task-1", task_type="development")
        create_task(flat_roadmap_env, "gate-task-1", task_type="completion_gate")

        complete_task(flat_roadmap_env, "dev-task-1")

        sprint = load_sprint(sprint_path)

        assert sprint.progress.development_tasks_total == 1
        assert sprint.progress.development_tasks_completed == 1
        assert sprint.progress.completion_gate_tasks_total == 1
        assert sprint.progress.completion_gate_tasks_completed == 0

    def test_sprint_progress_empty_sprint(self, flat_roadmap_env):
        """Empty sprint has zero progress."""
        sprint = load_sprint(empty_sprint_path)

        assert sprint.progress.tasks_total == 0
        assert sprint.progress.completion_percent == 0


class TestTrackProgressCalculation:
    """Test track progress calculation."""

    def test_track_progress_from_sprints(self, flat_roadmap_env):
        """Track progress calculated from sprint completion."""
        fs = FileSystemManager(flat_roadmap_env)

        # Complete 2 of 4 sprints
        complete_sprint(flat_roadmap_env, "sprint-001")
        complete_sprint(flat_roadmap_env, "sprint-002")

        track = load_track(track_path)

        assert track.progress.sprints_total == 4
        assert track.progress.sprints_completed == 2
        assert track.progress.completion_percent == 50

    def test_track_aggregates_task_counts(self, flat_roadmap_env):
        """Track aggregates task counts from all sprints."""
        track = load_track(track_path)

        # Total tasks = sum of all sprint tasks
        expected_total = sum(s.progress.tasks_total for s in sprints)
        assert track.progress.tasks_total == expected_total

    def test_track_progress_flat_structure(self, flat_roadmap_env):
        """Track progress works with flat directory structure."""
        fs = FileSystemManager(flat_roadmap_env)
        assert fs.structure_format == "flat"

        _update_track_progress(fs, "track-001")

        track = load_track(track_path)
        assert track.progress.tasks_total > 0


class TestRoadmapProgressCalculation:
    """Test roadmap progress calculation."""

    def test_roadmap_progress_from_tracks(self, flat_roadmap_env):
        """Roadmap progress calculated from track completion."""
        roadmap = load_roadmap(roadmap_path)

        assert roadmap.progress.tracks_total > 0
        assert roadmap.progress.completion_percent >= 0

    def test_roadmap_aggregates_all_levels(self, flat_roadmap_env):
        """Roadmap aggregates sprints and tasks from all tracks."""
        roadmap = load_roadmap(roadmap_path)

        assert roadmap.progress.sprints_total > 0
        assert roadmap.progress.tasks_total > 0
```

### 2. Progress Propagation Tests

```python
class TestProgressPropagation:
    """Test progress propagation up the hierarchy."""

    def test_task_completion_updates_sprint(self, flat_roadmap_env):
        """Completing a task updates sprint progress."""
        sprint_before = load_sprint(sprint_path)
        initial_completed = sprint_before.progress.tasks_completed

        complete_task(flat_roadmap_env, "task-001")

        sprint_after = load_sprint(sprint_path)
        assert sprint_after.progress.tasks_completed == initial_completed + 1

    def test_task_completion_updates_track(self, flat_roadmap_env):
        """Completing a task updates track progress."""
        track_before = load_track(track_path)
        initial_completed = track_before.progress.tasks_completed

        complete_task(flat_roadmap_env, "task-001")

        track_after = load_track(track_path)
        assert track_after.progress.tasks_completed == initial_completed + 1

    def test_task_completion_updates_roadmap(self, flat_roadmap_env):
        """Completing a task updates roadmap progress."""
        roadmap_before = load_roadmap(roadmap_path)
        initial_completed = roadmap_before.progress.tasks_completed

        complete_task(flat_roadmap_env, "task-001")

        roadmap_after = load_roadmap(roadmap_path)
        assert roadmap_after.progress.tasks_completed == initial_completed + 1

    def test_sprint_completion_updates_track(self, flat_roadmap_env):
        """Completing a sprint updates track progress."""
        # Complete all tasks in sprint first
        for task_id in sprint_tasks:
            complete_task(flat_roadmap_env, task_id)

        track_before = load_track(track_path)
        initial_completed = track_before.progress.sprints_completed

        complete_sprint(flat_roadmap_env, "sprint-001")

        track_after = load_track(track_path)
        assert track_after.progress.sprints_completed == initial_completed + 1

    def test_full_chain_propagation(self, flat_roadmap_env):
        """Full propagation: task → sprint → track → roadmap."""
        # Record initial state
        roadmap_before = load_roadmap(roadmap_path)
        track_before = load_track(track_path)
        sprint_before = load_sprint(sprint_path)

        # Complete one task
        complete_task(flat_roadmap_env, "task-001")

        # Verify all levels updated
        sprint_after = load_sprint(sprint_path)
        assert sprint_after.progress.tasks_completed > sprint_before.progress.tasks_completed

        track_after = load_track(track_path)
        assert track_after.progress.tasks_completed > track_before.progress.tasks_completed

        roadmap_after = load_roadmap(roadmap_path)
        assert roadmap_after.progress.tasks_completed > roadmap_before.progress.tasks_completed
```

### 3. Auto-Progression Tests

```python
class TestAutoProgression:
    """Test automatic status progression."""

    def test_sprint_auto_starts_on_task_completion(self, flat_roadmap_env):
        """Sprint auto-starts when first task is completed."""
        sprint_before = load_sprint(sprint_path)
        assert sprint_before.status == Status.NOT_STARTED

        complete_task(flat_roadmap_env, "task-001")

        sprint_after = load_sprint(sprint_path)
        assert sprint_after.status == Status.IN_PROGRESS

    def test_sprint_auto_completes_all_tasks_done(self, flat_roadmap_env):
        """Sprint auto-completes when all dev tasks done."""
        # Complete all development tasks
        for task_id in dev_tasks:
            complete_task(flat_roadmap_env, task_id)

        sprint = load_sprint(sprint_path)
        # Should be in completion_gate_check or beyond
        assert sprint.status != Status.IN_PROGRESS

    def test_track_auto_starts_on_sprint_start(self, flat_roadmap_env):
        """Track auto-starts when first sprint starts."""
        track_before = load_track(track_path)
        assert track_before.status == Status.NOT_STARTED

        start_sprint(flat_roadmap_env, "sprint-001")

        track_after = load_track(track_path)
        assert track_after.status == Status.IN_PROGRESS

    def test_track_auto_completes_all_sprints_done(self, flat_roadmap_env):
        """Track auto-completes when all sprints complete."""
        # Complete all sprints
        for sprint_id in track_sprints:
            complete_all_tasks_in_sprint(sprint_id)
            complete_sprint(flat_roadmap_env, sprint_id)

        track = load_track(track_path)
        assert track.status == Status.COMPLETED

    def test_no_auto_progression_if_blocked(self, flat_roadmap_env):
        """No auto-progression if entity is blocked."""
        # Add a blocking dependency
        add_dependency(sprint_id, blocker_id, status="in_progress")

        # Complete all tasks
        for task_id in sprint_tasks:
            complete_task(flat_roadmap_env, task_id)

        sprint = load_sprint(sprint_path)
        # Should not auto-progress due to blocker
        assert sprint.blocked is True
```

### 4. Structure Compatibility Tests

```python
class TestStructureCompatibility:
    """Test both flat and nested structures."""

    def test_progress_in_flat_structure(self, flat_roadmap_env):
        """Progress works in flat ULID structure."""
        fs = FileSystemManager(flat_roadmap_env)
        assert fs.structure_format == "flat"

        complete_task(flat_roadmap_env, "01KC2D0N8H7E5C2Q9V3K1B4J6M")

        # Verify updates propagated
        sprint = load_sprint(sprint_path)
        assert sprint.progress.tasks_completed > 0

    def test_progress_in_nested_structure(self, nested_roadmap_env):
        """Progress works in nested slug structure."""
        fs = FileSystemManager(nested_roadmap_env)
        assert fs.structure_format == "nested"

        complete_task(nested_roadmap_env, "track-1-sprint-1-task-001")

        # Verify updates propagated
        sprint = load_sprint(sprint_path)
        assert sprint.progress.tasks_completed > 0

    def test_track_id_extracted_correctly_flat(self, flat_roadmap_env):
        """Track ID extracted from sprint model in flat structure."""
        sprint = load_sprint(sprint_path)

        # track_id should be ULID
        assert len(sprint.track_id) == 26
        assert sprint.track_id.isalnum()

    def test_track_id_extracted_correctly_nested(self, nested_roadmap_env):
        """Track ID extracted from ID parsing in nested structure."""
        # In nested, track_id can be derived from sprint_id
        sprint_id = "track-1-sprint-1"
        expected_track_id = "track-1"

        # Still works via model
        sprint = load_sprint(sprint_path)
        assert sprint.track_id == expected_track_id
```

### 5. Edge Case Tests

```python
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_progress_with_no_tasks(self, flat_roadmap_env):
        """Progress handles sprint with no tasks."""
        _update_sprint_progress(fs, empty_sprint_id)

        sprint = load_sprint(empty_sprint_path)
        assert sprint.progress.tasks_total == 0
        assert sprint.progress.completion_percent == 0

    def test_progress_with_missing_sprint(self, flat_roadmap_env):
        """Progress handles missing sprint gracefully."""
        # Should not raise
        _update_sprint_progress(fs, "nonexistent-sprint")

    def test_progress_with_orphan_task(self, flat_roadmap_env):
        """Progress handles task without valid sprint."""
        # Task with invalid sprint_id
        task = create_task(flat_roadmap_env, "orphan-task", sprint_id="invalid")

        # Should not raise, just skip
        complete_task(flat_roadmap_env, "orphan-task")

    def test_progress_concurrent_updates(self, flat_roadmap_env):
        """Progress handles concurrent task completions."""
        import threading

        def complete_task_thread(task_id):
            complete_task(flat_roadmap_env, task_id)

        threads = [
            threading.Thread(target=complete_task_thread, args=(f"task-{i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        sprint = load_sprint(sprint_path)
        assert sprint.progress.tasks_completed == 5

    def test_progress_with_malformed_yaml(self, flat_roadmap_env):
        """Progress handles malformed YAML files."""
        # Corrupt a task file
        (tasks_dir / "bad.yaml").write_text("not: valid: yaml: {[")

        # Should not raise, just skip bad file
        _update_sprint_progress(fs, sprint_id)
```

---

## Test Fixtures

```python
# tests/conftest.py

@pytest.fixture
def flat_roadmap_env(tmp_path):
    """Create flat ULID-based roadmap environment."""
    create_flat_structure(tmp_path)
    return tmp_path


@pytest.fixture
def nested_roadmap_env(tmp_path):
    """Create nested slug-based roadmap environment."""
    create_nested_structure(tmp_path)
    return tmp_path


def create_flat_structure(path: Path):
    """Create test roadmap with flat ULID structure."""
    vibey_dir = path / ".vibey"
    roadmap_dir = vibey_dir / "roadmap"

    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir()
    (roadmap_dir / "tasks").mkdir()

    # Create roadmap.yaml
    (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test Roadmap
  status: in_progress
  progress:
    tracks_total: 1
    tracks_completed: 0
""")

    # Create track
    track_id = "01KC2D0FT6KF4V2R1J0HDFR1ZM"
    (roadmap_dir / "tracks" / f"{track_id}.yaml").write_text(f"""
track:
  id: {track_id}
  name: Test Track
  status: not_started
  progress:
    sprints_total: 1
    sprints_completed: 0
""")

    # Create sprint
    sprint_id = "01KC2D0JKVT80AFQ6C1PA8CKJD"
    (roadmap_dir / "sprints" / f"{sprint_id}.yaml").write_text(f"""
sprint:
  id: {sprint_id}
  track_id: {track_id}
  name: Test Sprint
  status: not_started
  progress:
    tasks_total: 5
    tasks_completed: 0
""")

    # Create tasks
    for i in range(5):
        task_id = f"01KC2D0N8H{i}E5C2Q9V3K1B4J6M"
        (roadmap_dir / "tasks" / f"{task_id}.yaml").write_text(f"""
task:
  id: {task_id}
  sprint_id: {sprint_id}
  track_id: {track_id}
  title: Task {i+1}
  status: not_started
""")

    return path
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/operations/roadmap/test_progress.py` | Progress calculation tests |
| `tests/operations/roadmap/test_propagation.py` | Propagation tests |
| `tests/operations/roadmap/test_auto_progression.py` | Auto-progression tests |
| `tests/operations/roadmap/conftest.py` | Test fixtures |

---

## Success Criteria

- [ ] All progress calculation tests pass
- [ ] All propagation tests pass
- [ ] All auto-progression tests pass
- [ ] Both flat and nested structure tests pass
- [ ] Edge case tests pass
- [ ] Tests run in CI pipeline
- [ ] Test coverage > 80% for progress code

---

## Dependencies

- Tasks 002-003 (implementation complete)

---

## Notes

These tests serve as:
1. **Verification** that Bug #1 is fixed
2. **Regression prevention** for future changes
3. **Documentation** of expected behavior
4. **Specification** for how progress should work
