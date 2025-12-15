"""
Tests for vibey.roadmap.models.common module.

Tests enums, dataclasses, and utility functions.
"""

import pytest
from datetime import datetime, timezone, timedelta

from vibey.roadmap.models.common import (
    safe_datetime_compare,
    Status,
    TaskStatus,
    Priority,
    TaskType,
    GateStatus,
    DependencyType,
    Complexity,
    SizeCategory,
    DeliverableType,
    ActivityType,
    VersionBumpTrigger,
    DependencyStatus,
    PlatformDeployment,
)


class TestSafeDatetimeCompare:
    """Test safe_datetime_compare function."""

    def test_both_none(self):
        """Test with both datetimes None."""
        assert safe_datetime_compare(None, None) is None

    def test_first_none(self):
        """Test with first datetime None."""
        dt = datetime.now(timezone.utc)
        assert safe_datetime_compare(None, dt) is None

    def test_second_none(self):
        """Test with second datetime None."""
        dt = datetime.now(timezone.utc)
        assert safe_datetime_compare(dt, None) is None

    def test_equal_aware_datetimes(self):
        """Test equal timezone-aware datetimes."""
        dt = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert safe_datetime_compare(dt, dt) == 0

    def test_first_earlier(self):
        """Test first datetime is earlier."""
        dt1 = datetime(2025, 12, 14, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert safe_datetime_compare(dt1, dt2) == -1

    def test_first_later(self):
        """Test first datetime is later."""
        dt1 = datetime(2025, 12, 16, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert safe_datetime_compare(dt1, dt2) == 1

    def test_naive_datetime(self):
        """Test with naive datetime (no timezone)."""
        dt1 = datetime(2025, 12, 14, 10, 0, 0)  # naive
        dt2 = datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        # Should handle gracefully
        result = safe_datetime_compare(dt1, dt2)
        assert result == -1

    def test_both_naive(self):
        """Test with both naive datetimes."""
        dt1 = datetime(2025, 12, 14, 10, 0, 0)
        dt2 = datetime(2025, 12, 15, 10, 0, 0)
        assert safe_datetime_compare(dt1, dt2) == -1


class TestStatusEnum:
    """Test Status enum."""

    def test_all_statuses(self):
        """Test all status values exist."""
        assert Status.NOT_STARTED.value == "not_started"
        assert Status.IN_PROGRESS.value == "in_progress"
        assert Status.PAUSED.value == "paused"
        assert Status.COMPLETION_GATE_CHECK.value == "completion_gate_check"
        assert Status.COMPLETED.value == "completed"
        assert Status.PRODUCTION_GATE_CHECK.value == "production_gate_check"
        assert Status.PRODUCTION_READY.value == "production_ready"
        assert Status.DEPLOYED.value == "deployed"
        assert Status.SUPERSEDED.value == "superseded"
        assert Status.WONT_DO.value == "wont_do"

    def test_string_enum(self):
        """Test Status is a string enum."""
        assert isinstance(Status.COMPLETED, str)
        assert Status.COMPLETED == "completed"


class TestTaskStatusEnum:
    """Test TaskStatus enum."""

    def test_no_production_statuses(self):
        """Test TaskStatus doesn't have production statuses."""
        values = [s.value for s in TaskStatus]
        assert "production_ready" not in values
        assert "production_gate_check" not in values
        assert "deployed" not in values


class TestPriorityEnum:
    """Test Priority enum."""

    def test_all_priorities(self):
        """Test all priority values."""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


class TestTaskTypeEnum:
    """Test TaskType enum."""

    def test_development_types(self):
        """Test development task types."""
        assert TaskType.DEVELOPMENT.value == "development"
        assert TaskType.TESTING.value == "testing"
        assert TaskType.DOCUMENTATION.value == "documentation"

    def test_gate_types(self):
        """Test gate task types."""
        assert TaskType.GATE.value == "gate"
        assert TaskType.COMPLETION_GATE.value == "completion_gate"
        assert TaskType.PRODUCTION_GATE.value == "production_gate"


class TestSizeCategory:
    """Test SizeCategory enum."""

    def test_from_tokens_small(self):
        """Test small category from tokens."""
        assert SizeCategory.from_tokens(5000) == SizeCategory.SMALL
        assert SizeCategory.from_tokens(9999) == SizeCategory.SMALL

    def test_from_tokens_medium(self):
        """Test medium category from tokens."""
        assert SizeCategory.from_tokens(10000) == SizeCategory.MEDIUM
        assert SizeCategory.from_tokens(29999) == SizeCategory.MEDIUM

    def test_from_tokens_large(self):
        """Test large category from tokens."""
        assert SizeCategory.from_tokens(30000) == SizeCategory.LARGE
        assert SizeCategory.from_tokens(74999) == SizeCategory.LARGE

    def test_from_tokens_xlarge(self):
        """Test x-large category from tokens."""
        assert SizeCategory.from_tokens(75000) == SizeCategory.X_LARGE
        assert SizeCategory.from_tokens(149999) == SizeCategory.X_LARGE

    def test_from_tokens_xxlarge(self):
        """Test xx-large category from tokens."""
        assert SizeCategory.from_tokens(150000) == SizeCategory.XX_LARGE
        assert SizeCategory.from_tokens(500000) == SizeCategory.XX_LARGE

    def test_get_token_range(self):
        """Test getting token range for category."""
        min_t, max_t = SizeCategory.SMALL.get_token_range()
        assert min_t == 0
        assert max_t == 10_000

        min_t, max_t = SizeCategory.MEDIUM.get_token_range()
        assert min_t == 10_000
        assert max_t == 30_000

    def test_get_midpoint(self):
        """Test getting midpoint for category."""
        assert SizeCategory.SMALL.get_midpoint() == 5000
        assert SizeCategory.MEDIUM.get_midpoint() == 20000


class TestDependencyStatus:
    """Test DependencyStatus dataclass."""

    @pytest.fixture
    def sample_dependency(self):
        """Create a sample dependency status."""
        return DependencyStatus(
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="in_progress",
            blocks_transition_to="completed",
            last_checked=datetime.now(timezone.utc),
        )

    def test_is_satisfied_not_satisfied(self, sample_dependency):
        """Test is_satisfied when not satisfied."""
        assert not sample_dependency.is_satisfied()

    def test_is_satisfied_satisfied(self):
        """Test is_satisfied when satisfied."""
        dep = DependencyStatus(
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="completed",
            blocks_transition_to="completed",
            last_checked=datetime.now(timezone.utc),
        )
        assert dep.is_satisfied()

    def test_is_satisfied_beyond_required(self):
        """Test is_satisfied when beyond required status."""
        dep = DependencyStatus(
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="production_ready",
            blocks_transition_to="completed",
            last_checked=datetime.now(timezone.utc),
        )
        assert dep.is_satisfied()

    def test_blocks_transition_true(self, sample_dependency):
        """Test blocks_transition returns True when blocking."""
        assert sample_dependency.blocks_transition("completed")

    def test_blocks_transition_false_earlier_status(self, sample_dependency):
        """Test blocks_transition returns False for earlier status."""
        assert not sample_dependency.blocks_transition("in_progress")

    def test_blocks_transition_false_satisfied(self):
        """Test blocks_transition returns False when satisfied."""
        dep = DependencyStatus(
            blocker_id="task-001",
            blocker_type="task",
            required_status="completed",
            current_status="completed",
            blocks_transition_to="completed",
            last_checked=datetime.now(timezone.utc),
        )
        assert not dep.blocks_transition("completed")


class TestPlatformDeployment:
    """Test PlatformDeployment dataclass."""

    def test_valid_deployment(self):
        """Test creating a valid deployment."""
        now = int(datetime.now(timezone.utc).timestamp())
        deploy = PlatformDeployment(
            platform="claude-code",
            context_window=200000,
            deployed_at=now,
            deployed_by="user@example.com",
            primary=True,
        )
        assert deploy.platform == "claude-code"
        assert deploy.context_window == 200000
        assert deploy.primary

    def test_empty_platform_raises(self):
        """Test empty platform raises error."""
        with pytest.raises(ValueError, match="Platform name is required"):
            PlatformDeployment(
                platform="",
                context_window=200000,
                deployed_at=1234567890,
                deployed_by="user@example.com",
            )

    def test_negative_context_window_raises(self):
        """Test negative context window raises error."""
        with pytest.raises(ValueError, match="must be positive"):
            PlatformDeployment(
                platform="claude-code",
                context_window=-100,
                deployed_at=1234567890,
                deployed_by="user@example.com",
            )

    def test_zero_context_window_raises(self):
        """Test zero context window raises error."""
        with pytest.raises(ValueError, match="must be positive"):
            PlatformDeployment(
                platform="claude-code",
                context_window=0,
                deployed_at=1234567890,
                deployed_by="user@example.com",
            )

    def test_negative_timestamp_raises(self):
        """Test negative timestamp raises error."""
        with pytest.raises(ValueError, match="positive Unix timestamp"):
            PlatformDeployment(
                platform="claude-code",
                context_window=200000,
                deployed_at=-1,
                deployed_by="user@example.com",
            )

    def test_empty_deployed_by_raises(self):
        """Test empty deployed_by raises error."""
        with pytest.raises(ValueError, match="deployed_by is required"):
            PlatformDeployment(
                platform="claude-code",
                context_window=200000,
                deployed_at=1234567890,
                deployed_by="",
            )


class TestActivityTypeEnum:
    """Test ActivityType enum."""

    def test_roadmap_events(self):
        """Test roadmap-related events."""
        assert ActivityType.ROADMAP_STARTED.value == "roadmap_started"
        assert ActivityType.ROADMAP_COMPLETED.value == "roadmap_completed"
        assert ActivityType.ROADMAP_INITIALIZED.value == "roadmap_initialized"

    def test_track_events(self):
        """Test track-related events."""
        assert ActivityType.TRACK_ADDED.value == "track_added"
        assert ActivityType.TRACK_STARTED.value == "track_started"
        assert ActivityType.TRACK_COMPLETED.value == "track_completed"

    def test_sprint_events(self):
        """Test sprint-related events."""
        assert ActivityType.SPRINT_STARTED.value == "sprint_started"
        assert ActivityType.SPRINT_COMPLETED.value == "sprint_completed"

    def test_task_events(self):
        """Test task-related events."""
        assert ActivityType.TASK_STARTED.value == "task_started"
        assert ActivityType.TASK_COMPLETED.value == "task_completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
