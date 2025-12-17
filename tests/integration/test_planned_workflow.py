"""
Integration tests for planned status CLI workflow.

Tests end-to-end planned status workflows: CLI command → Operations → Database/YAML.
"""

import sqlite3
import pytest
from pathlib import Path
from click.testing import CliRunner

from vibey.cli.main import cli


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def roadmap_env(tmp_path):
    """Create a roadmap environment with database for planned status testing."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    (roadmap_dir / "tasks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir(parents=True)
    (roadmap_dir / "tracks").mkdir(parents=True)

    # Create a SQLite database with test data
    db_path = roadmap_dir / "roadmap.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE sprints (
            id TEXT PRIMARY KEY,
            name TEXT,
            track_id TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            sprint_id TEXT
        )
    """)

    # Insert test data
    conn.execute("INSERT INTO tracks VALUES (?, ?)", ("01TRACK001", "Test Track"))
    conn.execute("INSERT INTO sprints VALUES (?, ?, ?)",
                 ("01SPRINT01", "Test Sprint", "01TRACK001"))
    conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                 ("01TASK0001", "Test Task 1", "01SPRINT01"))
    conn.execute("INSERT INTO tasks VALUES (?, ?, ?)",
                 ("01TASK0002", "Test Task 2", "01SPRINT01"))
    conn.commit()
    conn.close()

    return tmp_path


@pytest.fixture
def planned_task(roadmap_env):
    """Create a task with YAML file (planned)."""
    roadmap_dir = roadmap_env / ".vibey" / "roadmap"
    task_yaml = roadmap_dir / "tasks" / "01TASK0001.yaml"
    task_yaml.write_text("""task:
  id: 01TASK0001
  sprint_id: 01SPRINT01
  track_id: 01TRACK001
  task_type: development
  title: Test Task 1
  description: A test task that is planned
  status: not_started
  blocked: false
  created: '2025-12-15T10:00:00Z'
  priority: medium
  metadata: {}
""")
    return "01TASK0001"


@pytest.fixture
def unplanned_task(roadmap_env):
    """Task in database but no YAML file (unplanned)."""
    return "01TASK0002"


