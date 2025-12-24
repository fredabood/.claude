"""
Layer 1 Ticket class for the unified ticket architecture.

Ticket extends Completable with work-specific semantics:
- Lifecycle (status, timestamps)
- Assignment (agents, priority)
- Work evidence (commits)
- Hierarchy (parent_ref)
- Token tracking (estimates, budgets, usage, enforcement)

Design Principle: Ticket IS a Completable with additional work tracking.
Completion is determined by criteria (inherited from Completable).
Ticket adds work semantics on top.

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


# =============================================================================
# TOKEN MODELS
# =============================================================================


class TokenEstimate(BaseModel):
    """
    Planning estimate with min/max/target range.

    Used to estimate expected token usage for a ticket before execution.
    The range allows for uncertainty in estimates while providing
    guidance for budget allocation.

    Lifecycle by status:
    - not_started: estimate populated, budget optional, usage null
    - in_progress: estimate + budget, usage accumulating
    - completed: estimate preserved, usage final
    """

    min: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum expected tokens (optimistic estimate)"
    )
    max: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum expected tokens (pessimistic estimate)"
    )
    target: Optional[int] = Field(
        default=None,
        ge=0,
        description="Target token count (most likely estimate)"
    )

    @model_validator(mode='after')
    def validate_range(self) -> 'TokenEstimate':
        """Validate that min <= target <= max."""
        if self.min is not None and self.target is not None and self.min > self.target:
            raise ValueError('min must be <= target')
        if self.target is not None and self.max is not None and self.target > self.max:
            raise ValueError('target must be <= max')
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError('min must be <= max')
        return self

    @property
    def has_range(self) -> bool:
        """Check if a full range (min, max) is defined."""
        return self.min is not None and self.max is not None

    @property
    def range_size(self) -> Optional[int]:
        """Get the size of the estimate range (max - min)."""
        if self.min is not None and self.max is not None:
            return self.max - self.min
        return None


class EscalationStep(BaseModel):
    """
    Automatic mode escalation at usage threshold.

    When token usage reaches the specified ratio of budget,
    enforcement mode is automatically escalated to the specified mode.

    Example:
        EscalationStep(at=0.9, mode="soft_stop")
        # At 90% budget usage, switch to soft_stop mode
    """

    at: float = Field(
        description="Usage ratio threshold (0.0-1.0+, where 1.0 = 100% of budget)"
    )
    mode: str = Field(
        description="Mode to escalate to (warn, soft_stop, hard_stop)"
    )

    @field_validator('at')
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is non-negative."""
        if v < 0:
            raise ValueError('at must be >= 0')
        return v

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate mode is a recognized value."""
        valid_modes = {'warn', 'soft_stop', 'hard_stop'}
        if v not in valid_modes:
            raise ValueError(f"mode must be one of: {', '.join(sorted(valid_modes))}")
        return v


class TokenEnforcement(BaseModel):
    """
    Budget enforcement settings (per-direction or ticket-level).

    Controls how token budgets are enforced during execution:
    - warn: Notify but allow continued execution
    - soft_stop: Request pause, allow override
    - hard_stop: Terminate execution immediately

    Enforcement resolution order (per direction):
    1. ticket.input_tokens.enforcement (direction-specific)
    2. .vibey/config/token_budgets.yaml (project default)
    3. Built-in defaults (warn, [0.8, 0.9, 1.0])
    """

    # Core enforcement
    mode: str = Field(
        default="warn",
        description="Enforcement mode: warn, soft_stop, hard_stop"
    )
    thresholds: List[float] = Field(
        default_factory=lambda: [0.8, 0.9, 1.0],
        description="Warning thresholds as ratios (0.8 = 80%)"
    )
    allow_override: bool = Field(
        default=True,
        description="Allow CLI/env override of enforcement"
    )
    grace_percent: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overage grace as ratio (0.1 = 10% over budget allowed)"
    )
    escalation: Optional[List[EscalationStep]] = Field(
        default=None,
        description="Auto-escalation steps at usage thresholds"
    )

    # Hierarchical enforcement (all optional, disabled by default)
    require_children_sum_valid: bool = Field(
        default=False,
        description="Validation: sum(children budgets) <= parent budget"
    )
    check_ancestors_during_execution: bool = Field(
        default=False,
        description="Runtime: check parent budgets during execution"
    )
    block_new_children_when_exceeded: bool = Field(
        default=False,
        description="Pre-start: block child creation if parent exceeded"
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate mode is a recognized value."""
        valid_modes = {'warn', 'soft_stop', 'hard_stop'}
        if v not in valid_modes:
            raise ValueError(f"mode must be one of: {', '.join(sorted(valid_modes))}")
        return v

    @field_validator('thresholds')
    @classmethod
    def validate_thresholds(cls, v: List[float]) -> List[float]:
        """Validate thresholds are positive and sorted."""
        if not v:
            return v
        for threshold in v:
            if threshold <= 0:
                raise ValueError('thresholds must be positive')
        return sorted(v)

    def get_active_mode(self, usage_ratio: float) -> str:
        """
        Get the active enforcement mode based on usage ratio.

        Checks escalation steps to determine if mode should be escalated.
        """
        active_mode = self.mode
        if self.escalation:
            for step in sorted(self.escalation, key=lambda s: s.at):
                if usage_ratio >= step.at:
                    active_mode = step.mode
        return active_mode

    def get_triggered_thresholds(self, usage_ratio: float) -> List[float]:
        """Get list of thresholds that have been triggered."""
        return [t for t in self.thresholds if usage_ratio >= t]


