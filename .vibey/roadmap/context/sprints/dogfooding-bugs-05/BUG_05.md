# Bug #5: SQLite Database Out of Sync with YAML

**Date:** 2025-12-09
**Severity:** CRITICAL
**Status:** DOCUMENTED

---

## Description

SQLite database out of sync with YAML files after migration.

---

## Root Cause

Migration updated YAML but not SQLite database.

---

## Files Affected

- `.vibey/roadmap.db`
- `vibey/roadmap/serialization/sql_loader.py`

---

## Tasks

1. **Add database sync step to migration script** (development, medium complexity)
2. **Implement automatic db rebuild after YAML changes** (development, high complexity)
3. **Add CLI command to force db resync** (development, medium complexity)
4. **Add integration test for YAML-DB sync** (testing, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #5: SQLite Database Out of Sync with YAML

### Success Criteria
1. Root cause addressed: Migration updated YAML but not SQLite database.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
