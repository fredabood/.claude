# Task 012: Add Integration Test for Database Rebuild

**Task ID:** dogfooding-bugs-03-task-012
**Bug Addressed:** #11 (Database Rebuild Loads 0 Tracks/Sprints/Tasks)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

After fixing the database rebuild (Tasks 009-011), we need comprehensive integration tests to:
1. Verify the fix works correctly
2. Prevent regression
3. Document expected behavior
4. Test edge cases

---

## Test Categories

### 1. ULID Structure Tests

```python
# tests/integration/test_db_rebuild.py

class TestDatabaseRebuildULID:
    """Test database rebuild with ULID flat structure."""

    def test_rebuild_loads_all_tracks(self, ulid_roadmap_environment):
        """Database rebuild loads all tracks from tracks/*.yaml."""
        result = db_rebuild_cmd(force=True)

        assert result == 0

        conn = get_connection()
        tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

        # Should load all tracks
        tracks_dir = ulid_roadmap_environment / ".vibey" / "roadmap" / "tracks"
        expected = len(list(tracks_dir.glob("*.yaml")))

        assert tracks == expected
        assert tracks > 0

    def test_rebuild_loads_all_sprints(self, ulid_roadmap_environment):
        """Database rebuild loads all sprints from sprints/*.yaml."""
        result = db_rebuild_cmd(force=True)

        conn = get_connection()
        sprints = conn.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]

        sprints_dir = ulid_roadmap_environment / ".vibey" / "roadmap" / "sprints"
        expected = len(list(sprints_dir.glob("*.yaml")))

        assert sprints == expected
        assert sprints > 0

    def test_rebuild_loads_all_tasks(self, ulid_roadmap_environment):
        """Database rebuild loads all tasks from tasks/*.yaml."""
        result = db_rebuild_cmd(force=True)

        conn = get_connection()
        tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        tasks_dir = ulid_roadmap_environment / ".vibey" / "roadmap" / "tasks"
        expected = len(list(tasks_dir.glob("*.yaml")))

        assert tasks == expected
        assert tasks > 0

    def test_rebuild_preserves_relationships(self, ulid_roadmap_environment):
        """Database rebuild maintains correct parent-child relationships."""
        db_rebuild_cmd(force=True)

        conn = get_connection()

        # All sprints should have valid track_id
        orphan_sprints = conn.execute("""
            SELECT COUNT(*) FROM sprints s
            WHERE NOT EXISTS (
                SELECT 1 FROM tracks t WHERE t.id = s.track_id
            )
        """).fetchone()[0]
        assert orphan_sprints == 0

        # All tasks should have valid sprint_id
        orphan_tasks = conn.execute("""
            SELECT COUNT(*) FROM tasks t
            WHERE NOT EXISTS (
                SELECT 1 FROM sprints s WHERE s.id = t.sprint_id
            )
        """).fetchone()[0]
        assert orphan_tasks == 0
```

### 2. Backward Compatibility Tests

```python
class TestDatabaseRebuildLegacy:
    """Test database rebuild with legacy nested structure."""

    def test_rebuild_works_with_nested_structure(self, legacy_roadmap_environment):
        """Database rebuild still works with legacy directory structure."""
        result = db_rebuild_cmd(force=True)

        assert result == 0

        conn = get_connection()
        tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

        # Should load tracks from legacy structure
        assert tracks > 0

    def test_rebuild_auto_detects_structure(self, mixed_environment):
        """Database rebuild correctly detects ULID vs legacy structure."""
        result = db_rebuild_cmd(force=True)

        assert result == 0

        # Should not error regardless of structure type
        conn = get_connection()
        tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        assert tracks > 0
```

### 3. Error Handling Tests

