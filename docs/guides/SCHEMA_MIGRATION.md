# Schema Migration Guide

## Overview

The schema migration tool (`scripts/migrate-roadmap-schema.py`) automates the process of updating roadmap YAML files to new schema versions. It handles format standardization, backward compatibility improvements, and schema version upgrades.

## Features

- **Version-Based Migrations**: Apply transformations specific to target schema versions
- **Dry-Run Mode**: Preview changes without modifying files
- **Interactive Mode**: Confirm each change before applying
- **Automatic Backups**: Creates timestamped backups before modifications
- **Batch Processing**: Migrate entire directory trees
- **Selective Migration**: Target specific files
- **Progress Reporting**: Detailed summary of changes made

## Usage

### Basic Usage

```bash
# Dry run to see what would change (recommended first step)
python scripts/migrate-roadmap-schema.py --dry-run --verbose

# Apply migrations to all files
python scripts/migrate-roadmap-schema.py --to-version 2.1

# Interactive mode - confirm each file
python scripts/migrate-roadmap-schema.py --interactive --verbose
```

### Advanced Usage

```bash
# Migrate specific files only
python scripts/migrate-roadmap-schema.py \
  --files .vibey/roadmap/my-track/track.yaml \
          .vibey/roadmap/my-track/my-sprint/sprint.yaml

# Migrate custom directory
python scripts/migrate-roadmap-schema.py \
  --directory /path/to/roadmap \
  --to-version 2.1

# Dry run on specific files with detailed output
python scripts/migrate-roadmap-schema.py \
  --dry-run \
  --verbose \
  --files .vibey/roadmap/*/track.yaml
```

## Schema Version 2.1 Migrations

The following transformations are applied when migrating to version 2.1:

### 1. Dependencies to Structured Format

**Transforms**: Simple string dependencies → Structured objects

**Before**:
```yaml
dependencies:
  - interface-unification
  - roadmap-system
```

**After**:
```yaml
dependencies:
  - type: track
    target_id: interface-unification
    target_status: completed
    reason: Dependency on track completion
    optional: false
  - type: track
    target_id: roadmap-system
    target_status: completed
    reason: Dependency on track completion
    optional: false
```

**Applies to**: Track and sprint `dependencies` and `blocks` fields

### 2. Add Missing roadmap_id

**Transforms**: Adds roadmap_id if missing

**Before**:
```yaml
sprint:
  id: my-sprint-1
  name: My Sprint
  track_id: my-track
  # roadmap_id missing
```

**After**:
```yaml
sprint:
  id: my-sprint-1
  name: My Sprint
  track_id: my-track
  roadmap_id: vibey-framework-v2  # Added
```

**Applies to**: Sprint and task files

### 3. Fix Null estimated_tokens

**Transforms**: Null estimated_tokens → Default value of 1

**Before**:
```yaml
task:
  estimated_tokens: null
```

**After**:
```yaml
task:
  estimated_tokens: 1
```

**Applies to**: Task files

### 4. Rename Fields for Consistency

**Transforms**: Field name standardization

**Sprint task summaries - 'name' → 'title'**:

**Before**:
```yaml
tasks:
  - id: my-task-1
    name: My Task  # Old field name
    status: completed
```

**After**:
```yaml
tasks:
  - id: my-task-1
    title: My Task  # Standardized field name
    status: completed
```

**Gate info - 'blocking' → 'is_blocking'**:

**Before**:
```yaml
gate_info:
  threshold: 90
  blocking: true  # Old field name
```

**After**:
```yaml
gate_info:
  threshold: 90
  is_blocking: true  # Standardized field name
```

### 5. Fix Legacy Task Types

**Transforms**: Old task type values → Current enum values

**Before**:
```yaml
task:
  task_type: quality_gate  # Legacy value
```

**After**:
```yaml
task:
  task_type: completion_gate  # Current value
```

**Mapping**:
- `quality_gate` → `completion_gate`

### 6. Add Missing Gate Fields

**Transforms**: Infers `blocks_status` from `task_type` if missing

**Before**:
```yaml
task:
  task_type: completion_gate
  gate_info:
    threshold: 100
    is_blocking: true
    # blocks_status missing
```

**After**:
```yaml
task:
  task_type: completion_gate
  gate_info:
    threshold: 100
    is_blocking: true
    blocks_status: completed  # Inferred from task_type
```

**Inference rules**:
- `completion_gate` → `blocks_status: completed`
- `production_gate` → `blocks_status: production_ready`
- `development` → `blocks_status: completed` (default)

### 7. Add Missing Progress Section

**Transforms**: Creates minimal progress section if missing

**Before**:
```yaml
sprint:
  id: my-sprint-1
  # progress section missing
```

**After**:
```yaml
sprint:
  id: my-sprint-1
  progress:
    development_tasks_total: 0
    development_tasks_completed: 0
    completion_gate_tasks_total: 0
    completion_gate_tasks_completed: 0
    production_gate_tasks_total: 0
    production_gate_tasks_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0
```

Also calculates `completion_percent` if missing but other fields present.

## Backup and Rollback

### Automatic Backups

When not in dry-run mode, the script automatically creates backups:

```
.vibey/roadmap/my-track/
├── track.yaml                    # Original (modified)
└── .schema-migration-backups/
    └── track.yaml.20251120_153045.bak  # Backup with timestamp
```

