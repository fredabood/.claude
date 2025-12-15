# Task Plan: CLI commands don't create activity log entries for pre-commit hook

## Bug ID
01KC9JGV5886MAAP1A02QPJJHW

## Problem Statement
When using CLI commands like create-sprint, create-task, and db dump, the activity log entries are not created. This causes the pre-commit hook to block commits with 'No activity log entry for' errors, even though the CLI was used.

## Root Cause Analysis
This is a consolidation bug that encompasses multiple specific issues:
- Sprint 9: create-sprint/create-task (01KCAKH33KHF0HWVTM5C7AP3Y2)
- Sprint 11: db dump (01KC8FGN8HVDFHC9MYVRFK3WHN)

The root cause is that several CLI commands write YAML files but don't call the JSONL activity log writer.

## Files to Modify

### Primary Files
1. `vibey/cli/commands.py` - All create/update commands
2. `vibey/operations/roadmap/jsonl_activity_log.py` - Activity log writer

### Commands Needing Activity Log Integration
- `create-track`
- `create-sprint`
- `create-task`
- `db dump`
- `db rebuild`
- Any command that creates or modifies YAML files

## Implementation Steps

1. **Audit all commands for YAML writes**
   ```bash
   grep -rn "save_\|write_\|dump_" vibey/cli/commands.py
   ```

2. **Create unified logging helper**
   ```python
   def log_roadmap_file_change(
       root_dir: Path,
       file_path: Path,
       action: str,
       entity_id: str,
       source: str = "cli"
   ):
       """Log a roadmap file modification for pre-commit hook."""
       from vibey.operations.roadmap.jsonl_activity_log import JSONLActivityLog
       log = JSONLActivityLog(root_dir)
       log.log_file_modification(
           file_path=file_path,
           action=action,
           entity_id=entity_id,
           source=source
       )
   ```

3. **Integrate into each command**
   - Add logging call after each YAML write
   - Include command name as source

4. **Verify pre-commit hook checks**
   - Ensure hook looks for entries in correct location
   - Ensure entry format matches hook expectations

## Test Requirements
- Run each create command - verify activity log entry
- Git commit after CLI changes - hook should pass
- Verify entries in `.vibey/roadmap/activity_log/`

## Related Bugs
- 01KCAKH33KHF0HWVTM5C7AP3Y2 (Sprint 9)
- 01KC8FGN8HVDFHC9MYVRFK3WHN (Sprint 11)

## Resolution
This is a meta-bug. Fixing the specific bugs (Sprint 9 Task 003, Sprint 11 Task 004) will resolve this.

## Estimated Complexity
Medium - requires integration across multiple commands
