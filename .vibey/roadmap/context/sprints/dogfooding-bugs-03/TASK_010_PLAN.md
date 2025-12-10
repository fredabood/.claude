# Task 010: Update sql_loader init to Iterate tracks/*.yaml

**Task ID:** dogfooding-bugs-03-task-010
**Bug Addressed:** #11 (Database Rebuild Loads 0 Tracks/Sprints/Tasks)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The `sql_loader.py` module has functions that may rely on the old nested directory structure. We need to ensure all loader functions work with the ULID flat structure:

- `tracks/*.yaml` - All track files
- `sprints/*.yaml` - All sprint files
- `tasks/*.yaml` - All task files

---

## Current Implementation Analysis

### sql_loader.py Functions

The `sql_loader.py` module loads entities FROM the database, not from YAML files. This is the SQLite → Python direction.

```python
# sql_loader.py - loads from database
def load_roadmap(roadmap_id: str) -> Roadmap
def load_track(track_id: str) -> Track
def load_sprint(sprint_id: str) -> Sprint
def load_task(task_id: str) -> Task
```

### yaml_loader.py Functions

The `yaml_loader.py` module loads FROM YAML files. This is what needs updating:

```python
# yaml_loader.py - loads from YAML files
def load_roadmap(file_path: Path) -> Roadmap
def load_track(file_path: Path) -> Track
def load_sprint(file_path: Path) -> Sprint
def load_task(file_path: Path) -> Task
```

### The Real Problem

The issue is in `_load_roadmap_to_db` (covered in Task 009), NOT in the loader functions themselves. The loaders accept a file path and work correctly - the problem is the code that CALLS them with wrong paths.

---

## Investigation Needed

### 1. Check yaml_loader.py Path Handling

```python
# vibey/roadmap/serialization/yaml_loader.py

def load_track(file_path: Path) -> Track:
    """Load track from YAML file."""
    # Does this require specific directory structure?
    # Or just the file contents?
```

### 2. Check for Directory-Dependent Code

Search for code that assumes:
- Track files are at `{track_id}/track.yaml`
- Sprint files are at `{track_id}/{sprint_id}/sprint.yaml`
- Task files are at `{track_id}/{sprint_id}/{task_id}/task.yaml`

---

## Implementation

### Update yaml_loader.py (if needed)

If the loader extracts parent relationship info from directory paths, update to use YAML content:

```python
def load_sprint(file_path: Path) -> Sprint:
    """Load sprint from YAML file.

    The track_id is read from the YAML content, not inferred from path.
    """
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    sprint_data = data.get('sprint', data)

    # ULID structure: track_id is explicit in YAML
    track_id = sprint_data.get('track_id')

    return Sprint(
        id=sprint_data['id'],
        track_id=track_id,  # From YAML, not path
        name=sprint_data['name'],
        # ...
    )
```

### Add Helper Functions for Bulk Loading

```python
# vibey/roadmap/serialization/yaml_loader.py

def load_all_tracks(roadmap_dir: Path) -> List[Track]:
    """Load all tracks from tracks/ directory.

    Args:
        roadmap_dir: Path to .vibey/roadmap/

    Returns:
        List of Track objects
    """
    tracks = []
    tracks_dir = roadmap_dir / "tracks"

    if not tracks_dir.exists():
        return tracks

    for track_file in sorted(tracks_dir.glob("*.yaml")):
        try:
            track = load_track(track_file)
            tracks.append(track)
        except Exception as e:
            logger.warning(f"Failed to load track {track_file}: {e}")
            continue

    return tracks


def load_all_sprints(roadmap_dir: Path) -> List[Sprint]:
    """Load all sprints from sprints/ directory."""
    sprints = []
    sprints_dir = roadmap_dir / "sprints"

    if not sprints_dir.exists():
        return sprints

    for sprint_file in sorted(sprints_dir.glob("*.yaml")):
        try:
            sprint = load_sprint(sprint_file)
            sprints.append(sprint)
        except Exception as e:
            logger.warning(f"Failed to load sprint {sprint_file}: {e}")
            continue

    return sprints


def load_all_tasks(roadmap_dir: Path) -> List[Task]:
    """Load all tasks from tasks/ directory."""
    tasks = []
    tasks_dir = roadmap_dir / "tasks"

    if not tasks_dir.exists():
        return tasks

    for task_file in sorted(tasks_dir.glob("*.yaml")):
        try:
            task = load_task(task_file)
            tasks.append(task)
        except Exception as e:
            logger.warning(f"Failed to load task {task_file}: {e}")
            continue

    return tasks
```

### Update db_init_cmd to Use Helpers

