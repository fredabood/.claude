# Task 006: Add Tests for JSONL Activity Log

**Task ID:** dogfooding-bugs-07-task-006
**Bug Addressed:** #13 (Activity Log Not Migrated to JSONL Format)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

After implementing the JSONL activity log system (Tasks 001-005), comprehensive tests are needed to:

1. Verify all components work correctly
2. Ensure backward compatibility
3. Provide regression protection
4. Document expected behavior

---

## Test Categories

### 1. Unit Tests - ActivityEvent

```python
# tests/operations/roadmap/test_activity_event.py

import pytest
import json
from datetime import datetime, timezone


class TestActivityEvent:
    """Tests for ActivityEvent dataclass."""

    def test_create_with_required_fields(self):
        """ActivityEvent can be created with required fields."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        event = ActivityEvent(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
        )

        assert event.timestamp == "2025-11-15T10:00:00+00:00"
        assert event.object_type == "task"
        assert event.object_id == "task_123"
        assert event.reason is None  # Optional

    def test_to_json_line_format(self):
        """to_json_line produces valid JSON without newlines."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        event = ActivityEvent(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
        )

        json_line = event.to_json_line()

        # Should be valid JSON
        parsed = json.loads(json_line)
        assert parsed["object_type"] == "task"

        # Should not contain newlines
        assert '\n' not in json_line

    def test_from_json_line_parsing(self):
        """from_json_line parses JSON correctly."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        line = '{"timestamp":"2025-11-15T10:00:00+00:00","object_type":"task","object_id":"task_123","field":"status","old_value":"not_started","new_value":"in_progress","changed_by":"cli","reason":null,"commit":null,"source":"manual"}'

        event = ActivityEvent.from_json_line(line)

        assert event.object_type == "task"
        assert event.object_id == "task_123"
        assert event.reason is None

    def test_roundtrip_preserves_data(self):
        """Serialization roundtrip preserves all data."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        original = ActivityEvent(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="sprint",
            object_id="sprint_456",
            field="name",
            old_value="Old Name",
            new_value="New Name",
            changed_by="user",
            reason="Clarification",
            commit="abc123",
            source="api",
        )

        restored = ActivityEvent.from_json_line(original.to_json_line())

        assert restored.timestamp == original.timestamp
        assert restored.object_type == original.object_type
        assert restored.object_id == original.object_id
        assert restored.field == original.field
        assert restored.old_value == original.old_value
        assert restored.new_value == original.new_value
        assert restored.changed_by == original.changed_by
        assert restored.reason == original.reason
        assert restored.commit == original.commit
        assert restored.source == original.source

    def test_handles_complex_values(self):
        """Handles complex old_value/new_value (lists, dicts)."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        event = ActivityEvent(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="task",
            object_id="task_123",
            field="metadata",
            old_value={"priority": "low", "tags": ["bug"]},
            new_value={"priority": "high", "tags": ["bug", "critical"]},
            changed_by="cli",
        )

        restored = ActivityEvent.from_json_line(event.to_json_line())

        assert restored.old_value["priority"] == "low"
        assert restored.new_value["priority"] == "high"
        assert "critical" in restored.new_value["tags"]

    def test_handles_unicode(self):
        """Handles unicode characters in values."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        event = ActivityEvent(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="task",
            object_id="task_123",
            field="name",
            old_value="Test",
            new_value="Tëst with émojis 🎉",
            changed_by="用户",
        )

        restored = ActivityEvent.from_json_line(event.to_json_line())

        assert restored.new_value == "Tëst with émojis 🎉"
        assert restored.changed_by == "用户"


class TestActivityEventFromAuditEntry:
    """Tests for converting from AuditEntry."""

    def test_from_audit_entry(self):
        """ActivityEvent can be created from AuditEntry."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent
        from vibey.operations.roadmap.audit_trail import AuditEntry

        audit_entry = AuditEntry(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
            reason="Starting work",
            commit="abc123",
            source="manual",
        )

        event = ActivityEvent.from_audit_entry(audit_entry)

        assert event.timestamp == audit_entry.timestamp
        assert event.object_type == audit_entry.object_type
        assert event.reason == audit_entry.reason
```

### 2. Unit Tests - ActivityLogWriter

