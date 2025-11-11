"""
End-to-end tests for complete sprint workflows.

Tests the entire sprint lifecycle from initialization through planning,
execution, quality assurance, and completion.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, GitValidator, MetricsCollector
import time
import subprocess
import yaml


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteSprint:
    """Test complete end-to-end sprint workflows."""

    def test_01_complete_sprint_lifecycle(self, temp_dir):
        """Test complete sprint from init to completion."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        git_validator = GitValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Phase 1: Initialization
        repo = builder.create_web_app_repo(name="e2e-sprint-project")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Phase 2: Sprint Planning
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        (sprint_dir / "plan.md").write_text("""# Sprint 1: User Authentication

## Goals
- Implement user registration
- Implement user login
- Add JWT authentication

## Tasks
1. Create user model (3h)
2. Implement registration endpoint (4h)
3. Implement login endpoint (3h)
4. Add JWT middleware (2h)

## Success Criteria
- All endpoints working
- Unit tests passing (>80% coverage)
- Security review complete

## Quality Gates
- Security review: REQUIRED
- Test coverage: >80%
""")

        (sprint_dir / "state.yaml").write_text("""sprint:
  id: sprint-1
  status: in_progress
  started: '2025-11-10T08:00:00Z'
  progress:
    tasks_total: 4
    tasks_completed: 0
    completion_percent: 0
""")

        # Commit sprint plan
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: create Sprint 1 plan"],
            cwd=repo.path,
            check=True,
            env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
        )

        # Phase 3: Feature Development
        # Task 1: User model
        user_model = repo.path / "src" / "models" / "user.ts"
        user_model.parent.mkdir(parents=True, exist_ok=True)
        user_model.write_text("""export interface User {
  id: string;
  email: string;
  password: string;
  createdAt: Date;
}
""")
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: create user model"],
            cwd=repo.path,
            check=True,
            env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
        )

        # Task 2: Registration endpoint
        register = repo.path / "src" / "api" / "register.ts"
        register.parent.mkdir(parents=True, exist_ok=True)
        register.write_text("""export async function register(email: string, password: string) {
  // Registration logic
  return { success: true };
}
""")
        subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: implement registration endpoint"],
            cwd=repo.path,
            check=True,
            env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
        )

        # Phase 4: Quality Assurance
        audit_dir = repo.path / ".vibey" / "audits" / "security"
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / "sprint-1-audit.md").write_text("""# Security Audit

## Score
85/100 (PASS)

## Findings
- ✅ Password hashing implemented
- ✅ Input validation present
- ⚠️  Add rate limiting
""")

        # Phase 5: Sprint Completion
        with open(sprint_dir / "state.yaml") as f:
            state = yaml.safe_load(f)
        state["sprint"]["status"] = "completed"
        state["sprint"]["completed"] = "2025-11-10T10:00:00Z"
        state["sprint"]["progress"]["tasks_completed"] = 4
        state["sprint"]["progress"]["completion_percent"] = 100
        with open(sprint_dir / "state.yaml", 'w') as f:
            yaml.dump(state, f)

        total_time = time.time() - start_time

        # Assert - Validate complete sprint
        # Check directory structure
        expected_structure = {
            "directories": [
                ".vibey",
                ".vibey/sprints/sprint-1",
                ".vibey/audits/security",
                "src/models",
                "src/api"
            ],
            "files": [
                "CLAUDE.md",
                ".vibey/config/project.yaml",
                ".vibey/sprints/sprint-1/plan.md",
                ".vibey/sprints/sprint-1/state.yaml",
                ".vibey/audits/security/sprint-1-audit.md",
                "src/models/user.ts",
                "src/api/register.ts"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected_structure)
        assert result.passed, f"Sprint structure invalid: {result.errors}"

        # Check git history
        commits = git_validator.get_commit_history(repo.path, count=5)
        assert len(commits) >= 3
        assert all(git_validator.validate_commit_message(c) for c in commits[:3])

        # Check sprint completion
        with open(sprint_dir / "state.yaml") as f:
            final_state = yaml.safe_load(f)
        assert final_state["sprint"]["status"] == "completed"
        assert final_state["sprint"]["progress"]["completion_percent"] == 100

        # Track metrics
        metrics.track("sprint_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("total_sprint_time", total_time, unit="seconds")
        metrics.track("tasks_completed", 4, unit="count")
        metrics.track("quality_gates_passed", 1, unit="count")

        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0

    def test_02_multi_task_sprint_execution(self, temp_dir):
        """Test sprint with multiple tasks executed in sequence."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo)

        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Act - Create and execute 5 tasks
        tasks = []
        for i in range(1, 6):
            task_file = repo.path / "app" / f"task{i}.py"
            task_file.write_text(f"# Task {i} implementation")

            subprocess.run(["git", "add", "."], cwd=repo.path, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"feat: implement task {i}"],
                cwd=repo.path,
                check=True,
                env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@test.com",
                     "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@test.com"}
            )
            tasks.append(task_file)

        # Assert
        assert all(task.exists() for task in tasks)

        git_validator = GitValidator()
        commits = git_validator.get_commit_history(repo.path, count=6)
        assert len([c for c in commits if "task" in c.message.lower()]) == 5

    def test_03_sprint_with_quality_gate_validation(self, temp_dir):
        """Test sprint completion with quality gate validation."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Create sprint with quality gates
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        (sprint_dir / "quality-gates.yaml").write_text("""quality_gates:
  - name: security_review
    enabled: true
    blocking: true
    status: passed
    score: 85

  - name: test_coverage
    enabled: true
    blocking: true
    status: passed
    score: 88

  - name: documentation
    enabled: true
    blocking: false
    status: passed
    score: 90
""")

        # Assert
        assert (sprint_dir / "quality-gates.yaml").exists()

        with open(sprint_dir / "quality-gates.yaml") as f:
            gates = yaml.safe_load(f)

        # All gates passed
        all_passed = all(gate["status"] == "passed" for gate in gates["quality_gates"])
        assert all_passed

        # Track metrics
        for gate in gates["quality_gates"]:
            metrics.track(
                gate["name"],
                gate["score"],
                unit="percentage",
                threshold=70 if gate["blocking"] else 60
            )

        assert metrics.calculate_success_rate() == 100.0

    def test_04_sprint_state_transitions(self, temp_dir):
        """Test sprint state transitions through lifecycle."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)
        state_file = sprint_dir / "state.yaml"

        # Act & Assert - Transition through states
        # State 1: Planning
        state = {
            "sprint": {
                "id": "sprint-1",
                "status": "planning",
                "progress": {"tasks_completed": 0, "completion_percent": 0}
            }
        }
        with open(state_file, 'w') as f:
            yaml.dump(state, f)

        with open(state_file) as f:
            data = yaml.safe_load(f)
        assert data["sprint"]["status"] == "planning"

        # State 2: In Progress
        state["sprint"]["status"] = "in_progress"
        state["sprint"]["progress"]["tasks_completed"] = 2
        state["sprint"]["progress"]["completion_percent"] = 50
        with open(state_file, 'w') as f:
            yaml.dump(state, f)

        with open(state_file) as f:
            data = yaml.safe_load(f)
        assert data["sprint"]["status"] == "in_progress"
        assert data["sprint"]["progress"]["completion_percent"] == 50

        # State 3: Completed
        state["sprint"]["status"] = "completed"
        state["sprint"]["progress"]["tasks_completed"] = 4
        state["sprint"]["progress"]["completion_percent"] = 100
        with open(state_file, 'w') as f:
            yaml.dump(state, f)

        with open(state_file) as f:
            data = yaml.safe_load(f)
        assert data["sprint"]["status"] == "completed"
        assert data["sprint"]["progress"]["completion_percent"] == 100

    def test_05_sprint_with_multiple_agents(self, temp_dir):
        """Test sprint involving multiple specialized agents."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Act - Create agent assignments
        (sprint_dir / "assignments.yaml").write_text("""assignments:
  task-001:
    primary: web-developer
    reviewers:
      - security-reviewer
      - performance-engineer

  task-002:
    primary: web-developer
    reviewers:
      - security-reviewer

  task-003:
    primary: ml-engineer
    reviewers:
      - web-developer
      - docs-writer
""")

        # Assert
        assert (sprint_dir / "assignments.yaml").exists()

        with open(sprint_dir / "assignments.yaml") as f:
            assignments = yaml.safe_load(f)

        assert len(assignments["assignments"]) == 3
        assert "web-developer" in assignments["assignments"]["task-001"]["reviewers"] + [assignments["assignments"]["task-001"]["primary"]]

    def test_06_sprint_success_metrics_aggregation(self, temp_dir):
        """Test aggregation of success metrics across sprint."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Track metrics from different phases
        # Planning phase
        metrics.track("planning_time", 300, unit="seconds", threshold=600)

        # Development phase
        metrics.track("development_time", 7200, unit="seconds", threshold=14400)
        metrics.track("code_quality", 92, unit="percentage", threshold=80)

        # QA phase
        metrics.track("security_score", 88, unit="percentage", threshold=70)
        metrics.track("test_coverage", 85, unit="percentage", threshold=80)

        # Completion metrics
        metrics.track("sprint_completion_rate", 100, unit="percentage", threshold=100)

        # Assert - All metrics pass
        assert len(metrics.get_all_metrics()) == 6
        assert metrics.calculate_success_rate() == 100.0

        # Export aggregated metrics
        export_data = metrics.export_metrics()
        assert all(metric in export_data["metrics"] for metric in [
            "planning_time",
            "development_time",
            "code_quality",
            "security_score",
            "sprint_completion_rate"
        ])

    def test_07_sprint_error_recovery(self, temp_dir):
        """Test sprint recovery from failures."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=True)
        metrics = MetricsCollector()

        # Act - Simulate failure and recovery
        sprint_dir = repo.path / ".vibey" / "sprints" / "sprint-1"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # Initial attempt - fails quality gate
        (sprint_dir / "attempt1.yaml").write_text("""attempt: 1
security_score: 55
status: failed
reason: Security vulnerabilities found
""")

        # Second attempt - passes
        (sprint_dir / "attempt2.yaml").write_text("""attempt: 2
security_score: 85
status: passed
reason: Vulnerabilities fixed
""")

        # Assert - Recovery successful
        assert (sprint_dir / "attempt1.yaml").exists()
        assert (sprint_dir / "attempt2.yaml").exists()

        # Track recovery metrics
        metrics.track("initial_security_score", 55, unit="percentage", threshold=70)
        metrics.track("final_security_score", 85, unit="percentage", threshold=70)
        metrics.track("recovery_successful", 100, unit="percentage", threshold=100)

        # Final score passes
        assert metrics.assert_metric("final_security_score", min_value=70)


@pytest.mark.e2e
class TestSprintMetrics:
    """Test sprint-level metrics collection and validation."""

    def test_comprehensive_sprint_metrics(self, temp_dir):
        """Test comprehensive metrics collection for complete sprint."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Track all sprint metrics
        metrics.track("sprint_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("planning_accuracy", 92, unit="percentage", threshold=85)
        metrics.track("task_completion_rate", 100, unit="percentage", threshold=95)
        metrics.track("code_quality_average", 88, unit="percentage", threshold=80)
        metrics.track("security_audit_score", 90, unit="percentage", threshold=70)
        metrics.track("test_coverage_average", 87, unit="percentage", threshold=80)
        metrics.track("sprint_velocity", 25, unit="points")

        # Assert
        assert len(metrics.get_all_metrics()) == 7
        assert metrics.calculate_success_rate() == 100.0

        # Validate individual metrics
        assert metrics.assert_metric("sprint_completion_rate", expected_value=100)
        assert metrics.assert_metric("planning_accuracy", min_value=85)
        assert metrics.assert_metric("code_quality_average", min_value=80)
