# Roadmap Data Model Fix - Embedded Tasks Migration

**Date:** 2025-11-09
**Issue:** Status updates failing for documentation-system track and other tracks
**Root Cause:** Data model mismatch between embedded and separate task formats
**Status:** ✅ Fixed

---

## Problem Summary

Multiple tracks (including `documentation-system`) showed `not_started` status even though tasks were being completed. This was a recurring issue affecting task completion tracking and progress updates.

### Symptoms

1. Tasks marked as completed, but sprint/track status remained `not_started`
2. `roadmap-update.py --complete-task` command failed with:
   ```
   ❌ Tasks file not found for sprint '{sprint-id}'
   ```
3. Progress metrics not updating despite actual work being done
4. Silent failures - no clear error messages about the root cause

---

## Root Cause

The Vibey roadmap system evolved to support **two different data structures**, which are incompatible:

### Format 1: Separate Task Files (Expected by tooling)
```
.vibey/
├── tracks/core-framework.yaml
├── sprints/core-framework-3.yaml
└── tasks/core-framework-3-tasks.yaml  ← Tasks in separate file
```

### Format 2: Embedded Tasks (Legacy/manual creation)
```
.vibey/
├── tracks/documentation-system.yaml
└── sprints/documentation-system-1.yaml  ← Tasks embedded in sprint YAML
```

### Why It Failed

The `roadmap-update.py` script (line 166-170) **only works with Format 1**:

```python
tasks_path = fs.get_tasks_path(sprint_id)  # Looks for .vibey/tasks/{sprint-id}-tasks.yaml

if not tasks_path.exists():
    print(f"❌ Tasks file not found for sprint '{sprint_id}'")
    return False  # FAILS HERE for embedded tasks
```

When tasks are embedded in the sprint YAML:
- The separate tasks file doesn't exist
- `complete_task()` returns False immediately
- No status update occurs
- **Silent failure** - user never knows why

### Additional Format Issues

Beyond embedded tasks, we also found:

1. **Incorrect data types**: `estimated_tokens` as strings instead of integers
2. **Wrong dependency format**: Task IDs as strings instead of dependency objects
3. **Missing metadata fields**: `last_updated` not present in sprint/track metadata
4. **Inconsistent schemas**: Different tracks using different field names (`name` vs `title`)

---

## Solution

### 1. Migration Script

Created `framework/scripts/migrate-embedded-tasks.py` to automatically:

- Detect sprints with embedded tasks
- Convert tasks to standard separate-file format
- Add all required metadata fields
- Fix data type mismatches
- Convert dependency formats
- Create backups before modifying files

**Usage:**
```bash
# Dry run (preview changes)
python3 framework/scripts/migrate-embedded-tasks.py

# Execute migration
python3 framework/scripts/migrate-embedded-tasks.py --execute
```

**Features:**
- ✅ Safe: Always backs up original files before modification
- ✅ Smart: Auto-converts data types and formats
- ✅ Thorough: Validates all required fields
- ✅ Clear: Shows exactly what will change

### 2. Validation Script

Created `framework/scripts/validate-roadmap-format.py` to prevent recurrence:

- Checks all sprints for embedded tasks
- Validates required fields exist
- Verifies correct data types
- Checks dependency format
- Can be used in CI/pre-commit hooks

**Usage:**
```bash
# Validate roadmap format
python3 framework/scripts/validate-roadmap-format.py

# Exit code 0 if valid, 1 if issues found
```

**What it validates:**
- ✅ No embedded tasks in sprint files
- ✅ Task files exist for each sprint
- ✅ Required fields present (id, sprint_id, track_id, etc.)
- ✅ Correct data types (estimated_tokens is int, not string)
- ✅ Proper dependency format (objects, not strings)
- ✅ Metadata completeness

---

## Migration Results (2025-11-09)

### Sprints Migrated

**Before migration:**
- Total sprints: 8
- With embedded tasks: 4
  - `documentation-system-1` (8 tasks)
  - `documentation-system-2` (6 tasks)
  - `documentation-system-3` (5 tasks)
  - `core-framework-2` (13 tasks)

