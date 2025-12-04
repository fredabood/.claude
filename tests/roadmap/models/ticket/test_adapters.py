"""
Tests for model adapters.

Tests cover:
- Status mapping functions
- Criterion generation utilities
- Criterion extraction utilities
- ModelAdapter class methods
"""

import pytest
from datetime import datetime, timezone

from vibey.roadmap.models.ticket import (
    # Enums
    TicketStatus,
    Priority,
    TaskType,
    # Criterion types
    Criterion,
    CompletableTarget,
    FileExistsTarget,
    # Adapters
    map_status_to_ticket_status,
    map_ticket_status_to_status,
    map_priority,
    map_task_type,
    children_to_criteria,
    dependencies_to_criteria,
    deliverables_to_criteria,
    extract_child_ids,
    extract_dependency_ids,
    extract_deliverable_paths,
    ModelAdapter,
)


# =============================================================================
# STATUS MAPPING TESTS
# =============================================================================


class TestStatusMapping:
    """Tests for status mapping functions."""

    def test_map_not_started(self):
        """Test mapping not_started status."""
        assert map_status_to_ticket_status("not_started") == TicketStatus.NOT_STARTED

    def test_map_in_progress(self):
        """Test mapping in_progress status."""
        assert map_status_to_ticket_status("in_progress") == TicketStatus.IN_PROGRESS

    def test_map_completed(self):
        """Test mapping completed status."""
        assert map_status_to_ticket_status("completed") == TicketStatus.COMPLETED

    def test_map_production_ready(self):
        """Test mapping production_ready status."""
        assert map_status_to_ticket_status("production_ready") == TicketStatus.PRODUCTION_READY

    def test_map_blocked_to_not_started(self):
        """Test mapping blocked to not_started."""
        assert map_status_to_ticket_status("blocked") == TicketStatus.NOT_STARTED

    def test_map_unknown_to_not_started(self):
        """Test unknown status maps to not_started."""
        assert map_status_to_ticket_status("unknown") == TicketStatus.NOT_STARTED

    def test_reverse_map_not_started(self):
        """Test reverse mapping not_started."""
        assert map_ticket_status_to_status(TicketStatus.NOT_STARTED) == "not_started"

    def test_reverse_map_completed(self):
        """Test reverse mapping completed."""
        assert map_ticket_status_to_status(TicketStatus.COMPLETED) == "completed"


class TestPriorityMapping:
    """Tests for priority mapping."""

    def test_map_critical(self):
        """Test mapping critical priority."""
        assert map_priority("critical") == Priority.CRITICAL

    def test_map_high(self):
        """Test mapping high priority."""
        assert map_priority("high") == Priority.HIGH

    def test_map_medium(self):
        """Test mapping medium priority."""
        assert map_priority("medium") == Priority.MEDIUM

    def test_map_low(self):
        """Test mapping low priority."""
        assert map_priority("low") == Priority.LOW

    def test_map_unknown_to_medium(self):
        """Test unknown priority maps to medium."""
        assert map_priority("unknown") == Priority.MEDIUM


class TestTaskTypeMapping:
    """Tests for task type mapping."""

    def test_map_development(self):
        """Test mapping development type."""
        assert map_task_type("development") == TaskType.DEVELOPMENT

    def test_map_documentation(self):
        """Test mapping documentation type."""
        assert map_task_type("documentation") == TaskType.DOCUMENTATION

    def test_map_testing(self):
        """Test mapping testing type."""
        assert map_task_type("testing") == TaskType.TESTING

    def test_map_unknown_to_development(self):
        """Test unknown type maps to development."""
        assert map_task_type("unknown") == TaskType.DEVELOPMENT


# =============================================================================
# CRITERION GENERATION TESTS
# =============================================================================


class TestChildrenToCriteria:
    """Tests for children_to_criteria function."""

    def test_empty_list(self):
        """Test empty children list."""
        criteria = children_to_criteria([])
        assert criteria == []

    def test_single_child(self):
        """Test single child conversion."""
        criteria = children_to_criteria(["task-001"])
        assert len(criteria) == 1
        assert isinstance(criteria[0], Criterion)
        assert isinstance(criteria[0].target, CompletableTarget)
        assert criteria[0].target.completable_id == "task-001"
        assert criteria[0].blocks_transition_to == TicketStatus.COMPLETED

    def test_multiple_children(self):
        """Test multiple children conversion."""
        criteria = children_to_criteria(["task-001", "task-002", "task-003"])
        assert len(criteria) == 3
        ids = [c.target.completable_id for c in criteria]
        assert set(ids) == {"task-001", "task-002", "task-003"}

    def test_custom_description_template(self):
        """Test custom description template."""
        criteria = children_to_criteria(["task-001"], "Sprint {} finished")
        assert "Sprint task-001 finished" in criteria[0].description


class TestDependenciesToCriteria:
    """Tests for dependencies_to_criteria function."""

    def test_empty_list(self):
        """Test empty dependencies list."""
        criteria = dependencies_to_criteria([])
        assert criteria == []

    def test_single_dependency(self):
        """Test single dependency conversion."""
        criteria = dependencies_to_criteria(["other-task"])
        assert len(criteria) == 1
        assert criteria[0].blocks_transition_to == TicketStatus.IN_PROGRESS

    def test_multiple_dependencies(self):
        """Test multiple dependencies conversion."""
        criteria = dependencies_to_criteria(["dep-1", "dep-2"])
        assert len(criteria) == 2
        for c in criteria:
            assert c.blocks_transition_to == TicketStatus.IN_PROGRESS


