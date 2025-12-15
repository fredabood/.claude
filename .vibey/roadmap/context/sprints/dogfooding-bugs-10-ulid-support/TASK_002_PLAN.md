# Task Plan: Git hook doesn't recognize ULID task IDs in commit messages

## Bug ID
01KCH7766JSCJ36G91HS4YRSBW

## Problem Statement
The pre-commit hook for validating task references doesn't recognize ULID-formatted task IDs. Commits with 'Task: 01KC...' footer are rejected with 'Commit does not reference a task'. Need to update task ID regex pattern.

## Root Cause Analysis
The git hooks use regex patterns to extract task IDs from commit messages. The pattern expects slug format like `track-sprint-task-001` and doesn't match ULID format `01KC2D0JK7READW9KAK1HBX4B8`.

## Files to Modify

### Primary Files
1. `vibey/operations/git/hooks/pre_push.py` - Task ID extraction
2. `vibey/operations/git/hooks/post_commit.py` - Task ID extraction
3. `.git/hooks/pre-commit` or `vibey/operations/roadmap/hooks/pre-push` - Installed hooks

## Implementation Steps

1. **Find current task ID regex patterns**
   ```bash
   grep -rn "task.*regex\|Task.*pattern\|[0-9]{3}" vibey/operations/git/
   grep -rn "task.*regex\|Task.*pattern" vibey/operations/roadmap/hooks/
   ```

2. **Define ULID pattern**
   ```python
   # ULID: 26 characters, Crockford's Base32 (0-9, A-Z excluding I, L, O, U)
   ULID_PATTERN = r'[0-9A-HJKMNP-TV-Z]{26}'

   # Combined pattern for both formats
   TASK_ID_PATTERN = rf'(?:{ULID_PATTERN}|[\w-]+-task-\d+)'
   ```

3. **Update hook task ID extraction**
   ```python
   def extract_task_id(commit_message: str) -> Optional[str]:
       """Extract task ID from commit message footer."""
       # Look for "Task: <id>" pattern
       match = re.search(rf'Task:\s*({TASK_ID_PATTERN})', commit_message)
       if match:
           return match.group(1)
       return None
   ```

4. **Update task ID validation**
   ```python
   def is_valid_task_id(task_id: str, root_dir: Path) -> bool:
       """Validate task ID exists in roadmap."""
       fs = FileSystemManager(root_dir)
       task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
       return task_path.exists()
   ```

5. **Reinstall hooks after update**
   - Run hook installer to update .git/hooks

## Test Requirements
- Commit with `Task: 01KC2D0JK7READW9KAK1HBX4B8` - should pass
- Commit with `Task: track-sprint-task-001` - should still pass
- Commit with invalid task ID - should fail appropriately

## Estimated Complexity
Simple - regex pattern update
