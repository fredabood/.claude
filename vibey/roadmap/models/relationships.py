"""
Relationship Entity Models - Triangle Model

This module defines the three relationship entities that form the Triangle Model
for tracking relationships between Tickets, Commits, and Artifacts.

The Triangle Model:
                         +-------------+
                         |   Ticket    |
                         +-------------+
                        /               \
                       /                 \
          TicketCommitLink          TicketArtifactAssociation
                     /                     \
                    /                       \
        +-------------+               +-------------+
        |  GitCommit  |---------------|  Artifact   |
        +-------------+               +-------------+
                    CommitArtifactChange

Design Note:
This module uses Pydantic BaseModel (not dataclasses) because:
- These are relationship entities that need rich validation
- Signals have complex nested structures requiring type coercion
- JSON serialization/deserialization is a common operation
- These models integrate with the Context System V2 which may involve
  user-provided data through commit message parsing

Reference: DESIGN_DECISIONS.md in Sprint 0 planning

Version: 1.0 (Context System V2)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ReferenceType(str, Enum):
    """Type of reference from a commit to a ticket.

    TASK_REFERENCE: Commit mentions a task (Task: line) - work was done on it
    COMPLETION_CLAIM: Commit claims to complete a task (Completes: line) - triggers criteria check
    """

    TASK_REFERENCE = "task_reference"
    COMPLETION_CLAIM = "completion_claim"


class AssociationSource(str, Enum):
    """How an artifact became associated with a ticket.

    PLAN_REFERENCE: Referenced in plan context before work started
    RUNTIME_TRACKING: AI logged file access via MCP during work
    COMMIT_BOOTSTRAP: First commit with message ref established the association
    MANUAL: User explicitly linked via CLI command
    CRITERION_TARGET: FileExistsTarget in a criterion references this artifact
    """

    PLAN_REFERENCE = "plan_reference"
    RUNTIME_TRACKING = "runtime_tracking"
    COMMIT_BOOTSTRAP = "commit_bootstrap"
    MANUAL = "manual"
    CRITERION_TARGET = "criterion_target"


class ChangeType(str, Enum):
    """Type of change made to an artifact in a commit.

    ADDED: New artifact created
    MODIFIED: Existing artifact content changed
    DELETED: Artifact removed
    RENAMED: Artifact moved/renamed (previous_path will be set)
    """

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


# =============================================================================
# Signal Models
# =============================================================================


class FileOverlapSignal(BaseModel):
    """Signal based on file/artifact overlap between commit and ticket.

    When a commit touches files that are associated with a ticket,
    this creates a file overlap signal for linking.

    Attributes:
        matched: Whether any overlap was detected
        overlapping_artifact_ids: List of artifact IDs that overlap
        confidence: Calculated as len(overlap) / len(commit_artifacts)
    """

    matched: bool
    overlapping_artifact_ids: List[str] = Field(default_factory=list)
    confidence: float

    class Config:
        """Pydantic model configuration."""

        frozen = True


class MessageRefSignal(BaseModel):
    """Signal based on explicit ticket reference in commit message.

    When a commit message contains Task: or Completes: lines,
    this creates a message reference signal.

    Attributes:
        matched: Whether any ticket reference was found in message
        ticket_ids: List of ticket IDs referenced
        reference_type: Type of reference (TASK_REFERENCE or COMPLETION_CLAIM)
        confidence: Always 1.0 for explicit references
    """

    matched: bool
    ticket_ids: List[str] = Field(default_factory=list)
    reference_type: Optional[ReferenceType] = None
    confidence: float = 1.0

    class Config:
        """Pydantic model configuration."""

        frozen = True


class ManualSignal(BaseModel):
    """Signal based on manual/explicit user linking.

    When a user explicitly links a commit to a ticket via CLI,
    this creates a manual signal.

    Attributes:
        matched: Whether a manual link exists
        linked_by: Who created the link (user identifier)
        linked_at: When the link was created
        confidence: Always 1.0 for manual links
    """

    matched: bool
    linked_by: Optional[str] = None
    linked_at: Optional[datetime] = None
    confidence: float = 1.0

    class Config:
        """Pydantic model configuration."""

        frozen = True


class LinkSignals(BaseModel):
    """Container for all signals that contribute to a commit-ticket link.

    A TicketCommitLink can be established through multiple signals.
    This container holds all detected signals for analysis.

    Attributes:
        file_overlap: Signal from file/artifact overlap detection
        message_ref: Signal from commit message parsing
        manual: Signal from explicit user linking
    """

    file_overlap: Optional[FileOverlapSignal] = None
    message_ref: Optional[MessageRefSignal] = None
    manual: Optional[ManualSignal] = None

    class Config:
        """Pydantic model configuration."""

        frozen = True

    def has_any_signal(self) -> bool:
        """Check if any signal is present and matched."""
        return any(
            [
                self.file_overlap and self.file_overlap.matched,
                self.message_ref and self.message_ref.matched,
                self.manual and self.manual.matched,
            ]
        )

    def compute_aggregate_confidence(self) -> float:
        """Compute aggregate confidence from all signals.

        Uses max confidence from matched signals.
        Returns 0.0 if no signals matched.
        """
        confidences = []
        if self.file_overlap and self.file_overlap.matched:
            confidences.append(self.file_overlap.confidence)
        if self.message_ref and self.message_ref.matched:
            confidences.append(self.message_ref.confidence)
        if self.manual and self.manual.matched:
            confidences.append(self.manual.confidence)

        return max(confidences) if confidences else 0.0


# =============================================================================
# Relationship Entity Models
# =============================================================================


class TicketCommitLink(BaseModel):
    """Ticket <-> GitCommit relationship entity.

    Represents a link between a ticket (task) and a git commit.
    Links can be established through message references, file overlap,
    or manual user linking.

    This is one edge of the Triangle Model.

    Attributes:
        ticket_id: The ticket/task ID (ULID)
        commit_sha: The full git commit SHA
        reference_type: How the commit references the ticket
        signals: All signals that contributed to this link
        aggregate_confidence: Combined confidence score (0.0 to 1.0)
        linked_at: When this link was created
        link_source: Where the link originated (pre_commit_hook, post_commit, manual)
    """

    ticket_id: str
    commit_sha: str
    reference_type: ReferenceType
    signals: LinkSignals
    aggregate_confidence: float
    linked_at: datetime
    link_source: str  # pre_commit_hook | post_commit | manual

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @classmethod
    def create(
        cls,
        ticket_id: str,
        commit_sha: str,
        reference_type: ReferenceType,
        signals: LinkSignals,
        link_source: str,
    ) -> "TicketCommitLink":
        """Create a new TicketCommitLink with computed fields.

        Args:
            ticket_id: The ticket/task ID
            commit_sha: The git commit SHA
            reference_type: Type of reference
            signals: The link signals
            link_source: Where the link originated

        Returns:
            A new TicketCommitLink instance
        """
        return cls(
            ticket_id=ticket_id,
            commit_sha=commit_sha,
            reference_type=reference_type,
            signals=signals,
            aggregate_confidence=signals.compute_aggregate_confidence(),
            linked_at=datetime.now(timezone.utc),
            link_source=link_source,
        )


class TicketArtifactAssociation(BaseModel):
    """Ticket <-> Artifact relationship entity.

    Represents an association between a ticket and an artifact.
    Artifacts can be associated through plan references, runtime tracking,
    commit bootstrapping, manual linking, or criterion targets.

    This is one edge of the Triangle Model.

    Attributes:
        ticket_id: The ticket/task ID (ULID)
        artifact_id: The artifact ID (ULID)
        association_source: How this association was created
        added_at: When this association was created
        added_by: Who/what created this association (optional)
    """

    ticket_id: str
    artifact_id: str
    association_source: AssociationSource
    added_at: datetime
    added_by: Optional[str] = None

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @classmethod
    def create(
        cls,
        ticket_id: str,
        artifact_id: str,
        source: AssociationSource,
        added_by: Optional[str] = None,
    ) -> "TicketArtifactAssociation":
        """Create a new TicketArtifactAssociation.

        Args:
            ticket_id: The ticket/task ID
            artifact_id: The artifact ID
            source: How this association was created
            added_by: Who/what created this association

        Returns:
            A new TicketArtifactAssociation instance
        """
        return cls(
            ticket_id=ticket_id,
            artifact_id=artifact_id,
            association_source=source,
            added_at=datetime.now(timezone.utc),
            added_by=added_by,
        )


class CommitArtifactChange(BaseModel):
    """GitCommit <-> Artifact relationship entity.

    Represents a change made to an artifact by a commit.
    Records what type of change was made and additional metrics.

    This is one edge of the Triangle Model.

    Attributes:
        commit_sha: The git commit SHA
        artifact_id: The artifact ID (ULID)
        change_type: Type of change (added, modified, deleted, renamed)
        previous_path: For renames, the path before the rename
        lines_added: Number of lines added (if available)
        lines_removed: Number of lines removed (if available)
        recorded_at: When this change was recorded
    """

    commit_sha: str
    artifact_id: str
    change_type: ChangeType
    previous_path: Optional[str] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None
    recorded_at: datetime

    class Config:
        """Pydantic model configuration."""

        frozen = True

    @classmethod
    def create(
        cls,
        commit_sha: str,
        artifact_id: str,
        change_type: ChangeType,
        previous_path: Optional[str] = None,
        lines_added: Optional[int] = None,
        lines_removed: Optional[int] = None,
    ) -> "CommitArtifactChange":
        """Create a new CommitArtifactChange.

        Args:
            commit_sha: The git commit SHA
            artifact_id: The artifact ID
            change_type: Type of change
            previous_path: For renames, the original path
            lines_added: Number of lines added
            lines_removed: Number of lines removed

        Returns:
            A new CommitArtifactChange instance
        """
        return cls(
            commit_sha=commit_sha,
            artifact_id=artifact_id,
            change_type=change_type,
            previous_path=previous_path,
            lines_added=lines_added,
            lines_removed=lines_removed,
            recorded_at=datetime.now(timezone.utc),
        )

    @property
    def net_lines(self) -> Optional[int]:
        """Calculate net line change (added - removed).

        Returns:
            Net line change, or None if line counts not available
        """
        if self.lines_added is None or self.lines_removed is None:
            return None
        return self.lines_added - self.lines_removed
