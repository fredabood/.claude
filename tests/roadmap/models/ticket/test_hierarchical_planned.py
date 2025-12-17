"""
Tests for hierarchical planned status aggregation.

Tests the is_planned, planned_progress, and unplanned_children properties
added to HierarchicalTicket.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.targets import CompletableTarget


@pytest.fixture
def roadmap_env(tmp_path):
    """Create minimal roadmap environment."""
    roadmap_root = tmp_path / ".vibey" / "roadmap"
    (roadmap_root / "tasks").mkdir(parents=True)
    (roadmap_root / "sprints").mkdir(parents=True)
    (roadmap_root / "tracks").mkdir(parents=True)

    HierarchicalTicket.set_roadmap_root(roadmap_root)

    yield {'root': tmp_path, 'roadmap': roadmap_root}

    HierarchicalTicket.clear_roadmap_root()
    HierarchicalTicket.clear_loaders()


class TestIsPlanned:
    """Tests for is_planned property."""

    def test_leaf_planned_when_yaml_exists(self, roadmap_env):
        """Leaf ticket is planned when YAML exists."""
        # Create YAML file
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TESTLEAF.yaml"
        yaml_path.write_text("task:\n  id: 01TESTLEAF\n  name: Test Task")

        ticket = HierarchicalTicket(
            id="01TESTLEAF",
            name="Test Task",
            criteria=[],  # No children = leaf
        )

        assert ticket.is_parent is False  # No children = leaf
        assert ticket.is_planned is True

    def test_leaf_not_planned_when_yaml_missing(self, roadmap_env):
        """Leaf ticket is not planned when YAML doesn't exist."""
        ticket = HierarchicalTicket(
            id="01MISSING",
            name="Missing Task",
            criteria=[],
        )

        assert ticket.is_parent is False  # No children = leaf
        assert ticket.is_planned is False

    def test_planned_without_roadmap_root_returns_true(self, tmp_path):
        """Without roadmap root configured, assume planned."""
        # Clear roadmap root
        HierarchicalTicket.clear_roadmap_root()

        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test Task",
            criteria=[],
        )

        assert ticket.is_planned is True

    def test_parent_planned_when_all_children_planned(self, roadmap_env):
        """Parent is planned when all children are planned."""
        # Create YAML for children
        for i in range(3):
            yaml_path = roadmap_env['roadmap'] / "tasks" / f"01CHILD{i}.yaml"
            yaml_path.write_text(f"task:\n  id: 01CHILD{i}\n  name: Child {i}")

        # Create mock loader that returns leaf tickets
        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],  # Leaf
            )

        mock_loader = MagicMock()
        mock_loader.load = mock_load
        HierarchicalTicket.set_loader(mock_loader)

        # Create parent with children as criteria
        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent Sprint",
            criteria=[
                Criterion(
                    id=f"child-{i}",
                    description=f"Child {i}",
                    target=CompletableTarget(completable_id=f"01CHILD{i}"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                )
                for i in range(3)
            ],
        )

        assert parent.is_parent is True
        assert parent.is_planned is True

    def test_parent_not_planned_when_child_not_planned(self, roadmap_env):
        """Parent is not planned when any child is not planned."""
        # Only create YAML for some children
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01CHILD0.yaml"
        yaml_path.write_text("task:\n  id: 01CHILD0\n  name: Child 0")
        # 01CHILD1 has no YAML

        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],  # Leaf
            )

        mock_loader = MagicMock()
        mock_loader.load = mock_load
        HierarchicalTicket.set_loader(mock_loader)

        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent Sprint",
            criteria=[
                Criterion(
                    id="child-0",
                    description="Child 0",
                    target=CompletableTarget(completable_id="01CHILD0"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-1",
                    description="Child 1",
                    target=CompletableTarget(completable_id="01CHILD1"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        assert parent.is_planned is False


class TestPlannedProgress:
    """Tests for planned_progress property."""

    def test_leaf_progress_counts_required_criteria(self, roadmap_env):
        """Leaf progress counts required criteria."""
        # Create YAML file so YAML criterion is met
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  name: Test")

        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test",
            criteria=[],
        )

        progress = ticket.planned_progress
        # YAML exists (1 met), context doesn't exist but is optional (not counted)
        assert progress.total == 1
        assert progress.completed == 1

    def test_leaf_progress_without_yaml(self, roadmap_env):
        """Leaf progress when YAML doesn't exist."""
        ticket = HierarchicalTicket(
            id="01MISSING",
            name="Missing",
            criteria=[],
        )

        progress = ticket.planned_progress
        # YAML is required but doesn't exist
        assert progress.total == 1
        assert progress.completed == 0

    def test_parent_progress_counts_children(self, roadmap_env):
        """Parent progress counts planned children."""
        # Create YAML for only one child
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01CHILD0.yaml"
        yaml_path.write_text("task:\n  id: 01CHILD0\n  name: Child 0")

        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],
            )

        mock_loader = MagicMock()
        mock_loader.load = mock_load
        HierarchicalTicket.set_loader(mock_loader)

        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent",
            criteria=[
                Criterion(
                    id="child-0",
                    description="Child 0",
                    target=CompletableTarget(completable_id="01CHILD0"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-1",
                    description="Child 1",
                    target=CompletableTarget(completable_id="01CHILD1"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        progress = parent.planned_progress
        assert progress.total == 2  # 2 children
        assert progress.completed == 1  # Only 01CHILD0 has YAML

    def test_progress_without_roadmap_root(self, tmp_path):
        """Progress without roadmap root returns empty."""
        HierarchicalTicket.clear_roadmap_root()

        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test",
            criteria=[],
        )

        progress = ticket.planned_progress
        assert progress.total == 0
        assert progress.completed == 0


class TestUnplannedChildren:
    """Tests for unplanned_children property."""

    def test_leaf_returns_empty(self, roadmap_env):
        """Leaf ticket returns empty list."""
        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test",
            criteria=[],
        )

        assert ticket.unplanned_children == []

    def test_parent_returns_unplanned_ids(self, roadmap_env):
        """Parent returns IDs of unplanned children."""
        # Create YAML for only one child
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01CHILD0.yaml"
        yaml_path.write_text("task:\n  id: 01CHILD0\n  name: Child 0")

        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],
            )

        mock_loader = MagicMock()
        mock_loader.load = mock_load
        HierarchicalTicket.set_loader(mock_loader)

        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent",
            criteria=[
                Criterion(
                    id="child-0",
                    description="Child 0",
                    target=CompletableTarget(completable_id="01CHILD0"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="child-1",
                    description="Child 1",
                    target=CompletableTarget(completable_id="01CHILD1"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        unplanned = parent.unplanned_children
        assert "01CHILD1" in unplanned
        assert "01CHILD0" not in unplanned

    def test_parent_empty_when_all_planned(self, roadmap_env):
        """Parent returns empty when all children are planned."""
        # Create YAML for all children
        for i in range(2):
            yaml_path = roadmap_env['roadmap'] / "tasks" / f"01CHILD{i}.yaml"
            yaml_path.write_text(f"task:\n  id: 01CHILD{i}\n  name: Child {i}")

        def mock_load(ticket_id):
            return HierarchicalTicket(
                id=ticket_id,
                name=f"Child {ticket_id}",
                criteria=[],
            )

        mock_loader = MagicMock()
        mock_loader.load = mock_load
        HierarchicalTicket.set_loader(mock_loader)

        parent = HierarchicalTicket(
            id="01PARENT",
            name="Parent",
            criteria=[
                Criterion(
                    id=f"child-{i}",
                    description=f"Child {i}",
                    target=CompletableTarget(completable_id=f"01CHILD{i}"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                )
                for i in range(2)
            ],
        )

        assert parent.unplanned_children == []


class TestPlannedCache:
    """Tests for planned status caching."""

    def test_cache_cleared_on_roadmap_root_change(self, roadmap_env):
        """Cache is cleared when roadmap root changes."""
        # Create YAML
        yaml_path = roadmap_env['roadmap'] / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task:\n  id: 01TEST\n  name: Test")

        ticket = HierarchicalTicket(
            id="01TEST",
            name="Test",
            criteria=[],
        )

        # First check - should be planned
        assert ticket.is_planned is True

        # Change roadmap root
        new_root = roadmap_env['root'] / "other" / ".vibey" / "roadmap"
        (new_root / "tasks").mkdir(parents=True)
        HierarchicalTicket.set_roadmap_root(new_root)

        # YAML doesn't exist in new root - should not be planned
        assert ticket.is_planned is False
