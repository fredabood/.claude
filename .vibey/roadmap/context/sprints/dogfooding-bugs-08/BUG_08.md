# Bug #8: YAML Loader Missing blocked Field

**Date:** 2025-12-09
**Severity:** CRITICAL
**Status:** DOCUMENTED

---

## Description

yaml_loader.py expects 'blocked' field but v2 migration removed it.

---

## Root Cause

v1_to_v2.py removed blocked field but loader still requires it.

---

## Files Affected

- `vibey/roadmap/serialization/yaml_loader.py`

---

## Tasks

1. **Update load_roadmap to use .get('blocked', False)** (development, low complexity)
2. **Update load_track for backward compatibility** (development, low complexity)
3. **Update load_sprint for backward compatibility** (development, low complexity)
4. **Update load_task for backward compatibility** (development, low complexity)
5. **Add migration test for v1 to v2 loading** (testing, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #8: YAML Loader Missing blocked Field

### Success Criteria
1. Root cause addressed: v1_to_v2.py removed blocked field but loader still requires it.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
