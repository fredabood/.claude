"""
Tests for Completable and Criterion classes.
"""

import pytest
from datetime import datetime

from vibey.roadmap.models.ticket.completable import Completable, Criterion
from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
    ManualTarget,
)
from vibey.roadmap.models.ticket.enums import TicketStatus


class TestCriterion:
    """Tests for Criterion class."""

    def test_basic_criterion(self):
        """Test basic criterion creation."""
        target = ManualTarget()
        criterion = Criterion(
            id="test-criterion",
            description="Test must pass",
            target=target,
        )
        assert criterion.id == "test-criterion"
        assert criterion.description == "Test must pass"
        assert criterion.blocks_transition_to == TicketStatus.COMPLETED
        assert criterion.required
        assert not criterion.is_met  # ManualTarget not assessed

    def test_criterion_blocks_transition_to(self):
        """Test criterion with different blocking targets."""
        target = ManualTarget(assessed=True, met=True)

        # Default blocks COMPLETED
        criterion1 = Criterion(
            id="c1",
            description="Completion criterion",
            target=target,
        )
        assert criterion1.blocks_transition_to == TicketStatus.COMPLETED

        # Explicit IN_PROGRESS (dependency)
        criterion2 = Criterion(
            id="c2",
            description="Dependency",
            target=target,
            blocks_transition_to=TicketStatus.IN_PROGRESS,
        )
        assert criterion2.blocks_transition_to == TicketStatus.IN_PROGRESS

        # Explicit PRODUCTION_READY (production gate)
        criterion3 = Criterion(
            id="c3",
            description="Production gate",
            target=target,
            blocks_transition_to=TicketStatus.PRODUCTION_READY,
        )
        assert criterion3.blocks_transition_to == TicketStatus.PRODUCTION_READY

    def test_criterion_is_met_required(self):
        """Test is_met for required criterion."""
        # Unmet target
        unmet_target = ManualTarget()
        criterion = Criterion(
            id="c1",
            description="Test",
            target=unmet_target,
            required=True,
        )
        assert not criterion.is_met

        # Met target
        met_target = ManualTarget(assessed=True, met=True)
        criterion2 = Criterion(
            id="c2",
            description="Test",
            target=met_target,
            required=True,
        )
        assert criterion2.is_met

    def test_criterion_is_met_not_required(self):
        """Test is_met for non-required criterion."""
        # Even with unmet target, non-required is always met
        unmet_target = ManualTarget()
        criterion = Criterion(
            id="c1",
            description="Optional test",
            target=unmet_target,
            required=False,
        )
        assert criterion.is_met

    def test_criterion_with_completable_target(self):
        """Test criterion with CompletableTarget."""
        target = CompletableTarget(
            completable_id="task-001",
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.IN_PROGRESS,
        )
        criterion = Criterion(
            id="dep-task-001",
            description="Task 001 must complete",
            target=target,
            blocks_transition_to=TicketStatus.IN_PROGRESS,
        )
        assert not criterion.is_met  # IN_PROGRESS < COMPLETED

        # Update target status
        target.current_status = TicketStatus.COMPLETED
        assert criterion.is_met

    def test_criterion_status_description(self):
        """Test status_description property."""
        target = ManualTarget()
        criterion = Criterion(
            id="c1",
            description="Review required",
            target=target,
        )
        desc = criterion.status_description
        assert "Awaiting" in desc or "manual" in desc.lower()


