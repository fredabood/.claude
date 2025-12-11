# Task 012: Migrate CLI Roadmap Lib Files

**Task ID:** `01KC6WAAM87S5VVJ1JBN29PBX2`
**Bug Addressed:** #19
**Complexity:** Medium
**Priority:** Medium
**Type:** Development

## Problem Statement

3 CLI roadmap library files contain hierarchical path construction patterns.

## Current State (from HIERARCHICAL_AUDIT.md)

| File | Lines | Notes |
|------|-------|-------|
| `filesystem.py` (cli/roadmap_lib) | 259, 279 | Hierarchical path construction |
| `compatibility.py` | 232, 234 | Hierarchical fallback detection |
| `yaml_dumper.py` | 55 | `task_dir.mkdir()` |

## Implementation Plan

### File 1: filesystem.py (2 locations)

Location: `vibey/cli/roadmap_lib/filesystem.py`

```python
# Line 259: Track path construction
# BEFORE:
return self.roadmap_root / track_slug / "track.yaml"

# AFTER:
# For ULID-based access:
return self.roadmap_root / "tracks" / f"{track_id}.yaml"
# For slug-based access (context directories):
# May need separate method or parameter

# Line 279: Sprint path construction
# BEFORE:
return self.roadmap_root / track_slug / sprint_slug / "sprint.yaml"

# AFTER:
return self.roadmap_root / "sprints" / f"{sprint_id}.yaml"
```

Note: FileSystemManager may need method signature changes if it accepts slugs vs ULIDs.

### File 2: compatibility.py (2 locations)

Location: `vibey/roadmap/compatibility.py`

```python
# Lines 232, 234: Hierarchical fallback detection
# BEFORE:
potential_sprint_dir = track_dir / sprint_id
sprint_file = potential_sprint_dir / "sprint.yaml"

# This is fallback detection - may need to:
# 1. Remove hierarchical fallback entirely (recommended)
# 2. Or update to check flat structure first, then fallback

# AFTER (Option 1 - Remove fallback):
# Remove hierarchical fallback detection since we're migrating away from it

# AFTER (Option 2 - Update fallback):
# First check flat structure
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
if not sprint_file.exists():
    # Legacy fallback (deprecation warning)
    potential_sprint_dir = track_dir / sprint_id
    sprint_file = potential_sprint_dir / "sprint.yaml"
```

### File 3: yaml_dumper.py (1 location)

Location: `vibey/roadmap/serialization/yaml_dumper.py`

```python
# Line 55: Task directory creation
# BEFORE:
task_dir.mkdir(parents=True, exist_ok=True)

# AFTER:
# Remove nested task_dir creation
# Tasks should be saved directly to tasks/{id}.yaml
tasks_dir = roadmap_dir / "tasks"
tasks_dir.mkdir(parents=True, exist_ok=True)
# Then save: save_task(task, tasks_dir / f"{task.id}.yaml")
```

## Files to Modify

| File | Locations |
|------|-----------|
| `vibey/cli/roadmap_lib/filesystem.py` | 2 |
| `vibey/roadmap/compatibility.py` | 2 |
| `vibey/roadmap/serialization/yaml_dumper.py` | 1 |

## Testing

1. Test FileSystemManager path resolution
2. Test compatibility layer (if kept)
3. Test YAML dumper task saving

## Success Criteria

- [ ] `filesystem.py` uses flat paths
- [ ] Hierarchical fallback removed or updated
- [ ] No `task_dir.mkdir()` for nested directories
- [ ] All path resolution uses flat structure

## Dependencies

- Task 002 (YAMLBackend): Defines flat structure patterns
