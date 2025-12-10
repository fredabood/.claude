# Task 009: Update db_rebuild_cmd to Load from ULID Files

**Task ID:** dogfooding-bugs-03-task-009
**Bug Addressed:** #11 (Database Rebuild Loads 0 Tracks/Sprints/Tasks)
**Complexity:** High
**Type:** Development

---

## Problem Statement

The `db_rebuild_cmd` function calls `_load_roadmap_to_db` which uses the OLD nested directory structure:
```
.vibey/roadmap/
├── {track_id}/
│   ├── track.yaml
│   └── {sprint_id}/
│       ├── sprint.yaml
│       └── {task_id}/
│           └── task.yaml
```

But the current ULID-based flat structure is:
```
.vibey/roadmap/
├── tracks/
│   ├── {ULID}.yaml
│   └── ...
├── sprints/
│   ├── {ULID}.yaml
│   └── ...
├── tasks/
│   ├── {ULID}.yaml
│   └── ...
└── roadmap.yaml
```

This mismatch causes `db_rebuild_cmd` to find 0 tracks/sprints/tasks.

---

## Root Cause Analysis

### Current Code Flow (lines 1878-2082 in commands.py)

```python
def _load_roadmap_to_db(conn, roadmap, vibey_dir: Path):
    """Load roadmap data into database."""
    roadmap_dir = vibey_dir / "roadmap"

    # OLD: Iterate track summaries from roadmap.yaml
    for track_summary in roadmap.tracks:
        track_dir = roadmap_dir / track_summary.id  # ❌ Wrong path
        track_yaml = track_dir / "track.yaml"       # ❌ Doesn't exist

        if not track_yaml.exists():
            continue  # Silently skips EVERYTHING

        # ... load track, then iterate sprint summaries
        for sprint_summary in track.sprints:
            sprint_dir = track_dir / sprint_summary.id  # ❌ Wrong path
            # ...
```

### Why It Fails

1. `roadmap.tracks` contains `TrackSummary` objects with `id` field
2. Code builds path: `roadmap_dir / "sqlite-backend" / "track.yaml"`
3. But file actually at: `roadmap_dir / "tracks" / "01KC2D0FT6KF4V2R1J0HDFR1ZM.yaml"`
4. `if not track_yaml.exists(): continue` silently skips
5. Result: 0 tracks, 0 sprints, 0 tasks loaded

---

## Implementation

### Strategy: Flat File Iteration

Instead of walking roadmap.yaml → track.yaml → sprint.yaml → task.yaml hierarchy, iterate flat directories:

