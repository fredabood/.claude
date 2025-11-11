"""
Integration tests for Journey 5: Framework Management

Tests framework configuration updates, orchestration mode switching,
quality gate configuration, and agent management.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
from tests.utils.config_loader import ConfigLoader
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
        config_loader = ConfigLoader(repo.path)

        # Act - Switch to tiered mode (modular config)
        framework_file = repo.path / ".vibey" / "config" / "framework.yaml"
        with open(framework_file) as f:
            config = yaml.safe_load(f)

        config["framework"]["orchestration_mode"] = "tiered"
        config["framework"]["coordinator_enabled"] = True

        with open(framework_file, 'w') as f:
            yaml.dump(config, f)

        # Assert - Verify change using ConfigLoader
        config_loader = ConfigLoader(repo.path)  # Reload
        assert config_loader.get_orchestration_mode() == "tiered"

    def test_02_quality_gate_enablement(self, temp_dir):
        """Test enabling/disabling quality gates."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo, quality_gates_enabled=False)

        # Act - Enable quality gates (modular config)
        gates_file = repo.path / ".vibey" / "config" / "quality-gates.yaml"
        with open(gates_file) as f:
            config = yaml.safe_load(f)

        config["quality_gates"]["enabled"] = True
        config["quality_gates"]["gates"] = ["security_review", "test_coverage", "documentation"]

        with open(gates_file, 'w') as f:
            yaml.dump(config, f)

        # Assert - Verify using ConfigLoader
        config_loader = ConfigLoader(repo.path)
        assert config_loader.get_quality_gates_enabled() is True
        gates_config = config_loader.load_quality_gates_config()
        assert len(gates_config["quality_gates"]["gates"]) == 3

    def test_03_agent_configuration_update(self, temp_dir):
        """Test updating agent configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        metrics = MetricsCollector()

        # Act - Update agent list (modular config)
        agents_file = repo.path / ".vibey" / "config" / "agents.yaml"
        with open(agents_file) as f:
            config = yaml.safe_load(f)

        config["agents"]["enabled"] = [
            "web-developer",
            "security-reviewer",
            "performance-engineer",
            "ml-engineer"  # Add ML engineer
        ]

        with open(agents_file, 'w') as f:
            yaml.dump(config, f)

        # Assert - Verify using ConfigLoader
        config_loader = ConfigLoader(repo.path)
        agents_config = config_loader.load_agents_config()
        assert "ml-engineer" in agents_config["agents"]["enabled"]
        assert len(agents_config["agents"]["enabled"]) == 4

        metrics.track("config_update_success", 100, unit="percentage", threshold=100)

    def test_04_tech_stack_update(self, temp_dir):
        """Test updating project tech stack configuration."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Update tech stack (modular config)
        project_file = repo.path / ".vibey" / "config" / "project.yaml"
        with open(project_file) as f:
            config = yaml.safe_load(f)

        config["project"]["tech_stack"]["database"] = "mongodb"
        config["project"]["tech_stack"]["cache"] = "redis"

        with open(project_file, 'w') as f:
            yaml.dump(config, f)

        # Assert - Verify using ConfigLoader
        config_loader = ConfigLoader(repo.path)
        assert config_loader.get("project.tech_stack.database") == "mongodb"
        assert config_loader.get("project.tech_stack.cache") == "redis"

    def test_05_complete_framework_management_workflow(self, temp_dir):
        """Test complete framework configuration management workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        metrics = MetricsCollector()

        # Act - Complete management workflow (modular configs)
        repo = builder.create_web_app_repo(name="managed-project")
        builder.add_vibey_framework(repo, orchestration_mode="simple", quality_gates_enabled=False)

        # Step 1: Enable quality gates
        gates_file = repo.path / ".vibey" / "config" / "quality-gates.yaml"
        with open(gates_file) as f:
            config = yaml.safe_load(f)
        config["quality_gates"]["enabled"] = True
        config["quality_gates"]["gates"] = ["security_review"]
        with open(gates_file, 'w') as f:
            yaml.dump(config, f)

        # Step 2: Switch orchestration mode
        framework_file = repo.path / ".vibey" / "config" / "framework.yaml"
        with open(framework_file) as f:
            config = yaml.safe_load(f)
        config["framework"]["orchestration_mode"] = "balanced"
        with open(framework_file, 'w') as f:
            yaml.dump(config, f)

        # Step 3: Add agents
        agents_file = repo.path / ".vibey" / "config" / "agents.yaml"
        with open(agents_file) as f:
            config = yaml.safe_load(f)
        config["agents"]["enabled"] = ["web-developer", "security-reviewer", "performance-engineer"]
        with open(agents_file, 'w') as f:
            yaml.dump(config, f)

        # Assert - Final configuration using ConfigLoader
        config_loader = ConfigLoader(repo.path)
        assert config_loader.get_quality_gates_enabled() is True
        assert config_loader.get_orchestration_mode() == "balanced"
        agents_config = config_loader.load_agents_config()
        assert len(agents_config["agents"]["enabled"]) == 3

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

        # Act & Assert - Validate modular config structures
        project_file = repo.path / ".vibey" / "config" / "project.yaml"
        expected_project_schema = {
            "required_keys": ["project"],
            "key_types": {"project": "dict"}
        }
        result = validator.validate_yaml_structure(project_file, expected_project_schema)
        assert result.passed

        framework_file = repo.path / ".vibey" / "config" / "framework.yaml"
        expected_framework_schema = {
            "required_keys": ["framework"],
            "key_types": {"framework": "dict"}
        }
        result = validator.validate_yaml_structure(framework_file, expected_framework_schema)
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
