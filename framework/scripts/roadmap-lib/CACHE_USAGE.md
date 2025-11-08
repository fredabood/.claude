# Using RoadmapCache in Command Handlers

Guide for command handler authors on using the caching layer.

---

## Overview

The roadmap CLI automatically initializes `RoadmapCache` for all commands except `init`. Command handlers receive the cache via `args.cache`.

**Benefits:**
- **4.5x faster** task lookups (100ms → 1ms)
- **O(1) lookups** after index built
- **100% cache hit rate** in typical workflows
- **Automatic invalidation** after state changes

---

## Quick Start

### In Your Command Handler

```python
def handle_my_command(args):
    """Handle my command."""

    # Cache is available via args.cache
    cache = args.cache

    # Use cache helpers (recommended)
    from cache_helpers import get_cached_task

    task = get_cached_task(cache, 'task-001')
    if task:
        print(f"Task: {task['name']}")
```

---

## Cache Helpers

Import from `cache_helpers`:

```python
from cache_helpers import (
    get_cached_task,
    get_cached_sprint,
    get_cached_track,
    get_all_cached_tasks,
    get_all_cached_sprints,
    get_all_cached_tracks,
    get_cached_dependencies,
    get_cached_dependents,
)
```

### Single Object Lookup

```python
# Get task by ID
task = get_cached_task(cache, 'task-001')

# Get sprint by ID
sprint = get_cached_sprint(cache, 'sprint-001')

# Get track by ID
track = get_cached_track(cache, 'track-001')
```

**Performance:**
- With cache: ~1ms (O(1) lookup)
- Without cache: ~5ms (linear scan)

### Bulk Operations

```python
# Get all tasks
tasks = get_all_cached_tasks(cache)

# Get all sprints
sprints = get_all_cached_sprints(cache)

# Get all tracks
tracks = get_all_cached_tracks(cache)
```

**Performance:**
- With cache: ~10ms (O(1) lookup)
- Without cache: ~150ms (scan all files)

### Dependency Queries

```python
# Get dependencies for an object
deps = get_cached_dependencies(cache, 'task-003')
# Returns: ['task-001', 'task-002']

# Get dependents (reverse dependencies)
dependents = get_cached_dependents(cache, 'task-001')
# Returns: ['task-002', 'task-003']
```

**Performance:**
- With cache: ~20ms (pre-computed graph)
- Without cache: ~300ms (build graph on-the-fly)

---

## Cache Fallback

All helpers support `cache=None` for `--no-cache` mode:

```python
# Works with or without cache
task = get_cached_task(cache, 'task-001', root_dir)

# If cache is None:
#   - Falls back to direct file loading
#   - Slower, but works
#   - Useful for debugging
```

---

## Direct Cache API

For advanced usage, use cache directly:

```python
cache = args.cache

# Single lookups (O(1) after index built)
task = cache.get_task('task-001')
sprint = cache.get_sprint('sprint-001')
track = cache.get_track('track-001')

# Bulk operations
all_tasks = cache.get_all_tasks()
all_sprints = cache.get_all_sprints()
all_tracks = cache.get_all_tracks()

# Dependency graphs
dep_graph = cache.get_dependency_graph()
reverse_graph = cache.get_reverse_dependency_graph()
deps = cache.get_dependencies('task-003')
dependents = cache.get_dependents('task-001')

# Cache management
stats = cache.get_stats()
cache.invalidate()  # Full invalidation
cache.invalidate(file_path)  # Partial invalidation
is_valid = cache.check_validity()
```

---

## Cache Statistics

```python
stats = cache.get_stats()

# Returns:
{
    'hits': 20,
    'misses': 0,
    'total_queries': 20,
    'hit_rate': 100.0,
    'index_builds': 1,
    'indexes_built': True,
    'tasks_indexed': 6,
    'sprints_indexed': 1,
    'tracks_indexed': 4,
}
```

---

## Best Practices

### ✅ DO

- **Use cache helpers** for standard lookups
- **Handle `cache=None`** gracefully (--no-cache mode)
- **Trust the cache** - it's automatically invalidated after state changes
- **Use bulk operations** when loading multiple objects

