# Task 004: Add Integration Test for YAML-DB Sync

**Task ID:** dogfooding-bugs-03-task-004
**Bug Addressed:** #5 (SQLite Database Out of Sync with YAML)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

The YAML-database synchronization functionality needs comprehensive integration tests to verify end-to-end behavior and prevent regressions.

---

## Test Categories

### 1. Sync Direction Tests

```python
# tests/integration/test_yaml_db_sync.py

class TestSyncDirection:
    """Test sync direction detection and execution."""

    def test_detect_yaml_ahead(self, synced_environment):
        """Detect when YAML is newer than database."""
        # Modify a YAML file after sync
        track_file = synced_environment / ".vibey/roadmap/tracks/track1.yaml"
        data = yaml.safe_load(track_file.read_text())
        data['track']['status'] = 'completed'
        track_file.write_text(yaml.dump(data))

        sync = SyncManager(...)
        status = sync.get_sync_status()

        assert status['status'] == 'YAML_AHEAD'
        assert 'track1.yaml' in str(status['modified_yaml_files'])

    def test_detect_db_ahead(self, synced_environment):
        """Detect when database is newer than YAML."""
        # Modify database directly
        conn = get_connection(...)
        conn.execute("UPDATE tracks SET status = 'completed' WHERE id = 'track1'")
        conn.commit()
        sync = SyncManager(...)
        sync.mark_db_dirty()

        status = sync.get_sync_status()

        assert status['status'] == 'DB_AHEAD'
        assert status['is_dirty'] is True

    def test_detect_conflict(self, synced_environment):
        """Detect when both have changes (conflict)."""
        # Modify YAML
        track_file = synced_environment / ".vibey/roadmap/tracks/track1.yaml"
        data = yaml.safe_load(track_file.read_text())
        data['track']['status'] = 'completed'
        track_file.write_text(yaml.dump(data))

        # And mark database dirty
        sync = SyncManager(...)
        sync.mark_db_dirty()

        status = sync.get_sync_status()

        assert status['status'] == 'CONFLICT'

    def test_detect_in_sync(self, synced_environment):
        """Detect when in sync."""
        sync = SyncManager(...)
        status = sync.get_sync_status()

        assert status['status'] == 'IN_SYNC'
```

### 2. Sync Execution Tests

```python
class TestSyncExecution:
    """Test sync execution."""

    def test_yaml_to_db_sync(self, out_of_sync_environment):
        """YAML -> DB sync loads all entities."""
        sync = SyncManager(...)
        report = sync.rebuild()

        assert report['tracks'] > 0
        assert report['sprints'] > 0
        assert report['tasks'] > 0

        # Verify database updated
        conn = get_connection(...)
        track_count = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        assert track_count == report['tracks']

    def test_db_to_yaml_sync(self, out_of_sync_environment):
        """DB -> YAML sync writes all files."""
        sync = SyncManager(...)
        report = sync.dump()

        assert report['files_written'] > 0

        # Verify YAML files match database
        conn = get_connection(...)
        tracks = conn.execute("SELECT id, status FROM tracks").fetchall()

        for track in tracks:
            track_file = out_of_sync_environment / f".vibey/roadmap/tracks/{track['id']}.yaml"
            data = yaml.safe_load(track_file.read_text())
            assert data['track']['status'] == track['status']

    def test_sync_preserves_data_integrity(self, synced_environment):
        """Round-trip sync preserves all data."""
        # Capture original state
        original_tracks = count_yaml_tracks(synced_environment)

        sync = SyncManager(...)

        # YAML -> DB
        sync.rebuild()

        # DB -> YAML
        sync.dump()

        # Verify data preserved
        final_tracks = count_yaml_tracks(synced_environment)
        assert original_tracks == final_tracks
```

### 3. Edge Case Tests

