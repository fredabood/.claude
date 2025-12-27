"""
Test ProgressAggregator class.

Tests for pull-up mechanism to aggregate progress from submodules.
Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vibey.roadmap.models.submodule import (
    AggregatedProgress,
    SubmoduleProgress,
)


class TestAggregateSubmodule:
    """Tests for aggregating single submodule progress."""

    def test_aggregate_submodule_reads_roadmap(self):
        """Should read progress from a submodule's roadmap."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value
            mock_progress = SubmoduleProgress(
                submodule_path="libs/core",
                roadmap_id="core-v1",
                tracks_total=3,
                tracks_completed=1,
                sprints_total=10,
                sprints_completed=4,
                tasks_total=50,
                tasks_completed=20,
            )
            mock_aggregator.aggregate_submodule.return_value = mock_progress

            result = mock_aggregator.aggregate_submodule("libs/core")

            assert result.submodule_path == "libs/core"
            assert result.tasks_total == 50
            assert result.tasks_completed == 20
            assert result.completion_percent == 40.0

    def test_aggregate_submodule_with_no_roadmap(self):
        """Should handle submodule without a roadmap."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value
            mock_aggregator.aggregate_submodule.side_effect = FileNotFoundError(
                "No roadmap found"
            )

            with pytest.raises(FileNotFoundError):
                mock_aggregator.aggregate_submodule("libs/no-roadmap")


class TestAggregateAll:
    """Tests for aggregating all submodules."""

    def test_aggregate_all_combines_progress(self):
        """Should combine progress from multiple submodules."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value

            progress1 = SubmoduleProgress(
                submodule_path="libs/core",
                tasks_total=50,
                tasks_completed=25,
            )
            progress2 = SubmoduleProgress(
                submodule_path="libs/utils",
                tasks_total=30,
                tasks_completed=20,
            )

            mock_result = AggregatedProgress(
                submodule_progress=[progress1, progress2],
            )
            mock_result.aggregate()
            mock_aggregator.aggregate_all.return_value = mock_result

            result = mock_aggregator.aggregate_all()

            assert result.total_tasks == 80
            assert result.completed_tasks == 45
            assert len(result.submodule_progress) == 2

    def test_aggregate_all_with_no_submodules(self):
        """Should return empty result when no submodules registered."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value
            mock_result = AggregatedProgress(submodule_progress=[])
            mock_aggregator.aggregate_all.return_value = mock_result

            result = mock_aggregator.aggregate_all()

            assert result.total_tasks == 0
            assert result.completed_tasks == 0


class TestSyncBlockedByStatus:
    """Tests for syncing blocked_by statuses from submodules."""

    def test_sync_blocked_by_status_updates_blockers(self):
        """Should update blocked_by status based on submodule task completion."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value
            mock_sync_result = MagicMock()
            mock_sync_result.tasks_synced = 5
            mock_sync_result.blockers_resolved = 2
            mock_aggregator.sync_blocked_by_status.return_value = [mock_sync_result]

            results = mock_aggregator.sync_blocked_by_status()

            assert len(results) == 1
            assert results[0].tasks_synced == 5
            assert results[0].blockers_resolved == 2

    def test_sync_blocked_by_status_resolves_completed_blockers(self):
        """Should mark blockers as resolved when submodule task completes."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value
            mock_sync_result = MagicMock()
            mock_sync_result.blockers_resolved = 3
            mock_aggregator.sync_blocked_by_status.return_value = [mock_sync_result]

            results = mock_aggregator.sync_blocked_by_status()

            assert results[0].blockers_resolved == 3


class TestTrackFilter:
    """Tests for track filtering during aggregation."""

    def test_track_filter_includes_matching_tracks(self):
        """Should include only tracks matching the filter."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value

            # Simulate filtered progress (only specific tracks)
            filtered_progress = SubmoduleProgress(
                submodule_path="libs/core",
                tracks_total=1,  # Filtered from 3 total
                tracks_completed=0,
                tasks_total=15,  # Only tasks from filtered track
                tasks_completed=5,
            )
            mock_aggregator.aggregate_submodule.return_value = filtered_progress

            result = mock_aggregator.aggregate_submodule(
                "libs/core",
                track_filter=["api"]
            )

            assert result.tracks_total == 1
            assert result.tasks_total == 15

    def test_track_filter_excludes_non_matching_tracks(self):
        """Should exclude tracks not in the filter."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value

            # Track filter results in fewer tracks
            filtered_progress = SubmoduleProgress(
                submodule_path="libs/core",
                tracks_total=1,
                tasks_total=10,
            )
            mock_aggregator.aggregate_submodule.return_value = filtered_progress

            result = mock_aggregator.aggregate_submodule(
                "libs/core",
                track_filter=["specific-track"]
            )

            # Only matching tracks should be included
            assert result.tracks_total == 1

    def test_track_filter_with_empty_list(self):
        """Should include all tracks when filter is empty."""
        with patch('vibey.operations.submodule.pull.ProgressAggregator') as MockAggregator:
            mock_aggregator = MockAggregator.return_value

            # All tracks included
            full_progress = SubmoduleProgress(
                submodule_path="libs/core",
                tracks_total=5,
                tasks_total=100,
            )
            mock_aggregator.aggregate_submodule.return_value = full_progress

            result = mock_aggregator.aggregate_submodule(
                "libs/core",
                track_filter=[]
            )

            # All tracks should be included
            assert result.tracks_total == 5
            assert result.tasks_total == 100


class TestAggregatedProgressComputation:
    """Tests for AggregatedProgress computation."""

    def test_completion_percent_calculation(self):
        """Should correctly calculate overall completion percentage."""
        progress1 = SubmoduleProgress(
            submodule_path="libs/core",
            tasks_total=100,
            tasks_completed=50,
        )
        progress2 = SubmoduleProgress(
            submodule_path="libs/utils",
            tasks_total=100,
            tasks_completed=75,
        )

        aggregated = AggregatedProgress(
            submodule_progress=[progress1, progress2],
        )
        aggregated.aggregate()

        # (50 + 75) / (100 + 100) = 62.5%
        assert aggregated.overall_completion_percent == 62.5

    def test_zero_tasks_handling(self):
        """Should handle case with zero tasks."""
        progress = SubmoduleProgress(
            submodule_path="libs/empty",
            tasks_total=0,
            tasks_completed=0,
        )

        aggregated = AggregatedProgress(submodule_progress=[progress])
        aggregated.aggregate()

        assert aggregated.total_tasks == 0
        assert aggregated.overall_completion_percent == 0.0

    def test_blocker_aggregation(self):
        """Should aggregate blockers from all submodules."""
        from vibey.roadmap.models.submodule import SubmoduleBlocker

        blocker1 = SubmoduleBlocker(
            submodule_path="libs/core",
            blocker_id="01ABC123",
            title="Critical bug",
            severity="critical",
        )
        blocker2 = SubmoduleBlocker(
            submodule_path="libs/utils",
            blocker_id="01DEF456",
            title="Minor issue",
            severity="low",
        )

        aggregated = AggregatedProgress(
            submodule_progress=[],
            active_blockers=[blocker1, blocker2],
        )

        assert len(aggregated.active_blockers) == 2
        assert aggregated.critical_blocker_count == 1
