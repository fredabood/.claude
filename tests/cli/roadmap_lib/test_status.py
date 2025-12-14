"""
Tests for vibey.cli.roadmap_lib.status module.

Tests the status progression utilities for roadmap state management.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.models import Status, TaskStatus
from vibey.cli.roadmap_lib.status import (
    StatusManager,
    can_progress_status,
    progress_status_if_ready,
)


class TestStatusManagerSprintProgression:
    """Test sprint status progression logic."""

    def test_can_progress_to_completion_gate_check(self):
        """Test checking if sprint can progress to completion_gate_check."""
        manager = StatusManager()

        # Mock sprint with all dev tasks completed
        sprint = MagicMock()
        sprint.all_development_tasks_completed.return_value = True

        can_progress, reason = manager.can_progress_sprint(sprint, Status.COMPLETION_GATE_CHECK)

        assert can_progress is True
        assert "development tasks completed" in reason.lower()

    def test_cannot_progress_to_completion_gate_check_incomplete(self):
        """Test cannot progress when dev tasks incomplete."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.all_development_tasks_completed.return_value = False

        can_progress, reason = manager.can_progress_sprint(sprint, Status.COMPLETION_GATE_CHECK)

        assert can_progress is False
        assert "not all" in reason.lower()

    def test_can_progress_to_completed(self):
        """Test checking if sprint can progress to completed."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.COMPLETION_GATE_CHECK
        sprint.all_completion_gates_passed.return_value = True

        can_progress, reason = manager.can_progress_sprint(sprint, Status.COMPLETED)

        assert can_progress is True
        assert "gates passed" in reason.lower()

    def test_cannot_progress_to_completed_wrong_status(self):
        """Test cannot progress to completed from wrong status."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.IN_PROGRESS

        can_progress, reason = manager.can_progress_sprint(sprint, Status.COMPLETED)

        assert can_progress is False
        assert "completion_gate_check" in reason.lower()

    def test_cannot_progress_to_completed_gates_not_passed(self):
        """Test cannot progress when completion gates not passed."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.COMPLETION_GATE_CHECK
        sprint.all_completion_gates_passed.return_value = False

        can_progress, reason = manager.can_progress_sprint(sprint, Status.COMPLETED)

        assert can_progress is False
        assert "not all" in reason.lower()

    def test_can_progress_to_production_gate_check(self):
        """Test checking if sprint can progress to production_gate_check."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.COMPLETED

        can_progress, reason = manager.can_progress_sprint(sprint, Status.PRODUCTION_GATE_CHECK)

        assert can_progress is True
        assert "ready for production gates" in reason.lower()

    def test_cannot_progress_to_production_gate_check_not_completed(self):
        """Test cannot progress to production gate check if not completed."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.IN_PROGRESS

        can_progress, reason = manager.can_progress_sprint(sprint, Status.PRODUCTION_GATE_CHECK)

        assert can_progress is False
        assert "must be completed" in reason.lower()

    def test_can_progress_to_production_ready(self):
        """Test checking if sprint can progress to production_ready."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.PRODUCTION_GATE_CHECK
        sprint.all_production_gates_passed.return_value = True

        can_progress, reason = manager.can_progress_sprint(sprint, Status.PRODUCTION_READY)

        assert can_progress is True
        assert "gates passed" in reason.lower()

    def test_cannot_progress_to_production_ready_wrong_status(self):
        """Test cannot progress to production_ready from wrong status."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.COMPLETED

        can_progress, reason = manager.can_progress_sprint(sprint, Status.PRODUCTION_READY)

        assert can_progress is False
        assert "production_gate_check" in reason.lower()

    def test_can_progress_to_deployed(self):
        """Test checking if sprint can progress to deployed."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.PRODUCTION_READY

        can_progress, reason = manager.can_progress_sprint(sprint, Status.DEPLOYED)

        assert can_progress is True
        assert "can be deployed" in reason.lower()

    def test_cannot_progress_to_deployed_not_ready(self):
        """Test cannot progress to deployed if not production ready."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.COMPLETED

        can_progress, reason = manager.can_progress_sprint(sprint, Status.DEPLOYED)

        assert can_progress is False
        assert "production_ready" in reason.lower()

    def test_invalid_target_status(self):
        """Test invalid target status returns False."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.IN_PROGRESS

        can_progress, reason = manager.can_progress_sprint(sprint, Status.PAUSED)

        assert can_progress is False
        assert "invalid target status" in reason.lower()


