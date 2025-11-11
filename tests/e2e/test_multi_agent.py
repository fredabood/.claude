"""
End-to-end tests for multi-agent orchestration.

Tests agent handoffs, coordinator routing, parallel execution,
and agent state management across complete workflows.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
import yaml


@pytest.mark.e2e
class TestMultiAgentOrchestration:
    """Test multi-agent orchestration in E2E workflows."""

    def test_01_sequential_agent_handoff(self, temp_dir):
        """Test sequential handoff between agents."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Create handoff chain: web-dev → security → docs
        handoff_dir = repo.path / ".vibey" / "handoffs"
        handoff_dir.mkdir(parents=True, exist_ok=True)

        # Handoff 1: Web Developer → Security Reviewer
        (handoff_dir / "1-webdev-to-security.md").write_text("""# Handoff: Web Developer → Security Reviewer

## Feature Completed
User authentication system

## Security Review Needed
- JWT implementation
- Password hashing
- Input validation

## Files to Review
- src/auth/login.ts
- src/auth/register.ts
""")

        # Handoff 2: Security Reviewer → Documentation Writer
        (handoff_dir / "2-security-to-docs.md").write_text("""# Handoff: Security Reviewer → Documentation Writer

## Security Review Complete
All security checks passed (Score: 88/100)

## Documentation Needed
- API authentication endpoints
- Security best practices
- Error handling

## Approved Files
- src/auth/login.ts (approved)
- src/auth/register.ts (approved)
""")

        # Assert - Handoff chain complete
        assert (handoff_dir / "1-webdev-to-security.md").exists()
        assert (handoff_dir / "2-security-to-docs.md").exists()

        validator = StateValidator()
        h1_result = validator.validate_file_content(
            handoff_dir / "1-webdev-to-security.md",
            contains=["Feature Completed", "Security Review Needed"]
        )
        assert h1_result.passed

    def test_02_parallel_agent_execution(self, temp_dir):
        """Test parallel execution of multiple agents."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo)

        # Act - Simulate parallel agent work
        agent_outputs = repo.path / ".vibey" / "agent-outputs"
        agent_outputs.mkdir(parents=True, exist_ok=True)

        # Security reviewer (parallel task 1)
        (agent_outputs / "security-review.md").write_text("""# Security Review
Started: 10:00
Completed: 10:15
Score: 85/100
""")

        # Performance engineer (parallel task 2)
        (agent_outputs / "performance-audit.md").write_text("""# Performance Audit
Started: 10:00
Completed: 10:12
Score: 92/100
""")

        # Documentation writer (parallel task 3)
        (agent_outputs / "docs-update.md").write_text("""# Documentation Update
Started: 10:00
Completed: 10:10
Coverage: 100%
""")

        # Assert - All executed in parallel (overlapping times)
        assert (agent_outputs / "security-review.md").exists()
        assert (agent_outputs / "performance-audit.md").exists()
        assert (agent_outputs / "docs-update.md").exists()

        # All started at same time
        files = list(agent_outputs.glob("*.md"))
        assert len(files) == 3

    def test_03_coordinator_routing_tiered_mode(self, temp_dir):
        """Test coordinator agent routing in tiered orchestration mode."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, orchestration_mode="tiered")

        # Act - Create coordinator routing decisions
        routing_dir = repo.path / ".vibey" / "routing"
        routing_dir.mkdir(parents=True, exist_ok=True)

        (routing_dir / "decisions.yaml").write_text("""routing_decisions:
  - request: "Implement user authentication"
    analysis: Complex feature requiring security review
    route_to:
      - web-developer
      - security-reviewer
    sequence: sequential

  - request: "Optimize database queries"
    analysis: Performance-focused task
    route_to:
      - performance-engineer
    sequence: single

  - request: "Add API documentation"
    analysis: Documentation task
    route_to:
      - docs-writer
    sequence: single
""")

        # Assert
        assert (routing_dir / "decisions.yaml").exists()

        with open(routing_dir / "decisions.yaml") as f:
            routing = yaml.safe_load(f)

        assert len(routing["routing_decisions"]) == 3
        assert routing["routing_decisions"][0]["sequence"] == "sequential"

    def test_04_agent_state_management(self, temp_dir):
        """Test agent state tracking across workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Track agent states
        state_dir = repo.path / ".vibey" / "agent-states"
        state_dir.mkdir(parents=True, exist_ok=True)

        (state_dir / "web-developer.yaml").write_text("""agent: web-developer
