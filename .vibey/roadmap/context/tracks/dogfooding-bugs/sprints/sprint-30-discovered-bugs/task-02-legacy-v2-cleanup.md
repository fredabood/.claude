# Task 02: Orphaned Legacy v2 Format YAML Not Cleaned Up During Migrations

## Bug Description

Task file `01KC2D0JK325ABWVR9FQD5ZNQY` existed in `.vibey/roadmap/tasks/` using the old v2 YAML format with `parent_ref` instead of `sprint_id`. This file was not cleaned up during the migration to the flat structure.

## Impact

- File failed to load with `ValueError: Completion date must be after start date`
- Also used legacy field names: `name` instead of `title`, `created_at` instead of `created`
- Orphaned file caused db rebuild to silently skip (compounded by Task 01)
- Migration to flat structure didn't validate or clean up invalid legacy files

## Legacy v2 Format (Old)

```yaml
task:
  id: 01KC2D0JK325ABWVR9FQD5ZNQY
  parent_ref: sprint/some-slug        # OLD: should be sprint_id
  name: Some Task Name                # OLD: should be title
  created_at: 2025-12-11T00:00:00Z   # OLD: should be created
  started_at: 2025-12-24T00:00:00Z   # OLD: should be started
  completed_at: 2025-12-11T00:00:00Z # OLD: should be completed (also invalid date order!)
```

## Current v3 Format (Expected)

```yaml
task:
  id: 01KC2D0JK325ABWVR9FQD5ZNQY
  sprint_id: 01KC2D0JKVT80AFQ6C1PA8CKJD   # ULID reference
  track_id: 01KC39XSXJ39N12HWJ93F77KQ9    # ULID reference
  roadmap_id: vibey-framework-v2
  title: Some Task Name
  created: '2025-12-11T00:00:00+00:00'
  started: '2025-12-24T00:00:00+00:00'
  completed: '2025-12-25T00:00:00+00:00'
```

## Implementation Plan

### Step 1: Create Format Detection Utility

**File**: `vibey/roadmap/serialization/format_detector.py`

```python
from enum import Enum
from pathlib import Path
import yaml

class YAMLFormat(Enum):
    V2_LEGACY = "v2_legacy"      # Uses parent_ref, name, created_at
    V3_CURRENT = "v3_current"    # Uses sprint_id, title, created
    UNKNOWN = "unknown"

def detect_task_format(yaml_path: Path) -> YAMLFormat:
    """Detect the format version of a task YAML file."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    task = data.get("task", {})

    # Check for v2 legacy markers
    if "parent_ref" in task or "name" in task or "created_at" in task:
        return YAMLFormat.V2_LEGACY

    # Check for v3 current markers
    if "sprint_id" in task and "title" in task and "created" in task:
        return YAMLFormat.V3_CURRENT

    return YAMLFormat.UNKNOWN
```

### Step 2: Add Legacy Detection to DB Rebuild

**File**: `vibey/operations/roadmap/db_rebuild.py`

```python
def scan_for_legacy_files(roadmap_dir: Path) -> List[Tuple[Path, YAMLFormat]]:
    """Scan for legacy format files that need migration or cleanup."""
    legacy_files = []

    for yaml_file in roadmap_dir.glob("tasks/*.yaml"):
        format_version = detect_task_format(yaml_file)
        if format_version == YAMLFormat.V2_LEGACY:
            legacy_files.append((yaml_file, format_version))

    return legacy_files
```

### Step 3: Add CLI Command for Legacy Cleanup

**File**: `vibey/cli/commands.py`

```python
@roadmap_db.command("cleanup-legacy")
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
@click.option("--delete", is_flag=True, help="Delete legacy files instead of migrating")
@click.option("--backup", type=click.Path(), help="Backup directory for deleted files")
def cleanup_legacy(dry_run: bool, delete: bool, backup: str):
    """Find and handle legacy v2 format YAML files."""
    legacy_files = scan_for_legacy_files(roadmap_dir)

    if not legacy_files:
        click.echo("No legacy format files found.")
        return

    click.echo(f"Found {len(legacy_files)} legacy format files:")
    for file_path, format_version in legacy_files:
        click.echo(f"  - {file_path.name} ({format_version.value})")

    if dry_run:
        return

    # Handle files...
```

### Step 4: Add Migration Warning to DB Rebuild

```python
def rebuild_database(roadmap_dir: Path, result: RebuildResult):
    # Check for legacy files first
    legacy_files = scan_for_legacy_files(roadmap_dir)
    if legacy_files:
        result.add_warning(
            f"Found {len(legacy_files)} legacy v2 format files. "
            f"Run 'vibey roadmap db cleanup-legacy' to handle them."
        )

    # Continue with rebuild...
```

### Step 5: Add Pre-commit Hook Check

**File**: `vibey/operations/git/hooks/pre_commit.py`

```python
def check_yaml_format(staged_files: List[Path]) -> List[str]:
    """Check that staged YAML files use current format."""
    errors = []
    for file_path in staged_files:
        if file_path.suffix == ".yaml" and "roadmap/tasks/" in str(file_path):
            format_version = detect_task_format(file_path)
            if format_version == YAMLFormat.V2_LEGACY:
                errors.append(f"{file_path.name}: Uses legacy v2 format")
    return errors
```

## Test Cases

1. **Detect v2 format** - File with `parent_ref` detected as legacy
2. **Detect v3 format** - File with `sprint_id` detected as current
3. **Cleanup dry-run** - Shows files without modifying
4. **Cleanup with delete** - Removes legacy files
5. **Cleanup with backup** - Backs up before deletion
6. **Pre-commit check** - Blocks commit of legacy format files

## Files to Create/Modify

| File | Action |
|------|--------|
| `vibey/roadmap/serialization/format_detector.py` | Create |
| `vibey/operations/roadmap/db_rebuild.py` | Add legacy scan |
| `vibey/cli/commands.py` | Add cleanup-legacy command |
| `vibey/operations/git/hooks/pre_commit.py` | Add format check |

## Acceptance Criteria

- [ ] Format detection utility identifies v2 vs v3 format
- [ ] DB rebuild warns about legacy format files
- [ ] `cleanup-legacy` command lists legacy files
- [ ] `cleanup-legacy --delete` removes files
- [ ] `cleanup-legacy --backup` creates backup before deletion
- [ ] Pre-commit hook blocks legacy format files
