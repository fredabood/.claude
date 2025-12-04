"""
Tests for TaskTicket (Layer 3 domain model).

Tests cover:
- TaskTicket creation with required fields
- Ultimate child hierarchy constraints (must have parent, no children)
- Parent reference validation (sprint_id must match parent_ref)
- No CompletableTarget criteria allowed (leaf node)
- Task type classification (development, gate, documentation, etc.)
- Gate task validation (gate_info required for gate tasks)
- Token estimation and efficiency tracking
- Audit results management
- Size category computation
"""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from vibey.roadmap.models.ticket import (
    AuditResults,
    Complexity,
    CompletableTarget,
    Criterion,
    FileExistsTarget,
    GateInfo,
    SizeCategory,
    TaskTicket,
    TaskType,
    TestPassesTarget,
    ThresholdTarget,
    TicketStatus,
    TicketType,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


def make_file_criterion(criterion_id: str, path: str, exists: bool = False) -> Criterion:
    """Helper to create a FileExists criterion."""
    return Criterion(
        id=criterion_id,
        name=f"File {path}",
        description=f"File {path} must exist",
        target=FileExistsTarget(
            paths=[path],
            exists=exists,
        ),
        blocks_transition_to=TicketStatus.COMPLETED,
    )


def make_test_criterion(criterion_id: str, passed: bool = False) -> Criterion:
    """Helper to create a TestPasses criterion."""
    return Criterion(
        id=criterion_id,
        name="Test suite",
        description="Tests must pass",
        target=TestPassesTarget(
            test_command="pytest tests/",
            pass_threshold=100.0,
            current_pass_rate=100.0 if passed else 0.0,
        ),
        blocks_transition_to=TicketStatus.COMPLETED,
    )


@pytest.fixture
def base_task_kwargs():
    """Base kwargs for creating a valid TaskTicket."""
    created = datetime.now(timezone.utc) - timedelta(hours=1)
    return {
        "id": "task-1",
        "name": "Task 1",
        "sprint_id": "sprint-1",
        "track_id": "track-1",
        "roadmap_id": "roadmap-1",
        "parent_ref": "sprint-1",
        "created_at": created,
        "estimated_tokens": 1000,
    }


# =============================================================================
# BASIC CREATION TESTS
# =============================================================================


class TestTaskTicketCreation:
    """Tests for TaskTicket instantiation."""

    def test_create_minimal_task(self, base_task_kwargs):
        """TaskTicket can be created with minimal required fields."""
        task = TaskTicket(**base_task_kwargs)

        assert task.id == "task-1"
        assert task.name == "Task 1"
        assert task.sprint_id == "sprint-1"
        assert task.track_id == "track-1"
        assert task.roadmap_id == "roadmap-1"
        assert task.parent_ref == "sprint-1"
        assert task.ticket_type == TicketType.TASK
        assert task.estimated_tokens == 1000

    def test_create_task_with_classification(self, base_task_kwargs):
        """TaskTicket can be created with task type classification."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.DOCUMENTATION,
            title="Write API docs",
            phase_label="documentation",
        )

        assert task.task_type_detail == TaskType.DOCUMENTATION
        assert task.title == "Write API docs"
        assert task.phase_label == "documentation"

    def test_create_task_with_estimation(self, base_task_kwargs):
        """TaskTicket can be created with estimation fields."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 2000
        task = TaskTicket(
            **kwargs,
            actual_tokens=1800,
            complexity=Complexity.HIGH,
        )

        assert task.estimated_tokens == 2000
        assert task.actual_tokens == 1800
        assert task.complexity == Complexity.HIGH

    def test_create_task_with_assignment(self, base_task_kwargs):
        """TaskTicket can be created with assignment."""
        task = TaskTicket(
            **base_task_kwargs,
            assigned_agent="backend-engineer",
        )

        assert task.assigned_agent == "backend-engineer"

    def test_create_task_with_criteria(self, base_task_kwargs):
        """TaskTicket can be created with non-CompletableTarget criteria."""
        criteria = [
            make_file_criterion("file-1", "src/api.py", exists=True),
            make_test_criterion("tests-1", passed=True),
        ]
        task = TaskTicket(**base_task_kwargs, criteria=criteria)

        assert len(task.criteria) == 2


# =============================================================================
# HIERARCHY CONSTRAINT TESTS
# =============================================================================


class TestTaskHierarchyConstraints:
    """Tests for TaskTicket hierarchy constraints."""

    def test_task_requires_parent_ref(self, base_task_kwargs):
        """TaskTicket must have parent_ref set."""
        kwargs = {**base_task_kwargs}
        kwargs["parent_ref"] = None

        with pytest.raises(ValueError, match="must have a parent_ref"):
            TaskTicket(**kwargs)

    def test_parent_ref_must_match_sprint_id(self, base_task_kwargs):
        """parent_ref must match sprint_id."""
        kwargs = {**base_task_kwargs}
        kwargs["parent_ref"] = "different-sprint"

        with pytest.raises(ValueError, match="must match sprint_id"):
            TaskTicket(**kwargs)

    def test_sprint_id_cannot_be_empty(self, base_task_kwargs):
        """sprint_id cannot be empty."""
        kwargs = {**base_task_kwargs}
        kwargs["sprint_id"] = ""
        kwargs["parent_ref"] = ""

        with pytest.raises(ValueError, match="cannot be empty"):
            TaskTicket(**kwargs)

    def test_track_id_cannot_be_empty(self, base_task_kwargs):
        """track_id cannot be empty."""
        kwargs = {**base_task_kwargs}
        kwargs["track_id"] = "  "

        with pytest.raises(ValueError, match="cannot be empty"):
            TaskTicket(**kwargs)

    def test_roadmap_id_cannot_be_empty(self, base_task_kwargs):
        """roadmap_id cannot be empty."""
        kwargs = {**base_task_kwargs}
        kwargs["roadmap_id"] = ""

        with pytest.raises(ValueError, match="cannot be empty"):
            TaskTicket(**kwargs)

    def test_is_ultimate_child_always_true(self, base_task_kwargs):
        """Task is_ultimate_child is always True."""
        task = TaskTicket(**base_task_kwargs)

        assert task.is_ultimate_child is True

    def test_is_ultimate_parent_always_false(self, base_task_kwargs):
        """Task is_ultimate_parent is always False."""
        task = TaskTicket(**base_task_kwargs)

        assert task.is_ultimate_parent is False

    def test_is_intermediate_always_false(self, base_task_kwargs):
        """Task is_intermediate is always False."""
        task = TaskTicket(**base_task_kwargs)

        assert task.is_intermediate is False

    def test_is_child_always_true(self, base_task_kwargs):
        """Task is_child is always True."""
        task = TaskTicket(**base_task_kwargs)

        assert task.is_child is True

    def test_is_parent_always_false(self, base_task_kwargs):
        """Task is_parent is always False."""
        task = TaskTicket(**base_task_kwargs)

        assert task.is_parent is False

    def test_children_always_empty(self, base_task_kwargs):
        """Task children is always empty list."""
        task = TaskTicket(**base_task_kwargs)

        assert task.children == []


# =============================================================================
# NO CHILDREN CONSTRAINT TESTS
# =============================================================================


class TestNoChildrenConstraint:
    """Tests for leaf node constraint (no CompletableTarget criteria)."""

    def test_cannot_have_completable_target_criteria(self, base_task_kwargs):
        """TaskTicket cannot have CompletableTarget criteria."""
        criteria = [
            Criterion(
                id="child-task",
                name="Child task",
                description="Child task must be complete",
                target=CompletableTarget(
                    completable_id="child-task-1",
                    required_status=TicketStatus.COMPLETED,
                    current_status=TicketStatus.NOT_STARTED,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]

        with pytest.raises(ValueError, match="cannot have CompletableTarget"):
            TaskTicket(**base_task_kwargs, criteria=criteria)

    def test_can_have_file_exists_criteria(self, base_task_kwargs):
        """TaskTicket can have FileExistsTarget criteria."""
        criteria = [make_file_criterion("file-1", "src/api.py")]
        task = TaskTicket(**base_task_kwargs, criteria=criteria)

        assert len(task.criteria) == 1

    def test_can_have_test_passes_criteria(self, base_task_kwargs):
        """TaskTicket can have TestPassesTarget criteria."""
        criteria = [make_test_criterion("tests-1")]
        task = TaskTicket(**base_task_kwargs, criteria=criteria)

        assert len(task.criteria) == 1

    def test_can_have_threshold_criteria(self, base_task_kwargs):
        """TaskTicket can have ThresholdTarget criteria."""
        criteria = [
            Criterion(
                id="coverage",
                name="Test coverage",
                description="Coverage must be >= 85%",
                target=ThresholdTarget(
                    metric_name="coverage",
                    threshold=85.0,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        task = TaskTicket(**base_task_kwargs, criteria=criteria)

        assert len(task.criteria) == 1


# =============================================================================
# TASK TYPE TESTS
# =============================================================================


class TestTaskTypeClassification:
    """Tests for task type classification."""

    def test_default_task_type_is_development(self, base_task_kwargs):
        """Default task type is DEVELOPMENT."""
        task = TaskTicket(**base_task_kwargs)

        assert task.task_type_detail == TaskType.DEVELOPMENT
        assert task.is_development_task() is True

    def test_documentation_task(self, base_task_kwargs):
        """Documentation task classification."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.DOCUMENTATION,
        )

        assert task.is_documentation_task() is True
        assert task.is_development_task() is False

    def test_testing_task(self, base_task_kwargs):
        """Testing task classification."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.TESTING,
        )

        assert task.is_testing_task() is True

    def test_quality_gate_task(self, base_task_kwargs):
        """Quality gate task classification."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.GATE,
            gate_info=GateInfo(blocks_status=TicketStatus.COMPLETED),
        )

        assert task.is_quality_gate() is True


# =============================================================================
# GATE TASK TESTS
# =============================================================================


class TestGateTask:
    """Tests for gate task validation and behavior."""

    def test_gate_task_requires_gate_info(self, base_task_kwargs):
        """Gate tasks must have gate_info set."""
        with pytest.raises(ValueError, match="Gate tasks must have gate_info"):
            TaskTicket(
                **base_task_kwargs,
                task_type_detail=TaskType.GATE,
            )

    def test_non_gate_task_cannot_have_gate_info(self, base_task_kwargs):
        """Non-gate tasks cannot have gate_info."""
        with pytest.raises(ValueError, match="cannot have gate_info"):
            TaskTicket(
                **base_task_kwargs,
                task_type_detail=TaskType.DEVELOPMENT,
                gate_info=GateInfo(blocks_status=TicketStatus.COMPLETED),
            )

    def test_gate_info_has_passed(self, base_task_kwargs):
        """GateInfo.has_passed() based on score and threshold."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.GATE,
            gate_info=GateInfo(
                blocks_status=TicketStatus.COMPLETED,
                threshold=80.0,
                score=85.0,
            ),
        )

        assert task.gate_info.has_passed() is True
        assert task.has_passed_gate() is True

    def test_gate_info_not_passed_below_threshold(self, base_task_kwargs):
        """GateInfo fails when score below threshold."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.GATE,
            gate_info=GateInfo(
                blocks_status=TicketStatus.COMPLETED,
                threshold=80.0,
                score=75.0,
            ),
        )

        assert task.gate_info.has_passed() is False
        assert task.has_passed_gate() is False

    def test_gate_info_not_passed_without_score(self, base_task_kwargs):
        """GateInfo fails when score not set."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.GATE,
            gate_info=GateInfo(blocks_status=TicketStatus.COMPLETED),
        )

        assert task.gate_info.has_passed() is False

    def test_evaluate_gate(self, base_task_kwargs):
        """evaluate_gate updates gate score."""
        task = TaskTicket(
            **base_task_kwargs,
            task_type_detail=TaskType.GATE,
            gate_info=GateInfo(
                blocks_status=TicketStatus.COMPLETED,
                threshold=80.0,
            ),
        )

        task = task.evaluate_gate(90.0)

        assert task.gate_info.score == 90.0
        assert task.gate_info.evaluated_at is not None
        assert task.has_passed_gate() is True

    def test_evaluate_gate_fails_for_non_gate_task(self, base_task_kwargs):
        """evaluate_gate raises for non-gate tasks."""
        task = TaskTicket(**base_task_kwargs)

        with pytest.raises(ValueError, match="not a gate task"):
            task.evaluate_gate(90.0)

    def test_has_passed_gate_false_for_non_gate_task(self, base_task_kwargs):
        """has_passed_gate returns False for non-gate tasks."""
        task = TaskTicket(**base_task_kwargs)

        assert task.has_passed_gate() is False


# =============================================================================
# TOKEN ESTIMATION TESTS
# =============================================================================


class TestTokenEstimation:
    """Tests for token estimation and efficiency."""

    def test_estimated_tokens_required(self, base_task_kwargs):
        """estimated_tokens is required."""
        kwargs = {**base_task_kwargs}
        del kwargs["estimated_tokens"]

        with pytest.raises(ValueError):
            TaskTicket(**kwargs)

    def test_estimated_tokens_must_be_positive(self, base_task_kwargs):
        """estimated_tokens must be > 0."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 0

        with pytest.raises(ValueError):
            TaskTicket(**kwargs)

    def test_token_efficiency_under_budget(self, base_task_kwargs):
        """Token efficiency < 1.0 means under budget."""
        task = TaskTicket(
            **base_task_kwargs,
            actual_tokens=800,
        )

        assert task.token_efficiency == 0.8

    def test_token_efficiency_over_budget(self, base_task_kwargs):
        """Token efficiency > 1.0 means over budget."""
        task = TaskTicket(
            **base_task_kwargs,
            actual_tokens=1200,
        )

        assert task.token_efficiency == 1.2

    def test_token_efficiency_none_without_actual(self, base_task_kwargs):
        """Token efficiency is None if actual_tokens not set."""
        task = TaskTicket(**base_task_kwargs)

        assert task.token_efficiency is None

    def test_record_tokens(self, base_task_kwargs):
        """record_tokens sets actual_tokens."""
        task = TaskTicket(**base_task_kwargs)
        task = task.record_tokens(850)

        assert task.actual_tokens == 850
        assert task.token_efficiency == 0.85


# =============================================================================
# SIZE CATEGORY TESTS
# =============================================================================


class TestSizeCategory:
    """Tests for size category computation."""

    def test_size_category_tiny(self, base_task_kwargs):
        """Size category TINY for < 500 tokens."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 300
        task = TaskTicket(**kwargs)

        assert task.size_category == SizeCategory.TINY

    def test_size_category_small(self, base_task_kwargs):
        """Size category SMALL for 500-1000 tokens."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 750
        task = TaskTicket(**kwargs)

        assert task.size_category == SizeCategory.SMALL

    def test_size_category_medium(self, base_task_kwargs):
        """Size category MEDIUM for 1000-2500 tokens."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 1500
        task = TaskTicket(**kwargs)

        assert task.size_category == SizeCategory.MEDIUM

    def test_size_category_large(self, base_task_kwargs):
        """Size category LARGE for 2500-5000 tokens."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 3500
        task = TaskTicket(**kwargs)

        assert task.size_category == SizeCategory.LARGE

    def test_size_category_huge(self, base_task_kwargs):
        """Size category HUGE for > 5000 tokens."""
        kwargs = {**base_task_kwargs}
        kwargs["estimated_tokens"] = 6000
        task = TaskTicket(**kwargs)

        assert task.size_category == SizeCategory.HUGE


# =============================================================================
# AUDIT TESTS
# =============================================================================


class TestAuditResults:
    """Tests for audit results management."""

    def test_record_audit(self, base_task_kwargs):
        """record_audit creates AuditResults."""
        task = TaskTicket(**base_task_kwargs)
        task = task.record_audit(
            audit_type="code_quality",
            issues_found=5,
            recommendations=["Add tests", "Fix naming"],
        )

        assert task.audit_results is not None
        assert task.audit_results.audit_type == "code_quality"
        assert task.audit_results.issues_found == 5
        assert task.audit_results.issues_fixed == 0
        assert len(task.audit_results.recommendations) == 2

    def test_fix_audit_issue(self, base_task_kwargs):
        """fix_audit_issue increments issues_fixed."""
        task = TaskTicket(**base_task_kwargs)
        task = task.record_audit("security", issues_found=3)
        task = task.fix_audit_issue()
        task = task.fix_audit_issue()

        assert task.audit_results.issues_fixed == 2
        assert task.audit_results.issues_remaining == 1

    def test_fix_audit_issue_without_audit_fails(self, base_task_kwargs):
        """fix_audit_issue raises without audit results."""
        task = TaskTicket(**base_task_kwargs)

        with pytest.raises(ValueError, match="no audit results"):
            task.fix_audit_issue()

    def test_audit_is_resolved(self, base_task_kwargs):
        """is_resolved when all issues fixed."""
        task = TaskTicket(**base_task_kwargs)
        task = task.record_audit("code_quality", issues_found=2)
        task = task.fix_audit_issue()
        task = task.fix_audit_issue()

        assert task.audit_results.is_resolved is True


# =============================================================================
# GATE INFO CLASS TESTS
# =============================================================================


class TestGateInfoClass:
    """Tests for GateInfo class."""

    def test_create_gate_info(self):
        """GateInfo can be created with required fields."""
        gate = GateInfo(blocks_status=TicketStatus.COMPLETED)

        assert gate.blocks_status == TicketStatus.COMPLETED
        assert gate.threshold == 100.0
        assert gate.is_blocking is True
        assert gate.score is None

    def test_gate_evaluate(self):
        """evaluate sets score and timestamp."""
        gate = GateInfo(blocks_status=TicketStatus.COMPLETED, threshold=80.0)
        gate = gate.evaluate(85.0)

        assert gate.score == 85.0
        assert gate.evaluated_at is not None

    def test_gate_has_passed(self):
        """has_passed returns True when score >= threshold."""
        gate = GateInfo(
            blocks_status=TicketStatus.COMPLETED,
            threshold=80.0,
            score=80.0,
        )

        assert gate.has_passed() is True


# =============================================================================
# AUDIT RESULTS CLASS TESTS
# =============================================================================


class TestAuditResultsClass:
    """Tests for AuditResults class."""

    def test_create_audit_results(self):
        """AuditResults can be created with required fields."""
        audit = AuditResults(audit_type="security")

        assert audit.audit_type == "security"
        assert audit.issues_found == 0
        assert audit.issues_fixed == 0
        assert audit.audited_at is not None

    def test_issues_remaining(self):
        """issues_remaining computed correctly."""
        audit = AuditResults(
            audit_type="code_quality",
            issues_found=5,
            issues_fixed=3,
        )

        assert audit.issues_remaining == 2

    def test_is_resolved(self):
        """is_resolved when no issues remaining."""
        audit = AuditResults(
            audit_type="code_quality",
            issues_found=2,
            issues_fixed=2,
        )

        assert audit.is_resolved is True

    def test_not_resolved_with_issues(self):
        """is_resolved False when issues remain."""
        audit = AuditResults(
            audit_type="code_quality",
            issues_found=3,
            issues_fixed=1,
        )

        assert audit.is_resolved is False


# =============================================================================
# SIZE CATEGORY CLASS TESTS
# =============================================================================


class TestSizeCategoryClass:
    """Tests for SizeCategory class."""

    def test_from_tokens_boundary_values(self):
        """from_tokens handles boundary values correctly."""
        assert SizeCategory.from_tokens(499) == SizeCategory.TINY
        assert SizeCategory.from_tokens(500) == SizeCategory.SMALL
        assert SizeCategory.from_tokens(999) == SizeCategory.SMALL
        assert SizeCategory.from_tokens(1000) == SizeCategory.MEDIUM
        assert SizeCategory.from_tokens(2499) == SizeCategory.MEDIUM
        assert SizeCategory.from_tokens(2500) == SizeCategory.LARGE
        assert SizeCategory.from_tokens(4999) == SizeCategory.LARGE
        assert SizeCategory.from_tokens(5000) == SizeCategory.HUGE
