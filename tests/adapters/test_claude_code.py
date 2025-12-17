"""
Tests for Claude Code adapter.

Tests the ClaudeCodeAdapter platform adapter implementation.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass
from enum import Enum

from vibey.adapters.claude_code import ClaudeCodeAdapter
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
class MockProjectConfig:
    """Mock project configuration."""
    project: MockProject = None
    tech_stack: MockTechStack = None

    def __post_init__(self):
        self.project = self.project or MockProject()
        self.tech_stack = self.tech_stack or MockTechStack()


@dataclass
class MockAgentConfig:
    """Mock agent configuration."""
    enabled: list = None

    def __post_init__(self):
        self.enabled = self.enabled or ["code-reviewer", "test-writer"]


@dataclass
class MockAgents:
    """Mock agents config."""
    agents: MockAgentConfig = None

    def __post_init__(self):
        self.agents = self.agents or MockAgentConfig()


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
    agents: MockAgents = None
    framework: MockFramework = None

    def __post_init__(self):
        self.project = self.project or MockProjectConfig()
        self.agents = self.agents or MockAgents()
        self.framework = self.framework or MockFramework()


class TestClaudeCodeAdapter:
    """Test ClaudeCodeAdapter class."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return ClaudeCodeAdapter()

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
        assert adapter.get_platform_name() == "claude-code"

    def test_get_deployment_dir_default(self, adapter):
        """Test deployment dir defaults to .claude in cwd."""
        deploy_dir = adapter.get_deployment_dir()
        assert deploy_dir.name == ".claude"

    def test_get_deployment_dir_custom_root(self, adapter, tmp_path):
        """Test deployment dir with custom project root."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".claude"

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "CLAUDE.md" in required

    def test_get_optional_files(self, adapter):
        """Test optional files list."""
        optional = adapter.get_optional_files()
        assert "agents/" in optional
        assert "workflows/" in optional
        assert "templates/" in optional
        assert "commands/" in optional

    def test_supports_feature_agents(self, adapter):
        """Test agents feature is supported."""
        assert adapter.supports_feature("agents") is True

    def test_supports_feature_workflows(self, adapter):
        """Test workflows feature is supported."""
        assert adapter.supports_feature("workflows") is True

    def test_supports_feature_quality_gates(self, adapter):
        """Test quality-gates feature is supported."""
        assert adapter.supports_feature("quality-gates") is True

    def test_supports_feature_roadmap(self, adapter):
        """Test roadmap feature is supported."""
        assert adapter.supports_feature("roadmap") is True

    def test_supports_feature_unknown(self, adapter):
        """Test unknown feature returns False."""
        assert adapter.supports_feature("unknown-feature") is False

    def test_generate_context_file(self, adapter, mock_config, tmp_path):
        """Test generating CLAUDE.md."""
        output_path = tmp_path / "CLAUDE.md"
        adapter.generate_context_file(mock_config, output_path)

        assert output_path.exists()
        content = output_path.read_text()

        # Check required sections
        assert "TestProject" in content
        assert "application" in content
        assert "Python" in content
        assert "VIBEY_FRAMEWORK_MANAGED" in content
        assert "code-reviewer" in content.lower() or "Code Reviewer" in content

    def test_generate_context_file_with_tech_stack(self, adapter, tmp_path):
        """Test context file with full tech stack."""
        config = MockConfig(
            project=MockProjectConfig(
                tech_stack=MockTechStack(
                    languages=["Python", "TypeScript"],
                    frameworks=["FastAPI", "React"],
                    databases=["PostgreSQL"],
                    infrastructure=["Docker", "AWS"],
                )
            )
        )
        output_path = tmp_path / "CLAUDE.md"
        adapter.generate_context_file(config, output_path)

        content = output_path.read_text()
        assert "Python" in content
        assert "TypeScript" in content
        assert "FastAPI" in content
        assert "PostgreSQL" in content
        assert "Docker" in content

    def test_validate_deployment_missing_dir(self, adapter, tmp_path):
        """Test validation fails when directory missing."""
        is_valid, errors = adapter.validate_deployment(tmp_path / "nonexistent")
        assert is_valid is False
        assert any("does not exist" in e for e in errors)

    def test_validate_deployment_missing_claude_md(self, adapter, tmp_path):
        """Test validation fails without CLAUDE.md."""
        tmp_path.mkdir(exist_ok=True)
        is_valid, errors = adapter.validate_deployment(tmp_path)
        assert is_valid is False
        assert any("CLAUDE.md" in e for e in errors)

    def test_validate_deployment_empty_claude_md(self, adapter, tmp_path):
        """Test validation fails with empty CLAUDE.md."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("")
        is_valid, errors = adapter.validate_deployment(tmp_path)
        assert is_valid is False
        assert any("empty" in e for e in errors)

    def test_validate_deployment_missing_marker(self, adapter, tmp_path):
        """Test validation fails without Vibey marker."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Project\nSome content without marker")
        is_valid, errors = adapter.validate_deployment(tmp_path)
        assert is_valid is False
        assert any("marker" in e for e in errors)

    def test_validate_deployment_success(self, adapter, tmp_path):
        """Test validation succeeds with valid deployment."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Project\n\n<!-- VIBEY_FRAMEWORK_MANAGED -->")
        is_valid, errors = adapter.validate_deployment(tmp_path)
        assert is_valid is True
        assert errors == []

    def test_deploy_creates_directory(self, adapter, mock_config, source_dir):
        """Test deploy creates .claude directory."""
        target = source_dir.parent / ".claude"
        result = adapter.deploy(source_dir, mock_config, target)

        assert target.exists()
        assert target.is_dir()

    def test_deploy_generates_claude_md(self, adapter, mock_config, source_dir):
        """Test deploy creates CLAUDE.md."""
        target = source_dir.parent / ".claude"
        result = adapter.deploy(source_dir, mock_config, target)

        claude_md = target / "CLAUDE.md"
        assert claude_md.exists()
        assert claude_md in result.files_created

    def test_deploy_clean_removes_existing(self, adapter, mock_config, source_dir):
        """Test deploy with clean=True removes existing."""
        target = source_dir.parent / ".claude"
        target.mkdir(parents=True)
        (target / "old_file.txt").write_text("old content")

        result = adapter.deploy(source_dir, mock_config, target, clean=True)

        assert not (target / "old_file.txt").exists()
        assert target in result.files_deleted

    def test_deploy_copies_agents_dir(self, adapter, mock_config, source_dir):
        """Test deploy copies agents directory."""
        agents_dir = source_dir.parent / "agents"
        agents_dir.mkdir()
        (agents_dir / "test-agent.md").write_text("# Test Agent")

        target = source_dir.parent / ".claude"
        result = adapter.deploy(source_dir, mock_config, target)

        assert (target / "agents" / "test-agent.md").exists()

    def test_deploy_copies_workflows_dir(self, adapter, mock_config, source_dir):
        """Test deploy copies workflows directory."""
        workflows_dir = source_dir.parent / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "test-workflow.md").write_text("# Test Workflow")

        target = source_dir.parent / ".claude"
        result = adapter.deploy(source_dir, mock_config, target)

        assert (target / "workflows" / "test-workflow.md").exists()

    def test_deploy_result_success(self, adapter, mock_config, source_dir):
        """Test successful deploy returns success result."""
        target = source_dir.parent / ".claude"
        result = adapter.deploy(source_dir, mock_config, target)

        assert result.success is True
        assert result.platform == "claude-code"
        assert result.validation_passed is True
        assert len(result.errors) == 0

    def test_deploy_result_has_duration(self, adapter, mock_config, source_dir):
        """Test deploy result has duration."""
        target = source_dir.parent / ".claude"
        result = adapter.deploy(source_dir, mock_config, target)

        assert result.duration_seconds >= 0

    def test_deploy_handles_exception(self, adapter, mock_config, source_dir):
        """Test deploy handles exceptions gracefully."""
        # Mock generate_context_file to raise exception
        with patch.object(adapter, 'generate_context_file', side_effect=RuntimeError("boom")):
            target = source_dir.parent / ".claude"
            result = adapter.deploy(source_dir, mock_config, target)

            assert result.success is False
            assert any("Deployment failed" in e or "boom" in str(e) for e in result.errors)

    def test_generate_mcp_config(self, adapter, tmp_path):
        """Test MCP config file generation."""
        mcp_path = adapter.generate_mcp_config(tmp_path)

        assert mcp_path.exists()
        assert mcp_path.name == ".mcp.json"

        config = json.loads(mcp_path.read_text())
        assert "mcpServers" in config
        assert "vibey" in config["mcpServers"]
        assert "command" in config["mcpServers"]["vibey"]
        assert "args" in config["mcpServers"]["vibey"]

    def test_get_metadata(self, adapter):
        """Test adapter metadata."""
        metadata = adapter.get_metadata()

        assert metadata["platform"] == "claude-code"
        assert "adapter_version" in metadata
        assert "vibey_version" in metadata


