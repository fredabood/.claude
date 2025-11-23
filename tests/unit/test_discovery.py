"""
Unit tests for Discovery modules.

Tests AgentDiscovery, WorkflowDiscovery, ToolGenerator, and ToolDiscovery.
"""

import pytest
from pathlib import Path

from framework.mcp.discovery import (
    FrontmatterParser,
    AgentDiscovery,
    AgentDefinition,
    WorkflowDiscovery,
    WorkflowDefinition,
    ToolGenerator,
    ToolDiscovery,
)


class TestAgentDefinition:
    """Tests for AgentDefinition dataclass."""

    def test_from_frontmatter_minimal(self):
        """Test creating AgentDefinition with minimal frontmatter."""
        frontmatter = {
            'id': 'test-agent',
            'name': 'Test Agent',
            'type': 'quality',
            'version': '1.0.0',
        }
        agent = AgentDefinition.from_frontmatter(frontmatter)

        assert agent.id == 'test-agent'
        assert agent.name == 'Test Agent'
        assert agent.type == 'quality'
        assert agent.version == '1.0.0'
        assert agent.description == ''
        assert agent.triggers == {}
        assert agent.inputs == []
        assert agent.outputs == []
        assert agent.aliases == []

    def test_from_frontmatter_full(self):
        """Test creating AgentDefinition with full frontmatter."""
        frontmatter = {
            'id': 'test-engineer',
            'name': 'Test Engineer',
            'type': 'quality',
            'version': '2.0.0',
            'description': 'Writes and runs tests',
            'triggers': {
                'keywords': ['write tests', 'pytest'],
                'file_patterns': ['tests/*']
            },
            'inputs': [
                {'name': 'code_to_test', 'type': 'string', 'required': True}
            ],
            'outputs': [
                {'name': 'test_results', 'type': 'object'}
            ],
            'aliases': ['tester', 'qa-engineer']
        }
        agent = AgentDefinition.from_frontmatter(frontmatter)

        assert agent.id == 'test-engineer'
        assert agent.description == 'Writes and runs tests'
        assert agent.triggers['keywords'] == ['write tests', 'pytest']
        assert len(agent.inputs) == 1
        assert agent.inputs[0]['name'] == 'code_to_test'
        assert agent.aliases == ['tester', 'qa-engineer']

    def test_from_frontmatter_with_filepath(self):
        """Test creating AgentDefinition with filepath."""
        frontmatter = {
            'id': 'test-agent',
            'name': 'Test Agent',
            'type': 'quality',
            'version': '1.0.0',
        }
        filepath = Path('/path/to/agent.md')
        agent = AgentDefinition.from_frontmatter(frontmatter, filepath)

        assert agent.filepath == filepath


