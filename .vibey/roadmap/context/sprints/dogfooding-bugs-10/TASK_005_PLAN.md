# Task 005: Migrate recalculator.py to Flat Structure

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXT`
**Bug Addressed:** #19
**Complexity:** Medium
**Priority:** Medium
**Type:** Development

## Problem Statement

`vibey/roadmap/recalculator.py` creates nested task directories when applying recalculation plans.

## Current State (from HIERARCHICAL_AUDIT.md)

| Line | Function | Pattern | Issue |
|------|----------|---------|-------|
| 363 | `apply_recalculation_plan()` | `task_dir.mkdir(parents=True)` | Creates nested dirs |
| 370 | `apply_recalculation_plan()` | `sprint_file = sprint_dir / "sprint.yaml"` | Reads from nested |

## Implementation Plan

### Step 1: Update task creation in apply_recalculation_plan()

```python
# BEFORE (lines 360-370):
def apply_recalculation_plan(plan, roadmap_dir):
    # ... when creating subtasks
    task_dir = sprint_dir / subtask.id
    task_dir.mkdir(parents=True, exist_ok=True)
    save_task(subtask, task_dir / "task.yaml")

    # Reading sprint
    sprint_file = sprint_dir / "sprint.yaml"

# AFTER:
def apply_recalculation_plan(plan, roadmap_dir):
    tasks_dir = roadmap_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # When creating subtasks
    save_task(subtask, tasks_dir / f"{subtask.id}.yaml")

    # Reading sprint
    sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### Step 2: Update any sprint reading patterns

Ensure all sprint file access uses flat path:
```python
sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
```

### Step 3: Update any track reading patterns

Ensure all track file access uses flat path:
```python
track_file = roadmap_dir / "tracks" / f"{track_id}.yaml"
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/recalculator.py` | Update task creation and file reading |

## Testing

1. Run recalculation with a test sprint
2. Verify new tasks created in `tasks/` directory
3. Verify no nested ULID directories created
4. Verify sprint updates work correctly

## Success Criteria

- [ ] `task_dir.mkdir()` pattern removed
- [ ] Tasks saved to `tasks/{id}.yaml`
- [ ] Sprint reading uses `sprints/{id}.yaml`
- [ ] No nested directories created during recalculation

## Dependencies

- Task 002 (YAMLBackend): Defines flat save patterns
