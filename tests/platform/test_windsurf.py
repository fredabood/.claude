"""
Platform-specific tests for Windsurf adapter.

Tests Windsurf adapter functionality including MCP configuration,
context generation, and export capabilities.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.adapters.windsurf import WindsurfAdapter


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
    """Create a WindsurfAdapter instance with real project root."""
    return WindsurfAdapter(Path(__file__).parent.parent.parent)


@pytest.mark.platform
class TestWindsurfAdapter:
    """Test Windsurf adapter functionality."""

    def test_get_platform_name(self, adapter):
        """Test platform name is correct."""
        assert adapter.get_platform_name() == "windsurf"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test deployment directory path."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".windsurf"

    def test_supports_feature_agents(self, adapter):
        """Test that agents feature is supported."""
        assert adapter.supports_feature("agents") is True

    def test_supports_feature_workflows(self, adapter):
        """Test that workflows feature is supported."""
        assert adapter.supports_feature("workflows") is True

    def test_supports_feature_mcp(self, adapter):
        """Test that MCP feature is supported."""
        assert adapter.supports_feature("mcp") is True

    def test_supports_feature_roadmap(self, adapter):
        """Test that roadmap feature is supported."""
        assert adapter.supports_feature("roadmap") is True

    def test_supports_feature_unknown(self, adapter):
        """Test that unknown features are not supported."""
        assert adapter.supports_feature("unknown_feature") is False

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "mcp_config.json" in required
        assert "WINDSURF.md" in required

    @patch('vibey.adapters.windsurf.adapter.AgentDiscovery')
    @patch('vibey.adapters.windsurf.adapter.WorkflowDiscovery')
    def test_export_creates_files(self, mock_workflow_disc, mock_agent_disc,
                                   adapter, tmp_path, mock_agent, mock_workflow):
        """Test that export creates all required files."""
        mock_agent_disc.return_value.discover.return_value = [mock_agent]
        mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert result.success is True
        assert (output_dir / "mcp_config.json").exists()
        assert (output_dir / "WINDSURF.md").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / ".checksums.json").exists()

    @patch('vibey.adapters.windsurf.adapter.AgentDiscovery')
    @patch('vibey.adapters.windsurf.adapter.WorkflowDiscovery')
    def test_export_mcp_config_format(self, mock_workflow_disc, mock_agent_disc,
                                       adapter, tmp_path, mock_agent, mock_workflow):
        """Test MCP config uses Claude Desktop format."""
        mock_agent_disc.return_value.discover.return_value = [mock_agent]
        mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        config_path = output_dir / "mcp_config.json"
        with open(config_path) as f:
            config = json.load(f)

        # Windsurf uses Claude Desktop format (mcpServers, not servers)
        assert "mcpServers" in config
        assert "vibey" in config["mcpServers"]
        assert "command" in config["mcpServers"]["vibey"]
        assert "args" in config["mcpServers"]["vibey"]

    def test_export_result_counts(self, adapter, tmp_path):
        """Test that export result has correct counts."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        # Uses real discovery - check we found agents and workflows
        assert result.success is True
        assert result.agents_count > 0  # Should find real agents
        assert result.workflows_count > 0  # Should find real workflows
        assert len(result.files_created) == 4

    def test_export_checksums_generated(self, adapter, tmp_path):
        """Test that checksums are generated for drift detection."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert "mcp_config.json" in result.checksums
        assert len(result.checksums["mcp_config.json"]) == 16

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

    def test_context_contains_agents(self, adapter, tmp_path):
        """Test that context file lists agents."""
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "WINDSURF.md"
        content = context_path.read_text()

        # Should contain real agents from framework
        assert "vibey_" in content  # Tool prefix
        assert "## Available Agents" in content or "**" in content

    def test_context_contains_workflows(self, adapter, tmp_path):
        """Test that context file lists workflows."""
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "WINDSURF.md"
        content = context_path.read_text()

        # Should contain real workflows from framework
        assert "vibey_workflow_" in content
        assert "## Available Workflows" in content or "**" in content


@pytest.mark.platform
class TestWindsurfMCPConfig:
    """Test Windsurf MCP configuration specifics."""

    def test_mcp_config_matches_claude_desktop(self, tmp_path, mock_agent, mock_workflow):
        """Test that MCP config format matches Claude Desktop."""
        adapter = WindsurfAdapter(tmp_path)

        with patch('vibey.adapters.windsurf.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.windsurf.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                config_path = output_dir / "mcp_config.json"
                with open(config_path) as f:
                    config = json.load(f)

                # Verify Claude Desktop format compatibility
                assert "mcpServers" in config
                vibey_config = config["mcpServers"]["vibey"]
                assert "command" in vibey_config
                assert "args" in vibey_config
                assert vibey_config["command"] == "python"
                assert "-m" in vibey_config["args"]
