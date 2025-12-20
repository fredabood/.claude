"""
Generic Ticket Model - Universal Work Item Abstraction

This module defines the core Generic Ticket model that serves as the universal
representation of work items across different project management tools.

Design Goals:
1. Tool-Agnostic: No assumptions about specific PM tools (Vibey, Jira, GitHub, etc.)
2. Generic Terms: Uses neutral vocabulary (Project, Workstream, Iteration, WorkItem)
3. Extensible: Metadata dict allows adapter-specific extensions
4. Consistent: Unified status and criteria system across all adapters

Hierarchy Mapping Examples:
    | Generic Term   | Vibey     | Jira            | GitHub     | Trello |
    |----------------|-----------|-----------------|------------|--------|
    | PROJECT        | Roadmap   | Project         | Repository | Board  |
    | WORKSTREAM     | Track     | Epic/Component  | Milestone  | List   |
    | ITERATION      | Sprint    | Sprint          | -          | -      |
    | WORK_ITEM      | Task      | Issue           | Issue      | Card   |

Reference: UNIFIED_ADAPTER_ARCHITECTURE.md Part 3.1
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HierarchyType(str, Enum):
    """
    Generic hierarchy levels for work organization.

    These levels represent the universal structure found across PM tools,
    though not all tools support all levels (e.g., GitHub doesn't have Sprints).
    """

    PROJECT = "project"
    """Top-level container. Maps to: Roadmap (Vibey), Project (Jira), Repository (GitHub), Board (Trello)"""

    WORKSTREAM = "workstream"
    """Grouping/theme. Maps to: Track (Vibey), Epic/Component (Jira), Milestone (GitHub), List (Trello)"""

    ITERATION = "iteration"
    """Time-boxed period. Maps to: Sprint (Vibey/Jira). Not all tools support this."""

    WORK_ITEM = "work_item"
    """Atomic unit of work. Maps to: Task (Vibey), Issue (Jira/GitHub), Card (Trello)"""


class TicketStatus(str, Enum):
    """
    Universal status values for work items.

    These represent the core lifecycle states common to all PM tools.
    Adapters map tool-specific statuses to these universal values.
    """

    NOT_STARTED = "not_started"
    """Work has not begun. Default initial state."""

    IN_PROGRESS = "in_progress"
    """Work is actively being done."""

    BLOCKED = "blocked"
    """Work cannot proceed due to dependencies or issues."""

    COMPLETED = "completed"
    """Work is finished. All acceptance criteria met."""

    CANCELLED = "cancelled"
    """Work was abandoned or deemed unnecessary."""


class TicketPriority(str, Enum):
    """Universal priority levels."""

    CRITICAL = "critical"
    """Highest priority - must be done immediately."""

    HIGH = "high"
    """High priority - should be done soon."""

    MEDIUM = "medium"
    """Normal priority - default level."""

    LOW = "low"
    """Low priority - can be deferred."""


class CriterionType(str, Enum):
    """Types of acceptance criteria."""

    CODE = "code"
    """Code-related criterion (implementation, refactoring)."""

    TEST = "test"
    """Testing criterion (unit tests, integration tests)."""

    ARTIFACT = "artifact"
    """Artifact criterion (documentation, files to create)."""

    REVIEW = "review"
    """Review criterion (code review, design review)."""

    MANUAL = "manual"
    """Manual verification criterion."""


class CriterionStatus(str, Enum):
    """Status of a criterion."""

    NOT_MET = "not_met"
    """Criterion has not been satisfied."""

    MET = "met"
    """Criterion has been satisfied."""

    SKIPPED = "skipped"
    """Criterion was intentionally skipped."""


class Criterion(BaseModel):
    """
    Acceptance criterion for a work item.

    Criteria define what must be true for a work item to be considered complete.
    This follows the Unified Ticket Architecture's completable pattern.
    """

    type: CriterionType = CriterionType.MANUAL
    """Type of criterion."""

    description: str
    """Human-readable description of what must be satisfied."""

    status: CriterionStatus = CriterionStatus.NOT_MET
    """Current status of this criterion."""

    verified_at: Optional[datetime] = None
    """When this criterion was verified as met."""

    verified_by: Optional[str] = None
    """Who or what verified this criterion (user, CI, etc.)."""

    notes: Optional[str] = None
    """Additional notes about the criterion or its verification."""


class Ticket(BaseModel):
    """
    Generic Ticket - the universal work item abstraction.

    All PM tools map their entities to this model. The CLI and MCP server
    work exclusively with this model, enabling tool-agnostic operations.

    This is the core abstraction that enables Vibey to integrate with
    multiple PM tools without coupling to any specific tool's semantics.

    Design Principles:
    1. Every field has a clear purpose and is tool-agnostic
    2. Adapter-specific data goes in the `metadata` dict
    3. Hierarchy is represented through parent_id/children_ids
    4. Status follows universal lifecycle semantics
    5. Criteria enable the completable pattern

    Example Usage:
        # Create a work item
        task = Ticket(
            id="01KC2D0JK7READW9KAK1HBX4B8",
            source_adapter="vibey",
            hierarchy_type=HierarchyType.WORK_ITEM,
            name="Implement user authentication",
            status=TicketStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
        )

        # Adapters convert to/from this format
        vibey_task = vibey_adapter.map_from_generic(task)
        jira_issue = jira_adapter.map_from_generic(task)
    """

    # =========================================================================
    # IDENTITY
    # =========================================================================

    id: str
    """
    Unique identifier within the adapter's namespace.
    For Vibey: ULID (e.g., "01KC2D0JK7READW9KAK1HBX4B8")
    For Jira: Issue key (e.g., "PROJ-123")
    For GitHub: Issue number (e.g., "42")
    """

    external_id: Optional[str] = None
    """
    Original identifier in the source system.
    Useful for syncing between systems. If this ticket was imported from
    another system, this stores the original ID for back-references.
    """

    source_adapter: str
    """
    Name of the adapter that owns this ticket.
    Examples: "vibey", "jira", "github", "trello", "asana"
    """

    # =========================================================================
    # CLASSIFICATION
    # =========================================================================

    hierarchy_type: HierarchyType
    """
    Position in the work hierarchy.
    Determines how this item relates to others (container vs leaf).
    """

    item_type: Optional[str] = None
    """
    Adapter-specific subtype within the hierarchy level.
    Examples:
    - Vibey WORK_ITEM: "development", "completion_gate", "production_gate"
    - Jira WORK_ITEM: "bug", "story", "task"
    - GitHub WORK_ITEM: "bug", "feature", "enhancement"
    """

    # =========================================================================
    # CONTENT
    # =========================================================================

    name: str
    """
    Short title/summary of the work item.
    Should be concise and descriptive.
    """

    description: Optional[str] = None
    """
    Detailed description of the work.
    May include markdown formatting in most PM tools.
    """

    # =========================================================================
    # HIERARCHY
    # =========================================================================

    parent_id: Optional[str] = None
    """
    ID of the parent ticket in the hierarchy.
    None for top-level items (projects).
    """

    children_ids: List[str] = Field(default_factory=list)
    """
    IDs of child tickets.
    Empty for leaf items (work items with no subtasks).
    """

    # =========================================================================
    # STATUS
    # =========================================================================

    status: TicketStatus = TicketStatus.NOT_STARTED
    """
    Current lifecycle status.
    Adapters map tool-specific statuses to these universal values.
    """

    blocked: bool = False
    """
    Whether progress is blocked.
    True if waiting on dependencies, reviews, or external factors.
    """

    blocked_reason: Optional[str] = None
    """
    Human-readable explanation of why progress is blocked.
    Should describe what's needed to unblock.
    """

    # =========================================================================
    # TIMESTAMPS
    # =========================================================================

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """When this ticket was created."""

    updated_at: Optional[datetime] = None
    """When this ticket was last modified."""

    started_at: Optional[datetime] = None
    """When work on this ticket began (status -> IN_PROGRESS)."""

    completed_at: Optional[datetime] = None
    """When this ticket was completed (status -> COMPLETED)."""

    # =========================================================================
    # ASSIGNMENT
    # =========================================================================

    assignee: Optional[str] = None
    """
    Primary person/agent assigned to this work.
    Format depends on adapter (username, email, ID, etc.).
    """

    labels: List[str] = Field(default_factory=list)
    """
    Tags/labels applied to this ticket.
    Used for categorization and filtering.
    """

    priority: Optional[TicketPriority] = None
    """
    Priority level for this work.
    None means use default (typically MEDIUM).
    """

    # =========================================================================
    # PROGRESS (for containers)
    # =========================================================================

    children_total: int = 0
    """
    Total number of child items.
    Only meaningful for container types (PROJECT, WORKSTREAM, ITERATION).
    """

    children_completed: int = 0
    """
    Number of completed child items.
    Only meaningful for container types.
    """

    completion_percent: float = 0.0
    """
    Percentage of child items completed (0.0 to 100.0).
    Computed as: (children_completed / children_total * 100) if children_total > 0
    """

    # =========================================================================
    # CRITERIA (Completable Pattern)
    # =========================================================================

    criteria: List[Criterion] = Field(default_factory=list)
    """
    Acceptance criteria that must be met for completion.
    Follows the Unified Ticket Architecture's completable pattern.
    """

    # =========================================================================
    # METADATA
    # =========================================================================

    metadata: Dict[str, Any] = Field(default_factory=dict)
    """
    Adapter-specific metadata.
    Use this for data that doesn't fit the generic model but is needed
    by specific adapters or for round-trip preservation.

    Examples:
    - Vibey: {"track_id": "...", "sprint_id": "...", "complexity": "medium"}
    - Jira: {"project_key": "PROJ", "issue_type": "Story", "story_points": 5}
    - GitHub: {"repository": "owner/repo", "milestone_id": 123}
    """

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def is_complete(self) -> bool:
        """Check if this ticket is complete."""
        return self.status == TicketStatus.COMPLETED

    @property
    def is_blocked(self) -> bool:
        """Check if this ticket is blocked."""
        return self.blocked or self.status == TicketStatus.BLOCKED

    @property
    def is_container(self) -> bool:
        """Check if this ticket is a container (has or can have children)."""
        return self.hierarchy_type in (
            HierarchyType.PROJECT,
            HierarchyType.WORKSTREAM,
            HierarchyType.ITERATION,
        )

    @property
    def is_leaf(self) -> bool:
        """Check if this ticket is a leaf (work item with no children)."""
        return self.hierarchy_type == HierarchyType.WORK_ITEM

    @property
    def all_criteria_met(self) -> bool:
        """Check if all acceptance criteria are satisfied."""
        if not self.criteria:
            return True
        return all(c.status == CriterionStatus.MET for c in self.criteria)

    @property
    def criteria_progress(self) -> tuple[int, int]:
        """Get criteria progress as (met, total) tuple."""
        if not self.criteria:
            return (0, 0)
        met = sum(1 for c in self.criteria if c.status == CriterionStatus.MET)
        return (met, len(self.criteria))

    # =========================================================================
    # METHODS
    # =========================================================================

    def update_progress(self) -> None:
        """
        Update completion_percent based on children counts.
        Call this after modifying children_total or children_completed.
        """
        if self.children_total > 0:
            self.completion_percent = (self.children_completed / self.children_total) * 100.0
        else:
            self.completion_percent = 0.0

    def mark_started(self, when: Optional[datetime] = None) -> None:
        """Mark this ticket as in progress."""
        self.status = TicketStatus.IN_PROGRESS
        self.started_at = when or datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_completed(self, when: Optional[datetime] = None) -> None:
        """Mark this ticket as completed."""
        self.status = TicketStatus.COMPLETED
        self.completed_at = when or datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_blocked(self, reason: Optional[str] = None) -> None:
        """Mark this ticket as blocked."""
        self.status = TicketStatus.BLOCKED
        self.blocked = True
        self.blocked_reason = reason
        self.updated_at = datetime.now(timezone.utc)

    def unblock(self) -> None:
        """Remove blocked status."""
        if self.status == TicketStatus.BLOCKED:
            self.status = TicketStatus.IN_PROGRESS if self.started_at else TicketStatus.NOT_STARTED
        self.blocked = False
        self.blocked_reason = None
        self.updated_at = datetime.now(timezone.utc)

    class Config:
        """Pydantic configuration."""
        use_enum_values = False  # Keep enums as enum objects, not strings
