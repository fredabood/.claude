# Task Plan: Add CLI command for bulk task status updates

## Bug ID
01KCAH9JF0JX1KWDPJV65PAXJC

## Problem Statement
Need `vibey roadmap bulk-complete sprint <id>` to mark all tasks in a sprint as completed. Currently must edit each task YAML individually.

## Root Cause Analysis
No bulk operation commands exist - all status changes must be done task-by-task.

## Files to Modify

### Primary Files
1. `vibey/cli/main.py` - Add new CLI command group
2. `vibey/cli/commands.py` - Add bulk_complete_sprint_cmd function
3. `vibey/operations/roadmap/update.py` - Add bulk update operation

## Implementation Steps

1. **Add bulk command group to CLI**
   ```python
   @roadmap.group()
   def bulk():
       """Bulk operations on roadmap items."""
       pass

   @bulk.command('complete-sprint')
   @click.argument('sprint_id')
   def bulk_complete_sprint(sprint_id):
       """Mark all tasks in a sprint as completed."""
   ```

2. **Implement bulk_complete_sprint_cmd in commands.py**
   - Load all tasks for the sprint
   - Filter to non-completed tasks
   - Update each task status to completed
   - Update sprint progress
   - Create activity log entries for each

3. **Add operation function in update.py**
   ```python
   def bulk_complete_sprint_tasks(root_dir: Path, sprint_id: str) -> dict:
       """Complete all tasks in a sprint."""
   ```

4. **Add safety checks**
   - Confirm before completing (--yes flag to skip)
   - Show count of tasks to be completed
   - Handle already-completed tasks gracefully

## Test Requirements
- Run command on sprint with 5 incomplete tasks - all should complete
- Run command on sprint with all completed - should show "no tasks to complete"
- Verify activity log entries created
- Verify sprint progress updated

## Estimated Complexity
Medium - new command requiring iteration and multiple updates
