# Sprint 28: Deferred Task Schema and Progress Bugs

**Sprint ID:** 01KD43809NC3FPJJ179MAZRKCK
**Track:** CLI Dogfooding Bug Fixes (01KC39XSXJ39N12HWJ93F77KQ9)
**Status:** Not Started

## Sprint Overview

This sprint addresses bugs discovered during roadmap state verification. Four issues were found:

1. The `deferred` field exists in YAML but is not stored in the SQLite database
2. Sprints with only deferred incomplete tasks don't auto-progress to completed status
3. CLI edit command doesn't recognize `production_ready` as valid status
4. CLI revert command doesn't support reverting from `production_ready`

### Sprint Goal
Fix deferred field storage, sprint auto-progression, and CLI status validation

### Success Criteria
- Deferred field is stored in database schema
- Sprints with only deferred incomplete tasks auto-progress to completed/production_ready
- CLI edit recognizes all TicketStatus values
- CLI revert supports production_ready -> in_progress

---

## Task Plans

### Task 1: Add deferred column to database schema
**ID:** 01KD438MN86VRXS70K6BPZNB51
**Status:** Not Started
**Priority:** Medium
**Complexity:** Simple
**Estimated Tokens:** 500

#### Problem Statement
The YAML files have a `deferred: true` field for tasks that are intentionally put on hold, but this field is not stored in the SQLite database. When querying the database for task state, the deferred status is lost.

#### Root Cause
The tasks table schema in `vibey/roadmap/serialization/sql_dumper.py` doesn't include a `deferred` column. The field is parsed from YAML but not persisted to SQLite.

#### Solution
1. Add `deferred INTEGER NOT NULL DEFAULT 0` column to the tasks table DDL
2. Update `sql_dumper.py` to write the deferred field when inserting tasks
3. Update `sql_loader.py` to read the deferred field when loading tasks
4. Add migration path for existing databases (ALTER TABLE or rebuild)

#### Files to Modify
- `vibey/roadmap/serialization/sql_dumper.py` - Add column to schema, write field
- `vibey/roadmap/serialization/sql_loader.py` - Read field when loading
- Possibly `vibey/roadmap/models/task.py` - Ensure deferred is in the model

#### Verification
- Round-trip test: Create task with `deferred: true`, rebuild DB, query DB, verify deferred=1
- Existing tasks without deferred field should have deferred=0

---

### Task 2: Sprint auto-progress should skip deferred tasks
**ID:** 01KD438MN86VRXS70K6BPZNB52
**Status:** Not Started
**Priority:** Medium
**Complexity:** Medium
**Estimated Tokens:** 800
**Depends On:** Task 1 (deferred field must be queryable in DB)

#### Problem Statement
Sprints with only deferred incomplete tasks should auto-progress to completed or production_ready status. Currently, a sprint remains in_progress even when all non-deferred tasks are complete.

Example: Sprint 10 "Validation and Sync Bugs" has 4/5 tasks complete, but the 5th task is marked as `deferred: true`. The sprint status remains `in_progress` but should be `completed`.

#### Root Cause
The auto-progress logic in `vibey/operations/roadmap/update.py` counts all incomplete tasks, not just non-deferred incomplete tasks:

```python
# Current logic (problematic)
incomplete_count = sum(1 for t in tasks if t.status != 'completed')
```

It should be:
```python
# Fixed logic
incomplete_count = sum(1 for t in tasks if t.status != 'completed' and not t.deferred)
```

#### Solution
1. Update sprint auto-progress logic to exclude deferred tasks from incomplete count
2. Update track auto-progress logic similarly
3. Add tests verifying sprints with only deferred incomplete tasks auto-complete

#### Files to Modify
- `vibey/operations/roadmap/update.py` - Update progress_sprint_status() and progress_track_status()
- `vibey/cli/roadmap_lib/status.py` - Similar logic may exist here
- Tests for auto-progress behavior

#### Verification
- Sprint with 4/5 tasks complete (5th is deferred) should auto-progress to completed
- Track with all sprints completed (except sprints with only deferred tasks) should auto-progress

---

### Task 3: CLI edit validation doesn't recognize production_ready status
**ID:** 01KD43YW9SS8J7TZEVEHNPKAWZ
**Status:** Not Started
**Priority:** High
**Complexity:** Simple
**Estimated Tokens:** 300

#### Problem Statement
The `vibey roadmap edit file` command fails with validation error when editing files that have status=production_ready. The validator only recognizes a subset of status values.

#### Error Message
```
Invalid status: production_ready (must be one of ['not_started', 'in_progress', 'blocked', 'completed'])
```

