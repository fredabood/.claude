# Task 011: Add Progress Reporting During Database Rebuild

**Task ID:** dogfooding-bugs-03-task-011
**Bug Addressed:** #11 (Database Rebuild Loads 0 Tracks/Sprints/Tasks)
**Complexity:** Low
**Type:** Enhancement

---

## Problem Statement

When `db_rebuild_cmd` runs, users see minimal feedback:

```
🔄 Rebuilding database from YAML...
   Backup created: .vibey/roadmap.db.bak
   Creating schema (25 tables)...
   Creating views (13 computed views)...
   Creating triggers (40 triggers)...
   Loading roadmap data from YAML...
   Loaded 0 tracks, 0 sprints, 0 tasks    <-- User sees this and wonders why

✅ Database rebuilt successfully
```

With the ULID fix (Tasks 009-010), we need better progress reporting so users understand what's happening, especially for large roadmaps (1000+ entities).

---

## Current Behavior

### No Progress During Loading

```python
# Current: Silent loading with final count only
for track_file in tracks_dir.glob("*.yaml"):
    track = load_track(track_file)
    db_create_track(...)
    loaded_tracks += 1

print(f"   Loaded {loaded_tracks} tracks, ...")
```

### Missing Information

- No indication of total expected entities
- No progress during long operations
- No breakdown by entity type during loading
- No timing information

---

## Implementation

### Progress Reporter Class

```python
# vibey/cli/progress.py

from typing import Optional
import sys
import time


class ProgressReporter:
    """Report progress during database operations."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.start_time = None
        self._last_update = 0

    def start_operation(self, operation: str):
        """Start a timed operation."""
        self.start_time = time.time()
        if self.verbose:
            print(f"   {operation}...")

    def update_count(self, entity_type: str, current: int, total: Optional[int] = None):
        """Update progress count (throttled to avoid spam)."""
        now = time.time()
        # Only update every 0.5 seconds
        if now - self._last_update < 0.5:
            return

        self._last_update = now

        if self.verbose:
            if total:
                pct = (current / total) * 100
                sys.stdout.write(f"\r      Loading {entity_type}: {current}/{total} ({pct:.0f}%)     ")
            else:
                sys.stdout.write(f"\r      Loading {entity_type}: {current}...     ")
            sys.stdout.flush()

    def complete_entity_type(self, entity_type: str, loaded: int, skipped: int = 0):
        """Mark an entity type as complete."""
        if self.verbose:
            # Clear progress line
            sys.stdout.write("\r" + " " * 60 + "\r")
            if skipped:
                print(f"      ✓ {entity_type}: {loaded} loaded, {skipped} skipped")
            else:
                print(f"      ✓ {entity_type}: {loaded} loaded")

    def complete_operation(self, success: bool = True):
        """Complete the operation with timing."""
        if self.start_time and self.verbose:
            elapsed = time.time() - self.start_time
            if elapsed > 1:
                print(f"      (took {elapsed:.1f}s)")

    def error(self, message: str):
        """Report an error."""
        print(f"      ❌ Error: {message}")

    def warning(self, message: str):
        """Report a warning."""
        print(f"      ⚠️  {message}")
```

### Updated db_rebuild Flow

