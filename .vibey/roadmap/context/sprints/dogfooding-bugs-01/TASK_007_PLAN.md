# Task 007: Update load_sprint for Backward Compatibility

**Task ID:** dogfooding-bugs-01-task-007
**Bug Addressed:** #8 (blocked field KeyError in v2 format)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The `load_sprint()` function may not handle YAML files without the `blocked` field, which was removed in the v2 ULID migration.

---

## Current State Analysis

Looking at `yaml_loader.py` around line 1057+:

### Sprint Model Validation

From `vibey/roadmap/models/sprint.py:190-193`:
```python
# Validate blocked status matches depends_on
has_unsatisfied_deps = any(not dep.is_satisfied() for dep in self.depends_on)
if self.blocked != has_unsatisfied_deps:
    raise ValueError(f"Blocked flag ({self.blocked}) must match unsatisfied dependencies ({has_unsatisfied_deps})")
```

### Current Loader Code (around line 1293)

```python
blocked=computed_blocked,  # Use computed value instead of YAML value
```

The loader already computes blocked status! This is good.

### Blocked_by Handling (line 1180)

```python
for b in sprint_data.get('blocked_by', []):
```

This already uses `.get()` with default.

---

## Solution Design

The sprint loader appears to already handle v2 format well. Need to verify:

1. **blocked_reason** field handling
2. **depends_on** field handling
3. **blocked_by** field handling
4. Model validation with computed blocked status

### Potential Issues

Line 1296 shows:
```python
blocked_reason=sprint_data.get('blocked_reason'),
```

This is fine - returns None if missing.

---

## Implementation Steps

1. **Audit** `load_sprint()` for any direct key access without `.get()`
2. **Verify** v2 format detection and handling
3. **Check** model validation handles computed blocked correctly
4. **Add** any missing `.get()` calls
5. **Test** with v1 and v2 format sprint YAML files

---

## Files to Review

| File | Lines | Status |
|------|-------|--------|
| `vibey/roadmap/serialization/yaml_loader.py` | 1057-1326 | Review needed |
| `vibey/roadmap/models/sprint.py` | 190-193 | Validation logic |

---

## Key Areas to Check

```python
# Line 1180 - ALREADY CORRECT
for b in sprint_data.get('blocked_by', []):

# Line 1293-1296 - Check these
blocked=computed_blocked,  # Uses computed value - GOOD
blocked_reason=sprint_data.get('blocked_reason'),  # CORRECT

# Need to find where computed_blocked comes from
```

### Computed Blocked Logic (around line 1273)

```python
# Check for blockers and unsatisfied dependencies
has_blockers = len(blocked_by) > 0
has_unsatisfied_deps = any(
    dep.current_status != dep.required_status
    for dep in depends_on
    if isinstance(dep, SprintBlocker) or ...
)
computed_blocked = has_blockers or has_unsatisfied_deps
```

This is already v2-compatible!

---

## Testing Strategy

### Test Case 1: v1 Format Sprint

```yaml
sprint:
  id: test-sprint-v1
  track_id: test-track
  name: Sprint 1
  status: in_progress
  blocked: false
  blocked_by: []
  depends_on: []
```

### Test Case 2: v2 Format Sprint (ULID)

```yaml
sprint:
  id: 01KC3AD75P4TW2MAWDWJC4YCMB
  track_id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  name: Sprint 1
  status: not_started
  # No blocked field - computed
  criteria: []
```

---

## Success Criteria

- [ ] `load_sprint()` handles YAML without `blocked` field
- [ ] `load_sprint()` handles YAML without `blocked_by` field
- [ ] `load_sprint()` handles YAML without `depends_on` field
- [ ] Model validation works with computed blocked status
- [ ] Backward compatible with v1 format

---

## Dependencies

None - can be worked on independently or in parallel with Tasks 005, 006, 008.

---

## Notes

Based on the code review, `load_sprint()` may already be v2-compatible. This task is primarily:
1. Verification/audit of existing code
2. Adding test coverage
3. Documentation

If no changes are needed, document why and add tests to prevent regression.
