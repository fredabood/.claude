# Task 002: Implement Auto-Progression Logic in update.py

**Task ID:** dogfooding-bugs-04-task-002
**Bug Addressed:** #1 (Track and Sprint Progress Not Auto-Updated After Task Completion)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The `_update_sprint_progress()` and `_update_track_progress()` functions fail with ULID-based flat structure because they extract `track_id` from `sprint_id` using string manipulation instead of reading the `track_id` field from the Sprint model.

---

## Current Implementation (Broken)

```python
# update.py:1346-1439
def _update_sprint_progress(fs: FileSystemManager, sprint_id: str):
    """Update sprint progress based on task completion."""
    sprint_path = fs.get_sprint_path(sprint_id)
    # ...

    # BROKEN: Assumes hierarchical ID format
    track_id = sprint_id.rsplit('-', 1)[0]  # Line 1438
    _update_track_progress(fs, track_id)
```

With ULID `01KC2D0JKVT80AFQ6C1PA8CKJD`:
- `rsplit('-', 1)[0]` returns `01KC2D0JKVT80AFQ6C1PA8CKJ` (truncated ULID)
- Track lookup fails → progress chain breaks

---

## Implementation

### Fix 1: Use Sprint Model's track_id

```python
# update.py:1346
def _update_sprint_progress(fs: FileSystemManager, sprint_id: str):
    """Update sprint progress based on task completion."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        return

    sprint = load_sprint(sprint_path)
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        return

    # Load tasks for this sprint (filter by sprint_id in flat structure)
    if fs.structure_format == "flat":
        all_tasks = load_tasks(tasks_path)
        tasks = [t for t in all_tasks if getattr(t, 'sprint_id', None) == sprint_id]
    else:
        tasks = load_tasks(tasks_path)

    # ... existing progress calculation ...

    # FIXED: Get track_id from sprint model instead of parsing ID
    track_id = sprint.track_id  # Use model field
    _update_track_progress(fs, track_id)
```

### Fix 2: Handle Flat Structure Task Loading

The `get_tasks_path()` returns the entire `tasks/` directory in flat structure. Need to filter:

```python
def _load_tasks_for_sprint(fs: FileSystemManager, sprint_id: str) -> List[Task]:
    """Load tasks belonging to a specific sprint.

    Handles both flat and nested directory structures.

    Args:
        fs: FileSystemManager instance
        sprint_id: Sprint ID to filter tasks for

    Returns:
        List of Task objects belonging to the sprint
    """
    tasks_path = fs.get_tasks_path(sprint_id)

    if not tasks_path.exists():
        return []

    if fs.structure_format == "flat":
        # Flat structure: tasks/ contains all tasks, filter by sprint_id
        all_tasks = []
        for task_file in tasks_path.glob("*.yaml"):
            try:
                task = load_task(task_file)
                if getattr(task, 'sprint_id', None) == sprint_id:
                    all_tasks.append(task)
            except Exception:
                continue
        return all_tasks
    else:
        # Nested structure: all tasks in this path belong to sprint
        return load_tasks(tasks_path)
```

### Fix 3: Update _update_track_progress to Handle Flat Structure

```python
# update.py:1442
def _update_track_progress(fs: FileSystemManager, track_id: str):
    """Update track progress based on sprint completion."""
    track_path = fs.get_track_path(track_id)
    if not track_path.exists():
        return

    try:
        track = load_track(track_path)
    except Exception as e:
        print(f"⚠️  Failed to load track {track_id}: {e}")
        return

    # Calculate progress from sprint files (not sprint summaries in track)
    if fs.structure_format == "flat":
        # Find all sprints belonging to this track
        sprints_dir = fs.roadmap_root / "sprints"
        total_sprints = 0
        completed_sprints = 0
        total_tasks = 0
        completed_tasks = 0

        for sprint_file in sprints_dir.glob("*.yaml"):
            try:
                sprint = load_sprint(sprint_file)
                if sprint.track_id != track_id:
                    continue

                total_sprints += 1
                if sprint.status in [Status.COMPLETED, Status.PRODUCTION_GATE_CHECK,
                                     Status.PRODUCTION_READY, Status.DEPLOYED]:
                    completed_sprints += 1

                total_tasks += sprint.progress.tasks_total
                completed_tasks += sprint.progress.tasks_completed
            except Exception:
                continue
    else:
        # Nested structure: use sprint summaries in track
        total_sprints = len(track.sprints)
        completed_sprints = 0
        total_tasks = 0
        completed_tasks = 0

        for sprint_summary in track.sprints:
            sprint_path = fs.get_sprint_path(sprint_summary.id)
            if sprint_path.exists():
                sprint = load_sprint(sprint_path)
                # ... existing logic ...

    # Update track progress
    track.progress.sprints_total = total_sprints
    track.progress.sprints_completed = completed_sprints
    track.progress.tasks_total = total_tasks
    track.progress.tasks_completed = completed_tasks
    completion_percent = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    track.progress.completion_percent = completion_percent

    # ... rest of function unchanged ...
```

