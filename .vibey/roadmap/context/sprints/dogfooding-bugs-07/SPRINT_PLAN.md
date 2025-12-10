# Sprint 7: Activity Log Migration

**Bugs Addressed:** #13
**Priority:** MEDIUM
**Status:** NOT_STARTED

---

## Description

Migrate activity log from audit-trail.yaml to time-bucketed JSONL format as designed in unified architecture.

---

## Goal

Activity log uses JSONL format

---

## Success Criteria

- activity_log/ directory exists
- Events written to YYYY-MM.jsonl files
- Old audit-trail.yaml migrated
- All consumers use new format

---

## Dependencies

None (can start immediately)

---

## Tasks (6 total)

1. **Create activity_log/ directory structure** (development, low complexity)
2. **Write JSONL writer for activity events** (development, medium complexity)
3. **Write JSONL reader for activity queries** (development, medium complexity)
4. **Migrate existing audit-trail.yaml to JSONL** (development, medium complexity)
5. **Update all activity log consumers** (development, medium complexity)
6. **Add tests for JSONL activity log** (testing, medium complexity)

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
- Bug #13
