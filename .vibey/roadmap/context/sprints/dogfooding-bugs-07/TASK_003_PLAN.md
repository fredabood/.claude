# Task 003: Write JSONL Reader for Activity Queries

**Task ID:** dogfooding-bugs-07-task-003
**Bug Addressed:** #13 (Activity Log Not Migrated to JSONL Format)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The current `AuditTrailManager` loads the entire `audit-trail.yaml` file into memory for queries. With JSONL format, we need a reader that can:

1. Read events from time-bucketed JSONL files
2. Support filtering by object type, ID, date range
3. Stream large files without loading all into memory
4. Query across multiple month files

---

## Current State

**Current Implementation (audit_trail.py:156-170):**
```python
def _load_trail_from_yaml(self) -> dict:
    """Load trail data from YAML file."""
    if not self.audit_file.exists():
        return {"entries": []}

    with open(self.audit_file) as f:
        data = yaml.safe_load(f)

    return data if data else {"entries": []}
```

**Current Query Method (audit_trail.py:220-250):**
```python
def get_history(
    self,
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    limit: int = 50,
) -> List[AuditEntry]:
    """Get audit history with optional filters."""
    entries = self.trail.get("entries", [])

    if object_type:
        entries = [e for e in entries if e.get("object_type") == object_type]
    if object_id:
        entries = [e for e in entries if e.get("object_id") == object_id]

    # Sort by timestamp descending
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return [AuditEntry(**e) for e in entries[:limit]]
```

---

## Implementation

### 1. Create ActivityLogReader Class

```python
# vibey/operations/roadmap/jsonl_activity_log.py (add to existing file)

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional, List, Callable
import json


class ActivityLogReader:
    """
    Reads activity events from time-bucketed JSONL files.

    Supports streaming reads and filtering.
    """

    def __init__(self, activity_log_dir: Path):
        """
        Initialize reader.

        Args:
            activity_log_dir: Path to activity_log directory
        """
        self.activity_log_dir = activity_log_dir

    def _get_log_files(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Path]:
        """
        Get list of JSONL files in date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of JSONL file paths, sorted by date
        """
        if not self.activity_log_dir.exists():
            return []

        files = list(self.activity_log_dir.glob("*.jsonl"))

        # Parse dates from filenames
        dated_files = []
        for f in files:
            try:
                # Parse YYYY-MM.jsonl
                year, month = f.stem.split('-')
                file_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
                dated_files.append((file_date, f))
            except (ValueError, IndexError):
                continue  # Skip malformed filenames

        # Filter by date range
        if start_date:
            start_month = datetime(start_date.year, start_date.month, 1, tzinfo=timezone.utc)
            dated_files = [(d, f) for d, f in dated_files if d >= start_month]

        if end_date:
            end_month = datetime(end_date.year, end_date.month, 1, tzinfo=timezone.utc)
            dated_files = [(d, f) for d, f in dated_files if d <= end_month]

        # Sort by date
        dated_files.sort(key=lambda x: x[0])

        return [f for _, f in dated_files]

    def _read_file(self, file_path: Path) -> Iterator[ActivityEvent]:
        """
        Stream events from a single JSONL file.

        Args:
            file_path: Path to JSONL file

        Yields:
            ActivityEvent objects
        """
        if not file_path.exists():
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    event = ActivityEvent.from_json_line(line)
                    yield event
                except json.JSONDecodeError as e:
                    # Log warning but continue
                    import sys
                    print(f"Warning: Invalid JSON at {file_path}:{line_num}: {e}",
                          file=sys.stderr)
                    continue

    def stream_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        field: Optional[str] = None,
    ) -> Iterator[ActivityEvent]:
        """
        Stream events matching filters.

        Args:
            start_date: Start of date range
            end_date: End of date range
            object_type: Filter by object type (track, sprint, task, roadmap)
            object_id: Filter by object ID
            field: Filter by field name

        Yields:
            Matching ActivityEvent objects
        """
        files = self._get_log_files(start_date, end_date)

        for file_path in files:
            for event in self._read_file(file_path):
                # Apply filters
                if object_type and event.object_type != object_type:
                    continue
                if object_id and event.object_id != object_id:
                    continue
                if field and event.field != field:
                    continue

                # Check timestamp range
                if start_date or end_date:
                    try:
                        event_time = datetime.fromisoformat(
                            event.timestamp.replace('Z', '+00:00')
                        )
                        if start_date and event_time < start_date:
                            continue
                        if end_date and event_time > end_date:
                            continue
                    except ValueError:
                        continue  # Skip events with invalid timestamps

                yield event

    def get_history(
        self,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ActivityEvent]:
        """
        Get activity history with filters (matches AuditTrailManager API).

        Args:
            object_type: Filter by object type
            object_id: Filter by object ID
            limit: Maximum events to return
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of ActivityEvent objects, newest first
        """
        events = list(self.stream_events(
            start_date=start_date,
            end_date=end_date,
            object_type=object_type,
            object_id=object_id,
        ))

        # Sort by timestamp descending (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def get_object_history(
        self,
        object_type: str,
        object_id: str,
        limit: int = 50,
    ) -> List[ActivityEvent]:
        """
        Get history for a specific object.

        Args:
            object_type: Object type (track, sprint, task, roadmap)
            object_id: Object ID
            limit: Maximum events to return

        Returns:
            List of ActivityEvent objects, newest first
        """
        return self.get_history(
            object_type=object_type,
            object_id=object_id,
            limit=limit,
        )

    def get_recent_activity(
        self,
        limit: int = 50,
        days: int = 30,
    ) -> List[ActivityEvent]:
        """
        Get recent activity across all objects.

        Args:
            limit: Maximum events to return
            days: Number of days to look back

        Returns:
            List of ActivityEvent objects, newest first
        """
        from datetime import timedelta

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        return self.get_history(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    def count_events(
        self,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count events matching filters (without loading all into memory).

        Args:
            object_type: Filter by object type
            object_id: Filter by object ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Count of matching events
        """
        count = 0
        for _ in self.stream_events(
            start_date=start_date,
            end_date=end_date,
            object_type=object_type,
            object_id=object_id,
        ):
            count += 1
        return count
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/jsonl_activity_log.py` | Add `ActivityLogReader` class |

