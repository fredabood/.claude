# Task 004: Design New Loading Strategy for ULID Files

**Task ID:** dogfooding-bugs-02-task-004
**Bug Addressed:** #10 (Monolithic roadmap.yaml read instead of ULID files)
**Complexity:** Medium
**Type:** Research/Design

---

## Problem Statement

Currently, `load_roadmap()` reads from monolithic `roadmap.yaml` which only contains `TrackSummary` objects. It needs to discover and load full track data from individual ULID files.

---

## Current Architecture

```
.vibey/roadmap/
├── roadmap.yaml          # Contains TrackSummary only (id, name, status, priority)
├── tracks/
│   ├── .id               # slug=ulid mappings
│   ├── 01KC2D0JK...yaml  # Full track data
│   └── ...
├── sprints/
│   ├── .id
│   └── *.yaml
└── tasks/
    ├── .id
    └── *.yaml
```

---

## Design Options

### Option 1: Progressive Enhancement (Recommended)

Keep `roadmap.yaml` as index, enhance with lazy loading:

```python
def load_roadmap(file_path: Path) -> Roadmap:
    """Load roadmap with track discovery from ULID files."""
    # 1. Load base roadmap from roadmap.yaml
    roadmap_data = yaml.safe_load(file_path.read_text())

    # 2. Discover tracks from tracks/*.yaml
    tracks_dir = file_path.parent / "tracks"
    discovered_tracks = discover_tracks_from_ulid_files(tracks_dir)

    # 3. Merge: ULID files are source of truth
    # roadmap.yaml tracks are just a cache/index
    merged_tracks = merge_track_sources(
        yaml_tracks=roadmap_data.get('tracks', []),
        ulid_tracks=discovered_tracks
    )

    # 4. Build Roadmap with full track data
    return Roadmap(
        ...
        tracks=merged_tracks,
    )
```

**Pros:**
- Backward compatible
- Supports mixed legacy/ULID
- roadmap.yaml remains for quick status

**Cons:**
- Two sources of truth
- Sync complexity

### Option 2: ULID-First Loading

Ignore `roadmap.yaml` tracks, load entirely from ULID files:

```python
def load_roadmap(file_path: Path) -> Roadmap:
    """Load roadmap from ULID files."""
    # 1. Load roadmap metadata only from roadmap.yaml
    roadmap_data = yaml.safe_load(file_path.read_text())

    # 2. Discover all tracks from tracks/*.yaml
    tracks_dir = file_path.parent / "tracks"
    tracks = []
    for track_file in tracks_dir.glob("*.yaml"):
        track = load_track(track_file)
        tracks.append(track)

    # 3. Build Roadmap (ignore tracks from roadmap.yaml)
    return Roadmap(
        id=roadmap_data['id'],
        name=roadmap_data['name'],
        ...
        tracks=[TrackSummary.from_track(t) for t in tracks],
    )
```

**Pros:**
- Single source of truth
- No sync issues
- ULID files are authoritative

**Cons:**
- Slower (must read all track files)
- roadmap.yaml becomes just metadata

### Option 3: Lazy Loading with Cache

```python
class LazyRoadmap:
    """Roadmap with lazy-loaded track details."""

    def __init__(self, roadmap_data, tracks_dir):
        self._roadmap_data = roadmap_data
        self._tracks_dir = tracks_dir
        self._track_cache: Dict[str, Track] = {}

    @property
    def tracks(self) -> List[TrackSummary]:
        """Return track summaries (from roadmap.yaml or discovered)."""
        # Fast: return summaries only
        ...

    def get_track(self, track_id: str) -> Track:
        """Load full track on demand."""
        if track_id not in self._track_cache:
            track_path = self._tracks_dir / f"{track_id}.yaml"
            self._track_cache[track_id] = load_track(track_path)
        return self._track_cache[track_id]
```

---

## Recommended Design

**Option 2: ULID-First Loading** with these specifics:

1. `roadmap.yaml` contains only:
   - Roadmap metadata (id, name, version, status)
   - Progress counters (tracks_total, tasks_completed, etc.)
   - No track list (or optional cache for display)

2. Track discovery from `tracks/*.yaml`:
   - Enumerate all files
   - Parse each to get TrackSummary
   - Full Track loaded on demand

3. Sprint/Task discovery follows hierarchy:
   - Sprint's `track_id` links to parent
   - Task's `sprint_id` links to parent

---

## Data Flow

```
CLI Command: vibey roadmap status
    │
    ▼
FileSystemManager.get_roadmap_path()
    │
    ▼
load_roadmap(roadmap_path)
    │
    ├──► Read .vibey/roadmap/roadmap.yaml (metadata only)
    │
    └──► discover_tracks_from_ulid_files()
         ├──► Enumerate tracks/*.yaml
         ├──► For each: extract TrackSummary (id, name, status)
         └──► Return List[TrackSummary]
    │
    ▼
Roadmap object with track summaries
    │
    ▼ (if detailed view requested)
load_track(track_id) for specific tracks
```

---

## Interface Changes

```python
# New function
def discover_tracks(tracks_dir: Path) -> List[TrackSummary]:
    """Discover track summaries from ULID files."""
    ...

# Modified function
def load_roadmap(file_path: Path, discover_tracks: bool = True) -> Roadmap:
    """Load roadmap with optional track discovery."""
    ...
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | Add track discovery |
| `vibey/cli/roadmap_lib/filesystem.py` | Track enumeration helpers |
| `vibey/operations/roadmap/query.py` | Use new loading strategy |

---

## Success Criteria

- [ ] Design document approved
- [ ] Interface changes defined
- [ ] Data flow documented
- [ ] Backward compatibility plan
- [ ] Migration strategy for existing code

---

## Dependencies

- Tasks 001-003 (path resolution)

---

## Notes

This is a **design task**. The output is a documented design that Tasks 005-008 will implement.

Document should cover:
1. Final architecture decision
2. Function signatures
3. Data structures
4. Error handling
5. Performance considerations
