# Sprint 1: CLI Startup Unblock

**Bugs Addressed:** #6, #8
**Priority:** CRITICAL
**Status:** NOT_STARTED
**Task Plans:** 9 detailed plans available in this directory

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

### Bug #6: SQLAlchemy Optional Dependency

| # | Task | Complexity | Plan |
|---|------|------------|------|
| 1 | Implement lazy imports in orm.py | Medium | [TASK_001_PLAN.md](./TASK_001_PLAN.md) |
| 2 | Move ORM imports behind try/except ImportError | Low | [TASK_002_PLAN.md](./TASK_002_PLAN.md) |
| 3 | Add SQLAlchemy to optional dependencies in pyproject.toml | Low | [TASK_003_PLAN.md](./TASK_003_PLAN.md) |
| 4 | Add test for CLI without SQLAlchemy installed | Medium | [TASK_004_PLAN.md](./TASK_004_PLAN.md) |

### Bug #8: Blocked Field Backward Compatibility

| # | Task | Complexity | Plan |
|---|------|------------|------|
| 5 | Update load_roadmap to use .get('blocked', False) | Low | [TASK_005_PLAN.md](./TASK_005_PLAN.md) |
| 6 | Update load_track for backward compatibility | Low | [TASK_006_PLAN.md](./TASK_006_PLAN.md) |
| 7 | Update load_sprint for backward compatibility | Low | [TASK_007_PLAN.md](./TASK_007_PLAN.md) |
| 8 | Update load_task for backward compatibility | Low | [TASK_008_PLAN.md](./TASK_008_PLAN.md) |
| 9 | Add migration test for v1 to v2 loading | Medium | [TASK_009_PLAN.md](./TASK_009_PLAN.md) |

---

## Key Files Affected

| File | Bug | Issue |
|------|-----|-------|
| `vibey/roadmap/models/ticket/orm.py` | #6 | Unconditional SQLAlchemy import at line 23-43 |
| `vibey/roadmap/models/ticket/__init__.py` | #6 | Imports ORM at line 129 |
| `pyproject.toml` | #6 | SQLAlchemy in required deps at line 38 |
| `vibey/roadmap/serialization/yaml_loader.py` | #8 | load_* functions need .get() for blocked |
| `vibey/roadmap/models/*.py` | #8 | Model validation expects blocked field |

---

## Execution Order

```
Tasks 1-3 (SQLAlchemy lazy loading)
    │
    └───► Task 4 (Test SQLAlchemy optional)

Tasks 5-8 (blocked field .get() updates)
    │
    └───► Task 9 (Migration tests)
```

Tasks can be parallelized within each bug:
- Tasks 1-4 (Bug #6) can run in parallel with Tasks 5-9 (Bug #8)
- Task 4 depends on Tasks 1-3 completion
- Task 9 depends on Tasks 5-8 completion

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
- Bug #6: SQLAlchemy unconditional import breaks CLI
- Bug #8: YAML loader requires 'blocked' field removed in v2

---

## Verification Checklist

After completing all tasks:

- [ ] `pip install .` (without SQLAlchemy) succeeds
- [ ] `vibey roadmap status` works without SQLAlchemy
- [ ] `vibey roadmap db rebuild` shows helpful error when SQLAlchemy missing
- [ ] v1 format YAML files load correctly
- [ ] v2 format YAML files (no blocked field) load correctly
- [ ] All tests pass
- [ ] No regressions in existing functionality
