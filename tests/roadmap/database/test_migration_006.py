"""
Tests for migration 006: Unified Ticket Schema.

Verifies the migration creates the unified tickets and criteria tables
and correctly migrates data from the legacy schema.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from vibey.roadmap.database.schema import (
    create_schema,
    get_unified_schema_ddl,
    get_unified_views_ddl,
    create_unified_schema,
    has_unified_schema,
    run_migration,
    get_table_names,
    get_schema_version,
)
from vibey.roadmap.database.connection import get_connection


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        yield conn, db_path
        conn.close()


@pytest.fixture
def populated_legacy_db(temp_db):
    """Create a temp db with legacy schema and sample data."""
    conn, db_path = temp_db

    # Create legacy schema
    create_schema(conn=conn)

    # Insert sample roadmap
    conn.execute("""
        INSERT INTO roadmaps (id, name, version, status, created)
        VALUES ('test-roadmap', 'Test Roadmap', '1.0.0', 'in_progress', datetime('now'))
    """)

    # Insert sample track
    conn.execute("""
        INSERT INTO tracks (id, roadmap_id, name, status, priority, created)
        VALUES ('test-track', 'test-roadmap', 'Test Track', 'in_progress', 'high', datetime('now'))
    """)

    # Insert sample sprint
    conn.execute("""
        INSERT INTO sprints (id, track_id, roadmap_id, name, status, created)
        VALUES ('test-sprint', 'test-track', 'test-roadmap', 'Test Sprint', 'not_started', datetime('now'))
    """)

    # Insert sample tasks
    conn.execute("""
        INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created, estimated_tokens)
        VALUES ('test-task-1', 'test-sprint', 'test-track', 'test-roadmap', 'development', 'Task 1', 'not_started', datetime('now'), 100)
    """)
    conn.execute("""
        INSERT INTO tasks (id, sprint_id, track_id, roadmap_id, task_type, title, status, created, estimated_tokens)
        VALUES ('test-task-2', 'test-sprint', 'test-track', 'test-roadmap', 'development', 'Task 2', 'completed', datetime('now'), 200)
    """)

    # Insert dependency relationship
    conn.execute("""
        INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, required_status, blocks_transition_to, reason)
        VALUES ('task', 'test-task-2', 'task', 'test-task-1', 'completed', 'in_progress', 'Task 2 depends on Task 1')
    """)

    conn.commit()
    yield conn, db_path


class TestUnifiedSchemaCreation:
    """Tests for unified schema DDL creation."""

    def test_get_unified_schema_ddl_contains_tickets_table(self):
        """Test that unified schema DDL includes tickets table."""
        ddl = get_unified_schema_ddl()
        assert "CREATE TABLE IF NOT EXISTS tickets" in ddl
        assert "ticket_type TEXT NOT NULL" in ddl
        assert "parent_id TEXT REFERENCES tickets(id)" in ddl

    def test_get_unified_schema_ddl_contains_criteria_table(self):
        """Test that unified schema DDL includes criteria table."""
        ddl = get_unified_schema_ddl()
        assert "CREATE TABLE IF NOT EXISTS criteria" in ddl
        assert "target_type TEXT NOT NULL" in ddl
        assert "blocks_transition_to TEXT NOT NULL" in ddl

    def test_get_unified_views_ddl_contains_progress_views(self):
        """Test that unified views DDL includes progress views."""
        ddl = get_unified_views_ddl()
        assert "v_unified_roadmap_progress" in ddl
        assert "v_unified_track_progress" in ddl
        assert "v_unified_sprint_progress" in ddl

    def test_create_unified_schema_creates_tables(self, temp_db):
        """Test that create_unified_schema creates the necessary tables."""
        conn, db_path = temp_db

        create_unified_schema(conn=conn, include_views=False)

        tables = get_table_names(conn=conn)
        assert "tickets" in tables
        assert "criteria" in tables


class TestHasUnifiedSchema:
    """Tests for has_unified_schema function."""

    def test_has_unified_schema_false_for_empty_db(self, temp_db):
        """Test that has_unified_schema returns False for empty db."""
        conn, db_path = temp_db
        assert has_unified_schema(conn=conn) is False

    def test_has_unified_schema_false_for_legacy_only(self, populated_legacy_db):
        """Test that has_unified_schema returns False with only legacy tables."""
        conn, db_path = populated_legacy_db
        assert has_unified_schema(conn=conn) is False

    def test_has_unified_schema_true_after_creation(self, temp_db):
        """Test that has_unified_schema returns True after creation."""
        conn, db_path = temp_db
        create_unified_schema(conn=conn, include_views=False)
        assert has_unified_schema(conn=conn) is True


class TestMigration006:
    """Tests for the 006_unified_ticket_schema migration."""

    def test_migration_creates_unified_tables(self, populated_legacy_db):
        """Test that migration creates tickets and criteria tables."""
        conn, db_path = populated_legacy_db

        # Run migration
        run_migration("006_unified_ticket_schema.sql", conn=conn)

        tables = get_table_names(conn=conn)
        assert "tickets" in tables
        assert "criteria" in tables

    def test_migration_migrates_roadmap(self, populated_legacy_db):
        """Test that migration copies roadmap data."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        result = conn.execute(
            "SELECT * FROM tickets WHERE id = 'test-roadmap'"
        ).fetchone()

        assert result is not None
        assert result['ticket_type'] == 'roadmap'
        assert result['name'] == 'Test Roadmap'

    def test_migration_migrates_track(self, populated_legacy_db):
        """Test that migration copies track data."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        result = conn.execute(
            "SELECT * FROM tickets WHERE id = 'test-track'"
        ).fetchone()

        assert result is not None
        assert result['ticket_type'] == 'track'
        assert result['parent_id'] == 'test-roadmap'
        assert result['priority'] == 'high'

    def test_migration_migrates_sprint(self, populated_legacy_db):
        """Test that migration copies sprint data."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        result = conn.execute(
            "SELECT * FROM tickets WHERE id = 'test-sprint'"
        ).fetchone()

        assert result is not None
        assert result['ticket_type'] == 'sprint'
        assert result['parent_id'] == 'test-track'

    def test_migration_migrates_tasks(self, populated_legacy_db):
        """Test that migration copies task data."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        results = conn.execute(
            "SELECT * FROM tickets WHERE ticket_type = 'task' ORDER BY id"
        ).fetchall()

        assert len(results) == 2
        assert results[0]['name'] == 'Task 1'
        assert results[0]['parent_id'] == 'test-sprint'
        assert results[0]['task_type_detail'] == 'development'
        assert results[1]['name'] == 'Task 2'
        assert results[1]['status'] == 'completed'

    def test_migration_creates_dependency_criteria(self, populated_legacy_db):
        """Test that migration converts dependencies to criteria."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        results = conn.execute(
            "SELECT * FROM criteria WHERE ticket_id = 'test-task-2'"
        ).fetchall()

        assert len(results) == 1
        criterion = results[0]
        assert criterion['target_type'] == 'completable'
        assert criterion['blocks_transition_to'] == 'in_progress'
        assert 'test-task-1' in criterion['target_json']

    def test_migration_updates_schema_version(self, populated_legacy_db):
        """Test that migration updates schema version to 2.0.0."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        version = get_schema_version(conn=conn)
        assert version == '2.0.0'


class TestUnifiedViews:
    """Tests for unified schema views."""

    def test_sprint_progress_view(self, populated_legacy_db):
        """Test that sprint progress view returns correct counts."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        result = conn.execute(
            "SELECT * FROM v_unified_sprint_progress WHERE sprint_id = 'test-sprint'"
        ).fetchone()

        assert result is not None
        assert result['tasks_total'] == 2
        assert result['tasks_completed'] == 1
        assert result['completion_percent'] == 50

    def test_track_progress_view(self, populated_legacy_db):
        """Test that track progress view returns correct counts."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        result = conn.execute(
            "SELECT * FROM v_unified_track_progress WHERE track_id = 'test-track'"
        ).fetchone()

        assert result is not None
        assert result['sprints_total'] == 1
        assert result['tasks_total'] == 2
        assert result['tasks_completed'] == 1

    def test_ticket_children_view(self, populated_legacy_db):
        """Test that ticket children view shows parent-child relationships."""
        conn, db_path = populated_legacy_db

        run_migration("006_unified_ticket_schema.sql", conn=conn)

        results = conn.execute(
            "SELECT * FROM v_ticket_children WHERE parent_id = 'test-sprint'"
        ).fetchall()

        assert len(results) == 2
        child_ids = [r['child_id'] for r in results]
        assert 'test-task-1' in child_ids
        assert 'test-task-2' in child_ids
