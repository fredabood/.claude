# Test Failures Analysis - 2025-11-12

**Status:** In Progress
**Test Suite:** tests/cli/test_roadmap_cli_comprehensive.py
**Failures:** 17 out of 57 tests failing

---

## Summary

Investigation of 17 failing tests in the comprehensive CLI test suite revealed several root causes requiring fixes. Initial defensive coding was applied to the YAML loader, but additional work is needed.

---

## Test Failures Breakdown

### Category 1: AttributeError - 'str' object has no attribute 'get' (Multiple Tests)

**Affected Tests:**
- test_roadmap_status_filter_by_sprint
- test_roadmap_show_sprint
- test_roadmap_context_task (multiple variations)
- test_detailed_view_formatting
- test_sprint_lifecycle

**Error Message:**
```
❌ Error: 'str' object has no attribute 'get'
```

**Root Cause Analysis:**
1. **Primary Issue (FIXED):** YAML loader in `vibey/roadmap/serialization/yaml_loader.py` line 601 was accessing `sprint_data['metadata']` directly without checking if it's a dict
   - Fixed by adding defensive coding to handle non-dict metadata

2. **Secondary Issue (PENDING):** Error propagation in CLI causes dict/string mismatches
   - query_sprint_details() returns a dict successfully when called directly
   - Error only occurs through full CLI path (`python -m vibey roadmap show...`)
   - Suggests issue in CLI layer between commands.py and formatters

**Files Modified:**
- `/vibey/roadmap/serialization/yaml_loader.py` - Added defensive metadata handling

**Next Steps:**
- Debug CLI error propagation between query and format functions
- Check if exception handling is converting dicts to strings somewhere
- Verify format_sprint_details receives correct data type

---

### Category 2: Summarize Command Path Issues

**Affected Tests:**
- test_roadmap_summarize_sprint
- test_roadmap_summarize_track
- test_summarize_output_format

**Error Message:**
```
❌ Sprint file not found: /path/.vibey/roadmap/sprints/user-management-1-auth.yaml
```

**Root Cause:**
- Summarize command looking in old flat structure (`.vibey/roadmap/sprints/`)
- Should use hierarchical structure (`.vibey/roadmap/track-id/sprint-id/`)

**Files to Fix:**
- Check `vibey/cli/roadmap-summarize.py` or `vibey/operations/roadmap/summarize.py`
- Update path resolution to use FileSystemManager

---

### Category 3: Idempotent Operation Issues

**Affected Tests:**
- test_roadmap_start_already_started
- test_idempotent_state_operations

**Error:**
```
❌ Sprint already started (status: in_progress)
```
**Expected:** Return code 0 (success - idempotent)
**Actual:** Return code 1 (error)

**Root Cause:**
- Start command returns error when item is already in_progress
- Should be idempotent (succeed without changes if already in desired state)

**Files to Fix:**
- Check start command implementation
- Make it return success if already in desired state

---

### Category 4: Field Name Mismatch

**Affected Tests:**
- test_roadmap_complete_task

**Issue:**
```python
# Test expects:
assert "completed_at" in data["task"]

# But model has:
data["task"]["completed"]  # datetime field without "_at" suffix
```

**Root Cause:**
- Test assertion uses wrong field name
- Task model uses `completed`, `started` (not `completed_at`, `started_at`)

**Fix:** Update test to use correct field names

---

### Category 5: Error Exit Code Issues

**Affected Tests:**
- test_error_message_formatting
- test_ready_to_start_after_dependency_resolves

**Issue:**
```python
# Test expects non-zero for errors:
assert result.returncode != 0

# But command returns:
result.returncode == 0  # Success even for errors
```

**Root Cause:**
- Error messages printed but exit code not set correctly
- Commands should return non-zero on error

---

## Fixes Applied

### 1. YAML Loader Metadata Handling

**File:** `vibey/roadmap/serialization/yaml_loader.py`

**Change:**
```python
# Before (line 601):
meta_data = sprint_data['metadata']

# After:
meta_data = sprint_data.get('metadata')
if not meta_data or not isinstance(meta_data, dict):
    from datetime import timezone
    meta_data = {'last_updated': datetime.now(timezone.utc).isoformat()}
```

**Impact:**
- Prevents AttributeError when metadata is missing or not a dict
- Provides sensible defaults
- Fixes the primary cause of "'str' object has no attribute 'get'" error

---

## Remaining Work

### Priority 1: CLI Error Propagation (CRITICAL)

**Status:** Needs Investigation

The query functions work correctly when called directly, but fail through the CLI. This suggests:
1. Exception handling converting data types
2. Middleware modifying responses
3. Caching issues

**Debug Approach:**
1. Add logging to track data types through CLI pipeline
2. Check commands.py exception handling
3. Verify formatters.py input validation

### Priority 2: Summarize Command Paths (HIGH)

**Status:** Clear Fix Needed

Update path resolution in summarize command to use hierarchical structure via FileSystemManager.

### Priority 3: Idempotent Operations (MEDIUM)

**Status:** Design Decision + Implementation

Decide on idempotent behavior pattern, then implement across start/complete commands.

### Priority 4: Test Assertions (LOW)

**Status:** Simple Fixes

Update test expectations to match actual model field names.

---

## Testing Strategy

### Unit Test Approach
```bash
# Test specific failing test:
python3 -m pytest tests/cli/test_roadmap_cli_comprehensive.py::TestRoadmapShow::test_roadmap_show_sprint -xvs

# Test all show command tests:
python3 -m pytest tests/cli/test_roadmap_cli_comprehensive.py::TestRoadmapShow -xvs

# Test all failing tests:
python3 -m pytest tests/cli/test_roadmap_cli_comprehensive.py -k "show_sprint or summarize or start_already" -xvs
```

### Debug Scripts Created

1. `debug_test.py` - Tests query functions directly (WORKS)
2. `debug_cli_test.py` - Tests full CLI path (FAILS)

These scripts help isolate where the error occurs in the pipeline.

---

## Metrics

**Current Status:**
- **Tests Passing:** 40/57 (70%)
- **Tests Failing:** 17/57 (30%)
- **Fixes Applied:** 1 (metadata handling)
- **Fixes Pending:** 5 categories

**Target:**
- **Goal:** 57/57 tests passing (100%)
- **Estimated Time:** 4-6 hours for remaining fixes

---

## Notes

1. The YAML loader fix is defensive and backward-compatible
2. Test helper creates valid YAML, so issue is in loading/processing
3. Direct function calls work; CLI path fails (points to CLI layer issue)
4. Some tests may need update (field names), not code fixes

---

**Last Updated:** 2025-11-12
**Next Action:** Debug CLI error propagation in commands.py/formatters.py
