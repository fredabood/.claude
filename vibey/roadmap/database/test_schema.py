"""
Unit tests for database schema creation.

Tests:
- Schema DDL creation
- Index creation
- Schema validation
- Foreign key constraints
- CHECK constraints
"""

import sqlite3
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.database.connection import (
    get_connection,
    close_all_connections,
    DEFAULT_VIBEY_DIR,
)
from vibey.roadmap.database.schema import (
    SCHEMA_VERSION,
    EXPECTED_TABLES,
    create_schema,
    schema_exists,
    get_schema_version,
    drop_all_tables,
    get_schema_ddl,
    get_index_ddl,
    get_table_names,
    get_index_names,
    validate_schema,
)


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vibey_dir = Path(tmpdir) / DEFAULT_VIBEY_DIR
        vibey_dir.mkdir()
        yield Path(tmpdir)
        close_all_connections()


@pytest.fixture
def db_with_schema(temp_db_dir):
    """Create a database with the schema initialized."""
    db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
    conn = get_connection(db_path=db_path)
    create_schema(conn)
    return conn, db_path


class TestSchemaCreation:
    """Tests for schema creation."""

    def test_create_schema_creates_25_tables(self, temp_db_dir):
        """create_schema creates exactly 25 tables."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        conn = get_connection(db_path=db_path)

        create_schema(conn)

        tables = get_table_names(conn)
        assert len(tables) == 25

    def test_create_schema_creates_all_expected_tables(self, temp_db_dir):
        """create_schema creates all expected tables."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        conn = get_connection(db_path=db_path)

        create_schema(conn)

        tables = set(get_table_names(conn))
        expected = set(EXPECTED_TABLES)
        assert tables == expected

    def test_create_schema_creates_indexes(self, temp_db_dir):
        """create_schema creates indexes."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        conn = get_connection(db_path=db_path)

        create_schema(conn)

        indexes = get_index_names(conn)
        # Should have at least 20 indexes
        assert len(indexes) >= 20

    def test_create_schema_is_idempotent(self, temp_db_dir):
        """create_schema can be called multiple times without error."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        conn = get_connection(db_path=db_path)

        create_schema(conn)
        create_schema(conn)  # Should not raise

        tables = get_table_names(conn)
        assert len(tables) == 25

    def test_schema_version_is_set(self, db_with_schema):
        """Schema version is set after creation."""
        conn, _ = db_with_schema
        version = get_schema_version(conn)
        assert version == SCHEMA_VERSION

    def test_database_state_initialized(self, db_with_schema):
        """database_state singleton row is initialized."""
        conn, _ = db_with_schema
        result = conn.execute(
            "SELECT id, schema_version, is_dirty FROM database_state"
        ).fetchone()

        assert result["id"] == 1
        assert result["schema_version"] == SCHEMA_VERSION
        assert result["is_dirty"] == 0


class TestSchemaExists:
    """Tests for schema_exists function."""

    def test_returns_false_before_creation(self, temp_db_dir):
        """schema_exists returns False before schema is created."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        conn = get_connection(db_path=db_path)

        assert schema_exists(conn) is False

    def test_returns_true_after_creation(self, db_with_schema):
        """schema_exists returns True after schema is created."""
        conn, _ = db_with_schema
        assert schema_exists(conn) is True


class TestDropAllTables:
    """Tests for drop_all_tables function."""

    def test_drops_all_tables(self, db_with_schema):
        """drop_all_tables removes all tables."""
        conn, _ = db_with_schema

        # Verify tables exist
        assert len(get_table_names(conn)) == 25

        # Drop all tables
        drop_all_tables(conn)

        # Verify all tables are gone
        assert len(get_table_names(conn)) == 0

    def test_can_recreate_after_drop(self, db_with_schema):
        """Can recreate schema after dropping all tables."""
        conn, _ = db_with_schema

        drop_all_tables(conn)
        create_schema(conn)

        assert len(get_table_names(conn)) == 25


class TestValidateSchema:
    """Tests for validate_schema function."""

    def test_valid_schema(self, db_with_schema):
        """validate_schema returns valid for correct schema."""
        conn, _ = db_with_schema
        result = validate_schema(conn)

        assert result["valid"] is True
        assert result["table_count"] == 25
        assert result["missing_tables"] == []
        assert result["extra_tables"] == []
        assert result["schema_version"] == SCHEMA_VERSION

    def test_invalid_schema_missing_tables(self, temp_db_dir):
        """validate_schema detects missing tables."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        conn = get_connection(db_path=db_path)

        # Create only roadmaps table
        conn.execute("""
            CREATE TABLE roadmaps (id TEXT PRIMARY KEY)
        """)
        conn.execute("""
            CREATE TABLE database_state (id INTEGER PRIMARY KEY, schema_version TEXT)
        """)
        conn.execute("INSERT INTO database_state VALUES (1, '1.0.0')")

        result = validate_schema(conn)

        assert result["valid"] is False
        assert "tracks" in result["missing_tables"]
        assert "sprints" in result["missing_tables"]


