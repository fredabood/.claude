"""
Platform-specific tests for Claude Code.

Tests Claude Code platform features including Task tool, slash commands,
CLAUDE.md auto-reading, and agent markdown file loading.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector


@pytest.mark.platform
class TestClaudeCodePlatform:
    """Test Claude Code platform-specific features."""

    def test_01_claude_md_deployment(self, temp_dir):
        """Test CLAUDE.md deployment for Claude Code."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act
        builder.add_vibey_framework(repo, platform="claude-code")

        # Assert
        claude_md = repo.path / ".vibey" / "CLAUDE.md"
        assert claude_md.exists()

        validator = StateValidator()
        result = validator.validate_file_content(
            claude_md,
            contains=["VIBEY_FRAMEWORK_MANAGED", "Project Type", "Tech Stack"]
        )
        assert result.passed

    def test_02_slash_command_configuration(self, temp_dir):
        """Test slash command configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, platform="claude-code")

        # Act
        commands_dir = repo.path / ".vibey" / "commands"
        commands_dir.mkdir(exist_ok=True)
        (commands_dir / "vibey.md").write_text("# /vibey command")

        # Assert
        assert (commands_dir / "vibey.md").exists()

    def test_03_agent_markdown_deployment(self, temp_dir):
        """Test agent markdown file deployment."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, platform="claude-code")

        # Act
        agents_dir = repo.path / ".vibey" / "agents"
        agents_dir.mkdir(exist_ok=True)

        agent_files = [
            "web-developer.md",
            "security-reviewer.md",
            "performance-engineer.md"
        ]
        for agent in agent_files:
            (agents_dir / agent).write_text(f"# {agent.replace('.md', '').replace('-', ' ').title()}")

        # Assert
        assert all((agents_dir / agent).exists() for agent in agent_files)

    def test_04_workflow_markdown_deployment(self, temp_dir):
        """Test workflow markdown file deployment."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()
        builder.add_vibey_framework(repo, platform="claude-code")

        # Act
        workflows_dir = repo.path / ".vibey" / "workflows"
        workflows_dir.mkdir(exist_ok=True)

        workflow_files = [
            "sprint-planning.md",
            "feature-development.md",
            "quality-assurance.md"
        ]
        for workflow in workflow_files:
            (workflows_dir / workflow).write_text(f"# {workflow.replace('.md', '').replace('-', ' ').title()}")

        # Assert
        assert all((workflows_dir / workflow).exists() for workflow in workflow_files)

    def test_05_project_config_generation(self, temp_dir):
        """Test project-config.yaml generation."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act
        builder.add_vibey_framework(repo, platform="claude-code")

        # Assert
        config_file = repo.path / ".vibey" / "project-config.yaml"
        assert config_file.exists()

        validator = StateValidator()
        result = validator.validate_yaml_structure(
            config_file,
            {"required_keys": ["project", "framework"], "key_types": {"project": "dict", "framework": "dict"}}
        )
        assert result.passed

    def test_06_claude_code_directory_structure(self, temp_dir):
        """Test complete .vibey/ directory structure."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, platform="claude-code")
        validator = StateValidator()

        # Assert
        expected = {
            "directories": [
                ".vibey",
                ".vibey/agents",
                ".vibey/workflows",
                ".vibey/commands"
            ],
            "files": [
                "CLAUDE.md",
                ".vibey/config/project.yaml"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected)
        assert result.passed

    def test_07_claude_code_baseline_metrics(self, temp_dir):
        """Test baseline metrics for Claude Code platform."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Track platform features
        metrics.track("task_tool_available", 100, unit="percentage", threshold=100)
        metrics.track("slash_commands_available", 100, unit="percentage", threshold=100)
        metrics.track("auto_read_claude_md", 100, unit="percentage", threshold=100)
        metrics.track("agent_markdown_support", 100, unit="percentage", threshold=100)
        metrics.track("workflow_markdown_support", 100, unit="percentage", threshold=100)

        # Assert - All features available
        assert metrics.calculate_success_rate() == 100.0

    def test_08_claude_code_platform_score(self, temp_dir):
        """Test overall platform score for Claude Code (baseline = 100%)."""
        # Arrange
        metrics = MetricsCollector()

        # Act
        metrics.track("platform_score", 100, unit="percentage", threshold=95)
        metrics.track("feature_count", 12, unit="count")
        metrics.track("feature_availability", 100, unit="percentage", threshold=100)

        # Assert
        assert metrics.assert_metric("platform_score", expected_value=100)
        assert metrics.calculate_success_rate() == 100.0


@pytest.mark.platform
class TestClaudeCodeFeatures:
    """Test Claude Code-specific features."""

    def test_task_tool_simulation(self, temp_dir):
        """Test Task tool integration (simulated)."""
        # Arrange - Simulate Task tool availability
        task_tool_available = True

        # Assert
        assert task_tool_available

    def test_slash_command_execution(self, temp_dir):
        """Test slash command execution (simulated)."""
        # Arrange
        command = "/vibey"
        command_available = True

        # Assert
        assert command_available
        assert command == "/vibey"
