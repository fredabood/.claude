# Task Plan: Legacy task files with slug sprint_ids not cleaned during flat migration

## Bug ID
01KCC75KMNZ9C2NZZQBQ7PX2QV

## Problem Statement
21 task YAML files had legacy slug sprint_ids (e.g., user-journey-audit-43) instead of ULIDs. These caused database to have duplicate tasks with mismatched sprint references.

## Root Cause Analysis
During migration to flat directory structure, some task files were not updated to use ULID sprint_ids. The old slug-based sprint_ids don't resolve correctly in the new structure.

## Files to Modify

### Primary Files
1. `vibey/operations/roadmap/migration.py` - Migration logic
2. Create one-time cleanup script

## Implementation Steps

1. **Identify affected files**
   ```bash
   grep -rn "sprint_id:.*-" .vibey/roadmap/tasks/ | grep -v "01K"
   ```

2. **Create sprint_id resolution map**
   ```python
   def build_sprint_id_map(root_dir: Path) -> dict[str, str]:
       """Map legacy sprint slugs to ULIDs."""
       id_file = root_dir / ".vibey/roadmap/sprints/.id"
       mapping = {}
       if id_file.exists():
           for line in id_file.read_text().strip().split("\n"):
               if "=" in line:
                   slug, ulid = line.split("=", 1)
                   mapping[slug] = ulid
       return mapping
   ```

3. **Create cleanup script**
   ```python
   def fix_legacy_sprint_ids(root_dir: Path):
       """Fix task files with legacy sprint_ids."""
       mapping = build_sprint_id_map(root_dir)
       tasks_dir = root_dir / ".vibey/roadmap/tasks"

       for task_file in tasks_dir.glob("*.yaml"):
           task = load_task(task_file)

           # Check if sprint_id is legacy format
           if task.sprint_id and "-" in task.sprint_id and not task.sprint_id.startswith("01K"):
               if task.sprint_id in mapping:
                   task.sprint_id = mapping[task.sprint_id]
                   save_task(task, task_file)
                   print(f"Fixed: {task_file.name}")
               else:
                   print(f"Warning: No mapping for {task.sprint_id} in {task_file.name}")
   ```

4. **Add to migration validation**
   - After migration, check all sprint_ids are ULIDs
   - Report any that weren't converted

5. **Clean up duplicates**
   - Identify duplicate tasks (same content, different IDs)
   - Remove legacy duplicates, keep ULID version

## Test Requirements
- Run cleanup - should fix all legacy sprint_ids
- Verify no duplicate tasks in database after rebuild
- All task sprint_ids should be ULIDs

## Estimated Complexity
Simple - one-time data cleanup
