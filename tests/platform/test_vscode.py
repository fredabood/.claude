"""
Platform-specific tests for VS Code adapter.

Tests VS Code adapter functionality including native MCP configuration,
context generation, and export capabilities.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.adapters.vscode import VSCodeAdapter


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
    """Create a VSCodeAdapter instance with real project root."""
    return VSCodeAdapter(Path(__file__).parent.parent.parent)


@pytest.mark.platform
class TestVSCodeAdapter:
    """Test VS Code adapter functionality."""

    def test_get_platform_name(self, adapter):
        """Test platform name is correct."""
        assert adapter.get_platform_name() == "vscode"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test deployment directory path."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".vscode"

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

    def test_supports_feature_resources(self, adapter):
        """Test that resources feature is supported (VS Code full MCP)."""
        assert adapter.supports_feature("resources") is True

    def test_supports_feature_prompts(self, adapter):
        """Test that prompts feature is supported (VS Code full MCP)."""
        assert adapter.supports_feature("prompts") is True

    def test_supports_feature_unknown(self, adapter):
        """Test that unknown features are not supported."""
        assert adapter.supports_feature("unknown_feature") is False

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "mcp.json" in required
        assert "VSCODE.md" in required

    @patch('vibey.adapters.vscode.adapter.AgentDiscovery')
    @patch('vibey.adapters.vscode.adapter.WorkflowDiscovery')
    def test_export_creates_files(self, mock_workflow_disc, mock_agent_disc,
                                   adapter, tmp_path, mock_agent, mock_workflow):
        """Test that export creates all required files."""
        mock_agent_disc.return_value.discover.return_value = [mock_agent]
        mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert result.success is True
        assert (output_dir / "mcp.json").exists()
        assert (output_dir / "VSCODE.md").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / ".checksums.json").exists()

    @patch('vibey.adapters.vscode.adapter.AgentDiscovery')
    @patch('vibey.adapters.vscode.adapter.WorkflowDiscovery')
    def test_export_mcp_config_format(self, mock_workflow_disc, mock_agent_disc,
                                       adapter, tmp_path, mock_agent, mock_workflow):
        """Test MCP config uses VS Code native format."""
        mock_agent_disc.return_value.discover.return_value = [mock_agent]
        mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        config_path = output_dir / "mcp.json"
        with open(config_path) as f:
            config = json.load(f)

        # VS Code uses "servers" not "mcpServers"
        assert "servers" in config
        assert "vibey" in config["servers"]
        assert "command" in config["servers"]["vibey"]
        assert "args" in config["servers"]["vibey"]

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

        assert "mcp.json" in result.checksums
        assert len(result.checksums["mcp.json"]) == 16

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
class TestVSCodeMCPConfig:
    """Test VS Code native MCP configuration specifics."""

    def test_mcp_config_uses_servers_key(self, tmp_path, mock_agent, mock_workflow):
        """Test that MCP config uses VS Code 'servers' format (not 'mcpServers')."""
        adapter = VSCodeAdapter(tmp_path)

        with patch('vibey.adapters.vscode.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.vscode.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                config_path = output_dir / "mcp.json"
                with open(config_path) as f:
                    config = json.load(f)

                # VS Code uses "servers" (different from Claude Desktop's "mcpServers")
                assert "servers" in config
                assert "mcpServers" not in config

    def test_mcp_config_vibey_server(self, tmp_path, mock_agent, mock_workflow):
        """Test Vibey MCP server configuration."""
        adapter = VSCodeAdapter(tmp_path)

        with patch('vibey.adapters.vscode.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.vscode.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                config_path = output_dir / "mcp.json"
                with open(config_path) as f:
                    config = json.load(f)

                vibey_config = config["servers"]["vibey"]
                assert vibey_config["command"] == "python"
                assert "-m" in vibey_config["args"]
                assert "framework.mcp.server" in vibey_config["args"]


@pytest.mark.platform
class TestVSCodeContext:
    """Test VS Code context file generation."""

    def test_context_contains_mcp_integration(self, tmp_path, mock_agent, mock_workflow):
        """Test that context mentions MCP integration."""
        adapter = VSCodeAdapter(tmp_path)

        with patch('vibey.adapters.vscode.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.vscode.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "VSCODE.md"
                content = context_path.read_text()

                assert "MCP" in content
                assert ".vscode/mcp.json" in content

    def test_context_lists_roadmap_tools(self, tmp_path, mock_agent, mock_workflow):
        """Test that context lists roadmap tools."""
        adapter = VSCodeAdapter(tmp_path)

        with patch('vibey.adapters.vscode.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.vscode.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "VSCODE.md"
                content = context_path.read_text()

                assert "vibey_roadmap_status" in content
                assert "vibey_start_task" in content
                assert "vibey_complete_task" in content

    def test_context_lists_agents(self, tmp_path):
        """Test that context lists discovered agents."""
        adapter = VSCodeAdapter(tmp_path)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "VSCODE.md"
        content = context_path.read_text()

        # Should contain real agents from framework
        assert "vibey_" in content  # Tool prefix
        assert "Agent" in content

    def test_context_lists_workflows(self, tmp_path):
        """Test that context lists discovered workflows."""
        # Use real project root for discovery
        project_root = Path(__file__).parent.parent.parent
        adapter = VSCodeAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "VSCODE.md"
        content = context_path.read_text()

        # Should contain real workflows from framework
        assert "vibey_workflow_" in content
        assert "Workflow" in content
