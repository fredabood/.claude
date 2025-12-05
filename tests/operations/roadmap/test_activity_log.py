"""
Tests for unified activity logging in roadmap operations.

Tests the UnifiedActivityLog class and convenience functions.
"""

import pytest
from pathlib import Path

# Get the project root directory (where .vibey/ exists)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestUnifiedActivityLog:
    """Tests for UnifiedActivityLog class."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_get_activity_log_returns_instance(self, root_dir):
        """Test that get_activity_log returns a UnifiedActivityLog instance."""
        from vibey.operations.roadmap.activity_log import (
            get_activity_log,
            UnifiedActivityLog,
        )

        log = get_activity_log(root_dir)
        assert isinstance(log, UnifiedActivityLog)
        assert log.root_dir == root_dir

    def test_get_recent_activities(self, root_dir):
        """Test getting recent activities."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        activities = log.get_recent_activities(limit=10)

        assert isinstance(activities, list)
        # Each activity should be an AuditEntry
        for activity in activities:
            assert hasattr(activity, 'timestamp')
            assert hasattr(activity, 'object_type')
            assert hasattr(activity, 'object_id')

    def test_get_object_activities(self, root_dir):
        """Test getting activities for a specific object."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        activities = log.get_object_activities("sqlite-backend-9-task-001")

        assert isinstance(activities, list)
        # All activities should be for the specified object
        for activity in activities:
            assert activity.object_id == "sqlite-backend-9-task-001"

    def test_generate_report(self, root_dir):
        """Test generating an activity report."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        report = log.generate_report()

        assert isinstance(report, str)
        assert "Audit Trail Report" in report

    def test_generate_report_for_object(self, root_dir):
        """Test generating a report for a specific object."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        report = log.generate_report(object_id="sqlite-backend-9-task-001")

        assert isinstance(report, str)
        assert "sqlite-backend-9-task-001" in report or "Total entries: 0" in report

    def test_get_suspicious_activities(self, root_dir):
        """Test detecting suspicious activities."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        suspicious = log.get_suspicious_activities()

        assert isinstance(suspicious, list)
        # Each suspicious entry is a tuple of (entry, reason)
        for item in suspicious:
            assert isinstance(item, tuple)
            assert len(item) == 2


class TestActivityLogConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_log_task_started_function_exists(self):
        """Test that log_task_started function exists and is callable."""
        from vibey.operations.roadmap.activity_log import log_task_started

        assert callable(log_task_started)

    def test_log_task_completed_function_exists(self):
        """Test that log_task_completed function exists and is callable."""
        from vibey.operations.roadmap.activity_log import log_task_completed

        assert callable(log_task_completed)

    def test_log_sprint_started_function_exists(self):
        """Test that log_sprint_started function exists and is callable."""
        from vibey.operations.roadmap.activity_log import log_sprint_started

        assert callable(log_sprint_started)

    def test_log_sprint_completed_function_exists(self):
        """Test that log_sprint_completed function exists and is callable."""
        from vibey.operations.roadmap.activity_log import log_sprint_completed

        assert callable(log_sprint_completed)

    def test_log_track_started_function_exists(self):
        """Test that log_track_started function exists and is callable."""
        from vibey.operations.roadmap.activity_log import log_track_started

        assert callable(log_track_started)

    def test_log_track_completed_function_exists(self):
        """Test that log_track_completed function exists and is callable."""
        from vibey.operations.roadmap.activity_log import log_track_completed

        assert callable(log_track_completed)


class TestActivityLogMethodSignatures:
    """Tests for method signatures and parameters."""

    @pytest.fixture
    def root_dir(self):
        """Use the actual project root as test fixture."""
        return PROJECT_ROOT

    def test_log_task_blocked_method_exists(self, root_dir):
        """Test that log_task_blocked method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_task_blocked')
        assert callable(log.log_task_blocked)

    def test_log_task_unblocked_method_exists(self, root_dir):
        """Test that log_task_unblocked method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_task_unblocked')
        assert callable(log.log_task_unblocked)

    def test_log_sprint_progress_method_exists(self, root_dir):
        """Test that log_sprint_progress method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_sprint_progress')
        assert callable(log.log_sprint_progress)

    def test_log_track_progress_method_exists(self, root_dir):
        """Test that log_track_progress method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_track_progress')
        assert callable(log.log_track_progress)

    def test_log_quality_gate_passed_method_exists(self, root_dir):
        """Test that log_quality_gate_passed method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_quality_gate_passed')
        assert callable(log.log_quality_gate_passed)

    def test_log_quality_gate_failed_method_exists(self, root_dir):
        """Test that log_quality_gate_failed method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_quality_gate_failed')
        assert callable(log.log_quality_gate_failed)

    def test_log_standard_enforced_method_exists(self, root_dir):
        """Test that log_standard_enforced method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_standard_enforced')
        assert callable(log.log_standard_enforced)

    def test_log_activity_method_exists(self, root_dir):
        """Test that log_activity method exists."""
        from vibey.operations.roadmap.activity_log import get_activity_log

        log = get_activity_log(root_dir)
        assert hasattr(log, 'log_activity')
        assert callable(log.log_activity)


class TestActivityLogImports:
    """Tests for module imports."""

    def test_can_import_from_operations_module(self):
        """Test that activity log can be imported from operations module."""
        from vibey.operations.roadmap import (
            UnifiedActivityLog,
            get_activity_log,
            log_task_started,
            log_task_completed,
            log_sprint_started,
            log_sprint_completed,
            log_track_started,
            log_track_completed,
        )

        assert UnifiedActivityLog is not None
        assert callable(get_activity_log)
        assert callable(log_task_started)
        assert callable(log_task_completed)
        assert callable(log_sprint_started)
        assert callable(log_sprint_completed)
        assert callable(log_track_started)
        assert callable(log_track_completed)