```python
# tests/operations/roadmap/test_activity_log_writer.py

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone


class TestActivityLogWriter:
    """Tests for ActivityLogWriter class."""

    @pytest.fixture
    def log_dir(self, tmp_path):
        """Create empty activity_log directory."""
        log_dir = tmp_path / "activity_log"
        log_dir.mkdir()
        return log_dir

    def test_init_creates_directory(self, tmp_path):
        """Writer creates directory if missing."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogWriter

        log_dir = tmp_path / "new_log_dir"
        writer = ActivityLogWriter(log_dir)

        assert log_dir.exists()

    def test_write_event_creates_file(self, log_dir):
        """Writing event creates JSONL file."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(log_dir)
        event = ActivityEvent(
            timestamp="2025-11-15T10:00:00+00:00",
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="a",
            new_value="b",
            changed_by="cli",
        )

        writer.write_event(event)

        expected = log_dir / "2025-11.jsonl"
        assert expected.exists()

    def test_write_event_appends(self, log_dir):
        """Multiple writes append to same file."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(log_dir)

        for i in range(5):
            event = ActivityEvent(
                timestamp="2025-11-15T10:00:00+00:00",
                object_type="task",
                object_id=f"task_{i}",
                field="status",
                old_value="a",
                new_value="b",
                changed_by="cli",
            )
            writer.write_event(event)

        lines = (log_dir / "2025-11.jsonl").read_text().strip().split('\n')
        assert len(lines) == 5

    def test_events_grouped_by_month(self, log_dir):
        """Events go to correct month files."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(log_dir)

        # Events from different months
        months = [
            ("2025-10-15T10:00:00+00:00", "2025-10.jsonl"),
            ("2025-11-15T10:00:00+00:00", "2025-11.jsonl"),
            ("2025-12-15T10:00:00+00:00", "2025-12.jsonl"),
        ]

        for timestamp, expected_file in months:
            event = ActivityEvent(
                timestamp=timestamp,
                object_type="task",
                object_id="task_1",
                field="status",
                old_value="a",
                new_value="b",
                changed_by="cli",
            )
            writer.write_event(event)

        for _, expected_file in months:
            assert (log_dir / expected_file).exists()

    def test_log_change_convenience(self, log_dir):
        """log_change creates timestamp automatically."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogWriter

        writer = ActivityLogWriter(log_dir)
        event = writer.log_change(
            object_type="sprint",
            object_id="sprint_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
        )

        # Should have current timestamp
        assert event.timestamp is not None
        assert "2025" in event.timestamp  # Current year

    def test_write_events_batch(self, log_dir):
        """write_events handles batch efficiently."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(log_dir)
        events = [
            ActivityEvent(
                timestamp="2025-11-15T10:00:00+00:00",
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

        lines = (log_dir / "2025-11.jsonl").read_text().strip().split('\n')
        assert len(lines) == 100

    def test_each_line_is_valid_json(self, log_dir):
        """Each line in file is valid JSON."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityEvent
        )

        writer = ActivityLogWriter(log_dir)

        for i in range(3):
            event = ActivityEvent(
                timestamp="2025-11-15T10:00:00+00:00",
                object_type="task",
                object_id=f"task_{i}",
                field="status",
                old_value="a",
                new_value="b",
                changed_by="cli",
            )
            writer.write_event(event)

        for line in (log_dir / "2025-11.jsonl").read_text().strip().split('\n'):
            parsed = json.loads(line)
            assert "object_type" in parsed
```

### 3. Unit Tests - ActivityLogReader

