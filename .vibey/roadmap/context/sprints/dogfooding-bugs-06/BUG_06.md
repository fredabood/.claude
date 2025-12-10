# Bug #6: Missing SQLAlchemy Dependency Breaks CLI

**Date:** 2025-12-09
**Severity:** CRITICAL
**Status:** DOCUMENTED

---

## Description

All CLI commands fail due to unconditional SQLAlchemy import.

---

## Root Cause

orm.py unconditionally imports SQLAlchemy at module load time.

---

## Files Affected

- `vibey/roadmap/models/ticket/__init__.py`
- `vibey/roadmap/models/ticket/orm.py`

---

## Tasks

1. **Implement lazy imports in orm.py** (development, medium complexity)
2. **Move ORM imports behind try/except ImportError** (development, low complexity)
3. **Add SQLAlchemy to optional dependencies** (development, low complexity)
4. **Add test for CLI without SQLAlchemy installed** (testing, medium complexity)

---

## Sprint Plan

### Goal
Fix Bug #6: Missing SQLAlchemy Dependency Breaks CLI

### Success Criteria
1. Root cause addressed: orm.py unconditionally imports SQLAlchemy at module load time.
2. All affected files updated
3. Unit tests pass
4. Integration tests pass

### Approach
1. Research and understand the bug
2. Implement the fix
3. Add/update tests
4. Verify fix works
