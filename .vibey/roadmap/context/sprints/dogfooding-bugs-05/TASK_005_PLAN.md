# Task 005: Create ULIDManager for ULID Generation

**Task ID:** dogfooding-bugs-05-task-005
**Bug Addressed:** #15 (No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The sprint plan originally identified the need to create a ULIDManager for ULID generation. However, **this functionality already exists** in `vibey/roadmap/id_generator.py`.

---

## Current Implementation (ALREADY EXISTS!)

**File:** `vibey/roadmap/id_generator.py` (341 lines)

The module provides complete ULID-based ID generation:

```python
# Core generation functions
def generate_track_id() -> str:
    """Generate track ID: track_{ulid}"""
    ulid = ULID()
    return f"track_{str(ulid)}"

def generate_sprint_id() -> str:
    """Generate sprint ID: sprint_{ulid}"""
    ulid = ULID()
    return f"sprint_{str(ulid)}"

def generate_task_id() -> str:
    """Generate task ID: task_{ulid}"""
    ulid = ULID()
    return f"task_{str(ulid)}"

# Generic generation with type parameter
def generate_id(type: str, timestamp: Optional[datetime] = None) -> str:
    """Generate an ID for any type, optionally with specific timestamp."""

# Timestamp-based generation (for migration)
def generate_id_from_timestamp(prefix: str, timestamp: datetime) -> str:
    """Generate an ID from a specific timestamp."""

# Validation functions
def is_valid_id(id: str) -> bool:
    """Check if an ID is valid ULID-based format."""

def is_ulid_format(id: str) -> bool:
    """Check if an ID uses ULID format (vs old slug format)."""

# Utility functions
def extract_timestamp(id: str) -> datetime:
    """Extract creation timestamp from a ULID-based ID."""

def extract_prefix(id: str) -> str:
    """Extract type prefix from an ID."""

def compare_ids_by_timestamp(id1: str, id2: str) -> int:
    """Compare two IDs by their creation timestamp."""
```

---

## What This Task Should Do Instead

Since the core functionality exists, this task should:

1. **Verify completeness** - Ensure all needed functions are present
2. **Add any missing utilities** - If other tasks need additional helpers
3. **Add documentation** - Ensure docstrings are comprehensive
4. **Add test coverage** - Ensure the module is well-tested

---

## Implementation

### Verification Checklist

| Function | Status | Used By |
|----------|--------|---------|
| `generate_track_id()` | ✅ Exists | Task 001, Task 004 |
| `generate_sprint_id()` | ✅ Exists | Task 002, Task 004 |
| `generate_task_id()` | ✅ Exists | Task 003, Task 004 |
| `generate_id(type, timestamp)` | ✅ Exists | Migration tools |
| `is_valid_id(id)` | ✅ Exists | Validation |
| `is_ulid_format(id)` | ✅ Exists | Format detection |
| `extract_timestamp(id)` | ✅ Exists | Audit/display |
| `extract_prefix(id)` | ✅ Exists | Type detection |

### Potential Additions (Optional)

```python
# vibey/roadmap/id_generator.py - Optional additions

def generate_artifact_id() -> str:
    """
    Generate a unique artifact ID using ULID.

    Returns:
        str: Artifact ID in format "artifact_{ulid}"

    Example:
        >>> artifact_id = generate_artifact_id()
        >>> print(artifact_id)
        artifact_01JB3QVF8MART5KDLP9QWXYZ12
    """
    ulid = ULID()
    return f"artifact_{str(ulid)}"


def get_id_type(id: str) -> Optional[str]:
    """
    Get the type of an entity from its ID.

    Args:
        id: ID to check

    Returns:
        Type string ("track", "sprint", "task", "artifact") or None

    Example:
        >>> get_id_type("track_01JB3QVDZ8TRK9XN1FJFHGWPRM")
        "track"
        >>> get_id_type("invalid-id")
        None
    """
    if "_" not in id:
        return None

    prefix = id.split("_", 1)[0]
    valid_types = ["track", "sprint", "task", "artifact"]

    return prefix if prefix in valid_types else None


def id_to_filename(id: str) -> str:
    """
    Convert ID to filename format.

    Args:
        id: Entity ID

    Returns:
        Filename with .yaml extension

    Example:
        >>> id_to_filename("track_01JB3QVDZ8TRK9XN1FJFHGWPRM")
        "track_01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml"
    """
    return f"{id}.yaml"


def filename_to_id(filename: str) -> str:
    """
    Extract ID from filename.

    Args:
        filename: Filename (with or without path, with .yaml extension)

    Returns:
        Entity ID

    Example:
        >>> filename_to_id("track_01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml")
        "track_01JB3QVDZ8TRK9XN1FJFHGWPRM"
    """
    from pathlib import Path
    return Path(filename).stem
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/id_generator.py` | Add optional helper functions |
| `tests/roadmap/test_id_generator.py` | Add comprehensive tests |

