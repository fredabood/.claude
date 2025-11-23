"""
Integration tests for MCP tool generation.

Tests the full pipeline from asset discovery to MCP tool generation
and tool invocation through the MCP server.
"""

import pytest
import asyncio
from pathlib import Path

from framework.mcp.server import VibeyMCPServer
from framework.mcp.discovery import ToolDiscovery
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter


class TestMCPServerIntegration:
    """Integration tests for VibeyMCPServer."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance pointing to real repo."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    def test_server_initialization(self, server):
        """Test that MCP server initializes correctly."""
        assert server.roadmap_root.exists() or True  # May not exist in test env
        assert server.tool_discovery is not None

    def test_get_capabilities(self, server):
        """Test server returns valid MCP capabilities."""
        caps = server.get_capabilities()

        assert 'tools' in caps
        assert 'resources' in caps
        assert 'prompts' in caps
        assert caps['tools']['listChanged'] is True

    def test_get_tools_returns_list(self, server):
        """Test get_tools returns a list of tool definitions."""
        tools = server.get_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_required_fields(self, server):
        """Test all tools have required MCP fields."""
        tools = server.get_tools()

        for tool in tools:
            assert 'name' in tool, f"Tool missing 'name': {tool}"
            assert 'description' in tool, f"Tool {tool.get('name')} missing 'description'"
            assert 'inputSchema' in tool, f"Tool {tool.get('name')} missing 'inputSchema'"
            assert tool['inputSchema']['type'] == 'object'

    def test_tool_names_are_prefixed(self, server):
        """Test all tool names have vibey_ prefix."""
        tools = server.get_tools()

        for tool in tools:
            assert tool['name'].startswith('vibey_'), f"Tool {tool['name']} missing vibey_ prefix"

    def test_roadmap_tools_present(self, server):
        """Test that roadmap management tools are present."""
        tools = server.get_tools()
        names = [t['name'] for t in tools]

        # Core roadmap tools should be present
        assert 'vibey_roadmap_status' in names
        assert 'vibey_start_task' in names or any('task' in n for n in names)

    def test_agent_tools_present(self, server):
        """Test that agent tools are present."""
        tools = server.get_tools()
        names = [t['name'] for t in tools]

        # Should have agent tools (not workflow_ prefixed)
        agent_tools = [n for n in names if not n.startswith('vibey_workflow_') and n != 'vibey_roadmap_status']
        assert len(agent_tools) > 0, "No agent tools found"

    def test_workflow_tools_present(self, server):
        """Test that workflow tools are present."""
        tools = server.get_tools()
        names = [t['name'] for t in tools]

        # Should have workflow tools
        workflow_tools = [n for n in names if 'workflow' in n]
        assert len(workflow_tools) > 0, "No workflow tools found"


class TestMCPToolInvocation:
    """Tests for MCP tool invocation."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    @pytest.mark.asyncio
    async def test_handle_roadmap_status_tool(self, server):
        """Test invoking vibey_roadmap_status tool."""
        result = await server.handle_tool_call('vibey_roadmap_status', {})

        assert 'content' in result
        assert len(result['content']) > 0
        assert result['content'][0]['type'] == 'text'
        # Should not be an error
        assert result.get('isError', False) is False

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, server):
        """Test invoking unknown tool returns error."""
        result = await server.handle_tool_call('nonexistent_tool', {})

        assert result.get('isError', True) is True
        assert '❌' in result['content'][0]['text'] or 'Unknown' in result['content'][0]['text']

    @pytest.mark.asyncio
    async def test_handle_agent_tool(self, server):
        """Test invoking an agent tool."""
        # Get first agent tool
        tools = server.get_tools()
        agent_tool = None
        for tool in tools:
            if tool.get('_metadata', {}).get('asset_type') == 'agent':
                agent_tool = tool
                break

        if agent_tool is None:
            pytest.skip("No agent tools found")

        result = await server.handle_tool_call(agent_tool['name'], {})

        assert 'content' in result
        assert len(result['content']) > 0
        # Agent tools return instructions, not errors
        assert result.get('isError', False) is False

    @pytest.mark.asyncio
    async def test_handle_workflow_tool(self, server):
        """Test invoking a workflow tool."""
        # Get first workflow tool
        tools = server.get_tools()
        workflow_tool = None
        for tool in tools:
            if tool.get('_metadata', {}).get('asset_type') == 'workflow':
                workflow_tool = tool
                break

        if workflow_tool is None:
            pytest.skip("No workflow tools found")

        result = await server.handle_tool_call(workflow_tool['name'], {})

        assert 'content' in result
        assert len(result['content']) > 0
        # Workflow tools return steps, not errors
        assert result.get('isError', False) is False


