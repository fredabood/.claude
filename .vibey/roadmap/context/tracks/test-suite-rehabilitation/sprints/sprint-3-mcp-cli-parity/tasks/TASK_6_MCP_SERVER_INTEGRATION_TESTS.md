# Task 6: Add MCP Server Integration Tests

## Task Metadata
- **ID:** `01KCMGW5F2CF5XNFPWBGF9YZH0`
- **Sprint:** Sprint 3: MCP/CLI Parity & Integration Tests
- **Priority:** High
- **Complexity:** Complex
- **Type:** Testing
- **Estimated Effort:** 4-6 hours

## Objective
Create comprehensive integration tests for the MCP server that test the full request/response cycle, including tool discovery, execution, and error handling.

## Current State Analysis

### MCP Server Location
- Main server: `vibey/mcp/server.py`
- Uses FastMCP or similar framework
- Handles `tools/list`, `tools/call`, and other MCP protocol methods

### Key Components to Test
1. Server initialization
2. Tool discovery (`tools/list`)
3. Tool execution (`tools/call`)
4. Request validation
5. Response formatting
6. Error handling
7. Concurrent request handling

## Implementation Steps

### Step 1: Create Integration Test Infrastructure
**File:** `tests/mcp/test_server_integration.py`
```python
import pytest
import asyncio
from pathlib import Path

@pytest.fixture
def mcp_server(tmp_path):
    """Create MCP server instance for testing."""
    from vibey.mcp.server import create_server

    # Set up test environment
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)

    server = create_server(root_dir=tmp_path)
    return server

@pytest.fixture
def sample_roadmap(tmp_path):
    """Create sample roadmap data for integration tests."""
    # Create tracks, sprints, tasks YAML files
    # Initialize database
    pass
```

### Step 2: Test Tool Discovery
```python
class TestToolDiscovery:
    """Test tools/list functionality."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/list",
            "params": {}
        })
        assert "tools" in response
        assert len(response["tools"]) > 0

    @pytest.mark.asyncio
    async def test_tools_have_required_fields(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/list",
            "params": {}
        })
        for tool in response["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    @pytest.mark.asyncio
    async def test_unified_tools_included(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/list",
            "params": {}
        })
        tool_names = [t["name"] for t in response["tools"]]
        # Check unified tools are present
        assert "vibey_roadmap_status" in tool_names
        assert "vibey_roadmap_show" in tool_names
```

### Step 3: Test Tool Execution
```python
class TestToolExecution:
    """Test tools/call functionality."""

    @pytest.mark.asyncio
    async def test_call_roadmap_status(self, mcp_server, sample_roadmap):
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "vibey_roadmap_status",
                "arguments": {}
            }
        })
        assert "content" in response or "result" in response

    @pytest.mark.asyncio
    async def test_call_with_parameters(self, mcp_server, sample_roadmap):
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "vibey_roadmap_show",
                "arguments": {"item_id": "test-task-id"}
            }
        })
        # Verify response structure
        pass

    @pytest.mark.asyncio
    async def test_call_unknown_tool_returns_error(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        })
        assert "error" in response
```

### Step 4: Test Request Validation
```python
class TestRequestValidation:
    """Test MCP protocol request validation."""

    @pytest.mark.asyncio
    async def test_missing_method_returns_error(self, mcp_server):
        response = await mcp_server.handle_request({
            "params": {}
        })
        assert "error" in response

    @pytest.mark.asyncio
    async def test_invalid_method_returns_error(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "invalid/method",
            "params": {}
        })
        assert "error" in response

    @pytest.mark.asyncio
    async def test_missing_required_argument(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "vibey_roadmap_show",
                "arguments": {}  # Missing required item_id
            }
        })
        assert "error" in response
```

### Step 5: Test Error Handling
```python
class TestErrorHandling:
    """Test error response formatting."""

    @pytest.mark.asyncio
    async def test_not_found_error_format(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "vibey_roadmap_show",
                "arguments": {"item_id": "nonexistent"}
            }
        })
        assert "error" in response
        # Verify error has proper structure

    @pytest.mark.asyncio
    async def test_validation_error_format(self, mcp_server):
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "vibey_roadmap_start",
                "arguments": {"item_id": "invalid-format"}
            }
        })
        # Verify validation error response
        pass

    @pytest.mark.asyncio
    async def test_internal_error_handled_gracefully(self, mcp_server, mocker):
        # Mock an internal error
        mocker.patch(
            "vibey.operations.roadmap.status.get_roadmap_status",
            side_effect=Exception("Internal error")
        )
        response = await mcp_server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "vibey_roadmap_status",
                "arguments": {}
            }
        })
        assert "error" in response
        # Should not expose stack trace
```

### Step 6: Test Concurrent Requests
```python
class TestConcurrency:
    """Test concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_server, sample_roadmap):
        # Execute multiple requests concurrently
        requests = [
            mcp_server.handle_request({
                "method": "tools/call",
                "params": {"name": "vibey_roadmap_status", "arguments": {}}
            })
            for _ in range(10)
        ]
        responses = await asyncio.gather(*requests)

        # All should succeed
        for response in responses:
            assert "error" not in response

    @pytest.mark.asyncio
    async def test_no_state_corruption_under_concurrency(self, mcp_server, sample_roadmap):
        # Test that concurrent writes don't corrupt state
        pass
```

### Step 7: Test Performance
```python
class TestPerformance:
    """Test response time requirements."""

    @pytest.mark.asyncio
    async def test_tool_list_response_time(self, mcp_server):
        import time
        start = time.perf_counter()
        await mcp_server.handle_request({
            "method": "tools/list",
            "params": {}
        })
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0  # Should be under 1 second

    @pytest.mark.asyncio
    async def test_simple_tool_call_response_time(self, mcp_server):
        import time
        start = time.perf_counter()
        await mcp_server.handle_request({
            "method": "tools/call",
            "params": {"name": "vibey_roadmap_status", "arguments": {}}
        })
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0  # Should be under 2 seconds
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/mcp/test_server_integration.py` | Create | Main integration tests |
| `tests/mcp/conftest.py` | Modify | Add server fixtures |

## Acceptance Criteria

- [ ] Tool discovery (`tools/list`) tested
- [ ] Tool execution (`tools/call`) tested for multiple tools
- [ ] Request validation tested (missing/invalid params)
- [ ] Error handling tested (not found, validation, internal)
- [ ] Concurrent request handling tested
- [ ] Response times acceptable (<2s for simple operations)
- [ ] All tests pass in CI

## Test Execution
```bash
# Run integration tests
pytest tests/mcp/test_server_integration.py -v

# Run with timing info
pytest tests/mcp/test_server_integration.py -v --durations=10
```

## Dependencies
- pytest
- pytest-asyncio
- pytest-mock (for error simulation)

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Server startup overhead | Use session-scoped fixtures |
| Test isolation | Fresh tmp_path for each test |
| Async complexity | Consistent use of pytest-asyncio |
| Flaky timing tests | Use reasonable thresholds, retry logic |
