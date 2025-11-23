"""
Platform-specific tests for Continue.dev adapter.

Tests Continue adapter functionality including context generation,
settings generation, and export capabilities.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.adapters.continuedev import ContinueAdapter


@pytest.fixture
def mock_agent():
    """Create a mock agent definition."""
    agent = MagicMock()
    agent.id = "test-agent"
    agent.name = "Test Agent"
    agent.description = "A test agent for unit testing"
    agent.triggers = ["test", "testing"]
    return agent


@pytest.fixture
def mock_workflow():
    """Create a mock workflow definition."""
    workflow = MagicMock()
    workflow.id = "test-workflow"
    workflow.name = "Test Workflow"
    workflow.description = "A test workflow for unit testing"
    workflow.steps = ["step1", "step2"]
    workflow.estimated_duration = "1 hour"
    return workflow


@pytest.fixture
def adapter():
    """Create a ContinueAdapter instance with real project root."""
    # Use real project root so discovery finds actual agents/workflows
    return ContinueAdapter(Path(__file__).parent.parent.parent)


@pytest.mark.platform
class TestContinueAdapter:
    """Test Continue.dev adapter functionality."""

    def test_get_platform_name(self, adapter):
        """Test platform name is correct."""
        assert adapter.get_platform_name() == "continue"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test deployment directory path."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".continue"

    def test_supports_feature_agents(self, adapter):
        """Test that agents feature is supported."""
        assert adapter.supports_feature("agents") is True

    def test_supports_feature_workflows(self, adapter):
        """Test that workflows feature is supported."""
        assert adapter.supports_feature("workflows") is True

    def test_supports_feature_mcp(self, adapter):
        """Test that MCP feature is supported."""
        assert adapter.supports_feature("mcp") is True

    def test_supports_feature_unknown(self, adapter):
        """Test that unknown features are not supported."""
        assert adapter.supports_feature("unknown_feature") is False

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert ".continuerc.yaml" in required
        assert "CONTINUE.md" in required

    def test_export_creates_files(self, adapter, tmp_path):
        """Test that export creates all required files."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert result.success is True
        assert (output_dir / ".continuerc.yaml").exists()
        assert (output_dir / "CONTINUE.md").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / ".checksums.json").exists()

    def test_export_result_counts(self, adapter, tmp_path):
        """Test that export result has correct counts."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        # Uses real discovery - should find agents and workflows
        assert result.success is True
        assert result.context.agents_count > 0
        assert result.context.workflows_count > 0
        assert len(result.files_created) == 4

    def test_export_checksums_generated(self, adapter, tmp_path):
        """Test that checksums are generated for drift detection."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert ".continuerc.yaml" in result.checksums
        assert len(result.checksums[".continuerc.yaml"]) == 16  # SHA256 truncated

    def test_validate_deployment_success(self, adapter, tmp_path):
        """Test deployment validation passes for valid deployment."""
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        is_valid, errors = adapter.validate_deployment(output_dir)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_deployment_missing_files(self, adapter, tmp_path):
        """Test deployment validation fails for missing files."""
        output_dir = tmp_path / "empty"
        output_dir.mkdir()

        is_valid, errors = adapter.validate_deployment(output_dir)
        assert is_valid is False
        assert len(errors) > 0


@pytest.mark.platform
class TestContinueContextGenerator:
    """Test Continue.dev context generator."""

    def test_build_context_header(self, tmp_path):
        """Test context file header generation."""
        from vibey.adapters.continuedev.context_generator import ContinueContextGenerator

        # Use real project root
        project_root = Path(__file__).parent.parent.parent
        generator = ContinueContextGenerator(project_root)
        result = generator.generate()

        assert "# Vibey Agent Framework" in result.content

    def test_build_agent_section(self, tmp_path):
        """Test agent section generation."""
        from vibey.adapters.continuedev.context_generator import ContinueContextGenerator

        project_root = Path(__file__).parent.parent.parent
        generator = ContinueContextGenerator(project_root)
        result = generator.generate()

        # Should contain real agents
        assert result.agents_count > 0
        assert "vibey_" in result.content

    def test_build_workflow_section(self, tmp_path):
        """Test workflow section generation."""
        from vibey.adapters.continuedev.context_generator import ContinueContextGenerator

        project_root = Path(__file__).parent.parent.parent
        generator = ContinueContextGenerator(project_root)
        result = generator.generate()

        # Should contain real workflows
        assert result.workflows_count > 0
        assert "vibey_workflow_" in result.content


@pytest.mark.platform
class TestContinueSettingsGenerator:
    """Test Continue.dev settings generator."""

    def test_build_mcp_config(self, tmp_path):
        """Test MCP server configuration generation."""
        from vibey.adapters.continuedev.settings_generator import ContinueSettingsGenerator

        project_root = Path(__file__).parent.parent.parent
        generator = ContinueSettingsGenerator(project_root)
        result = generator.generate()

        # Content is YAML string containing mcpServers
        assert "mcpServers" in result.content

    def test_build_prompts(self, tmp_path):
        """Test prompts configuration generation."""
        from vibey.adapters.continuedev.settings_generator import ContinueSettingsGenerator

        project_root = Path(__file__).parent.parent.parent
        generator = ContinueSettingsGenerator(project_root)
        result = generator.generate()

        # Settings should be generated
        assert result.content is not None
        assert result.checksum is not None
        assert result.mcp_servers >= 1
