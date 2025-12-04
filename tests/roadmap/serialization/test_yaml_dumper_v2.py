"""
Tests for v2 YAML dumper functions.

These tests verify the Pydantic ticket model serialization to YAML format.
"""

import pytest
from datetime import datetime, timezone

from vibey.roadmap.serialization.yaml_dumper import (
    _dump_git_commit,
    _dump_criterion,
    dump_task_ticket,
    dump_sprint_ticket,
    dump_track_ticket,
    dump_roadmap_ticket,
)
from vibey.roadmap.models.ticket.ticket import GitCommit, Ticket
from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.domain import (
    TaskTicket,
    SprintTicket,
    TrackTicket,
    RoadmapTicket,
)
from vibey.roadmap.models.ticket.enums import (
    TicketStatus,
    TicketType,
    TaskType,
    Priority,
    Complexity,
    CriterionTargetType,
    ThresholdComparison,
    DeliverableType,
)
from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
    ThresholdTarget,
)


class TestDumpGitCommit:
    """Tests for _dump_git_commit helper function."""

    def test_dump_basic_commit(self):
        """Test dumping a basic git commit."""
        commit = GitCommit(
            sha="abc123",
            message="Initial commit",
            date=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            author="test@example.com",
        )

        result = _dump_git_commit(commit)

        assert result['sha'] == "abc123"
        assert result['message'] == "Initial commit"
        assert result['author'] == "test@example.com"
        assert "2025-01-01" in result['date']
        assert result['platform'] is None
        assert result['files_added'] == []
        assert result['files_modified'] == []
        assert result['files_deleted'] == []

    def test_dump_commit_with_files(self):
        """Test dumping a commit with file changes."""
        commit = GitCommit(
            sha="def456",
            message="Add feature",
            date=datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            author="dev@example.com",
            platform="claude-code",
            files_added=["src/new_file.py", "tests/test_new.py"],
            files_modified=["src/existing.py"],
        )

        result = _dump_git_commit(commit)

        assert result['platform'] == "claude-code"
        assert result['files_added'] == ["src/new_file.py", "tests/test_new.py"]
        assert result['files_modified'] == ["src/existing.py"]
        assert result['files_deleted'] == []

    def test_dump_commit_sorts_lists(self):
        """Test that file lists are sorted for deterministic output."""
        commit = GitCommit(
            sha="xyz789",
            message="Refactor",
            date=datetime(2025, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            author="dev@example.com",
            files_modified=["z_file.py", "a_file.py", "m_file.py"],
        )

        result = _dump_git_commit(commit)

        assert result['files_modified'] == ["a_file.py", "m_file.py", "z_file.py"]


class TestDumpCriterion:
    """Tests for _dump_criterion helper function."""

    def test_dump_completable_target_criterion(self):
        """Test dumping a criterion with CompletableTarget."""
        criterion = Criterion(
            id="dep-task-001",
            description="Task 001 must complete",
            blocks_transition_to=TicketStatus.IN_PROGRESS,
            target=CompletableTarget(
                completable_id="task-001",
                required_status=TicketStatus.COMPLETED,
            ),
            required=True,
        )

        result = _dump_criterion(criterion)

        assert result['id'] == "dep-task-001"
        assert result['description'] == "Task 001 must complete"
        assert result['blocks_transition_to'] == "in_progress"
        assert result['target']['type'] == "completable"
        assert result['target']['completable_id'] == "task-001"
        assert result['target']['required_status'] == "completed"
        assert result['required'] is True

    def test_dump_file_exists_target_criterion(self):
        """Test dumping a criterion with FileExistsTarget."""
        criterion = Criterion(
            id="deliverable-001",
            description="README must exist",
            blocks_transition_to=TicketStatus.COMPLETED,
            target=FileExistsTarget(
                paths=["README.md"],
                deliverable_type=DeliverableType.DOCUMENTATION,
            ),
            required=True,
        )

        result = _dump_criterion(criterion)

        assert result['target']['type'] == "file_exists"
        assert result['target']['paths'] == ["README.md"]
        assert result['target']['deliverable_type'] == "documentation"

    def test_dump_threshold_target_criterion(self):
        """Test dumping a criterion with ThresholdTarget."""
        criterion = Criterion(
            id="quality-gate-001",
            description="Test coverage must be >= 80%",
            blocks_transition_to=TicketStatus.COMPLETED,
            target=ThresholdTarget(
                metric_name="test_coverage",
                threshold=80.0,
                comparison=ThresholdComparison.GTE,
                current_value=85.0,
            ),
            required=True,
        )

        result = _dump_criterion(criterion)

        assert result['target']['type'] == "threshold"
        assert result['target']['metric_name'] == "test_coverage"
        assert result['target']['comparison'] == "gte"
        assert result['target']['threshold'] == 80.0
        assert result['target']['current_value'] == 85.0


class TestDumpTaskTicket:
    """Tests for dump_task_ticket function."""

    def test_dump_minimal_task(self):
        """Test dumping a minimal task ticket."""
        task = TaskTicket(
            id="task-001",
            name="Test Task",
            parent_ref="sprint-001",
            sprint_id="sprint-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            estimated_tokens=100,
        )

        result = dump_task_ticket(task)

        assert 'task' in result
        task_data = result['task']
        assert task_data['id'] == "task-001"
        assert task_data['name'] == "Test Task"
        assert task_data['format_version'] == "v2"
        assert task_data['ticket_type'] == "task"
        assert task_data['status'] == "not_started"
        assert task_data['criteria'] == []
        assert task_data['commits_local'] == []

    def test_dump_task_with_commits(self):
        """Test dumping a task with commits uses commits_local key."""
        task = TaskTicket(
            id="task-002",
            name="Task with commits",
            parent_ref="sprint-001",
            sprint_id="sprint-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            estimated_tokens=200,
            commits=[
                GitCommit(
                    sha="abc123",
                    message="Implement feature",
                    date=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                    author="dev@example.com",
                )
            ],
        )

        result = dump_task_ticket(task)

        # Should use commits_local key (not commits)
        assert 'commits_local' in result['task']
        assert len(result['task']['commits_local']) == 1
        assert result['task']['commits_local'][0]['sha'] == "abc123"

    def test_dump_task_with_criteria(self):
        """Test dumping a task with criteria."""
        task = TaskTicket(
            id="task-003",
            name="Task with criteria",
            parent_ref="sprint-001",
            sprint_id="sprint-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            estimated_tokens=300,
            criteria=[
                Criterion(
                    id="deliverable-001",
                    description="README must exist",
                    blocks_transition_to=TicketStatus.COMPLETED,
                    target=FileExistsTarget(
                        paths=["README.md"],
                        deliverable_type=DeliverableType.DOCUMENTATION,
                    ),
                )
            ],
        )

        result = dump_task_ticket(task)

        assert len(result['task']['criteria']) == 1
        assert result['task']['criteria'][0]['id'] == "deliverable-001"

    def test_dump_task_with_task_specific_fields(self):
        """Test dumping a task with task-specific fields."""
        task = TaskTicket(
            id="task-004",
            name="Complex task",
            parent_ref="sprint-001",
            sprint_id="sprint-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            task_type_detail=TaskType.DEVELOPMENT,
            estimated_tokens=1000,
            actual_tokens=850,
            complexity=Complexity.HIGH,
            phase_label="implementation",
        )

        result = dump_task_ticket(task)

        task_data = result['task']
        assert task_data['task_type_detail'] == "development"
        assert task_data['estimated_tokens'] == 1000
        assert task_data['actual_tokens'] == 850
        assert task_data['complexity'] == "high"
        assert task_data['phase_label'] == "implementation"


class TestDumpSprintTicket:
    """Tests for dump_sprint_ticket function."""

    def test_dump_minimal_sprint(self):
        """Test dumping a minimal sprint ticket."""
        sprint = SprintTicket(
            id="sprint-001",
            name="Sprint 1",
            parent_ref="track-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
        )

        result = dump_sprint_ticket(sprint)

        assert 'sprint' in result
        sprint_data = result['sprint']
        assert sprint_data['id'] == "sprint-001"
        assert sprint_data['name'] == "Sprint 1"
        assert sprint_data['format_version'] == "v2"
        assert sprint_data['ticket_type'] == "sprint"

    def test_dump_sprint_with_sprint_specific_fields(self):
        """Test dumping a sprint with sprint-specific fields."""
        sprint = SprintTicket(
            id="sprint-002",
            name="Sprint 2",
            parent_ref="track-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            plan_file="docs/sprint-2-plan.md",
            goal="Complete feature X",
            success_criteria_text=["All tests pass", "Documentation updated"],
        )

        result = dump_sprint_ticket(sprint)

        sprint_data = result['sprint']
        assert sprint_data['plan_file'] == "docs/sprint-2-plan.md"
        assert sprint_data['goal'] == "Complete feature X"
        assert sprint_data['success_criteria'] == ["All tests pass", "Documentation updated"]


class TestDumpTrackTicket:
    """Tests for dump_track_ticket function."""

    def test_dump_minimal_track(self):
        """Test dumping a minimal track ticket."""
        track = TrackTicket(
            id="track-001",
            name="Feature Track",
            parent_ref="roadmap-001",
            roadmap_id="roadmap-001",
        )

        result = dump_track_ticket(track)

        assert 'track' in result
        track_data = result['track']
        assert track_data['id'] == "track-001"
        assert track_data['name'] == "Feature Track"
        assert track_data['format_version'] == "v2"
        assert track_data['ticket_type'] == "track"

    def test_dump_track_with_strategic_value(self):
        """Test dumping a track with strategic value."""
        track = TrackTicket(
            id="track-002",
            name="Important Track",
            parent_ref="roadmap-001",
            roadmap_id="roadmap-001",
            strategic_value=["Improves user experience", "Reduces latency"],
        )

        result = dump_track_ticket(track)

        assert result['track']['strategic_value'] == [
            "Improves user experience",
            "Reduces latency",
        ]


class TestDumpRoadmapTicket:
    """Tests for dump_roadmap_ticket function."""

    def test_dump_minimal_roadmap(self):
        """Test dumping a minimal roadmap ticket."""
        roadmap = RoadmapTicket(
            id="roadmap-001",
            name="Test Roadmap",
        )

        result = dump_roadmap_ticket(roadmap)

        assert 'roadmap' in result
        roadmap_data = result['roadmap']
        assert roadmap_data['id'] == "roadmap-001"
        assert roadmap_data['name'] == "Test Roadmap"
        assert roadmap_data['format_version'] == "v2"
        assert roadmap_data['ticket_type'] == "roadmap"
        assert roadmap_data['parent_ref'] is None  # Roadmap has no parent

    def test_dump_roadmap_with_version(self):
        """Test dumping a roadmap with version info."""
        roadmap = RoadmapTicket(
            id="roadmap-002",
            name="Versioned Roadmap",
            version="1.2.3",
        )

        result = dump_roadmap_ticket(roadmap)

        assert result['roadmap']['version'] == "1.2.3"


class TestDeterministicOutput:
    """Tests for deterministic output ordering."""

    def test_assigned_agents_sorted(self):
        """Test that assigned_agents are sorted in output."""
        task = TaskTicket(
            id="task-001",
            name="Task",
            parent_ref="sprint-001",
            sprint_id="sprint-001",
            track_id="track-001",
            roadmap_id="roadmap-001",
            estimated_tokens=100,
            assigned_agents=["zebra", "alpha", "mike"],
        )

        result = dump_task_ticket(task)

        assert result['task']['assigned_agents'] == ["alpha", "mike", "zebra"]

    def test_commits_files_sorted(self):
        """Test that commit file lists are sorted."""
        commit = GitCommit(
            sha="abc",
            message="test",
            date=datetime.now(timezone.utc),
            author="test",
            files_added=["z.py", "a.py"],
        )

        result = _dump_git_commit(commit)

        assert result['files_added'] == ["a.py", "z.py"]
