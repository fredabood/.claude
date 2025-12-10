# Task 006: Update load_track for Backward Compatibility

**Task ID:** dogfooding-bugs-01-task-006
**Bug Addressed:** #8 (blocked field KeyError in v2 format)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The `load_track()` function may not handle YAML files without the `blocked` field, which was removed in the v2 ULID migration.

---

## Current State Analysis

Looking at `yaml_loader.py` around line 815+, the `load_track()` function needs review for:
1. Direct access to `['blocked']` key
2. Access to `['blocked_by']` without default
3. Model validation requiring `blocked` field

### Track Model Validation

From `vibey/roadmap/models/track.py:165-168`:
```python
# Validate blocked status matches depends_on
has_unsatisfied_deps = any(not dep.is_satisfied() for dep in self.depends_on)
if self.blocked != has_unsatisfied_deps:
    raise ValueError(f"Blocked flag ({self.blocked}) must match unsatisfied dependencies ({has_unsatisfied_deps})")
```

---

## Solution Design

### 1. Audit load_track for blocked field access

Search for patterns:
- `track_data['blocked']` - needs `.get('blocked', False)`
- `track_data['blocked_by']` - needs `.get('blocked_by', [])`

### 2. Handle v2 format in load_track

v2 format tracks may not have:
- `blocked` field (computed from criteria)
- `blocked_by` field (replaced by criteria with CompletableTarget)
- `depends_on` in old format

### Proposed Fix

```python
# In load_track()
# Compute blocked status from depends_on or blocked_by
blocked_by = track_data.get('blocked_by', [])
depends_on = track_data.get('depends_on', [])

# For v2 format, blocked is computed
# For v1 format, use stored value
if 'blocked' in track_data:
    blocked = track_data['blocked']
else:
    # v2 format: compute from dependencies
    has_unsatisfied = any(
        dep.get('current_status') != dep.get('required_status', 'completed')
        for dep in depends_on
        if isinstance(dep, dict)
    )
    blocked = has_unsatisfied or len(blocked_by) > 0
```

---

## Implementation Steps

1. **Find** all direct `['blocked']` or `['blocked_by']` access in load_track()
2. **Replace** with `.get()` and appropriate defaults
3. **Add** v2 format detection (use `detect_yaml_format()`)
4. **Compute** blocked status if not present in v2 format
5. **Update** model validation to handle computed blocked
6. **Test** with v1 and v2 format track YAML files

---

## Files to Modify

| File | Function | Changes |
|------|----------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | `load_track()` | Use .get() for blocked fields |
| `vibey/roadmap/models/track.py` | `__post_init__` | Optional: soften validation |

---

## v1 vs v2 Format Detection

The `detect_yaml_format()` function already exists (line 156). Use it:

```python
def load_track(file_path: Union[str, Path]) -> Track:
    ...
    track_data = data['track']
    format_version = detect_yaml_format(track_data)

    if format_version == 'v2':
        # Handle v2 format - compute blocked from criteria
        blocked = compute_blocked_status(track_data)
    else:
        # v1 format - use stored value
        blocked = track_data.get('blocked', False)
```

---

## Testing Strategy

### Test Case 1: v1 Format Track

```yaml
track:
  id: test-track-v1
  name: Test Track
  status: in_progress
  blocked: false
  blocked_by: []
  depends_on: []
  progress:
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
```

### Test Case 2: v2 Format Track (ULID)

```yaml
track:
  id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  name: Test Track
  status: in_progress
  # No blocked field - computed from criteria
  criteria: []
  progress:
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0.0
```

---

## Success Criteria

- [ ] `load_track()` handles YAML without `blocked` field
- [ ] `load_track()` handles YAML without `blocked_by` field
- [ ] `load_track()` handles YAML without `depends_on` field
- [ ] Model validation doesn't fail for v2 format
- [ ] Backward compatible with v1 format

---

## Dependencies

None - can be worked on independently or in parallel with Task 005.

---

## Notes

The same pattern applies to Sprint and Task loaders (Tasks 007 and 008). Consider extracting a shared helper function:

```python
def _compute_blocked_status(data: Dict[str, Any], format_version: str) -> bool:
    """Compute blocked status for v1 or v2 format."""
    if 'blocked' in data:
        return data['blocked']
    # v2 format: compute from dependencies
    return False  # Default to not blocked
```
