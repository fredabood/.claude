"""
End-to-end tests for Goose integration.

Tests the full pipeline from MCP server startup to tool invocation
as Goose would experience it.
"""

import pytest
import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vibey.mcp.server import VibeyMCPServer
from vibey.mcp.discovery import ToolDiscovery


class TestGooseMCPServerE2E:
    """E2E tests for MCP server as Goose would use it."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(PROJECT_ROOT)
        )

    def test_server_full_initialization(self, server):
        """Test server initializes with all components."""
        # Server should have tool discovery
        assert server.tool_discovery is not None

        # Server should expose capabilities
        caps = server.get_capabilities()
        assert caps is not None
        assert 'tools' in caps

        # Server should have tools ready
        tools = server.get_tools()
        assert len(tools) > 0

    def test_tool_count_matches_assets(self, server):
        """Test tool count includes discovered assets plus roadmap tools."""
        tools = server.get_tools()
        stats = server.tool_discovery.get_stats()

        # Server includes discovery tools + roadmap management tools
        # Roadmap tools: start_task, complete_task, query_task, start_sprint,
        # complete_sprint, refresh_progress, query_sprint, query_track,
        # list_blockers, list_dependencies, roadmap_status (11 total)
        roadmap_tools = [t for t in tools if not t.get('_metadata')]
        discovered_tools = [t for t in tools if t.get('_metadata')]

        # Roadmap tools should be present
        assert len(roadmap_tools) > 0, "No roadmap management tools found"

        # Discovered tools should match discovery stats
        agent_tools = [t for t in discovered_tools if t.get('_metadata', {}).get('asset_type') == 'agent']
        workflow_tools = [t for t in discovered_tools if t.get('_metadata', {}).get('asset_type') == 'workflow']

        assert len(agent_tools) == stats['agent_tools']
        assert len(workflow_tools) == stats['workflow_tools']

        # Total should be roadmap + discovered
        assert len(tools) == len(roadmap_tools) + stats['total_tools']

    def test_all_tools_callable(self, server):
        """Test all tools can be invoked without errors."""
        tools = server.get_tools()

        for tool in tools[:5]:  # Test first 5 to keep test fast
            # Invoke with empty args (tools should handle gracefully)
            result = asyncio.run(server.handle_tool_call(tool['name'], {}))

            # Should return valid MCP response format
            assert 'content' in result
            assert isinstance(result['content'], list)
            assert len(result['content']) > 0

            # Content should have type and appropriate field
            content = result['content'][0]
            assert 'type' in content
            if content['type'] == 'text':
                assert 'text' in content

    @pytest.mark.asyncio
    async def test_roadmap_status_full_response(self, server):
        """Test roadmap status returns comprehensive data."""
        result = await server.handle_tool_call('vibey_roadmap_status', {})

        assert result.get('isError', False) is False

        text = result['content'][0]['text']

        # Should contain key roadmap information
        assert 'Roadmap' in text or '📊' in text
        assert 'Progress' in text or 'progress' in text.lower()

    @pytest.mark.asyncio
    async def test_query_track_returns_details(self, server):
        """Test querying a track returns detailed info."""
        # First get available tracks from roadmap status
        status_result = await server.handle_tool_call('vibey_roadmap_status', {})

        # Try to query goose-port track if it exists
        result = await server.handle_tool_call('vibey_query_track', {
            'track_id': 'goose-port'
        })

        # Should return track details or error if not found
        assert 'content' in result
        text = result['content'][0]['text']

        if result.get('isError', False):
            # Track not found is acceptable in test env
            assert 'not found' in text.lower() or '❌' in text
        else:
            # Should have track info
            assert 'Track' in text or 'goose-port' in text.lower()

    @pytest.mark.asyncio
    async def test_agent_tool_returns_instructions(self, server):
        """Test agent tools return usable instructions."""
        tools = server.get_tools()

        # Find an agent tool
        agent_tool = None
        for tool in tools:
            if tool.get('_metadata', {}).get('asset_type') == 'agent':
                agent_tool = tool
                break

        if agent_tool is None:
            pytest.skip("No agent tools found")

        result = await server.handle_tool_call(agent_tool['name'], {})

        assert result.get('isError', False) is False
        text = result['content'][0]['text']

        # Agent response should contain useful content
        assert len(text) > 50  # Should have substantial content

    @pytest.mark.asyncio
    async def test_workflow_tool_returns_steps(self, server):
        """Test workflow tools return workflow steps."""
        tools = server.get_tools()

        # Find a workflow tool
        workflow_tool = None
        for tool in tools:
            if tool.get('_metadata', {}).get('asset_type') == 'workflow':
                workflow_tool = tool
                break

        if workflow_tool is None:
            pytest.skip("No workflow tools found")

        result = await server.handle_tool_call(workflow_tool['name'], {})

        assert result.get('isError', False) is False
        text = result['content'][0]['text']

        # Workflow response should contain steps or structure
        assert len(text) > 50  # Should have substantial content


class TestGooseExtensionManifest:
    """Tests for Goose extension manifest generation."""

    @pytest.fixture
    def discovery(self):
        """Create discovery instance."""
        return ToolDiscovery(root_dir=PROJECT_ROOT, tool_prefix='vibey')

    def test_manifest_generation(self, discovery):
        """Test extension manifest can be generated."""
        tools = discovery.get_all_tools()
        stats = discovery.get_stats()

        # Build manifest structure as Goose expects
        manifest = {
            'name': 'vibey',
            'version': '1.0.0',
            'type': 'mcp',
            'description': f'Vibey Agent Framework - {stats["total_tools"]} tools',
            'mcp': {
                'command': 'python',
                'args': ['-m', 'vibey.mcp.server']
            },
            'capabilities': {
                'tools': stats['total_tools'],
                'agents': stats['agent_tools'],
                'workflows': stats['workflow_tools']
            }
        }

        # Verify manifest structure
        assert manifest['name'] == 'vibey'
        assert manifest['type'] == 'mcp'
        assert manifest['capabilities']['tools'] > 0

    def test_tool_names_goose_compatible(self, discovery):
        """Test tool names are Goose-compatible (snake_case, prefixed)."""
        tools = discovery.get_all_tools()

        for tool in tools:
            name = tool['name']

            # Must start with vibey_
            assert name.startswith('vibey_'), f"Tool {name} missing prefix"

            # Must be snake_case (no hyphens)
            assert '-' not in name, f"Tool {name} contains hyphen"

            # Must be valid identifier
            assert name.replace('_', '').isalnum(), f"Tool {name} has invalid chars"


class TestGooseRecipeGeneration:
    """Tests for Goose recipe generation from workflows."""

    @pytest.fixture
    def discovery(self):
        """Create discovery instance."""
        return ToolDiscovery(root_dir=PROJECT_ROOT, tool_prefix='vibey')

    def test_workflow_to_recipe_structure(self, discovery):
        """Test workflows can be converted to recipe structure."""
        workflows = discovery.workflow_discovery.discover()

        if not workflows:
            pytest.skip("No workflows found")

        workflow = workflows[0]

        # Build recipe structure
        recipe = {
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'version': workflow.version,
            'steps': []
        }

        # If workflow has steps, convert them (steps are WorkflowStep dataclass)
        if workflow.steps:
            for step in workflow.steps:
                recipe_step = {
                    'name': step.name or 'Unnamed',
                    'tool': f"vibey_{(step.agent or 'unknown').replace('-', '_')}",
                    'order': step.order
                }
                recipe['steps'].append(recipe_step)

        # Verify recipe structure
        assert recipe['id'] is not None
        assert recipe['name'] is not None
        assert recipe['version'] is not None

    def test_all_workflows_convertible(self, discovery):
        """Test all workflows can be converted to recipes."""
        workflows = discovery.workflow_discovery.discover()

        for workflow in workflows:
            # Each workflow should have required fields
            assert workflow.id, f"Workflow missing id"
            assert workflow.name, f"Workflow {workflow.id} missing name"
            assert workflow.version, f"Workflow {workflow.id} missing version"

            # Type should be valid
            valid_types = {'development', 'planning', 'quality', 'documentation',
                          'architecture', 'infrastructure', 'deployment'}
            assert workflow.type in valid_types, \
                f"Workflow {workflow.id} has invalid type: {workflow.type}"


class TestGooseToolInvocationFlow:
    """Tests simulating Goose's tool invocation flow."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(PROJECT_ROOT)
        )

    def test_tool_list_request(self, server):
        """Test tools/list request as Goose sends it."""
        # Goose calls get_tools() to list available tools
        tools = server.get_tools()

        # Response should be list of tool definitions
        assert isinstance(tools, list)

        # Each tool should have MCP-required fields
        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool

    @pytest.mark.asyncio
    async def test_tool_call_request(self, server):
        """Test tools/call request as Goose sends it."""
        # Goose calls handle_tool_call with name and arguments
        result = await server.handle_tool_call(
            'vibey_roadmap_status',
            {}  # Empty arguments for this tool
        )

        # Response should follow MCP CallToolResult format
        assert 'content' in result
        assert isinstance(result['content'], list)

        # isError should be present and False for success
        assert result.get('isError', False) is False

    @pytest.mark.asyncio
    async def test_invalid_tool_request(self, server):
        """Test invalid tool request handling."""
        result = await server.handle_tool_call(
            'nonexistent_tool_12345',
            {}
        )

        # Should return error response, not raise exception
        assert result.get('isError', True) is True
        assert 'content' in result

        # Error message should be helpful
        text = result['content'][0]['text']
        assert 'Unknown' in text or '❌' in text


