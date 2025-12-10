# Task 002: Write JSONL Writer for Activity Events

**Task ID:** dogfooding-bugs-07-task-002
**Bug Addressed:** #13 (Activity Log Not Migrated to JSONL Format)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The current `AuditTrailManager` in `audit_trail.py` uses `yaml.safe_dump()` to write all events to a monolithic YAML file. This needs to be replaced with a JSONL writer that:

1. Writes events to time-bucketed files (`YYYY-MM.jsonl`)
2. Appends each event as a single JSON line
3. Handles concurrent writes safely
4. Maintains backward compatibility during migration

---

## Current State

**Current Implementation (audit_trail.py:192-195):**
```python
def _save_trail(self) -> None:
    """Save the audit trail to YAML file."""
    with open(self.audit_file, 'w') as f:
        yaml.safe_dump(self.trail, f, default_flow_style=False, sort_keys=False)
```

**Current AuditEntry Structure (audit_trail.py:40-60):**
```python
@dataclass
class AuditEntry:
    timestamp: str
    object_type: str  # "track", "sprint", "task", "roadmap"
    object_id: str
    field: str
    old_value: Any
    new_value: Any
    changed_by: str
    reason: Optional[str] = None
    commit: Optional[str] = None
    source: str = "manual"
```

---

## Implementation

### 1. Create ActivityLogWriter Class

```python
# vibey/operations/roadmap/jsonl_activity_log.py

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import fcntl  # For file locking on Unix


@dataclass
class ActivityEvent:
    """
    Single activity event for JSONL storage.

    Mirrors AuditEntry but optimized for JSONL format.
    """
    timestamp: str
    object_type: str
    object_id: str
    field: str
    old_value: Any
    new_value: Any
    changed_by: str
    reason: Optional[str] = None
    commit: Optional[str] = None
    source: str = "manual"

    def to_json_line(self) -> str:
        """Convert to JSON line (without trailing newline)."""
        return json.dumps(asdict(self), ensure_ascii=False, separators=(',', ':'))

    @classmethod
    def from_json_line(cls, line: str) -> 'ActivityEvent':
        """Parse from JSON line."""
        data = json.loads(line.strip())
        return cls(**data)

    @classmethod
    def from_audit_entry(cls, entry: 'AuditEntry') -> 'ActivityEvent':
        """Convert from legacy AuditEntry."""
        return cls(
            timestamp=entry.timestamp,
            object_type=entry.object_type,
            object_id=entry.object_id,
            field=entry.field,
            old_value=entry.old_value,
            new_value=entry.new_value,
            changed_by=entry.changed_by,
            reason=entry.reason,
            commit=entry.commit,
            source=entry.source,
        )


class ActivityLogWriter:
    """
    Writes activity events to time-bucketed JSONL files.

    File format: .vibey/roadmap/activity_log/YYYY-MM.jsonl
    Each line is a complete JSON object representing one event.
    """

    def __init__(self, activity_log_dir: Path):
        """
        Initialize writer.

        Args:
            activity_log_dir: Path to activity_log directory
        """
        self.activity_log_dir = activity_log_dir
        self.activity_log_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_for_timestamp(self, timestamp: str) -> Path:
        """
        Get JSONL file path for a given timestamp.

        Args:
            timestamp: ISO format timestamp (e.g., "2025-11-15T10:30:00+00:00")

        Returns:
            Path to JSONL file for that month
        """
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Fallback to current time if timestamp is invalid
            dt = datetime.now(timezone.utc)

        filename = f"{dt.year}-{dt.month:02d}.jsonl"
        return self.activity_log_dir / filename

    def _get_current_file(self) -> Path:
        """Get JSONL file for current month."""
        now = datetime.now(timezone.utc)
        filename = f"{now.year}-{now.month:02d}.jsonl"
        return self.activity_log_dir / filename

    def write_event(self, event: ActivityEvent) -> None:
        """
        Write a single event to the appropriate JSONL file.

        Uses file locking for concurrent write safety.

        Args:
            event: ActivityEvent to write
        """
        file_path = self._get_file_for_timestamp(event.timestamp)
        json_line = event.to_json_line()

        # Append with file locking
        with open(file_path, 'a', encoding='utf-8') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(json_line + '\n')
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def write_events(self, events: list[ActivityEvent]) -> None:
        """
        Write multiple events to appropriate JSONL files.

        Events are grouped by month for efficient writes.

        Args:
            events: List of ActivityEvents to write
        """
        # Group events by target file
        events_by_file: dict[Path, list[ActivityEvent]] = {}
        for event in events:
            file_path = self._get_file_for_timestamp(event.timestamp)
            if file_path not in events_by_file:
                events_by_file[file_path] = []
            events_by_file[file_path].append(event)

        # Write each group
        for file_path, file_events in events_by_file.items():
            lines = [e.to_json_line() + '\n' for e in file_events]

            with open(file_path, 'a', encoding='utf-8') as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    f.writelines(lines)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def log_change(
        self,
        object_type: str,
        object_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        changed_by: str = "cli",
        reason: Optional[str] = None,
        commit: Optional[str] = None,
        source: str = "manual",
    ) -> ActivityEvent:
        """
        Log a change event (convenience method matching AuditTrailManager API).

        Args:
            object_type: Type of object changed (track, sprint, task, roadmap)
            object_id: ID of the object
            field: Field that was changed
            old_value: Previous value
            new_value: New value
            changed_by: Who made the change
            reason: Optional reason for change
            commit: Optional git commit hash
            source: Source of change (manual, cli, api, etc.)

        Returns:
            The created ActivityEvent
        """
        event = ActivityEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            object_type=object_type,
            object_id=object_id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
            commit=commit,
            source=source,
        )

        self.write_event(event)
        return event
```

