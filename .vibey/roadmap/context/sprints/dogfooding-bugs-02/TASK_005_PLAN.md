# Task 005: Update load_roadmap to Discover Tracks from tracks/*.yaml

**Task ID:** dogfooding-bugs-02-task-005
**Bug Addressed:** #10 (Monolithic roadmap.yaml read instead of ULID files)
**Complexity:** High
**Type:** Development

---

## Problem Statement

`load_roadmap()` currently parses tracks from the `tracks` array in `roadmap.yaml`. This array only contains `TrackSummary` data, not full track information. Tracks created in the ULID system are invisible.

---

## Current Implementation

```python
# yaml_loader.py:624-810
def load_roadmap(file_path: Union[str, Path]) -> Roadmap:
    ...
    # Line 754-765: Parse tracks as TrackSummary
    tracks = [
        TrackSummary(
            id=t['id'],
            name=t['name'],
            status=Status(t.get('status', 'not_started')),
            priority=Priority(t.get('priority', 'medium')),
        )
        for t in roadmap_data.get('tracks', [])
    ]
```

---

## New Implementation

```python
def load_roadmap(file_path: Union[str, Path]) -> Roadmap:
    """
    Load a roadmap from YAML files.

    Uses ULID-first strategy:
    1. Load metadata from roadmap.yaml
    2. Discover tracks from tracks/*.yaml
    3. Merge any tracks listed in roadmap.yaml (backward compat)

    Args:
        file_path: Path to roadmap.yaml

    Returns:
        Roadmap object with discovered tracks
    """
    file_path = Path(file_path)
    roadmap_dir = file_path.parent

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'roadmap' not in data:
        raise ValueError("Missing 'roadmap' root key")

    roadmap_data = data['roadmap']

    # Discover tracks from ULID files
    tracks_dir = roadmap_dir / "tracks"
    discovered_tracks = _discover_track_summaries(tracks_dir)

    # Merge with roadmap.yaml tracks (for backward compatibility)
    yaml_tracks = roadmap_data.get('tracks', [])
    merged_tracks = _merge_track_sources(discovered_tracks, yaml_tracks)

    # ... rest of roadmap construction with merged_tracks
```

### Helper Functions

```python
def _discover_track_summaries(tracks_dir: Path) -> List[TrackSummary]:
    """
    Discover track summaries from tracks/*.yaml files.

    Args:
        tracks_dir: Path to tracks/ directory

    Returns:
        List of TrackSummary from ULID files
    """
    if not tracks_dir.exists():
        return []

    summaries = []
    for track_file in tracks_dir.glob("*.yaml"):
        try:
            with open(track_file, 'r') as f:
                data = yaml.safe_load(f)

            track_data = data.get('track', {})
            summary = TrackSummary(
                id=track_data.get('id', track_file.stem),
                name=track_data.get('name', ''),
                status=Status(track_data.get('status', 'not_started')),
                priority=Priority(track_data.get('priority', 'medium')),
            )
            summaries.append(summary)
        except Exception as e:
            logger.warning(f"Failed to load track {track_file}: {e}")

    return summaries


def _merge_track_sources(
    discovered: List[TrackSummary],
    yaml_tracks: List[Dict[str, Any]]
) -> List[TrackSummary]:
    """
    Merge track sources with ULID files taking priority.

    Args:
        discovered: Tracks from ULID files
        yaml_tracks: Tracks from roadmap.yaml

    Returns:
        Merged list (discovered + any yaml-only tracks)
    """
    # Build set of discovered IDs
    discovered_ids = {t.id for t in discovered}

    # Start with discovered tracks (source of truth)
    merged = list(discovered)

    # Add any tracks from YAML that weren't discovered
    # (handles nested structure or pre-migration state)
    for t in yaml_tracks:
        track_id = t.get('id')
        if track_id and track_id not in discovered_ids:
            merged.append(TrackSummary(
                id=track_id,
                name=t.get('name', ''),
                status=Status(t.get('status', 'not_started')),
                priority=Priority(t.get('priority', 'medium')),
            ))

    return merged
```

---

## Files to Modify

| File | Function | Changes |
|------|----------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | `load_roadmap()` | Add track discovery |
| `vibey/roadmap/serialization/yaml_loader.py` | NEW: `_discover_track_summaries()` | Add helper |
| `vibey/roadmap/serialization/yaml_loader.py` | NEW: `_merge_track_sources()` | Add helper |

---

## Testing Strategy

```python
def test_load_roadmap_discovers_tracks(tmp_path):
    """Roadmap loads tracks from ULID files."""
    # Setup
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)
    tracks_dir = roadmap_dir / "tracks"
    tracks_dir.mkdir()

    # Create roadmap.yaml with no tracks
    (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test
  version: 1.0.0
  status: in_progress
  tracks: []
""")

    # Create track file
    (tracks_dir / "01KC2D0JKTE7Z4HCNHST8ZVW4R.yaml").write_text("""
track:
  id: 01KC2D0JKTE7Z4HCNHST8ZVW4R
  name: Discovered Track
  status: in_progress
  priority: high
""")

    # Load roadmap
    roadmap = load_roadmap(roadmap_dir / "roadmap.yaml")

    # Verify track was discovered
    assert len(roadmap.tracks) == 1
    assert roadmap.tracks[0].id == "01KC2D0JKTE7Z4HCNHST8ZVW4R"
    assert roadmap.tracks[0].name == "Discovered Track"
```

---

## Success Criteria

- [ ] `load_roadmap()` discovers tracks from `tracks/*.yaml`
- [ ] Tracks in ULID files appear in roadmap.tracks
- [ ] unified-architecture-migration track now visible
- [ ] Backward compatible with nested structure
- [ ] All 39 tracks visible in `roadmap status`

---

## Dependencies

- Task 004 (design complete)

---

## Notes

This is the core fix for Bug #10. After this task:
- ULID files are the source of truth for track data
- roadmap.yaml becomes a cache/index
- New tracks automatically appear