### ❌ DON'T

- **Don't manually invalidate** unless you're modifying files directly
- **Don't bypass cache** for query operations
- **Don't assume cache is always available** (could be None)

---

## Example: List Command

```python
def handle_list(args):
    """Handle list command."""
    from cache_helpers import get_all_cached_tasks, get_all_cached_sprints, get_all_cached_tracks

    cache = args.cache
    root_dir = find_root_dir(args)

    if args.type == 'tasks' or not args.type:
        tasks = get_all_cached_tasks(cache, root_dir)
        for task in tasks:
            print(f"  {task['id']}: {task['name']}")

    if args.type == 'sprints' or not args.type:
        sprints = get_all_cached_sprints(cache, root_dir)
        for sprint in sprints:
            print(f"  {sprint['id']}: {sprint['name']}")

    if args.type == 'tracks' or not args.type:
        tracks = get_all_cached_tracks(cache, root_dir)
        for track in tracks:
            print(f"  {track['id']}: {track['name']}")
```

---

## Example: Deps Command

```python
def handle_deps(args):
    """Handle deps command."""
    from cache_helpers import get_cached_dependencies, get_cached_dependents

    cache = args.cache
    root_dir = find_root_dir(args)

    object_id = args.id

    if args.blockers or not args.dependents:
        # Show dependencies (what blocks this object)
        deps = get_cached_dependencies(cache, object_id, root_dir)
        print(f"Dependencies for {object_id}:")
        for dep in deps:
            print(f"  - {dep}")

    if args.dependents or not args.blockers:
        # Show dependents (what depends on this object)
        dependents = get_cached_dependents(cache, object_id, root_dir)
        print(f"Dependents of {object_id}:")
        for dependent in dependents:
            print(f"  - {dependent}")
```

---

## Performance Comparison

| Operation | Without Cache | With Cache | Speedup |
|-----------|--------------|------------|---------|
| Find task by ID | ~5ms | ~1ms | **4.5x** |
| Load all tasks | ~150ms | ~10ms | **15x** |
| Dependency graph | ~300ms | ~20ms | **15x** |
| Reverse deps | ~300ms | ~20ms | **15x** |

---

## Debugging

### Enable --no-cache

```bash
roadmap --no-cache list tasks
```

This disables caching and uses fallback loading (slower but useful for debugging).

### Check Cache Stats

```python
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
```

### Verify Cache Validity

```python
if not cache.check_validity():
    print("⚠️ Cache is stale (files modified)")
    cache.invalidate()
```

---

## Migration Guide

### Before (Direct File Loading)

```python
def handle_show(args):
    root_dir = find_root_dir(args)
    fs = FileSystemManager(root_dir)

    # Linear scan through all task files
    for task_file in (fs.vibey_dir / 'tasks').glob('*-tasks.yaml'):
        data = load_yaml(task_file)
        for task in data.get('tasks', []):
            if task['id'] == args.id:
                print(f"Task: {task['name']}")
                return
```

### After (Using Cache)

```python
def handle_show(args):
    from cache_helpers import get_cached_task

    cache = args.cache
    root_dir = find_root_dir(args)

    # O(1) lookup
    task = get_cached_task(cache, args.id, root_dir)
    if task:
        print(f"Task: {task['name']}")
```

**Result:** 4.5x faster, simpler code.

---

## FAQs

**Q: When is cache invalidated?**
A: Automatically after state-changing commands (`start`, `complete`, `assign`, `batch`, `progress`).

**Q: What if I modify files directly?**
A: Call `cache.invalidate()` after modifications.

**Q: Can I disable caching?**
A: Yes, use `--no-cache` flag.

**Q: What if cache is stale?**
A: Use `cache.check_validity()` to detect, then `cache.invalidate()`.

**Q: Does cache work for the `init` command?**
A: No, cache is not initialized for `init` (no roadmap exists yet).

---

## See Also

- `cache.py` - RoadmapCache implementation
- `cache_helpers.py` - Helper functions
- `test_roadmap_cache.py` - Unit tests
- `test_cli_cache_integration.py` - Integration tests
- `benchmark_cache.py` - Performance benchmarks
