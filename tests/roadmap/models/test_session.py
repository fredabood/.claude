"""
Tests for session models.

Tests the session dataclasses, enums, and model methods.
"""

import pytest
from datetime import datetime, timezone, timedelta

from vibey.roadmap.models.session import (
    SessionStatus,
    SessionEventType,
    DecisionCategory,
    DecisionConfidence,
    SessionEvent,
    Decision,
    ContextSnapshot,
    SessionCommit,
    SessionStats,
    Session,
)


class TestSessionStatusEnum:
    """Test SessionStatus enum."""

    def test_active_value(self):
        """Test ACTIVE value."""
        assert SessionStatus.ACTIVE.value == "active"

    def test_paused_value(self):
        """Test PAUSED value."""
        assert SessionStatus.PAUSED.value == "paused"

    def test_completed_value(self):
        """Test COMPLETED value."""
        assert SessionStatus.COMPLETED.value == "completed"

    def test_abandoned_value(self):
        """Test ABANDONED value."""
        assert SessionStatus.ABANDONED.value == "abandoned"

    def test_string_type(self):
        """Test enum is string-based."""
        assert isinstance(SessionStatus.ACTIVE, str)


class TestSessionEventTypeEnum:
    """Test SessionEventType enum."""

    def test_lifecycle_events(self):
        """Test lifecycle event types."""
        assert SessionEventType.SESSION_START.value == "session_start"
        assert SessionEventType.SESSION_END.value == "session_end"
        assert SessionEventType.SESSION_PAUSE.value == "session_pause"
        assert SessionEventType.SESSION_RESUME.value == "session_resume"

    def test_task_events(self):
        """Test task event types."""
        assert SessionEventType.TASK_START.value == "task_start"
        assert SessionEventType.TASK_COMPLETE.value == "task_complete"
        assert SessionEventType.TASK_PAUSED.value == "task_paused"

    def test_decision_events(self):
        """Test decision event types."""
        assert SessionEventType.DECISION_MADE.value == "decision_made"
        assert SessionEventType.QUESTION_ASKED.value == "question_asked"

    def test_file_events(self):
        """Test file event types."""
        assert SessionEventType.FILE_READ.value == "file_read"
        assert SessionEventType.FILE_MODIFIED.value == "file_modified"
        assert SessionEventType.FILE_CREATED.value == "file_created"
        assert SessionEventType.FILE_DELETED.value == "file_deleted"

    def test_git_events(self):
        """Test git event types."""
        assert SessionEventType.COMMIT_MADE.value == "commit_made"
        assert SessionEventType.BRANCH_CHANGED.value == "branch_changed"


class TestDecisionCategoryEnum:
    """Test DecisionCategory enum."""

    def test_architecture_value(self):
        """Test ARCHITECTURE value."""
        assert DecisionCategory.ARCHITECTURE.value == "architecture"

    def test_implementation_value(self):
        """Test IMPLEMENTATION value."""
        assert DecisionCategory.IMPLEMENTATION.value == "implementation"

    def test_other_value(self):
        """Test OTHER value."""
        assert DecisionCategory.OTHER.value == "other"


class TestDecisionConfidenceEnum:
    """Test DecisionConfidence enum."""

    def test_low_value(self):
        """Test LOW value."""
        assert DecisionConfidence.LOW.value == "low"

    def test_medium_value(self):
        """Test MEDIUM value."""
        assert DecisionConfidence.MEDIUM.value == "medium"

    def test_high_value(self):
        """Test HIGH value."""
        assert DecisionConfidence.HIGH.value == "high"


