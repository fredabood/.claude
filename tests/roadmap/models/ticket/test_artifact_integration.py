"""
Tests for Artifact System integration across Ticket layers.

Tests cover:
- Layer 1 (Ticket): artifact_criteria, referenced_artifact_ids, stale detection
- Layer 2 (HierarchicalTicket): artifact aggregation, documentation health
- Layer 3 (Domain models): RoadmapTicket and SprintTicket artifact accessors

Design Reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.8
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List, Optional

from vibey.roadmap.models.ticket.ticket import Ticket
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.domain import (
    RoadmapTicket,
    SprintTicket,
    TrackTicket,
    TaskTicket,
    ArtifactInfo,
    ArtifactLoader,
)
from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.targets import (
    ArtifactTarget,
    CompletableTarget,
    FileExistsTarget,
)
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactType,
    ArtifactVerification,
    ContextArtifactSubtype,
    DocumentationHealth,
)


# =============================================================================
# MOCK ARTIFACT LOADER
# =============================================================================


class MockArtifactLoader:
    """Mock artifact loader for testing."""

    def __init__(self):
        self._artifacts: Dict[str, ArtifactInfo] = {}
        self._orphans: List[str] = []

    def add_artifact(
        self,
        artifact_id: str,
        artifact_type: ArtifactType,
        subtype: Optional[str] = None,
    ) -> None:
        """Add an artifact to the mock loader."""
        self._artifacts[artifact_id] = ArtifactInfo(
            id=artifact_id,
            artifact_type=artifact_type,
            artifact_subtype=subtype,
        )

    def set_orphans(self, orphan_ids: List[str]) -> None:
        """Set orphan artifact IDs."""
        self._orphans = orphan_ids

    def get_artifact_info(self, artifact_id: str) -> Optional[ArtifactInfo]:
        """Get artifact info by ID."""
        return self._artifacts.get(artifact_id)

    def get_orphan_artifact_ids(self) -> List[str]:
        """Get orphan artifact IDs."""
        return self._orphans


# =============================================================================
# MOCK TICKET LOADER
# =============================================================================


class MockTicketLoader:
    """Mock ticket loader for hierarchy testing."""

    def __init__(self):
        self._tickets: Dict[str, HierarchicalTicket] = {}

    def add_ticket(self, ticket: HierarchicalTicket) -> None:
        """Add a ticket to the mock loader."""
        self._tickets[ticket.id] = ticket

    def load(self, ticket_id: str) -> HierarchicalTicket:
        """Load a ticket by ID."""
        if ticket_id not in self._tickets:
            raise ValueError(f"Ticket not found: {ticket_id}")
        return self._tickets[ticket_id]


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def artifact_loader():
    """Create a mock artifact loader."""
    loader = MockArtifactLoader()
    # Add some test artifacts
    loader.add_artifact("art-code-1", ArtifactType.CODE)
    loader.add_artifact("art-code-2", ArtifactType.CODE)
    loader.add_artifact("art-test-1", ArtifactType.TEST)
    loader.add_artifact("art-doc-1", ArtifactType.DOCUMENTATION)
    loader.add_artifact("art-doc-2", ArtifactType.DOCUMENTATION)
    loader.add_artifact("art-agent-1", ArtifactType.AGENT)
    loader.add_artifact("art-workflow-1", ArtifactType.WORKFLOW)
    loader.add_artifact("art-template-1", ArtifactType.TEMPLATE)
    loader.add_artifact(
        "art-context-planning",
        ArtifactType.CONTEXT,
        ContextArtifactSubtype.PLANNING_DOC.value,
    )
    loader.add_artifact(
        "art-context-notes",
        ArtifactType.CONTEXT,
        ContextArtifactSubtype.IMPLEMENTATION_NOTES.value,
    )
    loader.add_artifact(
        "art-context-decision",
        ArtifactType.CONTEXT,
        ContextArtifactSubtype.DECISION_RECORD.value,
    )
    return loader


@pytest.fixture
def ticket_loader():
    """Create a mock ticket loader."""
    return MockTicketLoader()


@pytest.fixture(autouse=True)
def cleanup_loaders():
    """Clean up loaders after each test."""
    yield
    HierarchicalTicket.clear_loaders()
    RoadmapTicket.clear_artifact_loader()


# =============================================================================
# LAYER 1 (TICKET) TESTS
# =============================================================================


class TestTicketArtifactCriteria:
    """Tests for Ticket.artifact_criteria property."""

    def test_artifact_criteria_empty(self):
        """Test ticket with no artifact criteria."""
        ticket = Ticket(id="test-1", name="Test Ticket")
        assert ticket.artifact_criteria == []

    def test_artifact_criteria_found(self):
        """Test ticket with artifact criteria."""
        artifact_target = ArtifactTarget(
            artifact_id="art-doc-1",
            verification=ArtifactVerification.EXISTS,
            artifact_exists=True,
        )
        criterion = Criterion(
            id="crit-1",
            description="Documentation artifact",
            target=artifact_target,
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = Ticket(id="test-1", name="Test Ticket", criteria=[criterion])

        assert len(ticket.artifact_criteria) == 1
        assert ticket.artifact_criteria[0].id == "crit-1"

    def test_artifact_criteria_mixed(self):
        """Test ticket with mixed criteria types."""
        artifact_criterion = Criterion(
            id="crit-artifact",
            description="Artifact criterion",
            target=ArtifactTarget(artifact_id="art-1", artifact_exists=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        file_criterion = Criterion(
            id="crit-file",
            description="File criterion",
            target=FileExistsTarget(paths=["src/file.py"], all_exist=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = Ticket(
            id="test-1",
            name="Test Ticket",
            criteria=[artifact_criterion, file_criterion],
        )

        assert len(ticket.artifact_criteria) == 1
        assert ticket.artifact_criteria[0].id == "crit-artifact"


class TestTicketReferencedArtifactIds:
    """Tests for Ticket.referenced_artifact_ids property."""

    def test_no_artifacts(self):
        """Test ticket with no artifact references."""
        ticket = Ticket(id="test-1", name="Test Ticket")
        assert ticket.referenced_artifact_ids == []

    def test_single_artifact(self):
        """Test ticket referencing single artifact."""
        criterion = Criterion(
            id="crit-1",
            description="Doc artifact",
            target=ArtifactTarget(artifact_id="art-doc-1", artifact_exists=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = Ticket(id="test-1", name="Test Ticket", criteria=[criterion])

        assert ticket.referenced_artifact_ids == ["art-doc-1"]

    def test_multiple_artifacts(self):
        """Test ticket referencing multiple artifacts."""
        criteria = [
            Criterion(
                id=f"crit-{i}",
                description=f"Artifact {i}",
                target=ArtifactTarget(artifact_id=f"art-{i}", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            )
            for i in range(3)
        ]
        ticket = Ticket(id="test-1", name="Test Ticket", criteria=criteria)

        assert set(ticket.referenced_artifact_ids) == {"art-0", "art-1", "art-2"}


class TestTicketStaleArtifacts:
    """Tests for Ticket stale artifact detection."""

    def test_no_stale_artifacts(self):
        """Test ticket with no stale artifacts."""
        criterion = Criterion(
            id="crit-1",
            description="Fresh doc",
            target=ArtifactTarget(
                artifact_id="art-doc-1",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=False,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = Ticket(id="test-1", name="Test Ticket", criteria=[criterion])

        assert ticket.stale_artifact_criteria == []
        assert ticket.has_stale_artifacts is False

    def test_stale_artifacts_detected(self):
        """Test detection of stale artifacts."""
        criterion = Criterion(
            id="crit-1",
            description="Stale doc",
            target=ArtifactTarget(
                artifact_id="art-doc-stale",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=True,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = Ticket(id="test-1", name="Test Ticket", criteria=[criterion])

        assert len(ticket.stale_artifact_criteria) == 1
        assert ticket.has_stale_artifacts is True


# =============================================================================
# LAYER 2 (HIERARCHICAL TICKET) TESTS
# =============================================================================


class TestHierarchicalTicketArtifactCriteria:
    """Tests for HierarchicalTicket.artifact_criteria override."""

    def test_includes_instantiated_criteria(self):
        """Test that artifact_criteria uses all_criteria (includes instantiated)."""
        # Create artifact criterion
        artifact_criterion = Criterion(
            id="crit-artifact",
            description="Artifact criterion",
            target=ArtifactTarget(artifact_id="art-1", artifact_exists=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = HierarchicalTicket(
            id="test-1",
            name="Test Ticket",
            criteria=[artifact_criterion],
        )

        assert len(ticket.artifact_criteria) == 1


class TestHierarchicalTicketAllReferencedArtifacts:
    """Tests for HierarchicalTicket.all_referenced_artifacts aggregation."""

    def test_ultimate_child_returns_local(self):
        """Test ultimate child returns local referenced_artifact_ids."""
        criterion = Criterion(
            id="crit-1",
            description="Artifact",
            target=ArtifactTarget(artifact_id="art-1", artifact_exists=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        # Ultimate child has parent but no children
        ticket = HierarchicalTicket(
            id="task-1",
            name="Task",
            parent_ref="sprint-1",
            criteria=[criterion],
        )

        assert ticket.all_referenced_artifacts == ["art-1"]

    def test_parent_aggregates_from_children(self, ticket_loader):
        """Test parent aggregates artifacts from children."""
        # Create grandparent (track) - needed for ancestor chain
        grandparent = HierarchicalTicket(
            id="track-1",
            name="Track",
            parent_ref=None,  # Root ticket
            criteria=[],
        )
        ticket_loader.add_ticket(grandparent)

        # Create child with artifact
        child_criterion = Criterion(
            id="crit-child",
            description="Child artifact",
            target=ArtifactTarget(artifact_id="art-child", artifact_exists=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        child = HierarchicalTicket(
            id="task-1",
            name="Task",
            parent_ref="sprint-1",
            criteria=[child_criterion],
        )
        ticket_loader.add_ticket(child)

        # Create parent with its own artifact and child reference
        parent_criterion = Criterion(
            id="crit-parent",
            description="Parent artifact",
            target=ArtifactTarget(artifact_id="art-parent", artifact_exists=True),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        child_ref = Criterion(
            id="crit-child-ref",
            description="Child reference",
            target=CompletableTarget(completable_id="task-1", status=TicketStatus.COMPLETED),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        parent = HierarchicalTicket(
            id="sprint-1",
            name="Sprint",
            parent_ref="track-1",
            criteria=[parent_criterion, child_ref],
        )
        ticket_loader.add_ticket(parent)

        # Configure loader
        HierarchicalTicket.set_loader(ticket_loader)

        # Check aggregation
        all_artifacts = parent.all_referenced_artifacts
        assert set(all_artifacts) == {"art-parent", "art-child"}


class TestHierarchicalTicketStaleDocumentation:
    """Tests for HierarchicalTicket stale documentation aggregation."""

    def test_healthy_documentation(self):
        """Test ticket with no stale documentation."""
        criterion = Criterion(
            id="crit-1",
            description="Fresh doc",
            target=ArtifactTarget(
                artifact_id="art-doc-1",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=False,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = HierarchicalTicket(
            id="test-1",
            name="Test Ticket",
            parent_ref="parent-1",
            criteria=[criterion],
        )

        assert ticket.stale_documentation_artifacts == []
        assert ticket.has_stale_documentation is False

    def test_stale_documentation_detected(self):
        """Test stale documentation detection."""
        criterion = Criterion(
            id="crit-1",
            description="Stale doc",
            target=ArtifactTarget(
                artifact_id="art-stale",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=True,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = HierarchicalTicket(
            id="test-1",
            name="Test Ticket",
            parent_ref="parent-1",
            criteria=[criterion],
        )

        assert ticket.stale_documentation_artifacts == ["art-stale"]
        assert ticket.has_stale_documentation is True


class TestHierarchicalTicketDocumentationHealth:
    """Tests for HierarchicalTicket.documentation_health property."""

    def test_healthy(self):
        """Test healthy documentation status."""
        criterion = Criterion(
            id="crit-1",
            description="Fresh doc",
            target=ArtifactTarget(
                artifact_id="art-1",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=False,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        ticket = HierarchicalTicket(
            id="test-1",
            name="Test",
            parent_ref="parent-1",
            criteria=[criterion],
        )

        assert ticket.documentation_health == DocumentationHealth.HEALTHY

    def test_degraded(self):
        """Test degraded documentation status (stale but not blocking)."""
        criterion = Criterion(
            id="crit-1",
            description="Stale doc (not blocking)",
            target=ArtifactTarget(
                artifact_id="art-1",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=True,
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS,  # Not blocking COMPLETED
            required=False,
        )
        ticket = HierarchicalTicket(
            id="test-1",
            name="Test",
            parent_ref="parent-1",
            criteria=[criterion],
        )

        assert ticket.documentation_health == DocumentationHealth.DEGRADED

    def test_critical(self):
        """Test critical documentation status (stale and blocking)."""
        criterion = Criterion(
            id="crit-1",
            description="Stale doc blocking completion",
            target=ArtifactTarget(
                artifact_id="art-1",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=True,
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
            required=True,
        )
        ticket = HierarchicalTicket(
            id="test-1",
            name="Test",
            parent_ref="parent-1",
            criteria=[criterion],
        )

        assert ticket.documentation_health == DocumentationHealth.CRITICAL


# =============================================================================
# LAYER 3 (ROADMAP TICKET) TESTS
# =============================================================================


class TestRoadmapTicketArtifactLoader:
    """Tests for RoadmapTicket artifact loader configuration."""

    def test_set_artifact_loader(self, artifact_loader):
        """Test setting artifact loader."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        assert RoadmapTicket._artifact_loader is not None

    def test_clear_artifact_loader(self, artifact_loader):
        """Test clearing artifact loader."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        RoadmapTicket.clear_artifact_loader()
        assert RoadmapTicket._artifact_loader is None


class TestRoadmapTicketArtifactAccessors:
    """Tests for RoadmapTicket artifact accessor properties."""

    def test_all_project_documentation(self, artifact_loader, ticket_loader):
        """Test all_project_documentation returns DOCUMENTATION artifacts."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        # Create roadmap with documentation artifact criteria
        criteria = [
            Criterion(
                id="crit-doc-1",
                description="Doc 1",
                target=ArtifactTarget(artifact_id="art-doc-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-code-1",
                description="Code 1",
                target=ArtifactTarget(artifact_id="art-code-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Roadmap",
            criteria=criteria,
        )

        docs = roadmap.all_project_documentation
        assert "art-doc-1" in docs
        assert "art-code-1" not in docs

    def test_framework_components(self, artifact_loader, ticket_loader):
        """Test framework_components returns AGENT, WORKFLOW, TEMPLATE artifacts."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        criteria = [
            Criterion(
                id="crit-agent",
                description="Agent",
                target=ArtifactTarget(artifact_id="art-agent-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-workflow",
                description="Workflow",
                target=ArtifactTarget(artifact_id="art-workflow-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-code",
                description="Code",
                target=ArtifactTarget(artifact_id="art-code-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Roadmap",
            criteria=criteria,
        )

        components = roadmap.framework_components
        assert "art-agent-1" in components
        assert "art-workflow-1" in components
        assert "art-code-1" not in components

    def test_orphan_artifacts(self, artifact_loader):
        """Test orphan_artifacts returns artifacts not referenced by tickets."""
        artifact_loader.set_orphans(["art-orphan-1", "art-orphan-2"])
        RoadmapTicket.set_artifact_loader(artifact_loader)

        roadmap = RoadmapTicket(id="roadmap-1", name="Roadmap")
        orphans = roadmap.orphan_artifacts

        assert orphans == ["art-orphan-1", "art-orphan-2"]

    def test_code_artifacts(self, artifact_loader, ticket_loader):
        """Test code_artifacts returns CODE type artifacts."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        criteria = [
            Criterion(
                id="crit-code-1",
                description="Code 1",
                target=ArtifactTarget(artifact_id="art-code-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-test-1",
                description="Test 1",
                target=ArtifactTarget(artifact_id="art-test-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Roadmap",
            criteria=criteria,
        )

        codes = roadmap.code_artifacts
        assert "art-code-1" in codes
        assert "art-test-1" not in codes

    def test_no_loader_returns_empty(self):
        """Test that properties return empty without loader configured."""
        roadmap = RoadmapTicket(id="roadmap-1", name="Roadmap")

        assert roadmap.framework_components == []
        assert roadmap.orphan_artifacts == []
        assert roadmap.code_artifacts == []
        assert roadmap.test_artifacts == []


# =============================================================================
# LAYER 3 (SPRINT TICKET) TESTS
# =============================================================================


class TestSprintTicketArtifactAccessors:
    """Tests for SprintTicket artifact accessor properties."""

    def test_sprint_context_artifacts(self, artifact_loader):
        """Test sprint_context_artifacts returns CONTEXT type artifacts."""
        RoadmapTicket.set_artifact_loader(artifact_loader)

        criteria = [
            Criterion(
                id="crit-planning",
                description="Planning doc",
                target=ArtifactTarget(
                    artifact_id="art-context-planning",
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-code",
                description="Code",
                target=ArtifactTarget(artifact_id="art-code-1", artifact_exists=True),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            criteria=criteria,
        )

        context = sprint.sprint_context_artifacts
        assert "art-context-planning" in context
        assert "art-code-1" not in context

    def test_planning_artifacts(self, artifact_loader):
        """Test planning_artifacts returns PLANNING_DOC subtype."""
        RoadmapTicket.set_artifact_loader(artifact_loader)

        criteria = [
            Criterion(
                id="crit-planning",
                description="Planning doc",
                target=ArtifactTarget(
                    artifact_id="art-context-planning",
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-notes",
                description="Implementation notes",
                target=ArtifactTarget(
                    artifact_id="art-context-notes",
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            criteria=criteria,
        )

        planning = sprint.planning_artifacts
        assert "art-context-planning" in planning
        assert "art-context-notes" not in planning

    def test_implementation_notes_artifacts(self, artifact_loader):
        """Test implementation_notes_artifacts returns IMPL_NOTES subtype."""
        RoadmapTicket.set_artifact_loader(artifact_loader)

        criteria = [
            Criterion(
                id="crit-notes",
                description="Implementation notes",
                target=ArtifactTarget(
                    artifact_id="art-context-notes",
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            criteria=criteria,
        )

        notes = sprint.implementation_notes_artifacts
        assert "art-context-notes" in notes

    def test_decision_record_artifacts(self, artifact_loader):
        """Test decision_record_artifacts returns DECISION_RECORD subtype."""
        RoadmapTicket.set_artifact_loader(artifact_loader)

        criteria = [
            Criterion(
                id="crit-decision",
                description="Decision record",
                target=ArtifactTarget(
                    artifact_id="art-context-decision",
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            criteria=criteria,
        )

        decisions = sprint.decision_record_artifacts
        assert "art-context-decision" in decisions

    def test_no_loader_returns_empty(self):
        """Test that properties return empty without loader configured."""
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
        )

        assert sprint.sprint_context_artifacts == []
        assert sprint.planning_artifacts == []
        assert sprint.implementation_notes_artifacts == []
        assert sprint.decision_record_artifacts == []


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestArtifactIntegrationEndToEnd:
    """End-to-end integration tests for artifact system."""

    def test_full_hierarchy_artifact_aggregation(self, artifact_loader, ticket_loader):
        """Test artifact aggregation across full ticket hierarchy."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        # Create task with code artifact
        task = TaskTicket(
            id="task-1",
            name="Task 1",
            parent_ref="sprint-1",
            sprint_id="sprint-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            estimated_tokens=1000,
            criteria=[
                Criterion(
                    id="crit-task-code",
                    description="Task code",
                    target=ArtifactTarget(artifact_id="art-code-1", artifact_exists=True),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(task)

        # Create sprint with context artifact and task reference
        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint 1",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-sprint-context",
                    description="Sprint context",
                    target=ArtifactTarget(
                        artifact_id="art-context-planning",
                        artifact_exists=True,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-task-ref",
                    description="Task reference",
                    target=CompletableTarget(
                        completable_id="task-1",
                        status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(sprint)

        # Create track with doc artifact and sprint reference
        track = TrackTicket(
            id="track-1",
            name="Track 1",
            parent_ref="roadmap-1",
            roadmap_id="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-track-doc",
                    description="Track doc",
                    target=ArtifactTarget(artifact_id="art-doc-1", artifact_exists=True),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-sprint-ref",
                    description="Sprint reference",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(track)

        # Create roadmap with agent artifact and track reference
        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Roadmap",
            criteria=[
                Criterion(
                    id="crit-roadmap-agent",
                    description="Roadmap agent",
                    target=ArtifactTarget(artifact_id="art-agent-1", artifact_exists=True),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-track-ref",
                    description="Track reference",
                    target=CompletableTarget(
                        completable_id="track-1",
                        status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(roadmap)

        # Verify aggregation at each level
        assert "art-code-1" in task.all_referenced_artifacts
        assert set(sprint.all_referenced_artifacts) >= {"art-context-planning", "art-code-1"}
        assert set(track.all_referenced_artifacts) >= {"art-doc-1", "art-context-planning", "art-code-1"}
        assert set(roadmap.all_referenced_artifacts) >= {
            "art-agent-1",
            "art-doc-1",
            "art-context-planning",
            "art-code-1",
        }

    def test_documentation_health_propagation(self, artifact_loader, ticket_loader):
        """Test documentation health across hierarchy with stale docs."""
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        # Create hierarchy chain to satisfy ancestor lookups
        roadmap = RoadmapTicket(id="roadmap-1", name="Roadmap")
        ticket_loader.add_ticket(roadmap)

        track = TrackTicket(
            id="track-1",
            name="Track",
            parent_ref="roadmap-1",
            roadmap_id="roadmap-1",
        )
        ticket_loader.add_ticket(track)

        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
        )
        ticket_loader.add_ticket(sprint)

        # Create task with stale doc that blocks completion
        task = TaskTicket(
            id="task-stale",
            name="Task with Stale Doc",
            parent_ref="sprint-1",
            sprint_id="sprint-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            estimated_tokens=1000,
            criteria=[
                Criterion(
                    id="crit-stale",
                    description="Stale documentation",
                    target=ArtifactTarget(
                        artifact_id="art-doc-1",
                        verification=ArtifactVerification.NOT_STALE,
                        artifact_exists=True,
                        artifact_is_stale=True,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                    required=True,
                ),
            ],
        )
        ticket_loader.add_ticket(task)

        assert task.has_stale_documentation is True
        assert task.documentation_health == DocumentationHealth.CRITICAL