---

## Testing Strategy

```python
# tests/operations/roadmap/test_jsonl_reader.py

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta


class TestActivityLogReader:
    """Tests for ActivityLogReader class."""

    @pytest.fixture
    def populated_log_dir(self, tmp_path):
        """Create activity_log with sample data."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        log_dir = tmp_path / "activity_log"
        log_dir.mkdir()

        # November events
        nov_file = log_dir / "2025-11.jsonl"
        nov_events = [
            ActivityEvent(
                timestamp="2025-11-15T10:00:00+00:00",
                object_type="task",
                object_id="task_001",
                field="status",
                old_value="not_started",
                new_value="in_progress",
                changed_by="cli",
            ),
            ActivityEvent(
                timestamp="2025-11-16T10:00:00+00:00",
                object_type="sprint",
                object_id="sprint_001",
                field="status",
                old_value="not_started",
                new_value="in_progress",
                changed_by="cli",
            ),
        ]
        nov_file.write_text('\n'.join(e.to_json_line() for e in nov_events) + '\n')

        # December events
        dec_file = log_dir / "2025-12.jsonl"
        dec_events = [
            ActivityEvent(
                timestamp="2025-12-01T10:00:00+00:00",
                object_type="task",
                object_id="task_001",
                field="status",
                old_value="in_progress",
                new_value="completed",
                changed_by="cli",
            ),
        ]
        dec_file.write_text('\n'.join(e.to_json_line() for e in dec_events) + '\n')

        return log_dir

    def test_get_log_files_returns_all(self, populated_log_dir):
        """Reader finds all JSONL files."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        files = reader._get_log_files()

        assert len(files) == 2
        assert any("2025-11" in str(f) for f in files)
        assert any("2025-12" in str(f) for f in files)

    def test_get_log_files_filters_by_date(self, populated_log_dir):
        """Reader filters files by date range."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)

        # Only November
        files = reader._get_log_files(
            start_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 11, 30, tzinfo=timezone.utc),
        )

        assert len(files) == 1
        assert "2025-11" in str(files[0])

    def test_stream_events_all(self, populated_log_dir):
        """stream_events returns all events."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        events = list(reader.stream_events())

        assert len(events) == 3

    def test_stream_events_filter_by_object_type(self, populated_log_dir):
        """stream_events filters by object_type."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        events = list(reader.stream_events(object_type="task"))

        assert len(events) == 2
        assert all(e.object_type == "task" for e in events)

    def test_stream_events_filter_by_object_id(self, populated_log_dir):
        """stream_events filters by object_id."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        events = list(reader.stream_events(object_id="sprint_001"))

        assert len(events) == 1
        assert events[0].object_type == "sprint"

    def test_get_history_returns_newest_first(self, populated_log_dir):
        """get_history returns events sorted by timestamp descending."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        events = reader.get_history(limit=10)

        # Verify descending order
        timestamps = [e.timestamp for e in events]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_history_respects_limit(self, populated_log_dir):
        """get_history respects limit parameter."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        events = reader.get_history(limit=1)

        assert len(events) == 1

    def test_get_object_history(self, populated_log_dir):
        """get_object_history returns history for specific object."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)
        events = reader.get_object_history("task", "task_001")

        assert len(events) == 2
        assert all(e.object_id == "task_001" for e in events)

    def test_count_events(self, populated_log_dir):
        """count_events returns correct count."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log_dir)

        assert reader.count_events() == 3
        assert reader.count_events(object_type="task") == 2
        assert reader.count_events(object_type="sprint") == 1

    def test_handles_empty_directory(self, tmp_path):
        """Reader handles empty or missing directory."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(tmp_path / "nonexistent")

        assert list(reader.stream_events()) == []
        assert reader.get_history() == []
        assert reader.count_events() == 0

    def test_handles_malformed_json(self, tmp_path):
        """Reader skips malformed JSON lines."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        log_dir = tmp_path / "activity_log"
        log_dir.mkdir()

        # File with one valid and one invalid line
        (log_dir / "2025-11.jsonl").write_text(
            '{"timestamp":"2025-11-15T10:00:00+00:00","object_type":"task","object_id":"task_001","field":"status","old_value":"a","new_value":"b","changed_by":"cli","reason":null,"commit":null,"source":"manual"}\n'
            'not valid json\n'
            '{"timestamp":"2025-11-16T10:00:00+00:00","object_type":"task","object_id":"task_002","field":"status","old_value":"a","new_value":"b","changed_by":"cli","reason":null,"commit":null,"source":"manual"}\n'
        )

        reader = ActivityLogReader(log_dir)
        events = list(reader.stream_events())

        # Should get 2 valid events, skip the bad line
        assert len(events) == 2
```

---

## Success Criteria

- [ ] `ActivityLogReader` class created
- [ ] `_get_log_files()` returns files filtered by date range
- [ ] `stream_events()` yields events without loading all into memory
- [ ] Filtering works by object_type, object_id, field, date range
- [ ] `get_history()` matches AuditTrailManager API
- [ ] `get_object_history()` convenience method works
- [ ] `get_recent_activity()` returns recent events
- [ ] `count_events()` counts without loading all data
- [ ] Malformed JSON lines are skipped with warning
- [ ] All tests pass

---

## Dependencies

- Task 001 (directory structure)
- Task 002 (writer creates files)

---

## Notes

### Streaming Benefits

The reader uses generators to avoid loading entire files into memory:
- Large log files can be processed efficiently
- Memory usage stays constant regardless of log size
- Filters are applied during streaming

### Query Patterns

Common query patterns supported:
1. **Recent activity**: `get_recent_activity(days=7)`
2. **Object history**: `get_object_history("task", "task_123")`
3. **Type filtering**: `get_history(object_type="sprint")`
4. **Date range**: `get_history(start_date=..., end_date=...)`
5. **Event count**: `count_events(object_type="task")`
