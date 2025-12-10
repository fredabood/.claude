# Bug #12: New Tracks Missing from roadmap.yaml

**Date:** 2025-12-09
**Severity:** HIGH
**Status:** DOCUMENTED

---

## Description

Tracks created in ULID system don't appear in monolithic roadmap.yaml.

---

## Root Cause

No sync mechanism from ULID files back to roadmap.yaml.

---

## Files Affected

- `.vibey/roadmap/roadmap.yaml`

---

## Tasks

1. **Implement sync mechanism ULID files → roadmap.yaml** (development, medium complexity)
2. **Add CLI command to sync roadmap.yaml** (development, medium complexity)
3. **Consider deprecating roadmap.yaml as source of truth** (research, low complexity)
4. **Add validation to detect sync discrepancies** (development, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #12: New Tracks Missing from roadmap.yaml

### Success Criteria
1. Root cause addressed: No sync mechanism from ULID files back to roadmap.yaml.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
