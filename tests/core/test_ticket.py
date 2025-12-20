"""
Tests for vibey/core/ticket.py - Generic Ticket model.

Tests cover:
- Enum values (HierarchyType, TicketStatus, TicketPriority)
- Ticket model creation and validation
- Default values and optional fields
- Status transition methods
- Serialization/deserialization
"""

import pytest
from datetime import datetime, timezone

from vibey.core.ticket import (
    Criterion,
    CriterionStatus,
    CriterionType,
    HierarchyType,
    Ticket,
    TicketPriority,
    TicketStatus,
)


class TestHierarchyType:
    """Test HierarchyType enum."""

    def test_all_values_exist(self):
        """Verify all expected hierarchy types exist."""
        assert HierarchyType.PROJECT is not None
        assert HierarchyType.WORKSTREAM is not None
        assert HierarchyType.ITERATION is not None
        assert HierarchyType.WORK_ITEM is not None

    def test_value_strings(self):
        """Verify enum value strings."""
        assert HierarchyType.PROJECT.value == "project"
        assert HierarchyType.WORKSTREAM.value == "workstream"
        assert HierarchyType.ITERATION.value == "iteration"
        assert HierarchyType.WORK_ITEM.value == "work_item"


class TestTicketStatus:
    """Test TicketStatus enum."""

    def test_all_values_exist(self):
        """Verify all expected statuses exist."""
        assert TicketStatus.NOT_STARTED is not None
        assert TicketStatus.IN_PROGRESS is not None
        assert TicketStatus.BLOCKED is not None
        assert TicketStatus.COMPLETED is not None
        assert TicketStatus.CANCELLED is not None

    def test_value_strings(self):
        """Verify enum value strings."""
        assert TicketStatus.NOT_STARTED.value == "not_started"
        assert TicketStatus.IN_PROGRESS.value == "in_progress"
        assert TicketStatus.BLOCKED.value == "blocked"
        assert TicketStatus.COMPLETED.value == "completed"
        assert TicketStatus.CANCELLED.value == "cancelled"


class TestTicketPriority:
    """Test TicketPriority enum."""

    def test_all_values_exist(self):
        """Verify all expected priorities exist."""
        assert TicketPriority.LOW is not None
        assert TicketPriority.MEDIUM is not None
        assert TicketPriority.HIGH is not None
        assert TicketPriority.CRITICAL is not None

    def test_value_strings(self):
        """Verify enum value strings."""
        assert TicketPriority.LOW.value == "low"
        assert TicketPriority.MEDIUM.value == "medium"
        assert TicketPriority.HIGH.value == "high"
        assert TicketPriority.CRITICAL.value == "critical"


class TestCriterion:
    """Test Criterion model."""

    def test_create_criterion(self):
        """Test creating a criterion with required fields."""
        criterion = Criterion(
            type=CriterionType.CODE,
            description="Implement feature X",
        )
        assert criterion.type == CriterionType.CODE
        assert criterion.description == "Implement feature X"
        assert criterion.status == CriterionStatus.NOT_MET  # default

    def test_criterion_with_status(self):
        """Test creating a criterion with explicit status."""
        criterion = Criterion(
            type=CriterionType.TEST,
            description="All tests pass",
            status=CriterionStatus.MET,
        )
        assert criterion.status == CriterionStatus.MET


class TestTicketCreation:
    """Test Ticket model creation."""

    def test_minimal_ticket(self):
        """Test creating a ticket with minimal required fields."""
        ticket = Ticket(
            id="TEST-001",
            name="Test Ticket",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
        )
        assert ticket.id == "TEST-001"
        assert ticket.name == "Test Ticket"
        assert ticket.hierarchy_type == HierarchyType.WORK_ITEM
        assert ticket.source_adapter == "test"
        # Check defaults
        assert ticket.status == TicketStatus.NOT_STARTED
        assert ticket.priority is None  # Default is None
        assert ticket.description is None
        assert ticket.parent_id is None
        assert ticket.criteria == []
        assert ticket.labels == []
        assert ticket.metadata == {}

    def test_full_ticket(self):
        """Test creating a ticket with all fields."""
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            id="PROJ-001",
            name="Project Alpha",
            hierarchy_type=HierarchyType.PROJECT,
            description="A test project",
            status=TicketStatus.IN_PROGRESS,
            priority=TicketPriority.HIGH,
            source_adapter="vibey",
            external_id="ext-123",
            parent_id=None,
            children_ids=["TRACK-001", "TRACK-002"],
            created_at=now,
            started_at=now,
            assignee="user1",
            labels=["important", "q1"],
            children_total=10,
            children_completed=3,
            criteria=[
                Criterion(type=CriterionType.CODE, description="Code complete"),
            ],
            metadata={"custom_field": "value"},
        )
        assert ticket.id == "PROJ-001"
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.priority == TicketPriority.HIGH
        assert len(ticket.children_ids) == 2
        assert len(ticket.criteria) == 1
        assert ticket.metadata["custom_field"] == "value"