```python
class TestSyncEdgeCases:
    """Test edge cases and error handling."""

    def test_sync_handles_malformed_yaml(self, synced_environment):
        """Sync handles malformed YAML gracefully."""
        # Create malformed file
        malformed = synced_environment / ".vibey/roadmap/tracks/bad.yaml"
        malformed.write_text("not: valid: yaml: {[")

        sync = SyncManager(...)
        report = sync.rebuild()

        assert 'errors' in report
        assert any('bad.yaml' in str(e) for e in report['errors'])

    def test_sync_handles_missing_directory(self, tmp_path):
        """Sync handles missing directories."""
        # Create minimal structure
        (tmp_path / ".vibey/roadmap").mkdir(parents=True)

        sync = SyncManager(...)
        report = sync.rebuild()

        assert report['tracks'] == 0  # Graceful, not error

    def test_sync_handles_empty_database(self, synced_environment):
        """Sync to empty database works."""
        # Delete all data
        conn = get_connection(...)
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM sprints")
        conn.execute("DELETE FROM tracks")
        conn.commit()

        sync = SyncManager(...)
        report = sync.rebuild()

        # Should reload from YAML
        conn = get_connection(...)
        assert conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0] > 0

    def test_sync_incremental_is_fast(self, large_synced_environment):
        """Incremental sync is faster than full rebuild."""
        import time

        # Modify one file
        track_file = large_synced_environment / ".vibey/roadmap/tracks/track1.yaml"
        data = yaml.safe_load(track_file.read_text())
        data['track']['name'] = 'Modified Track'
        track_file.write_text(yaml.dump(data))

        sync = SyncManager(...)

        # Time incremental sync
        start = time.time()
        sync.auto_sync_if_needed()
        incremental_time = time.time() - start

        # Reset and time full rebuild
        sync.rebuild()
        start = time.time()
        sync.rebuild()  # Full rebuild
        full_time = time.time() - start

        assert incremental_time < full_time / 2  # At least 2x faster
```

### 4. CLI Integration Tests

```python
class TestSyncCLI:
    """Test CLI sync commands."""

    def test_cli_sync_from_yaml(self, synced_environment, cli_runner):
        """CLI sync --from-yaml works."""
        result = cli_runner.invoke(cli, [
            'roadmap', 'db', 'sync', '--from-yaml', '--force'
        ])

        assert result.exit_code == 0
        assert "Database rebuilt" in result.output

    def test_cli_sync_dry_run(self, out_of_sync_environment, cli_runner):
        """CLI sync --dry-run shows changes without applying."""
        result = cli_runner.invoke(cli, [
            'roadmap', 'db', 'sync', '--dry-run'
        ])

        assert result.exit_code == 0
        assert "dry run" in result.output

        # Verify no changes made
        # (check timestamps, checksums, etc.)

    def test_cli_sync_conflict_requires_flag(self, conflict_environment, cli_runner):
        """CLI sync requires explicit flag for conflicts."""
        result = cli_runner.invoke(cli, ['roadmap', 'db', 'sync'])

        assert result.exit_code == 1
        assert "Both database and YAML" in result.output
```

---

## Test Fixtures

```python
# conftest.py

@pytest.fixture
def synced_environment(tmp_path):
    """Create environment with YAML and synced database."""
    create_test_yaml_files(tmp_path, tracks=5, sprints=10, tasks=50)
    create_and_sync_database(tmp_path)
    return tmp_path


@pytest.fixture
def out_of_sync_environment(tmp_path):
    """Create environment with YAML but outdated database."""
    create_test_yaml_files(tmp_path, tracks=5, sprints=10, tasks=50)
    create_and_sync_database(tmp_path)
    # Add new track to YAML only
    add_yaml_track(tmp_path, "new-track")
    return tmp_path


@pytest.fixture
def conflict_environment(tmp_path):
    """Create environment with conflicts."""
    create_test_yaml_files(tmp_path)
    create_and_sync_database(tmp_path)
    # Modify YAML
    modify_yaml_track(tmp_path, "track1")
    # Mark DB dirty
    mark_db_dirty(tmp_path)
    return tmp_path


@pytest.fixture
def large_synced_environment(tmp_path):
    """Create large environment for performance testing."""
    create_test_yaml_files(tmp_path, tracks=50, sprints=100, tasks=500)
    create_and_sync_database(tmp_path)
    return tmp_path
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/integration/test_yaml_db_sync.py` | Sync integration tests |
| `tests/integration/conftest.py` | Sync test fixtures |

---

## Success Criteria

- [ ] Direction detection tests pass
- [ ] Sync execution tests pass
- [ ] Edge case tests pass
- [ ] CLI integration tests pass
- [ ] Performance tests pass (incremental faster than full)
- [ ] All tests run in CI

---

## Dependencies

- Tasks 001-003 (sync implementation)

---

## Notes

These tests verify Bug #5 is fixed and prevent regression. They also document expected sync behavior for future development.
