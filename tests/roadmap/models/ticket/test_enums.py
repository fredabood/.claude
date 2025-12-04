"""
Tests for unified ticket architecture enum types.

Covers all 12 enum types defined in vibey.roadmap.models.ticket.enums.
"""

import pytest
from vibey.roadmap.models.ticket.enums import (
    # Ticket lifecycle
    TicketStatus,
    TicketType,
    # Task classification
    TaskType,
    Complexity,
    Priority,
    # Criterion targets
    CriterionTargetType,
    ThresholdComparison,
    # Requirement system
    InheritMode,
    EnforcementMode,
    RequirementType,
    # Dependencies
    DependencyRelation,
    # Deliverables
    DeliverableType,
    # Activity log
    ActivityType,
)


# =============================================================================
# TicketStatus Tests
# =============================================================================


class TestTicketStatus:
    """Tests for TicketStatus enum."""

    def test_all_values_exist(self):
        """Verify all expected status values exist."""
        expected = [
            "not_started",
            "in_progress",
            "paused",
            "completion_gate_check",
            "completed",
            "production_gate_check",
            "production_ready",
            "deployed",
            "wont_do",
            "superseded",
        ]
        actual = [s.value for s in TicketStatus]
        assert set(actual) == set(expected)

    def test_value_serialization(self):
        """Verify enum value is correct string."""
        assert TicketStatus.NOT_STARTED.value == "not_started"
        assert TicketStatus.COMPLETED.value == "completed"
        # StrEnum allows direct comparison with strings
        assert TicketStatus.NOT_STARTED == "not_started"
        assert TicketStatus.COMPLETED == "completed"

    def test_from_string(self):
        """Verify enum can be created from string."""
        assert TicketStatus("not_started") == TicketStatus.NOT_STARTED
        assert TicketStatus("completed") == TicketStatus.COMPLETED

    def test_progression_order(self):
        """Verify progression order is correct."""
        order = TicketStatus.progression_order()
        assert order[0] == TicketStatus.NOT_STARTED
        assert order[-1] == TicketStatus.DEPLOYED
        assert len(order) == 8  # Excludes terminal statuses

    def test_terminal_statuses(self):
        """Verify terminal statuses are identified."""
        terminal = TicketStatus.terminal_statuses()
        assert TicketStatus.WONT_DO in terminal
        assert TicketStatus.SUPERSEDED in terminal
        assert TicketStatus.COMPLETED not in terminal

    def test_is_terminal(self):
        """Verify is_terminal method works."""
        assert TicketStatus.WONT_DO.is_terminal()
        assert TicketStatus.SUPERSEDED.is_terminal()
        assert not TicketStatus.COMPLETED.is_terminal()
        assert not TicketStatus.NOT_STARTED.is_terminal()

    def test_can_progress_to(self):
        """Verify can_progress_to logic."""
        # Forward progression allowed
        assert TicketStatus.NOT_STARTED.can_progress_to(TicketStatus.IN_PROGRESS)
        assert TicketStatus.IN_PROGRESS.can_progress_to(TicketStatus.COMPLETED)

        # Backward progression not allowed
        assert not TicketStatus.COMPLETED.can_progress_to(TicketStatus.NOT_STARTED)

        # Same status not allowed
        assert not TicketStatus.IN_PROGRESS.can_progress_to(TicketStatus.IN_PROGRESS)

        # Terminal statuses cannot progress
        assert not TicketStatus.WONT_DO.can_progress_to(TicketStatus.COMPLETED)


# =============================================================================
# TicketType Tests
# =============================================================================


class TestTicketType:
    """Tests for TicketType enum."""

    def test_all_values_exist(self):
        """Verify all expected type values exist."""
        expected = ["roadmap", "track", "sprint", "task"]
        actual = [t.value for t in TicketType]
        assert set(actual) == set(expected)

    def test_hierarchy_order(self):
        """Verify hierarchy order is correct."""
        order = TicketType.hierarchy_order()
        assert order == [
            TicketType.ROADMAP,
            TicketType.TRACK,
            TicketType.SPRINT,
            TicketType.TASK,
        ]

    def test_parent_type(self):
        """Verify parent_type returns correct parent."""
        assert TicketType.TASK.parent_type() == TicketType.SPRINT
        assert TicketType.SPRINT.parent_type() == TicketType.TRACK
        assert TicketType.TRACK.parent_type() == TicketType.ROADMAP
        assert TicketType.ROADMAP.parent_type() is None

    def test_child_type(self):
        """Verify child_type returns correct child."""
        assert TicketType.ROADMAP.child_type() == TicketType.TRACK
        assert TicketType.TRACK.child_type() == TicketType.SPRINT
        assert TicketType.SPRINT.child_type() == TicketType.TASK
        assert TicketType.TASK.child_type() is None


