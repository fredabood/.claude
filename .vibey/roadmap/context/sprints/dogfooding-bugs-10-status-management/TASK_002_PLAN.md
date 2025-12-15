# Task Plan: Add CLI command for data reconciliation

## Bug ID
01KCAH9PG05Z3TB46Z74H9DBFV

## Problem Statement
Need `vibey roadmap reconcile` to fix mismatches between sprint status and task status. Should detect sprints marked complete with incomplete tasks and offer to fix.

## Root Cause Analysis
No validation command exists to detect and fix status inconsistencies between parent/child objects in the roadmap hierarchy.

## Files to Modify

### Primary Files
1. `vibey/cli/main.py` - Add reconcile command
2. `vibey/cli/commands.py` - Add reconcile_cmd function
3. `vibey/operations/roadmap/validate.py` - Add reconciliation logic

## Implementation Steps

1. **Define reconciliation checks**
   - Sprint marked completed but has incomplete tasks
   - Track marked completed but has incomplete sprints
   - Task marked completed but dates are null
   - Progress counts don't match actual task counts

2. **Add reconcile command to CLI**
   ```python
   @roadmap.command()
   @click.option('--fix', is_flag=True, help='Auto-fix issues')
   @click.option('--dry-run', is_flag=True, help='Show issues without fixing')
   def reconcile(fix, dry_run):
       """Detect and fix status inconsistencies."""
   ```

3. **Implement reconciliation in validate.py**
   ```python
   def find_inconsistencies(root_dir: Path) -> List[Inconsistency]:
       """Find all status inconsistencies."""

   def fix_inconsistencies(root_dir: Path, issues: List[Inconsistency]) -> int:
       """Fix detected inconsistencies."""
   ```

4. **Define fix strategies**
   - Completed sprint with incomplete tasks → mark sprint as in_progress
   - Completed task with null dates → set completed date to now
   - Progress mismatch → recalculate from tasks

## Test Requirements
- Create sprint with mismatched status - reconcile should detect
- Run with --fix - should correct issues
- Run with --dry-run - should report but not change

## Estimated Complexity
Complex - requires comprehensive validation logic
