# Sprint 6: Tooling Polish

**Bugs Addressed:** #7, #14
**Priority:** LOW
**Status:** NOT_STARTED

---

## Description

Clean up validator to exclude sample code directories and verify duplicate roadmap.yaml fix is complete.

---

## Goal

Validation and tooling work correctly

---

## Success Criteria

- Validator skips context/sample_code directories
- Single roadmap.yaml verified at correct location
- Startup warns if duplicate found

---

## Dependencies

None (can start immediately)

---

## Tasks (6 total)

### Bug #7: Validator Doesn't Exclude context/sample_code Directories

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 001 | Add VALIDATION_EXCLUDE_PATTERNS constant | Development | Low | [TASK_001_PLAN.md](./TASK_001_PLAN.md) |
| 002 | Update validator to skip excluded paths | Development | Low | [TASK_002_PLAN.md](./TASK_002_PLAN.md) |
| 003 | Add unit test for exclusion patterns | Testing | Low | [TASK_003_PLAN.md](./TASK_003_PLAN.md) |

### Bug #14: Duplicate roadmap.yaml Files Existed at Two Locations

| Task | Title | Type | Complexity | Plan |
|------|-------|------|------------|------|
| 004 | Verify single roadmap.yaml exists at correct location | Testing | Low | [TASK_004_PLAN.md](./TASK_004_PLAN.md) |
| 005 | Add startup check to warn if duplicate exists | Development | Low | [TASK_005_PLAN.md](./TASK_005_PLAN.md) |
| 006 | Document canonical location in CLAUDE.md | Documentation | Low | [TASK_006_PLAN.md](./TASK_006_PLAN.md) |

**Note:** Bug #14 is already **Fixed** - the duplicate file was deleted. Tasks 004-006 add verification, safeguards, and documentation to prevent recurrence.

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
- Bug #7
- Bug #14
