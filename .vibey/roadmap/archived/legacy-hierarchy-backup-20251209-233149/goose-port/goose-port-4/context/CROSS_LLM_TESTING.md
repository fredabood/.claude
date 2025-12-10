# Cross-LLM Testing Guide

> **Sprint 4 Documentation**
> **Created:** 2025-11-22
> **Status:** Complete

## Overview

This guide documents how to test the Vibey MCP server across different LLM platforms. The MCP server is platform-agnostic - any client that speaks MCP can use it.

## Supported Platforms

| Platform | MCP Support | Test Status | Configuration |
|----------|-------------|-------------|---------------|
| **Goose** | ✅ Native | ✅ Tested | Extension in `~/.config/goose/config.yaml` |
| **Claude Code** | ✅ Native | ✅ Tested | `.mcp.json` at project root |
| **Continue.dev** | ✅ Native | 🔄 Ready | `config.json` MCP servers |
| **Cursor** | ⚠️ Limited | ⏳ Planned | Requires MCP plugin |
| **GPT-4 (via proxy)** | ⚠️ Indirect | ⏳ Research | Requires MCP→Function bridge |

## Testing Prerequisites

### 1. MCP Server Running

Verify the server can start:

```bash
cd /Users/fredabood/Repositories/vibey
.venv/bin/python scripts/run-mcp-server.py
```

### 2. Python Environment

```bash
# Ensure dependencies
.venv/bin/pip install mcp pyyaml rich
```

### 3. Roadmap Data (Optional but Recommended)

```bash
# Verify roadmap exists
ls .vibey/roadmap/
```

## Platform-Specific Setup

### Goose (Block)

**Configuration:** `~/.config/goose/config.yaml`

```yaml
extensions:
  vibey:
    name: vibey
    type: stdio
    cmd: /path/to/vibey/.venv/bin/python
    args:
      - /path/to/vibey/scripts/run-mcp-server.py
    enabled: true
    timeout: 300
    description: Vibey Agent Framework - 46 tools
```

**Test Commands:**

```bash
# Start Goose in a project
goose session

# Invoke vibey tool
> /tool vibey_roadmap_status
```

**Expected Response:**
```
📊 Roadmap: Vibey Development Roadmap

**Version:** 2.0.0
**Status:** in_progress
**Blocked:** No

**Overall Progress:**
- Completion: 94%
- Tracks: 13/20 complete
...
```

### Claude Code

**Configuration:** `.mcp.json` at project root

```json
{
  "mcpServers": {
    "vibey": {
      "command": "/path/to/vibey/.venv/bin/python",
      "args": ["/path/to/vibey/scripts/run-mcp-server.py"]
    }
  }
}
```

**Test Process:**

1. Open project in VS Code with Claude Code extension
2. Restart Claude Code (Cmd+Shift+P → "Claude Code: Restart")
3. Ask Claude to use a Vibey tool:
   - "What's the roadmap status?"
   - "Start task mcp-server-1-task-001"

**Expected Behavior:**
- Claude shows tool invocation in UI
- Response appears with formatted roadmap data

### Continue.dev

**Configuration:** `~/.continue/config.json`

```json
{
  "mcpServers": [
    {
      "name": "vibey",
      "command": "/path/to/vibey/.venv/bin/python",
      "args": ["/path/to/vibey/scripts/run-mcp-server.py"]
    }
  ]
}
```

**Test Commands:**
- Use Continue.dev chat
- Reference `@vibey_roadmap_status` tool

### Custom MCP Client

For building custom integrations:

```python
import asyncio
from mcp import Client, StdioServerParameters

async def test_vibey_server():
    # Connect to Vibey MCP server
    server_params = StdioServerParameters(
        command="/path/to/.venv/bin/python",
        args=["/path/to/scripts/run-mcp-server.py"]
    )

    async with Client(server_params) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools")

        # Invoke a tool
        result = await client.call_tool(
            "vibey_roadmap_status",
            arguments={}
        )
        print(result)

asyncio.run(test_vibey_server())
```

## Test Scenarios

### Scenario 1: Tool Discovery

**Purpose:** Verify all tools are discoverable

**Steps:**
1. Connect to MCP server
2. List all tools
3. Verify tool count (expect 46 tools)
4. Verify tool names have `vibey_` prefix

**Expected Results:**
- 11 roadmap management tools
- 19+ agent tools
- 16+ workflow tools

### Scenario 2: Roadmap Status

**Purpose:** Verify roadmap query works

**Tool:** `vibey_roadmap_status`

**Input:** `{}`

**Expected Output:**
```
📊 Roadmap: [name]
**Version:** [version]
**Status:** [status]
**Progress:**
- Completion: [percentage]
- Tracks: X/Y complete
```

### Scenario 3: Task Lifecycle

**Purpose:** Verify task state transitions

**Steps:**
1. Query task: `vibey_query_task` with `task_id`
2. Start task: `vibey_start_task` with `task_id`
3. Complete task: `vibey_complete_task` with `task_id`
4. Verify status changed

