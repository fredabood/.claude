# Bug #3: CLI Looks for roadmap.yaml in Wrong Location

**Date:** 2025-12-09
**Severity:** HIGH
**Status:** DOCUMENTED

---

## Description

CLI commands look for roadmap.yaml at wrong location after flat structure migration.

---

## Root Cause

FileSystemManager.get_roadmap_path() returns wrong path.

---

## Files Affected

- `vibey/cli/roadmap_lib/filesystem.py`

---

## Tasks

1. **Update FileSystemManager.get_roadmap_path() to use roadmap_root** (development, low complexity)
2. **Update all callers to use correct path** (development, low complexity)
3. **Add unit test for path resolution** (testing, low complexity)

---

## Sprint Plan

### Goal
Fix Bug #3: CLI Looks for roadmap.yaml in Wrong Location

### Success Criteria
1. Root cause addressed: FileSystemManager.get_roadmap_path() returns wrong path.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
