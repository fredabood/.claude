"""
Tests for relationship entity models (Triangle Model).

Tests the relationship models, enums, and helper methods for the
Context System V2 Triangle Model.
"""

import pytest
from datetime import datetime, timezone, timedelta

from vibey.roadmap.models.relationships import (
    ReferenceType,
    AssociationSource,
    ChangeType,
    FileOverlapSignal,
    MessageRefSignal,
    ManualSignal,
    LinkSignals,
    TicketCommitLink,
    TicketArtifactAssociation,
    CommitArtifactChange,
)


class TestReferenceTypeEnum:
    """Test ReferenceType enum."""

    def test_task_reference_value(self):
        """Test TASK_REFERENCE value."""
        assert ReferenceType.TASK_REFERENCE.value == "task_reference"

    def test_completion_claim_value(self):
        """Test COMPLETION_CLAIM value."""
        assert ReferenceType.COMPLETION_CLAIM.value == "completion_claim"

    def test_string_type(self):
        """Test enum is string-based."""
        assert isinstance(ReferenceType.TASK_REFERENCE, str)
        assert isinstance(ReferenceType.COMPLETION_CLAIM, str)


class TestAssociationSourceEnum:
    """Test AssociationSource enum."""

    def test_plan_reference_value(self):
        """Test PLAN_REFERENCE value."""
        assert AssociationSource.PLAN_REFERENCE.value == "plan_reference"

    def test_runtime_tracking_value(self):
        """Test RUNTIME_TRACKING value."""
        assert AssociationSource.RUNTIME_TRACKING.value == "runtime_tracking"

    def test_commit_bootstrap_value(self):
        """Test COMMIT_BOOTSTRAP value."""
        assert AssociationSource.COMMIT_BOOTSTRAP.value == "commit_bootstrap"

    def test_manual_value(self):
        """Test MANUAL value."""
        assert AssociationSource.MANUAL.value == "manual"

    def test_criterion_target_value(self):
        """Test CRITERION_TARGET value."""
        assert AssociationSource.CRITERION_TARGET.value == "criterion_target"

    def test_string_type(self):
        """Test enum is string-based."""
        assert isinstance(AssociationSource.PLAN_REFERENCE, str)


class TestChangeTypeEnum:
    """Test ChangeType enum."""

    def test_added_value(self):
        """Test ADDED value."""
        assert ChangeType.ADDED.value == "added"

    def test_modified_value(self):
        """Test MODIFIED value."""
        assert ChangeType.MODIFIED.value == "modified"

    def test_deleted_value(self):
        """Test DELETED value."""
        assert ChangeType.DELETED.value == "deleted"

    def test_renamed_value(self):
        """Test RENAMED value."""
        assert ChangeType.RENAMED.value == "renamed"

    def test_string_type(self):
        """Test enum is string-based."""
        assert isinstance(ChangeType.ADDED, str)


class TestFileOverlapSignal:
    """Test FileOverlapSignal model."""

    def test_basic_construction(self):
        """Test basic FileOverlapSignal construction."""
        signal = FileOverlapSignal(
            matched=True,
            overlapping_artifact_ids=["01ART001", "01ART002"],
            confidence=0.75,
        )
        assert signal.matched is True
        assert len(signal.overlapping_artifact_ids) == 2
        assert signal.confidence == 0.75

    def test_no_match(self):
        """Test FileOverlapSignal with no match."""
        signal = FileOverlapSignal(
            matched=False,
            overlapping_artifact_ids=[],
            confidence=0.0,
        )
        assert signal.matched is False
        assert signal.overlapping_artifact_ids == []
        assert signal.confidence == 0.0

    def test_default_overlapping_artifact_ids(self):
        """Test default for overlapping_artifact_ids."""
        signal = FileOverlapSignal(matched=True, confidence=1.0)
        assert signal.overlapping_artifact_ids == []

    def test_immutable(self):
        """Test that FileOverlapSignal is immutable."""
        signal = FileOverlapSignal(matched=True, confidence=0.5)
        with pytest.raises(Exception):  # Pydantic will raise ValidationError
            signal.matched = False


