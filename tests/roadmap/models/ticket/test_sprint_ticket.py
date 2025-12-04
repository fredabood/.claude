"""
Tests for SprintTicket (Layer 3 domain model).

Tests cover:
- SprintTicket creation with required fields
- Intermediate hierarchy constraints (must have parent)
- Parent reference validation (track_id must match parent_ref)
- Extended lifecycle timestamps and ordering
- Development gate management
- Task criteria and progress tracking
- Lifecycle transition methods
"""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from vibey.roadmap.models.ticket import (
    Completable,
    CompletableTarget,
    Criterion,
    DevelopmentGate,
    GateStatus,
    SprintTicket,
    TicketLoader,
    TicketStatus,
    TicketType,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


def make_task_criterion(
    task_id: str,
    completed: bool = False,
) -> Criterion:
    """Helper to create a task criterion."""
    return Criterion(
        id=f"criterion-{task_id}",
        name=f"Task {task_id}",
        description=f"Task {task_id} must be completed",
        target=CompletableTarget(
            completable_id=task_id,
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.COMPLETED if completed else TicketStatus.NOT_STARTED,
        ),
        blocks_transition_to=TicketStatus.COMPLETED,
    )


class MockTaskTicket:
    """Mock task for testing sprint aggregate methods."""

    def __init__(self):
        self.parent_ref = None
        self.requirements_local = []
        self.all_criteria: List[Criterion] = []

    @property
    def parent(self):
        return None


class MockLoader:
    """Mock loader for testing hierarchy navigation."""

    def __init__(self):
        self.tickets = {}

    def load(self, ticket_id: str) -> Completable:
        if ticket_id not in self.tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        return self.tickets[ticket_id]


@pytest.fixture
def mock_loader():
    """Provide a mock loader."""
    return MockLoader()


@pytest.fixture
def base_sprint_kwargs():
    """Base kwargs for creating a valid SprintTicket."""
    created = datetime.now(timezone.utc) - timedelta(hours=1)
    return {
        "id": "sprint-1",
        "name": "Sprint 1",
        "track_id": "track-1",
        "roadmap_id": "roadmap-1",
        "parent_ref": "track-1",
        "created_at": created,
    }


# =============================================================================
# BASIC CREATION TESTS
# =============================================================================


class TestSprintTicketCreation:
    """Tests for SprintTicket instantiation."""

    def test_create_minimal_sprint(self, base_sprint_kwargs):
        """SprintTicket can be created with minimal required fields."""
        sprint = SprintTicket(**base_sprint_kwargs)

        assert sprint.id == "sprint-1"
        assert sprint.name == "Sprint 1"
        assert sprint.track_id == "track-1"
        assert sprint.roadmap_id == "roadmap-1"
        assert sprint.parent_ref == "track-1"
        assert sprint.ticket_type == TicketType.SPRINT

    def test_create_sprint_with_planning_fields(self, base_sprint_kwargs):
        """SprintTicket can be created with planning fields."""
        sprint = SprintTicket(
            **base_sprint_kwargs,
            goal="Complete the MVP",
            plan_file="docs/sprint-1-plan.md",
            success_criteria_text=["Feature A working", "Tests passing"],
            risks=["Time constraint", "Technical complexity"],
        )

        assert sprint.goal == "Complete the MVP"
        assert sprint.plan_file == "docs/sprint-1-plan.md"
        assert len(sprint.success_criteria_text) == 2
        assert len(sprint.risks) == 2

    def test_create_sprint_with_estimation(self, base_sprint_kwargs):
        """SprintTicket can be created with estimation fields."""
        sprint = SprintTicket(
            **base_sprint_kwargs,
            estimated_tokens=10000,
            actual_tokens=8500,
        )

        assert sprint.estimated_tokens == 10000
        assert sprint.actual_tokens == 8500

    def test_create_sprint_with_development_gates(self, base_sprint_kwargs):
        """SprintTicket can be created with development gates."""
        gates = [
            DevelopmentGate(name="code_review", description="Code review required"),
            DevelopmentGate(name="security_audit", blocking=False),
        ]
        sprint = SprintTicket(
            **base_sprint_kwargs,
            development_gates=gates,
        )

        assert len(sprint.development_gates) == 2
        assert sprint.development_gates[0].name == "code_review"
        assert sprint.development_gates[1].blocking is False


# =============================================================================
# HIERARCHY CONSTRAINT TESTS
# =============================================================================


class TestSprintHierarchyConstraints:
    """Tests for SprintTicket hierarchy constraints."""

    def test_sprint_requires_parent_ref(self, base_sprint_kwargs):
        """SprintTicket must have parent_ref set."""
        kwargs = {**base_sprint_kwargs}
        del kwargs["parent_ref"]
        kwargs["parent_ref"] = None

        with pytest.raises(ValueError, match="must have a parent_ref"):
            SprintTicket(**kwargs)

    def test_parent_ref_must_match_track_id(self, base_sprint_kwargs):
        """parent_ref must match track_id."""
        kwargs = {**base_sprint_kwargs}
        kwargs["parent_ref"] = "different-track"

        with pytest.raises(ValueError, match="must match track_id"):
            SprintTicket(**kwargs)

    def test_track_id_cannot_be_empty(self, base_sprint_kwargs):
        """track_id cannot be empty."""
        kwargs = {**base_sprint_kwargs}
        kwargs["track_id"] = ""
        kwargs["parent_ref"] = ""

        with pytest.raises(ValueError, match="cannot be empty"):
            SprintTicket(**kwargs)

    def test_roadmap_id_cannot_be_empty(self, base_sprint_kwargs):
        """roadmap_id cannot be empty."""
        kwargs = {**base_sprint_kwargs}
        kwargs["roadmap_id"] = "  "

        with pytest.raises(ValueError, match="cannot be empty"):
            SprintTicket(**kwargs)

    def test_is_intermediate_always_true(self, base_sprint_kwargs):
        """Sprint is_intermediate is always True."""
        sprint = SprintTicket(**base_sprint_kwargs)

        assert sprint.is_intermediate is True

    def test_is_ultimate_parent_always_false(self, base_sprint_kwargs):
        """Sprint is_ultimate_parent is always False."""
        sprint = SprintTicket(**base_sprint_kwargs)

        assert sprint.is_ultimate_parent is False

    def test_is_ultimate_child_always_false(self, base_sprint_kwargs):
        """Sprint is_ultimate_child is always False."""
        sprint = SprintTicket(**base_sprint_kwargs)

        assert sprint.is_ultimate_child is False

    def test_is_child_always_true(self, base_sprint_kwargs):
        """Sprint is_child is always True."""
        sprint = SprintTicket(**base_sprint_kwargs)

        assert sprint.is_child is True


# =============================================================================
# EXTENDED LIFECYCLE TIMESTAMP TESTS
# =============================================================================


class TestExtendedLifecycleTimestamps:
    """Tests for extended lifecycle timestamp validation."""

    def test_valid_timestamp_progression(self, base_sprint_kwargs):
        """Valid timestamp progression is accepted."""
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=10)
        sprint = SprintTicket(
            **kwargs,
            started_at=now - timedelta(hours=5),
            completed_at=now - timedelta(hours=4),
            completion_gate_check_at=now - timedelta(hours=3),
            production_gate_check_at=now - timedelta(hours=2),
            production_ready_at=now - timedelta(hours=1),
            deployed_at=now,
        )

        assert sprint.deployed_at is not None

    def test_completion_gate_before_completed_fails(self, base_sprint_kwargs):
        """completion_gate_check_at cannot be before completed_at."""
        now = datetime.now(timezone.utc)
        kwargs = {
            **base_sprint_kwargs,
            "started_at": now - timedelta(hours=3),
            "completed_at": now - timedelta(hours=1),
            "completion_gate_check_at": now - timedelta(hours=2),  # Before completed
        }

        with pytest.raises(ValueError, match="cannot be before"):
            SprintTicket(**kwargs)

    def test_production_gate_before_completion_gate_fails(self, base_sprint_kwargs):
        """production_gate_check_at cannot be before completion_gate_check_at."""
        now = datetime.now(timezone.utc)
        kwargs = {
            **base_sprint_kwargs,
            "started_at": now - timedelta(hours=5),
            "completed_at": now - timedelta(hours=4),
            "completion_gate_check_at": now - timedelta(hours=2),
            "production_gate_check_at": now - timedelta(hours=3),  # Before completion gate
        }

        with pytest.raises(ValueError, match="cannot be before"):
            SprintTicket(**kwargs)

    def test_deployed_before_production_ready_fails(self, base_sprint_kwargs):
        """deployed_at cannot be before production_ready_at."""
        now = datetime.now(timezone.utc)
        kwargs = {
            **base_sprint_kwargs,
            "started_at": now - timedelta(hours=5),
            "completed_at": now - timedelta(hours=4),
            "production_ready_at": now - timedelta(hours=1),
            "deployed_at": now - timedelta(hours=2),  # Before production ready
        }

        with pytest.raises(ValueError, match="cannot be before"):
            SprintTicket(**kwargs)


