# Task Plan: Enforce task completion before sprint completion

## Bug ID
01KCAH9TCSDKACPJQPP6TFCTK0

## Problem Statement
The complete_sprint() function should refuse to complete a sprint if any tasks are not completed. Currently validation is wrapped in try/except and bypassed.

## Root Cause Analysis
Validation exists but is caught and ignored in exception handler, allowing invalid state transitions.

## Files to Modify

### Primary Files
1. `vibey/operations/roadmap/update.py` - complete_sprint function
2. `vibey/cli/roadmap-update.py` - CLI handler for complete

## Implementation Steps

1. **Find current validation code**
   ```bash
   grep -n "complete_sprint\|incomplete.*task" vibey/operations/roadmap/update.py
   ```

2. **Fix validation to not be swallowed**
   - Remove try/except that catches validation errors
   - Or re-raise validation errors after logging

3. **Add explicit pre-completion check**
   ```python
   def complete_sprint(root_dir: Path, sprint_id: str) -> dict:
       # Load sprint and its tasks
       tasks = get_sprint_tasks(root_dir, sprint_id)
       incomplete = [t for t in tasks if t.status != 'completed']

       if incomplete:
           raise ValidationError(
               f"Cannot complete sprint: {len(incomplete)} tasks incomplete. "
               f"Use --force to override."
           )
   ```

4. **Add --force flag for override**
   - Allow completion with warning if --force passed
   - Log forced completion in activity log

5. **Update CLI to show incomplete tasks**
   ```
   Cannot complete sprint: 3 tasks incomplete:
   - Task 1: title (not_started)
   - Task 2: title (in_progress)
   Use --force to complete anyway.
   ```

## Test Requirements
- Try to complete sprint with incomplete tasks - should fail
- Complete sprint with --force - should succeed with warning
- Complete sprint with all tasks done - should succeed normally

## Estimated Complexity
Simple - fix exception handling and add validation message
