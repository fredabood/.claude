# Task 008: Test Pre-commit Hook with Fresh Database

**Task ID:** dogfooding-bugs-03-task-008
**Bug Addressed:** #9 (Pre-commit Hook Database Error - Missing is_dirty Column)
**Complexity:** Low
**Type:** Testing

---

## Problem Statement

After fixing the pre-commit hook (Tasks 005-007), we need comprehensive tests to verify the hook works correctly with:
1. Fresh database (newly created)
2. Old database (missing columns)
3. No database (YAML-only mode)
4. Corrupted database

---

## Test Categories

### 1. Fresh Database Tests

```python
# tests/operations/git/hooks/test_pre_commit.py

class TestPreCommitFreshDatabase:
    """Test pre-commit hook with fresh database."""

    def test_hook_runs_with_fresh_database(self, fresh_roadmap_with_db):
        """Hook runs successfully with newly created database."""
        hook = PreCommitHook(repo_path=fresh_roadmap_with_db)
        result = hook.run()

        assert result == 0  # Success

    def test_hook_detects_dirty_database(self, fresh_roadmap_with_db):
        """Hook detects when database has uncommitted changes."""
        # Mark database dirty
        from vibey.roadmap.serialization.backend import SyncManager
        sync = SyncManager(...)
        sync.mark_db_dirty()

        hook = PreCommitHook(repo_path=fresh_roadmap_with_db)

        # Should sync before allowing commit
        # (Check that _sync_database_to_yaml is called)

    def test_hook_clears_dirty_after_sync(self, fresh_roadmap_with_db):
        """Hook clears dirty flag after syncing."""
        sync = SyncManager(...)
        sync.mark_db_dirty()

        hook = PreCommitHook(repo_path=fresh_roadmap_with_db)
        hook.run()

        assert sync.is_db_dirty() is False
```

### 2. Old Database Tests

```python
class TestPreCommitOldDatabase:
    """Test pre-commit hook with old database schema."""

    def test_hook_handles_missing_is_dirty(self, old_schema_database):
        """Hook handles database without is_dirty column."""
        hook = PreCommitHook(repo_path=old_schema_database)
        result = hook.run()

        assert result == 0  # Should not crash

    def test_hook_auto_repairs_schema(self, old_schema_database):
        """Hook auto-repairs database schema."""
        hook = PreCommitHook(repo_path=old_schema_database)
        hook.run()

        # Verify is_dirty column now exists
        conn = sqlite3.connect(old_schema_database / ".vibey/roadmap.db")
        columns = conn.execute("PRAGMA table_info(database_state)").fetchall()
        col_names = [col[1] for col in columns]
        assert 'is_dirty' in col_names

    def test_hook_handles_missing_database_state(self, missing_state_database):
        """Hook handles database without database_state table."""
        hook = PreCommitHook(repo_path=missing_state_database)
        result = hook.run()

        assert result == 0  # Should not crash
```

### 3. No Database Tests

```python
class TestPreCommitNoDatabase:
    """Test pre-commit hook with YAML-only mode."""

    def test_hook_runs_without_database(self, yaml_only_roadmap):
        """Hook runs when no database exists."""
        hook = PreCommitHook(repo_path=yaml_only_roadmap)
        result = hook.run()

        assert result == 0

    def test_hook_validates_yaml_without_db(self, yaml_only_roadmap):
        """Hook validates YAML files even without database."""
        # Stage invalid YAML
        invalid_yaml = yaml_only_roadmap / ".vibey/roadmap/tracks/bad.yaml"
        invalid_yaml.write_text("not: valid: yaml")
        stage_file(yaml_only_roadmap, invalid_yaml)

        hook = PreCommitHook(repo_path=yaml_only_roadmap)
        hook.run()

        assert any(i.rule == 'yaml_integrity' for i in hook.issues)
```

### 4. Error Handling Tests

