# Task 005: Update All Activity Log Consumers

**Task ID:** dogfooding-bugs-07-task-005
**Bug Addressed:** #13 (Activity Log Not Migrated to JSONL Format)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

After implementing the JSONL writer and reader (Tasks 002-003), all code that uses the activity log must be updated to use the new format. The main consumers are:

1. `AuditTrailManager` in `audit_trail.py` - core audit logging
2. `UnifiedActivityLog` in `activity_log.py` - wrapper for higher-level operations
3. CLI commands that display activity history
4. Any other code that reads/writes audit data

---

## Current State

**Current Architecture:**
```
UnifiedActivityLog (activity_log.py)
    └── AuditTrailManager (audit_trail.py)
            └── audit-trail.yaml (YAML file)
```

**Target Architecture:**
```
UnifiedActivityLog (activity_log.py)
    └── ActivityLogWriter/Reader (jsonl_activity_log.py)
            └── activity_log/YYYY-MM.jsonl (JSONL files)
```

---

## Implementation

### 1. Update AuditTrailManager

The `AuditTrailManager` class needs to be updated to use JSONL instead of YAML. We have two options:

**Option A: Replace AuditTrailManager internals (Recommended)**
```python
# vibey/operations/roadmap/audit_trail.py

class AuditTrailManager:
    """
    Manages audit trail for roadmap changes.

    Now uses JSONL format for storage.
    """

    def __init__(self, root_dir: Path, warn_on_duplicate: bool = True):
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.roadmap_dir = self.vibey_dir / "roadmap"

        # NEW: Use JSONL activity log
        self.activity_log_dir = self.roadmap_dir / "activity_log"

        # Import JSONL classes
        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter,
            ActivityLogReader,
        )

        self._writer = ActivityLogWriter(self.activity_log_dir)
        self._reader = ActivityLogReader(self.activity_log_dir)

        # DEPRECATED: Keep for migration period
        self.audit_file = self.roadmap_dir / "audit-trail.yaml"

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
    ) -> 'AuditEntry':
        """
        Log a change to the audit trail.

        Now writes to JSONL format.
        """
        # Use JSONL writer
        event = self._writer.log_change(
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

        # Convert to AuditEntry for backward compatibility
        return AuditEntry(
            timestamp=event.timestamp,
            object_type=event.object_type,
            object_id=event.object_id,
            field=event.field,
            old_value=event.old_value,
            new_value=event.new_value,
            changed_by=event.changed_by,
            reason=event.reason,
            commit=event.commit,
            source=event.source,
        )

    def get_history(
        self,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        limit: int = 50,
    ) -> List['AuditEntry']:
        """
        Get audit history with optional filters.

        Now reads from JSONL format.
        """
        events = self._reader.get_history(
            object_type=object_type,
            object_id=object_id,
            limit=limit,
        )

        # Convert to AuditEntry for backward compatibility
        return [
            AuditEntry(
                timestamp=e.timestamp,
                object_type=e.object_type,
                object_id=e.object_id,
                field=e.field,
                old_value=e.old_value,
                new_value=e.new_value,
                changed_by=e.changed_by,
                reason=e.reason,
                commit=e.commit,
                source=e.source,
            )
            for e in events
        ]

    def get_object_history(
        self,
        object_type: str,
        object_id: str,
        limit: int = 50,
    ) -> List['AuditEntry']:
        """Get history for a specific object."""
        return self.get_history(
            object_type=object_type,
            object_id=object_id,
            limit=limit,
        )

    # DEPRECATED methods - keep for migration period
    def _load_trail_from_yaml(self) -> dict:
        """DEPRECATED: Load trail data from YAML file."""
        import warnings
        warnings.warn(
            "_load_trail_from_yaml is deprecated. Use JSONL format.",
            DeprecationWarning,
        )

        if not self.audit_file.exists():
            return {"entries": []}

        import yaml
        with open(self.audit_file) as f:
            data = yaml.safe_load(f)

        return data if data else {"entries": []}

    def _save_trail(self) -> None:
        """DEPRECATED: Save trail to YAML file."""
        import warnings
        warnings.warn(
            "_save_trail is deprecated. Use JSONL format.",
            DeprecationWarning,
        )
        # No-op - JSONL writes are immediate
        pass
```