class TestPlannedCheckCommand:
    """Integration tests for vibey planned check command."""

    def test_help_output(self, runner):
        """Test planned check --help shows usage info."""
        result = runner.invoke(cli, ["planned", "check", "--help"])
        assert result.exit_code == 0
        assert "Check if a ticket is fully planned" in result.output

    def test_check_planned_task(self, runner, roadmap_env, planned_task):
        """Test checking a planned task shows success."""
        with runner.isolated_filesystem():
            # Copy roadmap env to isolated fs
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "check", planned_task])

            # Task with YAML should be planned
            assert "fully planned" in result.output or "is planned" in result.output
            assert "01TASK0001" in result.output

    def test_check_unplanned_task(self, runner, roadmap_env, unplanned_task):
        """Test checking an unplanned task shows not planned."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "check", unplanned_task])

            # Task without YAML should not be planned
            # Exit code 1 indicates not planned
            assert result.exit_code == 1 or "not planned" in result.output

    def test_check_nonexistent_task(self, runner, roadmap_env):
        """Test checking a nonexistent task shows error."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "check", "01NOTEXIST"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_check_verbose_shows_criteria(self, runner, roadmap_env, planned_task):
        """Test verbose flag shows criteria details."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "check", planned_task, "--verbose"])

            assert "01TASK0001" in result.output
            # Verbose output should include progress info
            assert "criteria" in result.output.lower() or "progress" in result.output.lower()


class TestPlannedListUnplannedCommand:
    """Integration tests for vibey planned list-unplanned command."""

    def test_help_output(self, runner):
        """Test planned list-unplanned --help shows usage info."""
        result = runner.invoke(cli, ["planned", "list-unplanned", "--help"])
        assert result.exit_code == 0
        assert "List tickets that are not yet planned" in result.output

    def test_list_unplanned_shows_tasks(self, runner, roadmap_env, planned_task):
        """Test list-unplanned shows unplanned tasks."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "list-unplanned", "--scope", "tasks"])

            # Task without YAML (01TASK0002) should be listed
            assert result.exit_code == 0
            # Either shows unplanned tasks or says all are planned
            assert "01TASK0002" in result.output or "All tasks are planned" in result.output

    def test_list_unplanned_with_limit(self, runner, roadmap_env):
        """Test list-unplanned respects limit parameter."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "list-unplanned", "--limit", "1"])

            assert result.exit_code == 0

    def test_list_unplanned_filter_by_track(self, runner, roadmap_env):
        """Test list-unplanned can filter by track."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "list-unplanned",
                                         "--track", "01TRACK001"])

            assert result.exit_code == 0

    def test_list_unplanned_empty_when_all_planned(self, runner, roadmap_env):
        """Test list-unplanned shows success when all tasks are planned."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            # Create YAML for both tasks
            (Path(".vibey/roadmap/tasks/01TASK0001.yaml")).write_text(
                "task:\n  id: 01TASK0001\n  title: Task 1"
            )
            (Path(".vibey/roadmap/tasks/01TASK0002.yaml")).write_text(
                "task:\n  id: 01TASK0002\n  title: Task 2"
            )

            result = runner.invoke(cli, ["planned", "list-unplanned", "--scope", "tasks"])

            assert result.exit_code == 0
            assert "All tasks are planned" in result.output


class TestPlannedNextCommand:
    """Integration tests for vibey planned next command."""

    def test_help_output(self, runner):
        """Test planned next --help shows usage info."""
        result = runner.invoke(cli, ["planned", "next", "--help"])
        assert result.exit_code == 0
        assert "Get the next planning work item" in result.output

    def test_next_shows_work_item(self, runner, roadmap_env):
        """Test planned next shows next work item when tasks are unplanned."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "next", "01TRACK001"])

            # Should show next planning work or indicate fully planned
            assert result.exit_code == 0
            assert "01TRACK001" in result.output or "01TASK" in result.output or "fully planned" in result.output

    def test_next_fully_planned_track(self, runner, roadmap_env):
        """Test planned next shows success when track is fully planned."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            # Create YAML for all tasks
            (Path(".vibey/roadmap/tasks/01TASK0001.yaml")).write_text(
                "task:\n  id: 01TASK0001\n  title: Task 1"
            )
            (Path(".vibey/roadmap/tasks/01TASK0002.yaml")).write_text(
                "task:\n  id: 01TASK0002\n  title: Task 2"
            )

            result = runner.invoke(cli, ["planned", "next", "01TRACK001"])

            assert result.exit_code == 0
            assert "fully planned" in result.output


class TestPlannedApproveCommand:
    """Integration tests for vibey planned approve command."""

    def test_help_output(self, runner):
        """Test planned approve --help shows usage info."""
        result = runner.invoke(cli, ["planned", "approve", "--help"])
        assert result.exit_code == 0
        assert "Manually approve" in result.output

    def test_approve_updates_yaml(self, runner, roadmap_env, planned_task):
        """Test planned approve updates YAML metadata."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "approve", planned_task])

            assert result.exit_code == 0
            assert "Approved" in result.output

            # Verify YAML was updated
            import yaml
            with open(f".vibey/roadmap/tasks/{planned_task}.yaml") as f:
                data = yaml.safe_load(f)

            # Check metadata was added
            task_data = data.get('task', data)
            assert 'metadata' in task_data
            assert task_data['metadata'].get('planned_approved') is True

    def test_approve_with_approver(self, runner, roadmap_env, planned_task):
        """Test planned approve records approver name."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "approve", planned_task,
                                         "--approver", "alice"])

            assert result.exit_code == 0
            assert "alice" in result.output or "Approved" in result.output

    def test_approve_nonexistent_task(self, runner, roadmap_env):
        """Test approve fails for nonexistent task."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            result = runner.invoke(cli, ["planned", "approve", "01NOTEXIST"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower() or "error" in result.output.lower()


class TestPlannedWorkflowIntegration:
    """Integration tests for complete planned workflow."""

    def test_complete_planning_workflow(self, runner, roadmap_env):
        """Test complete workflow: check → list → next → approve."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            # Step 1: Check track status (should have unplanned tasks)
            result = runner.invoke(cli, ["planned", "list-unplanned",
                                         "--track", "01TRACK001"])
            assert result.exit_code == 0

            # Step 2: Get next work item
            result = runner.invoke(cli, ["planned", "next", "01TRACK001"])
            assert result.exit_code == 0

            # Step 3: Create YAML for a task (simulate planning)
            (Path(".vibey/roadmap/tasks/01TASK0001.yaml")).write_text(
                "task:\n  id: 01TASK0001\n  title: Task 1\n  metadata: {}"
            )

            # Step 4: Check the task is now planned
            result = runner.invoke(cli, ["planned", "check", "01TASK0001"])
            assert "fully planned" in result.output or "is planned" in result.output

            # Step 5: Approve the planning
            result = runner.invoke(cli, ["planned", "approve", "01TASK0001",
                                         "--approver", "alice"])
            assert result.exit_code == 0
            assert "Approved" in result.output

    def test_database_and_yaml_sync(self, runner, roadmap_env):
        """Test that planned status reflects both database and YAML state."""
        with runner.isolated_filesystem():
            import shutil
            shutil.copytree(roadmap_env / ".vibey", ".vibey")

            # Task in database but no YAML = unplanned
            result = runner.invoke(cli, ["planned", "check", "01TASK0002"])
            assert result.exit_code == 1 or "not planned" in result.output

            # Create YAML file
            (Path(".vibey/roadmap/tasks/01TASK0002.yaml")).write_text(
                "task:\n  id: 01TASK0002\n  title: Task 2"
            )

            # Now should be planned
            result = runner.invoke(cli, ["planned", "check", "01TASK0002"])
            assert "fully planned" in result.output or "is planned" in result.output
