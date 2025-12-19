"""
Tests for Relationship Entity Models.

Tests for TicketCommitLink, TicketArtifactAssociation, and CommitArtifactChange
relationship entities that form the triangle model.

Task: 01KCMNDFWS0C2N2FJJBZRR3FC8
Track: Context System V2
Sprint: Sprint 2: Context Implementation
"""

import pytest
from datetime import datetime, timezone

from vibey.roadmap.models.ticket.relationships import (
    # Enums
    ReferenceType,
    ChangeType,
    AssociationSource,
    LinkSource,
    # Signal models
    FileOverlapSignal,
    MessageRefSignal,
    ManualSignal,
    LinkSignals,
    # Relationship entities
    TicketCommitLink,
    TicketArtifactAssociation,
    CommitArtifactChange,
)


# =============================================================================
# ENUM TESTS
# =============================================================================


class TestEnums:
    """Tests for relationship enums."""

    def test_reference_type_values(self):
        """Test ReferenceType enum values."""
        assert ReferenceType.TASK_REFERENCE == "task_reference"
        assert ReferenceType.COMPLETION_CLAIM == "completion_claim"

    def test_change_type_values(self):
        """Test ChangeType enum values."""
        assert ChangeType.ADDED == "added"
        assert ChangeType.MODIFIED == "modified"
        assert ChangeType.DELETED == "deleted"
        assert ChangeType.RENAMED == "renamed"

    def test_association_source_values(self):
        """Test AssociationSource enum values."""
        assert AssociationSource.PLAN_REFERENCE == "plan_reference"
        assert AssociationSource.RUNTIME_TRACKING == "runtime_tracking"
        assert AssociationSource.COMMIT_BOOTSTRAP == "commit_bootstrap"
        assert AssociationSource.MANUAL == "manual"
        assert AssociationSource.CRITERION_TARGET == "criterion_target"

    def test_link_source_values(self):
        """Test LinkSource enum values."""
        assert LinkSource.PRE_COMMIT_HOOK == "pre_commit_hook"
        assert LinkSource.POST_COMMIT == "post_commit"
        assert LinkSource.MANUAL == "manual"
        assert LinkSource.RECONCILIATION == "reconciliation"


# =============================================================================
# SIGNAL MODEL TESTS
# =============================================================================


class TestFileOverlapSignal:
    """Tests for FileOverlapSignal."""

    def test_calculate_confidence_with_overlap(self):
        """Test confidence calculation with overlapping artifacts."""
        signal = FileOverlapSignal(
            overlapping_artifact_ids=["art_1", "art_2"]
        )

        confidence = signal.calculate_confidence(4)

        assert confidence == 0.5
        assert signal.matched is True
        assert signal.confidence == 0.5

    def test_calculate_confidence_no_overlap(self):
        """Test confidence calculation with no overlap."""
        signal = FileOverlapSignal()

        confidence = signal.calculate_confidence(4)

        assert confidence == 0.0
        assert signal.matched is False

    def test_calculate_confidence_empty_commit(self):
        """Test confidence calculation with empty commit."""
        signal = FileOverlapSignal(
            overlapping_artifact_ids=["art_1"]
        )

        confidence = signal.calculate_confidence(0)

        assert confidence == 0.0
        assert signal.matched is False

    def test_calculate_confidence_full_overlap(self):
        """Test confidence calculation with full overlap."""
        signal = FileOverlapSignal(
            overlapping_artifact_ids=["art_1", "art_2", "art_3"]
        )

        confidence = signal.calculate_confidence(3)

        assert confidence == 1.0
        assert signal.matched is True


class TestMessageRefSignal:
    """Tests for MessageRefSignal."""

    def test_default_confidence(self):
        """Test that message refs have high confidence by default."""
        signal = MessageRefSignal(
            matched=True,
            ticket_ids=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            reference_type=ReferenceType.TASK_REFERENCE,
        )

        assert signal.confidence == 1.0

    def test_completion_claim_reference(self):
        """Test completion claim reference type."""
        signal = MessageRefSignal(
            matched=True,
            ticket_ids=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
            reference_type=ReferenceType.COMPLETION_CLAIM,
        )

        assert signal.reference_type == ReferenceType.COMPLETION_CLAIM


