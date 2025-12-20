# Task Plan: Fix blocked_by/depends_on ULID strings cause parsing error

**Task ID:** 01KCY39YJW8A3YDNTFJY5KMDGR
**Priority:** High
**Complexity:** Medium

## Problem Statement

Sprints with simple ULID strings in `blocked_by` or `depends_on` fields cause a `'str' object has no attribute 'get'` error, causing the sprint and all its tasks to be skipped during database load.

### Example Failing YAML

```yaml
sprint:
  blocked_by:
  - 01KCMTYK3KX9Q8B1ZS5Z4MRV7Q   # Simple ULID string - FAILS
  depends_on:
  - 01KCMTYK3KX9Q8B1ZS5Z4MRV7Q   # Simple ULID string - FAILS
```

### Expected Format (Per Code)

```yaml
sprint:
  blocked_by:
  - dependency_id: 01KCMTYK3KX9Q8B1ZS5Z4MRV7Q
    dependency_type: sprint
    current_status: not_started
    required_status: completed
  depends_on:
  - blocker_id: 01KCMTYK3KX9Q8B1ZS5Z4MRV7Q
    blocker_type: sprint
    required_status: completed
    current_status: not_started
```

### Root Cause

In `vibey/roadmap/serialization/yaml_loader.py` lines 1322-1357:
- `blocked_by` parsing has backward compatibility for simple strings (lines 1322-1344)
- `depends_on` parsing does NOT have backward compatibility - it calls `.get()` on each item assuming dict

### Affected Code Locations

| File | Lines | Description |
|------|-------|-------------|
| `vibey/roadmap/serialization/yaml_loader.py` | 1322-1344 | blocked_by parsing (has string support) |
| `vibey/roadmap/serialization/yaml_loader.py` | 1346-1357 | depends_on parsing (MISSING string support) |

## Implementation Plan

### Step 1: Verify Current Code
- [ ] Read yaml_loader.py lines 1322-1357
- [ ] Confirm blocked_by has `isinstance(b, str)` check
- [ ] Confirm depends_on lacks this check

### Step 2: Add String Support to depends_on

```python
# Parse depends_on (new cached dependency tracking)
depends_on = []
for d in sprint_data.get('depends_on', []):
    if isinstance(d, str):
        # Simple string format - just a ULID reference
        depends_on.append(DependencyStatus(
            blocker_id=d,
            blocker_type='sprint',
            required_status='completed',
            current_status='not_started',
            blocks_transition_to='completed',
            last_checked=datetime.now(),
        ))
    elif isinstance(d, dict):
        # Full structured format
        depends_on.append(DependencyStatus(
            blocker_id=d.get('blocker_id', d.get('dependency_id', 'unknown')),
            blocker_type=d.get('blocker_type', d.get('dependency_type', 'sprint')),
            required_status=d.get('required_status', d.get('target_status', 'completed')),
            current_status=d.get('current_status', 'not_started'),
            blocks_transition_to=d.get('blocks_transition_to', 'completed'),
            last_checked=_parse_datetime(d.get('last_checked', datetime.now())),
        ))
```

### Step 3: Add Regression Test
- [ ] Create test sprint YAML with simple ULID strings in both fields
- [ ] Verify sprint loads successfully
- [ ] Add test to `tests/roadmap/serialization/test_yaml_loader.py`

### Step 4: Verify Fix
- [ ] Run `vibey roadmap db rebuild`
- [ ] Confirm Git Submodule Sprint 2 now loads
- [ ] Confirm all 8 tasks in that sprint load

## Acceptance Criteria

- [ ] Simple ULID strings in `blocked_by` field work (already works)
- [ ] Simple ULID strings in `depends_on` field work (fix needed)
- [ ] Both dict and string formats supported for backward compatibility
- [ ] Regression test added and passing
- [ ] Git Submodule Sprint 2 loads successfully

## Estimated Effort

- Analysis: 10 minutes
- Implementation: 20 minutes
- Testing: 15 minutes
- **Total: ~45 minutes**
