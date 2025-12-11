# Task 004: Migrate integrity_audit.py to Flat Structure

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXS`
**Bug Addressed:** #19
**Complexity:** High
**Priority:** High
**Type:** Development

## Problem Statement

`vibey/roadmap/database/integrity_audit.py` expects hierarchical directory structure when auditing YAML files. It has 6+ patterns that need migration.

## Current State (from HIERARCHICAL_AUDIT.md)

| Line | Function | Pattern | Issue |
|------|----------|---------|-------|
| 211 | `audit_*` | `track_yaml = track_dir / "track.yaml"` | Expects nested |
| 232 | `audit_*` | `sprint_yaml = sprint_dir / "sprint.yaml"` | Expects nested |
| 363 | `audit_*` | `track_yaml = track_dir / "track.yaml"` | Expects nested |
| 392 | `audit_*` | `sprint_yaml = sprint_dir / "sprint.yaml"` | Expects nested |
| 714-757 | `_load_track_from_yaml()` | Multiple hierarchical patterns | Full rewrite needed |
| 857 | `audit_*` | `track_yaml = track_dir / "track.yaml"` | Expects nested |

## Implementation Plan

### Step 1: Identify all audit functions

Review all functions in integrity_audit.py that access YAML files:
- `audit_track_integrity()`
- `audit_sprint_integrity()`
- `audit_task_integrity()`
- `_load_track_from_yaml()`
- `find_orphaned_files()`
- `count_tasks_in_yaml()`

### Step 2: Update track loading pattern

```python
# BEFORE (line 211, 363, 857):
track_yaml = track_dir / "track.yaml"

# AFTER:
track_yaml = roadmap_dir / "tracks" / f"{track_id}.yaml"
```

### Step 3: Update sprint loading pattern

```python
# BEFORE (line 232, 392):
sprint_yaml = sprint_dir / "sprint.yaml"

# AFTER:
sprint_yaml = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### Step 4: Rewrite _load_track_from_yaml() (lines 714-757)

This function likely iterates directories. Update to:
1. List files from `tracks/*.yaml`
2. Load each track directly
3. For sprints, load from `sprints/*.yaml` filtering by track_id
4. For tasks, load from `tasks/*.yaml` filtering by sprint_id

### Step 5: Update orphan detection

Orphan detection should look for:
- Files in `tracks/` not in database
- Files in `sprints/` not in database
- Files in `tasks/` not in database
- NOT: ULID directories that don't match entities

### Step 6: Update task counting

Task counting should iterate `tasks/*.yaml` and filter by sprint_id, not by nested directory structure.

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/database/integrity_audit.py` | Update 6+ functions |

## Testing

1. Run integrity audit: `vibey roadmap db validate`
2. Verify correct file paths are checked
3. Verify orphan detection works with flat structure
4. Verify task counting matches database

## Success Criteria

- [ ] All `track_dir / "track.yaml"` patterns migrated
- [ ] All `sprint_dir / "sprint.yaml"` patterns migrated
- [ ] `_load_track_from_yaml()` rewritten for flat structure
- [ ] Orphan detection works with flat structure
- [ ] Task counting uses flat task filtering
- [ ] All audit functions pass

## Dependencies

- Task 002 (YAMLBackend): Defines flat structure patterns
