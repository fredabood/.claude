"""
Relationship Entity Models for the Unified Ticket Architecture.

This module defines the three relationship entities that form the triangle model:
- TicketCommitLink: Ticket <-> GitCommit relationship
- TicketArtifactAssociation: Ticket <-> Artifact relationship
- CommitArtifactChange: GitCommit <-> Artifact relationship

These entities enable triangle validation in the pre-commit hook by tracking
all three edges of the Ticket-Commit-Artifact triangle.

Design Reference: Sprint 2 Implementation Plan (Context System V2)
Task: 01KCMNDFWS0C2N2FJJBZRR3FC8
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================


class ReferenceType(str, Enum):
    """Type of ticket reference in commit message."""

    TASK_REFERENCE = "task_reference"  # Task: marker
    COMPLETION_CLAIM = "completion_claim"  # Completes: marker


class ChangeType(str, Enum):
    """Type of change to an artifact in a commit."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class AssociationSource(str, Enum):
    """How an artifact became associated with a ticket."""

    PLAN_REFERENCE = "plan_reference"  # Pre-work planning
    RUNTIME_TRACKING = "runtime_tracking"  # AI logs during work
    COMMIT_BOOTSTRAP = "commit_bootstrap"  # First commit establishes
    MANUAL = "manual"  # CLI command
    CRITERION_TARGET = "criterion_target"  # FileExistsTarget reference


class LinkSource(str, Enum):
    """Where a commit-ticket link originated."""

    PRE_COMMIT_HOOK = "pre_commit_hook"
    POST_COMMIT = "post_commit"
    MANUAL = "manual"
    RECONCILIATION = "reconciliation"


# =============================================================================
# SIGNAL MODELS
# =============================================================================


class FileOverlapSignal(BaseModel):
    """
    Signal: Commit artifacts match ticket's artifact associations.

    Used for confidence scoring when linking commits to tickets.
    Higher overlap = higher confidence the commit is related.
    """

    matched: bool = False
    overlapping_artifact_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.0

    def calculate_confidence(self, commit_artifact_count: int) -> float:
        """
        Calculate confidence based on overlap ratio.

        Confidence = overlap_count / commit_artifact_count
        """
        if commit_artifact_count == 0:
            self.confidence = 0.0
            self.matched = False
            return 0.0

        self.confidence = len(self.overlapping_artifact_ids) / commit_artifact_count
        self.matched = self.confidence > 0
        return self.confidence


class MessageRefSignal(BaseModel):
    """
    Signal: Ticket ID found in commit message.

    Always has confidence 1.0 when matched (explicit reference).
    """

    matched: bool = False
    ticket_ids: List[str] = Field(default_factory=list)
    reference_type: Optional[ReferenceType] = None
    confidence: float = 1.0  # Always 1.0 when matched


class ManualSignal(BaseModel):
    """
    Signal: User explicitly linked commit to ticket.

    Always has confidence 1.0 when matched (human decision).
    """

    matched: bool = False
    linked_by: Optional[str] = None
    linked_at: Optional[datetime] = None
    confidence: float = 1.0  # Always 1.0 when manually linked


class LinkSignals(BaseModel):
    """
    Combined signals for commit-ticket relationship.

    Used to track how a commit became linked to a ticket.
    Multiple signals can be present (e.g., message ref AND file overlap).
    """

    file_overlap: Optional[FileOverlapSignal] = None
    message_ref: Optional[MessageRefSignal] = None
    manual: Optional[ManualSignal] = None

    def calculate_aggregate_confidence(self) -> float:
        """
        Calculate aggregate confidence from all signals.

        Strategy: Use highest confidence among signals.
        Message ref and manual are always 1.0 when matched.
        File overlap varies based on overlap ratio.
        """
        confidences = []

        if self.file_overlap and self.file_overlap.matched:
            confidences.append(self.file_overlap.confidence)
        if self.message_ref and self.message_ref.matched:
            confidences.append(self.message_ref.confidence)
        if self.manual and self.manual.matched:
            confidences.append(self.manual.confidence)

        return max(confidences) if confidences else 0.0

    @property
    def is_matched(self) -> bool:
        """Check if any signal indicates a match."""
        return (
            (self.file_overlap is not None and self.file_overlap.matched)
            or (self.message_ref is not None and self.message_ref.matched)
            or (self.manual is not None and self.manual.matched)
        )


# =============================================================================
# RELATIONSHIP ENTITIES
# =============================================================================


