# Bug Fix: Sprint Status Auto-Progression from NOT_STARTED

**Date**: 2025-11-20
**Issue**: `--recalculate-all` and `--refresh-progress` didn't auto-progress sprints in `not_started` status
**Root Cause**: `StatusManager.progress_sprint_status()` only handled `in_progress` → `completion_gate_check` and later transitions
**Fix**: Added `NOT_STARTED` → `IN_PROGRESS` case to status progression logic

## The Problem

When completing all tasks in Sprint 9, the following happened:

1. ✅ Tasks marked as complete (using `roadmap complete <task-id>`)
2. ✅ Sprint progress updated to 100% (4/4 tasks completed)
3. ❌ Sprint status stuck at `not_started`
4. ❌ `--recalculate-all` didn't auto-progress the sprint
5. ❌ `--refresh-progress` didn't auto-progress the sprint

**Expected behavior**: Sprint should auto-progress through status transitions:
- `not_started` → `in_progress` (when tasks completed)
- `in_progress` → `completion_gate_check` (when all dev tasks done)
- `completion_gate_check` → `completed` (when gates passed)

**Actual behavior**: Sprint stayed in `not_started` despite all tasks being complete.

## Root Cause Analysis

### The Bug Location

**File**: `vibey/cli/roadmap_lib/status.py` (and `vibey/cli/roadmap-lib/status.py`)

**Function**: `StatusManager.progress_sprint_status()`

**Problem code**:
```python
def progress_sprint_status(self, sprint: Sprint):
    current_status = sprint.status

    # Define progression path
    if current_status == Status.IN_PROGRESS:  # ← Missing NOT_STARTED case!
        can_progress, reason = self.can_progress_sprint(sprint, Status.COMPLETION_GATE_CHECK)
        if can_progress:
            return True, Status.COMPLETION_GATE_CHECK, reason
        else:
            return False, None, f"Cannot progress: {reason}"

    elif current_status == Status.COMPLETION_GATE_CHECK:
        ...

    else:
        return False, None, f"No automatic progression from status: {current_status}"
        # ↑ This was triggered for NOT_STARTED status!
```

### Why This Happened

The status progression logic only handled these transitions:
- ✅ `IN_PROGRESS` → `COMPLETION_GATE_CHECK`
- ✅ `COMPLETION_GATE_CHECK` → `COMPLETED` → `PRODUCTION_GATE_CHECK`
- ✅ `PRODUCTION_GATE_CHECK` → `PRODUCTION_READY`
- ❌ `NOT_STARTED` → anything (missing!)

When `update_sprint_progress()` was called:
1. Sprint progress was recalculated correctly (4/4 tasks = 100%)
2. `progress_sprint_status()` was called to check for status transitions
3. Hit the `else` clause: `"No automatic progression from status: not_started"`
4. Sprint stayed in `not_started` status
5. Progress saved but status unchanged

## The Workaround (Bad Approach)

**What I initially did** (wrong):
1. Created `--progress-sprint` command to manually force progression
2. Used it to progress Sprint 9 manually
3. This worked but was treating symptoms, not the root cause

**Why this was wrong**:
- Created technical debt (workaround command)
- Didn't fix the underlying issue
- Would need manual intervention for every sprint
- Other users would hit the same bug

## The Proper Fix (Good Approach)

**What I should have done** (and did after you pointed it out):

### 1. Added NOT_STARTED Case to Status Progression

**File**: `vibey/cli/roadmap_lib/status.py` (lines 104-112)

**Added code**:
```python
def progress_sprint_status(self, sprint: Sprint):
    current_status = sprint.status

    # Define progression path
    if current_status == Status.NOT_STARTED:  # ← NEW CASE
        # Auto-start sprint if tasks have been completed or if progress has been made
        if sprint.progress.tasks_completed > 0:
            return True, Status.IN_PROGRESS, "Tasks have been completed, auto-starting sprint"
        elif sprint.progress.tasks_total > 0 and sprint.started is not None:
            # Sprint was explicitly started
            return True, Status.IN_PROGRESS, "Sprint was started"
        else:
            return False, None, "No tasks started yet"

    elif current_status == Status.IN_PROGRESS:
        ...
```

### 2. Removed Workaround Command

**File**: `vibey/cli/roadmap-update.py`

**Removed**:
- `--progress-sprint` argument definition
- `--progress-sprint` handler logic (~40 lines)

**Kept**:
- `--refresh-progress` (now works correctly)
- `--recalculate-all` (now works correctly)

### 3. Applied to Both Status Files

Fixed in both locations:
- `vibey/cli/roadmap_lib/status.py` (underscore version)
- `vibey/cli/roadmap-lib/status.py` (hyphen version - duplicate)

## Testing the Fix

### Test Scenario

Created mock sprint with:
- Status: `NOT_STARTED`
- Tasks completed: 4/4 (100%)
- Expected: Auto-progress to `IN_PROGRESS`

