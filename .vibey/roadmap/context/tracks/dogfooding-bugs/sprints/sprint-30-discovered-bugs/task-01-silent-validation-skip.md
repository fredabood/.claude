# Task 01: Database Rebuild Silently Skips Tasks with Validation Errors

## Bug Description

When `vibey roadmap db rebuild` encounters a YAML file that fails validation, it silently skips the file without reporting an error. This causes YAML/DB count mismatches that are difficult to diagnose.

## Impact

- 25 tasks were silently skipped during rebuilds
- No error messages or warnings shown to user
- User unaware of data loss
- Debugging requires manual file-by-file testing

## Current Behavior

```bash
$ vibey roadmap db rebuild
Rebuilding database...
✅ Database rebuilt successfully
   Tracks: 40, Sprints: 220, Tasks: 1787
```

No indication that 25 tasks failed to load.

## Expected Behavior

```bash
$ vibey roadmap db rebuild
Rebuilding database...
⚠️  3 files failed to load:
   - tasks/01KC2D0JK325ABWVR9FQD5ZNQY.yaml: ValueError: Completion date must be after start date
   - tasks/01KD99P0CK180MYKD4DRP72NM3.yaml: KeyError: 'required_status'
   - tasks/01KD99P0CK180MYKD4DRP72NM4.yaml: KeyError: 'required_status'

✅ Database rebuilt with warnings
   Tracks: 40, Sprints: 220, Tasks: 1787 (3 skipped)

See .vibey/roadmap/rebuild-errors.log for details
```

## Implementation Plan

### Step 1: Add Error Collection

**File**: `vibey/operations/roadmap/db_rebuild.py` (or equivalent)

```python
class RebuildResult:
    def __init__(self):
        self.tracks_loaded = 0
        self.sprints_loaded = 0
        self.tasks_loaded = 0
        self.errors: List[Tuple[str, Exception]] = []

    def add_error(self, file_path: str, error: Exception):
        self.errors.append((file_path, error))

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
```

### Step 2: Wrap File Loading with Error Handling

```python
def load_tasks_from_yaml(task_dir: Path, result: RebuildResult) -> List[Task]:
    tasks = []
    for yaml_file in task_dir.glob("*.yaml"):
        try:
            task = load_task(yaml_file)
            tasks.append(task)
            result.tasks_loaded += 1
        except Exception as e:
            result.add_error(str(yaml_file), e)
    return tasks
```

### Step 3: Add CLI Flags

**File**: `vibey/cli/commands.py`

```python
@roadmap_db.command("rebuild")
@click.option("--strict", is_flag=True, help="Abort on first error")
@click.option("--verbose", is_flag=True, help="Show each file processed")
@click.option("--report", type=click.Path(), help="Write error report to file")
def rebuild(strict: bool, verbose: bool, report: str):
    ...
```

### Step 4: Display Error Summary

```python
def display_rebuild_result(result: RebuildResult):
    if result.has_errors:
        click.echo(f"⚠️  {len(result.errors)} files failed to load:")
        for file_path, error in result.errors[:10]:  # Show first 10
            click.echo(f"   - {Path(file_path).name}: {type(error).__name__}: {error}")
        if len(result.errors) > 10:
            click.echo(f"   ... and {len(result.errors) - 10} more")
```

### Step 5: Write Error Log

```python
def write_error_log(result: RebuildResult, log_path: Path):
    with open(log_path, "w") as f:
        f.write(f"# Rebuild Error Log - {datetime.now().isoformat()}\n\n")
        for file_path, error in result.errors:
            f.write(f"## {file_path}\n")
            f.write(f"Error: {type(error).__name__}: {error}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n\n")
```

## Test Cases

1. **Normal rebuild** - All files load, no warnings
2. **File with validation error** - Error reported, file skipped, rebuild continues
3. **--strict flag** - Abort on first error with exit code 1
4. **--verbose flag** - Show each file as it's processed
5. **--report flag** - Write detailed error log to specified path
6. **Multiple errors** - All errors collected and summarized

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/db_rebuild.py` | Add RebuildResult class, error collection |
| `vibey/cli/commands.py` | Add --strict, --verbose, --report flags |
| `vibey/roadmap/serialization/yaml_loader.py` | Ensure exceptions bubble up cleanly |

## Acceptance Criteria

- [ ] Rebuild reports count of files that failed to load
- [ ] Each error shows filename and error message
- [ ] --strict flag aborts on first error
- [ ] --verbose flag shows progress
- [ ] Error log written to .vibey/roadmap/rebuild-errors.log
- [ ] Exit code 0 for success, 1 for errors (unless --strict)
