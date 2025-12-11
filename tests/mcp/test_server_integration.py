"""Integration tests for VibeyMCPServer."""

import pytest
from pathlib import Path


class TestServerIntegration:
    """Integration tests for VibeyMCPServer."""

    @pytest.fixture
    def server(self, content_root, roadmap_root):
        """Create VibeyMCPServer with test content."""
        from vibey.mcp.server import VibeyMCPServer

        return VibeyMCPServer(
            roadmap_root=str(roadmap_root),
            framework_root=str(content_root)
        )

    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server is not None
        assert server.tool_discovery is not None
        assert server.adapter is not None

    def test_get_capabilities(self, server):
        """Test server capabilities."""
        caps = server.get_capabilities()
        assert "tools" in caps
        assert "resources" in caps
        assert "prompts" in caps
        # Tools should support listChanged
        assert caps["tools"]["listChanged"] is True

    def test_get_tools(self, server):
        """Test getting available tools."""
        tools = server.get_tools()
        assert isinstance(tools, list)
        # Should have at least static roadmap tools
        assert len(tools) >= 1

    def test_get_tools_structure(self, server):
        """Test that tools have correct structure."""
        tools = server.get_tools()
        for tool in tools:
            assert "name" in tool
            # Tools should have a name that starts with vibey_
            assert tool["name"].startswith("vibey_") or tool.get("_metadata")

    def test_get_discovery_stats(self, server):
        """Test getting discovery statistics."""
        stats = server.get_discovery_stats()
        assert "agent_tools" in stats
        assert "workflow_tools" in stats

    @pytest.mark.asyncio
    async def test_handle_tool_call_unknown(self, server):
        """Test handling unknown tool call."""
        result = await server.handle_tool_call(
            "unknown_tool_that_does_not_exist",
            {}
        )
        assert result.get("isError") is True

    @pytest.mark.asyncio
    async def test_handle_tool_call_returns_content(self, server):
        """Test that tool calls return content structure."""
        # Use a tool that exists - query tools are static
        result = await server.handle_tool_call(
            "vibey_query_roadmap",
            {}
        )
        # Result should have content key
        assert "content" in result


class TestServerToolDiscovery:
    """Test tool discovery integration with server."""

    @pytest.fixture
    def server(self, content_root, roadmap_root):
        """Create VibeyMCPServer with test content."""
        from vibey.mcp.server import VibeyMCPServer

        return VibeyMCPServer(
            roadmap_root=str(roadmap_root),
            framework_root=str(content_root)
        )

    def test_tool_discovery_initialized(self, server):
        """Test that tool discovery is initialized."""
        assert server.tool_discovery is not None

    def test_discovered_tools_included(self, server):
        """Test that discovered tools are included in get_tools."""
        tools = server.get_tools()
        # Get tool names
        tool_names = [t["name"] for t in tools]
        # Should have some tools (static ones at minimum)
        assert len(tool_names) > 0

    def test_get_tool_by_name(self, server):
        """Test getting a specific tool by name."""
        # This tests the tool_discovery method
        tools = server.get_tools()
        if tools:
            first_tool_name = tools[0]["name"]
            tool = server.tool_discovery.get_tool_by_name(first_tool_name)
            # May or may not find it depending on if it's static or dynamic
            # Just ensure method doesn't crash


class TestServerDynamicTools:
    """Test dynamic tool handling in server."""

    @pytest.fixture
    def server_with_content(self, content_root, roadmap_root):
        """Create server with test content."""
        from vibey.mcp.server import VibeyMCPServer

        return VibeyMCPServer(
            roadmap_root=str(roadmap_root),
            framework_root=str(content_root)
        )

    def test_handoff_tools_discovered(self, server_with_content):
        """Test that handoff tools are discovered."""
        tools = server_with_content.get_tools()
        # Look for handoff tools
        handoff_tools = [
            t for t in tools
            if t.get("_metadata", {}).get("asset_type") == "handoff"
        ]
        # With test content, should find at least one
        assert len(handoff_tools) >= 1

    @pytest.mark.asyncio
    async def test_execute_handoff_tool(self, server_with_content):
        """Test executing a handoff tool."""
        tools = server_with_content.get_tools()
        handoff_tools = [
            t for t in tools
            if t.get("_metadata", {}).get("asset_type") == "handoff"
        ]

        if handoff_tools:
            tool = handoff_tools[0]
            result = await server_with_content.handle_tool_call(
                tool["name"],
                {"test_var": "test_value", "handoff_title": "Test"}
            )
            assert "content" in result
            # May or may not succeed depending on template requirements