### Test Result

```bash
$ python3 test_fix.py

Sprint status: Status.NOT_STARTED
Tasks completed: 4/4

Result:
  Progressed: True
  New status: Status.IN_PROGRESS
  Message: Tasks have been completed, auto-starting sprint

✅ SUCCESS: NOT_STARTED status is now handled correctly!
```

### Verification

```bash
# Verify workaround command removed
$ python3 vibey/cli/roadmap-update.py --help | grep progress-sprint
# (no output - command removed)

# Verify existing commands still work
$ python3 vibey/cli/roadmap-update.py --help | grep -A 2 refresh-progress
  --refresh-progress    Refresh all progress calculations
```

## How It Works Now

### Automatic Progression Flow

When `--recalculate-all` or `--refresh-progress` is run:

1. **Load sprint** from YAML file
2. **Load tasks** from hierarchical directory structure
3. **Calculate progress** from task statuses
4. **Update sprint.progress** fields
5. **Check for status progression**:
   - If `NOT_STARTED` + tasks completed > 0 → `IN_PROGRESS`
   - If `IN_PROGRESS` + all dev tasks done → `COMPLETION_GATE_CHECK`
   - If `COMPLETION_GATE_CHECK` + all gates passed → `COMPLETED` → `PRODUCTION_GATE_CHECK`
   - etc.
6. **Save updated sprint** with new status and timestamp
7. **Update track progress** (cascading updates)

### Expected Behavior

For Sprint 9 scenario (all tasks complete, sprint in `not_started`):

**Before fix**:
```bash
$ python3 vibey/cli/roadmap-update.py --recalculate-all
🔄 Recalculating entire roadmap hierarchy...
  ✅ 12 sprints recalculated
# Sprint 9 stays in not_started status
```

**After fix**:
```bash
$ python3 vibey/cli/roadmap-update.py --recalculate-all
🔄 Recalculating entire roadmap hierarchy...
🎉 Sprint 'CLI State Management Bugs' progressed to in_progress: Tasks have been completed, auto-starting sprint
🎉 Sprint 'CLI State Management Bugs' progressed to completion_gate_check: All development tasks completed
  ✅ 12 sprints recalculated
# Sprint 9 auto-progresses through TWO transitions in one recalculation!
```

## Lessons Learned

### What I Did Wrong

1. **Treated symptoms instead of root cause**: Created workaround command instead of fixing the bug
2. **Didn't investigate thoroughly**: Should have debugged why existing commands failed
3. **Created technical debt**: Workaround command would need maintenance

### What I Should Have Done

1. **Debug the existing commands first**: Understand why `--recalculate-all` didn't work
2. **Find and fix root cause**: Missing `NOT_STARTED` case in status progression
3. **Test the fix**: Verify existing commands now work correctly
4. **No new commands needed**: Leverage existing infrastructure

### Good Engineering Practices

✅ **Fix root causes, not symptoms**
✅ **Understand existing code before adding new code**
✅ **Minimize technical debt**
✅ **Test fixes thoroughly**
✅ **Remove workarounds after proper fix**

## Impact

### Immediate Impact

- ✅ `--recalculate-all` now handles all sprint statuses
- ✅ `--refresh-progress` now handles all sprint statuses
- ✅ Sprints auto-progress through entire lifecycle
- ✅ No manual intervention needed
- ✅ Cleaner codebase (removed workaround)

### Long-Term Impact

- ✅ Future sprints will auto-progress correctly
- ✅ Less manual status management
- ✅ More reliable roadmap state tracking
- ✅ Easier for other users to work with roadmap system

## Files Modified

1. **vibey/cli/roadmap_lib/status.py** (lines 104-112)
   - Added `NOT_STARTED` case to `progress_sprint_status()`

2. **vibey/cli/roadmap-lib/status.py** (lines 104-112)
   - Added `NOT_STARTED` case to `progress_sprint_status()` (duplicate file)

3. **vibey/cli/roadmap-update.py**
   - Removed `--progress-sprint` argument (lines 1093-1097 deleted)
   - Removed `--progress-sprint` handler (lines 1155-1197 deleted)

## Related Issues

This bug likely affected:
- Any sprint that had tasks completed before being explicitly started
- Development workflows where tasks were completed incrementally
- Batch completion scenarios (completing multiple tasks at once)

## Prevention

To prevent similar bugs in the future:

1. **Complete status coverage**: Ensure all status transition cases are handled
2. **Test edge cases**: Test with sprints in all possible statuses
3. **Integration tests**: Test full workflows (create → start → complete)
4. **Code review**: Check for missing enum cases in switch/if-elif chains
5. **Documentation**: Document expected status transitions clearly

---

**Status**: ✅ Bug fixed and workaround removed
**Fix verified**: Tested and working correctly
**Impact**: High - affects all sprint status progressions
**Priority**: Critical - was blocking basic roadmap workflows
