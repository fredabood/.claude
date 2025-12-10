# Task 009: Add Migration Test for v1 to v2 Loading

**Task ID:** dogfooding-bugs-01-task-009
**Bug Addressed:** #8 (blocked field KeyError in v2 format)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

There are no comprehensive tests verifying that:
1. v1 format YAML files load correctly
2. v2 format YAML files (without blocked field) load correctly
3. Mixed v1/v2 formats in the same roadmap load correctly
4. The transition from v1 to v2 format is seamless

---

## Solution Design

Create a comprehensive test suite that validates v1/v2 format loading for all roadmap object types.

### Test Categories

1. **Unit Tests** - Test each loader function with v1 and v2 formats
2. **Integration Tests** - Test full roadmap loading with mixed formats
3. **Regression Tests** - Ensure specific bug scenarios don't recur
4. **Round-Trip Tests** - Load v1, save as v2, reload

---

## Implementation

### Test File Structure

```
tests/
  roadmap/
    serialization/
      test_yaml_loader_v1_v2.py
      fixtures/
        v1/
          roadmap.yaml
          track.yaml
          sprint.yaml
          task.yaml
        v2/
          roadmap.yaml
          track.yaml
          sprint.yaml
          task.yaml
```

### Test Cases

```python
# tests/roadmap/serialization/test_yaml_loader_v1_v2.py

import pytest
from pathlib import Path
from vibey.roadmap.serialization.yaml_loader import (
    load_roadmap,
    load_track,
    load_sprint,
    load_task,
    detect_yaml_format,
)

class TestFormatDetection:
    """Test v1 vs v2 format detection."""

    def test_detect_v1_format_with_blocked_field(self):
        data = {'id': 'test', 'blocked': False, 'blocked_by': []}
        assert detect_yaml_format(data) == 'v1'

    def test_detect_v2_format_with_criteria(self):
        data = {'id': 'test', 'criteria': []}
        assert detect_yaml_format(data) == 'v2'

    def test_detect_v2_format_with_parent_ref(self):
        data = {'id': 'test', 'parent_ref': 'parent-id'}
        assert detect_yaml_format(data) == 'v2'


class TestLoadRoadmapFormats:
    """Test roadmap loading for v1 and v2 formats."""

    def test_load_v1_roadmap_with_blocked(self, tmp_path):
        """v1 format with explicit blocked field."""
        yaml_content = '''
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  version_strategy:
    major_on: roadmap_milestone
    minor_on: track_completion
    patch_on: sprint_production_ready
  status: in_progress
  blocked: false
  blocked_by: []
  created: '2024-01-01T00:00:00+00:00'
  progress:
    tracks_total: 0
    tracks_completed: 0
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
  tracks: []
'''
        roadmap_file = tmp_path / "roadmap.yaml"
        roadmap_file.write_text(yaml_content)

        roadmap = load_roadmap(roadmap_file)
        assert roadmap.id == 'test-roadmap'
        assert roadmap.blocked == False

    def test_load_v2_roadmap_without_blocked(self, tmp_path):
        """v2 format without blocked field (computed)."""
        yaml_content = '''
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  version_strategy:
    major_on: roadmap_milestone
    minor_on: track_completion
    patch_on: sprint_production_ready
  status: in_progress
  created: '2024-01-01T00:00:00+00:00'
  progress:
    tracks_total: 0
    tracks_completed: 0
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
  tracks: []
'''
        roadmap_file = tmp_path / "roadmap.yaml"
        roadmap_file.write_text(yaml_content)

        roadmap = load_roadmap(roadmap_file)
        assert roadmap.id == 'test-roadmap'
        assert roadmap.blocked == False  # Default value


class TestLoadTrackFormats:
    """Test track loading for v1 and v2 formats."""

    def test_load_v1_track_with_blocked(self, tmp_path):
        """v1 format with explicit blocked field."""
        yaml_content = '''
track:
  id: test-track
  roadmap_id: test-roadmap
  name: Test Track
  status: in_progress
  blocked: false
  blocked_by: []
  depends_on: []
  priority: medium
  created: '2024-01-01T00:00:00+00:00'
  progress:
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
  sprints: []
'''
        track_file = tmp_path / "track.yaml"
        track_file.write_text(yaml_content)

        track = load_track(track_file)
        assert track.id == 'test-track'
        assert track.blocked == False

    def test_load_v2_track_ulid_format(self, tmp_path):
        """v2 ULID format without blocked field."""
        yaml_content = '''
track:
  id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  roadmap_id: vibey-framework-v2
  name: Test Track
  status: in_progress
  priority: medium
  created: '2024-01-01T00:00:00+00:00'
  progress:
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
  sprints: []
'''
        track_file = tmp_path / "track.yaml"
        track_file.write_text(yaml_content)

        track = load_track(track_file)
        assert track.id == '01KC2D0JKVT80AFQ6C1PA8CKJD'
        assert track.blocked == False  # Default


class TestLoadSprintFormats:
    """Test sprint loading for v1 and v2 formats."""

    def test_load_v1_sprint_with_blocked(self, tmp_path):
        """v1 format with explicit blocked field."""
        yaml_content = '''
sprint:
  id: test-sprint
  track_id: test-track
  roadmap_id: test-roadmap
  name: Sprint 1
  status: not_started
  blocked: false
  blocked_by: []
  depends_on: []
  created: '2024-01-01T00:00:00+00:00'
  tasks: []
'''
        sprint_file = tmp_path / "sprint.yaml"
        sprint_file.write_text(yaml_content)

        sprint = load_sprint(sprint_file)
        assert sprint.id == 'test-sprint'
        # blocked may be computed

    def test_load_v2_sprint_ulid_format(self, tmp_path):
        """v2 ULID format without blocked field."""
        yaml_content = '''
sprint:
  id: 01KC3AD75P4TW2MAWDWJC4YCMB
  track_id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  roadmap_id: vibey-framework-v2
  name: Sprint 1
  status: not_started
  created: '2024-01-01T00:00:00+00:00'
  tasks: []
'''
        sprint_file = tmp_path / "sprint.yaml"
        sprint_file.write_text(yaml_content)

        sprint = load_sprint(sprint_file)
        assert sprint.id == '01KC3AD75P4TW2MAWDWJC4YCMB'


class TestLoadTaskFormats:
    """Test task loading for v1 and v2 formats."""

    def test_load_v1_task_with_blocked(self, tmp_path):
        """v1 format with explicit blocked field."""
        yaml_content = '''
tasks:
  - id: test-task
    sprint_id: test-sprint
    track_id: test-track
    title: Test Task
    status: not_started
    blocked: false
    blocked_by: []
    depends_on: []
    created: '2024-01-01T00:00:00+00:00'
'''
        task_file = tmp_path / "tasks.yaml"
        task_file.write_text(yaml_content)

        from vibey.roadmap.serialization.yaml_loader import load_tasks
        tasks = load_tasks(task_file)
        assert len(tasks) == 1
        assert tasks[0].blocked == False

    def test_load_v2_task_ulid_format(self, tmp_path):
        """v2 ULID format without blocked field."""
        yaml_content = '''
task:
  id: 01KC3B2K4MNPQ2RABC4DEFGHIJ
  sprint_id: 01KC3AD75P4TW2MAWDWJC4YCMB
  track_id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  title: Test Task
  status: not_started
  created: '2024-01-01T00:00:00+00:00'
'''
        task_file = tmp_path / "task.yaml"
        task_file.write_text(yaml_content)

        task = load_task(task_file)
        assert task.id == '01KC3B2K4MNPQ2RABC4DEFGHIJ'


class TestMigrationScenarios:
    """Test real-world migration scenarios."""

    def test_mixed_v1_v2_in_same_roadmap(self, tmp_path):
        """Roadmap with some v1 and some v2 format files."""
        # Create v1 roadmap
        # Create v2 track
        # Verify both load correctly together
        pass  # Implementation needed

    def test_blocked_true_with_unsatisfied_deps(self, tmp_path):
        """v1 format with blocked=true and dependencies."""
        pass  # Implementation needed

    def test_bug_8_regression(self, tmp_path):
        """Specific test for Bug #8 - KeyError on blocked field."""
        yaml_content = '''
roadmap:
  id: test-roadmap
  name: Test
  version: 1.0.0
  status: in_progress
  created: '2024-01-01T00:00:00+00:00'
  progress:
    tracks_total: 0
    tracks_completed: 0
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
  tracks: []
'''
        # This MUST NOT raise KeyError for 'blocked'
        roadmap_file = tmp_path / "roadmap.yaml"
        roadmap_file.write_text(yaml_content)

        roadmap = load_roadmap(roadmap_file)
        assert roadmap is not None
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/roadmap/serialization/test_yaml_loader_v1_v2.py` | Main test file |
| `tests/roadmap/serialization/fixtures/v1/*.yaml` | v1 format fixtures |
| `tests/roadmap/serialization/fixtures/v2/*.yaml` | v2 format fixtures |

---

## Success Criteria

- [ ] All v1 format fixtures load without errors
- [ ] All v2 format fixtures load without errors
- [ ] Format detection works correctly
- [ ] Bug #8 regression test passes
- [ ] Test coverage for all load_* functions
- [ ] CI runs these tests

---

## Dependencies

- **Tasks 005-008** should be completed first
- Tests will verify those fixes work correctly

---

## Notes

This test suite serves as:
1. Verification that Bug #8 is fixed
2. Regression prevention for future changes
3. Documentation of v1 vs v2 format differences
4. Migration guide through test examples