class Tokens(BaseModel):
    """
    All token data for one direction (input or output).

    Container for token estimate, budget, usage, and enforcement
    settings for a single direction. Ticket has separate Tokens
    for input and output.

    Design note: These are LOCAL values for this ticket only.
    Aggregation happens in HierarchicalTicket (Layer 2) via
    computed properties.
    """

    estimate: Optional[TokenEstimate] = Field(
        default=None,
        description="Planning estimate with min/max/target range"
    )
    budget: Optional[int] = Field(
        default=None,
        ge=0,
        description="Hard limit for this direction"
    )
    usage: Optional[int] = Field(
        default=None,
        ge=0,
        description="Actual consumption (accumulated during execution)"
    )
    enforcement: Optional[TokenEnforcement] = Field(
        default=None,
        description="Per-direction override of enforcement settings"
    )

    @model_validator(mode='after')
    def validate_budget(self) -> 'Tokens':
        """Validate budget >= estimate.target if both are set."""
        if self.budget is not None and self.estimate is not None and self.estimate.target is not None:
            if self.budget < self.estimate.target:
                raise ValueError('budget must be >= estimate.target')
        return self

    @property
    def usage_ratio(self) -> Optional[float]:
        """Get usage as a ratio of budget (None if no budget or usage)."""
        if self.budget is None or self.budget == 0 or self.usage is None:
            return None
        return self.usage / self.budget

    @property
    def remaining(self) -> Optional[int]:
        """Get remaining tokens (budget - usage, None if no budget)."""
        if self.budget is None:
            return None
        usage = self.usage or 0
        return max(0, self.budget - usage)

    @property
    def is_over_budget(self) -> bool:
        """Check if usage exceeds budget."""
        if self.budget is None or self.usage is None:
            return False
        return self.usage > self.budget

    @property
    def is_within_budget(self) -> bool:
        """Check if usage is within budget (or no budget set)."""
        return not self.is_over_budget

from vibey.roadmap.models.ticket.completable import Completable, Criterion
from vibey.roadmap.models.ticket.enums import Priority, TicketStatus
from vibey.roadmap.models.ticket.requirements import Requirement
from vibey.roadmap.models.ticket.support import Progress
from vibey.roadmap.models.ticket.targets import (
    ArtifactTarget,
    CompletableTarget,
    FileExistsTarget,
    ManualTarget,
    TestPassesTarget,
)