**Option B: Create new JSONLAuditTrailManager (If backward compat needed)**
```python
# vibey/operations/roadmap/audit_trail.py

class JSONLAuditTrailManager(AuditTrailManager):
    """
    AuditTrailManager using JSONL format.

    Drop-in replacement for AuditTrailManager.
    """

    def __init__(self, root_dir: Path):
        # Skip parent __init__ to avoid YAML setup
        self.root_dir = root_dir
        self.activity_log_dir = root_dir / ".vibey" / "roadmap" / "activity_log"

        from vibey.operations.roadmap.jsonl_activity_log import (
            ActivityLogWriter,
            ActivityLogReader,
        )

        self._writer = ActivityLogWriter(self.activity_log_dir)
        self._reader = ActivityLogReader(self.activity_log_dir)

    # Override methods to use JSONL...


# Factory function to get appropriate manager
def get_audit_trail_manager(root_dir: Path, use_jsonl: bool = True) -> AuditTrailManager:
    """
    Get audit trail manager.

    Args:
        root_dir: Project root directory
        use_jsonl: If True (default), use JSONL format

    Returns:
        AuditTrailManager instance
    """
    if use_jsonl:
        return JSONLAuditTrailManager(root_dir)
    return AuditTrailManager(root_dir)
```

### 2. Update UnifiedActivityLog

The `UnifiedActivityLog` wrapper doesn't need major changes if `AuditTrailManager` is updated, but we should ensure it works correctly:

```python
# vibey/operations/roadmap/activity_log.py

class UnifiedActivityLog:
    """
    Unified interface for activity logging.

    Wraps AuditTrailManager (now using JSONL format).
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self._manager = AuditTrailManager(root_dir)

    def log_task_started(self, task_id: str, reason: Optional[str] = None) -> None:
        """Log task started."""
        self._manager.log_change(
            object_type="task",
            object_id=task_id,
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="cli",
            reason=reason,
            source="activity_log",
        )

    def log_task_completed(self, task_id: str, reason: Optional[str] = None) -> None:
        """Log task completed."""
        self._manager.log_change(
            object_type="task",
            object_id=task_id,
            field="status",
            old_value="in_progress",
            new_value="completed",
            changed_by="cli",
            reason=reason,
            source="activity_log",
        )

    # ... other methods remain unchanged, they delegate to _manager

    def get_recent_activity(self, limit: int = 50) -> List:
        """Get recent activity across all objects."""
        return self._manager.get_history(limit=limit)

    def get_task_history(self, task_id: str, limit: int = 20) -> List:
        """Get history for a specific task."""
        return self._manager.get_object_history("task", task_id, limit=limit)
```

### 3. Update CLI Commands

Update any CLI commands that display activity history:

```python
# vibey/cli/commands.py

@roadmap.command()
@click.option('--limit', '-n', default=20, help='Number of events to show')
@click.option('--type', '-t', 'object_type', help='Filter by object type')
@click.option('--id', 'object_id', help='Filter by object ID')
def activity(limit: int, object_type: Optional[str], object_id: Optional[str]):
    """Show recent roadmap activity."""
    from vibey.operations.roadmap.audit_trail import AuditTrailManager

    manager = AuditTrailManager(Path.cwd())
    entries = manager.get_history(
        object_type=object_type,
        object_id=object_id,
        limit=limit,
    )

    if not entries:
        click.echo("No activity found.")
        return

    for entry in entries:
        timestamp = entry.timestamp[:19]  # Trim to seconds
        click.echo(f"[{timestamp}] {entry.object_type}/{entry.object_id}")
        click.echo(f"  {entry.field}: {entry.old_value} → {entry.new_value}")
        if entry.reason:
            click.echo(f"  Reason: {entry.reason}")
        click.echo("")
```

### 4. Remove YAML Dependencies

After migration is complete, remove YAML-related code:

```python
# vibey/operations/roadmap/audit_trail.py

# REMOVE these imports
# import yaml

# REMOVE these attributes
# self.audit_file = self.roadmap_dir / "audit-trail.yaml"
# self.trail = self._load_trail_from_yaml()

# REMOVE these methods
# def _load_trail_from_yaml(self) -> dict:
# def _save_trail(self) -> None:
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/audit_trail.py` | Update `AuditTrailManager` to use JSONL |
| `vibey/operations/roadmap/activity_log.py` | Verify `UnifiedActivityLog` works with new format |
| `vibey/cli/commands.py` | Update activity display commands |

---

## Testing Strategy