class TicketCommitLink(BaseModel):
    """
    Relationship: Ticket <-> GitCommit.

    Represents the edge between a ticket and a git commit.
    Created when commits reference tickets via Task: or Completes: markers,
    or when file overlap is detected.
    """

    ticket_id: str = Field(description="ULID of the linked ticket")
    commit_sha: str = Field(description="SHA of the linked commit")
    reference_type: ReferenceType = Field(
        description="Type of reference (task or completion)"
    )
    signals: LinkSignals = Field(
        default_factory=LinkSignals,
        description="Signals that created this link"
    )
    aggregate_confidence: float = Field(
        default=0.0,
        description="Aggregate confidence from all signals"
    )
    linked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the link was created"
    )
    link_source: LinkSource = Field(
        default=LinkSource.PRE_COMMIT_HOOK,
        description="Where this link originated"
    )

    @classmethod
    def from_pre_commit(
        cls,
        ticket_id: str,
        commit_sha: str,
        reference_type: ReferenceType,
        signals: LinkSignals,
    ) -> "TicketCommitLink":
        """Create link from pre-commit hook."""
        return cls(
            ticket_id=ticket_id,
            commit_sha=commit_sha,
            reference_type=reference_type,
            signals=signals,
            aggregate_confidence=signals.calculate_aggregate_confidence(),
            linked_at=datetime.now(timezone.utc),
            link_source=LinkSource.PRE_COMMIT_HOOK,
        )

    @classmethod
    def from_manual(
        cls,
        ticket_id: str,
        commit_sha: str,
        linked_by: str,
    ) -> "TicketCommitLink":
        """Create link from manual CLI command."""
        signals = LinkSignals(
            manual=ManualSignal(
                matched=True,
                linked_by=linked_by,
                linked_at=datetime.now(timezone.utc),
            )
        )
        return cls(
            ticket_id=ticket_id,
            commit_sha=commit_sha,
            reference_type=ReferenceType.TASK_REFERENCE,
            signals=signals,
            aggregate_confidence=1.0,
            linked_at=datetime.now(timezone.utc),
            link_source=LinkSource.MANUAL,
        )


class TicketArtifactAssociation(BaseModel):
    """
    Relationship: Ticket <-> Artifact.

    Represents the edge between a ticket and an artifact.
    Created when artifacts are associated with tickets through:
    - Planning references (plan context)
    - Runtime tracking (AI working)
    - Commit bootstrap (first commit)
    - Manual CLI commands
    - Criterion targets (FileExistsTarget)
    """

    ticket_id: str = Field(description="ULID of the associated ticket")
    artifact_id: str = Field(description="ULID of the associated artifact")
    association_source: AssociationSource = Field(
        description="How this association was created"
    )
    added_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the association was created"
    )
    added_by: Optional[str] = Field(
        default=None,
        description="Who/what added this association"
    )

    @classmethod
    def from_commit_bootstrap(
        cls,
        ticket_id: str,
        artifact_id: str,
    ) -> "TicketArtifactAssociation":
        """Create association when commit first links artifact to ticket."""
        return cls(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            association_source=AssociationSource.COMMIT_BOOTSTRAP,
            added_at=datetime.now(timezone.utc),
            added_by="pre_commit_hook",
        )

    @classmethod
    def from_plan_reference(
        cls,
        ticket_id: str,
        artifact_id: str,
    ) -> "TicketArtifactAssociation":
        """Create association from planning phase."""
        return cls(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            association_source=AssociationSource.PLAN_REFERENCE,
            added_at=datetime.now(timezone.utc),
            added_by="plan_context",
        )

    @classmethod
    def from_manual(
        cls,
        ticket_id: str,
        artifact_id: str,
        added_by: str,
    ) -> "TicketArtifactAssociation":
        """Create association from CLI command."""
        return cls(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            association_source=AssociationSource.MANUAL,
            added_at=datetime.now(timezone.utc),
            added_by=added_by,
        )


class CommitArtifactChange(BaseModel):
    """
    Relationship: GitCommit <-> Artifact.

    Represents the edge between a commit and an artifact.
    Records what change was made to an artifact in a commit.
    """

    commit_sha: str = Field(description="SHA of the commit")
    artifact_id: str = Field(description="ULID of the changed artifact")
    change_type: ChangeType = Field(description="Type of change made")
    previous_path: Optional[str] = Field(
        default=None,
        description="Previous path for renamed files"
    )
    lines_added: Optional[int] = Field(
        default=None,
        description="Number of lines added"
    )
    lines_removed: Optional[int] = Field(
        default=None,
        description="Number of lines removed"
    )
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this change was recorded"
    )

    @classmethod
    def from_staged_file(
        cls,
        commit_sha: str,
        artifact_id: str,
        change_type: ChangeType,
        lines_added: Optional[int] = None,
        lines_removed: Optional[int] = None,
        previous_path: Optional[str] = None,
    ) -> "CommitArtifactChange":
        """Create change record from staged file analysis."""
        return cls(
            commit_sha=commit_sha,
            artifact_id=artifact_id,
            change_type=change_type,
            previous_path=previous_path,
            lines_added=lines_added,
            lines_removed=lines_removed,
            recorded_at=datetime.now(timezone.utc),
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ReferenceType",
    "ChangeType",
    "AssociationSource",
    "LinkSource",
    # Signal models
    "FileOverlapSignal",
    "MessageRefSignal",
    "ManualSignal",
    "LinkSignals",
    # Relationship entities
    "TicketCommitLink",
    "TicketArtifactAssociation",
    "CommitArtifactChange",
]
