# Task 009: Migrate commands.py Hierarchical Paths

**Task ID:** `01KC6WAAM87S5VVJ1JBN29PBWZ`
**Bug Addressed:** #19
**Complexity:** Medium
**Priority:** Medium
**Type:** Development

## Problem Statement

`vibey/cli/commands.py` contains 5 locations that construct hierarchical paths for track/sprint access.

## Current State (from HIERARCHICAL_AUDIT.md)

| Line | Pattern | Issue |
|------|---------|-------|
| 2677 | `track_dir = roadmap_dir / track_summary.id` | Creates ULID path |
| 2678 | `track_yaml = track_dir / "track.yaml"` | Reads from nested |
| 2708 | `sprint_dir = track_dir / sprint_summary.id` | Creates nested path |
| 2709 | `sprint_yaml = sprint_dir / "sprint.yaml"` | Reads from nested |
| 3023 | `sprint_dir = roadmap_dir / track_id / sprint_id` | Creates nested path |

## Implementation Plan

### Step 1: Update track access pattern (lines 2677-2678)

```python
# BEFORE:
track_dir = roadmap_dir / track_summary.id
track_yaml = track_dir / "track.yaml"

# AFTER:
track_yaml = roadmap_dir / "tracks" / f"{track_summary.id}.yaml"
```

### Step 2: Update sprint access pattern (lines 2708-2709)

```python
# BEFORE:
sprint_dir = track_dir / sprint_summary.id
sprint_yaml = sprint_dir / "sprint.yaml"

# AFTER:
sprint_yaml = roadmap_dir / "sprints" / f"{sprint_summary.id}.yaml"
```

### Step 3: Update sprint directory reference (line 3023)

```python
# BEFORE:
sprint_dir = roadmap_dir / track_id / sprint_id

# AFTER:
sprint_yaml = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
# (only use sprint_yaml, not sprint_dir)
```

### Step 4: Search for similar patterns

Search commands.py for other occurrences:
```bash
grep -n "track_dir\|sprint_dir\|/ track\|/ sprint" vibey/cli/commands.py
```

Update any additional patterns found.

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands.py` | Update 5+ locations |

## Testing

1. Test `vibey roadmap show track <id>` - should read from flat structure
2. Test `vibey roadmap show sprint <id>` - should read from flat structure
3. Test any commands that modify tracks/sprints

## Success Criteria

- [ ] All `track_dir = roadmap_dir / track.id` patterns removed
- [ ] All `sprint_dir = track_dir / sprint.id` patterns removed
- [ ] Uses `tracks/{id}.yaml` for track access
- [ ] Uses `sprints/{id}.yaml` for sprint access
- [ ] All related CLI commands work correctly

## Dependencies

- Task 002 (YAMLBackend): Defines flat structure patterns
