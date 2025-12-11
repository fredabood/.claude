# Task 011: Migrate Roadmap Operations Files

**Task ID:** `01KC6WAAM87S5VVJ1JBN29PBX1`
**Bug Addressed:** #19
**Complexity:** High
**Priority:** Medium
**Type:** Development

## Problem Statement

5 roadmap operations files contain hierarchical path patterns that need migration.

## Current State (from HIERARCHICAL_AUDIT.md)

| File | Lines | Notes |
|------|-------|-------|
| `migration.py` (operations/roadmap) | 103, 110, 230, 255, 322, 325, 376, 386, 580 | 9 patterns |
| `yaml_remediation.py` | 145, 155, 241 | 3 patterns |
| `toc_generator.py` | 201, 219, 240, 293, 297 | 5 patterns |
| `migrate_to_criteria.py` | 39, 46, 209, 259 | 4 patterns |
| `summarize.py` | 168 | 1 pattern |

## Implementation Plan

### File 1: migration.py (9 locations)

Location: `vibey/operations/roadmap/migration.py`

```python
# Lines 103, 110: Hierarchical structure detection
# May need to update detection logic for flat structure

# Lines 230, 255: Directory creation
# BEFORE:
track_dir = roadmap_dir / track_id
sprint_dir = track_dir / sprint_id

# AFTER:
# Use flat paths
track_file = roadmap_dir / "tracks" / f"{track_id}.yaml"
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"

# Lines 322, 325, 376, 386: File writing
# BEFORE:
_write_yaml(sprint_dir / "sprint.yaml", sprint_data)
_write_yaml(track_dir / "track.yaml", track_summary)

# AFTER:
_write_yaml(roadmap_dir / "sprints" / f"{sprint_id}.yaml", sprint_data)
_write_yaml(roadmap_dir / "tracks" / f"{track_id}.yaml", track_summary)

# Line 580: Track YAML access
# BEFORE:
track_yaml = track_dir / "track.yaml"

# AFTER:
track_yaml = roadmap_dir / "tracks" / f"{track_id}.yaml"
```

### File 2: yaml_remediation.py (3 locations)

Location: `vibey/roadmap/database/yaml_remediation.py`

```python
# Lines 145, 155, 241
# BEFORE:
track_yaml = d / "track.yaml"
sprint_yaml = sprint_dir / "sprint.yaml"

# AFTER:
track_yaml = roadmap_dir / "tracks" / f"{track_id}.yaml"
sprint_yaml = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### File 3: toc_generator.py (5 locations)

Location: `vibey/roadmap/toc_generator.py`

```python
# Lines 201, 219, 240, 293, 297
# BEFORE:
track_yaml_path = track_dir / "track.yaml"
sprint_yaml_path = sprint_dir / "sprint.yaml"

# AFTER:
track_yaml_path = roadmap_dir / "tracks" / f"{track_id}.yaml"
sprint_yaml_path = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

Note: TOC generator may need logic changes since it iterates directories.

### File 4: migrate_to_criteria.py (4 locations)

Location: `vibey/roadmap/operations/migrate_to_criteria.py`

```python
# Lines 39, 46: Directory detection
# May need to update to detect flat structure

# Lines 209, 259: File access
# BEFORE:
sprint_file = sprint_dir / "sprint.yaml"
track_file = track_dir / "track.yaml"

# AFTER:
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
track_file = roadmap_dir / "tracks" / f"{track_id}.yaml"
```

### File 5: summarize.py (1 location)

Location: `vibey/operations/roadmap/summarize.py`

```python
# Line 168
# BEFORE:
sprint_file = sprint_dir / 'sprint.yaml'

# AFTER:
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

## Files to Modify

| File | Locations |
|------|-----------|
| `vibey/operations/roadmap/migration.py` | 9 |
| `vibey/roadmap/database/yaml_remediation.py` | 3 |
| `vibey/roadmap/toc_generator.py` | 5 |
| `vibey/roadmap/operations/migrate_to_criteria.py` | 4 |
| `vibey/operations/roadmap/summarize.py` | 1 |

## Testing

1. Test migration functionality
2. Test YAML remediation
3. Test TOC generation
4. Test criteria migration
5. Test summarization

## Success Criteria

- [ ] All 5 files updated
- [ ] All hierarchical patterns migrated
- [ ] Directory iteration logic updated where needed
- [ ] All related functionality works correctly

## Dependencies

- Task 002 (YAMLBackend): Defines flat structure patterns