class TestMessageRefSignal:
    """Test MessageRefSignal model."""

    def test_basic_construction(self):
        """Test basic MessageRefSignal construction."""
        signal = MessageRefSignal(
            matched=True,
            ticket_ids=["01TASK001", "01TASK002"],
            reference_type=ReferenceType.TASK_REFERENCE,
            confidence=1.0,
        )
        assert signal.matched is True
        assert len(signal.ticket_ids) == 2
        assert signal.reference_type == ReferenceType.TASK_REFERENCE
        assert signal.confidence == 1.0

    def test_completion_claim(self):
        """Test MessageRefSignal with completion claim."""
        signal = MessageRefSignal(
            matched=True,
            ticket_ids=["01TASK001"],
            reference_type=ReferenceType.COMPLETION_CLAIM,
        )
        assert signal.reference_type == ReferenceType.COMPLETION_CLAIM

    def test_default_values(self):
        """Test default values."""
        signal = MessageRefSignal(matched=False)
        assert signal.ticket_ids == []
        assert signal.reference_type is None
        assert signal.confidence == 1.0

    def test_immutable(self):
        """Test that MessageRefSignal is immutable."""
        signal = MessageRefSignal(matched=False)
        with pytest.raises(Exception):
            signal.matched = True


class TestManualSignal:
    """Test ManualSignal model."""

    def test_basic_construction(self):
        """Test basic ManualSignal construction."""
        now = datetime.now(timezone.utc)
        signal = ManualSignal(
            matched=True,
            linked_by="user@example.com",
            linked_at=now,
            confidence=1.0,
        )
        assert signal.matched is True
        assert signal.linked_by == "user@example.com"
        assert signal.linked_at == now
        assert signal.confidence == 1.0

    def test_default_values(self):
        """Test default values."""
        signal = ManualSignal(matched=True)
        assert signal.linked_by is None
        assert signal.linked_at is None
        assert signal.confidence == 1.0

    def test_immutable(self):
        """Test that ManualSignal is immutable."""
        signal = ManualSignal(matched=True)
        with pytest.raises(Exception):
            signal.linked_by = "changed"


class TestLinkSignals:
    """Test LinkSignals container model."""

    def test_basic_construction(self):
        """Test basic LinkSignals construction."""
        signals = LinkSignals()
        assert signals.file_overlap is None
        assert signals.message_ref is None
        assert signals.manual is None

    def test_with_all_signals(self):
        """Test with all signals present."""
        file_signal = FileOverlapSignal(matched=True, confidence=0.8)
        msg_signal = MessageRefSignal(matched=True, confidence=1.0)
        manual_signal = ManualSignal(matched=True, confidence=1.0)

        signals = LinkSignals(
            file_overlap=file_signal,
            message_ref=msg_signal,
            manual=manual_signal,
        )
        assert signals.file_overlap is not None
        assert signals.message_ref is not None
        assert signals.manual is not None

    def test_has_any_signal_true(self):
        """Test has_any_signal returns True when signals present."""
        signals = LinkSignals(
            message_ref=MessageRefSignal(matched=True, confidence=1.0),
        )
        assert signals.has_any_signal() is True

    def test_has_any_signal_false_no_signals(self):
        """Test has_any_signal returns False with no signals."""
        signals = LinkSignals()
        assert signals.has_any_signal() is False

    def test_has_any_signal_false_not_matched(self):
        """Test has_any_signal returns False when signals not matched."""
        signals = LinkSignals(
            message_ref=MessageRefSignal(matched=False),
            file_overlap=FileOverlapSignal(matched=False, confidence=0.0),
        )
        assert signals.has_any_signal() is False

    def test_compute_aggregate_confidence_single(self):
        """Test compute_aggregate_confidence with single signal."""
        signals = LinkSignals(
            file_overlap=FileOverlapSignal(matched=True, confidence=0.75),
        )
        assert signals.compute_aggregate_confidence() == 0.75

    def test_compute_aggregate_confidence_multiple(self):
        """Test compute_aggregate_confidence returns max."""
        signals = LinkSignals(
            file_overlap=FileOverlapSignal(matched=True, confidence=0.5),
            message_ref=MessageRefSignal(matched=True, confidence=1.0),
        )
        assert signals.compute_aggregate_confidence() == 1.0

    def test_compute_aggregate_confidence_none(self):
        """Test compute_aggregate_confidence returns 0 with no signals."""
        signals = LinkSignals()
        assert signals.compute_aggregate_confidence() == 0.0

    def test_compute_aggregate_confidence_unmatched(self):
        """Test compute_aggregate_confidence ignores unmatched signals."""
        signals = LinkSignals(
            file_overlap=FileOverlapSignal(matched=False, confidence=0.9),
            message_ref=MessageRefSignal(matched=True, confidence=0.5),
        )
        assert signals.compute_aggregate_confidence() == 0.5