# =============================================================================
# TASK CRITERIA TESTS
# =============================================================================


class TestTaskCriteria:
    """Tests for task criteria accessors."""

    def test_task_criteria_returns_completable_targets(self, base_sprint_kwargs):
        """task_criteria returns CompletableTarget criteria blocking completion."""
        criteria = [
            make_task_criterion("task-1"),
            make_task_criterion("task-2", completed=True),
        ]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        assert len(sprint.task_criteria) == 2

    def test_tasks_total_counts_all_tasks(self, base_sprint_kwargs):
        """tasks_total returns count of all task criteria."""
        criteria = [
            make_task_criterion("task-1"),
            make_task_criterion("task-2"),
            make_task_criterion("task-3"),
        ]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        assert sprint.tasks_total == 3

    def test_tasks_completed_counts_met_criteria(self, base_sprint_kwargs):
        """tasks_completed returns count of completed task criteria."""
        criteria = [
            make_task_criterion("task-1", completed=True),
            make_task_criterion("task-2", completed=True),
            make_task_criterion("task-3", completed=False),
        ]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        assert sprint.tasks_completed == 2

    def test_get_task_ids_returns_all_task_ids(self, base_sprint_kwargs):
        """get_task_ids returns list of task IDs from criteria."""
        criteria = [
            make_task_criterion("task-1"),
            make_task_criterion("task-2"),
        ]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        task_ids = sprint.get_task_ids()
        assert "task-1" in task_ids
        assert "task-2" in task_ids


