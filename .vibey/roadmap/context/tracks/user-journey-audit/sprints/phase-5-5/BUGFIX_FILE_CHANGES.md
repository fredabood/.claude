# Bugfix File Changes (Sprint 16: Silent Sprint Skipping Bug)

## Summary
This document records files modified during the dogfooding-bugs Sprint 16 bugfix.

## Bug Description
Sprints with `status=completed` but `completed=null` were silently skipped during `db rebuild`. The fix adds error reporting for skipped files.

## Files Modified

### vibey/cli/commands.py
- **Lines Modified**: 3006-3191
- **Change**: Added `skipped_files` list to track failed file loads during `_load_roadmap_to_db_flat()`
- **Details**:
  - Added collection of (entity_type, filename, error_message) tuples
  - Added summary output showing which files were skipped and why
  - Limits output to first 10 skipped files to avoid spam

### vibey/roadmap/serialization/backend.py
- **Lines Modified**: 572-614
- **Change**: Added logging warnings for skipped files in `SyncManager.rebuild()`
- **Details**:
  - Added `import logging` and logger initialization
  - Added `logger.warning()` calls for each skipped track/sprint/task
  - Added `skipped_files` list for tracking

## Impact
- Users now see exactly which YAML files failed to load during `db rebuild`
- Error messages include the filename and specific error
- Easier debugging when files have validation issues

## Commit
- Hash: 1eecfbb8
- Message: "fix(roadmap): Report skipped files during db rebuild instead of silent skip"
