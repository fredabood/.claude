"""
Integration tests for standards CLI commands.

Tests the complete standards workflow:
- Adding standards via CLI
- Checking standards status
- Enforcement during task/sprint completion
- Override mechanism
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from vibey.roadmap.models import (
    Standard,
    StandardType,
    EnforcementMode,
    Roadmap,
    Track,
    Sprint,
    Task,
    TaskType,
    TaskStatus,
    Status,
    Priority,
    Complexity,
    VersionStrategy,
    VersionBumpTrigger,
    Progress,
    TrackSummary,
    Metadata,
    TrackProgress,
    SprintSummary,
    TrackMetadata,
    SprintProgress,
    TaskSummary,
    SprintMetadata,
    TaskMetadata,
    GitCommit,
)
from vibey.roadmap.serialization import (
    save_roadmap,
    save_track,
    save_sprint,
    save_tasks,
)
from vibey.operations.roadmap import (
    complete_task,
    complete_sprint,
    enforce_standards,
)


@pytest.fixture
def test_roadmap_with_task(tmp_path):
    """
    Create a test roadmap with a task ready for completion.

    Structure:
    - Roadmap with 1 BLOCKING standard (test-coverage)
    - Track (backend)
    - Sprint (backend-1)
    - Task (backend-1-task-001) with insufficient commits
    """
    vibey_dir = tmp_path / ".vibey"
    vibey_dir.mkdir(parents=True)
    roadmap_dir = vibey_dir / "roadmap"
    roadmap_dir.mkdir(parents=True)

    now = datetime.now(timezone.utc)

    # Create roadmap with blocking standard
    roadmap_standard = Standard(
        id="test-coverage",
        name="Test Coverage",
        description="80% test coverage required",
        type=StandardType.TEST_RUN,
        enforcement=EnforcementMode.BLOCKING,
        validation={"command": "pytest --cov", "threshold": 80},
        created=now,
    )

    roadmap = Roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        version_strategy=VersionStrategy(
            major_on=VersionBumpTrigger.ROADMAP_MILESTONE,
            minor_on=VersionBumpTrigger.TRACK_COMPLETION,
            patch_on=VersionBumpTrigger.SPRINT_PRODUCTION_READY,
        ),
        status=Status.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,
        progress=Progress(
            tracks_total=1,
            tracks_completed=0,
            sprints_total=1,
            sprints_completed=0,
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[
            TrackSummary(
                id="backend",
                name="Backend Track",
                status=Status.IN_PROGRESS,
                priority=Priority.HIGH,
            )
        ],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.3.0",
            schema_version="2.1",
            last_updated=now,
        ),
        standards=[roadmap_standard],
    )

    save_roadmap(roadmap, roadmap_dir / "roadmap.yaml")

    # Create track
    track = Track(
        id="backend",
        name="Backend Track",
        roadmap_id="test-roadmap",
        status=Status.IN_PROGRESS,
        blocked=False,
        priority=Priority.HIGH,
        created=now,
        started=now,
        progress=TrackProgress(
            sprints_total=1,
            sprints_completed=0,
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        sprints=[
            SprintSummary(
                id="backend-1",
                name="Sprint 1",
                status=Status.IN_PROGRESS,
            )
        ],
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        quality_gates=[],
        assigned_agents=[],
        metadata=TrackMetadata(
            created_by="test",
            last_updated=now,
        ),
        standards=[],
    )

    track_dir = roadmap_dir / "backend"
    track_dir.mkdir()
    save_track(track, track_dir / "track.yaml")

    # Create sprint
    sprint = Sprint(
        id="backend-1",
        name="Sprint 1",
        track_id="backend",
        roadmap_id="test-roadmap",
        status=Status.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,
        progress=SprintProgress(
            development_tasks_total=1,
            development_tasks_completed=0,
            completion_gate_tasks_total=0,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=0,
            production_gate_tasks_completed=0,
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        tasks=[
            TaskSummary(
                id="backend-1-task-001",
                title="Test Task",
                task_type=TaskType.DEVELOPMENT,
                status=TaskStatus.IN_PROGRESS,
            )
        ],
        development_gates=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=SprintMetadata(
            last_updated=now,
        ),
        standards=[],
    )

    sprint_dir = track_dir / "backend-1"
    sprint_dir.mkdir()
    save_sprint(sprint, sprint_dir / "sprint.yaml")

    # Create task with no commits (will fail commit standard)
    task = Task(
        id="backend-1-task-001",
        sprint_id="backend-1",
        track_id="backend",
        roadmap_id="test-roadmap",
        task_type=TaskType.DEVELOPMENT,
        title="Test Task",
        description="Test description",
        status=TaskStatus.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,
        assigned_agent="test-agent",
        priority=Priority.MEDIUM,
        estimated_tokens=1000,
        complexity=Complexity.MEDIUM,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=TaskMetadata(last_updated=now),
        deliverables=[],
        commits=[],  # No commits - will fail if we add commit standard
    )

    # Save tasks in hierarchical format (sprint_dir is the tasks directory)
    save_tasks([task], sprint_dir)

    return tmp_path


class TestStandardsEnforcement:
    """Test standards enforcement during completion."""

    def test_task_completion_blocked_by_standard(self, test_roadmap_with_task):
        """Task completion should be blocked if BLOCKING standard fails."""
        # The test-coverage standard will fail because we can't run pytest
        result = complete_task(
            test_roadmap_with_task,
            "backend-1-task-001",
            completed_by="test"
        )

        # Should fail due to standard enforcement
        # Note: This will actually error because pytest can't run,
        # but in production the validator would execute and fail gracefully
        assert result == 1  # Error exit code

    def test_task_completion_with_override(self, test_roadmap_with_task):
        """Task completion should succeed if standard is overridden."""
        from vibey.roadmap.serialization import load_roadmap, save_roadmap

        # Add override for the test-coverage standard
        roadmap_path = test_roadmap_with_task / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard("test-coverage")
        standard.add_override(
            target_id="backend-1-task-001",
            reason="Emergency hotfix - testing not required",
            overridden_by="admin"
        )

        save_roadmap(roadmap, roadmap_path)

        # Now task should complete successfully
        result = complete_task(
            test_roadmap_with_task,
            "backend-1-task-001",
            completed_by="test"
        )

        assert result == 0  # Success


class TestCheckStandardsCommand:
    """Test check-standards command."""

    def test_check_standards_shows_all_standards(self, test_roadmap_with_task):
        """check-standards should show all applicable standards."""
        from vibey.cli.roadmap_commands.check_standards import handle_check_standards
        from argparse import Namespace

        args = Namespace(
            id="backend-1-task-001",
            dir=str(test_roadmap_with_task),
            verbose=True
        )

        # This will print results - we're mainly checking it doesn't crash
        result = handle_check_standards(args)

        # Should return 1 because standard will fail (can't run pytest)
        assert result == 1

    def test_check_standards_for_sprint(self, test_roadmap_with_task):
        """check-standards should work for sprints."""
        from vibey.cli.roadmap_commands.check_standards import handle_check_standards
        from argparse import Namespace

        args = Namespace(
            id="backend-1",
            dir=str(test_roadmap_with_task),
            verbose=False
        )

        result = handle_check_standards(args)

        # Sprint has same standard as task, should also fail
        assert result == 1


class TestOverrideStandardCommand:
    """Test override-standard command."""

    def test_override_standard_adds_override(self, test_roadmap_with_task):
        """override-standard should add override to standard."""
        from vibey.cli.roadmap_commands.override_standard import handle_override_standard
        from vibey.roadmap.serialization import load_roadmap
        from argparse import Namespace

        args = Namespace(
            standard_id="test-coverage",
            item_id="backend-1-task-001",
            reason="Emergency hotfix",
            overridden_by="admin",
            dir=str(test_roadmap_with_task)
        )

        result = handle_override_standard(args)

        assert result == 0  # Success

        # Verify override was added
        roadmap_path = test_roadmap_with_task / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard("test-coverage")
        assert standard is not None
        assert standard.has_override_for("backend-1-task-001")

        override = standard.get_override_for("backend-1-task-001")
        assert override.reason == "Emergency hotfix"
        assert override.overridden_by == "admin"

    def test_override_nonexistent_standard_fails(self, test_roadmap_with_task):
        """override-standard should fail for nonexistent standard."""
        from vibey.cli.roadmap_commands.override_standard import handle_override_standard
        from argparse import Namespace

        args = Namespace(
            standard_id="nonexistent-standard",
            item_id="backend-1-task-001",
            reason="Test",
            overridden_by="test",
            dir=str(test_roadmap_with_task)
        )

        result = handle_override_standard(args)

        assert result == 1  # Failure


class TestAddStandardCommand:
    """Test add-standard command."""

    def test_add_standard_to_roadmap(self, test_roadmap_with_task):
        """add-standard should add standard to roadmap."""
        from vibey.cli.roadmap_commands.add_standard import handle_add_standard
        from vibey.roadmap.serialization import load_roadmap
        from argparse import Namespace

        args = Namespace(
            level="roadmap",
            target_id=None,
            standard_id="commit-required",
            name="Commit Required",
            description="All tasks must have commits",
            type="commit_check",
            enforcement="blocking",
            validation='{"min_commits": 1}',
            dir=str(test_roadmap_with_task)
        )

        result = handle_add_standard(args)

        assert result == 0  # Success

        # Verify standard was added
        roadmap_path = test_roadmap_with_task / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard("commit-required")
        assert standard is not None
        assert standard.name == "Commit Required"
        assert standard.type == StandardType.COMMIT_CHECK
        assert standard.enforcement == EnforcementMode.BLOCKING
        assert standard.validation == {"min_commits": 1}

    def test_add_standard_to_track(self, test_roadmap_with_task):
        """add-standard should add standard to track."""
        from vibey.cli.roadmap_commands.add_standard import handle_add_standard
        from vibey.roadmap.serialization import load_track
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        from argparse import Namespace

        args = Namespace(
            level="track",
            target_id="backend",
            standard_id="doc-review",
            name="Documentation Review",
            description="All tasks should update docs",
            type="file_check",
            enforcement="warning",
            validation='{"pattern": "**/*.md", "min_files": 1}',
            dir=str(test_roadmap_with_task)
        )

        result = handle_add_standard(args)

        assert result == 0  # Success

        # Verify standard was added
        fs = FileSystemManager(test_roadmap_with_task)
        track_path = fs.get_track_path("backend")
        track = load_track(track_path)

        standard = track.get_standard("doc-review")
        assert standard is not None
        assert standard.name == "Documentation Review"
        assert standard.type == StandardType.FILE_CHECK
        assert standard.enforcement == EnforcementMode.WARNING

    def test_add_duplicate_standard_fails(self, test_roadmap_with_task):
        """add-standard should fail if standard ID already exists."""
        from vibey.cli.roadmap_commands.add_standard import handle_add_standard
        from argparse import Namespace

        args = Namespace(
            level="roadmap",
            target_id=None,
            standard_id="test-coverage",  # Already exists
            name="Duplicate",
            description="Duplicate standard",
            type="commit_check",
            enforcement="blocking",
            validation='{"min_commits": 1}',
            dir=str(test_roadmap_with_task)
        )

        result = handle_add_standard(args)

        assert result == 1  # Failure

    def test_add_standard_invalid_json_fails(self, test_roadmap_with_task):
        """add-standard should fail with invalid JSON."""
        from vibey.cli.roadmap_commands.add_standard import handle_add_standard
        from argparse import Namespace

        args = Namespace(
            level="roadmap",
            target_id=None,
            standard_id="new-standard",
            name="Test",
            description="Test",
            type="commit_check",
            enforcement="blocking",
            validation='invalid json',  # Invalid JSON
            dir=str(test_roadmap_with_task)
        )

        result = handle_add_standard(args)

        assert result == 1  # Failure


class TestEnforcementIntegration:
    """Test complete enforcement workflow."""

    def test_complete_workflow(self, test_roadmap_with_task):
        """Test complete workflow: add standard -> check -> override -> complete."""
        from vibey.cli.roadmap_commands.add_standard import handle_add_standard
        from vibey.cli.roadmap_commands.check_standards import handle_check_standards
        from vibey.cli.roadmap_commands.override_standard import handle_override_standard
        from argparse import Namespace

        root_dir = test_roadmap_with_task

        # Step 1: Add a commit standard
        add_args = Namespace(
            level="roadmap",
            target_id=None,
            standard_id="commit-required",
            name="Commit Required",
            description="All tasks must have commits",
            type="commit_check",
            enforcement="blocking",
            validation='{"min_commits": 1}',
            dir=str(root_dir)
        )

        result = handle_add_standard(add_args)
        assert result == 0

        # Step 2: Check standards (should show 2 standards, both failing)
        check_args = Namespace(
            id="backend-1-task-001",
            dir=str(root_dir),
            verbose=True
        )

        result = handle_check_standards(check_args)
        assert result == 1  # Has failures

        # Step 3: Override both standards
        override_args1 = Namespace(
            standard_id="commit-required",
            item_id="backend-1-task-001",
            reason="Emergency hotfix - no commits needed",
            overridden_by="admin",
            dir=str(root_dir)
        )

        result = handle_override_standard(override_args1)
        assert result == 0

        override_args2 = Namespace(
            standard_id="test-coverage",
            item_id="backend-1-task-001",
            reason="Emergency hotfix - testing waived",
            overridden_by="admin",
            dir=str(root_dir)
        )

        result = handle_override_standard(override_args2)
        assert result == 0

        # Step 4: Complete task (should now succeed)
        result = complete_task(root_dir, "backend-1-task-001", completed_by="test")
        assert result == 0  # Success