class TestSessionEvent:
    """Test SessionEvent dataclass."""

    def test_basic_construction(self):
        """Test basic SessionEvent construction."""
        now = datetime.now(timezone.utc)
        event = SessionEvent(
            id="01EVENT001",
            session_id="01SESSION01",
            timestamp=now,
            event_type=SessionEventType.SESSION_START,
        )
        assert event.id == "01EVENT001"
        assert event.session_id == "01SESSION01"
        assert event.event_type == SessionEventType.SESSION_START

    def test_default_values(self):
        """Test default values."""
        now = datetime.now(timezone.utc)
        event = SessionEvent(
            id="01EVENT001",
            session_id="01SESSION01",
            timestamp=now,
            event_type=SessionEventType.CUSTOM,
        )
        assert event.data == {}
        assert event.task_id is None
        assert event.commit_sha is None
        assert event.file_path is None

    def test_with_optional_fields(self):
        """Test with optional fields."""
        now = datetime.now(timezone.utc)
        event = SessionEvent(
            id="01EVENT001",
            session_id="01SESSION01",
            timestamp=now,
            event_type=SessionEventType.TASK_START,
            task_id="task-001",
            data={"message": "Started task"},
        )
        assert event.task_id == "task-001"
        assert event.data["message"] == "Started task"

    def test_validation_missing_id(self):
        """Test validation fails without id."""
        with pytest.raises(ValueError, match="id is required"):
            SessionEvent(
                id="",
                session_id="01SESSION01",
                timestamp=datetime.now(timezone.utc),
                event_type=SessionEventType.CUSTOM,
            )

    def test_validation_missing_session_id(self):
        """Test validation fails without session_id."""
        with pytest.raises(ValueError, match="session_id is required"):
            SessionEvent(
                id="01EVENT001",
                session_id="",
                timestamp=datetime.now(timezone.utc),
                event_type=SessionEventType.CUSTOM,
            )

    def test_timezone_naive_conversion(self):
        """Test naive datetime is converted to UTC."""
        naive_dt = datetime(2025, 12, 15, 10, 0, 0)
        event = SessionEvent(
            id="01EVENT001",
            session_id="01SESSION01",
            timestamp=naive_dt,
            event_type=SessionEventType.CUSTOM,
        )
        assert event.timestamp.tzinfo == timezone.utc


class TestDecision:
    """Test Decision dataclass."""

    @pytest.fixture
    def basic_decision(self):
        """Create basic decision."""
        return Decision(
            id="01DECISION01",
            session_id="01SESSION01",
            timestamp=datetime.now(timezone.utc),
            description="Use approach A over B",
        )

    def test_basic_construction(self, basic_decision):
        """Test basic Decision construction."""
        assert basic_decision.id == "01DECISION01"
        assert basic_decision.description == "Use approach A over B"

    def test_default_values(self, basic_decision):
        """Test default values."""
        assert basic_decision.category == DecisionCategory.OTHER
        assert basic_decision.confidence == DecisionConfidence.MEDIUM
        assert basic_decision.revisit is False
        assert basic_decision.rationale is None
        assert basic_decision.alternatives == []
        assert basic_decision.related_files == []

    def test_full_construction(self):
        """Test Decision with all fields."""
        decision = Decision(
            id="01DECISION01",
            session_id="01SESSION01",
            timestamp=datetime.now(timezone.utc),
            description="Use FastAPI over Flask",
            category=DecisionCategory.ARCHITECTURE,
            confidence=DecisionConfidence.HIGH,
            revisit=False,
            rationale="Better async support",
            alternatives=[{"name": "Flask", "reason_rejected": "Less async support"}],
            related_files=["app/main.py"],
            related_commits=["abc123"],
            related_tasks=["task-001"],
        )
        assert decision.category == DecisionCategory.ARCHITECTURE
        assert decision.confidence == DecisionConfidence.HIGH
        assert len(decision.alternatives) == 1
        assert len(decision.related_files) == 1

    def test_validation_missing_id(self):
        """Test validation fails without id."""
        with pytest.raises(ValueError, match="id is required"):
            Decision(
                id="",
                session_id="01SESSION01",
                timestamp=datetime.now(timezone.utc),
                description="Test",
            )

    def test_validation_missing_description(self):
        """Test validation fails without description."""
        with pytest.raises(ValueError, match="description is required"):
            Decision(
                id="01DECISION01",
                session_id="01SESSION01",
                timestamp=datetime.now(timezone.utc),
                description="",
            )

    def test_to_event(self, basic_decision):
        """Test converting decision to event."""
        event = basic_decision.to_event()
        assert event.id == basic_decision.id
        assert event.session_id == basic_decision.session_id
        assert event.event_type == SessionEventType.DECISION_MADE
        assert event.data["description"] == basic_decision.description

    def test_from_event(self, basic_decision):
        """Test creating decision from event."""
        event = basic_decision.to_event()
        reconstructed = Decision.from_event(event)
        assert reconstructed.id == basic_decision.id
        assert reconstructed.description == basic_decision.description
        assert reconstructed.category == basic_decision.category

    def test_from_event_wrong_type(self):
        """Test from_event raises for wrong event type."""
        event = SessionEvent(
            id="01EVENT001",
            session_id="01SESSION01",
            timestamp=datetime.now(timezone.utc),
            event_type=SessionEventType.TASK_START,
        )
        with pytest.raises(ValueError, match="Expected DECISION_MADE"):
            Decision.from_event(event)