```python
class TestPreCommitErrorHandling:
    """Test pre-commit hook error handling."""

    def test_hook_handles_database_locked(self, fresh_roadmap_with_db):
        """Hook handles locked database gracefully."""
        # Lock database by opening exclusive connection
        db_path = fresh_roadmap_with_db / ".vibey/roadmap.db"
        lock_conn = sqlite3.connect(db_path)
        lock_conn.execute("BEGIN EXCLUSIVE")

        hook = PreCommitHook(repo_path=fresh_roadmap_with_db)
        result = hook.run()

        # Should fail open, not block commit
        assert result == 0

        lock_conn.rollback()
        lock_conn.close()

    def test_hook_handles_corrupted_database(self, corrupted_database):
        """Hook handles corrupted database gracefully."""
        hook = PreCommitHook(repo_path=corrupted_database)
        result = hook.run()

        # Should fail open, not block commit
        assert result == 0

    def test_hook_handles_permission_error(self, readonly_database):
        """Hook handles read-only database gracefully."""
        hook = PreCommitHook(repo_path=readonly_database)
        result = hook.run()

        # Should fail open, not block commit
        assert result == 0
```

### 5. Integration Tests

```python
class TestPreCommitIntegration:
    """End-to-end pre-commit hook tests."""

    def test_full_commit_workflow(self, fresh_roadmap_with_db):
        """Full commit workflow with database sync."""
        # Make changes via CLI
        subprocess.run([
            'vibey', 'roadmap', 'update', 'task', 'task-1',
            '--status', 'completed'
        ], cwd=fresh_roadmap_with_db)

        # Stage YAML files
        subprocess.run(['git', 'add', '.'], cwd=fresh_roadmap_with_db)

        # Run pre-commit hook
        hook = PreCommitHook(repo_path=fresh_roadmap_with_db)
        result = hook.run()

        assert result == 0

        # Verify YAML files were synced
        # (database changes should be in YAML)

    def test_hook_blocks_invalid_completion(self, fresh_roadmap_with_db):
        """Hook blocks invalid completion status changes."""
        # Try to mark task complete without meeting criteria
        task_file = fresh_roadmap_with_db / ".vibey/roadmap/tasks/task-1.yaml"
        data = yaml.safe_load(task_file.read_text())
        data['task']['status'] = 'completed'
        task_file.write_text(yaml.dump(data))

        subprocess.run(['git', 'add', task_file], cwd=fresh_roadmap_with_db)

        hook = PreCommitHook(repo_path=fresh_roadmap_with_db)
        hook.config.completion_verification['mode'] = 'blocking'
        result = hook.run()

        # Should block if completion criteria not met
        # (depends on task having unmet criteria)
```

---

## Test Fixtures

```python
# conftest.py

@pytest.fixture
def fresh_roadmap_with_db(tmp_path):
    """Create fresh roadmap with synced database."""
    create_test_roadmap(tmp_path)
    create_and_sync_database(tmp_path)
    init_git_repo(tmp_path)
    return tmp_path


@pytest.fixture
def old_schema_database(tmp_path):
    """Create database with old schema (missing is_dirty)."""
    create_test_roadmap(tmp_path)

    db_path = tmp_path / ".vibey/roadmap.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE database_state (
            id INTEGER PRIMARY KEY,
            schema_version TEXT
        )
    """)
    conn.execute("INSERT INTO database_state VALUES (1, '0.9.0')")
    conn.commit()

    init_git_repo(tmp_path)
    return tmp_path


@pytest.fixture
def yaml_only_roadmap(tmp_path):
    """Create roadmap with YAML only (no database)."""
    create_test_roadmap(tmp_path)
    init_git_repo(tmp_path)
    return tmp_path


@pytest.fixture
def corrupted_database(tmp_path):
    """Create roadmap with corrupted database."""
    create_test_roadmap(tmp_path)
    db_path = tmp_path / ".vibey/roadmap.db"
    db_path.write_bytes(b"corrupted data not a sqlite file")
    init_git_repo(tmp_path)
    return tmp_path
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/operations/git/hooks/test_pre_commit.py` | Pre-commit hook tests |
| `tests/operations/git/hooks/conftest.py` | Test fixtures |

---

## Success Criteria

- [ ] Fresh database tests pass
- [ ] Old database tests pass
- [ ] No database tests pass
- [ ] Error handling tests pass
- [ ] Integration tests pass
- [ ] All tests run in CI

---

## Dependencies

- Tasks 005-007 (pre-commit fixes)

---

## Notes

These tests verify Bug #9 is fixed:
- Hook no longer crashes on `is_dirty` column error
- Hook auto-repairs old databases
- Hook fails open (never blocks commits on errors)
- Hook works in all scenarios