# =============================================================================
# DEVELOPMENT GATE TESTS
# =============================================================================


class TestDevelopmentGates:
    """Tests for development gate management."""

    def test_add_gate(self, base_sprint_kwargs):
        """add_gate adds a new development gate."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("code_review", "All code must be reviewed")

        assert len(sprint.development_gates) == 1
        assert sprint.development_gates[0].name == "code_review"
        assert sprint.development_gates[0].blocking is True

    def test_add_non_blocking_gate(self, base_sprint_kwargs):
        """add_gate can add non-blocking gates."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("documentation", blocking=False)

        assert sprint.development_gates[0].blocking is False

    def test_resolve_gate_pass(self, base_sprint_kwargs):
        """resolve_gate can pass a gate."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("code_review")
        sprint = sprint.resolve_gate("code_review", passed=True, resolver="reviewer-1")

        assert sprint.development_gates[0].status == GateStatus.PASSED
        assert sprint.development_gates[0].resolver == "reviewer-1"
        assert sprint.development_gates[0].resolved_at is not None

    def test_resolve_gate_fail(self, base_sprint_kwargs):
        """resolve_gate can fail a gate."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("security_audit")
        sprint = sprint.resolve_gate("security_audit", passed=False)

        assert sprint.development_gates[0].status == GateStatus.FAILED

    def test_resolve_nonexistent_gate_raises(self, base_sprint_kwargs):
        """resolve_gate raises ValueError for nonexistent gate."""
        sprint = SprintTicket(**base_sprint_kwargs)

        with pytest.raises(ValueError, match="not found"):
            sprint.resolve_gate("nonexistent", passed=True)

    def test_blocking_gates_returns_unresolved_blocking_gates(self, base_sprint_kwargs):
        """blocking_gates returns only blocking gates that are unresolved."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("code_review")
        sprint = sprint.add_gate("security_audit")
        sprint = sprint.add_gate("optional_check", blocking=False)
        sprint = sprint.resolve_gate("code_review", passed=True)

        assert len(sprint.blocking_gates) == 1
        assert sprint.blocking_gates[0].name == "security_audit"

    def test_all_gates_passed_when_all_blocking_passed(self, base_sprint_kwargs):
        """all_gates_passed is True when all blocking gates passed."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("code_review")
        sprint = sprint.add_gate("optional", blocking=False)
        sprint = sprint.resolve_gate("code_review", passed=True)

        assert sprint.all_gates_passed is True

    def test_all_gates_passed_false_when_blocking_gate_not_passed(self, base_sprint_kwargs):
        """all_gates_passed is False when blocking gate not passed."""
        sprint = SprintTicket(**base_sprint_kwargs)
        sprint = sprint.add_gate("code_review")

        assert sprint.all_gates_passed is False


# =============================================================================
# GATE STATUS ENUM TESTS
# =============================================================================


