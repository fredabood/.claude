"""
Platform-specific tests for Replit adapter.

Tests Replit adapter functionality including MCP configuration,
context generation, and export capabilities.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.adapters.replit import ReplitAdapter


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
    """Create a ReplitAdapter instance with real project root."""
    return ReplitAdapter(Path(__file__).parent.parent.parent)


@pytest.mark.platform
class TestReplitAdapter:
    """Test Replit adapter functionality."""

    def test_get_platform_name(self, adapter):
        """Test platform name is correct."""
        assert adapter.get_platform_name() == "replit"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test deployment directory path."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".replit-vibey"

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

    def test_supports_feature_web(self, adapter):
        """Test that web feature is supported."""
        assert adapter.supports_feature("web") is True

    def test_supports_feature_templates(self, adapter):
        """Test that templates feature is supported."""
        assert adapter.supports_feature("templates") is True

    def test_supports_feature_unknown(self, adapter):
        """Test that unknown features are not supported."""
        assert adapter.supports_feature("unknown_feature") is False

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "mcp.json" in required
        assert "REPLIT.md" in required

    def test_export_creates_files(self, tmp_path, mock_agent, mock_workflow):
        """Test that export creates all required files."""
        with patch('vibey.adapters.replit.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.replit.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = ReplitAdapter(tmp_path)
                output_dir = tmp_path / "output"
                result = adapter.export(output_dir)

                assert result.success is True
                assert (output_dir / "mcp.json").exists()
                assert (output_dir / "REPLIT.md").exists()
                assert (output_dir / "README.md").exists()
                assert (output_dir / ".checksums.json").exists()

    def test_export_mcp_config_format(self, tmp_path, mock_agent, mock_workflow):
        """Test MCP config uses Replit mcpServers format."""
        with patch('vibey.adapters.replit.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.replit.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = ReplitAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                config_path = output_dir / "mcp.json"
                with open(config_path) as f:
                    config = json.load(f)

                assert "mcpServers" in config
                assert "vibey" in config["mcpServers"]
                # Replit-specific env variable
                assert config["mcpServers"]["vibey"]["env"].get("REPLIT") == "1"

    def test_export_result_counts(self, adapter, tmp_path):
        """Test that export result has correct counts."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert result.success is True
        assert result.agents_count > 0
        assert result.workflows_count > 0
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
class TestReplitContext:
    """Test Replit context file generation."""

    def test_context_contains_platform_features(self, tmp_path, mock_agent, mock_workflow):
        """Test that context lists Replit platform features."""
        with patch('vibey.adapters.replit.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.replit.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = ReplitAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "REPLIT.md"
                content = context_path.read_text()

                assert "Web-based IDE" in content
                assert "Native MCP" in content
                assert "Templates" in content
                assert "Multiplayer" in content

    def test_context_lists_roadmap_tools(self, tmp_path, mock_agent, mock_workflow):
        """Test that context lists roadmap tools."""
        with patch('vibey.adapters.replit.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.replit.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = ReplitAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "REPLIT.md"
                content = context_path.read_text()

                assert "vibey_roadmap_status" in content
                assert "vibey_start_task" in content
                assert "vibey_complete_task" in content

    def test_context_lists_agents(self, tmp_path):
        """Test that context lists discovered agents."""
        project_root = Path(__file__).parent.parent.parent
        adapter = ReplitAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "REPLIT.md"
        content = context_path.read_text()

        assert "vibey_" in content
        assert "Agent" in content

    def test_context_lists_workflows(self, tmp_path):
        """Test that context lists discovered workflows."""
        project_root = Path(__file__).parent.parent.parent
        adapter = ReplitAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "REPLIT.md"
        content = context_path.read_text()

        assert "vibey_workflow_" in content
        assert "Workflow" in content

    def test_context_includes_forking_instructions(self, tmp_path, mock_agent, mock_workflow):
        """Test that context includes forking instructions."""
        with patch('vibey.adapters.replit.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.replit.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = ReplitAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "REPLIT.md"
                content = context_path.read_text()

                assert "Fork" in content
