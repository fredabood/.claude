"""
Tests for vibey.cli.roadmap_lib.blockers module.

Tests blocker computation for roadmap objects.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timezone

from vibey.cli.roadmap_lib.blockers import (
    BlockerComputer,
    compute_blockers,
    is_blocked,
)


class TestStatusSatisfied:
    """Test _status_satisfied helper method."""

    @pytest.fixture
    def computer(self):
        """Create BlockerComputer instance."""
        with patch('vibey.cli.roadmap_lib.blockers.FileSystemManager'):
            return BlockerComputer()

    def test_same_status_satisfied(self, computer):
        """Test same status is satisfied."""
        assert computer._status_satisfied("completed", "completed") is True

    def test_higher_status_satisfied(self, computer):
        """Test higher status satisfies lower requirement."""
        assert computer._status_satisfied("completed", "in_progress") is True
        assert computer._status_satisfied("deployed", "completed") is True

    def test_lower_status_not_satisfied(self, computer):
        """Test lower status doesn't satisfy higher requirement."""
        assert computer._status_satisfied("in_progress", "completed") is False
        assert computer._status_satisfied("not_started", "in_progress") is False

    def test_status_progression_order(self, computer):
        """Test full status progression order."""
        # not_started < in_progress < paused < completion_gate_check < completed
        assert computer._status_satisfied("not_started", "not_started") is True
        assert computer._status_satisfied("in_progress", "not_started") is True
        assert computer._status_satisfied("paused", "in_progress") is True
        assert computer._status_satisfied("completed", "paused") is True
        assert computer._status_satisfied("production_ready", "completed") is True

    def test_unknown_status_exact_match(self, computer):
        """Test unknown status requires exact match."""
        assert computer._status_satisfied("custom", "custom") is True
        assert computer._status_satisfied("custom", "other") is False


class TestComputeRoadmapBlockers:
    """Test roadmap blocker computation."""

    @pytest.fixture
    def computer(self):
        """Create BlockerComputer instance."""
        with patch('vibey.cli.roadmap_lib.blockers.FileSystemManager'):
            return BlockerComputer()

    def test_no_dependencies_no_blockers(self, computer):
        """Test roadmap with no dependencies has no blockers."""
        roadmap = MagicMock()
        roadmap.dependencies = []

        blockers = computer.compute_roadmap_blockers(roadmap)

        assert blockers == []

    def test_completed_dependency_no_blocker(self, computer):
        """Test completed external dependency is not a blocker."""
        dep = MagicMock()
        dep.name = "external-dep"
        dep.status = "completed"

        roadmap = MagicMock()
        roadmap.dependencies = [dep]

        blockers = computer.compute_roadmap_blockers(roadmap)

        assert blockers == []

    def test_incomplete_dependency_is_blocker(self, computer):
        """Test incomplete external dependency is a blocker."""
        dep = MagicMock()
        dep.name = "external-dep"
        dep.status = "in_progress"

        roadmap = MagicMock()
        roadmap.dependencies = [dep]

        blockers = computer.compute_roadmap_blockers(roadmap)

        assert len(blockers) == 1
        assert blockers[0].dependency_id == "external-dep"
        assert blockers[0].current_status == "in_progress"
        assert blockers[0].required_status == "completed"


class TestComputeTrackBlockers:
    """Test track blocker computation."""

    @pytest.fixture
    def computer(self):
        """Create BlockerComputer instance."""
        with patch('vibey.cli.roadmap_lib.blockers.FileSystemManager'):
            return BlockerComputer()

    def test_no_dependencies_no_blockers(self, computer):
        """Test track with no dependencies has no blockers."""
        track = MagicMock()
        track.dependencies = []

        blockers = computer.compute_track_blockers(track)

        assert blockers == []

    def test_missing_dependency_is_blocker(self, computer):
        """Test missing dependency creates blocker."""
        dep = MagicMock()
        dep.target_id = "missing-track"
        dep.type.value = "track"
        dep.target_status = "completed"

        track = MagicMock()
        track.dependencies = [dep]

        # Mock _get_object_status to return None (not found)
        computer._get_object_status = MagicMock(return_value=None)

        blockers = computer.compute_track_blockers(track)

        assert len(blockers) == 1
        assert blockers[0].dependency_id == "missing-track"
        assert blockers[0].current_status == "not_found"

    def test_unsatisfied_dependency_is_blocker(self, computer):
        """Test unsatisfied dependency creates blocker."""
        dep = MagicMock()
        dep.target_id = "other-track"
        dep.type.value = "track"
        dep.target_status = "completed"

        track = MagicMock()
        track.dependencies = [dep]

        # Mock _get_object_status to return in_progress
        computer._get_object_status = MagicMock(return_value="in_progress")

        blockers = computer.compute_track_blockers(track)

        assert len(blockers) == 1
        assert blockers[0].current_status == "in_progress"
        assert blockers[0].required_status == "completed"

    def test_satisfied_dependency_no_blocker(self, computer):
        """Test satisfied dependency is not a blocker."""
        dep = MagicMock()
        dep.target_id = "other-track"
        dep.type.value = "track"
        dep.target_status = "in_progress"

        track = MagicMock()
        track.dependencies = [dep]

        # Mock _get_object_status to return completed (satisfies in_progress)
        computer._get_object_status = MagicMock(return_value="completed")

        blockers = computer.compute_track_blockers(track)

        assert blockers == []


