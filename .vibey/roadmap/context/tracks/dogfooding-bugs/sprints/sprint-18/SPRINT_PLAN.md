# Sprint 18: Edit Command Validation Bugs

**Sprint ID:** 01KCMQCNPM0H28BW0WQ02PDESG
**Track:** CLI Dogfooding Bug Fixes (01KC39XSXJ39N12HWJ93F77KQ9)
**Status:** not_started
**Tasks:** 1 total, 0 completed

---

## Sprint Overview

This sprint addresses a validation gap in the `vibey roadmap edit file` command where setting `status=completed` does not require a completion date timestamp.

## Root Cause Analysis

### Current Validation State

The `SafeYAMLEditor` in `vibey/operations/roadmap/safe_yaml_editor.py` has inconsistent completion validation:

| Entity | Status Enum Check | Completion Date Check |
|--------|-------------------|----------------------|
| Task   | Yes (line 473)    | **Yes** (lines 498-500) |
| Sprint | Yes (line 528)    | **No** (missing) |
| Track  | Yes (line 556)    | **No** (missing) |

### Task Validation (Correct)
```python
# Lines 498-500 in safe_yaml_editor.py
if task.get('status') == 'completed':
    if not task.get('completed'):
        result.add_error("Task marked completed but 'completed' timestamp missing")
```

### Sprint Validation (Missing Check)
```python
# Lines 526-530 - only validates status enum
if 'status' in sprint:
    valid_statuses = ['not_started', 'in_progress', 'completion_gate_check', 'completed']
    if sprint['status'] not in valid_statuses:
        result.add_error(f"Invalid status: ...")
# MISSING: completion date check when status='completed'
```

### Track Validation (Missing Check)
```python
# Lines 554-558 - only validates status enum
if 'status' in track:
    valid_statuses = ['not_started', 'in_progress', 'blocked', 'completed']
    if track['status'] not in valid_statuses:
        result.add_error(f"Invalid status: ...")
# MISSING: completion date check when status='completed'
```

---

## Tasks

### Task 1: Fix edit file command to require completion date when setting completed status

**ID:** 01KCMQCWDAE9HMY14VRSSTA5FR
**Type:** development
**Complexity:** simple
**Priority:** high

#### Problem Statement
The `vibey roadmap edit file` command allows setting `status=completed` on sprints and tracks without requiring a `completed` timestamp. This creates inconsistent data that causes issues during database loading (entries are silently skipped).

#### Implementation Plan

1. **Add sprint completion validation** in `_validate_sprint_yaml` (after line 530):
   ```python
   # Validate completion logic
   if sprint.get('status') == 'completed':
       if not sprint.get('completed'):
           result.add_error("Sprint marked completed but 'completed' timestamp missing")
   ```

2. **Add track completion validation** in `_validate_track_yaml` (after line 558):
   ```python
   # Validate completion logic
   if track.get('status') == 'completed':
       if not track.get('completed'):
           result.add_error("Track marked completed but 'completed' timestamp missing")
   ```

#### Files to Modify
- `vibey/operations/roadmap/safe_yaml_editor.py`
  - `_validate_sprint_yaml()` - Add completion timestamp check
  - `_validate_track_yaml()` - Add completion timestamp check

#### Acceptance Criteria
- [ ] `vibey roadmap edit file sprints/X.yaml --set sprint.status=completed` fails with clear error if no completion date
- [ ] `vibey roadmap edit file tracks/X.yaml --set track.status=completed` fails with clear error if no completion date
- [ ] Setting status=completed with a completion date still works
- [ ] Task completion validation remains unchanged (already correct)

---

## Testing Strategy

1. **Manual Testing**
   ```bash
   # Should fail - no completion date
   vibey roadmap edit file .vibey/roadmap/sprints/01KCMQCNPM0H28BW0WQ02PDESG.yaml \
     --set sprint.status=completed

   # Should succeed - has completion date
   vibey roadmap edit file .vibey/roadmap/sprints/01KCMQCNPM0H28BW0WQ02PDESG.yaml \
     --set sprint.status=completed \
     --set sprint.completed=2025-12-17T00:00:00Z
   ```

2. **Verify Consistency**
   - All three entity types (task, sprint, track) should have the same validation pattern
   - Error messages should be clear and actionable

---

## Notes

- This bug was discovered during Sprint 17 work when fixing sprint status mismatches
- The database loader silently skips entries marked completed without timestamps, causing data loss
