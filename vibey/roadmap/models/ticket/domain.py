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
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import ActivityType, TicketStatus, TicketType
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
# EXPORTS
# =============================================================================

__all__ = [
    # Support classes
    "VersionHistoryEntry",
    "ActivityLogEntry",
    "PlatformDeployment",
    "VersionStrategy",
    # Domain models
    "RoadmapTicket",
    # Future exports (Tasks 009-011):
    # "TrackTicket",
    # "SprintTicket",
    # "TaskTicket",
]