# =============================================================================
# TaskType Tests
# =============================================================================


class TestTaskType:
    """Tests for TaskType enum."""

    def test_all_values_exist(self):
        """Verify all expected task type values exist."""
        expected = [
            "development",
            "documentation",
            "testing",
            "research",
            "review",
            "infrastructure",
            "gate",
        ]
        actual = [t.value for t in TaskType]
        assert set(actual) == set(expected)

    def test_value_serialization(self):
        """Verify enum value is correct string."""
        assert TaskType.DEVELOPMENT.value == "development"
        assert TaskType.GATE.value == "gate"
        # StrEnum allows direct comparison with strings
        assert TaskType.DEVELOPMENT == "development"
        assert TaskType.GATE == "gate"


# =============================================================================
# Complexity Tests
# =============================================================================


class TestComplexity:
    """Tests for Complexity enum."""

    def test_all_values_exist(self):
        """Verify all expected complexity values exist."""
        expected = ["low", "medium", "high", "critical"]
        actual = [c.value for c in Complexity]
        assert set(actual) == set(expected)


# =============================================================================
# Priority Tests
# =============================================================================


class TestPriority:
    """Tests for Priority enum."""

    def test_all_values_exist(self):
        """Verify all expected priority values exist."""
        expected = ["critical", "high", "medium", "low"]
        actual = [p.value for p in Priority]
        assert set(actual) == set(expected)

    def test_priority_order(self):
        """Verify priority order is highest to lowest."""
        order = Priority.priority_order()
        assert order == [
            Priority.CRITICAL,
            Priority.HIGH,
            Priority.MEDIUM,
            Priority.LOW,
        ]

    def test_comparison_operators(self):
        """Verify comparison operators work correctly."""
        assert Priority.CRITICAL > Priority.HIGH
        assert Priority.HIGH > Priority.MEDIUM
        assert Priority.MEDIUM > Priority.LOW

        assert Priority.LOW < Priority.MEDIUM
        assert Priority.MEDIUM < Priority.HIGH
        assert Priority.HIGH < Priority.CRITICAL

        assert Priority.HIGH >= Priority.HIGH
        assert Priority.HIGH >= Priority.MEDIUM
        assert Priority.LOW <= Priority.LOW
        assert Priority.LOW <= Priority.MEDIUM


# =============================================================================
# CriterionTargetType Tests
# =============================================================================


class TestCriterionTargetType:
    """Tests for CriterionTargetType enum."""

    def test_core_values_exist(self):
        """Verify core target type values exist."""
        core_expected = [
            "completable",
            "file_exists",
            "test_passes",
            "test_coverage",
            "threshold",
            "manual",
            "external",
        ]
        actual = [t.value for t in CriterionTargetType]
        for expected in core_expected:
            assert expected in actual, f"Missing {expected}"


# =============================================================================
# ThresholdComparison Tests
# =============================================================================


class TestThresholdComparison:
    """Tests for ThresholdComparison enum."""

    def test_all_values_exist(self):
        """Verify all comparison operators exist."""
        expected = ["gte", "gt", "eq", "lte", "lt"]
        actual = [c.value for c in ThresholdComparison]
        assert set(actual) == set(expected)

    def test_compare_gte(self):
        """Test >= comparison."""
        assert ThresholdComparison.GTE.compare(80, 80)
        assert ThresholdComparison.GTE.compare(90, 80)
        assert not ThresholdComparison.GTE.compare(70, 80)

    def test_compare_gt(self):
        """Test > comparison."""
        assert ThresholdComparison.GT.compare(90, 80)
        assert not ThresholdComparison.GT.compare(80, 80)
        assert not ThresholdComparison.GT.compare(70, 80)

    def test_compare_eq(self):
        """Test == comparison."""
        assert ThresholdComparison.EQ.compare(80, 80)
        assert not ThresholdComparison.EQ.compare(90, 80)
        assert not ThresholdComparison.EQ.compare(70, 80)

    def test_compare_lte(self):
        """Test <= comparison."""
        assert ThresholdComparison.LTE.compare(80, 80)
        assert ThresholdComparison.LTE.compare(70, 80)
        assert not ThresholdComparison.LTE.compare(90, 80)

    def test_compare_lt(self):
        """Test < comparison."""
        assert ThresholdComparison.LT.compare(70, 80)
        assert not ThresholdComparison.LT.compare(80, 80)
        assert not ThresholdComparison.LT.compare(90, 80)

    def test_description(self):
        """Test human-readable descriptions."""
        assert ThresholdComparison.GTE.description(80) == "at least 80"
        assert ThresholdComparison.GT.description(80) == "more than 80"
        assert ThresholdComparison.EQ.description(80) == "exactly 80"
        assert ThresholdComparison.LTE.description(80) == "at most 80"
        assert ThresholdComparison.LT.description(80) == "less than 80"


