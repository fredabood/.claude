# Schema Fix Strategy

**Sprint:** roadmap-integrity-fixes-8
**Created:** 2025-11-20
**Based on:** SCHEMA_AUDIT_REPORT_2025-11-20.md

---

## Overview

This document provides step-by-step fix strategies for each category of schema validation error found during the audit.

**Total Errors:** 110 files
**Estimated Total Time:** 4-5 hours
**Priority Order:** Loader bug → Enum values → Model updates → Data fixes

---

## Strategy 1: Fix YAML Loader Bug (P0 - 15 minutes)

### Problem
85 task.yaml files fail with "Invalid tasks file format" because the loader doesn't recognize the `{task: ...}` format when given a file path.

### Root Cause
`yaml_loader.py` lines 724-735: Missing check for singular `task` key

### Fix Steps

**1. Update yaml_loader.py (5 minutes)**

```python
# File: vibey/roadmap/serialization/yaml_loader.py
# Location: Line 734 (before the else clause)

# BEFORE:
    else:
        # Legacy flat structure
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        # Tasks can be a list or dict with 'tasks' key
        if isinstance(data, list):
            tasks_data = data
        elif 'tasks' in data:
            tasks_data = data['tasks']
        else:
            raise ValueError("Invalid tasks file format")

# AFTER:
    else:
        # Legacy flat structure
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        # Tasks can be a list or dict with 'tasks'/'task' key
        if isinstance(data, list):
            tasks_data = data
        elif 'task' in data:
            # Single task file (hierarchical structure)
            tasks_data = [data['task']]
        elif 'tasks' in data:
            # Multiple tasks file (legacy structure)
            tasks_data = data['tasks']
        else:
            raise ValueError("Invalid tasks file format")
```

**2. Test the fix (5 minutes)**

```bash
# Test with one failing file
python3 -c "
from pathlib import Path
from vibey.roadmap.serialization import load_task

task_path = Path('.vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/infrastructure-fixes-1-task-001/task.yaml')
task = load_task(task_path)
print(f'✅ Successfully loaded: {task.id}')
"
```

**3. Validate all files (5 minutes)**

```bash
python scripts/validate-roadmap-schema.py --verbose | grep -c "✗.*Invalid tasks file format"
# Expected: 0 (down from 85)
```

### Expected Impact
- Resolves 85 of 110 errors (77%)
- Reveals true schema validation issues
- Unblocks all task validation

---

## Strategy 2: Fix Invalid GateStatus Values (P0 - 30 minutes)

### Problem
2 tracks use invalid GateStatus enum values:
- `conditionally_passed` (claude-port)
- `superseded` (roadmap-integration)

### Fix Steps

**1. Fix claude-port/track.yaml (15 minutes)**

```bash
# Inspect the file
grep -B 5 -A 5 "conditionally_passed" .vibey/roadmap/claude-port/track.yaml
```

**Determine correct status:**
- If gate passed with conditions → `passed`
- If gate partially passed → `in_progress`
- If gate blocked → `blocked`

**Replace value:**
```yaml
# BEFORE:
quality_gates:
  - id: completion-gate
    status: conditionally_passed

# AFTER:
quality_gates:
  - id: completion-gate
    status: passed
    notes: "Passed with conditions documented in sprint notes"
```

**2. Fix roadmap-integration/track.yaml (15 minutes)**

```bash
# Inspect the file
grep -B 5 -A 5 "superseded" .vibey/roadmap/roadmap-integration/track.yaml
```

**Determine correct status:**
- If gate no longer applicable → `skipped`
- If gate replaced by new gate → `skipped`

**Replace value:**
```yaml
# BEFORE:
quality_gates:
  - id: old-gate
    status: superseded

# AFTER:
quality_gates:
  - id: old-gate
    status: skipped
    notes: "Superseded by new quality gate in Sprint 2"
```

### Expected Impact
- Resolves 2 critical enum validation errors
- Prevents future invalid enum usage

---

## Strategy 3: Update Models for Optional Fields (P1 - 3 hours)

### Problem A: Missing sprint_id in 11 tracks

**Current Model:**
```python
class Track:
    sprint_id: str  # Required but not always applicable
```

**Fix: Make Optional (1.5 hours)**

```python
# File: vibey/roadmap/models/track.py

from typing import Optional

class Track:
    sprint_id: Optional[str] = None  # ID of current active sprint, if any
```

**Validation:**
1. Update model
2. Run tests: `pytest tests/ -k track`
3. Validate all tracks load correctly
4. Update documentation

---

