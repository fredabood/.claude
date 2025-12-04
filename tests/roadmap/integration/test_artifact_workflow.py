"""
End-to-end integration tests for artifact workflows.

Tests cover:
- Create artifact, reference in criterion, complete ticket
- Modify source, detect stale docs, block completion
- Update docs, clear stale flag, complete ticket
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from vibey.roadmap.models.ticket.artifact import Artifact, ArtifactProvenance
from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactType,
    ArtifactVerification,
    DocumentationHealth,
    ProvenanceType,
)
from vibey.roadmap.models.ticket.ticket import Ticket
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.domain import (
    RoadmapTicket,
    SprintTicket,
    TrackTicket,
    TaskTicket,
    ArtifactInfo,
)
from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.targets import ArtifactTarget, CompletableTarget
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.operations.impact_analyzer import (
    ImpactAnalyzer,
    ArtifactSummary,
)


# =============================================================================
# MOCK INFRASTRUCTURE
# =============================================================================


class MockArtifactRegistry:
    """Mock artifact registry for integration testing."""

    def __init__(self):
        self._artifacts: Dict[str, Artifact] = {}

    def add(self, artifact: Artifact) -> None:
        """Add an artifact to the registry."""
        self._artifacts[artifact.id] = artifact

    def get(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        return self._artifacts.get(artifact_id)

    def get_all(self) -> List[Artifact]:
        """Get all artifacts."""
        return list(self._artifacts.values())

    def get_referencing_criteria(self, artifact_id: str) -> List[str]:
        """Get criterion IDs that reference this artifact (mock implementation)."""
        return []

    def update(self, artifact: Artifact) -> None:
        """Update an artifact in the registry."""
        self._artifacts[artifact.id] = artifact

    def mark_stale(self, artifact_id: str) -> bool:
        """Mark an artifact as stale."""
        if artifact_id in self._artifacts:
            artifact = self._artifacts[artifact_id]
            updated = artifact.model_copy(update={"is_stale": True})
            self._artifacts[artifact_id] = updated
            return True
        return False

    def clear_stale(self, artifact_id: str) -> bool:
        """Clear stale flag on an artifact."""
        if artifact_id in self._artifacts:
            artifact = self._artifacts[artifact_id]
            updated = artifact.model_copy(update={"is_stale": False})
            self._artifacts[artifact_id] = updated
            return True
        return False


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


class MockArtifactLoader:
    """Mock artifact loader for domain model testing."""

    def __init__(self, registry: MockArtifactRegistry):
        self._registry = registry

    def get_artifact_info(self, artifact_id: str) -> Optional[ArtifactInfo]:
        """Get artifact info by ID."""
        artifact = self._registry.get(artifact_id)
        if artifact is None:
            return None
        return ArtifactInfo(
            id=artifact.id,
            artifact_type=artifact.artifact_type,
            artifact_subtype=None,
        )

    def get_orphan_artifact_ids(self) -> List[str]:
        """Get orphan artifact IDs (none in this mock)."""
        return []


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def artifact_registry():
    """Create a mock artifact registry."""
    return MockArtifactRegistry()


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
# WORKFLOW 1: CREATE ARTIFACT → REFERENCE → COMPLETE
# =============================================================================


class TestCreateArtifactAndCompleteWorkflow:
    """Test workflow: Create artifact, reference in criterion, complete ticket."""

    def test_complete_ticket_with_artifact_criterion(self, artifact_registry):
        """Test completing a ticket that has an artifact criterion."""
        # Step 1: Create artifact
        artifact = Artifact(
            id="art-code-module",
            name="Core Module",
            artifact_type=ArtifactType.CODE,
            paths=["src/core/module.py"],
            provenance=ArtifactProvenance.ticket_created(ticket_id="task-001"),
            file_exists=True,
            content_hash="abc123",
        )
        artifact_registry.add(artifact)

        # Step 2: Create ticket with artifact criterion
        now = datetime.now(timezone.utc)
        criterion = Criterion(
            id="crit-deliverable",
            description="Core module delivered",
            target=ArtifactTarget(
                artifact_id="art-code-module",
                verification=ArtifactVerification.EXISTS,
                artifact_exists=True,  # Simulating verification passed
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
            required=True,
        )
        ticket = Ticket(
            id="task-001",
            name="Implement core module",
            criteria=[criterion],
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        # Step 3: Verify ticket can complete
        can_complete, reasons = ticket.can_complete()
        assert can_complete is True, f"Should be able to complete: {reasons}"

        # Step 4: Complete the ticket
        completed_ticket = ticket.complete()
        assert completed_ticket.status == TicketStatus.COMPLETED

    def test_cannot_complete_without_artifact(self):
        """Test that ticket cannot complete when artifact doesn't exist."""
        now = datetime.now(timezone.utc)
        criterion = Criterion(
            id="crit-deliverable",
            description="Core module delivered",
            target=ArtifactTarget(
                artifact_id="art-missing",
                verification=ArtifactVerification.EXISTS,
                artifact_exists=False,  # Artifact doesn't exist
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
            required=True,
        )
        ticket = Ticket(
            id="task-001",
            name="Implement core module",
            criteria=[criterion],
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        can_complete, reasons = ticket.can_complete()
        assert can_complete is False
        assert len(reasons) > 0


# =============================================================================
# WORKFLOW 2: SOURCE CHANGE → STALE DOCS → BLOCKED
# =============================================================================


class TestSourceChangeStaleDocsWorkflow:
    """Test workflow: Modify source, detect stale docs, block completion."""

    def test_stale_documentation_blocks_completion(self, artifact_registry):
        """Test that stale documentation blocks ticket completion."""
        # Step 1: Create source code artifact
        source = Artifact(
            id="art-api-code",
            name="API Module",
            artifact_type=ArtifactType.CODE,
            paths=["src/api/routes.py"],
            provenance=ArtifactProvenance.ticket_created(ticket_id="task-001"),
            file_exists=True,
            content_hash="original_hash_123",
        )
        artifact_registry.add(source)

        # Step 2: Create documentation artifact that documents the source
        docs = Artifact(
            id="art-api-docs",
            name="API Documentation",
            artifact_type=ArtifactType.DOCUMENTATION,
            paths=["docs/api.md"],
            provenance=ArtifactProvenance.ticket_created(ticket_id="task-001"),
            file_exists=True,
            content_hash="docs_hash_456",
            documents_artifact_id="art-api-code",
            documented_source_hash="original_hash_123",  # Matches source
            is_stale=False,
        )
        artifact_registry.add(docs)

        # Step 3: Simulate source code change (hash changes)
        updated_source = source.model_copy(update={"content_hash": "new_hash_789"})
        artifact_registry.update(updated_source)

        # Step 4: Documentation is now stale (source hash changed)
        # In real system, ImpactAnalyzer would detect this
        artifact_registry.mark_stale("art-api-docs")

        # Step 5: Create ticket with NOT_STALE verification requirement
        now = datetime.now(timezone.utc)
        criterion = Criterion(
            id="crit-docs",
            description="API documentation is current",
            target=ArtifactTarget(
                artifact_id="art-api-docs",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=True,  # Documentation is stale
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
            required=True,
        )
        ticket = Ticket(
            id="task-update-api",
            name="Update API",
            criteria=[criterion],
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        # Step 6: Verify ticket cannot complete due to stale docs
        can_complete, reasons = ticket.can_complete()
        assert can_complete is False
        assert ticket.has_stale_artifacts is True

    def test_impact_analyzer_detects_stale_docs(self, artifact_registry):
        """Test that ImpactAnalyzer detects documentation staleness."""
        # Create source and docs artifacts
        source = Artifact(
            id="art-source",
            name="Source Code",
            artifact_type=ArtifactType.CODE,
            paths=["src/module.py"],
            provenance=ArtifactProvenance.pre_existing(),
            file_exists=True,
            content_hash="hash_v1",
        )
        artifact_registry.add(source)

        docs = Artifact(
            id="art-docs",
            name="Module Docs",
            artifact_type=ArtifactType.DOCUMENTATION,
            paths=["docs/module.md"],
            provenance=ArtifactProvenance.ticket_created(ticket_id="task-001"),
            file_exists=True,
            documents_artifact_id="art-source",
            documented_source_hash="hash_v1",  # Matches
            is_stale=False,
        )
        artifact_registry.add(docs)

        # Create analyzer
        analyzer = ImpactAnalyzer(artifact_registry)

        # Analyze change to source file
        report = analyzer.analyze_file_changes(["src/module.py"])

        # Should identify source artifact
        assert report.total_artifacts_affected >= 1


# =============================================================================
# WORKFLOW 3: UPDATE DOCS → CLEAR STALE → COMPLETE
# =============================================================================


class TestUpdateDocsClearStaleWorkflow:
    """Test workflow: Update docs, clear stale flag, complete ticket."""

    def test_update_docs_enables_completion(self, artifact_registry):
        """Test that updating docs allows ticket completion."""
        # Step 1: Start with stale documentation
        docs = Artifact(
            id="art-stale-docs",
            name="Stale Docs",
            artifact_type=ArtifactType.DOCUMENTATION,
            paths=["docs/readme.md"],
            provenance=ArtifactProvenance.ticket_created(ticket_id="task-001"),
            file_exists=True,
            is_stale=True,  # Currently stale
        )
        artifact_registry.add(docs)

        # Step 2: Create ticket that requires non-stale docs
        now = datetime.now(timezone.utc)
        criterion = Criterion(
            id="crit-docs-current",
            description="Documentation is current",
            target=ArtifactTarget(
                artifact_id="art-stale-docs",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=True,  # Reflects current stale state
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
            required=True,
        )
        ticket = Ticket(
            id="task-docs",
            name="Update documentation",
            criteria=[criterion],
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        # Step 3: Cannot complete while docs are stale
        can_complete_before, _ = ticket.can_complete()
        assert can_complete_before is False

        # Step 4: Simulate updating documentation (clear stale flag)
        artifact_registry.clear_stale("art-stale-docs")

        # Step 5: Update ticket criterion to reflect new state
        updated_criterion = Criterion(
            id="crit-docs-current",
            description="Documentation is current",
            target=ArtifactTarget(
                artifact_id="art-stale-docs",
                verification=ArtifactVerification.NOT_STALE,
                artifact_exists=True,
                artifact_is_stale=False,  # No longer stale
            ),
            blocks_transition_to=TicketStatus.COMPLETED,
            required=True,
        )
        updated_ticket = ticket.model_copy(update={"criteria": [updated_criterion]})

        # Step 6: Now ticket can complete
        can_complete_after, reasons = updated_ticket.can_complete()
        assert can_complete_after is True, f"Should be able to complete: {reasons}"


# =============================================================================
# HIERARCHY INTEGRATION TESTS
# =============================================================================


class TestHierarchyArtifactIntegration:
    """Test artifact integration across ticket hierarchy."""

    def test_documentation_health_across_hierarchy(
        self, artifact_registry, ticket_loader
    ):
        """Test documentation health propagates through hierarchy."""
        # Configure loaders
        artifact_loader = MockArtifactLoader(artifact_registry)
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        # Create roadmap
        roadmap = RoadmapTicket(id="roadmap-1", name="Test Roadmap")
        ticket_loader.add_ticket(roadmap)

        # Create track
        track = TrackTicket(
            id="track-1",
            name="Test Track",
            parent_ref="roadmap-1",
            roadmap_id="roadmap-1",
        )
        ticket_loader.add_ticket(track)

        # Create sprint
        sprint = SprintTicket(
            id="sprint-1",
            name="Test Sprint",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
        )
        ticket_loader.add_ticket(sprint)

        # Create task with stale documentation criterion
        task = TaskTicket(
            id="task-1",
            name="Task with Stale Docs",
            parent_ref="sprint-1",
            sprint_id="sprint-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            estimated_tokens=1000,
            criteria=[
                Criterion(
                    id="crit-stale-doc",
                    description="Documentation criterion",
                    target=ArtifactTarget(
                        artifact_id="art-doc-1",
                        verification=ArtifactVerification.NOT_STALE,
                        artifact_exists=True,
                        artifact_is_stale=True,  # Stale!
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                    required=True,
                ),
            ],
        )
        ticket_loader.add_ticket(task)

        # Verify task has stale documentation
        assert task.has_stale_documentation is True
        assert task.documentation_health == DocumentationHealth.CRITICAL

    def test_artifact_aggregation_across_hierarchy(
        self, artifact_registry, ticket_loader
    ):
        """Test artifacts aggregate from children to parents."""
        # Configure loaders
        artifact_loader = MockArtifactLoader(artifact_registry)
        RoadmapTicket.set_artifact_loader(artifact_loader)
        HierarchicalTicket.set_loader(ticket_loader)

        # Add test artifacts to registry
        for i in range(3):
            artifact = Artifact(
                id=f"art-{i}",
                name=f"Artifact {i}",
                artifact_type=ArtifactType.CODE,
                paths=[f"src/file{i}.py"],
                provenance=ArtifactProvenance.pre_existing(),
                file_exists=True,
            )
            artifact_registry.add(artifact)

        # Create hierarchy
        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Roadmap",
            criteria=[
                Criterion(
                    id="crit-roadmap-art",
                    description="Roadmap artifact",
                    target=ArtifactTarget(artifact_id="art-0", artifact_exists=True),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-track-ref",
                    description="Track ref",
                    target=CompletableTarget(
                        completable_id="track-1",
                        status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(roadmap)

        track = TrackTicket(
            id="track-1",
            name="Track",
            parent_ref="roadmap-1",
            roadmap_id="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-track-art",
                    description="Track artifact",
                    target=ArtifactTarget(artifact_id="art-1", artifact_exists=True),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-sprint-ref",
                    description="Sprint ref",
                    target=CompletableTarget(
                        completable_id="sprint-1",
                        status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(track)

        sprint = SprintTicket(
            id="sprint-1",
            name="Sprint",
            parent_ref="track-1",
            track_id="track-1",
            roadmap_id="roadmap-1",
            criteria=[
                Criterion(
                    id="crit-sprint-art",
                    description="Sprint artifact",
                    target=ArtifactTarget(artifact_id="art-2", artifact_exists=True),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_loader.add_ticket(sprint)

        # Verify aggregation
        all_artifacts = roadmap.all_referenced_artifacts
        assert "art-0" in all_artifacts
        assert "art-1" in all_artifacts
        assert "art-2" in all_artifacts


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestArtifactWorkflowEdgeCases:
    """Test edge cases in artifact workflows."""

    def test_empty_artifact_criteria(self):
        """Test ticket with no artifact criteria."""
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            id="task-no-artifacts",
            name="Task without artifacts",
            criteria=[],
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        assert ticket.artifact_criteria == []
        assert ticket.referenced_artifact_ids == []
        assert ticket.has_stale_artifacts is False

    def test_multiple_artifact_criteria(self, artifact_registry):
        """Test ticket with multiple artifact criteria."""
        # Create artifacts
        for i in range(3):
            artifact = Artifact(
                id=f"art-multi-{i}",
                name=f"Multi Artifact {i}",
                artifact_type=ArtifactType.CODE,
                paths=[f"src/multi{i}.py"],
                provenance=ArtifactProvenance.pre_existing(),
                file_exists=True,
            )
            artifact_registry.add(artifact)

        # Create ticket with multiple artifact criteria
        now = datetime.now(timezone.utc)
        criteria = [
            Criterion(
                id=f"crit-multi-{i}",
                description=f"Criterion {i}",
                target=ArtifactTarget(
                    artifact_id=f"art-multi-{i}",
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            )
            for i in range(3)
        ]

        ticket = Ticket(
            id="task-multi",
            name="Multi-artifact task",
            criteria=criteria,
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        assert len(ticket.artifact_criteria) == 3
        assert set(ticket.referenced_artifact_ids) == {
            "art-multi-0",
            "art-multi-1",
            "art-multi-2",
        }

    def test_mixed_verification_modes(self):
        """Test ticket with different verification modes."""
        now = datetime.now(timezone.utc)
        criteria = [
            Criterion(
                id="crit-exists",
                description="Exists check",
                target=ArtifactTarget(
                    artifact_id="art-exists",
                    verification=ArtifactVerification.EXISTS,
                    artifact_exists=True,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-not-stale",
                description="Not stale check",
                target=ArtifactTarget(
                    artifact_id="art-not-stale",
                    verification=ArtifactVerification.NOT_STALE,
                    artifact_exists=True,
                    artifact_is_stale=False,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            Criterion(
                id="crit-hash",
                description="Hash check",
                target=ArtifactTarget(
                    artifact_id="art-hash",
                    verification=ArtifactVerification.HASH_UNCHANGED,
                    artifact_exists=True,
                    artifact_hash="expected_hash",
                    expected_hash="expected_hash",
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]

        ticket = Ticket(
            id="task-mixed",
            name="Mixed verification task",
            criteria=criteria,
            status=TicketStatus.IN_PROGRESS,
            created_at=now - timedelta(hours=1),
            started_at=now,
        )

        assert len(ticket.artifact_criteria) == 3
        can_complete, _ = ticket.can_complete()
        assert can_complete is True
