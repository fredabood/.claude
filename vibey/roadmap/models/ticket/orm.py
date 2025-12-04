"""
SQLAlchemy ORM models for the unified ticket architecture.

This module provides SQLAlchemy ORM models that map to the Pydantic models
in the ticket package. The design uses:

1. Single-Table Inheritance for Tickets
   - One `tickets` table with discriminator column
   - All ticket types share common columns
   - Type-specific columns nullable

2. Separate Criteria Table (polymorphic targets)
   - Criteria stored with polymorphic target types as JSON
   - blocks_transition_to determines what the criterion blocks

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
Task Reference: sqlite-backend-6-task-012
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    declared_attr,
    mapped_column,
    relationship,
)
from sqlalchemy.types import JSON

from vibey.roadmap.models.ticket.enums import (
    Complexity,
    DeliverableType,
    GateStatus,
    Priority,
    TaskType,
    TicketStatus,
    TicketType,
    ThresholdComparison,
)


# =============================================================================
# BASE CLASS
# =============================================================================


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for ticket models."""
    pass


# =============================================================================
# TICKET ORM (Single-Table Inheritance)
# =============================================================================


class TicketORM(Base):
    """
    Base ORM model for all ticket types.

    Uses single-table inheritance with discriminator column `ticket_type`.
    All ticket types share common columns, type-specific columns are nullable.

    Columns:
    - Identity: id, name, description
    - Hierarchy: parent_id, sequence, slug (ULID ordering)
    - Lifecycle: status, timestamps
    - Work: assigned_agents_json, priority, commits_json
    - Requirements: requirements_local_json
    - Metadata: metadata_json

    Type-specific columns documented in subclasses.
    """

    __tablename__ = "tickets"

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Type Discriminator
    # -------------------------------------------------------------------------
    ticket_type: Mapped[str] = mapped_column(String, nullable=False)

    # -------------------------------------------------------------------------
    # Hierarchy & Ordering (ULID system)
    # -------------------------------------------------------------------------
    parent_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("tickets.id"), nullable=True
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    slug: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    status: Mapped[str] = mapped_column(String, nullable=False, default="not_started")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # -------------------------------------------------------------------------
    # Work Assignment (JSON)
    # -------------------------------------------------------------------------
    assigned_agents_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    estimated_duration: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # -------------------------------------------------------------------------
    # Work Evidence (JSON)
    # -------------------------------------------------------------------------
    commits_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Requirements (JSON)
    # -------------------------------------------------------------------------
    requirements_local_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Deferral Flag
    # -------------------------------------------------------------------------
    deferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # -------------------------------------------------------------------------
    # Metadata (JSON)
    # -------------------------------------------------------------------------
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Type-Specific Columns (Nullable)
    # -------------------------------------------------------------------------

    # Roadmap-specific
    version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version_strategy_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activity_log_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Track-specific
    strategic_value_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Sprint-specific
    plan_file: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success_criteria_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    development_gates_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Task-specific
    task_type_detail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    estimated_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    complexity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    gate_info_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audit_results_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phase_label: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------

    criteria: Mapped[List["CriterionORM"]] = relationship(
        "CriterionORM",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    parent: Mapped[Optional["TicketORM"]] = relationship(
        "TicketORM",
        remote_side=[id],
        foreign_keys=[parent_id],
        backref="children",
    )

    # -------------------------------------------------------------------------
    # Polymorphism Configuration
    # -------------------------------------------------------------------------

    __mapper_args__ = {
        "polymorphic_on": ticket_type,
        "polymorphic_identity": "ticket",
    }

    # -------------------------------------------------------------------------
    # Conversion Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_pydantic(cls, ticket: "Ticket") -> "TicketORM":
        """
        Create ORM instance from Pydantic model.

        This is the base implementation. Subclasses override for type-specific fields.

        Args:
            ticket: Pydantic Ticket instance

        Returns:
            TicketORM instance
        """
        import json
        from vibey.roadmap.models.ticket import Ticket, GitCommit

        orm_instance = cls(
            id=ticket.id,
            name=ticket.name,
            description=ticket.description,
            ticket_type=ticket.ticket_type.value if hasattr(ticket, 'ticket_type') else 'ticket',
            parent_id=ticket.parent_ref,
            sequence=getattr(ticket, 'sequence', 0),
            slug=getattr(ticket, 'slug', None),
            status=ticket.status.value,
            created_at=ticket.created_at,
            started_at=ticket.started_at,
            completed_at=ticket.completed_at,
            updated_at=ticket.updated_at,
            assigned_agents_json=json.dumps(ticket.assigned_agents) if ticket.assigned_agents else None,
            priority=ticket.priority.value if ticket.priority else None,
            estimated_duration=ticket.estimated_duration,
            commits_json=json.dumps([c.model_dump(mode='json') for c in ticket.commits]) if ticket.commits else None,
            requirements_local_json=json.dumps([r.model_dump(mode='json') for r in ticket.requirements_local]) if ticket.requirements_local else None,
            deferred=ticket.deferred,
            metadata_json=json.dumps(ticket.metadata) if ticket.metadata else None,
        )

        # Add criteria
        for criterion in ticket.criteria:
            orm_instance.criteria.append(CriterionORM.from_pydantic(criterion))

        return orm_instance

    def to_pydantic(self) -> "Ticket":
        """
        Convert ORM instance to Pydantic model.

        This is the base implementation. Subclasses override for type-specific fields.

        Returns:
            Pydantic Ticket instance
        """
        import json
        from vibey.roadmap.models.ticket import Ticket, Criterion, GitCommit, Requirement

        criteria = [c.to_pydantic() for c in self.criteria]

        commits = []
        if self.commits_json:
            commits_data = json.loads(self.commits_json)
            commits = [GitCommit.model_validate(c) for c in commits_data]

        requirements = []
        if self.requirements_local_json:
            req_data = json.loads(self.requirements_local_json)
            requirements = [Requirement.model_validate(r) for r in req_data]

        assigned_agents = []
        if self.assigned_agents_json:
            assigned_agents = json.loads(self.assigned_agents_json)

        metadata = {}
        if self.metadata_json:
            metadata = json.loads(self.metadata_json)

        return Ticket(
            id=self.id,
            name=self.name,
            description=self.description or "",
            parent_ref=self.parent_id,
            status=TicketStatus(self.status),
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            updated_at=self.updated_at,
            assigned_agents=assigned_agents,
            priority=Priority(self.priority) if self.priority else Priority.MEDIUM,
            estimated_duration=self.estimated_duration,
            commits=commits,
            requirements_local=requirements,
            deferred=self.deferred,
            metadata=metadata,
            criteria=criteria,
        )

    def __repr__(self) -> str:
        return f"<TicketORM(id={self.id!r}, type={self.ticket_type!r}, status={self.status!r})>"


# =============================================================================
# TICKET SUBCLASSES (Polymorphic)
# =============================================================================


class RoadmapTicketORM(TicketORM):
    """
    ORM model for Roadmap tickets.

    Additional fields:
    - version: Semantic version
    - version_strategy_json: Version strategy configuration
    - activity_log_json: Activity log entries
    """

    __mapper_args__ = {
        "polymorphic_identity": "roadmap",
    }

    @classmethod
    def from_pydantic(cls, ticket: "RoadmapTicket") -> "RoadmapTicketORM":
        """Create ORM instance from Pydantic RoadmapTicket."""
        import json
        from vibey.roadmap.models.ticket import RoadmapTicket

        orm_instance = super().from_pydantic.__func__(cls, ticket)
        orm_instance.ticket_type = "roadmap"
        orm_instance.version = ticket.version
        if ticket.version_strategy:
            orm_instance.version_strategy_json = ticket.version_strategy.model_dump_json()
        if ticket.activity_log:
            orm_instance.activity_log_json = json.dumps([
                a.model_dump(mode='json') for a in ticket.activity_log
            ])
        return orm_instance

    def to_pydantic(self) -> "RoadmapTicket":
        """Convert to Pydantic RoadmapTicket."""
        import json
        from vibey.roadmap.models.ticket import (
            RoadmapTicket, Criterion, GitCommit, Requirement,
            VersionStrategy, ActivityLogEntry
        )

        base = super().to_pydantic()

        version_strategy = None
        if self.version_strategy_json:
            version_strategy = VersionStrategy.model_validate_json(self.version_strategy_json)

        activity_log = []
        if self.activity_log_json:
            log_data = json.loads(self.activity_log_json)
            activity_log = [ActivityLogEntry.model_validate(a) for a in log_data]

        return RoadmapTicket(
            **base.model_dump(exclude={'criteria'}),
            ticket_type=TicketType.ROADMAP,
            version=self.version or "0.0.1",
            version_strategy=version_strategy,
            activity_log=activity_log,
            criteria=[c.to_pydantic() for c in self.criteria],
        )


class TrackTicketORM(TicketORM):
    """
    ORM model for Track tickets.

    Additional fields:
    - strategic_value_json: List of strategic value statements
    """

    __mapper_args__ = {
        "polymorphic_identity": "track",
    }

    @classmethod
    def from_pydantic(cls, ticket: "TrackTicket") -> "TrackTicketORM":
        """Create ORM instance from Pydantic TrackTicket."""
        import json
        from vibey.roadmap.models.ticket import TrackTicket

        orm_instance = super().from_pydantic.__func__(cls, ticket)
        orm_instance.ticket_type = "track"
        if ticket.strategic_value:
            orm_instance.strategic_value_json = json.dumps(ticket.strategic_value)
        return orm_instance

    def to_pydantic(self) -> "TrackTicket":
        """Convert to Pydantic TrackTicket."""
        import json
        from vibey.roadmap.models.ticket import TrackTicket, Criterion

        base = super().to_pydantic()

        strategic_value = []
        if self.strategic_value_json:
            strategic_value = json.loads(self.strategic_value_json)

        return TrackTicket(
            **base.model_dump(exclude={'criteria'}),
            ticket_type=TicketType.TRACK,
            strategic_value=strategic_value,
            criteria=[c.to_pydantic() for c in self.criteria],
        )


class SprintTicketORM(TicketORM):
    """
    ORM model for Sprint tickets.

    Additional fields:
    - plan_file: Path to sprint plan file
    - goal: Sprint goal description
    - success_criteria_json: Success criteria
    - development_gates_json: Development gates
    """

    __mapper_args__ = {
        "polymorphic_identity": "sprint",
    }

    @classmethod
    def from_pydantic(cls, ticket: "SprintTicket") -> "SprintTicketORM":
        """Create ORM instance from Pydantic SprintTicket."""
        import json
        from vibey.roadmap.models.ticket import SprintTicket

        orm_instance = super().from_pydantic.__func__(cls, ticket)
        orm_instance.ticket_type = "sprint"
        orm_instance.plan_file = ticket.plan_file
        orm_instance.goal = ticket.goal
        if ticket.success_criteria_text:
            orm_instance.success_criteria_json = json.dumps(ticket.success_criteria_text)
        if ticket.development_gates:
            orm_instance.development_gates_json = json.dumps([
                g.model_dump(mode='json') for g in ticket.development_gates
            ])
        return orm_instance

    def to_pydantic(self) -> "SprintTicket":
        """Convert to Pydantic SprintTicket."""
        import json
        from vibey.roadmap.models.ticket import SprintTicket, Criterion, DevelopmentGate

        base = super().to_pydantic()

        success_criteria = []
        if self.success_criteria_json:
            success_criteria = json.loads(self.success_criteria_json)

        development_gates = []
        if self.development_gates_json:
            gates_data = json.loads(self.development_gates_json)
            development_gates = [DevelopmentGate.model_validate(g) for g in gates_data]

        return SprintTicket(
            **base.model_dump(exclude={'criteria'}),
            ticket_type=TicketType.SPRINT,
            plan_file=self.plan_file,
            goal=self.goal,
            success_criteria_text=success_criteria,
            development_gates=development_gates,
            criteria=[c.to_pydantic() for c in self.criteria],
        )


class TaskTicketORM(TicketORM):
    """
    ORM model for Task tickets.

    Additional fields:
    - task_type_detail: Task type (development, completion_gate, production_gate)
    - estimated_tokens: Token estimate
    - actual_tokens: Actual tokens used
    - complexity: Task complexity
    - gate_info_json: Gate information (for gate tasks)
    - audit_results_json: Audit results
    - phase_label: Development phase
    """

    __mapper_args__ = {
        "polymorphic_identity": "task",
    }

    @classmethod
    def from_pydantic(cls, ticket: "TaskTicket") -> "TaskTicketORM":
        """Create ORM instance from Pydantic TaskTicket."""
        import json
        from vibey.roadmap.models.ticket import TaskTicket

        orm_instance = super().from_pydantic.__func__(cls, ticket)
        orm_instance.ticket_type = "task"
        orm_instance.task_type_detail = ticket.task_type_detail.value if ticket.task_type_detail else None
        orm_instance.estimated_tokens = ticket.estimated_tokens
        orm_instance.actual_tokens = ticket.actual_tokens
        orm_instance.complexity = ticket.complexity.value if ticket.complexity else None
        orm_instance.phase_label = ticket.phase_label
        if ticket.gate_info:
            orm_instance.gate_info_json = ticket.gate_info.model_dump_json()
        if ticket.audit_results:
            orm_instance.audit_results_json = ticket.audit_results.model_dump_json()
        return orm_instance

    def to_pydantic(self) -> "TaskTicket":
        """Convert to Pydantic TaskTicket."""
        from vibey.roadmap.models.ticket import TaskTicket, Criterion, GateInfo, AuditResults

        base = super().to_pydantic()

        gate_info = None
        if self.gate_info_json:
            gate_info = GateInfo.model_validate_json(self.gate_info_json)

        audit_results = None
        if self.audit_results_json:
            audit_results = AuditResults.model_validate_json(self.audit_results_json)

        # TaskTicket requires sprint_id, track_id, roadmap_id
        # These are typically derived from the hierarchy but stored as parent_id
        # For now, use the id pattern to derive them
        sprint_id = self.parent_id or self.id.rsplit("-", 1)[0] if "-" in self.id else self.id
        track_id = sprint_id.rsplit("-", 1)[0] if "-" in sprint_id else sprint_id
        roadmap_id = track_id.rsplit("-", 1)[0] if "-" in track_id else track_id

        return TaskTicket(
            **base.model_dump(exclude={'criteria'}),
            ticket_type=TicketType.TASK,
            task_type_detail=TaskType(self.task_type_detail) if self.task_type_detail else TaskType.DEVELOPMENT,
            estimated_tokens=self.estimated_tokens or 0,
            actual_tokens=self.actual_tokens,
            complexity=Complexity(self.complexity) if self.complexity else None,
            phase_label=self.phase_label,
            gate_info=gate_info,
            audit_results=audit_results,
            sprint_id=sprint_id,
            track_id=track_id,
            roadmap_id=roadmap_id,
            criteria=[c.to_pydantic() for c in self.criteria],
        )


# =============================================================================
# CRITERION ORM
# =============================================================================


class CriterionORM(Base):
    """
    ORM model for completion criteria.

    Criteria are stored separately from tickets with polymorphic targets.
    The target_type discriminator determines how to deserialize target_json.

    Columns:
    - id: Criterion identifier
    - ticket_id: Parent ticket reference
    - description: Human-readable description
    - required: Whether criterion is required
    - blocks_transition_to: Which transition this blocks (in_progress, completed, production_ready)
    - target_type: Polymorphic discriminator
    - target_json: Type-specific target data
    - is_met: Cached result
    - last_checked: When target was last evaluated
    """

    __tablename__ = "criteria"

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )

    # -------------------------------------------------------------------------
    # Definition
    # -------------------------------------------------------------------------
    description: Mapped[str] = mapped_column(String, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    # -------------------------------------------------------------------------
    # Blocking Configuration
    # -------------------------------------------------------------------------
    blocks_transition_to: Mapped[str] = mapped_column(
        String, nullable=False, default="completed"
    )

    # -------------------------------------------------------------------------
    # Polymorphic Target
    # -------------------------------------------------------------------------
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    target_json: Mapped[str] = mapped_column(Text, nullable=False)

    # -------------------------------------------------------------------------
    # Cached State
    # -------------------------------------------------------------------------
    is_met: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_checked: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    ticket: Mapped["TicketORM"] = relationship("TicketORM", back_populates="criteria")

    # -------------------------------------------------------------------------
    # Indexes
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index("idx_criteria_ticket", "ticket_id"),
        Index("idx_criteria_blocks_transition", "ticket_id", "blocks_transition_to"),
        Index("idx_criteria_target_type", "target_type"),
    )

    # -------------------------------------------------------------------------
    # Conversion Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_pydantic(cls, criterion: "Criterion") -> "CriterionORM":
        """
        Create ORM instance from Pydantic Criterion.

        Args:
            criterion: Pydantic Criterion instance

        Returns:
            CriterionORM instance
        """
        return cls(
            id=criterion.id,
            description=criterion.description,
            required=criterion.required,
            blocks_transition_to=criterion.blocks_transition_to.value,
            target_type=criterion.target.type.value,  # 'type' field on target
            target_json=criterion.target.model_dump_json(),
            is_met=criterion.is_met,
            last_checked=datetime.now(timezone.utc),
        )

    def to_pydantic(self) -> "Criterion":
        """
        Convert ORM instance to Pydantic Criterion.

        Returns:
            Pydantic Criterion instance
        """
        from vibey.roadmap.models.ticket import Criterion, create_target

        target = deserialize_target(self.target_type, self.target_json)

        return Criterion(
            id=self.id,
            description=self.description,
            required=self.required,
            blocks_transition_to=TicketStatus(self.blocks_transition_to),
            target=target,
        )

    def __repr__(self) -> str:
        return f"<CriterionORM(id={self.id!r}, type={self.target_type!r}, blocks={self.blocks_transition_to!r})>"


