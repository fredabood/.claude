# Task 007: Update query.py to Use New Loading Strategy

**Task ID:** dogfooding-bugs-02-task-007
**Bug Addressed:** #10 (Monolithic roadmap.yaml read)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The query layer (`vibey/operations/roadmap/query.py`) needs to be updated to use the new ULID-aware loading strategy instead of relying solely on monolithic file loading.

---

## Current Implementation

```python
# query.py:79-94
def load_roadmap(file_path_or_id, root_dir: Optional[Path] = None):
    """Load roadmap from appropriate backend."""
    if root_dir and _use_sqlite_backend(root_dir):
        sql_load_roadmap, _, _, _ = _get_sql_loaders()
        roadmap_id = ...
        return sql_load_roadmap(roadmap_id)
    return yaml_load_roadmap(file_path_or_id)
```

This calls `yaml_load_roadmap` which reads from monolithic file.

---

## New Implementation

```python
def load_roadmap(file_path_or_id, root_dir: Optional[Path] = None) -> Roadmap:
    """
    Load roadmap from appropriate backend.

    For YAML backend with flat structure:
    - Loads metadata from roadmap.yaml
    - Discovers tracks from tracks/*.yaml
    - Merges track sources

    Args:
        file_path_or_id: Path to YAML file or roadmap ID for SQLite
        root_dir: Root directory for backend detection

    Returns:
        Roadmap object
    """
    if root_dir and _use_sqlite_backend(root_dir):
        sql_load_roadmap, _, _, _ = _get_sql_loaders()
        roadmap_id = file_path_or_id if isinstance(file_path_or_id, str) and not file_path_or_id.endswith('.yaml') else 'vibey-framework-v2'
        return sql_load_roadmap(roadmap_id)

    # YAML loading with track discovery
    return yaml_load_roadmap(file_path_or_id)  # Updated in Task 005


def load_track(file_path_or_id, root_dir: Optional[Path] = None) -> Track:
    """
    Load track from appropriate backend.

    For YAML backend with flat structure:
    - Loads track from tracks/{ulid}.yaml
    - Discovers sprints from sprints/*.yaml

    Args:
        file_path_or_id: Path to YAML file or track ID for SQLite
        root_dir: Root directory for backend detection

    Returns:
        Track object with sprint summaries
    """
    if root_dir and _use_sqlite_backend(root_dir):
        _, sql_load_track, _, _ = _get_sql_loaders()
        if isinstance(file_path_or_id, Path):
            track_id = file_path_or_id.stem  # ULID from filename
        else:
            track_id = file_path_or_id
        return sql_load_track(track_id)

    # For YAML, check if file exists at path
    if isinstance(file_path_or_id, Path) and file_path_or_id.exists():
        return yaml_load_track(file_path_or_id)

    # Otherwise, use FileSystemManager to resolve
    if root_dir:
        fs = FileSystemManager(root_dir)
        track_path = fs.get_track_path(file_path_or_id)
        if track_path.exists():
            return yaml_load_track(track_path)

    raise FileNotFoundError(f"Track not found: {file_path_or_id}")


def query_roadmap_summary(root_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Query roadmap summary for status display.

    Uses lazy loading to avoid reading all files.

    Args:
        root_dir: Project root directory

    Returns:
        Summary dict with tracks, progress, etc.
    """
    root_dir = root_dir or find_roadmap_root()
    if not root_dir:
        return {"error": "No roadmap found"}

    fs = FileSystemManager(root_dir)
    roadmap_path = fs.get_roadmap_path()

    if not roadmap_path.exists():
        return {"error": f"Roadmap not found at {roadmap_path}"}

    roadmap = load_roadmap(roadmap_path, root_dir=root_dir)

    # Build summary without loading full track details
    return {
        "id": roadmap.id,
        "name": roadmap.name,
        "version": roadmap.version,
        "status": roadmap.status.value,
        "progress": {
            "tracks_total": len(roadmap.tracks),
            "tracks_completed": sum(1 for t in roadmap.tracks if t.status == Status.COMPLETED),
            # These come from roadmap metadata, not calculated
            "sprints_total": roadmap.progress.sprints_total,
            "sprints_completed": roadmap.progress.sprints_completed,
            "tasks_total": roadmap.progress.tasks_total,
            "tasks_completed": roadmap.progress.tasks_completed,
            "completion_percent": roadmap.progress.completion_percent,
        },
        "tracks": [
            {
                "id": t.id,
                "name": t.name,
                "status": t.status.value,
                "priority": t.priority.value,
            }
            for t in roadmap.tracks
        ],
    }
```

---

## Files to Modify

| File | Function | Changes |
|------|----------|---------|
| `vibey/operations/roadmap/query.py` | `load_roadmap()` | Add ULID-aware path handling |
| `vibey/operations/roadmap/query.py` | `load_track()` | Add FileSystemManager integration |
| `vibey/operations/roadmap/query.py` | `load_sprint()` | Add FileSystemManager integration |
| `vibey/operations/roadmap/query.py` | `load_tasks()` | Add task discovery |
| `vibey/operations/roadmap/query.py` | `query_roadmap_summary()` | Use new loading |

---

## Integration Points

### CLI Commands Using query.py

| Command | Function Used | Update Needed |
|---------|--------------|---------------|
| `vibey roadmap status` | `query_roadmap_summary()` | Yes |
| `vibey roadmap show track X` | `load_track()` | Yes |
| `vibey roadmap show sprint X` | `load_sprint()` | Yes |
| `vibey roadmap list tracks` | `load_roadmap()` | Yes |

---

## Testing Strategy

```python
def test_query_roadmap_summary_discovers_tracks(tmp_path):
    """Summary includes tracks from ULID files."""
    # Setup flat structure with tracks
    ...

    summary = query_roadmap_summary(tmp_path)

    assert "tracks" in summary
    assert len(summary["tracks"]) > 0
    # Verify discovered track is included


def test_load_track_uses_filesystem_manager(tmp_path):
    """load_track resolves paths via FileSystemManager."""
    # Setup
    ...

    track = load_track("01KC2D0JKTE7Z4HCNHST8ZVW4R", root_dir=tmp_path)

    assert track.id == "01KC2D0JKTE7Z4HCNHST8ZVW4R"
```

---

## Success Criteria

- [ ] `query_roadmap_summary()` shows all 39 tracks
- [ ] `load_track()` works with both paths and IDs
- [ ] `load_sprint()` works with ULID IDs
- [ ] CLI commands use updated query functions
- [ ] Backward compatible with SQLite backend

---

## Dependencies

- Task 005 (load_roadmap with discovery)
- Task 006 (lazy loading)

---

## Notes

This task ties together the loading strategy changes from Tasks 004-006 with the CLI layer. After this task, all query operations will use the new ULID-aware loading.