class TestAgentDiscovery:
    """Tests for AgentDiscovery class."""

    @pytest.fixture
    def discovery(self, tmp_path):
        """Create discovery instance with temp directory."""
        # Create agents directory structure
        agents_dir = tmp_path / 'framework' / 'agents'
        agents_dir.mkdir(parents=True)
        return AgentDiscovery(tmp_path)

    @pytest.fixture
    def populated_discovery(self, tmp_path):
        """Create discovery with sample agents."""
        agents_dir = tmp_path / 'framework' / 'agents'
        agents_dir.mkdir(parents=True)

        # Create test agent file
        (agents_dir / 'test-engineer.md').write_text("""---
id: test-engineer
name: Test Engineer
type: quality
version: 1.0.0
description: Writes comprehensive tests
---

# Test Engineer

Instructions for test engineer...
""")

        # Create web developer file
        (agents_dir / 'web-developer.md').write_text("""---
id: web-developer
name: Web Developer
type: development
version: 1.0.0
description: Builds web applications
---

# Web Developer

Instructions for web developer...
""")

        # Create README (should be skipped)
        (agents_dir / 'README.md').write_text("# Agents README")

        return AgentDiscovery(tmp_path)

    def test_discover_empty_directory(self, discovery):
        """Test discovering agents in empty directory."""
        agents = discovery.discover()
        assert agents == []

    def test_discover_nonexistent_directory(self, tmp_path):
        """Test discovering agents when directory doesn't exist."""
        discovery = AgentDiscovery(tmp_path)
        agents = discovery.discover()
        assert agents == []

    def test_discover_agents(self, populated_discovery):
        """Test discovering agents from files."""
        agents = populated_discovery.discover()

        assert len(agents) == 2
        ids = [a.id for a in agents]
        assert 'test-engineer' in ids
        assert 'web-developer' in ids

    def test_discover_skips_readme(self, populated_discovery):
        """Test that README files are skipped."""
        agents = populated_discovery.discover()
        ids = [a.id for a in agents]
        # README should not appear as an agent
        assert all('readme' not in id.lower() for id in ids)

    def test_get_agent_by_id(self, populated_discovery):
        """Test getting agent by ID."""
        agent = populated_discovery.get_agent_by_id('test-engineer')

        assert agent is not None
        assert agent.name == 'Test Engineer'
        assert agent.type == 'quality'

    def test_get_agent_by_id_not_found(self, populated_discovery):
        """Test getting non-existent agent returns None."""
        agent = populated_discovery.get_agent_by_id('nonexistent')
        assert agent is None

    def test_get_agents_by_type(self, populated_discovery):
        """Test filtering agents by type."""
        quality_agents = populated_discovery.get_agents_by_type('quality')

        assert len(quality_agents) == 1
        assert quality_agents[0].id == 'test-engineer'

    def test_discover_invalid_agent_skipped(self, tmp_path):
        """Test that invalid agents are skipped."""
        agents_dir = tmp_path / 'framework' / 'agents'
        agents_dir.mkdir(parents=True)

        # Create invalid agent (missing required fields)
        (agents_dir / 'invalid.md').write_text("""---
id: invalid
# Missing name, type, version
---

# Invalid Agent
""")

        # Create valid agent
        (agents_dir / 'valid.md').write_text("""---
id: valid
name: Valid Agent
type: development
version: 1.0.0
---

# Valid Agent
""")

        discovery = AgentDiscovery(tmp_path)
        agents = discovery.discover()

        # Only valid agent should be returned
        assert len(agents) == 1
        assert agents[0].id == 'valid'


class TestToolGenerator:
    """Tests for ToolGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create tool generator instance."""
        return ToolGenerator(tool_prefix='vibey')

    def test_agent_to_tool(self, generator):
        """Test generating MCP tool from agent definition."""
        agent = AgentDefinition(
            id='test-engineer',
            name='Test Engineer',
            type='quality',
            version='1.0.0',
            description='Writes comprehensive tests',
            inputs=[
                {'name': 'code_to_test', 'type': 'string', 'required': True},
                {'name': 'coverage', 'type': 'number', 'required': False}
            ]
        )

        tool = generator.agent_to_tool(agent)

        assert tool['name'] == 'vibey_test_engineer'
        assert 'Writes comprehensive tests' in tool['description']
        assert tool['inputSchema']['type'] == 'object'
        assert 'code_to_test' in tool['inputSchema']['properties']
        assert 'code_to_test' in tool['inputSchema']['required']
        assert 'coverage' in tool['inputSchema']['properties']
        assert 'coverage' not in tool['inputSchema']['required']

    def test_agent_to_tool_no_inputs(self, generator):
        """Test generating tool for agent with no inputs."""
        agent = AgentDefinition(
            id='simple-agent',
            name='Simple Agent',
            type='core',
            version='1.0.0',
            inputs=[]
        )

        tool = generator.agent_to_tool(agent)

        assert tool['name'] == 'vibey_simple_agent'
        assert tool['inputSchema']['properties'] == {}
        assert tool['inputSchema']['required'] == []

    def test_workflow_to_tool(self, generator):
        """Test generating MCP tool from workflow definition."""
        workflow = WorkflowDefinition(
            id='feature-dev',
            name='Feature Development',
            type='development',
            version='1.0.0',
            description='Complete feature development workflow',
            complexity='medium',
            inputs=[
                {'name': 'feature_spec', 'type': 'string', 'required': True}
            ]
        )

        tool = generator.workflow_to_tool(workflow)

        assert tool['name'] == 'vibey_workflow_feature_dev'
        assert 'feature development' in tool['description'].lower()
        assert 'feature_spec' in tool['inputSchema']['properties']

    def test_tool_name_normalization(self, generator):
        """Test that tool names are properly normalized."""
        agent = AgentDefinition(
            id='my-complex-agent',
            name='Complex Agent',
            type='core',
            version='1.0.0'
        )

        tool = generator.agent_to_tool(agent)

        # Should replace hyphens with underscores
        assert tool['name'] == 'vibey_my_complex_agent'


