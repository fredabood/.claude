# Task 012: Implement Sync Mechanism ULID Files to roadmap.yaml

**Task ID:** dogfooding-bugs-02-task-012
**Bug Addressed:** #12 (New tracks not syncing to roadmap.yaml)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

Tracks created in the ULID flat structure are not automatically synced to `roadmap.yaml`. This causes the monolithic file to have stale data (37 tracks when there are 39).

---

## Design

### Sync Strategy

1. **ULID files are source of truth** for track data
2. **roadmap.yaml is a cache/index** for quick status display
3. **Sync updates roadmap.yaml** from ULID files

### Sync Operations

1. **Discover**: Find all tracks in `tracks/*.yaml`
2. **Compare**: Check against `roadmap.yaml` tracks list
3. **Update**: Add missing, update changed, optionally remove deleted

---

## Implementation

### Core Sync Function

```python
# vibey/operations/roadmap/sync.py

from pathlib import Path
from typing import List, Dict, Any, Tuple
import yaml
import logging

logger = logging.getLogger(__name__)


def sync_roadmap_yaml(roadmap_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Sync roadmap.yaml with ULID track files.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        dry_run: If True, report changes without applying

    Returns:
        Sync report with added, updated, removed tracks
    """
    roadmap_path = roadmap_dir / "roadmap.yaml"
    tracks_dir = roadmap_dir / "tracks"

    # Load current roadmap.yaml
    with open(roadmap_path, 'r') as f:
        data = yaml.safe_load(f)

    roadmap_data = data['roadmap']
    yaml_tracks = {t['id']: t for t in roadmap_data.get('tracks', [])}

    # Discover ULID tracks
    ulid_tracks = {}
    for track_file in tracks_dir.glob("*.yaml"):
        try:
            with open(track_file, 'r') as f:
                track_data = yaml.safe_load(f)

            track_info = track_data.get('track', {})
            track_id = track_info.get('id', track_file.stem)
            ulid_tracks[track_id] = {
                'id': track_id,
                'name': track_info.get('name', ''),
                'status': track_info.get('status', 'not_started'),
                'priority': track_info.get('priority', 'medium'),
            }
        except Exception as e:
            logger.warning(f"Failed to read {track_file}: {e}")

    # Calculate diff
    added = []
    updated = []
    removed = []

    # Find added and updated
    for track_id, track_info in ulid_tracks.items():
        if track_id not in yaml_tracks:
            added.append(track_info)
        elif _track_changed(yaml_tracks[track_id], track_info):
            updated.append(track_info)

    # Find removed (in yaml but not in ULID)
    for track_id in yaml_tracks:
        if track_id not in ulid_tracks:
            removed.append(yaml_tracks[track_id])

    report = {
        'added': added,
        'updated': updated,
        'removed': removed,
        'total_ulid': len(ulid_tracks),
        'total_yaml': len(yaml_tracks),
    }

    if dry_run:
        return report

    # Apply changes
    new_tracks = []

    # Add all ULID tracks (source of truth)
    for track_id, track_info in sorted(ulid_tracks.items(), key=lambda x: x[1]['name']):
        new_tracks.append(track_info)

    roadmap_data['tracks'] = new_tracks

    # Update progress counters
    roadmap_data['progress'] = roadmap_data.get('progress', {})
    roadmap_data['progress']['tracks_total'] = len(new_tracks)

    # Write back
    with open(roadmap_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Synced roadmap.yaml: +{len(added)} -{len(removed)} ~{len(updated)}")

    return report


def _track_changed(yaml_track: Dict, ulid_track: Dict) -> bool:
    """Check if track data has changed."""
    for key in ['name', 'status', 'priority']:
        if yaml_track.get(key) != ulid_track.get(key):
            return True
    return False
```

### Progress Sync

```python
def sync_progress_counters(roadmap_dir: Path) -> Dict[str, int]:
    """
    Recalculate and sync progress counters.

    Counts tracks, sprints, tasks from ULID files and updates roadmap.yaml.
    """
    roadmap_path = roadmap_dir / "roadmap.yaml"

    # Count from ULID files
    tracks = list((roadmap_dir / "tracks").glob("*.yaml"))
    sprints = list((roadmap_dir / "sprints").glob("*.yaml"))
    tasks = list((roadmap_dir / "tasks").glob("*.yaml"))

    # Count completed
    def count_completed(files: List[Path], status_key: str = 'status') -> int:
        completed = 0
        for f in files:
            try:
                data = yaml.safe_load(f.read_text())
                root_key = list(data.keys())[0]  # 'track', 'sprint', or 'task'
                if data[root_key].get(status_key) == 'completed':
                    completed += 1
            except:
                pass
        return completed

    tracks_completed = count_completed(tracks)
    sprints_completed = count_completed(sprints)
    tasks_completed = count_completed(tasks)

    progress = {
        'tracks_total': len(tracks),
        'tracks_completed': tracks_completed,
        'sprints_total': len(sprints),
        'sprints_completed': sprints_completed,
        'tasks_total': len(tasks),
        'tasks_completed': tasks_completed,
        'completion_percent': round(tasks_completed / len(tasks) * 100, 1) if tasks else 0,
    }

    # Update roadmap.yaml
    with open(roadmap_path, 'r') as f:
        data = yaml.safe_load(f)

    data['roadmap']['progress'] = progress

    with open(roadmap_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return progress
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/sync.py` | NEW: Sync functions |
| `vibey/operations/roadmap/__init__.py` | Export sync functions |

---

## Testing Strategy

```python
def test_sync_adds_new_tracks(tmp_path):
    """New tracks in ULID files are added to roadmap.yaml."""
    # Setup with 2 tracks in ULID, 1 in roadmap.yaml
    ...

    report = sync_roadmap_yaml(tmp_path / ".vibey/roadmap")

    assert len(report['added']) == 1


def test_sync_updates_changed_tracks(tmp_path):
    """Changed tracks are updated in roadmap.yaml."""
    # Setup with track having different status
    ...

    report = sync_roadmap_yaml(tmp_path / ".vibey/roadmap")

    assert len(report['updated']) == 1


def test_sync_dry_run_no_changes(tmp_path):
    """Dry run reports changes without applying."""
    ...

    report = sync_roadmap_yaml(tmp_path / ".vibey/roadmap", dry_run=True)

    # Verify roadmap.yaml unchanged
```

---

## Success Criteria

- [ ] `sync_roadmap_yaml()` syncs tracks from ULID files
- [ ] Progress counters are updated
- [ ] Dry run mode works
- [ ] unified-architecture-migration appears after sync
- [ ] Existing tracks not duplicated

---

## Dependencies

- Tasks 005-008 (ULID loading works)

---

## Notes

This sync mechanism is one-way: ULID → roadmap.yaml. The ULID files are always the source of truth.

In the future, consider:
- Automatic sync on file changes (file watcher)
- Git hook to sync before commit
- CLI command to trigger sync
