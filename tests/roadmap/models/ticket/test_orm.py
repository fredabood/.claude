"""
Tests for SQLAlchemy ORM models.

Tests:
- TicketORM single-table inheritance
- CriterionORM polymorphic targets
- Target serialization/deserialization
- Pydantic <-> ORM round-trip conversion
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
    Complexity,
    CriterionTargetType,
    # Pydantic models
    Ticket,
    Criterion,
    RoadmapTicket,
    TrackTicket,
    SprintTicket,
    TaskTicket,
    GitCommit,
    # Target types
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    ManualTarget,
    ThresholdTarget,
    # ORM
    Base,
    TicketORM,
    RoadmapTicketORM,
    TrackTicketORM,
    SprintTicketORM,
    TaskTicketORM,
    CriterionORM,
    deserialize_target,
    serialize_target,
    get_ticket_orm_class,
    create_unified_schema,
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
def now():
    """Current timestamp."""
    return datetime.now(timezone.utc)


@pytest.fixture
def base_ticket_kwargs(now):
    """Base kwargs for creating Ticket instances."""
    return {
        "name": "Test Ticket",
        "description": "A test ticket",
        "created_at": now,
        "updated_at": now,
    }


# =============================================================================
# TICKET ORM TESTS
# =============================================================================


class TestTicketORM:
    """Tests for TicketORM base class."""

    def test_create_ticket_orm(self, session, now):
        """Can create a TicketORM instance."""
        ticket = TicketORM(
            id="test-001",
            name="Test Ticket",
            description="A test ticket",
            ticket_type="ticket",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "test-001")
        assert loaded is not None
        assert loaded.name == "Test Ticket"
        assert loaded.ticket_type == "ticket"
        assert loaded.status == "not_started"

    def test_ticket_orm_relationships(self, session, now):
        """TicketORM parent-child relationship works."""
        parent = TicketORM(
            id="parent-001",
            name="Parent",
            ticket_type="track",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        child = TicketORM(
            id="child-001",
            name="Child",
            ticket_type="sprint",
            status="not_started",
            parent_id="parent-001",
            created_at=now,
            updated_at=now,
        )
        session.add_all([parent, child])
        session.commit()

        loaded_child = session.get(TicketORM, "child-001")
        assert loaded_child.parent is not None
        assert loaded_child.parent.id == "parent-001"

    def test_ticket_orm_criteria_relationship(self, session, now):
        """TicketORM criteria relationship works."""
        ticket = TicketORM(
            id="test-001",
            name="Test",
            ticket_type="task",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        criterion = CriterionORM(
            id="crit-001",
            ticket_id="test-001",
            description="A criterion",
            target_type="file_exists",
            target_json='{"paths": ["test.py"], "all_required": true}',
        )
        ticket.criteria.append(criterion)
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "test-001")
        assert len(loaded.criteria) == 1
        assert loaded.criteria[0].description == "A criterion"

    def test_ticket_orm_deferred_flag(self, session, now):
        """TicketORM deferred flag works."""
        ticket = TicketORM(
            id="deferred-001",
            name="Deferred",
            ticket_type="sprint",
            status="not_started",
            deferred=True,
            created_at=now,
            updated_at=now,
        )
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "deferred-001")
        assert loaded.deferred is True


# =============================================================================
# POLYMORPHIC SUBCLASS TESTS
# =============================================================================


class TestPolymorphicTickets:
    """Tests for polymorphic ticket subclasses."""

    def test_roadmap_ticket_orm(self, session, now):
        """RoadmapTicketORM uses correct discriminator."""
        ticket = RoadmapTicketORM(
            id="roadmap-001",
            name="My Roadmap",
            ticket_type="roadmap",
            status="not_started",
            version="1.0.0",
            created_at=now,
            updated_at=now,
        )
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "roadmap-001")
        assert isinstance(loaded, RoadmapTicketORM)
        assert loaded.ticket_type == "roadmap"
        assert loaded.version == "1.0.0"

    def test_track_ticket_orm(self, session, now):
        """TrackTicketORM uses correct discriminator."""
        ticket = TrackTicketORM(
            id="track-001",
            name="My Track",
            ticket_type="track",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "track-001")
        assert isinstance(loaded, TrackTicketORM)
        assert loaded.ticket_type == "track"

    def test_sprint_ticket_orm(self, session, now):
        """SprintTicketORM uses correct discriminator."""
        ticket = SprintTicketORM(
            id="sprint-001",
            name="Sprint 1",
            ticket_type="sprint",
            status="not_started",
            goal="Deliver MVP",
            created_at=now,
            updated_at=now,
        )
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "sprint-001")
        assert isinstance(loaded, SprintTicketORM)
        assert loaded.ticket_type == "sprint"
        assert loaded.goal == "Deliver MVP"

    def test_task_ticket_orm(self, session, now):
        """TaskTicketORM uses correct discriminator."""
        ticket = TaskTicketORM(
            id="task-001",
            name="Task 1",
            ticket_type="task",
            status="not_started",
            task_type_detail="development",
            estimated_tokens=1500,
            created_at=now,
            updated_at=now,
        )
        session.add(ticket)
        session.commit()

        loaded = session.get(TicketORM, "task-001")
        assert isinstance(loaded, TaskTicketORM)
        assert loaded.ticket_type == "task"
        assert loaded.task_type_detail == "development"
        assert loaded.estimated_tokens == 1500


# =============================================================================
# CRITERION ORM TESTS
# =============================================================================


class TestCriterionORM:
    """Tests for CriterionORM."""

    def test_create_criterion_orm(self, session, now):
        """Can create CriterionORM with polymorphic target."""
        ticket = TicketORM(
            id="test-001",
            name="Test",
            ticket_type="task",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        criterion = CriterionORM(
            id="crit-001",
            description="File must exist",
            required=True,
            blocks_transition_to="completed",
            target_type="file_exists",
            target_json='{"paths": ["src/main.py"], "all_required": true}',
            is_met=False,
        )
        ticket.criteria.append(criterion)
        session.add(ticket)
        session.commit()

        loaded = session.get(CriterionORM, "crit-001")
        assert loaded.target_type == "file_exists"
        assert loaded.blocks_transition_to == "completed"

    def test_criterion_blocks_in_progress(self, session, now):
        """Criterion can block IN_PROGRESS transition."""
        ticket = TicketORM(
            id="test-001",
            name="Test",
            ticket_type="task",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        criterion = CriterionORM(
            id="dep-001",
            description="Depends on other task",
            required=True,
            blocks_transition_to="in_progress",
            target_type="completable",
            target_json='{"completable_id": "other-task", "required_status": "completed", "current_status": "not_started"}',
            is_met=False,
        )
        ticket.criteria.append(criterion)
        session.add(ticket)
        session.commit()

        loaded = session.get(CriterionORM, "dep-001")
        assert loaded.blocks_transition_to == "in_progress"

    def test_criterion_cascade_delete(self, session, now):
        """Criteria are deleted when ticket is deleted."""
        ticket = TicketORM(
            id="test-001",
            name="Test",
            ticket_type="task",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        criterion = CriterionORM(
            id="crit-001",
            description="Will be deleted",
            target_type="file_exists",
            target_json='{"paths": ["test.py"]}',
        )
        ticket.criteria.append(criterion)
        session.add(ticket)
        session.commit()

        # Delete ticket
        session.delete(ticket)
        session.commit()

        # Criterion should be gone
        loaded = session.get(CriterionORM, "crit-001")
        assert loaded is None


# =============================================================================
# TARGET SERIALIZATION TESTS
# =============================================================================


class TestTargetSerialization:
    """Tests for target serialization/deserialization."""

    def test_deserialize_completable_target(self):
        """Can deserialize CompletableTarget."""
        target_json = '{"completable_id": "task-001", "required_status": "completed", "current_status": "in_progress"}'
        target = deserialize_target("completable", target_json)

        assert isinstance(target, CompletableTarget)
        assert target.completable_id == "task-001"
        assert target.required_status == TicketStatus.COMPLETED
        assert target.current_status == TicketStatus.IN_PROGRESS

    def test_deserialize_file_exists_target(self):
        """Can deserialize FileExistsTarget."""
        target_json = '{"paths": ["src/main.py", "tests/test_main.py"], "all_required": true}'
        target = deserialize_target("file_exists", target_json)

        assert isinstance(target, FileExistsTarget)
        assert len(target.paths) == 2
        assert target.all_required is True

    def test_deserialize_test_passes_target(self):
        """Can deserialize TestPassesTarget."""
        target_json = '{"test_command": "pytest tests/", "pass_threshold": 100.0}'
        target = deserialize_target("test_passes", target_json)

        assert isinstance(target, TestPassesTarget)
        assert target.test_command == "pytest tests/"
        assert target.pass_threshold == 100.0

    def test_deserialize_manual_target(self):
        """Can deserialize ManualTarget."""
        target_json = '{"assessor": "tech-lead", "instructions": "Review the code"}'
        target = deserialize_target("manual", target_json)

        assert isinstance(target, ManualTarget)
        assert target.assessor == "tech-lead"
        assert target.instructions == "Review the code"

    def test_serialize_target(self):
        """Can serialize a target."""
        target = FileExistsTarget(paths=["src/main.py"])
        target_type, target_json = serialize_target(target)

        assert target_type == "file_exists"
        assert "src/main.py" in target_json

    def test_deserialize_unknown_target_raises(self):
        """Unknown target type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown target type"):
            deserialize_target("unknown_type", '{}')


