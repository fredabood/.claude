# Bug #9: Pre-commit Hook Database Error

**Date:** 2025-12-09
**Severity:** MEDIUM
**Status:** DOCUMENTED

---

## Description

Pre-commit hook fails with 'no such column: is_dirty' error.

---

## Root Cause

Database schema out of date or hook queries non-existent column.

---

## Files Affected

- `.vibey/hooks/`

---

## Tasks

1. **Investigate is_dirty column in schema history** (research, low complexity)
2. **Update pre-commit hook to use correct schema** (development, medium complexity)
3. **Add database migration script for schema updates** (development, medium complexity)
4. **Test pre-commit hook with fresh database** (testing, low complexity)

---

## Sprint Plan

### Goal
Fix Bug #9: Pre-commit Hook Database Error

### Success Criteria
1. Root cause addressed: Database schema out of date or hook queries non-existent column.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
