"""
Tests for computed_tokens and DeliverableType functionality.

Tests:
- DeliverableType on FileExistsTarget
- computed_tokens aggregation on HierarchicalTicket
- start_with_context_check platform warning
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List

from vibey.roadmap.models.ticket import (
    HierarchicalTicket,
    FileExistsTarget,
    DeliverableType,
    TicketStatus,
    Criterion,
    CompletableTarget,
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


class MockSiblingLoader:
    """Mock sibling loader for testing."""

    def __init__(self, tickets: Dict[str, "HierarchicalTicket"] = None):
        self.tickets = tickets or {}

    def load_siblings(self, parent_id: str, exclude_id: str) -> List["HierarchicalTicket"]:
        """Load siblings (other children of same parent)."""
        return [
            t for t in self.tickets.values()
            if t.parent_ref == parent_id and t.id != exclude_id
        ]


@pytest.fixture
def base_ticket_kwargs():
    """Base kwargs for creating HierarchicalTicket instances."""
    return {
        "name": "Test Ticket",
        "description": "A test ticket",
        "created_at": datetime.now(timezone.utc),
    }


# =============================================================================
# DELIVERABLE TYPE TESTS
# =============================================================================


class TestDeliverableType:
    """Tests for DeliverableType on FileExistsTarget."""

    def test_default_deliverable_type_is_other(self):
        """Default deliverable_type should be OTHER."""
        target = FileExistsTarget(paths=["README.md"])
        assert target.deliverable_type == DeliverableType.OTHER

    def test_can_set_code_deliverable_type(self):
        """Can set deliverable_type to CODE."""
        target = FileExistsTarget(
            paths=["src/main.py"],
            deliverable_type=DeliverableType.CODE
        )
        assert target.deliverable_type == DeliverableType.CODE

    def test_can_set_test_deliverable_type(self):
        """Can set deliverable_type to TEST."""
        target = FileExistsTarget(
            paths=["tests/test_main.py"],
            deliverable_type=DeliverableType.TEST
        )
        assert target.deliverable_type == DeliverableType.TEST

    def test_can_set_documentation_deliverable_type(self):
        """Can set deliverable_type to DOCUMENTATION."""
        target = FileExistsTarget(
            paths=["docs/README.md"],
            deliverable_type=DeliverableType.DOCUMENTATION
        )
        assert target.deliverable_type == DeliverableType.DOCUMENTATION

    def test_can_set_config_deliverable_type(self):
        """Can set deliverable_type to CONFIG."""
        target = FileExistsTarget(
            paths=["config.yaml"],
            deliverable_type=DeliverableType.CONFIG
        )
        assert target.deliverable_type == DeliverableType.CONFIG

    def test_can_set_design_deliverable_type(self):
        """Can set deliverable_type to DESIGN."""
        target = FileExistsTarget(
            paths=["design/mockup.png"],
            deliverable_type=DeliverableType.DESIGN
        )
        assert target.deliverable_type == DeliverableType.DESIGN

    def test_deliverable_type_serializes(self):
        """DeliverableType should serialize correctly."""
        target = FileExistsTarget(
            paths=["src/api.py"],
            deliverable_type=DeliverableType.CODE
        )
        data = target.model_dump()
        assert data["deliverable_type"] == "code"

    def test_deliverable_type_deserializes(self):
        """DeliverableType should deserialize correctly."""
        data = {
            "paths": ["test.py"],
            "deliverable_type": "test"
        }
        target = FileExistsTarget.model_validate(data)
        assert target.deliverable_type == DeliverableType.TEST


# =============================================================================
# COMPUTED TOKENS TESTS
# =============================================================================


class TestComputedTokens:
    """Tests for computed_tokens on HierarchicalTicket."""

    def test_ultimate_child_returns_estimated_tokens(self, base_ticket_kwargs):
        """Ultimate child should return its estimated_tokens."""
        # Create a task-like ticket (child, no children)
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",  # Has parent, so is_child=True
            # No children, so is_parent=False
            # Therefore is_ultimate_child=True
        )
        # Add estimated_tokens as attribute
        task.__dict__["estimated_tokens"] = 1500

        assert task.is_ultimate_child
        assert task.computed_tokens == 1500

    def test_ultimate_child_without_estimated_tokens_returns_zero(self, base_ticket_kwargs):
        """Ultimate child without estimated_tokens should return 0."""
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
        )

        assert task.is_ultimate_child
        assert task.computed_tokens == 0

    def test_parent_aggregates_from_children(self, base_ticket_kwargs):
        """Parent should aggregate computed_tokens from children."""
        # Create tasks (children)
        task1 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
        )
        task1.__dict__["estimated_tokens"] = 1000

        task2 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-002",
            parent_ref="sprint-001",
        )
        task2.__dict__["estimated_tokens"] = 2000

        task3 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-003",
            parent_ref="sprint-001",
        )
        task3.__dict__["estimated_tokens"] = 1500

        # Create sprint (parent) with children
        sprint = HierarchicalTicket(
            **base_ticket_kwargs,
            id="sprint-001",
            parent_ref="track-001",
            criteria=[
                Criterion(
                    id="child-task-001",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        current_status=TicketStatus.NOT_STARTED
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-task-002",
                    description="Task 2",
                    target=CompletableTarget(
                        completable_id="task-002",
                        current_status=TicketStatus.NOT_STARTED
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-task-003",
                    description="Task 3",
                    target=CompletableTarget(
                        completable_id="task-003",
                        current_status=TicketStatus.NOT_STARTED
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        # Set up loader
        loader = MockLoader({
            "task-001": task1,
            "task-002": task2,
            "task-003": task3,
        })
        HierarchicalTicket.set_loader(loader)

        try:
            # Sprint should aggregate: 1000 + 2000 + 1500 = 4500
            assert sprint.is_parent
            assert not sprint.is_ultimate_child
            assert sprint.computed_tokens == 4500
        finally:
            HierarchicalTicket.clear_loaders()

    def test_computed_tokens_in_serialization(self, base_ticket_kwargs):
        """computed_tokens should appear in serialized output."""
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
        )
        task.__dict__["estimated_tokens"] = 2500

        data = task.model_dump()
        assert "computed_tokens" in data
        assert data["computed_tokens"] == 2500


# =============================================================================
# START WITH CONTEXT CHECK TESTS
# =============================================================================


class TestStartWithContextCheck:
    """Tests for start_with_context_check method."""

    def test_start_without_context_window(self, base_ticket_kwargs):
        """Start without context window should work normally."""
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            status=TicketStatus.NOT_STARTED,
        )
        task.__dict__["estimated_tokens"] = 1000

        started, warnings = task.start_with_context_check()

        assert started.status == TicketStatus.IN_PROGRESS
        assert warnings == []

    def test_start_with_sufficient_context_window(self, base_ticket_kwargs):
        """Start with sufficient context window should have no warnings."""
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            status=TicketStatus.NOT_STARTED,
        )
        task.__dict__["estimated_tokens"] = 1000

        started, warnings = task.start_with_context_check(
            platform_context_window=100000  # 100k tokens
        )

        assert started.status == TicketStatus.IN_PROGRESS
        assert warnings == []

    def test_start_with_insufficient_context_window(self, base_ticket_kwargs):
        """Start with insufficient context window should add warning."""
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            status=TicketStatus.NOT_STARTED,
        )
        task.__dict__["estimated_tokens"] = 5000

        started, warnings = task.start_with_context_check(
            platform_context_window=2000  # Only 2k tokens
        )

        # Should still start (warning, not blocker)
        assert started.status == TicketStatus.IN_PROGRESS
        assert len(warnings) == 1
        assert "5000 tokens" in warnings[0]
        assert "2000" in warnings[0]
        assert "Consider splitting" in warnings[0]

    def test_start_with_blocked_ticket_raises(self, base_ticket_kwargs):
        """Start with blocked ticket should raise even with context check."""
        # Create a task blocked by a dependency
        # Note: Use FileExistsTarget for blocking criterion to avoid needing loader
        # (CompletableTarget would make it a parent, requiring loader for computed_tokens)
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",  # is_child=True, is_parent=False (no CompletableTarget)
            status=TicketStatus.NOT_STARTED,
            criteria=[
                Criterion(
                    id="dep-001",
                    description="Blocked by other task",
                    target=CompletableTarget(
                        completable_id="other-task",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                )
            ]
        )
        task.__dict__["estimated_tokens"] = 1000

        # The issue is that CompletableTarget in criteria makes it a parent,
        # which requires loader for computed_tokens. Since the test is about
        # blocking behavior, use a simpler approach with manual criterion
        # that still blocks IN_PROGRESS
        task2 = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-002",
            parent_ref="sprint-001",
            status=TicketStatus.NOT_STARTED,
            criteria=[
                Criterion(
                    id="manual-check",
                    description="Must be approved before starting",
                    target=FileExistsTarget(
                        paths=["/nonexistent/required/file.txt"],
                        existing_paths=[],  # Not satisfied
                        missing_paths=["/nonexistent/required/file.txt"],
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                )
            ]
        )
        task2.__dict__["estimated_tokens"] = 1000

        with pytest.raises(ValueError, match="Cannot start"):
            task2.start_with_context_check(platform_context_window=100000)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestDeliverableTypeIntegration:
    """Integration tests for deliverable type queries."""

    def test_filter_deliverables_by_type(self, base_ticket_kwargs):
        """Can filter deliverables by type."""
        task = HierarchicalTicket(
            **base_ticket_kwargs,
            id="task-001",
            parent_ref="sprint-001",
            criteria=[
                Criterion(
                    id="code-1",
                    description="Main module",
                    target=FileExistsTarget(
                        paths=["src/main.py"],
                        deliverable_type=DeliverableType.CODE,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="test-1",
                    description="Main tests",
                    target=FileExistsTarget(
                        paths=["tests/test_main.py"],
                        deliverable_type=DeliverableType.TEST,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="docs-1",
                    description="Documentation",
                    target=FileExistsTarget(
                        paths=["docs/README.md"],
                        deliverable_type=DeliverableType.DOCUMENTATION,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ]
        )

        # Get all deliverables
        all_deliverables = task.deliverables
        assert len(all_deliverables) == 3

        # Filter by type
        code_deliverables = [
            c for c in all_deliverables
            if isinstance(c.target, FileExistsTarget)
            and c.target.deliverable_type == DeliverableType.CODE
        ]
        test_deliverables = [
            c for c in all_deliverables
            if isinstance(c.target, FileExistsTarget)
            and c.target.deliverable_type == DeliverableType.TEST
        ]
        doc_deliverables = [
            c for c in all_deliverables
            if isinstance(c.target, FileExistsTarget)
            and c.target.deliverable_type == DeliverableType.DOCUMENTATION
        ]

        assert len(code_deliverables) == 1
        assert len(test_deliverables) == 1
        assert len(doc_deliverables) == 1