class TestStatusManagerAutoProgression:
    """Test automatic status progression."""

    def test_auto_progress_from_not_started_with_tasks_completed(self):
        """Test auto-start sprint when tasks completed."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.NOT_STARTED
        sprint.progress.tasks_completed = 1

        progressed, new_status, message = manager.progress_sprint_status(sprint)

        assert progressed is True
        assert new_status == Status.IN_PROGRESS
        assert "auto-starting" in message.lower()

    def test_auto_progress_from_not_started_when_started(self):
        """Test start sprint when explicitly started."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.NOT_STARTED
        sprint.progress.tasks_completed = 0
        sprint.progress.tasks_total = 5
        sprint.started = datetime.now(timezone.utc)

        progressed, new_status, message = manager.progress_sprint_status(sprint)

        assert progressed is True
        assert new_status == Status.IN_PROGRESS

    def test_no_progress_from_not_started_no_tasks(self):
        """Test no progress when no tasks started."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.NOT_STARTED
        sprint.progress.tasks_completed = 0
        sprint.progress.tasks_total = 5
        sprint.started = None

        progressed, new_status, message = manager.progress_sprint_status(sprint)

        assert progressed is False
        assert new_status is None

    def test_auto_progress_from_in_progress(self):
        """Test auto-progress from in_progress to completion_gate_check."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.IN_PROGRESS
        sprint.all_development_tasks_completed.return_value = True

        progressed, new_status, message = manager.progress_sprint_status(sprint)

        assert progressed is True
        assert new_status == Status.COMPLETION_GATE_CHECK

    def test_no_progress_from_in_progress_incomplete(self):
        """Test no progress when dev tasks incomplete."""
        manager = StatusManager()

        sprint = MagicMock()
        sprint.status = Status.IN_PROGRESS
        sprint.all_development_tasks_completed.return_value = False

        progressed, new_status, message = manager.progress_sprint_status(sprint)

        assert progressed is False
        assert new_status is None


class TestStatusManagerTrackProgression:
    """Test track status progression logic."""

    def test_can_progress_track_to_completed(self):
        """Test track can progress to completed when all sprints done."""
        manager = StatusManager()

        sprint1 = MagicMock()
        sprint1.status = Status.COMPLETED
        sprint2 = MagicMock()
        sprint2.status = Status.PRODUCTION_READY

        track = MagicMock()
        track.sprints = [sprint1, sprint2]

        can_progress, reason = manager.can_progress_track(track, Status.COMPLETED)

        assert can_progress is True
        assert "completed" in reason.lower()

    def test_cannot_progress_track_incomplete_sprints(self):
        """Test track cannot progress with incomplete sprints."""
        manager = StatusManager()

        sprint1 = MagicMock()
        sprint1.status = Status.COMPLETED
        sprint2 = MagicMock()
        sprint2.status = Status.IN_PROGRESS

        track = MagicMock()
        track.sprints = [sprint1, sprint2]

        can_progress, reason = manager.can_progress_track(track, Status.COMPLETED)

        assert can_progress is False
        assert "1 sprints not completed" in reason

    def test_can_progress_track_to_production_ready(self):
        """Test track can progress to production_ready."""
        manager = StatusManager()

        sprint1 = MagicMock()
        sprint1.status = Status.PRODUCTION_READY
        sprint2 = MagicMock()
        sprint2.status = Status.DEPLOYED

        track = MagicMock()
        track.sprints = [sprint1, sprint2]

        can_progress, reason = manager.can_progress_track(track, Status.PRODUCTION_READY)

        assert can_progress is True
        assert "production ready" in reason.lower()

    def test_auto_progress_track_from_in_progress(self):
        """Test auto-progress track from in_progress to completed."""
        manager = StatusManager()

        sprint1 = MagicMock()
        sprint1.status = Status.COMPLETED
        sprint2 = MagicMock()
        sprint2.status = Status.PRODUCTION_READY

        track = MagicMock()
        track.status = Status.IN_PROGRESS
        track.sprints = [sprint1, sprint2]

        progressed, new_status, message = manager.progress_track_status(track)

        assert progressed is True
        assert new_status == Status.COMPLETED


