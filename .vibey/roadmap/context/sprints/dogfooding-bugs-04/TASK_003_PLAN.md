# Task 003: Add Post-Task-Completion Hook for Parent Updates

**Task ID:** dogfooding-bugs-04-task-003
**Bug Addressed:** #1 (Track and Sprint Progress Not Auto-Updated After Task Completion)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

While Task 002 fixes the progress update chain, we need a robust hook system to ensure parent objects are always updated when children change status. This provides:

1. A centralized place to handle status change side effects
2. Audit logging of status changes
3. Extensibility for future features (notifications, webhooks)
4. Explicit auto-progression triggers

---

## Current Architecture

```python
# In complete_task():
task.status = TaskStatus.COMPLETED
save_task(task, tasks_path)
_update_sprint_progress(fs, sprint_id)  # Direct call - tightly coupled
```

---

## Implementation

### Hook System Design

```python
# vibey/operations/roadmap/hooks.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Callable
from enum import Enum

class StatusChangeEvent(Enum):
    """Types of status change events."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    SPRINT_BLOCKED = "sprint_blocked"
    TRACK_STARTED = "track_started"
    TRACK_COMPLETED = "track_completed"
    TRACK_BLOCKED = "track_blocked"


@dataclass
class StatusChange:
    """Represents a status change event."""
    event_type: StatusChangeEvent
    entity_type: str  # "task", "sprint", "track", "roadmap"
    entity_id: str
    old_status: str
    new_status: str
    timestamp: datetime
    changed_by: str
    metadata: dict = None

    @property
    def parent_entity_type(self) -> Optional[str]:
        """Get parent entity type."""
        if self.entity_type == "task":
            return "sprint"
        elif self.entity_type == "sprint":
            return "track"
        elif self.entity_type == "track":
            return "roadmap"
        return None


class StatusChangeHook(ABC):
    """Base class for status change hooks."""

    @abstractmethod
    def on_status_change(self, change: StatusChange, root_dir: Path) -> None:
        """Handle a status change event."""
        pass


class ProgressUpdateHook(StatusChangeHook):
    """
    Hook that updates parent progress when child status changes.

    This is the primary hook for Bug #1 fix.
    """

    def on_status_change(self, change: StatusChange, root_dir: Path) -> None:
        """Update parent progress after status change."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(root_dir)

        if change.entity_type == "task":
            # Task changed → update sprint progress
            sprint_id = self._get_parent_id(change.entity_id, "task", fs)
            if sprint_id:
                self._update_sprint_progress(fs, sprint_id)

        elif change.entity_type == "sprint":
            # Sprint changed → update track progress
            track_id = self._get_parent_id(change.entity_id, "sprint", fs)
            if track_id:
                self._update_track_progress(fs, track_id)

        elif change.entity_type == "track":
            # Track changed → update roadmap progress
            self._update_roadmap_progress(fs)

    def _get_parent_id(self, entity_id: str, entity_type: str, fs) -> Optional[str]:
        """Get parent ID for an entity."""
        from vibey.roadmap.serialization import load_sprint, load_track, load_task

        if entity_type == "task":
            # Get sprint_id from task
            task_path = fs.get_task_path(entity_id)
            if task_path and task_path.exists():
                task = load_task(task_path)
                return getattr(task, 'sprint_id', None)

            # Fallback: try parsing from task_id (hierarchical format)
            if '-task-' in entity_id:
                return entity_id.split('-task-')[0]

        elif entity_type == "sprint":
            # Get track_id from sprint
            sprint_path = fs.get_sprint_path(entity_id)
            if sprint_path and sprint_path.exists():
                sprint = load_sprint(sprint_path)
                return sprint.track_id

        return None

    def _update_sprint_progress(self, fs, sprint_id: str) -> None:
        """Update sprint progress (delegated to update.py)."""
        from vibey.operations.roadmap.update import _update_sprint_progress
        _update_sprint_progress(fs, sprint_id)

    def _update_track_progress(self, fs, track_id: str) -> None:
        """Update track progress (delegated to update.py)."""
        from vibey.operations.roadmap.update import _update_track_progress
        _update_track_progress(fs, track_id)

    def _update_roadmap_progress(self, fs) -> None:
        """Update roadmap progress (delegated to update.py)."""
        from vibey.operations.roadmap.update import _update_roadmap_progress
        _update_roadmap_progress(fs)


class AutoProgressionHook(StatusChangeHook):
    """
    Hook that triggers automatic status progression.

    When a child completes, check if parent can auto-progress.
    """

    def on_status_change(self, change: StatusChange, root_dir: Path) -> None:
        """Check for auto-progression opportunities."""
        from vibey.cli.roadmap_lib.status import StatusManager
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        from vibey.roadmap.serialization import load_sprint, load_track, load_roadmap

        # Only trigger on completion events
        if "completed" not in change.new_status.lower():
            return

        fs = FileSystemManager(root_dir)
        status_manager = StatusManager(root_dir)

        if change.entity_type == "task":
            # Check if sprint should auto-progress
            sprint_id = self._get_sprint_id(change.entity_id, fs)
            if sprint_id:
                sprint_path = fs.get_sprint_path(sprint_id)
                if sprint_path.exists():
                    sprint = load_sprint(sprint_path)
                    progressed, new_status, message = status_manager.progress_sprint_status(sprint)
                    if progressed:
                        print(f"🎉 Sprint auto-progressed to {new_status.value}: {message}")

        elif change.entity_type == "sprint":
            # Check if track should auto-progress
            track_id = self._get_track_id(change.entity_id, fs)
            if track_id:
                track_path = fs.get_track_path(track_id)
                if track_path.exists():
                    track = load_track(track_path)
                    progressed, new_status, message = status_manager.progress_track_status(track)
                    if progressed:
                        print(f"🎉 Track auto-progressed to {new_status.value}: {message}")

        elif change.entity_type == "track":
            # Check if roadmap should auto-progress
            roadmap_path = fs.get_roadmap_path()
            if roadmap_path.exists():
                roadmap = load_roadmap(roadmap_path)
                progressed, new_status, message = status_manager.progress_roadmap_status(roadmap)
                if progressed:
                    print(f"🎉 Roadmap auto-progressed to {new_status.value}: {message}")

    def _get_sprint_id(self, task_id: str, fs) -> Optional[str]:
        """Get sprint ID for a task."""
        # Implementation similar to ProgressUpdateHook._get_parent_id
        pass

    def _get_track_id(self, sprint_id: str, fs) -> Optional[str]:
        """Get track ID for a sprint."""
        # Implementation similar to ProgressUpdateHook._get_parent_id
        pass


class AuditLogHook(StatusChangeHook):
    """Hook that logs status changes to audit trail."""

    def on_status_change(self, change: StatusChange, root_dir: Path) -> None:
        """Log status change to audit trail."""
        from vibey.operations.roadmap.audit_trail import log_status_change

        log_status_change(
            root_dir=root_dir,
            object_type=change.entity_type,
            object_id=change.entity_id,
            old_status=change.old_status,
            new_status=change.new_status,
            reason=f"Status changed via {change.changed_by}",
            changed_by=change.changed_by,
        )


# Hook registry
_hooks: List[StatusChangeHook] = []


def register_hook(hook: StatusChangeHook) -> None:
    """Register a status change hook."""
    _hooks.append(hook)


def unregister_hook(hook: StatusChangeHook) -> None:
    """Unregister a status change hook."""
    _hooks.remove(hook)


def trigger_hooks(change: StatusChange, root_dir: Path) -> None:
    """Trigger all registered hooks for a status change."""
    for hook in _hooks:
        try:
            hook.on_status_change(change, root_dir)
        except Exception as e:
            print(f"⚠️  Hook {hook.__class__.__name__} failed: {e}")


def initialize_default_hooks() -> None:
    """Initialize default hooks."""
    register_hook(ProgressUpdateHook())
    register_hook(AutoProgressionHook())
    register_hook(AuditLogHook())
```

