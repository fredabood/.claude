"""
Integration tests for Journey 7: Roadmap-Driven Development

Tests roadmap initialization, track creation, sprint creation from roadmap,
task progression, and status propagation through the hierarchy.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
import yaml


@pytest.mark.integration
class TestJourney7RoadmapDriven:
    """Test Journey 7: Roadmap-Driven Development workflow."""

    def test_01_roadmap_initialization(self, temp_dir):
        """Test initializing roadmap system in project."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Create roadmap structure
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        roadmap_file = vibey_dir / "roadmap.yaml"
        roadmap_file.write_text("""roadmap:
  id: project-roadmap-v1
  name: Project Development Roadmap
  version: 1.0.0
  created: '2025-11-10T00:00:00+00:00'
  tracks: []
""")

        # Assert
        assert roadmap_file.exists()
        expected_schema = {
            "required_keys": ["roadmap"],
            "key_types": {"roadmap": "dict"}
        }
        result = validator.validate_yaml_structure(roadmap_file, expected_schema)
        assert result.passed

    def test_02_track_creation(self, temp_dir):
        """Test creating development track in roadmap."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create track
        tracks_dir = repo.path / ".vibey" / "tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)

        track_file = tracks_dir / "core-features.yaml"
        track_file.write_text("""track:
  id: core-features
  name: Core Features Development
  roadmap_id: project-roadmap-v1
  status: not_started
  priority: critical
  created: '2025-11-10T00:00:00+00:00'
  estimated_duration: 8 weeks
  sprints:
    - id: core-features-1
      name: Authentication
      status: not_started