class TestStatusManagerRoadmapProgression:
    """Test roadmap status progression logic."""

    def test_auto_progress_roadmap_to_completed(self):
        """Test auto-progress roadmap to completed when all tracks done."""
        manager = StatusManager()

        track1 = MagicMock()
        track1.status = Status.COMPLETED
        track2 = MagicMock()
        track2.status = Status.PRODUCTION_READY

        roadmap = MagicMock()
        roadmap.status = Status.IN_PROGRESS
        roadmap.tracks = [track1, track2]

        progressed, new_status, message = manager.progress_roadmap_status(roadmap)

        assert progressed is True
        assert new_status == Status.COMPLETED

    def test_no_progress_roadmap_incomplete_tracks(self):
        """Test no progress with incomplete tracks."""
        manager = StatusManager()

        track1 = MagicMock()
        track1.status = Status.COMPLETED
        track2 = MagicMock()
        track2.status = Status.IN_PROGRESS

        roadmap = MagicMock()
        roadmap.status = Status.IN_PROGRESS
        roadmap.tracks = [track1, track2]

        progressed, new_status, message = manager.progress_roadmap_status(roadmap)

        assert progressed is False
        assert new_status is None
        assert "1 tracks not completed" in message


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_can_progress_status_sprint(self):
        """Test can_progress_status with sprint (uses isinstance check)."""
        from vibey.roadmap.models import Sprint

        # Use spec to make isinstance work
        sprint = MagicMock(spec=Sprint)
        sprint.all_development_tasks_completed.return_value = True

        with patch('vibey.cli.roadmap_lib.status.FileSystemManager'):
            can_progress, reason = can_progress_status(sprint, Status.COMPLETION_GATE_CHECK)

        assert can_progress is True

    def test_can_progress_status_unknown_type(self):
        """Test can_progress_status with unknown type."""
        obj = "not a valid object"

        with patch('vibey.cli.roadmap_lib.status.FileSystemManager'):
            can_progress, reason = can_progress_status(obj, Status.COMPLETED)

        assert can_progress is False
        assert "unknown" in reason.lower()

    def test_progress_status_if_ready_sprint(self):
        """Test progress_status_if_ready with sprint (uses isinstance check)."""
        from vibey.roadmap.models import Sprint

        # Create mock sprint that passes isinstance check
        # Use create_autospec with instance=True for better compatibility
        sprint = MagicMock(spec=Sprint)
        sprint.status = Status.NOT_STARTED
        # Create nested mock for progress attribute
        progress_mock = MagicMock()
        progress_mock.tasks_completed = 1
        type(sprint).progress = property(lambda self: progress_mock)

        with patch('vibey.cli.roadmap_lib.status.FileSystemManager'):
            progressed, new_status, message = progress_status_if_ready(sprint)

        assert progressed is True
        assert new_status == Status.IN_PROGRESS

    def test_progress_status_if_ready_unknown_type(self):
        """Test progress_status_if_ready with unknown type."""
        obj = {"not": "valid"}

        with patch('vibey.cli.roadmap_lib.status.FileSystemManager'):
            progressed, new_status, message = progress_status_if_ready(obj)

        assert progressed is False
        assert new_status is None
        assert "unknown" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
