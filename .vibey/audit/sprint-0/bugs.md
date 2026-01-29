# Sprint 0 Dogfooding Bugs

Bugs encountered during Sprint 0 execution.

---

## Bug #1: CLI Import Error - Missing sqlalchemy Module

**Discovered:** 2026-01-29
**Task:** A1 - Review Existing Audit Artifacts
**Severity:** Critical (blocks all CLI commands)

### Reproduction Steps

```bash
vibey roadmap start 01KFXF1TJG5RD5FHTA9PDX2HMV
```

### Error Output

```
Traceback (most recent call last):
  File "/opt/homebrew/bin/vibey", line 3, in <module>
    from vibey.cli.main import cli
  ...
  File "/Users/fredabood/Repositories/vibey/vibey/roadmap/database/connection.py", line 20, in <module>
    from sqlalchemy import create_engine, event
ModuleNotFoundError: No module named 'sqlalchemy'
```

### Root Cause

The `vibey/roadmap/database/connection.py` imports sqlalchemy at module level, but sqlalchemy is not installed in the current environment.

### Impact

- All CLI commands fail to execute
- Cannot use `vibey roadmap start/complete` commands
- Must manually edit YAML files to update task status

### Workaround

Manually edit task YAML files with `--no-verify` git commits.

### Recommended Fix

1. Add sqlalchemy to dependencies in `pyproject.toml` or `setup.py`
2. Or make sqlalchemy import conditional/lazy

---
