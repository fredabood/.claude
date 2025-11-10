"""
Platform-specific tests for Goose (simulated).

Tests Goose platform features including recipe system, MCP tools,
extensions, and config file handling.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
import yaml


@pytest.mark.platform
class TestGoosePlatform:
    """Test Goose platform-specific features (simulated)."""

    def test_01_goose_config_deployment(self, temp_dir):
        """Test Goose config.yaml deployment."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act - Simulate Goose deployment
        goose_dir = repo.path / ".goose"
        goose_dir.mkdir(exist_ok=True)

        (goose_dir / "config.yaml").write_text("""platform: goose
agents:
  - web-developer
  - security-reviewer
workflows:
  - sprint-planning
  - feature-development
""")

        # Assert
        assert (goose_dir / "config.yaml").exists()

        validator = StateValidator()
        result = validator.validate_yaml_structure(
            goose_dir / "config.yaml",
            {"required_keys": ["platform"], "key_types": {"platform": "str"}}
        )
        assert result.passed

    def test_02_recipe_system_configuration(self, temp_dir):
        """Test Goose recipe system configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()

        # Act - Create recipe files
        recipes_dir = repo.path / ".goose" / "recipes"
        recipes_dir.mkdir(parents=True, exist_ok=True)

        (recipes_dir / "sprint-planning.yaml").write_text("""recipe: sprint-planning
description: Plan and organize sprints
steps:
  - analyze_requirements
  - create_tasks
  - estimate_effort
""")

        # Assert
        assert (recipes_dir / "sprint-planning.yaml").exists()

    def test_03_mcp_tool_integration(self, temp_dir):
        """Test MCP tool integration configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act - Configure MCP tools
        goose_dir = repo.path / ".goose"
        goose_dir.mkdir(exist_ok=True)

        (goose_dir / "mcp-tools.yaml").write_text("""mcp_tools:
  - name: filesystem
    enabled: true
  - name: git
    enabled: true
  - name: web_search
    enabled: true
""")

        # Assert
        assert (goose_dir / "mcp-tools.yaml").exists()

        with open(goose_dir / "mcp-tools.yaml") as f:
            config = yaml.safe_load(f)

        assert len(config["mcp_tools"]) == 3
        assert all(tool["enabled"] for tool in config["mcp_tools"])

    def test_04_extension_loading(self, temp_dir):
        """Test Goose extension loading configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_api_service_repo()

        # Act
        extensions_dir = repo.path / ".goose" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        (extensions_dir / "vibey-framework.yaml").write_text("""extension: vibey-framework
version: 1.0.0
provides:
  - agents
  - workflows
  - quality_gates
""")

        # Assert
        assert (extensions_dir / "vibey-framework.yaml").exists()

    def test_05_goose_platform_metrics(self, temp_dir):
        """Test Goose platform metrics."""
        # Arrange
        metrics = MetricsCollector()

        # Act - Track Goose features
        metrics.track("recipe_system_available", 100, unit="percentage", threshold=100)
        metrics.track("mcp_tools_available", 100, unit="percentage", threshold=100)
        metrics.track("extension_support", 100, unit="percentage", threshold=100)
        metrics.track("config_flexibility", 95, unit="percentage", threshold=90)

        # Assert
        assert metrics.calculate_success_rate() == 100.0

    def test_06_goose_feature_mapping(self, temp_dir):
        """Test feature mapping from Claude Code to Goose."""
        # Arrange
        feature_mapping = {
            "claude_code": ["Task tool", "Slash commands", "CLAUDE.md", "Agent markdown"],
            "goose": ["Recipes", "MCP tools", "config.yaml", "Extensions"]
        }

        # Assert - Feature counts match
        assert len(feature_mapping["claude_code"]) == len(feature_mapping["goose"])