class TestTicketCommitLink:
    """Test TicketCommitLink model."""

    @pytest.fixture
    def basic_signals(self):
        """Create basic link signals."""
        return LinkSignals(
            message_ref=MessageRefSignal(
                matched=True,
                ticket_ids=["01TASK001"],
                reference_type=ReferenceType.TASK_REFERENCE,
                confidence=1.0,
            ),
        )

    def test_basic_construction(self, basic_signals):
        """Test basic TicketCommitLink construction."""
        now = datetime.now(timezone.utc)
        link = TicketCommitLink(
            ticket_id="01TASK001",
            commit_sha="abc123def456789012345678901234567890abcd",
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=basic_signals,
            aggregate_confidence=1.0,
            linked_at=now,
            link_source="pre_commit_hook",
        )
        assert link.ticket_id == "01TASK001"
        assert link.commit_sha.startswith("abc123")
        assert link.reference_type == ReferenceType.TASK_REFERENCE
        assert link.aggregate_confidence == 1.0
        assert link.link_source == "pre_commit_hook"

    def test_create_factory(self, basic_signals):
        """Test create factory method."""
        link = TicketCommitLink.create(
            ticket_id="01TASK001",
            commit_sha="abc123",
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=basic_signals,
            link_source="post_commit",
        )
        assert link.ticket_id == "01TASK001"
        assert link.commit_sha == "abc123"
        assert link.aggregate_confidence == 1.0  # computed from signals
        assert link.linked_at is not None
        assert link.link_source == "post_commit"

    def test_create_with_completion_claim(self):
        """Test create with completion claim reference type."""
        signals = LinkSignals(
            message_ref=MessageRefSignal(
                matched=True,
                ticket_ids=["01TASK001"],
                reference_type=ReferenceType.COMPLETION_CLAIM,
            ),
        )
        link = TicketCommitLink.create(
            ticket_id="01TASK001",
            commit_sha="abc123",
            reference_type=ReferenceType.COMPLETION_CLAIM,
            signals=signals,
            link_source="pre_commit_hook",
        )
        assert link.reference_type == ReferenceType.COMPLETION_CLAIM

    def test_immutable(self, basic_signals):
        """Test that TicketCommitLink is immutable."""
        link = TicketCommitLink.create(
            ticket_id="01TASK001",
            commit_sha="abc123",
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=basic_signals,
            link_source="manual",
        )
        with pytest.raises(Exception):
            link.ticket_id = "01TASK002"


class TestTicketArtifactAssociation:
    """Test TicketArtifactAssociation model."""

    def test_basic_construction(self):
        """Test basic TicketArtifactAssociation construction."""
        now = datetime.now(timezone.utc)
        assoc = TicketArtifactAssociation(
            ticket_id="01TASK001",
            artifact_id="01ART001",
            association_source=AssociationSource.PLAN_REFERENCE,
            added_at=now,
            added_by="planner",
        )
        assert assoc.ticket_id == "01TASK001"
        assert assoc.artifact_id == "01ART001"
        assert assoc.association_source == AssociationSource.PLAN_REFERENCE
        assert assoc.added_at == now
        assert assoc.added_by == "planner"

    def test_create_factory(self):
        """Test create factory method."""
        assoc = TicketArtifactAssociation.create(
            ticket_id="01TASK001",
            artifact_id="01ART001",
            source=AssociationSource.RUNTIME_TRACKING,
            added_by="ai_agent",
        )
        assert assoc.ticket_id == "01TASK001"
        assert assoc.artifact_id == "01ART001"
        assert assoc.association_source == AssociationSource.RUNTIME_TRACKING
        assert assoc.added_at is not None
        assert assoc.added_by == "ai_agent"

    def test_create_without_added_by(self):
        """Test create without added_by."""
        assoc = TicketArtifactAssociation.create(
            ticket_id="01TASK001",
            artifact_id="01ART001",
            source=AssociationSource.COMMIT_BOOTSTRAP,
        )
        assert assoc.added_by is None

    def test_all_association_sources(self):
        """Test all association sources work."""
        for source in AssociationSource:
            assoc = TicketArtifactAssociation.create(
                ticket_id="01TASK001",
                artifact_id="01ART001",
                source=source,
            )
            assert assoc.association_source == source

    def test_immutable(self):
        """Test that TicketArtifactAssociation is immutable."""
        assoc = TicketArtifactAssociation.create(
            ticket_id="01TASK001",
            artifact_id="01ART001",
            source=AssociationSource.MANUAL,
        )
        with pytest.raises(Exception):
            assoc.artifact_id = "01ART002"


