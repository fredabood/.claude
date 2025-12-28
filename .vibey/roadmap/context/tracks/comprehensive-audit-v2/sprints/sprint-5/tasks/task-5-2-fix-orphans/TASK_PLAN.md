# Task 5.2: Fix Orphan Tasks and Broken References - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ3443F |
| Sprint | Sprint 5: Remediation & Reporting |
| Type | development |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 2,500 |
| Dependencies | Sprint 2 Task 2.5 (ORPHAN_AUDIT.md) |

## Objective

Fix all orphaned entities and broken dependency references found during Sprint 2's data integrity validation. This ensures all roadmap entities have valid parent references and all task dependencies resolve correctly.

## Input Requirements

From Sprint 2 Task 2.5 (Orphan Audit), we need:
1. `ORPHAN_AUDIT.md` - Full audit results
2. `ORPHAN_CLEANUP.yaml` - Machine-readable cleanup instructions
3. List of orphan tasks (invalid sprint_id)
4. List of orphan sprints (invalid track_id)
5. List of broken blocked_by/depends_on references
6. List of invalid .id file mappings

## Background

### Problem Statement
The dual storage system (YAML + SQLite) can develop referential integrity issues:
- Tasks may reference non-existent sprints (orphan tasks)
- Sprints may reference non-existent tracks (orphan sprints)
- Task dependencies may point to deleted or renamed tasks
- .id files in the old nested structure may be stale

### Why This Matters
- **Query Accuracy:** Orphaned entities may not appear in reports
- **Dependency Tracking:** Broken references cause incorrect blocking logic
- **Data Integrity:** Inconsistent references indicate system health issues
- **Navigation:** Invalid mappings break lookups

## Implementation Steps

### Step 1: Load Cleanup Instructions

```bash
# Navigate to Sprint 2 outputs
cd .vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-2/outputs/

# Review the cleanup file
cat ORPHAN_CLEANUP.yaml
```

Expected structure:
```yaml
orphan_tasks:
  - id: 01KC...
    title: "..."
    invalid_sprint_id: 01KC...
    action: delete | reassign
    reassign_to: 01KC...  # if reassign

orphan_sprints:
  - id: 01KC...
    name: "..."
    invalid_track_id: 01KC...
    action: delete | reassign

broken_dependencies:
  - task_id: 01KC...
    field: blocked_by | depends_on
    invalid_value: 01KC...
    action: clear | update
    update_to: 01KC...  # if update
```

### Step 2: Backup Current State

```bash
# Create backup before any changes
cp .vibey/roadmap.db .vibey/roadmap.db.pre-orphan-fix

# Git commit current state
git add .vibey/roadmap/
git commit -m "chore: snapshot before orphan/reference remediation"
```

### Step 3: Fix Orphan Tasks

For each orphan task, either reassign or delete:

#### Option A: Reassign to Valid Sprint
```bash
# Using CLI if available
vibey roadmap update task <task-id> --sprint-id <valid-sprint-id>

# Or direct YAML edit
# Edit .vibey/roadmap/tasks/<task-id>.yaml
# Change sprint_id to valid sprint
```

#### Option B: Delete Orphan Task
```bash
# Using CLI
vibey roadmap delete task <task-id>

# Or remove YAML file
rm .vibey/roadmap/tasks/<task-id>.yaml
```

### Step 4: Fix Orphan Sprints

For each orphan sprint:

#### Option A: Reassign to Valid Track
```bash
# Edit .vibey/roadmap/sprints/<sprint-id>.yaml
# Change track_id to valid track
```

#### Option B: Delete Orphan Sprint
```bash
# Remove YAML file (after deleting child tasks)
rm .vibey/roadmap/sprints/<sprint-id>.yaml
```

### Step 5: Fix Broken Dependency References

For each broken blocked_by/depends_on reference:

```yaml
# Before
task:
  id: 01KC...ABC
  blocked_by:
    - 01KC...VALID
    - 01KC...INVALID  # This reference is broken

# After
task:
  id: 01KC...ABC
  blocked_by:
    - 01KC...VALID
    # Removed: 01KC...INVALID (non-existent)
```

Batch fix script:
```python
#!/usr/bin/env python3
"""Fix broken dependency references."""

import yaml
from pathlib import Path

def fix_broken_dependencies(cleanup_file: str):
    """Remove or update broken dependency references."""

    with open(cleanup_file) as f:
        cleanup = yaml.safe_load(f)

    tasks_dir = Path('.vibey/roadmap/tasks/')
    results = []

    for broken in cleanup.get('broken_dependencies', []):
        task_id = broken['task_id']
        field = broken['field']  # blocked_by or depends_on
        invalid_value = broken['invalid_value']
        action = broken['action']

        task_file = tasks_dir / f"{task_id}.yaml"
        if not task_file.exists():
            print(f"Warning: Task file not found: {task_id}")
            continue

        with open(task_file) as f:
            task_data = yaml.safe_load(f)

        # Get the field value
        field_value = task_data.get('task', {}).get(field, [])
        if not isinstance(field_value, list):
            field_value = [field_value] if field_value else []

        # Remove the invalid reference
        if invalid_value in field_value:
            field_value.remove(invalid_value)
            print(f"Removed {invalid_value} from {task_id}.{field}")

        # Update to new value if specified
        if action == 'update' and 'update_to' in broken:
            field_value.append(broken['update_to'])
            print(f"Added {broken['update_to']} to {task_id}.{field}")

        # Save updated task
        task_data['task'][field] = field_value if field_value else None

        with open(task_file, 'w') as f:
            yaml.dump(task_data, f, default_flow_style=False)

        results.append({
            'task_id': task_id,
            'field': field,
            'action': action,
            'status': 'fixed'
        })

    return results
```