class TestForeignKeyConstraints:
    """Tests for foreign key constraints."""

    def test_track_requires_valid_roadmap(self, db_with_schema):
        """Track requires valid roadmap_id."""
        conn, _ = db_with_schema

        # Insert a roadmap first
        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test Roadmap', '1.0.0', 'in_progress', '2025-01-01')
        """)

        # Track with valid roadmap_id should work
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test Track', 'not_started', '2025-01-01')
        """)

        # Track with invalid roadmap_id should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO tracks (id, roadmap_id, name, status, created)
                VALUES ('t2', 'invalid', 'Bad Track', 'not_started', '2025-01-01')
            """)

    def test_cascade_delete_tracks(self, db_with_schema):
        """Deleting roadmap cascades to tracks."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test Roadmap', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test Track', 'not_started', '2025-01-01')
        """)

        # Delete roadmap
        conn.execute("DELETE FROM roadmaps WHERE id = 'rm1'")

        # Track should be gone
        result = conn.execute("SELECT * FROM tracks WHERE id = 't1'").fetchone()
        assert result is None

    def test_sprint_requires_valid_track(self, db_with_schema):
        """Sprint requires valid track_id."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)

        # Sprint with valid track_id should work
        conn.execute("""
            INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
            VALUES ('s1', 't1', 'rm1', 'Sprint 1', 'not_started', '2025-01-01')
        """)

        # Sprint with invalid track_id should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
                VALUES ('s2', 'invalid', 'rm1', 'Bad Sprint', 'not_started', '2025-01-01')
            """)


class TestCheckConstraints:
    """Tests for CHECK constraints."""

    def test_roadmap_status_constraint(self, db_with_schema):
        """Roadmap status must be valid."""
        conn, _ = db_with_schema

        # Valid status works
        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)

        # Invalid status fails
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO roadmaps (id, name, version, status, created)
                VALUES ('rm2', 'Test', '1.0.0', 'invalid_status', '2025-01-01')
            """)

    def test_task_type_constraint(self, db_with_schema):
        """Task type must be valid."""
        conn, _ = db_with_schema

        # Set up hierarchy
        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
            VALUES ('s1', 't1', 'rm1', 'Sprint 1', 'not_started', '2025-01-01')
        """)

        # Valid task type works
        conn.execute("""
            INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created)
            VALUES ('task1', 's1', 't1', 'rm1', 'development', 'Test Task', 'not_started', '2025-01-01')
        """)

        # Invalid task type fails
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created)
                VALUES ('task2', 's1', 't1', 'rm1', 'invalid_type', 'Bad Task', 'not_started', '2025-01-01')
            """)

    def test_priority_constraint(self, db_with_schema):
        """Priority must be valid."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)

        # Valid priority works
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, priority, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', 'high', '2025-01-01')
        """)

        # Invalid priority fails
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO tracks (id, roadmap_id, name, status, priority, created)
                VALUES ('t2', 'rm1', 'Test', 'not_started', 'ultra_high', '2025-01-01')
            """)

    def test_quality_gate_status_constraint(self, db_with_schema):
        """Quality gate status must be valid."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)

        # Valid status works
        conn.execute("""
            INSERT INTO quality_gates (owner_type, owner_id, name, status)
            VALUES ('track', 't1', 'Test Gate', 'passed')
        """)

        # Invalid status fails
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO quality_gates (owner_type, owner_id, name, status)
                VALUES ('track', 't1', 'Bad Gate', 'invalid_status')
            """)


class TestPolymorphicTables:
    """Tests for polymorphic table structures."""

    def test_external_dependencies_owner_types(self, db_with_schema):
        """External dependencies can have different owner types."""
        conn, _ = db_with_schema

        # Insert roadmap
        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)

        # Roadmap-level dependency
        conn.execute("""
            INSERT INTO external_dependencies (owner_type, owner_id, name)
            VALUES ('roadmap', 'rm1', 'Python 3.10')
        """)

        # Track-level dependency
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO external_dependencies (owner_type, owner_id, name)
            VALUES ('track', 't1', 'SQLite 3.35')
        """)

        # Count dependencies by type
        result = conn.execute("""
            SELECT owner_type, COUNT(*) as cnt FROM external_dependencies GROUP BY owner_type
        """).fetchall()

        counts = {row["owner_type"]: row["cnt"] for row in result}
        assert counts["roadmap"] == 1
        assert counts["track"] == 1

    def test_quality_gates_owner_types(self, db_with_schema):
        """Quality gates can belong to tracks or sprints."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
            VALUES ('s1', 't1', 'rm1', 'Sprint 1', 'not_started', '2025-01-01')
        """)

        # Track-level gate
        conn.execute("""
            INSERT INTO quality_gates (owner_type, owner_id, name)
            VALUES ('track', 't1', 'Track Gate')
        """)

        # Sprint-level gate
        conn.execute("""
            INSERT INTO quality_gates (owner_type, owner_id, name)
            VALUES ('sprint', 's1', 'Sprint Gate')
        """)

        gates = conn.execute("SELECT * FROM quality_gates").fetchall()
        assert len(gates) == 2


