"""
Platform-specific tests for GitHub Copilot adapter.

Tests Copilot adapter functionality including repository instructions,
custom agent profiles, and context file generation.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibey.adapters.copilot import CopilotAdapter


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
    """Create a CopilotAdapter instance with real project root."""
    return CopilotAdapter(Path(__file__).parent.parent.parent)


@pytest.mark.platform
class TestCopilotAdapter:
    """Test GitHub Copilot adapter functionality."""

    def test_get_platform_name(self, adapter):
        """Test platform name is correct."""
        assert adapter.get_platform_name() == "copilot"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test deployment directory path."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".github"

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

    def test_supports_feature_instructions(self, adapter):
        """Test that instructions feature is supported (Copilot specific)."""
        assert adapter.supports_feature("instructions") is True

    def test_supports_feature_unknown(self, adapter):
        """Test that unknown features are not supported."""
        assert adapter.supports_feature("unknown_feature") is False

    def test_get_required_files(self, adapter):
        """Test required files list."""
        required = adapter.get_required_files()
        assert "copilot-instructions.md" in required
        assert "COPILOT.md" in required
        assert "agents/" in required

    def test_export_creates_files(self, tmp_path, mock_agent, mock_workflow):
        """Test that export creates all required files."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_agent_disc:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_workflow_disc:
                mock_agent_disc.return_value.discover.return_value = [mock_agent]
                mock_workflow_disc.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                result = adapter.export(output_dir)

                assert result.success is True
                assert (output_dir / "copilot-instructions.md").exists()
                assert (output_dir / "COPILOT.md").exists()
                assert (output_dir / "agents").is_dir()
                assert (output_dir / "agents" / "test-agent.md").exists()
                assert (output_dir / "COPILOT_README.md").exists()
                assert (output_dir / ".checksums.json").exists()

    def test_export_result_counts(self, adapter, tmp_path):
        """Test that export result has correct counts."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        # Uses real discovery - check we found agents and workflows
        assert result.success is True
        assert result.agents_count > 0  # Should find real agents
        assert result.workflows_count > 0  # Should find real workflows
        # Files: instructions, copilot.md, readme, checksums + N agent profiles
        assert len(result.files_created) > 4

    def test_export_checksums_generated(self, adapter, tmp_path):
        """Test that checksums are generated for drift detection."""
        output_dir = tmp_path / "output"
        result = adapter.export(output_dir)

        assert "copilot-instructions.md" in result.checksums
        assert len(result.checksums["copilot-instructions.md"]) == 16

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
class TestCopilotInstructions:
    """Test Copilot instructions file generation."""

    def test_instructions_contains_framework_info(self, tmp_path, mock_agent, mock_workflow):
        """Test that instructions contains Vibey framework information."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                instructions_path = output_dir / "copilot-instructions.md"
                content = instructions_path.read_text()

                assert "Vibey" in content
                assert "Agent" in content
                assert "MCP" in content

    def test_instructions_lists_agents(self, tmp_path, mock_agent, mock_workflow):
        """Test that instructions lists available agents."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                instructions_path = output_dir / "copilot-instructions.md"
                content = instructions_path.read_text()

                assert "Test Agent" in content

    def test_instructions_mentions_mcp_tools(self, tmp_path, mock_agent, mock_workflow):
        """Test that instructions mentions MCP tools."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                instructions_path = output_dir / "copilot-instructions.md"
                content = instructions_path.read_text()

                assert "vibey_roadmap_status" in content
                assert "vibey_start_task" in content


