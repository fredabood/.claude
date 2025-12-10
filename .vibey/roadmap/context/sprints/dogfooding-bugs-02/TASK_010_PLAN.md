# Task 010: Fix Track Filtering/Discovery Logic

**Task ID:** dogfooding-bugs-02-task-010
**Bug Addressed:** #2 (Tracks not showing in status)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

Track discovery/filtering logic has issues causing some tracks to be invisible in CLI output. Based on Bug #2, the unified-architecture-migration track is missing from `roadmap status`.

---

## Potential Root Causes

1. **Structure detection returning "nested"** when it should be "flat"
2. **Track filtering by status** (only showing certain statuses)
3. **Slug-to-ULID mapping missing** for newly created tracks
4. **Error during track file parsing** causing silent skip

---

## Implementation

### Fix 1: Robust Structure Detection

```python
def _detect_structure_format(self) -> Literal["flat", "nested"]:
    """
    Detect directory structure format.

    Flat structure: tracks/, sprints/, tasks/ directories with YAML files
    Nested structure: track subdirectories with sprint subdirectories
    """
    if not self.roadmap_root.exists():
        return "nested"  # Default for new projects

    # Check for flat structure markers
    tracks_dir = self.roadmap_root / "tracks"
    sprints_dir = self.roadmap_root / "sprints"

    # Flat structure if tracks/ contains YAML files
    if tracks_dir.exists():
        yaml_files = list(tracks_dir.glob("*.yaml"))
        if yaml_files:
            return "flat"

    # Flat structure if sprints/ contains YAML files
    if sprints_dir.exists():
        yaml_files = list(sprints_dir.glob("*.yaml"))
        if yaml_files:
            return "flat"

    return "nested"
```

### Fix 2: Improved list_tracks

```python
def list_tracks(self) -> list[str]:
    """
    List all track IDs.

    For flat structure: returns ULIDs from tracks/*.yaml filenames
    For nested structure: returns directory names (slugs)

    Returns:
        List of track IDs (ULIDs or slugs depending on structure)
    """
    if self.structure_format == "flat":
        tracks_dir = self.roadmap_root / "tracks"
        if not tracks_dir.exists():
            logger.warning(f"Tracks directory not found: {tracks_dir}")
            return []

        # Get all YAML files
        track_ids = []
        for track_file in tracks_dir.iterdir():
            # Skip non-files and hidden files
            if not track_file.is_file():
                continue
            if track_file.name.startswith('.'):
                continue
            if track_file.suffix != '.yaml':
                continue

            track_ids.append(track_file.stem)

        logger.debug(f"Discovered {len(track_ids)} tracks in flat structure")
        return track_ids

    else:
        # Nested structure
        track_ids = []
        for item in self.roadmap_root.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith('.'):
                continue
            if item.name in ('tracks', 'sprints', 'tasks', 'context', 'archived'):
                continue  # Skip flat structure dirs

            # Check if it's a track directory (has track.yaml)
            if (item / "track.yaml").exists():
                track_ids.append(item.name)

        logger.debug(f"Discovered {len(track_ids)} tracks in nested structure")
        return track_ids
```

### Fix 3: Add Error Handling for Track Loading

```python
def list_tracks_with_summaries(self) -> List[Tuple[str, str, str]]:
    """
    List tracks with their summaries.

    Returns:
        List of (id, name, status) tuples
    """
    summaries = []
    track_ids = self.list_tracks()

    for track_id in track_ids:
        try:
            track_path = self.get_track_path(track_id)
            with open(track_path, 'r') as f:
                data = yaml.safe_load(f)

            track_data = data.get('track', {})
            summaries.append((
                track_id,
                track_data.get('name', 'Unknown'),
                track_data.get('status', 'not_started'),
            ))
        except Exception as e:
            logger.warning(f"Failed to load track {track_id}: {e}")
            # Include track with error indicator
            summaries.append((track_id, f"ERROR: {e}", 'unknown'))

    return summaries
```

---

## Files to Modify

| File | Function | Changes |
|------|----------|---------|
| `vibey/cli/roadmap_lib/filesystem.py` | `_detect_structure_format()` | More robust detection |
| `vibey/cli/roadmap_lib/filesystem.py` | `list_tracks()` | Better filtering, logging |
| `vibey/cli/roadmap_lib/filesystem.py` | NEW: `list_tracks_with_summaries()` | Error-tolerant listing |

---

## Testing Strategy

```python
def test_list_tracks_finds_all_tracks(tmp_path):
    """All track files are discovered."""
    # Create 5 track files
    tracks_dir = tmp_path / ".vibey/roadmap/tracks"
    tracks_dir.mkdir(parents=True)
    (tmp_path / ".vibey/roadmap/sprints").mkdir()
    (tmp_path / ".vibey/roadmap/tasks").mkdir()

    for i in range(5):
        (tracks_dir / f"track_{i}.yaml").write_text(f"""
track:
  id: track_{i}
  name: Track {i}
""")

    fs = FileSystemManager(tmp_path)
    tracks = fs.list_tracks()

    assert len(tracks) == 5


def test_list_tracks_skips_hidden_files(tmp_path):
    """Hidden files are not included."""
    tracks_dir = tmp_path / ".vibey/roadmap/tracks"
    tracks_dir.mkdir(parents=True)
    (tmp_path / ".vibey/roadmap/sprints").mkdir()
    (tmp_path / ".vibey/roadmap/tasks").mkdir()

    (tracks_dir / "visible.yaml").write_text("track: {}")
    (tracks_dir / ".hidden.yaml").write_text("track: {}")
    (tracks_dir / ".id").write_text("mapping file")

    fs = FileSystemManager(tmp_path)
    tracks = fs.list_tracks()

    assert tracks == ["visible"]
```

---

## Success Criteria

- [ ] Structure detection is robust
- [ ] list_tracks() returns all 39 tracks
- [ ] Hidden files and non-YAML files are excluded
- [ ] Errors during loading are logged, not fatal
- [ ] unified-architecture-migration track appears in status

---

## Dependencies

- Task 009 (debugging complete, root cause known)

---

## Notes

This fix should be minimal and focused. The goal is to fix the immediate track discovery issue without refactoring the entire FileSystemManager.