def parse_task_markers(message: str) -> Tuple[List[str], List[str]]:
    """
    Parse Task: and Completes: markers from commit message.

    Supports both single-value and comma-separated formats:
    - Task: 01TASK_A
    - Task: 01TASK_A, 01TASK_B
    - Completes: 01TASK_A

    Args:
        message: The commit message to parse

    Returns:
        Tuple of (references, completes) - Lists of ticket IDs
    """
    references: List[str] = []
    completes: List[str] = []

    for line in message.split('\n'):
        line_stripped = line.strip()

        if line_stripped.startswith('Task:'):
            # Extract value after "Task:"
            value = line_stripped[5:].strip()
            if value:
                # Handle comma-separated IDs
                refs = value.split(',')
                references.extend(r.strip() for r in refs if r.strip())

        elif line_stripped.startswith('Completes:'):
            # Extract value after "Completes:"
            value = line_stripped[10:].strip()
            if value:
                # Handle comma-separated IDs (though typically single value)
                ticket_ids = value.split(',')
                completes.extend(t.strip() for t in ticket_ids if t.strip())

    return references, completes


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
    references_tickets: List[str] = Field(
        default_factory=list,
        description="Ticket IDs referenced by this commit (from Task: markers)"
    )
    completes_tickets: List[str] = Field(
        default_factory=list,
        description="Ticket IDs marked as completed by this commit (from Completes: markers)"
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

    @property
    def all_referenced_tickets(self) -> List[str]:
        """All tickets referenced by this commit (both Task: and Completes:)."""
        # Use dict.fromkeys to deduplicate while preserving order
        all_tickets = self.references_tickets + self.completes_tickets
        return list(dict.fromkeys(all_tickets))

    @classmethod
    def from_git(
        cls,
        sha: str,
        message: str,
        date: datetime,
        author: str,
        platform: Optional[str] = None,
        files_added: Optional[List[str]] = None,
        files_modified: Optional[List[str]] = None,
        files_deleted: Optional[List[str]] = None,
    ) -> "GitCommit":
        """
        Create a GitCommit from git metadata, automatically parsing markers.

        This factory method parses Task: and Completes: markers from the
        commit message to populate references_tickets and completes_tickets.

        Args:
            sha: Full 40-char SHA or abbreviated
            message: Full commit message (subject + body)
            date: Commit date
            author: Commit author
            platform: Platform that created this commit (optional)
            files_added: List of added file paths (optional)
            files_modified: List of modified file paths (optional)
            files_deleted: List of deleted file paths (optional)

        Returns:
            GitCommit instance with parsed ticket references
        """
        # Parse Task: and Completes: markers from message
        references, completes = parse_task_markers(message)

        return cls(
            sha=sha,
            message=message,
            date=date,
            author=author,
            platform=platform,
            submitted_at=datetime.now(timezone.utc),
            references_tickets=references,
            completes_tickets=completes,
            files_added=files_added or [],
            files_modified=files_modified or [],
            files_deleted=files_deleted or [],
        )


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
    # TOKEN TRACKING (Layer 1 - Local Values Only)
    # =========================================================================
    # Token tracking per direction (each with own enforcement)
    # These are LOCAL values. Aggregation happens in HierarchicalTicket (Layer 2).

    input_tokens: Optional[Tokens] = Field(
        default=None,
        description="Token tracking for input direction (estimate, budget, usage, enforcement)"
    )
    output_tokens: Optional[Tokens] = Field(
        default=None,
        description="Token tracking for output direction (estimate, budget, usage, enforcement)"
    )

    # Optional combined budget at ticket level
    total_token_budget: Optional[int] = Field(
        default=None,
        ge=0,
        description="Combined budget for input + output tokens"
    )
    total_token_enforcement: Optional[TokenEnforcement] = Field(
        default=None,
        description="Ticket-level enforcement settings (applies to combined usage)"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @field_validator("started_at")
    @classmethod
    def started_after_created(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """
        Validate started_at vs created_at.

        Note: We allow started_at < created_at to support retroactive task creation,
        where work begins before the task is formally added to the system.
        This is a valid real-world scenario and should not cause validation failure.
        """
        # Allow started_at to be before created_at (retroactive task creation)
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
        """
        Validate and auto-repair status/timestamp consistency.

        Instead of raising errors for missing timestamps, auto-set them
        to allow loading legacy data that may be missing these fields.
        This follows the same pattern as DevelopmentGate.validate_resolved_timestamp.
        """
        if self.status == TicketStatus.IN_PROGRESS and self.started_at is None:
            # Auto-set started_at for IN_PROGRESS tickets missing this field
            # Use created_at as fallback, or current time if neither exists
            fallback_time = self.created_at if self.created_at else datetime.now(timezone.utc)
            object.__setattr__(self, "started_at", fallback_time)
        if self.status == TicketStatus.COMPLETED and self.completed_at is None:
            # Auto-set completed_at for COMPLETED tickets missing this field
            # Use started_at as fallback, or created_at, or current time
            fallback_time = self.started_at or self.created_at or datetime.now(timezone.utc)
            object.__setattr__(self, "completed_at", fallback_time)
        return self

    @model_validator(mode="after")
    def validate_total_token_budget(self) -> "Ticket":
        """
        Validate total_token_budget >= sum of input + output budgets.

        This is an always-on validation that ensures the total budget
        is sufficient to cover the individual direction budgets.

        Error format: "total_token_budget ({total}) must be >= sum of
                       input ({input}) + output ({output}) budgets"
        """
        if self.total_token_budget is not None:
            input_budget = self.input_tokens.budget if self.input_tokens else 0
            output_budget = self.output_tokens.budget if self.output_tokens else 0
            direction_sum = (input_budget or 0) + (output_budget or 0)

            if direction_sum > 0 and self.total_token_budget < direction_sum:
                raise ValueError(
                    f"total_token_budget ({self.total_token_budget:,}) must be >= "
                    f"sum of input ({input_budget or 0:,}) + output ({output_budget or 0:,}) budgets"
                )
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

    @property
    def artifact_criteria(self) -> List[Criterion]:
        """
        Get criteria that reference artifacts.

        Returns criteria with ArtifactTarget.
        """
        return [
            c for c in self.criteria
            if isinstance(c.target, ArtifactTarget)
        ]

    @property
    def referenced_artifact_ids(self) -> List[str]:
        """
        Get IDs of artifacts referenced by this ticket's criteria.

        Returns list of artifact IDs from all ArtifactTarget criteria.
        """
        return [
            c.target.artifact_id
            for c in self.artifact_criteria
        ]

    @property
    def stale_artifact_criteria(self) -> List[Criterion]:
        """
        Get artifact criteria where the artifact is stale.

        Returns criteria with ArtifactTarget where artifact_is_stale=True.
        """
        return [
            c for c in self.artifact_criteria
            if c.target.artifact_is_stale
        ]

    @property
    def has_stale_artifacts(self) -> bool:
        """Check if any referenced artifacts are stale."""
        return len(self.stale_artifact_criteria) > 0

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
    # Token models
    "TokenEstimate",
    "EscalationStep",
    "TokenEnforcement",
    "Tokens",
    # Ticket models
    "GitCommit",
    "Ticket",
    "parse_task_markers",
]