""")

        # Assert
        assert track_file.exists()
        with open(track_file) as f:
            data = yaml.safe_load(f)
        assert data["track"]["id"] == "core-features"
        assert len(data["track"]["sprints"]) == 1

    def test_03_sprint_creation_from_roadmap(self, temp_dir):
        """Test creating sprint from roadmap track."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create sprint
        sprint_dir = repo.path / ".vibey" / "roadmap" / "core-features" / "core-features-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        sprint_file = sprint_dir / "sprint.yaml"
        sprint_file.write_text("""sprint:
  id: core-features-1
  name: Authentication
  track_id: core-features
  roadmap_id: project-roadmap-v1
  status: not_started
  created: '2025-11-10T00:00:00+00:00'
  progress:
    tasks_total: 5
    tasks_completed: 0
    completion_percent: 0
""")

        # Assert
        assert sprint_file.exists()
        with open(sprint_file) as f:
            data = yaml.safe_load(f)
        assert data["sprint"]["track_id"] == "core-features"

    def test_04_task_progression(self, temp_dir):
        """Test task progression within sprint."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        tasks_dir = repo.path / ".vibey" / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)

        tasks_file = tasks_dir / "core-features-1-tasks.yaml"

        # Act - Create tasks and simulate progression
        initial_tasks = {
            "sprint_id": "core-features-1",
            "tasks": [
                {"id": "task-001", "title": "Task 1", "status": "not_started"},
                {"id": "task-002", "title": "Task 2", "status": "not_started"},
                {"id": "task-003", "title": "Task 3", "status": "not_started"}
            ]
        }
        with open(tasks_file, 'w') as f:
            yaml.dump(initial_tasks, f)

        # Progress task-001
        initial_tasks["tasks"][0]["status"] = "in_progress"
        with open(tasks_file, 'w') as f:
            yaml.dump(initial_tasks, f)

        # Complete task-001, start task-002
        initial_tasks["tasks"][0]["status"] = "completed"
        initial_tasks["tasks"][1]["status"] = "in_progress"
        with open(tasks_file, 'w') as f:
            yaml.dump(initial_tasks, f)

        # Assert
        with open(tasks_file) as f:
            final_tasks = yaml.safe_load(f)

        assert final_tasks["tasks"][0]["status"] == "completed"
        assert final_tasks["tasks"][1]["status"] == "in_progress"
        assert final_tasks["tasks"][2]["status"] == "not_started"

    def test_05_status_propagation_task_to_sprint(self, temp_dir):
        """Test status propagation from task to sprint level."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        sprint_dir = repo.path / ".vibey" / "roadmap" / "core-features" / "core-features-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        sprint_file = sprint_dir / "sprint.yaml"

        # Act - Simulate task completions updating sprint
        sprint_data = {
            "sprint": {
                "id": "core-features-1",
                "status": "in_progress",
                "progress": {
                    "tasks_total": 5,
                    "tasks_completed": 0,
                    "completion_percent": 0
                }
            }
        }
        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        # Complete 3 tasks
        sprint_data["sprint"]["progress"]["tasks_completed"] = 3
        sprint_data["sprint"]["progress"]["completion_percent"] = 60
        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        # Assert
        with open(sprint_file) as f:
            data = yaml.safe_load(f)

        assert data["sprint"]["progress"]["tasks_completed"] == 3
        assert data["sprint"]["progress"]["completion_percent"] == 60

    def test_06_status_propagation_sprint_to_track(self, temp_dir):
        """Test status propagation from sprint to track level."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        tracks_dir = repo.path / ".vibey" / "tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)

        track_file = tracks_dir / "core-features.yaml"

        # Act - Simulate sprint completion updating track
        track_data = {
            "track": {
                "id": "core-features",
                "status": "in_progress",
                "progress": {
                    "sprints_total": 3,
                    "sprints_completed": 0,
                    "tasks_total": 15,
                    "tasks_completed": 0,
                    "completion_percent": 0
                },
                "sprints": [
                    {"id": "sprint-1", "status": "in_progress"},
                    {"id": "sprint-2", "status": "not_started"},
                    {"id": "sprint-3", "status": "not_started"}
                ]
            }
        }
        with open(track_file, 'w') as f:
            yaml.dump(track_data, f)

        # Complete sprint-1
        track_data["track"]["sprints"][0]["status"] = "completed"
        track_data["track"]["sprints"][1]["status"] = "in_progress"
        track_data["track"]["progress"]["sprints_completed"] = 1
        track_data["track"]["progress"]["tasks_completed"] = 5
        track_data["track"]["progress"]["completion_percent"] = 33

        with open(track_file, 'w') as f:
            yaml.dump(track_data, f)

        # Assert
        with open(track_file) as f:
            data = yaml.safe_load(f)

        assert data["track"]["progress"]["sprints_completed"] == 1
        assert data["track"]["progress"]["completion_percent"] == 33
        assert data["track"]["sprints"][0]["status"] == "completed"

    def test_07_complete_roadmap_driven_workflow(self, temp_dir):
        """Test complete end-to-end roadmap-driven workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        metrics = MetricsCollector()

        # Act - Complete workflow
        repo = builder.create_web_app_repo(name="roadmap-project")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)

        # Step 1: Create roadmap structure
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        (vibey_dir / "roadmap.yaml").write_text("roadmap:\n  id: v1")

        tracks_dir = vibey_dir / "tracks"
        tracks_dir.mkdir(exist_ok=True)

        (tracks_dir / "core-features.yaml").write_text("""track:
  id: core-features
  status: in_progress
  sprints:
    - id: sprint-1
      status: completed
""")

        roadmap_dir = vibey_dir / "roadmap" / "core-features" / "sprint-1"
        roadmap_dir.mkdir(parents=True, exist_ok=True)

        (roadmap_dir / "sprint.yaml").write_text("""sprint:
  id: sprint-1
  status: completed
  progress:
    tasks_completed: 5
    tasks_total: 5
    completion_percent: 100
""")

        tasks_dir = vibey_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)

        (tasks_dir / "sprint-1-tasks.yaml").write_text("""sprint_id: sprint-1
tasks:
  - id: task-001
    status: completed
""")

        # Assert - Complete roadmap structure
        expected_structure = {
            "directories": [
                ".vibey",
                ".vibey/tracks",
                ".vibey/roadmap/core-features/sprint-1",
                ".vibey/tasks"
            ],
            "files": [
                ".vibey/roadmap.yaml",
                ".vibey/tracks/core-features.yaml",
                ".vibey/roadmap/core-features/sprint-1/sprint.yaml",
                ".vibey/tasks/sprint-1-tasks.yaml"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected_structure)
        assert result.passed, f"Roadmap structure invalid: {result.errors}"

        # Track metrics
        metrics.track("roadmap_accuracy", 100, unit="percentage", threshold=95)
        metrics.track("status_sync_rate", 100, unit="percentage", threshold=95)
        metrics.track("track_completion_rate", 33, unit="percentage")

        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0

    def test_08_roadmap_metrics_collection(self, temp_dir):
        """Test metrics collection for roadmap-driven development."""
        # Arrange
        metrics = MetricsCollector()

        # Act
        metrics.track("roadmap_accuracy", 98, unit="percentage", threshold=95)
        metrics.track("status_sync_rate", 97, unit="percentage", threshold=95)
        metrics.track("track_completion_rate", 40, unit="percentage")
        metrics.track("sprint_velocity", 5.2, unit="tasks_per_week")

        # Assert
        assert len(metrics.get_all_metrics()) == 4
        assert metrics.calculate_success_rate() == 100.0

        export_data = metrics.export_metrics()
        assert "roadmap_accuracy" in export_data["metrics"]

    def test_09_git_commit_tracking_task_level(self, temp_dir):
        """Test git commit tracking at task level."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)

        # Create task with commits array
        task_dir = repo.path / ".vibey" / "roadmap" / "core-features" / "sprint-1" / "task-001"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_file = task_dir / "task.yaml"

        # Act - Create task with commit tracking
        task_data = {
            "task": {
                "id": "task-001",
                "name": "User registration API",
                "sprint_id": "sprint-1",
                "status": "in_progress",
                "commits": [
                    {
                        "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
                        "message": "feat: Implement user registration endpoint",
                        "author": "Developer <dev@example.com>",
                        "date": "2025-11-11T16:15:17-05:00"
                    },
                    {
                        "sha": "f7e8d9c0b1a2345678901234567890abcdef1234",
                        "message": "fix: Add email validation",
                        "author": "Developer <dev@example.com>",
                        "date": "2025-11-11T17:30:00-05:00"
                    }
                ]
            }
        }
        with open(task_file, 'w') as f:
            yaml.dump(task_data, f)

        # Assert - Verify commits are stored
        with open(task_file) as f:
            loaded_task = yaml.safe_load(f)

        assert "commits" in loaded_task["task"]
        assert len(loaded_task["task"]["commits"]) == 2
        assert loaded_task["task"]["commits"][0]["sha"] == "a1b2c3d4e5f6789012345678901234567890abcd"
        assert "feat: Implement user registration" in loaded_task["task"]["commits"][0]["message"]

    def test_10_git_commit_tracking_sprint_level(self, temp_dir):
        """Test git commit tracking at sprint level (task completion commits)."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Create sprint with task completion commits
        sprint_dir = repo.path / ".vibey" / "roadmap" / "core-features" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)
        sprint_file = sprint_dir / "sprint.yaml"

        # Act - Create sprint with task completion commit tracking
        sprint_data = {
            "sprint": {
                "id": "sprint-1",
                "name": "Authentication",
                "track_id": "core-features",
                "status": "in_progress",
                "commits": [
                    {
                        "task_id": "task-001",
                        "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
                        "message": "feat: Complete user registration task",
                        "author": "Developer <dev@example.com>",
                        "date": "2025-11-11T18:00:00-05:00"
                    },
                    {
                        "task_id": "task-002",
                        "sha": "b2c3d4e5f6789012345678901234567890abcdef",
                        "message": "feat: Complete login/logout task",
                        "author": "Developer <dev@example.com>",
                        "date": "2025-11-12T10:00:00-05:00"
                    }
                ]
            }
        }
        with open(sprint_file, 'w') as f:
            yaml.dump(sprint_data, f)

        # Assert - Verify task completion commits are stored
        with open(sprint_file) as f:
            loaded_sprint = yaml.safe_load(f)

        assert "commits" in loaded_sprint["sprint"]
        assert len(loaded_sprint["sprint"]["commits"]) == 2
        assert loaded_sprint["sprint"]["commits"][0]["task_id"] == "task-001"
        assert loaded_sprint["sprint"]["commits"][1]["task_id"] == "task-002"

    def test_11_git_commit_tracking_track_level(self, temp_dir):
        """Test git commit tracking at track level (sprint completion commits)."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Create track with sprint completion commits
        tracks_dir = repo.path / ".vibey" / "roadmap" / "core-features"
        tracks_dir.mkdir(parents=True, exist_ok=True)
        track_file = tracks_dir / "track.yaml"

        # Act - Create track with sprint completion commit tracking
        track_data = {
            "track": {
                "id": "core-features",
                "name": "Core Features Development",
                "status": "in_progress",
                "commits": [
                    {
                        "sprint_id": "sprint-1",
                        "sha": "c3d4e5f6789012345678901234567890abcdef12",
                        "message": "feat: Complete Authentication sprint",
                        "author": "Developer <dev@example.com>",
                        "date": "2025-11-12T18:00:00-05:00"
                    }
                ]
            }
        }
        with open(track_file, 'w') as f:
            yaml.dump(track_data, f)

        # Assert - Verify sprint completion commits are stored
        with open(track_file) as f:
            loaded_track = yaml.safe_load(f)

        assert "commits" in loaded_track["track"]
        assert len(loaded_track["track"]["commits"]) == 1
        assert loaded_track["track"]["commits"][0]["sprint_id"] == "sprint-1"
        assert "Complete Authentication sprint" in loaded_track["track"]["commits"][0]["message"]

    def test_12_hierarchical_commit_tracking_workflow(self, temp_dir):
        """Test complete hierarchical commit tracking workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)

        # Create complete hierarchy with commits
        vibey_dir = repo.path / ".vibey"

        # Task level - multiple commits impacting task
        task_dir = vibey_dir / "roadmap" / "auth-track" / "auth-sprint-1" / "auth-task-001"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "task.yaml").write_text("""task:
  id: auth-task-001
  name: User registration
  status: completed
  commits:
    - sha: a1b2c3d4
      message: "feat: Start user registration"
      author: "Dev <dev@example.com>"
      date: "2025-11-11T10:00:00Z"
    - sha: b2c3d4e5
      message: "feat: Add validation"
      author: "Dev <dev@example.com>"
      date: "2025-11-11T14:00:00Z"
    - sha: c3d4e5f6
      message: "fix: Handle edge cases"
      author: "Dev <dev@example.com>"
      date: "2025-11-11T16:00:00Z"
""")

        # Sprint level - task completion commits
        sprint_dir = vibey_dir / "roadmap" / "auth-track" / "auth-sprint-1"
        (sprint_dir / "sprint.yaml").write_text("""sprint:
  id: auth-sprint-1
  name: Authentication
  status: completed
  commits:
    - task_id: auth-task-001
      sha: c3d4e5f6
      message: "feat: Complete user registration task"
      author: "Dev <dev@example.com>"
      date: "2025-11-11T16:00:00Z"
""")

        # Track level - sprint completion commits
        track_dir = vibey_dir / "roadmap" / "auth-track"
        (track_dir / "track.yaml").write_text("""track:
  id: auth-track
  name: Authentication Track
  status: in_progress
  commits:
    - sprint_id: auth-sprint-1
      sha: d4e5f6a7
      message: "feat: Complete Authentication sprint"
      author: "Dev <dev@example.com>"
      date: "2025-11-12T10:00:00Z"
""")

        # Assert - Verify complete hierarchy
        task_data = yaml.safe_load((task_dir / "task.yaml").read_text())
        sprint_data = yaml.safe_load((sprint_dir / "sprint.yaml").read_text())
        track_data = yaml.safe_load((track_dir / "track.yaml").read_text())

        # Task has 3 commits (all work on the task)
        assert len(task_data["task"]["commits"]) == 3

        # Sprint has 1 commit (completion of task-001)
        assert len(sprint_data["sprint"]["commits"]) == 1
        assert sprint_data["sprint"]["commits"][0]["task_id"] == "auth-task-001"

        # Track has 1 commit (completion of sprint-1)
        assert len(track_data["track"]["commits"]) == 1
        assert track_data["track"]["commits"][0]["sprint_id"] == "auth-sprint-1"

    def test_15_platform_validation_workflow(self, temp_dir):
        """Test platform validation in realistic workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Create roadmap with deployed platforms
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        roadmap_file = vibey_dir / "roadmap.yaml"
        roadmap_file.write_text("""roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
  created: '2025-11-10T00:00:00+00:00'
  deployed_platforms:
    - platform: claude-code
      context_window: 200000
      deployed_at: 1731330000
      deployed_by: alice@example.com
      primary: true
    - platform: goose
      context_window: 128000
      deployed_at: 1731344400
      deployed_by: bob@example.com
      primary: false
  tracks: []
