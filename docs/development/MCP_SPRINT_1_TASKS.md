# MCP Server Foundation - Sprint 1 Task Breakdown

**Sprint:** mcp-server-1
**Sprint Name:** MCP Protocol Integration
**Duration:** 2 weeks
**Track:** mcp-server
**Priority:** Critical

---

## Sprint Goal

Establish the foundational MCP server infrastructure for Vibey, including:
- Working MCP server scaffold using Python SDK
- JSON-RPC 2.0 communication over stdio
- Capability negotiation and lifecycle management
- 3-4 basic roadmap management tools functional
- Adapter pattern for integration with existing roadmap system

---

## Tasks

### Task 001: MCP Python SDK Setup & Environment Configuration

**ID:** `mcp-server-1-task-001`
**Title:** MCP Python SDK Setup & Environment Configuration
**Type:** Development
**Priority:** Critical
**Estimated Tokens:** 2,000
**Complexity:** Low

**Description:**
Set up the development environment for MCP server development, including installing the official MCP Python SDK, configuring the project structure, and setting up testing infrastructure.

**Acceptance Criteria:**
- ✅ MCP Python SDK installed (`pip install mcp`)
- ✅ Project structure created (`framework/mcp/` directory)
- ✅ `requirements.txt` updated with MCP dependencies
- ✅ Basic test infrastructure set up (pytest)
- ✅ Development environment documented

**Dependencies:** None

**Deliverables:**
- `framework/mcp/` directory structure
- Updated `requirements.txt`
- `framework/mcp/tests/` with pytest configuration
- `docs/development/MCP_DEVELOPMENT_SETUP.md`

---

### Task 002: Basic MCP Server Scaffold

**ID:** `mcp-server-1-task-002`
**Title:** Basic MCP Server Scaffold
**Type:** Development
**Priority:** Critical
**Estimated Tokens:** 4,000
**Complexity:** Medium

**Description:**
Create the basic MCP server scaffold that handles initialization, capability negotiation, and lifecycle management. The server should accept JSON-RPC 2.0 messages over stdio and respond correctly to MCP protocol handshake.

**Acceptance Criteria:**
- ✅ Server initializes and listens on stdio
- ✅ Handles `initialize` request with capability negotiation
- ✅ Returns server capabilities (tools support with `listChanged: true`)
- ✅ Handles `initialized` notification
- ✅ Handles graceful shutdown
- ✅ Logs all protocol messages for debugging

**Dependencies:**
- Task 001 (MCP SDK setup)

**Implementation Notes:**
```python
# framework/mcp/server.py

from mcp import Server
from mcp.types import (
    InitializeRequest,
    ServerCapabilities,
    Tool,
)

class VibeyMCPServer:
    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        self.server = Server("vibey-roadmap")
        self.roadmap_root = Path(roadmap_root)
        self._register_handlers()

    def _register_handlers(self):
        @self.server.initialize()
        async def handle_initialize(params: InitializeRequest):
            return ServerCapabilities(
                tools=ToolsCapability(listChanged=True),
                resources=ResourcesCapability(subscribe=True),
                prompts=PromptsCapability(listChanged=False)
            )

    async def run(self):
        async with stdio_server() as streams:
            await self.server.run(streams[0], streams[1])
```

**Deliverables:**
- `framework/mcp/server.py` - Main server implementation
- `framework/mcp/__init__.py` - Package initialization
- `framework/mcp/tests/test_server.py` - Basic server tests

---

### Task 003: Roadmap Adapter Layer

**ID:** `mcp-server-1-task-003`
**Title:** Roadmap Adapter Layer
**Type:** Development
**Priority:** Critical
**Estimated Tokens:** 5,000
**Complexity:** Medium

**Description:**
Create an adapter layer that bridges the MCP server with Vibey's existing roadmap system. This adapter should provide a clean interface for roadmap operations without duplicating business logic.

**Acceptance Criteria:**
- ✅ `RoadmapAdapter` class created
- ✅ Wraps existing roadmap-update.py functionality
- ✅ Wraps existing roadmap-query.py functionality
- ✅ Handles file system operations via FileSystemManager
- ✅ Proper error handling and validation
- ✅ Unit tests for adapter methods

