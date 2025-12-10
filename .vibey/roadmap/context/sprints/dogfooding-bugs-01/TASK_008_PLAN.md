# Task 008: Update load_task for Backward Compatibility

**Task ID:** dogfooding-bugs-01-task-008
**Bug Addressed:** #8 (blocked field KeyError in v2 format)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The `load_task()` and `load_tasks()` functions may not handle YAML files without the `blocked` field, which was removed in the v2 ULID migration.

---

## Current State Analysis

Looking at `yaml_loader.py` around line 1328+:

### Task Model Validation

From `vibey/roadmap/models/task.py:277-280`:
```python
# blocked should be True if ANY dependency in depends_on is not satisfied
has_unsatisfied_deps = any(not dep.is_satisfied() for dep in self.depends_on)
if self.blocked != has_unsatisfied_deps:
    raise ValueError(f"Blocked flag ({self.blocked}) must match unsatisfied dependencies ({has_unsatisfied_deps})")
```

### Current Loader Code (around line 1494)

```python
for b in task_data.get('blocked_by', []):
```

This already uses `.get()` with default - good!

---

## Solution Design

Similar to sprints, the task loader needs to:
1. Use `.get()` for all optional fields
2. Compute `blocked` status if not present
3. Handle both v1 and v2 formats

### Key Fields to Check

- `blocked` - may not exist in v2
- `blocked_by` - may not exist in v2
- `depends_on` - may use different format in v2
- `blocked_reason` - optional field

---

## Implementation Steps

1. **Locate** `load_task()` and `load_tasks()` functions
2. **Audit** for direct `['blocked']` access
3. **Add** `.get('blocked', False)` where needed
4. **Compute** blocked status from dependencies if not present
5. **Handle** v2 format task files (ULID-based)
6. **Test** with v1 and v2 format task YAML files

---

## Files to Modify

| File | Functions | Changes |
|------|-----------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | `load_task()`, `load_tasks()` | Use .get() |
| `vibey/roadmap/models/task.py` | `__post_init__` | Optional: soften validation |

---

## Current v2 Format Task

From ULID migration, task files look like:
```yaml
task:
  id: 01KC3B2K4MNPQ2RABC4DEFGHIJ
  sprint_id: 01KC3AD75P4TW2MAWDWJC4YCMB
  track_id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  title: Implement feature X
  description: ...
  status: not_started
  # No blocked field
  # No blocked_by field (replaced by criteria)
  criteria: []
```

---

## Proposed Fix

```python
# In load_tasks() or _parse_task_data()

# v1 format: use stored blocked value
# v2 format: compute from dependencies/criteria
if 'blocked' in task_data:
    blocked = task_data['blocked']
else:
    # v2 format - compute blocked status
    blocked_by = task_data.get('blocked_by', [])
    depends_on = task_data.get('depends_on', [])

    # Check for unsatisfied dependencies
    has_unsatisfied = False
    for dep in depends_on:
        if isinstance(dep, dict):
            current = dep.get('current_status')
            required = dep.get('required_status', 'completed')
            if current != required:
                has_unsatisfied = True
                break

    blocked = has_unsatisfied or len(blocked_by) > 0
```

---

## Testing Strategy

### Test Case 1: v1 Format Task

```yaml
task:
  id: test-task-v1
  sprint_id: test-sprint
  title: Test Task
  status: not_started
  blocked: false
  blocked_by: []
  depends_on: []
```

### Test Case 2: v2 Format Task (ULID)

```yaml
task:
  id: 01KC3B2K4MNPQ2RABC4DEFGHIJ
  sprint_id: 01KC3AD75P4TW2MAWDWJC4YCMB
  title: Test Task
  status: not_started
  # No blocked field
  criteria: []
```

### Test Case 3: v1 Format with Blockers

```yaml
task:
  id: test-task-blocked
  sprint_id: test-sprint
  title: Blocked Task
  status: not_started
  blocked: true
  blocked_by:
    - blocker_id: other-task
      blocker_type: task
      reason: Waiting for other task
```

---

## Success Criteria

- [ ] `load_task()` handles YAML without `blocked` field
- [ ] `load_tasks()` handles directory with v2 format task files
- [ ] Computed blocked status matches dependency state
- [ ] Model validation works with v2 format
- [ ] Backward compatible with v1 format

---

## Dependencies

None - can be worked on independently or in parallel with Tasks 005-007.

---

## Notes

This is the last of the load_* functions to update. Consider:

1. **Shared helper function** - Extract common blocked computation logic
2. **Format detection** - Use existing `detect_yaml_format()` function
3. **Migration path** - Document how v1 files can be migrated to v2
