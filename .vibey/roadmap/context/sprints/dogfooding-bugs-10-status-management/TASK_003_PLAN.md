# Task Plan: Add CLI command to revert sprint status

## Bug ID
01KCAH9ECZXRMJN05DQ9ZAS46V

## Problem Statement
Need `vibey roadmap revert sprint <id>` to change status back to not_started or in_progress. Currently no way to undo a premature completion.

## Root Cause Analysis
Only forward status transitions are supported. No revert/undo operations exist.

## Files to Modify

### Primary Files
1. `vibey/cli/main.py` - Add revert command
2. `vibey/cli/commands.py` - Add revert_sprint_cmd function
3. `vibey/operations/roadmap/transitions.py` - Add revert transition logic

## Implementation Steps

1. **Add revert command to CLI**
   ```python
   @roadmap.command()
   @click.argument('item_type', type=click.Choice(['sprint', 'task', 'track']))
   @click.argument('item_id')
   @click.option('--to', 'target_status', required=True,
                 type=click.Choice(['not_started', 'in_progress']))
   def revert(item_type, item_id, target_status):
       """Revert an item to a previous status."""
   ```

2. **Implement revert logic in transitions.py**
   ```python
   def revert_status(root_dir: Path, item_type: str, item_id: str,
                     target_status: str) -> bool:
       """Revert item status to earlier state."""
   ```

3. **Clear completion metadata on revert**
   - Set completed timestamp to null
   - Preserve started timestamp if reverting to in_progress
   - Clear both if reverting to not_started

4. **Add validation**
   - Only allow revert from completed → in_progress/not_started
   - Only allow revert from in_progress → not_started
   - Log revert in activity log with reason

5. **Update parent progress on revert**
   - If reverting task, update sprint progress
   - If reverting sprint, update track progress

## Test Requirements
- Revert completed sprint to in_progress - verify status and dates
- Revert completed task to not_started - verify cleared timestamps
- Verify parent progress updates correctly

## Estimated Complexity
Medium - reverse of existing complete logic with metadata clearing
