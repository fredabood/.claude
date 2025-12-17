# Database Operations

> **Time Required:** 10 minutes
> **Difficulty:** Intermediate
> **Prerequisites:** Vibey installed, project initialized

---

## Overview

This walkthrough covers SQLite database management in Vibey. The database is a cache for fast queries; YAML files are the source of truth.

> **Dual Storage Architecture:** Vibey stores roadmap data in two places:
> 1. **YAML files** (`.vibey/roadmap/`) - Source of truth, version controlled
> 2. **SQLite database** (`.vibey/roadmap.db`) - Query cache, regenerable
>
> You can always rebuild the database from YAML files. See [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md).

---

## Common Database Operations

### Check Database Status

```bash
vibey roadmap db status
```

Shows:
- Database file location and size
- Table counts
- Last sync timestamp
- YAML vs database record counts

### Rebuild Database from YAML

When YAML files are edited externally or the database gets corrupted:

```bash
vibey roadmap db rebuild
```

This:
1. Reads all YAML files from `.vibey/roadmap/`
2. Drops and recreates all database tables
3. Inserts all records from YAML
4. Verifies integrity

### Validate Database Integrity

```bash
vibey roadmap db validate
```

Checks:
- Foreign key constraints
- Record count matches between YAML and SQLite
- ULID format validity
- Required field presence

---

## Database Maintenance

### View Database Statistics

```bash
vibey roadmap db stats
```

Shows detailed statistics:
- Record counts per table
- Index usage
- Storage efficiency

### Vacuum Database

Reclaim disk space after deletions:

```bash
vibey roadmap db vacuum
```

### Migrate Database Schema

When upgrading Vibey versions with schema changes:

```bash
vibey roadmap db migrate
```

Applies any pending schema migrations.

---

## Troubleshooting Database Issues

### Database Out of Sync

If the database doesn't match YAML files:

```bash
# Check what's different
vibey roadmap db validate

# Rebuild from YAML (source of truth)
vibey roadmap db rebuild
```

### Database Corrupted

If the database file is corrupted:

```bash
# Delete the database (YAML is source of truth)
rm .vibey/roadmap.db

# Rebuild from YAML
vibey roadmap db rebuild
```

### Missing Records

If records are missing from queries:

```bash
# Validate the database
vibey roadmap db validate

# If validation fails, rebuild
vibey roadmap db rebuild
```

---

## Understanding the Schema

The SQLite database contains 26 tables:

| Table | Purpose |
|-------|---------|
| `tracks` | Track records and metadata |
| `sprints` | Sprint records and progress |
| `tasks` | Task records and status |
| `dependencies` | Task dependency relationships |
| `commits` | Git commit associations |
| `activity_log` | Roadmap activity history |
| ... | (See `vibey roadmap db stats` for full list) |

---

## Command Reference

### Database Commands
```bash
vibey roadmap db status          # Check database status
vibey roadmap db rebuild         # Rebuild from YAML
vibey roadmap db validate        # Validate integrity
vibey roadmap db stats           # View statistics
vibey roadmap db vacuum          # Reclaim disk space
vibey roadmap db migrate         # Apply schema migrations
```

---

## See Also

- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - Dual storage explained
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