# =============================================================================
# TARGET SERIALIZATION
# =============================================================================


def deserialize_target(target_type: str, target_json: str) -> "CriterionTarget":
    """
    Deserialize a target from its type and JSON data.

    Args:
        target_type: Target type discriminator
        target_json: JSON-encoded target data

    Returns:
        Appropriate CriterionTarget subclass instance

    Raises:
        ValueError: If target_type is unknown
    """
    from vibey.roadmap.models.ticket import (
        CompletableTarget,
        FileExistsTarget,
        TestPassesTarget,
        TestCoverageTarget,
        ThresholdTarget,
        ManualTarget,
        ExternalTarget,
    )

    target_classes = {
        "completable": CompletableTarget,
        "file_exists": FileExistsTarget,
        "test_passes": TestPassesTarget,
        "test_coverage": TestCoverageTarget,
        "threshold": ThresholdTarget,
        "manual": ManualTarget,
        "external": ExternalTarget,
    }

    if target_type not in target_classes:
        raise ValueError(f"Unknown target type: {target_type}")

    return target_classes[target_type].model_validate_json(target_json)


def serialize_target(target: "CriterionTarget") -> tuple[str, str]:
    """
    Serialize a target to its type and JSON data.

    Args:
        target: CriterionTarget instance

    Returns:
        Tuple of (target_type, target_json)
    """
    return (target.type.value, target.model_dump_json())