**Dependencies:**
- Task 002 (Server scaffold)

**Implementation Notes:**
```python
# framework/mcp/adapters/roadmap_adapter.py

from pathlib import Path
from datetime import datetime, timezone
from framework.roadmap.models import Sprint, Track, Task
from framework.roadmap.serialization import load_task, save_task, load_sprint
from framework.scripts.roadmap_lib.filesystem import FileSystemManager
from framework.scripts.roadmap_lib.status import StatusManager

class RoadmapAdapter:
    """Adapter between MCP server and Vibey roadmap system."""

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        self.root = Path(roadmap_root)
        self.fs = FileSystemManager(self.root)
        self.status_manager = StatusManager(self.root)

    def start_task(self, task_id: str) -> dict:
        """Start a task."""
        task_path = self.fs.get_task_path(task_id)
        task = load_task(task_path)

        task.status = Status.IN_PROGRESS
        task.started = datetime.now(timezone.utc)

        save_task(task, task_path)
        self._update_sprint_progress(task.sprint_id)

        return {
            "success": True,
            "task_id": task_id,
            "status": "in_progress"
        }

    def complete_task(self, task_id: str, actual_tokens: int = None) -> dict:
        """Complete a task."""
        # Similar pattern
        pass

    def query_task(self, task_id: str) -> dict:
        """Query task details."""
        task_path = self.fs.get_task_path(task_id)
        task = load_task(task_path)
        return task.to_dict()
```

**Deliverables:**
- `framework/mcp/adapters/roadmap_adapter.py` - Main adapter
- `framework/mcp/adapters/__init__.py` - Package initialization
- `framework/mcp/tests/test_roadmap_adapter.py` - Adapter tests

---

### Task 004: Task Management Tools Implementation

**ID:** `mcp-server-1-task-004`
**Title:** Task Management Tools Implementation
**Type:** Development
**Priority:** High
**Estimated Tokens:** 4,000
**Complexity:** Medium

**Description:**
Implement the three core task management tools: `vibey_start_task`, `vibey_complete_task`, and `vibey_query_task`. These tools should use the adapter layer and follow MCP tool specification.

**Acceptance Criteria:**
- ✅ `vibey_start_task` tool implemented
- ✅ `vibey_complete_task` tool implemented
- ✅ `vibey_query_task` tool implemented
- ✅ All tools registered with server
- ✅ Input validation via JSON Schema
- ✅ Proper error responses with `isError: true`
- ✅ Integration tests for each tool

**Dependencies:**
- Task 003 (Adapter layer)

**Implementation Notes:**
```python
# framework/mcp/tools/task_tools.py

from mcp.types import Tool, TextContent

def get_task_tools() -> list[Tool]:
    """Get task management tool definitions."""
    return [
        Tool(
            name="vibey_start_task",
            title="Start Task",
            description="Mark a task as in progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID (e.g., 'mcp-server-1-task-001')"
                    }
                },
                "required": ["task_id"]
            }
        ),
        # ... other tools
    ]

async def handle_start_task(adapter: RoadmapAdapter, arguments: dict) -> dict:
    """Handle vibey_start_task tool call."""
    task_id = arguments["task_id"]

    try:
        result = adapter.start_task(task_id)
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"✅ Task '{task_id}' started successfully"
                )
            ],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"❌ Error starting task: {str(e)}"
                )
            ],
            "isError": True
        }
```

**Deliverables:**
- `framework/mcp/tools/task_tools.py` - Task tool definitions and handlers
- `framework/mcp/tools/__init__.py` - Package initialization
- `framework/mcp/tests/test_task_tools.py` - Task tool tests

---

### Task 005: Tool Registration & Lifecycle Management

**ID:** `mcp-server-1-task-005`
**Title:** Tool Registration & Lifecycle Management
**Type:** Development
**Priority:** High
**Estimated Tokens:** 3,000
**Complexity:** Medium

**Description:**
Implement the tool registration system and lifecycle management, including handling `tools/list` requests, `tools/call` invocations, and tool change notifications.

