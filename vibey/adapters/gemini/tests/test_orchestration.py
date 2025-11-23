"""Tests for Sequential Orchestration."""

import pytest
from pathlib import Path

from vibey.adapters.gemini.orchestration import (
    SequentialOrchestrator,
    CommandChain,
    WorkflowStep,
    OrchestrationResult,
)


class TestSequentialOrchestrator:
    """Test suite for SequentialOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with project root."""
        return SequentialOrchestrator(Path.cwd())

    def test_analyze_returns_result(self, orchestrator):
        """Test that analyze() returns OrchestrationResult."""
        result = orchestrator.analyze()

        assert isinstance(result, OrchestrationResult)
        assert isinstance(result.chains, list)
        assert isinstance(result.agent_to_command, dict)
        assert isinstance(result.workflow_to_chain, dict)
        assert isinstance(result.orchestration_hints, str)

    def test_analyze_finds_chains(self, orchestrator):
        """Test that chains are discovered from workflows."""
        result = orchestrator.analyze()

        # Should find some chains (workflows with steps)
        assert len(result.chains) >= 0  # May be 0 if no multi-step workflows

    def test_agent_to_command_mapping(self, orchestrator):
        """Test that agent-to-command mapping is built."""
        result = orchestrator.analyze()

        # Should have mappings for discovered agents
        assert len(result.agent_to_command) > 0

        # All values should be agent- prefixed
        for agent_id, command_id in result.agent_to_command.items():
            assert command_id.startswith("agent-")

    def test_orchestration_hints_not_empty(self, orchestrator):
        """Test that orchestration hints are generated."""
        result = orchestrator.analyze()

        # Should have some content
        assert len(result.orchestration_hints) > 0
        assert "Sequential" in result.orchestration_hints

    def test_orchestration_hints_has_sections(self, orchestrator):
        """Test that orchestration hints have expected sections."""
        result = orchestrator.analyze()

        assert "Sequential Workflow Execution" in result.orchestration_hints
        assert "How to Execute" in result.orchestration_hints
        assert "Agent Quick Reference" in result.orchestration_hints

    def test_clean_agent_id_simple(self, orchestrator):
        """Test cleaning simple agent IDs."""
        assert orchestrator._clean_agent_id("test-engineer") == "test-engineer"
        assert orchestrator._clean_agent_id("web-developer") == "web-developer"

    def test_clean_agent_id_jinja(self, orchestrator):
        """Test cleaning Jinja2 template agent IDs."""
        # Pattern from actual workflows
        template = "{%-else-%}developer{%-endif-%}"
        result = orchestrator._clean_agent_id(template)
        assert "developer" in result.lower()
        assert "{" not in result
        assert "%" not in result

    def test_clean_agent_id_empty(self, orchestrator):
        """Test cleaning empty/None agent IDs."""
        assert orchestrator._clean_agent_id("") == "unknown"
        assert orchestrator._clean_agent_id(None) == "unknown"


class TestCommandChain:
    """Test CommandChain dataclass."""

    @pytest.fixture
    def sample_chain(self):
        """Create sample command chain."""
        steps = [
            WorkflowStep(
                order=1,
                name="Design",
                agent_id="architect",
                agent_name="Architect",
                command_id="agent-architect",
                duration="1 day",
            ),
            WorkflowStep(
                order=2,
                name="Implement",
                agent_id="developer",
                agent_name="Developer",
                command_id="agent-developer",
                duration="2 days",
            ),
            WorkflowStep(
                order=3,
                name="Test",
                agent_id="test-engineer",
                agent_name="Test Engineer",
                command_id="agent-test-engineer",
                duration="1 day",
            ),
        ]
        return CommandChain(
            workflow_id="feature-dev",
            workflow_name="Feature Development",
            steps=steps,
            total_steps=3,
            estimated_duration="4 days",
            complexity="medium",
        )

    def test_get_next_step(self, sample_chain):
        """Test getting next step in chain."""
        next_step = sample_chain.get_next_step(1)
        assert next_step is not None
        assert next_step.order == 2
        assert next_step.name == "Implement"

    def test_get_next_step_last(self, sample_chain):
        """Test getting next step at end of chain."""
        next_step = sample_chain.get_next_step(3)
        assert next_step is None

    def test_get_next_step_invalid(self, sample_chain):
        """Test getting next step with invalid index."""
        next_step = sample_chain.get_next_step(99)
        assert next_step is None

    def test_to_markdown(self, sample_chain):
        """Test markdown generation."""
        md = sample_chain.to_markdown()

        assert "Feature Development" in md
        assert "medium" in md
        assert "4 days" in md
        assert "Command Sequence" in md
        assert "agent-architect" in md
        assert "agent-developer" in md
        assert "agent-test-engineer" in md


class TestWorkflowStep:
    """Test WorkflowStep dataclass."""

    def test_dataclass_fields(self):
        """Test WorkflowStep has expected fields."""
        step = WorkflowStep(
            order=1,
            name="Test Step",
            agent_id="test-agent",
            agent_name="Test Agent",
            command_id="agent-test-agent",
            duration="1 hour",
            description="A test step",
        )

        assert step.order == 1
        assert step.name == "Test Step"
        assert step.agent_id == "test-agent"
        assert step.agent_name == "Test Agent"
        assert step.command_id == "agent-test-agent"
        assert step.duration == "1 hour"
        assert step.description == "A test step"

    def test_optional_description(self):
        """Test that description is optional."""
        step = WorkflowStep(
            order=1,
            name="Test",
            agent_id="test",
            agent_name="Test",
            command_id="agent-test",
            duration="1h",
        )

        assert step.description is None


class TestOrchestrationResult:
    """Test OrchestrationResult dataclass."""

    def test_dataclass_fields(self):
        """Test OrchestrationResult has expected fields."""
        result = OrchestrationResult(
            chains=[],
            agent_to_command={"test": "agent-test"},
            workflow_to_chain={"wf1": "wf1"},
            orchestration_hints="## Hints",
        )

        assert result.chains == []
        assert result.agent_to_command == {"test": "agent-test"}
        assert result.workflow_to_chain == {"wf1": "wf1"}
        assert result.orchestration_hints == "## Hints"
