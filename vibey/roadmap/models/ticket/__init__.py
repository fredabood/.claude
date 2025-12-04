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
    # Gate status
    GateStatus,
    # Dependencies
    DependencyRelation,
    # Deliverables
    DeliverableType,
    # Activity log
    ActivityType,
)

from vibey.roadmap.models.ticket.artifact_enums import (
    # Artifact classification
    ArtifactType,
    ProvenanceType,
    ArtifactVerification,
    # Artifact subtypes
    ContextArtifactSubtype,
    DocumentationSubtype,
    # Documentation health
    DocumentationHealth,
)

from vibey.roadmap.models.ticket.support import (
    Progress,
    TestResult,
    RefreshContext,
    TicketRegistry,
    TestRunner,
    MetricsSource,
    HttpClient,
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

from vibey.roadmap.models.ticket.hierarchical import (
    HierarchicalTicket,
    TicketLoader,
    SiblingLoader,
)

from vibey.roadmap.models.ticket.domain import (
    # Support classes
    VersionHistoryEntry,
    ActivityLogEntry,
    PlatformDeployment,
    VersionStrategy,
    DevelopmentGate,
    GateInfo,
    AuditResults,
    SizeCategory,
    # Domain models
    RoadmapTicket,
    TrackTicket,
    SprintTicket,
    TaskTicket,
)

from vibey.roadmap.models.ticket.orm import (
    # Base
    Base,
    # ORM Models
    TicketORM,
    RoadmapTicketORM,
    TrackTicketORM,
    SprintTicketORM,
    TaskTicketORM,
    CriterionORM,
    # Serialization
    deserialize_target,
    serialize_target,
    # Schema
    get_unified_schema_ddl,
    create_unified_schema,
    # Factory
    get_ticket_orm_class,
)

from vibey.roadmap.models.ticket.repository import (
    # Connection
    get_engine,
    get_session_factory,
    # Repositories
    TicketRepository,
    CriterionRepository,
    # Factory
    RepositoryFactory,
)

from vibey.roadmap.models.ticket.adapters import (
    # Status mapping
    map_status_to_ticket_status,
    map_ticket_status_to_status,
    map_priority,
    map_task_type,
    # Criterion generation
    children_to_criteria,
    dependencies_to_criteria,
    deliverables_to_criteria,
    # Criterion extraction
    extract_child_ids,
    extract_dependency_ids,
    extract_deliverable_paths,
    # Main adapter
    ModelAdapter,
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
    # Enums - Gate status
    "GateStatus",
    # Enums - Dependencies
    "DependencyRelation",
    # Enums - Deliverables
    "DeliverableType",
    # Enums - Activity log
    "ActivityType",
    # Enums - Artifact system
    "ArtifactType",
    "ProvenanceType",
    "ArtifactVerification",
    "ContextArtifactSubtype",
    "DocumentationSubtype",
    "DocumentationHealth",
    # Support classes
    "Progress",
    "TestResult",
    "RefreshContext",
    "TicketRegistry",
    "TestRunner",
    "MetricsSource",
    "HttpClient",
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
    # Layer 2: HierarchicalTicket
    "HierarchicalTicket",
    "TicketLoader",
    "SiblingLoader",
    # Layer 3: Domain Models - Support classes
    "VersionHistoryEntry",
    "ActivityLogEntry",
    "PlatformDeployment",
    "VersionStrategy",
    "DevelopmentGate",
    "GateInfo",
    "AuditResults",
    "SizeCategory",
    # Layer 3: Domain Models
    "RoadmapTicket",
    "TrackTicket",
    "SprintTicket",
    "TaskTicket",
    # ORM - Base
    "Base",
    # ORM - Models
    "TicketORM",
    "RoadmapTicketORM",
    "TrackTicketORM",
    "SprintTicketORM",
    "TaskTicketORM",
    "CriterionORM",
    # ORM - Serialization
    "deserialize_target",
    "serialize_target",
    # ORM - Schema
    "get_unified_schema_ddl",
    "create_unified_schema",
    # ORM - Factory
    "get_ticket_orm_class",
    # Repository - Connection
    "get_engine",
    "get_session_factory",
    # Repository - Classes
    "TicketRepository",
    "CriterionRepository",
    # Repository - Factory
    "RepositoryFactory",
    # Adapters - Status mapping
    "map_status_to_ticket_status",
    "map_ticket_status_to_status",
    "map_priority",
    "map_task_type",
    # Adapters - Criterion generation
    "children_to_criteria",
    "dependencies_to_criteria",
    "deliverables_to_criteria",
    # Adapters - Criterion extraction
    "extract_child_ids",
    "extract_dependency_ids",
    "extract_deliverable_paths",
    # Adapters - Main class
    "ModelAdapter",
]