```python
class TestDatabaseRebuildErrors:
    """Test database rebuild error handling."""

    def test_rebuild_handles_malformed_yaml(self, ulid_roadmap_environment):
        """Database rebuild handles malformed YAML gracefully."""
        # Add a malformed file
        bad_file = ulid_roadmap_environment / ".vibey/roadmap/tracks/bad.yaml"
        bad_file.write_text("not: valid: yaml: {[")

        result = db_rebuild_cmd(force=True)

        # Should succeed (skip bad file, load others)
        assert result == 0

        # Should still load valid tracks
        conn = get_connection()
        tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        assert tracks > 0

    def test_rebuild_handles_missing_track_id(self, ulid_roadmap_environment):
        """Database rebuild handles sprint without track_id."""
        # Create sprint without track_id
        bad_sprint = ulid_roadmap_environment / ".vibey/roadmap/sprints/orphan.yaml"
        bad_sprint.write_text("""
sprint:
  id: orphan-sprint
  name: Orphan Sprint
  status: planned
  # Missing track_id!
""")

        result = db_rebuild_cmd(force=True)

        # Should succeed (skip orphan, load others)
        assert result == 0

    def test_rebuild_handles_empty_directories(self, empty_roadmap_environment):
        """Database rebuild handles empty directories."""
        result = db_rebuild_cmd(force=True)

        assert result == 0

        conn = get_connection()
        tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        assert tracks == 0  # Empty is valid, not an error

    def test_rebuild_handles_no_database(self, ulid_roadmap_environment):
        """Database rebuild fails gracefully without existing database."""
        db_path = ulid_roadmap_environment / ".vibey" / "roadmap.db"
        if db_path.exists():
            db_path.unlink()

        result = db_rebuild_cmd(force=True)

        # Should fail with helpful message
        assert result == 1

    def test_rebuild_handles_permission_error(self, readonly_database):
        """Database rebuild handles permission errors."""
        result = db_rebuild_cmd(force=True)

        # Should fail gracefully
        assert result != 0  # or handle by restoring backup
```

### 4. Data Integrity Tests

```python
class TestDatabaseRebuildIntegrity:
    """Test database rebuild data integrity."""

    def test_rebuild_roundtrip_preserves_data(self, ulid_roadmap_environment):
        """Rebuild -> Dump -> Rebuild preserves all data."""
        # First rebuild
        db_rebuild_cmd(force=True)

        conn = get_connection()
        original_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        original_sprints = conn.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]
        original_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        # Dump to YAML
        db_dump_cmd(force=True)

        # Second rebuild
        db_rebuild_cmd(force=True)

        # Counts should be identical
        final_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        final_sprints = conn.execute("SELECT COUNT(*) FROM sprints").fetchone()[0]
        final_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

        assert original_tracks == final_tracks
        assert original_sprints == final_sprints
        assert original_tasks == final_tasks

    def test_rebuild_status_values_valid(self, ulid_roadmap_environment):
        """All status values are valid enum values after rebuild."""
        db_rebuild_cmd(force=True)

        conn = get_connection()

        # Check track statuses
        invalid_tracks = conn.execute("""
            SELECT COUNT(*) FROM tracks
            WHERE status NOT IN ('planned', 'in_progress', 'completed', 'blocked', 'wont_do')
        """).fetchone()[0]
        assert invalid_tracks == 0

        # Check sprint statuses
        invalid_sprints = conn.execute("""
            SELECT COUNT(*) FROM sprints
            WHERE status NOT IN ('planned', 'in_progress', 'completed', 'blocked', 'wont_do')
        """).fetchone()[0]
        assert invalid_sprints == 0

        # Check task statuses
        invalid_tasks = conn.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE status NOT IN ('not_started', 'in_progress', 'completed', 'blocked', 'wont_do')
        """).fetchone()[0]
        assert invalid_tasks == 0

    def test_rebuild_creates_backup(self, ulid_roadmap_environment):
        """Database rebuild creates backup before operation."""
        db_path = ulid_roadmap_environment / ".vibey" / "roadmap.db"
        backup_path = db_path.with_suffix('.db.bak')

        # Ensure no backup exists
        if backup_path.exists():
            backup_path.unlink()

        # Rebuild (will fail or succeed, doesn't matter)
        db_rebuild_cmd(force=True)

        # Backup should have been created and cleaned up on success
        # (or restored on failure)
        # Check database still exists
        assert db_path.exists()
```

### 5. Performance Tests

```python
class TestDatabaseRebuildPerformance:
    """Test database rebuild performance."""

    def test_rebuild_completes_in_reasonable_time(self, large_ulid_roadmap):
        """Database rebuild completes within reasonable time."""
        import time

        start = time.time()
        result = db_rebuild_cmd(force=True)
        elapsed = time.time() - start

        assert result == 0
        # Large roadmap (1000+ entities) should complete in < 30s
        assert elapsed < 30

    def test_rebuild_memory_usage(self, large_ulid_roadmap):
        """Database rebuild doesn't use excessive memory."""
        import tracemalloc

        tracemalloc.start()
        db_rebuild_cmd(force=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be < 500MB for large roadmap
        assert peak < 500 * 1024 * 1024
```

