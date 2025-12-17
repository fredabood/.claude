"""
Tests for Goose adapter.

Tests the GooseAdapter platform adapter implementation.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from enum import Enum

from vibey.adapters.goose import GooseAdapter
from vibey.adapters.base import DeploymentResult


class MockProjectType(str, Enum):
    """Mock project type enum."""
    LIBRARY = "library"
    APPLICATION = "application"


class MockOrchestrationMode(str, Enum):
    """Mock orchestration mode enum."""
    SIMPLE = "simple"
    BALANCED = "balanced"
    TIERED = "tiered"


@dataclass
class MockProject:
    """Mock project config."""
    name: str = "TestProject"
    type: MockProjectType = MockProjectType.APPLICATION
    version: str = "1.0.0"
    description: str = "Test project description"


@dataclass
class MockTechStack:
    """Mock tech stack config."""
    languages: list = None
    frameworks: list = None
    databases: list = None
    infrastructure: list = None

    def __post_init__(self):
        self.languages = self.languages or ["Python"]
        self.frameworks = self.frameworks or []
        self.databases = self.databases or []
        self.infrastructure = self.infrastructure or []


@dataclass
class MockPaths:
    """Mock paths config."""
    source: str = "src"
    tests: str = "tests"
    docs: str = "docs"


@dataclass
class MockProjectConfig:
    """Mock project configuration."""
    project: MockProject = None
    tech_stack: MockTechStack = None
    paths: MockPaths = None

    def __post_init__(self):
        self.project = self.project or MockProject()
        self.tech_stack = self.tech_stack or MockTechStack()
        self.paths = self.paths or MockPaths()


@dataclass
class MockFrameworkSettings:
    """Mock framework settings."""
    orchestration_mode: MockOrchestrationMode = MockOrchestrationMode.BALANCED


@dataclass
class MockFramework:
    """Mock framework config."""
    framework: MockFrameworkSettings = None

    def __post_init__(self):
        self.framework = self.framework or MockFrameworkSettings()


@dataclass
class MockConfig:
    """Mock Vibey configuration."""
    project: MockProjectConfig = None
    framework: MockFramework = None

    def __post_init__(self):
        self.project = self.project or MockProjectConfig()
        self.framework = self.framework or MockFramework()


class TestGooseAdapter:
    """Test GooseAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return GooseAdapter()

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        return MockConfig()

    @pytest.fixture
    def source_dir(self, tmp_path):
        """Create source directory structure."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        return vibey_dir

    def test_get_platform_name(self, adapter):
        """Test get_platform_name returns correct name."""
        assert adapter.get_platform_name() == "goose"

    def test_get_deployment_dir_default(self, adapter):
        """Test deployment dir defaults to .goose in cwd."""
        deploy_dir = adapter.get_deployment_dir()
        assert deploy_dir.name == ".goose"

    def test_get_deployment_dir_custom_root(self, adapter, tmp_path):
        """Test deployment dir with custom project root."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".goose"

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "../.goosehints" in required

    def test_get_optional_files(self, adapter):
        """Test optional files list."""
        optional = adapter.get_optional_files()
        assert "extensions/" in optional
        assert "recipes/" in optional

    def test_supports_feature_workflows(self, adapter):
        """Test workflows feature is supported (via recipes)."""
        assert adapter.supports_feature("workflows") is True

    def test_supports_feature_templates(self, adapter):
        """Test templates feature has limited support."""
        assert adapter.supports_feature("templates") is True

    def test_supports_feature_roadmap(self, adapter):
        """Test roadmap feature has partial support."""
        # Roadmap is in partially_supported dict
        assert adapter.supports_feature("roadmap") is True

    def test_supports_feature_agents_unsupported(self, adapter):
        """Test agents feature is not directly supported."""
        assert adapter.supports_feature("agents") is False

    def test_supports_feature_quality_gates_unsupported(self, adapter):
        """Test quality-gates feature is not supported."""
        assert adapter.supports_feature("quality-gates") is False

    def test_generate_context_file(self, adapter, mock_config, tmp_path):
        """Test generating .goosehints."""
        output_path = tmp_path / ".goosehints"
        adapter.generate_context_file(mock_config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check required sections
        assert "TestProject" in content
        assert "application" in content
        assert "Python" in content
        assert "VIBEY_FRAMEWORK_MANAGED" in content
        assert "Goose" in content

    def test_generate_context_file_with_tech_stack(self, adapter, tmp_path):
        """Test context file with full tech stack."""
        config = MockConfig(
            project=MockProjectConfig(
                tech_stack=MockTechStack(
                    languages=["Python", "Go"],
                    frameworks=["Django"],
                    databases=["MySQL"],
                    infrastructure=["Kubernetes"],
                )
            )
        )
        output_path = tmp_path / ".goosehints"
        adapter.generate_context_file(config, output_path)

        content = output_path.read_text()
        assert "Python" in content
        assert "Go" in content
        assert "Django" in content
        assert "MySQL" in content
        assert "Kubernetes" in content

    def test_generate_context_file_includes_paths(self, adapter, mock_config, tmp_path):
        """Test context file includes project paths."""
        output_path = tmp_path / ".goosehints"
        adapter.generate_context_file(mock_config, output_path)

        content = output_path.read_text()
        # The mock config has paths configured
        assert "src" in content
        assert "tests" in content
        assert "docs" in content

    def test_validate_deployment_missing_dir(self, adapter, tmp_path):
        """Test validation fails when directory missing."""
        is_valid, errors = adapter.validate_deployment(tmp_path / "nonexistent")
        assert is_valid is False
        assert any("does not exist" in e for e in errors)

    def test_validate_deployment_missing_goosehints(self, adapter, tmp_path):
        """Test validation fails without .goosehints."""
        goose_dir = tmp_path / ".goose"
        goose_dir.mkdir()
        (goose_dir / "extensions").mkdir()
        (goose_dir / "recipes").mkdir()

        is_valid, errors = adapter.validate_deployment(goose_dir)
        assert is_valid is False
        assert any(".goosehints" in e for e in errors)

    def test_validate_deployment_empty_goosehints(self, adapter, tmp_path):
        """Test validation fails with empty .goosehints."""
        goose_dir = tmp_path / ".goose"
        goose_dir.mkdir()
        (goose_dir / "extensions").mkdir()
        (goose_dir / "recipes").mkdir()
        (tmp_path / ".goosehints").write_text("")

        is_valid, errors = adapter.validate_deployment(goose_dir)
        assert is_valid is False
        assert any("empty" in e for e in errors)

    def test_validate_deployment_missing_marker(self, adapter, tmp_path):
        """Test validation fails without Vibey marker."""
        goose_dir = tmp_path / ".goose"
        goose_dir.mkdir()
        (goose_dir / "extensions").mkdir()
        (goose_dir / "recipes").mkdir()
        (tmp_path / ".goosehints").write_text("# Project\nContent without marker")

        is_valid, errors = adapter.validate_deployment(goose_dir)
        assert is_valid is False
        assert any("marker" in e for e in errors)

    def test_validate_deployment_missing_subdirs(self, adapter, tmp_path):
        """Test validation fails without required subdirectories."""
        goose_dir = tmp_path / ".goose"
        goose_dir.mkdir()
        (tmp_path / ".goosehints").write_text("# Test\n<!-- VIBEY_FRAMEWORK_MANAGED -->")

        is_valid, errors = adapter.validate_deployment(goose_dir)
        assert is_valid is False
        assert any("extensions" in e or "recipes" in e for e in errors)

    def test_validate_deployment_success(self, adapter, tmp_path):
        """Test validation succeeds with valid deployment."""
        goose_dir = tmp_path / ".goose"
        goose_dir.mkdir()
        (goose_dir / "extensions").mkdir()
        (goose_dir / "recipes").mkdir()
        (tmp_path / ".goosehints").write_text("# Project\n\n<!-- VIBEY_FRAMEWORK_MANAGED -->")

        is_valid, errors = adapter.validate_deployment(goose_dir)
        assert is_valid is True
        assert errors == []

    def test_deploy_creates_directory(self, adapter, mock_config, source_dir):
        """Test deploy creates .goose directory."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        assert target.exists()
        assert target.is_dir()

    def test_deploy_creates_subdirectories(self, adapter, mock_config, source_dir):
        """Test deploy creates extensions and recipes directories."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        assert (target / "extensions").exists()
        assert (target / "recipes").exists()

    def test_deploy_generates_goosehints(self, adapter, mock_config, source_dir):
        """Test deploy creates .goosehints in project root."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        goosehints = source_dir.parent / ".goosehints"
        assert goosehints.exists()
        assert goosehints in result.files_created

    def test_deploy_clean_removes_existing(self, adapter, mock_config, source_dir):
        """Test deploy with clean=True removes existing."""
        target = source_dir.parent / ".goose"
        target.mkdir(parents=True)
        (target / "old_file.txt").write_text("old content")

        result = adapter.deploy(source_dir, mock_config, target, clean=True)

        assert not (target / "old_file.txt").exists()
        assert target in result.files_deleted

    def test_deploy_converts_workflows_to_recipes(self, adapter, mock_config, source_dir):
        """Test deploy converts workflows to recipes."""
        workflows_dir = source_dir.parent / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "test-workflow.md").write_text("# Test Workflow")

        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        assert (target / "recipes" / "test-workflow.md").exists()
        assert any("Workflows converted" in w for w in result.warnings)

    def test_deploy_creates_extensions_readme(self, adapter, mock_config, source_dir):
        """Test deploy creates README in extensions directory."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        readme = target / "extensions" / "README.md"
        assert readme.exists()
        assert "toolkit" in readme.read_text().lower()

    def test_deploy_warns_about_agents(self, adapter, mock_config, source_dir):
        """Test deploy warns that agents cannot be converted."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        assert any("agents" in w.lower() for w in result.warnings)

    def test_deploy_result_success(self, adapter, mock_config, source_dir):
        """Test successful deploy returns success result."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        assert result.success is True
        assert result.platform == "goose"
        assert result.validation_passed is True
        assert len(result.errors) == 0

    def test_deploy_result_has_duration(self, adapter, mock_config, source_dir):
        """Test deploy result has duration."""
        target = source_dir.parent / ".goose"
        result = adapter.deploy(source_dir, mock_config, target)

        assert result.duration_seconds >= 0

    def test_deploy_handles_exception(self, adapter, mock_config, source_dir):
        """Test deploy handles exceptions gracefully."""
        # Mock generate_context_file to raise exception
        with patch.object(adapter, 'generate_context_file', side_effect=RuntimeError("boom")):
            target = source_dir.parent / ".goose"
            result = adapter.deploy(source_dir, mock_config, target)

            assert result.success is False
            assert any("Deployment failed" in e or "boom" in str(e) for e in result.errors)

    def test_get_metadata(self, adapter):
        """Test adapter metadata."""
        metadata = adapter.get_metadata()

        assert metadata["platform"] == "goose"
        assert "adapter_version" in metadata
        assert "vibey_version" in metadata


class TestGooseAdapterIntegration:
    """Integration tests for GooseAdapter."""

    @pytest.fixture
    def full_project(self, tmp_path):
        """Create a full project structure."""
        # Create .vibey directory
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()

        # Create workflows directory
        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "sprint-planning.md").write_text("# Sprint Planning")
        (tmp_path / "workflows" / "code-review.md").write_text("# Code Review")

        return tmp_path

    def test_full_deployment(self, full_project):
        """Test complete deployment with workflows."""
        adapter = GooseAdapter()
        config = MockConfig()

        result = adapter.deploy(
            source_dir=full_project / ".vibey",
            config=config,
            clean=True,
        )

        assert result.success is True

        # Check deployment structure
        goose_dir = full_project / ".goose"
        assert goose_dir.exists()
        assert (goose_dir / "extensions").exists()
        assert (goose_dir / "recipes").exists()
        assert (full_project / ".goosehints").exists()

        # Check workflows converted to recipes
        assert (goose_dir / "recipes" / "sprint-planning.md").exists()
        assert (goose_dir / "recipes" / "code-review.md").exists()

    def test_deployment_validation_passes(self, full_project):
        """Test deployment passes validation."""
        adapter = GooseAdapter()
        config = MockConfig()

        # Deploy
        result = adapter.deploy(
            source_dir=full_project / ".vibey",
            config=config,
        )

        assert result.success is True
        assert result.validation_passed is True

        # Validate again independently
        is_valid, errors = adapter.validate_deployment(full_project / ".goose")
        assert is_valid is True

    def test_nested_workflows_converted(self, full_project):
        """Test nested workflow directories are converted."""
        adapter = GooseAdapter()
        config = MockConfig()

        # Create nested workflow
        nested = full_project / "workflows" / "nested"
        nested.mkdir()
        (nested / "deep-workflow.md").write_text("# Deep Workflow")

        result = adapter.deploy(
            source_dir=full_project / ".vibey",
            config=config,
        )

        assert result.success is True
        assert (full_project / ".goose" / "recipes" / "nested" / "deep-workflow.md").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
