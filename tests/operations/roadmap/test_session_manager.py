"""
Tests for SessionManager.

Sprint 3.2 Task 8: Integration Testing
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from vibey.operations.roadmap.session_manager import SessionManager
from vibey.roadmap.models.session import (
    Session,
    SessionStatus,
    SessionEvent,
    SessionEventType,
    Decision,
    DecisionCategory,
    DecisionConfidence,
)


@pytest.fixture
def temp_roadmap():
    """Create a temporary roadmap directory."""
    temp_dir = Path(tempfile.mkdtemp())
    roadmap_path = temp_dir / ".vibey" / "roadmap"
    roadmap_path.mkdir(parents=True)

    yield roadmap_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def session_manager(temp_roadmap):
    """Create a SessionManager with temporary storage."""
    return SessionManager(temp_roadmap)


class TestSessionLifecycle:
    """Tests for session lifecycle operations."""

    def test_start_session(self, session_manager):
        """Test starting a new session."""
        session = session_manager.start_session(
            name="Test Session",
            goals=["Goal 1", "Goal 2"],
        )

        assert session is not None
        assert session.name == "Test Session"
        assert session.status == SessionStatus.ACTIVE
        assert session.goals == ["Goal 1", "Goal 2"]
        assert session.id is not None
        assert len(session.id) == 26  # ULID length

    def test_start_session_auto_name(self, session_manager):
        """Test starting session with auto-generated name."""
        session = session_manager.start_session()

        assert session is not None
        assert "Session" in session.name
        assert session.status == SessionStatus.ACTIVE

    def test_start_session_with_associations(self, session_manager):
        """Test starting session with track/sprint/task associations."""
        session = session_manager.start_session(
            name="Associated Session",
            track_id="test-track",
            sprint_id="test-sprint",
            task_ids=["task-1", "task-2"],
        )

        assert session.track_id == "test-track"
        assert session.sprint_id == "test-sprint"
        assert session.task_ids == ["task-1", "task-2"]

    def test_start_session_with_existing_active(self, session_manager):
        """Test error when starting session with active session."""
        # Start first session
        session_manager.start_session(name="First Session")

        # Try to start second session
        with pytest.raises(ValueError) as exc:
            session_manager.start_session(name="Second Session")

        assert "already active" in str(exc.value).lower()

    def test_end_session(self, session_manager):
        """Test ending a session."""
        session = session_manager.start_session(name="Test Session")
        session_id = session.id

        ended = session_manager.end_session(
            summary="Completed successfully",
            status=SessionStatus.COMPLETED,
        )

        assert ended.id == session_id
        assert ended.status == SessionStatus.COMPLETED
        assert ended.summary == "Completed successfully"
        assert ended.ended is not None

    def test_end_session_abandoned(self, session_manager):
        """Test ending session as abandoned."""
        session_manager.start_session(name="Test Session")

        ended = session_manager.end_session(status=SessionStatus.ABANDONED)

        assert ended.status == SessionStatus.ABANDONED

    def test_end_session_no_active(self, session_manager):
        """Test error when ending with no active session."""
        with pytest.raises(ValueError) as exc:
            session_manager.end_session()

        assert "no session" in str(exc.value).lower()

    def test_pause_resume_session(self, session_manager):
        """Test pause and resume flow."""
        session = session_manager.start_session(name="Test Session")
        session_id = session.id

        # Pause
        paused = session_manager.pause_session()
        assert paused.status == SessionStatus.PAUSED
        assert paused.paused is not None

        # Resume
        resumed = session_manager.resume_session(session_id)
        assert resumed.status == SessionStatus.ACTIVE
        assert resumed.paused is None

    def test_get_active_session(self, session_manager):
        """Test getting active session."""
        # No active session initially
        assert session_manager.get_active_session() is None

        # Start session
        session = session_manager.start_session(name="Test Session")

        # Get active session
        active = session_manager.get_active_session()
        assert active is not None
        assert active.id == session.id

        # End session
        session_manager.end_session()

        # No active session after ending
        assert session_manager.get_active_session() is None


class TestEventLogging:
    """Tests for event logging."""

    def test_log_event(self, session_manager):
        """Test logging events to session."""
        session = session_manager.start_session(name="Test Session")

        event = session_manager.log_event(
            event_type=SessionEventType.NOTE,
            data={"message": "Test note"},
        )

        assert event is not None
        assert event.event_type == SessionEventType.NOTE
        assert event.data == {"message": "Test note"}
        assert event.session_id == session.id

    def test_log_event_with_associations(self, session_manager):
        """Test logging event with task/commit/file associations."""
        session_manager.start_session(name="Test Session")

        event = session_manager.log_event(
            event_type=SessionEventType.FILE_MODIFIED,
            data={"action": "modified"},
            task_id="test-task",
            commit_sha="abc123",
            file_path="test.py",
        )

        assert event.task_id == "test-task"
        assert event.commit_sha == "abc123"
        assert event.file_path == "test.py"

    def test_log_event_no_active_session(self, session_manager):
        """Test error when logging without active session."""
        with pytest.raises(ValueError) as exc:
            session_manager.log_event(
                event_type=SessionEventType.NOTE,
                data={"message": "Test"},
            )

        assert "no active session" in str(exc.value).lower()

    def test_log_decision(self, session_manager):
        """Test logging decisions."""
        session_manager.start_session(name="Test Session")

        decision = session_manager.log_decision(
            description="Use SQLite for storage",
            rationale="Better query performance",
            alternatives=[{"name": "YAML only", "reason": "Simpler but slower"}],
            category=DecisionCategory.ARCHITECTURE,
            confidence=DecisionConfidence.HIGH,
        )

        assert decision is not None
        assert decision.description == "Use SQLite for storage"
        assert decision.rationale == "Better query performance"
        assert decision.category == DecisionCategory.ARCHITECTURE
        assert decision.confidence == DecisionConfidence.HIGH


class TestAssociations:
    """Tests for task and commit associations."""

    def test_associate_task(self, session_manager):
        """Test associating task with session."""
        session = session_manager.start_session(name="Test Session")

        session_manager.associate_task("task-001")

        # Verify task is associated
        updated = session_manager.get_session(session.id)
        assert "task-001" in updated.task_ids

    def test_associate_commit(self, session_manager):
        """Test associating commit with session."""
        session = session_manager.start_session(name="Test Session")

        session_manager.associate_commit(
            commit_sha="abc123def456",
            message="Test commit",
        )

        # Verify commit is associated
        updated = session_manager.get_session(session.id)
        assert len(updated.commits) == 1
        assert updated.commits[0].commit_sha == "abc123def456"


class TestQueries:
    """Tests for session queries."""

    def test_list_sessions(self, session_manager):
        """Test listing sessions."""
        # Create and end multiple sessions
        s1 = session_manager.start_session(name="Session 1")
        session_manager.end_session()

        s2 = session_manager.start_session(name="Session 2")
        session_manager.end_session()

        s3 = session_manager.start_session(name="Session 3")
        session_manager.end_session()

        # List all sessions
        sessions = session_manager.list_sessions()
        assert len(sessions) == 3

    def test_list_sessions_with_status_filter(self, session_manager):
        """Test listing sessions with status filter."""
        # Create sessions with different statuses
        session_manager.start_session(name="Completed")
        session_manager.end_session(status=SessionStatus.COMPLETED)

        session_manager.start_session(name="Abandoned")
        session_manager.end_session(status=SessionStatus.ABANDONED)

        session_manager.start_session(name="Active")
        # Leave active

        # Filter by status
        completed = session_manager.list_sessions(status=SessionStatus.COMPLETED)
        assert len(completed) == 1
        assert completed[0].name == "Completed"

        active = session_manager.list_sessions(status=SessionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "Active"

    def test_get_session(self, session_manager):
        """Test getting session by ID."""
        session = session_manager.start_session(name="Test Session")

        retrieved = session_manager.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.name == "Test Session"

    def test_get_session_not_found(self, session_manager):
        """Test getting non-existent session."""
        result = session_manager.get_session("nonexistent-id")
        assert result is None


class TestSessionPersistence:
    """Tests for session persistence across manager instances."""

    def test_session_persists_to_yaml(self, temp_roadmap):
        """Test session data persists to YAML file."""
        manager1 = SessionManager(temp_roadmap)
        session = manager1.start_session(name="Persistent Session")
        session_id = session.id
        manager1.end_session()

        # Create new manager instance
        manager2 = SessionManager(temp_roadmap)

        # Should find the session
        retrieved = manager2.get_session(session_id)
        assert retrieved is not None
        assert retrieved.name == "Persistent Session"

    def test_session_file_created(self, temp_roadmap):
        """Test session YAML file is created."""
        manager = SessionManager(temp_roadmap)
        session = manager.start_session(name="Test Session")

        # Check file exists
        sessions_dir = temp_roadmap / "sessions"
        session_file = sessions_dir / f"{session.id}.yaml"

        assert sessions_dir.exists()
        assert session_file.exists()
