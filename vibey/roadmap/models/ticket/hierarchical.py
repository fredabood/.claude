"""
Layer 2 HierarchicalTicket class for the unified ticket architecture.

HierarchicalTicket extends Ticket with smart accessors for:
- Aggregation (commits from children)
- Inheritance (requirements cascade with modes)
- Sibling ordering (sequence-based navigation)
- Hierarchy traversal (parent, children, ancestors, descendants)

Design Principle: Smart accessors use hierarchy attributes to
determine field behavior automatically. No L3 knowledge needed.

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

import logging
from datetime import datetime, timezone
from typing import Any, ClassVar, List, Optional, Protocol, TYPE_CHECKING, Tuple

from pydantic import Field, computed_field

logger = logging.getLogger(__name__)

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import ActivityType, TicketStatus, TicketType
from vibey.roadmap.models.ticket.requirements import (
    RequirementInstantiator,
    RequirementResolver,
)
from vibey.roadmap.models.ticket.support import Progress, RefreshContext
from vibey.roadmap.models.ticket.targets import (
    ArtifactTarget,
    CompletableTarget,
    FileExistsTarget,
    ManualTarget,
    TestPassesTarget,
    ThresholdTarget,
)
from vibey.roadmap.models.ticket.ticket import GitCommit, Ticket
from vibey.roadmap.models.ticket.artifact_enums import (
    ArtifactVerification,
    DocumentationHealth,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket


# =============================================================================
# LOADER PROTOCOL
# =============================================================================


class TicketLoader(Protocol):
    """Protocol for loading tickets by ID."""

    def load(self, ticket_id: str) -> "HierarchicalTicket":
        """Load a ticket by its ID."""
        ...


class SiblingLoader(Protocol):
    """Protocol for loading siblings of a ticket."""

    def load_siblings(self, parent_id: str, exclude_id: str) -> List["HierarchicalTicket"]:
        """Load siblings (other children of same parent)."""
        ...


# =============================================================================
# HIERARCHICAL TICKET CLASS
# =============================================================================


class HierarchicalTicket(Ticket):
    """
    Layer 2: Ticket with smart accessors and hierarchy navigation.

    HierarchicalTicket extends Ticket with:
    - ULID identity fields (sequence, slug)
    - Sibling navigation (siblings, next_sibling, prev_sibling)
    - Aggregated commits (from children if parent)
    - Effective requirements (inherited with resolution modes)
    - Instantiated criteria (from applicable requirements)
    - Hierarchy traversal (parent, children_tickets, ancestors, descendants)

    Key Principle: Smart accessors automatically adapt behavior based on
    hierarchy position (is_parent, is_child, is_ultimate_parent, etc.)
    """

    # =========================================================================
    # CLASS-LEVEL LOADER (Dependency Injection)
    # =========================================================================

    _loader: ClassVar[Optional[TicketLoader]] = None
    _sibling_loader: ClassVar[Optional[SiblingLoader]] = None

    @classmethod
    def set_loader(cls, loader: TicketLoader) -> None:
        """Set the ticket loader for hierarchy navigation."""
        cls._loader = loader

    @classmethod
    def set_sibling_loader(cls, loader: SiblingLoader) -> None:
        """Set the sibling loader for sibling navigation."""
        cls._sibling_loader = loader

    @classmethod
    def clear_loaders(cls) -> None:
        """Clear all loaders (useful for testing)."""
        cls._loader = None
        cls._sibling_loader = None

    # =========================================================================
    # ULID IDENTITY & ORDERING
    # =========================================================================

    sequence: int = Field(
        default=0,
        description="Explicit ordering among siblings (mutable, 0-indexed)"
    )
    slug: str = Field(
        default="",
        description="Human-readable path segment (mutable)"
    )

    # Note: parent_ref from Ticket serves as parent_id (ULID reference)

    # =========================================================================
    # LOCAL COMMITS STORAGE
    # =========================================================================

    # Note: We inherit 'commits' from Ticket but override the property
    # to provide aggregation behavior. The parent's commits field stores local commits.

    # =========================================================================
    # SIBLING NAVIGATION
    # =========================================================================

    @property
    def siblings(self) -> List["HierarchicalTicket"]:
        """
        Other children of the same parent, sorted by sequence.

        Returns empty list if this is a root ticket (no parent).
        Requires sibling_loader to be configured.
        """
        if self.parent_ref is None:
            return []
        if self._sibling_loader is None:
            # Fallback: return empty if no loader
            return []
        return sorted(
            self._sibling_loader.load_siblings(self.parent_ref, self.id),
            key=lambda t: t.sequence
        )

    @property
    def next_sibling(self) -> Optional["HierarchicalTicket"]:
        """
        Next sibling by sequence (not by ID).

        Returns None if this is the last sibling or has no siblings.
        """
        sibs = self.siblings
        if not sibs:
            return None

        # Find siblings with higher sequence
        higher = [s for s in sibs if s.sequence > self.sequence]
        if not higher:
            return None
        return min(higher, key=lambda s: s.sequence)

    @property
    def prev_sibling(self) -> Optional["HierarchicalTicket"]:
        """
        Previous sibling by sequence.

        Returns None if this is the first sibling or has no siblings.
        """
        sibs = self.siblings
        if not sibs:
            return None

        # Find siblings with lower sequence
        lower = [s for s in sibs if s.sequence < self.sequence]
        if not lower:
            return None
        return max(lower, key=lambda s: s.sequence)

    def reorder(self, new_sequence: int) -> "HierarchicalTicket":
        """
        Change position without changing identity.

        Returns a new ticket with updated sequence.
        Note: Does NOT change self.id - identity is immutable.
        """
        return self.model_copy(update={
            "sequence": new_sequence,
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # SMART ACCESSORS - COMMITS (Aggregation)
    # =========================================================================

    @property
    def commits_local(self) -> List[GitCommit]:
        """Access to local commits only (not aggregated)."""
        # The commits field is inherited from Ticket
        # Access it via model_fields to get the stored value
        return list(self.commits)

    @property
    def commits_aggregated(self) -> List[GitCommit]:
        """
        Commits aggregated from this ticket and all descendants.

        - is_ultimate_child: return local commits only
        - is_parent: aggregate from all children recursively
        """
        if self.is_ultimate_child:
            return self.commits_local
        return self._aggregate_commits()

    def _aggregate_commits(self) -> List[GitCommit]:
        """Collect commits from all descendant tickets."""
        all_commits = list(self.commits)  # Local commits
        for child in self.children_tickets:
            if hasattr(child, 'commits_aggregated'):
                all_commits.extend(child.commits_aggregated)
            else:
                all_commits.extend(child.commits)
        return sorted(all_commits, key=lambda c: c.date)

    # =========================================================================
    # SMART ACCESSORS - REQUIREMENTS (Inheritance)
    # =========================================================================

    @property
    def requirements_effective(self) -> List[Any]:
        """
        Requirements: local if root, effective (inherited) if child.

        Uses RequirementResolver to handle inheritance modes:
        - INHERIT: stricter of local vs ancestor
        - OVERRIDE: local replaces ancestor
        - SKIP: explicitly excluded

        Note: Full inheritance resolution requires loading ancestors via the
        configured loader. Without ancestors, returns local requirements only.
        """
        if self.is_ultimate_parent or self._loader is None:
            return list(self.requirements_local)

        # Collect ancestor requirements
        ancestor_reqs: List[Any] = []
        for ancestor in self.ancestors:
            ancestor_reqs.extend(ancestor.requirements_local)

        if not ancestor_reqs:
            return list(self.requirements_local)

        # Resolve with inheritance
        return RequirementResolver().resolve(
            local_requirements=list(self.requirements_local),
            ancestor_requirements=ancestor_reqs,
        )

    # =========================================================================
    # SMART ACCESSORS - CRITERIA (Instantiated from Requirements)
    # =========================================================================

    @property
    def instantiated_criteria(self) -> List[Criterion]:
        """
        Criteria generated from applicable requirements.

        These are ADDED to explicit criteria, not replacing them.
        """
        effective_reqs = self.requirements_effective
        if not effective_reqs:
            return []
        return RequirementInstantiator().instantiate(
            requirements=effective_reqs,
            ticket_id=self.id,
            ticket_name=self.name,
        )

    @property
    def all_criteria(self) -> List[Criterion]:
        """Explicit criteria + instantiated from requirements."""
        return self.criteria + self.instantiated_criteria

    # =========================================================================
    # PROGRESS (Override to use all_criteria)
    # =========================================================================

    def progress_for_transition(self, status: TicketStatus) -> Progress:
        """
        Progress toward a specific transition, excluding deferred children.

        Filters all_criteria by blocks_transition_to, excludes deferred children
        for COMPLETED/PRODUCTION_READY transitions, then computes:
        progress = met_criteria / total_criteria

        Overrides Completable.progress_for_transition to use all_criteria
        and exclude deferred children.
        """
        relevant = []
        for c in self.all_criteria:
            if c.blocks_transition_to != status:
                continue

            # Exclude deferred children from progress calculation
            if isinstance(c.target, CompletableTarget):
                if status in (TicketStatus.COMPLETED, TicketStatus.PRODUCTION_READY):
                    if self._is_child_deferred(c.target.completable_id):
                        continue

            relevant.append(c)

        total = len(relevant)
        if total == 0:
            return Progress(total=0, completed=0)
        met = sum(1 for c in relevant if c.is_met)
        return Progress(total=total, completed=met)

    # =========================================================================
    # CONVENIENCE ACCESSORS (Override to use all_criteria)
    # =========================================================================

    @property
    def deliverables(self) -> List[Criterion]:
        """
        Get file deliverable criteria.

        Returns criteria with FileExistsTarget from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, FileExistsTarget)
        ]

    @property
    def tests(self) -> List[Criterion]:
        """
        Get test criteria.

        Returns criteria with TestPassesTarget from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, TestPassesTarget)
        ]

    @property
    def subtasks(self) -> List[Criterion]:
        """
        Get subtask criteria (children that block completion).

        Returns criteria with CompletableTarget and blocks_transition_to=COMPLETED
        from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def dependencies(self) -> List[Criterion]:
        """
        Get dependency criteria (block starting).

        Returns criteria with CompletableTarget and blocks_transition_to=IN_PROGRESS
        from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.IN_PROGRESS
        ]

    @property
    def thresholds(self) -> List[Criterion]:
        """
        Get threshold-based criteria.

        Returns criteria with ThresholdTarget from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, ThresholdTarget)
        ]

    @property
    def manual_checks(self) -> List[Criterion]:
        """
        Get manual check criteria.

        Returns criteria with ManualTarget from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, ManualTarget)
        ]

    @property
    def production_gates(self) -> List[Criterion]:
        """
        Get production gate criteria.

        Returns criteria with blocks_transition_to=PRODUCTION_READY from all_criteria.
        """
        return [
            c for c in self.all_criteria
            if c.blocks_transition_to == TicketStatus.PRODUCTION_READY
        ]

    # =========================================================================
    # ARTIFACT ACCESSORS (Aggregation)
    # =========================================================================

    @property
    def artifact_criteria(self) -> List[Criterion]:
        """
        Get criteria that reference artifacts.

        Returns criteria with ArtifactTarget from all_criteria.
        Overrides Ticket.artifact_criteria to use all_criteria instead of criteria.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, ArtifactTarget)
        ]

    @property
    def all_referenced_artifacts(self) -> List[str]:
        """
        All artifact IDs referenced by this ticket and descendants.

        - is_ultimate_child: return local referenced_artifact_ids only
        - is_parent: aggregate from all children recursively

        Returns deduplicated list of artifact IDs.
        """
        if self.is_ultimate_child:
            return self.referenced_artifact_ids

        all_ids = list(self.referenced_artifact_ids)
        for child in self.children_tickets:
            if hasattr(child, 'all_referenced_artifacts'):
                all_ids.extend(child.all_referenced_artifacts)
            else:
                all_ids.extend(child.referenced_artifact_ids)
        return list(set(all_ids))

    @property
    def stale_documentation_artifacts(self) -> List[str]:
        """
        Artifact IDs for stale documentation in this subtree.

        Finds all artifacts where:
        - verification == ArtifactVerification.NOT_STALE
        - artifact_is_stale == True

        Returns deduplicated list of stale artifact IDs.
        """
        stale: List[str] = []

        # Check local artifact criteria
        for criterion in self.artifact_criteria:
            if isinstance(criterion.target, ArtifactTarget):
                if (criterion.target.verification == ArtifactVerification.NOT_STALE
                        and criterion.target.artifact_is_stale):
                    stale.append(criterion.target.artifact_id)

        # Aggregate from children if not a leaf
        if not self.is_ultimate_child:
            for child in self.children_tickets:
                if hasattr(child, 'stale_documentation_artifacts'):
                    stale.extend(child.stale_documentation_artifacts)

        return list(set(stale))

    @property
    def has_stale_documentation(self) -> bool:
        """True if any documentation in this subtree is stale."""
        return len(self.stale_documentation_artifacts) > 0

    @property
    def documentation_health(self) -> DocumentationHealth:
        """
        Aggregate documentation health status.

        Returns:
            - HEALTHY: No stale documentation
            - CRITICAL: Stale docs that block completion (required criteria)
            - DEGRADED: Stale docs exist but don't block completion
        """
        stale_count = len(self.stale_documentation_artifacts)
        if stale_count == 0:
            return DocumentationHealth.HEALTHY

        # Check if any stale docs block completion
        for criterion in self.artifact_criteria:
            if not isinstance(criterion.target, ArtifactTarget):
                continue
            if (criterion.target.artifact_is_stale
                    and criterion.blocks_transition_to == TicketStatus.COMPLETED
                    and criterion.required):
                return DocumentationHealth.CRITICAL

        return DocumentationHealth.DEGRADED

    # =========================================================================
    # DEFERRED CHILDREN SUPPORT
    # =========================================================================

    def _is_child_deferred(self, child_id: str) -> bool:
        """
        Check if a child ticket is deferred.

        Args:
            child_id: ID of the child ticket to check

        Returns:
            True if child exists and has deferred=True, False otherwise
        """
        if self._loader is None:
            return False
        try:
            child = self._loader.load(child_id)
            return child.deferred if hasattr(child, 'deferred') else False
        except Exception:
            return False

    @property
    def required_children(self) -> List[str]:
        """
        Children that are required (not deferred).

        Returns IDs of children that must complete for this ticket to complete.
        """
        return [
            c.target.completable_id
            for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and not self._is_child_deferred(c.target.completable_id)
        ]

    @property
    def deferred_children(self) -> List[str]:
        """
        Children that are deferred (optional for production).

        Returns IDs of children that don't block this ticket's completion.
        """
        return [
            c.target.completable_id
            for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and self._is_child_deferred(c.target.completable_id)
        ]

    # =========================================================================
    # TRANSITION CHECKS (Override to exclude deferred children)
    # =========================================================================

    def can_transition_to(self, status: TicketStatus) -> Tuple[bool, List[str]]:
        """
        Check if transition is allowed, excluding deferred children.

        Deferred children are skipped for COMPLETED and PRODUCTION_READY checks.
        This allows a parent to complete even if deferred children are incomplete.

        Args:
            status: The target status to transition to

        Returns:
            Tuple of (can_transition: bool, blocking_reasons: List[str])
        """
        blocking_reasons = []

        for c in self.all_criteria:
            if c.blocks_transition_to != status:
                continue
            if not c.required:
                continue

            # Skip deferred children for completion-related transitions
            if isinstance(c.target, CompletableTarget):
                if status in (TicketStatus.COMPLETED, TicketStatus.PRODUCTION_READY):
                    if self._is_child_deferred(c.target.completable_id):
                        continue  # Deferred child doesn't block

            if not c.is_met:
                blocking_reasons.append(c.description)

        return (len(blocking_reasons) == 0, blocking_reasons)

    # =========================================================================
    # HIERARCHY TRAVERSAL
    # =========================================================================

    @property
    def parent(self) -> Optional["HierarchicalTicket"]:
        """Load parent ticket if exists."""
        if self.parent_ref is None:
            return None
        return self._load_ticket(self.parent_ref)

    @property
    def children_tickets(self) -> List["HierarchicalTicket"]:
        """Load all child tickets."""
        return [self._load_ticket(child_id) for child_id in self.children]

    @property
    def ancestors(self) -> List["HierarchicalTicket"]:
        """All ancestors from parent to root."""
        result: List["HierarchicalTicket"] = []
        current = self.parent
        while current is not None:
            result.append(current)
            current = current.parent
        return result

    @property
    def descendants(self) -> List["HierarchicalTicket"]:
        """All descendants (children, grandchildren, etc.)."""
        result: List["HierarchicalTicket"] = []
        for child in self.children_tickets:
            result.append(child)
            result.extend(child.descendants)
        return result

    @property
    def root(self) -> "HierarchicalTicket":
        """Get the root ticket (ultimate parent)."""
        if self.is_ultimate_parent:
            return self
        ancestors = self.ancestors
        return ancestors[-1] if ancestors else self

    @property
    def depth(self) -> int:
        """Depth in the hierarchy (0 for root)."""
        return len(self.ancestors)

    # =========================================================================
    # TOKEN ESTIMATION
    # =========================================================================

    @computed_field
    @property
    def computed_tokens(self) -> int:
        """
        Token estimate for this ticket.

        - Ultimate children (tasks): return estimated_tokens field value
        - Parents: aggregate from children's computed_tokens

        Used for platform context window fitting and capacity planning.
        """
        if self.is_ultimate_child:
            # Tasks have estimated_tokens field
            return getattr(self, 'estimated_tokens', 0)

        # Parents aggregate from children
        return sum(
            child.computed_tokens
            for child in self.children_tickets
        )

    def _load_ticket(self, ticket_id: str) -> "HierarchicalTicket":
        """Load a ticket by ID using the configured loader."""
        if self._loader is None:
            raise RuntimeError(
                "No loader configured. Call HierarchicalTicket.set_loader() first."
            )
        return self._loader.load(ticket_id)

    # =========================================================================
    # HIERARCHY MANIPULATION
    # =========================================================================

    def get_path(self) -> List[str]:
        """Get the path from root to this ticket as list of IDs."""
        return [a.id for a in reversed(self.ancestors)] + [self.id]

    def get_slug_path(self) -> str:
        """Get the human-readable path using slugs."""
        parts = [a.slug or a.id for a in reversed(self.ancestors)]
        parts.append(self.slug or self.id)
        return "/".join(parts)

    # =========================================================================
    # AUTO-PROGRESSION
    # =========================================================================

    def auto_progress(self, context: RefreshContext) -> List[str]:
        """
        Refresh automatic criteria and progress status if possible.

        This method:
        1. Refreshes all automatic criteria (those with is_automatic=True)
        2. Checks each possible status transition in order
        3. Transitions when all criteria for that status are met
        4. Logs each transition to the context's activity log

        Design Reference: UNIFIED_TICKET_ARCHITECTURE.md Part 11.5

        Args:
            context: RefreshContext with external system access and activity log

        Returns:
            List of transition descriptions (e.g., ["ticket-1: NOT_STARTED → IN_PROGRESS"])
        """
        transitions: List[str] = []

        # Step 1: Refresh all automatic criteria
        for criterion in self.all_criteria:
            if hasattr(criterion.target, 'is_automatic') and criterion.target.is_automatic:
                if hasattr(criterion.target, 'refresh'):
                    criterion.target.refresh(context)

        # Step 2: Check each possible transition in order
        status_order = [
            TicketStatus.IN_PROGRESS,
            TicketStatus.COMPLETION_GATE_CHECK,
            TicketStatus.COMPLETED,
            TicketStatus.PRODUCTION_GATE_CHECK,
            TicketStatus.PRODUCTION_READY,
        ]

        # Terminal states cannot progress
        if self.status.is_terminal():
            return transitions

        for target_status in status_order:
            if self.status.precedes(target_status):
                can, reasons = self.can_transition_to(target_status)
                if can:
                    old_status = self.status
                    self._transition_to(target_status)
                    transitions.append(f"{self.id}: {old_status.value} → {target_status.value}")

                    # Log the auto-progression
                    context.activity_log.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "type": ActivityType.AUTO_PROGRESSION.value,
                        "description": f"Auto-progressed from {old_status.value} to {target_status.value}",
                        "entity_type": getattr(self, 'ticket_type', TicketType.TASK).value,
                        "entity_id": self.id,
                        "field": "status",
                        "old_value": old_status.value,
                        "new_value": target_status.value,
                    })
                else:
                    # Can't transition to this status - stop trying later statuses
                    # (you can't skip ahead in the progression order)
                    break

        return transitions

    def _transition_to(self, status: TicketStatus) -> None:
        """
        Internal method to update status and timestamps.

        This is a mutable operation that updates the ticket in place.
        For immutable operations, use the start()/complete() methods
        that return new ticket instances.

        Args:
            status: The target status to transition to
        """
        # Update status
        object.__setattr__(self, 'status', status)
        object.__setattr__(self, 'updated_at', datetime.now(timezone.utc))

        # Update status-specific timestamps
        if status == TicketStatus.IN_PROGRESS:
            if self.started_at is None:
                object.__setattr__(self, 'started_at', datetime.now(timezone.utc))
        elif status == TicketStatus.COMPLETED:
            if self.completed_at is None:
                object.__setattr__(self, 'completed_at', datetime.now(timezone.utc))
        # Note: Other status-specific timestamps can be added as needed

    # =========================================================================
    # LIFECYCLE METHODS (Override with platform awareness)
    # =========================================================================

    def start_with_context_check(
        self,
        platform_context_window: Optional[int] = None
    ) -> Tuple["HierarchicalTicket", List[str]]:
        """
        Transition ticket to IN_PROGRESS with optional context window check.

        This extends the base start() method to add a warning if the ticket's
        computed_tokens exceeds the platform's context window size.

        Args:
            platform_context_window: Optional max tokens for the platform.
                If provided and computed_tokens exceeds this, a warning is added.

        Returns:
            Tuple of (started ticket, list of warnings).
            Warnings include context window issues.

        Raises:
            ValueError: If cannot start (dependencies not met)
        """
        warnings: List[str] = []

        # Check platform fit (warning, not blocker)
        if platform_context_window is not None:
            tokens = self.computed_tokens
            if tokens > platform_context_window:
                warning = (
                    f"Ticket requires ~{tokens} tokens but platform "
                    f"context window is {platform_context_window}. Consider splitting."
                )
                warnings.append(warning)
                logger.warning(warning)

        # Use base start() which validates and transitions
        started = self.start()

        # Return as HierarchicalTicket
        return started, warnings


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "HierarchicalTicket",
    "TicketLoader",
    "SiblingLoader",
]
