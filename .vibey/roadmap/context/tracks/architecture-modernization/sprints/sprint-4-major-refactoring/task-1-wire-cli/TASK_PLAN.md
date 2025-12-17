# Task 1: Wire CLI to Unified Ticket Models

**Task ID:** `01KCMMFTTPM8JA1GFD4QQA23VT`
**Sprint:** Sprint 4: Major Refactoring
**Priority:** High | **Complexity:** Medium | **Type:** Development

---

## Problem Statement

The unified ticket architecture is fully implemented but NOT wired to the CLI:

| Component | Status | Location |
|-----------|--------|----------|
| `Ticket` model | ✅ Complete | `vibey/roadmap/models/ticket/ticket.py` |
| `Completable` base | ✅ Complete | `vibey/roadmap/models/ticket/completable.py` |
| `HierarchicalTicket` | ✅ Complete | `vibey/roadmap/models/ticket/hierarchical.py` |
| `ModelAdapter` | ✅ Complete | `vibey/roadmap/models/ticket/adapters.py` |
| `transition_ticket()` | ✅ Complete | `vibey/operations/roadmap/transitions.py` |
| Unified commands | ⚠️ Broken | Import non-existent `start_item`/`complete_item` |
| Old CLI commands | ⚠️ Legacy | Use old models, don't use criteria |

**Key Finding:** `vibey/unified/commands/roadmap.py` imports `start_item` and `complete_item` from `transitions.py`, but these functions DON'T EXIST. The file has `transition_task()`, `transition_sprint()`, etc.

---

## Existing Infrastructure

### Already Implemented

```
vibey/operations/roadmap/transitions.py:
├── TransitionBlockedError          # Exception with blocking reasons
├── transition_ticket()             # Generic transition (validates via can_transition_to)
├── transition_task()               # Task-specific (load → transition → save)
├── transition_sprint()             # Sprint-specific
├── transition_track()              # Track-specific
└── transition_roadmap()            # Roadmap-specific

vibey/roadmap/models/ticket/adapters.py:
├── map_status_to_ticket_status()   # Legacy → TicketStatus
├── map_ticket_status_to_status()   # TicketStatus → Legacy
├── children_to_criteria()          # Child IDs → CompletableTarget criteria
├── dependencies_to_criteria()      # Deps → criteria blocking IN_PROGRESS
├── deliverables_to_criteria()      # Paths → FileExistsTarget criteria
├── ModelAdapter.task_to_ticket()   # Legacy Task → TaskTicket
└── ModelAdapter.ticket_to_task()   # TaskTicket → Legacy Task
```

### Current CLI Flow (Old)

```
commands.py:roadmap_start_cmd()
    → start_task() or start_sprint()   # Internal functions
    → Uses old models directly
    → NO criteria validation
```

### Target CLI Flow (New)

```
unified/commands/roadmap.py:roadmap_start()
    → start_item()                     # NEW: Generic wrapper
    → transitions.py:transition_task() # Already exists
    → ticket.can_transition_to()       # Criteria validation
    → ticket.start()                   # Immutable transition
    → yaml_dumper.save_task_ticket()   # Persistence
```

---

## Implementation Steps

### Step 1: Create Generic Wrapper Functions (30 min)

Add `start_item()` and `complete_item()` to `transitions.py`:

