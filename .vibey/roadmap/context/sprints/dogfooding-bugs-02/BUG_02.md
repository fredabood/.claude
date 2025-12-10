# Bug #2: Track Not Showing in roadmap status

**Date:** 2025-12-09
**Severity:** LOW
**Status:** DOCUMENTED

---

## Description

The `vibey roadmap status` command does not display certain tracks in its output.

---

## Root Cause

Track discovery issue in flat structure implementation.

---

## Files Affected

- `vibey/operations/roadmap/query.py`
- `vibey/cli/roadmap_lib/filesystem.py`

---

## Tasks

1. **Debug track discovery in FileSystemManager.list_tracks()** (research, low complexity)
2. **Fix track filtering/discovery logic** (development, medium complexity)
3. **Add integration test for track listing** (testing, low complexity)

---

## Sprint Plan

### Goal
Fix Bug #2: Track Not Showing in roadmap status

### Success Criteria
1. Root cause addressed: Track discovery issue in flat structure implementation.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
