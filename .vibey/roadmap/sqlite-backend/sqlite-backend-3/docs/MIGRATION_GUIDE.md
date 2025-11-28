# SQLite Backend Migration Guide

This guide covers migrating from YAML-only roadmap storage to the SQLite backend.

## Overview

The SQLite backend provides:
- **Faster queries**: SQL aggregation vs parsing hundreds of YAML files
- **Data consistency**: Foreign keys prevent orphan entities
- **Auto-aggregation**: Computed views eliminate manual counter updates
- **Change detection**: Checksum-based YAML modification tracking

YAML files remain the source of truth for version control (human-readable diffs).

## Quick Start

### Initialize Database from YAML

```bash
# Create database from existing YAML files
vibey roadmap db init

# Or use --force to overwrite existing database
vibey roadmap db init --force
```

### Check Database Status

```bash
# Show database state
vibey roadmap db status

# Validate database integrity
vibey roadmap db validate
```

## Two-Way Sync

### YAML → SQLite (rebuild)

When you modify YAML files manually or pull changes:

```bash
# Rebuild database from YAML
vibey roadmap db rebuild
```

This is automatically triggered by the **post-merge** git hook when roadmap YAML files are updated.

### SQLite → YAML (dump)

When the database has changes that need to be committed:

```bash
# Dump database state to YAML files
vibey roadmap db dump

# Force dump (overwrite modified YAML files)
vibey roadmap db dump --force
```

This is automatically triggered by the **pre-commit** git hook to ensure YAML files are in sync.

## Git Hook Integration

### Automatic Hooks

When you initialize or rebuild the database, git hooks are configured:

1. **pre-commit**: Dumps database changes to YAML before commit
2. **post-merge**: Rebuilds database when YAML files are updated after pull/merge
3. **post-checkout**: Rebuilds database when switching branches

### Manual Hook Installation

If hooks aren't working, verify they exist:

```bash
ls -la .git/hooks/pre-commit .git/hooks/post-merge
```

To manually install hooks:

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
python3 -m vibey.operations.git.hooks pre-commit
EOF
chmod +x .git/hooks/pre-commit

# Create post-merge hook
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
python3 -m vibey.operations.git.hooks post-merge
EOF
chmod +x .git/hooks/post-merge
```

## Conflict Resolution

### Database Dirty + YAML Modified

If both database and YAML have changes:

```bash
# Check status
vibey roadmap db status

# Option 1: Keep database changes, overwrite YAML
vibey roadmap db dump --force

# Option 2: Keep YAML changes, overwrite database
vibey roadmap db rebuild --force
```

### Resolving Validation Errors

```bash
# Run full validation
vibey roadmap db validate --level full

# Fix common issues:
# 1. Missing references: rebuild from YAML
vibey roadmap db rebuild --force

# 2. Schema mismatch: reinitialize
vibey roadmap db init --force
```

## Backend Configuration

### Configuration File

Backend settings are in `.vibey/config/roadmap.yaml`:

```yaml
backend: auto  # auto, sqlite, or yaml

database:
  path: .vibey/roadmap.db
  validate_on_load: true
  fallback_to_yaml: true
```

### Backend Modes

| Mode | Description |
|------|-------------|
| `auto` | Use SQLite if database exists and is valid, otherwise YAML |
| `sqlite` | Always use SQLite (error if database doesn't exist) |
| `yaml` | Always use YAML (ignore database) |

### CLI Backend Override

```bash
# Force specific backend for a command
vibey roadmap --backend sqlite query stats
vibey roadmap --backend yaml show
```

## Query Commands

The SQLite backend enables fast SQL-powered queries:

```bash
# Overall statistics
vibey roadmap db query stats

# Progress by track/sprint/status
vibey roadmap db query progress --by track

# List blocked tasks
vibey roadmap db query blocked --verbose

# Show dependency chains
vibey roadmap db query deps TASK_ID
```

## Troubleshooting

### Database Not Found

```
Error: Database not found. Run 'vibey roadmap db init' to create database.
```

Solution:
```bash
vibey roadmap db init
```

### YAML Modified Outside Database

```
Error: YAML files modified outside database
```

This means YAML files were edited manually or pulled from git. Options:

```bash
# Load YAML changes into database
vibey roadmap db rebuild

# Or overwrite YAML with database state
vibey roadmap db dump --force
```

### Database Has Uncommitted Changes

```
Error: Database has uncommitted changes
```

The database was modified but not dumped to YAML. Options:

```bash
# Dump changes to YAML
vibey roadmap db dump

# Or discard database changes
vibey roadmap db rebuild --force
```

### Schema Version Mismatch

```
Error: Schema version mismatch (expected 1.0.0, got X.X.X)
```

The database was created with a different schema version:

```bash
# Reinitialize with current schema
vibey roadmap db init --force
```

## Best Practices

1. **Always commit after `db dump`**: Ensure YAML changes are tracked
2. **Pull before modifying**: Avoid conflicts by syncing first
3. **Use `--force` carefully**: It discards uncommitted changes
4. **Run `db validate` periodically**: Catch data integrity issues early
5. **Keep database in `.gitignore`**: Only YAML should be version controlled

## Data Flow

```
┌─────────────────┐      ┌─────────────────┐
│   YAML Files    │◄────►│  SQLite DB      │
│  (.vibey/       │      │  (.vibey/       │
│   roadmap/*.    │      │   roadmap.db)   │
│   yaml)         │      │                 │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │  git push/pull         │  CLI queries
         │                        │  Fast aggregation
         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│   Git Remote    │      │   vibey CLI     │
│  (source of     │      │  (read/write    │
│   truth)        │      │   operations)   │
└─────────────────┘      └─────────────────┘
```

## Version History

- **1.0.0** (Sprint 3): Initial release with dump/rebuild/hooks