class TestContextSnapshot:
    """Test ContextSnapshot dataclass."""

    def test_basic_construction(self):
        """Test basic ContextSnapshot construction."""
        snapshot = ContextSnapshot(
            id="01SNAP0001",
            session_id="01SESSION01",
            timestamp=datetime.now(timezone.utc),
            snapshot_type="session_start",
        )
        assert snapshot.id == "01SNAP0001"
        assert snapshot.snapshot_type == "session_start"

    def test_default_values(self):
        """Test default values."""
        snapshot = ContextSnapshot(
            id="01SNAP0001",
            session_id="01SESSION01",
            timestamp=datetime.now(timezone.utc),
            snapshot_type="checkpoint",
        )
        assert snapshot.git_branch is None
        assert snapshot.git_commit is None
        assert snapshot.git_dirty is False
        assert snapshot.git_staged_files == []
        assert snapshot.context_files == {}
        assert snapshot.active_track_id is None

    def test_full_construction(self):
        """Test with all fields."""
        snapshot = ContextSnapshot(
            id="01SNAP0001",
            session_id="01SESSION01",
            timestamp=datetime.now(timezone.utc),
            snapshot_type="session_start",
            git_branch="feature/test",
            git_commit="abc123",
            git_dirty=True,
            git_staged_files=["file1.py"],
            git_modified_files=["file2.py"],
            context_files={"README.md": "hash123"},
            active_track_id="track-1",
            active_sprint_id="sprint-1",
            active_task_ids=["task-001"],
            environment={"python_version": "3.11"},
        )
        assert snapshot.git_branch == "feature/test"
        assert snapshot.git_dirty is True
        assert len(snapshot.git_staged_files) == 1
        assert len(snapshot.context_files) == 1

    def test_validation_missing_id(self):
        """Test validation fails without id."""
        with pytest.raises(ValueError, match="id is required"):
            ContextSnapshot(
                id="",
                session_id="01SESSION01",
                timestamp=datetime.now(timezone.utc),
                snapshot_type="checkpoint",
            )


class TestSessionCommit:
    """Test SessionCommit dataclass."""

    def test_basic_construction(self):
        """Test basic construction."""
        commit = SessionCommit(
            session_id="01SESSION01",
            commit_sha="abc123def456789012345678901234567890abcd",
            short_sha="abc123d",
            timestamp=datetime.now(timezone.utc),
            message="feat: Add feature",
        )
        assert commit.session_id == "01SESSION01"
        assert commit.commit_sha.startswith("abc123")
        assert commit.short_sha == "abc123d"
        assert commit.message == "feat: Add feature"

    def test_default_values(self):
        """Test default values."""
        commit = SessionCommit(
            session_id="01SESSION01",
            commit_sha="abc123",
            short_sha="abc",
            timestamp=datetime.now(timezone.utc),
            message="Test",
        )
        assert commit.author is None
        assert commit.files_changed == 0
        assert commit.insertions == 0
        assert commit.deletions == 0

    def test_with_stats(self):
        """Test with commit stats."""
        commit = SessionCommit(
            session_id="01SESSION01",
            commit_sha="abc123",
            short_sha="abc",
            timestamp=datetime.now(timezone.utc),
            message="Test",
            author="John Doe",
            files_changed=5,
            insertions=100,
            deletions=50,
        )
        assert commit.author == "John Doe"
        assert commit.files_changed == 5
        assert commit.insertions == 100
        assert commit.deletions == 50

    def test_validation_missing_session_id(self):
        """Test validation fails without session_id."""
        with pytest.raises(ValueError, match="session_id is required"):
            SessionCommit(
                session_id="",
                commit_sha="abc123",
                short_sha="abc",
                timestamp=datetime.now(timezone.utc),
                message="Test",
            )

    def test_validation_missing_commit_sha(self):
        """Test validation fails without commit_sha."""
        with pytest.raises(ValueError, match="commit_sha is required"):
            SessionCommit(
                session_id="01SESSION01",
                commit_sha="",
                short_sha="abc",
                timestamp=datetime.now(timezone.utc),
                message="Test",
            )