#### Root Cause
The SafeYamlEditor validator in `vibey/operations/roadmap/safe_yaml_editor.py` has an incomplete list of valid statuses. It doesn't include all TicketStatus enum values.

#### Solution
Update the status validator to use the TicketStatus enum directly:
```python
from vibey.roadmap.models.ticket.enums import TicketStatus
VALID_STATUSES = [s.value for s in TicketStatus]
```

#### Files to Modify
- `vibey/operations/roadmap/safe_yaml_editor.py` - Update status validation

#### Verification
- `vibey roadmap edit file track.yaml --set status=in_progress` succeeds on production_ready file

---

### Task 4: CLI revert doesn't support production_ready to in_progress
**ID:** 01KD43YW9SS8J7TZEVEHNPKAX0
**Status:** Not Started
**Priority:** Medium
**Complexity:** Simple
**Estimated Tokens:** 400

#### Problem Statement
The `vibey roadmap revert` command cannot revert tracks/sprints from production_ready status back to in_progress. This prevents correcting premature production_ready transitions.

#### Error Message
```
Cannot revert track from 'production_ready' to 'in_progress'. Valid transitions from 'production_ready': []
```

#### Root Cause
The revert command in `vibey/cli/commands.py` or related module has a limited set of allowed transitions.

#### Solution
Update the revert transition map to support:
- production_ready -> in_progress
- production_ready -> completed
- deployed -> production_ready
- deployed -> in_progress

#### Files to Modify
- `vibey/cli/commands.py` or `vibey/operations/roadmap/update.py` - Add revert transitions

#### Verification
- `vibey roadmap revert <track-id> --to in_progress` succeeds from production_ready

---

## Sprint Summary

| Task | Title | Status | Priority | Depends On |
|------|-------|--------|----------|------------|
| 1 | Add deferred column to database schema | **COMPLETED** | Medium | Task 5 |
| 2 | Sprint auto-progress should skip deferred tasks | **COMPLETED** | Medium | Task 1 |
| 3 | CLI edit validation doesn't recognize production_ready | **COMPLETED** | High | - |
| 4 | CLI revert doesn't support production_ready transitions | **COMPLETED** | Medium | - |
| 5 | Fix blocker_type CHECK constraint violation | **COMPLETED** | Critical | - |

**Completion:** 5/5 tasks (100%)

## Completed Tasks

### Task 1 - COMPLETED (2025-12-22)
- Added `deferred` column to tasks table schema in `vibey/roadmap/database/schema.py` line 222
- Updated `create_task` CRUD function to accept and write deferred field
- Updated `_load_roadmap_to_db_flat` to pass `deferred=task.deferred` when creating tasks
- Updated sql_dumper.py to write deferred field in save_tasks()
- Updated sql_loader.py to read deferred field in _load_task_from_row()
- Updated Task dataclass in task.py to include deferred field
- Updated yaml_loader.py for both v1 Task and v2 TaskTicket loaders
- Verified: Task 01KCY39YJW8A3YDNTFJY5KMDGT now has deferred=1 in database

### Task 5 - COMPLETED (2025-12-22)
- Issue: Database rebuild failed with CHECK constraint error for blocker_type
- Root cause: Schema only allowed 'track', 'sprint', 'task' but YAML data had 'external'
- Solution: Updated `vibey/roadmap/database/schema.py` lines 254, 258, 273, 277
- Added 'external' as valid blocker_type in entity_blocks and entity_blocked_by tables
- Database now successfully rebuilds: 50 tracks, 255 sprints, 1682 tasks

### Task 3 - COMPLETED (2025-12-22)
- Updated `safe_yaml_editor.py` to import `TicketStatus` enum and use it for validation
- Now accepts all valid statuses instead of hardcoded subset
- Commit: f8988188

### Task 4 - COMPLETED (2025-12-22)
- Updated `main.py` revert command to accept more target statuses
- Updated `commands_legacy.py` valid_transitions to support full lifecycle
- Added proper timestamp clearing for all status levels
- Commit: f8988188

### Task 2 - COMPLETED (2025-12-23)
- Modified `vibey/operations/roadmap/update.py` lines 1602-1624
- Added helper `is_deferred()` function to check task deferred status
- Modified progress calculations to exclude deferred tasks from totals
- Added `deferred` attribute to MockTask for v2 format tasks
- Verified: Sprint with only deferred incomplete tasks now auto-progresses

## Related Work
- Sprint 10: Validation and Sync Bugs (Task 4 - deferred) - original bug for YAML progress sync
- This sprint is a prerequisite for proper resolution of that deferred task
