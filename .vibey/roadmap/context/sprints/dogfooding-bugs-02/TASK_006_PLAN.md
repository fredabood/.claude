# Task 006: Implement Lazy Loading for Track Details

**Task ID:** dogfooding-bugs-02-task-006
**Bug Addressed:** #10 (Monolithic roadmap.yaml read)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

Loading all track details (sprints, tasks) for 39 tracks is slow and memory-intensive. Implement lazy loading so track details are only loaded when needed.

---

## Design

### Current Flow (Eager Loading)
```
load_roadmap()
    └──► Load all tracks
         └──► For each track: load all sprints
              └──► For each sprint: load all tasks
```
Total operations: 39 tracks × N sprints × M tasks = thousands of file reads

### New Flow (Lazy Loading)
```
load_roadmap()
    └──► Discover TrackSummary (id, name, status)

get_track_details(track_id)
    └──► Load full track
         └──► Discover SprintSummary (id, name, status)

get_sprint_details(sprint_id)
    └──► Load full sprint
         └──► Discover TaskSummary (id, title, status)
```

---

## Implementation

### 1. Add TrackSummary → Full Track Loading

```python
def load_track_details(
    track_id: str,
    tracks_dir: Path,
    sprints_dir: Path,
) -> Track:
    """
    Load full track details including sprint summaries.

    Args:
        track_id: Track ULID
        tracks_dir: Path to tracks/ directory
        sprints_dir: Path to sprints/ directory

    Returns:
        Track with SprintSummary children
    """
    # Load track YAML
    track_path = tracks_dir / f"{track_id}.yaml"
    track = load_track(track_path)

    # Discover sprints for this track
    track.sprints = _discover_sprint_summaries(sprints_dir, track_id)

    return track


def _discover_sprint_summaries(
    sprints_dir: Path,
    track_id: str
) -> List[SprintSummary]:
    """Discover sprint summaries for a track."""
    summaries = []

    for sprint_file in sprints_dir.glob("*.yaml"):
        try:
            with open(sprint_file, 'r') as f:
                data = yaml.safe_load(f)

            sprint_data = data.get('sprint', {})

            # Filter by track_id
            if sprint_data.get('track_id') != track_id:
                continue

            summary = SprintSummary(
                id=sprint_data.get('id', sprint_file.stem),
                name=sprint_data.get('name', ''),
                status=Status(sprint_data.get('status', 'not_started')),
            )
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to load sprint {sprint_file}: {e}")

    return summaries
```

### 2. Add Sprint → Task Discovery

```python
def load_sprint_details(
    sprint_id: str,
    sprints_dir: Path,
    tasks_dir: Path,
) -> Sprint:
    """Load full sprint details including task summaries."""
    sprint_path = sprints_dir / f"{sprint_id}.yaml"
    sprint = load_sprint(sprint_path)

    # Discover tasks for this sprint
    sprint.tasks = _discover_task_summaries(tasks_dir, sprint_id)

    return sprint


def _discover_task_summaries(
    tasks_dir: Path,
    sprint_id: str
) -> List[TaskSummary]:
    """Discover task summaries for a sprint."""
    summaries = []

    for task_file in tasks_dir.glob("*.yaml"):
        try:
            with open(task_file, 'r') as f:
                data = yaml.safe_load(f)

            task_data = data.get('task', {})

            # Filter by sprint_id
            if task_data.get('sprint_id') != sprint_id:
                continue

            summary = TaskSummary(
                id=task_data.get('id', task_file.stem),
                title=task_data.get('title', ''),
                status=TaskStatus(task_data.get('status', 'not_started')),
            )
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to load task {task_file}: {e}")

    return summaries
```

### 3. Query Layer Integration

```python
# vibey/operations/roadmap/query.py

def get_track(track_id: str, root_dir: Path) -> Track:
    """Get full track details with lazy sprint loading."""
    fs = FileSystemManager(root_dir)

    tracks_dir = fs.roadmap_root / "tracks"
    sprints_dir = fs.roadmap_root / "sprints"

    return load_track_details(track_id, tracks_dir, sprints_dir)


def get_sprint(sprint_id: str, root_dir: Path) -> Sprint:
    """Get full sprint details with lazy task loading."""
    fs = FileSystemManager(root_dir)

    sprints_dir = fs.roadmap_root / "sprints"
    tasks_dir = fs.roadmap_root / "tasks"

    return load_sprint_details(sprint_id, sprints_dir, tasks_dir)
```

---

## Performance Optimization

### Indexing Sprint-Track Relationships

Instead of scanning all sprint files for each track, build an index:

```python
def _build_sprint_index(sprints_dir: Path) -> Dict[str, List[str]]:
    """Build track_id → [sprint_ids] index."""
    index = defaultdict(list)

    for sprint_file in sprints_dir.glob("*.yaml"):
        with open(sprint_file, 'r') as f:
            data = yaml.safe_load(f)
        sprint_data = data.get('sprint', {})
        track_id = sprint_data.get('track_id')
        if track_id:
            index[track_id].append(sprint_file.stem)

    return dict(index)
```

### Caching

```python
class RoadmapCache:
    """In-memory cache for loaded roadmap objects."""

    def __init__(self):
        self._tracks: Dict[str, Track] = {}
        self._sprints: Dict[str, Sprint] = {}
        self._sprint_index: Optional[Dict[str, List[str]]] = None

    def get_track(self, track_id: str) -> Optional[Track]:
        return self._tracks.get(track_id)

    def set_track(self, track: Track):
        self._tracks[track.id] = track
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | Add lazy loading functions |
| `vibey/operations/roadmap/query.py` | Add get_track, get_sprint wrappers |
| `vibey/cli/roadmap_lib/filesystem.py` | Add directory helpers if needed |

---

## Success Criteria

- [ ] Track details loaded on demand
- [ ] Sprint details loaded on demand
- [ ] Task details loaded on demand
- [ ] Performance improvement for `roadmap status` (no full load)
- [ ] Backward compatible with existing APIs

---

## Dependencies

- Task 005 (track discovery)

---

## Notes

This optimization is important for large roadmaps. The Vibey roadmap has:
- 39 tracks
- 205 sprints
- 1123 tasks

Full eager loading would read ~1400 YAML files. Lazy loading reduces this to ~40 for status display.
