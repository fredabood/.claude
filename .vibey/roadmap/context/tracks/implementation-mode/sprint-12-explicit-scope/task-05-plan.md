# Task 05: Add completion detection for parent tickets

**Task ID**: `01KDC7N5Z4HSMXG430A6WA831Y`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 4000

## Description

Implement logic to detect when all children of a `--ticket` ULID are complete. Auto-mark parent as complete when all children pass. Stop loop when target ticket reaches completed status.

## Current Behavior

The implementation loop runs until:
- No more executable tasks
- max_tasks limit reached
- max_tokens limit reached
- User interrupt

## Target Behavior

When `--ticket <ULID>` is used:
1. After each task, check if target ticket can be completed
2. For tracks: all sprints complete → track complete
3. For sprints: all tasks complete → sprint complete
4. For tasks: task complete → stop immediately
5. Stop loop when target ticket is marked complete

## Implementation Steps

### Step 1: Add TicketCompletionChecker class (new file or in loop.py)

```python
# vibey/services/implementation/completion.py

from pathlib import Path
from typing import Optional, Tuple
import sqlite3

from vibey.roadmap.database.connection import get_connection


class TicketCompletionChecker:
    """
    Check and update completion status of hierarchical tickets.
    """

    def __init__(self, roadmap_root: Path):
        self.roadmap_root = roadmap_root
        self.db_path = roadmap_root / "roadmap.db"

    def check_and_complete(
        self,
        target_ticket: str,
        target_type: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if target ticket can be completed.

        Args:
            target_ticket: ULID of target ticket
            target_type: 'track', 'sprint', or 'task'

        Returns:
            Tuple of (is_complete, message)
        """
        if target_type == "task":
            return self._check_task_complete(target_ticket)
        elif target_type == "sprint":
            return self._check_sprint_complete(target_ticket)
        elif target_type == "track":
            return self._check_track_complete(target_ticket)

        return False, None

    def _check_task_complete(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """Check if a task is complete."""
        conn = get_connection(db_path=self.db_path)
        cursor = conn.execute(
            "SELECT status FROM tasks WHERE id = ?", [task_id]
        )
        row = cursor.fetchone()

        if row and row["status"] == "completed":
            return True, f"Task {task_id} completed"

        return False, None

    def _check_sprint_complete(self, sprint_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a sprint can be completed (all tasks done).

        If all tasks are complete, mark the sprint as complete.
        """
        conn = get_connection(db_path=self.db_path)

        # Count incomplete tasks
        cursor = conn.execute(
            """
            SELECT COUNT(*) as incomplete
            FROM tasks
            WHERE sprint_id = ? AND status != 'completed'
            """,
            [sprint_id],
        )
        row = cursor.fetchone()

        if row["incomplete"] == 0:
            # All tasks complete - mark sprint complete
            self._mark_sprint_complete(sprint_id)
            return True, f"Sprint {sprint_id} completed (all tasks done)"

        return False, f"{row['incomplete']} tasks remaining"

    def _check_track_complete(self, track_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a track can be completed (all sprints done).

        If all sprints are complete, mark the track as complete.
        """
        conn = get_connection(db_path=self.db_path)

        # Count incomplete sprints
        cursor = conn.execute(
            """
            SELECT COUNT(*) as incomplete
            FROM sprints
            WHERE track_id = ? AND status NOT IN ('completed', 'production_ready')
            """,
            [track_id],
        )
        row = cursor.fetchone()

        if row["incomplete"] == 0:
            # All sprints complete - mark track complete
            self._mark_track_complete(track_id)
            return True, f"Track {track_id} completed (all sprints done)"

        return False, f"{row['incomplete']} sprints remaining"

    def _mark_sprint_complete(self, sprint_id: str) -> None:
        """Mark a sprint as complete in YAML and DB."""
        from vibey.operations.roadmap.status_manager import StatusManager

        status_manager = StatusManager(self.roadmap_root.parent)
        status_manager.complete_sprint(sprint_id)

    def _mark_track_complete(self, track_id: str) -> None:
        """Mark a track as complete in YAML and DB."""
        from vibey.operations.roadmap.status_manager import StatusManager

        status_manager = StatusManager(self.roadmap_root.parent)
        status_manager.complete_track(track_id)
```

### Step 2: Integrate into ImplementationLoop (loop.py)

```python
# In ImplementationLoop class

async def run(self) -> LoopResult:
    """Run the implementation loop."""
    # ... existing setup ...

    # Create completion checker if targeting specific ticket
    completion_checker = None
    if self.config.target_ticket:
        completion_checker = TicketCompletionChecker(self.roadmap_root)

    while True:
        # ... existing task execution ...

        # Check target ticket completion
        if completion_checker and self.config.target_ticket:
            is_complete, message = completion_checker.check_and_complete(
                self.config.target_ticket,
                self.config.target_ticket_type,
            )

            if is_complete:
                logger.info(message)
                self.state.stop_reason = "target_complete"
                break

        # ... continue loop ...
```

### Step 3: Add stop_reason to LoopState/LoopResult

```python
# In state.py or result.py

class LoopResult:
    # ... existing fields ...
    stop_reason: str  # Add: "target_complete" as valid value
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/services/implementation/completion.py` | NEW: TicketCompletionChecker class |
| `vibey/services/implementation/loop.py` | Integrate completion checking |
| `vibey/services/implementation/__init__.py` | Export new class |

## Test Cases

1. `--ticket <task>` → Stops after that task completes
2. `--ticket <sprint>` → Continues until all tasks done, marks sprint complete
3. `--ticket <track>` → Continues until all sprints done, marks track complete
4. Sprint with 1 task remaining → Completes sprint after task
5. Already complete ticket → Stops immediately

## Acceptance Criteria

- [ ] TicketCompletionChecker class implemented
- [ ] Task completion detection works
- [ ] Sprint auto-completion when all tasks done
- [ ] Track auto-completion when all sprints done
- [ ] Loop stops with "target_complete" reason
- [ ] YAML files updated when parent is completed
