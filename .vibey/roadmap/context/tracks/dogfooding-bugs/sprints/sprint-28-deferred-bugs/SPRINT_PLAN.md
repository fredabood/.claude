# Sprint 28: Deferred Task Schema and Progress Bugs

**Sprint ID:** 01KD43809NC3FPJJ179MAZRKCK
**Track:** CLI Dogfooding Bug Fixes (01KC39XSXJ39N12HWJ93F77KQ9)
**Status:** Not Started

## Sprint Overview

This sprint addresses bugs discovered during roadmap state verification. Two issues were found related to how deferred tasks are handled:

1. The `deferred` field exists in YAML but is not stored in the SQLite database
2. Sprints with only deferred incomplete tasks don't auto-progress to completed status

### Sprint Goal
Fix deferred field storage and sprint auto-progression with deferred tasks

### Success Criteria
- Deferred field is stored in database schema
- Sprints with only deferred incomplete tasks auto-progress to completed/production_ready

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

## Sprint Summary

| Task | Title | Status | Priority | Depends On |
|------|-------|--------|----------|------------|
| 1 | Add deferred column to database schema | Not Started | Medium | - |
| 2 | Sprint auto-progress should skip deferred tasks | Not Started | Medium | Task 1 |

**Completion:** 0/2 tasks (0%)

## Related Work
- Sprint 10: Validation and Sync Bugs (Task 4 - deferred) - original bug for YAML progress sync
- This sprint is a prerequisite for proper resolution of that deferred task