### Fix 4: Update _update_roadmap_progress Similarly

```python
# update.py:1514
def _update_roadmap_progress(fs: FileSystemManager):
    """Update roadmap progress based on track completion."""
    roadmap_path = fs.get_roadmap_path()
    if not roadmap_path.exists():
        return

    roadmap = load_roadmap(roadmap_path)

    if fs.structure_format == "flat":
        # Flat structure: scan tracks/ directory
        tracks_dir = fs.roadmap_root / "tracks"
        total_tracks = 0
        completed_tracks = 0
        total_sprints = 0
        completed_sprints = 0
        total_tasks = 0
        completed_tasks = 0

        for track_file in tracks_dir.glob("*.yaml"):
            try:
                track = load_track(track_file)
                total_tracks += 1

                if track.status in [Status.COMPLETED, Status.PRODUCTION_READY, Status.DEPLOYED]:
                    completed_tracks += 1

                total_sprints += track.progress.sprints_total
                completed_sprints += track.progress.sprints_completed
                total_tasks += track.progress.tasks_total
                completed_tasks += track.progress.tasks_completed
            except Exception:
                continue
    else:
        # Nested structure: use track summaries in roadmap
        # ... existing logic ...

    # Update roadmap progress
    # ... rest unchanged ...
```

---

## Files to Modify

| File | Lines | Changes |
|------|-------|---------|
| `vibey/operations/roadmap/update.py` | 1346-1440 | Fix track_id extraction, add task filtering |
| `vibey/operations/roadmap/update.py` | 1442-1512 | Handle flat structure in track progress |
| `vibey/operations/roadmap/update.py` | 1514-1573 | Handle flat structure in roadmap progress |

---

## Helper Function to Add

```python
def _get_sprint_track_id(fs: FileSystemManager, sprint_id: str) -> Optional[str]:
    """
    Get the track_id for a sprint.

    Handles both flat (read from model) and nested (parse ID) structures.

    Args:
        fs: FileSystemManager instance
        sprint_id: Sprint ID

    Returns:
        Track ID or None if not found
    """
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        return None

    sprint = load_sprint(sprint_path)
    return sprint.track_id
```

---

## Testing Strategy

```python
def test_progress_propagation_flat_structure(flat_roadmap_environment):
    """Progress propagates correctly in flat structure."""
    # Complete a task
    result = complete_task(flat_roadmap_environment, "task-001")
    assert result == 0

    # Verify sprint progress updated
    sprint = load_sprint(sprint_path)
    assert sprint.progress.tasks_completed > 0

    # Verify track progress updated
    track = load_track(track_path)
    assert track.progress.tasks_completed > 0

    # Verify roadmap progress updated
    roadmap = load_roadmap(roadmap_path)
    assert roadmap.progress.tasks_completed > 0


def test_track_id_from_sprint_model(flat_roadmap_environment):
    """Track ID is read from sprint model, not parsed from ID."""
    sprint = load_sprint(sprint_path)
    track_id = sprint.track_id

    # Track ID should be valid ULID
    assert len(track_id) == 26
    assert track_id.isalnum()
```

---

## Success Criteria

- [ ] `track_id` extracted from Sprint model (not parsed from ID)
- [ ] Task loading filters by `sprint_id` in flat structure
- [ ] Track progress calculates from sprint files in flat structure
- [ ] Roadmap progress calculates from track files in flat structure
- [ ] All existing tests continue to pass
- [ ] Progress propagates end-to-end after task completion

---

## Dependencies

- Task 001 (research confirms approach)

---

## Notes

This fix maintains backward compatibility with nested structure while adding support for flat structure. The key insight is that ULID-based IDs are independent, so parent-child relationships must be read from model fields, not inferred from ID strings.
