# Sprint 30: Data Integrity Audit - Discovered Bugs

## Overview

These bugs were discovered during the Sprint 29 Data Integrity Audit when investigating why 25 tasks were missing from the SQLite database despite having YAML files.

## Root Cause Analysis

The audit revealed a chain of failures:
1. **YAML files with validation errors** → silently skipped during `db rebuild`
2. **No error reporting** → user unaware of data loss
3. **Legacy format files** → not cleaned up during migrations

## Bug Summary

| Task | Bug | Impact | Priority |
|------|-----|--------|----------|
| 01 | Database rebuild silently skips validation errors | 25 tasks not loaded, no warning | High |
| 02 | Legacy v2 format YAML not cleaned up | Orphaned files cause silent failures | Medium |
| 03 | YAML loader fails silently on malformed depends_on | 24 tasks skipped due to missing field | High |

## Dependency Graph

```
Task 03 (depends_on fix)
    ↓
Task 01 (error reporting) ← Most impactful
    ↓
Task 02 (legacy cleanup) ← Prevents recurrence
```

## Recommended Execution Order

1. **Task 03** - Fix YAML loader to handle missing depends_on fields gracefully
2. **Task 01** - Add comprehensive error reporting to db rebuild
3. **Task 02** - Add legacy format detection and cleanup

## Success Criteria

- [ ] `vibey roadmap db rebuild` reports all files that fail to load
- [ ] `--strict` flag available to abort on first error
- [ ] `--verbose` flag shows each file processed
- [ ] Legacy v2 format files detected and reported
- [ ] depends_on entries without required_status handled gracefully

## Files Likely to Change

```
vibey/roadmap/serialization/yaml_loader.py   # Task 03
vibey/cli/commands.py                        # Task 01
vibey/operations/roadmap/db_rebuild.py       # Task 01
vibey/operations/roadmap/migrations/         # Task 02
```
