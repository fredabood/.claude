"""
Tests for session YAML serialization.

Sprint 3.2 Task 8: Integration Testing
"""

import pytest
import tempfile
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
    SessionStats,
)
from vibey.roadmap.serialization.session_yaml import (
    load_session,
    dump_session,
    load_session_from_file,
    save_session_to_file,
)


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
        decisions=[
            Decision(
                id="01KCDECISION123456789012",
                session_id="01KCTEST12345678901234567",
                timestamp=now,
                description="Test decision",
                category=DecisionCategory.ARCHITECTURE,
                confidence=DecisionConfidence.HIGH,
                rationale="Good reason",
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


class TestSessionDumping:
    """Tests for dumping sessions to dictionaries."""

    def test_dump_basic_session(self, sample_session):
        """Test dumping a basic session."""
        data = dump_session(sample_session)

        assert "session" in data
        session_data = data["session"]

        assert session_data["id"] == "01KCTEST12345678901234567"
        assert session_data["name"] == "Test Session"
        assert session_data["status"] == "active"
        assert session_data["roadmap_id"] == "test-roadmap"

    def test_dump_session_events(self, sample_session):
        """Test dumping session with events."""
        data = dump_session(sample_session)
        events = data["session"]["events"]

        assert len(events) == 1
        assert events[0]["event_type"] == "session_start"

    def test_dump_session_decisions(self, sample_session):
        """Test dumping session with decisions."""
        data = dump_session(sample_session)
        decisions = data["session"]["decisions"]

        assert len(decisions) == 1
        assert decisions[0]["description"] == "Test decision"
        assert decisions[0]["category"] == "architecture"

    def test_dump_session_commits(self, sample_session):
        """Test dumping session with commits."""
        data = dump_session(sample_session)
        commits = data["session"]["commits"]

        assert len(commits) == 1
        assert commits[0]["commit_sha"] == "abc123def456"


class TestSessionLoading:
    """Tests for loading sessions from dictionaries."""

    def test_load_basic_session(self, sample_session):
        """Test roundtrip: dump and load session."""
        data = dump_session(sample_session)
        loaded = load_session(data)

        assert loaded.id == sample_session.id
        assert loaded.name == sample_session.name
        assert loaded.status == sample_session.status

    def test_load_session_events(self, sample_session):
        """Test loading session with events."""
        data = dump_session(sample_session)
        loaded = load_session(data)

        assert len(loaded.events) == 1
        assert loaded.events[0].event_type == SessionEventType.SESSION_START

    def test_load_session_decisions(self, sample_session):
        """Test loading session with decisions."""
        data = dump_session(sample_session)
        loaded = load_session(data)

        assert len(loaded.decisions) == 1
        assert loaded.decisions[0].category == DecisionCategory.ARCHITECTURE

    def test_load_session_flat_format(self):
        """Test loading session from flat format (no wrapper)."""
        data = {
            "id": "01KCFLAT12345678901234567",
            "name": "Flat Session",
            "status": "active",
            "roadmap_id": "test-roadmap",
            "created": "2025-01-01T00:00:00+00:00",
        }

        loaded = load_session(data)
        assert loaded.id == "01KCFLAT12345678901234567"
        assert loaded.name == "Flat Session"


class TestFileOperations:
    """Tests for file I/O operations."""

    def test_save_and_load_file(self, sample_session):
        """Test saving and loading session from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "session.yaml"

            # Save
            save_session_to_file(sample_session, file_path)
            assert file_path.exists()

            # Load
            loaded = load_session_from_file(file_path)
            assert loaded.id == sample_session.id
            assert loaded.name == sample_session.name

    def test_save_creates_parent_dirs(self, sample_session):
        """Test save creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "subdir" / "deep" / "session.yaml"

            save_session_to_file(sample_session, file_path)
            assert file_path.exists()

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_session_from_file(Path("/nonexistent/path/session.yaml"))

    def test_roundtrip_preserves_data(self, sample_session):
        """Test full roundtrip preserves all data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "session.yaml"

            save_session_to_file(sample_session, file_path)
            loaded = load_session_from_file(file_path)

            # Basic fields
            assert loaded.id == sample_session.id
            assert loaded.name == sample_session.name
            assert loaded.status == sample_session.status
            assert loaded.roadmap_id == sample_session.roadmap_id
            assert loaded.track_id == sample_session.track_id
            assert loaded.sprint_id == sample_session.sprint_id
            assert loaded.branch == sample_session.branch
            assert loaded.goals == sample_session.goals
            assert loaded.task_ids == sample_session.task_ids

            # Events
            assert len(loaded.events) == len(sample_session.events)

            # Decisions
            assert len(loaded.decisions) == len(sample_session.decisions)

            # Commits
            assert len(loaded.commits) == len(sample_session.commits)


class TestDatetimeParsing:
    """Tests for datetime parsing and formatting."""

    def test_parse_iso_datetime(self):
        """Test parsing ISO format datetime."""
        data = {
            "id": "01KCTEST12345678901234567",
            "name": "Test",
            "status": "active",
            "roadmap_id": "test",
            "created": "2025-01-15T10:30:00+00:00",
        }

        loaded = load_session(data)
        assert loaded.created.year == 2025
        assert loaded.created.month == 1
        assert loaded.created.day == 15
        assert loaded.created.hour == 10
        assert loaded.created.minute == 30

    def test_parse_datetime_with_z(self):
        """Test parsing datetime with Z suffix."""
        data = {
            "id": "01KCTEST12345678901234567",
            "name": "Test",
            "status": "active",
            "roadmap_id": "test",
            "created": "2025-01-15T10:30:00Z",
        }

        loaded = load_session(data)
        assert loaded.created is not None
        assert loaded.created.tzinfo is not None
