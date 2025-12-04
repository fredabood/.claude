"""
Core completion model for the unified ticket architecture.

This module defines the fundamental abstractions:
- Completable: Base class for anything that can be completed
- Criterion: A requirement that blocks a state transition

Design Principle: Everything that can be completed shares the same
abstraction. Completion is determined by criteria, and criteria have
polymorphic targets.

The key innovation is the `blocks_transition_to` field on Criterion,
which unifies:
- Dependencies (blocks IN_PROGRESS)
- Success criteria (blocks COMPLETED)
- Production gates (blocks PRODUCTION_READY)

This ELIMINATES the separate Dependency class.

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, computed_field

from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.models.ticket.support import Progress
from vibey.roadmap.models.ticket.targets import AnyTarget, CompletableTarget


class Criterion(BaseModel):
    """
    A requirement that blocks a state transition.

    The blocks_transition_to field enables UNIFIED blocking:
    - IN_PROGRESS: Must be met before work can start (dependency)
    - COMPLETED: Must be met before marking complete (success criteria)
    - PRODUCTION_READY: Must be met before deployment (production gate)

    This REPLACES the separate Dependency class. A "dependency" is now
    just a Criterion with blocks_transition_to=IN_PROGRESS.

    Example - Task 003 depends on Task 002:

    OLD (separate Dependency class):
        dependencies:
          - target_id: task-002
            required_status: completed
            blocks_transition_to: in_progress

    NEW (unified Criterion):
        criteria:
          - id: dep-task-002
            description: "Task 002 must complete before starting"
            target:
              type: completable
              completable_id: task-002
              required_status: completed
            blocks_transition_to: in_progress
    """

    # Identity
    id: str = Field(description="Unique identifier within parent Completable")
    description: str = Field(description="What must be true for this criterion")

    # THE key field for unified blocking
    blocks_transition_to: TicketStatus = Field(
        default=TicketStatus.COMPLETED,
        description="Which state transition this criterion guards"
    )

    # What satisfies this criterion (polymorphic)
    target: AnyTarget = Field(description="Target that determines satisfaction")

    # Optionality
    required: bool = Field(
        default=True,
        description="If False, criterion doesn't block transition (informational)"
    )

    @computed_field
    @property
    def is_met(self) -> bool:
        """
        Check if this criterion is satisfied.

        Non-required criteria are always considered met.
        """
        if not self.required:
            return True
        return self.target.is_satisfied()

    @property
    def status_description(self) -> str:
        """Get human-readable description of criterion status."""
        return self.target.get_status_description()

    def refresh(self) -> None:
        """Update target's cached state from external sources."""
        self.target.refresh()


