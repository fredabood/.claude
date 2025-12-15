# Task Plan: auto-progress --check shows UNKNOWN instead of track/sprint names

## Bug ID
01KC9J6NXBB3G748D5R67DFJYH

## Problem Statement
When running `vibey roadmap auto-progress --check`, the output shows 'UNKNOWN: <ULID>' instead of resolving the track/sprint name. The IDs are valid tracks but the display logic doesn't look up the name.

## Root Cause Analysis
The auto-progress command displays IDs but doesn't resolve them to human-readable names when the items are ULIDs.

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap_commands/progress.py` - Auto-progress command
2. `vibey/cli/roadmap_lib/formatting.py` - Display formatting helpers

## Implementation Steps

1. **Find auto-progress display logic**
   ```bash
   grep -n "UNKNOWN\|auto.*progress" vibey/cli/roadmap_commands/progress.py
   ```

2. **Add name resolution helper**
   ```python
   def resolve_item_name(root_dir: Path, item_id: str) -> str:
       """Resolve ULID to human-readable name."""
       fs = FileSystemManager(root_dir)

       # Try tasks
       task_path = fs.roadmap_root / "tasks" / f"{item_id}.yaml"
       if task_path.exists():
           task = load_task(task_path)
           return f"Task: {task.title}"

       # Try sprints
       sprint_path = fs.roadmap_root / "sprints" / f"{item_id}.yaml"
       if sprint_path.exists():
           sprint = load_sprint(sprint_path)
           return f"Sprint: {sprint.name}"

       # Try tracks
       track_path = fs.roadmap_root / "tracks" / f"{item_id}.yaml"
       if track_path.exists():
           track = load_track(track_path)
           return f"Track: {track.name}"

       return f"UNKNOWN: {item_id}"
   ```

3. **Update progress display**
   ```python
   def format_progress_item(root_dir: Path, item_id: str, progress: dict) -> str:
       name = resolve_item_name(root_dir, item_id)
       return f"{name} ({item_id[:8]}...): {progress['percent']}%"
   ```

4. **Cache name lookups for performance**
   - Build lookup dict on first access
   - Reuse for subsequent calls in same command

## Test Requirements
- `vibey roadmap auto-progress --check` - should show names
- Performance with 1000+ items - should be fast

## Estimated Complexity
Simple - add name lookup before display
