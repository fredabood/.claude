# MCP Server Development Setup

**Version:** 1.0
**Date:** 2025-11-10
**Track:** mcp-server
**Sprint:** Sprint 1

---

## Overview

This guide covers setting up a development environment for working on the Vibey MCP Server.

---

## Prerequisites

### Required

- **Python 3.10+** - MCP SDK requires Python 3.10 or newer
- **Git** - For version control
- **Vibey Framework Repository** - Cloned locally

### Recommended

- **Virtual Environment** - `venv` or `conda`
- **IDE** - VS Code, PyCharm, or similar with Python support
- **MCP Inspector** - For testing MCP servers (npm install -g @modelcontextprotocol/inspector)

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/vibey-framework/vibey.git
cd vibey
```

### 2. Create Virtual Environment

```bash
# Using venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# OR using conda
conda create -n vibey-mcp python=3.10
conda activate vibey-mcp
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import yaml, jinja2; print('Core dependencies OK')"
```

### 4. Verify Project Structure

```bash
ls -la framework/mcp/
```

You should see:
```
framework/mcp/
├── __init__.py
├── server.py
├── README.md
├── adapters/
├── tools/
├── resources/
├── prompts/
├── utils/
└── tests/
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest framework/mcp/tests/

# Run specific test file
pytest framework/mcp/tests/test_validation.py

# Run with verbose output
pytest framework/mcp/tests/ -v

# Run with coverage
pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
```

### Running the Server (Placeholder)

```bash
# Run server
python3 framework/mcp/server.py

# Run with custom roadmap path
python3 framework/mcp/server.py --roadmap-root /path/to/.vibey/roadmap
```

**Note:** The server is currently a placeholder awaiting MCP SDK integration.

### Code Quality

```bash
# Format code with black
black framework/mcp/

# Lint with ruff
ruff check framework/mcp/

# Type check with mypy
mypy framework/mcp/
```

---

## MCP Python SDK Integration

### Installation (When Available)

The MCP Python SDK is required for full server functionality:

```bash
pip install mcp
```

### Verifying SDK Installation

```python
# test_mcp_sdk.py
try:
    import mcp
    from mcp import Server
    print(f"MCP SDK version: {mcp.__version__}")
    print("MCP SDK installed successfully!")
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp")
```

### SDK Documentation

- Official Docs: https://modelcontextprotocol.io/
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Examples: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples

---

## Testing with MCP Inspector

The MCP Inspector is an official tool for testing MCP servers:

### Installation

```bash
npm install -g @modelcontextprotocol/inspector
```

### Running Inspector

```bash
# Start your MCP server
python3 framework/mcp/server.py

# In another terminal, connect inspector
mcp-inspector python framework/mcp/server.py
```

The inspector provides:
- Tool list visualization
- Interactive tool invocation
- Request/response inspection
- Protocol debugging

---

## Project Structure

### Core Files

**`server.py`** - Main MCP server implementation
- Server initialization
- Capability negotiation
- Tool registration
- Request routing

**`adapters/roadmap_adapter.py`** - Adapter to existing roadmap system
- Wraps roadmap-update.py functionality
- Wraps roadmap-query.py functionality
- No business logic duplication

**`tools/task_tools.py`** - Task management tools
- `vibey_start_task`
- `vibey_complete_task`
- `vibey_query_task`

**`utils/errors.py`** - Custom exceptions
- `VibeyMCPError` (base)
- `TaskNotFoundError`
- `SprintNotFoundError`
- `InvalidStateTransitionError`

**`utils/validation.py`** - Input validation
- JSON schema validation
- ID format validation
- Error handling

### Test Files

**`tests/test_validation.py`** - Validation utility tests
**`tests/test_adapter.py`** - Adapter layer tests (to be created)
**`tests/test_task_tools.py`** - Task tool tests (to be created)
**`tests/test_server.py`** - Server integration tests (to be created)

---

## Development Tasks

### Sprint 1 Checklist

- [x] Project structure created
- [x] Requirements file updated
- [x] Error classes defined
- [x] Validation utilities implemented
- [x] Roadmap adapter created
- [x] Task tools implemented
- [x] Server scaffold created
- [ ] MCP SDK integrated
- [ ] Integration tests created
- [ ] Documentation complete

### Current Status

**Completed:**
- Project structure (Task 001)
- Adapter layer (Task 003)
- Task tools (Task 004)
- Error handling & validation (Task 006)

**In Progress:**
- MCP SDK integration (Task 002)
- Integration tests (Task 007)

**Pending:**
- Full documentation (Task 008)

---

## Common Development Tasks

### Adding a New Tool

1. **Define tool** in appropriate `tools/*.py` file:
```python
def get_sprint_tools():
    return [{
        "name": "vibey_start_sprint",
        "title": "Start Sprint",
        "description": "Mark a sprint as in progress",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sprint_id": {"type": "string"}
            },
            "required": ["sprint_id"]
        }
    }]
```

2. **Implement handler**:
```python
async def handle_start_sprint(arguments, adapter):
    sprint_id = arguments["sprint_id"]
    result = adapter.start_sprint(sprint_id)
    return {
        "content": [{"type": "text", "text": f"✅ Sprint {sprint_id} started"}],
        "isError": False
    }
```

3. **Register in server.py**:
```python
def get_tools(self):
    tools = []
    tools.extend(get_task_tools())
    tools.extend(get_sprint_tools())  # Add this
    return tools
```

4. **Add routing**:
```python
async def handle_tool_call(self, tool_name, arguments):
    if "sprint" in tool_name:
        return await handle_sprint_tool(tool_name, arguments, self.adapter)
    # ...
```

5. **Write tests**:
```python
# tests/test_sprint_tools.py
async def test_start_sprint():
    adapter = RoadmapAdapter()
    result = await handle_start_sprint({"sprint_id": "test-1"}, adapter)
    assert result["isError"] == False
```

### Debugging

**Enable debug logging:**
```python
# In server.py
logging.basicConfig(level=logging.DEBUG)
```

**Inspect tool calls:**
```python
logger.debug(f"Tool: {tool_name}, Args: {arguments}")
```

**Test adapter directly:**
```python
# test_adapter_manual.py
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter

adapter = RoadmapAdapter()
result = adapter.query_task("mcp-server-1-task-001")
print(result)
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'framework'`

**Solution:** Ensure you're running from repository root:
```bash
cd /path/to/vibey
python3 -m framework.mcp.server
```

### YAML Loading Errors

**Problem:** `FileNotFoundError` when loading tasks

**Solution:** Check roadmap root path:
```bash
ls -la .vibey/roadmap/
python3 framework/mcp/server.py --roadmap-root .vibey/roadmap
```

### Test Failures

**Problem:** Tests fail with import errors

**Solution:** Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov
```

---

## Next Steps

After completing Sprint 1:

1. **MCP SDK Integration** - Complete server.py with actual SDK
2. **Integration Tests** - Test server with MCP Inspector
3. **Sprint 2** - Implement sprint management and query tools
4. **Claude Desktop** - Test end-to-end integration

---

## Resources

### Documentation

- [MCP Server Design](./MCP_SERVER_DESIGN.md)
- [Sprint 1 Tasks](./MCP_SPRINT_1_TASKS.md)
- [Framework Roadmap](../FRAMEWORK_ROADMAP.md)

### External Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [Python SDK Docs](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Claude Desktop Config](https://docs.claude.com/claude-desktop)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Status:** Sprint 1 Development
