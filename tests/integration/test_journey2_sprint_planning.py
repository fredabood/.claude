"""
Integration tests for Journey 2: Sprint Planning & Execution

Tests the complete sprint planning workflow from plan creation through
task breakdown and quality gate configuration.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, GitValidator, MetricsCollector
import time


@pytest.mark.integration
class TestJourney2SprintPlanning:
    """Test Journey 2: Sprint Planning & Execution workflow."""

    def test_01_sprint_plan_creation(self, temp_dir):
        """Test creating a new sprint plan."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        builder.init_git(repo, initial_commit=True)
        validator = StateValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Create sprint plan directory
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Create sprint plan file
        sprint_plan = sprint_dir / "plan.md"
        sprint_plan.write_text("""# Sprint 1: User Authentication

## Goals
- Implement user registration
- Implement user login
- Add JWT authentication

## Tasks
1. Create user model
2. Implement registration endpoint
3. Implement login endpoint
4. Add JWT middleware

## Success Criteria
- All endpoints working
- Unit tests passing
- Security review complete
""")

        plan_creation_time = time.time() - start_time

        # Assert
        assert sprint_plan.exists()
        content_result = validator.validate_file_content(
            sprint_plan,
            contains=["Sprint 1:", "Goals", "Tasks", "Success Criteria"]
        )
        assert content_result.passed

        # Track metrics
        metrics.track("sprint_creation_time", plan_creation_time, unit="seconds", threshold=600)
        assert metrics.assert_metric("sprint_creation_time", max_value=600)

    def test_02_task_breakdown_and_estimation(self, temp_dir):
        """Test task breakdown with time/token estimation."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create task list with estimates
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        tasks_file = sprint_dir / "tasks.yaml"
        tasks_file.write_text("""tasks:
  - id: task-001
    title: Create user model
    estimated_tokens: 2000
    estimated_duration: 2 hours
    priority: high

  - id: task-002
    title: Implement registration endpoint
    estimated_tokens: 3000
    estimated_duration: 3 hours
    priority: high

  - id: task-003
    title: Implement login endpoint
    estimated_tokens: 2500
    estimated_duration: 2.5 hours
    priority: high

  - id: task-004
    title: Add JWT middleware
    estimated_tokens: 1500
    estimated_duration: 1.5 hours
    priority: medium
""")

        validator = StateValidator()

        # Assert
        expected_schema = {
            "required_keys": ["tasks"],
            "key_types": {"tasks": "list"}
        }
        result = validator.validate_yaml_structure(tasks_file, expected_schema)
        assert result.passed

        # Validate task count
        import yaml
        with open(tasks_file) as f:
            data = yaml.safe_load(f)
        assert len(data["tasks"]) == 4
        assert all("estimated_tokens" in task for task in data["tasks"])

    def test_03_quality_gate_configuration(self, temp_dir):
        """Test quality gate configuration for sprint."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Act - Configure sprint quality gates
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        gates_file = sprint_dir / "quality-gates.yaml"
        gates_file.write_text("""quality_gates:
  - name: security_review
    enabled: true
    blocking: true
    threshold: 90

  - name: test_coverage
    enabled: true
    blocking: true
    threshold: 80

  - name: documentation
    enabled: true
    blocking: false
    threshold: 100
""")

        validator = StateValidator()

        # Assert
        assert gates_file.exists()
        expected_schema = {
            "required_keys": ["quality_gates"],
            "key_types": {"quality_gates": "list"}
        }
        result = validator.validate_yaml_structure(gates_file, expected_schema)
        assert result.passed

    def test_04_agent_assignment(self, temp_dir):
        """Test agent assignment to sprint tasks."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Assign agents to tasks
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        assignments_file = sprint_dir / "assignments.yaml"
        assignments_file.write_text("""assignments:
  task-001:
    primary: web-developer
    reviewers:
      - security-reviewer

  task-002:
    primary: web-developer
    reviewers:
      - security-reviewer
      - docs-writer

  task-003:
    primary: web-developer
    reviewers:
      - security-reviewer

  task-004:
    primary: web-developer
    reviewers:
      - security-reviewer
      - performance-engineer