class TestTicketProperties:
    """Test Ticket computed properties."""

    def test_is_complete(self):
        """Test is_complete property."""
        ticket = Ticket(
            id="T1",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            status=TicketStatus.COMPLETED,
        )
        assert ticket.is_complete is True

        ticket.status = TicketStatus.IN_PROGRESS
        assert ticket.is_complete is False

    def test_is_blocked(self):
        """Test is_blocked property."""
        ticket = Ticket(
            id="T1",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            status=TicketStatus.BLOCKED,
        )
        assert ticket.is_blocked is True

        ticket.status = TicketStatus.IN_PROGRESS
        ticket.blocked = False
        assert ticket.is_blocked is False

    def test_is_container(self):
        """Test is_container property for different hierarchy types."""
        project = Ticket(id="P1", name="Project", hierarchy_type=HierarchyType.PROJECT, source_adapter="test")
        assert project.is_container is True

        workstream = Ticket(id="W1", name="Track", hierarchy_type=HierarchyType.WORKSTREAM, source_adapter="test")
        assert workstream.is_container is True

        iteration = Ticket(id="I1", name="Sprint", hierarchy_type=HierarchyType.ITERATION, source_adapter="test")
        assert iteration.is_container is True

        work_item = Ticket(id="T1", name="Task", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test")
        assert work_item.is_container is False

    def test_is_leaf(self):
        """Test is_leaf property."""
        work_item = Ticket(id="T1", name="Task", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test")
        assert work_item.is_leaf is True

        project = Ticket(id="P1", name="Project", hierarchy_type=HierarchyType.PROJECT, source_adapter="test")
        assert project.is_leaf is False

    def test_all_criteria_met(self):
        """Test all_criteria_met property."""
        # No criteria
        ticket = Ticket(id="T1", name="Test", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test")
        assert ticket.all_criteria_met is True

        # All criteria met
        ticket = Ticket(
            id="T2",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            criteria=[
                Criterion(type=CriterionType.CODE, description="A", status=CriterionStatus.MET),
                Criterion(type=CriterionType.TEST, description="B", status=CriterionStatus.MET),
            ],
        )
        assert ticket.all_criteria_met is True

        # Some criteria not met
        ticket = Ticket(
            id="T3",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            criteria=[
                Criterion(type=CriterionType.CODE, description="A", status=CriterionStatus.MET),
                Criterion(type=CriterionType.TEST, description="B", status=CriterionStatus.NOT_MET),
            ],
        )
        assert ticket.all_criteria_met is False


class TestTicketMethods:
    """Test Ticket methods."""

    def test_update_progress(self):
        """Test update_progress method."""
        ticket = Ticket(id="T1", name="Test", hierarchy_type=HierarchyType.WORKSTREAM, source_adapter="test")
        ticket.children_total = 10
        ticket.children_completed = 5
        ticket.update_progress()
        assert ticket.completion_percent == 50.0

    def test_mark_started(self):
        """Test mark_started method."""
        ticket = Ticket(id="T1", name="Test", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test")
        ticket.mark_started()
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.started_at is not None

    def test_mark_started_with_explicit_time(self):
        """Test mark_started with explicit time."""
        ticket = Ticket(
            id="T1",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
        )
        explicit_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ticket.mark_started(when=explicit_time)
        assert ticket.started_at == explicit_time

    def test_mark_completed(self):
        """Test mark_completed method."""
        ticket = Ticket(
            id="T1",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            status=TicketStatus.IN_PROGRESS,
        )
        ticket.mark_completed()
        assert ticket.status == TicketStatus.COMPLETED
        assert ticket.completed_at is not None

    def test_mark_completed_does_not_set_started(self):
        """Test mark_completed only sets completed_at, not started_at."""
        ticket = Ticket(id="T1", name="Test", hierarchy_type=HierarchyType.WORK_ITEM, source_adapter="test")
        ticket.mark_completed()
        # mark_completed does not set started_at
        assert ticket.started_at is None
        assert ticket.completed_at is not None

    def test_mark_blocked(self):
        """Test mark_blocked method."""
        ticket = Ticket(
            id="T1",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            status=TicketStatus.IN_PROGRESS,
        )
        ticket.mark_blocked("Waiting for dependency")
        assert ticket.status == TicketStatus.BLOCKED
        assert ticket.blocked_reason == "Waiting for dependency"

    def test_unblock(self):
        """Test unblock method."""
        ticket = Ticket(
            id="T1",
            name="Test",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            status=TicketStatus.BLOCKED,
            blocked_reason="Some reason",
            blocked=True,
        )
        ticket.unblock()
        # Returns to NOT_STARTED because started_at is None
        assert ticket.status == TicketStatus.NOT_STARTED
        assert ticket.blocked_reason is None


class TestTicketSerialization:
    """Test Ticket serialization/deserialization."""

    def test_model_dump(self):
        """Test serializing ticket to dict."""
        ticket = Ticket(
            id="T1",
            name="Test Ticket",
            hierarchy_type=HierarchyType.WORK_ITEM,
            source_adapter="test",
            status=TicketStatus.IN_PROGRESS,
        )
        data = ticket.model_dump()
        assert data["id"] == "T1"
        assert data["name"] == "Test Ticket"
        assert data["source_adapter"] == "test"

    def test_model_validate(self):
        """Test deserializing ticket from dict."""
        data = {
            "id": "T2",
            "name": "Another Ticket",
            "hierarchy_type": "project",
            "source_adapter": "jira",
            "status": "completed",
        }
        ticket = Ticket.model_validate(data)
        assert ticket.id == "T2"
        assert ticket.name == "Another Ticket"
        assert ticket.hierarchy_type == HierarchyType.PROJECT
        assert ticket.status == TicketStatus.COMPLETED

    def test_json_round_trip(self):
        """Test JSON serialization round trip."""
        original = Ticket(
            id="T3",
            name="Round Trip Test",
            hierarchy_type=HierarchyType.ITERATION,
            source_adapter="test",
            status=TicketStatus.BLOCKED,
            priority=TicketPriority.HIGH,
            labels=["test", "important"],
        )
        json_str = original.model_dump_json()
        restored = Ticket.model_validate_json(json_str)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.hierarchy_type == original.hierarchy_type
        assert restored.status == original.status
        assert restored.priority == original.priority
        assert restored.labels == original.labels