class TestClaudeCodeAdapterIntegration:
    """Integration tests for ClaudeCodeAdapter."""

    @pytest.fixture
    def full_project(self, tmp_path):
        """Create a full project structure."""
        # Create .vibey directory
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()

        # Create component directories
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / "code-reviewer.md").write_text("# Code Reviewer")

        (tmp_path / "workflows").mkdir()
        (tmp_path / "workflows" / "sprint-planning.md").write_text("# Sprint Planning")

        (tmp_path / "templates").mkdir()
        (tmp_path / "templates" / "feature.md").write_text("# Feature Template")

        return tmp_path

    def test_full_deployment(self, full_project):
        """Test complete deployment with all components."""
        adapter = ClaudeCodeAdapter()
        config = MockConfig()

        result = adapter.deploy(
            source_dir=full_project / ".vibey",
            config=config,
            clean=True,
        )

        assert result.success is True

        # Check all components deployed
        target = full_project / ".claude"
        assert (target / "CLAUDE.md").exists()
        assert (target / "agents" / "code-reviewer.md").exists()
        assert (target / "workflows" / "sprint-planning.md").exists()
        assert (target / "templates" / "feature.md").exists()

    def test_deployment_validation_passes(self, full_project):
        """Test deployment passes validation."""
        adapter = ClaudeCodeAdapter()
        config = MockConfig()

        # Deploy
        result = adapter.deploy(
            source_dir=full_project / ".vibey",
            config=config,
        )

        assert result.success is True
        assert result.validation_passed is True

        # Validate again independently
        is_valid, errors = adapter.validate_deployment(full_project / ".claude")
        assert is_valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