class TestToolDiscovery:
    """Tests for ToolDiscovery class."""

    @pytest.fixture
    def discovery(self, tmp_path):
        """Create tool discovery with sample files."""
        # Create agents
        agents_dir = tmp_path / 'framework' / 'agents'
        agents_dir.mkdir(parents=True)
        (agents_dir / 'test-agent.md').write_text("""---
id: test-agent
name: Test Agent
type: quality
version: 1.0.0
---

# Test Agent
""")

        # Create workflows
        workflows_dir = tmp_path / 'framework' / 'workflows'
        workflows_dir.mkdir(parents=True)
        (workflows_dir / 'test-workflow.md').write_text("""---
id: test-workflow
name: Test Workflow
type: development
version: 1.0.0
---

# Test Workflow
""")

        return ToolDiscovery(root_dir=tmp_path, tool_prefix='vibey')

    def test_get_all_tools(self, discovery):
        """Test getting all tools from discovery."""
        tools = discovery.get_all_tools()

        assert len(tools) >= 2
        names = [t['name'] for t in tools]
        assert 'vibey_test_agent' in names
        assert 'vibey_workflow_test_workflow' in names

    def test_get_tool_by_name(self, discovery):
        """Test getting specific tool by name."""
        tool = discovery.get_tool_by_name('vibey_test_agent')

        assert tool is not None
        assert tool['name'] == 'vibey_test_agent'

    def test_get_tool_by_name_not_found(self, discovery):
        """Test getting non-existent tool returns None."""
        tool = discovery.get_tool_by_name('nonexistent_tool')
        assert tool is None

    def test_get_stats(self, discovery):
        """Test getting discovery statistics."""
        stats = discovery.get_stats()

        # Check expected keys from actual API
        assert 'total_tools' in stats
        assert 'agent_tools' in stats
        assert 'workflow_tools' in stats
        assert stats['agent_tools'] >= 1
        assert stats['workflow_tools'] >= 1

    def test_caching(self, discovery):
        """Test that discovery results are cached."""
        # First call
        tools1 = discovery.get_all_tools()

        # Second call should use cache
        tools2 = discovery.get_all_tools()

        # Should be same list (from cache)
        assert tools1 == tools2

    def test_force_refresh(self, discovery):
        """Test force refresh bypasses cache."""
        # First call
        tools1 = discovery.get_all_tools()

        # Force refresh
        tools2 = discovery.get_all_tools(force_refresh=True)

        # Should still have same tools
        assert len(tools1) == len(tools2)


class TestRealAgents:
    """
    Integration tests using real agent files.

    These tests use the actual framework/agents/ directory
    to ensure the discovery system works with real data.
    """

    @pytest.fixture
    def real_discovery(self):
        """Create discovery pointing to real Vibey repo."""
        repo_root = Path(__file__).parent.parent.parent
        return AgentDiscovery(repo_root)

    def test_discover_real_agents(self, real_discovery):
        """Test discovering agents from real framework/agents/ directory."""
        agents = real_discovery.discover()

        # Should find multiple agents
        assert len(agents) > 0

        # All agents should have required fields
        for agent in agents:
            assert agent.id, f"Agent missing id"
            assert agent.name, f"Agent {agent.id} missing name"
            assert agent.type, f"Agent {agent.id} missing type"
            assert agent.version, f"Agent {agent.id} missing version"

    def test_real_agent_types(self, real_discovery):
        """Test that real agents have valid types."""
        agents = real_discovery.discover()
        valid_types = {'core', 'planning', 'development', 'quality', 'documentation', 'architecture'}

        for agent in agents:
            assert agent.type in valid_types, f"Agent {agent.id} has invalid type: {agent.type}"