class TestGateStatus:
    """Tests for GateStatus enum."""

    def test_is_resolved_for_passed(self):
        """PASSED status is resolved."""
        assert GateStatus.PASSED.is_resolved() is True

    def test_is_resolved_for_failed(self):
        """FAILED status is resolved."""
        assert GateStatus.FAILED.is_resolved() is True

    def test_is_resolved_for_not_started(self):
        """NOT_STARTED status is not resolved."""
        assert GateStatus.NOT_STARTED.is_resolved() is False

    def test_is_blocking_for_not_started(self):
        """NOT_STARTED status is blocking."""
        assert GateStatus.NOT_STARTED.is_blocking() is True

    def test_is_blocking_for_passed(self):
        """PASSED status is not blocking."""
        assert GateStatus.PASSED.is_blocking() is False


# =============================================================================
# DEVELOPMENT GATE CLASS TESTS
# =============================================================================


class TestDevelopmentGate:
    """Tests for DevelopmentGate class."""

    def test_create_gate(self):
        """DevelopmentGate can be created with minimal fields."""
        gate = DevelopmentGate(name="code_review")

        assert gate.name == "code_review"
        assert gate.status == GateStatus.NOT_STARTED
        assert gate.blocking is True

    def test_pass_gate(self):
        """pass_gate returns new gate with PASSED status."""
        gate = DevelopmentGate(name="code_review")
        passed = gate.pass_gate("reviewer")

        assert passed.status == GateStatus.PASSED
        assert passed.resolver == "reviewer"
        assert passed.resolved_at is not None

    def test_fail_gate(self):
        """fail_gate returns new gate with FAILED status."""
        gate = DevelopmentGate(name="security")
        failed = gate.fail_gate()

        assert failed.status == GateStatus.FAILED
        assert failed.resolved_at is not None


# =============================================================================
# LIFECYCLE TRANSITION TESTS
# =============================================================================