**Acceptance Criteria:**
- ✅ Server responds to `tools/list` requests
- ✅ Server handles `tools/call` requests
- ✅ Tool routing dispatches to correct handler
- ✅ Tool change notifications work (if tools added dynamically)
- ✅ Proper error handling for unknown tools
- ✅ Integration tests for tool lifecycle

**Dependencies:**
- Task 004 (Task tools)

**Implementation Notes:**
```python
# In framework/mcp/server.py

def _register_tool_handlers(self):
    @self.server.list_tools()
    async def handle_list_tools():
        tools = []
        tools.extend(get_task_tools())
        # More tools in future sprints
        return tools

    @self.server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        if name == "vibey_start_task":
            return await handle_start_task(self.adapter, arguments)
        elif name == "vibey_complete_task":
            return await handle_complete_task(self.adapter, arguments)
        elif name == "vibey_query_task":
            return await handle_query_task(self.adapter, arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
```

**Deliverables:**
- Updated `framework/mcp/server.py` with tool handlers
- `framework/mcp/tests/test_tool_lifecycle.py` - Lifecycle tests

---

### Task 006: Error Handling & Validation

**ID:** `mcp-server-1-task-006`
**Title:** Error Handling & Validation
**Type:** Development
**Priority:** High
**Estimated Tokens:** 3,000
**Complexity:** Medium

**Description:**
Implement comprehensive error handling and validation throughout the MCP server, including input validation, state validation, and proper error responses.

**Acceptance Criteria:**
- ✅ All tool inputs validated against JSON schemas
- ✅ File system errors handled gracefully
- ✅ State validation errors return descriptive messages
- ✅ All errors return proper MCP error responses
- ✅ Logging infrastructure for debugging
- ✅ Error handling tests

**Dependencies:**
- Task 005 (Tool registration)

**Implementation Notes:**
```python
# framework/mcp/utils/validation.py

from jsonschema import validate, ValidationError

def validate_tool_input(tool_name: str, arguments: dict, schema: dict) -> None:
    """Validate tool input against JSON schema."""
    try:
        validate(instance=arguments, schema=schema)
    except ValidationError as e:
        raise ValueError(f"Invalid input for {tool_name}: {e.message}")

# framework/mcp/utils/errors.py

class VibeyMCPError(Exception):
    """Base exception for Vibey MCP server."""
    pass

class TaskNotFoundError(VibeyMCPError):
    """Task not found."""
    pass

class InvalidTaskStateError(VibeyMCPError):
    """Invalid task state transition."""
    pass
```

**Deliverables:**
- `framework/mcp/utils/validation.py` - Validation utilities
- `framework/mcp/utils/errors.py` - Custom exception classes
- `framework/mcp/utils/__init__.py` - Package initialization
- `framework/mcp/tests/test_validation.py` - Validation tests

---

### Task 007: Integration Testing & MCP Inspector

**ID:** `mcp-server-1-task-007`
**Title:** Integration Testing & MCP Inspector
**Type:** Testing
**Priority:** High
**Estimated Tokens:** 3,000
**Complexity:** Medium

**Description:**
Create comprehensive integration tests for the MCP server and test with the official MCP Inspector tool to validate protocol compliance.

**Acceptance Criteria:**
- ✅ Integration tests cover full tool invocation flow
- ✅ Tests validate server initialization
- ✅ Tests validate capability negotiation
- ✅ Tests validate tool list/call operations
- ✅ MCP Inspector successfully connects to server
- ✅ All tools visible and invokable in Inspector
- ✅ Test documentation created

**Dependencies:**
- Task 006 (Error handling)

**Testing Approach:**
```python
# framework/mcp/tests/test_integration.py

import pytest
from mcp.client import Client

@pytest.mark.asyncio
async def test_server_initialization():
    """Test server initializes correctly."""
    async with create_test_server() as server:
        # Send initialize request
        response = await server.request("initialize", {
            "protocolVersion": "2025-06-18",
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })

        assert response["protocolVersion"] == "2025-06-18"
        assert "tools" in response["capabilities"]

@pytest.mark.asyncio
async def test_start_task_tool():
    """Test vibey_start_task tool."""
    async with create_test_server() as server:
        # List tools
        tools = await server.request("tools/list", {})
        assert any(t["name"] == "vibey_start_task" for t in tools["tools"])

        # Call tool
        result = await server.request("tools/call", {
            "name": "vibey_start_task",
            "arguments": {"task_id": "test-sprint-1-task-001"}
        })

        assert result["isError"] == False
        assert "started successfully" in result["content"][0]["text"]
```