class TestDeliverablesToCriteria:
    """Tests for deliverables_to_criteria function."""

    def test_empty_list(self):
        """Test empty deliverables list."""
        criteria = deliverables_to_criteria([])
        assert criteria == []

    def test_single_path(self):
        """Test single path conversion."""
        criteria = deliverables_to_criteria(["src/main.py"])
        assert len(criteria) == 1
        assert isinstance(criteria[0].target, FileExistsTarget)
        assert "src/main.py" in criteria[0].target.paths

    def test_multiple_paths(self):
        """Test multiple paths conversion."""
        criteria = deliverables_to_criteria(["src/a.py", "src/b.py"])
        assert len(criteria) == 2


# =============================================================================
# CRITERION EXTRACTION TESTS
# =============================================================================


class TestExtractChildIds:
    """Tests for extract_child_ids function."""

    def test_empty_criteria(self):
        """Test extraction from empty criteria."""
        ids = extract_child_ids([])
        assert ids == []

    def test_extract_completion_blocking(self):
        """Test extraction of completion-blocking children."""
        criteria = [
            Criterion(
                id="c1",
                description="Child",
                target=CompletableTarget(
                    completable_id="child-1",
                    required_status=TicketStatus.COMPLETED,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
        ]
        ids = extract_child_ids(criteria)
        assert ids == ["child-1"]

    def test_ignores_dependency_criteria(self):
        """Test that dependency criteria are ignored."""
        criteria = [
            Criterion(
                id="c1",
                description="Dependency",
                target=CompletableTarget(
                    completable_id="dep-1",
                    required_status=TicketStatus.COMPLETED,
                ),
                blocks_transition_to=TicketStatus.IN_PROGRESS,  # Dependency
            ),
        ]
        ids = extract_child_ids(criteria)
        assert ids == []


class TestExtractDependencyIds:
    """Tests for extract_dependency_ids function."""

    def test_empty_criteria(self):
        """Test extraction from empty criteria."""
        ids = extract_dependency_ids([])
        assert ids == []

    def test_extract_start_blocking(self):
        """Test extraction of start-blocking dependencies."""
        criteria = [
            Criterion(
                id="c1",
                description="Dependency",
                target=CompletableTarget(
                    completable_id="dep-1",
                    required_status=TicketStatus.COMPLETED,
                ),
                blocks_transition_to=TicketStatus.IN_PROGRESS,
            ),
        ]
        ids = extract_dependency_ids(criteria)
        assert ids == ["dep-1"]

    def test_ignores_child_criteria(self):
        """Test that child criteria are ignored."""
        criteria = [
            Criterion(
                id="c1",
                description="Child",
                target=CompletableTarget(
                    completable_id="child-1",
                    required_status=TicketStatus.COMPLETED,
                ),
                blocks_transition_to=TicketStatus.COMPLETED,  # Child
            ),
        ]
        ids = extract_dependency_ids(criteria)
        assert ids == []


class TestExtractDeliverablePaths:
    """Tests for extract_deliverable_paths function."""

    def test_empty_criteria(self):
        """Test extraction from empty criteria."""
        paths = extract_deliverable_paths([])
        assert paths == []

    def test_extract_file_paths(self):
        """Test extraction of file paths."""
        criteria = [
            Criterion(
                id="c1",
                description="File",
                target=FileExistsTarget(paths=["src/main.py", "src/utils.py"]),
            ),
        ]
        paths = extract_deliverable_paths(criteria)
        assert set(paths) == {"src/main.py", "src/utils.py"}


# =============================================================================
# MODEL ADAPTER TESTS
# =============================================================================


class TestModelAdapterTask:
    """Tests for ModelAdapter task conversion."""

    def test_task_to_ticket_basic(self):
        """Test basic task to ticket conversion."""
        # Create a mock task object
        class MockTask:
            id = "task-001"
            title = "Test Task"
            description = "A test task"
            status = type("Status", (), {"value": "not_started"})()
            priority = type("Priority", (), {"value": "high"})()
            task_type = type("TaskType", (), {"value": "development"})()
            sprint_id = "sprint-001"
            track_id = "track-001"
            roadmap_id = "roadmap-001"
            estimated_tokens = 1500
            created = datetime.now(timezone.utc)
            started = None
            completed = None
            deliverables = []
            depends_on = []

        task = MockTask()
        result = ModelAdapter.task_to_ticket(task)

        assert result["id"] == "task-001"
        assert result["name"] == "Test Task"
        assert result["status"] == TicketStatus.NOT_STARTED
        assert result["priority"] == Priority.HIGH
        assert result["sprint_id"] == "sprint-001"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestAdapterRoundTrip:
    """Tests for round-trip conversion."""

    def test_children_round_trip(self):
        """Test children list -> criteria -> children list."""
        original = ["task-001", "task-002", "task-003"]
        criteria = children_to_criteria(original)
        extracted = extract_child_ids(criteria)
        assert set(extracted) == set(original)

    def test_dependencies_round_trip(self):
        """Test dependencies list -> criteria -> dependencies list."""
        original = ["dep-001", "dep-002"]
        criteria = dependencies_to_criteria(original)
        extracted = extract_dependency_ids(criteria)
        assert set(extracted) == set(original)
