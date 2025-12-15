# Task Plan: Sprint YAML shows tasks_total: 0 when tasks exist

## Bug ID
01KCC76RA9QWQPVYXMKBW28DWE

## Problem Statement
Sprint YAML file `progress.tasks_total` shows 0 even when task YAML files exist for the sprint. The database correctly counts tasks but YAML is out of sync.

## Root Cause Analysis
The sprint progress fields are computed/cached values that are not automatically updated when tasks are created. The database recomputes on load, but the YAML file retains stale values.

## Files to Modify

### Primary Files
1. `vibey/cli/commands.py` - create_task_cmd should update sprint progress
2. `vibey/operations/roadmap/update.py` - Progress update functions
3. `vibey/cli/roadmap-update.py` - Update sprint progress after task changes

## Implementation Steps

1. **Find where tasks are counted**
   ```bash
   grep -rn "tasks_total\|task.*count" vibey/operations/roadmap/
   ```

2. **Add progress update to task creation**
   ```python
   def create_task_cmd(...):
       # ... create task ...

       # Update parent sprint progress
       update_sprint_progress(root_dir, sprint_id)
   ```

3. **Implement progress update function**
   ```python
   def update_sprint_progress(root_dir: Path, sprint_id: str):
       """Update sprint progress from its tasks."""
       fs = FileSystemManager(root_dir)

       # Load sprint
       sprint_path = fs.roadmap_root / "sprints" / f"{sprint_id}.yaml"
       sprint = load_sprint(sprint_path)

       # Count tasks for this sprint
       tasks_dir = fs.roadmap_root / "tasks"
       total = 0
       completed = 0

       for task_file in tasks_dir.glob("*.yaml"):
           task = load_task(task_file)
           if task.sprint_id == sprint_id:
               total += 1
               if task.status == "completed":
                   completed += 1

       # Update sprint progress
       sprint.progress.tasks_total = total
       sprint.progress.tasks_completed = completed
       sprint.progress.completion_percent = (completed / total * 100) if total > 0 else 0

       # Save sprint
       save_sprint(sprint, sprint_path)
   ```

4. **Add to sync command**
   - `vibey roadmap sync` should update all sprint progress
   - Already exists but may need to be enhanced

5. **Trigger progress update on task status change**
   - After complete_task, update sprint progress
   - After start_task, no change needed (only counts completed)

## Test Requirements
- Create task in sprint - sprint tasks_total should increment
- Complete task - tasks_completed should increment
- Verify YAML and database values match

## Estimated Complexity
Medium - requires integration with task lifecycle