---

## Testing Strategy

```python
# tests/roadmap/test_id_generator.py

import pytest
from datetime import datetime, timezone
from vibey.roadmap.id_generator import (
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
    generate_id,
    is_valid_id,
    is_ulid_format,
    extract_timestamp,
    extract_prefix,
    compare_ids_by_timestamp,
)


class TestIdGeneration:
    """Test ID generation functions."""

    def test_generate_track_id_format(self):
        """Track ID has correct format."""
        track_id = generate_track_id()
        assert track_id.startswith("track_")
        assert len(track_id) == 32  # "track_" (6) + ULID (26)
        assert is_valid_id(track_id)

    def test_generate_sprint_id_format(self):
        """Sprint ID has correct format."""
        sprint_id = generate_sprint_id()
        assert sprint_id.startswith("sprint_")
        assert len(sprint_id) == 33  # "sprint_" (7) + ULID (26)
        assert is_valid_id(sprint_id)

    def test_generate_task_id_format(self):
        """Task ID has correct format."""
        task_id = generate_task_id()
        assert task_id.startswith("task_")
        assert len(task_id) == 31  # "task_" (5) + ULID (26)
        assert is_valid_id(task_id)

    def test_ids_are_unique(self):
        """Generated IDs are unique."""
        ids = [generate_track_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_ids_are_sortable(self):
        """IDs are lexicographically sortable by time."""
        import time
        id1 = generate_track_id()
        time.sleep(0.01)
        id2 = generate_track_id()
        assert id1 < id2


class TestIdValidation:
    """Test ID validation functions."""

    def test_valid_track_id(self):
        """Valid track ID passes validation."""
        track_id = generate_track_id()
        assert is_valid_id(track_id)
        assert is_ulid_format(track_id)

    def test_invalid_id_formats(self):
        """Invalid formats rejected."""
        assert not is_valid_id("invalid")
        assert not is_valid_id("track-old-style")
        assert not is_valid_id("track_short")
        assert not is_valid_id("")

    def test_old_format_detection(self):
        """Old slug format detected as non-ULID."""
        assert not is_ulid_format("my-track")
        assert not is_ulid_format("sprint-1")
        assert not is_ulid_format("task-001")


class TestTimestampExtraction:
    """Test timestamp extraction."""

    def test_extract_timestamp(self):
        """Timestamp extracted correctly."""
        before = datetime.now(timezone.utc)
        track_id = generate_track_id()
        after = datetime.now(timezone.utc)

        ts = extract_timestamp(track_id)
        assert before <= ts <= after

    def test_extract_prefix(self):
        """Prefix extracted correctly."""
        assert extract_prefix(generate_track_id()) == "track"
        assert extract_prefix(generate_sprint_id()) == "sprint"
        assert extract_prefix(generate_task_id()) == "task"


class TestIdComparison:
    """Test ID comparison."""

    def test_compare_ids_by_timestamp(self):
        """IDs compare correctly by timestamp."""
        import time
        id1 = generate_track_id()
        time.sleep(0.01)
        id2 = generate_track_id()

        assert compare_ids_by_timestamp(id1, id2) == -1
        assert compare_ids_by_timestamp(id2, id1) == 1
        assert compare_ids_by_timestamp(id1, id1) == 0
```

---

## Success Criteria

- [ ] Verify `id_generator.py` has all needed functions
- [ ] Add any missing helper functions
- [ ] Ensure comprehensive test coverage
- [ ] Document module usage in docstrings
- [ ] Validate integration with Tasks 001-004

---

## Dependencies

None - This task is a foundation for other tasks.

---

## Notes

**This task is essentially complete!** The `id_generator.py` module already provides:

1. ✅ Track ID generation (`generate_track_id()`)
2. ✅ Sprint ID generation (`generate_sprint_id()`)
3. ✅ Task ID generation (`generate_task_id()`)
4. ✅ Generic ID generation (`generate_id()`)
5. ✅ Timestamp-based generation (`generate_id_from_timestamp()`)
6. ✅ ID validation (`is_valid_id()`, `is_ulid_format()`)
7. ✅ Timestamp extraction (`extract_timestamp()`)
8. ✅ Prefix extraction (`extract_prefix()`)
9. ✅ ID comparison (`compare_ids_by_timestamp()`)

The module is 341 lines with comprehensive docstrings and examples.

**Recommended action:** Mark this task as mostly complete, add comprehensive tests if missing, and optionally add artifact ID generation for future use.
