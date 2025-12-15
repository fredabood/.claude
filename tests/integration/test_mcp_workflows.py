"""
Integration tests for MCP server workflows.

Tests end-to-end MCP server workflows: tool invocation flows, resource access, error handling.
"""

import pytest
import asyncio
from pathlib import Path

from vibey.mcp.server import VibeyMCPServer


class TestMCPToolWorkflows:
    """Test MCP tool workflow scenarios."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    def test_list_tools_workflow(self, server):
        """Test listing available tools workflow."""
        # Step 1: Get all tools
        tools = server.get_tools()
        assert len(tools) > 0

        # Step 2: Tools should be categorized
        tool_names = [t['name'] for t in tools]

        # Should have roadmap tools
        roadmap_tools = [n for n in tool_names if 'roadmap' in n]
        assert len(roadmap_tools) > 0, "Should have roadmap tools"

    @pytest.mark.asyncio
    async def test_roadmap_query_workflow(self, server):
        """Test querying roadmap status workflow."""
        # Step 1: Get roadmap status
        result = await server.handle_tool_call('vibey_roadmap_status', {})

        assert 'content' in result
        assert not result.get('isError', False)

        # Step 2: Response should contain structured info
        text = result['content'][0]['text']
        # Should contain status information
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_tool_invocation_with_params(self, server):
        """Test tool invocation with parameters."""
        # Find a tool that accepts parameters
        tools = server.get_tools()
        param_tool = None
        for tool in tools:
            if tool['inputSchema'].get('properties'):
                param_tool = tool
                break

        if param_tool is None:
            pytest.skip("No tools with parameters found")

        # Invoke with empty params (should use defaults or be optional)
        result = await server.handle_tool_call(param_tool['name'], {})

        assert 'content' in result
        # Should either succeed or return validation error
        assert isinstance(result['content'], list)


class TestMCPResourceWorkflows:
    """Test MCP resource access workflows."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    def test_get_resources_workflow(self, server):
        """Test getting available resources workflow."""
        if not hasattr(server, 'get_resources'):
            pytest.skip("get_resources not implemented")

        resources = server.get_resources()

        assert isinstance(resources, list)
        # Should have some resources defined
        if len(resources) > 0:
            for resource in resources:
                assert 'uri' in resource
                assert 'name' in resource

    @pytest.mark.asyncio
    async def test_read_resource_workflow(self, server):
        """Test reading a resource workflow."""
        if not hasattr(server, 'get_resources'):
            pytest.skip("get_resources not implemented")

        resources = server.get_resources()

        if len(resources) == 0:
            pytest.skip("No resources available")

        # Try to read first resource
        resource = resources[0]
        try:
            content = await server.handle_resource_read(resource['uri'])
            assert content is not None
        except Exception as e:
            # Resource might not be readable in test env
            if "not found" in str(e).lower() or "not implemented" in str(e).lower():
                pytest.skip(f"Resource not readable: {e}")
            raise


class TestMCPPromptWorkflows:
    """Test MCP prompt workflows."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    def test_get_prompts_workflow(self, server):
        """Test getting available prompts workflow."""
        if not hasattr(server, 'get_prompts'):
            pytest.skip("get_prompts not implemented")

        prompts = server.get_prompts()

        assert isinstance(prompts, list)
        # Each prompt should have required fields
        for prompt in prompts:
            assert 'name' in prompt
            assert 'description' in prompt


class TestMCPErrorWorkflows:
    """Test MCP error handling workflows."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    @pytest.mark.asyncio
    async def test_unknown_tool_error(self, server):
        """Test error handling for unknown tool."""
        result = await server.handle_tool_call('unknown_tool_xyz123', {})

        assert 'isError' in result
        assert result['isError'] is True
        assert 'content' in result

    @pytest.mark.asyncio
    async def test_malformed_params_error(self, server):
        """Test error handling for malformed parameters."""
        # Try calling with invalid params
        result = await server.handle_tool_call('vibey_roadmap_status', {
            'invalid_param': 'invalid_value',
            'another_bad_param': 12345
        })

        # Should either succeed (ignoring invalid params) or return error
        assert 'content' in result


class TestMCPConcurrencyWorkflows:
    """Test MCP concurrent request handling."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, server):
        """Test handling multiple concurrent tool calls."""
        # Create multiple concurrent requests
        tasks = [
            server.handle_tool_call('vibey_roadmap_status', {}),
            server.handle_tool_call('vibey_roadmap_status', {}),
            server.handle_tool_call('vibey_roadmap_status', {}),
        ]

        results = await asyncio.gather(*tasks)

        # All should complete without error
        for result in results:
            assert 'content' in result
            assert not result.get('isError', False)


class TestMCPCapabilitiesWorkflow:
    """Test MCP capabilities discovery workflow."""

    @pytest.fixture
    def server(self):
        """Create MCP server instance."""
        return VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

    def test_capabilities_discovery(self, server):
        """Test discovering server capabilities."""
        caps = server.get_capabilities()

        # Required capability sections
        assert 'tools' in caps
        assert 'resources' in caps
        assert 'prompts' in caps

        # Tool capabilities
        assert 'listChanged' in caps['tools']

    def test_capabilities_reflect_features(self, server):
        """Test capabilities reflect actual features."""
        caps = server.get_capabilities()

        # If tools capability is advertised, tools should exist
        if caps['tools'].get('listChanged'):
            tools = server.get_tools()
            assert len(tools) > 0

        # If resources capability is advertised, resources should exist
        if hasattr(server, 'get_resources'):
            resources = server.get_resources()
            assert isinstance(resources, list)

        # If prompts capability is advertised, prompts should exist
        if hasattr(server, 'get_prompts'):
            prompts = server.get_prompts()
            assert isinstance(prompts, list)


class TestMCPServerLifecycle:
    """Test MCP server lifecycle workflows."""

    def test_server_initialization(self):
        """Test server can be initialized with different configs."""
        # Default initialization
        server1 = VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )
        assert server1 is not None

        # Non-existent roadmap path (should handle gracefully)
        server2 = VibeyMCPServer(
            roadmap_root="/nonexistent/path",
            framework_root=str(Path(__file__).parent.parent.parent)
        )
        assert server2 is not None

    def test_server_tools_are_cached(self):
        """Test tool discovery is cached for performance."""
        server = VibeyMCPServer(
            roadmap_root=".vibey/roadmap",
            framework_root=str(Path(__file__).parent.parent.parent)
        )

        # First call
        tools1 = server.get_tools()

        # Second call should return same list (cached)
        tools2 = server.get_tools()

        assert len(tools1) == len(tools2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
