# Task Plan: Fix TypeError in roadmap start when estimated_tokens is None

## Bug ID
01KCEWQQQA930VK1J282TC9XGT

## Problem Statement
`vibey roadmap start <sprint-id>` fails with TypeError when tasks have null estimated_tokens.

Error location: `vibey/roadmap/compatibility.py:165`

Stack trace:
```
File "/Users/fredabood/Repositories/vibey/vibey/roadmap/compatibility.py", line 165, in check_task_compatibility
    utilization = (estimated_tokens / context_window) * 100
TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'
```

## Root Cause Analysis
The `check_task_compatibility` function doesn't handle the case where `estimated_tokens` is None before attempting division.

## Files to Modify

### Primary Files
1. `vibey/roadmap/compatibility.py` - Line 165

## Implementation Steps

1. **Add null check before division**
   ```python
   def check_task_compatibility(task: Task, context_window: int = 200000):
       """Check if task fits within context window."""
       estimated_tokens = task.estimated_tokens

       # Handle null estimated_tokens
       if estimated_tokens is None:
           # Skip compatibility check or use default
           return {
               "compatible": True,
               "utilization": None,
               "warning": "No token estimate available"
           }

       utilization = (estimated_tokens / context_window) * 100
       # ... rest of function
   ```

2. **Consider default value option**
   ```python
   # Alternative: use default token estimate
   DEFAULT_ESTIMATED_TOKENS = 1000  # Conservative default

   if estimated_tokens is None:
       estimated_tokens = DEFAULT_ESTIMATED_TOKENS
       warning = f"Using default estimate of {DEFAULT_ESTIMATED_TOKENS} tokens"
   ```

3. **Update callers to handle None utilization**
   - Check return value before displaying percentage

## Test Requirements
- Start sprint with task having null estimated_tokens - should not error
- Start sprint with task having estimated_tokens - should show utilization
- Verify compatibility check still works for valid cases

## Estimated Complexity
Simple - null check addition