### Step 6: Update .id Mapping Files (if needed)

Check for stale .id files:

```bash
# Find all .id files
find .vibey/roadmap -name ".id" -type f

# For each .id file, verify the referenced YAML exists
for id_file in $(find .vibey/roadmap -name ".id" -type f); do
  id_content=$(cat "$id_file")
  dir=$(dirname "$id_file")

  # Check if corresponding YAML exists in flat structure
  if [ ! -f ".vibey/roadmap/tasks/${id_content}.yaml" ] && \
     [ ! -f ".vibey/roadmap/sprints/${id_content}.yaml" ] && \
     [ ! -f ".vibey/roadmap/tracks/${id_content}.yaml" ]; then
    echo "STALE: $id_file -> $id_content"
    # Remove stale .id file
    rm "$id_file"
  fi
done
```

### Step 7: Rebuild Database

```bash
# Rebuild database to ensure consistency
vibey roadmap db rebuild --force

# Verify rebuild success
vibey roadmap db status

# Validate referential integrity
vibey roadmap db validate
```

### Step 8: Verify All ULID References Resolve

```sql
-- Re-run orphan check queries to verify fixes
SELECT 'orphan_task' AS type, t.id, t.title
FROM tasks t
LEFT JOIN sprints s ON t.sprint_id = s.id
WHERE s.id IS NULL;

SELECT 'orphan_sprint' AS type, s.id, s.name
FROM sprints s
LEFT JOIN tracks tr ON s.track_id = tr.id
WHERE tr.id IS NULL;

-- Verify no broken dependencies remain
SELECT t.id, t.title, t.blocked_by
FROM tasks t
WHERE t.blocked_by IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM tasks t2 WHERE t2.id = t.blocked_by);
```

All queries should return 0 rows.

### Step 9: Document All Changes

Create remediation log:

```markdown
# Orphan Remediation Log

## Execution Summary
- **Date:** Dec 28, 2024
- **Orphan Tasks Fixed:** X
- **Orphan Sprints Fixed:** Y
- **Broken Dependencies Fixed:** Z
- **Stale .id Files Removed:** W

## Individual Corrections

### Orphan Tasks (X total)

| Task ID | Title | Action | Details |
|---------|-------|--------|---------|
| 01KC... | ... | reassigned | To sprint 01KC... |
| 01KC... | ... | deleted | Obsolete task |

### Orphan Sprints (Y total)

| Sprint ID | Name | Action | Details |
|-----------|------|--------|---------|
| 01KC... | ... | reassigned | To track 01KC... |

### Broken Dependencies (Z total)

| Task ID | Field | Invalid Ref | Action |
|---------|-------|-------------|--------|
| 01KC... | blocked_by | 01KC... | removed |

### Stale .id Files (W total)

| Path | Referenced ID | Action |
|------|---------------|--------|
| .vibey/.../tasks/.id | 01KC... | deleted |

## Verification

All orphan queries now return 0 rows.
```

## Validation Checklist

- [ ] ORPHAN_CLEANUP.yaml loaded from Sprint 2 outputs
- [ ] Pre-remediation backup created
- [ ] All orphan tasks reassigned or deleted
- [ ] All orphan sprints reassigned or deleted
- [ ] All broken blocked_by references fixed
- [ ] All broken depends_on references fixed
- [ ] Stale .id files removed
- [ ] Database rebuilt successfully
- [ ] Orphan verification queries return 0 rows
- [ ] ORPHAN_REMEDIATION_LOG.md created

## Deliverables

1. **ORPHAN_REMEDIATION_LOG.md**
   - Complete record of all changes
   - Before/after entity counts
   - Verification results

2. **Clean Dependency Graph**
   - All references now valid
   - No orphaned entities

3. **Database Backup**
   - .vibey/roadmap.db.pre-orphan-fix (if rollback needed)

## Output Location

```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/
```

## Acceptance Criteria

- [ ] Zero orphan tasks (all sprint_id references valid)
- [ ] Zero orphan sprints (all track_id references valid)
- [ ] Zero broken blocked_by references
- [ ] Zero broken depends_on references
- [ ] All .id files point to existing YAML
- [ ] Database validates successfully
- [ ] Remediation log is complete and accurate

## Estimated Time

- Load cleanup file: 5 minutes
- Backup creation: 5 minutes
- Fix orphan tasks: 20 minutes (depends on count)
- Fix orphan sprints: 10 minutes
- Fix broken dependencies: 20 minutes
- Update .id files: 10 minutes
- Database rebuild: 5 minutes
- Verification: 15 minutes
- Documentation: 20 minutes
- **Total: ~2 hours**

## Rollback Plan

If issues discovered:

```bash
# Restore database
cp .vibey/roadmap.db.pre-orphan-fix .vibey/roadmap.db

# Or git revert
git revert HEAD  # If changes committed
```

## Notes

- Review Sprint 2 Task 2.5 findings before starting
- Some orphans may be intentional (archived entities) - document decisions
- The .id files are from the old nested directory structure - may be deprecated
- Consider implementing foreign key constraints to prevent future orphans
