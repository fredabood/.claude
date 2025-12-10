# Known CLI Issues

## CLI-001: Sprint Summary Not Updated on Task Status Change

**Date Identified:** 2025-12-04
**Severity:** Medium
**Status:** Open - Will be fixed by SQLite backend

### Description

When using `vibey roadmap update task --status completed`, the task's individual `task.yaml` file is updated correctly, but the parent `sprint.yaml` summary (progress counters and task status list) is not updated.

### Impact

- Sprint progress shows incorrect counts (e.g., 4/11 instead of 6/11)
- Sprint task list shows stale statuses
- Track progress aggregates are also stale
- Requires manual fix to sprint.yaml after task completion

### Root Cause

The CLI update command updates the task.yaml but doesn't propagate changes up the hierarchy to sprint.yaml and track.yaml.

### Workaround

Manually edit sprint.yaml after task completion:
1. Update `progress.tasks_completed` and `progress.development_tasks_completed`
2. Update `progress.completion_percent`
3. Update the task status in the `tasks:` list

### Resolution

The SQLite backend (sqlite-backend track) will fix this permanently by:
1. Computing progress from database rather than storing in YAML
2. Using triggers to maintain consistency
3. Dumping accurate state on sync operations

The current sqlite-backend-8 sprint (Serialization Migration) and sqlite-backend-9 (Operations Migration) will address this when the CLI is migrated to use the database backend.

### Related Tasks

- sqlite-backend-8-task-007: Create migration CLI command
- sqlite-backend-9: Operations Migration sprint
