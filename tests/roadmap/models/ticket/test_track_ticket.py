"""
Tests for TrackTicket domain model.

Tests cover:
- TrackTicket creation and validation
- Intermediate hierarchy constraints
- Parent requirement (must have parent_ref)
- roadmap_id validation
- Sprint child accessors
- Aggregate progress (tasks_total, tasks_completed)
- Strategic value field
- Inherited behavior from HierarchicalTicket
"""

from datetime import datetime, timezone, timedelta
from typing import List

import pytest

from vibey.roadmap.models.ticket import (
    # Domain model
    TrackTicket,
    # Dependencies
    Criterion,
    CompletableTarget,
    FileExistsTarget,
    HierarchicalTicket,
    TicketLoader,
    TicketStatus,
    TicketType,
    Priority,
)


# =============================================================================
# MOCK LOADER FOR TESTING
# =============================================================================


class MockSprintTicket:
    """Mock sprint for testing aggregate progress."""

    def __init__(self, tasks_total: int = 0, tasks_completed: int = 0):
        self.tasks_total = tasks_total
        self.tasks_completed = tasks_completed
        self.all_criteria: List[Criterion] = []
        self.parent_ref = None  # No parent (root mock)
        self.requirements_local = []

    @property
    def parent(self):
        """No parent for mock root ticket."""
        return None


class MockTicketLoader:
    """Mock loader for testing hierarchy traversal."""

    def __init__(self):
        self.tickets = {}

    def add(self, ticket_id: str, ticket: HierarchicalTicket) -> None:
        self.tickets[ticket_id] = ticket

    def add_mock_sprint(
        self, sprint_id: str, tasks_total: int = 0, tasks_completed: int = 0
    ) -> None:
        self.tickets[sprint_id] = MockSprintTicket(tasks_total, tasks_completed)

    def load(self, ticket_id: str) -> HierarchicalTicket:
        if ticket_id not in self.tickets:
            raise KeyError(f"Ticket not found: {ticket_id}")
        return self.tickets[ticket_id]


# =============================================================================
# TRACK TICKET TESTS - CREATION AND VALIDATION
# =============================================================================