```python
# tests/operations/roadmap/test_activity_log_reader.py

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta


class TestActivityLogReader:
    """Tests for ActivityLogReader class."""

    @pytest.fixture
    def populated_log(self, tmp_path):
        """Create activity_log with test data."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityEvent

        log_dir = tmp_path / "activity_log"
        log_dir.mkdir()

        # November data
        nov_events = [
            ActivityEvent(
                timestamp="2025-11-10T10:00:00+00:00",
                object_type="task",
                object_id="task_001",
                field="status",
                old_value="not_started",
                new_value="in_progress",
                changed_by="cli",
            ),
            ActivityEvent(
                timestamp="2025-11-15T10:00:00+00:00",
                object_type="sprint",
                object_id="sprint_001",
                field="status",
                old_value="not_started",
                new_value="in_progress",
                changed_by="cli",
            ),
            ActivityEvent(
                timestamp="2025-11-20T10:00:00+00:00",
                object_type="task",
                object_id="task_001",
                field="status",
                old_value="in_progress",
                new_value="completed",
                changed_by="cli",
            ),
        ]
        (log_dir / "2025-11.jsonl").write_text(
            '\n'.join(e.to_json_line() for e in nov_events) + '\n'
        )

        # December data
        dec_events = [
            ActivityEvent(
                timestamp="2025-12-01T10:00:00+00:00",
                object_type="track",
                object_id="track_001",
                field="status",
                old_value="in_progress",
                new_value="completed",
                changed_by="cli",
            ),
        ]
        (log_dir / "2025-12.jsonl").write_text(
            '\n'.join(e.to_json_line() for e in dec_events) + '\n'
        )

        return log_dir

    def test_stream_all_events(self, populated_log):
        """stream_events yields all events."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)
        events = list(reader.stream_events())

        assert len(events) == 4

    def test_filter_by_object_type(self, populated_log):
        """Filter events by object_type."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)

        task_events = list(reader.stream_events(object_type="task"))
        sprint_events = list(reader.stream_events(object_type="sprint"))

        assert len(task_events) == 2
        assert len(sprint_events) == 1

    def test_filter_by_object_id(self, populated_log):
        """Filter events by object_id."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)
        events = list(reader.stream_events(object_id="task_001"))

        assert len(events) == 2

    def test_filter_by_date_range(self, populated_log):
        """Filter events by date range."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)
        events = list(reader.stream_events(
            start_date=datetime(2025, 11, 12, tzinfo=timezone.utc),
            end_date=datetime(2025, 11, 25, tzinfo=timezone.utc),
        ))

        # Should get Nov 15 and Nov 20 events
        assert len(events) == 2

    def test_get_history_sorted_descending(self, populated_log):
        """get_history returns newest first."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)
        events = reader.get_history()

        timestamps = [e.timestamp for e in events]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_history_respects_limit(self, populated_log):
        """get_history respects limit."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)
        events = reader.get_history(limit=2)

        assert len(events) == 2

    def test_get_object_history(self, populated_log):
        """get_object_history returns specific object's events."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)
        events = reader.get_object_history("task", "task_001")

        assert len(events) == 2
        assert all(e.object_id == "task_001" for e in events)

    def test_count_events(self, populated_log):
        """count_events returns correct count."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(populated_log)

        assert reader.count_events() == 4
        assert reader.count_events(object_type="task") == 2

    def test_handles_empty_directory(self, tmp_path):
        """Handles missing/empty directory gracefully."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        reader = ActivityLogReader(tmp_path / "nonexistent")

        assert list(reader.stream_events()) == []
        assert reader.get_history() == []
        assert reader.count_events() == 0

    def test_skips_malformed_lines(self, tmp_path):
        """Skips malformed JSON lines."""
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader

        log_dir = tmp_path / "activity_log"
        log_dir.mkdir()

        (log_dir / "2025-11.jsonl").write_text(
            '{"timestamp":"2025-11-15T10:00:00+00:00","object_type":"task","object_id":"task_001","field":"status","old_value":"a","new_value":"b","changed_by":"cli","reason":null,"commit":null,"source":"manual"}\n'
            'invalid json line\n'
            '{"timestamp":"2025-11-16T10:00:00+00:00","object_type":"task","object_id":"task_002","field":"status","old_value":"a","new_value":"b","changed_by":"cli","reason":null,"commit":null,"source":"manual"}\n'
        )

        reader = ActivityLogReader(log_dir)
        events = list(reader.stream_events())

        assert len(events) == 2  # Skipped the bad line
```

### 4. Integration Tests

