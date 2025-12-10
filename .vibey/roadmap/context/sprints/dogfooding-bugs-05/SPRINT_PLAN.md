# Sprint 5: CLI Create Commands

**Bugs Addressed:** #15
**Priority:** HIGH
**Status:** NOT_STARTED

---

## Description

Add CLI commands to create new tracks, sprints, and tasks using the ULID flat file structure. Update create-from-plan to use new structure.

---

## Goal

Users can create roadmap objects via CLI

---

## Success Criteria

- 'vibey roadmap create track' works
- 'vibey roadmap create sprint' works
- 'vibey roadmap create task' works
- create-from-plan uses ULID flat structure

---

## Dependencies

- dogfooding-bugs-02

---

## Tasks (6 total)

### Bug #15: No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 001 | Add create track CLI command | Development | Medium | [TASK_001_PLAN.md](./TASK_001_PLAN.md) |
| 002 | Add create sprint CLI command | Development | Medium | [TASK_002_PLAN.md](./TASK_002_PLAN.md) |
| 003 | Add create task CLI command | Development | Medium | [TASK_003_PLAN.md](./TASK_003_PLAN.md) |
| 004 | Update create-from-plan to use ULID flat structure | Development | High | [TASK_004_PLAN.md](./TASK_004_PLAN.md) |
| 005 | Create ULIDManager for ULID generation | Development | Low | [TASK_005_PLAN.md](./TASK_005_PLAN.md) |
| 006 | Add integration tests for create commands | Testing | Medium | [TASK_006_PLAN.md](./TASK_006_PLAN.md) |

**Key Finding:** Task 005 (ULIDManager) is **already implemented** in `vibey/roadmap/id_generator.py` (341 lines). The module provides complete ULID generation functions:
- `generate_track_id()` → `track_01JB3QVDZ8TRK9XN1FJFHGWPRM`
- `generate_sprint_id()` → `sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ`
- `generate_task_id()` → `task_01JB3QVE5NTSK2BPFQR8LVXABC`

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
- Bug #15
