# Roadmap CLI Bugs - Sprint State Management

**Date:** 2025-11-20
**Context:** Attempting to use `vibey roadmap complete` to mark Sprint 7 tasks as completed
**Result:** Multiple bugs prevented deterministic YAML updates via CLI

---

## Bug 1: Deliverables Schema Incompatibility

**Location:** `/workspaces/vibey/vibey/roadmap/serialization/yaml_loader.py:817`

**Error:**
```
KeyError: 'type'
```

**Root Cause:**
The `load_tasks()` function expects deliverables in the format:
```yaml
deliverables:
  - type: documentation
    paths:
      - path/to/file
```

But Sprint 7 task YAML files had deliverables as plain strings:
```yaml
deliverables:
  - Fixed aider-port/track.yaml
  - Pre-commit hook script
```

**Code Location:**
```python
# yaml_loader.py line 815-821
deliverables = [
    Deliverable(
        type=DeliverableType(d['type']),  # KeyError if d is a string
        paths=d['paths'],
    )
    for d in task_data.get('deliverables', [])
]
```

**Fix Needed:**
Backward-compatible deliverables parsing:
```python
deliverables = []
for d in task_data.get('deliverables', []):
    if isinstance(d, str):
        # Legacy format: plain string
        deliverables.append(Deliverable(
            type=DeliverableType.OTHER,
            paths=[d]
        ))
    elif isinstance(d, dict):
        # New format: dict with type and paths
        deliverables.append(Deliverable(
            type=DeliverableType(d['type']),
            paths=d['paths']
        ))
```

---

## Bug 2: Invalid DeliverableType Value

**Location:** `/workspaces/vibey/vibey/roadmap/serialization/yaml_loader.py:817`

**Error:**
```
'configuration' is not a valid DeliverableType
```

**Root Cause:**
Task YAML used `type: configuration`, but valid enum values are:
- `code`
- `test`
- `documentation`
- `config` (not "configuration")
- `other`

**Fix Needed:**
Either:
1. Add alias mapping in loader: `{"configuration": "config"}`
2. Add validation/migration script to normalize values
3. Document valid values and validate at creation time

---

## Bug 3: Standards Enforcement Field Mismatch

**Location:** `/workspaces/vibey/vibey/operations/roadmap/update.py:79-88`

**Error:**
```
❌ Standards resolution failed: 'title'
```

**Root Cause:**
The `enforce_standards()` function tries to access `task.title`, but Task objects have `task.name`, not `task.title`.

**Code Location:**
```python
# update.py line 79
enforcement_result = enforce_standards(task_id, root_dir, operation="complete")
```

The standards enforcement system is trying to access a field that doesn't exist in the Task data model.

**Fix Needed:**
1. Check `/workspaces/vibey/vibey/operations/roadmap/standards_enforcement.py`
2. Update field references: `task.title` → `task.name`
3. Or add backward-compatible property to Task model

---

## Bug 4: Task Object Structure Mismatch

**Affected:** Complete task workflow

**Issue:**
The Task dataclass in `/workspaces/vibey/vibey/roadmap/models/task.py` defines certain fields, but:
- YAML files use `name` field
- Code expects `title` field
- Inconsistent field naming across models

**Fix Needed:**
Audit all Task model usage and ensure consistent field names:
```bash
# Find all Task field accesses
grep -rn "task\.title\|task\.name" vibey/
```

---

## Impact

**Current State:**
- Sprint 7 marked complete via **manual YAML edits** (commit 617b8fd)
- Not deterministic or reproducible
- Violates principle of automated state management

**Workaround Used:**
```python
# Manual YAML updates - NOT RECOMMENDED
task['status'] = 'completed'
task['completed'] = datetime.now(timezone.utc).isoformat()
```

**Proper Solution Required:**
Fix bugs 1-4, then use:
```bash
python -m vibey.cli.main roadmap complete <task-id>
```

---

## Recommended Fixes Priority

1. **P0 - Bug 3** (standards field mismatch)
   - Blocks all task completion operations
   - Quick fix: update field name reference

2. **P0 - Bug 1** (deliverables schema)
   - Blocks loading tasks with legacy format
   - Medium fix: add backward compatibility

3. **P1 - Bug 2** (invalid enum value)
   - Data validation issue
   - Quick fix: normalize values or add aliases

4. **P1 - Bug 4** (model consistency)
   - Architecture issue
   - Longer fix: audit and standardize field names

---

## Testing After Fix

Create test case that:
1. Starts with fresh task YAML in various formats
2. Calls `vibey roadmap complete <task-id>`
3. Verifies deterministic YAML updates:
   - Status changed to 'completed'
   - Completion timestamp added
   - Metadata updated
   - Sprint progress recalculated
4. No manual YAML edits required

---

## Notes

- Sprint 7 is complete (100%, 13/13 tasks)
- But completion was done non-deterministically
- Future sprints MUST use proper tooling
- These bugs block adoption of roadmap system for automated workflows