class Completable(BaseModel):
    """
    Base class for anything that can be completed.

    This is the foundation of the unified ticket architecture. Both
    Tickets (work items) and Artifacts (file entities) extend this class.

    The key innovation is criteria-based completion: instead of tracking
    completion state directly, completion is COMPUTED from whether all
    blocking criteria are satisfied.

    Core Principle:
        Completion is computed, not declared. An entity cannot be marked
        complete unless all criteria blocking that transition are satisfied.
    """

    # Identity (ULID-based, immutable)
    id: str = Field(description="Unique identifier (ULID format)")
    name: str = Field(description="Display name (mutable)")
    description: Optional[str] = Field(default=None, description="Detailed description")

    # THE source of truth for ALL blocking
    criteria: List[Criterion] = Field(
        default_factory=list,
        description="Criteria that block state transitions"
    )

    @computed_field
    @property
    def children(self) -> List[str]:
        """
        Children are derived from CompletableTarget criteria.

        This creates the parent-child hierarchy dynamically based on
        which Completables this one depends on for completion.
        """
        return [
            c.target.completable_id
            for c in self.criteria
            if isinstance(c.target, CompletableTarget)
        ]

    def can_transition_to(self, status: TicketStatus) -> Tuple[bool, List[str]]:
        """
        THE unified interface for checking state transitions.

        Returns (can_transition, blocking_reasons).

        This single method handles ALL transition checks:
        - can_transition_to(IN_PROGRESS) checks dependencies
        - can_transition_to(COMPLETED) checks success criteria
        - can_transition_to(PRODUCTION_READY) checks production gates

        Args:
            status: The target status to transition to

        Returns:
            Tuple of (can_transition: bool, blocking_reasons: List[str])
        """
        blocking_reasons = [
            c.description
            for c in self.criteria
            if c.blocks_transition_to == status and not c.is_met
        ]
        return (len(blocking_reasons) == 0, blocking_reasons)

    def progress_for_transition(self, status: TicketStatus) -> Progress:
        """
        Get progress toward a specific state transition.

        Args:
            status: The target status to measure progress toward

        Returns:
            Progress object with total/completed/percent
        """
        relevant = [c for c in self.criteria if c.blocks_transition_to == status]
        total = len(relevant)
        met = sum(1 for c in relevant if c.is_met)
        return Progress(
            total=total,
            completed=met,
        )

    @property
    def progress(self) -> Progress:
        """
        Default progress = progress toward COMPLETED.

        This is the most commonly needed progress metric.
        """
        return self.progress_for_transition(TicketStatus.COMPLETED)

    @property
    def is_complete(self) -> bool:
        """
        Check if all COMPLETED criteria are met.

        Shorthand for can_transition_to(COMPLETED)[0].
        """
        can_complete, _ = self.can_transition_to(TicketStatus.COMPLETED)
        return can_complete

    @property
    def blocking_reasons(self) -> List[str]:
        """
        Get reasons blocking COMPLETED transition.

        Shorthand for can_transition_to(COMPLETED)[1].
        """
        _, reasons = self.can_transition_to(TicketStatus.COMPLETED)
        return reasons

    # Convenience methods for common transitions

    def can_start(self) -> Tuple[bool, List[str]]:
        """Check if can transition to IN_PROGRESS (start work)."""
        return self.can_transition_to(TicketStatus.IN_PROGRESS)

    def can_complete(self) -> Tuple[bool, List[str]]:
        """Check if can transition to COMPLETED."""
        return self.can_transition_to(TicketStatus.COMPLETED)

    def can_deploy(self) -> Tuple[bool, List[str]]:
        """Check if can transition to PRODUCTION_READY."""
        return self.can_transition_to(TicketStatus.PRODUCTION_READY)

    # Criterion management

    def get_criterion(self, criterion_id: str) -> Optional[Criterion]:
        """Get a criterion by ID."""
        for c in self.criteria:
            if c.id == criterion_id:
                return c
        return None

    def add_criterion(self, criterion: Criterion) -> None:
        """Add a criterion to this Completable."""
        # Check for duplicate ID
        if self.get_criterion(criterion.id) is not None:
            raise ValueError(f"Criterion with ID '{criterion.id}' already exists")
        self.criteria.append(criterion)

    def remove_criterion(self, criterion_id: str) -> bool:
        """
        Remove a criterion by ID.

        Returns True if removed, False if not found.
        """
        for i, c in enumerate(self.criteria):
            if c.id == criterion_id:
                self.criteria.pop(i)
                return True
        return False

    def refresh_criteria(self) -> None:
        """Refresh all criteria targets from external sources."""
        for criterion in self.criteria:
            criterion.refresh()

    # Query methods

    def criteria_for_transition(self, status: TicketStatus) -> List[Criterion]:
        """Get all criteria that block a specific transition."""
        return [c for c in self.criteria if c.blocks_transition_to == status]

    def blocking_criteria_for_transition(self, status: TicketStatus) -> List[Criterion]:
        """Get unmet criteria that block a specific transition."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == status and not c.is_met
        ]

    def met_criteria_for_transition(self, status: TicketStatus) -> List[Criterion]:
        """Get met criteria for a specific transition."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == status and c.is_met
        ]


# Export all classes
__all__ = [
    "Completable",
    "Criterion",
]