```python
# vibey/operations/roadmap/transitions.py

def start_item(root_dir: Path, item_id: str, force: bool = False) -> dict:
    """
    Start a task, sprint, or track.

    Auto-detects item type from filesystem and delegates to appropriate
    transition function.

    Args:
        root_dir: Project root directory
        item_id: ULID of item to start
        force: If True, bypass blocking criteria

    Returns:
        Dict with updated item info: {'id': str, 'status': str, 'type': str}

    Raises:
        TransitionBlockedError: If blocked and force=False
        FileNotFoundError: If item doesn't exist
    """
    fs = FileSystemManager(root_dir)
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Detect type
    if (roadmap_root / "tasks" / f"{item_id}.yaml").exists():
        ticket = transition_task(item_id, TicketStatus.IN_PROGRESS, root_dir)
        return {'id': ticket.id, 'status': ticket.status.value, 'type': 'task'}
    elif (roadmap_root / "sprints" / f"{item_id}.yaml").exists():
        ticket = transition_sprint(item_id, TicketStatus.IN_PROGRESS, root_dir)
        return {'id': ticket.id, 'status': ticket.status.value, 'type': 'sprint'}
    elif (roadmap_root / "tracks" / f"{item_id}.yaml").exists():
        ticket = transition_track(item_id, TicketStatus.IN_PROGRESS, root_dir)
        return {'id': ticket.id, 'status': ticket.status.value, 'type': 'track'}
    else:
        raise FileNotFoundError(f"Item not found: {item_id}")


def complete_item(root_dir: Path, item_id: str, notes: str = None) -> dict:
    """
    Complete a task, sprint, or track.

    Auto-detects item type from filesystem and delegates to appropriate
    transition function.

    Args:
        root_dir: Project root directory
        item_id: ULID of item to complete
        notes: Optional completion notes

    Returns:
        Dict with updated item info: {'id': str, 'status': str, 'type': str}

    Raises:
        TransitionBlockedError: If blocked by criteria
        FileNotFoundError: If item doesn't exist
    """
    fs = FileSystemManager(root_dir)
    roadmap_root = root_dir / ".vibey" / "roadmap"

    # Detect type
    if (roadmap_root / "tasks" / f"{item_id}.yaml").exists():
        ticket = transition_task(item_id, TicketStatus.COMPLETED, root_dir)
        return {'id': ticket.id, 'status': ticket.status.value, 'type': 'task'}
    elif (roadmap_root / "sprints" / f"{item_id}.yaml").exists():
        ticket = transition_sprint(item_id, TicketStatus.COMPLETED, root_dir)
        return {'id': ticket.id, 'status': ticket.status.value, 'type': 'sprint'}
    elif (roadmap_root / "tracks" / f"{item_id}.yaml").exists():
        ticket = transition_track(item_id, TicketStatus.COMPLETED, root_dir)
        return {'id': ticket.id, 'status': ticket.status.value, 'type': 'track'}
    else:
        raise FileNotFoundError(f"Item not found: {item_id}")
```

### Step 2: Update Unified Commands Error Handling (15 min)

Update `vibey/unified/commands/roadmap.py` to handle `TransitionBlockedError`:

```python
# vibey/unified/commands/roadmap.py

from vibey.operations.roadmap.transitions import (
    start_item,
    complete_item,
    TransitionBlockedError,
)

@unified_command(...)
def roadmap_start(...) -> CommandResult:
    try:
        result = start_item(root_dir, item_id, force=force)
        return CommandResult.ok(
            data=result,
            message=f"Started {result['type']} {item_id}"
        )
    except TransitionBlockedError as e:
        return CommandResult.fail(
            error=f"Blocked: {'; '.join(e.reasons)}"
        )
    except FileNotFoundError as e:
        return CommandResult.fail(error=str(e))
```

### Step 3: Add Criteria Display to `roadmap show` (45 min)

Update `roadmap_show()` to display criteria status:

```python
# vibey/unified/commands/roadmap.py

def format_criteria_status(ticket: HierarchicalTicket) -> str:
    """Format criteria status for CLI output."""
    lines = []

    # Group by transition target
    for target_status in [TicketStatus.IN_PROGRESS, TicketStatus.COMPLETED]:
        criteria = ticket.criteria_for_transition(target_status)
        if not criteria:
            continue

        lines.append(f"\nCriteria for {target_status.value.upper()}:")
        for c in criteria:
            icon = "✓" if c.is_met else "○"
            req = "" if c.required else " (optional)"
            lines.append(f"  {icon} {c.description}{req}")

    return "\n".join(lines)


@unified_command(name="roadmap_show", ...)
def roadmap_show(item_id: str, format: str = "text", ...) -> CommandResult:
    # ... existing code ...

    # Add criteria to output
    if format == "text":
        formatted = format_task_details(result)

        # Load as ticket for criteria
        from vibey.operations.roadmap.query import load_task_ticket
        ticket = load_task_ticket(item_id, root_dir)
        criteria_text = format_criteria_status(ticket)

        formatted += criteria_text
        return CommandResult.ok(data=result, message=formatted)
```

### Step 4: Migrate Old CLI to Use New Functions (30 min)

Update `commands.py` to use new transition system:

```python
# vibey/cli/commands.py

def roadmap_start_cmd(item_id: str) -> int:
    """Start a sprint or task."""
    from vibey.operations.roadmap.transitions import (
        start_item,
        TransitionBlockedError,
    )

    root_dir = Path.cwd()

    try:
        result = start_item(root_dir, item_id)
        print(f"✅ Started {result['type']} '{item_id}'")
        return 0
    except TransitionBlockedError as e:
        print(f"❌ Cannot start {item_id}:")
        for reason in e.reasons:
            print(f"   - {reason}")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1


def roadmap_complete_cmd(item_id: str, skip_commit_check: bool = False, force: bool = False) -> int:
    """Complete a track, sprint, or task."""
    from vibey.operations.roadmap.transitions import (
        complete_item,
        TransitionBlockedError,
    )

    root_dir = Path.cwd()

    try:
        result = complete_item(root_dir, item_id)
        print(f"✅ Completed {result['type']} '{item_id}'")
        return 0
    except TransitionBlockedError as e:
        print(f"❌ Cannot complete {item_id}:")
        for reason in e.reasons:
            print(f"   - {reason}")
        if force:
            print("⚠️  Use --force to override (not recommended)")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
```

### Step 5: Add Unit Tests (45 min)

```python
# tests/operations/roadmap/test_transitions.py

import pytest
from pathlib import Path

from vibey.operations.roadmap.transitions import (
    start_item,
    complete_item,
    TransitionBlockedError,
)


class TestStartItem:
    """Tests for start_item()."""

    def test_start_task_success(self, roadmap_env, sample_task):
        """Starting an unblocked task should succeed."""
        result = start_item(roadmap_env['root'], sample_task.id)
        assert result['status'] == 'in_progress'
        assert result['type'] == 'task'

    def test_start_blocked_task_fails(self, roadmap_env, blocked_task):
        """Starting a blocked task should raise TransitionBlockedError."""
        with pytest.raises(TransitionBlockedError) as exc:
            start_item(roadmap_env['root'], blocked_task.id)
        assert len(exc.value.reasons) > 0

    def test_start_nonexistent_raises(self, roadmap_env):
        """Starting non-existent item should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            start_item(roadmap_env['root'], 'nonexistent')


class TestCompleteItem:
    """Tests for complete_item()."""

    def test_complete_task_success(self, roadmap_env, in_progress_task):
        """Completing an in-progress task should succeed."""
        result = complete_item(roadmap_env['root'], in_progress_task.id)
        assert result['status'] == 'completed'

    def test_complete_with_unmet_criteria_fails(self, roadmap_env, task_with_criteria):
        """Completing task with unmet criteria should fail."""
        with pytest.raises(TransitionBlockedError) as exc:
            complete_item(roadmap_env['root'], task_with_criteria.id)
        assert 'criteria' in str(exc.value).lower() or len(exc.value.reasons) > 0
```

---

## Files to Modify

| File | Change |
|------|--------|
| `vibey/operations/roadmap/transitions.py` | Add `start_item()`, `complete_item()` |
| `vibey/unified/commands/roadmap.py` | Fix imports, add error handling, add criteria display |
| `vibey/cli/commands.py` | Update `roadmap_start_cmd`, `roadmap_complete_cmd` |
| `tests/operations/roadmap/test_transitions.py` | Add unit tests |

---

## Acceptance Criteria

- [ ] `start_item()` and `complete_item()` exist and work
- [ ] Unified commands no longer crash on import
- [ ] `vibey roadmap start <id>` uses criteria-based validation
- [ ] `vibey roadmap complete <id>` uses criteria-based validation
- [ ] `vibey roadmap show <id>` displays criteria status
- [ ] Blocked transitions show clear error messages with reasons
- [ ] All existing tests pass
- [ ] New unit tests pass

---

## Backward Compatibility

The changes are backward compatible:
- Same CLI interface (`vibey roadmap start`, `vibey roadmap complete`)
- Same error codes (0 = success, 1 = failure)
- Enhanced error messages (show blocking reasons)
- New feature: criteria display in `roadmap show`

---

## Estimated Effort

| Step | Time |
|------|------|
| Step 1: Create wrapper functions | 30 min |
| Step 2: Update unified commands | 15 min |
| Step 3: Add criteria display | 45 min |
| Step 4: Migrate old CLI | 30 min |
| Step 5: Add unit tests | 45 min |
| **Total** | **~3 hours** |