```python
# tests/operations/roadmap/test_activity_log_integration.py

import pytest
from pathlib import Path


class TestActivityLogIntegration:
    """Integration tests for full activity log system."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create test project structure."""
        (tmp_path / ".vibey" / "roadmap" / "activity_log").mkdir(parents=True)
        return tmp_path

    def test_write_then_read(self, project):
        """Events can be written and read back."""
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter, ActivityLogReader
        )

        log_dir = project / ".vibey" / "roadmap" / "activity_log"

        # Write
        writer = ActivityLogWriter(log_dir)
        writer.log_change(
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="test",
        )

        # Read
        reader = ActivityLogReader(log_dir)
        events = reader.get_history()

        assert len(events) == 1
        assert events[0].object_id == "task_123"

    def test_audit_trail_manager_integration(self, project):
        """AuditTrailManager works with JSONL backend."""
        from vibey.operations.roadmap.audit_trail import AuditTrailManager

        manager = AuditTrailManager(project)

        # Log some changes
        manager.log_change("task", "task_1", "status", "a", "b", "test")
        manager.log_change("task", "task_2", "status", "a", "b", "test")
        manager.log_change("sprint", "sprint_1", "status", "a", "b", "test")

        # Query back
        all_entries = manager.get_history()
        task_entries = manager.get_history(object_type="task")

        assert len(all_entries) == 3
        assert len(task_entries) == 2

    def test_unified_activity_log_integration(self, project):
        """UnifiedActivityLog works with JSONL backend."""
        from vibey.operations.roadmap.activity_log import UnifiedActivityLog

        log = UnifiedActivityLog(project)

        # Use high-level methods
        log.log_task_started("task_123")
        log.log_task_completed("task_123")

        # Query back
        history = log.get_task_history("task_123")

        assert len(history) == 2

    def test_concurrent_writes(self, project):
        """Handles concurrent writes safely."""
        import threading
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogWriter

        log_dir = project / ".vibey" / "roadmap" / "activity_log"
        writer = ActivityLogWriter(log_dir)

        def write_events(thread_id):
            for i in range(10):
                writer.log_change(
                    object_type="task",
                    object_id=f"task_{thread_id}_{i}",
                    field="status",
                    old_value="a",
                    new_value="b",
                    changed_by=f"thread_{thread_id}",
                )

        threads = [
            threading.Thread(target=write_events, args=(i,))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Count events
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader
        reader = ActivityLogReader(log_dir)

        assert reader.count_events() == 50  # 5 threads * 10 events


class TestMigrationIntegration:
    """Integration tests for migration process."""

    @pytest.fixture
    def project_with_yaml(self, tmp_path):
        """Create project with audit-trail.yaml."""
        import yaml

        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        yaml_data = {
            "entries": [
                {
                    "timestamp": "2025-11-15T10:00:00+00:00",
                    "object_type": "task",
                    "object_id": "task_001",
                    "field": "status",
                    "old_value": "not_started",
                    "new_value": "in_progress",
                    "changed_by": "cli",
                    "reason": None,
                    "commit": None,
                    "source": "manual",
                },
            ]
        }

        with open(roadmap_dir / "audit-trail.yaml", 'w') as f:
            yaml.safe_dump(yaml_data, f)

        return tmp_path

    def test_full_migration_workflow(self, project_with_yaml):
        """Full migration from YAML to JSONL."""
        from vibey.operations.roadmap.migrate_activity_log import ActivityLogMigrator

        migrator = ActivityLogMigrator(project_with_yaml)

        # Analyze
        analysis = migrator.analyze()
        assert analysis["total_entries"] == 1

        # Migrate
        report = migrator.migrate(dry_run=False)
        assert report.is_success()

        # Verify
        result = migrator.verify()
        assert result["match"] is True

        # Read back
        from vibey.operations.roadmap.jsonl_activity_log import ActivityLogReader
        reader = ActivityLogReader(
            project_with_yaml / ".vibey" / "roadmap" / "activity_log"
        )
        events = reader.get_history()
        assert len(events) == 1
        assert events[0].object_id == "task_001"
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/operations/roadmap/test_activity_event.py` | ActivityEvent tests |
| `tests/operations/roadmap/test_activity_log_writer.py` | Writer tests |
| `tests/operations/roadmap/test_activity_log_reader.py` | Reader tests |
| `tests/operations/roadmap/test_activity_log_integration.py` | Integration tests |

---

## Success Criteria

- [ ] All ActivityEvent tests pass
- [ ] All ActivityLogWriter tests pass
- [ ] All ActivityLogReader tests pass
- [ ] All integration tests pass
- [ ] Migration tests pass
- [ ] Concurrent write tests pass
- [ ] Edge case tests pass (empty, malformed, unicode)
- [ ] Test coverage > 90% for JSONL modules
- [ ] Tests run in CI pipeline

---

## Dependencies

- Tasks 001-005 (all implementation complete)

---

## Notes

### Test Organization

```
tests/operations/roadmap/
├── test_activity_event.py          # Unit: ActivityEvent dataclass
├── test_activity_log_writer.py     # Unit: ActivityLogWriter
├── test_activity_log_reader.py     # Unit: ActivityLogReader
├── test_activity_log_integration.py # Integration: Full system
├── test_migrate_activity_log.py    # Unit: Migration (Task 004)
└── test_audit_trail_jsonl.py       # Unit: Updated AuditTrailManager
```

### Running Tests

```bash
# Run all activity log tests
pytest tests/operations/roadmap/test_activity*.py -v

# Run with coverage
pytest tests/operations/roadmap/test_activity*.py --cov=vibey.operations.roadmap.jsonl_activity_log --cov-report=term-missing

# Run specific test class
pytest tests/operations/roadmap/test_activity_log_writer.py::TestActivityLogWriter -v
```

### Coverage Goals

| Module | Target |
|--------|--------|
| `jsonl_activity_log.py` | > 95% |
| `migrate_activity_log.py` | > 90% |
| `audit_trail.py` (JSONL parts) | > 90% |
