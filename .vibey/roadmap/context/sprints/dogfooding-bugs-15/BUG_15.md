# Bug #15: No CLI Commands to Create Tracks/Sprints/Tasks

**Date:** 2025-12-09
**Severity:** HIGH
**Status:** DOCUMENTED

---

## Description

CLI lacks commands to create new tracks/sprints/tasks in ULID structure.

---

## Root Cause

ULID migration focused on data migration, not CLI operations.

---

## Files Affected

- `vibey/cli/roadmap_create_from_plan.py`
- `vibey/cli/commands.py`

---

## Tasks

1. **Add create track CLI command** (development, medium complexity)
2. **Add create sprint CLI command** (development, medium complexity)
3. **Add create task CLI command** (development, medium complexity)
4. **Update create-from-plan to use ULID flat structure** (development, high complexity)
5. **Create ULIDManager for ULID generation** (development, low complexity)
6. **Add integration tests for create commands** (testing, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #15: No CLI Commands to Create Tracks/Sprints/Tasks

### Success Criteria
1. Root cause addressed: ULID migration focused on data migration, not CLI operations.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
