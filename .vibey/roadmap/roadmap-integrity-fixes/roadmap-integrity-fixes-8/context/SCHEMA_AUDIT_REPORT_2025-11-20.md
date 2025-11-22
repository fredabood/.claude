# Schema Validation Audit Report

**Date:** 2025-11-20
**Sprint:** roadmap-integrity-fixes-8 (Task 001)
**Validator:** scripts/validate-roadmap-schema.py
**Scope:** 435 YAML files across 20 tracks

---

## Executive Summary

**Schema Compliance Rate:** 4.8% (21/435 files passing)
**Total Failures:** 414 files
**Critical Issues:** 110 files with blocking errors
**Root Cause:** Loader bug + schema mismatches + invalid enum values

### Key Findings

1. **85 files (77%)**: "Invalid tasks file format" - Loader bug, not data bug
2. **11 files**: Missing required `sprint_id` field in track.yaml
3. **11 files**: Missing required `task_id` field in sprint.yaml
4. **2 files**: Invalid GateStatus enum values
5. **1 file**: Task count mismatch

---

## Error Categorization

### 1. Invalid Task Format (85 files) - LOADER BUG

**Error Message:** `Unexpected error: Invalid tasks file format`

**Root Cause:**
The `load_tasks()` function in `yaml_loader.py:735` doesn't recognize the `task:` key (singular) when given a file path.

**Current Behavior:**
```python
# yaml_loader.py lines 724-735
if file_path.is_dir():
    # Correctly handles: {task: {...}}
elif isinstance(data, list):
    # Handles: [{...}, {...}]
elif 'tasks' in data:
    # Handles: {tasks: [...]}
else:
    raise ValueError("Invalid tasks file format")  # ❌ FAILS HERE
```

**Actual File Format:**
```yaml
# task.yaml (CORRECT format for hierarchical structure)
task:
  id: infrastructure-fixes-1-task-001
  name: Debug and fix roadmap CLI import error
  ...
```

**The Problem:**
When `validate-roadmap-schema.py` calls `load_task(file_path)` where `file_path` is a file (not directory), it passes the file path to `load_tasks()` which doesn't handle the `{task: ...}` format.

**Fix Strategy:** P0 - Fix loader, not data

```python
# yaml_loader.py line 734 - ADD THIS:
elif 'task' in data:  # Handle singular 'task' key
    tasks_data = [data['task']]
elif 'tasks' in data:
    tasks_data = data['tasks']
```

**Affected Files:** 85 task.yaml files across 9 sprints
- infrastructure-fixes-1: 13 tasks
- mcp-server-1: 8 tasks
- mcp-server-2: 8 tasks
- core-framework-2: 13 tasks
- core-framework-3: 7 tasks
- missing-agents-1: 11 tasks
- documentation-system-1: 8 tasks
- documentation-system-2: 6 tasks
- documentation-system-3: 5 tasks
- roadmap-integration-1: 2 tasks
- roadmap-integration-2: 2 tasks
- roadmap-integration-3: 5 tasks

**Estimated Fix Time:** 15 minutes (1 line code change + test)

---

### 2. Missing `sprint_id` in track.yaml (11 files) - DATA BUG

**Error Message:** `Unexpected error: 'sprint_id'`

**Root Cause:**
Track model expects `sprint_id` field but these tracks don't have it.

**Affected Tracks:**
1. aider-port
2. windsurf-port
3. continue-port
4. multi-platform
5. mcp-server
6. core-framework
7. directory-migration
8. missing-agents
9. documentation-system
10. roadmap-system
11. testing-system

**Fix Strategy:** P1 - Add missing field or make optional

**Option 1: Add sprint_id field (if applicable)**
```yaml
# track.yaml
track:
  id: aider-port
  sprint_id: aider-port-1  # Current sprint
  ...
```

**Option 2: Make field optional in model**
```python
# models/track.py
class Track:
    sprint_id: Optional[str] = None  # Current sprint ID
```

**Recommended:** Option 2 (make optional)
**Rationale:** Not all tracks have an active sprint. Field should be optional and populated only when a sprint is in progress.

**Estimated Fix Time:** 2 hours (update model + validate all tracks)

---

### 3. Missing `task_id` in sprint.yaml (11 files) - DATA BUG

**Error Message:** `Unexpected error: 'task_id'`

**Root Cause:**
Sprint model expects `task_id` field but these sprints don't have it.

**Affected Sprints:**
1. mcp-server-1
2. mcp-server-2
3. core-framework-2
4. core-framework-3
5. missing-agents-1
6. documentation-system-1
7. documentation-system-2
8. documentation-system-3
9. roadmap-integration-1
10. roadmap-integration-2
11. roadmap-integration-3

**Fix Strategy:** P1 - Make field optional or remove from model

**Analysis:**
Sprint should NOT have a `task_id` field. Sprints contain multiple tasks. The model likely has this field by mistake or it's for a different purpose (like "current active task").

