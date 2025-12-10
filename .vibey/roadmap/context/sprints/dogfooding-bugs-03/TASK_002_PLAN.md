# Task 002: Implement Automatic DB Rebuild After YAML Changes

**Task ID:** dogfooding-bugs-03-task-002
**Bug Addressed:** #5 (SQLite Database Out of Sync with YAML)
**Complexity:** High
**Type:** Development

---

## Problem Statement

When YAML files are modified manually or by other tools, the database becomes stale. The system needs automatic detection and sync of YAML changes.

---

## Design Options

### Option A: File Watcher (Real-time)
- Background process monitors YAML files
- Syncs database on file changes
- Pros: Immediate sync
- Cons: Complex, resource-intensive, requires daemon

### Option B: On-Command Check (Recommended)
- Check YAML timestamps before any query
- Sync if files modified since last load
- Pros: Simple, no daemon, lazy sync
- Cons: Slight delay on first query after change

### Option C: Pre-Commit Hook Only
- Sync as part of commit process
- Pros: No overhead during development
- Cons: Database stale during development

**Recommendation:** Option B with Option C as fallback

---

## Implementation

### YAML Modification Detection

```python
# vibey/roadmap/serialization/backend.py (SyncManager additions)

def check_yaml_freshness(self) -> Dict[str, Any]:
    """
    Check if YAML files have been modified since last database load.

    Returns:
        Dict with:
        - needs_sync: bool
        - modified_files: list of modified file paths
        - last_load: timestamp of last database load
    """
    from vibey.roadmap.database import get_connection

    conn = get_connection(db_path=self.db_path)

    # Get last load time
    row = conn.execute("""
        SELECT last_yaml_load FROM database_state WHERE id = 1
    """).fetchone()

    last_load = row['last_yaml_load'] if row else None

    if last_load is None:
        # Never loaded, needs full rebuild
        return {
            'needs_sync': True,
            'modified_files': [],
            'last_load': None,
            'reason': 'never_loaded',
        }

    # Check checksums
    modified = self.check_yaml_modified()

    return {
        'needs_sync': len(modified) > 0,
        'modified_files': modified,
        'last_load': last_load,
        'reason': 'files_modified' if modified else 'up_to_date',
    }


def auto_sync_if_needed(self) -> Optional[Dict[str, Any]]:
    """
    Automatically sync database if YAML files have changed.

    Returns:
        Sync report if sync was performed, None otherwise
    """
    freshness = self.check_yaml_freshness()

    if not freshness['needs_sync']:
        return None

    logger.info(f"YAML files modified since last load, syncing database...")
    logger.debug(f"Modified files: {freshness['modified_files']}")

    # Perform incremental sync for modified files only
    if freshness['reason'] == 'files_modified' and len(freshness['modified_files']) < 50:
        return self.incremental_sync(freshness['modified_files'])
    else:
        return self.full_rebuild()
```

### Incremental Sync

```python
def incremental_sync(self, modified_files: List[str]) -> Dict[str, Any]:
    """
    Sync only the modified files (faster than full rebuild).

    Args:
        modified_files: List of modified YAML file paths

    Returns:
        Sync report
    """
    from vibey.roadmap.serialization.sql_dumper import (
        dump_track_to_db,
        dump_sprint_to_db,
        dump_task_to_db,
    )

    report = {'tracks': 0, 'sprints': 0, 'tasks': 0, 'errors': []}

    conn = get_connection(db_path=self.db_path)

    for file_path in modified_files:
        try:
            full_path = self.roadmap_dir / file_path
            data = yaml.safe_load(full_path.read_text())

            # Determine entity type from path
            if '/tracks/' in file_path:
                dump_track_to_db(conn, data['track'], upsert=True)
                report['tracks'] += 1
            elif '/sprints/' in file_path:
                dump_sprint_to_db(conn, data['sprint'], upsert=True)
                report['sprints'] += 1
            elif '/tasks/' in file_path:
                dump_task_to_db(conn, data['task'], upsert=True)
                report['tasks'] += 1

            # Update checksum
            self.update_checksum(file_path)

        except Exception as e:
            report['errors'].append({'file': file_path, 'error': str(e)})

    conn.commit()
    self.mark_db_clean()

    return report
```

### Integration with Query Layer

```python
# vibey/operations/roadmap/query.py

def query_roadmap_summary(root_dir: Path = None) -> Roadmap:
    """
    Query roadmap summary with automatic YAML sync.
    """
    if root_dir is None:
        root_dir = Path.cwd()

    # Auto-sync if using database backend
    if _use_sqlite_backend(root_dir):
        from vibey.roadmap.serialization.backend import SyncManager

        db_path = root_dir / ".vibey" / "roadmap.db"
        roadmap_dir = root_dir / ".vibey" / "roadmap"

        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)
        sync_report = sync.auto_sync_if_needed()

        if sync_report:
            logger.info(f"Auto-synced: {sync_report['tracks']} tracks, "
                       f"{sync_report['sprints']} sprints, {sync_report['tasks']} tasks")

    # Continue with query
    return _query_roadmap_from_backend(root_dir)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/backend.py` | Add `check_yaml_freshness()`, `auto_sync_if_needed()`, `incremental_sync()` |
| `vibey/operations/roadmap/query.py` | Call `auto_sync_if_needed()` before queries |
| `vibey/roadmap/serialization/sql_dumper.py` | Add `upsert=True` parameter to dump functions |

---

## Testing Strategy

```python
def test_auto_sync_detects_modified_yaml(tmp_path):
    """Auto-sync detects YAML modifications."""
    setup_synced_db(tmp_path)

    # Modify a track file
    track_file = tmp_path / ".vibey/roadmap/tracks/track1.yaml"
    data = yaml.safe_load(track_file.read_text())
    data['track']['status'] = 'completed'
    track_file.write_text(yaml.dump(data))

    # Check freshness
    sync = SyncManager(...)
    freshness = sync.check_yaml_freshness()

    assert freshness['needs_sync'] is True
    assert 'track1.yaml' in str(freshness['modified_files'])


def test_auto_sync_performs_incremental(tmp_path):
    """Small changes trigger incremental sync, not full rebuild."""
    setup_synced_db(tmp_path)

    # Modify 2 files
    modify_files(tmp_path, count=2)

    sync = SyncManager(...)
    report = sync.auto_sync_if_needed()

    assert report is not None
    # Should be fast (incremental), not seconds (full rebuild)
```

---

## Success Criteria

- [ ] YAML modification detection works
- [ ] Incremental sync for small changes (<50 files)
- [ ] Full rebuild for large changes (>50 files)
- [ ] Auto-sync integrates with query layer
- [ ] Sync is transparent to users

---

## Dependencies

- Task 001 (database sync infrastructure)

---

## Notes

The auto-sync adds a small overhead to the first query after YAML changes, but subsequent queries are fast. The 50-file threshold can be tuned based on performance testing.

Consider adding a `VIBEY_AUTO_SYNC=false` environment variable to disable for CI/CD.
