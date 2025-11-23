"""
Platform-specific tests for Cursor adapter.

Tests Cursor adapter functionality including MCP configuration (mcpServers format),
.cursorrules generation, and context file generation.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.adapters.cursor import CursorAdapter


@pytest.fixture
def mock_agent():
    """Create a mock agent definition."""
    agent = MagicMock()
    agent.id = "test-agent"
    agent.name = "Test Agent"
    agent.description = "A test agent for unit testing"
    agent.triggers = {
        "keywords": ["test", "testing", "validate"],
        "contexts": [],
        "file_patterns": [],
        "priority": "medium"
    }
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
    """Create a CursorAdapter instance with real project root."""
    return CursorAdapter(Path(__file__).parent.parent.parent)


@pytest.mark.platform
class TestCursorAdapter:
    """Test Cursor adapter functionality."""

    def test_get_platform_name(self, adapter):
        """Test platform name is correct."""
        assert adapter.get_platform_name() == "cursor"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test deployment directory path."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".cursor"

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

    def test_supports_feature_rules(self, adapter):
        """Test that rules feature is supported (Cursor specific)."""
        assert adapter.supports_feature("rules") is True

    def test_supports_feature_unknown(self, adapter):
        """Test that unknown features are not supported."""
        assert adapter.supports_feature("unknown_feature") is False

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "mcp.json" in required
        assert "CURSOR.md" in required
        assert ".cursorrules" in required

    @patch('vibey.adapters.cursor.adapter.AgentDiscovery')
    @patch('vibey.adapters.cursor.adapter.WorkflowDiscovery')
    def test_export_creates_files(self, mock_workflow_disc, mock_agent_disc,
                                   adapter, tmp_path, mock_agent, mock_workflow):
        """Test that export creates all required files."""
        mock_agent_disc.return_value.discover.return_value = [mock_agent]
        mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert result.success is True
        assert (output_dir / "mcp.json").exists()
        assert (output_dir / "CURSOR.md").exists()
        # .cursorrules goes in project root (output_dir.parent), not in .cursor/
        assert (output_dir.parent / ".cursorrules").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / ".checksums.json").exists()

    @patch('vibey.adapters.cursor.adapter.AgentDiscovery')
    @patch('vibey.adapters.cursor.adapter.WorkflowDiscovery')
    def test_export_mcp_config_format(self, mock_workflow_disc, mock_agent_disc,
                                       adapter, tmp_path, mock_agent, mock_workflow):
        """Test MCP config uses Claude Desktop format (mcpServers)."""
        mock_agent_disc.return_value.discover.return_value = [mock_agent]
        mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        config_path = output_dir / "mcp.json"
        with open(config_path) as f:
            config = json.load(f)

        # Cursor uses "mcpServers" (Claude Desktop format)
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
        assert len(result.files_created) == 5  # mcp.json, .cursorrules, CURSOR.md, README, checksums

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
class TestCursorMCPConfig:
    """Test Cursor MCP configuration specifics."""

    def test_mcp_config_uses_mcpservers_key(self, tmp_path, mock_agent, mock_workflow):
        """Test that MCP config uses Cursor 'mcpServers' format."""
        adapter = CursorAdapter(tmp_path)

        with patch('vibey.adapters.cursor.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.cursor.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                config_path = output_dir / "mcp.json"
                with open(config_path) as f:
                    config = json.load(f)

                # Cursor uses "mcpServers" (Claude Desktop format)
                assert "mcpServers" in config
                assert "servers" not in config

    def test_mcp_config_vibey_server(self, tmp_path, mock_agent, mock_workflow):
        """Test Vibey MCP server configuration."""
        adapter = CursorAdapter(tmp_path)

        with patch('vibey.adapters.cursor.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.cursor.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                config_path = output_dir / "mcp.json"
                with open(config_path) as f:
                    config = json.load(f)

                vibey_config = config["mcpServers"]["vibey"]
                assert vibey_config["command"] == "python"
                assert "-m" in vibey_config["args"]
                assert "framework.mcp.server" in vibey_config["args"]


@pytest.mark.platform
class TestCursorRules:
    """Test .cursorrules file generation."""

    def test_cursorrules_created(self, tmp_path, mock_agent, mock_workflow):
        """Test that .cursorrules file is created."""
        with patch('vibey.adapters.cursor.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.cursor.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CursorAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                # .cursorrules goes in project root (output_dir.parent)
                rules_path = output_dir.parent / ".cursorrules"
                assert rules_path.exists()
                content = rules_path.read_text()
                assert len(content) > 0

    def test_cursorrules_contains_framework_info(self, tmp_path, mock_agent, mock_workflow):
        """Test that .cursorrules contains Vibey framework information."""
        with patch('vibey.adapters.cursor.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.cursor.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CursorAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                # .cursorrules goes in project root (output_dir.parent)
                rules_path = output_dir.parent / ".cursorrules"
                content = rules_path.read_text()

                assert "Vibey" in content
                assert "MCP" in content

    def test_cursorrules_lists_agents(self, tmp_path):
        """Test that .cursorrules lists discovered agents."""
        project_root = Path(__file__).parent.parent.parent
        adapter = CursorAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        # .cursorrules goes in project root (output_dir.parent)
        rules_path = output_dir.parent / ".cursorrules"
        content = rules_path.read_text()

        # Should contain real agents from framework
        assert "vibey_" in content  # Tool prefix


@pytest.mark.platform
class TestCursorContext:
    """Test Cursor context file generation."""

    def test_context_contains_mcp_integration(self, tmp_path, mock_agent, mock_workflow):
        """Test that context mentions MCP integration."""
        adapter = CursorAdapter(tmp_path)

        with patch('vibey.adapters.cursor.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.cursor.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "CURSOR.md"
                content = context_path.read_text()

                assert "MCP" in content
                assert ".cursor/mcp.json" in content

    def test_context_lists_roadmap_tools(self, tmp_path, mock_agent, mock_workflow):
        """Test that context lists roadmap tools."""
        adapter = CursorAdapter(tmp_path)

        with patch('vibey.adapters.cursor.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.cursor.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "CURSOR.md"
                content = context_path.read_text()

                assert "vibey_roadmap_status" in content
                assert "vibey_start_task" in content
                assert "vibey_complete_task" in content

    def test_context_lists_agents(self, tmp_path):
        """Test that context lists discovered agents."""
        project_root = Path(__file__).parent.parent.parent
        adapter = CursorAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "CURSOR.md"
        content = context_path.read_text()

        # Should contain real agents from framework
        assert "vibey_" in content  # Tool prefix
        assert "Agent" in content

    def test_context_lists_workflows(self, tmp_path):
        """Test that context lists discovered workflows."""
        project_root = Path(__file__).parent.parent.parent
        adapter = CursorAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "CURSOR.md"
        content = context_path.read_text()

        # Should contain real workflows from framework
        assert "vibey_workflow_" in content
        assert "Workflow" in content