# =============================================================================
# PYDANTIC <-> ORM CONVERSION TESTS
# =============================================================================


class TestPydanticOrmConversion:
    """Tests for Pydantic <-> ORM round-trip conversion."""

    def test_ticket_to_orm_roundtrip(self, session, base_ticket_kwargs, now):
        """Ticket round-trips through ORM without data loss."""
        # Create Pydantic ticket
        pydantic_ticket = Ticket(
            **base_ticket_kwargs,
            id="test-001",
            status=TicketStatus.IN_PROGRESS,
            started_at=now,
            assigned_agents=["agent-1", "agent-2"],
            priority=Priority.HIGH,
            deferred=True,
            criteria=[
                Criterion(
                    id="crit-001",
                    description="File exists",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        # Convert to ORM
        orm_ticket = TicketORM.from_pydantic(pydantic_ticket)
        session.add(orm_ticket)
        session.commit()

        # Load from DB and convert back
        loaded_orm = session.get(TicketORM, "test-001")
        roundtrip_ticket = loaded_orm.to_pydantic()

        # Verify
        assert roundtrip_ticket.id == pydantic_ticket.id
        assert roundtrip_ticket.name == pydantic_ticket.name
        assert roundtrip_ticket.status == pydantic_ticket.status
        assert roundtrip_ticket.assigned_agents == pydantic_ticket.assigned_agents
        assert roundtrip_ticket.priority == pydantic_ticket.priority
        assert roundtrip_ticket.deferred == pydantic_ticket.deferred
        assert len(roundtrip_ticket.criteria) == 1
        assert roundtrip_ticket.criteria[0].id == "crit-001"

    def test_criterion_to_orm_roundtrip(self, session, now):
        """Criterion round-trips through ORM without data loss."""
        # Create Pydantic criterion
        pydantic_criterion = Criterion(
            id="crit-001",
            description="Test must pass",
            required=True,
            blocks_transition_to=TicketStatus.COMPLETED,
            target=TestPassesTarget(
                test_command="pytest tests/",
                pass_threshold=100.0,
                coverage_threshold=80.0,
            ),
        )

        # Convert to ORM
        orm_criterion = CriterionORM.from_pydantic(pydantic_criterion)

        # Create parent ticket to attach criterion
        ticket = TicketORM(
            id="test-001",
            name="Test",
            ticket_type="task",
            status="not_started",
            created_at=now,
            updated_at=now,
        )
        orm_criterion.ticket_id = "test-001"
        ticket.criteria.append(orm_criterion)
        session.add(ticket)
        session.commit()

        # Load from DB and convert back
        loaded_orm = session.get(CriterionORM, "crit-001")
        roundtrip_criterion = loaded_orm.to_pydantic()

        # Verify
        assert roundtrip_criterion.id == pydantic_criterion.id
        assert roundtrip_criterion.description == pydantic_criterion.description
        assert roundtrip_criterion.required == pydantic_criterion.required
        assert roundtrip_criterion.blocks_transition_to == pydantic_criterion.blocks_transition_to
        assert isinstance(roundtrip_criterion.target, TestPassesTarget)
        assert roundtrip_criterion.target.test_command == "pytest tests/"

    def test_task_ticket_orm_roundtrip(self, session, now):
        """TaskTicket round-trips correctly with task-specific fields."""
        # Create parent hierarchy first (roadmap -> track -> sprint)
        roadmap = RoadmapTicket(
            id="roadmap-001",
            name="Test Roadmap",
            created_at=now,
            updated_at=now,
        )
        orm_roadmap = RoadmapTicketORM.from_pydantic(roadmap)
        session.add(orm_roadmap)

        track = TrackTicket(
            id="track-001",
            name="Test Track",
            created_at=now,
            updated_at=now,
            roadmap_id="roadmap-001",
            parent_ref="roadmap-001",
        )
        orm_track = TrackTicketORM.from_pydantic(track)
        session.add(orm_track)

        sprint = SprintTicket(
            id="sprint-001",
            name="Test Sprint",
            created_at=now,
            updated_at=now,
            track_id="track-001",
            roadmap_id="roadmap-001",
            parent_ref="track-001",
        )
        orm_sprint = SprintTicketORM.from_pydantic(sprint)
        session.add(orm_sprint)
        session.commit()

        pydantic_task = TaskTicket(
            id="task-001",
            name="Implementation Task",
            description="Implement the feature",
            created_at=now,
            updated_at=now,
            task_type_detail=TaskType.DEVELOPMENT,  # Correct field name
            estimated_tokens=2500,
            actual_tokens=3000,
            complexity=Complexity.MEDIUM,
            phase_label="implementation",
            sprint_id="sprint-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            parent_ref="sprint-001",  # Required for TaskTicket
        )

        # Convert to ORM
        orm_task = TaskTicketORM.from_pydantic(pydantic_task)
        session.add(orm_task)
        session.commit()

        # Load and convert back
        loaded_orm = session.get(TicketORM, "task-001")
        roundtrip_task = loaded_orm.to_pydantic()

        # Verify task-specific fields
        assert isinstance(roundtrip_task, TaskTicket)
        assert roundtrip_task.task_type_detail == TaskType.DEVELOPMENT
        assert roundtrip_task.estimated_tokens == 2500
        assert roundtrip_task.actual_tokens == 3000
        assert roundtrip_task.complexity == Complexity.MEDIUM
        assert roundtrip_task.phase_label == "implementation"


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_ticket_orm_class_roadmap(self):
        """get_ticket_orm_class returns RoadmapTicketORM for roadmap type."""
        cls = get_ticket_orm_class("roadmap")
        assert cls == RoadmapTicketORM

    def test_get_ticket_orm_class_track(self):
        """get_ticket_orm_class returns TrackTicketORM for track type."""
        cls = get_ticket_orm_class("track")
        assert cls == TrackTicketORM

    def test_get_ticket_orm_class_sprint(self):
        """get_ticket_orm_class returns SprintTicketORM for sprint type."""
        cls = get_ticket_orm_class("sprint")
        assert cls == SprintTicketORM

    def test_get_ticket_orm_class_task(self):
        """get_ticket_orm_class returns TaskTicketORM for task type."""
        cls = get_ticket_orm_class("task")
        assert cls == TaskTicketORM

    def test_get_ticket_orm_class_with_enum(self):
        """get_ticket_orm_class accepts TicketType enum."""
        cls = get_ticket_orm_class(TicketType.TASK)
        assert cls == TaskTicketORM

    def test_get_ticket_orm_class_unknown(self):
        """get_ticket_orm_class returns TicketORM for unknown type."""
        cls = get_ticket_orm_class("unknown")
        assert cls == TicketORM