class TestManualSignal:
    """Tests for ManualSignal."""

    def test_manual_signal_with_metadata(self):
        """Test manual signal with linked_by and linked_at."""
        now = datetime.now(timezone.utc)
        signal = ManualSignal(
            matched=True,
            linked_by="user@example.com",
            linked_at=now,
        )

        assert signal.matched is True
        assert signal.linked_by == "user@example.com"
        assert signal.linked_at == now
        assert signal.confidence == 1.0


class TestLinkSignals:
    """Tests for combined LinkSignals."""

    def test_aggregate_confidence_single_signal(self):
        """Test aggregate confidence with single signal."""
        signals = LinkSignals(
            message_ref=MessageRefSignal(matched=True, ticket_ids=["01ABC"])
        )

        assert signals.calculate_aggregate_confidence() == 1.0

    def test_aggregate_confidence_multiple_signals(self):
        """Test aggregate confidence takes maximum."""
        file_signal = FileOverlapSignal(overlapping_artifact_ids=["art_1"])
        file_signal.calculate_confidence(4)  # 0.25 confidence

        signals = LinkSignals(
            file_overlap=file_signal,
            message_ref=MessageRefSignal(matched=True, ticket_ids=["01ABC"]),
        )

        # Should take max (1.0 from message_ref)
        assert signals.calculate_aggregate_confidence() == 1.0

    def test_aggregate_confidence_no_signals(self):
        """Test aggregate confidence with no matched signals."""
        signals = LinkSignals()

        assert signals.calculate_aggregate_confidence() == 0.0

    def test_is_matched_property(self):
        """Test is_matched property."""
        signals_no_match = LinkSignals()
        assert signals_no_match.is_matched is False

        signals_with_match = LinkSignals(
            message_ref=MessageRefSignal(matched=True, ticket_ids=["01ABC"])
        )
        assert signals_with_match.is_matched is True


# =============================================================================
# TICKET COMMIT LINK TESTS
# =============================================================================


class TestTicketCommitLink:
    """Tests for TicketCommitLink relationship entity."""

    def test_create_basic_link(self):
        """Test creating a basic ticket-commit link."""
        link = TicketCommitLink(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            commit_sha="abc123def456",
            reference_type=ReferenceType.TASK_REFERENCE,
        )

        assert link.ticket_id == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        assert link.commit_sha == "abc123def456"
        assert link.reference_type == ReferenceType.TASK_REFERENCE
        assert link.link_source == LinkSource.PRE_COMMIT_HOOK

    def test_from_pre_commit_factory(self):
        """Test the from_pre_commit factory method."""
        signals = LinkSignals(
            message_ref=MessageRefSignal(
                matched=True,
                ticket_ids=["01KCMNDFWS0C2N2FJJBZRR3FC8"],
                reference_type=ReferenceType.TASK_REFERENCE,
            )
        )

        link = TicketCommitLink.from_pre_commit(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            commit_sha="abc123",
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=signals,
        )

        assert link.link_source == LinkSource.PRE_COMMIT_HOOK
        assert link.aggregate_confidence == 1.0
        assert link.signals == signals

    def test_from_manual_factory(self):
        """Test the from_manual factory method."""
        link = TicketCommitLink.from_manual(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            commit_sha="abc123",
            linked_by="user@example.com",
        )

        assert link.link_source == LinkSource.MANUAL
        assert link.aggregate_confidence == 1.0
        assert link.signals.manual is not None
        assert link.signals.manual.linked_by == "user@example.com"


# =============================================================================
# TICKET ARTIFACT ASSOCIATION TESTS
# =============================================================================


