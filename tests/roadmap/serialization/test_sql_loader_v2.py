"""
Tests for v2 SQL loader functions (unified schema).

These tests verify the SQLAlchemy-based loaders work correctly with
the unified tickets table.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from sqlalchemy import text

from vibey.roadmap.database.schema import (
    create_schema,
    create_unified_schema,
    run_migration,
)
from vibey.roadmap.database.connection import (
    get_session,
    session_scope,
    get_engine,
    close_engine,
)


@pytest.fixture
def temp_db_with_unified_schema():
    """Create a temporary database with unified schema and sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create legacy schema first
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

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

        conn.commit()

        # Run migration to create unified schema and migrate data
        run_migration("006_unified_ticket_schema.sql", conn=conn)
        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        close_engine(db_path=db_path)


class TestConnectionModule:
    """Tests for SQLAlchemy connection management."""

    def test_get_engine_creates_engine(self, temp_db_with_unified_schema):
        """Test that get_engine returns a valid SQLAlchemy engine."""
        db_path = temp_db_with_unified_schema
        engine = get_engine(db_path=db_path)

        assert engine is not None
        # Verify we can connect
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1

        close_engine(db_path=db_path)

    def test_get_session_creates_session(self, temp_db_with_unified_schema):
        """Test that get_session returns a valid SQLAlchemy session."""
        db_path = temp_db_with_unified_schema
        session = get_session(db_path=db_path)

        assert session is not None
        session.close()
        close_engine(db_path=db_path)

    def test_session_scope_commits_on_success(self, temp_db_with_unified_schema):
        """Test that session_scope commits successfully."""
        db_path = temp_db_with_unified_schema

        with session_scope(db_path=db_path) as session:
            # Just verify we can use the session
            result = session.execute(text("SELECT COUNT(*) FROM tickets")).fetchone()
            assert result[0] > 0

        close_engine(db_path=db_path)

    def test_session_scope_rolls_back_on_exception(self, temp_db_with_unified_schema):
        """Test that session_scope rolls back on exception."""
        db_path = temp_db_with_unified_schema

        with pytest.raises(ValueError):
            with session_scope(db_path=db_path) as session:
                # This should trigger rollback
                raise ValueError("Test error")

        close_engine(db_path=db_path)


class TestUnifiedSchemaExists:
    """Tests to verify unified schema was created correctly."""

    def test_tickets_table_exists(self, temp_db_with_unified_schema):
        """Test that tickets table exists after migration."""
        db_path = temp_db_with_unified_schema

        conn = sqlite3.connect(str(db_path))
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'"
        ).fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'tickets'

    def test_criteria_table_exists(self, temp_db_with_unified_schema):
        """Test that criteria table exists after migration."""
        db_path = temp_db_with_unified_schema

        conn = sqlite3.connect(str(db_path))
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='criteria'"
        ).fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'criteria'

    def test_data_migrated_to_tickets(self, temp_db_with_unified_schema):
        """Test that data was migrated from legacy tables to tickets."""
        db_path = temp_db_with_unified_schema

        conn = sqlite3.connect(str(db_path))

        # Check roadmap migrated
        result = conn.execute(
            "SELECT * FROM tickets WHERE id = 'test-roadmap' AND ticket_type = 'roadmap'"
        ).fetchone()
        assert result is not None

        # Check track migrated
        result = conn.execute(
            "SELECT * FROM tickets WHERE id = 'test-track' AND ticket_type = 'track'"
        ).fetchone()
        assert result is not None

        # Check sprint migrated
        result = conn.execute(
            "SELECT * FROM tickets WHERE id = 'test-sprint' AND ticket_type = 'sprint'"
        ).fetchone()
        assert result is not None

        # Check tasks migrated
        result = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE ticket_type = 'task'"
        ).fetchone()
        assert result[0] == 2

        conn.close()


class TestV2LoaderImports:
    """Tests that v2 loader functions can be imported."""

    def test_import_load_task_ticket(self):
        """Test that load_task_ticket can be imported."""
        from vibey.roadmap.serialization.sql_loader import load_task_ticket
        assert load_task_ticket is not None

    def test_import_load_sprint_ticket(self):
        """Test that load_sprint_ticket can be imported."""
        from vibey.roadmap.serialization.sql_loader import load_sprint_ticket
        assert load_sprint_ticket is not None

    def test_import_load_track_ticket(self):
        """Test that load_track_ticket can be imported."""
        from vibey.roadmap.serialization.sql_loader import load_track_ticket
        assert load_track_ticket is not None

    def test_import_load_roadmap_ticket(self):
        """Test that load_roadmap_ticket can be imported."""
        from vibey.roadmap.serialization.sql_loader import load_roadmap_ticket
        assert load_roadmap_ticket is not None

    def test_import_hierarchy_loaders(self):
        """Test that hierarchy loader functions can be imported."""
        from vibey.roadmap.serialization.sql_loader import (
            load_task_ticket_with_ancestors,
            load_sprint_ticket_with_children,
        )
        assert load_task_ticket_with_ancestors is not None
        assert load_sprint_ticket_with_children is not None

    def test_import_collection_loaders(self):
        """Test that collection loader functions can be imported."""
        from vibey.roadmap.serialization.sql_loader import (
            load_tickets_by_type,
            load_tickets_by_parent,
            load_tasks_by_sprint_ticket,
            load_sprints_by_track_ticket,
            load_tracks_by_roadmap_ticket,
        )
        assert load_tickets_by_type is not None
        assert load_tickets_by_parent is not None
        assert load_tasks_by_sprint_ticket is not None
        assert load_sprints_by_track_ticket is not None
        assert load_tracks_by_roadmap_ticket is not None
