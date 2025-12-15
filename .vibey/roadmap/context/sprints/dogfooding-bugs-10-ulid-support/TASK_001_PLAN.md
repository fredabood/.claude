# Task Plan: CLI complete command doesn't support ULID task IDs

## Bug ID
01KCH7051YHKTSVQ21JRB81VM9

## Problem Statement
The `vibey roadmap complete` command expects slug-based IDs but the roadmap now uses ULIDs. Error: 'Cannot find track or sprint with ID: 01KC81GRE7HFXA9J6FYFM7H3BY'. Need to update argument parsing to accept both ULID and slug formats.

## Root Cause Analysis
In `vibey/cli/roadmap_commands/complete.py` line 14:
```python
if '-task-' in args.id:
    cmd = ["python3", str(script_path), "--complete-task", args.id]
else:
    cmd = ["python3", str(script_path), "--complete-sprint", args.id]
```

The code checks for `-task-` substring to determine if the ID is a task. ULIDs don't contain this pattern, so they're incorrectly identified as sprints.

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap_commands/complete.py` - Fix ID type detection
2. `vibey/cli/roadmap_commands/start.py` - Same issue, fix together
3. `vibey/cli/commands.py` - _resolve_id function may need updates

## Implementation Steps

1. **Create ULID detection helper**
   ```python
   def is_ulid(id_str: str) -> bool:
       """Check if string is a ULID (26 alphanumeric chars)."""
       return len(id_str) == 26 and id_str.isalnum()
   ```

2. **Create item type resolver for ULIDs**
   ```python
   def get_item_type_from_ulid(root_dir: Path, ulid: str) -> str:
       """Determine if ULID is a task, sprint, or track."""
       fs = FileSystemManager(root_dir)

       # Check tasks directory
       if (fs.roadmap_root / "tasks" / f"{ulid}.yaml").exists():
           return "task"
       # Check sprints directory
       if (fs.roadmap_root / "sprints" / f"{ulid}.yaml").exists():
           return "sprint"
       # Check tracks directory
       if (fs.roadmap_root / "tracks" / f"{ulid}.yaml").exists():
           return "track"

       raise ValueError(f"Cannot find item with ID: {ulid}")
   ```

3. **Update complete.py**
   ```python
   def handle_complete(args):
       if is_ulid(args.id):
           item_type = get_item_type_from_ulid(Path.cwd(), args.id)
       elif '-task-' in args.id:
           item_type = 'task'
       else:
           item_type = 'sprint'
   ```

4. **Apply same fix to start.py**

## Test Requirements
- `vibey roadmap complete 01KC...` (task ULID) - should complete task
- `vibey roadmap complete 01KC...` (sprint ULID) - should complete sprint
- `vibey roadmap complete track-sprint-task-001` - legacy format still works

## Related Bugs
- 01KC8FTXZB94YTTB79VPK3SNRM (Sprint 11: same issue)
- 01KCEWQQQA930VK1J282TC9XGV (Sprint 15: start command same issue)
- 01KC9J8FKMMYCVQEZ891EX5JTD (Sprint 13: start command same issue)

## Estimated Complexity
Medium - requires item type detection from filesystem