class TestCompletable:
    """Tests for Completable class."""

    def test_basic_completable(self):
        """Test basic completable creation."""
        completable = Completable(
            id="test-001",
            name="Test Completable",
            description="A test item",
        )
        assert completable.id == "test-001"
        assert completable.name == "Test Completable"
        assert completable.description == "A test item"
        assert completable.criteria == []
        assert completable.children == []

    def test_completable_no_criteria_is_complete(self):
        """Test completable with no criteria is considered complete."""
        completable = Completable(id="test-001", name="Test")
        assert completable.is_complete
        can_complete, reasons = completable.can_complete()
        assert can_complete
        assert reasons == []

    def test_completable_with_met_criteria(self):
        """Test completable with all criteria met."""
        target = ManualTarget(assessed=True, met=True)
        criterion = Criterion(
            id="c1",
            description="Manual check",
            target=target,
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[criterion],
        )
        assert completable.is_complete
        can_complete, reasons = completable.can_complete()
        assert can_complete
        assert reasons == []

    def test_completable_with_unmet_criteria(self):
        """Test completable with unmet criteria."""
        target = ManualTarget()
        criterion = Criterion(
            id="c1",
            description="Manual check required",
            target=target,
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[criterion],
        )
        assert not completable.is_complete
        can_complete, reasons = completable.can_complete()
        assert not can_complete
        assert "Manual check required" in reasons

    def test_can_transition_to_in_progress(self):
        """Test can_transition_to for IN_PROGRESS (dependencies)."""
        dep_target = CompletableTarget(
            completable_id="task-000",
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.NOT_STARTED,
        )
        dep_criterion = Criterion(
            id="dep-task-000",
            description="Task 000 must complete first",
            target=dep_target,
            blocks_transition_to=TicketStatus.IN_PROGRESS,
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[dep_criterion],
        )

        # Cannot start because dependency not met
        can_start, reasons = completable.can_start()
        assert not can_start
        assert "Task 000 must complete first" in reasons

        # Update dependency status
        dep_target.current_status = TicketStatus.COMPLETED
        can_start, reasons = completable.can_start()
        assert can_start
        assert reasons == []

    def test_can_transition_to_production_ready(self):
        """Test can_transition_to for PRODUCTION_READY."""
        gate_target = ManualTarget()
        gate_criterion = Criterion(
            id="prod-gate",
            description="Security review required",
            target=gate_target,
            blocks_transition_to=TicketStatus.PRODUCTION_READY,
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[gate_criterion],
        )

        # Can complete (no COMPLETED criteria)
        can_complete, _ = completable.can_complete()
        assert can_complete

        # Cannot deploy (PRODUCTION_READY blocked)
        can_deploy, reasons = completable.can_deploy()
        assert not can_deploy
        assert "Security review required" in reasons

    def test_progress_for_transition(self):
        """Test progress_for_transition method."""
        met_target = ManualTarget(assessed=True, met=True)
        unmet_target = ManualTarget()

        criteria = [
            Criterion(id="c1", description="Check 1", target=met_target),
            Criterion(id="c2", description="Check 2", target=unmet_target),
            Criterion(id="c3", description="Check 3", target=met_target),
        ]
        completable = Completable(id="test-001", name="Test", criteria=criteria)

        progress = completable.progress_for_transition(TicketStatus.COMPLETED)
        assert progress.total == 3
        assert progress.completed == 2
        assert progress.completion_percent == pytest.approx(66.7, rel=0.1)

    def test_progress_default(self):
        """Test default progress property."""
        target = ManualTarget(assessed=True, met=True)
        criterion = Criterion(id="c1", description="Check", target=target)
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[criterion],
        )
        progress = completable.progress
        assert progress.total == 1
        assert progress.completed == 1
        assert progress.is_complete

    def test_children_from_completable_targets(self):
        """Test that children are derived from CompletableTarget criteria."""
        target1 = CompletableTarget(completable_id="child-001")
        target2 = CompletableTarget(completable_id="child-002")
        manual = ManualTarget()

        criteria = [
            Criterion(id="c1", description="Child 1", target=target1),
            Criterion(id="c2", description="Child 2", target=target2),
            Criterion(id="c3", description="Manual", target=manual),
        ]
        completable = Completable(id="parent-001", name="Parent", criteria=criteria)

        # Only CompletableTarget children are included
        assert completable.children == ["child-001", "child-002"]

    def test_add_criterion(self):
        """Test adding a criterion."""
        completable = Completable(id="test-001", name="Test")
        assert len(completable.criteria) == 0

        criterion = Criterion(
            id="c1",
            description="New criterion",
            target=ManualTarget(),
        )
        completable.add_criterion(criterion)
        assert len(completable.criteria) == 1
        assert completable.get_criterion("c1") == criterion

    def test_add_criterion_duplicate_id_raises(self):
        """Test that adding duplicate criterion ID raises error."""
        completable = Completable(id="test-001", name="Test")
        criterion1 = Criterion(id="c1", description="First", target=ManualTarget())
        criterion2 = Criterion(id="c1", description="Duplicate", target=ManualTarget())

        completable.add_criterion(criterion1)
        with pytest.raises(ValueError, match="already exists"):
            completable.add_criterion(criterion2)

    def test_remove_criterion(self):
        """Test removing a criterion."""
        criterion = Criterion(id="c1", description="Test", target=ManualTarget())
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[criterion],
        )

        assert completable.remove_criterion("c1")
        assert len(completable.criteria) == 0
        assert completable.get_criterion("c1") is None

        # Removing non-existent returns False
        assert not completable.remove_criterion("c1")

    def test_get_criterion(self):
        """Test getting a criterion by ID."""
        criterion = Criterion(id="c1", description="Test", target=ManualTarget())
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[criterion],
        )

        assert completable.get_criterion("c1") == criterion
        assert completable.get_criterion("nonexistent") is None

    def test_blocking_reasons(self):
        """Test blocking_reasons property."""
        criterion = Criterion(
            id="c1",
            description="This is blocking",
            target=ManualTarget(),
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[criterion],
        )

        reasons = completable.blocking_reasons
        assert "This is blocking" in reasons

    def test_criteria_for_transition(self):
        """Test criteria_for_transition method."""
        start_criterion = Criterion(
            id="c1",
            description="Dependency",
            target=ManualTarget(assessed=True, met=True),
            blocks_transition_to=TicketStatus.IN_PROGRESS,
        )
        complete_criterion = Criterion(
            id="c2",
            description="Success",
            target=ManualTarget(),
            blocks_transition_to=TicketStatus.COMPLETED,
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[start_criterion, complete_criterion],
        )

        start_criteria = completable.criteria_for_transition(TicketStatus.IN_PROGRESS)
        assert len(start_criteria) == 1
        assert start_criteria[0].id == "c1"

        complete_criteria = completable.criteria_for_transition(TicketStatus.COMPLETED)
        assert len(complete_criteria) == 1
        assert complete_criteria[0].id == "c2"

    def test_blocking_criteria_for_transition(self):
        """Test blocking_criteria_for_transition method."""
        met_criterion = Criterion(
            id="c1",
            description="Met",
            target=ManualTarget(assessed=True, met=True),
        )
        unmet_criterion = Criterion(
            id="c2",
            description="Unmet",
            target=ManualTarget(),
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[met_criterion, unmet_criterion],
        )

        blocking = completable.blocking_criteria_for_transition(TicketStatus.COMPLETED)
        assert len(blocking) == 1
        assert blocking[0].id == "c2"

    def test_met_criteria_for_transition(self):
        """Test met_criteria_for_transition method."""
        met_criterion = Criterion(
            id="c1",
            description="Met",
            target=ManualTarget(assessed=True, met=True),
        )
        unmet_criterion = Criterion(
            id="c2",
            description="Unmet",
            target=ManualTarget(),
        )
        completable = Completable(
            id="test-001",
            name="Test",
            criteria=[met_criterion, unmet_criterion],
        )

        met = completable.met_criteria_for_transition(TicketStatus.COMPLETED)
        assert len(met) == 1
        assert met[0].id == "c1"