# =============================================================================
# SCHEMA CREATION
# =============================================================================


def get_unified_schema_ddl() -> str:
    """
    Get DDL for the unified ticket schema.

    This creates the `tickets` and `criteria` tables for the unified model.
    Separate from the legacy schema in database/schema.py.

    Returns:
        SQL DDL string
    """
    return """
-- =============================================================================
-- UNIFIED TICKET SCHEMA
-- =============================================================================

-- Tickets table (single-table inheritance)
CREATE TABLE IF NOT EXISTS tickets (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    ticket_type TEXT NOT NULL,  -- discriminator: roadmap, track, sprint, task

    -- Hierarchy & Ordering (ULID system)
    parent_id TEXT REFERENCES tickets(id),
    sequence INTEGER DEFAULT 0,
    slug TEXT,

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'not_started',
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL,

    -- Work Assignment (JSON)
    assigned_agents_json TEXT,
    priority TEXT,
    estimated_duration TEXT,

    -- Work Evidence (JSON)
    commits_json TEXT,

    -- Requirements (JSON)
    requirements_local_json TEXT,

    -- Deferral Flag
    deferred INTEGER DEFAULT 0,

    -- Metadata (JSON)
    metadata_json TEXT,

    -- Roadmap-specific
    version TEXT,
    version_strategy_json TEXT,
    activity_log_json TEXT,

    -- Track-specific
    strategic_value_json TEXT,

    -- Sprint-specific
    plan_file TEXT,
    goal TEXT,
    success_criteria_json TEXT,
    development_gates_json TEXT,

    -- Task-specific
    task_type_detail TEXT,
    estimated_tokens INTEGER,
    actual_tokens INTEGER,
    complexity TEXT,
    gate_info_json TEXT,
    audit_results_json TEXT,
    phase_label TEXT
);

-- Criteria table (polymorphic targets)
CREATE TABLE IF NOT EXISTS criteria (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    required INTEGER DEFAULT 1,

    -- UNIFIED BLOCKING: which transition does this block?
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed',
    -- Values: 'in_progress', 'completed', 'production_ready'

    -- Target (polymorphic via target_type)
    target_type TEXT NOT NULL,  -- discriminator
    target_json TEXT NOT NULL,  -- type-specific target data

    -- Cached state
    is_met INTEGER,  -- boolean, cached
    last_checked TEXT
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Ticket lookups
CREATE INDEX IF NOT EXISTS idx_tickets_parent ON tickets(parent_id);
CREATE INDEX IF NOT EXISTS idx_tickets_type ON tickets(ticket_type);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_sequence ON tickets(parent_id, sequence);

-- Criteria lookups
CREATE INDEX IF NOT EXISTS idx_criteria_ticket ON criteria(ticket_id);
CREATE INDEX IF NOT EXISTS idx_criteria_blocks_transition ON criteria(ticket_id, blocks_transition_to);
CREATE INDEX IF NOT EXISTS idx_criteria_target_type ON criteria(target_type);

-- Finding children (CompletableTarget blocking COMPLETED)
CREATE INDEX IF NOT EXISTS idx_criteria_completable_target
    ON criteria(json_extract(target_json, '$.completable_id'))
    WHERE target_type = 'completable' AND blocks_transition_to = 'completed';

-- Finding dependencies (CompletableTarget blocking IN_PROGRESS)
CREATE INDEX IF NOT EXISTS idx_criteria_dependencies
    ON criteria(json_extract(target_json, '$.completable_id'))
    WHERE target_type = 'completable' AND blocks_transition_to = 'in_progress';

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View for required vs deferred children
CREATE VIEW IF NOT EXISTS v_required_children AS
SELECT
    parent.id AS parent_id,
    child.id AS child_id,
    child.deferred
FROM tickets parent
JOIN criteria c ON c.ticket_id = parent.id
JOIN tickets child ON json_extract(c.target_json, '$.completable_id') = child.id
WHERE c.target_type = 'completable';
"""


def create_unified_schema(engine) -> None:
    """
    Create the unified ticket schema.

    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.create_all(engine)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def get_ticket_orm_class(ticket_type: Union[str, TicketType]) -> Type[TicketORM]:
    """
    Get the appropriate ORM class for a ticket type.

    Args:
        ticket_type: Ticket type as string or enum

    Returns:
        TicketORM subclass
    """
    if isinstance(ticket_type, TicketType):
        ticket_type = ticket_type.value

    type_map = {
        "roadmap": RoadmapTicketORM,
        "track": TrackTicketORM,
        "sprint": SprintTicketORM,
        "task": TaskTicketORM,
    }

    return type_map.get(ticket_type, TicketORM)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Base
    "Base",
    # ORM Models
    "TicketORM",
    "RoadmapTicketORM",
    "TrackTicketORM",
    "SprintTicketORM",
    "TaskTicketORM",
    "CriterionORM",
    # Serialization
    "deserialize_target",
    "serialize_target",
    # Schema
    "get_unified_schema_ddl",
    "create_unified_schema",
    # Factory
    "get_ticket_orm_class",
]
