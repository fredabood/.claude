"""
Tests for deferred flag functionality.

Tests:
- Deferred field on Ticket
- _is_child_deferred helper
- required_children and deferred_children properties
- can_transition_to excludes deferred children
- progress_for_transition excludes deferred children
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List

from vibey.roadmap.models.ticket import (
    HierarchicalTicket,
    Ticket,
    Criterion,
    CompletableTarget,
    FileExistsTarget,
    TicketStatus,
)


# =============================================================================
# FIXTURES
# =============================================================================


class MockLoader:
    """Mock loader for testing hierarchy navigation."""

    def __init__(self, tickets: Dict[str, "HierarchicalTicket"] = None):
        self.tickets = tickets or {}

    def load(self, ticket_id: str) -> "HierarchicalTicket":
        """Load a ticket by ID."""
        if ticket_id in self.tickets:
            return self.tickets[ticket_id]
        raise ValueError(f"Ticket not found: {ticket_id}")


@pytest.fixture
def base_ticket_kwargs():
    """Base kwargs for creating Ticket instances."""
    return {
        "name": "Test Ticket",
        "description": "A test ticket",
        "created_at": datetime.now(timezone.utc),
    }


# =============================================================================
# DEFERRED FIELD TESTS
# =============================================================================


class TestDeferredField:
    """Tests for deferred field on Ticket."""

    def test_default_not_deferred(self, base_ticket_kwargs):
        """Tickets should not be deferred by default."""
        ticket = Ticket(**base_ticket_kwargs, id="task-001")
        assert ticket.deferred is False

    def test_can_set_deferred_true(self, base_ticket_kwargs):
        """Can set deferred to True."""
        ticket = Ticket(**base_ticket_kwargs, id="task-001", deferred=True)
        assert ticket.deferred is True

    def test_deferred_serializes(self, base_ticket_kwargs):
        """Deferred field should serialize correctly."""
        ticket = Ticket(**base_ticket_kwargs, id="task-001", deferred=True)
        data = ticket.model_dump()
        assert data["deferred"] is True

    def test_deferred_deserializes(self, base_ticket_kwargs):
        """Deferred field should deserialize correctly."""
        data = {
            "id": "task-001",
            "name": "Test",
            "deferred": True,
        }
        ticket = Ticket.model_validate(data)
        assert ticket.deferred is True


class TestHierarchicalDeferredField:
    """Tests for deferred field on HierarchicalTicket."""

    def test_hierarchical_inherits_deferred(self, base_ticket_kwargs):
        """HierarchicalTicket should inherit deferred field."""
        ticket = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            deferred=True
        )
        assert ticket.deferred is True


# =============================================================================
# IS CHILD DEFERRED TESTS
# =============================================================================


class TestIsChildDeferred:
    """Tests for _is_child_deferred helper."""

    def test_no_loader_returns_false(self, base_ticket_kwargs):
        """Without loader, _is_child_deferred should return False."""
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
        )
        HierarchicalTicket.clear_loaders()
        assert parent._is_child_deferred("task-001") is False

    def test_child_not_deferred(self, base_ticket_kwargs):
        """Non-deferred child should return False."""
        child = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            deferred=False,
        )
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
        )

        loader = MockLoader({"task-001": child})
        HierarchicalTicket.set_loader(loader)

        try:
            assert parent._is_child_deferred("task-001") is False
        finally:
            HierarchicalTicket.clear_loaders()

    def test_child_is_deferred(self, base_ticket_kwargs):
        """Deferred child should return True."""
        child = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            deferred=True,
        )
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
        )

        loader = MockLoader({"task-001": child})
        HierarchicalTicket.set_loader(loader)

        try:
            assert parent._is_child_deferred("task-001") is True
        finally:
            HierarchicalTicket.clear_loaders()

    def test_nonexistent_child_returns_false(self, base_ticket_kwargs):
        """Non-existent child should return False."""
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
        )

        loader = MockLoader({})  # Empty loader
        HierarchicalTicket.set_loader(loader)

        try:
            assert parent._is_child_deferred("nonexistent") is False
        finally:
            HierarchicalTicket.clear_loaders()


# =============================================================================
# REQUIRED AND DEFERRED CHILDREN TESTS
# =============================================================================


class TestRequiredAndDeferredChildren:
    """Tests for required_children and deferred_children properties."""

    def test_required_children_excludes_deferred(self, base_ticket_kwargs):
        """required_children should exclude deferred children."""
        # Create children
        task1 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            deferred=False,
        )
        task2 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-002",
            parent_ref="sprint-001",
            deferred=True,  # Deferred
        )
        task3 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-003",
            parent_ref="sprint-001",
            deferred=False,
        )

        # Create parent with child criteria
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Task 1",
                    target=CompletableTarget(completable_id="task-001"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-2",
                    description="Task 2 (deferred)",
                    target=CompletableTarget(completable_id="task-002"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-3",
                    description="Task 3",
                    target=CompletableTarget(completable_id="task-003"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        loader = MockLoader({
            "task-001": task1,
            "task-002": task2,
            "task-003": task3,
        })
        HierarchicalTicket.set_loader(loader)

        try:
            required = parent.required_children
            deferred = parent.deferred_children

            assert "task-001" in required
            assert "task-003" in required
            assert "task-002" not in required

            assert "task-002" in deferred
            assert "task-001" not in deferred
            assert "task-003" not in deferred
        finally:
            HierarchicalTicket.clear_loaders()


# =============================================================================
# CAN TRANSITION TO TESTS
# =============================================================================


class TestCanTransitionToWithDeferred:
    """Tests for can_transition_to excluding deferred children."""

    def test_can_complete_with_incomplete_deferred_child(self, base_ticket_kwargs):
        """Parent can complete when deferred child is incomplete."""
        now = datetime.now(timezone.utc)

        # Required child - completed
        task1_kwargs = {**base_ticket_kwargs}
        task1_kwargs["created_at"] = now
        task1 = HierarchicalTicket(
            **task1_kwargs,
            id="task-001",
            deferred=False,
            status=TicketStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        )
        # Deferred child - NOT completed
        task2 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-002",
            deferred=True,
            status=TicketStatus.NOT_STARTED,  # Not complete!
        )

        # Create parent with child criteria (no parent_ref to avoid loading parent)
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        current_status=TicketStatus.COMPLETED,  # Met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-2",
                    description="Task 2 (deferred)",
                    target=CompletableTarget(
                        completable_id="task-002",
                        current_status=TicketStatus.NOT_STARTED,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        loader = MockLoader({
            "task-001": task1,
            "task-002": task2,
        })
        HierarchicalTicket.set_loader(loader)

        try:
            can, reasons = parent.can_transition_to(TicketStatus.COMPLETED)
            # Should be able to complete because task-002 is deferred
            assert can is True
            assert len(reasons) == 0
        finally:
            HierarchicalTicket.clear_loaders()

    def test_cannot_complete_with_incomplete_required_child(self, base_ticket_kwargs):
        """Parent cannot complete when required child is incomplete."""
        # Required child - NOT completed
        task1 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            deferred=False,
            status=TicketStatus.NOT_STARTED,
        )

        # Create parent with child criteria
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Task 1 must complete",
                    target=CompletableTarget(
                        completable_id="task-001",
                        current_status=TicketStatus.NOT_STARTED,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        loader = MockLoader({"task-001": task1})
        HierarchicalTicket.set_loader(loader)

        try:
            can, reasons = parent.can_transition_to(TicketStatus.COMPLETED)
            # Should NOT be able to complete because task-001 is required
            assert can is False
            assert "Task 1 must complete" in reasons
        finally:
            HierarchicalTicket.clear_loaders()

    def test_deferred_still_blocks_in_progress(self, base_ticket_kwargs):
        """Deferred children should still block IN_PROGRESS transition."""
        # Deferred dependency
        dep_task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="dep-001",
            deferred=True,  # Deferred, but...
            status=TicketStatus.NOT_STARTED,
        )

        # Create task with dependency (no parent_ref to avoid loading issues)
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            status=TicketStatus.NOT_STARTED,
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Dependency must complete first",
                    target=CompletableTarget(
                        completable_id="dep-001",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,  # Not COMPLETED
                ),
            ]
        )

        loader = MockLoader({"dep-001": dep_task})
        HierarchicalTicket.set_loader(loader)

        try:
            can, reasons = task.can_transition_to(TicketStatus.IN_PROGRESS)
            # Deferred should NOT be excluded for IN_PROGRESS
            assert can is False
            assert "Dependency must complete first" in reasons
        finally:
            HierarchicalTicket.clear_loaders()


# =============================================================================
# PROGRESS TESTS
# =============================================================================


class TestProgressWithDeferred:
    """Tests for progress_for_transition excluding deferred children."""

    def test_progress_excludes_deferred_for_completed(self, base_ticket_kwargs):
        """Progress should exclude deferred children for COMPLETED."""
        # Required children
        task1 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            deferred=False,
        )
        task2 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-002",
            parent_ref="sprint-001",
            deferred=False,
        )
        # Deferred child
        task3 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-003",
            parent_ref="sprint-001",
            deferred=True,
        )

        # Create parent with 3 children
        parent = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        current_status=TicketStatus.COMPLETED,  # Met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-2",
                    description="Task 2",
                    target=CompletableTarget(
                        completable_id="task-002",
                        current_status=TicketStatus.NOT_STARTED,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-3",
                    description="Task 3 (deferred)",
                    target=CompletableTarget(
                        completable_id="task-003",
                        current_status=TicketStatus.NOT_STARTED,  # Not met, but deferred
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        loader = MockLoader({
            "task-001": task1,
            "task-002": task2,
            "task-003": task3,
        })
        HierarchicalTicket.set_loader(loader)

        try:
            progress = parent.progress_for_transition(TicketStatus.COMPLETED)
            # Should only count 2 children (task-003 is deferred)
            assert progress.total == 2
            # 1 of 2 completed
            assert progress.completed == 1
            assert progress.completion_percent == 50.0
        finally:
            HierarchicalTicket.clear_loaders()

    def test_progress_includes_deferred_for_in_progress(self, base_ticket_kwargs):
        """Progress should include deferred dependencies for IN_PROGRESS."""
        # Deferred dependency
        dep = HierarchicalTicket(
            **base_ticket_kwargs,
            id="dep-001",
            deferred=True,
        )

        # Task with deferred dependency (no parent_ref to avoid loading issues)
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Dependency",
                    target=CompletableTarget(
                        completable_id="dep-001",
                        current_status=TicketStatus.NOT_STARTED,
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
            ]
        )

        loader = MockLoader({"dep-001": dep})
        HierarchicalTicket.set_loader(loader)

        try:
            progress = task.progress_for_transition(TicketStatus.IN_PROGRESS)
            # Deferred should NOT be excluded for IN_PROGRESS
            assert progress.total == 1
            assert progress.completed == 0
        finally:
            HierarchicalTicket.clear_loaders()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestDeferredIntegration:
    """Integration tests for deferred functionality."""

    def test_track_with_deferred_sprint(self, base_ticket_kwargs):
        """Track can complete with deferred sprint incomplete."""
        now = datetime.now(timezone.utc)

        # Required sprints - completed
        sprint1_kwargs = {**base_ticket_kwargs}
        sprint1_kwargs["created_at"] = now
        sprint1 = HierarchicalTicket(
            **sprint1_kwargs,
            id="sprint-001",
            deferred=False,
            status=TicketStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        )
        sprint2_kwargs = {**base_ticket_kwargs}
        sprint2_kwargs["created_at"] = now
        sprint2 = HierarchicalTicket(
            **sprint2_kwargs,
            id="sprint-002",
            deferred=False,
            status=TicketStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        )
        # Deferred sprint - not completed (optimization work)
        sprint3 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-003",
            deferred=True,
            status=TicketStatus.NOT_STARTED,
        )

        # Track with 3 sprints (no parent_ref to avoid loading issues)
        track = HierarchicalTicket(
            **base_ticket_kwargs,
            id="track-001",
            criteria=[
                Criterion(
                    id="sprint-1",
                    description="Sprint 1",
                    target=CompletableTarget(
                        completable_id="sprint-001",
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="sprint-2",
                    description="Sprint 2",
                    target=CompletableTarget(
                        completable_id="sprint-002",
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="sprint-3",
                    description="Sprint 3 (deferred)",
                    target=CompletableTarget(
                        completable_id="sprint-003",
                        current_status=TicketStatus.NOT_STARTED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        loader = MockLoader({
            "sprint-001": sprint1,
            "sprint-002": sprint2,
            "sprint-003": sprint3,
        })
        HierarchicalTicket.set_loader(loader)

        try:
            # Track should be able to complete
            can, reasons = track.can_transition_to(TicketStatus.COMPLETED)
            assert can is True
            assert len(reasons) == 0

            # Progress should show 2/2 (100%)
            progress = track.progress_for_transition(TicketStatus.COMPLETED)
            assert progress.total == 2  # Only 2 required sprints
            assert progress.completed == 2
            assert progress.completion_percent == 100.0

            # Children lists should be correct
            assert track.required_children == ["sprint-001", "sprint-002"]
            assert track.deferred_children == ["sprint-003"]
        finally:
            HierarchicalTicket.clear_loaders()
