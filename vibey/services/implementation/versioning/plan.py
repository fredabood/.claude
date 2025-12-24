"""
Plan stage versioning for task implementation.

This module provides versioning capabilities specific to the PLAN stage
of task implementation. It builds on the core ContentVersioner to add
plan-specific functionality:

- Plan status tracking (draft, review, approved, executing)
- Criteria count and file planning metadata
- Diffing between plan versions
- Pre-execution snapshots
- Plan rollback support

Usage:
    from vibey.services.implementation.versioning import (
        PlanVersioner,
        PlanVersionMetadata,
        PlanDiff,
    )
    from pathlib import Path

    # Initialize with core versioner
    versioner = ContentVersioner(Path(".vibey/roadmap/versions"))
    plan_versioner = PlanVersioner(versioner)

    # Create initial plan version
    version = plan_versioner.version_plan_creation(
        ticket=task,
        plan="# Implementation Plan\n...",
        author="claude-code",
    )

    # Create revision
    revision = plan_versioner.version_plan_revision(
        ticket=task,
        revised_plan="# Updated Plan\n...",
        author="claude-code",
        reason="Scope adjustment based on review",
    )

    # Get diff between versions
    diff = plan_versioner.get_plan_diff(
        ticket_id=task.id,
        from_version=version.version_id,
        to_version=revision.version_id,
    )

Design Reference:
- Context System V2 Architecture
- Implementation Mode Track Sprint 6
- Task: Implement PlanVersioner for plan stage versioning
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import unified_diff
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

from vibey.services.implementation.versioning.core import (
    ContentVersion,
    ContentVersioner,
    VersionStage,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PlanVersionMetadata:
    """
    Metadata for plan versions.

    Captures plan-specific information that helps track the state
    and progress of a plan through its lifecycle.

    Attributes:
        plan_status: Current status (draft, review, approved, executing)
        criteria_count: Number of acceptance criteria in the plan
        estimated_tokens: Estimated tokens for implementation
        files_planned: List of files mentioned in the plan
        reviewer: ID of reviewer (if in review/approved status)
        approval_timestamp: When the plan was approved

    Example:
        >>> metadata = PlanVersionMetadata(
        ...     plan_status="approved",
        ...     criteria_count=5,
        ...     estimated_tokens=10000,
        ...     files_planned=["vibey/services/foo.py"],
        ... )
    """

    plan_status: str  # draft, review, approved, executing
    criteria_count: int
    estimated_tokens: Optional[int] = None
    files_planned: List[str] = field(default_factory=list)
    reviewer: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan_status": self.plan_status,
            "criteria_count": self.criteria_count,
            "estimated_tokens": self.estimated_tokens,
            "files_planned": self.files_planned,
            "reviewer": self.reviewer,
            "approval_timestamp": (
                self.approval_timestamp.isoformat()
                if self.approval_timestamp
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanVersionMetadata":
        """Create from dictionary."""
        approval_ts = data.get("approval_timestamp")
        if isinstance(approval_ts, str):
            approval_ts = datetime.fromisoformat(approval_ts.replace("Z", "+00:00"))

        return cls(
            plan_status=data.get("plan_status", "draft"),
            criteria_count=data.get("criteria_count", 0),
            estimated_tokens=data.get("estimated_tokens"),
            files_planned=data.get("files_planned", []),
            reviewer=data.get("reviewer"),
            approval_timestamp=approval_ts,
        )


@dataclass
class PlanDiff:
    """
    Diff between two plan versions.

    Provides a structured view of changes between plan versions,
    including line-level changes and section-level summaries.

    Attributes:
        from_version: Source version ID
        to_version: Target version ID
        added_lines: Lines added in the new version
        removed_lines: Lines removed from the old version
        changed_sections: Section headers that were modified
        unified_diff: Standard unified diff format string

    Example:
        >>> diff = plan_versioner.get_plan_diff(
        ...     ticket_id="01ABC...",
        ...     from_version="01XYZ...",
        ...     to_version="01DEF...",
        ... )
        >>> print(f"Added: {len(diff.added_lines)} lines")
        >>> print(f"Removed: {len(diff.removed_lines)} lines")
    """

    from_version: str
    to_version: str
    added_lines: List[str]
    removed_lines: List[str]
    changed_sections: List[str]
    unified_diff: str

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes between versions."""
        return bool(self.added_lines or self.removed_lines)

    @property
    def summary(self) -> str:
        """Get a human-readable summary of changes."""
        if not self.has_changes:
            return "No changes"

        parts = []
        if self.added_lines:
            parts.append(f"+{len(self.added_lines)} lines")
        if self.removed_lines:
            parts.append(f"-{len(self.removed_lines)} lines")
        if self.changed_sections:
            parts.append(f"{len(self.changed_sections)} sections changed")

        return ", ".join(parts)