# =============================================================================
# InheritMode Tests
# =============================================================================


class TestInheritMode:
    """Tests for InheritMode enum."""

    def test_all_values_exist(self):
        """Verify all inheritance modes exist."""
        expected = ["inherit", "override", "skip"]
        actual = [m.value for m in InheritMode]
        assert set(actual) == set(expected)


# =============================================================================
# EnforcementMode Tests
# =============================================================================


class TestEnforcementMode:
    """Tests for EnforcementMode enum."""

    def test_all_values_exist(self):
        """Verify all enforcement modes exist."""
        expected = ["blocking", "warning", "audit"]
        actual = [m.value for m in EnforcementMode]
        assert set(actual) == set(expected)


# =============================================================================
# RequirementType Tests
# =============================================================================


class TestRequirementType:
    """Tests for RequirementType enum."""

    def test_all_values_exist(self):
        """Verify all requirement types exist."""
        expected = [
            "test_coverage",
            "code_style",
            "documentation",
            "security",
            "performance",
            "review",
            "custom",
        ]
        actual = [r.value for r in RequirementType]
        assert set(actual) == set(expected)


# =============================================================================
# DependencyRelation Tests
# =============================================================================


class TestDependencyRelation:
    """Tests for DependencyRelation enum."""

    def test_all_values_exist(self):
        """Verify all dependency relations exist."""
        expected = ["blocks", "depends_on", "related"]
        actual = [d.value for d in DependencyRelation]
        assert set(actual) == set(expected)


# =============================================================================
# DeliverableType Tests
# =============================================================================


class TestDeliverableType:
    """Tests for DeliverableType enum."""

    def test_all_values_exist(self):
        """Verify all deliverable types exist."""
        expected = ["code", "test", "documentation", "config", "design", "other"]
        actual = [d.value for d in DeliverableType]
        assert set(actual) == set(expected)


# =============================================================================
# ActivityType Tests
# =============================================================================


class TestActivityType:
    """Tests for ActivityType enum."""

    def test_roadmap_events_exist(self):
        """Verify roadmap event types exist."""
        roadmap_events = [
            "roadmap_initialized",
            "roadmap_started",
            "roadmap_completed",
            "roadmap_deployed",
        ]
        actual = [a.value for a in ActivityType]
        for event in roadmap_events:
            assert event in actual

    def test_track_events_exist(self):
        """Verify track event types exist."""
        track_events = ["track_added", "track_started", "track_completed"]
        actual = [a.value for a in ActivityType]
        for event in track_events:
            assert event in actual

    def test_sprint_events_exist(self):
        """Verify sprint event types exist."""
        sprint_events = [
            "sprint_started",
            "sprint_completed",
            "sprint_production_ready",
        ]
        actual = [a.value for a in ActivityType]
        for event in sprint_events:
            assert event in actual

    def test_task_events_exist(self):
        """Verify task event types exist."""
        task_events = ["task_started", "task_completed"]
        actual = [a.value for a in ActivityType]
        for event in task_events:
            assert event in actual

    def test_quality_events_exist(self):
        """Verify quality event types exist."""
        quality_events = ["quality_gate", "criterion_met", "criterion_failed"]
        actual = [a.value for a in ActivityType]
        for event in quality_events:
            assert event in actual


# =============================================================================
# JSON/YAML Serialization Tests
# =============================================================================


class TestSerialization:
    """Tests for JSON/YAML serialization compatibility."""

    def test_str_enum_inheritance(self):
        """Verify all enums inherit from str for serialization."""
        enums_to_test = [
            TicketStatus,
            TicketType,
            TaskType,
            Complexity,
            Priority,
            CriterionTargetType,
            ThresholdComparison,
            InheritMode,
            EnforcementMode,
            RequirementType,
            DependencyRelation,
            DeliverableType,
            ActivityType,
        ]

        for enum_class in enums_to_test:
            for member in enum_class:
                # Should serialize to string value
                assert isinstance(member.value, str)
                # StrEnum members compare equal to their string value
                assert member == member.value
                # Should be usable as dict key
                d = {member: "test"}
                assert d[member] == "test"

    def test_json_round_trip(self):
        """Verify enums survive JSON serialization."""
        import json

        test_data = {
            "status": TicketStatus.IN_PROGRESS.value,
            "type": TicketType.TASK.value,
            "priority": Priority.HIGH.value,
        }

        # Serialize to JSON
        json_str = json.dumps(test_data)

        # Deserialize
        loaded = json.loads(json_str)

        # Reconstruct enums
        assert TicketStatus(loaded["status"]) == TicketStatus.IN_PROGRESS
        assert TicketType(loaded["type"]) == TicketType.TASK
        assert Priority(loaded["priority"]) == Priority.HIGH
