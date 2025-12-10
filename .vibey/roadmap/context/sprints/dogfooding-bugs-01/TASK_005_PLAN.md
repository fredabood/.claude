# Task 005: Update load_roadmap to Use .get('blocked', False)

**Task ID:** dogfooding-bugs-01-task-005
**Bug Addressed:** #8 (blocked field KeyError in v2 format)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

In the v2 ULID migration, the `blocked` field was removed from YAML files. This field is now computed from criteria rather than stored explicitly. However, some code paths may still expect the `blocked` key to exist.

### Current State Analysis

Looking at `yaml_loader.py` line 795:
```python
blocked=roadmap_data.get('blocked', False),  # v2: computed from criteria
```

This already uses `.get()` with a default value, so the loader itself is safe. However, the issue may be in:
1. Model validation (requires blocked to match depends_on)
2. Validator code that expects blocked key

---

## Root Cause

The `Roadmap` dataclass model at `vibey/roadmap/models/roadmap.py:170-173` validates:
```python
# Validate blocked status matches blocker list
has_blockers = len(self.blocked_by) > 0
if self.blocked != has_blockers:
    raise ValueError(f"Blocked flag ({self.blocked}) must match blocker list (has_blockers={has_blockers})")
```

When loading v2 format YAML without `blocked_by` list, the model expects consistency.

---

## Solution Design

The loader already handles this correctly with `.get('blocked', False)`. The issue is ensuring:
1. The `blocked_by` list is also handled with a default
2. Model validation accounts for v2 format (no blocked field)

### Verify Current Implementation

```python
# Line 795 in load_roadmap - ALREADY CORRECT
blocked=roadmap_data.get('blocked', False),

# Need to verify blocked_by handling - Line 705
for b in roadmap_data.get('blocked_by', [])  # ALREADY CORRECT
```

---

## Implementation Steps

1. **Audit** `load_roadmap()` function for any direct `['blocked']` access
2. **Verify** that `blocked_by` uses `.get('blocked_by', [])`
3. **Check** model validation logic in `Roadmap.__post_init__`
4. **Add** defensive handling for v2 format (no blockers = not blocked)
5. **Test** with v2 format YAML file (no blocked field)

---

## Files to Review

| File | Lines | Status |
|------|-------|--------|
| `vibey/roadmap/serialization/yaml_loader.py` | 624-810 | ✅ Uses .get() |
| `vibey/roadmap/models/roadmap.py` | 170-173 | ⚠️ May need update |
| `vibey/roadmap/validation/validator.py` | 190-193 | ✅ Checks key exists first |

---

## Proposed Changes

### If model validation needs update:

```python
# In Roadmap.__post_init__ validation
def __post_init__(self):
    # Validate blocked status matches blocker list
    has_blockers = len(self.blocked_by) > 0
    # v2 format: blocked is computed, may not be explicitly set
    if hasattr(self, 'blocked') and self.blocked != has_blockers:
        # Auto-correct in v2 format
        object.__setattr__(self, 'blocked', has_blockers)
```

### If validation should be skipped for v2 format:

Add a flag or detect v2 format and skip validation.

---

## Testing Strategy

Create test YAML files:

### v1 Format (with blocked field):
```yaml
roadmap:
  id: test-v1
  name: Test
  version: 1.0.0
  status: in_progress
  blocked: false
  blocked_by: []
```

### v2 Format (without blocked field):
```yaml
roadmap:
  id: test-v2
  name: Test
  version: 1.0.0
  status: in_progress
  # No blocked field - computed from criteria
```

Test both load successfully.

---

## Success Criteria

- [ ] `load_roadmap()` handles YAML without `blocked` field
- [ ] `load_roadmap()` handles YAML without `blocked_by` field
- [ ] Model validation doesn't fail for v2 format
- [ ] Backward compatible with v1 format

---

## Dependencies

None - this can be worked on independently.

---

## Notes

This task may result in "no changes needed" if the current implementation already handles v2 format correctly. The main value is:
1. Confirming the implementation is correct
2. Adding test coverage
3. Documenting the v1/v2 format handling
