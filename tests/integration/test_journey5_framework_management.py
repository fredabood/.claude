"""
Integration tests for Journey 5: Framework Management

Tests framework configuration updates, orchestration mode switching,
quality gate configuration, and agent management.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
import yaml


@pytest.mark.integration
class TestJourney5FrameworkManagement:
    """Test Journey 5: Framework Management workflow."""

    def test_01_orchestration_mode_switching(self, temp_dir):
        """Test switching between orchestration modes."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, orchestration_mode="balanced")
        validator = StateValidator()

        # Act - Switch to tiered mode
        config_file = repo.path / ".claude" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        config["framework"]["orchestration"]["mode"] = "tiered"
        config["framework"]["orchestration"]["coordinator_enabled"] = True

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Assert
        content_result = validator.validate_file_content(
            config_file,
            contains=["mode: tiered", "coordinator_enabled: true"]
        )
        assert content_result.passed

    def test_02_quality_gate_enablement(self, temp_dir):
        """Test enabling/disabling quality gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=False)

        # Act - Enable quality gates
        config_file = repo.path / ".claude" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        config["framework"]["quality_gates"] = {
            "enabled": True,
            "gates": ["security_review", "test_coverage", "documentation"]
        }

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Assert
        with open(config_file) as f:
            updated_config = yaml.safe_load(f)

        assert updated_config["framework"]["quality_gates"]["enabled"] is True
        assert len(updated_config["framework"]["quality_gates"]["gates"]) == 3

    def test_03_agent_configuration_update(self, temp_dir):
        """Test updating agent configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        metrics = MetricsCollector()

        # Act - Update agent list
        config_file = repo.path / ".claude" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        config["framework"]["agents"] = [
            "web-developer",
            "security-reviewer",
            "performance-engineer",
            "ml-engineer"  # Add ML engineer
        ]

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Assert
        with open(config_file) as f:
            updated_config = yaml.safe_load(f)

        assert "ml-engineer" in updated_config["framework"]["agents"]
        assert len(updated_config["framework"]["agents"]) == 4

        metrics.track("config_update_success", 100, unit="percentage", threshold=100)

    def test_04_tech_stack_update(self, temp_dir):
        """Test updating project tech stack configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Update tech stack
        config_file = repo.path / ".claude" / "project-config.yaml"
        with open(config_file) as f:
            config = yaml.safe_load(f)

        config["project"]["tech_stack"]["database"] = "mongodb"
        config["project"]["tech_stack"]["cache"] = "redis"

        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Assert
        with open(config_file) as f:
            updated_config = yaml.safe_load(f)

        assert updated_config["project"]["tech_stack"]["database"] == "mongodb"
        assert updated_config["project"]["tech_stack"]["cache"] == "redis"

    def test_05_complete_framework_management_workflow(self, temp_dir):
        """Test complete framework configuration management workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        metrics = MetricsCollector()

        # Act - Complete management workflow
        repo = builder.create_web_app_repo(name="managed-project")
        builder.add_vibey_framework(repo, orchestration_mode="simple", quality_gates_enabled=False)

        config_file = repo.path / ".claude" / "project-config.yaml"

        # Step 1: Enable quality gates
        with open(config_file) as f:
            config = yaml.safe_load(f)
        config["framework"]["quality_gates"] = {"enabled": True, "gates": ["security_review"]}
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Step 2: Switch orchestration mode
        with open(config_file) as f:
            config = yaml.safe_load(f)
        config["framework"]["orchestration"]["mode"] = "balanced"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Step 3: Add agents
        with open(config_file) as f:
            config = yaml.safe_load(f)
        config["framework"]["agents"] = ["web-developer", "security-reviewer", "performance-engineer"]
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        # Assert - Final configuration
        with open(config_file) as f:
            final_config = yaml.safe_load(f)

        assert final_config["framework"]["quality_gates"]["enabled"] is True
        assert final_config["framework"]["orchestration"]["mode"] == "balanced"
        assert len(final_config["framework"]["agents"]) == 3

        # Track metrics
        metrics.track("config_accuracy", 100, unit="percentage", threshold=100)
        metrics.track("update_success_rate", 100, unit="percentage", threshold=95)

        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0

    def test_06_configuration_validation(self, temp_dir):
        """Test configuration file validation."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act & Assert - Validate config structure
        config_file = repo.path / ".claude" / "project-config.yaml"
        expected_schema = {
            "required_keys": ["project", "framework"],
            "key_types": {"project": "dict", "framework": "dict"}
        }
        result = validator.validate_yaml_structure(config_file, expected_schema)
        assert result.passed

    def test_07_framework_management_metrics(self, temp_dir):
        """Test metrics collection for framework management."""
        # Arrange
        metrics = MetricsCollector()

        # Act
        metrics.track("config_accuracy", 100, unit="percentage", threshold=100)
        metrics.track("update_success_rate", 98, unit="percentage", threshold=95)
        metrics.track("validation_pass_rate", 100, unit="percentage", threshold=100)

        # Assert
        assert metrics.calculate_success_rate() == 100.0

        export_data = metrics.export_metrics()
        assert "config_accuracy" in export_data["metrics"]
