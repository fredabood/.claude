# Post Mortem: CLI Roadmap Complete Command Validation Errors

**Task ID:** 01KCVMA0FDHNQQZ8SXSE4RCT3C
**Sprint:** Sprint 24 - Progress Tracking and CLI Validation Bugs
**Track:** CLI Dogfooding Bug Fixes
**Status:** Completed
**Date:** 2025-12-19

## Problem Statement

The `vibey roadmap complete <task-id>` command was failing with the error message:

```
Cannot complete 01KCVMA0F3G5XHEG45BX363K6V:
   - Track 01KC2D0JK06MN77ZHAGAHF5VKB must complete
   - Track 01KC2D0JK0HWMWQJY4A4ET0EGX must complete
   ... (all 48 tracks)
```

This error incorrectly required ALL tracks in the roadmap to be completed before a single task could be marked as complete.

## Root Cause Analysis

The bug was located in `QueryTicketLoader._load_uncached()` in `/vibey/operations/roadmap/query.py`.

### The Detection Logic Flaw

```python
def _load_uncached(self, ticket_id: str) -> HierarchicalTicket:
    if '-task-' in ticket_id:  # Only detects legacy slug-based task IDs
        return self._load_task_as_ticket(ticket_id)
    elif self._is_sprint_id(ticket_id):
        return self._load_sprint_as_ticket(ticket_id)
    elif self._is_track_id(ticket_id):
        return self._load_track_as_ticket(ticket_id)
    else:
        return self._load_roadmap_as_ticket(ticket_id)  # FALLBACK
```

The code only recognized task IDs containing `-task-` (legacy slug format like `backend-1-task-003`). ULID-based task IDs like `01KCVMA0F3G5XHEG45BX363K6V` fell through to the roadmap loader, which returned the entire roadmap with 48 track completion criteria.

### Secondary Issues

1. **v2 Format YAML Loading**: The `_load_task_ticket_v2()` function expected `sprint_id`, `track_id`, and `roadmap_id` fields, but v2 format YAML files use `parent_ref` instead.

2. **Missing track_id Derivation**: When loading v2 format tasks, `track_id` wasn't being derived from the sprint's `parent_ref`.

3. **Legacy Task Loader in update.py**: The `complete_task()` and `start_task()` functions were using the v1 `load_task()` function for ULID tasks, which failed on v2 format files.

## Solution

### 1. ULID Task Detection

Added new methods to `QueryTicketLoader`:

```python
def _is_ulid_task_id(self, ticket_id: str) -> bool:
    """Check if ID is a ULID-based task ID."""
    if len(ticket_id) != 26 or not ticket_id.isalnum() or not ticket_id.startswith('01'):
        return False
    task_path = self.fs.roadmap_root / "tasks" / f"{ticket_id}.yaml"
    return task_path.exists()

def _load_ulid_task_as_ticket(self, task_id: str) -> TaskTicket:
    """Load a ULID-based task from flat directory."""
    from vibey.roadmap.serialization.yaml_loader import load_task_ticket as yaml_load_task_ticket
    task_path = self.fs.roadmap_root / "tasks" / f"{task_id}.yaml"
    return yaml_load_task_ticket(task_path)
```

### 2. v2 Format Support in yaml_loader.py

Updated `_load_task_ticket_v2()` to derive hierarchy IDs from `parent_ref`:

```python
parent_ref = task_data.get('parent_ref', '')
sprint_id = task_data.get('sprint_id', parent_ref)
track_id = task_data.get('track_id', '')

# Look up track_id from sprint file if not provided
if not track_id and sprint_id:
    sprint_file = sprints_dir / f"{sprint_id}.yaml"
    if sprint_file.exists():
        sprint_data = yaml.safe_load(f)
        track_id = sprint_data.get('sprint', {}).get('parent_ref', '')
```

### 3. Format Detection in update.py

Added v2 format detection in `complete_task()` and `start_task()`:

```python
format_version = task_data.get('task', {}).get('format_version', 'v1')
if format_version == 'v2':
    # Use unified ticket loader
    task_ticket = yaml_load_task_ticket(tasks_path)
    # Convert to legacy Task for downstream compatibility
    task = Task(...)
else:
    # Use legacy loader
    task = load_task(tasks_path)
```

## Files Changed

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/query.py` | Added `_is_ulid_task_id()`, `_load_ulid_task_as_ticket()` methods |
| `vibey/operations/roadmap/update.py` | Added v2 format detection and TaskTicket-to-Task conversion |
| `vibey/roadmap/serialization/yaml_loader.py` | Fixed `_load_task_ticket_v2()` to derive track_id from parent_ref |

## Verification

```bash
# Before fix:
$ vibey roadmap complete 01KCVMA0F3G5XHEG45BX363K6V
Cannot complete 01KCVMA0F3G5XHEG45BX363K6V:
   - Track 01KC2D0JK06MN77ZHAGAHF5VKB must complete
   ... (48 tracks)

# After fix:
$ vibey roadmap complete 01KCVMA0F3G5XHEG45BX363K6V
Completed task '01KCVMA0F3G5XHEG45BX363K6V'
```

## Lessons Learned

1. **ID Format Migration**: When migrating from slug-based IDs to ULIDs, all code paths that detect entity types from ID patterns need to be updated.

2. **Format Version Handling**: Multiple code paths (CLI, operations, serialization) need consistent handling of v1 vs v2 format YAML files.

3. **Fallback Behavior**: Loading the wrong entity type (roadmap instead of task) can manifest as cryptic validation errors that are hard to trace back to the root cause.

## Related Tasks

- **01KCVMA0F3G5XHEG45BX363K6V**: Sprint progress not auto-updating when tasks completed via direct YAML edit
- **01KCVMA0FT9M259NES1XF022T1**: `vibey roadmap db rebuild` validation errors for 1500+ items

## Commit Reference

```
9ab36e7e fix(01KCVMA0FT9M259NES1XF022T1): Fix db rebuild validation errors for 1500+ items
```
