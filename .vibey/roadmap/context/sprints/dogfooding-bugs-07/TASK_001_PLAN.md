# Task 001: Create activity_log/ Directory Structure

**Task ID:** dogfooding-bugs-07-task-001
**Bug Addressed:** #13 (Activity Log Not Migrated to JSONL Format)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The unified architecture specifies that activity log data should be stored in time-bucketed JSONL files at `.vibey/roadmap/activity_log/`. Currently, no such directory exists and all activity data is stored in a monolithic `audit-trail.yaml` file.

---

## Current State

**Designed Format (per unified architecture):**
```
.vibey/roadmap/activity_log/
├── 2025-11.jsonl    # November 2025 events
├── 2025-12.jsonl    # December 2025 events
└── ...
```

**Actual Format:**
```
.vibey/roadmap/audit-trail.yaml   # 1,684 lines, monolithic YAML
```

---

## Implementation

### 1. Add Directory Constant to FileSystemManager

```python
# vibey/cli/roadmap_lib/filesystem.py

class FileSystemManager:
    """Manages file system operations for roadmap."""

    def __init__(self, root_dir: Path, warn_on_duplicate: bool = True):
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.roadmap_root = self.vibey_dir / "roadmap"

        # Existing directories
        self.tracks_dir = self.roadmap_root / "tracks"
        self.sprints_dir = self.roadmap_root / "sprints"
        self.tasks_dir = self.roadmap_root / "tasks"
        self.artifacts_dir = self.roadmap_root / "artifacts"
        self.context_dir = self.roadmap_root / "context"

        # NEW: Activity log directory
        self.activity_log_dir = self.roadmap_root / "activity_log"
```

### 2. Add Directory Creation Method

```python
# vibey/cli/roadmap_lib/filesystem.py

def ensure_activity_log_dir(self) -> Path:
    """
    Ensure activity_log directory exists.

    Returns:
        Path to activity_log directory
    """
    self.activity_log_dir.mkdir(parents=True, exist_ok=True)
    return self.activity_log_dir


def get_activity_log_path(self, year: int, month: int) -> Path:
    """
    Get path to activity log file for a specific month.

    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        Path to JSONL file (e.g., .vibey/roadmap/activity_log/2025-11.jsonl)
    """
    filename = f"{year}-{month:02d}.jsonl"
    return self.activity_log_dir / filename


def get_current_activity_log_path(self) -> Path:
    """
    Get path to activity log file for current month.

    Returns:
        Path to current month's JSONL file
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return self.get_activity_log_path(now.year, now.month)
```

### 3. Update ensure_directories Method

```python
# vibey/cli/roadmap_lib/filesystem.py

def ensure_directories(self) -> None:
    """Create all required roadmap directories if they don't exist."""
    directories = [
        self.roadmap_root,
        self.tracks_dir,
        self.sprints_dir,
        self.tasks_dir,
        self.artifacts_dir,
        self.context_dir,
        self.activity_log_dir,  # NEW
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/roadmap_lib/filesystem.py` | Add `activity_log_dir` attribute, `ensure_activity_log_dir()`, `get_activity_log_path()`, `get_current_activity_log_path()` methods |

---

## Testing Strategy

```python
# tests/cli/roadmap_lib/test_filesystem_activity_log.py

import pytest
from pathlib import Path


class TestActivityLogDirectory:
    """Tests for activity_log directory management."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temp project structure."""
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)
        return tmp_path

    def test_activity_log_dir_attribute(self, temp_project):
        """FileSystemManager has activity_log_dir attribute."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(temp_project)

        expected = temp_project / ".vibey" / "roadmap" / "activity_log"
        assert fs.activity_log_dir == expected

    def test_ensure_activity_log_dir_creates_directory(self, temp_project):
        """ensure_activity_log_dir creates directory if missing."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(temp_project)
        result = fs.ensure_activity_log_dir()

        assert result.exists()
        assert result.is_dir()

    def test_get_activity_log_path_format(self, temp_project):
        """get_activity_log_path returns correct path format."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(temp_project)
        path = fs.get_activity_log_path(2025, 11)

        assert path.name == "2025-11.jsonl"
        assert path.parent == fs.activity_log_dir

    def test_get_activity_log_path_zero_padded_month(self, temp_project):
        """Month is zero-padded in filename."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(temp_project)

        assert fs.get_activity_log_path(2025, 1).name == "2025-01.jsonl"
        assert fs.get_activity_log_path(2025, 9).name == "2025-09.jsonl"
        assert fs.get_activity_log_path(2025, 12).name == "2025-12.jsonl"

    def test_get_current_activity_log_path(self, temp_project):
        """get_current_activity_log_path uses current month."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        from datetime import datetime, timezone

        fs = FileSystemManager(temp_project)
        now = datetime.now(timezone.utc)

        path = fs.get_current_activity_log_path()
        expected_name = f"{now.year}-{now.month:02d}.jsonl"

        assert path.name == expected_name

    def test_ensure_directories_includes_activity_log(self, temp_project):
        """ensure_directories creates activity_log directory."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(temp_project)
        fs.ensure_directories()

        assert fs.activity_log_dir.exists()
```

### Manual Verification

```bash
# Verify directory creation
python3 -c "
from pathlib import Path
from vibey.cli.roadmap_lib.filesystem import FileSystemManager

fs = FileSystemManager(Path.cwd())
fs.ensure_activity_log_dir()
print(f'Created: {fs.activity_log_dir}')
print(f'Exists: {fs.activity_log_dir.exists()}')
"

# Verify path generation
python3 -c "
from pathlib import Path
from vibey.cli.roadmap_lib.filesystem import FileSystemManager

fs = FileSystemManager(Path.cwd())
print(f'Nov 2025: {fs.get_activity_log_path(2025, 11)}')
print(f'Current: {fs.get_current_activity_log_path()}')
"
```

---

## Success Criteria

- [ ] `activity_log_dir` attribute added to FileSystemManager
- [ ] `ensure_activity_log_dir()` method creates directory
- [ ] `get_activity_log_path(year, month)` returns correct path
- [ ] `get_current_activity_log_path()` returns current month's path
- [ ] `ensure_directories()` includes activity_log
- [ ] Month is zero-padded in filename (01-12)
- [ ] All tests pass

---

## Dependencies

None - this is the first task in the sprint.

---

## Notes

This task establishes the foundation for the JSONL activity log system. Subsequent tasks will:
- Task 002: Write events to these JSONL files
- Task 003: Read events from these JSONL files
- Task 004: Migrate existing data from audit-trail.yaml
- Task 005: Update consumers to use new format
- Task 006: Add comprehensive tests

The directory structure follows the time-bucketed pattern from the unified architecture:
- One file per month: `YYYY-MM.jsonl`
- Append-only within each file
- Easy to archive old months
- Efficient queries for recent activity