### 2. Add Cross-Platform File Locking

```python
# vibey/operations/roadmap/jsonl_activity_log.py (continued)

import sys

# Cross-platform file locking
if sys.platform == 'win32':
    import msvcrt

    def _lock_file(f):
        """Lock file on Windows."""
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(f):
        """Unlock file on Windows."""
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock_file(f):
        """Lock file on Unix."""
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock_file(f):
        """Unlock file on Unix."""
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/jsonl_activity_log.py` | NEW: Create ActivityEvent dataclass and ActivityLogWriter class |

---

## Testing Strategy

```python
# tests/operations/roadmap/test_jsonl_writer.py

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone


class TestActivityEvent:
    """Tests for ActivityEvent dataclass."""

    def test_to_json_line(self):
        """Event serializes to valid JSON."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        event = ActivityEvent(
            timestamp="2025-11-15T10:30:00+00:00",
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
        )

        json_line = event.to_json_line()
        parsed = json.loads(json_line)

        assert parsed["object_type"] == "task"
        assert parsed["object_id"] == "task_123"
        assert parsed["new_value"] == "in_progress"

    def test_from_json_line(self):
        """Event deserializes from JSON line."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        line = '{"timestamp":"2025-11-15T10:30:00+00:00","object_type":"task","object_id":"task_123","field":"status","old_value":"not_started","new_value":"in_progress","changed_by":"cli","reason":null,"commit":null,"source":"manual"}'

        event = ActivityEvent.from_json_line(line)

        assert event.object_type == "task"
        assert event.object_id == "task_123"
        assert event.new_value == "in_progress"

    def test_roundtrip(self):
        """Event survives serialization roundtrip."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        original = ActivityEvent(
            timestamp="2025-11-15T10:30:00+00:00",
            object_type="sprint",
            object_id="sprint_456",
            field="name",
            old_value="Old Name",
            new_value="New Name",
            changed_by="user",
            reason="Clarification",
        )

        json_line = original.to_json_line()
        restored = ActivityEvent.from_json_line(json_line)

        assert restored.timestamp == original.timestamp
        assert restored.object_type == original.object_type
        assert restored.reason == original.reason


class TestActivityLogWriter:
    """Tests for ActivityLogWriter class."""

    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create temp activity_log directory."""
        log_dir = tmp_path / "activity_log"
        log_dir.mkdir()
        return log_dir

    def test_write_event_creates_file(self, temp_log_dir):
        """Writing event creates JSONL file."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(temp_log_dir)
        event = ActivityEvent(
            timestamp="2025-11-15T10:30:00+00:00",
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
        )

        writer.write_event(event)

        expected_file = temp_log_dir / "2025-11.jsonl"
        assert expected_file.exists()

    def test_write_event_appends(self, temp_log_dir):
        """Multiple events append to same file."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(temp_log_dir)

        for i in range(3):
            event = ActivityEvent(
                timestamp="2025-11-15T10:30:00+00:00",
                object_type="task",
                object_id=f"task_{i}",
                field="status",
                old_value="a",
                new_value="b",
                changed_by="cli",
            )
            writer.write_event(event)

        lines = (temp_log_dir / "2025-11.jsonl").read_text().strip().split('\n')
        assert len(lines) == 3

    def test_events_grouped_by_month(self, temp_log_dir):
        """Events go to different files by month."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(temp_log_dir)

        # November event
        writer.write_event(ActivityEvent(
            timestamp="2025-11-15T10:30:00+00:00",
            object_type="task",
            object_id="task_1",
            field="status",
            old_value="a",
            new_value="b",
            changed_by="cli",
        ))

        # December event
        writer.write_event(ActivityEvent(
            timestamp="2025-12-01T10:30:00+00:00",
            object_type="task",
            object_id="task_2",
            field="status",
            old_value="a",
            new_value="b",
            changed_by="cli",
        ))

        assert (temp_log_dir / "2025-11.jsonl").exists()
        assert (temp_log_dir / "2025-12.jsonl").exists()

    def test_log_change_convenience_method(self, temp_log_dir):
        """log_change() creates and writes event."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogWriter

        writer = ActivityLogWriter(temp_log_dir)

        event = writer.log_change(
            object_type="sprint",
            object_id="sprint_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
            reason="Starting work",
        )

        assert event.object_type == "sprint"
        assert event.reason == "Starting work"

        # File should exist with event
        files = list(temp_log_dir.glob("*.jsonl"))
        assert len(files) == 1

    def test_write_events_batch(self, temp_log_dir):
        """write_events() handles batch writes."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(temp_log_dir)
        events = [
            ActivityEvent(
                timestamp="2025-11-15T10:30:00+00:00",
                object_type="task",
                object_id=f"task_{i}",
                field="status",
                old_value="a",
                new_value="b",
                changed_by="cli",
            )
            for i in range(100)
        ]

        writer.write_events(events)

        lines = (temp_log_dir / "2025-11.jsonl").read_text().strip().split('\n')
        assert len(lines) == 100
```