@pytest.mark.platform
class TestCopilotAgentProfiles:
    """Test Copilot custom agent profile generation."""

    def test_agent_profiles_created(self, tmp_path, mock_agent, mock_workflow):
        """Test that agent profiles are created in agents/ directory."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                agents_dir = output_dir / "agents"
                assert agents_dir.is_dir()
                assert (agents_dir / "test-agent.md").exists()

    def test_agent_profile_content(self, tmp_path, mock_agent, mock_workflow):
        """Test agent profile contains expected content."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                profile_path = output_dir / "agents" / "test-agent.md"
                content = profile_path.read_text()

                assert "Test Agent" in content
                assert "test agent for unit testing" in content
                assert "vibey_test_agent" in content  # MCP tool name

    def test_agent_profile_includes_triggers(self, tmp_path, mock_agent, mock_workflow):
        """Test agent profile includes trigger keywords as capabilities."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                profile_path = output_dir / "agents" / "test-agent.md"
                content = profile_path.read_text()

                # Should include trigger keywords from triggers dict
                assert "test" in content
                assert "testing" in content

    def test_multiple_agent_profiles(self, tmp_path, mock_workflow):
        """Test multiple agent profiles are created."""
        mock_agent1 = MagicMock()
        mock_agent1.id = "agent-one"
        mock_agent1.name = "Agent One"
        mock_agent1.description = "First agent"
        mock_agent1.triggers = {"keywords": ["first"], "contexts": [], "file_patterns": [], "priority": "high"}

        mock_agent2 = MagicMock()
        mock_agent2.id = "agent-two"
        mock_agent2.name = "Agent Two"
        mock_agent2.description = "Second agent"
        mock_agent2.triggers = {"keywords": ["second"], "contexts": [], "file_patterns": [], "priority": "medium"}

        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent1, mock_agent2]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                agents_dir = output_dir / "agents"
                assert (agents_dir / "agent-one.md").exists()
                assert (agents_dir / "agent-two.md").exists()


@pytest.mark.platform
class TestCopilotContext:
    """Test Copilot context file generation."""

    def test_context_contains_integration_info(self, tmp_path, mock_agent, mock_workflow):
        """Test that context mentions Copilot integration."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "COPILOT.md"
                content = context_path.read_text()

                assert "Copilot" in content
                assert "MCP" in content
                assert ".github/copilot-instructions.md" in content
                assert ".github/agents/" in content

    def test_context_lists_roadmap_tools(self, tmp_path, mock_agent, mock_workflow):
        """Test that context lists roadmap tools."""
        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                adapter.export(output_dir)

                context_path = output_dir / "COPILOT.md"
                content = context_path.read_text()

                assert "vibey_roadmap_status" in content
                assert "vibey_start_task" in content
                assert "vibey_complete_task" in content

    def test_context_lists_agents(self, tmp_path):
        """Test that context lists discovered agents."""
        project_root = Path(__file__).parent.parent.parent
        adapter = CopilotAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "COPILOT.md"
        content = context_path.read_text()

        # Should contain real agents from framework
        assert "vibey_" in content  # Tool prefix

    def test_context_lists_workflows(self, tmp_path):
        """Test that context lists discovered workflows."""
        project_root = Path(__file__).parent.parent.parent
        adapter = CopilotAdapter(project_root)
        output_dir = tmp_path / "output"
        adapter.export(output_dir)

        context_path = output_dir / "COPILOT.md"
        content = context_path.read_text()

        # Should contain real workflows from framework
        assert "vibey_workflow_" in content


@pytest.mark.platform
class TestCopilotAgentTriggersEdgeCase:
    """Test edge cases for agent triggers handling."""

    def test_agent_without_triggers(self, tmp_path, mock_workflow):
        """Test agent profile generation when triggers is None."""
        mock_agent = MagicMock()
        mock_agent.id = "no-triggers-agent"
        mock_agent.name = "No Triggers Agent"
        mock_agent.description = "Agent without triggers"
        mock_agent.triggers = None

        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                result = adapter.export(output_dir)

                assert result.success is True
                profile_path = output_dir / "agents" / "no-triggers-agent.md"
                assert profile_path.exists()

    def test_agent_with_empty_triggers(self, tmp_path, mock_workflow):
        """Test agent profile generation when triggers dict has empty keywords."""
        mock_agent = MagicMock()
        mock_agent.id = "empty-triggers-agent"
        mock_agent.name = "Empty Triggers Agent"
        mock_agent.description = "Agent with empty triggers"
        mock_agent.triggers = {"keywords": [], "contexts": [], "file_patterns": [], "priority": "low"}

        with patch('vibey.adapters.copilot.adapter.AgentDiscovery') as mock_ad:
            with patch('vibey.adapters.copilot.adapter.WorkflowDiscovery') as mock_wd:
                mock_ad.return_value.discover.return_value = [mock_agent]
                mock_wd.return_value.discover.return_value = [mock_workflow]

                adapter = CopilotAdapter(tmp_path)
                output_dir = tmp_path / "output"
                result = adapter.export(output_dir)

                assert result.success is True
                profile_path = output_dir / "agents" / "empty-triggers-agent.md"
                assert profile_path.exists()
                content = profile_path.read_text()
                # Should have fallback capabilities
                assert "Specialized in" in content
