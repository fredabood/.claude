# Task 001: Add Database Sync Step to Migration Script

**Task ID:** dogfooding-bugs-03-task-001
**Bug Addressed:** #5 (SQLite Database Out of Sync with YAML)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

When YAML files are migrated to the ULID flat structure, the SQLite database is not updated. This causes the database to have stale data (37 tracks vs 38 in YAML).

---

## Current State

The migration scripts (e.g., `directory_migration_v2.py`) update YAML files but do not touch the SQLite database. After migration:
- YAML files: 38 tracks (current)
- Database: 37 tracks (stale)

---

## Implementation

### Migration Script Integration

```python
# vibey/roadmap/operations/migrate_to_ulid.py (or existing migration script)

def run_migration(root_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run ULID migration with automatic database sync.

    Args:
        root_dir: Project root directory
        dry_run: If True, report changes without applying

    Returns:
        Migration report
    """
    report = {
        'yaml_migrated': 0,
        'db_synced': False,
        'tracks': 0,
        'sprints': 0,
        'tasks': 0,
    }

    # Step 1: Migrate YAML files
    yaml_report = migrate_yaml_to_ulid(root_dir, dry_run)
    report['yaml_migrated'] = yaml_report['files_migrated']

    if dry_run:
        return report

    # Step 2: Sync database with YAML
    db_path = root_dir / ".vibey" / "roadmap.db"

    if db_path.exists():
        print("Syncing database with migrated YAML files...")
        db_report = rebuild_database_from_ulid(root_dir)
        report['db_synced'] = True
        report['tracks'] = db_report['tracks']
        report['sprints'] = db_report['sprints']
        report['tasks'] = db_report['tasks']
    else:
        print("No database found, skipping sync.")

    return report


def rebuild_database_from_ulid(root_dir: Path) -> Dict[str, int]:
    """
    Rebuild database from ULID flat structure.

    Args:
        root_dir: Project root directory

    Returns:
        Counts of loaded entities
    """
    from vibey.roadmap.database import get_connection
    from vibey.roadmap.database.schema import create_schema, drop_all_tables

    db_path = root_dir / ".vibey" / "roadmap.db"
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    # Backup existing database
    backup_path = db_path.with_suffix('.db.bak')
    if db_path.exists():
        shutil.copy(db_path, backup_path)
        print(f"  Backup created: {backup_path}")

    # Recreate schema
    conn = get_connection(db_path=db_path)
    drop_all_tables(conn)
    create_schema(conn)

    # Load from ULID files
    counts = load_all_from_ulid(conn, roadmap_dir)

    return counts
```

### Helper Functions

```python
def load_all_from_ulid(conn, roadmap_dir: Path) -> Dict[str, int]:
    """
    Load all entities from ULID flat structure into database.

    Args:
        conn: Database connection
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        Entity counts
    """
    from vibey.roadmap.serialization.sql_dumper import (
        dump_track_to_db,
        dump_sprint_to_db,
        dump_task_to_db,
    )

    tracks_dir = roadmap_dir / "tracks"
    sprints_dir = roadmap_dir / "sprints"
    tasks_dir = roadmap_dir / "tasks"

    counts = {'tracks': 0, 'sprints': 0, 'tasks': 0}

    # Load roadmap first
    roadmap_path = roadmap_dir / "roadmap.yaml"
    if roadmap_path.exists():
        roadmap_data = yaml.safe_load(roadmap_path.read_text())
        dump_roadmap_to_db(conn, roadmap_data)

    # Load tracks
    for track_file in tracks_dir.glob("*.yaml"):
        try:
            track_data = yaml.safe_load(track_file.read_text())
            dump_track_to_db(conn, track_data['track'])
            counts['tracks'] += 1
        except Exception as e:
            print(f"  Warning: Failed to load {track_file.name}: {e}")

    # Load sprints
    for sprint_file in sprints_dir.glob("*.yaml"):
        try:
            sprint_data = yaml.safe_load(sprint_file.read_text())
            dump_sprint_to_db(conn, sprint_data['sprint'])
            counts['sprints'] += 1
        except Exception as e:
            print(f"  Warning: Failed to load {sprint_file.name}: {e}")

    # Load tasks
    for task_file in tasks_dir.glob("*.yaml"):
        try:
            task_data = yaml.safe_load(task_file.read_text())
            dump_task_to_db(conn, task_data['task'])
            counts['tasks'] += 1
        except Exception as e:
            print(f"  Warning: Failed to load {task_file.name}: {e}")

    conn.commit()
    return counts
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/operations/migrate_to_ulid.py` | Add database sync step |
| `vibey/roadmap/serialization/sql_dumper.py` | Add ULID-aware dump functions |

---

## Testing Strategy

```python
def test_migration_syncs_database(tmp_path):
    """Database is synced after YAML migration."""
    # Setup: Create YAML files and old database
    setup_test_migration(tmp_path)

    # Run migration
    report = run_migration(tmp_path)

    # Verify database updated
    assert report['db_synced'] is True
    assert report['tracks'] == 38
    assert report['sprints'] > 0


def test_migration_creates_backup(tmp_path):
    """Migration creates database backup."""
    setup_test_migration(tmp_path)

    run_migration(tmp_path)

    backup_path = tmp_path / ".vibey" / "roadmap.db.bak"
    assert backup_path.exists()
```

---

## Success Criteria

- [ ] Migration script syncs database after YAML update
- [ ] Database backup created before sync
- [ ] All 38+ tracks loaded into database
- [ ] Sprints and tasks loaded correctly
- [ ] Error handling for failed entity loads

---

## Dependencies

- Depends on Sprint 2 (ULID file loading works)

---

## Notes

This is the "automatic" approach - sync happens as part of migration. Users don't need to run a separate command. The backup ensures data safety.