### Update complete_task to Use Hooks

```python
# vibey/operations/roadmap/update.py

from vibey.operations.roadmap.hooks import (
    StatusChange, StatusChangeEvent, trigger_hooks, initialize_default_hooks
)

# Initialize hooks at module load
initialize_default_hooks()


def complete_task(
    root_dir: Path,
    task_id: str,
    completed_by: str = "system",
    skip_commit_check: bool = False
) -> int:
    """Mark a task as completed."""
    # ... existing validation code ...

    # Capture old status
    old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

    # Update task
    task.status = TaskStatus.COMPLETED
    task.completed = datetime.now(timezone.utc)
    task.metadata.last_modified = datetime.now(timezone.utc)
    task.metadata.last_modified_by = completed_by

    # Save task
    save_task(task, tasks_path)
    _sync_task_to_db(task, root_dir)
    print(f"✅ Task '{task.title}' marked as completed")

    # Trigger hooks (replaces direct _update_sprint_progress call)
    change = StatusChange(
        event_type=StatusChangeEvent.TASK_COMPLETED,
        entity_type="task",
        entity_id=task_id,
        old_status=old_status,
        new_status="completed",
        timestamp=datetime.now(timezone.utc),
        changed_by=completed_by,
        metadata={"sprint_id": sprint_id}
    )
    trigger_hooks(change, root_dir)

    return 0
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/hooks.py` | NEW: Hook system |
| `vibey/operations/roadmap/update.py` | Use hooks instead of direct calls |