**After migration:**
- Total sprints: 8
- With embedded tasks: 0 ✅
- All using separate task files ✅

### Tasks Migrated

- **Total tasks migrated:** 32 tasks
- **Format conversions:**
  - Added `sprint_id`, `track_id`, `roadmap_id` fields
  - Converted `estimated_effort` strings → `estimated_tokens` integers
  - Converted task ID strings → dependency objects
  - Added missing metadata fields

### Validation Results

**After migration + manual fixes:**
```
Sprints checked: 8
Tasks checked: 55
Tracks checked: 11

Errors: 0 ✅
Warnings: 0 ✅
```

### Track Dependency Fixes

Fixed 5 tracks with string dependencies → dependency objects:
- `aider-port.yaml`
- `continue-port.yaml`
- `windsurf-port.yaml`
- `jetbrains-port.yaml`
- `mcp-server.yaml`

---

## Impact

### Before Fix
- ❌ Task completions failed silently for 4 sprints
- ❌ Status updates didn't work
- ❌ Progress metrics stale
- ❌ No clear error messages
- ❌ Manual investigation required to diagnose

### After Fix
- ✅ All task completions work
- ✅ Status updates propagate correctly
- ✅ Progress metrics accurate
- ✅ Clear validation errors if issues occur
- ✅ Automated detection and migration

---

## Files Modified

### New Scripts Created
1. `framework/scripts/migrate-embedded-tasks.py` (480 lines)
   - Automated migration tool
   - Safe backup mechanism
   - Comprehensive conversion logic

2. `framework/scripts/validate-roadmap-format.py` (350 lines)
   - Format validation
   - Pre-commit hook ready
   - Clear error reporting

### Data Files Fixed
- `.vibey/sprints/documentation-system-1.yaml` - Removed embedded tasks
- `.vibey/sprints/documentation-system-2.yaml` - Removed embedded tasks
- `.vibey/sprints/documentation-system-3.yaml` - Removed embedded tasks
- `.vibey/sprints/core-framework-2.yaml` - Removed embedded tasks

### Task Files Created
- `.vibey/tasks/documentation-system-1-tasks.yaml` (8 tasks)
- `.vibey/tasks/documentation-system-2-tasks.yaml` (6 tasks)
- `.vibey/tasks/documentation-system-3-tasks.yaml` (5 tasks)
- `.vibey/tasks/core-framework-2-tasks.yaml` (13 tasks)

### Track Files Fixed
- `.vibey/tracks/aider-port.yaml` - Fixed dependencies
- `.vibey/tracks/continue-port.yaml` - Fixed dependencies
- `.vibey/tracks/windsurf-port.yaml` - Fixed dependencies
- `.vibey/tracks/jetbrains-port.yaml` - Fixed dependencies
- `.vibey/tracks/mcp-server.yaml` - Fixed dependencies
- `.vibey/tracks/documentation-system.yaml` - Fixed dependencies

### Backups Created
- `.vibey/migration-backups/backup_20251109_163859/` - All original sprint files

---

## Best Practices Going Forward

### For Creating New Sprints

1. **Always use separate task files**
   ```yaml
   # ✅ CORRECT: .vibey/tasks/my-sprint-1-tasks.yaml
   tasks:
   - id: my-sprint-1-task-001
     sprint_id: my-sprint-1
     track_id: my-track
     ...
   ```

2. **Never embed tasks in sprint YAML**
   ```yaml
   # ❌ WRONG: .vibey/sprints/my-sprint-1.yaml
   sprint:
     id: my-sprint-1
     tasks:  # Don't do this!
     - id: task-001
       ...
   ```

3. **Run validation before committing**
   ```bash
   python3 framework/scripts/validate-roadmap-format.py
   ```

### Required Task Fields

Every task must have:
```yaml
- id: string (task-{sprint-id}-{number})
  sprint_id: string
  track_id: string
  roadmap_id: string
  task_type: string (development|completion_gate|production_gate)
  title: string
  description: string
  status: string (not_started|in_progress|completed)
  blocked: boolean
  created: datetime (ISO 8601)
  started: datetime|null
  completed: datetime|null
  assigned_agent: string
  priority: string (low|medium|high|critical)
  phase_label: string|null
  estimated_tokens: integer  # NOT STRING!
  actual_tokens: integer|null
  complexity: string
  gate_info: object|null
  audit_results: object|null
  dependencies: array[object]  # NOT array[string]!
  blocks: array[string]
  blocked_by: array[string]
  deliverables: array[string]
  commits: array[string]
  metadata:
    last_updated: datetime
    token_efficiency: float|null
    duration_hours: float|null
```

