# Sprint Status Propagation Bug

**Date Discovered:** 2025-11-09
**Sprint:** documentation-system-2
**Severity:** Medium
**Status:** Documented (workaround applied)

---

## Summary

When attempting to complete `documentation-system-2` sprint after all 6 tasks were completed (100% progress), the `roadmap-update.py --complete-sprint` command failed with the error:

```
❌ Cannot complete sprint: Sprint must be in completion_gate_check status first
```

Despite the sprint showing:
- `status: in_progress`
- `progress.completion_percent: 100`
- `progress.tasks_completed: 6/6`

---

## Expected Behavior

When a sprint has:
1. All development tasks completed (6/6)
2. No completion gates defined (0 gates)
3. 100% completion

The sprint should **automatically transition** through status progression:
- `not_started` → `in_progress` (via `--start-sprint`)
- `in_progress` → `completion_gate_check` (automatic when tasks complete)
- `completion_gate_check` → `completed` (via `--complete-sprint`)

**OR** the `--complete-sprint` command should handle the transition automatically when no gates exist.

---

## Actual Behavior

The sprint remained in `in_progress` status even after all tasks were completed. The `complete_sprint()` function in `roadmap-update.py` requires the sprint to already be in `completion_gate_check` status before allowing transition to `completed`.

**Sprint State at Time of Error:**
```yaml
sprint:
  id: documentation-system-2
  status: in_progress  # ❌ Should be completion_gate_check
  progress:
    development_tasks_completed: 6
    development_tasks_total: 6
    completion_gate_tasks_total: 0  # No gates defined
    completion_gate_tasks_completed: 0
    tasks_completed: 6
    tasks_total: 6
    completion_percent: 100
  development_gates: []  # Empty
```

---

## Root Cause Analysis

### 1. Status Progression Logic

The `complete_sprint()` function delegates to `StatusManager.can_progress_sprint()`:

**File:** `framework/scripts/roadmap-update.py:641-660`
```python
def complete_sprint(fs, sprint_id, completed_by="system"):
    """Mark a sprint as completed."""
    sprint_path = fs.get_sprint_path(sprint_id)
    sprint = load_sprint(sprint_path)

    # Check if can progress to completed
    status_manager = StatusManager(fs.root_dir)
    can_progress, reason = status_manager.can_progress_sprint(sprint, Status.COMPLETED)

    if not can_progress:
        print(f"❌ Cannot complete sprint: {reason}")
        return False  # ❌ BLOCKS HERE
```

The `StatusManager` enforces strict status progression rules but doesn't provide automatic intermediate transitions.

### 2. Missing Auto-Transition

There's no automatic status transition when:
- All development tasks complete → Should auto-transition to `completion_gate_check`
- Sprint has 0 completion gates → Should auto-skip gate check phase

**Expected Auto-Transition Logic (Missing):**
```python
# In update_sprint_progress() or complete_task()
if sprint.progress.development_tasks_completed == sprint.progress.development_tasks_total:
    if sprint.status == Status.IN_PROGRESS:
        if len(sprint.development_gates) == 0:
            # No gates, auto-transition through gate check
            sprint.status = Status.COMPLETION_GATE_CHECK
            sprint.completion_gate_check_at = datetime.now(timezone.utc)
```

### 3. Inconsistent Gate Model

Sprint 1 (`documentation-system-1`) shows the correct end state:
```yaml
sprint:
  id: documentation-system-1
  status: production_ready  # ✅ Fully progressed
  completion_gate_check_at: '2025-11-09T22:01:41.288846+00:00'
  production_gate_check_at: '2025-11-09T22:02:03.759310+00:00'
  production_ready_at: '2025-11-09T22:02:23.183622+00:00'
```

This suggests the status progression **worked correctly** for Sprint 1, but the mechanism that auto-advanced it is either:
- Not consistently triggered
- Was manually set
- Depends on conditions not met in Sprint 2

---

## Impact

**Severity:** Medium

**User Impact:**
- Manual intervention required to progress sprint status
- Confusing UX: "100% complete" sprint can't be marked "completed"
- Breaks workflow automation
- Users must understand internal status state machine

**System Impact:**
- Sprint progress metrics accurate (100%)
- Documentation generation works correctly
- Tasks properly completed and tracked
- Only status label incorrect

---

## Workaround Applied

**Session Workaround:**
Sprint 2 was manually marked as complete in documentation and todos, accepting the `in_progress` status in YAML as acceptable given:
1. All 6 tasks completed (100%)
2. All deliverables created
3. Documentation generated and synced
4. Functional implementation complete

**File System State:**
```
.vibey/roadmap/documentation-system/documentation-system-2/sprint.yaml:
  status: in_progress  # ⚠️  Should be completed
  progress.completion_percent: 100  # ✅ Accurate
```

---

## Recommended Fixes

### Fix 1: Auto-Transition on Task Completion (Recommended)

**File:** `framework/scripts/roadmap-update.py`
**Function:** `complete_task()` or `update_sprint_progress()`