status: active
current_task: task-001
tasks_completed: 3
tasks_in_progress: 1
""")

        (state_dir / "security-reviewer.yaml").write_text("""agent: security-reviewer
status: waiting
current_task: null
tasks_completed: 2
tasks_in_progress: 0
waiting_for: web-developer
""")

        # Assert
        with open(state_dir / "web-developer.yaml") as f:
            webdev = yaml.safe_load(f)

        with open(state_dir / "security-reviewer.yaml") as f:
            security = yaml.safe_load(f)

        assert webdev["status"] == "active"
        assert security["status"] == "waiting"
        assert security["waiting_for"] == "web-developer"

    def test_05_handoff_template_validation(self, temp_dir):
        """Test validation of handoff templates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Create standardized handoff
        handoff_dir = repo.path / ".vibey" / "handoffs"
        handoff_dir.mkdir(parents=True, exist_ok=True)

        (handoff_dir / "standard-handoff.md").write_text("""# Handoff: Agent A → Agent B

## Context
Task description and background

## Work Completed
- Item 1
- Item 2

## Next Steps
- Action 1
- Action 2

## Files Changed
- file1.ts
- file2.ts

## Notes
Additional context
""")

        # Assert - Validate template structure
        result = validator.validate_file_content(
            handoff_dir / "standard-handoff.md",
            contains=[
                "Context",
                "Work Completed",
                "Next Steps",
                "Files Changed",
                "Notes"
            ]
        )
        assert result.passed

    def test_06_complete_multi_agent_workflow(self, temp_dir):
        """Test complete workflow involving multiple agents."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo(name="multi-agent-project")
        builder.init_git(repo, initial_commit=True)
        builder.add_vibey_framework(repo, orchestration_mode="balanced")
        metrics = MetricsCollector()

        # Act - Execute multi-agent workflow
        # Agent 1: Web Developer
        feature_file = repo.path / "src" / "feature.ts"
        feature_file.write_text("export const feature = {};")

        # Agent 2: Security Reviewer
        audit_dir = repo.path / ".vibey" / "audits" / "security"
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / "review.md").write_text("Score: 90/100")

        # Agent 3: Performance Engineer
        perf_dir = repo.path / ".vibey" / "audits" / "performance"
        perf_dir.mkdir(parents=True, exist_ok=True)
        (perf_dir / "report.md").write_text("Score: 88/100")

        # Agent 4: Documentation Writer
        (repo.path / "docs" / "feature.md").mkdir(parents=True, exist_ok=True)
        (repo.path / "docs" / "feature.md" / "../feature.md").write_text("# Feature Documentation")

        # Assert - All agent outputs present
        assert feature_file.exists()
        assert (audit_dir / "review.md").exists()
        assert (perf_dir / "report.md").exists()

        # Track multi-agent metrics
        metrics.track("agents_involved", 4, unit="count")
        metrics.track("handoffs_completed", 3, unit="count")
        metrics.track("coordination_success", 100, unit="percentage", threshold=95)

        assert metrics.assert_metric("coordination_success", min_value=95)


@pytest.mark.e2e
class TestOrchestrationModes:
    """Test different orchestration modes."""

    def test_simple_mode_explicit_routing(self, temp_dir):
        """Test simple orchestration mode with explicit agent selection."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, orchestration_mode="simple")

        # Act - Explicit agent selection
        config_file = repo.path / ".vibey" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["framework"]["orchestration"]["mode"] == "simple"

    def test_balanced_mode_pattern_matching(self, temp_dir):
        """Test balanced orchestration mode with pattern matching."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo, orchestration_mode="balanced")

        # Act
        config_file = repo.path / ".vibey" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["framework"]["orchestration"]["mode"] == "balanced"

    def test_tiered_mode_coordinator_enabled(self, temp_dir):
        """Test tiered orchestration mode with coordinator."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, orchestration_mode="tiered")

        # Act
        config_file = repo.path / ".vibey" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["framework"]["orchestration"]["mode"] == "tiered"
        assert config["framework"]["orchestration"].get("coordinator_enabled", False)
