"""
Tests for session SQLite serialization.

Sprint 3.2 Task 8: Integration Testing
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.models.session import (
    Session,
    SessionStatus,
    SessionEvent,
    SessionEventType,
    Decision,
    DecisionCategory,
    DecisionConfidence,
    ContextSnapshot,
    SessionCommit,
)
from vibey.roadmap.serialization.session_sql import (
    load_session,
    list_sessions,
    get_active_session,
    get_sessions_by_commit,
    get_sessions_by_task,
    save_session,
    delete_session,
    ensure_session_tables,
    _parse_datetime,
    _format_datetime,
    _parse_json,
    _dump_json,
    _to_path,
)
from vibey.roadmap.database import get_connection
from vibey.roadmap.database.schema import create_schema


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / ".vibey" / "roadmap.db"
    db_path.parent.mkdir(parents=True)

    # Initialize database with base schema first (creates database_state table)
    create_schema(db_path=db_path)

    # Then add session tables
    ensure_session_tables(str(db_path))

    yield str(db_path)

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    now = datetime.now(timezone.utc)
    return Session(
        id="01KCTEST12345678901234567",
        name="Test Session",
        status=SessionStatus.ACTIVE,
        created=now,
        started=now,
        roadmap_id="test-roadmap",
        track_id="test-track",
        sprint_id="test-sprint",
        task_ids=["task-1", "task-2"],
        branch="main",
        start_commit="abc123",
        goals=["Goal 1", "Goal 2"],
        events=[
            SessionEvent(
                id="01KCEVENT123456789012345",
                session_id="01KCTEST12345678901234567",
                timestamp=now,
                event_type=SessionEventType.SESSION_START,
                data={"name": "Test Session"},
            ),
        ],
        commits=[
            SessionCommit(
                session_id="01KCTEST12345678901234567",
                commit_sha="abc123def456",
                short_sha="abc123d",
                timestamp=now,
                message="Test commit",
                author="Test Author",
            ),
        ],
        metadata={"key": "value"},
    )


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_to_path_with_string(self):
        """Test _to_path with string input."""
        result = _to_path("/some/path")
        assert isinstance(result, Path)
        assert str(result) == "/some/path"

    def test_to_path_with_path(self):
        """Test _to_path with Path input."""
        path = Path("/some/path")
        result = _to_path(path)
        assert result is path

    def test_to_path_with_none(self):
        """Test _to_path with None input."""
        result = _to_path(None)
        assert result is None

    def test_parse_datetime_iso(self):
        """Test parsing ISO datetime string."""
        result = _parse_datetime("2025-01-15T10:30:00+00:00")
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo is not None

    def test_parse_datetime_z_suffix(self):
        """Test parsing datetime with Z suffix."""
        result = _parse_datetime("2025-01-15T10:30:00Z")
        assert result is not None
        assert result.tzinfo is not None

    def test_parse_datetime_none(self):
        """Test parsing None returns None."""
        result = _parse_datetime(None)
        assert result is None

    def test_parse_datetime_already_datetime(self):
        """Test parsing datetime object passes through."""
        now = datetime.now(timezone.utc)
        result = _parse_datetime(now)
        assert result == now

    def test_format_datetime(self):
        """Test formatting datetime."""
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _format_datetime(dt)
        assert "2025-01-15" in result
        assert "10:30:00" in result

    def test_format_datetime_none(self):
        """Test formatting None returns None."""
        result = _format_datetime(None)
        assert result is None

    def test_parse_json_valid(self):
        """Test parsing valid JSON."""
        result = _parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_none(self):
        """Test parsing None returns default."""
        result = _parse_json(None, {"default": True})
        assert result == {"default": True}

    def test_parse_json_invalid(self):
        """Test parsing invalid JSON returns default."""
        result = _parse_json("not json", {"default": True})
        assert result == {"default": True}

    def test_dump_json(self):
        """Test dumping to JSON."""
        result = _dump_json({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_dump_json_none(self):
        """Test dumping None returns None."""
        result = _dump_json(None)
        assert result is None


class TestSessionSaving:
    """Tests for saving sessions to SQLite."""

    def test_save_basic_session(self, temp_db, sample_session):
        """Test saving a basic session."""
        save_session(sample_session, temp_db)

        # Verify it was saved
        loaded = load_session(sample_session.id, temp_db)
        assert loaded is not None
        assert loaded.id == sample_session.id
        assert loaded.name == sample_session.name

    def test_save_session_with_events(self, temp_db, sample_session):
        """Test saving session with events."""
        save_session(sample_session, temp_db)

        loaded = load_session(sample_session.id, temp_db)
        assert len(loaded.events) == 1
        assert loaded.events[0].event_type == SessionEventType.SESSION_START

    def test_save_session_with_commits(self, temp_db, sample_session):
        """Test saving session with commits."""
        save_session(sample_session, temp_db)

        loaded = load_session(sample_session.id, temp_db)
        assert len(loaded.commits) == 1
        assert loaded.commits[0].commit_sha == "abc123def456"

    def test_save_session_with_tasks(self, temp_db, sample_session):
        """Test saving session with task associations."""
        save_session(sample_session, temp_db)

        loaded = load_session(sample_session.id, temp_db)
        assert "task-1" in loaded.task_ids
        assert "task-2" in loaded.task_ids

    def test_save_session_update(self, temp_db, sample_session):
        """Test updating an existing session."""
        save_session(sample_session, temp_db)

        # Update and save again
        sample_session.name = "Updated Session"
        sample_session.status = SessionStatus.COMPLETED
        save_session(sample_session, temp_db)

        loaded = load_session(sample_session.id, temp_db)
        assert loaded.name == "Updated Session"
        assert loaded.status == SessionStatus.COMPLETED


class TestSessionLoading:
    """Tests for loading sessions from SQLite."""

    def test_load_session(self, temp_db, sample_session):
        """Test loading a session."""
        save_session(sample_session, temp_db)

        loaded = load_session(sample_session.id, temp_db)
        assert loaded is not None
        assert loaded.id == sample_session.id

    def test_load_session_not_found(self, temp_db):
        """Test loading non-existent session returns None."""
        result = load_session("nonexistent-id", temp_db)
        assert result is None

    def test_load_session_preserves_status(self, temp_db, sample_session):
        """Test status is preserved through save/load."""
        sample_session.status = SessionStatus.PAUSED
        save_session(sample_session, temp_db)

        loaded = load_session(sample_session.id, temp_db)
        assert loaded.status == SessionStatus.PAUSED


class TestSessionListing:
    """Tests for listing sessions."""

    def test_list_all_sessions(self, temp_db):
        """Test listing all sessions."""
        now = datetime.now(timezone.utc)

        # Create multiple sessions
        for i in range(3):
            session = Session(
                id=f"01KCTEST{i:020d}",
                name=f"Session {i}",
                status=SessionStatus.COMPLETED,
                created=now,
                roadmap_id="test-roadmap",
            )
            save_session(session, temp_db)

        sessions = list_sessions(temp_db)
        assert len(sessions) == 3

    def test_list_sessions_by_status(self, temp_db):
        """Test filtering sessions by status."""
        now = datetime.now(timezone.utc)

        # Create sessions with different statuses
        session1 = Session(
            id="01KCSESSION1234567890123",
            name="Active Session",
            status=SessionStatus.ACTIVE,
            created=now,
            roadmap_id="test",
        )
        session2 = Session(
            id="01KCSESSION2234567890123",
            name="Completed Session",
            status=SessionStatus.COMPLETED,
            created=now,
            roadmap_id="test",
        )

        save_session(session1, temp_db)
        save_session(session2, temp_db)

        # Filter by active
        active = list_sessions(temp_db, status=SessionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "Active Session"

        # Filter by completed
        completed = list_sessions(temp_db, status=SessionStatus.COMPLETED)
        assert len(completed) == 1
        assert completed[0].name == "Completed Session"

    def test_list_sessions_by_track(self, temp_db):
        """Test filtering sessions by track."""
        now = datetime.now(timezone.utc)

        session1 = Session(
            id="01KCSESSION1234567890123",
            name="Track A Session",
            status=SessionStatus.COMPLETED,
            created=now,
            roadmap_id="test",
            track_id="track-a",
        )
        session2 = Session(
            id="01KCSESSION2234567890123",
            name="Track B Session",
            status=SessionStatus.COMPLETED,
            created=now,
            roadmap_id="test",
            track_id="track-b",
        )

        save_session(session1, temp_db)
        save_session(session2, temp_db)

        # Filter by track
        result = list_sessions(temp_db, track_id="track-a")
        assert len(result) == 1
        assert result[0].track_id == "track-a"

    def test_list_sessions_limit(self, temp_db):
        """Test listing with limit."""
        now = datetime.now(timezone.utc)

        # Create 5 sessions
        for i in range(5):
            session = Session(
                id=f"01KCTEST{i:020d}",
                name=f"Session {i}",
                status=SessionStatus.COMPLETED,
                created=now,
                roadmap_id="test",
            )
            save_session(session, temp_db)

        # Limit to 2
        sessions = list_sessions(temp_db, limit=2)
        assert len(sessions) == 2


class TestActiveSession:
    """Tests for active session queries."""

    def test_get_active_session(self, temp_db, sample_session):
        """Test getting active session."""
        save_session(sample_session, temp_db)

        active = get_active_session(temp_db)
        assert active is not None
        assert active.id == sample_session.id

    def test_get_active_session_none(self, temp_db):
        """Test getting active session when none exists."""
        active = get_active_session(temp_db)
        assert active is None


class TestSessionQueries:
    """Tests for session queries."""

    def test_get_sessions_by_commit(self, temp_db, sample_session):
        """Test getting sessions by commit."""
        save_session(sample_session, temp_db)

        sessions = get_sessions_by_commit("abc123def456", temp_db)
        assert len(sessions) == 1
        assert sessions[0].id == sample_session.id

    def test_get_sessions_by_commit_not_found(self, temp_db):
        """Test getting sessions by non-existent commit."""
        sessions = get_sessions_by_commit("nonexistent", temp_db)
        assert len(sessions) == 0

    def test_get_sessions_by_task(self, temp_db, sample_session):
        """Test getting sessions by task."""
        save_session(sample_session, temp_db)

        sessions = get_sessions_by_task("task-1", temp_db)
        assert len(sessions) == 1
        assert sessions[0].id == sample_session.id


class TestSessionDeletion:
    """Tests for session deletion."""

    def test_delete_session(self, temp_db, sample_session):
        """Test deleting a session."""
        save_session(sample_session, temp_db)

        # Delete
        result = delete_session(sample_session.id, temp_db)
        assert result is True

        # Verify deleted
        loaded = load_session(sample_session.id, temp_db)
        assert loaded is None

    def test_delete_session_not_found(self, temp_db):
        """Test deleting non-existent session."""
        result = delete_session("nonexistent-id", temp_db)
        assert result is False

    def test_delete_session_cascades(self, temp_db, sample_session):
        """Test delete cascades to events, commits, tasks."""
        save_session(sample_session, temp_db)

        # Delete
        delete_session(sample_session.id, temp_db)

        # Verify events are gone
        conn = get_connection(Path(temp_db))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM session_events WHERE session_id = ?",
            (sample_session.id,)
        )
        count = cursor.fetchone()[0]
        assert count == 0


class TestTableCreation:
    """Tests for table creation."""

    def test_ensure_session_tables(self):
        """Test ensuring session tables exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / ".vibey" / "roadmap.db"
            db_path.parent.mkdir(parents=True)

            # First create base schema (includes database_state)
            create_schema(db_path=db_path)

            # Then add session tables
            ensure_session_tables(str(db_path))

            # Verify tables exist
            conn = get_connection(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='sessions'
            """)
            assert cursor.fetchone() is not None

    def test_ensure_tables_idempotent(self, temp_db):
        """Test ensuring tables is idempotent."""
        # Call multiple times
        ensure_session_tables(temp_db)
        ensure_session_tables(temp_db)
        ensure_session_tables(temp_db)

        # Should still work
        conn = get_connection(Path(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions")
        # No error means success


class TestRoundtrip:
    """Tests for full save/load roundtrips."""

    def test_full_session_roundtrip(self, temp_db):
        """Test full session data survives roundtrip."""
        now = datetime.now(timezone.utc)

        # Create session with all fields
        session = Session(
            id="01KCROUNDTRIP12345678901",
            name="Full Session",
            status=SessionStatus.COMPLETED,
            created=now,
            started=now,
            ended=now,
            roadmap_id="test-roadmap",
            track_id="test-track",
            sprint_id="test-sprint",
            task_ids=["task-1", "task-2", "task-3"],
            branch="feature-branch",
            start_commit="start123",
            end_commit="end456",
            goals=["Goal A", "Goal B"],
            summary="Session completed successfully",
            events=[
                SessionEvent(
                    id="01KCEVENT1000000000000000",
                    session_id="01KCROUNDTRIP12345678901",
                    timestamp=now,
                    event_type=SessionEventType.SESSION_START,
                    data={"name": "Full Session"},
                ),
                SessionEvent(
                    id="01KCEVENT2000000000000000",
                    session_id="01KCROUNDTRIP12345678901",
                    timestamp=now,
                    event_type=SessionEventType.NOTE,
                    data={"message": "Test note"},
                ),
            ],
            commits=[
                SessionCommit(
                    session_id="01KCROUNDTRIP12345678901",
                    commit_sha="abc123def456789",
                    short_sha="abc123d",
                    timestamp=now,
                    message="First commit",
                    author="Test Author",
                    files_changed=5,
                    insertions=100,
                    deletions=50,
                ),
            ],
            metadata={"custom_key": "custom_value"},
        )

        # Save and load
        save_session(session, temp_db)
        loaded = load_session(session.id, temp_db)

        # Verify all fields
        assert loaded.id == session.id
        assert loaded.name == session.name
        assert loaded.status == session.status
        assert loaded.roadmap_id == session.roadmap_id
        assert loaded.track_id == session.track_id
        assert loaded.sprint_id == session.sprint_id
        assert loaded.branch == session.branch
        assert loaded.start_commit == session.start_commit
        assert loaded.end_commit == session.end_commit
        assert loaded.goals == session.goals
        assert loaded.summary == session.summary

        # Verify task IDs
        assert set(loaded.task_ids) == set(session.task_ids)

        # Verify events
        assert len(loaded.events) == 2

        # Verify commits
        assert len(loaded.commits) == 1
        assert loaded.commits[0].files_changed == 5
        assert loaded.commits[0].insertions == 100
        assert loaded.commits[0].deletions == 50
