# Task Plan: Fix sync process incorrectly setting completed status without date

**Task ID:** 01KCY39YJW8A3YDNTFJY5KMDGV
**Priority:** High
**Complexity:** Simple

## Problem Statement

The YAML sync/recalculate process incorrectly changes track status to `completed` without setting the `completed_at` date, causing subsequent validation failures. When the database is rebuilt, these tracks are skipped with "Completed tracks must have a completion date".

### Example

```yaml
# After sync, track shows:
track:
  status: completed        # Set by sync
  completed: null          # NOT set - causes validation failure!
```

### Root Cause

The status calculation logic in `vibey/operations/roadmap/update.py` sets `status=completed` when all tasks are done, but doesn't set the `completed` timestamp. The validation then rejects the track.

### Affected Code Locations

| File | Lines | Description |
|------|-------|-------------|
| `vibey/operations/roadmap/update.py` | 1275-1278 | Track completion status set |
| `vibey/operations/roadmap/update.py` | 1725-1732 | Status progression in _update_track_progress |
| `vibey/operations/roadmap/status_manager.py` | Various | StatusManager logic |

## Implementation Plan

### Step 1: Find Status Setting Code
- [ ] Search for where `status = Status.COMPLETED` or `status = 'completed'` is set
- [ ] Identify all locations where status is changed without timestamp

### Step 2: Implement Fix

Wherever status is set to completed, also set the timestamp:

```python
# WRONG (current code):
track.status = Status.COMPLETED

# RIGHT (fixed code):
track.status = Status.COMPLETED
if not track.completed:
    track.completed = datetime.now(timezone.utc)
```

### Step 3: Fix All Locations

Locations to fix:
1. `update.py` - `complete_track()` function (lines 1275-1278)
2. `update.py` - `_update_track_progress()` if it sets completed status
3. `status_manager.py` - any status transitions to completed
4. Any sync/recalculate logic that sets status

### Step 4: Add Validation Guard

Add a guard in yaml_dumper.py or the status setter:

```python
def set_status(entity, new_status):
    if new_status == Status.COMPLETED and not entity.completed:
        entity.completed = datetime.now(timezone.utc)
    if new_status in (Status.IN_PROGRESS, Status.COMPLETED) and not entity.started:
        entity.started = datetime.now(timezone.utc)
    entity.status = new_status
```

### Step 5: Add Regression Test
- [ ] Create track with all tasks completed
- [ ] Run status progression/sync
- [ ] Verify track has both `status: completed` AND `completed: <timestamp>`
- [ ] Add test to `tests/operations/roadmap/test_update.py`

### Step 6: Verify Fix
- [ ] Run `vibey roadmap db rebuild`
- [ ] Confirm no "Completed tracks must have a completion date" errors
- [ ] Check all completed tracks have completion dates

## Acceptance Criteria

- [ ] When status is set to `completed`, `completed` timestamp is always set
- [ ] When status is set to `in_progress`, `started` timestamp is always set
- [ ] No validation errors for completed entities without dates
- [ ] Regression test added and passing

## Estimated Effort

- Analysis: 15 minutes
- Implementation: 30 minutes
- Testing: 15 minutes
- **Total: ~1 hour**