```python
# vibey/cli/commands.py

def _load_roadmap_to_db_ulid(conn, roadmap, vibey_dir: Path):
    """Load roadmap data into database (ULID flat structure)."""
    from vibey.roadmap.serialization.yaml_loader import (
        load_all_tracks,
        load_all_sprints,
        load_all_tasks,
    )

    roadmap_dir = vibey_dir / "roadmap"

    # Create roadmap record
    db_create_roadmap(...)

    # Load all entities using new helpers
    tracks = load_all_tracks(roadmap_dir)
    for track in tracks:
        db_create_track(track, conn=conn)
    print(f"   Loaded {len(tracks)} tracks")

    sprints = load_all_sprints(roadmap_dir)
    for sprint in sprints:
        db_create_sprint(sprint, conn=conn)
    print(f"   Loaded {len(sprints)} sprints")

    tasks = load_all_tasks(roadmap_dir)
    for task in tasks:
        db_create_task(task, conn=conn)
    print(f"   Loaded {len(tasks)} tasks")
```

---

## YAML Structure Requirements

### Track YAML (tracks/{ULID}.yaml)

```yaml
track:
  id: "01KC2D0FT6KF4V2R1J0HDFR1ZM"
  name: "SQLite Backend"
  status: "in_progress"
  # No path dependency - all info in YAML
```

### Sprint YAML (sprints/{ULID}.yaml)

```yaml
sprint:
  id: "01KC2D0JKVT80AFQ6C1PA8CKJD"
  track_id: "01KC2D0FT6KF4V2R1J0HDFR1ZM"  # Required!
  name: "Sprint 1"
  status: "completed"
```

### Task YAML (tasks/{ULID}.yaml)

```yaml
task:
  id: "01KC2D0N8H7E5C2Q9V3K1B4J6M"
  sprint_id: "01KC2D0JKVT80AFQ6C1PA8CKJD"  # Required!
  track_id: "01KC2D0FT6KF4V2R1J0HDFR1ZM"   # Required (denormalized)
  title: "Task title"
  status: "completed"
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | Add `load_all_tracks()`, `load_all_sprints()`, `load_all_tasks()` |
| `vibey/cli/commands.py` | Update to use new helpers |

---

## Testing Strategy

```python
def test_load_all_tracks_ulid(ulid_roadmap_dir):
    """load_all_tracks finds all tracks in tracks/ directory."""
    tracks = load_all_tracks(ulid_roadmap_dir)

    assert len(tracks) == 39  # Expected count
    assert all(hasattr(t, 'id') for t in tracks)
    assert all(hasattr(t, 'name') for t in tracks)


def test_load_all_sprints_with_track_ids(ulid_roadmap_dir):
    """load_all_sprints loads track_id from YAML content."""
    sprints = load_all_sprints(ulid_roadmap_dir)

    assert len(sprints) == 213  # Expected count
    # All sprints have track_id
    assert all(getattr(s, 'track_id', None) is not None for s in sprints)


def test_load_all_tasks_with_parent_ids(ulid_roadmap_dir):
    """load_all_tasks loads sprint_id and track_id from YAML content."""
    tasks = load_all_tasks(ulid_roadmap_dir)

    assert len(tasks) == 1125  # Expected count
    # All tasks have sprint_id
    assert all(getattr(t, 'sprint_id', None) is not None for t in tasks)


def test_load_all_handles_missing_dir(tmp_path):
    """load_all_* returns empty list if directory doesn't exist."""
    tracks = load_all_tracks(tmp_path)
    assert tracks == []


def test_load_all_handles_malformed_yaml(ulid_roadmap_dir, tmp_malformed):
    """load_all_* skips malformed YAML files gracefully."""
    # Add a malformed file
    (ulid_roadmap_dir / "tracks" / "bad.yaml").write_text("not: valid: yaml: {[")

    tracks = load_all_tracks(ulid_roadmap_dir)
    # Should still load valid tracks, skip bad one
    assert len(tracks) >= 38  # 39 - 1 bad
```

---

## Success Criteria

- [ ] `load_all_tracks()` iterates `tracks/*.yaml`
- [ ] `load_all_sprints()` iterates `sprints/*.yaml`
- [ ] `load_all_tasks()` iterates `tasks/*.yaml`
- [ ] Parent IDs (track_id, sprint_id) read from YAML content
- [ ] Graceful handling of malformed files
- [ ] Empty directories return empty lists

---

## Dependencies

- Task 009 (db_rebuild_cmd update - parallel work)

---

## Notes

This task adds helper functions for bulk loading from flat directories. The individual loaders (`load_track`, `load_sprint`, `load_task`) may not need changes if they already read from YAML content rather than inferring from paths.

Key principle: **All relationship information (track_id, sprint_id) must be explicit in YAML content**, not derived from directory structure.
