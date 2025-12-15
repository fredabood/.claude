# Task Plan: Date validation errors silently skip tasks during db rebuild

## Bug ID
01KCCJ5D4KN02GX20FGF19AV6Y

## Problem Statement
Tasks with invalid date relationships (started > completed, started < created) are silently skipped during `vibey roadmap db rebuild`.

Issues found:
1. Task with started date after completed date
2. Task with started date before created date
3. Tasks with status: completed but started/completed both null

## Root Cause Analysis
The YAML loader or SQL loader has validation that rejects invalid date combinations, but the error is caught and the task is skipped without user notification.

## Files to Modify

### Primary Files
1. `vibey/roadmap/serialization/yaml_loader.py` - YAML loading with validation
2. `vibey/roadmap/serialization/sql_loader.py` - SQL loading with validation
3. `vibey/cli/commands.py` - db_rebuild_cmd error handling

## Implementation Steps

1. **Find validation that causes silent skip**
   ```bash
   grep -rn "skip\|continue\|except.*pass" vibey/roadmap/serialization/
   ```

2. **Add verbose error collection**
   ```python
   class LoaderResult:
       def __init__(self):
           self.loaded_items = []
           self.skipped_items = []
           self.errors = []

   def load_tasks_with_errors(directory: Path) -> LoaderResult:
       result = LoaderResult()
       for file in directory.glob("*.yaml"):
           try:
               task = load_task(file)
               result.loaded_items.append(task)
           except ValidationError as e:
               result.errors.append({
                   "file": str(file),
                   "error": str(e)
               })
               result.skipped_items.append(file.stem)
       return result
   ```

3. **Update db rebuild to report errors**
   ```python
   def db_rebuild_cmd():
       result = load_all_with_errors(root_dir)

       if result.errors:
           click.echo(f"⚠️  {len(result.errors)} items skipped due to errors:")
           for error in result.errors:
               click.echo(f"  - {error['file']}: {error['error']}")

       click.echo(f"✅ Loaded {len(result.loaded_items)} items")
   ```

4. **Add auto-fix option**
   ```python
   @click.option('--fix-dates', is_flag=True, help='Auto-fix invalid dates')
   def db_rebuild(fix_dates):
       if fix_dates:
           # Set completed date to now for completed tasks with null dates
           # Set started <= completed for invalid relationships
   ```

5. **Define date fix strategies**
   - `completed` is null but status is completed → set to now
   - `started` > `completed` → set started = completed
   - `started` < `created` → set started = created

## Test Requirements
- Rebuild with invalid date task - should report error clearly
- `--fix-dates` should auto-correct and report fixes
- Valid tasks should load normally

## Estimated Complexity
Medium - requires error collection and optional auto-fix