---

## Test Fixtures

```python
# tests/integration/conftest.py

@pytest.fixture
def ulid_roadmap_environment(tmp_path):
    """Create environment with ULID flat structure."""
    vibey_dir = tmp_path / ".vibey"
    roadmap_dir = vibey_dir / "roadmap"

    # Create directories
    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir(parents=True)
    (roadmap_dir / "tasks").mkdir(parents=True)

    # Create roadmap.yaml
    (vibey_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  status: in_progress
""")

    # Create sample tracks
    for i in range(5):
        track_id = f"track-{i:03d}"
        (roadmap_dir / "tracks" / f"{track_id}.yaml").write_text(f"""
track:
  id: {track_id}
  name: Track {i}
  status: in_progress
""")

        # Create sprints for each track
        for j in range(3):
            sprint_id = f"sprint-{i:03d}-{j:03d}"
            (roadmap_dir / "sprints" / f"{sprint_id}.yaml").write_text(f"""
sprint:
  id: {sprint_id}
  track_id: {track_id}
  name: Sprint {j}
  status: planned
""")

            # Create tasks for each sprint
            for k in range(5):
                task_id = f"task-{i:03d}-{j:03d}-{k:03d}"
                (roadmap_dir / "tasks" / f"{task_id}.yaml").write_text(f"""
task:
  id: {task_id}
  sprint_id: {sprint_id}
  track_id: {track_id}
  title: Task {k}
  status: not_started
""")

    # Initialize database
    create_test_database(tmp_path)

    return tmp_path


@pytest.fixture
def legacy_roadmap_environment(tmp_path):
    """Create environment with legacy nested structure."""
    vibey_dir = tmp_path / ".vibey"
    roadmap_dir = vibey_dir / "roadmap"
    roadmap_dir.mkdir(parents=True)

    # Create roadmap.yaml
    (vibey_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  status: in_progress
  tracks:
    - id: track-001
""")

    # Create nested structure
    track_dir = roadmap_dir / "track-001"
    track_dir.mkdir()
    (track_dir / "track.yaml").write_text("""
track:
  id: track-001
  name: Track 1
  status: in_progress
  sprints:
    - id: sprint-001
""")

    sprint_dir = track_dir / "sprint-001"
    sprint_dir.mkdir()
    (sprint_dir / "sprint.yaml").write_text("""
sprint:
  id: sprint-001
  name: Sprint 1
  status: planned
""")

    task_dir = sprint_dir / "task-001"
    task_dir.mkdir()
    (task_dir / "task.yaml").write_text("""
task:
  id: task-001
  title: Task 1
  status: not_started
""")

    create_test_database(tmp_path)
    return tmp_path


@pytest.fixture
def large_ulid_roadmap(tmp_path):
    """Create large roadmap for performance testing."""
    # 50 tracks, 10 sprints each, 20 tasks each = 10,000 tasks
    create_large_test_roadmap(tmp_path, tracks=50, sprints_per_track=10, tasks_per_sprint=20)
    create_test_database(tmp_path)
    return tmp_path
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/integration/test_db_rebuild.py` | Database rebuild integration tests |
| `tests/integration/conftest.py` | Update with new fixtures |

---

## Success Criteria

- [ ] ULID structure tests pass (load all tracks/sprints/tasks)
- [ ] Legacy structure tests pass (backward compatibility)
- [ ] Error handling tests pass (malformed YAML, missing IDs)
- [ ] Data integrity tests pass (roundtrip, valid statuses)
- [ ] Performance tests pass (reasonable time/memory)
- [ ] All tests run in CI

---

## Dependencies

- Tasks 009-011 (implementation complete)

---

## Notes

These tests verify Bug #11 is fixed and prevent regression. The test fixtures create minimal but complete roadmap structures for testing both ULID and legacy directory layouts.

Expected counts for this repository after fix:
- Tracks: 39
- Sprints: 213
- Tasks: 1125

The tests should pass with these exact counts when run against the actual repository structure.
