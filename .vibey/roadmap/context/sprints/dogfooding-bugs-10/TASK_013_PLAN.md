# Task 013: Deprecate directory_migration.py HierarchicalPathResolver

**Task ID:** `01KC6WAAM87S5VVJ1JBN29PBX3`
**Bug Addressed:** #19
**Complexity:** Low
**Priority:** Low
**Type:** Development

## Problem Statement

`vibey/roadmap/serialization/directory_migration.py` contains `HierarchicalPathResolver` class that constructs hierarchical paths. This should be deprecated or removed.

## Current State (from HIERARCHICAL_AUDIT.md)

| Line | Function | Pattern |
|------|----------|---------|
| 97 | `HierarchicalPathResolver.track_path()` | `roadmap_dir / track_id / 'track.yaml'` |
| 113 | `HierarchicalPathResolver.sprint_path()` | `track_id / sprint_id / 'sprint.yaml'` |
| 131 | `HierarchicalPathResolver.task_path()` | `track_id / sprint_id / task_id / 'task.yaml'` |
| 148-152 | `HierarchicalPathResolver.context_path()` | Nested context paths |

## Implementation Plan

### Option A: Delete HierarchicalPathResolver (Recommended)

If no code depends on it after migration:

1. Search for usages:
```bash
grep -r "HierarchicalPathResolver" vibey/
```

2. If no usages found, delete the class or file.

### Option B: Create FlatPathResolver Replacement

If path resolution is still needed:

```python
class FlatPathResolver:
    """Resolve paths for flat YAML structure."""

    def __init__(self, roadmap_dir: Path):
        self.roadmap_dir = Path(roadmap_dir)

    def track_path(self, track_id: str) -> Path:
        return self.roadmap_dir / "tracks" / f"{track_id}.yaml"

    def sprint_path(self, sprint_id: str) -> Path:
        return self.roadmap_dir / "sprints" / f"{sprint_id}.yaml"

    def task_path(self, task_id: str) -> Path:
        return self.roadmap_dir / "tasks" / f"{task_id}.yaml"

    def context_path(self, entity_type: str, entity_slug: str) -> Path:
        """Context directories use slugs for human readability."""
        return self.roadmap_dir / "context" / entity_type / entity_slug
```

### Option C: Add Deprecation Warnings

If keeping for backward compatibility:

```python
import warnings

class HierarchicalPathResolver:
    def __init__(self, roadmap_dir: Path):
        warnings.warn(
            "HierarchicalPathResolver is deprecated. Use FlatPathResolver instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # ... existing code
```

## Implementation Steps

1. Search for all usages of `HierarchicalPathResolver`
2. Update or remove usages found
3. Either delete class or add deprecation
4. If replacement needed, create `FlatPathResolver`
5. Update imports in dependent files

## Files to Modify

| File | Action |
|------|--------|
| `vibey/roadmap/serialization/directory_migration.py` | Deprecate/delete HierarchicalPathResolver |
| Any files importing HierarchicalPathResolver | Update imports |

## Testing

1. Search for broken imports after changes
2. Run test suite
3. Verify no code depends on hierarchical path resolution

## Success Criteria

- [ ] `HierarchicalPathResolver` deprecated or deleted
- [ ] No broken imports
- [ ] `FlatPathResolver` created if needed
- [ ] All tests pass

## Dependencies

- Tasks 009-012: Should complete migration of all callers first
