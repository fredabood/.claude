# Task Plan: Fix track status not auto-updating to in_progress

**Task ID:** 01KCY39YJW8A3YDNTFJY5KMDGS
**Priority:** Medium
**Complexity:** Medium

## Problem Statement

Tracks remain in `not_started` status even when tasks have been started or completed. This requires manual status updates and causes confusion about actual project state.

### Example

```yaml
# Track shows not_started...
track:
  status: not_started

# ...but tasks are completed
task:
  status: completed
  completed_at: '2025-12-19T19:00:00+00:00'
```

### Root Cause

The status progression logic in `vibey/operations/roadmap/update.py` (`_update_track_progress()`) uses `StatusManager.progress_track_status()` which only progresses status forward when all criteria are met. It doesn't automatically set `in_progress` when work begins.

### Affected Code Locations

| File | Lines | Description |
|------|-------|-------------|
| `vibey/operations/roadmap/update.py` | 1725-1732 | Status progression call |
| `vibey/operations/roadmap/status_manager.py` | Various | StatusManager.progress_track_status() |

## Implementation Plan

### Step 1: Analyze Current Status Logic
- [ ] Read update.py lines 1683-1752 (`_update_track_progress()`)
- [ ] Read StatusManager.progress_track_status() implementation
- [ ] Understand current status transition rules

### Step 2: Identify Fix Location

The fix should be in `_update_track_progress()`:

```python
def _update_track_progress(track, sprints, fs):
    # ... existing progress calculation ...

    # NEW: Auto-update to in_progress if work has started
    if track.status == Status.NOT_STARTED:
        # Check if any sprint is in_progress or completed
        has_active_work = any(
            s.status in (Status.IN_PROGRESS, Status.COMPLETED, Status.PRODUCTION_READY)
            for s in sprints
        )
        # Or check if any task is in_progress or completed
        if not has_active_work:
            for sprint in sprints:
                tasks = load_tasks_for_sprint(sprint.id, fs)
                has_active_work = any(
                    t.status in (TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)
                    for t in tasks
                )
                if has_active_work:
                    break

        if has_active_work:
            track.status = Status.IN_PROGRESS
            track.started = track.started or datetime.now(timezone.utc)
            print(f"🔄 Track '{track.name}' auto-updated to in_progress")

    # ... rest of existing logic ...
```

### Step 3: Handle Edge Cases
- [ ] Track with `started` date but `not_started` status → set to `in_progress`
- [ ] Track with completed tasks but `not_started` status → set to `in_progress`
- [ ] Don't regress status (in_progress → not_started)

### Step 4: Add Regression Test
- [ ] Create track with not_started status
- [ ] Add task with completed status
- [ ] Run progress update
- [ ] Verify track status changed to in_progress
- [ ] Add test to `tests/operations/roadmap/test_update.py`

### Step 5: Verify Fix
- [ ] Run `vibey roadmap db rebuild`
- [ ] Confirm tracks with active work show in_progress
- [ ] Confirm started date is set automatically

## Acceptance Criteria

- [ ] Tracks auto-update to `in_progress` when any task starts
- [ ] Tracks auto-update to `in_progress` when any sprint starts
- [ ] `started` date is set automatically if missing
- [ ] Status never regresses (in_progress → not_started)
- [ ] Regression test added and passing

## Estimated Effort

- Analysis: 20 minutes
- Implementation: 45 minutes
- Testing: 20 minutes
- **Total: ~1.5 hours**
