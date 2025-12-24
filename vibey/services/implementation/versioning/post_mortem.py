"""
Post-mortem stage versioning for task implementation.

This module provides versioning functionality for the POST_MORTEM stage
of ticket implementation, tracking post-mortem evolution, reviews, and
knowledge base integration.

Key Features:
- Version post-mortems at key lifecycle points (initial, revision, final)
- Track metadata (status, learnings count, reviewer)
- Compute deltas to show evolution over time
- Support linking to knowledge base

Design Reference:
- Implementation Mode Track Sprint 3
- Content Versioning System
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ulid import ULID

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.post_mortem import PostMortem

from vibey.services.implementation.versioning.core import (
    ContentVersion,
    ContentVersioner,
    VersionStage,
)

logger = logging.getLogger(__name__)


# =============================================================================
# POST-MORTEM VERSION METADATA
# =============================================================================


@dataclass
class PostMortemVersionMetadata:
    """
    Metadata for post-mortem versions.

    Tracks the status and state of a post-mortem through its lifecycle.

    Attributes:
        pm_status: Current status (draft, reviewed, finalized, archived)
        learnings_count: Number of lessons learned captured
        recommendations_count: Number of recommendations made
        reviewed_by: Reviewer identifier (if reviewed)
        finalized_at: When the post-mortem was finalized
        linked_to_knowledge_base: Whether linked to org knowledge base

    Example:
        >>> metadata = PostMortemVersionMetadata(
        ...     pm_status="reviewed",
        ...     learnings_count=5,
        ...     recommendations_count=3,
        ...     reviewed_by="senior-engineer",
        ... )
    """

    pm_status: str  # draft, reviewed, finalized, archived
    learnings_count: int
    recommendations_count: int
    reviewed_by: Optional[str] = None
    finalized_at: Optional[datetime] = None
    linked_to_knowledge_base: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pm_status": self.pm_status,
            "learnings_count": self.learnings_count,
            "recommendations_count": self.recommendations_count,
            "reviewed_by": self.reviewed_by,
            "finalized_at": (
                self.finalized_at.isoformat() if self.finalized_at else None
            ),
            "linked_to_knowledge_base": self.linked_to_knowledge_base,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostMortemVersionMetadata":
        """Create from dictionary."""
        finalized_at = data.get("finalized_at")
        if isinstance(finalized_at, str):
            finalized_at = datetime.fromisoformat(finalized_at.replace("Z", "+00:00"))

        return cls(
            pm_status=data.get("pm_status", "draft"),
            learnings_count=data.get("learnings_count", 0),
            recommendations_count=data.get("recommendations_count", 0),
            reviewed_by=data.get("reviewed_by"),
            finalized_at=finalized_at,
            linked_to_knowledge_base=data.get("linked_to_knowledge_base", False),
        )


# =============================================================================
# POST-MORTEM DELTA
# =============================================================================


@dataclass
class PostMortemDelta:
    """
    Delta between two post-mortem versions.

    Captures what changed between two versions of a post-mortem,
    useful for tracking evolution and review history.

    Attributes:
        from_version: Version ID of the earlier version
        to_version: Version ID of the later version
        timestamp: When the delta was computed
        author: Who made the changes
        changes: List of human-readable change descriptions
        added_learnings: Learnings added in the newer version
        removed_learnings: Learnings removed from the older version
        similarity_ratio: Content similarity (0.0 to 1.0, 1.0 = identical)

    Example:
        >>> delta = PostMortemDelta(
        ...     from_version="01KCZF73PX...",
        ...     to_version="01KCZF73QY...",
        ...     timestamp=datetime.now(timezone.utc),
        ...     author="claude-code",
        ...     changes=["Added 2 new learnings", "Updated summary"],
        ...     added_learnings=["Always test edge cases"],
        ...     removed_learnings=[],
        ...     similarity_ratio=0.85,
        ... )
    """

    from_version: str
    to_version: str
    timestamp: datetime
    author: str
    changes: List[str] = field(default_factory=list)
    added_learnings: List[str] = field(default_factory=list)
    removed_learnings: List[str] = field(default_factory=list)
    similarity_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "timestamp": self.timestamp.isoformat(),
            "author": self.author,
            "changes": self.changes,
            "added_learnings": self.added_learnings,
            "removed_learnings": self.removed_learnings,
            "similarity_ratio": self.similarity_ratio,
        }


# =============================================================================
# POST-MORTEM VERSIONER
# =============================================================================


class PostMortemVersioner:
    """
    Versioning for the POST_MORTEM stage of ticket implementation.

    Provides specialized versioning operations for post-mortems,
    including lifecycle management, review tracking, and knowledge
    base integration.

    Attributes:
        versioner: The core ContentVersioner for storage

    Example:
        >>> from pathlib import Path
        >>> versioner = ContentVersioner(Path(".vibey/roadmap/versions"))
        >>> pm_versioner = PostMortemVersioner(versioner)
        >>> version = pm_versioner.version_initial_post_mortem(
        ...     ticket=task,
        ...     post_mortem=pm,
        ...     author="claude-code",
        ... )
    """

    def __init__(self, versioner: ContentVersioner):
        """
        Initialize PostMortemVersioner.

        Args:
            versioner: The core ContentVersioner for storage operations.
        """
        self.versioner = versioner

    # =========================================================================
    # VERSION CREATION
    # =========================================================================

    def version_initial_post_mortem(
        self,
        ticket: "HierarchicalTicket",
        post_mortem: "PostMortem",
        author: str,
    ) -> ContentVersion:
        """
        Create initial post-mortem version.

        Called when a post-mortem is first created for a completed task.
        Sets the status to "draft" and captures initial learnings.

        Args:
            ticket: The HierarchicalTicket the post-mortem belongs to
            post_mortem: The PostMortem object to version
            author: Who is creating this version

        Returns:
            The created ContentVersion
        """
        # Extract content and metadata from post-mortem
        content = post_mortem.to_markdown()
        metadata = self._extract_pm_metadata(post_mortem)
        metadata["pm_status"] = "draft"

        # Create version with POST_MORTEM stage
        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.POST_MORTEM,
            content=content,
            author=author,
            change_summary="Initial post-mortem creation",
            metadata=metadata,
        )

    def version_post_mortem_revision(
        self,
        ticket: "HierarchicalTicket",
        revised: "PostMortem",
        author: str,
        reason: str,
    ) -> ContentVersion:
        """
        Version post-mortem revision.

        Called when a post-mortem is updated with new learnings,
        corrections, or additional analysis.

        Args:
            ticket: The HierarchicalTicket the post-mortem belongs to
            revised: The revised PostMortem object
            author: Who made the revision
            reason: Why the revision was made

        Returns:
            The created ContentVersion
        """
        content = revised.to_markdown()
        metadata = self._extract_pm_metadata(revised)

        # Preserve status unless explicitly changed
        current = self.get_current_post_mortem(ticket.id)
        if current and current.metadata.get("pm_status"):
            # Keep existing status if not finalized
            current_status = current.metadata.get("pm_status", "draft")
            if current_status != "finalized":
                metadata["pm_status"] = current_status

        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.POST_MORTEM,
            content=content,
            author=author,
            change_summary=f"Revision: {reason}",
            metadata=metadata,
        )

    def version_post_mortem_finalization(
        self,
        ticket: "HierarchicalTicket",
        final: "PostMortem",
        author: str,
    ) -> ContentVersion:
        """
        Create final archived version.

        Called when a post-mortem is finalized and ready for archival.
        Sets the status to "finalized" and records the finalization timestamp.

        Args:
            ticket: The HierarchicalTicket the post-mortem belongs to
            final: The final PostMortem object
            author: Who is finalizing this

        Returns:
            The created ContentVersion
        """
        content = final.to_markdown()
        metadata = self._extract_pm_metadata(final)
        metadata["pm_status"] = "finalized"
        metadata["finalized_at"] = datetime.now(timezone.utc).isoformat()

        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.POST_MORTEM,
            content=content,
            author=author,
            change_summary="Post-mortem finalized and archived",
            metadata=metadata,
        )

    # =========================================================================
    # VERSION RETRIEVAL
    # =========================================================================

    def get_current_post_mortem(self, ticket_id: str) -> Optional[ContentVersion]:
        """
        Get current post-mortem content.

        Args:
            ticket_id: ID of the ticket

        Returns:
            Current ContentVersion for post-mortem, or None if none exists
        """
        return self.versioner.get_current(ticket_id, VersionStage.POST_MORTEM)

    def get_post_mortem_history(self, ticket_id: str) -> List[ContentVersion]:
        """
        Get all post-mortem versions for ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of ContentVersions, sorted by timestamp (oldest first)
        """
        return self.versioner.get_history(ticket_id, VersionStage.POST_MORTEM)

    # =========================================================================
    # EVOLUTION TRACKING
    # =========================================================================

    def get_post_mortem_evolution(self, ticket_id: str) -> List[PostMortemDelta]:
        """
        Show how post-mortem evolved over time.

        Computes deltas between consecutive versions to show the
        progression of the post-mortem analysis.

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of PostMortemDeltas showing evolution between versions
        """
        history = self.get_post_mortem_history(ticket_id)

        if len(history) < 2:
            return []

        deltas = []
        for i in range(len(history) - 1):
            delta = self._compute_delta(history[i], history[i + 1])
            deltas.append(delta)

        return deltas

    # =========================================================================
    # STATUS MANAGEMENT
    # =========================================================================

    def mark_as_reviewed(
        self,
        ticket: "HierarchicalTicket",
        reviewer: str,
    ) -> ContentVersion:
        """
        Mark current version as reviewed.

        Updates the post-mortem status to "reviewed" and records
        the reviewer information.

        Args:
            ticket: The HierarchicalTicket
            reviewer: Who reviewed the post-mortem

        Returns:
            New ContentVersion with reviewed status
        """
        current = self.get_current_post_mortem(ticket.id)
        if current is None:
            raise ValueError(f"No post-mortem exists for ticket {ticket.id}")

        # Update metadata with review information
        metadata = dict(current.metadata)
        metadata["pm_status"] = "reviewed"
        metadata["reviewed_by"] = reviewer

        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.POST_MORTEM,
            content=current.content,
            author=reviewer,
            change_summary=f"Marked as reviewed by {reviewer}",
            metadata=metadata,
        )

    def link_to_knowledge_base(
        self,
        ticket: "HierarchicalTicket",
        author: str,
    ) -> ContentVersion:
        """
        Mark post-mortem as linked to knowledge base.

        Records that the learnings from this post-mortem have been
        integrated into the organization's knowledge base.

        Args:
            ticket: The HierarchicalTicket
            author: Who linked the post-mortem

        Returns:
            New ContentVersion with knowledge base linkage
        """
        current = self.get_current_post_mortem(ticket.id)
        if current is None:
            raise ValueError(f"No post-mortem exists for ticket {ticket.id}")

        # Update metadata with knowledge base linkage
        metadata = dict(current.metadata)
        metadata["linked_to_knowledge_base"] = True

        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.POST_MORTEM,
            content=current.content,
            author=author,
            change_summary="Linked to organization knowledge base",
            metadata=metadata,
        )

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _extract_pm_metadata(self, post_mortem: "PostMortem") -> Dict[str, Any]:
        """
        Extract metadata from post-mortem object.

        Extracts relevant counts and status information from the
        PostMortem dataclass.

        Args:
            post_mortem: The PostMortem to extract metadata from

        Returns:
            Dictionary of metadata suitable for version storage
        """
        # Count learnings and recommendations
        learnings_count = len(post_mortem.lessons_learned)
        recommendations_count = len(post_mortem.what_worked) + len(
            post_mortem.what_didnt_work
        )

        return {
            "pm_status": "draft",
            "learnings_count": learnings_count,
            "recommendations_count": recommendations_count,
            "task_id": post_mortem.task_id,
            "completed_at": post_mortem.completed_at.isoformat(),
            "duration_seconds": post_mortem.duration.total_seconds(),
            "tokens_used": post_mortem.tokens_used,
            "accomplishments_count": len(post_mortem.accomplishments),
            "discoveries_count": len(post_mortem.discoveries),
            "files_modified_count": len(post_mortem.files_modified),
            "commits_count": len(post_mortem.commits),
            "bugs_logged_count": len(post_mortem.bugs_logged),
        }

    def _compute_delta(
        self,
        v1: ContentVersion,
        v2: ContentVersion,
    ) -> PostMortemDelta:
        """
        Compute delta between two versions.

        Uses SequenceMatcher to compute content similarity and
        identifies changes in learnings.

        Args:
            v1: Earlier version
            v2: Later version

        Returns:
            PostMortemDelta capturing the differences
        """
        # Compute similarity ratio using SequenceMatcher
        matcher = SequenceMatcher(None, v1.content, v2.content)
        similarity_ratio = matcher.ratio()

        # Identify changes in learnings
        v1_learnings = self._extract_learnings_from_content(v1.content)
        v2_learnings = self._extract_learnings_from_content(v2.content)

        added_learnings = [l for l in v2_learnings if l not in v1_learnings]
        removed_learnings = [l for l in v1_learnings if l not in v2_learnings]

        # Build change summary list
        changes = []
        if added_learnings:
            changes.append(f"Added {len(added_learnings)} learning(s)")
        if removed_learnings:
            changes.append(f"Removed {len(removed_learnings)} learning(s)")

        # Compare metadata for status changes
        v1_status = v1.metadata.get("pm_status", "draft")
        v2_status = v2.metadata.get("pm_status", "draft")
        if v1_status != v2_status:
            changes.append(f"Status changed from {v1_status} to {v2_status}")

        # Check for reviewer changes
        v2_reviewer = v2.metadata.get("reviewed_by")
        if v2_reviewer and not v1.metadata.get("reviewed_by"):
            changes.append(f"Reviewed by {v2_reviewer}")

        # Check for knowledge base linkage
        if v2.metadata.get("linked_to_knowledge_base") and not v1.metadata.get(
            "linked_to_knowledge_base"
        ):
            changes.append("Linked to knowledge base")

        # Add change summary from version if available
        if v2.change_summary:
            changes.append(v2.change_summary)

        return PostMortemDelta(
            from_version=v1.version_id,
            to_version=v2.version_id,
            timestamp=v2.timestamp,
            author=v2.author,
            changes=changes,
            added_learnings=added_learnings,
            removed_learnings=removed_learnings,
            similarity_ratio=similarity_ratio,
        )

    def _extract_learnings_from_content(self, content: str) -> List[str]:
        """
        Extract lessons learned from markdown content.

        Parses the post-mortem markdown to find the lessons learned
        section and extract individual learnings.

        Args:
            content: Markdown content of the post-mortem

        Returns:
            List of learning strings
        """
        learnings = []
        in_lessons_section = False

        for line in content.split("\n"):
            line = line.strip()

            # Check for section header
            if line.startswith("## Lessons Learned"):
                in_lessons_section = True
                continue
            elif line.startswith("## ") and in_lessons_section:
                # Reached next section, stop parsing
                break

            # Extract list items in lessons section
            if in_lessons_section and line.startswith("- "):
                learning = line[2:].strip()
                # Skip placeholder text
                if not learning.startswith("_"):
                    learnings.append(learning)

        return learnings


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PostMortemDelta",
    "PostMortemVersioner",
    "PostMortemVersionMetadata",
]
