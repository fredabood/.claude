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

1. **Add VALIDATION_EXCLUDE_PATTERNS constant** (development, low complexity)
2. **Update validator to skip excluded paths** (development, low complexity)
3. **Add unit test for exclusion patterns** (testing, low complexity)
4. **Verify single roadmap.yaml exists at correct location** (testing, low complexity)
5. **Add startup check to warn if duplicate exists** (development, low complexity)
6. **Document canonical location in CLAUDE.md** (documentation, low complexity)

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
