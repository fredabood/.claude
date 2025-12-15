# Task Plan: create-sprint and create-task don't write activity log entries

## Bug ID
01KCAKH33KHF0HWVTM5C7AP3Y2

## Problem Statement
CLI commands `create-sprint` and `create-task` create YAML files but no activity log entries, causing pre-commit hook to block commits with 'No activity log entry for' errors.

## Root Cause Analysis
1. The pre-commit hook validates that all modified roadmap YAML files have corresponding activity log entries
2. `create-sprint` and `create-task` commands create YAML files but don't call the activity logging functions
3. Activity logging exists in `vibey/operations/roadmap/activity_log.py` but isn't integrated with create commands

## Files to Modify

### Primary Files
1. `vibey/cli/commands.py` - Contains create_sprint_cmd and create_task_cmd functions
2. `vibey/operations/roadmap/update.py` - Core update operations

### Activity Log Integration
1. `vibey/operations/roadmap/activity_log.py` - UnifiedActivityLog class
2. `vibey/operations/roadmap/jsonl_activity_log.py` - JSONL log implementation

## Implementation Steps

1. **Identify create command implementations**
   ```bash
   grep -n "def create_sprint\|def create_task" vibey/cli/commands.py
   ```

2. **Add activity log imports**
   ```python
   from vibey.operations.roadmap.activity_log import UnifiedActivityLog
   ```

3. **Integrate logging into create_sprint_cmd**
   - After YAML file is created successfully
   - Log with activity type: `sprint_created`
   - Include sprint ID, name, track reference

4. **Integrate logging into create_task_cmd**
   - After YAML file is created successfully
   - Log with activity type: `task_created`
   - Include task ID, title, sprint reference

5. **Verify JSONL log entry format**
   - Check that entry format matches what pre-commit hook expects
   - Entry should include file path, timestamp, action type

## Test Requirements
- Run `vibey roadmap create-sprint` - verify activity log entry created
- Run `vibey roadmap create-task` - verify activity log entry created
- Git commit after create - should pass pre-commit hook
- Check `.vibey/roadmap/activity_log/` for entries

## Related Bugs
- 01KC8FGN8HVDFHC9MYVRFK3WHN (Sprint 11: db dump same issue)
- 01KC9JGV5886MAAP1A02QPJJHW (Sprint 13: general activity log issue)

## Estimated Complexity
Medium - requires integration with activity log system