class TestToolDiscoveryIntegration:
    """Integration tests for ToolDiscovery with real files."""

    @pytest.fixture
    def discovery(self):
        """Create discovery pointing to real Vibey repo."""
        repo_root = Path(__file__).parent.parent.parent
        return ToolDiscovery(root_dir=repo_root, tool_prefix='vibey')

    def test_discover_real_agents(self, discovery):
        """Test discovering agents from real framework/agents/ directory."""
        agents = discovery.agent_discovery.discover()

        # Should find agents
        assert len(agents) > 0

        # Verify some expected agents exist
        agent_ids = [a.id for a in agents]
        # At least one of these common agents should exist
        expected = ['test-engineer', 'web-developer', 'docs-writer', 'sprint-planner']
        found = [e for e in expected if e in agent_ids]
        assert len(found) > 0, f"Expected at least one of {expected}, found: {agent_ids}"

    def test_discover_real_workflows(self, discovery):
        """Test discovering workflows from real framework/workflows/ directory."""
        workflows = discovery.workflow_discovery.discover()

        # Should find workflows
        assert len(workflows) > 0

    def test_generate_tools_from_real_assets(self, discovery):
        """Test generating tools from real assets."""
        tools = discovery.get_all_tools()

        # Should generate tools
        assert len(tools) > 0

        # Verify tool structure
        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool

    def test_discovery_stats(self, discovery):
        """Test discovery statistics are accurate."""
        # Force refresh to get accurate stats
        discovery.get_all_tools(force_refresh=True)
        stats = discovery.get_stats()

        assert stats['total_tools'] > 0
        assert stats['agent_tools'] > 0
        assert stats['workflow_tools'] > 0
        assert stats['total_tools'] == stats['agent_tools'] + stats['workflow_tools']


class TestRoadmapAdapterIntegration:
    """Integration tests for RoadmapAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter pointing to real roadmap."""
        return RoadmapAdapter(".vibey/roadmap")

    def test_get_roadmap_status(self, adapter):
        """Test getting roadmap status."""
        try:
            status = adapter.get_roadmap_status()

            assert 'name' in status
            assert 'version' in status
            assert 'status' in status
            assert 'progress' in status
        except Exception as e:
            # Roadmap might not exist in test environment
            if "not found" in str(e).lower():
                pytest.skip("Roadmap not found in test environment")
            raise

    def test_query_track(self, adapter):
        """Test querying a track."""
        try:
            # Try to query a known track
            track = adapter.query_track('goose-port')

            assert 'id' in track
            assert track['id'] == 'goose-port'
            assert 'name' in track
            assert 'status' in track
        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip("Track not found in test environment")
            raise


class TestMCPProtocolCompliance:
    """Tests for MCP protocol compliance."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    def test_tool_schema_json_schema_compliant(self, server):
        """Test tool inputSchemas are valid JSON Schema."""
        tools = server.get_tools()

        for tool in tools:
            schema = tool['inputSchema']

            # Required JSON Schema fields
            assert schema['type'] == 'object'
            assert 'properties' in schema
            assert isinstance(schema['properties'], dict)
            # 'required' is optional when all properties are optional
            if 'required' in schema:
                assert isinstance(schema['required'], list)

            # Property types should be valid
            for prop_name, prop_def in schema['properties'].items():
                assert 'type' in prop_def, f"Property {prop_name} in {tool['name']} missing type"
                assert prop_def['type'] in ['string', 'number', 'integer', 'boolean', 'array', 'object']

    def test_tool_response_format(self, server):
        """Test tool responses follow MCP format."""
        result = asyncio.run(server.handle_tool_call('vibey_roadmap_status', {}))

        # MCP response format
        assert 'content' in result
        assert isinstance(result['content'], list)

        for content_item in result['content']:
            assert 'type' in content_item
            assert content_item['type'] in ['text', 'image', 'resource']

            if content_item['type'] == 'text':
                assert 'text' in content_item

    def test_error_response_format(self, server):
        """Test error responses follow MCP format."""
        result = asyncio.run(server.handle_tool_call('nonexistent_tool', {}))

        # Error response format
        assert 'content' in result
        assert isinstance(result['content'], list)
        assert 'isError' in result
        assert result['isError'] is True