class TestJunctionTables:
    """Tests for junction tables (many-to-many relationships)."""

    def test_entity_deliverables_junction(self, db_with_schema):
        """Deliverables can be linked to multiple entities."""
        conn, _ = db_with_schema

        # Set up hierarchy
        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
            VALUES ('s1', 't1', 'rm1', 'Sprint 1', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created)
            VALUES ('task1', 's1', 't1', 'rm1', 'development', 'Task 1', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created)
            VALUES ('task2', 's1', 't1', 'rm1', 'development', 'Task 2', 'not_started', '2025-01-01')
        """)

        # Create a shared deliverable
        conn.execute("""
            INSERT INTO deliverables (description)
            VALUES ('Shared Documentation')
        """)
        deliverable_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Link to multiple tasks
        conn.execute("""
            INSERT INTO entity_deliverables (owner_type, owner_id, deliverable_id)
            VALUES ('task', 'task1', ?)
        """, (deliverable_id,))
        conn.execute("""
            INSERT INTO entity_deliverables (owner_type, owner_id, deliverable_id)
            VALUES ('task', 'task2', ?)
        """, (deliverable_id,))

        # Verify both links
        links = conn.execute("""
            SELECT owner_id FROM entity_deliverables WHERE deliverable_id = ?
        """, (deliverable_id,)).fetchall()

        assert len(links) == 2
        assert set(r["owner_id"] for r in links) == {"task1", "task2"}

    def test_entity_commits_junction(self, db_with_schema):
        """Commits can be linked to multiple entities."""
        conn, _ = db_with_schema

        # Set up hierarchy
        conn.execute("""
            INSERT INTO roadmaps (id, name, version, status, created)
            VALUES ('rm1', 'Test', '1.0.0', 'in_progress', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tracks (id, roadmap_id, name, status, created)
            VALUES ('t1', 'rm1', 'Test', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
            VALUES ('s1', 't1', 'rm1', 'Sprint 1', 'not_started', '2025-01-01')
        """)
        conn.execute("""
            INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created)
            VALUES ('task1', 's1', 't1', 'rm1', 'development', 'Task 1', 'not_started', '2025-01-01')
        """)

        # Create a commit
        conn.execute("""
            INSERT INTO commits (commit_hash, commit_message)
            VALUES ('abc123', 'feat: implement tasks 1 and 2')
        """)
        commit_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Link to task and sprint
        conn.execute("""
            INSERT INTO entity_commits (owner_type, owner_id, commit_id)
            VALUES ('task', 'task1', ?)
        """, (commit_id,))
        conn.execute("""
            INSERT INTO entity_commits (owner_type, owner_id, commit_id)
            VALUES ('sprint', 's1', ?)
        """, (commit_id,))

        # Verify both links
        links = conn.execute("""
            SELECT owner_type, owner_id FROM entity_commits WHERE commit_id = ?
        """, (commit_id,)).fetchall()

        assert len(links) == 2


class TestUniqueConstraints:
    """Tests for unique constraints."""

    def test_entity_blocks_unique(self, db_with_schema):
        """entity_blocks has unique constraint on blocker+blocked."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id)
            VALUES ('task', 't1', 'task', 't2')
        """)

        # Duplicate should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id)
                VALUES ('task', 't1', 'task', 't2')
            """)

    def test_commits_hash_unique(self, db_with_schema):
        """Commit hash must be unique."""
        conn, _ = db_with_schema

        conn.execute("""
            INSERT INTO commits (commit_hash, commit_message)
            VALUES ('abc123', 'First commit')
        """)

        # Same hash should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO commits (commit_hash, commit_message)
                VALUES ('abc123', 'Duplicate commit')
            """)


class TestDbPathParameter:
    """Tests for using db_path parameter instead of conn."""

    def test_create_schema_with_db_path(self, temp_db_dir):
        """create_schema creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"

        create_schema(db_path=db_path)

        # Verify schema was created
        conn = get_connection(db_path=db_path)
        assert len(get_table_names(conn)) == 25

    def test_schema_exists_with_db_path(self, temp_db_dir):
        """schema_exists creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"

        # Create database but no schema
        get_connection(db_path=db_path)
        close_all_connections()

        assert schema_exists(db_path=db_path) is False

        create_schema(db_path=db_path)
        close_all_connections()

        assert schema_exists(db_path=db_path) is True

    def test_get_schema_version_with_db_path(self, temp_db_dir):
        """get_schema_version creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        create_schema(db_path=db_path)
        close_all_connections()

        version = get_schema_version(db_path=db_path)
        assert version == SCHEMA_VERSION

    def test_get_schema_version_no_schema(self, temp_db_dir):
        """get_schema_version returns None when schema doesn't exist."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        # Create database but no schema
        get_connection(db_path=db_path)
        close_all_connections()

        version = get_schema_version(db_path=db_path)
        assert version is None

    def test_drop_all_tables_with_db_path(self, temp_db_dir):
        """drop_all_tables creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        create_schema(db_path=db_path)
        close_all_connections()

        drop_all_tables(db_path=db_path)

        conn = get_connection(db_path=db_path)
        assert len(get_table_names(conn)) == 0

    def test_get_table_names_with_db_path(self, temp_db_dir):
        """get_table_names creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        create_schema(db_path=db_path)
        close_all_connections()

        tables = get_table_names(db_path=db_path)
        assert len(tables) == 25

    def test_get_index_names_with_db_path(self, temp_db_dir):
        """get_index_names creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        create_schema(db_path=db_path)
        close_all_connections()

        indexes = get_index_names(db_path=db_path)
        assert len(indexes) >= 20

    def test_validate_schema_with_db_path(self, temp_db_dir):
        """validate_schema creates connection when not provided."""
        db_path = temp_db_dir / DEFAULT_VIBEY_DIR / "roadmap.db"
        create_schema(db_path=db_path)
        close_all_connections()

        result = validate_schema(db_path=db_path)
        assert result["valid"] is True