---

## Testing Strategy

```python
class TestProgressHooks:
    """Test status change hooks."""

    def test_progress_hook_updates_sprint(self, flat_roadmap_environment):
        """ProgressUpdateHook updates sprint on task completion."""
        hook = ProgressUpdateHook()
        change = StatusChange(
            event_type=StatusChangeEvent.TASK_COMPLETED,
            entity_type="task",
            entity_id="task-001",
            old_status="in_progress",
            new_status="completed",
            timestamp=datetime.now(timezone.utc),
            changed_by="test",
        )

        hook.on_status_change(change, flat_roadmap_environment)

        # Verify sprint progress updated
        sprint = load_sprint(sprint_path)
        assert sprint.progress.tasks_completed > 0

    def test_auto_progression_hook_triggers(self, flat_roadmap_environment):
        """AutoProgressionHook triggers when all tasks complete."""
        # Complete all tasks in sprint
        for task_id in task_ids:
            complete_task(flat_roadmap_environment, task_id)

        # Verify sprint auto-progressed
        sprint = load_sprint(sprint_path)
        assert sprint.status != Status.NOT_STARTED

    def test_hooks_chain_correctly(self, flat_roadmap_environment):
        """Hooks execute in correct order."""
        order = []

        class OrderTrackingHook(StatusChangeHook):
            def __init__(self, name):
                self.name = name

            def on_status_change(self, change, root_dir):
                order.append(self.name)

        register_hook(OrderTrackingHook("first"))
        register_hook(OrderTrackingHook("second"))

        trigger_hooks(change, flat_roadmap_environment)

        assert order == ["first", "second"]
```

---

## Success Criteria

- [ ] Hook system implemented with clean interface
- [ ] ProgressUpdateHook updates parents on child status change
- [ ] AutoProgressionHook triggers status progression
- [ ] AuditLogHook logs all status changes
- [ ] complete_task, start_task, etc. use hooks
- [ ] Hooks work with both flat and nested structures

---

## Dependencies

- Task 002 (progress update functions fixed)

---

## Notes

The hook system provides:
1. **Decoupling**: Status changes don't need to know about all side effects
2. **Extensibility**: Easy to add new hooks (notifications, metrics)
3. **Testability**: Hooks can be tested in isolation
4. **Auditability**: All status changes flow through the same path

This is a clean architecture improvement that also fixes Bug #1 by ensuring parent progress is always updated.
