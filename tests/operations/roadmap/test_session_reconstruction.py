"""
Tests for session reconstruction module.

Tests SessionReconstructor capabilities for audit, reporting, and continuation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.operations.roadmap.session_reconstruction import (
    SessionTimeline,
    SessionReconstructor,
    get_reconstructor,
)
from vibey.roadmap.models.session import (
    Session,
    SessionEvent,
    SessionEventType,
    SessionStatus,
    Decision,
    SessionCommit,
    ContextSnapshot,
)


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    now = datetime.now(timezone.utc)
    started = now - timedelta(hours=2)
    ended = now - timedelta(hours=1)
    session_id = "01ABCDEF123456789012345678"

    return Session(
        id=session_id,
        name="Test Session",
        status=SessionStatus.COMPLETED,
        started=started,
        ended=ended,
        branch="feature/test",
        goals=["Complete task 1", "Complete task 2"],
        task_ids=["task-001", "task-002"],
        events=[
            SessionEvent(
                id="01EVENT001",
                session_id=session_id,
                event_type=SessionEventType.SESSION_START,
                timestamp=started,
                data={"message": "Session started"},
            ),
            SessionEvent(
                id="01EVENT002",
                session_id=session_id,
                event_type=SessionEventType.TASK_START,
                timestamp=started + timedelta(minutes=10),
                task_id="task-001",
                data={},
            ),
            SessionEvent(
                id="01EVENT003",
                session_id=session_id,
                event_type=SessionEventType.TASK_COMPLETE,
                timestamp=started + timedelta(minutes=30),
                task_id="task-001",
                data={},
            ),
            SessionEvent(
                id="01EVENT004",
                session_id=session_id,
                event_type=SessionEventType.SESSION_END,
                timestamp=ended,
                data={"message": "Session ended"},
            ),
        ],
        commits=[
            SessionCommit(
                session_id=session_id,
                commit_sha="abc123def456789012345678901234567890abcd",
                short_sha="abc123d",
                message="feat: Add test feature",
                timestamp=started + timedelta(minutes=25),
            ),
        ],
        decisions=[
            Decision(
                id="01DECISION001",
                session_id=session_id,
                description="Use approach A over B",
                rationale="Better performance",
                timestamp=started + timedelta(minutes=15),
                alternatives=[{"name": "Approach B"}],
            ),
        ],
        context_snapshot=ContextSnapshot(
            id="01SNAPSHOT001",
            session_id=session_id,
            timestamp=started,
            snapshot_type="session_start",
            git_branch="feature/test",
            git_commit="initial123",
            active_track_id="track-1",
            active_sprint_id="sprint-1",
            active_task_ids=["task-001"],
            context_files={"README.md": "read"},
        ),
    )


@pytest.fixture
def reconstructor(tmp_path):
    """Create a SessionReconstructor with temp path."""
    roadmap_path = tmp_path / ".vibey" / "roadmap"
    roadmap_path.mkdir(parents=True)
    return SessionReconstructor(roadmap_path)


class TestSessionTimeline:
    """Test SessionTimeline dataclass."""

    def test_duration_seconds_with_ended_session(self):
        """Test duration calculation for completed session."""
        now = datetime.now(timezone.utc)
        session = Session(
            id="test-id",
            name="Test",
            status=SessionStatus.COMPLETED,
            started=now - timedelta(hours=1),
            ended=now,
        )
        timeline = SessionTimeline(session=session)

        # Should be approximately 3600 seconds (1 hour)
        assert 3590 <= timeline.duration_seconds <= 3610

    def test_duration_seconds_with_ongoing_session(self):
        """Test duration calculation for ongoing session."""
        now = datetime.now(timezone.utc)
        session = Session(
            id="test-id",
            name="Test",
            status=SessionStatus.ACTIVE,
            started=now - timedelta(minutes=30),
            ended=None,  # Still ongoing
        )
        timeline = SessionTimeline(session=session)

        # Should be approximately 1800 seconds (30 minutes)
        assert 1790 <= timeline.duration_seconds <= 1810

    def test_duration_seconds_with_no_start(self):
        """Test duration when session has no start time."""
        session = Session(
            id="test-id",
            name="Test",
            status=SessionStatus.COMPLETED,
            started=None,
            ended=None,
        )
        timeline = SessionTimeline(session=session)

        assert timeline.duration_seconds == 0

    def test_duration_formatted_hours(self):
        """Test formatted duration with hours."""
        now = datetime.now(timezone.utc)
        session = Session(
            id="test-id",
            name="Test",
            status=SessionStatus.COMPLETED,
            started=now - timedelta(hours=2, minutes=30),
            ended=now,
        )
        timeline = SessionTimeline(session=session)

        assert "2h" in timeline.duration_formatted
        assert "30m" in timeline.duration_formatted

    def test_duration_formatted_minutes_only(self):
        """Test formatted duration with minutes only."""
        now = datetime.now(timezone.utc)
        session = Session(
            id="test-id",
            name="Test",
            status=SessionStatus.COMPLETED,
            started=now - timedelta(minutes=45),
            ended=now,
        )
        timeline = SessionTimeline(session=session)

        assert "45m" in timeline.duration_formatted
        assert "h" not in timeline.duration_formatted


class TestSessionReconstructor:
    """Test SessionReconstructor class."""

    def test_init(self, tmp_path):
        """Test constructor."""
        reconstructor = SessionReconstructor(tmp_path)
        assert reconstructor.roadmap_path == tmp_path

    def test_get_session_not_found(self, reconstructor):
        """Test get_session returns None for missing session."""
        with patch.object(reconstructor, '_get_session_manager') as mock_mgr:
            mock_mgr.return_value.get_session.return_value = None
            result = reconstructor.get_session("nonexistent")
            assert result is None

    def test_get_session_found(self, reconstructor, sample_session):
        """Test get_session returns session when found."""
        with patch.object(reconstructor, '_get_session_manager') as mock_mgr:
            mock_mgr.return_value.get_session.return_value = sample_session
            result = reconstructor.get_session(sample_session.id)
            assert result == sample_session

    def test_get_session_timeline(self, reconstructor, sample_session):
        """Test get_session_timeline returns timeline."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = sample_session
            timeline = reconstructor.get_session_timeline(sample_session.id)

            assert isinstance(timeline, SessionTimeline)
            assert timeline.session == sample_session
            # Events should be sorted by timestamp
            assert len(timeline.events) == len(sample_session.events)

    def test_get_session_timeline_not_found(self, reconstructor):
        """Test get_session_timeline returns None for missing session."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = None
            result = reconstructor.get_session_timeline("nonexistent")
            assert result is None

    def test_get_decisions_made(self, reconstructor, sample_session):
        """Test get_decisions_made returns sorted decisions."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = sample_session
            decisions = reconstructor.get_decisions_made(sample_session.id)

            assert len(decisions) == 1
            assert decisions[0].description == "Use approach A over B"

    def test_get_decisions_made_not_found(self, reconstructor):
        """Test get_decisions_made returns empty for missing session."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = None
            result = reconstructor.get_decisions_made("nonexistent")
            assert result == []


class TestSessionContextReconstruction:
    """Test context reconstruction at a point in time."""

    def test_get_session_context_at_not_found(self, reconstructor):
        """Test returns empty dict for missing session."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = None
            result = reconstructor.get_session_context_at(
                "nonexistent",
                datetime.now(timezone.utc)
            )
            assert result == {}

    def test_get_session_context_at_initial(self, reconstructor, sample_session):
        """Test context at session start includes initial snapshot."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = sample_session
            result = reconstructor.get_session_context_at(
                sample_session.id,
                sample_session.started
            )

            assert result.get("git_branch") == "feature/test"
            assert result.get("git_commit") == "initial123"
            assert result.get("active_track_id") == "track-1"


class TestReportGeneration:
    """Test session report generation."""

    def test_generate_session_report_not_found(self, reconstructor):
        """Test report for missing session."""
        with patch.object(reconstructor, 'get_session_timeline') as mock_get:
            mock_get.return_value = None
            result = reconstructor.generate_session_report("nonexistent")
            assert "not found" in result.lower()

    def test_generate_markdown_report(self, reconstructor, sample_session):
        """Test markdown report generation."""
        timeline = SessionTimeline(
            session=sample_session,
            events=sample_session.events,
            commits=sample_session.commits,
            decisions=sample_session.decisions,
        )
        with patch.object(reconstructor, 'get_session_timeline') as mock_get:
            mock_get.return_value = timeline
            result = reconstructor.generate_session_report(sample_session.id, format="markdown")

            assert "# Session Report" in result
            assert "## Summary" in result
            assert sample_session.name in result
            assert "## Goals" in result
            assert "## Commits Made" in result
            assert "## Key Decisions" in result

    def test_generate_text_report(self, reconstructor, sample_session):
        """Test text report generation."""
        timeline = SessionTimeline(
            session=sample_session,
            events=sample_session.events,
            commits=sample_session.commits,
            decisions=sample_session.decisions,
        )
        with patch.object(reconstructor, 'get_session_timeline') as mock_get:
            mock_get.return_value = timeline
            result = reconstructor.generate_session_report(sample_session.id, format="text")

            assert "Session Report" in result
            assert sample_session.name in result
            assert "Goals:" in result


class TestExportForContinuation:
    """Test session export for continuation."""

    def test_export_not_found(self, reconstructor):
        """Test export returns empty dict for missing session."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = None
            result = reconstructor.export_for_continuation("nonexistent")
            assert result == {}

    def test_export_includes_incomplete_tasks(self, reconstructor, sample_session):
        """Test export identifies incomplete tasks."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = sample_session

            result = reconstructor.export_for_continuation(sample_session.id)

            # task-001 was completed, task-002 was not
            assert "task-002" in result.get("incomplete_tasks", [])
            assert "task-001" not in result.get("incomplete_tasks", [])

    def test_export_includes_session_info(self, reconstructor, sample_session):
        """Test export includes basic session info."""
        with patch.object(reconstructor, 'get_session') as mock_get:
            mock_get.return_value = sample_session

            result = reconstructor.export_for_continuation(sample_session.id)

            assert result.get("original_session_id") == sample_session.id
            assert result.get("original_session_name") == sample_session.name
            assert result.get("branch") == sample_session.branch
            assert result.get("continuation_suggested") is True


class TestFactoryFunction:
    """Test get_reconstructor factory function."""

    def test_get_reconstructor(self, tmp_path):
        """Test factory function creates reconstructor."""
        result = get_reconstructor(tmp_path)

        assert isinstance(result, SessionReconstructor)
        assert result.roadmap_path == tmp_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