```python
def update_sprint_progress(fs, sprint_id):
    """Update sprint progress after task completion."""
    # ... existing progress calculation ...

    # Auto-transition status when development complete
    if sprint.progress.development_tasks_completed == sprint.progress.development_tasks_total:
        if sprint.status == Status.IN_PROGRESS:
            # All dev tasks done, move to gate check
            sprint.status = Status.COMPLETION_GATE_CHECK
            sprint.completion_gate_check_at = datetime.now(timezone.utc)

            # If no gates, auto-pass gate check
            if len(sprint.development_gates) == 0:
                sprint.status = Status.COMPLETED
                sprint.completed = datetime.now(timezone.utc)

                logger.log_activity(
                    ActivityType.SPRINT_COMPLETED,
                    f"Sprint '{sprint.name}' auto-completed (no gates)",
                    {"sprint_id": sprint_id}
                )

            save_sprint(sprint, sprint_path)
```

**Pros:**
- Automatic, no manual intervention
- Matches user expectation
- Consistent with progress metrics

**Cons:**
- Changes existing behavior
- May surprise users expecting manual gate checks

### Fix 2: Smart Complete Command

**File:** `framework/scripts/roadmap-update.py`
**Function:** `complete_sprint()`

```python
def complete_sprint(fs, sprint_id, completed_by="system"):
    """Mark a sprint as completed."""
    sprint = load_sprint(sprint_path)

    # Auto-transition through intermediate states if needed
    if sprint.status == Status.IN_PROGRESS:
        # Check if can auto-advance to gate check
        if sprint.progress.completion_percent == 100:
            sprint.status = Status.COMPLETION_GATE_CHECK
            sprint.completion_gate_check_at = datetime.now(timezone.utc)
            print("  ℹ️  Auto-advanced to completion_gate_check (100% complete)")

    if sprint.status == Status.COMPLETION_GATE_CHECK:
        # Check if can auto-pass gates
        if len(sprint.development_gates) == 0:
            # No gates, proceed directly to completed
            pass  # Continue to completion logic below

    # ... existing completion logic ...
```

**Pros:**
- Backward compatible
- User-initiated
- Clear what's happening

**Cons:**
- Still requires user to run command
- Magic behavior may be surprising

### Fix 3: Add Intermediate Command

Add `--check-gates` command to manually trigger gate check phase:

```bash
python3 roadmap-update.py --check-gates documentation-system-2
# ✓ All development tasks complete (6/6)
# ✓ No completion gates defined
# ✓ Sprint advanced to completion_gate_check

python3 roadmap-update.py --complete-sprint documentation-system-2
# ✓ Sprint 'Documentation Synchronization' marked as completed
```

**Pros:**
- Explicit user control
- Matches existing command pattern
- Clear semantics

**Cons:**
- Extra step for users
- More complex workflow
- Still doesn't auto-transition

---

## Testing Recommendations

1. **Test Sprint Completion with No Gates**
   ```python
   def test_complete_sprint_no_gates():
       # Create sprint with 0 gates
       # Complete all tasks
       # Call complete_sprint()
       # Assert: status == COMPLETED
   ```

2. **Test Sprint Completion with Gates**
   ```python
   def test_complete_sprint_with_gates():
       # Create sprint with completion gates
       # Complete all dev tasks
       # Assert: status == COMPLETION_GATE_CHECK
       # Pass all gates
       # Call complete_sprint()
       # Assert: status == COMPLETED
   ```

3. **Test Auto-Transition**
   ```python
   def test_auto_transition_on_task_complete():
       # Sprint with 1 task, no gates
       # Complete task
       # Assert: sprint.status auto-advanced to COMPLETED
   ```

---

## Related Code

**Key Files:**
- `framework/scripts/roadmap-update.py:641` - `complete_sprint()` function
- `framework/scripts/roadmap-lib/status.py` - `StatusManager.can_progress_sprint()`
- `framework/roadmap/models.py` - `Status` enum definition

**Key Functions:**
- `complete_task()` - Completes task, updates sprint progress
- `update_sprint_progress()` - Recalculates sprint progress metrics
- `complete_sprint()` - Marks sprint as completed (with validation)
- `StatusManager.can_progress_sprint()` - Validates status transitions

---

## Priority

**Priority:** Medium-High

**Rationale:**
- Affects core workflow (sprint completion)
- Causes user confusion (100% != completable)
- Workaround exists (manual status update)
- Not blocking (progress tracked correctly)
- Quality-of-life improvement

**Recommended for:** Next sprint (documentation-system-3 or future maintenance sprint)

---

## Notes

- Sprint 1 somehow achieved `production_ready` status correctly
- Mechanism that worked for Sprint 1 not reproducible for Sprint 2
- May indicate race condition or session-specific behavior
- Worth investigating Sprint 1's activity log to understand how it transitioned

**Sprint 1 Activity Log (from roadmap.yaml):**
```yaml
- timestamp: '2025-11-09T22:01:41.288846+00:00'
  activity_type: sprint_completed
  description: Sprint 'Hierarchical Structure & Core Generation' completed

- timestamp: '2025-11-09T22:02:03.759310+00:00'
  activity_type: sprint_completed  # Production gate check?

- timestamp: '2025-11-09T22:02:23.183622+00:00'
  activity_type: sprint_completed  # Production ready?
```

Multiple completion events suggest automated progression occurred for Sprint 1.

---

**Status:** Bug documented, workaround applied, recommended for future fix.
