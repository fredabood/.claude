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
| 04 | recalculate_all auto-completes tracks incorrectly | Status corrections reverted on rebuild | **Critical** |

## Dependency Graph

```
Task 04 (auto-complete fix) ← CRITICAL: Blocks all status work
    ↓
Task 03 (depends_on fix) ✓ DONE
    ↓
Task 01 (error reporting) ← Already implemented!
    ↓
Task 02 (legacy cleanup) ← Prevents recurrence
```

## Recommended Execution Order

1. **Task 03** - Fix YAML loader to handle missing depends_on fields gracefully ✓ DONE
2. **Task 04** - Fix recalculate_all to not auto-complete tracks ✓ DONE
3. **Task 01** - Error reporting enhanced with --strict and --verbose flags ✓ DONE
4. **Task 02** - Add legacy format detection and cleanup ✓ DONE

## Success Criteria

- [x] depends_on entries without required_status handled gracefully (Task 03)
- [x] recalculate_all only updates progress counters, not status (Task 04)
- [x] `vibey roadmap db rebuild` reports all files that fail to load (Task 01)
- [x] `--strict` flag available to abort on first error (Task 01)
- [x] `--verbose` flag shows each file processed (Task 01)
- [x] Legacy v2 format files detected and reported (Task 02)

## Files Changed

```
vibey/roadmap/serialization/yaml_loader.py   # Task 03 ✓ DONE
vibey/operations/roadmap/update.py           # Task 04 ✓ DONE (removed auto-progression)
vibey/cli/main.py                            # Task 01 & 02 ✓ DONE (--strict, --verbose, cleanup-legacy)
vibey/cli/commands_legacy.py                 # Task 01 & 02 ✓ DONE (error reporting, legacy scan)
vibey/roadmap/serialization/format_detector.py # Task 02 ✓ NEW (format detection module)
```

## Post-Sprint Cleanup

After completing all tasks, one legacy v2 format file was discovered and cleaned up:

- **File**: `.vibey/roadmap/tasks/01KDDE9NEKAH3BM9PRFPHNNCNC.yaml`
- **Action**: Converted from v2 format (parent_ref, name, created_at) to v3 format (sprint_id, title, created)
- **Commit**: `fix(roadmap): Convert legacy v2 format task to v3 format`

## Sprint Status

**COMPLETED** - All 4 bugs fixed, all success criteria met, legacy files cleaned up.