### Scenario 4: Agent Invocation

**Purpose:** Verify agent tools return instructions

**Tool:** `vibey_test_engineer`

**Input:**
```json
{
  "task": "Write unit tests for the login function",
  "context": "Python Flask application"
}
```

**Expected Output:**
- Agent instructions/guidance
- Not an error

### Scenario 5: Workflow Invocation

**Purpose:** Verify workflow tools return steps

**Tool:** `vibey_workflow_feature_development`

**Input:**
```json
{
  "feature_name": "User dashboard",
  "requirements": "Display user metrics"
}
```

**Expected Output:**
- Workflow steps with agents
- Quality gates

## Error Testing

### Invalid Tool Name

**Input:** `nonexistent_tool_12345`

**Expected:**
```json
{
  "content": [{"type": "text", "text": "❌ Unknown tool..."}],
  "isError": true
}
```

### Missing Required Arguments

**Tool:** `vibey_query_track`
**Input:** `{}` (missing `track_id`)

**Expected:**
- Error message about missing parameter
- `isError: true`

### Track Not Found

**Tool:** `vibey_query_track`
**Input:** `{"track_id": "nonexistent-track"}`

**Expected:**
```json
{
  "content": [{"type": "text", "text": "❌ Error querying track..."}],
  "isError": true
}
```

## Performance Testing

### Baseline Metrics

| Operation | Expected Time | Threshold |
|-----------|--------------|-----------|
| Tool List | < 100ms | 1000ms |
| Roadmap Status | < 500ms | 2000ms |
| Query Track | < 300ms | 1000ms |
| Start Task | < 500ms | 2000ms |

### Load Testing

```python
import asyncio
import time

async def load_test(client, iterations=100):
    start = time.time()

    for i in range(iterations):
        await client.call_tool("vibey_roadmap_status", {})

    elapsed = time.time() - start
    print(f"{iterations} calls in {elapsed:.2f}s")
    print(f"Average: {elapsed/iterations*1000:.1f}ms per call")
```

## LLM-Specific Considerations

### Claude

- Understands MCP natively
- Can chain tool calls
- Handles structured output well

### GPT-4

- Requires MCP→Function bridge
- May need function calling format conversion
- Test with Azure OpenAI or OpenAI API

### Gemini

- Requires MCP proxy
- Similar to GPT-4 approach

### Local LLMs (via Ollama)

- Use with Continue.dev
- May have latency concerns
- Test with smaller models first

## Troubleshooting

### Server Won't Start

```bash
# Check Python path
which python
.venv/bin/python --version

# Check dependencies
.venv/bin/pip list | grep -E "mcp|yaml|rich"

# Run with debug
.venv/bin/python scripts/run-mcp-server.py --debug
```

### Tools Not Appearing

1. Restart the LLM client
2. Check MCP configuration path
3. Verify server script is executable
4. Check stderr for errors

### Slow Responses

1. Check if discovery is cached
2. Verify no disk I/O bottlenecks
3. Profile tool handler

### Wrong Data

1. Verify roadmap path is correct
2. Check file permissions
3. Run `vibey roadmap status` CLI to compare

## Test Matrix

| Test | Goose | Claude Code | Continue | Custom |
|------|-------|-------------|----------|--------|
| Tool Discovery | ✅ | ✅ | 🔄 | 🔄 |
| Roadmap Status | ✅ | ✅ | 🔄 | 🔄 |
| Query Track | ✅ | ✅ | 🔄 | 🔄 |
| Start Task | ✅ | ✅ | 🔄 | 🔄 |
| Complete Task | ✅ | ✅ | 🔄 | 🔄 |
| Agent Tools | ✅ | ✅ | 🔄 | 🔄 |
| Workflow Tools | ✅ | ✅ | 🔄 | 🔄 |
| Error Handling | ✅ | ✅ | 🔄 | 🔄 |

**Legend:**
- ✅ Tested and working
- 🔄 Ready to test
- ⏳ Planned
- ❌ Not supported

## Automated Testing

Run the automated test suite:

```bash
# All MCP tests
.venv/bin/python -m pytest tests/unit/test_frontmatter_parser.py \
  tests/unit/test_discovery.py \
  tests/integration/test_mcp_tools.py \
  tests/e2e/test_goose_integration.py \
  -v --no-cov

# Just E2E tests
.venv/bin/python -m pytest tests/e2e/test_goose_integration.py -v
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# .github/workflows/test-mcp.yml
name: MCP Server Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m venv .venv
          .venv/bin/pip install -r requirements.txt
      - name: Run tests
        run: |
          .venv/bin/python -m pytest tests/ -v --no-cov
```

## Next Steps

1. **Continue.dev Testing** - Set up and verify
2. **Custom Client SDK** - Build reusable test client
3. **Performance Regression** - Add to CI
4. **Multi-LLM Benchmarks** - Compare response quality
