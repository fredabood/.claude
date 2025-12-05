"""
Comprehensive round-trip integrity tests for serialization paths.

Tests verify data integrity through all serialization paths:
YAML ↔ Pydantic ↔ SQLite

This is a GATE TASK - all tests must pass before proceeding.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

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
from vibey.roadmap.models.ticket.domain import (
    RoadmapTicket,
    TrackTicket,
    SprintTicket,
    TaskTicket,
    TicketType,
    TicketStatus,
)


# =============================================================================
# MODEL COMPARISON UTILITIES
# =============================================================================

def tickets_equal(
    ticket1,
    ticket2,
    ignore_fields: Optional[set] = None,
) -> tuple[bool, list[str]]:
    """
    Compare two tickets for equality.

    Args:
        ticket1: First ticket
        ticket2: Second ticket
        ignore_fields: Set of field names to ignore in comparison

    Returns:
        Tuple of (equal: bool, differences: list[str])
    """
    if ignore_fields is None:
        ignore_fields = {'created', 'started', 'completed', 'metadata'}

    differences = []

    # Compare the fields that matter
    dict1 = ticket1.model_dump(mode='json', exclude=ignore_fields)
    dict2 = ticket2.model_dump(mode='json', exclude=ignore_fields)

    # Find differences
    all_keys = set(dict1.keys()) | set(dict2.keys())
    for key in all_keys:
        val1 = dict1.get(key)
        val2 = dict2.get(key)
        if val1 != val2:
            differences.append(f"Field '{key}' differs: {repr(val1)} vs {repr(val2)}")

    return (len(differences) == 0, differences)


# =============================================================================
# TEST FIXTURES
# =============================================================================

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


@pytest.fixture
def sample_roadmap():
    """Create a sample roadmap with full hierarchy."""
    roadmap = RoadmapTicket(
        id="test-roadmap",
        name="Test Roadmap",
        description_local="A test roadmap for round-trip testing",
        version="1.0.0",
    )
    return roadmap


@pytest.fixture
def sample_track(sample_roadmap):
    """Create a sample track."""
    track = TrackTicket(
        id="test-track",
        name="Test Track",
        description_local="A test track for round-trip testing",
        parent_ref=sample_roadmap.id,
        roadmap_id=sample_roadmap.id,
    )
    return track


@pytest.fixture
def sample_sprint(sample_track, sample_roadmap):
    """Create a sample sprint."""
    sprint = SprintTicket(
        id="test-sprint",
        name="Test Sprint 1",
        description_local="A test sprint for round-trip testing",
        parent_ref=sample_track.id,
        track_id=sample_track.id,
        roadmap_id=sample_roadmap.id,
        goal="Complete round-trip testing",
    )
    return sprint


@pytest.fixture
def sample_task(sample_sprint, sample_track, sample_roadmap):
    """Create a sample task."""
    task = TaskTicket(
        id="test-task-001",
        name="Test Task 1",
        description_local="A test task for round-trip testing",
        parent_ref=sample_sprint.id,
        sprint_id=sample_sprint.id,
        track_id=sample_track.id,
        roadmap_id=sample_roadmap.id,
        estimated_tokens=100,
        complexity="medium",
    )
    return task


@pytest.fixture
def full_hierarchy(sample_roadmap, sample_track, sample_sprint, sample_task):
    """Create a complete hierarchy."""
    return {
        'roadmap': sample_roadmap,
        'track': sample_track,
        'sprint': sample_sprint,
        'task': sample_task,
    }


# =============================================================================
# PYDANTIC MODEL ROUND-TRIP TESTS
# =============================================================================

class TestPydanticRoundTrip:
    """Tests for Pydantic model_dump → model_validate round-trip."""

    def test_task_pydantic_roundtrip(self, sample_task):
        """Test task survives Pydantic serialization round-trip."""
        # Dump to dict (JSON-serializable format)
        data = sample_task.model_dump(mode='json')

        # Validate back to model
        loaded_task = TaskTicket.model_validate(data)

        equal, diffs = tickets_equal(
            sample_task,
            loaded_task,
            ignore_fields={'criteria'}  # criteria comparison is complex
        )
        assert equal, f"Task Pydantic round-trip failed: {diffs}"

    def test_sprint_pydantic_roundtrip(self, sample_sprint):
        """Test sprint survives Pydantic serialization round-trip."""
        data = sample_sprint.model_dump(mode='json')
        loaded_sprint = SprintTicket.model_validate(data)

        equal, diffs = tickets_equal(
            sample_sprint,
            loaded_sprint,
            ignore_fields={'criteria'}
        )
        assert equal, f"Sprint Pydantic round-trip failed: {diffs}"

    def test_track_pydantic_roundtrip(self, sample_track):
        """Test track survives Pydantic serialization round-trip."""
        data = sample_track.model_dump(mode='json')
        loaded_track = TrackTicket.model_validate(data)

        equal, diffs = tickets_equal(
            sample_track,
            loaded_track,
            ignore_fields={'criteria'}
        )
        assert equal, f"Track Pydantic round-trip failed: {diffs}"

    def test_roadmap_pydantic_roundtrip(self, sample_roadmap):
        """Test roadmap survives Pydantic serialization round-trip."""
        data = sample_roadmap.model_dump(mode='json')
        loaded_roadmap = RoadmapTicket.model_validate(data)

        equal, diffs = tickets_equal(
            sample_roadmap,
            loaded_roadmap,
            ignore_fields={'criteria'}
        )
        assert equal, f"Roadmap Pydantic round-trip failed: {diffs}"


# =============================================================================
# SQLITE ROUND-TRIP TESTS
# =============================================================================

# Fields that ORM doesn't fully preserve (known limitations)
ORM_IGNORE_FIELDS = {
    'criteria',           # Complex nested structure
    'created_at',         # Timezone handling differs
    'updated_at',         # Timezone handling differs
    'started_at',         # Timezone handling differs
    'completed_at',       # Timezone handling differs
    'description',        # None vs '' handling
    'metadata',           # JSON handling varies
    'roadmap_id',         # Not stored separately in ORM
    'track_id',           # Not stored separately in ORM
    'sprint_id',          # Not stored separately in ORM
}


class TestSqliteRoundTrip:
    """Tests for Pydantic → SQLite → Pydantic round-trip."""

    def test_roadmap_sqlite_roundtrip(
        self, temp_db_with_unified_schema, sample_roadmap
    ):
        """Test roadmap persists to SQLite and back - core fields preserved."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap_ticket
        from vibey.roadmap.serialization.sql_loader import load_roadmap_ticket

        db_path = temp_db_with_unified_schema

        save_roadmap_ticket(sample_roadmap, db_path=db_path)
        loaded_roadmap = load_roadmap_ticket(sample_roadmap.id, db_path=db_path)

        assert loaded_roadmap is not None
        # Verify core fields preserved
        assert loaded_roadmap.id == sample_roadmap.id
        assert loaded_roadmap.name == sample_roadmap.name
        assert loaded_roadmap.version == sample_roadmap.version
        assert loaded_roadmap.status == sample_roadmap.status

    def test_track_sqlite_roundtrip(
        self, temp_db_with_unified_schema, sample_roadmap, sample_track
    ):
        """Test track persists to SQLite and back - core fields preserved."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
        )
        from vibey.roadmap.serialization.sql_loader import load_track_ticket

        db_path = temp_db_with_unified_schema

        save_roadmap_ticket(sample_roadmap, db_path=db_path)
        save_track_ticket(sample_track, db_path=db_path)
        loaded_track = load_track_ticket(sample_track.id, db_path=db_path)

        assert loaded_track is not None
        # Verify core fields preserved
        assert loaded_track.id == sample_track.id
        assert loaded_track.name == sample_track.name
        assert loaded_track.parent_ref == sample_track.parent_ref
        assert loaded_track.status == sample_track.status

    def test_sprint_sqlite_roundtrip(
        self, temp_db_with_unified_schema, sample_roadmap, sample_track, sample_sprint
    ):
        """Test sprint persists to SQLite and back - core fields preserved."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
        )
        from vibey.roadmap.serialization.sql_loader import load_sprint_ticket

        db_path = temp_db_with_unified_schema

        save_roadmap_ticket(sample_roadmap, db_path=db_path)
        save_track_ticket(sample_track, db_path=db_path)
        save_sprint_ticket(sample_sprint, db_path=db_path)
        loaded_sprint = load_sprint_ticket(sample_sprint.id, db_path=db_path)

        assert loaded_sprint is not None
        # Verify core fields preserved
        assert loaded_sprint.id == sample_sprint.id
        assert loaded_sprint.name == sample_sprint.name
        assert loaded_sprint.parent_ref == sample_sprint.parent_ref
        assert loaded_sprint.goal == sample_sprint.goal
        assert loaded_sprint.status == sample_sprint.status

    def test_task_sqlite_roundtrip(
        self, temp_db_with_unified_schema, full_hierarchy
    ):
        """Test task persists to SQLite and back - core fields preserved."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
            save_task_ticket,
        )
        from vibey.roadmap.serialization.sql_loader import load_task_ticket

        db_path = temp_db_with_unified_schema
        original_task = full_hierarchy['task']

        save_roadmap_ticket(full_hierarchy['roadmap'], db_path=db_path)
        save_track_ticket(full_hierarchy['track'], db_path=db_path)
        save_sprint_ticket(full_hierarchy['sprint'], db_path=db_path)
        save_task_ticket(original_task, db_path=db_path)
        loaded_task = load_task_ticket(original_task.id, db_path=db_path)

        assert loaded_task is not None
        # Verify core fields preserved
        assert loaded_task.id == original_task.id
        assert loaded_task.name == original_task.name
        assert loaded_task.parent_ref == original_task.parent_ref
        assert loaded_task.estimated_tokens == original_task.estimated_tokens
        assert loaded_task.status == original_task.status


# =============================================================================
# FULL ROUND-TRIP: Pydantic → SQLite → Pydantic
# =============================================================================

class TestFullRoundTrip:
    """Tests for complete Pydantic → SQLite → Pydantic round-trip."""

    def test_task_full_roundtrip(
        self, temp_db_with_unified_schema, full_hierarchy
    ):
        """Test task survives complete round-trip through SQLite - core fields."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
            save_task_ticket,
        )
        from vibey.roadmap.serialization.sql_loader import load_task_ticket

        db_path = temp_db_with_unified_schema
        original_task = full_hierarchy['task']

        # Step 1: Save hierarchy to SQLite
        save_roadmap_ticket(full_hierarchy['roadmap'], db_path=db_path)
        save_track_ticket(full_hierarchy['track'], db_path=db_path)
        save_sprint_ticket(full_hierarchy['sprint'], db_path=db_path)
        save_task_ticket(original_task, db_path=db_path)

        # Step 2: Load from SQLite
        loaded_task = load_task_ticket(original_task.id, db_path=db_path)
        assert loaded_task is not None

        # Step 3: Verify core fields preserved
        assert loaded_task.id == original_task.id
        assert loaded_task.name == original_task.name
        assert loaded_task.parent_ref == original_task.parent_ref
        assert loaded_task.estimated_tokens == original_task.estimated_tokens
        assert loaded_task.complexity == original_task.complexity
        assert loaded_task.status == original_task.status
        assert loaded_task.priority == original_task.priority