class TestMCPProtocolMessages:
    """Tests for MCP protocol message handling."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(PROJECT_ROOT)
        )

    def test_initialize_capabilities(self, server):
        """Test initialize response capabilities."""
        caps = server.get_capabilities()

        # MCP capabilities structure
        assert 'tools' in caps
        assert 'resources' in caps
        assert 'prompts' in caps

        # Tools should report listChanged capability
        assert caps['tools'].get('listChanged') is True

    def test_tool_schema_mcp_compliant(self, server):
        """Test tool schemas are MCP-compliant JSON Schema."""
        tools = server.get_tools()

        for tool in tools:
            schema = tool['inputSchema']

            # Must be object type
            assert schema['type'] == 'object'

            # Must have properties
            assert 'properties' in schema

            # Properties must be dict
            assert isinstance(schema['properties'], dict)

            # Each property must have type
            for prop_name, prop_def in schema['properties'].items():
                assert 'type' in prop_def, \
                    f"Property {prop_name} in {tool['name']} missing type"

    @pytest.mark.asyncio
    async def test_content_type_text(self, server):
        """Test response content type is 'text'."""
        result = await server.handle_tool_call('vibey_roadmap_status', {})

        for content in result['content']:
            # Currently we only support text content
            assert content['type'] == 'text'
            assert 'text' in content
            assert isinstance(content['text'], str)


class TestGooseConfigurationValidation:
    """Tests validating Goose configuration setup."""

    def test_config_file_structure(self):
        """Test Goose config file can be generated correctly."""
        config = {
            'extensions': {
                'vibey': {
                    'name': 'vibey',
                    'type': 'stdio',
                    'cmd': str(PROJECT_ROOT / '.venv' / 'bin' / 'python'),
                    'args': [str(PROJECT_ROOT / 'scripts' / 'run-mcp-server.py')],
                    'enabled': True,
                    'timeout': 300,
                    'description': 'Vibey Agent Framework'
                }
            }
        }

        # Verify structure
        vibey_ext = config['extensions']['vibey']
        assert vibey_ext['type'] == 'stdio'
        assert vibey_ext['enabled'] is True
        assert vibey_ext['timeout'] > 0

    def test_server_script_exists(self):
        """Test MCP server module exists."""
        server_module = PROJECT_ROOT / 'vibey' / 'mcp' / 'server.py'
        assert server_module.exists(), f"Server module not found: {server_module}"

    def test_server_script_syntax(self):
        """Test MCP server module has valid Python syntax."""
        server_module = PROJECT_ROOT / 'vibey' / 'mcp' / 'server.py'

        if not server_module.exists():
            pytest.skip("Server module not found")

        # Check syntax by compiling
        with open(server_module) as f:
            code = f.read()

        try:
            compile(code, server_module, 'exec')
        except SyntaxError as e:
            pytest.fail(f"Server module has syntax error: {e}")


class TestPerformanceBaseline:
    """Performance baseline tests for Goose integration."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(PROJECT_ROOT)
        )

    def test_tool_list_performance(self, server):
        """Test tool listing completes quickly."""
        import time

        start = time.time()
        tools = server.get_tools()
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Tool listing took {elapsed:.2f}s (should be <1s)"

        # Verify we got tools
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_tool_call_performance(self, server):
        """Test tool invocation completes quickly."""
        import time

        start = time.time()
        result = await server.handle_tool_call('vibey_roadmap_status', {})
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0, f"Tool call took {elapsed:.2f}s (should be <2s)"

        # Verify we got result
        assert 'content' in result

    def test_discovery_caching(self, server):
        """Test discovery results are cached for performance."""
        import time

        # First call (may need to discover)
        start1 = time.time()
        tools1 = server.get_tools()
        elapsed1 = time.time() - start1

        # Second call (should use cache)
        start2 = time.time()
        tools2 = server.get_tools()
        elapsed2 = time.time() - start2

        # Second call should be faster (cached)
        # Allow for some variance
        assert elapsed2 <= elapsed1 + 0.1, \
            f"Second call ({elapsed2:.3f}s) slower than first ({elapsed1:.3f}s)"

        # Results should match
        assert len(tools1) == len(tools2)
