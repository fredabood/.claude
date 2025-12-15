# Task Plan: roadmap start command doesn't accept ULID format

## Bug ID
01KC9J8FKMMYCVQEZ891EX5JTD

## Problem Statement
The `vibey roadmap start <ULID>` command fails with 'Cannot determine item type from ID'. It only accepts slug format (e.g., track-sprint-task-num) but should also accept raw ULIDs.

## Root Cause Analysis
Same as Sprint 10 bug 01KCH7051YHKTSVQ21JRB81VM9 - the start command uses `-task-` string detection.

In `vibey/cli/roadmap_commands/start.py` line 14:
```python
if '-task-' in args.id:
    cmd = ["python3", str(script_path), "--start-task", args.id]
else:
    cmd = ["python3", str(script_path), "--start-sprint", args.id]
```

## Resolution
**DUPLICATE** - Close as duplicate of 01KCH7051YHKTSVQ21JRB81VM9

The fix for Sprint 10 ULID Support Task 001 (adding ULID detection and item type resolution) will resolve this. The start.py file has identical logic to complete.py and should be fixed together.

## Related Bugs
- 01KCH7051YHKTSVQ21JRB81VM9 (Sprint 10: complete command)
- 01KCEWQQQA930VK1J282TC9XGV (Sprint 15: same issue)

## Estimated Complexity
N/A - Duplicate
