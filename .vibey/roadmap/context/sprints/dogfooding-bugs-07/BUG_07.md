# Bug #7: Validator Doesn't Exclude context/sample_code

**Date:** 2025-12-09
**Severity:** LOW
**Status:** DOCUMENTED

---

## Description

Validator checks files in context/sample_code which are not roadmap data.

---

## Root Cause

Missing exclusion pattern for sample_code directories.

---

## Files Affected

- `vibey/cli/roadmap_lib/validation.py`

---

## Tasks

1. **Add VALIDATION_EXCLUDE_PATTERNS constant** (development, low complexity)
2. **Update validator to skip excluded paths** (development, low complexity)
3. **Add unit test for exclusion patterns** (testing, low complexity)

---

## Sprint Plan

### Goal
Fix Bug #7: Validator Doesn't Exclude context/sample_code

### Success Criteria
1. Root cause addressed: Missing exclusion pattern for sample_code directories.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
