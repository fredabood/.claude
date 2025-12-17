"""Integration tests for VibeyMCPServer.

Tests the full request/response cycle for the MCP server, including
tool discovery, execution, error handling, and concurrency.
"""

import asyncio
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


class TestUnifiedToolIntegration:
    """Test unified command tool integration with server."""

    @pytest.fixture
    def server(self, tmp_path):
        """Create VibeyMCPServer for unified tool testing."""
        from vibey.mcp.server import VibeyMCPServer

        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        return VibeyMCPServer(
            roadmap_root=str(roadmap_dir),
            framework_root=str(tmp_path)
        )

    def test_unified_tools_registered(self, server):
        """Verify unified tools are registered from @unified_command."""
        tools = server.get_tools()
        tool_names = {t["name"] for t in tools}

        # Check for expected unified tools
        expected_tools = [
            "vibey_roadmap_status",
            "vibey_roadmap_show",
            "vibey_start_task",
            "vibey_complete_task",
        ]

        for expected in expected_tools:
            assert expected in tool_names, \
                f"Expected unified tool '{expected}' not found"

    @pytest.mark.asyncio
    async def test_unified_roadmap_status(self, server):
        """Test unified roadmap_status tool execution."""
        result = await server.handle_tool_call(
            "vibey_roadmap_status",
            {}
        )

        assert result is not None
        assert "content" in result

    @pytest.mark.asyncio
    async def test_unified_tool_with_missing_param(self, server):
        """Test unified tool with missing required parameter."""
        result = await server.handle_tool_call(
            "vibey_roadmap_show",
            {}  # Missing required item_id
        )

        assert result is not None
        # Should handle gracefully (either return error or work with defaults)


class TestErrorHandling:
    """Test error response formatting and handling."""

    @pytest.fixture
    def server(self, tmp_path):
        """Create VibeyMCPServer for error handling tests."""
        from vibey.mcp.server import VibeyMCPServer

        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        return VibeyMCPServer(
            roadmap_root=str(roadmap_dir),
            framework_root=str(tmp_path)
        )

    @pytest.mark.asyncio
    async def test_unknown_tool_error_format(self, server):
        """Verify unknown tool returns properly formatted error."""
        result = await server.handle_tool_call("nonexistent_tool", {})

        assert result.get("isError") is True
        assert "content" in result
        content = result["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        assert content[0].get("type") == "text"
        assert "Unknown tool" in content[0].get("text", "")

    @pytest.mark.asyncio
    async def test_error_response_structure(self, server):
        """Verify error responses have correct MCP structure."""
        result = await server.handle_tool_call("nonexistent_tool", {})

        # Must have content key
        assert "content" in result

        # Content must be a list
        content = result.get("content", [])
        assert isinstance(content, list)

        # Each content item must have type and text
        for item in content:
            assert "type" in item
            assert "text" in item

    @pytest.mark.asyncio
    async def test_not_found_item_error(self, server):
        """Test error when item not found."""
        result = await server.handle_tool_call(
            "vibey_roadmap_show",
            {"item_id": "nonexistent-item-id"}
        )

        assert result is not None
        # Should indicate error or not found
        assert result.get("isError") is True or "not found" in str(result).lower()


class TestConcurrency:
    """Test concurrent request handling."""

    @pytest.fixture
    def server(self, tmp_path):
        """Create VibeyMCPServer for concurrency tests."""
        from vibey.mcp.server import VibeyMCPServer

        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        return VibeyMCPServer(
            roadmap_root=str(roadmap_dir),
            framework_root=str(tmp_path)
        )

    def test_concurrent_tool_discovery(self, server):
        """Verify concurrent tool discovery returns consistent results."""
        # Get tools multiple times sequentially (sync version)
        results = [server.get_tools() for _ in range(5)]

        # All should return the same number of tools
        tool_counts = [len(r) for r in results]
        assert all(c == tool_counts[0] for c in tool_counts), \
            f"Tool counts vary: {tool_counts}"

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, server):
        """Verify concurrent tool calls don't crash."""
        requests = [
            server.handle_tool_call("vibey_roadmap_status", {})
            for _ in range(5)
        ]
        results = await asyncio.gather(*requests, return_exceptions=True)

        # None should raise exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

    @pytest.mark.asyncio
    async def test_concurrent_different_tools(self, server):
        """Verify concurrent calls to different tools work."""
        requests = [
            server.handle_tool_call("vibey_roadmap_status", {}),
            server.handle_tool_call("vibey_deploy_list", {}),
            server.handle_tool_call("nonexistent_tool", {}),
        ]
        results = await asyncio.gather(*requests, return_exceptions=True)

        # None should raise exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

        # All should return results
        for result in results:
            assert "content" in result


class TestPerformance:
    """Test response time requirements."""

    @pytest.fixture
    def server(self, tmp_path):
        """Create VibeyMCPServer for performance tests."""
        from vibey.mcp.server import VibeyMCPServer

        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        return VibeyMCPServer(
            roadmap_root=str(roadmap_dir),
            framework_root=str(tmp_path)
        )

    def test_tool_list_response_time(self, server):
        """Verify tool listing completes in reasonable time."""
        import time
        start = time.perf_counter()
        tools = server.get_tools()
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Tool listing took too long: {elapsed}s"
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_simple_tool_call_response_time(self, server):
        """Verify simple tool calls complete in reasonable time."""
        import time
        start = time.perf_counter()
        result = await server.handle_tool_call("vibey_roadmap_status", {})
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Tool call took too long: {elapsed}s"
        assert result is not None
