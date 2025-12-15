# Task Plan: CLI complexity choices don't match model enum values

## Bug ID
01KCAKHCZDGXXGAATBXSXW42Y3

## Problem Statement
CLI accepts `trivial/low/medium/high/complex` for --complexity but the model only has `simple/medium/complex`. Using `low` or `trivial` causes 'not a valid Complexity' validation errors.

## Root Cause Analysis
1. The `Complexity` enum in `vibey/roadmap/models/common.py` defines:
   - `SIMPLE = "simple"`
   - `MEDIUM = "medium"`
   - `COMPLEX = "complex"`

2. CLI commands (create-task, etc.) use hardcoded choice lists that don't match the enum.

## Files to Modify

### Primary Files
1. `vibey/cli/main.py` - CLI entry point with Click options
2. `vibey/cli/commands.py` - Command implementations

### Search Pattern
```bash
grep -r "trivial\|low.*high\|complexity.*choice" vibey/cli/
```

## Implementation Steps

1. **Find all CLI complexity choice definitions**
   - Search for Click options with complexity choices
   - Identify all places where the wrong values are used

2. **Update choices to match enum**
   - Replace `trivial/low/medium/high/complex` with `simple/medium/complex`
   - Use `[c.value for c in Complexity]` to derive choices from enum

3. **Add validation layer**
   - Import Complexity enum in CLI modules
   - Use enum values directly instead of hardcoded strings

4. **Update help text**
   - Ensure --help shows correct valid values

## Test Requirements
- Run `vibey roadmap create-task --help` - verify shows simple/medium/complex
- Create task with `--complexity simple` - should succeed
- Create task with `--complexity low` - should fail with clear error

## Related Bugs
- 01KC8FV9S1CWR4ZZ0VH4CEF9WW (Sprint 11: same issue)
- 01KC9JEJH4N15DS7NT0WMFPCHZ (Sprint 13: --help shows wrong values)
- 01KCC8ZBEZK4VYYYYVW8HM4DFW (Sprint 14: same issue)

## Estimated Complexity
Simple - string replacement with enum import