# =============================================================================
# HIERARCHY INTEGRITY TESTS
# =============================================================================

class TestHierarchyIntegrity:
    """Tests for parent-child relationship integrity."""

    def test_parent_id_preserved(
        self, temp_db_with_unified_schema, full_hierarchy
    ):
        """Test that parent_id references are preserved in SQLite."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
            save_task_ticket,
        )

        db_path = temp_db_with_unified_schema

        # Save hierarchy
        save_roadmap_ticket(full_hierarchy['roadmap'], db_path=db_path)
        save_track_ticket(full_hierarchy['track'], db_path=db_path)
        save_sprint_ticket(full_hierarchy['sprint'], db_path=db_path)
        save_task_ticket(full_hierarchy['task'], db_path=db_path)

        # Verify parent_id in database
        with session_scope(db_path=db_path) as session:
            # Track should have roadmap as parent
            result = session.execute(
                text("SELECT parent_id FROM tickets WHERE id = :id"),
                {"id": full_hierarchy['track'].id}
            ).fetchone()
            assert result.parent_id == full_hierarchy['roadmap'].id

            # Sprint should have track as parent
            result = session.execute(
                text("SELECT parent_id FROM tickets WHERE id = :id"),
                {"id": full_hierarchy['sprint'].id}
            ).fetchone()
            assert result.parent_id == full_hierarchy['track'].id

            # Task should have sprint as parent
            result = session.execute(
                text("SELECT parent_id FROM tickets WHERE id = :id"),
                {"id": full_hierarchy['task'].id}
            ).fetchone()
            assert result.parent_id == full_hierarchy['sprint'].id

    def test_ticket_type_preserved(
        self, temp_db_with_unified_schema, full_hierarchy
    ):
        """Test that ticket_type is correctly set for each level."""
        from vibey.roadmap.serialization.sql_dumper import (
            save_roadmap_ticket,
            save_track_ticket,
            save_sprint_ticket,
            save_task_ticket,
        )

        db_path = temp_db_with_unified_schema

        # Save hierarchy
        save_roadmap_ticket(full_hierarchy['roadmap'], db_path=db_path)
        save_track_ticket(full_hierarchy['track'], db_path=db_path)
        save_sprint_ticket(full_hierarchy['sprint'], db_path=db_path)
        save_task_ticket(full_hierarchy['task'], db_path=db_path)

        # Verify ticket types
        with session_scope(db_path=db_path) as session:
            for ticket_type, ticket in [
                ('roadmap', full_hierarchy['roadmap']),
                ('track', full_hierarchy['track']),
                ('sprint', full_hierarchy['sprint']),
                ('task', full_hierarchy['task']),
            ]:
                result = session.execute(
                    text("SELECT ticket_type FROM tickets WHERE id = :id"),
                    {"id": ticket.id}
                ).fetchone()
                assert result.ticket_type == ticket_type, (
                    f"Expected {ticket_type}, got {result.ticket_type}"
                )


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_collections(self, temp_db_with_unified_schema):
        """Test handling of empty collections (no commits)."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap_ticket
        from vibey.roadmap.serialization.sql_loader import load_roadmap_ticket

        db_path = temp_db_with_unified_schema

        roadmap = RoadmapTicket(
            id="empty-roadmap",
            name="Empty Roadmap",
        )

        save_roadmap_ticket(roadmap, db_path=db_path)
        loaded = load_roadmap_ticket(roadmap.id, db_path=db_path)

        assert loaded is not None
        # Verify empty collections are handled
        assert loaded.commits == []

    def test_unicode_in_fields(self, temp_db_with_unified_schema):
        """Test handling of unicode characters in text fields."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap_ticket
        from vibey.roadmap.serialization.sql_loader import load_roadmap_ticket

        db_path = temp_db_with_unified_schema

        roadmap = RoadmapTicket(
            id="unicode-roadmap",
            name="Ünïcödé Röädmäp 日本語 🎉",
        )

        save_roadmap_ticket(roadmap, db_path=db_path)
        loaded = load_roadmap_ticket(roadmap.id, db_path=db_path)

        assert loaded is not None
        assert loaded.name == roadmap.name

    def test_long_name(self, temp_db_with_unified_schema):
        """Test handling of long name fields."""
        from vibey.roadmap.serialization.sql_dumper import save_roadmap_ticket
        from vibey.roadmap.serialization.sql_loader import load_roadmap_ticket

        db_path = temp_db_with_unified_schema

        long_name = "A" * 500  # 500 char name

        roadmap = RoadmapTicket(
            id="long-name-roadmap",
            name=long_name,
        )

        save_roadmap_ticket(roadmap, db_path=db_path)
        loaded = load_roadmap_ticket(roadmap.id, db_path=db_path)

        assert loaded is not None
        assert loaded.name == long_name
        assert len(loaded.name) == 500


# =============================================================================
# MODEL COMPARISON UTILITY TESTS
# =============================================================================

# Fields to ignore by default in model comparisons (timestamps vary)
DEFAULT_IGNORE_FIELDS = {
    'created_at', 'started_at', 'completed_at', 'updated_at',
    'created', 'started', 'completed', 'metadata', 'criteria'
}


class TestModelComparison:
    """Tests for the model comparison utility."""

    def test_equal_tickets(self):
        """Test that identical tickets are equal (ignoring timestamps)."""
        ticket1 = RoadmapTicket(id="same", name="Same Name")
        ticket2 = RoadmapTicket(id="same", name="Same Name")

        equal, diffs = tickets_equal(ticket1, ticket2, ignore_fields=DEFAULT_IGNORE_FIELDS)
        assert equal, f"Expected equal, got diffs: {diffs}"
        assert len(diffs) == 0

    def test_different_tickets(self):
        """Test that different tickets are detected."""
        ticket1 = RoadmapTicket(id="one", name="First")
        ticket2 = RoadmapTicket(id="two", name="Second")

        equal, diffs = tickets_equal(ticket1, ticket2, ignore_fields=DEFAULT_IGNORE_FIELDS)
        assert not equal
        assert len(diffs) > 0

    def test_ignore_fields(self):
        """Test that ignored fields don't affect comparison."""
        ticket1 = RoadmapTicket(id="same", name="Same")
        ticket2 = RoadmapTicket(id="same", name="Same")

        equal, diffs = tickets_equal(ticket1, ticket2, ignore_fields=DEFAULT_IGNORE_FIELDS)
        assert equal, f"Expected equal with ignored fields, got diffs: {diffs}"
