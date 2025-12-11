# Task 002: Migrate YAMLBackend to Flat Structure

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXQ`
**Bug Addressed:** #19 (YAMLBackend creates hierarchical ULID directories)
**Complexity:** Medium
**Priority:** Critical (blocks other tasks)
**Type:** Development

## Problem Statement

The `YAMLBackend` class in `vibey/roadmap/serialization/backend.py` is the PRIMARY source of hierarchical ULID directory creation. Its `save_*()` methods create nested directories like:
```
.vibey/roadmap/{track_ulid}/track.yaml
.vibey/roadmap/{track_ulid}/{sprint_ulid}/sprint.yaml
```

Instead of the intended flat structure:
```
.vibey/roadmap/tracks/{ulid}.yaml
.vibey/roadmap/sprints/{ulid}.yaml
.vibey/roadmap/tasks/{ulid}.yaml
```

## Current State (from HIERARCHICAL_AUDIT.md)

| Line | Function | Pattern | Issue |
|------|----------|---------|-------|
| 160 | `load_track()` | `roadmap_dir / track_id / "track.yaml"` | Reads from hierarchical |
| 170-172 | `load_sprint()` | `track_dir / sprint_id / "sprint.yaml"` | Reads from hierarchical |
| 202-206 | `load_tasks_by_sprint()` | `track_dir / sprint_id` nested search | Hierarchical iteration |
| 212-220 | `load_tasks_by_track()` | nested `track_dir` iteration | Hierarchical iteration |
| 245 | `save_track()` | `roadmap_dir / track.id / "track.yaml"` | **CREATES ULID DIRS** |
| 253-255 | `save_sprint()` | `track_dir / sprint.id` mkdir | **CREATES NESTED DIRS** |
| 276-278 | `save_tasks()` | `track_id / sprint_id` mkdir | **CREATES NESTED DIRS** |

## Implementation Plan

### Step 1: Update save_track()
```python
# BEFORE (line 245):
def save_track(self, track: Track) -> None:
    save_track(track, self.roadmap_dir / track.id / "track.yaml")

# AFTER:
def save_track(self, track: Track) -> None:
    tracks_dir = self.roadmap_dir / "tracks"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    save_track(track, tracks_dir / f"{track.id}.yaml")
```

### Step 2: Update save_sprint()
```python
# BEFORE (lines 250-255):
def save_sprint(self, sprint: Sprint) -> None:
    track_dir = self.roadmap_dir / sprint.track_id
    sprint_dir = track_dir / sprint.id
    sprint_dir.mkdir(parents=True, exist_ok=True)
    save_sprint(sprint, sprint_dir / "sprint.yaml")

# AFTER:
def save_sprint(self, sprint: Sprint) -> None:
    sprints_dir = self.roadmap_dir / "sprints"
    sprints_dir.mkdir(parents=True, exist_ok=True)
    save_sprint(sprint, sprints_dir / f"{sprint.id}.yaml")
```

### Step 3: Update save_tasks()
```python
# BEFORE (lines 270-278):
def save_tasks(self, tasks: List[Task]) -> None:
    for sprint_id, sprint_tasks in grouped_tasks.items():
        track_id = sprint_tasks[0].track_id
        sprint_dir = self.roadmap_dir / track_id / sprint_id
        sprint_dir.mkdir(parents=True, exist_ok=True)
        save_tasks(sprint_tasks, sprint_dir)

# AFTER:
def save_tasks(self, tasks: List[Task]) -> None:
    tasks_dir = self.roadmap_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        save_task(task, tasks_dir / f"{task.id}.yaml")
```

### Step 4: Update load_track()
```python
# BEFORE (line 160):
def load_track(self, track_id: str) -> Track:
    return load_track(self.roadmap_dir / track_id / "track.yaml")

# AFTER:
def load_track(self, track_id: str) -> Track:
    return load_track(self.roadmap_dir / "tracks" / f"{track_id}.yaml")
```

### Step 5: Update load_sprint()
```python
# BEFORE (lines 168-172):
def load_sprint(self, track_id: str, sprint_id: str) -> Optional[Sprint]:
    track_dir = self.roadmap_dir / track_id
    sprint_dir = track_dir / sprint_id
    if sprint_dir.exists():
        return load_sprint(sprint_dir / "sprint.yaml")

# AFTER:
def load_sprint(self, track_id: str, sprint_id: str) -> Optional[Sprint]:
    sprint_path = self.roadmap_dir / "sprints" / f"{sprint_id}.yaml"
    if sprint_path.exists():
        return load_sprint(sprint_path)
```

### Step 6: Update load_tasks_by_sprint()
```python
# BEFORE (lines 194-206):
def load_tasks_by_sprint(self, track_id: str, sprint_id: str) -> List[Task]:
    track_dir = self.roadmap_dir / track_id
    sprint_dir = track_dir / sprint_id
    # ... iterates nested dirs

# AFTER:
def load_tasks_by_sprint(self, track_id: str, sprint_id: str) -> List[Task]:
    tasks_dir = self.roadmap_dir / "tasks"
    tasks = []
    for task_file in tasks_dir.glob("*.yaml"):
        task = load_task(task_file)
        if task.sprint_id == sprint_id:
            tasks.append(task)
    return tasks
```

### Step 7: Update load_tasks_by_track()
```python
# BEFORE (lines 208-220):
def load_tasks_by_track(self, track_id: str) -> List[Task]:
    track_dir = self.roadmap_dir / track_id
    # ... nested iteration

# AFTER:
def load_tasks_by_track(self, track_id: str) -> List[Task]:
    tasks_dir = self.roadmap_dir / "tasks"
    tasks = []
    for task_file in tasks_dir.glob("*.yaml"):
        task = load_task(task_file)
        if task.track_id == track_id:
            tasks.append(task)
    return tasks
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/backend.py` | Update 7 methods in YAMLBackend class |

## Testing

1. Run existing tests: `.venv/bin/pytest tests/roadmap/serialization/ -v`
2. Test `vibey roadmap db dump` - should create flat structure
3. Test `vibey roadmap db rebuild` - should read from flat structure
4. Verify no new `01KC*/` directories created

## Success Criteria

- [ ] `save_track()` writes to `tracks/{id}.yaml`
- [ ] `save_sprint()` writes to `sprints/{id}.yaml`
- [ ] `save_tasks()` writes to `tasks/{id}.yaml`
- [ ] `load_*()` methods read from flat structure
- [ ] No `mkdir` calls create nested ULID directories
- [ ] All existing tests pass

## Dependencies

- Task 001 (Audit): COMPLETE - provides line references
- Blocks: Tasks 003-006, 009-012
