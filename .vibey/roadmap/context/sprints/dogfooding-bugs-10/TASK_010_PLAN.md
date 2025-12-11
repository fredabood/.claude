# Task 010: Migrate Git Integration Files

**Task ID:** `01KC6WAAM87S5VVJ1JBN29PBX0`
**Bug Addressed:** #19
**Complexity:** High
**Priority:** Medium
**Type:** Development

## Problem Statement

8 git integration files expect hierarchical directory structure for track/sprint access.

## Current State (from HIERARCHICAL_AUDIT.md)

| File | Lines | Pattern |
|------|-------|---------|
| `git_sync.py` | 264, 300, 505, 515 | `sprint_dir / "sprint.yaml"` |
| `ci_integration.py` | 239, 507 | `track_id / "track.yaml"` |
| `commit_evidence.py` | 120, 174 | `track_dir / sprint_id` |
| `blocker_enforcer.py` | 277, 283 | `sprint_dir / "sprint.yaml"` |
| `error_handler.py` | 235, 250, 267, 372 | Multiple patterns |
| `merge_ordering.py` | 179, 216 | `track_dir / "track.yaml"` |
| `sprint_tagger.py` | 144 | `sprint_dir / "sprint.yaml"` |
| `state_reconstructor.py` | 207 | Reference to `track.yaml` |

## Implementation Plan

### File 1: git_sync.py (4 locations)

```python
# Lines 264, 300, 505, 515
# BEFORE:
sprint_file = sprint_dir / "sprint.yaml"

# AFTER:
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### File 2: ci_integration.py (2 locations)

```python
# Lines 239, 507
# BEFORE:
track_path = self.roadmap_root / track_id / "track.yaml"

# AFTER:
track_path = self.roadmap_root / "tracks" / f"{track_id}.yaml"
```

### File 3: commit_evidence.py (2 locations)

```python
# Lines 120, 174
# BEFORE:
sprint_dir = track_dir / sprint_id

# AFTER:
# Use flat paths directly, no sprint_dir needed
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### File 4: blocker_enforcer.py (2 locations)

```python
# Lines 277, 283
# BEFORE:
sprint_file = sprint_dir / "sprint.yaml"
track_file = track_dir / "track.yaml"

# AFTER:
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
track_file = roadmap_dir / "tracks" / f"{track_id}.yaml"
```

### File 5: error_handler.py (4 locations)

```python
# Lines 235, 250, 267, 372
# BEFORE:
track_file = track_dir / "track.yaml"
sprint_file = sprint_dir / "sprint.yaml"

# AFTER:
track_file = roadmap_dir / "tracks" / f"{track_id}.yaml"
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### File 6: merge_ordering.py (2 locations)

```python
# Lines 179, 216
# BEFORE:
track_file = track_dir / "track.yaml"
sprint_file = sprint_dir / "sprint.yaml"

# AFTER:
track_file = roadmap_dir / "tracks" / f"{track_id}.yaml"
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### File 7: sprint_tagger.py (1 location)

```python
# Line 144
# BEFORE:
sprint_file = sprint_dir / "sprint.yaml"

# AFTER:
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### File 8: state_reconstructor.py (1 location)

```python
# Line 207
# Review reference to track.yaml and update if necessary
```

## Files to Modify

| File | Locations |
|------|-----------|
| `vibey/operations/git/git_sync.py` | 4 |
| `vibey/operations/git/ci_integration.py` | 2 |
| `vibey/operations/git/commit_evidence.py` | 2 |
| `vibey/operations/git/blocker_enforcer.py` | 2 |
| `vibey/operations/git/error_handler.py` | 4 |
| `vibey/operations/git/merge_ordering.py` | 2 |
| `vibey/operations/git/sprint_tagger.py` | 1 |
| `vibey/operations/git/state_reconstructor.py` | 1 |

## Testing

1. Run git hook tests
2. Test `git commit` with pre-commit hook
3. Test blocker enforcement
4. Test CI integration if possible

## Success Criteria

- [ ] All 8 files updated
- [ ] All `sprint_dir / "sprint.yaml"` patterns migrated
- [ ] All `track_dir / "track.yaml"` patterns migrated
- [ ] Git hooks work correctly
- [ ] All git-related tests pass

## Dependencies

- Task 002 (YAMLBackend): Defines flat structure patterns
