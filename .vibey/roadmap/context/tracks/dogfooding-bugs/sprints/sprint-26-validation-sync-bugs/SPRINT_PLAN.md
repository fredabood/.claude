# Sprint 26: Validation and Sync Bugs

**Sprint ID:** 01KCY39YJW8A3YDNTFJY5KMDGP
**Track:** CLI Dogfooding Bug Fixes (01KC39XSXJ39N12HWJ93F77KQ9)
**Status:** In Progress (4/5 tasks completed, 1 deferred)

## Sprint Overview

This sprint addresses validation and synchronization bugs discovered during the roadmap state audit. These bugs affected data integrity between YAML files and the SQLite database, and caused silent failures during data loading.

### Sprint Goal
All validation errors are handled gracefully, sync process works correctly.

### Success Criteria
- No tasks silently skipped due to date validation
- Track status updates correctly when work begins
- Progress sync does not corrupt status fields

---

## Task Plans

### Task 1: Fix started_at Before created_at Validation
**ID:** 01KCY39YJW8A3YDNTFJY5KMDGQ
**Status:** COMPLETED
**Priority:** High
**Complexity:** Simple

#### Problem Statement
Tasks with `started_at` timestamp before `created_at` timestamp were being silently skipped during database load. This caused data loss when retroactively creating tasks for work that had already begun.

#### Root Cause
The validation in `vibey/roadmap/models/task.py`, `sprint.py`, `track.py`, and `roadmap.py` was too strict. It rejected tasks where work started before the formal task creation (a valid scenario for retroactive documentation).

#### Solution Implemented
Relaxed the date validation to allow `started_at < created_at`. This supports the common pattern of:
1. Starting work informally
2. Later creating the formal task record
3. Setting `started_at` to reflect when work actually began

#### Files Modified
- `vibey/roadmap/models/task.py` - Removed strict date ordering validation
- `vibey/roadmap/models/sprint.py` - Same fix
- `vibey/roadmap/models/track.py` - Same fix
- `vibey/roadmap/models/roadmap.py` - Same fix
- `vibey/roadmap/models/ticket/ticket.py` - Updated pydantic validator

#### Verification
- Tasks with retroactive start dates now load correctly
- Database rebuild no longer silently skips these tasks

---

### Task 2: Fix blocked_by/depends_on ULID String Parsing
**ID:** 01KCY39YJW8A3YDNTFJY5KMDGR
**Status:** COMPLETED
**Priority:** High
**Complexity:** Medium

#### Problem Statement
Simple ULID strings in `blocked_by` or `depends_on` fields caused an error: `'str' object has no attribute 'get'`. The parser expected a dictionary but received a plain string.

#### Root Cause
The YAML loader in `vibey/roadmap/serialization/yaml_loader.py` only handled the structured dictionary format for dependencies:
```yaml
depends_on:
  - blocker_id: 01KC...
    blocker_type: sprint
```

But not the simpler string format:
```yaml
depends_on:
  - 01KC...
```

#### Solution Implemented
Added type checking in the dependency parsing logic to handle both formats:
```python
for d in sprint_data.get('depends_on', []):
    if isinstance(d, str):
        # Simple string format - treat as sprint dependency
        depends_on.append(DependencyStatus(
            blocker_id=d,
            blocker_type='sprint',
            ...
        ))
    elif isinstance(d, dict):
        # Structured format
        depends_on.append(DependencyStatus(
            blocker_id=d.get('blocker_id'),
            ...
        ))
```

#### Files Modified
- `vibey/roadmap/serialization/yaml_loader.py` - Lines 1346-1368, added isinstance() check

#### Verification
- Both string and dictionary dependency formats now parse correctly
- Existing structured dependencies continue to work

---

### Task 3: Fix Track Status Not Auto-Updating to in_progress
**ID:** 01KCY39YJW8A3YDNTFJY5KMDGS
**Status:** COMPLETED
**Priority:** Medium
**Complexity:** Medium