### Dependency Format

**Correct dependency format:**
```yaml
dependencies:
- type: task|sprint|track
  target_id: other-task-id
  target_status: completed
  reason: Why this is needed
```

**Wrong (will fail validation):**
```yaml
dependencies:
- other-task-id  # String, not object!
```

---

## Testing Recommendations

### Pre-Commit Validation
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python3 framework/scripts/validate-roadmap-format.py
if [ $? -ne 0 ]; then
    echo "❌ Roadmap validation failed - fix errors before committing"
    exit 1
fi
```

### CI Pipeline
Add to GitHub Actions / CI:
```yaml
- name: Validate roadmap format
  run: python3 framework/scripts/validate-roadmap-format.py
```

### Manual Testing
```bash
# After creating new sprint/tasks
python3 framework/scripts/validate-roadmap-format.py

# Test task completion
python3 framework/scripts/roadmap-update.py --complete-task my-sprint-1-task-001

# Verify progress updated
grep "completion_percent" .vibey/sprints/my-sprint-1.yaml
```

---

## Lessons Learned

1. **Standardize data models early** - Having two formats causes silent failures
2. **Validate inputs** - Don't assume manual YAML edits follow schema
3. **Fail loudly** - Silent failures are worse than clear errors
4. **Provide migration tools** - Don't just document the "right way", provide automation
5. **Document the why** - Explain why one format over another

---

## Future Improvements

### Short Term
- [x] Create migration script ✅
- [x] Create validation script ✅
- [ ] Add validation to `roadmap-init.py` and `roadmap-prepare.py`
- [ ] Update user documentation with format requirements
- [ ] Add pre-commit hook example to repository

### Medium Term
- [ ] Generate task files automatically when creating sprints
- [ ] Prevent manual sprint file editing (use CLI only)
- [ ] Add JSON schema validation
- [ ] Create task file templates

### Long Term
- [ ] Unified data model with single source of truth
- [ ] Database backend instead of YAML files
- [ ] Real-time validation API
- [ ] Web UI for roadmap management

---

## References

- **Migration Script:** `framework/scripts/migrate-embedded-tasks.py`
- **Validation Script:** `framework/scripts/validate-roadmap-format.py`
- **Update Script:** `framework/scripts/roadmap-update.py`
- **Data Models:** `framework/roadmap/models/`
- **Serialization:** `framework/roadmap/serialization/`

---

## Appendix: Technical Details

### Conversion Logic

```python
# String dependencies → Object dependencies
"task-id-string"
↓
{
  "type": "task",
  "target_id": "task-id-string",
  "target_status": "completed",
  "reason": "Required prerequisite"
}

# Estimated effort → Estimated tokens
"3 days"
↓
3000  # 3 days * 1000 tokens/day

# Task fields
task['name'] → task['title']
task['assigned_agent'] || 'web-developer' → task['assigned_agent']
```

### File Structure After Migration

```
.vibey/
├── roadmap.yaml                      # Master roadmap
├── tracks/
│   ├── documentation-system.yaml     # Track definition (no tasks)
│   └── core-framework.yaml
├── sprints/
│   ├── documentation-system-1.yaml   # Sprint definition (no tasks)
│   ├── documentation-system-2.yaml
│   └── core-framework-2.yaml
├── tasks/
│   ├── documentation-system-1-tasks.yaml  # Tasks for sprint 1
│   ├── documentation-system-2-tasks.yaml  # Tasks for sprint 2
│   └── core-framework-2-tasks.yaml
└── migration-backups/
    └── backup_20251109_163859/       # Original files
        ├── documentation-system-1.yaml
        └── core-framework-2.yaml
```

---

**Last Updated:** 2025-11-09
**Author:** Claude Code
**Status:** Complete