```python
def _load_roadmap_to_db_ulid(conn, roadmap, vibey_dir: Path):
    """Load roadmap data into database (ULID flat structure)."""
    from datetime import datetime, timezone
    from vibey.roadmap.database.crud import (
        create_roadmap as db_create_roadmap,
        create_track as db_create_track,
        create_sprint as db_create_sprint,
        create_task as db_create_task,
    )
    from vibey.roadmap.serialization import load_track, load_sprint, load_task

    now = datetime.now(timezone.utc)
    roadmap_dir = vibey_dir / "roadmap"

    # Create roadmap record
    status_val = roadmap.status.value if hasattr(roadmap.status, 'value') else str(roadmap.status)
    db_create_roadmap(
        id=roadmap.id,
        name=roadmap.name,
        version=roadmap.version,
        status=_normalize_status(status_val),
        blocked=roadmap.blocked,
        created=roadmap.created or now,
        conn=conn,
    )

    # Track statistics
    loaded_tracks = 0
    loaded_sprints = 0
    loaded_tasks = 0
    skipped_tracks = 0
    skipped_sprints = 0
    skipped_tasks = 0

    # ==== NEW: Load from flat ULID directories ====

    # 1. Load all tracks from tracks/*.yaml
    tracks_dir = roadmap_dir / "tracks"
    if tracks_dir.exists():
        for track_file in sorted(tracks_dir.glob("*.yaml")):
            try:
                track = load_track(track_file)
                track_status = track.status.value if hasattr(track.status, 'value') else str(track.status)

                db_create_track(
                    id=track.id,
                    roadmap_id=roadmap.id,
                    name=track.name,
                    status=_normalize_status(track_status),
                    blocked=track.blocked,
                    priority=track.priority.value if hasattr(track, 'priority') and track.priority else 'medium',
                    created=track.created or now,
                    conn=conn,
                )
                loaded_tracks += 1
            except Exception as e:
                skipped_tracks += 1
                continue

    # 2. Load all sprints from sprints/*.yaml
    sprints_dir = roadmap_dir / "sprints"
    if sprints_dir.exists():
        for sprint_file in sorted(sprints_dir.glob("*.yaml")):
            try:
                sprint = load_sprint(sprint_file)
                sprint_status = sprint.status.value if hasattr(sprint.status, 'value') else str(sprint.status)

                # Extract track_id from sprint (required field)
                track_id = getattr(sprint, 'track_id', None)
                if not track_id:
                    # Try to infer from file metadata or skip
                    skipped_sprints += 1
                    continue

                # Build metadata, deliverables, quality_gates as before...
                sprint_metadata = None
                if sprint.metadata:
                    sprint_metadata = {
                        'last_updated': sprint.metadata.last_updated.isoformat() if sprint.metadata.last_updated else None,
                        'estimated_duration': sprint.metadata.estimated_duration,
                        'actual_duration': sprint.metadata.actual_duration,
                        'estimated_tokens': sprint.metadata.estimated_tokens,
                        'actual_tokens': sprint.metadata.actual_tokens,
                    }

                db_create_sprint(
                    id=sprint.id,
                    track_id=track_id,
                    roadmap_id=roadmap.id,
                    name=sprint.name,
                    status=_normalize_status(sprint_status),
                    blocked=sprint.blocked,
                    created=sprint.created or now,
                    started=sprint.started,
                    completed=sprint.completed,
                    description=sprint.description,
                    goal=sprint.goal,
                    notes=sprint.notes,
                    conn=conn,
                )
                loaded_sprints += 1
            except Exception as e:
                skipped_sprints += 1
                continue

    # 3. Load all tasks from tasks/*.yaml
    tasks_dir = roadmap_dir / "tasks"
    if tasks_dir.exists():
        for task_file in sorted(tasks_dir.glob("*.yaml")):
            try:
                task = load_task(task_file)
                task_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

                # Extract sprint_id and track_id from task (required fields)
                sprint_id = getattr(task, 'sprint_id', None)
                track_id = getattr(task, 'track_id', None)
                if not sprint_id:
                    skipped_tasks += 1
                    continue

                db_create_task(
                    id=task.id,
                    sprint_id=sprint_id,
                    track_id=track_id,
                    roadmap_id=roadmap.id,
                    title=task.title,
                    status=_normalize_status(task_status),
                    blocked=task.blocked,
                    created=task.created or now,
                    description=task.description,
                    conn=conn,
                )
                loaded_tasks += 1
            except Exception as e:
                skipped_tasks += 1
                continue

    # Print summary
    print(f"   Loaded {loaded_tracks} tracks, {loaded_sprints} sprints, {loaded_tasks} tasks")
    if skipped_tracks or skipped_sprints or skipped_tasks:
        print(f"   Skipped {skipped_tracks} tracks, {skipped_sprints} sprints, {skipped_tasks} tasks")
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands.py` | Add `_load_roadmap_to_db_ulid()`, update `db_init_cmd` to use it |

---

## Compatibility Strategy

```python
def _load_roadmap_to_db(conn, roadmap, vibey_dir: Path):
    """Load roadmap data into database.

    Supports both:
    - ULID flat structure (tracks/, sprints/, tasks/)
    - Legacy nested structure (track-id/sprint-id/task-id/)
    """
    roadmap_dir = vibey_dir / "roadmap"

    # Detect structure type
    if (roadmap_dir / "tracks").is_dir():
        # ULID flat structure
        return _load_roadmap_to_db_ulid(conn, roadmap, vibey_dir)
    else:
        # Legacy nested structure
        return _load_roadmap_to_db_legacy(conn, roadmap, vibey_dir)
```

---

## Testing Strategy

```python
def test_db_rebuild_ulid_structure(ulid_roadmap_environment):
    """Database rebuild works with ULID flat structure."""
    result = db_rebuild_cmd(force=True)

    assert result == 0

    # Verify counts
    conn = get_connection()
    tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    sprints = conn.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]
    tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    assert tracks > 0
    assert sprints > 0
    assert tasks > 0


def test_db_rebuild_legacy_structure(legacy_roadmap_environment):
    """Database rebuild still works with legacy nested structure."""
    result = db_rebuild_cmd(force=True)
    assert result == 0


def test_db_rebuild_detects_structure(mixed_environment):
    """Database rebuild correctly detects structure type."""
    # Should not error, should use appropriate loader
    result = db_rebuild_cmd(force=True)
    assert result == 0
```

---

## Success Criteria

- [ ] `db_rebuild_cmd` loads tracks from `tracks/*.yaml`
- [ ] `db_rebuild_cmd` loads sprints from `sprints/*.yaml`
- [ ] `db_rebuild_cmd` loads tasks from `tasks/*.yaml`
- [ ] Backward compatibility with legacy nested structure
- [ ] Progress reporting shows actual counts (not 0)

---

## Dependencies

- Task 010 (sql_loader update - parallel work)

---

## Notes

This is the primary fix for Bug #11. The current code silently fails because `track_yaml.exists()` returns False and the loop continues without error. After this fix, the database will correctly load all entities from the flat ULID structure.

Expected counts for this repository:
- Tracks: 39
- Sprints: 213
- Tasks: 1125
