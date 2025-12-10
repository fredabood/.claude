# Bug #11: Database Rebuild Loads 0 Items

**Date:** 2025-12-09
**Severity:** CRITICAL
**Status:** DOCUMENTED

---

## Description

`vibey roadmap db rebuild` reports 0 items loaded.

---

## Root Cause

Database init uses load_roadmap which only gets TrackSummary.

---

## Files Affected

- `vibey/cli/commands.py`
- `vibey/roadmap/serialization/sql_loader.py`

---

## Tasks

1. **Update db_rebuild_cmd to load from ULID files** (development, medium complexity)
2. **Update sql_loader init to iterate tracks/*.yaml** (development, medium complexity)
3. **Add progress reporting during rebuild** (development, low complexity)
4. **Add integration test for database rebuild** (testing, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #11: Database Rebuild Loads 0 Items

### Success Criteria
1. Root cause addressed: Database init uses load_roadmap which only gets TrackSummary.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