```python
def _load_roadmap_to_db_ulid(conn, roadmap, vibey_dir: Path, verbose: bool = True):
    """Load roadmap data into database (ULID flat structure)."""
    from vibey.cli.progress import ProgressReporter

    progress = ProgressReporter(verbose=verbose)
    roadmap_dir = vibey_dir / "roadmap"

    # Count files first for progress reporting
    tracks_dir = roadmap_dir / "tracks"
    sprints_dir = roadmap_dir / "sprints"
    tasks_dir = roadmap_dir / "tasks"

    total_tracks = len(list(tracks_dir.glob("*.yaml"))) if tracks_dir.exists() else 0
    total_sprints = len(list(sprints_dir.glob("*.yaml"))) if sprints_dir.exists() else 0
    total_tasks = len(list(tasks_dir.glob("*.yaml"))) if tasks_dir.exists() else 0

    print(f"   Found {total_tracks} tracks, {total_sprints} sprints, {total_tasks} tasks")

    # Create roadmap record
    db_create_roadmap(...)

    # Load tracks with progress
    progress.start_operation("Loading tracks")
    loaded_tracks = 0
    skipped_tracks = 0

    if tracks_dir.exists():
        for i, track_file in enumerate(sorted(tracks_dir.glob("*.yaml"))):
            progress.update_count("tracks", i + 1, total_tracks)
            try:
                track = load_track(track_file)
                db_create_track(...)
                loaded_tracks += 1
            except Exception as e:
                skipped_tracks += 1

    progress.complete_entity_type("Tracks", loaded_tracks, skipped_tracks)

    # Load sprints with progress
    progress.start_operation("Loading sprints")
    loaded_sprints = 0
    skipped_sprints = 0

    if sprints_dir.exists():
        for i, sprint_file in enumerate(sorted(sprints_dir.glob("*.yaml"))):
            progress.update_count("sprints", i + 1, total_sprints)
            try:
                sprint = load_sprint(sprint_file)
                db_create_sprint(...)
                loaded_sprints += 1
            except Exception as e:
                skipped_sprints += 1

    progress.complete_entity_type("Sprints", loaded_sprints, skipped_sprints)

    # Load tasks with progress
    progress.start_operation("Loading tasks")
    loaded_tasks = 0
    skipped_tasks = 0

    if tasks_dir.exists():
        for i, task_file in enumerate(sorted(tasks_dir.glob("*.yaml"))):
            progress.update_count("tasks", i + 1, total_tasks)
            try:
                task = load_task(task_file)
                db_create_task(...)
                loaded_tasks += 1
            except Exception as e:
                skipped_tasks += 1

    progress.complete_entity_type("Tasks", loaded_tasks, skipped_tasks)
    progress.complete_operation()
```

### Expected Output

```
🔄 Rebuilding database from YAML...
   Backup created: .vibey/roadmap.db.bak
   Creating schema (25 tables)...
   Creating views (13 computed views)...
   Creating triggers (40 triggers)...
   Loading roadmap data from YAML...
   Found 39 tracks, 213 sprints, 1125 tasks
   Loading tracks...
      ✓ Tracks: 39 loaded
   Loading sprints...
      ✓ Sprints: 213 loaded
   Loading tasks...
      ✓ Tasks: 1125 loaded
      (took 2.3s)

✅ Database rebuilt successfully
   Schema version: 1.0.0
   Roadmaps: 1
   Tracks:   39
   Sprints:  213
   Tasks:    1125
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/cli/progress.py` | NEW: Progress reporter class |
| `vibey/cli/commands.py` | Use ProgressReporter in `_load_roadmap_to_db_ulid()` |

---

## CLI Flags

```python
@db.command()
@click.option('--verbose/--quiet', '-v/-q', default=True, help='Show progress')
@click.pass_context
def rebuild(ctx, verbose: bool):
    """Rebuild database from YAML files."""
    from vibey.cli.commands import db_rebuild_cmd
    ctx.exit(db_rebuild_cmd(verbose=verbose))
```

---

## Testing Strategy

```python
def test_progress_reporter_updates(capsys):
    """Progress reporter shows updates."""
    reporter = ProgressReporter(verbose=True)
    reporter.start_operation("Loading")
    reporter.update_count("items", 50, 100)
    reporter.complete_entity_type("Items", 100, 0)

    captured = capsys.readouterr()
    assert "Loading" in captured.out
    assert "Items: 100 loaded" in captured.out


def test_progress_reporter_quiet_mode(capsys):
    """Progress reporter respects quiet mode."""
    reporter = ProgressReporter(verbose=False)
    reporter.start_operation("Loading")
    reporter.complete_entity_type("Items", 100, 0)

    captured = capsys.readouterr()
    assert captured.out == ""


def test_db_rebuild_shows_progress(ulid_roadmap_environment, capsys):
    """db_rebuild shows progress during loading."""
    result = db_rebuild_cmd(force=True, verbose=True)

    captured = capsys.readouterr()
    assert "Found" in captured.out
    assert "tracks" in captured.out
    assert "sprints" in captured.out
    assert "tasks" in captured.out
```

---

## Success Criteria

- [ ] Progress shows expected entity counts before loading
- [ ] Progress updates during loading (throttled)
- [ ] Final summary shows loaded/skipped counts
- [ ] Timing information for slow operations
- [ ] `--quiet` flag suppresses progress output
- [ ] Works correctly in non-TTY environments

---

## Dependencies

- Tasks 009-010 (fix the 0 count issue first)

---

## Notes

Good progress reporting helps users:
1. Understand what's happening during long operations
2. Identify where issues occur (which entity type?)
3. Feel confident the tool is working
4. Debug validation errors (see skipped counts)

The throttling prevents console spam during fast operations while still showing progress for slow ones.
