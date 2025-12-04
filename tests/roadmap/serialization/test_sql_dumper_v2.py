"""
Tests for v2 SQL dumper functions (unified schema).

These tests verify the SQLAlchemy-based dumpers work correctly with
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
    run_migration,
)
from vibey.roadmap.database.connection import (
    session_scope,
    close_engine,
)


@pytest.fixture
def temp_db_with_unified_schema():
    """Create a temporary database with unified schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create legacy schema first (required for migration)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        create_schema(conn=conn)
        conn.commit()

        # Run migration to create unified schema
        run_migration("006_unified_ticket_schema.sql", conn=conn)
        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        close_engine(db_path=db_path)


class TestV2DumperImports:
    """Tests that v2 dumper functions can be imported."""

    def test_import_save_task_ticket(self):
        """Test that save_task_ticket can be imported."""
        from vibey.roadmap.serialization.sql_dumper import save_task_ticket
        assert save_task_ticket is not None

    def test_import_save_sprint_ticket(self):
        """Test that save_sprint_ticket can be imported."""
        from vibey.roadmap.serialization.sql_dumper import save_sprint_ticket
        assert save_sprint_ticket is not None

    def test_import_save_track_ticket(self):
        """Test that save_track_ticket can be imported."""
        from vibey.roadmap.serialization.sql_dumper import save_track_ticket
        assert save_track_ticket is not None

    def test_import_save_roadmap_ticket(self):
        """Test that save_roadmap_ticket can be imported."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap_ticket
        assert save_roadmap_ticket is not None

    def test_import_save_ticket(self):
        """Test that save_ticket dispatcher can be imported."""
        from vibey.roadmap.serialization.sql_dumper import save_ticket
        assert save_ticket is not None

    def test_import_transaction_savers(self):
        """Test that transaction save functions can be imported."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_sprint_with_tasks,
            save_track_with_sprints,
            save_full_roadmap_tickets,
        )
        assert save_sprint_with_tasks is not None
        assert save_track_with_sprints is not None
        assert save_full_roadmap_tickets is not None

    def test_import_delete_functions(self):
        """Test that delete functions can be imported."""
        from vibey.roadmap.serialization.sql_dumper import (
            delete_ticket,
            delete_tickets_by_parent,
        )
        assert delete_ticket is not None
        assert delete_tickets_by_parent is not None


class TestSaveRoadmapTicket:
    """Tests for save_roadmap_ticket function."""

    def test_save_roadmap_ticket_creates_record(self, temp_db_with_unified_schema):
        """Test that save_roadmap_ticket creates a record in tickets table."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap_ticket
        from vibey.roadmap.models.ticket.domain import RoadmapTicket

        db_path = temp_db_with_unified_schema

        roadmap = RoadmapTicket(
            id="test-roadmap-new",
            name="New Test Roadmap",
        )

        save_roadmap_ticket(roadmap, db_path=db_path)

        # Verify record was created
        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT * FROM tickets WHERE id = 'test-roadmap-new'")
            ).fetchone()

            assert result is not None
            assert result.name == "New Test Roadmap"
            assert result.ticket_type == "roadmap"


class TestSaveTrackTicket:
    """Tests for save_track_ticket function."""

    def test_save_track_ticket_creates_record(self, temp_db_with_unified_schema):
        """Test that save_track_ticket creates a record in tickets table."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
        )
        from vibey.roadmap.models.ticket.domain import RoadmapTicket, TrackTicket

        db_path = temp_db_with_unified_schema

        # First create parent roadmap
        roadmap = RoadmapTicket(
            id="test-roadmap-parent",
            name="Parent Roadmap",
        )
        save_roadmap_ticket(roadmap, db_path=db_path)

        # Then create track
        track = TrackTicket(
            id="test-track-new",
            name="New Test Track",
            parent_ref="test-roadmap-parent",
            roadmap_id="test-roadmap-parent",
        )

        save_track_ticket(track, db_path=db_path)

        # Verify record was created
        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT * FROM tickets WHERE id = 'test-track-new'")
            ).fetchone()

            assert result is not None
            assert result.name == "New Test Track"
            assert result.ticket_type == "track"
            assert result.parent_id == "test-roadmap-parent"


