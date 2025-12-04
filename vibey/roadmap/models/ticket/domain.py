"""
Layer 3 Domain Models for the unified ticket architecture.

Domain models are the concrete ticket types representing the Vibey roadmap hierarchy:
- RoadmapTicket: Ultimate parent, contains tracks
- TrackTicket: Contains sprints (Task 009)
- SprintTicket: Contains tasks (Task 010)
- TaskTicket: Ultimate child, atomic work unit (Task 011)

Design Principle: L3 contains ONLY semantic-specific fields.
All common fields and behaviors are inherited from L1/L2.

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import (
    ActivityType,
    Complexity,
    GateStatus,
    TaskType,
    TicketStatus,
    TicketType,
)
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.targets import CompletableTarget

if TYPE_CHECKING:
    pass  # Forward references for TrackTicket when implemented


# =============================================================================
# ROADMAP-SPECIFIC SUPPORT CLASSES
# =============================================================================


class VersionHistoryEntry(BaseModel):
    """
    Historical version entry for RoadmapTicket.

    Records when versions were released, associated milestones,
    and optional git tags.
    """

    version: str = Field(description="Semantic version string (e.g., '1.0.0')")
    released_at: datetime = Field(description="When this version was released")
    milestone: Optional[str] = Field(
        default=None,
        description="Associated milestone name"
    )
    git_tag: Optional[str] = Field(
        default=None,
        description="Git tag for this version"
    )
    description: Optional[str] = Field(
        default=None,
        description="Release notes or description"
    )

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate version follows semantic versioning format."""
        # Basic semver pattern: MAJOR.MINOR.PATCH with optional prerelease/build
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*))?(?:\+([\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*))?$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid semantic version format: {v}")
        return v


class ActivityLogEntry(BaseModel):
    """
    Activity log entry for tracking roadmap-level events.

    Records significant events in the roadmap lifecycle.
    """

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the activity occurred"
    )
    action: ActivityType = Field(description="Type of activity")
    ticket_id: Optional[str] = Field(
        default=None,
        description="Related ticket ID if applicable"
    )
    actor: Optional[str] = Field(
        default=None,
        description="Who performed the action (agent or user)"
    )
    details: Optional[str] = Field(
        default=None,
        description="Additional details about the activity"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured context data"
    )


class PlatformDeployment(BaseModel):
    """
    Platform deployment record.

    Tracks deployment of the roadmap to different platforms.
    """

    platform: str = Field(description="Platform name (e.g., 'claude-code', 'goose')")
    context_window: Optional[int] = Field(
        default=None,
        ge=0,
        description="Platform context window size"
    )
    deployed_at: Optional[datetime] = Field(
        default=None,
        description="When deployed to this platform"
    )
    primary: bool = Field(
        default=False,
        description="Whether this is the primary platform"
    )
    version: Optional[str] = Field(
        default=None,
        description="Version deployed to this platform"
    )


class VersionStrategy(BaseModel):
    """
    Version bump strategy configuration.

    Defines when to bump each component of semantic version.
    """

    scheme: str = Field(
        default="semver",
        description="Versioning scheme (semver, calver, etc.)"
    )
    auto_bump: bool = Field(
        default=False,
        description="Whether to automatically bump version"
    )
    major_triggers: List[str] = Field(
        default_factory=list,
        description="Events that trigger major bump"
    )
    minor_triggers: List[str] = Field(
        default_factory=list,
        description="Events that trigger minor bump"
    )
    patch_triggers: List[str] = Field(
        default_factory=list,
        description="Events that trigger patch bump"
    )


# =============================================================================
# ROADMAP TICKET (ULTIMATE PARENT)
# =============================================================================


