# Vibey MCP Server

**Model Context Protocol (MCP) server for Vibey roadmap management**

Version: 0.1.0 (Sprint 1 - In Progress)

---

## Overview

The Vibey MCP Server exposes Vibey's roadmap management functionality through the standardized Model Context Protocol, enabling integration with Claude Desktop, Goose, and any MCP-compatible AI assistant.

### What is MCP?

The Model Context Protocol (MCP) is an open standard created by Anthropic that standardizes how AI assistants connect to data sources and tools. Think of MCP like USB-C for AI applications - a universal connector that works across platforms.

### Why MCP for Vibey?

1. **Claude Desktop Integration** - Use Vibey directly from Claude Desktop
2. **Goose Foundation** - Enables the goose-port track (next major milestone)
3. **Ecosystem Access** - Opens up 1000+ tools in the MCP ecosystem
4. **Future-Proof** - Standard adopted by OpenAI, Google DeepMind, and others

---

## Current Status

**Sprint 1: MCP Protocol Integration** ✅ Complete

**Sprint 2: Roadmap Tools Implementation** ✅ Complete

✅ Completed:
- Project structure created
- Error handling and validation utilities
- Roadmap adapter layer (8 methods)
- Task management tools (3 tools)
- Sprint management tools (4 tools)
- Query tools (4 tools)
- Basic server scaffold

**Total:** 11 working tools across all roadmap object types

⏳ Next Sprint:
- Sprint 3: Resources and subscriptions
- Sprint 4: Testing and production readiness

---

## Architecture

```
MCP Client (Claude Desktop, Goose, etc.)
    ↓ JSON-RPC 2.0
Vibey MCP Server
    ├── Tools (Actions)
    │   └── Task Management (start, complete, query)
    ├── Resources (Data) [Sprint 3]
    └── Prompts (Templates) [Sprint 3]
    ↓
Roadmap Adapter Layer
    ↓
Existing Vibey Roadmap System
    ├── Models (Sprint, Track, Task)
    ├── Serialization (YAML loader/saver)
    └── Status Management
```

---

## Available Tools

### Task Management (3 tools)

**`vibey_start_task`** - Mark a task as in progress
**`vibey_complete_task`** - Mark a task as completed
**`vibey_query_task`** - Get detailed task information

Example:
```json
{
  "name": "vibey_complete_task",
  "arguments": {
    "task_id": "mcp-server-2-task-001",
    "actual_tokens": 5000
  }
}
```

### Sprint Management (4 tools)

**`vibey_start_sprint`** - Mark a sprint as in progress
**`vibey_complete_sprint`** - Mark a sprint as completed
**`vibey_query_sprint`** - Get detailed sprint information
**`vibey_refresh_progress`** - Recalculate all progress and trigger auto-progression

Example:
```json
{
  "name": "vibey_refresh_progress",
  "arguments": {}
}
```

### Query Tools (4 tools)

**`vibey_query_track`** - Get detailed track information
**`vibey_list_blockers`** - List all current blockers
**`vibey_list_dependencies`** - List dependencies for an object
**`vibey_roadmap_status`** - Get comprehensive roadmap overview

Example:
```json
{
  "name": "vibey_roadmap_status",
  "arguments": {}
}
```

---

## Installation

### Prerequisites

- Python 3.10+
- Vibey framework repository
- MCP Python SDK (to be installed)

### Setup

1. Install dependencies:
```bash
cd /path/to/vibey
pip install -r requirements.txt
```

2. Run the server (placeholder implementation):
```bash
python3 framework/mcp/server.py
```

---

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python3",
      "args": ["/path/to/vibey/framework/mcp/server.py"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### With Goose

Add to your Goose configuration (`goose.yaml`):

```yaml
extensions:
  vibey:
    type: mcp
    server:
      command: python3
      args:
        - /path/to/vibey/framework/mcp/server.py
      cwd: /path/to/your/project
```

---

## Development

### Project Structure

```
framework/mcp/
├── __init__.py           # Package initialization
├── server.py             # Main MCP server
├── README.md             # This file
├── adapters/
│   ├── __init__.py
│   └── roadmap_adapter.py  # Adapter to roadmap system
├── tools/
│   ├── __init__.py
│   └── task_tools.py     # Task management tools
├── resources/            # [Sprint 3]
│   └── __init__.py
├── prompts/              # [Sprint 3]
│   └── __init__.py
├── utils/
│   ├── __init__.py
│   ├── errors.py         # Custom exceptions
│   └── validation.py     # Input validation
└── tests/
    ├── __init__.py
    ├── test_adapter.py
    ├── test_task_tools.py
    └── test_server.py
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest framework/mcp/tests/

# Run with coverage
pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=html
```

### Adding New Tools

1. Create tool definitions in appropriate `tools/*.py` file
2. Implement tool handler function
3. Register tool in `server.py`'s `get_tools()` method
4. Add routing in `handle_tool_call()` method
5. Write tests

Example:
```python
# In framework/mcp/tools/sprint_tools.py

def get_sprint_tools():
    return [{
        "name": "vibey_start_sprint",
        "description": "Start a sprint",
        "inputSchema": { ... }
    }]

async def handle_sprint_tool(tool_name, arguments, adapter):
    if tool_name == "vibey_start_sprint":
        return await handle_start_sprint(arguments, adapter)
    # ...
```

---

## Documentation

- [MCP Server Design](../../docs/development/MCP_SERVER_DESIGN.md) - Complete architecture and design
- [Sprint 1 Tasks](../../docs/development/MCP_SPRINT_1_TASKS.md) - Detailed task breakdown
- [MCP Specification](https://modelcontextprotocol.io/) - Official MCP docs

---

## Roadmap

### Sprint 1: MCP Protocol Integration ✅ Complete
- ✅ Server scaffold
- ✅ Adapter layer
- ✅ Task tools (3 tools)
- ✅ Error handling & validation
- ⏳ MCP SDK integration (awaiting SDK)

### Sprint 2: Roadmap Tools Implementation ✅ Complete
- ✅ Sprint management tools (4 tools)
- ✅ Query tools (4 tools)
- ✅ Enhanced adapter (5 new methods)
- ✅ Comprehensive roadmap coverage

### Sprint 3: Resources & Subscriptions
- Roadmap resources (read-only data)
- Status resources
- Documentation resources
- Real-time subscriptions

### Sprint 4: Testing & Documentation
- Comprehensive test suite
- Claude Desktop integration guide
- Production readiness
- Performance optimization

---

## Contributing

See the main Vibey [CLAUDE.md](../../CLAUDE.md) for contribution guidelines.

### Sprint 1 Development Guidelines

- Follow existing code patterns
- All tools must have proper error handling
- Use the adapter layer (don't duplicate roadmap logic)
- Write tests for all new functionality
- Update documentation

---

## Support

- GitHub Issues: https://github.com/vibey-framework/vibey/issues
- Documentation: `docs/development/MCP_*.md`
- MCP Spec: https://modelcontextprotocol.io/

---

**Track:** mcp-server
**Priority:** Critical
**Status:** Sprint 1 In Progress