class TestLifecycleTransitions:
    """Tests for lifecycle transition methods."""

    def test_can_enter_completion_gate_check_when_all_tasks_done(self, base_sprint_kwargs):
        """can_enter_completion_gate_check returns True when all tasks complete."""
        criteria = [
            make_task_criterion("task-1", completed=True),
            make_task_criterion("task-2", completed=True),
        ]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        assert sprint.can_enter_completion_gate_check() is True

    def test_can_enter_completion_gate_check_false_when_tasks_incomplete(self, base_sprint_kwargs):
        """can_enter_completion_gate_check returns False when tasks incomplete."""
        criteria = [
            make_task_criterion("task-1", completed=True),
            make_task_criterion("task-2", completed=False),
        ]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        assert sprint.can_enter_completion_gate_check() is False

    def test_can_enter_completion_gate_check_false_when_no_tasks(self, base_sprint_kwargs):
        """can_enter_completion_gate_check returns False when no tasks."""
        sprint = SprintTicket(**base_sprint_kwargs)

        assert sprint.can_enter_completion_gate_check() is False

    def test_can_complete_requires_tasks_and_gates(self, base_sprint_kwargs):
        """can_complete requires all tasks done AND all gates passed."""
        criteria = [make_task_criterion("task-1", completed=True)]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)
        sprint = sprint.add_gate("review")

        can, reasons = sprint.can_complete()
        assert can is False
        assert any("gates" in r.lower() for r in reasons)

        sprint = sprint.resolve_gate("review", passed=True)
        can, reasons = sprint.can_complete()
        assert can is True

    def test_enter_completion_gate_check(self, base_sprint_kwargs):
        """enter_completion_gate_check transitions to COMPLETION_GATE_CHECK."""
        criteria = [make_task_criterion("task-1", completed=True)]
        started_at = datetime.now(timezone.utc) - timedelta(hours=1)
        sprint = SprintTicket(
            **base_sprint_kwargs,
            criteria=criteria,
            status=TicketStatus.IN_PROGRESS,
            started_at=started_at,
        )

        sprint = sprint.enter_completion_gate_check()

        assert sprint.status == TicketStatus.COMPLETION_GATE_CHECK
        assert sprint.completion_gate_check_at is not None

    def test_enter_completion_gate_check_fails_when_tasks_incomplete(self, base_sprint_kwargs):
        """enter_completion_gate_check raises ValueError when tasks incomplete."""
        criteria = [make_task_criterion("task-1", completed=False)]
        sprint = SprintTicket(**base_sprint_kwargs, criteria=criteria)

        with pytest.raises(ValueError, match="0/1 tasks completed"):
            sprint.enter_completion_gate_check()

    def test_enter_production_gate_check(self, base_sprint_kwargs):
        """enter_production_gate_check transitions to PRODUCTION_GATE_CHECK."""
        criteria = [make_task_criterion("task-1", completed=True)]
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=5)
        sprint = SprintTicket(
            **kwargs,
            criteria=criteria,
            status=TicketStatus.COMPLETED,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1),
        )

        sprint = sprint.enter_production_gate_check()

        assert sprint.status == TicketStatus.PRODUCTION_GATE_CHECK
        assert sprint.production_gate_check_at is not None

    def test_enter_production_gate_check_fails_when_not_completed(self, base_sprint_kwargs):
        """enter_production_gate_check raises ValueError when not completed."""
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=2)
        sprint = SprintTicket(
            **kwargs,
            status=TicketStatus.IN_PROGRESS,
            started_at=now - timedelta(hours=1),
        )

        with pytest.raises(ValueError, match="must be completed first"):
            sprint.enter_production_gate_check()

    def test_mark_production_ready(self, base_sprint_kwargs):
        """mark_production_ready transitions to PRODUCTION_READY."""
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=5)
        sprint = SprintTicket(
            **kwargs,
            status=TicketStatus.PRODUCTION_GATE_CHECK,
            started_at=now - timedelta(hours=3),
            completed_at=now - timedelta(hours=2),
            production_gate_check_at=now - timedelta(hours=1),
        )

        sprint = sprint.mark_production_ready()

        assert sprint.status == TicketStatus.PRODUCTION_READY
        assert sprint.production_ready_at is not None

    def test_mark_production_ready_fails_when_not_in_gate_check(self, base_sprint_kwargs):
        """mark_production_ready raises ValueError when not in gate check."""
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=3)
        sprint = SprintTicket(
            **kwargs,
            status=TicketStatus.COMPLETED,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1),
        )

        with pytest.raises(ValueError, match="must be in production gate check"):
            sprint.mark_production_ready()

    def test_deploy(self, base_sprint_kwargs):
        """deploy transitions to DEPLOYED."""
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=6)
        sprint = SprintTicket(
            **kwargs,
            status=TicketStatus.PRODUCTION_READY,
            started_at=now - timedelta(hours=4),
            completed_at=now - timedelta(hours=3),
            production_gate_check_at=now - timedelta(hours=2),
            production_ready_at=now - timedelta(hours=1),
        )

        sprint = sprint.deploy()

        assert sprint.status == TicketStatus.DEPLOYED
        assert sprint.deployed_at is not None

    def test_deploy_fails_when_not_production_ready(self, base_sprint_kwargs):
        """deploy raises ValueError when not production ready."""
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=3)
        sprint = SprintTicket(
            **kwargs,
            status=TicketStatus.COMPLETED,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1),
        )

        with pytest.raises(ValueError, match="must be production ready"):
            sprint.deploy()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSprintIntegration:
    """Integration tests for SprintTicket."""

    def test_full_sprint_lifecycle(self, base_sprint_kwargs):
        """Test complete sprint lifecycle from creation to deployment."""
        # Create sprint with tasks and gates
        criteria = [
            make_task_criterion("task-1", completed=True),
            make_task_criterion("task-2", completed=True),
        ]
        now = datetime.now(timezone.utc)
        kwargs = {**base_sprint_kwargs}
        kwargs["created_at"] = now - timedelta(hours=20)
        sprint = SprintTicket(
            **kwargs,
            criteria=criteria,
            status=TicketStatus.IN_PROGRESS,
            started_at=now - timedelta(hours=10),
            goal="Complete the first sprint",
            risks=["Time constraint"],
        )
        sprint = sprint.add_gate("code_review")
        sprint = sprint.add_gate("security_audit")

        # Verify initial state
        assert sprint.tasks_total == 2
        assert sprint.tasks_completed == 2
        assert sprint.can_enter_completion_gate_check() is True
        can, reasons = sprint.can_complete()
        assert can is False  # Gates not passed

        # Pass gates
        sprint = sprint.resolve_gate("code_review", passed=True)
        sprint = sprint.resolve_gate("security_audit", passed=True)
        can, reasons = sprint.can_complete()
        assert can is True

        # Transition through lifecycle
        sprint = sprint.enter_completion_gate_check()
        assert sprint.status == TicketStatus.COMPLETION_GATE_CHECK

        # Complete and move to production
        sprint = sprint.complete()
        assert sprint.status == TicketStatus.COMPLETED

        sprint = sprint.enter_production_gate_check()
        sprint = sprint.mark_production_ready()
        sprint = sprint.deploy()

        # Verify final state
        assert sprint.status == TicketStatus.DEPLOYED
        assert sprint.deployed_at is not None
        assert sprint.production_ready_at is not None
        assert sprint.completion_gate_check_at is not None