#### Problem Statement
Tracks remained in `not_started` status even when tasks within them were started or completed. The track should automatically transition to `in_progress` when work begins.

#### Root Cause
The `progress_track_status()` function in `vibey/cli/roadmap_lib/status.py` didn't handle the `NOT_STARTED` state. It only progressed tracks that were already `IN_PROGRESS`.

#### Solution Implemented
Added handling for `NOT_STARTED` status in track progression:
```python
if current_status == Status.NOT_STARTED:
    has_active_sprints = any(
        s.status in (Status.IN_PROGRESS, Status.COMPLETED, ...)
        for s in track.sprints
    )
    has_progress = track.progress.tasks_completed > 0

    if has_active_sprints or has_progress:
        return True, Status.IN_PROGRESS, "Auto-starting track"
```

#### Files Modified
- `vibey/cli/roadmap_lib/status.py` - Lines 186-202

#### Verification
- Tracks now auto-start when first task is started
- Tracks auto-start when sprints show progress

---

### Task 4: Fix YAML Progress Counters Not Synced with Database
**ID:** 01KCY39YJW8A3YDNTFJY5KMDGT
**Status:** DEFERRED
**Priority:** Low
**Complexity:** Medium

#### Problem Statement
Track YAML files show stale progress counters while the database has correct counts. After completing tasks, the YAML `progress.tasks_completed` doesn't update.

#### Root Cause
The system has dual storage (YAML + SQLite) but progress is only updated in one place. There are two possible solutions:

**Option A: Database as Single Source (Recommended)**
- Remove progress fields from YAML entirely
- Query database for all progress metrics
- YAML only stores identity and configuration

**Option B: Keep Progress in YAML**
- Add sync logic to update YAML after every status change
- More complex, higher chance of drift

#### Decision Needed
This requires a design decision before implementation. Recommended approach is Option A to simplify the data model and eliminate sync issues.

#### Deferred Because
- Requires architectural decision
- Low priority (display issue only, data is correct in DB)
- Current workaround: run `vibey roadmap db rebuild` to recalculate

---

### Task 5: Fix Sync Setting Completed Status Without Date
**ID:** 01KCY39YJW8A3YDNTFJY5KMDGV
**Status:** COMPLETED
**Priority:** High
**Complexity:** Simple

#### Problem Statement
The sync process was setting `status=completed` but leaving `completed_at=null`. This failed validation since completed items must have a completion timestamp.

#### Root Cause
The track auto-progression code in `vibey/operations/roadmap/update.py` changed status but didn't set the corresponding timestamp.

#### Solution Implemented
Added timestamp setting logic when status changes:
```python
if progressed and new_status:
    old_status = track.status
    track.status = new_status

    now = datetime.now(timezone.utc)
    if new_status == Status.IN_PROGRESS and not track.started:
        track.started = now
    elif new_status == Status.COMPLETED and not track.completed:
        track.completed = now
    elif new_status == Status.PRODUCTION_READY and not track.production_ready_at:
        track.production_ready_at = now
```

#### Files Modified
- `vibey/operations/roadmap/update.py` - Lines 1729-1743
- `vibey/cli/roadmap-update.py` - Lines 445-459 (legacy file, same fix)

#### Verification
- Status changes now always set appropriate timestamps
- Validation no longer fails on auto-progressed items

---

## Sprint Summary

| Task | Title | Status | Priority |
|------|-------|--------|----------|
| 1 | Fix started_at before created_at validation | COMPLETED | High |
| 2 | Fix blocked_by/depends_on ULID string parsing | COMPLETED | High |
| 3 | Fix track status not auto-updating | COMPLETED | Medium |
| 4 | Fix YAML progress counters sync | DEFERRED | Low |
| 5 | Fix sync setting completed without date | COMPLETED | High |

**Completion:** 4/5 tasks (80%), 1 deferred pending design decision

## Related Commits
- `c50cffe7` - fix(roadmap): Fix 4 validation and sync bugs in Sprint 10
