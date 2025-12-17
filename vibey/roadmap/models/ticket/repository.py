"""
Repository pattern for unified ticket persistence.

This module provides repository classes for managing tickets and criteria
in the SQLite database using SQLAlchemy ORM.

Repositories:
- TicketRepository: CRUD and query operations for tickets
- CriterionRepository: CRUD and query operations for criteria

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
Task Reference: sqlite-backend-6-task-012
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session, sessionmaker

from vibey.roadmap.models.ticket.enums import TicketStatus, TicketType
from vibey.roadmap.models.ticket.orm import (
    CriterionORM,
    TicketORM,
    RoadmapTicketORM,
    TrackTicketORM,
    SprintTicketORM,
    TaskTicketORM,
    create_unified_schema,
)


# =============================================================================
# DATABASE CONNECTION
# =============================================================================


def get_engine(db_path: Optional[Path] = None):
    """
    Get SQLAlchemy engine for the unified ticket database.

    Args:
        db_path: Path to SQLite database file. If None, uses in-memory database.

    Returns:
        SQLAlchemy engine
    """
    if db_path:
        url = f"sqlite:///{db_path}"
    else:
        url = "sqlite:///:memory:"

    engine = create_engine(url, echo=False)
    return engine


def get_session_factory(db_path: Optional[Path] = None):
    """
    Get session factory for the unified ticket database.

    Args:
        db_path: Path to SQLite database file. If None, uses in-memory database.

    Returns:
        SQLAlchemy sessionmaker
    """
    engine = get_engine(db_path)
    return sessionmaker(bind=engine)


# =============================================================================
# TICKET REPOSITORY
# =============================================================================


class TicketRepository:
    """
    Repository for managing tickets in the database.

    Provides CRUD operations and queries for tickets. All methods work with
    Pydantic models, converting to/from ORM internally.

    Usage:
        repo = TicketRepository(session)
        ticket = repo.get("task-001")
        repo.save(ticket)
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def get(self, ticket_id: str) -> Optional["Ticket"]:
        """
        Get a ticket by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Pydantic Ticket or None if not found
        """
        orm_ticket = self.session.get(TicketORM, ticket_id)
        if orm_ticket is None:
            return None
        return orm_ticket.to_pydantic()

    def get_with_criteria(self, ticket_id: str) -> Optional["Ticket"]:
        """
        Get a ticket with all its criteria eagerly loaded.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Pydantic Ticket with criteria or None if not found
        """
        # Criteria are already eagerly loaded via selectin
        return self.get(ticket_id)

    def get_orm(self, ticket_id: str) -> Optional[TicketORM]:
        """
        Get raw ORM instance by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            TicketORM instance or None
        """
        return self.session.get(TicketORM, ticket_id)

    def save(self, ticket: "Ticket") -> None:
        """
        Save a ticket to the database.

        Creates if new, updates if existing.

        Args:
            ticket: Pydantic Ticket to save
        """
        from vibey.roadmap.models.ticket import (
            RoadmapTicket, TrackTicket, SprintTicket, TaskTicket
        )

        # Determine ORM class based on ticket type
        if isinstance(ticket, RoadmapTicket):
            orm_class = RoadmapTicketORM
        elif isinstance(ticket, TrackTicket):
            orm_class = TrackTicketORM
        elif isinstance(ticket, SprintTicket):
            orm_class = SprintTicketORM
        elif isinstance(ticket, TaskTicket):
            orm_class = TaskTicketORM
        else:
            orm_class = TicketORM

        # Check if exists
        existing = self.session.get(TicketORM, ticket.id)
        if existing:
            # Update existing
            self._update_orm_from_pydantic(existing, ticket)
        else:
            # Create new
            orm_ticket = orm_class.from_pydantic(ticket)
            self.session.add(orm_ticket)

        self.session.flush()

    def _update_orm_from_pydantic(self, orm_ticket: TicketORM, ticket: "Ticket") -> None:
        """
        Update ORM instance from Pydantic model.

        Args:
            orm_ticket: Existing ORM instance
            ticket: Pydantic model with new values
        """
        import json

        orm_ticket.name = ticket.name
        orm_ticket.description = ticket.description
        orm_ticket.parent_id = ticket.parent_ref
        orm_ticket.status = ticket.status.value
        orm_ticket.started_at = ticket.started_at
        orm_ticket.completed_at = ticket.completed_at
        orm_ticket.updated_at = datetime.now(timezone.utc)
        orm_ticket.assigned_agents_json = json.dumps(ticket.assigned_agents) if ticket.assigned_agents else None
        orm_ticket.priority = ticket.priority.value if ticket.priority else None
        orm_ticket.estimated_duration = ticket.estimated_duration
        orm_ticket.commits_json = json.dumps([c.model_dump(mode='json') for c in ticket.commits]) if ticket.commits else None
        orm_ticket.requirements_local_json = json.dumps([r.model_dump(mode='json') for r in ticket.requirements_local]) if ticket.requirements_local else None
        orm_ticket.deferred = ticket.deferred
        orm_ticket.metadata_json = json.dumps(ticket.metadata) if ticket.metadata else None

        # Update criteria
        orm_ticket.criteria.clear()
        for criterion in ticket.criteria:
            orm_ticket.criteria.append(CriterionORM.from_pydantic(criterion))

    def delete(self, ticket_id: str) -> bool:
        """
        Delete a ticket by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            True if deleted, False if not found
        """
        orm_ticket = self.session.get(TicketORM, ticket_id)
        if orm_ticket is None:
            return False
        self.session.delete(orm_ticket)
        self.session.flush()
        return True

    def save_criterion(self, ticket_id: str, criterion: "Criterion") -> None:
        """
        Add or update a criterion for a ticket.

        Args:
            ticket_id: Parent ticket identifier
            criterion: Pydantic Criterion to save
        """
        orm_ticket = self.session.get(TicketORM, ticket_id)
        if orm_ticket is None:
            raise ValueError(f"Ticket not found: {ticket_id}")

        # Check if criterion exists
        existing = next(
            (c for c in orm_ticket.criteria if c.id == criterion.id),
            None
        )

        if existing:
            # Update existing
            existing.description = criterion.description
            existing.required = criterion.required
            existing.blocks_transition_to = criterion.blocks_transition_to.value
            existing.target_type = criterion.target.target_type.value
            existing.target_json = criterion.target.model_dump_json()
            existing.is_met = criterion.is_met
            existing.last_checked = datetime.now(timezone.utc)
        else:
            # Add new
            orm_criterion = CriterionORM.from_pydantic(criterion)
            orm_criterion.ticket_id = ticket_id
            orm_ticket.criteria.append(orm_criterion)

        self.session.flush()

    def delete_criterion(self, criterion_id: str) -> bool:
        """
        Delete a criterion by ID.

        Args:
            criterion_id: Criterion identifier

        Returns:
            True if deleted, False if not found
        """
        stmt = select(CriterionORM).where(CriterionORM.id == criterion_id)
        orm_criterion = self.session.execute(stmt).scalar_one_or_none()
        if orm_criterion is None:
            return False
        self.session.delete(orm_criterion)
        self.session.flush()
        return True

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    def find_children(self, parent_id: str) -> List["Ticket"]:
        """
        Find all children of a parent ticket.

        Children are tickets with CompletableTarget criteria pointing to them
        and blocks_transition_to = 'completed'.

        Args:
            parent_id: Parent ticket identifier

        Returns:
            List of child tickets
        """
        parent = self.session.get(TicketORM, parent_id)
        if parent is None:
            return []

        children = []
        for criterion in parent.criteria:
            if (criterion.target_type == "completable" and
                criterion.blocks_transition_to == "completed"):
                import json
                target_data = json.loads(criterion.target_json)
                child_id = target_data.get("completable_id")
                if child_id:
                    child = self.get(child_id)
                    if child:
                        children.append(child)

        return children

    def find_dependencies(self, ticket_id: str) -> List["Criterion"]:
        """
        Find all dependency criteria for a ticket.

        Dependencies are criteria with CompletableTarget and
        blocks_transition_to = 'in_progress'.

        Args:
            ticket_id: Ticket identifier

        Returns:
            List of dependency criteria
        """
        ticket = self.session.get(TicketORM, ticket_id)
        if ticket is None:
            return []

        return [
            c.to_pydantic()
            for c in ticket.criteria
            if c.target_type == "completable" and c.blocks_transition_to == "in_progress"
        ]

    def find_by_status(self, status: TicketStatus) -> List["Ticket"]:
        """
        Find all tickets with a given status.

        Args:
            status: Ticket status to filter by

        Returns:
            List of matching tickets
        """
        stmt = select(TicketORM).where(TicketORM.status == status.value)
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    def find_by_type(self, ticket_type: TicketType) -> List["Ticket"]:
        """
        Find all tickets of a given type.

        Args:
            ticket_type: Ticket type to filter by

        Returns:
            List of matching tickets
        """
        stmt = select(TicketORM).where(TicketORM.ticket_type == ticket_type.value)
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    def find_blocked(self) -> List["Ticket"]:
        """
        Find all tickets that are blocked.

        A ticket is blocked if can_start() returns False.
        We approximate by finding tickets with unmet IN_PROGRESS criteria.

        Returns:
            List of blocked tickets
        """
        # Find tickets with criteria that block IN_PROGRESS
        stmt = (
            select(TicketORM)
            .join(CriterionORM)
            .where(
                and_(
                    CriterionORM.blocks_transition_to == "in_progress",
                    CriterionORM.is_met == False,
                    TicketORM.status == "not_started",
                )
            )
            .distinct()
        )
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    def find_incomplete(self) -> List["Ticket"]:
        """
        Find all tickets that cannot complete.

        A ticket cannot complete if can_complete() returns False.
        We approximate by finding tickets with unmet COMPLETED criteria.

        Returns:
            List of incomplete tickets
        """
        # Find tickets with criteria that block COMPLETED
        stmt = (
            select(TicketORM)
            .join(CriterionORM)
            .where(
                and_(
                    CriterionORM.blocks_transition_to == "completed",
                    CriterionORM.is_met == False,
                    TicketORM.status.in_(["not_started", "in_progress"]),
                )
            )
            .distinct()
        )
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    def find_criteria_by_transition(
        self, ticket_id: str, blocks: TicketStatus
    ) -> List["Criterion"]:
        """
        Find criteria that block a specific transition.

        Args:
            ticket_id: Ticket identifier
            blocks: Status transition to filter by

        Returns:
            List of matching criteria
        """
        stmt = select(CriterionORM).where(
            and_(
                CriterionORM.ticket_id == ticket_id,
                CriterionORM.blocks_transition_to == blocks.value,
            )
        )
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    def find_by_parent(self, parent_id: str) -> List["Ticket"]:
        """
        Find all tickets with a given parent.

        Uses the parent_id foreign key directly.

        Args:
            parent_id: Parent ticket identifier

        Returns:
            List of child tickets
        """
        stmt = select(TicketORM).where(TicketORM.parent_id == parent_id)
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    def find_root_tickets(self) -> List["Ticket"]:
        """
        Find all root tickets (no parent).

        Returns:
            List of root tickets
        """
        stmt = select(TicketORM).where(TicketORM.parent_id == None)
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    def find_deferred(self) -> List["Ticket"]:
        """
        Find all deferred tickets.

        Returns:
            List of deferred tickets
        """
        stmt = select(TicketORM).where(TicketORM.deferred == True)
        result = self.session.execute(stmt).scalars().all()
        return [t.to_pydantic() for t in result]

    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------

    def save_all(self, tickets: List["Ticket"]) -> None:
        """
        Save multiple tickets.

        Args:
            tickets: List of tickets to save
        """
        for ticket in tickets:
            self.save(ticket)

    def count(self) -> int:
        """
        Count total tickets.

        Returns:
            Total ticket count
        """
        stmt = select(TicketORM)
        return len(self.session.execute(stmt).scalars().all())

    def count_by_status(self, status: TicketStatus) -> int:
        """
        Count tickets by status.

        Args:
            status: Status to count

        Returns:
            Count of tickets with given status
        """
        stmt = select(TicketORM).where(TicketORM.status == status.value)
        return len(self.session.execute(stmt).scalars().all())


