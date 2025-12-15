# Task Plan: add-commit command does not accept ULID task IDs

## Bug ID
01KC8FV1V847TF6K5NXRFV6P3G

## Problem Statement
The `roadmap add-commit` command rejects ULID task IDs with error 'Invalid task ID format'. It expects legacy slug format. Should accept both formats.

## Root Cause Analysis
The `vibey/cli/roadmap-add-commit.py` script validates task ID format using a pattern that only matches slug format `track-sprint-task-NNN`.

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap-add-commit.py` - Main script with ID validation
2. `vibey/operations/roadmap/add_commit.py` - Core add_commit operation

## Implementation Steps

1. **Find current ID validation**
   ```bash
   grep -n "task.*id\|Invalid.*format" vibey/cli/roadmap-add-commit.py
   ```

2. **Add ULID recognition**
   ```python
   def is_valid_task_id(task_id: str) -> bool:
       """Validate task ID format (ULID or legacy slug)."""
       # ULID format: 26 alphanumeric characters
       if len(task_id) == 26 and task_id.isalnum():
           return True
       # Legacy format: contains -task-
       if '-task-' in task_id:
           return True
       return False
   ```

3. **Update validation in add-commit script**
   - Replace hardcoded pattern match with is_valid_task_id()
   - Verify task exists in filesystem before adding commit

4. **Update add_commit_to_task operation**
   - Ensure it can load task by ULID
   - Use flat file structure: tasks/{ulid}.yaml

## Test Requirements
- `vibey roadmap add-commit 01KC... abc123` - should work
- `vibey roadmap add-commit track-sprint-task-001 abc123` - still works
- Invalid task ID - clear error message

## Related Bugs
- 01KCH7051YHKTSVQ21JRB81VM9 (Sprint 10: complete command same issue)
- 01KC8FTXZB94YTTB79VPK3SNRM (Sprint 11: complete command duplicate)

## Estimated Complexity
Simple - regex/validation update