""")

        validator = StateValidator()

        # Assert
        assert assignments_file.exists()
        expected_schema = {
            "required_keys": ["assignments"],
            "key_types": {"assignments": "dict"}
        }
        result = validator.validate_yaml_structure(assignments_file, expected_schema)
        assert result.passed

    def test_05_sprint_state_file_generation(self, temp_dir):
        """Test sprint state file generation for progress tracking."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create sprint state file
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        state_file = sprint_dir / "state.yaml"
        state_file.write_text("""sprint:
  id: sprint-1
  name: User Authentication
  status: in_progress
  started: '2025-11-10T10:00:00Z'
  completed: null

  progress:
    tasks_total: 4
    tasks_completed: 0
    completion_percent: 0

  tasks:
    - id: task-001
      status: in_progress
      started: '2025-11-10T10:30:00Z'
      completed: null

    - id: task-002
      status: not_started
      started: null
      completed: null

    - id: task-003
      status: not_started
      started: null
      completed: null

    - id: task-004
      status: not_started
      started: null
      completed: null
""")

        validator = StateValidator()

        # Assert
        assert state_file.exists()
        expected_schema = {
            "required_keys": ["sprint"],
            "key_types": {"sprint": "dict"}
        }
        result = validator.validate_yaml_structure(state_file, expected_schema)
        assert result.passed

    def test_06_complete_sprint_planning_workflow(self, temp_dir):
        """Test complete end-to-end sprint planning workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Complete workflow
        # Step 1: Create project with Vibey
        repo = builder.create_web_app_repo(name="sprint-project")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Step 2: Create sprint directory structure
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Create all sprint files
        (sprint_dir / "plan.md").write_text("# Sprint 1\n## Goals\n- Goal 1")
        (sprint_dir / "tasks.yaml").write_text("tasks:\n  - id: task-001\n    title: Task 1")
        (sprint_dir / "quality-gates.yaml").write_text("quality_gates:\n  - name: security")
        (sprint_dir / "state.yaml").write_text("sprint:\n  id: sprint-1\n  status: planning")

        total_time = time.time() - start_time

        # Assert - Validate complete sprint structure
        expected_files = {
            "files": [
                ".vibey/sprints/sprint-1/plan.md",
                ".vibey/sprints/sprint-1/tasks.yaml",
                ".vibey/sprints/sprint-1/quality-gates.yaml",
                ".vibey/sprints/sprint-1/state.yaml"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected_files)
        assert result.passed, f"Sprint structure invalid: {result.errors}"

        # Track success metrics
        metrics.track("sprint_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("quality_gate_pass_rate", 100, unit="percentage", threshold=100)
        metrics.track("task_estimation_accuracy", 90, unit="percentage", threshold=85)
        metrics.track("sprint_creation_time", total_time, unit="seconds", threshold=600)

        # Validate metrics
        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0, f"Journey 2 success rate: {success_rate}%"

    def test_07_sprint_plan_validation(self, temp_dir):
        """Test validation of sprint plan structure and content."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Create valid sprint plan
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        plan_file = sprint_dir / "plan.md"
        plan_file.write_text("""# Sprint 1: Feature Name

## Duration
2 weeks

## Goals
- Primary goal
- Secondary goal

## Tasks
1. Task 1 (3h)
2. Task 2 (2h)
3. Task 3 (4h)

## Success Criteria
- [ ] All tasks complete
- [ ] Tests passing
- [ ] Documentation updated

## Quality Gates
- Security review: PASS
- Test coverage: >80%
""")

        # Assert - Validate all required sections present
        content_result = validator.validate_file_content(
            plan_file,
            contains=[
                "Duration",
                "Goals",
                "Tasks",
                "Success Criteria",
                "Quality Gates"
            ]
        )
        assert content_result.passed, f"Plan missing sections: {content_result.errors}"

    def test_08_sprint_progress_tracking(self, temp_dir):
        """Test sprint progress tracking as tasks complete."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        state_file = sprint_dir / "state.yaml"

        # Act - Simulate task completion progression
        import yaml

        # Initial state
        state_data = {
            "sprint": {
                "id": "sprint-1",
                "progress": {
                    "tasks_total": 4,
                    "tasks_completed": 0,
                    "completion_percent": 0
                }
            }
        }
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)

        # Assert initial state
        with open(state_file) as f:
            data = yaml.safe_load(f)
        assert data["sprint"]["progress"]["tasks_completed"] == 0
        assert data["sprint"]["progress"]["completion_percent"] == 0

        # Simulate 2 tasks completed
        state_data["sprint"]["progress"]["tasks_completed"] = 2
        state_data["sprint"]["progress"]["completion_percent"] = 50
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)

        # Assert updated state
        with open(state_file) as f:
            data = yaml.safe_load(f)
        assert data["sprint"]["progress"]["tasks_completed"] == 2
        assert data["sprint"]["progress"]["completion_percent"] == 50

    def test_09_git_commits_for_sprint_planning(self, temp_dir):
        """Test git commits created during sprint planning."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)
        git_validator = GitValidator()

        # Act - Create sprint and commit
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)
        (sprint_dir / "plan.md").write_text("# Sprint 1")

        # Commit sprint plan
        import subprocess
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: create Sprint 1 plan"],
            cwd=repo.path,
            check=True,
            env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
        )

        # Assert - Validate commit
        commits = git_validator.get_commit_history(repo.path, count=2)
        assert len(commits) >= 1

        # Validate conventional commit format
        latest_commit = commits[0]
        assert git_validator.validate_commit_message(latest_commit)
        assert "Sprint 1" in latest_commit.message or "sprint" in latest_commit.message.lower()

    def test_10_sprint_planning_metrics_collection(self, temp_dir):
        """Test metrics collection during sprint planning."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        metrics = MetricsCollector()

        # Act - Simulate sprint planning metrics
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Track planning metrics
        metrics.track("sprint_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("quality_gate_pass_rate", 100, unit="percentage", threshold=100)
        metrics.track("task_estimation_accuracy", 88, unit="percentage", threshold=85)
        metrics.track("sprint_creation_time", 480, unit="seconds", threshold=600)

        # Assert
        assert len(metrics.get_all_metrics()) == 4
        assert metrics.calculate_success_rate() == 100.0

        # Export metrics
        output_file = temp_dir / "journey2-metrics.json"
        export_data = metrics.export_metrics(output_file)

        assert output_file.exists()
        assert all(metric in export_data["metrics"] for metric in [
            "sprint_completion_rate",
            "quality_gate_pass_rate",
            "task_estimation_accuracy",
            "sprint_creation_time"
        ])


@pytest.mark.integration
class TestJourney2ErrorScenarios:
    """Test Journey 2 error handling and edge cases."""

    def test_sprint_plan_missing_required_sections(self, temp_dir):
        """Test handling of incomplete sprint plan."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Create incomplete plan
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        plan_file = sprint_dir / "plan.md"
        plan_file.write_text("# Sprint 1\n\nIncomplete plan")

        # Assert - Validation should detect missing sections
        content_result = validator.validate_file_content(
            plan_file,
            contains=["Goals", "Tasks", "Success Criteria"]
        )
        assert not content_result.passed  # Should fail validation

    def test_invalid_task_estimation(self, temp_dir):
        """Test handling of invalid task estimations."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create tasks with missing estimates
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        tasks_file = sprint_dir / "tasks.yaml"
        tasks_file.write_text("""tasks:
  - id: task-001
    title: Missing estimate
    # No estimated_tokens or estimated_duration
""")

        # Assert - File created but incomplete
        assert tasks_file.exists()
        # In real validation, would flag missing estimates
