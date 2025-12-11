# Sprint 5: Cleanup and Verification - Task Plans

**Sprint ID**: `01KC7H29E0Z5BC7HK1CK222157`
**Track**: Embedded Task Migration
**Priority**: LOW
**Blocked By**: Sprint 4

---

## Task 001: Remove embedded tasks from sprint files

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215T`
**Estimated Tokens**: 20,000
**Complexity**: Simple

### Objective
Run cleanup script to remove 'tasks:' section from all sprint YAML files.

### Implementation Plan

#### Step 1: Create Cleanup Script
```python
# vibey/operations/migrations/cleanup_embedded_tasks.py

from pathlib import Path
import yaml
import shutil
from datetime import datetime

def remove_embedded_tasks(
    sprints_dir: Path,
    backup_dir: Path = None,
    dry_run: bool = True
) -> dict:
    """Remove embedded tasks from all sprint files."""

    if backup_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = sprints_dir.parent / f"backups/cleanup_{timestamp}"

    stats = {"processed": 0, "modified": 0, "skipped": 0}

    for sprint_file in sprints_dir.glob("*.yaml"):
        stats["processed"] += 1

        data = yaml.safe_load(sprint_file.read_text())
        sprint = data.get('sprint', {})

        if 'tasks' not in sprint:
            stats["skipped"] += 1
            continue

        if dry_run:
            print(f"Would remove tasks from: {sprint_file.name}")
            print(f"  Tasks count: {len(sprint['tasks'])}")
            stats["modified"] += 1
            continue

        # Create backup
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sprint_file, backup_dir / sprint_file.name)

        # Remove tasks
        del sprint['tasks']

        # Write updated file
        with open(sprint_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        print(f"Removed tasks from: {sprint_file.name}")
        stats["modified"] += 1

    return stats
```

#### Step 2: Add CLI Command
```python
@roadmap.command("cleanup-embedded")
@click.option("--dry-run/--execute", default=True)
def cleanup_embedded_cmd(dry_run: bool):
    """Remove embedded tasks from sprint files."""
    from vibey.operations.migrations.cleanup_embedded_tasks import (
        remove_embedded_tasks
    )
    stats = remove_embedded_tasks(
        sprints_dir=Path(".vibey/roadmap/sprints"),
        dry_run=dry_run
    )
    print(f"Processed: {stats['processed']}")
    print(f"Modified: {stats['modified']}")
    print(f"Skipped: {stats['skipped']}")
```

#### Step 3: Execute Cleanup
```bash
# Dry run first
vibey roadmap cleanup-embedded --dry-run

# Review output, then execute
vibey roadmap cleanup-embedded --execute
```

### Acceptance Criteria
- [ ] All sprint files have no 'tasks' key
- [ ] Backups created before modifications
- [ ] No data loss (tasks already in standalone files)

### Verification
```bash
# Verify no embedded tasks remain
grep -l "^  tasks:" .vibey/roadmap/sprints/*.yaml | wc -l
# Should be 0
```

---

## Task 002: Remove legacy embedded task migration code

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215V`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Remove or deprecate legacy migration code that handled embedded task formats.

### Files to Review
- `vibey/operations/migrations/embedded_tasks.py`
- `vibey/cli/migrate-embedded-tasks.py`
- `vibey/operations/roadmap/validate.py` (embedded task warnings)

### Implementation Plan

#### Step 1: Mark as Deprecated
Add deprecation notices to legacy files:
```python
# vibey/operations/migrations/embedded_tasks.py

"""
DEPRECATED: This module is no longer needed.

Embedded tasks have been fully migrated to standalone files.
Use load_tasks_by_sprint_flat() to query tasks.

This file is kept for reference only and will be removed in v3.0.
"""

import warnings

def migrate_embedded_tasks(*args, **kwargs):
    warnings.warn(
        "migrate_embedded_tasks is deprecated. "
        "All embedded tasks have been migrated to standalone files.",
        DeprecationWarning,
        stacklevel=2
    )
    return {"status": "deprecated", "message": "No migration needed"}
```

#### Step 2: Update Validation
Remove embedded task warnings from validator.py since they're no longer applicable.

#### Step 3: Document in CHANGELOG
```markdown
## Deprecated

- `migrate_embedded_tasks()` - No longer needed, all tasks use standalone files
- `vibey/cli/migrate-embedded-tasks.py` - Deprecated script
```

### Acceptance Criteria
- [ ] Legacy code marked deprecated
- [ ] No errors if deprecated code is called
- [ ] Documentation updated

---

## Task 003: Final verification and documentation

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215W`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Run comprehensive verification of the migration and update documentation.

### Verification Steps

#### Step 1: Count All Task Files
```bash
# Total standalone task files
ls -la .vibey/roadmap/tasks/*.yaml | wc -l
# Expected: ~2,459
```

#### Step 2: Verify No Embedded Tasks
```bash
# Should return 0 files
python3 -c "
import yaml
from pathlib import Path

count = 0
for f in Path('.vibey/roadmap/sprints').glob('*.yaml'):
    data = yaml.safe_load(f.read_text())
    if 'tasks' in data.get('sprint', {}):
        print(f'EMBEDDED TASKS: {f.name}')
        count += 1

print(f'Files with embedded tasks: {count}')
"
```

#### Step 3: Rebuild Database
```bash
vibey roadmap db rebuild
```

#### Step 4: Verify All Tracks
```bash
vibey roadmap status
```

Verify:
- Goose Port shows 34+ tasks
- JetBrains Port shows correct tasks
- All tracks have accurate counts

#### Step 5: Run Test Suite
```bash
pytest tests/roadmap/ -v
pytest tests/operations/ -v
```

### Documentation Updates

#### Update EMBEDDED_TASK_MIGRATION_PLAN.md
Add completion section:
```markdown
## Migration Complete

**Completed**: 2025-12-XX
**Final Statistics**:
- Standalone task files: X,XXX
- Embedded tasks removed from: XXX sprints
- Database rebuilt with accurate counts

**Verification**:
- [x] No sprint files have embedded tasks
- [x] All tracks show correct task counts
- [x] Test suite passes
```

#### Create Completion Report
```markdown
# EMBEDDED_TASK_MIGRATION_COMPLETE.md

## Summary
The embedded task migration was completed successfully.

## Before
- 1,129 standalone task files
- 1,330 embedded tasks in 202 sprint files
- Database showed incorrect counts for many tracks

## After
- 2,459 standalone task files
- 0 embedded tasks
- All track counts accurate

## Changes Made
1. Extracted 1,330 embedded tasks to standalone files
2. Updated 15 source files to use standalone queries
3. Removed 'tasks' arrays from 202 sprint files
4. Deprecated legacy migration code

## Verification
All tests pass. All tracks show accurate counts.
```

### Acceptance Criteria
- [ ] All ~2,459 tasks in standalone files
- [ ] No sprint files have tasks[] arrays
- [ ] Database counts match file counts
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Completion report created

---

## Sprint 5 Summary

| Task | Title | Tokens | Complexity |
|------|-------|--------|------------|
| 001 | Remove embedded tasks from sprints | 20,000 | Simple |
| 002 | Remove legacy migration code | 15,000 | Simple |
| 003 | Final verification and docs | 20,000 | Medium |

**Total Estimated Tokens**: 55,000
**Estimated Duration**: 1 day
**Sequential**: 001 → 002 → 003

---

## Track Completion Checklist

When all sprints complete:

- [ ] Sprint 1: All 1,330 embedded tasks extracted
- [ ] Sprint 2: Serialization code migrated
- [ ] Sprint 3: Git operations migrated
- [ ] Sprint 4: CLI and validation migrated
- [ ] Sprint 5: Cleanup complete

**Total Track Tokens**: ~425,000
**Total Track Duration**: ~10 days