class TestComputeSprintBlockers:
    """Test sprint blocker computation."""

    @pytest.fixture
    def computer(self):
        """Create BlockerComputer instance."""
        with patch('vibey.cli.roadmap_lib.blockers.FileSystemManager'):
            return BlockerComputer()

    def test_no_gates_no_blockers(self, computer):
        """Test sprint with no development gates has no blockers."""
        sprint = MagicMock()
        sprint.development_gates = []

        blockers = computer.compute_sprint_blockers(sprint)

        assert blockers == []

    def test_unsatisfied_gate_is_blocker(self, computer):
        """Test unsatisfied development gate creates blocker."""
        gate = MagicMock()
        gate.target_id = "prereq-sprint"
        gate.type.value = "sprint"
        gate.target_status = "completed"

        sprint = MagicMock()
        sprint.development_gates = [gate]

        computer._get_object_status = MagicMock(return_value="in_progress")

        blockers = computer.compute_sprint_blockers(sprint)

        assert len(blockers) == 1
        assert blockers[0].dependency_id == "prereq-sprint"


class TestComputeTaskBlockers:
    """Test task blocker computation."""

    @pytest.fixture
    def computer(self):
        """Create BlockerComputer instance."""
        with patch('vibey.cli.roadmap_lib.blockers.FileSystemManager'):
            return BlockerComputer()

    def test_no_dependencies_no_blockers(self, computer):
        """Test task with no dependencies has no blockers."""
        task = MagicMock()
        task.dependencies = []

        blockers = computer.compute_task_blockers(task)

        assert blockers == []

    def test_unsatisfied_task_dependency_is_blocker(self, computer):
        """Test unsatisfied task dependency creates blocker."""
        dep = MagicMock()
        dep.target_id = "prereq-task"
        dep.type.value = "task"
        dep.target_status = "completed"

        task = MagicMock()
        task.dependencies = [dep]

        computer._get_object_status = MagicMock(return_value="in_progress")

        blockers = computer.compute_task_blockers(task)

        assert len(blockers) == 1
        assert blockers[0].dependency_id == "prereq-task"


class TestGetObjectStatus:
    """Test _get_object_status helper method."""

    @pytest.fixture
    def computer(self):
        """Create BlockerComputer instance."""
        with patch('vibey.cli.roadmap_lib.blockers.FileSystemManager') as mock_fs:
            mock_fs_instance = MagicMock()
            mock_fs.return_value = mock_fs_instance
            comp = BlockerComputer()
            comp.fs = mock_fs_instance
            return comp

    def test_unknown_type_returns_none(self, computer):
        """Test unknown object type returns None."""
        result = computer._get_object_status("some-id", "unknown_type")
        assert result is None

    @patch('vibey.cli.roadmap_lib.blockers.load_track')
    def test_track_status(self, mock_load, computer):
        """Test getting track status."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        computer.fs.get_track_path.return_value = mock_path

        mock_track = MagicMock()
        mock_track.status.value = "completed"
        mock_load.return_value = mock_track

        result = computer._get_object_status("some-track", "track")

        assert result == "completed"

    def test_track_not_found(self, computer):
        """Test getting status for nonexistent track."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        computer.fs.get_track_path.return_value = mock_path

        result = computer._get_object_status("missing-track", "track")

        assert result is None

    @patch('vibey.cli.roadmap_lib.blockers.load_sprint')
    def test_sprint_status(self, mock_load, computer):
        """Test getting sprint status."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        computer.fs.get_sprint_path.return_value = mock_path

        mock_sprint = MagicMock()
        mock_sprint.status.value = "in_progress"
        mock_load.return_value = mock_sprint

        result = computer._get_object_status("some-sprint", "sprint")

        assert result == "in_progress"


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch('vibey.cli.roadmap_lib.blockers.FileSystemManager')
    def test_compute_blockers_roadmap(self, mock_fs):
        """Test compute_blockers with roadmap."""
        from vibey.roadmap.models import Roadmap

        roadmap = MagicMock(spec=Roadmap)
        roadmap.dependencies = []

        blockers = compute_blockers(roadmap)

        assert blockers == []

    @patch('vibey.cli.roadmap_lib.blockers.FileSystemManager')
    def test_compute_blockers_unknown_type(self, mock_fs):
        """Test compute_blockers with unknown type."""
        obj = "not a valid object"

        blockers = compute_blockers(obj)

        assert blockers == []

    @patch('vibey.cli.roadmap_lib.blockers.FileSystemManager')
    def test_is_blocked_false(self, mock_fs):
        """Test is_blocked returns False with no blockers."""
        from vibey.roadmap.models import Track

        track = MagicMock(spec=Track)
        track.dependencies = []

        result = is_blocked(track)

        assert result is False

    @patch('vibey.cli.roadmap_lib.blockers.FileSystemManager')
    def test_is_blocked_true(self, mock_fs):
        """Test is_blocked returns True with blockers."""
        from vibey.roadmap.models import Roadmap

        dep = MagicMock()
        dep.name = "ext-dep"
        dep.status = "pending"

        roadmap = MagicMock(spec=Roadmap)
        roadmap.dependencies = [dep]

        result = is_blocked(roadmap)

        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
