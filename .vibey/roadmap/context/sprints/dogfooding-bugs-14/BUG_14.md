# Bug #14: Duplicate roadmap.yaml Files

**Date:** 2025-12-09
**Severity:** HIGH
**Status:** FIXED

---

## Description

Two roadmap.yaml files existed with different data.

---

## Root Cause

Bug #3 caused CLI to use wrong location.

---

## Files Affected

None identified

---

## Tasks

1. **Verify single roadmap.yaml exists at correct location** (testing, low complexity)
2. **Add startup check to warn if duplicate exists** (development, low complexity)
3. **Document canonical location in CLAUDE.md** (documentation, low complexity)

---

## Sprint Plan

### Goal
Fix Bug #14: Duplicate roadmap.yaml Files

### Success Criteria
1. Root cause addressed: Bug #3 caused CLI to use wrong location.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
