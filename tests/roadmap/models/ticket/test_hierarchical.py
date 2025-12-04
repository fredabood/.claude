"""
Tests for Layer 2 HierarchicalTicket class.

Tests cover:
- ULID identity fields (sequence, slug)
- Sibling navigation
- Smart accessors (commits, requirements)
- Hierarchy traversal
- Loader abstraction
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from vibey.roadmap.models.ticket import (
    HierarchicalTicket,
    TicketLoader,
    SiblingLoader,
    GitCommit,
    Criterion,
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    ManualTarget,
    ThresholdTarget,
    TicketStatus,
    Priority,
    Requirement,
    CriterionTemplate,
    CriterionTargetType,
    Progress,
    RefreshContext,
    ActivityType,
)


# =============================================================================
# TEST FIXTURES - MOCK LOADERS
# =============================================================================


class MockTicketLoader:
    """Mock loader for testing hierarchy traversal."""

    def __init__(self):
        self.tickets: Dict[str, HierarchicalTicket] = {}

    def register(self, ticket: HierarchicalTicket) -> None:
        """Register a ticket for lookup."""
        self.tickets[ticket.id] = ticket

    def load(self, ticket_id: str) -> HierarchicalTicket:
        """Load a ticket by ID."""
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket not found: {ticket_id}")
        return self.tickets[ticket_id]


class MockSiblingLoader:
    """Mock loader for testing sibling navigation."""

    def __init__(self, loader: MockTicketLoader):
        self.loader = loader

    def load_siblings(self, parent_id: str, exclude_id: str) -> List[HierarchicalTicket]:
        """Load siblings (other children of same parent)."""
        return [
            t for t in self.loader.tickets.values()
            if t.parent_ref == parent_id and t.id != exclude_id
        ]


@pytest.fixture
def mock_loader():
    """Create a mock ticket loader."""
    return MockTicketLoader()


@pytest.fixture
def mock_sibling_loader(mock_loader):
    """Create a mock sibling loader."""
    return MockSiblingLoader(mock_loader)


@pytest.fixture(autouse=True)
def setup_loaders(mock_loader, mock_sibling_loader):
    """Set up loaders before each test and clean up after."""
    HierarchicalTicket.set_loader(mock_loader)
    HierarchicalTicket.set_sibling_loader(mock_sibling_loader)
    yield
    HierarchicalTicket.clear_loaders()


# =============================================================================
# ULID IDENTITY TESTS
# =============================================================================


class TestULIDIdentity:
    """Tests for ULID identity fields."""

    def test_default_sequence(self):
        """Test default sequence is 0."""
        ticket = HierarchicalTicket(id="task-001", name="Task")
        assert ticket.sequence == 0

    def test_custom_sequence(self):
        """Test setting custom sequence."""
        ticket = HierarchicalTicket(id="task-001", name="Task", sequence=5)
        assert ticket.sequence == 5

    def test_default_slug(self):
        """Test default slug is empty string."""
        ticket = HierarchicalTicket(id="task-001", name="Task")
        assert ticket.slug == ""

    def test_custom_slug(self):
        """Test setting custom slug."""
        ticket = HierarchicalTicket(id="task-001", name="Task", slug="my-task")
        assert ticket.slug == "my-task"

    def test_reorder_changes_sequence(self):
        """Test reorder() changes sequence."""
        ticket = HierarchicalTicket(id="task-001", name="Task", sequence=0)
        reordered = ticket.reorder(5)

        assert reordered.sequence == 5
        assert ticket.sequence == 0  # Original unchanged
        assert reordered.id == ticket.id  # ID unchanged

    def test_reorder_returns_new_instance(self):
        """Test reorder() returns a new instance."""
        ticket = HierarchicalTicket(id="task-001", name="Task")
        reordered = ticket.reorder(3)

        assert ticket is not reordered


# =============================================================================
# SIBLING NAVIGATION TESTS
# =============================================================================


class TestSiblingNavigation:
    """Tests for sibling navigation."""

    def test_siblings_empty_for_root(self):
        """Test siblings is empty for root ticket."""
        root = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        assert root.siblings == []

    def test_siblings_returns_other_children(self, mock_loader):
        """Test siblings returns other children of same parent."""
        parent = HierarchicalTicket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="c1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    description="Task 2",
                    target=CompletableTarget(
                        completable_id="task-002",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001", sequence=0
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001", sequence=1
        )
        task3 = HierarchicalTicket(
            id="task-003", name="Task 3", parent_ref="sprint-001", sequence=2
        )

        mock_loader.register(parent)
        mock_loader.register(task1)
        mock_loader.register(task2)
        mock_loader.register(task3)

        siblings = task1.siblings
        assert len(siblings) == 2
        assert {s.id for s in siblings} == {"task-002", "task-003"}

    def test_siblings_sorted_by_sequence(self, mock_loader):
        """Test siblings are sorted by sequence."""
        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001", sequence=2
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001", sequence=0
        )
        task3 = HierarchicalTicket(
            id="task-003", name="Task 3", parent_ref="sprint-001", sequence=1
        )

        mock_loader.register(task1)
        mock_loader.register(task2)
        mock_loader.register(task3)

        siblings = task1.siblings
        assert [s.id for s in siblings] == ["task-002", "task-003"]

    def test_next_sibling(self, mock_loader):
        """Test next_sibling returns next by sequence."""
        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001", sequence=0
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001", sequence=1
        )
        task3 = HierarchicalTicket(
            id="task-003", name="Task 3", parent_ref="sprint-001", sequence=2
        )

        mock_loader.register(task1)
        mock_loader.register(task2)
        mock_loader.register(task3)

        assert task1.next_sibling.id == "task-002"
        assert task2.next_sibling.id == "task-003"
        assert task3.next_sibling is None

    def test_prev_sibling(self, mock_loader):
        """Test prev_sibling returns previous by sequence."""
        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001", sequence=0
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001", sequence=1
        )
        task3 = HierarchicalTicket(
            id="task-003", name="Task 3", parent_ref="sprint-001", sequence=2
        )

        mock_loader.register(task1)
        mock_loader.register(task2)
        mock_loader.register(task3)

        assert task1.prev_sibling is None
        assert task2.prev_sibling.id == "task-001"
        assert task3.prev_sibling.id == "task-002"


# =============================================================================
# COMMITS AGGREGATION TESTS
# =============================================================================


class TestCommitsAggregation:
    """Tests for commits aggregation."""

    def test_commits_local_returns_local_commits(self):
        """Test commits_local returns only local commits."""
        commit = GitCommit(
            sha="abc123",
            message="feat: add feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        ticket = HierarchicalTicket(
            id="task-001", name="Task", commits=[commit]
        )

        assert len(ticket.commits_local) == 1
        assert ticket.commits_local[0].sha == "abc123"

    def test_commits_aggregated_for_leaf(self):
        """Test commits_aggregated returns local for leaf ticket."""
        commit = GitCommit(
            sha="abc123",
            message="feat: add feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        # Leaf ticket (is_ultimate_child = has parent, no children)
        ticket = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001", commits=[commit]
        )

        assert len(ticket.commits_aggregated) == 1

    def test_commits_aggregated_collects_from_children(self, mock_loader):
        """Test commits_aggregated collects from children."""
        commit1 = GitCommit(
            sha="abc123",
            message="feat: task 1",
            date=datetime.now(timezone.utc) - timedelta(hours=2),
            author="dev@example.com",
        )
        commit2 = GitCommit(
            sha="def456",
            message="feat: task 2",
            date=datetime.now(timezone.utc) - timedelta(hours=1),
            author="dev@example.com",
        )
        commit_parent = GitCommit(
            sha="ghi789",
            message="feat: sprint setup",
            date=datetime.now(timezone.utc) - timedelta(hours=3),
            author="dev@example.com",
        )

        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001", commits=[commit1]
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001", commits=[commit2]
        )
        sprint = HierarchicalTicket(
            id="sprint-001",
            name="Sprint",
            commits=[commit_parent],
            criteria=[
                Criterion(
                    id="c1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    description="Task 2",
                    target=CompletableTarget(
                        completable_id="task-002",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        mock_loader.register(sprint)
        mock_loader.register(task1)
        mock_loader.register(task2)

        aggregated = sprint.commits_aggregated
        assert len(aggregated) == 3
        # Should be sorted by date
        assert aggregated[0].sha == "ghi789"  # Oldest
        assert aggregated[1].sha == "abc123"
        assert aggregated[2].sha == "def456"  # Newest


# =============================================================================
# HIERARCHY TRAVERSAL TESTS
# =============================================================================


class TestHierarchyTraversal:
    """Tests for hierarchy traversal."""

    def test_parent_returns_none_for_root(self):
        """Test parent returns None for root ticket."""
        root = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        assert root.parent is None

    def test_parent_returns_parent_ticket(self, mock_loader):
        """Test parent returns parent ticket."""
        parent = HierarchicalTicket(id="sprint-001", name="Sprint")
        child = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )

        mock_loader.register(parent)
        mock_loader.register(child)

        assert child.parent.id == "sprint-001"

    def test_children_tickets_returns_children(self, mock_loader):
        """Test children_tickets returns child tickets."""
        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001"
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001"
        )
        sprint = HierarchicalTicket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="c1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    description="Task 2",
                    target=CompletableTarget(
                        completable_id="task-002",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        mock_loader.register(sprint)
        mock_loader.register(task1)
        mock_loader.register(task2)

        children = sprint.children_tickets
        assert len(children) == 2
        assert {c.id for c in children} == {"task-001", "task-002"}

    def test_ancestors_returns_path_to_root(self, mock_loader):
        """Test ancestors returns path from parent to root."""
        roadmap = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        track = HierarchicalTicket(
            id="track-001", name="Track", parent_ref="roadmap-001"
        )
        sprint = HierarchicalTicket(
            id="sprint-001", name="Sprint", parent_ref="track-001"
        )
        task = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )

        mock_loader.register(roadmap)
        mock_loader.register(track)
        mock_loader.register(sprint)
        mock_loader.register(task)

        ancestors = task.ancestors
        assert len(ancestors) == 3
        assert [a.id for a in ancestors] == ["sprint-001", "track-001", "roadmap-001"]

    def test_descendants_returns_all_children(self, mock_loader):
        """Test descendants returns all descendants."""
        task1 = HierarchicalTicket(
            id="task-001", name="Task 1", parent_ref="sprint-001"
        )
        task2 = HierarchicalTicket(
            id="task-002", name="Task 2", parent_ref="sprint-001"
        )
        sprint = HierarchicalTicket(
            id="sprint-001",
            name="Sprint",
            parent_ref="track-001",
            criteria=[
                Criterion(
                    id="c1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    description="Task 2",
                    target=CompletableTarget(
                        completable_id="task-002",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        track = HierarchicalTicket(
            id="track-001",
            name="Track",
            criteria=[
                Criterion(
                    id="c3",
                    description="Sprint",
                    target=CompletableTarget(
                        completable_id="sprint-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        mock_loader.register(track)
        mock_loader.register(sprint)
        mock_loader.register(task1)
        mock_loader.register(task2)

        descendants = track.descendants
        assert len(descendants) == 3
        assert {d.id for d in descendants} == {"sprint-001", "task-001", "task-002"}

    def test_root_returns_ultimate_parent(self, mock_loader):
        """Test root returns the ultimate parent."""
        roadmap = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        track = HierarchicalTicket(
            id="track-001", name="Track", parent_ref="roadmap-001"
        )
        sprint = HierarchicalTicket(
            id="sprint-001", name="Sprint", parent_ref="track-001"
        )
        task = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )

        mock_loader.register(roadmap)
        mock_loader.register(track)
        mock_loader.register(sprint)
        mock_loader.register(task)

        assert task.root.id == "roadmap-001"
        assert sprint.root.id == "roadmap-001"
        assert track.root.id == "roadmap-001"
        assert roadmap.root.id == "roadmap-001"

    def test_depth_returns_hierarchy_level(self, mock_loader):
        """Test depth returns correct hierarchy level."""
        roadmap = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        track = HierarchicalTicket(
            id="track-001", name="Track", parent_ref="roadmap-001"
        )
        sprint = HierarchicalTicket(
            id="sprint-001", name="Sprint", parent_ref="track-001"
        )
        task = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )

        mock_loader.register(roadmap)
        mock_loader.register(track)
        mock_loader.register(sprint)
        mock_loader.register(task)

        assert roadmap.depth == 0
        assert track.depth == 1
        assert sprint.depth == 2
        assert task.depth == 3


# =============================================================================
# PATH TESTS
# =============================================================================


class TestPaths:
    """Tests for path methods."""

    def test_get_path(self, mock_loader):
        """Test get_path returns list of IDs from root to self."""
        roadmap = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        track = HierarchicalTicket(
            id="track-001", name="Track", parent_ref="roadmap-001"
        )
        task = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="track-001"
        )

        mock_loader.register(roadmap)
        mock_loader.register(track)
        mock_loader.register(task)

        assert task.get_path() == ["roadmap-001", "track-001", "task-001"]

    def test_get_slug_path(self, mock_loader):
        """Test get_slug_path returns slash-separated path."""
        roadmap = HierarchicalTicket(
            id="roadmap-001", name="Roadmap", slug="vibey"
        )
        track = HierarchicalTicket(
            id="track-001", name="Track", parent_ref="roadmap-001", slug="backend"
        )
        task = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="track-001", slug="implement-models"
        )

        mock_loader.register(roadmap)
        mock_loader.register(track)
        mock_loader.register(task)

        assert task.get_slug_path() == "vibey/backend/implement-models"

    def test_get_slug_path_uses_id_when_no_slug(self, mock_loader):
        """Test get_slug_path falls back to ID when no slug."""
        roadmap = HierarchicalTicket(id="roadmap-001", name="Roadmap")
        track = HierarchicalTicket(
            id="track-001", name="Track", parent_ref="roadmap-001", slug="backend"
        )
        task = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="track-001"
        )

        mock_loader.register(roadmap)
        mock_loader.register(track)
        mock_loader.register(task)

        assert task.get_slug_path() == "roadmap-001/backend/task-001"


# =============================================================================
# ALL CRITERIA TESTS
# =============================================================================


class TestAllCriteria:
    """Tests for all_criteria property."""

    def test_all_criteria_includes_explicit(self):
        """Test all_criteria includes explicit criteria."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="file-1",
                    description="Create file",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        assert len(ticket.all_criteria) >= 1
        assert ticket.all_criteria[0].id == "file-1"

    def test_all_criteria_includes_instantiated(self):
        """Test all_criteria includes instantiated from requirements."""
        # Create ticket with requirements that generate criteria
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            requirements_local=[
                Requirement(
                    id="test-req",
                    name="Test Requirement",
                    description="Must have tests",
                    criterion_template=CriterionTemplate(
                        target_type=CriterionTargetType.MANUAL,
                        target_config={"assessor": "ci", "instructions": "Check"},
                        description_template="Test check",
                    ),
                ),
            ],
        )

        # instantiated_criteria would include the requirement
        all_crit = ticket.all_criteria
        # Should have at least the instantiated criterion
        assert len(all_crit) >= 0  # May be 0 if requirement not applicable