### Manual Rollback

To rollback a migration:

```bash
# Find the backup
ls .vibey/roadmap/my-track/.schema-migration-backups/

# Restore from backup
cp .vibey/roadmap/my-track/.schema-migration-backups/track.yaml.20251120_153045.bak \
   .vibey/roadmap/my-track/track.yaml
```

### Automated Rollback

If you need to rollback many files:

```bash
# Find all backup directories
find .vibey/roadmap -type d -name ".schema-migration-backups"

# Restore all backups (example script)
for backup_dir in $(find .vibey/roadmap -type d -name ".schema-migration-backups"); do
    parent_dir=$(dirname "$backup_dir")
    latest_backup=$(ls -t "$backup_dir"/*.bak | head -1)
    if [ -n "$latest_backup" ]; then
        cp "$latest_backup" "$parent_dir/$(basename ${latest_backup%.*.bak})"
        echo "Restored: $parent_dir"
    fi
done
```

## Output and Reporting

### Verbose Output

With `--verbose` flag, see detailed progress:

```
[DRY-RUN] .vibey/roadmap/my-track/track.yaml - Would apply 3 changes
[DRY-RUN] .vibey/roadmap/my-track/my-sprint/sprint.yaml - Would apply 2 changes
✓ .vibey/roadmap/other-track/track.yaml - No changes needed
```

### Summary Report

Every run produces a summary:

```
================================================================================
MIGRATION SUMMARY
================================================================================
Files processed: 125
✓ Migrated: 87
- Unchanged: 35
✗ Failed: 3

Details:
✓ .vibey/roadmap/track-1/track.yaml
    - Converted dependency 'interface-unification' to structured format
    - Converted block 'goose-port' to structured format
✓ .vibey/roadmap/track-2/sprint-1/sprint.yaml
    - Added roadmap_id: vibey-framework-v2
    - Renamed task 'name' → 'title' (task: task-001)
✗ .vibey/roadmap/track-3/track.yaml
    Error: Invalid YAML syntax
================================================================================
```

## Best Practices

### 1. Always Dry-Run First

```bash
# See what would change before applying
python scripts/migrate-roadmap-schema.py --dry-run --verbose > migration-preview.txt

# Review the preview
less migration-preview.txt

# Apply if satisfied
python scripts/migrate-roadmap-schema.py
```

### 2. Use Interactive Mode for Critical Files

```bash
# Confirm each change for important files
python scripts/migrate-roadmap-schema.py \
  --interactive \
  --files .vibey/roadmap/production-track/*.yaml
```

### 3. Backup Before Large Migrations

```bash
# Create manual backup of entire roadmap
cp -r .vibey/roadmap .vibey/roadmap.backup.$(date +%Y%m%d)

# Then run migration
python scripts/migrate-roadmap-schema.py
```

### 4. Validate After Migration

```bash
# Apply migrations
python scripts/migrate-roadmap-schema.py

# Validate all files pass schema
python scripts/validate-roadmap-schema.py --strict
```

## Troubleshooting

### Migration Fails with YAML Error

**Problem**: Invalid YAML syntax in source file

**Solution**:
```bash
# Validate YAML syntax first
python -c "import yaml; yaml.safe_load(open('.vibey/roadmap/my-track/track.yaml'))"

# Fix syntax errors, then re-run migration
```

### No Changes Applied

**Problem**: Files already in target format

**Solution**: This is normal! Files already compliant with version 2.1 won't be changed.

### Backup Directory Full

**Problem**: Multiple migration runs create many backups

**Solution**:
```bash
# Clean old backups (keep only latest)
find .vibey/roadmap -type d -name ".schema-migration-backups" -exec sh -c '
    cd "$1" && ls -t *.bak | tail -n +4 | xargs rm -f
' _ {} \;
```

## Extending the Migrator

### Adding New Transformations

To add a new migration transformation:

1. **Define transformation function** in `migrate-roadmap-schema.py`:

```python
def migrate_my_new_transformation(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Description of what this does."""
    changes = []

    if file_type == 'task' and 'task' in data:
        task = data['task']

        # Your transformation logic
        if some_condition:
            task['field'] = new_value
            changes.append("Description of change")

    return data, changes
```

2. **Register in MIGRATIONS dictionary**:

```python
MIGRATIONS: Dict[str, List[Callable]] = {
    '2.1': [
        migrate_dependencies_to_structured,
        migrate_add_missing_roadmap_id,
        # ... existing migrations ...
        migrate_my_new_transformation,  # Add yours here
    ],
}
```

3. **Test with dry-run**:

```bash
python scripts/migrate-roadmap-schema.py --dry-run --verbose
```

### Adding New Schema Versions

To add version 2.2:

```python
MIGRATIONS: Dict[str, List[Callable]] = {
    '2.1': [ ... ],
    '2.2': [
        migrate_v22_transformation_1,
        migrate_v22_transformation_2,
    ],
}
```

## See Also

- [Schema Validation Guide](./SCHEMA_VALIDATION.md)
- [Roadmap System Reference](../reference/ROADMAP_SYSTEM.md)
- [YAML Best Practices](./YAML_BEST_PRACTICES.md)
