"""
Unified Ticket Architecture models.

This package contains the model classes for the unified ticket architecture,
implementing the three-layer design:

Layer 0: Completable - Base class for anything with criteria
Layer 1: Ticket - Work items with lifecycle semantics
Layer 2: HierarchicalTicket - Parent-child navigation
Layer 3: Domain Models - RoadmapTicket, TrackTicket, SprintTicket, TaskTicket

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from vibey.roadmap.models.ticket.enums import (
    # Ticket lifecycle
    TicketStatus,
    TicketType,
    # Task classification
    TaskType,
    Complexity,
    Priority,
    # Criterion targets
    CriterionTargetType,
    ThresholdComparison,
    # Requirement system
    InheritMode,
    EnforcementMode,
    RequirementType,
    # Dependencies
    DependencyRelation,
    # Deliverables
    DeliverableType,
    # Activity log
    ActivityType,
)

from vibey.roadmap.models.ticket.support import (
    Progress,
    TestResult,
)

from vibey.roadmap.models.ticket.targets import (
    # Base class
    CriterionTarget,
    # Target types
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    TestCoverageTarget,
    ThresholdTarget,
    ManualTarget,
    ExternalTarget,
    # Union type
    AnyTarget,
    # Factory function
    create_target,
)

from vibey.roadmap.models.ticket.completable import (
    Completable,
    Criterion,
)

from vibey.roadmap.models.ticket.requirements import (
    CriterionTemplate,
    ApplicabilityRules,
    Requirement,
    RequirementResolver,
    RequirementInstantiator,
)

from vibey.roadmap.models.ticket.ticket import (
    GitCommit,
    Ticket,
)

__all__ = [
    # Enums - Ticket lifecycle
    "TicketStatus",
    "TicketType",
    # Enums - Task classification
    "TaskType",
    "Complexity",
    "Priority",
    # Enums - Criterion targets
    "CriterionTargetType",
    "ThresholdComparison",
    # Enums - Requirement system
    "InheritMode",
    "EnforcementMode",
    "RequirementType",
    # Enums - Dependencies
    "DependencyRelation",
    # Enums - Deliverables
    "DeliverableType",
    # Enums - Activity log
    "ActivityType",
    # Support classes
    "Progress",
    "TestResult",
    # Target types
    "CriterionTarget",
    "CompletableTarget",
    "FileExistsTarget",
    "TestPassesTarget",
    "TestCoverageTarget",
    "ThresholdTarget",
    "ManualTarget",
    "ExternalTarget",
    "AnyTarget",
    "create_target",
    # Core classes
    "Completable",
    "Criterion",
    # Requirement system
    "CriterionTemplate",
    "ApplicabilityRules",
    "Requirement",
    "RequirementResolver",
    "RequirementInstantiator",
    # Layer 1: Ticket
    "GitCommit",
    "Ticket",
]