```python
# tests/operations/roadmap/test_audit_trail_jsonl.py

import pytest
from pathlib import Path


class TestAuditTrailManagerJSONL:
    """Tests for AuditTrailManager with JSONL backend."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create test project."""
        (tmp_path / ".vibey" / "roadmap" / "activity_log").mkdir(parents=True)
        return tmp_path

    def test_log_change_writes_jsonl(self, project):
        """log_change writes to JSONL file."""
        from vibey.operations.roadmap.audit_trail import AuditTrailManager

        manager = AuditTrailManager(project)
        manager.log_change(
            object_type="task",
            object_id="task_123",
            field="status",
            old_value="not_started",
            new_value="in_progress",
            changed_by="test",
        )

        activity_log_dir = project / ".vibey" / "roadmap" / "activity_log"
        jsonl_files = list(activity_log_dir.glob("*.jsonl"))

        assert len(jsonl_files) == 1

    def test_get_history_reads_jsonl(self, project):
        """get_history reads from JSONL files."""
        from vibey.operations.roadmap.audit_trail import AuditTrailManager

        manager = AuditTrailManager(project)

        # Write some entries
        manager.log_change("task", "task_1", "status", "a", "b", "test")
        manager.log_change("task", "task_2", "status", "a", "b", "test")
        manager.log_change("sprint", "sprint_1", "status", "a", "b", "test")

        # Read back
        all_entries = manager.get_history()
        task_entries = manager.get_history(object_type="task")

        assert len(all_entries) == 3
        assert len(task_entries) == 2

    def test_returns_audit_entry_objects(self, project):
        """Results are AuditEntry objects for compatibility."""
        from vibey.operations.roadmap.audit_trail import AuditTrailManager, AuditEntry

        manager = AuditTrailManager(project)
        manager.log_change("task", "task_1", "status", "a", "b", "test")

        entries = manager.get_history()

        assert len(entries) == 1
        assert isinstance(entries[0], AuditEntry)
        assert entries[0].object_type == "task"


class TestUnifiedActivityLogJSONL:
    """Tests for UnifiedActivityLog with JSONL backend."""

    @pytest.fixture
    def project(self, tmp_path):
        """Create test project."""
        (tmp_path / ".vibey" / "roadmap" / "activity_log").mkdir(parents=True)
        return tmp_path

    def test_log_task_started(self, project):
        """log_task_started writes to JSONL."""
        from vibey.operations.roadmap.activity_log import UnifiedActivityLog

        log = UnifiedActivityLog(project)
        log.log_task_started("task_123", reason="Starting work")

        entries = log.get_task_history("task_123")

        assert len(entries) == 1
        assert entries[0].new_value == "in_progress"

    def test_log_task_completed(self, project):
        """log_task_completed writes to JSONL."""
        from vibey.operations.roadmap.activity_log import UnifiedActivityLog

        log = UnifiedActivityLog(project)
        log.log_task_completed("task_123", reason="Work done")

        entries = log.get_task_history("task_123")

        assert len(entries) == 1
        assert entries[0].new_value == "completed"

    def test_get_recent_activity(self, project):
        """get_recent_activity returns from JSONL."""
        from vibey.operations.roadmap.activity_log import UnifiedActivityLog

        log = UnifiedActivityLog(project)
        log.log_task_started("task_1")
        log.log_task_started("task_2")
        log.log_task_completed("task_1")

        recent = log.get_recent_activity(limit=10)

        assert len(recent) == 3
```

---

## Success Criteria

- [ ] `AuditTrailManager` uses JSONL writer/reader internally
- [ ] `log_change()` writes to JSONL files
- [ ] `get_history()` reads from JSONL files
- [ ] Results are `AuditEntry` objects for backward compatibility
- [ ] `UnifiedActivityLog` works with updated manager
- [ ] CLI activity commands work with new format
- [ ] No references to `audit-trail.yaml` in active code paths
- [ ] All existing tests pass
- [ ] All new tests pass

---

## Dependencies

- Task 002 (JSONL writer)
- Task 003 (JSONL reader)
- Task 004 (migration complete)

---

## Notes

### Backward Compatibility

During the transition period:
1. Keep `AuditEntry` dataclass unchanged
2. `AuditTrailManager` methods return `AuditEntry` objects
3. Deprecation warnings for YAML-related methods
4. After migration verification, remove deprecated code

### Testing Strategy

1. **Unit tests** - Test individual methods
2. **Integration tests** - Test full write/read cycle
3. **Regression tests** - Ensure existing functionality works
4. **Manual testing** - Verify CLI commands display correctly

### Migration Path

```
Phase 1: Add JSONL support (Tasks 001-003)
Phase 2: Migrate data (Task 004)
Phase 3: Update consumers (Task 005) ← This task
Phase 4: Add tests (Task 006)
Phase 5: Remove YAML code (future cleanup)
```
