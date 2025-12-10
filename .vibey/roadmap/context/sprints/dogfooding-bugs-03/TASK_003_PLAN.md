# Task 003: Add CLI Command to Force DB Resync

**Task ID:** dogfooding-bugs-03-task-003
**Bug Addressed:** #5 (SQLite Database Out of Sync with YAML)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

Users need a way to manually force a database resync when they know YAML files have changed, or when automatic detection fails.

---

## Implementation

### CLI Command Design

```python
# vibey/cli/main.py

@db.command()
@click.option('--from-yaml', is_flag=True, help='Rebuild database from YAML files')
@click.option('--from-db', is_flag=True, help='Overwrite YAML files from database')
@click.option('--dry-run', is_flag=True, help='Show what would be synced')
@click.option('--force', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def sync(ctx, from_yaml: bool, from_db: bool, dry_run: bool, force: bool):
    """
    Synchronize database and YAML files.

    By default, detects which source is newer and syncs in that direction.
    Use --from-yaml to force YAML as source of truth.
    Use --from-db to force database as source of truth.

    Examples:

        # Auto-detect and sync
        vibey roadmap db sync

        # Force rebuild from YAML
        vibey roadmap db sync --from-yaml

        # Preview without changes
        vibey roadmap db sync --dry-run
    """
    from vibey.cli.commands import db_sync_cmd
    ctx.exit(db_sync_cmd(
        from_yaml=from_yaml,
        from_db=from_db,
        dry_run=dry_run,
        force=force,
    ))
```

### Command Implementation

```python
# vibey/cli/commands.py

def db_sync_cmd(
    from_yaml: bool = False,
    from_db: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """Synchronize database with YAML files."""
    from vibey.roadmap.serialization.backend import SyncManager

    root_dir = Path.cwd()
    db_path = root_dir / ".vibey" / "roadmap.db"
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    if not db_path.exists() and not from_yaml:
        print("Error: No database found. Use --from-yaml to create one.")
        return 1

    if not roadmap_dir.exists():
        print("Error: No roadmap found. Run 'vibey roadmap init' first.")
        return 1

    sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

    # Mutual exclusion
    if from_yaml and from_db:
        print("Error: Cannot use both --from-yaml and --from-db")
        return 1

    # Check current status
    status = sync.get_sync_status()
    print(f"\n📊 Sync Status:")
    print(f"   Database: {'exists' if status['db_exists'] else 'missing'}")
    print(f"   YAML files: {status['yaml_files']}")
    print(f"   Dirty flag: {'yes' if status['is_dirty'] else 'no'}")
    print(f"   Modified YAML: {len(status['modified_yaml_files'])}")
    print(f"   Status: {status['status']}")

    # Determine sync direction
    if from_yaml:
        direction = 'yaml_to_db'
    elif from_db:
        direction = 'db_to_yaml'
    else:
        # Auto-detect
        if status['status'] == 'YAML_AHEAD':
            direction = 'yaml_to_db'
        elif status['status'] == 'DB_AHEAD':
            direction = 'db_to_yaml'
        elif status['status'] == 'CONFLICT':
            print("\n⚠️  Both database and YAML have been modified!")
            print("   Use --from-yaml or --from-db to choose source of truth.")
            return 1
        else:
            print("\n✅ Already in sync, nothing to do.")
            return 0

    # Show plan
    if direction == 'yaml_to_db':
        print(f"\n📥 Plan: Rebuild database from YAML files")
        if status['modified_yaml_files']:
            print("   Modified files:")
            for f in status['modified_yaml_files'][:10]:
                print(f"     - {f}")
            if len(status['modified_yaml_files']) > 10:
                print(f"     ... and {len(status['modified_yaml_files']) - 10} more")
    else:
        print(f"\n📤 Plan: Update YAML files from database")

    if dry_run:
        print("\n   (dry run - no changes made)")
        return 0

    # Confirm
    if not force:
        if direction == 'db_to_yaml':
            print("\n⚠️  This will OVERWRITE YAML files with database content!")
        click.confirm("Proceed?", abort=True)

    # Execute sync
    print("\n🔄 Syncing...")

    if direction == 'yaml_to_db':
        report = sync.rebuild()
        print(f"\n✅ Database rebuilt:")
        print(f"   Tracks:  {report.get('tracks', 0)}")
        print(f"   Sprints: {report.get('sprints', 0)}")
        print(f"   Tasks:   {report.get('tasks', 0)}")
    else:
        report = sync.dump()
        print(f"\n✅ YAML files updated:")
        print(f"   Files written: {report.get('files_written', 0)}")

    return 0
```

---

## Usage Examples

```bash
# Check sync status
vibey roadmap db sync --dry-run

# Rebuild database from YAML (explicit)
vibey roadmap db sync --from-yaml

# Update YAML from database
vibey roadmap db sync --from-db

# Force sync without confirmation
vibey roadmap db sync --from-yaml --force
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/main.py` | Add `db sync` command |
| `vibey/cli/commands.py` | Add `db_sync_cmd()` implementation |

---

## Testing Strategy

```python
def test_db_sync_from_yaml(tmp_path, cli_runner):
    """--from-yaml rebuilds database."""
    setup_yaml_and_db(tmp_path)

    result = cli_runner.invoke(cli, [
        'roadmap', 'db', 'sync', '--from-yaml', '--force'
    ])

    assert result.exit_code == 0
    assert "Database rebuilt" in result.output


def test_db_sync_from_db(tmp_path, cli_runner):
    """--from-db updates YAML files."""
    setup_yaml_and_db(tmp_path)

    result = cli_runner.invoke(cli, [
        'roadmap', 'db', 'sync', '--from-db', '--force'
    ])

    assert result.exit_code == 0
    assert "YAML files updated" in result.output


def test_db_sync_dry_run(tmp_path, cli_runner):
    """--dry-run shows plan without changes."""
    setup_out_of_sync(tmp_path)

    result = cli_runner.invoke(cli, ['roadmap', 'db', 'sync', '--dry-run'])

    assert result.exit_code == 0
    assert "dry run" in result.output


def test_db_sync_conflict_detection(tmp_path, cli_runner):
    """Detects conflicts when both modified."""
    setup_conflict(tmp_path)

    result = cli_runner.invoke(cli, ['roadmap', 'db', 'sync'])

    assert result.exit_code == 1
    assert "Both database and YAML" in result.output
```

---

## Success Criteria

- [ ] `vibey roadmap db sync` command works
- [ ] `--from-yaml` forces YAML as source
- [ ] `--from-db` forces database as source
- [ ] `--dry-run` shows plan without changes
- [ ] Conflict detection works
- [ ] Confirmation prompt for destructive operations

---

## Dependencies

- Task 001 (sync infrastructure)
- Task 002 (sync detection)

---

## Notes

This command replaces `vibey roadmap db rebuild` as the primary sync mechanism. The `rebuild` command could be deprecated or kept as an alias.