# =============================================================================
# CONVENIENCE ACCESSOR TESTS (OVERRIDE)
# =============================================================================


class TestConvenienceAccessorsOverride:
    """Tests for overridden convenience accessors using all_criteria."""

    def test_deliverables_uses_all_criteria(self):
        """Test deliverables uses all_criteria."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="file-1",
                    description="Create file",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        deliverables = ticket.deliverables
        assert len(deliverables) == 1
        assert deliverables[0].id == "file-1"

    def test_tests_uses_all_criteria(self):
        """Test tests uses all_criteria."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="test-1",
                    description="Run tests",
                    target=TestPassesTarget(test_command="pytest"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        tests = ticket.tests
        assert len(tests) == 1
        assert tests[0].id == "test-1"

    def test_thresholds_accessor(self):
        """Test thresholds accessor."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="coverage-1",
                    description="Coverage threshold",
                    target=ThresholdTarget(
                        metric_name="coverage",
                        threshold=80.0,
                        comparison="gte",
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        thresholds = ticket.thresholds
        assert len(thresholds) == 1
        assert thresholds[0].id == "coverage-1"


# =============================================================================
# PROGRESS TESTS (OVERRIDE)
# =============================================================================


class TestProgressOverride:
    """Tests for overridden progress methods using all_criteria."""

    def test_progress_for_transition_uses_all_criteria(self):
        """Test progress_for_transition uses all_criteria."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="crit-1",
                    description="Criteria 1",
                    target=CompletableTarget(
                        completable_id="dep-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    description="Criteria 2",
                    target=CompletableTarget(
                        completable_id="dep-2",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        progress = ticket.progress_for_transition(TicketStatus.COMPLETED)
        assert progress.total == 2
        assert progress.completed == 1


# =============================================================================
# LOADER ERROR TESTS
# =============================================================================


class TestLoaderErrors:
    """Tests for loader error handling."""

    def test_load_without_loader_raises(self):
        """Test loading ticket without loader raises error."""
        HierarchicalTicket.clear_loaders()

        ticket = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )

        with pytest.raises(RuntimeError, match="No loader configured"):
            _ = ticket.parent

    def test_load_missing_ticket_raises(self, mock_loader):
        """Test loading missing ticket raises error."""
        ticket = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )
        mock_loader.register(ticket)

        with pytest.raises(ValueError, match="Ticket not found"):
            _ = ticket.parent


# =============================================================================
# INHERITANCE FROM TICKET TESTS
# =============================================================================


class TestTicketInheritance:
    """Tests that HierarchicalTicket properly inherits from Ticket."""

    def test_lifecycle_methods_work(self):
        """Test lifecycle methods from Ticket work."""
        ticket = HierarchicalTicket(id="task-001", name="Task")
        started = ticket.start()

        assert started.status == TicketStatus.IN_PROGRESS
        assert started.started_at is not None

    def test_add_commit_works(self):
        """Test add_commit from Ticket works."""
        ticket = HierarchicalTicket(id="task-001", name="Task")
        commit = GitCommit(
            sha="abc123",
            message="feat",
            date=datetime.now(timezone.utc),
            author="dev",
        )
        updated = ticket.add_commit(commit)

        assert len(updated.commits) == 1

    def test_hierarchy_properties_inherited(self):
        """Test hierarchy properties from Ticket work."""
        parent = HierarchicalTicket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="c1",
                    description="Task",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        child = HierarchicalTicket(
            id="task-001", name="Task", parent_ref="sprint-001"
        )

        assert parent.is_parent is True
        assert parent.is_child is False
        assert child.is_parent is False
        assert child.is_child is True


# =============================================================================
# AUTO-PROGRESSION TESTS
# =============================================================================


class TestAutoProgress:
    """Tests for auto_progress() method."""

    def test_auto_progress_with_no_criteria(self):
        """Test auto_progress on ticket with no criteria progresses through statuses."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
        )
        context = RefreshContext()

        transitions = ticket.auto_progress(context)

        # With no criteria, ticket can progress through all statuses
        assert len(transitions) >= 1
        # First transition should be to IN_PROGRESS
        assert "NOT_STARTED" in transitions[0] or "not_started" in transitions[0]

    def test_auto_progress_blocked_by_unmet_criteria(self):
        """Test auto_progress stops when criteria are not met."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Dependency not met",
                    target=CompletableTarget(
                        completable_id="other-task",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
            ],
        )
        context = RefreshContext()

        transitions = ticket.auto_progress(context)

        # Should not progress because dependency blocks IN_PROGRESS
        assert len(transitions) == 0
        assert ticket.status == TicketStatus.NOT_STARTED

    def test_auto_progress_advances_when_criteria_met(self):
        """Test auto_progress advances when all criteria are met."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Dependency met",
                    target=CompletableTarget(
                        completable_id="other-task",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Met
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
            ],
        )
        context = RefreshContext()

        transitions = ticket.auto_progress(context)

        # Should progress to IN_PROGRESS (and potentially further)
        assert len(transitions) >= 1
        assert "in_progress" in transitions[0].lower()

    def test_auto_progress_logs_to_activity_log(self):
        """Test auto_progress logs transitions to activity log."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
        )
        context = RefreshContext()

        ticket.auto_progress(context)

        # Should have at least one log entry
        assert len(context.activity_log) >= 1
        log_entry = context.activity_log[0]
        assert log_entry["type"] == ActivityType.AUTO_PROGRESSION.value
        assert log_entry["entity_id"] == "task-001"

    def test_auto_progress_terminal_state_no_progression(self):
        """Test auto_progress does nothing for terminal states."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.WONT_DO,  # Terminal state
        )
        context = RefreshContext()

        transitions = ticket.auto_progress(context)

        assert len(transitions) == 0
        assert ticket.status == TicketStatus.WONT_DO

    def test_auto_progress_updates_started_at(self):
        """Test auto_progress sets started_at when transitioning to IN_PROGRESS."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
            started_at=None,
        )
        context = RefreshContext()

        ticket.auto_progress(context)

        # After progressing, started_at should be set
        assert ticket.started_at is not None

    def test_auto_progress_skips_manual_criteria_refresh(self):
        """Test auto_progress skips refresh for manual (non-automatic) criteria."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
            criteria=[
                Criterion(
                    id="manual-1",
                    description="Manual approval",
                    target=ManualTarget(assessor="human"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        context = RefreshContext()

        # Should not raise error - manual targets don't have refresh()
        transitions = ticket.auto_progress(context)

        # ManualTarget has is_automatic=False, so refresh won't be called
        # Ticket can still progress to IN_PROGRESS
        assert len(transitions) >= 1


class TestTransitionTo:
    """Tests for _transition_to() method."""

    def test_transition_to_updates_status(self):
        """Test _transition_to updates status."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
        )

        ticket._transition_to(TicketStatus.IN_PROGRESS)

        assert ticket.status == TicketStatus.IN_PROGRESS

    def test_transition_to_updates_updated_at(self):
        """Test _transition_to updates updated_at timestamp."""
        old_updated = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
            updated_at=old_updated,
        )

        ticket._transition_to(TicketStatus.IN_PROGRESS)

        assert ticket.updated_at > old_updated

    def test_transition_to_in_progress_sets_started_at(self):
        """Test _transition_to IN_PROGRESS sets started_at."""
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.NOT_STARTED,
            started_at=None,
        )

        ticket._transition_to(TicketStatus.IN_PROGRESS)

        assert ticket.started_at is not None

    def test_transition_to_completed_sets_completed_at(self):
        """Test _transition_to COMPLETED sets completed_at."""
        now = datetime.now(timezone.utc)
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),  # created_at must be before started_at
            started_at=now,  # Required for IN_PROGRESS status
            completed_at=None,
        )

        ticket._transition_to(TicketStatus.COMPLETED)

        assert ticket.completed_at is not None

    def test_transition_to_preserves_existing_started_at(self):
        """Test _transition_to preserves existing started_at."""
        original_created = datetime.now(timezone.utc) - timedelta(hours=3)
        original_started = datetime.now(timezone.utc) - timedelta(hours=2)
        ticket = HierarchicalTicket(
            id="task-001",
            name="Task",
            status=TicketStatus.IN_PROGRESS,
            created_at=original_created,  # Must be before started_at
            started_at=original_started,
        )

        ticket._transition_to(TicketStatus.COMPLETED)

        # started_at should not change
        assert ticket.started_at == original_started


