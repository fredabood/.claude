# CLI Issues Discovered During Sprint 12

**Date:** 2025-12-06
**Sprint:** sqlite-backend-12

---

## Issue 1: RuntimeWarning on module import

**Severity:** Low (cosmetic)
**Impact:** Warning message displayed, no functional impact

**Reproduction:**
```bash
python -m vibey.cli.main roadmap status
```

**Error:**
```
<frozen runpy>:128: RuntimeWarning: 'vibey.cli.main' found in sys.modules after import of package 'vibey.cli', but prior to execution of 'vibey.cli.main'; this may result in unpredictable behaviour
```

**Cause:** Import order issue when using `python -m vibey.cli.main`

**Suggested Fix:** Review import structure in `vibey/cli/__init__.py` and `vibey/cli/main.py` to ensure clean module loading.

---

## Issue 2: Missing sqlalchemy in system Python

**Severity:** Expected Behavior (not a bug)
**Impact:** CLI fails when using system Python without dependencies

**Reproduction:**
```bash
# Using system Python without venv
python3 -m vibey.cli.main roadmap status
# Error: ModuleNotFoundError: No module named 'sqlalchemy'
```

**Workaround:**
```bash
# Use venv Python
/Users/fredabood/Repositories/vibey/.venv/bin/python -m vibey.cli.main roadmap status
```

**Resolution:** Expected behavior - users must install dependencies or use the virtual environment.

---

## Recommendation

Add Issue 1 (RuntimeWarning) to Sprint 13 Task 009: "Update CLI and tooling for new directory structure" as a sub-item for cleanup.
