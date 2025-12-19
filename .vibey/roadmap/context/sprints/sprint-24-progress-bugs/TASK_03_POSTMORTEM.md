# Task 03 Postmortem: Database Rebuild Validation Errors

**Task ID:** 01KCVMA0FT9M259NES1XF022T1
**Date:** 2025-12-19
**Status:** RESOLVED

## Problem Summary

The `vibey roadmap db rebuild` command was skipping ~90% of roadmap data (1500+ items) due to validation errors like "Completed tracks must have a completion date".

### Before Fix
- Loaded: 21 tracks, 59 sprints, 193 tasks
- Skipped: 27 tracks, 173 sprints, 1397 tasks

### After Fix
- Loaded: 48 tracks, 232 sprints, 1588 tasks
- Skipped: 0 tracks, 0 sprints, 2 tasks (unrelated v2 format issue)

## Root Cause Analysis

### Primary Issue: V2 Format Detection False Positive

The `detect_yaml_format()` function in `yaml_loader.py` incorrectly detected v1 format YAML files as v2 format because:

1. The v2 format indicator `assigned_agents` field also exists in v1 format YAML files
2. When detected as v2, `_convert_v2_track_to_v1()` was called
3. This function looked for v2 field names (`created_at`, `started_at`, `completed_at`) instead of v1 field names (`created`, `started`, `completed`)
4. Since the YAML had v1 field names, dates like `completed` were parsed as `None`
5. This triggered validators: "Completed tracks must have a completion date"

### Code Flow
```
load_track() -> detect_yaml_format() -> returns 'v2' (incorrect)
             -> _convert_v2_track_to_v1()
             -> looks for 'completed_at' field (not present)
             -> passes None to Track constructor
             -> Track.__post_init__() validator fails
```

## Solution

Modified `_convert_v2_track_to_v1()` in `/vibey/roadmap/serialization/yaml_loader.py` to check both v1 and v2 field names:

```python
# Before (only checked v2 field names)
created=_parse_datetime(track_data.get('created_at')) or datetime.now(timezone.utc),
started=_parse_datetime(track_data.get('started_at')),
completed=_parse_datetime(track_data.get('completed_at')),

# After (checks both v1 and v2 field names)
created = _parse_datetime(track_data.get('created_at') or track_data.get('created')) or datetime.now(timezone.utc)
started = _parse_datetime(track_data.get('started_at') or track_data.get('started'))
completed = _parse_datetime(track_data.get('completed_at') or track_data.get('completed'))
```

## Files Changed

- `/vibey/roadmap/serialization/yaml_loader.py` - Lines 709-724

## Lessons Learned

1. **Format detection heuristics can be fragile** - The presence of a field doesn't reliably indicate format version if the field exists in both formats.

2. **Be defensive when handling multiple formats** - Converters should check all possible field names when bridging between formats.

3. **Test with real data** - The issue was only discovered when loading actual roadmap data, not test fixtures.

## Related Issues

Two tasks are still skipped due to a separate issue:
- `01KCVMA0F3G5XHEG45BX363K6V.yaml` - Missing `sprint_id` (pure v2 format uses `parent_ref`)
- `01KCVMA0FDHNQQZ8SXSE4RCT3C.yaml` - Same issue

These tasks are in pure v2 format and need `load_task()` to handle v2 format properly (out of scope for this fix).

## Verification

```bash
# Run rebuild to verify fix
vibey roadmap db rebuild --force

# Expected output:
# Loaded 48 tracks, 232 sprints, 1588 tasks
# Skipped 0 tracks, 0 sprints, 2 tasks (validation errors)
```

## Prevention

Consider adding:
1. More robust format detection (check for multiple indicators)
2. Integration tests that use real roadmap data samples
3. Better error messages that include field name suggestions
