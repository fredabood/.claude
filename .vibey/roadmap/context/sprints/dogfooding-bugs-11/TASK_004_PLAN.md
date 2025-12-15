# Task Plan: db dump command does not create activity log entries

## Bug ID
01KC8FGN8HVDFHC9MYVRFK3WHN

## Problem Statement
The `roadmap db dump` command exports YAML files from the database but does not create corresponding activity log entries. This causes the pre-commit hook to block commits because it cannot find activity log entries for the modified roadmap files.

## Root Cause Analysis
The `sql_dumper` module writes YAML files but doesn't call the activity logging functions. The pre-commit hook requires activity log entries for all roadmap file modifications.

## Files to Modify

### Primary Files
1. `vibey/roadmap/serialization/sql_dumper.py` - Add activity logging
2. `vibey/cli/commands.py` - db_dump_cmd function

### Activity Log Integration
1. `vibey/operations/roadmap/jsonl_activity_log.py` - JSONL log writer

## Implementation Steps

1. **Find db dump implementation**
   ```bash
   grep -n "def db_dump\|def dump" vibey/roadmap/serialization/sql_dumper.py
   grep -n "db.*dump" vibey/cli/commands.py
   ```

2. **Add activity log callback to dumper**
   ```python
   def dump_to_yaml(
       db_path: Path,
       output_dir: Path,
       on_file_written: Callable[[Path, str], None] = None
   ):
       """Dump database to YAML files."""
       # ... existing code ...
       for task in tasks:
           path = write_task_yaml(task, output_dir)
           if on_file_written:
               on_file_written(path, "task_exported")
   ```

3. **Integrate with activity log in CLI**
   ```python
   def db_dump_cmd():
       from vibey.operations.roadmap.jsonl_activity_log import JSONLActivityLog

       log = JSONLActivityLog(root_dir)

       def log_export(path: Path, action: str):
           log.log_file_modification(path, action, "db_dump")

       dump_to_yaml(db_path, output_dir, on_file_written=log_export)
   ```

4. **Ensure entry format matches hook expectations**
   - Include file path relative to roadmap root
   - Include timestamp
   - Include action type

## Test Requirements
- Run `vibey roadmap db dump`
- Check activity log has entries for each file
- Git commit should pass pre-commit hook

## Related Bugs
- 01KCAKH33KHF0HWVTM5C7AP3Y2 (Sprint 9: create commands same issue)
- 01KC9JGV5886MAAP1A02QPJJHW (Sprint 13: general activity log issue)

## Estimated Complexity
Medium - requires callback integration
