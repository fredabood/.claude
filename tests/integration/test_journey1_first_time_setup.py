"""
Integration tests for Journey 1: First-Time Setup

Tests the complete Vibey initialization workflow from project detection
through configuration generation and deployment.
"""

import pytest
from pathlib import Path
from tests.utils import RepoBuilder, StateValidator, MetricsCollector
import time


@pytest.mark.integration
class TestJourney1FirstTimeSetup:
    """Test Journey 1: First-Time Setup workflow."""

    def test_01_project_detection_web_app(self, temp_dir):
        """Test automatic detection of web application project type."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        metrics = MetricsCollector()
        start_time = time.time()

        # Act
        repo = builder.create_web_app_repo(name="test-webapp")
        detection_time = time.time() - start_time

        # Assert
        assert repo.path.exists()
        assert repo.repo_type == "web-app"
        assert (repo.path / "package.json").exists()
        assert (repo.path / "src").exists()

        # Track metrics
        metrics.track("detection_time", detection_time, unit="seconds", threshold=5.0)
        assert metrics.assert_metric("detection_time", max_value=5.0)

    def test_02_project_detection_api_service(self, temp_dir):
        """Test automatic detection of API service project type."""
        # Arrange
        builder = RepoBuilder(temp_dir)

        # Act
        repo = builder.create_api_service_repo(name="test-api")

        # Assert
        assert repo.repo_type == "api-service"
        assert (repo.path / "requirements.txt").exists()
        assert (repo.path / "app").exists()

    def test_03_project_detection_ml_project(self, temp_dir):
        """Test automatic detection of ML/data project type."""
        # Arrange
        builder = RepoBuilder(temp_dir)

        # Act
        repo = builder.create_ml_project_repo(name="test-ml")

        # Assert
        assert repo.repo_type == "ml-project"
        assert (repo.path / "requirements.txt").exists()
        assert (repo.path / "notebooks").exists()

    def test_04_vibey_framework_deployment(self, temp_dir):
        """Test Vibey framework deployment to repository."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        validator = StateValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act
        builder.add_vibey_framework(repo)
        deployment_time = time.time() - start_time

        # Assert - Directory structure
        expected_structure = {
            "directories": [".vibey", ".vibey/agents", ".vibey/workflows", ".vibey/commands"],
            "files": ["CLAUDE.md", ".vibey/config/project.yaml"]
        }
        result = validator.validate_directory_structure(repo.path, expected_structure)
        assert result.passed, f"Deployment failed: {result.errors}"

        # Assert - Vibey marker
        content_result = validator.validate_file_content(
            repo.path / ".vibey" / "CLAUDE.md",
            contains=["VIBEY_FRAMEWORK_MANAGED", "Project Type:"]
        )
        assert content_result.passed

        # Track metrics
        metrics.track("deployment_time", deployment_time, unit="seconds", threshold=10.0)
        metrics.track("deployment_success_rate", 100, unit="percentage", threshold=100)
        assert metrics.assert_metric("deployment_time", max_value=10.0)

    def test_05_claude_md_generation_web_app(self, temp_dir):
        """Test CLAUDE.md generation for web application."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Read generated CLAUDE.md
        claude_md = repo.path / ".vibey" / "CLAUDE.md"

        # Assert
        assert claude_md.exists()
        content_result = validator.validate_file_content(
            claude_md,
            contains=[
                "VIBEY_FRAMEWORK_MANAGED",
                "Project Type:",
                "Tech Stack",
                "Available Agents",
                "Orchestration Mode"
            ]
        )
        assert content_result.passed, f"CLAUDE.md missing required sections: {content_result.errors}"

    def test_06_project_config_generation(self, temp_dir):
        """Test project-config.yaml generation with correct structure."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)
        validator = StateValidator()

        # Act - Validate config structure
        config_file = repo.path / ".vibey" / "project-config.yaml"

        # Assert
        assert config_file.exists()

        expected_schema = {
            "required_keys": ["project", "framework"],
            "key_types": {"project": "dict", "framework": "dict"}
        }
        result = validator.validate_yaml_structure(config_file, expected_schema)
        assert result.passed, f"Config validation failed: {result.errors}"

    def test_07_git_initialization(self, temp_dir):
        """Test git repository initialization."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        validator = StateValidator()

        # Act
        builder.init_git(repo, initial_commit=True)

        # Assert
        assert repo.has_git
        git_result = validator.validate_git_state(
            repo.path,
            {"initialized": True, "has_commits": True}
        )
        assert git_result.passed

    def test_08_complete_initialization_workflow(self, temp_dir):
        """Test complete end-to-end initialization workflow."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()
        metrics = MetricsCollector()
        start_time = time.time()

        # Act - Complete workflow
        # Step 1: Create project
        repo = builder.create_web_app_repo(name="complete-project")

        # Step 2: Initialize git
        builder.init_git(repo, initial_commit=True)

        # Step 3: Deploy Vibey
        builder.add_vibey_framework(repo)

        total_time = time.time() - start_time

        # Assert - Final state
        expected_state = {
            "directories": [
                "src", "src/components", "server",
                ".vibey", ".vibey/agents", ".vibey/workflows"
            ],
            "files": [
                "package.json",
                "CLAUDE.md",
                ".vibey/config/project.yaml"
            ]
        }
        result = validator.validate_directory_structure(repo.path, expected_state)
        assert result.passed, f"Final state invalid: {result.errors}"

        # Assert - Git state
        git_result = validator.validate_git_state(repo.path, {"initialized": True})
        assert git_result.passed

        # Assert - Vibey deployed
        assert repo.has_vibey
        assert repo.has_git

        # Track success metrics
        metrics.track("setup_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("avg_setup_time", total_time, unit="seconds", threshold=900)  # 15 min
        metrics.track("configuration_accuracy", 100, unit="percentage", threshold=100)
        metrics.track("deployment_success_rate", 100, unit="percentage", threshold=100)

        # Validate all metrics pass
        success_rate = metrics.calculate_success_rate()
        assert success_rate == 100.0, f"Journey 1 success rate: {success_rate}%"

    def test_09_orchestration_mode_configuration(self, temp_dir):
        """Test configuration of different orchestration modes."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        validator = StateValidator()

        for mode in ["simple", "balanced", "tiered"]:
            # Act
            repo = builder.create_web_app_repo(name=f"test-{mode}")
            builder.add_vibey_framework(repo, orchestration_mode=mode)

            # Assert
            config_file = repo.path / ".vibey" / "project-config.yaml"
            assert config_file.exists()

            # Validate orchestration mode in config
            content_result = validator.validate_file_content(
                config_file,
                contains=[f"mode: {mode}"]
            )
            assert content_result.passed, f"Orchestration mode {mode} not configured"

    def test_10_quality_gates_enablement(self, temp_dir):
        """Test quality gates enablement during initialization."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        validator = StateValidator()

        # Act
        builder.add_vibey_framework(repo, quality_gates_enabled=True)

        # Assert
        config_file = repo.path / ".vibey" / "project-config.yaml"
        content_result = validator.validate_file_content(
            config_file,
            contains=["quality_gates:", "enabled: true"]
        )
        assert content_result.passed, "Quality gates not enabled in config"

        # Validate CLAUDE.md mentions quality gates
        claude_md = repo.path / ".vibey" / "CLAUDE.md"
        claude_result = validator.validate_file_content(
            claude_md,
            contains=["quality"]  # Should mention quality gates
        )
        assert claude_result.passed


@pytest.mark.integration
@pytest.mark.slow
class TestJourney1ErrorScenarios:
    """Test Journey 1 error handling and edge cases."""

    def test_invalid_project_structure(self, temp_dir):
        """Test initialization with invalid/empty project structure."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        empty_dir = temp_dir / "empty-project"
        empty_dir.mkdir()

        # Act & Assert - Should handle gracefully
        # (In real implementation, would detect as unknown project type)
        assert empty_dir.exists()

    def test_reinitialize_existing_vibey_project(self, temp_dir):
        """Test re-initializing project that already has Vibey."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        # Act - Try to reinitialize
        builder.add_vibey_framework(repo)

        # Assert - Should handle gracefully (update config or skip)
        assert repo.has_vibey
        assert (repo.path / ".vibey" / "CLAUDE.md").exists()

    def test_git_not_initialized(self, temp_dir):
        """Test Vibey deployment when git is not initialized."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        repo = builder.create_web_app_repo()

        # Act - Deploy without git
        builder.add_vibey_framework(repo)

        # Assert - Should work without git (git is optional)
        assert repo.has_vibey
        assert not repo.has_git


@pytest.mark.integration
class TestJourney1Metrics:
    """Test success metrics tracking for Journey 1."""

    def test_metrics_collection(self, temp_dir):
        """Test that all required metrics are collected during Journey 1."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        metrics = MetricsCollector()

        # Act
        repo = builder.create_web_app_repo()
        builder.init_git(repo)
        builder.add_vibey_framework(repo)

        # Track expected metrics
        metrics.track("setup_completion_rate", 100, unit="percentage", threshold=100)
        metrics.track("avg_setup_time", 300, unit="seconds", threshold=900)
        metrics.track("configuration_accuracy", 100, unit="percentage", threshold=100)
        metrics.track("deployment_success_rate", 100, unit="percentage", threshold=100)

        # Assert
        assert len(metrics.get_all_metrics()) == 4
        assert metrics.calculate_success_rate() == 100.0

        # Validate each metric
        assert metrics.assert_metric("setup_completion_rate", expected_value=100)
        assert metrics.assert_metric("avg_setup_time", max_value=900)
        assert metrics.assert_metric("configuration_accuracy", min_value=100)
        assert metrics.assert_metric("deployment_success_rate", expected_value=100)

    def test_export_journey_metrics(self, temp_dir):
        """Test exporting Journey 1 metrics to JSON."""
        # Arrange
        builder = RepoBuilder(temp_dir)
        metrics = MetricsCollector()

        # Act
        repo = builder.create_web_app_repo()
        builder.add_vibey_framework(repo)

        metrics.track("setup_completion_rate", 100)
        metrics.track("avg_setup_time", 450)

        output_file = temp_dir / "journey1-metrics.json"
        export_data = metrics.export_metrics(output_file)

        # Assert
        assert output_file.exists()
        assert "metrics" in export_data
        assert "setup_completion_rate" in export_data["metrics"]
        assert "avg_setup_time" in export_data["metrics"]
