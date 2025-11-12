"""
Roadmap Object Hierarchy - Data Models

This package contains Python dataclasses for the roadmap system.
These models map to the YAML schemas and provide type-safe access to roadmap data.

Version: 2.1 (Gate Model)

---

## Design Decision: Dataclasses vs Pydantic

This module uses **dataclasses** with manual validation, NOT Pydantic.

**Why dataclasses?**
- Framework internals (not user-facing)
- Trusted data source (created by framework scripts)
- Zero external dependencies (built-in Python)
- Explicit validation in __post_init__ methods

**Why NOT Pydantic?**
- Would add external dependency to framework core
- Rich error messages not needed (data is trusted)
- Type coercion not needed (we control the format)
- Current implementation works correctly

**Contrast with Config System:**
The config system (vibey/config/) DOES use Pydantic because:
- User-facing (users edit YAML files directly)
- Untrusted data source (users make mistakes)
- Rich validation errors improve UX
- Type coercion helps handle user input

**Framework Principle:**
"Right tool for the job"
- Framework internals → Dataclasses (minimal deps)
- User-facing features → Pydantic (better UX)

See: vibey/config/DESIGN_DECISIONS.md for detailed rationale
See: vibey/roadmap/DESIGN_DECISIONS.md for roadmap-specific decisions
"""

from .roadmap import (
    Roadmap,
    VersionStrategy,
    Progress,
    TrackSummary,
    Dependency,
    Blocker,
    VersionHistoryEntry,
    ActivityLogEntry,
    Metadata,
)

from .track import (
    Track,
    TrackProgress,
    SprintSummary,
    TrackDependency,
    TrackBlocker,
    QualityGate,
    TrackMetadata,
)

from .sprint import (
    Sprint,
    SprintProgress,
    TaskSummary,
    DevelopmentGate,
    SprintMetadata,
)

from .task import (
    Task,
    GateInfo,
    AuditResults,
    TaskDependency,
    TaskBlocker,
    Deliverable,
    GitCommit,
    TaskCompletionCommit,
    SprintCompletionCommit,
    TaskMetadata,
)

from .common import (
    Status,
    TaskStatus,
    Priority,
    TaskType,
    GateStatus,
    DependencyType,
    Complexity,
    DeliverableType,
    ActivityType,
    VersionBumpTrigger,
    DependencyStatus,
    PlatformDeployment,
)

from .standard import (
    Standard,
    StandardType,
    EnforcementMode,
    StandardOverride,
)

__all__ = [
    # Roadmap
    "Roadmap",
    "VersionStrategy",
    "Progress",
    "TrackSummary",
    "Dependency",
    "Blocker",
    "VersionHistoryEntry",
    "ActivityLogEntry",
    "Metadata",
    # Track
    "Track",
    "TrackProgress",
    "SprintSummary",
    "TrackDependency",
    "TrackBlocker",
    "QualityGate",
    "TrackMetadata",
    # Sprint
    "Sprint",
    "SprintProgress",
    "TaskSummary",
    "DevelopmentGate",
    "SprintMetadata",
    # Task
    "Task",
    "GateInfo",
    "AuditResults",
    "TaskDependency",
    "TaskBlocker",
    "Deliverable",
    "GitCommit",
    "TaskCompletionCommit",
    "SprintCompletionCommit",
    "TaskMetadata",
    # Common
    "Status",
    "TaskStatus",
    "Priority",
    "TaskType",
    "GateStatus",
    "DependencyType",
    "Complexity",
    "DeliverableType",
    "ActivityType",
    "VersionBumpTrigger",
    "DependencyStatus",
    "PlatformDeployment",
    # Standard
    "Standard",
    "StandardType",
    "EnforcementMode",
    "StandardOverride",
]

__version__ = "2.1"
