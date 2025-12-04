"""
Layer 1 Ticket class for the unified ticket architecture.

Ticket extends Completable with work-specific semantics:
- Lifecycle (status, timestamps)
- Assignment (agents, priority)
- Work evidence (commits)
- Hierarchy (parent_ref)

Design Principle: Ticket IS a Completable with additional work tracking.
Completion is determined by criteria (inherited from Completable).
Ticket adds work semantics on top.

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from vibey.roadmap.models.ticket.completable import Completable, Criterion
from vibey.roadmap.models.ticket.enums import Priority, TicketStatus
from vibey.roadmap.models.ticket.requirements import Requirement
from vibey.roadmap.models.ticket.support import Progress
from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    CriterionTarget,
    FileExistsTarget,
    ManualTarget,
    TestPassesTarget,
)


class GitCommit(BaseModel):
    """
    A git commit associated with ticket work.

    Tracks commits made during ticket implementation, including
    file changes and artifact links.
    """

    sha: str = Field(description="Full 40-char SHA or abbreviated")
    message: str = Field(description="Commit message")
    date: datetime = Field(description="Commit date")
    author: str = Field(description="Commit author")

    # Platform tracking
    platform: Optional[str] = Field(
        default=None,
        description="Platform that created this commit (claude-code, goose, cursor, etc.)"
    )
    submitted_at: Optional[datetime] = Field(
        default=None,
        description="When commit was recorded in the system"
    )

    # Extracted from message
    completes_tickets: List[str] = Field(
        default_factory=list,
        description="Ticket IDs marked as completed by this commit"
    )

    # File changes
    files_added: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    files_deleted: List[str] = Field(default_factory=list)

    # Artifact links (computed separately)
    creates_artifacts: List[str] = Field(default_factory=list)
    modifies_artifacts: List[str] = Field(default_factory=list)
    deletes_artifacts: List[str] = Field(default_factory=list)

    @property
    def all_changed_files(self) -> List[str]:
        """All files touched by this commit."""
        return self.files_added + self.files_modified + self.files_deleted

    @property
    def all_affected_artifacts(self) -> List[str]:
        """All artifacts affected by this commit."""
        return self.creates_artifacts + self.modifies_artifacts + self.deletes_artifacts


class Ticket(Completable):
    """
    Layer 1: Work item with lifecycle semantics.

    Ticket extends Completable with:
    - Status and lifecycle timestamps
    - Work assignment (agents, priority)
    - Work evidence (commits)
    - Requirement templates for children
    - Parent reference for hierarchy navigation

    Key Principles:
    - Completion is COMPUTED from criteria (inherited from Completable)
    - Dependencies are criteria with blocks_transition_to=IN_PROGRESS
    - Subtasks are criteria with CompletableTarget and blocks_transition_to=COMPLETED
    - All transitions use can_transition_to() as THE deterministic interface
    """

    # Hierarchy
    parent_ref: Optional[str] = Field(
        default=None,
        description="Parent ticket ID (denormalized for O(1) lookup)"
    )

    # Lifecycle
    status: TicketStatus = Field(
        default=TicketStatus.NOT_STARTED,
        description="Current lifecycle status"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When ticket was created"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="When work started (IN_PROGRESS)"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When work completed (COMPLETED)"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When ticket was last updated"
    )

    # Work Assignment
    assigned_agents: List[str] = Field(
        default_factory=list,
        description="Agents assigned to this ticket"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Work priority"
    )

    # Work Evidence
    commits: List[GitCommit] = Field(
        default_factory=list,
        description="Git commits associated with this work"
    )

    # Requirement Templates
    requirements_local: List[Requirement] = Field(
        default_factory=list,
        description="Requirement templates defined on this ticket (cascade to children)"
    )

    # Estimation
    estimated_duration: Optional[str] = Field(
        default=None,
        description="Estimated duration (e.g., '2 weeks', '3 days')"
    )

    # Deferral flag - marks ticket as optional for production
    deferred: bool = Field(
        default=False,
        description="If True, parent can complete without this ticket completing"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @field_validator("started_at")
    @classmethod
    def started_after_created(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate started_at >= created_at."""
        if v is not None and "created_at" in info.data:
            created = info.data["created_at"]
            if v < created:
                raise ValueError("started_at cannot be before created_at")
        return v

    @field_validator("completed_at")
    @classmethod
    def completed_after_started(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate completed_at >= started_at."""
        if v is not None and "started_at" in info.data:
            started = info.data.get("started_at")
            if started is not None and v < started:
                raise ValueError("completed_at cannot be before started_at")
        return v

    @model_validator(mode="after")
    def validate_status_consistency(self) -> "Ticket":
        """Validate status is consistent with timestamps."""
        if self.status == TicketStatus.IN_PROGRESS and self.started_at is None:
            raise ValueError("IN_PROGRESS status requires started_at to be set")
        if self.status == TicketStatus.COMPLETED and self.completed_at is None:
            raise ValueError("COMPLETED status requires completed_at to be set")
        return self

    # =========================================================================
    # HIERARCHY PROPERTIES (computed)
    # =========================================================================

    @computed_field
    @property
    def is_blocked(self) -> bool:
        """
        Check if ticket is blocked from starting.

        A ticket is blocked if any IN_PROGRESS criteria are not met.
        """
        can_start, _ = self.can_start()
        return not can_start

    @computed_field
    @property
    def is_parent(self) -> bool:
        """
        Check if this ticket has children.

        True if any criteria have CompletableTarget.
        """
        return len(self.children) > 0

    @computed_field
    @property
    def is_child(self) -> bool:
        """
        Check if this ticket is a child of another.

        True if parent_ref is set.
        """
        return self.parent_ref is not None

    @computed_field
    @property
    def is_ultimate_parent(self) -> bool:
        """
        Check if this is a root ticket (no parent).

        True for Roadmap tickets.
        """
        return self.is_parent and not self.is_child

    @computed_field
    @property
    def is_ultimate_child(self) -> bool:
        """
        Check if this is a leaf ticket (no children).

        True for Task tickets.
        """
        return self.is_child and not self.is_parent

    @computed_field
    @property
    def is_intermediate(self) -> bool:
        """
        Check if this is an intermediate ticket (has both parent and children).

        True for Track and Sprint tickets.
        """
        return self.is_parent and self.is_child

    # =========================================================================
    # PROGRESS PROPERTIES (convenience shortcuts)
    # =========================================================================

    @property
    def start_progress(self) -> Progress:
        """Progress toward IN_PROGRESS (dependencies)."""
        return self.progress_for_transition(TicketStatus.IN_PROGRESS)

    @property
    def completion_progress(self) -> Progress:
        """Progress toward COMPLETED (success criteria)."""
        return self.progress_for_transition(TicketStatus.COMPLETED)

    @property
    def deploy_progress(self) -> Progress:
        """Progress toward PRODUCTION_READY (production gates)."""
        return self.progress_for_transition(TicketStatus.PRODUCTION_READY)

    # =========================================================================
    # CONVENIENCE ACCESSORS (filter criteria by type)
    # =========================================================================

    @property
    def deliverables(self) -> List[Criterion]:
        """
        Get file deliverable criteria.

        Returns criteria with FileExistsTarget.
        """
        return [
            c for c in self.criteria
            if isinstance(c.target, FileExistsTarget)
        ]

    @property
    def tests(self) -> List[Criterion]:
        """
        Get test criteria.

        Returns criteria with TestPassesTarget.
        """
        return [
            c for c in self.criteria
            if isinstance(c.target, TestPassesTarget)
        ]

    @property
    def subtasks(self) -> List[Criterion]:
        """
        Get subtask criteria (children that block completion).

        Returns criteria with CompletableTarget and blocks_transition_to=COMPLETED.
        """
        return [
            c for c in self.criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def dependencies(self) -> List[Criterion]:
        """
        Get dependency criteria (block starting).

        Returns criteria with CompletableTarget and blocks_transition_to=IN_PROGRESS.
        """
        return [
            c for c in self.criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.IN_PROGRESS
        ]

    @property
    def manual_checks(self) -> List[Criterion]:
        """
        Get manual check criteria.

        Returns criteria with ManualTarget.
        """
        return [
            c for c in self.criteria
            if isinstance(c.target, ManualTarget)
        ]

    @property
    def production_gates(self) -> List[Criterion]:
        """
        Get production gate criteria.

        Returns criteria with blocks_transition_to=PRODUCTION_READY.
        """
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.PRODUCTION_READY
        ]

    # =========================================================================
    # LIFECYCLE METHODS
    # =========================================================================

    def start(self) -> "Ticket":
        """
        Transition ticket to IN_PROGRESS.

        Checks can_start() first and raises if blocked.

        Returns:
            Updated Ticket with new status

        Raises:
            ValueError: If cannot start (dependencies not met)
        """
        can, reasons = self.can_start()
        if not can:
            raise ValueError(
                f"Cannot start ticket '{self.id}': {'; '.join(reasons)}"
            )

        return self.model_copy(update={
            "status": TicketStatus.IN_PROGRESS,
            "started_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

    def complete(self) -> "Ticket":
        """
        Transition ticket to COMPLETED.

        Checks can_complete() first and raises if blocked.

        Returns:
            Updated Ticket with new status

        Raises:
            ValueError: If cannot complete (criteria not met)
        """
        can, reasons = self.can_complete()
        if not can:
            raise ValueError(
                f"Cannot complete ticket '{self.id}': {'; '.join(reasons)}"
            )

        return self.model_copy(update={
            "status": TicketStatus.COMPLETED,
            "completed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

    def pause(self) -> "Ticket":
        """
        Transition ticket to PAUSED.

        Can pause from any non-terminal status.

        Returns:
            Updated Ticket with new status
        """
        if self.status.is_terminal():
            raise ValueError(
                f"Cannot pause ticket '{self.id}': status '{self.status}' is terminal"
            )

        return self.model_copy(update={
            "status": TicketStatus.PAUSED,
            "updated_at": datetime.now(timezone.utc),
        })

    def cancel(self) -> "Ticket":
        """
        Transition ticket to WONT_DO (cancelled).

        Returns:
            Updated Ticket with terminal status
        """
        return self.model_copy(update={
            "status": TicketStatus.WONT_DO,
            "updated_at": datetime.now(timezone.utc),
        })

    def resume(self) -> "Ticket":
        """
        Resume a paused ticket to IN_PROGRESS.

        Returns:
            Updated Ticket with IN_PROGRESS status

        Raises:
            ValueError: If not paused
        """
        if self.status != TicketStatus.PAUSED:
            raise ValueError(
                f"Cannot resume ticket '{self.id}': not paused (status: {self.status})"
            )

        return self.model_copy(update={
            "status": TicketStatus.IN_PROGRESS,
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # COMMIT MANAGEMENT
    # =========================================================================

    def add_commit(self, commit: GitCommit) -> "Ticket":
        """
        Add a commit to this ticket.

        Returns:
            Updated Ticket with new commit
        """
        return self.model_copy(update={
            "commits": self.commits + [commit],
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # REQUIREMENT MANAGEMENT
    # =========================================================================

    def add_requirement(self, requirement: Requirement) -> "Ticket":
        """
        Add a requirement template to this ticket.

        Requirements cascade to children.

        Returns:
            Updated Ticket with new requirement
        """
        # Check for duplicate ID
        for req in self.requirements_local:
            if req.id == requirement.id:
                raise ValueError(f"Requirement with ID '{requirement.id}' already exists")

        return self.model_copy(update={
            "requirements_local": self.requirements_local + [requirement],
            "updated_at": datetime.now(timezone.utc),
        })

    def remove_requirement(self, requirement_id: str) -> "Ticket":
        """
        Remove a requirement template by ID.

        Returns:
            Updated Ticket without the requirement
        """
        new_requirements = [r for r in self.requirements_local if r.id != requirement_id]
        if len(new_requirements) == len(self.requirements_local):
            return self  # Nothing to remove

        return self.model_copy(update={
            "requirements_local": new_requirements,
            "updated_at": datetime.now(timezone.utc),
        })

    def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by ID."""
        for req in self.requirements_local:
            if req.id == requirement_id:
                return req
        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "GitCommit",
    "Ticket",
]