# =============================================================================
# PLAN VERSIONER
# =============================================================================


class PlanVersioner:
    """
    Versioning for the PLAN stage of ticket implementation.

    PlanVersioner provides plan-specific versioning operations built
    on top of the core ContentVersioner. It handles:

    - Initial plan creation with metadata extraction
    - Plan revisions with change tracking
    - Pre-execution snapshots for audit trail
    - Diffing between plan versions
    - Plan rollback to previous versions

    Attributes:
        versioner: Core ContentVersioner instance for storage

    Example:
        >>> versioner = ContentVersioner(Path(".vibey/roadmap/versions"))
        >>> plan_versioner = PlanVersioner(versioner)
        >>>
        >>> # Create initial plan
        >>> version = plan_versioner.version_plan_creation(
        ...     ticket=task,
        ...     plan="# Plan\n...",
        ...     author="claude-code",
        ... )
        >>>
        >>> # Get current plan
        >>> current_plan = plan_versioner.get_current_plan(task.id)
    """

    def __init__(self, versioner: ContentVersioner):
        """
        Initialize PlanVersioner.

        Args:
            versioner: Core ContentVersioner instance for storage operations
        """
        self.versioner = versioner

    # =========================================================================
    # VERSION CREATION
    # =========================================================================

    def version_plan_creation(
        self,
        ticket: "HierarchicalTicket",
        plan: str,
        author: str,
    ) -> ContentVersion:
        """
        Create initial plan version.

        Called when:
        - Task plan first generated
        - Plan created manually

        Args:
            ticket: The HierarchicalTicket being planned
            plan: Full plan content as markdown string
            author: Agent ID or user creating the plan

        Returns:
            ContentVersion with the created plan version
        """
        # Extract plan metadata
        metadata = self._extract_plan_metadata(plan, ticket)
        metadata["plan_status"] = "draft"
        metadata["version_type"] = "creation"

        version = self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.PLAN,
            content=plan,
            author=author,
            change_summary="Initial plan creation",
            metadata=metadata,
        )

        logger.info(f"Created initial plan version {version.version_id} for {ticket.id}")

        return version

    def version_plan_revision(
        self,
        ticket: "HierarchicalTicket",
        revised_plan: str,
        author: str,
        reason: str,
    ) -> ContentVersion:
        """
        Create version for plan revision.

        Called when:
        - Plan refined based on feedback
        - Scope adjusted
        - Approach changed

        Args:
            ticket: The HierarchicalTicket being replanned
            revised_plan: Updated plan content
            author: Agent ID or user making the revision
            reason: Explanation for why the plan was revised

        Returns:
            ContentVersion with the revision
        """
        # Extract updated metadata
        metadata = self._extract_plan_metadata(revised_plan, ticket)
        metadata["plan_status"] = "draft"  # Revisions reset to draft
        metadata["version_type"] = "revision"
        metadata["revision_reason"] = reason

        version = self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.PLAN,
            content=revised_plan,
            author=author,
            change_summary=f"Plan revision: {reason}",
            metadata=metadata,
        )

        logger.info(
            f"Created plan revision {version.version_id} for {ticket.id}: {reason}"
        )

        return version

    def version_pre_execution_snapshot(
        self,
        ticket: "HierarchicalTicket",
        author: str,
    ) -> ContentVersion:
        """
        Create final plan snapshot before execution.

        Captures:
        - Approved plan
        - All acceptance criteria
        - Estimated resources
        - Dependencies confirmed

        This creates an immutable record of the plan state at the moment
        execution begins, useful for audit trail and post-mortem analysis.

        Args:
            ticket: The HierarchicalTicket about to be executed
            author: Agent ID or user creating the snapshot

        Returns:
            ContentVersion with the pre-execution snapshot

        Raises:
            ValueError: If no current plan exists for the ticket
        """
        # Get current plan
        current = self.versioner.get_current(ticket.id, VersionStage.PLAN)
        if current is None:
            raise ValueError(f"No plan exists for ticket {ticket.id}")

        # Extract metadata with approved status
        metadata = self._extract_plan_metadata(current.content, ticket)
        metadata["plan_status"] = "executing"
        metadata["version_type"] = "pre_execution_snapshot"
        metadata["execution_started_at"] = datetime.now(timezone.utc).isoformat()

        # Add ticket state at execution start
        metadata["ticket_state"] = {
            "status": str(ticket.status.value) if hasattr(ticket.status, "value") else str(ticket.status),
            "criteria_count": len(ticket.criteria),
            "dependencies": [dep.description for dep in ticket.dependencies] if hasattr(ticket, "dependencies") else [],
        }

        version = self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.PLAN,
            content=current.content,
            author=author,
            change_summary="Pre-execution snapshot",
            metadata=metadata,
        )

        logger.info(
            f"Created pre-execution snapshot {version.version_id} for {ticket.id}"
        )

        return version

    # =========================================================================
    # PLAN DIFFING
    # =========================================================================

    def get_plan_diff(
        self,
        ticket_id: str,
        from_version: str,
        to_version: str,
    ) -> PlanDiff:
        """
        Generate diff between two plan versions.

        Shows:
        - Added sections
        - Removed sections
        - Changed content

        Args:
            ticket_id: ID of the ticket
            from_version: Version ID to compare from (older)
            to_version: Version ID to compare to (newer)

        Returns:
            PlanDiff with detailed change information

        Raises:
            ValueError: If either version is not found
        """
        # Get both versions
        from_ver = self.versioner.get_version(ticket_id, VersionStage.PLAN, from_version)
        to_ver = self.versioner.get_version(ticket_id, VersionStage.PLAN, to_version)

        if from_ver is None:
            raise ValueError(f"Version {from_version} not found for ticket {ticket_id}")
        if to_ver is None:
            raise ValueError(f"Version {to_version} not found for ticket {ticket_id}")

        # Split content into lines
        from_lines = from_ver.content.splitlines(keepends=True)
        to_lines = to_ver.content.splitlines(keepends=True)

        # Generate unified diff
        diff_lines = list(unified_diff(
            from_lines,
            to_lines,
            fromfile=f"plan-{from_version[:8]}",
            tofile=f"plan-{to_version[:8]}",
            lineterm="",
        ))
        unified = "".join(diff_lines)

        # Extract added and removed lines
        added_lines = []
        removed_lines = []
        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                removed_lines.append(line[1:].strip())

        # Identify changed sections (markdown headers)
        changed_sections = self._find_changed_sections(from_ver.content, to_ver.content)

        return PlanDiff(
            from_version=from_version,
            to_version=to_version,
            added_lines=added_lines,
            removed_lines=removed_lines,
            changed_sections=changed_sections,
            unified_diff=unified,
        )

    # =========================================================================
    # PLAN ROLLBACK
    # =========================================================================

    def rollback_plan(
        self,
        ticket: "HierarchicalTicket",
        to_version: str,
        author: str,
    ) -> ContentVersion:
        """
        Rollback plan to previous version.

        Creates a new version with the content from the specified version.
        This maintains the version history while restoring old content.

        Args:
            ticket: The HierarchicalTicket to rollback
            to_version: Version ID to restore content from
            author: Agent ID or user performing the rollback

        Returns:
            ContentVersion with the new version (containing rolled-back content)

        Raises:
            ValueError: If the target version is not found
        """
        # Get the target version
        target = self.versioner.get_version(ticket.id, VersionStage.PLAN, to_version)
        if target is None:
            raise ValueError(f"Version {to_version} not found for ticket {ticket.id}")

        # Extract metadata (from the old version, but updated)
        metadata = self._extract_plan_metadata(target.content, ticket)
        metadata["plan_status"] = "draft"  # Rollback resets to draft
        metadata["version_type"] = "rollback"
        metadata["rolled_back_from"] = to_version
        metadata["rollback_timestamp"] = datetime.now(timezone.utc).isoformat()

        # Create new version with old content
        version = self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.PLAN,
            content=target.content,
            author=author,
            change_summary=f"Rollback to version {to_version[:8]}",
            metadata=metadata,
        )

        logger.info(
            f"Rolled back plan for {ticket.id} to version {to_version[:8]}, "
            f"created new version {version.version_id}"
        )

        return version

    # =========================================================================
    # PLAN RETRIEVAL
    # =========================================================================

    def get_current_plan(self, ticket_id: str) -> Optional[str]:
        """
        Get current plan content.

        Args:
            ticket_id: ID of the ticket

        Returns:
            Current plan content as string, or None if no plan exists
        """
        current = self.versioner.get_current(ticket_id, VersionStage.PLAN)
        if current is None:
            return None
        return current.content

    def get_plan_history(self, ticket_id: str) -> List[ContentVersion]:
        """
        Get all plan versions for ticket.

        Returns versions sorted by timestamp (oldest first).

        Args:
            ticket_id: ID of the ticket

        Returns:
            List of ContentVersion objects for the PLAN stage
        """
        return self.versioner.get_history(ticket_id, stage=VersionStage.PLAN)

    def get_current_version(self, ticket_id: str) -> Optional[ContentVersion]:
        """
        Get current plan version (full ContentVersion object).

        Args:
            ticket_id: ID of the ticket

        Returns:
            Current ContentVersion or None if no plan exists
        """
        return self.versioner.get_current(ticket_id, VersionStage.PLAN)

    # =========================================================================
    # PLAN STATUS MANAGEMENT
    # =========================================================================

    def update_plan_status(
        self,
        ticket: "HierarchicalTicket",
        new_status: str,
        author: str,
        reviewer: Optional[str] = None,
    ) -> ContentVersion:
        """
        Update plan status without changing content.

        Used to transition plan through review workflow:
        - draft -> review
        - review -> approved
        - approved -> executing

        Args:
            ticket: The HierarchicalTicket
            new_status: New status (draft, review, approved, executing)
            author: Agent ID or user updating status
            reviewer: Reviewer ID (for review/approved transitions)

        Returns:
            ContentVersion with updated metadata

        Raises:
            ValueError: If no current plan exists or invalid status
        """
        valid_statuses = ["draft", "review", "approved", "executing"]
        if new_status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of: {valid_statuses}"
            )

        current = self.versioner.get_current(ticket.id, VersionStage.PLAN)
        if current is None:
            raise ValueError(f"No plan exists for ticket {ticket.id}")

        # Build updated metadata
        metadata = self._extract_plan_metadata(current.content, ticket)
        metadata["plan_status"] = new_status
        metadata["version_type"] = "status_change"
        metadata["previous_status"] = current.metadata.get("plan_status", "unknown")

        if reviewer:
            metadata["reviewer"] = reviewer

        if new_status == "approved":
            metadata["approval_timestamp"] = datetime.now(timezone.utc).isoformat()

        version = self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.PLAN,
            content=current.content,
            author=author,
            change_summary=f"Status changed to {new_status}",
            metadata=metadata,
        )

        logger.info(
            f"Updated plan status for {ticket.id} to {new_status}, "
            f"version {version.version_id}"
        )

        return version

    # =========================================================================
    # METADATA EXTRACTION
    # =========================================================================

    def _extract_plan_metadata(
        self, plan: str, ticket: "HierarchicalTicket"
    ) -> Dict[str, Any]:
        """
        Extract metadata from plan content.

        Parses the plan to extract:
        - Criteria count (from acceptance criteria section)
        - Files mentioned in the plan
        - Token estimates if present
        - Section headings

        Args:
            plan: Plan content as markdown string
            ticket: HierarchicalTicket for additional context

        Returns:
            Dictionary of extracted metadata
        """
        metadata: Dict[str, Any] = {}

        # Count criteria from ticket
        criteria_count = len(ticket.criteria) if hasattr(ticket, "criteria") else 0
        metadata["criteria_count"] = criteria_count

        # Extract files mentioned in the plan
        files_planned = self._extract_files_from_plan(plan)
        metadata["files_planned"] = files_planned

        # Extract token estimates if present
        estimated_tokens = self._extract_token_estimate(plan)
        if estimated_tokens:
            metadata["estimated_tokens"] = estimated_tokens

        # Extract section headings for structure tracking
        sections = self._extract_sections(plan)
        metadata["sections"] = sections

        # Add ticket reference info
        metadata["ticket_name"] = ticket.name if hasattr(ticket, "name") else ""

        return metadata

    def _extract_files_from_plan(self, plan: str) -> List[str]:
        """
        Extract file paths mentioned in the plan.

        Looks for patterns like:
        - `path/to/file.py`
        - vibey/path/file.ts
        - ./src/file.js
        """
        files: List[str] = []

        # Pattern for file paths (with common extensions)
        file_pattern = r'[`"\']?([a-zA-Z0-9_\-./]+\.(py|ts|js|yaml|yml|json|md|txt|sh|toml|cfg|ini))[`"\']?'

        matches = re.findall(file_pattern, plan, re.IGNORECASE)
        for match in matches:
            path = match[0]
            # Filter out URLs and common false positives
            if not path.startswith(("http", "www.", "//")):
                if path not in files:
                    files.append(path)

        return files

    def _extract_token_estimate(self, plan: str) -> Optional[int]:
        """
        Extract token estimate from plan content.

        Looks for patterns like:
        - Estimated tokens: ~5,000
        - Token estimate: 10000
        - **Estimated Input Tokens:** ~5,000
        """
        patterns = [
            r"estimated\s+(?:input\s+)?tokens?[:\s]+[~]?([0-9,]+)",
            r"token\s+estimate[:\s]+[~]?([0-9,]+)",
            r"tokens?[:\s]+(?:approximately\s+)?[~]?([0-9,]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, plan, re.IGNORECASE)
            if match:
                try:
                    # Remove commas and convert to int
                    return int(match.group(1).replace(",", ""))
                except ValueError:
                    continue

        return None

    def _extract_sections(self, plan: str) -> List[str]:
        """
        Extract section headers from plan.

        Returns list of markdown headers found in the plan.
        """
        sections: List[str] = []

        # Match markdown headers (# Header, ## Header, etc.)
        header_pattern = r"^(#{1,6})\s+(.+)$"

        for line in plan.split("\n"):
            match = re.match(header_pattern, line)
            if match:
                header_text = match.group(2).strip()
                sections.append(header_text)

        return sections

    def _find_changed_sections(self, old_content: str, new_content: str) -> List[str]:
        """
        Find section headers that changed between versions.

        Compares sections in both versions and identifies which changed.
        """
        old_sections = set(self._extract_sections(old_content))
        new_sections = set(self._extract_sections(new_content))

        # Sections that were added or removed
        changed = old_sections.symmetric_difference(new_sections)

        # Also check for sections with different content
        header_pattern = r"^(#{1,6})\s+(.+)$"
        old_section_content: Dict[str, str] = {}
        new_section_content: Dict[str, str] = {}

        # Parse old content into sections
        current_section = None
        current_content: List[str] = []
        for line in old_content.split("\n"):
            match = re.match(header_pattern, line)
            if match:
                if current_section:
                    old_section_content[current_section] = "\n".join(current_content)
                current_section = match.group(2).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        if current_section:
            old_section_content[current_section] = "\n".join(current_content)

        # Parse new content into sections
        current_section = None
        current_content = []
        for line in new_content.split("\n"):
            match = re.match(header_pattern, line)
            if match:
                if current_section:
                    new_section_content[current_section] = "\n".join(current_content)
                current_section = match.group(2).strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        if current_section:
            new_section_content[current_section] = "\n".join(current_content)

        # Check for content changes in existing sections
        for section in old_sections & new_sections:
            old = old_section_content.get(section, "")
            new = new_section_content.get(section, "")
            if old.strip() != new.strip():
                changed.add(section)

        return sorted(list(changed))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "PlanVersioner",
    # Data classes
    "PlanDiff",
    "PlanVersionMetadata",
]