**Recommended:** Make optional with clear documentation
```python
# models/sprint.py
class Sprint:
    task_id: Optional[str] = None  # Current active task (if applicable)
```

**Estimated Fix Time:** 1 hour (update model + validate)

---

### 4. Invalid GateStatus Values (2 files) - DATA BUG

**Error 1:** `'conditionally_passed' is not a valid GateStatus`
**File:** claude-port/track.yaml

**Error 2:** `'superseded' is not a valid GateStatus`
**File:** roadmap-integration/track.yaml

**Root Cause:**
These tracks use GateStatus values that don't exist in the enum.

**Valid GateStatus Values:**
```python
# models/common.py
class GateStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
```

**Fix Strategy:** P0 - Replace with valid values

**claude-port/track.yaml:**
```yaml
# Before:
quality_gates:
  - status: conditionally_passed

# After:
quality_gates:
  - status: passed  # Or add note explaining conditions
```

**roadmap-integration/track.yaml:**
```yaml
# Before:
quality_gates:
  - status: superseded

# After:
quality_gates:
  - status: skipped  # If superseded means not applicable
```

**Estimated Fix Time:** 30 minutes (inspect context + fix 2 files)

---

### 5. Task Count Mismatch (1 file) - DATA BUG

**Error:** `Tasks total (13) must equal sum of task types (17)`
**File:** infrastructure-fixes/infrastructure-fixes-1/sprint.yaml

**Root Cause:**
Sprint progress shows `tasks_total: 13` but task type breakdown sums to 17.

**Fix Strategy:** P1 - Recalculate and update

**Investigation needed:**
1. Count actual tasks in sprint
2. Verify task type breakdown
3. Update to correct values

**Estimated Fix Time:** 15 minutes (count + update)

---

## Fix Priority & Sequence

### Phase 1: Fix Loader (15 minutes)
**P0 - Blocks all other validation**

1. Add `elif 'task' in data:` to yaml_loader.py:734
2. Test with one failing task file
3. Re-run validation to verify 85 errors resolved

**Expected Result:** 85 → 0 errors, revealing true schema issues

---

### Phase 2: Fix Data Issues (3.5 hours)

**P0 - Critical (30 minutes)**
- Fix 2 invalid GateStatus values

**P1 - High (3 hours)**
- Make `sprint_id` optional in Track model (2h)
- Make `task_id` optional in Sprint model (1h)
- Fix task count mismatch (15min)

---

### Phase 3: Comprehensive Validation (2 hours)

After Phase 1-2 fixes:
1. Run schema validator again
2. Check for newly revealed errors
3. Run health dashboard
4. Verify 100% schema compliance

---

## Discrepancy Analysis

**Schema Validator:** 110 failures
**Health Dashboard:** 414 failures (4.8% pass rate)

**Why the difference?**

The schema validator **fails fast** on loader errors and doesn't continue validation. The health dashboard uses different validation logic that catches more issues.

**After fixing the loader bug**, we'll see the true number of schema issues.

---

## Testing Strategy

### Before Fixes
```bash
python scripts/validate-roadmap-schema.py --verbose > before-fix.txt
```

### After Phase 1 (Loader Fix)
```bash
python scripts/validate-roadmap-schema.py --verbose > after-loader-fix.txt
diff before-fix.txt after-loader-fix.txt
```

### After Phase 2 (Data Fixes)
```bash
python scripts/validate-roadmap-schema.py --strict
# Expected: 0 failures

python scripts/roadmap-health-dashboard.py
# Expected: Schema Compliance: 100%
```

---

## Recommendations

### Immediate Actions (P0)

1. **Fix loader bug** - 1 line code change unblocks everything
2. **Fix invalid enum values** - 2 files, prevents validation failures

### Short-term Actions (P1)

3. **Update models** - Make optional fields actually optional
4. **Fix data inconsistencies** - Task count mismatch

### Long-term Actions (P2)

5. **Add schema migration script** - Automate future fixes
6. **CI/CD validation** - Block PRs with schema violations
7. **Pre-commit hooks** - Catch issues before commit

---

## Files for Reference

**Loader:** `/workspaces/vibey/vibey/roadmap/serialization/yaml_loader.py:724-735`
**Validator:** `/workspaces/vibey/scripts/validate-roadmap-schema.py`
**Models:** `/workspaces/vibey/vibey/roadmap/models/`
**Test Data:** `/workspaces/vibey/.vibey/roadmap/`

---

## Next Steps

1. ✅ Audit complete (this report)
2. ⏭️ **Task 002**: Fix loader bug (15min)
3. ⏭️ **Task 003**: Fix invalid enum values (30min)
4. ⏭️ **Task 004**: Update models for optional fields (3h)
5. ⏭️ **Task 005**: Validate 100% pass rate (2h)

---

**Report Generated:** 2025-11-20
**Auditor:** Claude Code
**Status:** Sprint 8 Task 001 COMPLETE
