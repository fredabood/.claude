# MCP Integration Guide

**Version:** 2.5.0
**Status:** Production Ready
**Protocol:** Model Context Protocol (MCP)
**Last Updated:** 2025-11-12

---

## Table of Contents

1. [Overview](#overview)
2. [What is MCP?](#what-is-mcp)
3. [Why Use MCP with Vibey?](#why-use-mcp-with-vibey)
4. [Installation & Setup](#installation--setup)
5. [Server Architecture](#server-architecture)
6. [Available Tools](#available-tools)
7. [Client Configuration](#client-configuration)
8. [Usage Examples](#usage-examples)
9. [Development Guide](#development-guide)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Vibey MCP Server exposes the Vibey roadmap system through the Model Context Protocol, enabling AI coding assistants to directly manage tracks, sprints, and tasks through standardized tool calls.

### Key Features

- **11 MCP Tools** - Start/complete tasks & sprints, query status, update context
- **Real-time Updates** - Changes reflected immediately in roadmap state
- **Error Handling** - Comprehensive validation and actionable error messages
- **Platform Agnostic** - Works with any MCP-compatible client (Claude Desktop, etc.)
- **Unified Backend** - Uses same core library as Vibey CLI

---

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard developed by Anthropic for connecting AI assistants to external data sources and tools. It provides:

- **Standardized Communication** - JSON-RPC protocol over stdio or HTTP+SSE
- **Tool Invocation** - AI can call functions with structured inputs/outputs
- **Resources** - Access to documents, data, and context
- **Prompts** - Pre-defined templates for common tasks

### MCP Resources

- **Official Spec:** https://spec.modelcontextprotocol.io
- **Python SDK:** https://github.com/anthropics/mcp-python
- **Claude Desktop Integration:** https://claude.ai/docs/mcp

---

## Why Use MCP with Vibey?

### Use Cases

1. **AI-Driven Development** - Let AI assistant manage your roadmap while coding
2. **Automated Status Updates** - AI marks tasks complete as it finishes work
3. **Context-Aware Assistance** - AI queries task details to understand requirements
4. **Workflow Integration** - Combine roadmap management with code generation

### Advantages Over CLI

| Feature | MCP Server | CLI |
|---------|------------|-----|
| **Integration** | Native in AI chat | Requires bash execution |
| **Context** | AI has direct access | AI must parse text output |
| **Error Handling** | Structured JSON errors | Text parsing required |
| **Real-time** | Instant bidirectional | Polling required |
| **User Experience** | Conversational | Command-driven |

### When to Use Each

**Use MCP When:**
- Working within AI assistant (Claude Desktop, etc.)
- Want conversational roadmap management
- Need real-time AI awareness of project status
- Building AI-native workflows

**Use CLI When:**
- Scripting and automation (CI/CD)
- Manual terminal operations
- Batch operations
- Platform without MCP support

---

## Installation & Setup

### Prerequisites

1. **Python 3.7+** with pip
2. **Vibey Framework** installed
3. **MCP-compatible client** (Claude Desktop, etc.)

### Step 1: Install Vibey with MCP Support

```bash
# Clone repository
git clone https://github.com/your-org/vibey.git
cd vibey

# Install with MCP dependencies
pip install -e ".[mcp]"

# Verify MCP server
python -m framework.mcp.server --help
```

### Step 2: Test MCP Server

```bash
# Run server in test mode
python -m framework.mcp.server --roadmap-root .vibey/roadmap

# Should output:
# Vibey MCP Server - Ready
# Tools available: 11
```

### Step 3: Configure Client

See [Client Configuration](#client-configuration) below for platform-specific setup.

---

## Server Architecture

### Component Structure

```
framework/mcp/
├── server.py                    # Main MCP server
├── adapters/
│   └── roadmap_adapter.py       # Core library adapter
├── tools/
│   ├── task_tools.py            # Task management tools (3)
│   ├── sprint_tools.py          # Sprint management tools (4)
│   └── query_tools.py           # Query/status tools (4)
└── utils/
    ├── errors.py                # Error handling
    └── validation.py            # Input validation
```

### Design Principles

1. **Thin Adapter Layer** - MCP server wraps core library, no duplicate logic
2. **Shared Error Handling** - Uses `vibey/common/errors.py` (same as CLI)
3. **Stateless Tools** - Each tool call is independent
4. **Idempotent Operations** - Safe to retry (start/complete succeed if already in state)

### Protocol Transport

**Current:** stdio (JSON-RPC over stdin/stdout)
**Future:** HTTP+SSE for web-based clients

---

## Available Tools

The Vibey MCP Server exposes 11 tools organized into 3 categories.

### Task Management Tools (3)

#### `vibey_start_task`

Start a task (set status to `in_progress`).

**Input:**
```json
{
  "task_id": "sprint-1-task-001"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "✅ Task started: sprint-1-task-001\n   Status: in_progress\n   Started: 2025-11-12 14:30:00"
  }],
  "isError": false
}
```

**Behavior:**
- Validates task exists
- Checks for blockers (fails if blocked)
- Sets `status = in_progress`, records start time
- **Idempotent:** Returns success if already in_progress

---

#### `vibey_complete_task`

Complete a task (set status to `completed`).

**Input:**
```json
{
  "task_id": "sprint-1-task-001",
  "actual_tokens": 15000  // optional
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "✅ Task completed: sprint-1-task-001\n   Duration: 2 hours\n   Tokens: 15,000 (estimated: 12,000)"
  }],
  "isError": false
}
```

**Behavior:**
- Validates task is in_progress
- Runs quality gates (if defined)
- Sets `status = completed`, records completion time
- Updates parent sprint progress
- **Idempotent:** Returns success if already completed

---

#### `vibey_query_task`

Get detailed task information.

**Input:**
```json
{
  "task_id": "sprint-1-task-001"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "📋 Task: Implement unified error handling\n   Status: ✅ completed\n   Dependencies: 2 completed\n   Files: vibey/common/errors.py\n   Quality: >90% test coverage"
  }],
  "isError": false
}
```

**Returns:**
- Task name, description, status
- Dependencies and blockers
- Files to modify
- Quality requirements
- Git commits

---

### Sprint Management Tools (4)

#### `vibey_start_sprint`

Start a sprint.

**Input:**
```json
{
  "sprint_id": "sprint-1"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "✅ Sprint started: sprint-1\n   Name: Foundation\n   Tasks: 10 pending"
  }],
  "isError": false
}
```

---

#### `vibey_complete_sprint`

Complete a sprint (all tasks must be done).

**Input:**
```json
{
  "sprint_id": "sprint-1"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "✅ Sprint completed: sprint-1\n   Duration: 2 weeks (estimated: 2 weeks)\n   Tasks: 10/10 completed"
  }],
  "isError": false
}
```

**Validation:**
- All tasks must be completed
- Sprint must be in_progress
- Quality gates must pass

---

#### `vibey_query_sprint`

Get sprint details and task list.

**Input:**
```json
{
  "sprint_id": "sprint-1"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "🎯 Sprint: Foundation\n   Status: 🔵 in_progress\n   Progress: 7/10 tasks (70%)\n   Tasks:\n     ✅ task-001: Initialize project\n     ✅ task-002: Create models\n     🔵 task-003: Implement core logic\n     ..."
  }],
  "isError": false
}
```

---

#### `vibey_refresh_sprint_cache`

Refresh cached sprint/task data (useful after external updates).

**Input:**
```json
{
  "sprint_id": "sprint-1"  // optional, refreshes all if omitted
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "✅ Cache refreshed for sprint-1\n   Tasks: 10 loaded\n   Dependencies: 3 resolved"
  }],
  "isError": false
}
```

**Use Case:** Call this if you manually edit roadmap YAML files

---

### Query & Status Tools (4)

#### `vibey_list_sprints`

List all sprints in roadmap.

**Input:**
```json
{
  "track_id": "core-framework"  // optional, lists all if omitted
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "Sprints:\n  ✅ sprint-1: Foundation (10/10 tasks)\n  🔵 sprint-2: Integration (3/8 tasks)\n  ⚪ sprint-3: Testing (0/6 tasks)"
  }],
  "isError": false
}
```

---

#### `vibey_query_roadmap_status`

Get high-level roadmap overview.

**Input:**
```json
{}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "Vibey Framework Roadmap\n   Status: 🔵 In Progress\n   Progress: 46% (97/212 tasks)\n   Tracks: 3/14 completed"
  }],
  "isError": false
}
```

---

#### `vibey_query_track_details`

Get track details with sprint list.

**Input:**
```json
{
  "track_id": "core-framework"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "📦 Track: Core Framework\n   Status: ✅ completed\n   Progress: 20/20 tasks (100%)\n   Sprints: 2/2 completed"
  }],
  "isError": false
}
```

---

#### `vibey_list_tasks_by_status`

List tasks filtered by status.

**Input:**
```json
{
  "status": "in_progress",  // or "not_started", "completed", "blocked"
  "sprint_id": "sprint-1"   // optional filter
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "Tasks (in_progress):\n  🔵 sprint-1-task-003: Implement core logic\n  🔵 sprint-1-task-005: Add validation"
  }],
  "isError": false
}
```

---

## Client Configuration

### Claude Desktop (macOS)

1. **Locate config file:**
   ```bash
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. **Add Vibey MCP Server:**
   ```json
   {
     "mcpServers": {
       "vibey-roadmap": {
         "command": "python",
         "args": [
           "-m",
           "framework.mcp.server",
           "--roadmap-root",
           "/path/to/your/project/.vibey/roadmap"
         ]
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Verify in Claude:**
   - Open new chat
   - Type: "What tools do you have access to?"
   - Should see `vibey_*` tools listed

### Claude Desktop (Linux)

Config location: `~/.config/Claude/claude_desktop_config.json`

Same configuration as macOS.

### Claude Desktop (Windows)

Config location: `%APPDATA%\Claude\claude_desktop_config.json`

Same configuration as macOS (use Windows paths).

### Other MCP Clients

Any MCP-compatible client can use the Vibey server:

**Generic stdio config:**
```json
{
  "command": "python -m framework.mcp.server",
  "args": ["--roadmap-root", ".vibey/roadmap"],
  "env": {
    "PYTHONPATH": "/path/to/vibey"
  }
}
```

---

## Usage Examples

### Example 1: Starting a Task

**User:** "Start task sprint-1-task-003"

**Claude (via MCP):**
```
[calls vibey_start_task with task_id="sprint-1-task-003"]

✅ I've started task sprint-1-task-003 (Implement core logic).
The task is now in progress. Would you like me to show you the
details or get the implementation context?
```

---

### Example 2: Checking Sprint Status

**User:** "What's the status of sprint-1?"

**Claude (via MCP):**
```
[calls vibey_query_sprint with sprint_id="sprint-1"]

Sprint 1: Foundation
Status: In Progress (70% complete)

Completed (7):
  ✅ task-001: Initialize project structure
  ✅ task-002: Create base models
  ...

In Progress (1):
  🔵 task-003: Implement core logic

Not Started (2):
  ⚪ task-009: Write integration tests
  ⚪ task-010: Update documentation
```

---

### Example 3: Completing a Task

**User:** "Mark task-003 as complete. I finished implementing the error handling."

**Claude (via MCP):**
```
[calls vibey_complete_task with task_id="sprint-1-task-003"]

✅ Task sprint-1-task-003 completed successfully!

Duration: 2.5 hours
Sprint Progress: 80% (8/10 tasks)

Would you like me to:
1. Start the next task (task-004)?
2. Show remaining tasks in this sprint?
3. Update the sprint summary?
```

---

### Example 4: AI-Driven Workflow

**User:** "Help me work through sprint-1 tasks"

**Claude (via MCP):**
```
[calls vibey_query_sprint to see status]

Sure! Let me check sprint-1 status...

Sprint 1: Foundation (3/10 tasks completed)

Next task: sprint-1-task-004 (Add input validation)

[calls vibey_query_task for details]

Task Details:
- Add validation for user inputs in core.py
- Use Pydantic models for type checking
- Write unit tests for edge cases

Would you like me to:
1. Start this task and begin implementation?
2. Show me what files we need to modify?
3. Review the task dependencies first?
```

---

### Example 5: Error Handling

**User:** "Complete sprint-1"

**Claude (via MCP):**
```
[calls vibey_complete_sprint with sprint_id="sprint-1"]

❌ Cannot complete sprint-1:

Issues:
- 2 tasks still in progress (task-009, task-010)
- 1 quality gate failing (Test Coverage: 85% < 90%)

Next Steps:
1. Complete remaining tasks
2. Add tests to reach 90% coverage
3. Then try completing the sprint again

Would you like me to show the incomplete tasks?
```

---

## Development Guide

### Adding a New MCP Tool

Follow these steps to add a new tool to the MCP server.

#### Step 1: Define Tool Schema

Create or edit a tool file (e.g., `framework/mcp/tools/my_tools.py`):

```python
def get_my_tools() -> List[Dict[str, Any]]:
    """Get my custom tool definitions."""
    return [
        {
            "name": "vibey_my_custom_tool",
            "title": "My Custom Tool",
            "description": "Does something useful",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Second parameter",
                        "minimum": 0
                    }
                },
                "required": ["param1"]
            }
        }
    ]
```

#### Step 2: Implement Tool Handler

In the same file:

```python
async def handle_my_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Handle my custom tool invocation."""

    if tool_name == "vibey_my_custom_tool":
        param1 = arguments["param1"]
        param2 = arguments.get("param2", 0)

        try:
            # Use adapter to access core library
            result = adapter.do_something(param1, param2)

            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Success: {result}"
                }],
                "isError": False
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Error: {str(e)}"
                }],
                "isError": True
            }
```

#### Step 3: Register Tool in Server

Edit `framework/mcp/server.py`:

```python
from .tools.my_tools import get_my_tools, handle_my_tool

def get_tools(self) -> list[Dict[str, Any]]:
    """Get all available tools."""
    tools = []
    tools.extend(get_task_tools())
    tools.extend(get_sprint_tools())
    tools.extend(get_query_tools())
    tools.extend(get_my_tools())  # Add this
    return tools

async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
    """Handle tool invocation."""

    # Add routing
    if tool_name.startswith("vibey_my_"):
        return await handle_my_tool(tool_name, arguments, self.adapter)

    # ... existing routing ...
```

#### Step 4: Test Tool

```bash
# Start server
python -m framework.mcp.server

# In client (Claude Desktop), test:
"Call vibey_my_custom_tool with param1='test' and param2=42"
```

---

### Error Handling Best Practices

**Use Structured Errors:**
```python
from vibey.common.errors import VibeyError, ErrorRenderer

try:
    # Operation
    pass
except VibeyError as e:
    # Use unified error handling
    from vibey.common.error_renderers import MCPErrorRenderer
    return MCPErrorRenderer().render(e)
```

**Provide Actionable Feedback:**
```python
# Bad
return {"content": [{"type": "text", "text": "Error"}], "isError": True}

# Good
return {
    "content": [{
        "type": "text",
        "text": "❌ Task not found: sprint-1-task-999\n\n" +
               "Available tasks in sprint-1:\n" +
               "  - sprint-1-task-001\n" +
               "  - sprint-1-task-002\n\n" +
               "Try: vibey_query_sprint to see all tasks"
    }],
    "isError": True
}
```

---

### Testing MCP Tools

Create tests in `tests/mcp/test_tools.py`:

```python
import pytest
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter
from framework.mcp.tools.task_tools import handle_task_tool

@pytest.mark.asyncio
async def test_start_task():
    """Test starting a task via MCP."""
    adapter = RoadmapAdapter(test_roadmap_path)

    result = await handle_task_tool(
        "vibey_start_task",
        {"task_id": "sprint-1-task-001"},
        adapter
    )

    assert result["isError"] == False
    assert "started" in result["content"][0]["text"].lower()
```

---

## Troubleshooting

### Server Not Starting

**Issue:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
# Install MCP SDK
pip install mcp

# Or install Vibey with MCP support
pip install -e ".[mcp]"
```

---

### Tools Not Appearing in Claude

**Issue:** Claude doesn't see `vibey_*` tools

**Solutions:**

1. **Check config file location:**
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Should contain "mcpServers" with "vibey-roadmap"
   ```

2. **Verify server runs:**
   ```bash
   python -m framework.mcp.server --roadmap-root .vibey/roadmap
   # Should not error, press Ctrl+C to stop
   ```

3. **Check paths:**
   ```json
   {
     "mcpServers": {
       "vibey-roadmap": {
         "command": "python",
         "args": [
           "-m",
           "framework.mcp.server",
           "--roadmap-root",
           "/FULL/PATH/TO/.vibey/roadmap"  // Must be absolute
         ]
       }
     }
   }
   ```

4. **Restart Claude Desktop completely** (Cmd+Q, then reopen)

---

### Tool Calls Failing

**Issue:** `❌ Error: Roadmap not found`

**Solutions:**

1. **Verify roadmap path:**
   ```bash
   ls -la .vibey/roadmap/
   # Should show roadmap.yaml and track directories
   ```

2. **Check MCP server logs:**
   Claude Desktop logs are in:
   ```bash
   # macOS
   ~/Library/Logs/Claude/mcp-server-vibey-roadmap.log
   ```

3. **Test with CLI first:**
   ```bash
   cd /path/to/project
   vibey roadmap status
   # If this works, MCP should too
   ```

---

### Permission Errors

**Issue:** `Permission denied: .vibey/roadmap/...`

**Solution:**
```bash
# Fix permissions
chmod -R u+rw .vibey/

# Verify
ls -la .vibey/roadmap/
```

---

### JSON Parsing Errors

**Issue:** `JSONDecodeError in MCP communication`

**Cause:** Corrupt config file

**Solution:**
```bash
# Validate JSON syntax
python -c "import json; json.load(open('~/Library/Application Support/Claude/claude_desktop_config.json'))"

# Fix syntax errors, common issues:
# - Missing commas
# - Trailing commas (not allowed)
# - Unescaped backslashes in Windows paths (use \\ or /)
```

---

## Advanced Configuration

### Multiple Projects

Configure multiple Vibey servers for different projects:

```json
{
  "mcpServers": {
    "vibey-project-a": {
      "command": "python",
      "args": ["-m", "framework.mcp.server", "--roadmap-root", "/path/to/project-a/.vibey/roadmap"]
    },
    "vibey-project-b": {
      "command": "python",
      "args": ["-m", "framework.mcp.server", "--roadmap-root", "/path/to/project-b/.vibey/roadmap"]
    }
  }
}
```

Tools will be prefixed: `vibey-project-a_start_task`, `vibey-project-b_start_task`

---

### Environment Variables

Pass environment variables to MCP server:

```json
{
  "mcpServers": {
    "vibey-roadmap": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_ROOT": "/custom/path",
        "VIBEY_VERBOSE": "1",
        "PYTHONPATH": "/path/to/vibey"
      }
    }
  }
}
```

---

### Logging

Enable verbose logging for debugging:

```json
{
  "mcpServers": {
    "vibey-roadmap": {
      "command": "python",
      "args": ["-m", "framework.mcp.server", "--verbose"]
    }
  }
}
```

Logs appear in:
- **macOS:** `~/Library/Logs/Claude/mcp-server-vibey-roadmap.log`
- **Linux:** `~/.local/share/Claude/logs/mcp-server-vibey-roadmap.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp-server-vibey-roadmap.log`

---

## Future Enhancements

### Roadmap (MCP Server Development)

**Sprint 3: Resources & Prompts** (Planned Q1 2025)
- MCP Resources for roadmap docs (read `.vibey/roadmap/**/*.md`)
- Pre-defined prompts ("Start next task", "Sprint summary", etc.)
- Server-sent events for real-time updates

**Sprint 4: Advanced Features** (Planned Q2 2025)
- HTTP+SSE transport (web-based clients)
- Batch operations (start multiple tasks)
- Custom quality gate execution
- Dependency visualization

---

## Getting Help

### Documentation
- **CLI Reference:** `docs/reference/CLI_REFERENCE.md`
- **Getting Started:** `docs/guides/GETTING_STARTED.md`
- **Architecture:** `docs/development/ARCHITECTURE.md`

### Community
- **GitHub Issues:** https://github.com/your-org/vibey/issues
- **Discussions:** https://github.com/your-org/vibey/discussions
- **MCP Discord:** https://discord.gg/mcp (Anthropic's MCP community)

### Related Resources
- **MCP Specification:** https://spec.modelcontextprotocol.io
- **MCP Python SDK:** https://github.com/anthropics/mcp-python
- **Claude Desktop Docs:** https://claude.ai/docs/mcp

---

**Last Updated:** 2025-11-12
**Version:** 2.5.0
**Maintained By:** Vibey Framework Team
**License:** MIT