class TestTicketArtifactAssociation:
    """Tests for TicketArtifactAssociation relationship entity."""

    def test_create_basic_association(self):
        """Test creating a basic ticket-artifact association."""
        assoc = TicketArtifactAssociation(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            artifact_id="01ARTIFACTID123456789AB",
            association_source=AssociationSource.MANUAL,
        )

        assert assoc.ticket_id == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        assert assoc.artifact_id == "01ARTIFACTID123456789AB"
        assert assoc.association_source == AssociationSource.MANUAL

    def test_from_commit_bootstrap_factory(self):
        """Test the from_commit_bootstrap factory method."""
        assoc = TicketArtifactAssociation.from_commit_bootstrap(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            artifact_id="01ARTIFACTID123456789AB",
        )

        assert assoc.association_source == AssociationSource.COMMIT_BOOTSTRAP
        assert assoc.added_by == "pre_commit_hook"

    def test_from_plan_reference_factory(self):
        """Test the from_plan_reference factory method."""
        assoc = TicketArtifactAssociation.from_plan_reference(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            artifact_id="01ARTIFACTID123456789AB",
        )

        assert assoc.association_source == AssociationSource.PLAN_REFERENCE
        assert assoc.added_by == "plan_context"

    def test_from_manual_factory(self):
        """Test the from_manual factory method."""
        assoc = TicketArtifactAssociation.from_manual(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            artifact_id="01ARTIFACTID123456789AB",
            added_by="user@example.com",
        )

        assert assoc.association_source == AssociationSource.MANUAL
        assert assoc.added_by == "user@example.com"


# =============================================================================
# COMMIT ARTIFACT CHANGE TESTS
# =============================================================================


class TestCommitArtifactChange:
    """Tests for CommitArtifactChange relationship entity."""

    def test_create_basic_change(self):
        """Test creating a basic commit-artifact change."""
        change = CommitArtifactChange(
            commit_sha="abc123",
            artifact_id="01ARTIFACTID123456789AB",
            change_type=ChangeType.MODIFIED,
        )

        assert change.commit_sha == "abc123"
        assert change.artifact_id == "01ARTIFACTID123456789AB"
        assert change.change_type == ChangeType.MODIFIED

    def test_from_staged_file_factory(self):
        """Test the from_staged_file factory method."""
        change = CommitArtifactChange.from_staged_file(
            commit_sha="abc123",
            artifact_id="01ARTIFACTID123456789AB",
            change_type=ChangeType.ADDED,
            lines_added=50,
            lines_removed=0,
        )

        assert change.change_type == ChangeType.ADDED
        assert change.lines_added == 50
        assert change.lines_removed == 0

    def test_rename_with_previous_path(self):
        """Test rename change with previous path."""
        change = CommitArtifactChange.from_staged_file(
            commit_sha="abc123",
            artifact_id="01ARTIFACTID123456789AB",
            change_type=ChangeType.RENAMED,
            previous_path="old/path/file.py",
        )

        assert change.change_type == ChangeType.RENAMED
        assert change.previous_path == "old/path/file.py"


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================


class TestSerialization:
    """Tests for model serialization."""

    def test_ticket_commit_link_to_dict(self):
        """Test TicketCommitLink serialization."""
        link = TicketCommitLink(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            commit_sha="abc123",
            reference_type=ReferenceType.TASK_REFERENCE,
        )

        data = link.model_dump()

        assert data["ticket_id"] == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        assert data["commit_sha"] == "abc123"
        assert data["reference_type"] == "task_reference"

    def test_ticket_artifact_association_to_dict(self):
        """Test TicketArtifactAssociation serialization."""
        assoc = TicketArtifactAssociation(
            ticket_id="01KCMNDFWS0C2N2FJJBZRR3FC8",
            artifact_id="01ARTIFACTID123456789AB",
            association_source=AssociationSource.MANUAL,
        )

        data = assoc.model_dump()

        assert data["ticket_id"] == "01KCMNDFWS0C2N2FJJBZRR3FC8"
        assert data["artifact_id"] == "01ARTIFACTID123456789AB"
        assert data["association_source"] == "manual"

    def test_commit_artifact_change_to_dict(self):
        """Test CommitArtifactChange serialization."""
        change = CommitArtifactChange(
            commit_sha="abc123",
            artifact_id="01ARTIFACTID123456789AB",
            change_type=ChangeType.MODIFIED,
            lines_added=10,
            lines_removed=5,
        )

        data = change.model_dump()

        assert data["commit_sha"] == "abc123"
        assert data["artifact_id"] == "01ARTIFACTID123456789AB"
        assert data["change_type"] == "modified"
        assert data["lines_added"] == 10
        assert data["lines_removed"] == 5