class TestTrackTicketCreation:
    """Tests for TrackTicket creation and validation."""

    def test_create_minimal(self):
        """Test creating a minimal TrackTicket."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.id == "track-core"
        assert track.name == "Core Track"
        assert track.ticket_type == TicketType.TRACK
        assert track.roadmap_id == "roadmap-1"
        assert track.parent_ref == "roadmap-1"

    def test_create_with_strategic_value(self):
        """Test creating a TrackTicket with strategic value."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            strategic_value=[
                "Enables multi-platform support",
                "Improves code maintainability",
            ],
        )
        assert len(track.strategic_value) == 2
        assert "Enables multi-platform support" in track.strategic_value

    def test_parent_ref_required(self):
        """Test that parent_ref is required."""
        with pytest.raises(ValueError, match="must have a parent_ref"):
            TrackTicket(
                id="track-core",
                name="Core Track",
                roadmap_id="roadmap-1",
                # Missing parent_ref
            )

    def test_parent_ref_must_match_roadmap_id(self):
        """Test that parent_ref must match roadmap_id."""
        with pytest.raises(ValueError, match="must match roadmap_id"):
            TrackTicket(
                id="track-core",
                name="Core Track",
                roadmap_id="roadmap-1",
                parent_ref="different-roadmap",
            )

    def test_ticket_type_is_track(self):
        """Test that ticket_type is always TRACK."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.ticket_type == TicketType.TRACK


# =============================================================================
# TRACK TICKET TESTS - INTERMEDIATE HIERARCHY SEMANTICS
# =============================================================================


class TestTrackTicketHierarchy:
    """Tests for TrackTicket intermediate hierarchy semantics."""

    def test_is_not_ultimate_parent(self):
        """Test that Track is never the ultimate parent."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.is_ultimate_parent is False

    def test_is_child(self):
        """Test that Track is always a child."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.is_child is True

    def test_is_not_ultimate_child(self):
        """Test that Track is never an ultimate child."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.is_ultimate_child is False

    def test_is_intermediate(self):
        """Test that Track is always intermediate."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.is_intermediate is True


# =============================================================================
# TRACK TICKET TESTS - SPRINT CHILDREN
# =============================================================================


class TestTrackTicketSprintChildren:
    """Tests for TrackTicket sprint child accessors."""

    def test_sprint_criteria_empty(self):
        """Test sprint_criteria with no criteria."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )
        assert track.sprint_criteria == []
        assert track.sprints_total == 0
        assert track.sprints_completed == 0

    def test_sprint_criteria_with_sprints(self):
        """Test sprint_criteria with CompletableTarget criteria."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint 1 Complete",
                    description="Sprint 1 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="Sprint 2 Complete",
                    description="Sprint 2 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-2",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert len(track.sprint_criteria) == 2
        assert track.sprints_total == 2

    def test_get_sprint_ids(self):
        """Test getting sprint IDs from criteria."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint 1",
                    description="Sprint 1 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        sprint_ids = track.get_sprint_ids()
        assert sprint_ids == ["sprint-1"]

    def test_sprints_completed_count(self):
        """Test counting completed sprints."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint 1",
                    description="Sprint 1 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Met!
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="Sprint 2",
                    description="Sprint 2 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-2",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.IN_PROGRESS,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert track.sprints_completed == 1
        assert track.sprints_total == 2

    def test_non_sprint_criteria_not_counted(self):
        """Test that non-CompletableTarget criteria aren't counted as sprints."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint Criterion",
                    description="Sprint must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="File Criterion",
                    description="README file must exist",
                    target=FileExistsTarget(paths=["README.md"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert track.sprints_total == 1  # Only the CompletableTarget


# =============================================================================
# TRACK TICKET TESTS - AGGREGATE PROGRESS
# =============================================================================


class TestTrackTicketAggregateProgress:
    """Tests for TrackTicket aggregate progress (tasks across sprints)."""

    def test_tasks_total_without_loader(self):
        """Test tasks_total returns 0 without loader."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint 1",
                    description="Sprint 1",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        TrackTicket.clear_loaders()
        assert track.tasks_total == 0
        assert track.tasks_completed == 0

    def test_tasks_total_with_loader(self):
        """Test tasks_total aggregates from sprints."""
        loader = MockTicketLoader()
        loader.add_mock_sprint("sprint-1", tasks_total=5, tasks_completed=3)
        loader.add_mock_sprint("sprint-2", tasks_total=8, tasks_completed=8)
        # Also add a mock for the parent roadmap to avoid ancestor lookup errors
        loader.tickets["roadmap-1"] = MockSprintTicket(0, 0)  # Dummy parent
        TrackTicket.set_loader(loader)

        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint 1",
                    description="Sprint 1",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="Sprint 2",
                    description="Sprint 2",
                    target=CompletableTarget(
                        completable_id="sprint-2",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        assert track.tasks_total == 13  # 5 + 8
        assert track.tasks_completed == 11  # 3 + 8

        # Clean up
        TrackTicket.clear_loaders()

    def test_tasks_with_missing_sprint(self):
        """Test tasks aggregation handles missing sprints gracefully."""
        loader = MockTicketLoader()
        loader.add_mock_sprint("sprint-1", tasks_total=5, tasks_completed=3)
        # sprint-2 is NOT added to loader
        # Also add a mock for the parent roadmap to avoid ancestor lookup errors
        loader.tickets["roadmap-1"] = MockSprintTicket(0, 0)  # Dummy parent
        TrackTicket.set_loader(loader)

        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Sprint 1",
                    description="Sprint 1",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="Sprint 2",
                    description="Sprint 2",
                    target=CompletableTarget(
                        completable_id="sprint-2",  # Missing from loader
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        # Should only count sprint-1, not fail
        assert track.tasks_total == 5
        assert track.tasks_completed == 3

        # Clean up
        TrackTicket.clear_loaders()


# =============================================================================
# TRACK TICKET TESTS - INHERITED BEHAVIOR
# =============================================================================


class TestTrackTicketInheritedBehavior:
    """Tests for behavior inherited from HierarchicalTicket."""

    def test_lifecycle_from_ticket(self):
        """Test lifecycle methods work."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            status=TicketStatus.NOT_STARTED,
        )

        # Start
        started = track.start()
        assert started.status == TicketStatus.IN_PROGRESS
        assert started.started_at is not None

        # Complete
        completed = started.complete()
        assert completed.status == TicketStatus.COMPLETED
        assert completed.completed_at is not None

    def test_convenience_accessors(self):
        """Test convenience accessors from HierarchicalTicket."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="c1",
                    name="File",
                    description="README file must exist",
                    target=FileExistsTarget(paths=["README.md"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    name="Sprint",
                    description="Sprint must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        # deliverables (FileExistsTarget)
        assert len(track.deliverables) == 1

        # subtasks (CompletableTarget blocking COMPLETED)
        assert len(track.subtasks) == 1

    def test_progress_computation(self):
        """Test progress computation from Completable."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="c1",
                    name="Met Criterion",
                    description="Sprint 1 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    name="Unmet Criterion",
                    description="Sprint 2 must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-2",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        progress = track.progress
        assert progress.total == 2
        assert progress.completed == 1
        assert progress.completion_percent == 50.0

    def test_children_property(self):
        """Test children property from Completable."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="c1",
                    name="Sprint 1",
                    description="Sprint 1 complete",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    name="Sprint 2",
                    description="Sprint 2 complete",
                    target=CompletableTarget(
                        completable_id="sprint-2",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        # children property extracts completable_ids
        children = track.children
        assert "sprint-1" in children
        assert "sprint-2" in children

    def test_is_complete(self):
        """Test is_complete from Completable."""
        # All criteria met
        complete_track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="c1",
                    name="Sprint",
                    description="Sprint must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert complete_track.is_complete is True

        # Not all criteria met
        incomplete_track = TrackTicket(
            id="track-2",
            name="Track 2",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
            criteria=[
                Criterion(
                    id="c1",
                    name="Sprint",
                    description="Sprint must be completed",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.IN_PROGRESS,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert incomplete_track.is_complete is False

    def test_immutable_copy(self):
        """Test that modifications return new instances."""
        track = TrackTicket(
            id="track-core",
            name="Core Track",
            roadmap_id="roadmap-1",
            parent_ref="roadmap-1",
        )

        started = track.start()
        assert started is not track
        assert started.status != track.status