**Manual Testing:**
```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run server with inspector
mcp-inspector python framework/mcp/server.py
```

**Deliverables:**
- `framework/mcp/tests/test_integration.py` - Integration tests
- `docs/development/MCP_TESTING_GUIDE.md` - Testing documentation
- Test reports and coverage metrics

---

### Task 008: Documentation & Examples

**ID:** `mcp-server-1-task-008`
**Title:** Sprint 1 Documentation & Examples
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 2,000
**Complexity:** Low

**Description:**
Create documentation for Sprint 1 deliverables, including architecture overview, usage examples, and development guide.

**Acceptance Criteria:**
- ✅ Architecture documentation complete
- ✅ Tool usage examples provided
- ✅ Development setup guide updated
- ✅ Testing guide created
- ✅ README for `framework/mcp/` directory

**Dependencies:**
- Task 007 (Integration testing)

**Deliverables:**
- `framework/mcp/README.md` - MCP server overview
- `docs/development/MCP_ARCHITECTURE.md` - Architecture details
- `docs/development/MCP_USAGE_EXAMPLES.md` - Usage examples
- Updated `docs/development/MCP_DEVELOPMENT_SETUP.md`

---

## Sprint Summary

### Total Tasks: 8

**By Priority:**
- Critical: 3 tasks (001, 002, 003)
- High: 4 tasks (004, 005, 006, 007)
- Medium: 1 task (008)

**By Type:**
- Development: 6 tasks
- Testing: 1 task
- Documentation: 1 task

**By Complexity:**
- Low: 2 tasks
- Medium: 6 tasks

### Estimated Effort

- **Total Estimated Tokens:** 26,000 tokens
- **Duration:** 2 weeks
- **Team Size:** 2-3 developers
- **Hours:** ~80 hours total (~40 hours/week @ 2 devs)

### Dependency Chain

```
001 (SDK Setup)
  ↓
002 (Server Scaffold)
  ↓
003 (Adapter Layer)
  ↓
004 (Task Tools)
  ↓
005 (Tool Registration)
  ↓
006 (Error Handling)
  ↓
007 (Integration Testing)
  ↓
008 (Documentation)
```

### Success Criteria

Sprint 1 is considered complete when:

1. ✅ MCP server scaffold is functional
2. ✅ Server successfully negotiates capabilities with MCP clients
3. ✅ 3 task management tools work end-to-end
4. ✅ Adapter layer successfully integrates with existing roadmap system
5. ✅ MCP Inspector can connect and invoke tools
6. ✅ All unit and integration tests pass
7. ✅ Code coverage >70%
8. ✅ Documentation complete

---

## Risk Assessment

### High Risk

1. **MCP SDK Learning Curve** - Team may be unfamiliar with MCP Python SDK
   - Mitigation: Allocate time for SDK exploration, review examples

2. **Protocol Compliance** - Ensuring full MCP 2025-06-18 spec compliance
   - Mitigation: Use MCP Inspector for validation, follow official examples

### Medium Risk

3. **Adapter Complexity** - Integration with existing roadmap system may have edge cases
   - Mitigation: Start with simple operations, add complexity iteratively

4. **Error Handling** - Comprehensive error handling across all layers
   - Mitigation: Define error taxonomy early, test error paths

### Low Risk

5. **Testing Infrastructure** - Setting up pytest and MCP testing
   - Mitigation: Standard Python testing patterns, well-documented

---

## Post-Sprint Activities

After Sprint 1 completion:

1. **Sprint Retrospective** - Review what went well, what didn't
2. **Sprint 2 Planning** - Plan remaining roadmap tools (sprint management, query tools)
3. **Documentation Review** - Ensure all docs are current and accurate
4. **Demo** - Demonstrate MCP server working with MCP Inspector

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Sprint Start Date:** TBD
**Sprint End Date:** TBD (2 weeks after start)