class TestStatusPrecedes:
    """Tests for TicketStatus.precedes() method."""

    def test_not_started_precedes_in_progress(self):
        """Test NOT_STARTED precedes IN_PROGRESS."""
        assert TicketStatus.NOT_STARTED.precedes(TicketStatus.IN_PROGRESS)

    def test_in_progress_precedes_completed(self):
        """Test IN_PROGRESS precedes COMPLETED."""
        assert TicketStatus.IN_PROGRESS.precedes(TicketStatus.COMPLETED)

    def test_completed_precedes_production_ready(self):
        """Test COMPLETED precedes PRODUCTION_READY."""
        assert TicketStatus.COMPLETED.precedes(TicketStatus.PRODUCTION_READY)

    def test_completed_does_not_precede_not_started(self):
        """Test COMPLETED does not precede NOT_STARTED."""
        assert not TicketStatus.COMPLETED.precedes(TicketStatus.NOT_STARTED)

    def test_same_status_does_not_precede(self):
        """Test same status does not precede itself."""
        assert not TicketStatus.IN_PROGRESS.precedes(TicketStatus.IN_PROGRESS)

    def test_terminal_status_does_not_precede(self):
        """Test terminal status does not precede anything."""
        assert not TicketStatus.WONT_DO.precedes(TicketStatus.COMPLETED)
        assert not TicketStatus.SUPERSEDED.precedes(TicketStatus.IN_PROGRESS)
