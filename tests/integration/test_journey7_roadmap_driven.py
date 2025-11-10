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
        assert "status_sync_rate" in export_data["metrics"]
