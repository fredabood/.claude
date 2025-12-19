# Post-Mortem: Sprint Progress Auto-Update Bug Fix

## Task Information
- **Task ID:** 01KCVMA0F3G5XHEG45BX363K6V
- **Sprint:** Sprint 24: Progress Tracking and CLI Validation Bugs
- **Track:** CLI Dogfooding Bug Fixes (01KC39XSXJ39N12HWJ93F77KQ9)
- **Completed:** 2025-12-19

## Problem Summary

When tasks were completed by directly editing their YAML files (setting `status: completed`), the parent sprint's progress counters (`tasks_completed`, `tasks_total`, `completion_percent`) were not updated. This caused sprints to show 0% progress even when all tasks were done.

## Root Cause Analysis

### Multiple Contributing Factors

1. **V1 vs V2 Format Incompatibility**
   - V1 format tasks use `sprint_id` field to reference their parent sprint
   - V2 format tasks use `parent_ref` field instead
   - The `_update_sprint_progress()` function only checked `sprint_id`, missing V2 format tasks

2. **No Automatic Progress Sync**
   - CLI commands like `vibey roadmap complete` properly called `_update_sprint_progress()` after task completion
   - Direct YAML edits bypassed this logic entirely
   - No mechanism existed to detect and sync stale progress counters

3. **Database Views vs YAML Source of Truth**
   - SQLite views (`v_sprint_progress`) correctly computed progress from task statuses
   - But CLI status commands read progress from YAML files directly
   - YAML files stored static progress counters that were never updated on direct edits

## Solution Implemented

### 1. New CLI Command: `vibey roadmap sync-progress`

Added a dedicated command to recalculate all progress counters from actual task statuses:

```bash
vibey roadmap sync-progress         # Sync all progress counters
vibey roadmap sync-progress --verify  # Verify consistency after sync
vibey roadmap sync-progress -v      # Verbose output
```

**File:** `/vibey/cli/main.py` (lines 1080-1117)

### 2. Enhanced `db rebuild` Command

Modified `vibey roadmap db rebuild` to automatically sync progress counters after rebuilding:

```python
# After db_init_cmd succeeds:
from vibey.operations.roadmap import recalculate_all
sync_result = recalculate_all(root_dir, verify=False)
```

**File:** `/vibey/cli/commands_legacy.py` (lines 3384-3391)

### 3. V2 Format Task Support in Progress Calculation

Updated `_update_sprint_progress()` to handle V2 format tasks that use `parent_ref`:

```python
# When load_task() fails (often for v2 format), try raw YAML parse
parent_ref = task_data.get('parent_ref', '')
if parent_ref == sprint_ulid:
    # Create mock task for progress counting
    mock_task.task_type = task_type
    mock_task.status = TaskStatus(task_status_str)
    tasks.append(mock_task)
```

**File:** `/vibey/operations/roadmap/update.py` (lines 1546-1578)

## Files Changed

1. `/vibey/cli/main.py` - Added `sync-progress` command
2. `/vibey/cli/commands_legacy.py` - Enhanced `db_rebuild_cmd` to auto-sync progress
3. `/vibey/operations/roadmap/update.py` - Added V2 format support in `_update_sprint_progress()`

## Testing Results

Before fix:
```
Progress before update: tasks_total=0, tasks_completed=0
```

After fix:
```
Progress after update: tasks_total=3, tasks_completed=3
SUCCESS: Sprint now shows tasks!
```

## Recommendations

### Short-term

1. **Run `vibey roadmap sync-progress`** after pulling changes that include completed tasks
2. Use `vibey roadmap db rebuild` which now auto-syncs progress
3. Prefer using `vibey roadmap complete <task-id>` over direct YAML edits

### Long-term

1. Consider adding a git hook to auto-sync progress on commit/pull
2. Migrate all V1 format tasks to V2 format for consistency
3. Add validation warning when progress counters drift from actual task counts

## Lessons Learned

1. **Format versioning needs comprehensive testing** - The V2 format migration created edge cases that weren't caught during development
2. **Computed vs stored values** - When both exist, sync mechanisms must be explicit
3. **User workflows matter** - Direct YAML editing is a valid workflow that must be supported

## Related Issues

- Track completion validation error (separate bug in same sprint)
- CLI complete command validation issues (separate bug in same sprint)
