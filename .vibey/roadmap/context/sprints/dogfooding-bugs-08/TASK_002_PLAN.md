# Task 002: Fix sync command to update sprint/track progress

**Task ID:** dogfooding-bugs-08-task-002
**Bug Addressed:** #17 (sync command does not update sprint/track progress)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The `vibey roadmap sync` command only updates `roadmap.yaml` with aggregated progress from track files, but does NOT recalculate sprint or track progress from their underlying files.

When individual tasks are marked complete (directly in task files), the sprint and track files retain stale progress counts. The sync command just propagates these stale counts to `roadmap.yaml`.

---

## Root Cause

In `vibey/operations/roadmap/update.py:_update_roadmap_progress()`:

```python
for track_summary in roadmap.tracks:
    track_path = fs.get_track_path(track_summary.id)
    if track_path.exists():
        track = load_track(track_path)
        # Just READS track progress, doesn't recalculate from sprints
        total_tasks += track.progress.tasks_total
        completed_tasks += track.progress.tasks_completed
```

Missing: Cascade recalculation from task files → sprint files → track files → roadmap.yaml

---

## Fix

The sync command should:
1. For each sprint: recalculate progress from task files
2. For each track: recalculate progress from sprint files
3. Then update roadmap.yaml from track files

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands.py` | Update `roadmap_sync_cmd()` to cascade updates |
| `vibey/operations/roadmap/update.py` | Add `sync_all_progress()` function |

---

## Implementation

### Option A: Add cascade to `roadmap_sync_cmd()`

```python
def roadmap_sync_cmd(verbose: bool = False) -> int:
    """Sync status from individual files to main roadmap.yaml."""
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager
    from vibey.operations.roadmap.update import (
        _update_roadmap_progress,
        update_sprint_progress,
        update_track_progress,
    )
    from vibey.roadmap.serialization.yaml_loader import load_roadmap, load_track

    fs = FileSystemManager(root_dir)
    roadmap_path = fs.get_roadmap_path()
    roadmap = load_roadmap(roadmap_path)

    print("🔄 Syncing roadmap status...")

    # Step 1: Update each sprint's progress from task files
    for track_summary in roadmap.tracks:
        track_path = fs.get_track_path(track_summary.id)
        if not track_path.exists():
            continue
        track = load_track(track_path)
        for sprint_summary in track.sprints:
            if verbose:
                print(f"  Updating sprint: {sprint_summary.id}")
            update_sprint_progress(fs, sprint_summary.id)

    # Step 2: Update each track's progress from sprint files
    for track_summary in roadmap.tracks:
        if verbose:
            print(f"  Updating track: {track_summary.id}")
        update_track_progress(fs, track_summary.id)

    # Step 3: Update roadmap progress from track files
    _update_roadmap_progress(fs)

    print("✅ Roadmap synced successfully")
    return 0
```

### Check if `update_track_progress` exists

If not, create it following the pattern of `update_sprint_progress`:

```python
def update_track_progress(fs: FileSystemManager, track_id: str):
    """Update track progress based on sprint completion."""
    track_path = fs.get_track_path(track_id)
    if not track_path.exists():
        return

    track = load_track(track_path)

    # Recalculate from sprints
    total_sprints = len(track.sprints)
    completed_sprints = 0
    total_tasks = 0
    completed_tasks = 0

    for sprint_summary in track.sprints:
        sprint_path = fs.get_sprint_path(sprint_summary.id)
        if sprint_path.exists():
            sprint = load_sprint(sprint_path)
            if sprint.status in [Status.COMPLETED, Status.PRODUCTION_READY]:
                completed_sprints += 1
            total_tasks += sprint.progress.tasks_total
            completed_tasks += sprint.progress.tasks_completed
            # Also update embedded sprint status
            sprint_summary.status = sprint.status

    completion_percent = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    track.progress.sprints_total = total_sprints
    track.progress.sprints_completed = completed_sprints
    track.progress.tasks_total = total_tasks
    track.progress.tasks_completed = completed_tasks
    track.progress.completion_percent = completion_percent

    # Auto-update track status if all sprints complete
    if completed_sprints == total_sprints and total_sprints > 0:
        if track.status not in [Status.COMPLETED, Status.PRODUCTION_READY, Status.DEPLOYED]:
            track.status = Status.COMPLETED
            track.completed = datetime.now(timezone.utc)

    save_track(track, track_path)
```

---

## Testing

```bash
# 1. Manually mark a task complete in task file
# 2. Run sync
vibey roadmap sync --verbose

# 3. Check sprint file has updated progress
grep "tasks_completed" .vibey/roadmap/sprints/<sprint-id>.yaml

# 4. Check track file has updated progress
grep "tasks_completed" .vibey/roadmap/tracks/<track-id>.yaml
```

---

## Success Criteria

- [ ] `vibey roadmap sync` updates sprint progress from task files
- [ ] `vibey roadmap sync` updates track progress from sprint files
- [ ] `vibey roadmap sync` updates roadmap progress from track files
- [ ] Status cascades correctly (all tasks complete → sprint complete → track complete)
- [ ] --verbose flag shows what's being updated
