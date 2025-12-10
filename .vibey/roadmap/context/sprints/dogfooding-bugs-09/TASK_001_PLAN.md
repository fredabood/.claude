# Task 001: Fix update_sprint_progress for flat ULID structure

**Task ID:** dogfooding-bugs-09-task-001
**Bug Addressed:** #18 (update_sprint_progress does not work with flat ULID structure)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The `update_sprint_progress` function in `vibey/cli/roadmap-update.py` cannot load tasks for sprints when using the flat ULID directory structure.

**Current behavior:**
1. `update_sprint_progress(fs, sprint_id)` is called
2. `fs.get_tasks_path(sprint_id)` returns `.vibey/roadmap/tasks/` (entire directory)
3. `load_tasks(tasks_path)` tries to load from that directory
4. `load_tasks` expects nested structure (subdirectories with task.yaml) or a single file
5. For flat structure, it returns empty list because there are no task subdirectories

**Impact:**
- `vibey roadmap sync` doesn't recalculate sprint progress from task files
- Sprint progress stays stale after tasks are updated
- Bug #17 cascade fix doesn't work for flat structure

---

## Root Cause Analysis

**filesystem.py:296-299:**
```python
def get_tasks_path(self, sprint_id: str) -> Path:
    if self.structure_format == "flat":
        # In flat structure, all tasks are in tasks/ directory
        # Caller will need to filter by sprint_id  <-- THIS IS THE PROBLEM
        return self.roadmap_root / "tasks"
```

**roadmap-update.py:315-320:**
```python
tasks_path = fs.get_tasks_path(sprint_id)

if not tasks_path.exists():
    return

tasks = load_tasks(tasks_path)  # Returns [] for flat structure!
```

**yaml_loader.py:1360-1374:**
```python
def load_tasks(file_path):
    if file_path.is_dir():
        # Expects nested structure with task subdirectories
        for item in file_path.iterdir():
            if not item.is_dir():
                continue
            task_file = item / "task.yaml"
            # ... loads from subdirs
```

The issue: `load_tasks` doesn't know how to filter by sprint_id in flat structure.

---

## Solution

Add a `load_tasks_by_sprint_flat()` function to yaml_loader.py that:
1. Scans all YAML files in the flat tasks directory
2. Loads each task and checks if `sprint_id` matches
3. Returns only matching tasks

Then update `update_sprint_progress` to use this function for flat structure.

---

## Implementation

### 1. Add `load_tasks_by_sprint_flat` to yaml_loader.py

```python
def load_tasks_by_sprint_flat(tasks_dir: Path, sprint_id: str) -> List[Task]:
    """
    Load tasks for a specific sprint from flat ULID directory structure.

    In flat structure, all tasks are stored as individual YAML files in
    .vibey/roadmap/tasks/ with ULID filenames. This function scans all
    task files and returns those matching the given sprint_id.

    Args:
        tasks_dir: Path to tasks directory (.vibey/roadmap/tasks/)
        sprint_id: Sprint ID to filter by

    Returns:
        List of Task objects belonging to the sprint
    """
    if not tasks_dir.exists() or not tasks_dir.is_dir():
        return []

    tasks = []
    for task_file in tasks_dir.glob("*.yaml"):
        if task_file.name.startswith('.'):
            continue
        try:
            task = load_task(task_file)
            if task.sprint_id == sprint_id:
                tasks.append(task)
        except Exception:
            continue  # Skip malformed files

    return tasks
```

### 2. Update `update_sprint_progress` in roadmap-update.py

```python
def update_sprint_progress(fs: FileSystemManager, sprint_id: str):
    """Update sprint progress based on task completion."""
    sprint_path = fs.get_sprint_path(sprint_id)
    if not sprint_path.exists():
        return

    sprint = load_sprint(sprint_path)

    # Load tasks - handle both flat and nested structures
    if fs.structure_format == "flat":
        # Flat structure: query tasks by sprint_id
        from vibey.roadmap.serialization.yaml_loader import load_tasks_by_sprint_flat
        tasks_dir = fs.roadmap_root / "tasks"
        tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)
    else:
        # Nested structure: load from sprint directory
        tasks_path = fs.get_tasks_path(sprint_id)
        if not tasks_path.exists():
            return
        tasks = load_tasks(tasks_path)

    # ... rest of function unchanged
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/yaml_loader.py` | Add `load_tasks_by_sprint_flat()` function |
| `vibey/cli/roadmap-update.py` | Update `update_sprint_progress()` to use flat loader |

---

## Testing Strategy

### Manual Test
```bash
# 1. Create a task in flat structure
# 2. Mark task as complete via direct YAML edit
# 3. Run sync
vibey roadmap sync --verbose

# 4. Check sprint progress was updated
grep "tasks_completed" .vibey/roadmap/sprints/<sprint-id>.yaml

# 5. Verify it shows correct count
```

### Unit Test
```python
def test_load_tasks_by_sprint_flat(tmp_path):
    """Test loading tasks by sprint from flat structure."""
    from vibey.roadmap.serialization.yaml_loader import load_tasks_by_sprint_flat

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    # Create two tasks, one for target sprint
    (tasks_dir / "task1.yaml").write_text("""
task:
  id: TASK1
  sprint_id: SPRINT1
  title: Task 1
  status: completed
""")
    (tasks_dir / "task2.yaml").write_text("""
task:
  id: TASK2
  sprint_id: SPRINT2
  title: Task 2
  status: not_started
""")

    tasks = load_tasks_by_sprint_flat(tasks_dir, "SPRINT1")
    assert len(tasks) == 1
    assert tasks[0].id == "TASK1"
```

---

## Success Criteria

- [ ] `load_tasks_by_sprint_flat()` function added to yaml_loader.py
- [ ] `update_sprint_progress()` uses flat loader when structure is flat
- [ ] `vibey roadmap sync` correctly updates sprint progress for flat structure
- [ ] No regression for nested structure
- [ ] Manual test passes

---

## Dependencies

- Bug #17 fix (sync cascade) must be in place
- FileSystemManager must have `structure_format` attribute

---

## Notes

Alternative approaches considered:
1. **Use SQLite backend**: Already has `load_tasks_by_sprint()` but requires DB to be in sync
2. **Add sprint_id filter to load_tasks**: Would change API and affect other callers
3. **Add method to FileSystemManager**: Keeps logic in filesystem layer

The chosen approach (new function in yaml_loader) is cleanest because:
- Self-contained, doesn't affect other code
- Follows existing pattern (load_tasks, load_task, etc.)
- Can be unit tested independently
