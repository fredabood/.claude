"""
Tests for repository pattern implementation.

Tests:
- TicketRepository CRUD operations
- TicketRepository query methods
- CriterionRepository operations
- RepositoryFactory usage
"""

import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vibey.roadmap.models.ticket import (
    # Enums
    TicketStatus,
    TicketType,
    TaskType,
    Priority,
    # Pydantic models
    Ticket,
    Criterion,
    TaskTicket,
    SprintTicket,
    # Target types
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    # ORM
    Base,
    TicketORM,
    CriterionORM,
    create_unified_schema,
    # Repository
    TicketRepository,
    CriterionRepository,
    RepositoryFactory,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def engine():
    """Create in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_unified_schema(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def ticket_repo(session):
    """Create TicketRepository."""
    return TicketRepository(session)


@pytest.fixture
def criterion_repo(session):
    """Create CriterionRepository."""
    return CriterionRepository(session)


@pytest.fixture
def now():
    """Current timestamp."""
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_ticket(now):
    """Create a sample Ticket."""
    return Ticket(
        id="test-001",
        name="Test Ticket",
        description="A test ticket",
        status=TicketStatus.NOT_STARTED,
        created_at=now,
        updated_at=now,
        priority=Priority.MEDIUM,
    )


@pytest.fixture
def sample_task(now):
    """Create a sample TaskTicket."""
    return TaskTicket(
        id="task-001",
        name="Sample Task",
        description="A sample task",
        status=TicketStatus.NOT_STARTED,
        created_at=now,
        updated_at=now,
        task_type_detail=TaskType.DEVELOPMENT,
        estimated_tokens=1500,
        sprint_id="sprint-001",
        track_id="track-001",
        roadmap_id="roadmap-001",
        parent_ref="sprint-001",
    )


# =============================================================================
# TICKET REPOSITORY CRUD TESTS
# =============================================================================


class TestTicketRepositoryCrud:
    """Tests for TicketRepository CRUD operations."""

    def test_save_and_get(self, ticket_repo, sample_ticket, session):
        """Can save and retrieve a ticket."""
        ticket_repo.save(sample_ticket)
        session.commit()

        loaded = ticket_repo.get("test-001")
        assert loaded is not None
        assert loaded.id == "test-001"
        assert loaded.name == "Test Ticket"

    def test_get_nonexistent(self, ticket_repo):
        """Get returns None for nonexistent ticket."""
        loaded = ticket_repo.get("nonexistent")
        assert loaded is None

    def test_save_updates_existing(self, ticket_repo, sample_ticket, session, now):
        """Save updates an existing ticket."""
        ticket_repo.save(sample_ticket)
        session.commit()

        # Update and save again
        updated = Ticket(
            id="test-001",
            name="Updated Ticket",
            description="Updated description",
            status=TicketStatus.IN_PROGRESS,
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        ticket_repo.save(updated)
        session.commit()

        loaded = ticket_repo.get("test-001")
        assert loaded.name == "Updated Ticket"
        assert loaded.status == TicketStatus.IN_PROGRESS

    def test_delete(self, ticket_repo, sample_ticket, session):
        """Can delete a ticket."""
        ticket_repo.save(sample_ticket)
        session.commit()

        result = ticket_repo.delete("test-001")
        session.commit()

        assert result is True
        assert ticket_repo.get("test-001") is None

    def test_delete_nonexistent(self, ticket_repo):
        """Delete returns False for nonexistent ticket."""
        result = ticket_repo.delete("nonexistent")
        assert result is False

    def test_save_with_criteria(self, ticket_repo, session, now):
        """Can save ticket with criteria."""
        ticket = Ticket(
            id="test-001",
            name="Ticket with Criteria",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(
                    id="crit-001",
                    description="File exists",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-002",
                    description="Tests pass",
                    target=TestPassesTarget(test_command="pytest"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        loaded = ticket_repo.get("test-001")
        assert len(loaded.criteria) == 2

    def test_save_task_ticket(self, ticket_repo, sample_task, session):
        """Can save a TaskTicket."""
        ticket_repo.save(sample_task)
        session.commit()

        loaded = ticket_repo.get("task-001")
        assert loaded is not None
        # Note: TaskTicket conversion may return base Ticket if not loaded as TaskTicket
        # This is expected behavior for the base repository


# =============================================================================
# TICKET REPOSITORY QUERY TESTS
# =============================================================================


class TestTicketRepositoryQueries:
    """Tests for TicketRepository query methods."""

    def test_find_by_status(self, ticket_repo, session, now):
        """Can find tickets by status."""
        tickets = [
            Ticket(id="t1", name="T1", status=TicketStatus.NOT_STARTED, created_at=now, updated_at=now),
            Ticket(id="t2", name="T2", status=TicketStatus.IN_PROGRESS, created_at=now, updated_at=now, started_at=now),
            Ticket(id="t3", name="T3", status=TicketStatus.NOT_STARTED, created_at=now, updated_at=now),
        ]
        for t in tickets:
            ticket_repo.save(t)
        session.commit()

        not_started = ticket_repo.find_by_status(TicketStatus.NOT_STARTED)
        in_progress = ticket_repo.find_by_status(TicketStatus.IN_PROGRESS)

        assert len(not_started) == 2
        assert len(in_progress) == 1

    def test_find_by_parent(self, ticket_repo, session, now):
        """Can find tickets by parent."""
        parent = Ticket(
            id="parent-001",
            name="Parent",
            created_at=now,
            updated_at=now,
        )
        child1 = Ticket(
            id="child-001",
            name="Child 1",
            parent_ref="parent-001",
            created_at=now,
            updated_at=now,
        )
        child2 = Ticket(
            id="child-002",
            name="Child 2",
            parent_ref="parent-001",
            created_at=now,
            updated_at=now,
        )
        ticket_repo.save(parent)
        ticket_repo.save(child1)
        ticket_repo.save(child2)
        session.commit()

        children = ticket_repo.find_by_parent("parent-001")
        assert len(children) == 2

    def test_find_root_tickets(self, ticket_repo, session, now):
        """Can find root tickets (no parent)."""
        root1 = Ticket(id="root1", name="Root 1", created_at=now, updated_at=now)
        root2 = Ticket(id="root2", name="Root 2", created_at=now, updated_at=now)
        child = Ticket(id="child", name="Child", parent_ref="root1", created_at=now, updated_at=now)

        ticket_repo.save(root1)
        ticket_repo.save(root2)
        ticket_repo.save(child)
        session.commit()

        roots = ticket_repo.find_root_tickets()
        assert len(roots) == 2

    def test_find_deferred(self, ticket_repo, session, now):
        """Can find deferred tickets."""
        normal = Ticket(id="t1", name="Normal", deferred=False, created_at=now, updated_at=now)
        deferred = Ticket(id="t2", name="Deferred", deferred=True, created_at=now, updated_at=now)

        ticket_repo.save(normal)
        ticket_repo.save(deferred)
        session.commit()

        deferred_tickets = ticket_repo.find_deferred()
        assert len(deferred_tickets) == 1
        assert deferred_tickets[0].id == "t2"

    def test_count(self, ticket_repo, session, now):
        """Can count total tickets."""
        for i in range(5):
            ticket_repo.save(Ticket(id=f"t{i}", name=f"T{i}", created_at=now, updated_at=now))
        session.commit()

        assert ticket_repo.count() == 5

    def test_count_by_status(self, ticket_repo, session, now):
        """Can count tickets by status."""
        ticket_repo.save(Ticket(id="t1", name="T1", status=TicketStatus.NOT_STARTED, created_at=now, updated_at=now))
        ticket_repo.save(Ticket(id="t2", name="T2", status=TicketStatus.NOT_STARTED, created_at=now, updated_at=now))
        ticket_repo.save(Ticket(id="t3", name="T3", status=TicketStatus.IN_PROGRESS, created_at=now, updated_at=now, started_at=now))
        session.commit()

        assert ticket_repo.count_by_status(TicketStatus.NOT_STARTED) == 2
        assert ticket_repo.count_by_status(TicketStatus.IN_PROGRESS) == 1


# =============================================================================
# CRITERION REPOSITORY TESTS
# =============================================================================


class TestCriterionRepository:
    """Tests for CriterionRepository."""

    def test_get_criterion(self, ticket_repo, criterion_repo, session, now):
        """Can get a criterion by ID."""
        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(
                    id="crit-001",
                    description="Test criterion",
                    target=FileExistsTarget(paths=["test.py"]),
                ),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        criterion = criterion_repo.get("crit-001")
        assert criterion is not None
        assert criterion.description == "Test criterion"

    def test_find_by_ticket(self, ticket_repo, criterion_repo, session, now):
        """Can find criteria by ticket."""
        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(id="c1", description="C1", target=FileExistsTarget(paths=["a.py"])),
                Criterion(id="c2", description="C2", target=FileExistsTarget(paths=["b.py"])),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        criteria = criterion_repo.find_by_ticket("test-001")
        assert len(criteria) == 2

    def test_find_by_target_type(self, ticket_repo, criterion_repo, session, now):
        """Can find criteria by target type."""
        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(id="c1", description="File", target=FileExistsTarget(paths=["a.py"])),
                Criterion(id="c2", description="Test", target=TestPassesTarget(test_command="pytest")),
                Criterion(id="c3", description="File2", target=FileExistsTarget(paths=["b.py"])),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        file_criteria = criterion_repo.find_by_target_type("file_exists")
        test_criteria = criterion_repo.find_by_target_type("test_passes")

        assert len(file_criteria) == 2
        assert len(test_criteria) == 1

    def test_find_by_blocks_transition(self, ticket_repo, criterion_repo, session, now):
        """Can find criteria by blocks_transition_to."""
        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(
                    id="c1",
                    description="Blocks start",
                    target=CompletableTarget(completable_id="other", current_status=TicketStatus.NOT_STARTED),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
                Criterion(
                    id="c2",
                    description="Blocks complete",
                    target=FileExistsTarget(paths=["a.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        in_progress_blockers = criterion_repo.find_by_blocks_transition("in_progress")
        completed_blockers = criterion_repo.find_by_blocks_transition("completed")

        assert len(in_progress_blockers) == 1
        assert len(completed_blockers) == 1

    def test_update_is_met(self, ticket_repo, criterion_repo, session, now):
        """Can update is_met flag."""
        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(id="c1", description="C1", target=FileExistsTarget(paths=["a.py"])),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        result = criterion_repo.update_is_met("c1", True)
        session.commit()

        assert result is True
        # The is_met flag is stored on CriterionORM, not the target
        orm_criterion = criterion_repo.get_orm("c1")
        assert orm_criterion.is_met is True

    def test_find_manual(self, ticket_repo, criterion_repo, session, now):
        """Can find manual criteria."""
        from vibey.roadmap.models.ticket import ManualTarget

        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(id="c1", description="Auto", target=FileExistsTarget(paths=["a.py"])),
                Criterion(id="c2", description="Manual", target=ManualTarget(assessor="human")),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        manual = criterion_repo.find_manual()
        assert len(manual) == 1
        assert manual[0].id == "c2"

    def test_count(self, ticket_repo, criterion_repo, session, now):
        """Can count criteria."""
        ticket = Ticket(
            id="test-001",
            name="Test",
            created_at=now,
            updated_at=now,
            criteria=[
                Criterion(id="c1", description="C1", target=FileExistsTarget(paths=["a.py"])),
                Criterion(id="c2", description="C2", target=FileExistsTarget(paths=["b.py"])),
                Criterion(id="c3", description="C3", target=FileExistsTarget(paths=["c.py"])),
            ],
        )
        ticket_repo.save(ticket)
        session.commit()

        assert criterion_repo.count() == 3


# =============================================================================
# REPOSITORY FACTORY TESTS
# =============================================================================


class TestRepositoryFactory:
    """Tests for RepositoryFactory."""

    def test_create_factory(self, tmp_path):
        """Can create RepositoryFactory."""
        db_path = tmp_path / "test.db"
        factory = RepositoryFactory(db_path)
        factory.initialize()

        assert db_path.exists()

    def test_session_scope(self, tmp_path):
        """session_scope provides transactional context."""
        db_path = tmp_path / "test.db"
        factory = RepositoryFactory(db_path)
        factory.initialize()

        now = datetime.now(timezone.utc)

        with factory.session_scope() as session:
            repo = factory.ticket_repository(session)
            ticket = Ticket(id="t1", name="T1", created_at=now, updated_at=now)
            repo.save(ticket)

        # Verify persisted
        with factory.session_scope() as session:
            repo = factory.ticket_repository(session)
            loaded = repo.get("t1")
            assert loaded is not None

    def test_session_scope_rollback(self, tmp_path):
        """session_scope rolls back on exception."""
        db_path = tmp_path / "test.db"
        factory = RepositoryFactory(db_path)
        factory.initialize()

        now = datetime.now(timezone.utc)

        try:
            with factory.session_scope() as session:
                repo = factory.ticket_repository(session)
                ticket = Ticket(id="t1", name="T1", created_at=now, updated_at=now)
                repo.save(ticket)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Verify rolled back
        with factory.session_scope() as session:
            repo = factory.ticket_repository(session)
            loaded = repo.get("t1")
            assert loaded is None

    def test_in_memory_factory(self):
        """Can create in-memory factory."""
        factory = RepositoryFactory(None)  # None = in-memory
        factory.initialize()

        now = datetime.now(timezone.utc)

        with factory.session_scope() as session:
            repo = factory.ticket_repository(session)
            ticket = Ticket(id="t1", name="T1", created_at=now, updated_at=now)
            repo.save(ticket)
            loaded = repo.get("t1")
            assert loaded is not None