class TestSaveSprintTicket:
    """Tests for save_sprint_ticket function."""

    def test_save_sprint_ticket_creates_record(self, temp_db_with_unified_schema):
        """Test that save_sprint_ticket creates a record in tickets table."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
        )
        from vibey.roadmap.models.ticket.domain import (
            RoadmapTicket,
            TrackTicket,
            SprintTicket,
        )

        db_path = temp_db_with_unified_schema

        # Create parent hierarchy
        roadmap = RoadmapTicket(id="roadmap-1", name="Roadmap")
        save_roadmap_ticket(roadmap, db_path=db_path)

        track = TrackTicket(
            id="track-1",
            name="Track",
            parent_ref="roadmap-1",
            roadmap_id="roadmap-1",
        )
        save_track_ticket(track, db_path=db_path)

        # Create sprint
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
        )
        save_sprint_ticket(sprint, db_path=db_path)

        # Verify record was created
        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT * FROM tickets WHERE id = 'sprint-1'")
            ).fetchone()

            assert result is not None
            assert result.name == "Sprint 1"
            assert result.ticket_type == "sprint"
            assert result.parent_id == "track-1"


class TestSaveTaskTicket:
    """Tests for save_task_ticket function."""

    def test_save_task_ticket_creates_record(self, temp_db_with_unified_schema):
        """Test that save_task_ticket creates a record in tickets table."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
            save_task_ticket,
        )
        from vibey.roadmap.models.ticket.domain import (
            RoadmapTicket,
            TrackTicket,
            SprintTicket,
            TaskTicket,
        )

        db_path = temp_db_with_unified_schema

        # Create parent hierarchy
        roadmap = RoadmapTicket(id="roadmap-2", name="Roadmap")
        save_roadmap_ticket(roadmap, db_path=db_path)

        track = TrackTicket(
            id="track-2",
            name="Track",
            parent_ref="roadmap-2",
            roadmap_id="roadmap-2",
        )
        save_track_ticket(track, db_path=db_path)

        sprint = SprintTicket(
            id="sprint-2",
            name="Sprint",
            parent_ref="track-2",
            track_id="track-2",
            roadmap_id="roadmap-2",
        )
        save_sprint_ticket(sprint, db_path=db_path)

        # Create task
        task = TaskTicket(
            id="task-1",
            name="Task 1",
            parent_ref="sprint-2",
            sprint_id="sprint-2",
            track_id="track-2",
            roadmap_id="roadmap-2",
            estimated_tokens=100,
        )
        save_task_ticket(task, db_path=db_path)

        # Verify record was created
        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT * FROM tickets WHERE id = 'task-1'")
            ).fetchone()

            assert result is not None
            assert result.name == "Task 1"
            assert result.ticket_type == "task"
            assert result.parent_id == "sprint-2"
            assert result.estimated_tokens == 100


class TestSaveTicketDispatcher:
    """Tests for save_ticket dispatcher function."""

    def test_save_ticket_dispatches_to_roadmap(self, temp_db_with_unified_schema):
        """Test that save_ticket correctly dispatches RoadmapTicket."""
        from vibey.roadmap.serialization.sql_dumper import save_ticket
        from vibey.roadmap.models.ticket.domain import RoadmapTicket

        db_path = temp_db_with_unified_schema

        roadmap = RoadmapTicket(id="dispatch-roadmap", name="Dispatched Roadmap")
        save_ticket(roadmap, db_path=db_path)

        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT ticket_type FROM tickets WHERE id = 'dispatch-roadmap'")
            ).fetchone()
            assert result.ticket_type == "roadmap"

    def test_save_ticket_raises_for_unknown_type(self, temp_db_with_unified_schema):
        """Test that save_ticket raises TypeError for unknown types."""
        from vibey.roadmap.serialization.sql_dumper import save_ticket

        db_path = temp_db_with_unified_schema

        with pytest.raises(TypeError, match="Unknown ticket type"):
            save_ticket("not a ticket", db_path=db_path)


class TestDeleteTicket:
    """Tests for delete_ticket function."""

    def test_delete_ticket_removes_record(self, temp_db_with_unified_schema):
        """Test that delete_ticket removes a ticket."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            delete_ticket,
        )
        from vibey.roadmap.models.ticket.domain import RoadmapTicket

        db_path = temp_db_with_unified_schema

        roadmap = RoadmapTicket(id="to-delete", name="To Delete")
        save_roadmap_ticket(roadmap, db_path=db_path)

        # Verify it exists
        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT id FROM tickets WHERE id = 'to-delete'")
            ).fetchone()
            assert result is not None

        # Delete it
        deleted = delete_ticket("to-delete", db_path=db_path)
        assert deleted is True

        # Verify it's gone
        with session_scope(db_path=db_path) as session:
            result = session.execute(
                text("SELECT id FROM tickets WHERE id = 'to-delete'")
            ).fetchone()
            assert result is None

    def test_delete_ticket_returns_false_if_not_found(self, temp_db_with_unified_schema):
        """Test that delete_ticket returns False for non-existent ticket."""
        from vibey.roadmap.serialization.sql_dumper import delete_ticket

        db_path = temp_db_with_unified_schema

        deleted = delete_ticket("non-existent-ticket", db_path=db_path)
        assert deleted is False