class RoadmapTicket(HierarchicalTicket):
    """
    Layer 3: RoadmapTicket - Ultimate parent in the ticket hierarchy.

    Roadmap is ALWAYS an ultimate parent (is_ultimate_parent=True).
    It cannot have a parent_ref set (validation enforced).

    Hierarchy Constraints:
    - is_ultimate_parent: True (always - no parent allowed)
    - is_parent: True (always has Track children via CompletableTarget criteria)
    - is_child: False (never - root of hierarchy)
    - is_ultimate_child: False (never - always has children)

    Roadmap-Specific Fields (L3 only):
    - ticket_type: Literal["roadmap"] = "roadmap"
    - version: Semantic version string
    - version_strategy: How to auto-bump version
    - version_history: List of past versions
    - target_completion: Target completion date
    - deployed_at: When deployed
    - deployed_platforms: Where deployed
    - activity_log: Roadmap-level events

    Children are determined by CompletableTarget criteria referencing TrackTicket IDs.
    """

    # =========================================================================
    # TYPE DISCRIMINATOR
    # =========================================================================

    ticket_type: Literal[TicketType.ROADMAP] = Field(
        default=TicketType.ROADMAP,
        description="Type discriminator for roadmap tickets"
    )

    # =========================================================================
    # VERSION MANAGEMENT
    # =========================================================================

    version: str = Field(
        default="0.1.0",
        description="Semantic version string"
    )
    version_strategy: Optional[VersionStrategy] = Field(
        default=None,
        description="Version bump strategy"
    )
    version_history: List[VersionHistoryEntry] = Field(
        default_factory=list,
        description="Historical version entries"
    )

    # =========================================================================
    # TARGET DATES
    # =========================================================================

    target_completion: Optional[datetime] = Field(
        default=None,
        description="Target date for roadmap completion"
    )

    # =========================================================================
    # DEPLOYMENT TRACKING
    # =========================================================================

    deployed_at: Optional[datetime] = Field(
        default=None,
        description="When roadmap was first deployed"
    )
    deployed_platforms: List[PlatformDeployment] = Field(
        default_factory=list,
        description="Platforms where roadmap is deployed"
    )

    # =========================================================================
    # ACTIVITY TRACKING
    # =========================================================================

    activity_log: List[ActivityLogEntry] = Field(
        default_factory=list,
        description="Roadmap-level activity log"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version follows semantic versioning format."""
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*))?(?:\+([\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*))?$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid semantic version format: {v}")
        return v

    @model_validator(mode="after")
    def validate_ultimate_parent(self) -> "RoadmapTicket":
        """Ensure RoadmapTicket is always an ultimate parent (no parent)."""
        if self.parent_ref is not None:
            raise ValueError(
                "RoadmapTicket cannot have a parent_ref. "
                "Roadmap is always the ultimate parent in the hierarchy."
            )
        return self

    # =========================================================================
    # COMPUTED PROPERTIES (Ultimate Parent Semantics)
    # =========================================================================

    @property
    def is_ultimate_parent(self) -> bool:
        """Roadmap is always the ultimate parent."""
        return True

    @property
    def is_child(self) -> bool:
        """Roadmap is never a child."""
        return False

    @property
    def is_ultimate_child(self) -> bool:
        """Roadmap is never an ultimate child (always has children)."""
        return False

    # =========================================================================
    # TYPED CHILD ACCESSOR
    # =========================================================================

    @property
    def track_criteria(self) -> List[Criterion]:
        """
        Get criteria that reference track children.

        Returns CompletableTarget criteria that block COMPLETED status,
        which represent the roadmap's track children.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def tracks_total(self) -> int:
        """Total number of track children."""
        return len(self.track_criteria)

    @property
    def tracks_completed(self) -> int:
        """Number of completed track children."""
        return sum(1 for c in self.track_criteria if c.is_met)

    def get_track_ids(self) -> List[str]:
        """
        Get IDs of track children.

        Returns list of completable_id values from track criteria.
        """
        return [
            c.target.completable_id
            for c in self.track_criteria
            if isinstance(c.target, CompletableTarget)
        ]

    # Note: get_tracks() -> List[TrackTicket] would require TrackTicket import
    # which creates circular dependency. Users should use get_track_ids() and
    # load tracks via the configured loader.

    # =========================================================================
    # VERSION MANAGEMENT METHODS
    # =========================================================================

    def bump_version(self, part: str = "patch") -> "RoadmapTicket":
        """
        Bump the version number.

        Args:
            part: Which part to bump ("major", "minor", or "patch")

        Returns:
            New RoadmapTicket with bumped version
        """
        parts = self.version.split(".")
        major = int(parts[0])
        minor = int(parts[1])
        # Handle patch with prerelease suffix
        patch_str = parts[2].split("-")[0].split("+")[0]
        patch = int(patch_str)

        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid version part: {part}. Use 'major', 'minor', or 'patch'.")

        new_version = f"{major}.{minor}.{patch}"

        # Create version history entry
        history_entry = VersionHistoryEntry(
            version=self.version,
            released_at=datetime.now(timezone.utc),
            description=f"Bumped to {new_version}",
        )

        return self.model_copy(update={
            "version": new_version,
            "version_history": self.version_history + [history_entry],
            "updated_at": datetime.now(timezone.utc),
        })

    def release(
        self,
        milestone: Optional[str] = None,
        git_tag: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "RoadmapTicket":
        """
        Create a release entry for the current version.

        Args:
            milestone: Optional milestone name
            git_tag: Optional git tag
            description: Optional release notes

        Returns:
            New RoadmapTicket with release recorded in history
        """
        history_entry = VersionHistoryEntry(
            version=self.version,
            released_at=datetime.now(timezone.utc),
            milestone=milestone,
            git_tag=git_tag,
            description=description,
        )

        return self.model_copy(update={
            "version_history": self.version_history + [history_entry],
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # ACTIVITY LOG METHODS
    # =========================================================================

    def log_activity(
        self,
        action: ActivityType,
        details: Optional[str] = None,
        ticket_id: Optional[str] = None,
        actor: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "RoadmapTicket":
        """
        Add an activity log entry.

        Args:
            action: Type of activity
            details: Additional details
            ticket_id: Related ticket ID
            actor: Who performed the action
            context: Structured context data

        Returns:
            New RoadmapTicket with activity logged
        """
        entry = ActivityLogEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            ticket_id=ticket_id,
            actor=actor,
            details=details,
            context=context,
        )

        return self.model_copy(update={
            "activity_log": self.activity_log + [entry],
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # DEPLOYMENT METHODS
    # =========================================================================

    def deploy_to_platform(
        self,
        platform: str,
        primary: bool = False,
        context_window: Optional[int] = None,
    ) -> "RoadmapTicket":
        """
        Record deployment to a platform.

        Args:
            platform: Platform name
            primary: Whether this is the primary platform
            context_window: Platform context window size

        Returns:
            New RoadmapTicket with deployment recorded
        """
        now = datetime.now(timezone.utc)

        deployment = PlatformDeployment(
            platform=platform,
            context_window=context_window,
            deployed_at=now,
            primary=primary,
            version=self.version,
        )

        # Update deployed_at if this is first deployment
        deployed_at = self.deployed_at or now

        # If setting as primary, unset other primaries
        platforms = list(self.deployed_platforms)
        if primary:
            platforms = [
                p.model_copy(update={"primary": False})
                for p in platforms
            ]
        platforms.append(deployment)

        return self.model_copy(update={
            "deployed_at": deployed_at,
            "deployed_platforms": platforms,
            "updated_at": now,
        })

    def get_primary_platform(self) -> Optional[PlatformDeployment]:
        """Get the primary deployment platform."""
        for p in self.deployed_platforms:
            if p.primary:
                return p
        return None

    # =========================================================================
    # LIFECYCLE OVERRIDES
    # =========================================================================

    def start(self) -> "RoadmapTicket":
        """Start the roadmap, logging the activity."""
        started = super().start()
        return started.log_activity(
            action=ActivityType.ROADMAP_STARTED,
            details=f"Roadmap '{self.name}' started",
        )

    def complete(self) -> "RoadmapTicket":
        """Complete the roadmap, logging the activity."""
        completed = super().complete()
        return completed.log_activity(
            action=ActivityType.ROADMAP_COMPLETED,
            details=f"Roadmap '{self.name}' completed",
        )


# =============================================================================
# TRACK TICKET (INTERMEDIATE - Has Parent and Children)
# =============================================================================


class TrackTicket(HierarchicalTicket):
    """
    Layer 3: TrackTicket - Intermediate level in the ticket hierarchy.

    Track is ALWAYS intermediate (is_intermediate=True).
    It must have a parent (Roadmap) and children (Sprints).

    Hierarchy Constraints:
    - is_intermediate: True (always - has both parent and children)
    - is_parent: True (always has Sprint children via CompletableTarget criteria)
    - is_child: True (always has Roadmap parent via parent_ref)
    - is_ultimate_parent: False (never - always has parent)
    - is_ultimate_child: False (never - always has children)

    Track-Specific Fields (L3 only):
    - ticket_type: Literal["track"] = "track"
    - roadmap_id: str (required, must match parent_ref)
    - strategic_value: List[str] (why this track matters)

    Children are determined by CompletableTarget criteria referencing SprintTicket IDs.
    """

    # =========================================================================
    # TYPE DISCRIMINATOR
    # =========================================================================

    ticket_type: Literal[TicketType.TRACK] = Field(
        default=TicketType.TRACK,
        description="Type discriminator for track tickets"
    )

    # =========================================================================
    # PARENT REFERENCE
    # =========================================================================

    roadmap_id: str = Field(
        description="ID of the parent roadmap (must match parent_ref)"
    )

    # =========================================================================
    # STRATEGIC CONTEXT
    # =========================================================================

    strategic_value: List[str] = Field(
        default_factory=list,
        description="Strategic value propositions for this track"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @model_validator(mode="after")
    def validate_intermediate(self) -> "TrackTicket":
        """Ensure TrackTicket is always intermediate (has parent)."""
        if self.parent_ref is None:
            raise ValueError(
                "TrackTicket must have a parent_ref. "
                "Track is always intermediate in the hierarchy (has a Roadmap parent)."
            )
        if self.parent_ref != self.roadmap_id:
            raise ValueError(
                f"parent_ref ({self.parent_ref}) must match roadmap_id ({self.roadmap_id})"
            )
        return self

    # =========================================================================
    # COMPUTED PROPERTIES (Intermediate Semantics)
    # =========================================================================

    @property
    def is_ultimate_parent(self) -> bool:
        """Track is never the ultimate parent (always has roadmap above)."""
        return False

    @property
    def is_child(self) -> bool:
        """Track is always a child (of roadmap)."""
        return True

    @property
    def is_ultimate_child(self) -> bool:
        """Track is never an ultimate child (always has sprints below)."""
        return False

    @property
    def is_intermediate(self) -> bool:
        """Track is always intermediate (has both parent and children)."""
        return True

    # =========================================================================
    # TYPED CHILD ACCESSOR
    # =========================================================================

    @property
    def sprint_criteria(self) -> List[Criterion]:
        """
        Get criteria that reference sprint children.

        Returns CompletableTarget criteria that block COMPLETED status,
        which represent the track's sprint children.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def sprints_total(self) -> int:
        """Total number of sprint children."""
        return len(self.sprint_criteria)

    @property
    def sprints_completed(self) -> int:
        """Number of completed sprint children."""
        return sum(1 for c in self.sprint_criteria if c.is_met)

    def get_sprint_ids(self) -> List[str]:
        """
        Get IDs of sprint children.

        Returns list of completable_id values from sprint criteria.
        """
        return [
            c.target.completable_id
            for c in self.sprint_criteria
            if isinstance(c.target, CompletableTarget)
        ]

    # =========================================================================
    # AGGREGATE PROGRESS
    # =========================================================================

    @property
    def tasks_total(self) -> int:
        """
        Total tasks across all sprints.

        Note: Requires sprints to be loaded via the configured loader.
        Returns 0 if loader not configured.
        """
        if self._loader is None:
            return 0
        total = 0
        for sprint_id in self.get_sprint_ids():
            try:
                sprint = self._loader.load(sprint_id)
                if hasattr(sprint, 'tasks_total'):
                    total += sprint.tasks_total
                else:
                    # If sprint doesn't have tasks_total, count its CompletableTarget children
                    total += len([
                        c for c in sprint.all_criteria
                        if isinstance(c.target, CompletableTarget)
                        and c.blocks_transition_to == TicketStatus.COMPLETED
                    ])
            except Exception:
                pass
        return total

    @property
    def tasks_completed(self) -> int:
        """
        Completed tasks across all sprints.

        Note: Requires sprints to be loaded via the configured loader.
        Returns 0 if loader not configured.
        """
        if self._loader is None:
            return 0
        completed = 0
        for sprint_id in self.get_sprint_ids():
            try:
                sprint = self._loader.load(sprint_id)
                if hasattr(sprint, 'tasks_completed'):
                    completed += sprint.tasks_completed
                else:
                    # If sprint doesn't have tasks_completed, count met criteria
                    completed += sum(
                        1 for c in sprint.all_criteria
                        if isinstance(c.target, CompletableTarget)
                        and c.blocks_transition_to == TicketStatus.COMPLETED
                        and c.is_met
                    )
            except Exception:
                pass
        return completed


# =============================================================================
# SPRINT-SPECIFIC SUPPORT CLASSES
# =============================================================================


class DevelopmentGate(BaseModel):
    """
    Sprint-specific blocking condition.

    Development gates are used to track sprint-level quality checkpoints
    that must be passed before the sprint can complete.
    """

    name: str = Field(description="Gate name (e.g., 'code_review', 'security_audit')")
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the gate"
    )
    status: GateStatus = Field(
        default=GateStatus.NOT_STARTED,
        description="Current gate status"
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When the gate was resolved (passed or failed)"
    )
    blocking: bool = Field(
        default=True,
        description="Whether this gate blocks sprint completion"
    )
    resolver: Optional[str] = Field(
        default=None,
        description="Who/what resolved the gate"
    )

    @model_validator(mode="after")
    def validate_resolved_timestamp(self) -> "DevelopmentGate":
        """Ensure resolved_at is set when status is resolved."""
        if self.status.is_resolved() and self.resolved_at is None:
            # Auto-set resolved_at if status is resolved but timestamp missing
            object.__setattr__(self, "resolved_at", datetime.now(timezone.utc))
        return self

    def pass_gate(self, resolver: Optional[str] = None) -> "DevelopmentGate":
        """Mark gate as passed."""
        return self.model_copy(update={
            "status": GateStatus.PASSED,
            "resolved_at": datetime.now(timezone.utc),
            "resolver": resolver,
        })

    def fail_gate(self, resolver: Optional[str] = None) -> "DevelopmentGate":
        """Mark gate as failed."""
        return self.model_copy(update={
            "status": GateStatus.FAILED,
            "resolved_at": datetime.now(timezone.utc),
            "resolver": resolver,
        })


# =============================================================================
# SPRINT TICKET (INTERMEDIATE - Has Parent and Children)
# =============================================================================


class SprintTicket(HierarchicalTicket):
    """
    Layer 3: SprintTicket - Intermediate level in the ticket hierarchy.

    Sprint is ALWAYS intermediate (is_intermediate=True).
    It must have a parent (Track) and children (Tasks).

    Hierarchy Constraints:
    - is_intermediate: True (always - has both parent and children)
    - is_parent: True (always has Task children via CompletableTarget criteria)
    - is_child: True (always has Track parent via parent_ref)
    - is_ultimate_parent: False (never - always has parent)
    - is_ultimate_child: False (never - always has children)

    Sprint-Specific Fields (L3 only):
    - ticket_type: Literal["sprint"] = "sprint"
    - track_id: str (required, must match parent_ref)
    - roadmap_id: str (required, grandparent reference)
    - Extended lifecycle timestamps (completion_gate_check_at, production_gate_check_at, etc.)
    - Planning fields (plan_file, goal, success_criteria_text, risks)
    - Estimation fields (estimated_tokens, actual_tokens)
    - development_gates: List[DevelopmentGate] (sprint-specific blocking)

    Children are determined by CompletableTarget criteria referencing TaskTicket IDs.
    """

    # =========================================================================
    # TYPE DISCRIMINATOR
    # =========================================================================

    ticket_type: Literal[TicketType.SPRINT] = Field(
        default=TicketType.SPRINT,
        description="Type discriminator for sprint tickets"
    )

    # =========================================================================
    # PARENT REFERENCES
    # =========================================================================

    track_id: str = Field(
        description="ID of the parent track (must match parent_ref)"
    )
    roadmap_id: str = Field(
        description="ID of the grandparent roadmap"
    )

    # =========================================================================
    # EXTENDED LIFECYCLE TIMESTAMPS
    # =========================================================================

    completion_gate_check_at: Optional[datetime] = Field(
        default=None,
        description="When completion gate check started"
    )
    production_gate_check_at: Optional[datetime] = Field(
        default=None,
        description="When production gate check started"
    )
    production_ready_at: Optional[datetime] = Field(
        default=None,
        description="When sprint became production ready"
    )
    deployed_at: Optional[datetime] = Field(
        default=None,
        description="When sprint was deployed"
    )

    # =========================================================================
    # PLANNING FIELDS
    # =========================================================================

    plan_file: Optional[str] = Field(
        default=None,
        description="Path to sprint plan document"
    )
    goal: Optional[str] = Field(
        default=None,
        description="Sprint objective/goal"
    )
    success_criteria_text: List[str] = Field(
        default_factory=list,
        description="Human-readable success criteria (legacy, use criteria field instead)"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Identified risks for this sprint"
    )

    # =========================================================================
    # ESTIMATION FIELDS
    # =========================================================================

    estimated_tokens: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated token budget for sprint"
    )
    actual_tokens: Optional[int] = Field(
        default=None,
        ge=0,
        description="Actual tokens used"
    )

    # =========================================================================
    # DEVELOPMENT GATES
    # =========================================================================

    development_gates: List[DevelopmentGate] = Field(
        default_factory=list,
        description="Sprint-level quality gates"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @model_validator(mode="after")
    def validate_intermediate(self) -> "SprintTicket":
        """Ensure SprintTicket is always intermediate (has parent)."""
        if self.parent_ref is None:
            raise ValueError(
                "SprintTicket must have a parent_ref. "
                "Sprint is always intermediate in the hierarchy (has a Track parent)."
            )
        if self.parent_ref != self.track_id:
            raise ValueError(
                f"parent_ref ({self.parent_ref}) must match track_id ({self.track_id})"
            )
        return self

    @model_validator(mode="after")
    def validate_extended_lifecycle_order(self) -> "SprintTicket":
        """Validate extended lifecycle timestamps are in order."""
        # The order should be: started -> completed -> completion_gate_check ->
        # production_gate_check -> production_ready -> deployed
        timestamps = [
            ("started_at", self.started_at),
            ("completed_at", self.completed_at),
            ("completion_gate_check_at", self.completion_gate_check_at),
            ("production_gate_check_at", self.production_gate_check_at),
            ("production_ready_at", self.production_ready_at),
            ("deployed_at", self.deployed_at),
        ]

        prev_name = None
        prev_ts = None
        for name, ts in timestamps:
            if ts is not None:
                if prev_ts is not None and ts < prev_ts:
                    raise ValueError(
                        f"{name} cannot be before {prev_name}"
                    )
                prev_name = name
                prev_ts = ts
        return self

    @field_validator("track_id", "roadmap_id")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate required IDs are not empty."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v

    # =========================================================================
    # COMPUTED PROPERTIES (Intermediate Semantics)
    # =========================================================================

    @property
    def is_ultimate_parent(self) -> bool:
        """Sprint is never the ultimate parent (always has track above)."""
        return False

    @property
    def is_child(self) -> bool:
        """Sprint is always a child (of track)."""
        return True

    @property
    def is_ultimate_child(self) -> bool:
        """Sprint is never an ultimate child (always has tasks below)."""
        return False

    @property
    def is_intermediate(self) -> bool:
        """Sprint is always intermediate (has both parent and children)."""
        return True

    # =========================================================================
    # TYPED CHILD ACCESSOR
    # =========================================================================

    @property
    def task_criteria(self) -> List[Criterion]:
        """
        Get criteria that reference task children.

        Returns CompletableTarget criteria that block COMPLETED status,
        which represent the sprint's task children.
        """
        return [
            c for c in self.all_criteria
            if isinstance(c.target, CompletableTarget)
            and c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def tasks_total(self) -> int:
        """Total number of task children."""
        return len(self.task_criteria)

    @property
    def tasks_completed(self) -> int:
        """Number of completed task children."""
        return sum(1 for c in self.task_criteria if c.is_met)

    def get_task_ids(self) -> List[str]:
        """
        Get IDs of task children.

        Returns list of completable_id values from task criteria.
        """
        return [
            c.target.completable_id
            for c in self.task_criteria
            if isinstance(c.target, CompletableTarget)
        ]

    # =========================================================================
    # DEVELOPMENT GATE METHODS
    # =========================================================================

    @property
    def blocking_gates(self) -> List[DevelopmentGate]:
        """Get gates that are currently blocking."""
        return [g for g in self.development_gates if g.blocking and g.status.is_blocking()]

    @property
    def all_gates_passed(self) -> bool:
        """Check if all blocking gates have passed."""
        return all(
            not g.blocking or g.status == GateStatus.PASSED
            for g in self.development_gates
        )

    def add_gate(
        self,
        name: str,
        description: Optional[str] = None,
        blocking: bool = True,
    ) -> "SprintTicket":
        """Add a new development gate."""
        gate = DevelopmentGate(
            name=name,
            description=description,
            blocking=blocking,
        )
        return self.model_copy(update={
            "development_gates": self.development_gates + [gate],
            "updated_at": datetime.now(timezone.utc),
        })

    def resolve_gate(
        self,
        gate_name: str,
        passed: bool,
        resolver: Optional[str] = None,
    ) -> "SprintTicket":
        """Resolve a development gate by name."""
        new_gates = []
        found = False
        for gate in self.development_gates:
            if gate.name == gate_name:
                found = True
                if passed:
                    new_gates.append(gate.pass_gate(resolver))
                else:
                    new_gates.append(gate.fail_gate(resolver))
            else:
                new_gates.append(gate)

        if not found:
            raise ValueError(f"Gate '{gate_name}' not found")

        return self.model_copy(update={
            "development_gates": new_gates,
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # LIFECYCLE TRANSITION CHECKS
    # =========================================================================

    def can_enter_completion_gate_check(self) -> bool:
        """
        Check if sprint can enter completion gate check.

        Requires all development tasks to be complete.
        """
        return self.tasks_total > 0 and self.tasks_completed == self.tasks_total

    def can_complete(self) -> tuple[bool, list[str]]:
        """
        Check if sprint can be marked complete.

        Requires all tasks done AND all development gates passed.

        Returns:
            Tuple of (can_complete, list of blocking reasons)
        """
        # First check base class criteria
        base_can, base_reasons = super().can_complete()

        # Add sprint-specific checks
        reasons = list(base_reasons)

        if not self.can_enter_completion_gate_check():
            reasons.append(
                f"Not all tasks completed: {self.tasks_completed}/{self.tasks_total}"
            )

        if not self.all_gates_passed:
            blocking_gate_names = [g.name for g in self.blocking_gates]
            reasons.append(
                f"Blocking gates not passed: {', '.join(blocking_gate_names)}"
            )

        return len(reasons) == 0, reasons

    def can_be_production_ready(self) -> bool:
        """
        Check if sprint can be marked production ready.

        Requires completion and all gates passed.
        """
        return self.can_complete()

    # =========================================================================
    # EXTENDED LIFECYCLE METHODS
    # =========================================================================

    def enter_completion_gate_check(self) -> "SprintTicket":
        """
        Transition to completion gate check status.

        Raises ValueError if dev tasks not complete.
        """
        if not self.can_enter_completion_gate_check():
            raise ValueError(
                f"Cannot enter completion gate check: "
                f"{self.tasks_completed}/{self.tasks_total} tasks completed"
            )

        now = datetime.now(timezone.utc)
        return self.model_copy(update={
            "status": TicketStatus.COMPLETION_GATE_CHECK,
            "completion_gate_check_at": now,
            "updated_at": now,
        })

    def enter_production_gate_check(self) -> "SprintTicket":
        """
        Transition to production gate check status.

        Raises ValueError if completion gate not passed.
        """
        if self.status != TicketStatus.COMPLETED:
            raise ValueError(
                "Cannot enter production gate check: sprint must be completed first"
            )

        now = datetime.now(timezone.utc)
        return self.model_copy(update={
            "status": TicketStatus.PRODUCTION_GATE_CHECK,
            "production_gate_check_at": now,
            "updated_at": now,
        })

    def mark_production_ready(self) -> "SprintTicket":
        """
        Mark sprint as production ready.

        Raises ValueError if not in production gate check.
        """
        if self.status != TicketStatus.PRODUCTION_GATE_CHECK:
            raise ValueError(
                "Cannot mark production ready: must be in production gate check status"
            )

        now = datetime.now(timezone.utc)
        return self.model_copy(update={
            "status": TicketStatus.PRODUCTION_READY,
            "production_ready_at": now,
            "updated_at": now,
        })

    def deploy(self) -> "SprintTicket":
        """
        Mark sprint as deployed.

        Raises ValueError if not production ready.
        """
        if self.status != TicketStatus.PRODUCTION_READY:
            raise ValueError(
                "Cannot deploy: must be production ready first"
            )

        now = datetime.now(timezone.utc)
        return self.model_copy(update={
            "status": TicketStatus.DEPLOYED,
            "deployed_at": now,
            "updated_at": now,
        })


# =============================================================================
# TASK-SPECIFIC SUPPORT CLASSES
# =============================================================================


class GateInfo(BaseModel):
    """
    Information about a quality gate task.

    Gate tasks are special tasks that validate quality criteria
    before a sprint can progress to the next status.
    """

    blocks_status: TicketStatus = Field(
        description="The status transition this gate blocks"
    )
    threshold: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Pass threshold (0-100)"
    )
    is_blocking: bool = Field(
        default=True,
        description="Whether this gate blocks sprint progress"
    )
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Current score (0-100)"
    )
    evaluated_at: Optional[datetime] = Field(
        default=None,
        description="When the gate was last evaluated"
    )

    def has_passed(self) -> bool:
        """Check if the gate has passed based on score and threshold."""
        if self.score is None:
            return False
        return self.score >= self.threshold

    def evaluate(self, score: float) -> "GateInfo":
        """Record an evaluation with a score."""
        return self.model_copy(update={
            "score": score,
            "evaluated_at": datetime.now(timezone.utc),
        })


class AuditResults(BaseModel):
    """
    Results from a quality audit task.

    Audit tasks examine code, documentation, or other artifacts
    for issues that need to be addressed.
    """

    issues_found: int = Field(
        default=0,
        ge=0,
        description="Number of issues found during audit"
    )
    issues_fixed: int = Field(
        default=0,
        ge=0,
        description="Number of issues that have been fixed"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations from the audit"
    )
    audit_type: str = Field(
        description="Type of audit (e.g., 'security', 'code_quality', 'documentation')"
    )
    audited_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the audit was performed"
    )

    @property
    def issues_remaining(self) -> int:
        """Number of issues that still need to be fixed."""
        return max(0, self.issues_found - self.issues_fixed)

    @property
    def is_resolved(self) -> bool:
        """Check if all issues have been resolved."""
        return self.issues_remaining == 0


# =============================================================================
# SIZE CATEGORY (computed from token estimate)
# =============================================================================


class SizeCategory(str, Enum):
    """
    Size category computed from estimated tokens.

    Used to categorize tasks by their estimated effort.
    """

    TINY = "tiny"  # < 500 tokens
    SMALL = "small"  # 500-1000 tokens
    MEDIUM = "medium"  # 1000-2500 tokens
    LARGE = "large"  # 2500-5000 tokens
    HUGE = "huge"  # > 5000 tokens

    @classmethod
    def from_tokens(cls, tokens: int) -> "SizeCategory":
        """Compute size category from token estimate."""
        if tokens < 500:
            return cls.TINY
        elif tokens < 1000:
            return cls.SMALL
        elif tokens < 2500:
            return cls.MEDIUM
        elif tokens < 5000:
            return cls.LARGE
        else:
            return cls.HUGE


# =============================================================================
# TASK TICKET (ULTIMATE CHILD - Leaf Node)
# =============================================================================


class TaskTicket(HierarchicalTicket):
    """
    Layer 3: TaskTicket - Ultimate child in the ticket hierarchy.

    Task is ALWAYS an ultimate child (is_ultimate_child=True).
    It cannot have children (no CompletableTarget criteria allowed).

    Hierarchy Constraints:
    - is_ultimate_child: True (always - leaf node)
    - is_child: True (always has Sprint parent via parent_ref)
    - is_parent: False (never - cannot have children)
    - is_ultimate_parent: False (never - always has parent)
    - is_intermediate: False (never - leaf node)

    Task-Specific Fields (L3 only):
    - ticket_type: Literal["task"] = "task"
    - sprint_id: str (required, must match parent_ref)
    - track_id: str (required, grandparent reference)
    - roadmap_id: str (required, root reference)
    - task_type_detail: TaskType enum
    - title: str (alias for name, short task title)
    - assigned_agent: Optional[str]
    - estimated_tokens: int (required, > 0)
    - actual_tokens: Optional[int]
    - complexity: Complexity enum
    - gate_info: Optional[GateInfo] (for gate tasks)
    - audit_results: Optional[AuditResults] (for audit tasks)
    - phase_label: Optional[str]

    Children are NOT allowed (leaf node). Validation ensures no CompletableTarget criteria.
    """

    # =========================================================================
    # TYPE DISCRIMINATOR
    # =========================================================================

    ticket_type: Literal[TicketType.TASK] = Field(
        default=TicketType.TASK,
        description="Type discriminator for task tickets"
    )

    # =========================================================================
    # PARENT REFERENCES
    # =========================================================================

    sprint_id: str = Field(
        description="ID of the parent sprint (must match parent_ref)"
    )
    track_id: str = Field(
        description="ID of the grandparent track"
    )
    roadmap_id: str = Field(
        description="ID of the root roadmap"
    )

    # =========================================================================
    # TASK CLASSIFICATION
    # =========================================================================

    task_type_detail: TaskType = Field(
        default=TaskType.DEVELOPMENT,
        description="Classification of task work type"
    )
    title: str = Field(
        default="",
        description="Short task title (alias for name)"
    )
    phase_label: Optional[str] = Field(
        default=None,
        description="Phase or category label for grouping"
    )

    # =========================================================================
    # ASSIGNMENT
    # =========================================================================

    assigned_agent: Optional[str] = Field(
        default=None,
        description="Single agent assigned to this task"
    )

    # =========================================================================
    # ESTIMATION
    # =========================================================================

    estimated_tokens: int = Field(
        gt=0,
        description="Estimated token budget for task"
    )
    actual_tokens: Optional[int] = Field(
        default=None,
        ge=0,
        description="Actual tokens used"
    )
    complexity: Complexity = Field(
        default=Complexity.MEDIUM,
        description="Task complexity level"
    )

    # =========================================================================
    # GATE-SPECIFIC FIELDS
    # =========================================================================

    gate_info: Optional[GateInfo] = Field(
        default=None,
        description="Gate information (for gate tasks only)"
    )
    audit_results: Optional[AuditResults] = Field(
        default=None,
        description="Audit results (for audit tasks)"
    )

    # =========================================================================
    # VALIDATORS
    # =========================================================================

    @model_validator(mode="after")
    def validate_ultimate_child(self) -> "TaskTicket":
        """Ensure TaskTicket is always an ultimate child (has parent, no children)."""
        if self.parent_ref is None:
            raise ValueError(
                "TaskTicket must have a parent_ref. "
                "Task is always an ultimate child (has a Sprint parent)."
            )
        if self.parent_ref != self.sprint_id:
            raise ValueError(
                f"parent_ref ({self.parent_ref}) must match sprint_id ({self.sprint_id})"
            )
        return self

    @model_validator(mode="after")
    def validate_no_completable_children(self) -> "TaskTicket":
        """Ensure TaskTicket has no CompletableTarget criteria (leaf node)."""
        for criterion in self.criteria:
            if isinstance(criterion.target, CompletableTarget):
                raise ValueError(
                    f"TaskTicket cannot have CompletableTarget criteria. "
                    f"Found criterion '{criterion.id}' with CompletableTarget. "
                    f"Tasks are leaf nodes and cannot have child tickets."
                )
        return self

    @model_validator(mode="after")
    def validate_gate_info_consistency(self) -> "TaskTicket":
        """Ensure gate_info matches task_type_detail."""
        if self.task_type_detail == TaskType.GATE:
            if self.gate_info is None:
                raise ValueError(
                    "Gate tasks must have gate_info set"
                )
        else:
            if self.gate_info is not None:
                raise ValueError(
                    f"Non-gate tasks ({self.task_type_detail}) cannot have gate_info"
                )
        return self

    @field_validator("sprint_id", "track_id", "roadmap_id")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate required IDs are not empty."""
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v

    # =========================================================================
    # COMPUTED PROPERTIES (Ultimate Child Semantics)
    # =========================================================================

    @property
    def is_ultimate_parent(self) -> bool:
        """Task is never the ultimate parent."""
        return False

    @property
    def is_child(self) -> bool:
        """Task is always a child (of sprint)."""
        return True

    @property
    def is_ultimate_child(self) -> bool:
        """Task is always the ultimate child (leaf node)."""
        return True

    @property
    def is_intermediate(self) -> bool:
        """Task is never intermediate (leaf node)."""
        return False

    @property
    def is_parent(self) -> bool:
        """Task is never a parent (leaf node)."""
        return False

    # Override children to always return empty list
    @property
    def children(self) -> List[str]:
        """Tasks have no children (leaf node)."""
        return []

    # =========================================================================
    # TASK-SPECIFIC COMPUTED PROPERTIES
    # =========================================================================

    @property
    def token_efficiency(self) -> Optional[float]:
        """
        Compute token efficiency (actual / estimated).

        Returns None if actual_tokens not set.
        < 1.0 means under budget, > 1.0 means over budget.
        """
        if self.actual_tokens is None:
            return None
        return self.actual_tokens / self.estimated_tokens

    @property
    def size_category(self) -> SizeCategory:
        """Compute size category from estimated tokens."""
        return SizeCategory.from_tokens(self.estimated_tokens)

    # =========================================================================
    # TASK TYPE HELPERS
    # =========================================================================

    def is_development_task(self) -> bool:
        """Check if this is a development task."""
        return self.task_type_detail == TaskType.DEVELOPMENT

    def is_quality_gate(self) -> bool:
        """Check if this is a quality gate task."""
        return self.task_type_detail == TaskType.GATE

    def is_documentation_task(self) -> bool:
        """Check if this is a documentation task."""
        return self.task_type_detail == TaskType.DOCUMENTATION

    def is_testing_task(self) -> bool:
        """Check if this is a testing task."""
        return self.task_type_detail == TaskType.TESTING

    def has_passed_gate(self) -> bool:
        """
        Check if gate has passed (for gate tasks).

        Returns False for non-gate tasks.
        """
        if not self.is_quality_gate() or self.gate_info is None:
            return False
        return self.gate_info.has_passed()

    # =========================================================================
    # GATE MANAGEMENT
    # =========================================================================

    def evaluate_gate(self, score: float) -> "TaskTicket":
        """
        Evaluate the gate with a score.

        Raises ValueError if not a gate task.
        """
        if not self.is_quality_gate():
            raise ValueError(
                f"Cannot evaluate gate: task '{self.id}' is not a gate task"
            )

        return self.model_copy(update={
            "gate_info": self.gate_info.evaluate(score),
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # AUDIT MANAGEMENT
    # =========================================================================

    def record_audit(
        self,
        audit_type: str,
        issues_found: int = 0,
        recommendations: Optional[List[str]] = None,
    ) -> "TaskTicket":
        """Record audit results for this task."""
        audit = AuditResults(
            audit_type=audit_type,
            issues_found=issues_found,
            recommendations=recommendations or [],
        )
        return self.model_copy(update={
            "audit_results": audit,
            "updated_at": datetime.now(timezone.utc),
        })

    def fix_audit_issue(self) -> "TaskTicket":
        """Record that an audit issue has been fixed."""
        if self.audit_results is None:
            raise ValueError(
                f"Cannot fix audit issue: task '{self.id}' has no audit results"
            )

        return self.model_copy(update={
            "audit_results": self.audit_results.model_copy(update={
                "issues_fixed": self.audit_results.issues_fixed + 1,
            }),
            "updated_at": datetime.now(timezone.utc),
        })

    # =========================================================================
    # TOKEN TRACKING
    # =========================================================================

    def record_tokens(self, tokens: int) -> "TaskTicket":
        """Record actual tokens used."""
        return self.model_copy(update={
            "actual_tokens": tokens,
            "updated_at": datetime.now(timezone.utc),
        })


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Support classes
    "VersionHistoryEntry",
    "ActivityLogEntry",
    "PlatformDeployment",
    "VersionStrategy",
    "DevelopmentGate",
    "GateInfo",
    "AuditResults",
    "SizeCategory",
    # Domain models
    "RoadmapTicket",
    "TrackTicket",
    "SprintTicket",
    "TaskTicket",
]
