"""
Roadmap Object Hierarchy - Data Models

This package contains Python dataclasses for the roadmap system.
These models map to the YAML schemas and provide type-safe access to roadmap data.

Version: 2.1 (Gate Model)
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
    TaskMetadata,
)

from .common import (
    Status,
    Priority,
    TaskType,
    GateStatus,
    DependencyType,
    Complexity,
    DeliverableType,
    ActivityType,
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
    "TaskMetadata",
    # Common
    "Status",
    "Priority",
    "TaskType",
    "GateStatus",
    "DependencyType",
    "Complexity",
    "DeliverableType",
    "ActivityType",
]

__version__ = "2.1"
