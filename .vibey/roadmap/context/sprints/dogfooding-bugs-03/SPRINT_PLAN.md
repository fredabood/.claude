# Sprint 3: Database Synchronization

**Bugs Addressed:** #5, #9, #11
**Priority:** HIGH
**Status:** NOT_STARTED

---

## Description

Fix SQLite database backend to properly sync with YAML files. Update schema, fix rebuild command, and ensure pre-commit hook works.

---

## Goal

SQLite backend works correctly with ULID file system

---

## Success Criteria

- Database rebuild loads all 39 tracks, 213 sprints, 1125 tasks
- Pre-commit hook runs without is_dirty error
- Database stays in sync with YAML changes

---

## Dependencies

- dogfooding-bugs-02

---

## Tasks (12 total)

### Bug #5: SQLite Database Out of Sync with YAML

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 001 | Add database sync step to migration script | Development | Medium | [TASK_001_PLAN.md](./TASK_001_PLAN.md) |
| 002 | Implement automatic DB rebuild after YAML changes | Development | High | [TASK_002_PLAN.md](./TASK_002_PLAN.md) |
| 003 | Add CLI command to force DB resync | Development | Medium | [TASK_003_PLAN.md](./TASK_003_PLAN.md) |
| 004 | Add integration test for YAML-DB sync | Testing | Medium | [TASK_004_PLAN.md](./TASK_004_PLAN.md) |

### Bug #9: Pre-commit Hook Database Error (is_dirty column)

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 005 | Investigate is_dirty column in schema history | Research | Low | [TASK_005_PLAN.md](./TASK_005_PLAN.md) |
| 006 | Update pre-commit hook to use correct schema | Development | Medium | [TASK_006_PLAN.md](./TASK_006_PLAN.md) |
| 007 | Add database migration script for schema updates | Development | Medium | [TASK_007_PLAN.md](./TASK_007_PLAN.md) |
| 008 | Test pre-commit hook with fresh database | Testing | Low | [TASK_008_PLAN.md](./TASK_008_PLAN.md) |

### Bug #11: Database Rebuild Loads 0 Tracks/Sprints/Tasks

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 009 | Update db_rebuild_cmd to load from ULID files | Development | High | [TASK_009_PLAN.md](./TASK_009_PLAN.md) |
| 010 | Update sql_loader init to iterate tracks/*.yaml | Development | Medium | [TASK_010_PLAN.md](./TASK_010_PLAN.md) |
| 011 | Add progress reporting during rebuild | Development | Low | [TASK_011_PLAN.md](./TASK_011_PLAN.md) |
| 012 | Add integration test for database rebuild | Testing | Medium | [TASK_012_PLAN.md](./TASK_012_PLAN.md) |

---

## Sprint Plan

### Approach
1. Review affected code and understand current behavior
2. Design solution that maintains backward compatibility
3. Implement changes with comprehensive tests
4. Verify all success criteria are met
5. Update documentation as needed

### Risks
- Changes may affect other parts of the system
- Backward compatibility must be maintained
- Tests must cover edge cases

### Notes
This sprint consolidates the following original bugs:
- Bug #5
- Bug #9
- Bug #11