### Problem B: Missing task_id in 11 sprints

**Current Model:**
```python
class Sprint:
    task_id: str  # Required but unclear purpose
```

**Fix: Make Optional (1.5 hours)**

```python
# File: vibey/roadmap/models/sprint.py

from typing import Optional

class Sprint:
    task_id: Optional[str] = None  # ID of current active task, if any
```

**Validation:**
1. Update model
2. Run tests: `pytest tests/ -k sprint`
3. Validate all sprints load correctly
4. Update documentation

---

## Strategy 4: Fix Task Count Mismatch (P1 - 15 minutes)

### Problem
infrastructure-fixes-1/sprint.yaml: `tasks_total: 13` but task types sum to 17

### Fix Steps

**1. Count actual tasks**
```bash
ls .vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/ | grep task | wc -l
```

**2. Inspect sprint.yaml**
```bash
grep -A 10 "progress:" .vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/sprint.yaml
```

**3. Determine correct values**
```yaml
# Example fix:
progress:
  development_tasks: 10
  testing_tasks: 2
  documentation_tasks: 1
  tasks_total: 13  # Should equal sum of above
  tasks_completed: X
```

**4. Update and validate**
```bash
python scripts/validate-roadmap-schema.py --verbose | grep infrastructure-fixes-1
# Should pass
```

---

## Execution Plan

### Phase 1: Critical Fixes (45 minutes)
**DO FIRST - Unblocks everything else**

1. ✅ **Strategy 1**: Fix loader bug (15min)
   - Unblocks 85 task validations
   - Reveals true schema issues

2. ✅ **Strategy 2**: Fix enum values (30min)
   - Resolves 2 critical validation failures
   - Quick win, high impact

**Checkpoint:** Run validator, expect ~23 remaining errors (110 - 85 - 2)

---

### Phase 2: Model Updates (3 hours)
**Required for remaining 22 errors**

3. ✅ **Strategy 3A**: Make track.sprint_id optional (1.5h)
   - Resolves 11 track validation errors

4. ✅ **Strategy 3B**: Make sprint.task_id optional (1.5h)
   - Resolves 11 sprint validation errors

**Checkpoint:** Run validator, expect ~1 remaining error

---

### Phase 3: Data Cleanup (15 minutes)
**Final polish**

5. ✅ **Strategy 4**: Fix task count mismatch (15min)
   - Resolves last remaining error

**Checkpoint:** Run validator, expect 0 errors

---

### Phase 4: Comprehensive Validation (2 hours)
**Verify 100% compliance**

6. Run full validation suite
7. Run health dashboard
8. Document results
9. Update Sprint 8 progress

---

## Testing Checklist

After each phase:

```bash
# Schema validation
python scripts/validate-roadmap-schema.py --strict

# Health dashboard
python scripts/roadmap-health-dashboard.py

# Specific checks
python -c "
from vibey.roadmap.serialization import load_track, load_sprint, load_task
from pathlib import Path

# Test one file from each type
track = load_track(Path('.vibey/roadmap/core-framework/track.yaml'))
print(f'✅ Track: {track.id}')

sprint = load_sprint(Path('.vibey/roadmap/core-framework/core-framework-2'))
print(f'✅ Sprint: {sprint.id}')

task = load_task(Path('.vibey/roadmap/core-framework/core-framework-2/core-framework-2-task-001/task.yaml'))
print(f'✅ Task: {task.id}')
"
```

---

## Rollback Plan

If any fix causes issues:

**1. Loader Fix:**
```bash
git checkout HEAD -- vibey/roadmap/serialization/yaml_loader.py
```

**2. Enum Fix:**
```bash
git checkout HEAD -- .vibey/roadmap/claude-port/track.yaml
git checkout HEAD -- .vibey/roadmap/roadmap-integration/track.yaml
```

**3. Model Updates:**
```bash
git checkout HEAD -- vibey/roadmap/models/track.py
git checkout HEAD -- vibey/roadmap/models/sprint.py
```

**4. Data Fixes:**
```bash
git checkout HEAD -- .vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/sprint.yaml
```

---

## Success Criteria

- ✅ All 435 files pass schema validation (100%)
- ✅ Health score increases to 98+/100
- ✅ Zero critical or high severity schema issues
- ✅ All tests pass
- ✅ Documentation updated
- ✅ Fixes committed with clear messages

---

## Notes

- Always test after each phase
- Commit after each successful phase
- Document any unexpected issues
- Update this strategy if new patterns emerge

---

**Next:** Begin execution with Strategy 1 (Fix loader bug)