class TestCommitArtifactChange:
    """Test CommitArtifactChange model."""

    def test_basic_construction(self):
        """Test basic CommitArtifactChange construction."""
        now = datetime.now(timezone.utc)
        change = CommitArtifactChange(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.MODIFIED,
            lines_added=50,
            lines_removed=10,
            recorded_at=now,
        )
        assert change.commit_sha == "abc123"
        assert change.artifact_id == "01ART001"
        assert change.change_type == ChangeType.MODIFIED
        assert change.lines_added == 50
        assert change.lines_removed == 10

    def test_create_factory(self):
        """Test create factory method."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.ADDED,
            lines_added=100,
        )
        assert change.commit_sha == "abc123"
        assert change.artifact_id == "01ART001"
        assert change.change_type == ChangeType.ADDED
        assert change.lines_added == 100
        assert change.lines_removed is None
        assert change.recorded_at is not None

    def test_create_for_rename(self):
        """Test create for rename operation."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.RENAMED,
            previous_path="old/path/file.py",
        )
        assert change.change_type == ChangeType.RENAMED
        assert change.previous_path == "old/path/file.py"

    def test_net_lines_positive(self):
        """Test net_lines with more additions."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.MODIFIED,
            lines_added=100,
            lines_removed=50,
        )
        assert change.net_lines == 50

    def test_net_lines_negative(self):
        """Test net_lines with more removals."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.MODIFIED,
            lines_added=10,
            lines_removed=50,
        )
        assert change.net_lines == -40

    def test_net_lines_none(self):
        """Test net_lines when counts not available."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.DELETED,
        )
        assert change.net_lines is None

    def test_net_lines_partial(self):
        """Test net_lines when only one count available."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.MODIFIED,
            lines_added=100,
        )
        assert change.net_lines is None

    def test_all_change_types(self):
        """Test all change types work."""
        for change_type in ChangeType:
            change = CommitArtifactChange.create(
                commit_sha="abc123",
                artifact_id="01ART001",
                change_type=change_type,
            )
            assert change.change_type == change_type

    def test_immutable(self):
        """Test that CommitArtifactChange is immutable."""
        change = CommitArtifactChange.create(
            commit_sha="abc123",
            artifact_id="01ART001",
            change_type=ChangeType.ADDED,
        )
        with pytest.raises(Exception):
            change.change_type = ChangeType.DELETED


class TestTriangleModelIntegration:
    """Integration tests for the Triangle Model."""

    def test_complete_triangle_scenario(self):
        """Test a complete triangle scenario with all three relationships."""
        ticket_id = "01TASK001"
        commit_sha = "abc123def456"
        artifact_id = "01ART001"

        # Create signals for commit-ticket link
        signals = LinkSignals(
            message_ref=MessageRefSignal(
                matched=True,
                ticket_ids=[ticket_id],
                reference_type=ReferenceType.TASK_REFERENCE,
            ),
            file_overlap=FileOverlapSignal(
                matched=True,
                overlapping_artifact_ids=[artifact_id],
                confidence=1.0,
            ),
        )

        # 1. Ticket <-> Commit (TicketCommitLink)
        ticket_commit = TicketCommitLink.create(
            ticket_id=ticket_id,
            commit_sha=commit_sha,
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=signals,
            link_source="pre_commit_hook",
        )

        # 2. Ticket <-> Artifact (TicketArtifactAssociation)
        ticket_artifact = TicketArtifactAssociation.create(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            source=AssociationSource.PLAN_REFERENCE,
        )

        # 3. Commit <-> Artifact (CommitArtifactChange)
        commit_artifact = CommitArtifactChange.create(
            commit_sha=commit_sha,
            artifact_id=artifact_id,
            change_type=ChangeType.MODIFIED,
            lines_added=50,
            lines_removed=10,
        )

        # Verify triangle consistency
        assert ticket_commit.ticket_id == ticket_artifact.ticket_id
        assert ticket_commit.commit_sha == commit_artifact.commit_sha
        assert ticket_artifact.artifact_id == commit_artifact.artifact_id

    def test_multi_ticket_commit(self):
        """Test a commit referencing multiple tickets."""
        commit_sha = "abc123"

        signals = LinkSignals(
            message_ref=MessageRefSignal(
                matched=True,
                ticket_ids=["01TASK001", "01TASK002"],
                reference_type=ReferenceType.TASK_REFERENCE,
            ),
        )

        # Create links for both tickets
        link1 = TicketCommitLink.create(
            ticket_id="01TASK001",
            commit_sha=commit_sha,
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=signals,
            link_source="pre_commit_hook",
        )
        link2 = TicketCommitLink.create(
            ticket_id="01TASK002",
            commit_sha=commit_sha,
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=signals,
            link_source="pre_commit_hook",
        )

        # Same commit, different tickets
        assert link1.commit_sha == link2.commit_sha
        assert link1.ticket_id != link2.ticket_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