class TestSessionStats:
    """Test SessionStats dataclass."""

    def test_default_values(self):
        """Test default values."""
        stats = SessionStats()
        assert stats.duration_seconds == 0
        assert stats.events_count == 0
        assert stats.decisions_count == 0
        assert stats.commits_count == 0
        assert stats.files_modified == 0
        assert stats.tasks_worked == 0
        assert stats.errors_count == 0
        assert stats.token_usage is None

    def test_with_values(self):
        """Test with values."""
        stats = SessionStats(
            duration_seconds=3600,
            events_count=50,
            decisions_count=5,
            commits_count=3,
            files_modified=10,
            tasks_worked=2,
            errors_count=1,
            token_usage=10000,
        )
        assert stats.duration_seconds == 3600
        assert stats.token_usage == 10000


class TestSession:
    """Test Session dataclass."""

    @pytest.fixture
    def basic_session(self):
        """Create basic session."""
        return Session(
            id="01SESSION01",
            name="Test Session",
        )

    def test_basic_construction(self, basic_session):
        """Test basic Session construction."""
        assert basic_session.id == "01SESSION01"
        assert basic_session.name == "Test Session"
        assert basic_session.status == SessionStatus.ACTIVE

    def test_default_values(self, basic_session):
        """Test default values."""
        assert basic_session.started is None
        assert basic_session.ended is None
        assert basic_session.task_ids == []
        assert basic_session.commits == []
        assert basic_session.events == []
        assert basic_session.decisions == []
        assert basic_session.goals == []

    def test_validation_missing_id(self):
        """Test validation fails without id."""
        with pytest.raises(ValueError, match="id is required"):
            Session(id="", name="Test")

    def test_validation_missing_name(self):
        """Test validation fails without name."""
        with pytest.raises(ValueError, match="name is required"):
            Session(id="01SESSION01", name="")

    def test_is_active_true(self, basic_session):
        """Test is_active returns True when active."""
        assert basic_session.is_active is True

    def test_is_active_false(self):
        """Test is_active returns False when not active."""
        session = Session(
            id="01SESSION01",
            name="Test",
            status=SessionStatus.COMPLETED,
        )
        assert session.is_active is False

    def test_is_ended_completed(self):
        """Test is_ended for completed session."""
        session = Session(
            id="01SESSION01",
            name="Test",
            status=SessionStatus.COMPLETED,
        )
        assert session.is_ended is True

    def test_is_ended_abandoned(self):
        """Test is_ended for abandoned session."""
        session = Session(
            id="01SESSION01",
            name="Test",
            status=SessionStatus.ABANDONED,
        )
        assert session.is_ended is True

    def test_is_ended_active(self, basic_session):
        """Test is_ended for active session."""
        assert basic_session.is_ended is False

    def test_duration_seconds_not_started(self, basic_session):
        """Test duration_seconds when not started."""
        assert basic_session.duration_seconds is None

    def test_duration_seconds_started(self):
        """Test duration_seconds when started."""
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        session = Session(
            id="01SESSION01",
            name="Test",
            started=started,
        )
        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= session.duration_seconds <= 3610

    def test_duration_seconds_ended(self):
        """Test duration_seconds when ended."""
        started = datetime.now(timezone.utc) - timedelta(hours=2)
        ended = datetime.now(timezone.utc) - timedelta(hours=1)
        session = Session(
            id="01SESSION01",
            name="Test",
            started=started,
            ended=ended,
        )
        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= session.duration_seconds <= 3610

    def test_add_event(self, basic_session):
        """Test adding event."""
        event = SessionEvent(
            id="01EVENT001",
            session_id=basic_session.id,
            timestamp=datetime.now(timezone.utc),
            event_type=SessionEventType.CUSTOM,
        )
        basic_session.add_event(event)
        assert len(basic_session.events) == 1
        assert basic_session.events[0] == event

    def test_add_decision(self, basic_session):
        """Test adding decision."""
        decision = Decision(
            id="01DECISION01",
            session_id=basic_session.id,
            timestamp=datetime.now(timezone.utc),
            description="Test decision",
        )
        basic_session.add_decision(decision)
        assert len(basic_session.decisions) == 1
        # Also adds to events
        assert len(basic_session.events) == 1

    def test_add_commit(self, basic_session):
        """Test adding commit."""
        commit = SessionCommit(
            session_id=basic_session.id,
            commit_sha="abc123",
            short_sha="abc",
            timestamp=datetime.now(timezone.utc),
            message="Test commit",
        )
        basic_session.add_commit(commit)
        assert len(basic_session.commits) == 1

    def test_add_task(self, basic_session):
        """Test adding task."""
        basic_session.add_task("task-001")
        assert "task-001" in basic_session.task_ids

    def test_add_task_no_duplicates(self, basic_session):
        """Test adding same task twice doesn't duplicate."""
        basic_session.add_task("task-001")
        basic_session.add_task("task-001")
        assert basic_session.task_ids.count("task-001") == 1

    def test_set_goal(self, basic_session):
        """Test setting goal."""
        basic_session.set_goal("Complete feature X")
        assert "Complete feature X" in basic_session.goals

    def test_set_goal_no_duplicates(self, basic_session):
        """Test setting same goal twice doesn't duplicate."""
        basic_session.set_goal("Complete feature X")
        basic_session.set_goal("Complete feature X")
        assert basic_session.goals.count("Complete feature X") == 1

    def test_full_session(self):
        """Test full session with all fields."""
        now = datetime.now(timezone.utc)
        session = Session(
            id="01SESSION01",
            name="Feature Development",
            status=SessionStatus.ACTIVE,
            started=now - timedelta(hours=1),
            roadmap_id="roadmap-1",
            track_id="track-1",
            sprint_id="sprint-1",
            task_ids=["task-001"],
            branch="feature/test",
            goals=["Complete task 1"],
        )
        assert session.roadmap_id == "roadmap-1"
        assert session.track_id == "track-1"
        assert session.branch == "feature/test"
        assert len(session.task_ids) == 1

    def test_compute_stats(self, basic_session):
        """Test computing stats."""
        # Add some events
        for i in range(5):
            event = SessionEvent(
                id=f"01EVENT00{i}",
                session_id=basic_session.id,
                timestamp=datetime.now(timezone.utc),
                event_type=SessionEventType.FILE_MODIFIED,
                file_path=f"file{i}.py",
            )
            basic_session.add_event(event)

        # Add error event
        error_event = SessionEvent(
            id="01ERROR001",
            session_id=basic_session.id,
            timestamp=datetime.now(timezone.utc),
            event_type=SessionEventType.ERROR_ENCOUNTERED,
        )
        basic_session.add_event(error_event)

        # Add commit
        commit = SessionCommit(
            session_id=basic_session.id,
            commit_sha="abc123",
            short_sha="abc",
            timestamp=datetime.now(timezone.utc),
            message="Test",
        )
        basic_session.add_commit(commit)

        # Add task
        basic_session.add_task("task-001")

        stats = basic_session.compute_stats()
        assert stats.events_count == 6
        assert stats.errors_count == 1
        assert stats.commits_count == 1
        assert stats.tasks_worked == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