class TestDependencyAsCriterion:
    """
    Tests verifying that dependencies are properly represented as criteria.

    This demonstrates that the Dependency class has been eliminated and
    dependencies are now unified as Criterion with blocks_transition_to=IN_PROGRESS.
    """

    def test_dependency_as_criterion(self):
        """Test representing a dependency as a criterion."""
        # OLD: would have been a Dependency object
        # NEW: it's a Criterion with CompletableTarget

        dependency_target = CompletableTarget(
            completable_id="prerequisite-task",
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.NOT_STARTED,
        )
        dependency_criterion = Criterion(
            id="dep-prerequisite",
            description="Prerequisite task must complete before starting",
            target=dependency_target,
            blocks_transition_to=TicketStatus.IN_PROGRESS,  # This makes it a "dependency"
        )

        task = Completable(
            id="dependent-task",
            name="Dependent Task",
            criteria=[dependency_criterion],
        )

        # Task cannot start (dependency not met)
        can_start, reasons = task.can_start()
        assert not can_start
        assert "Prerequisite task must complete before starting" in reasons

        # Task can complete (no COMPLETED criteria)
        can_complete, _ = task.can_complete()
        assert can_complete

        # Satisfy the dependency
        dependency_target.current_status = TicketStatus.COMPLETED

        # Now task can start
        can_start, reasons = task.can_start()
        assert can_start
        assert reasons == []

    def test_multiple_dependencies(self):
        """Test multiple dependencies as criteria."""
        dep1 = CompletableTarget(
            completable_id="task-001",
            current_status=TicketStatus.COMPLETED,
        )
        dep2 = CompletableTarget(
            completable_id="task-002",
            current_status=TicketStatus.NOT_STARTED,
        )

        task = Completable(
            id="task-003",
            name="Task 003",
            criteria=[
                Criterion(
                    id="dep-001",
                    description="Depends on task-001",
                    target=dep1,
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
                Criterion(
                    id="dep-002",
                    description="Depends on task-002",
                    target=dep2,
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
            ],
        )

        # Cannot start because dep2 not met
        can_start, reasons = task.can_start()
        assert not can_start
        assert len(reasons) == 1
        assert "task-002" in reasons[0]

        # Progress shows 1/2 dependencies met
        progress = task.progress_for_transition(TicketStatus.IN_PROGRESS)
        assert progress.completed == 1
        assert progress.total == 2
