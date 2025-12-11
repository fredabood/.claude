# Task 003: Migrate round_trip_validation.py to Flat Structure

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXR`
**Bug Addressed:** #19
**Complexity:** Medium
**Priority:** High
**Type:** Development

## Problem Statement

`vibey/roadmap/database/round_trip_validation.py` creates hierarchical ULID directories during database-to-YAML dump operations for validation purposes.

## Current State (from HIERARCHICAL_AUDIT.md)

| Line | Function | Pattern | Issue |
|------|----------|---------|-------|
| 135 | `dump_database_to_yaml()` | `output_dir.mkdir()` | OK - temp dir |
| 146 | `dump_database_to_yaml()` | `track_dir.mkdir()` | **CREATES ULID DIRS** |
| 149 | `dump_database_to_yaml()` | `save_track(track, track_dir / "track.yaml")` | Hierarchical path |
| 156-157 | `dump_database_to_yaml()` | `sprint_dir = track_dir / sprint_id; sprint_dir.mkdir()` | **NESTED DIRS** |
| 160 | `dump_database_to_yaml()` | `save_sprint(sprint, sprint_dir / "sprint.yaml")` | Hierarchical path |

## Implementation Plan

### Step 1: Update dump_database_to_yaml()

```python
# BEFORE (lines 140-170):
def dump_database_to_yaml(db: Session, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    tracks = db.query(TrackORM).all()
    for track_orm in tracks:
        track = orm_to_model(track_orm)
        track_dir = output_dir / track.id
        track_dir.mkdir(parents=True, exist_ok=True)
        save_track(track, track_dir / "track.yaml")

        sprints = db.query(SprintORM).filter_by(track_id=track.id).all()
        for sprint_orm in sprints:
            sprint = orm_to_model(sprint_orm)
            sprint_dir = track_dir / sprint.id
            sprint_dir.mkdir(parents=True, exist_ok=True)
            save_sprint(sprint, sprint_dir / "sprint.yaml")

            # ... tasks similar pattern

# AFTER:
def dump_database_to_yaml(db: Session, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create flat structure directories
    tracks_dir = output_dir / "tracks"
    sprints_dir = output_dir / "sprints"
    tasks_dir = output_dir / "tasks"
    tracks_dir.mkdir(exist_ok=True)
    sprints_dir.mkdir(exist_ok=True)
    tasks_dir.mkdir(exist_ok=True)

    # Dump tracks to flat structure
    tracks = db.query(TrackORM).all()
    for track_orm in tracks:
        track = orm_to_model(track_orm)
        save_track(track, tracks_dir / f"{track.id}.yaml")

    # Dump sprints to flat structure
    sprints = db.query(SprintORM).all()
    for sprint_orm in sprints:
        sprint = orm_to_model(sprint_orm)
        save_sprint(sprint, sprints_dir / f"{sprint.id}.yaml")

    # Dump tasks to flat structure
    tasks = db.query(TaskORM).all()
    for task_orm in tasks:
        task = orm_to_model(task_orm)
        save_task(task, tasks_dir / f"{task.id}.yaml")
```

### Step 2: Update compare_yaml_directories() if exists

The comparison function may need to compare flat structure directories instead of nested ones.

```python
# Update to compare:
# dir1/tracks/*.yaml vs dir2/tracks/*.yaml
# dir1/sprints/*.yaml vs dir2/sprints/*.yaml
# dir1/tasks/*.yaml vs dir2/tasks/*.yaml
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/database/round_trip_validation.py` | Update dump function and comparison |

## Testing

1. Run round-trip validation test manually
2. Verify dump creates flat structure in temp directory
3. Compare validates correctly with flat structure

## Success Criteria

- [ ] `dump_database_to_yaml()` creates `tracks/`, `sprints/`, `tasks/` subdirs
- [ ] No nested ULID directories created
- [ ] Round-trip validation still passes
- [ ] Comparison works with flat structure

## Dependencies

- Task 002 (YAMLBackend): Should be done first as it defines the save patterns