---

## Success Criteria

- [ ] `ActivityEvent` dataclass created with `to_json_line()` and `from_json_line()`
- [ ] `ActivityLogWriter` class writes events to correct month file
- [ ] Events are appended (not overwritten)
- [ ] Cross-platform file locking implemented
- [ ] `log_change()` convenience method matches AuditTrailManager API
- [ ] Batch writes supported via `write_events()`
- [ ] All tests pass

---

## Dependencies

- Task 001 (directory structure in place)

---

## Notes

### JSONL Format Benefits

1. **Append-only** - New events added without reading entire file
2. **Line-based** - Easy streaming reads for large files
3. **Simple parsing** - Standard JSON per line
4. **Corruption resistant** - One bad line doesn't break file
5. **Efficient** - No indentation overhead like YAML

### Example JSONL Output

```jsonl
{"timestamp":"2025-11-15T10:30:00+00:00","object_type":"task","object_id":"task_123","field":"status","old_value":"not_started","new_value":"in_progress","changed_by":"cli","reason":null,"commit":null,"source":"manual"}
{"timestamp":"2025-11-15T10:31:00+00:00","object_type":"task","object_id":"task_123","field":"status","old_value":"in_progress","new_value":"completed","changed_by":"cli","reason":"Work finished","commit":"abc123","source":"manual"}
```