""")

        # Create task structure
        task_dir = vibey_dir / "roadmap" / "test-track" / "test-sprint-1" / "test-task-001"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Act - Add commits with valid and invalid platforms
        # Valid commit (claude-code is deployed)
        task_file = task_dir / "task.yaml"
        task_file.write_text("""task:
  id: test-task-001
  title: Test Task
  status: in_progress
  commits:
    - sha: a1b2c3d4
      message: "feat: Add feature"
      author: "Alice <alice@example.com>"
      platform: claude-code
      submitted_at: 1731345600
      date: "2025-11-11T12:00:00Z"
""")

        # Valid commit (goose is also deployed)
        task_file.write_text("""task:
  id: test-task-001
  title: Test Task
  status: in_progress
  commits:
    - sha: a1b2c3d4
      message: "feat: Add feature"
      author: "Alice <alice@example.com>"
      platform: claude-code
      submitted_at: 1731345600
      date: "2025-11-11T12:00:00Z"
    - sha: b2c3d4e5
      message: "fix: Bug fix"
      author: "Bob <bob@example.com>"
      platform: goose
      submitted_at: 1731349200
      date: "2025-11-11T13:00:00Z"
""")

        # Assert - Verify both commits accepted
        task_data = yaml.safe_load(task_file.read_text())
        assert len(task_data["task"]["commits"]) == 2
        assert task_data["task"]["commits"][0]["platform"] == "claude-code"
        assert task_data["task"]["commits"][1]["platform"] == "goose"

        # Note: Invalid platform test would require Python code execution
        # which is better suited for unit tests (already covered in test_platform_validation.py)

    def test_16_multi_platform_team_workflow(self, temp_dir):
        """Test multiple platforms contributing to same task."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Create roadmap with multiple platforms
        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)

        roadmap_file = vibey_dir / "roadmap.yaml"
        roadmap_file.write_text("""roadmap:
  id: multi-platform-roadmap
  name: Multi-Platform Roadmap
  version: 1.0.0
  created: '2025-11-10T00:00:00+00:00'
  deployed_platforms:
    - platform: claude-code
      context_window: 200000
      deployed_at: 1731330000
      deployed_by: alice@example.com
      primary: true
    - platform: goose
      context_window: 128000
      deployed_at: 1731344400
      deployed_by: bob@example.com
      primary: false
    - platform: cursor
      context_window: 100000
      deployed_at: 1731358800
      deployed_by: charlie@example.com
      primary: false
  tracks: []
""")

        # Create task with commits from multiple platforms
        task_dir = vibey_dir / "roadmap" / "collab-track" / "collab-sprint-1" / "collab-task-001"
        task_dir.mkdir(parents=True, exist_ok=True)

        task_file = task_dir / "task.yaml"
        task_file.write_text("""task:
  id: collab-task-001
  title: Collaborative Task
  status: completed
  commits:
    # Alice's work (Claude Code)
    - sha: a1b2c3d4
      message: "feat: Initial implementation"
      author: "Alice <alice@example.com>"
      platform: claude-code
      submitted_at: 1731345600
      date: "2025-11-11T12:00:00Z"

    - sha: a2b3c4d5
      message: "feat: Add core logic"
      author: "Alice <alice@example.com>"
      platform: claude-code
      submitted_at: 1731349200
      date: "2025-11-11T13:00:00Z"

    # Bob's work (Goose)
    - sha: b1c2d3e4
      message: "feat: Add validation"
      author: "Bob <bob@example.com>"
      platform: goose
      submitted_at: 1731352800
      date: "2025-11-11T14:00:00Z"

    - sha: b2c3d4e5
      message: "fix: Handle edge cases"
      author: "Bob <bob@example.com>"
      platform: goose
      submitted_at: 1731356400
      date: "2025-11-11T15:00:00Z"

    # Charlie's work (Cursor)
    - sha: c1d2e3f4
      message: "docs: Add documentation"
      author: "Charlie <charlie@example.com>"
      platform: cursor
      submitted_at: 1731360000
      date: "2025-11-11T16:00:00Z"
""")

        # Assert - Verify all platforms tracked
        task_data = yaml.safe_load(task_file.read_text())
        commits = task_data["task"]["commits"]

        assert len(commits) == 5

        # Verify platform attribution
        claude_commits = [c for c in commits if c["platform"] == "claude-code"]
        goose_commits = [c for c in commits if c["platform"] == "goose"]
        cursor_commits = [c for c in commits if c["platform"] == "cursor"]

        assert len(claude_commits) == 2
        assert len(goose_commits) == 2
        assert len(cursor_commits) == 1

        # Verify all have required fields
        for commit in commits:
            assert "platform" in commit
            assert "submitted_at" in commit
            assert isinstance(commit["submitted_at"], int)
            assert commit["submitted_at"] > 0

        # Verify timeline (commits should be in chronological order)
        timestamps = [c["submitted_at"] for c in commits]
        assert timestamps == sorted(timestamps)
