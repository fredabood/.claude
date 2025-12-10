# Task 006: Update Pre-commit Hook to Use Correct Schema

**Task ID:** dogfooding-bugs-03-task-006
**Bug Addressed:** #9 (Pre-commit Hook Database Error - Missing is_dirty Column)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The pre-commit hook queries `is_dirty` from `database_state` but the column may not exist in older databases. The hook should handle this gracefully.

---

## Current Implementation

```python
# vibey/operations/git/hooks/pre_commit.py:479-501

def _sync_database_to_yaml(self) -> bool:
    """Sync SQLite database to YAML if database has uncommitted changes."""
    try:
        from vibey.roadmap.database.connection import database_exists, get_db_path
        from vibey.roadmap.serialization.backend import SyncManager

        db_path = get_db_path(self.repo_path)

        if not database_exists(db_path=db_path):
            return True  # No database, nothing to sync

        roadmap_dir = self.repo_path / ".vibey" / "roadmap"
        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # This line fails if is_dirty column doesn't exist
        if not sync.is_db_dirty():
            return True
        ...
```

---

## Implementation

### Defensive Query in SyncManager

```python
# vibey/roadmap/serialization/backend.py

def is_db_dirty(self) -> bool:
    """
    Check if database has uncommitted changes.

    Returns False (not dirty) if:
    - Database doesn't exist
    - database_state table doesn't exist
    - is_dirty column doesn't exist (old schema)
    - No data in database_state
    """
    if not database_exists(db_path=self.db_path):
        return False

    try:
        conn = get_connection(db_path=self.db_path)

        # Check if table exists
        table_exists = conn.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type='table' AND name='database_state'
        """).fetchone()

        if not table_exists:
            logger.warning("database_state table missing, assuming clean")
            return False

        # Check if is_dirty column exists
        columns = conn.execute("PRAGMA table_info(database_state)").fetchall()
        col_names = [col[1] for col in columns]  # Column name is at index 1

        if 'is_dirty' not in col_names:
            logger.warning("is_dirty column missing, assuming clean")
            return False

        # Query normally
        row = conn.execute("""
            SELECT is_dirty FROM database_state WHERE id = 1
        """).fetchone()

        return bool(row and row[0])

    except sqlite3.OperationalError as e:
        logger.warning(f"Database query failed: {e}, assuming clean")
        return False
```

### Schema Auto-Repair

```python
# vibey/roadmap/serialization/backend.py

def ensure_database_state_table(self) -> bool:
    """
    Ensure database_state table exists with correct schema.

    Returns True if table was created/updated.
    """
    try:
        conn = get_connection(db_path=self.db_path)

        # Check if table exists
        table_exists = conn.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type='table' AND name='database_state'
        """).fetchone()

        if not table_exists:
            # Create table
            conn.execute("""
                CREATE TABLE database_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_yaml_load TEXT,
                    last_yaml_dump TEXT,
                    is_dirty INTEGER NOT NULL DEFAULT 0,
                    source_commit TEXT,
                    source_branch TEXT,
                    schema_version TEXT NOT NULL DEFAULT '1.0.0'
                )
            """)
            conn.execute("INSERT INTO database_state (id, schema_version) VALUES (1, '1.0.0')")
            conn.commit()
            logger.info("Created database_state table")
            return True

        # Check for missing columns
        columns = conn.execute("PRAGMA table_info(database_state)").fetchall()
        col_names = [col[1] for col in columns]

        if 'is_dirty' not in col_names:
            conn.execute("ALTER TABLE database_state ADD COLUMN is_dirty INTEGER NOT NULL DEFAULT 0")
            conn.commit()
            logger.info("Added is_dirty column to database_state")
            return True

        return False

    except Exception as e:
        logger.error(f"Failed to ensure database_state table: {e}")
        return False
```

### Updated Pre-commit Hook

```python
# vibey/operations/git/hooks/pre_commit.py

def _sync_database_to_yaml(self) -> bool:
    """Sync SQLite database to YAML if database has uncommitted changes."""
    try:
        from vibey.roadmap.database.connection import database_exists, get_db_path
        from vibey.roadmap.serialization.backend import SyncManager

        db_path = get_db_path(self.repo_path)

        if not database_exists(db_path=db_path):
            return True  # No database, nothing to sync

        roadmap_dir = self.repo_path / ".vibey" / "roadmap"
        sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)

        # Ensure database_state table is valid
        sync.ensure_database_state_table()

        # Now safe to query
        if not sync.is_db_dirty():
            return True  # Database is clean

        # Continue with sync...
        print(f"{self.YELLOW}[vibey]{self.RESET} Database has uncommitted changes, syncing to YAML...")
        # ...

    except ImportError:
        return True  # SQLite backend not available
    except Exception as e:
        # Log error but don't block commit
        logger.warning(f"Pre-commit hook error: {e}")
        return True  # Fail open
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/backend.py` | Add defensive `is_db_dirty()`, add `ensure_database_state_table()` |
| `vibey/operations/git/hooks/pre_commit.py` | Call `ensure_database_state_table()` before query |

---

## Testing Strategy

```python
def test_is_db_dirty_missing_table(tmp_path):
    """is_db_dirty returns False when table missing."""
    # Create empty database
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE dummy (id INTEGER)")
    conn.close()

    sync = SyncManager(db_path=db_path, roadmap_dir=tmp_path)
    assert sync.is_db_dirty() is False  # Should not raise


def test_is_db_dirty_missing_column(tmp_path):
    """is_db_dirty returns False when column missing."""
    # Create database with old schema
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE database_state (id INTEGER, schema_version TEXT)")
    conn.execute("INSERT INTO database_state VALUES (1, '0.9.0')")
    conn.close()

    sync = SyncManager(db_path=db_path, roadmap_dir=tmp_path)
    assert sync.is_db_dirty() is False  # Should not raise


def test_ensure_database_state_creates_table(tmp_path):
    """ensure_database_state_table creates missing table."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.close()

    sync = SyncManager(db_path=db_path, roadmap_dir=tmp_path)
    sync.ensure_database_state_table()

    # Verify table created
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT is_dirty FROM database_state WHERE id = 1").fetchone()
    assert row is not None


def test_ensure_database_state_adds_column(tmp_path):
    """ensure_database_state_table adds missing column."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE database_state (id INTEGER, schema_version TEXT)")
    conn.execute("INSERT INTO database_state VALUES (1, '0.9.0')")
    conn.close()

    sync = SyncManager(db_path=db_path, roadmap_dir=tmp_path)
    sync.ensure_database_state_table()

    # Verify column added
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT is_dirty FROM database_state WHERE id = 1").fetchone()
    assert row[0] == 0  # Default value
```

---

## Success Criteria

- [ ] `is_db_dirty()` handles missing table gracefully
- [ ] `is_db_dirty()` handles missing column gracefully
- [ ] `ensure_database_state_table()` creates table if missing
- [ ] `ensure_database_state_table()` adds column if missing
- [ ] Pre-commit hook runs without error on old databases

---

## Dependencies

- Task 005 (investigation complete)

---

## Notes

This is a defensive fix that makes the system self-healing. Old databases will be automatically updated when the pre-commit hook runs. The "fail open" approach ensures commits are never blocked by database issues.
