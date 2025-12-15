# Task Plan: Fix roadmap start command not recognizing ULID task IDs

## Bug ID
01KCEWQQQA930VK1J282TC9XGV

## Problem Statement
`vibey roadmap start <task-ulid>` fails with ID format error.

Error message:
```
Error: Cannot determine item type from ID: 01KCC0GB5D8K0D60VTX96Z7NZS
Expected format: <track>-<sprint>-task-<num> or <track>-<sprint>[-name]
```

The start command only recognizes legacy slug-based IDs, not the new ULID format.

## Root Cause Analysis
Same as Sprint 10 bug 01KCH7051YHKTSVQ21JRB81VM9 and Sprint 13 bug 01KC9J8FKMMYCVQEZ891EX5JTD.

In `vibey/cli/roadmap_commands/start.py`:
```python
if '-task-' in args.id:
    cmd = ["python3", str(script_path), "--start-task", args.id]
else:
    cmd = ["python3", str(script_path), "--start-sprint", args.id]
```

## Resolution
**DUPLICATE** - Close as duplicate of 01KCH7051YHKTSVQ21JRB81VM9

The fix for Sprint 10 ULID Support Task 001 will resolve this. The start.py and complete.py files have identical ID detection logic and should be fixed together.

## Implementation Reference
See Sprint 10 ULID Support TASK_001_PLAN.md for full implementation details.

Key changes:
1. Add `is_ulid()` helper function
2. Add `get_item_type_from_ulid()` to check filesystem
3. Update start.py to detect ULIDs and resolve item type

## Estimated Complexity
N/A - Duplicate
