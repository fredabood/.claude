# Platform Integrator Journey

> Connecting AI assistants to Vibey via MCP

**Persona:** Sam the Platform Integrator
**Duration:** Project-based integration work

---

## Journey Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PLATFORM INTEGRATOR JOURNEY                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Discovery   │ Setup       │ Integration │ Testing     │ Production          │
│ (2-4 hrs)   │ (2-4 hrs)   │ (1-2 days)  │ (1 day)     │ (ongoing)           │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ - Read MCP  │ - Install   │ - Connect   │ - Test      │ - Monitor           │
│   reference │   server    │   client    │   tools     │ - Update            │
│ - Plan      │ - Configure │ - Call      │ - Verify    │ - Extend            │
│   integration│ - Verify   │   tools     │   flow      │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

---

## Phase 1: Discovery

**Duration:** 2-4 hours
**Goal:** Understand MCP server capabilities

### Key Documentation

1. **docs/reference/MCP_REFERENCE.md** - Complete tool/resource/prompt reference
2. **MCP Protocol Spec** - https://modelcontextprotocol.io/
3. **vibey/mcp/** - Source code for reference

### MCP Server Overview

```
vibey-roadmap MCP Server
├── Tools (76 total)
│   ├── Task Tools (3)     - start, complete, query
│   ├── Sprint Tools (4)   - start, complete, refresh, query
│   ├── Query Tools (5)    - track, blockers, dependencies, status, standards
│   ├── Content Tools (7)  - list, show, search, create, update, delete, validate
│   ├── Agent Tools (19)   - Dynamic from framework/agents
│   ├── Workflow Tools (16)- Dynamic from framework/workflows
│   └── Handoff Tools (22) - Dynamic from framework/templates
├── Resources (8 templates)
│   ├── Workflows (4)      - definition, steps, metadata, quality-gates
│   └── Handoffs (4)       - template, variables, metadata, rendered
└── Prompts (4)
    └── Quality Gates      - check, security, coverage, docs
```

### Capability Assessment

| Feature | Available | Reference |
|---------|-----------|-----------|
| Task management | Yes | vibey_start_task, vibey_complete_task |
| Progress tracking | Yes | vibey_roadmap_status, vibey_refresh_progress |
| Content access | Yes | vibey_content_* tools |
| Workflow execution | Yes | vibey_<workflow>_workflow tools |
| Quality checks | Yes | Prompts |

---

## Phase 2: Server Setup

**Duration:** 2-4 hours
**Goal:** Get MCP server running and accessible

### Installation

```bash
# Install Vibey with MCP support
pip install vibey

# Verify MCP server available
python -c "from vibey.mcp.server import VibeyMCPServer; print('OK')"
```

### Running the Server

```bash
# Run MCP server (stdio transport)
python -m vibey.mcp.server

# Or use the entry point
vibey mcp server
```

### Server Configuration

The server reads from:
- `.vibey/roadmap/` - Roadmap data
- `framework/` - Agent/workflow content (optional)

### Verify Server

```bash
# Test introspection
vibey docs introspect-mcp

# Generate reference
vibey docs generate-mcp
```

---

## Phase 3: Integration

**Duration:** 1-2 days
**Goal:** Connect client to server and call tools

### Connection Setup

#### stdio Transport (default)

```python
# Example client connection
import subprocess
import json

process = subprocess.Popen(
    ["python", "-m", "vibey.mcp.server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Send initialize request
request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "0.1.0",
        "capabilities": {}
    },
    "id": 1
}

process.stdin.write(json.dumps(request).encode() + b"\n")
process.stdin.flush()
response = json.loads(process.stdout.readline())
```

#### Using MCP SDK

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def connect():
    async with stdio_client(
        ["python", "-m", "vibey.mcp.server"]
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available: {len(tools.tools)} tools")
```

### Calling Tools

#### Example: Start Task

```python
# Tool call request
result = await session.call_tool(
    "vibey_start_task",
    {"task_id": "01KC2D0JK7READW9KAK1HBX4A5"}
)
print(result.content[0].text)
```

#### Example: Get Status

```python
result = await session.call_tool("vibey_roadmap_status", {})
status = json.loads(result.content[0].text)
print(f"Tracks: {status['tracks']}")
print(f"Tasks completed: {status['tasks_completed']}")
```

#### Example: Query Task

```python
result = await session.call_tool(
    "vibey_query_task",
    {"task_id": "01KC2D0JK7READW9KAK1HBX4A5"}
)
task = json.loads(result.content[0].text)
print(f"Task: {task['title']}")
print(f"Status: {task['status']}")
```

### Accessing Resources

```python
# List resources
resources = await session.list_resources()

# Read resource
content = await session.read_resource(
    "vibey://workflows/sprint-planning"
)
print(content.contents[0].text)
```

### Using Prompts

```python
# Get prompt
prompt = await session.get_prompt(
    "vibey_quality_gate_check",
    {"gate_type": "security", "threshold": "80"}
)

# Use messages in your context
for message in prompt.messages:
    print(f"{message.role}: {message.content}")
```

---

## Phase 4: Testing

**Duration:** 1 day
**Goal:** Verify integration works correctly

### Tool Testing Checklist

| Tool | Test | Expected |
|------|------|----------|
| `vibey_roadmap_status` | Call with no args | Returns status JSON |
| `vibey_start_task` | Valid task ID | Status changes to in_progress |
| `vibey_complete_task` | Started task ID | Status changes to completed |
| `vibey_query_task` | Existing task ID | Returns task details |
| `vibey_query_task` | Invalid task ID | Returns error |

### Integration Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_task_workflow():
    """Test complete task workflow via MCP."""
    async with get_mcp_client() as client:
        # Create task (if supported)
        # ...

        # Start task
        result = await client.call_tool(
            "vibey_start_task",
            {"task_id": task_id}
        )
        assert "started" in result.content[0].text.lower()

        # Verify status changed
        result = await client.call_tool(
            "vibey_query_task",
            {"task_id": task_id}
        )
        task = json.loads(result.content[0].text)
        assert task["status"] == "in_progress"

        # Complete task
        result = await client.call_tool(
            "vibey_complete_task",
            {"task_id": task_id}
        )
        assert "completed" in result.content[0].text.lower()
```

### Error Handling

```python
# Test error responses
result = await client.call_tool(
    "vibey_start_task",
    {"task_id": "invalid-id"}
)

# Should get error response
assert result.isError == True
assert "not found" in result.content[0].text.lower()
```

---

## Phase 5: Production

**Duration:** Ongoing
**Goal:** Maintain and extend integration

### Monitoring

```python
# Health check
async def health_check():
    result = await client.call_tool("vibey_roadmap_status", {})
    return not result.isError
```

### Handling Updates

1. **Monitor releases** - Watch GitHub for new versions
2. **Check MCP_REFERENCE.md** - Review tool changes
3. **Test after update** - Run integration tests
4. **Update client** - If tool signatures change

### Building Custom Tools

```python
# Example: Custom tool wrapper
async def get_current_task():
    """Get the task currently in progress."""
    result = await client.call_tool(
        "vibey_roadmap_status",
        {}
    )
    status = json.loads(result.content[0].text)

    # Find in_progress task
    for task in status.get("tasks", []):
        if task["status"] == "in_progress":
            return task
    return None
```

---

## Tool Reference

### Core Tools

| Tool | Input | Output |
|------|-------|--------|
| `vibey_start_task` | `{task_id: string}` | Status message |
| `vibey_complete_task` | `{task_id: string, actual_tokens?: int}` | Status message |
| `vibey_query_task` | `{task_id: string}` | Task JSON |
| `vibey_roadmap_status` | `{}` | Status JSON |
| `vibey_refresh_progress` | `{}` | Progress JSON |

### Query Tools

| Tool | Input | Output |
|------|-------|--------|
| `vibey_query_track` | `{track_id: string}` | Track JSON |
| `vibey_query_sprint` | `{sprint_id: string}` | Sprint JSON |
| `vibey_list_blockers` | `{track_id?: string}` | Blockers JSON |

### Content Tools

| Tool | Input | Output |
|------|-------|--------|
| `vibey_content_list` | `{content_type: string}` | List JSON |
| `vibey_content_show` | `{content_type: string, item_id: string}` | Content |
| `vibey_content_search` | `{query: string}` | Results JSON |

---

## Resource URI Patterns

| Pattern | Example | MIME Type |
|---------|---------|-----------|
| `vibey://workflows/{id}` | `vibey://workflows/sprint-planning` | text/markdown |
| `vibey://workflows/{id}/steps` | `vibey://workflows/sprint-planning/steps` | application/json |
| `vibey://handoffs/{id}` | `vibey://handoffs/diagram-handoff` | text/x-jinja2-markdown |
| `vibey://handoffs/{id}/variables` | `vibey://handoffs/diagram-handoff/variables` | application/json |

---

## Documentation Touchpoints

| Activity | Documents |
|----------|-----------|
| Tool reference | docs/reference/MCP_REFERENCE.md |
| Protocol details | MCP Protocol Specification |
| Server source | vibey/mcp/server.py |
| Tool definitions | vibey/mcp/tools/*.py |
| Resource providers | vibey/mcp/resources/*.py |
