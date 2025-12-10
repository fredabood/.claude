# Task 003: Add Unit Test for Path Resolution

**Task ID:** dogfooding-bugs-02-task-003
**Bug Addressed:** #3 (Wrong path resolution)
**Complexity:** Low
**Type:** Testing

---

## Problem Statement

Path resolution logic lacks comprehensive tests. Without tests, regressions can reintroduce the wrong path bug.

---

## Test Cases

### 1. FileSystemManager Path Resolution

```python
# tests/cli/roadmap_lib/test_filesystem.py

import pytest
from pathlib import Path
from vibey.cli.roadmap_lib.filesystem import FileSystemManager

class TestFileSystemManagerPaths:
    """Test path resolution for flat and nested structures."""

    def test_get_roadmap_path_flat_structure(self, tmp_path):
        """Verify roadmap path is in roadmap/ subdirectory."""
        # Setup flat structure
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_roadmap_path()

        assert path == roadmap_dir / "roadmap.yaml"
        assert str(path).endswith(".vibey/roadmap/roadmap.yaml")

    def test_get_roadmap_path_nested_structure(self, tmp_path):
        """Verify roadmap path for legacy nested structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        # No tracks/sprints/tasks subdirs = nested structure

        fs = FileSystemManager(tmp_path)
        path = fs.get_roadmap_path()

        assert path == roadmap_dir / "roadmap.yaml"

    def test_get_track_path_flat_structure(self, tmp_path):
        """Verify track path uses ULID in flat structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_track_path("01KC2D0JKTE7Z4HCNHST8ZVW4R")

        assert str(path).endswith("tracks/01KC2D0JKTE7Z4HCNHST8ZVW4R.yaml")

    def test_get_sprint_path_flat_structure(self, tmp_path):
        """Verify sprint path uses ULID in flat structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_sprint_path("01KC3AD75P4TW2MAWDWJC4YCMB")

        assert str(path).endswith("sprints/01KC3AD75P4TW2MAWDWJC4YCMB.yaml")

    def test_get_task_path_flat_structure(self, tmp_path):
        """Verify task path uses ULID in flat structure."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        path = fs.get_task_path("01KC3B2K4MNPQ2RABC4DEFGHIJ")

        assert str(path).endswith("tasks/01KC3B2K4MNPQ2RABC4DEFGHIJ.yaml")


class TestStructureDetection:
    """Test automatic structure detection."""

    def test_detect_flat_structure(self, tmp_path):
        """Detect flat when tracks/sprints/tasks dirs exist."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        (roadmap_dir / "tracks").mkdir(parents=True)
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        fs = FileSystemManager(tmp_path)
        assert fs.structure_format == "flat"

    def test_detect_nested_structure(self, tmp_path):
        """Detect nested when no tracks/sprints/tasks dirs."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        fs = FileSystemManager(tmp_path)
        assert fs.structure_format == "nested"

    def test_detect_nested_by_default(self, tmp_path):
        """Default to nested when no structure exists."""
        fs = FileSystemManager(tmp_path)
        assert fs.structure_format == "nested"
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/cli/roadmap_lib/test_filesystem.py` | Path resolution tests |

---

## Implementation Steps

1. Create test file at `tests/cli/roadmap_lib/test_filesystem.py`
2. Implement test cases above
3. Run tests and verify they pass
4. Add to CI workflow

---

## Success Criteria

- [ ] Test file created with comprehensive path tests
- [ ] All tests pass
- [ ] Tests cover flat and nested structures
- [ ] Tests cover all path methods (roadmap, track, sprint, task)
- [ ] Structure detection is tested

---

## Dependencies

- Tasks 001, 002 (path resolution fixes)

---

## Notes

These tests serve as:
1. Verification that Bug #3 is fixed
2. Regression prevention
3. Documentation of expected path behavior
