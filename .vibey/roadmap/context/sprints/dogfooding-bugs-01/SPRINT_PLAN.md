# Sprint 1: CLI Startup Unblock

**Bugs Addressed:** #6, #8
**Priority:** CRITICAL
**Status:** NOT_STARTED

---

## Description

Fix critical import and schema issues blocking CLI startup. SQLAlchemy must be optional, and YAML loader must handle v2 format without 'blocked' field.

---

## Goal

Make CLI commands executable without errors

---

## Success Criteria

- CLI starts without SQLAlchemy installed
- YAML files load without KeyError for blocked field
- All load_* functions handle v1 and v2 formats

---

## Dependencies

None (can start immediately)

---

## Tasks (9 total)

1. **Implement lazy imports in orm.py** (development, medium complexity)
2. **Move ORM imports behind try/except ImportError** (development, low complexity)
3. **Add SQLAlchemy to optional dependencies in pyproject.toml** (development, low complexity)
4. **Add test for CLI without SQLAlchemy installed** (testing, medium complexity)
5. **Update load_roadmap to use .get('blocked', False)** (development, low complexity)
6. **Update load_track for backward compatibility** (development, low complexity)
7. **Update load_sprint for backward compatibility** (development, low complexity)
8. **Update load_task for backward compatibility** (development, low complexity)
9. **Add migration test for v1 to v2 loading** (testing, medium complexity)

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
- Bug #6
- Bug #8