# =============================================================================
# CRITERION REPOSITORY
# =============================================================================


class CriterionRepository:
    """
    Repository for managing criteria in the database.

    Provides direct access to criteria without going through tickets.
    Useful for bulk updates and queries across all criteria.

    Usage:
        repo = CriterionRepository(session)
        criteria = repo.find_by_target_type("test_passes")
        repo.update_is_met(criterion_id, True)
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def get(self, criterion_id: str) -> Optional["Criterion"]:
        """
        Get a criterion by ID.

        Args:
            criterion_id: Criterion identifier

        Returns:
            Pydantic Criterion or None if not found
        """
        orm_criterion = self.session.get(CriterionORM, criterion_id)
        if orm_criterion is None:
            return None
        return orm_criterion.to_pydantic()

    def get_orm(self, criterion_id: str) -> Optional[CriterionORM]:
        """
        Get raw ORM instance by ID.

        Args:
            criterion_id: Criterion identifier

        Returns:
            CriterionORM instance or None
        """
        return self.session.get(CriterionORM, criterion_id)

    def delete(self, criterion_id: str) -> bool:
        """
        Delete a criterion by ID.

        Args:
            criterion_id: Criterion identifier

        Returns:
            True if deleted, False if not found
        """
        orm_criterion = self.session.get(CriterionORM, criterion_id)
        if orm_criterion is None:
            return False
        self.session.delete(orm_criterion)
        self.session.flush()
        return True

    # -------------------------------------------------------------------------
    # Update Operations
    # -------------------------------------------------------------------------

    def update_is_met(self, criterion_id: str, is_met: bool) -> bool:
        """
        Update the is_met flag for a criterion.

        Args:
            criterion_id: Criterion identifier
            is_met: New is_met value

        Returns:
            True if updated, False if not found
        """
        orm_criterion = self.session.get(CriterionORM, criterion_id)
        if orm_criterion is None:
            return False
        orm_criterion.is_met = is_met
        orm_criterion.last_checked = datetime.now(timezone.utc)
        self.session.flush()
        return True

    def refresh_criterion(self, criterion_id: str, context: "RefreshContext") -> bool:
        """
        Refresh a criterion's is_met status.

        Calls refresh() on the target and updates the cached state.

        Args:
            criterion_id: Criterion identifier
            context: RefreshContext for external lookups

        Returns:
            True if refreshed, False if not found
        """
        orm_criterion = self.session.get(CriterionORM, criterion_id)
        if orm_criterion is None:
            return False

        # Convert to Pydantic and refresh
        pydantic_criterion = orm_criterion.to_pydantic()
        pydantic_criterion.target.refresh(context)

        # Update ORM
        orm_criterion.is_met = pydantic_criterion.is_met
        orm_criterion.target_json = pydantic_criterion.target.model_dump_json()
        orm_criterion.last_checked = datetime.now(timezone.utc)
        self.session.flush()
        return True

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    def find_by_ticket(self, ticket_id: str) -> List["Criterion"]:
        """
        Find all criteria for a ticket.

        Args:
            ticket_id: Ticket identifier

        Returns:
            List of criteria
        """
        stmt = select(CriterionORM).where(CriterionORM.ticket_id == ticket_id)
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    def find_by_target_type(self, target_type: str) -> List["Criterion"]:
        """
        Find all criteria with a given target type.

        Args:
            target_type: Target type (e.g., "completable", "test_passes")

        Returns:
            List of matching criteria
        """
        stmt = select(CriterionORM).where(CriterionORM.target_type == target_type)
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    def find_by_blocks_transition(self, blocks: str) -> List["Criterion"]:
        """
        Find all criteria that block a specific transition.

        Args:
            blocks: Transition to filter by (e.g., "in_progress", "completed")

        Returns:
            List of matching criteria
        """
        stmt = select(CriterionORM).where(CriterionORM.blocks_transition_to == blocks)
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    def find_unmet(self) -> List["Criterion"]:
        """
        Find all unmet criteria.

        Returns:
            List of unmet criteria
        """
        stmt = select(CriterionORM).where(CriterionORM.is_met == False)
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    def find_automatic(self) -> List["Criterion"]:
        """
        Find all criteria with automatic targets.

        Automatic targets are those that can be evaluated without manual input.

        Returns:
            List of criteria with automatic targets
        """
        automatic_types = ["completable", "file_exists", "test_passes", "test_coverage", "threshold", "external"]
        stmt = select(CriterionORM).where(CriterionORM.target_type.in_(automatic_types))
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    def find_manual(self) -> List["Criterion"]:
        """
        Find all criteria with manual targets.

        Returns:
            List of criteria with manual targets
        """
        stmt = select(CriterionORM).where(CriterionORM.target_type == "manual")
        result = self.session.execute(stmt).scalars().all()
        return [c.to_pydantic() for c in result]

    # -------------------------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------------------------

    def count(self) -> int:
        """
        Count total criteria.

        Returns:
            Total criterion count
        """
        stmt = select(CriterionORM)
        return len(self.session.execute(stmt).scalars().all())

    def refresh_all_automatic(self, context: "RefreshContext") -> int:
        """
        Refresh all automatic criteria.

        Args:
            context: RefreshContext for external lookups

        Returns:
            Number of criteria refreshed
        """
        automatic = self.find_automatic()
        refreshed = 0
        for criterion in automatic:
            orm_criterion = self.session.get(CriterionORM, criterion.id)
            if orm_criterion:
                criterion.target.refresh(context)
                orm_criterion.is_met = criterion.is_met
                orm_criterion.target_json = criterion.target.model_dump_json()
                orm_criterion.last_checked = datetime.now(timezone.utc)
                refreshed += 1
        self.session.flush()
        return refreshed


# =============================================================================
# REPOSITORY FACTORY
# =============================================================================


class RepositoryFactory:
    """
    Factory for creating repository instances.

    Manages database connection and session lifecycle.

    Usage:
        factory = RepositoryFactory(db_path)
        factory.initialize()  # Create schema

        with factory.session_scope() as session:
            ticket_repo = factory.ticket_repository(session)
            ticket_repo.save(ticket)
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize factory with database path.

        Args:
            db_path: Path to SQLite database file. If None, uses in-memory.
        """
        self.db_path = db_path
        self.engine = get_engine(db_path)
        self.SessionFactory = sessionmaker(bind=self.engine)

    def initialize(self) -> None:
        """Create database schema."""
        create_unified_schema(self.engine)

    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with factory.session_scope() as session:
                repo = factory.ticket_repository(session)
                repo.save(ticket)
        """
        from contextlib import contextmanager

        @contextmanager
        def _session_scope():
            session = self.SessionFactory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        return _session_scope()

    def ticket_repository(self, session: Session) -> TicketRepository:
        """Get ticket repository for session."""
        return TicketRepository(session)

    def criterion_repository(self, session: Session) -> CriterionRepository:
        """Get criterion repository for session."""
        return CriterionRepository(session)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Connection
    "get_engine",
    "get_session_factory",
    # Repositories
    "TicketRepository",
    "CriterionRepository",
    # Factory
    "RepositoryFactory",
]
