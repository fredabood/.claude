# D6: MCP Server Architecture Audit

**Task ID:** 01KFXK2HSTDRM3X3BEWMZVHH3H
**Phase:** D6: Interfaces
**Date:** 2026-01-29

## Executive Summary

The Vibey MCP Server (`VibeyMCPServer`) implements the Model Context Protocol using FastMCP from the official Python SDK. It exposes 76 tools across 7 categories with dynamic tool discovery for agents/workflows. Key finding: The server architecture supports remote mode via the `RoadmapAdapter` abstraction - this adapter can be swapped to route operations to Delta Lake instead of local storage.

**Key Statistics:**
- 1 main server class: `VibeyMCPServer`
- 76 MCP tools across 7 categories
- 8 MCP resources via 2 providers
- 4 MCP prompts via QualityGatePromptProvider
- stdio transport for AI assistant communication

## Server Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP SERVER ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

  AI ASSISTANT                         VIBEY MCP SERVER
  (Claude/Cursor)                      (vibey-roadmap)
  ─────────────                        ────────────────

┌─────────────────┐                 ┌─────────────────┐
│ MCP Client      │────── stdio ───▶│ VibeyMCPServer  │
│ (JSON-RPC)      │                 │                 │
└─────────────────┘                 └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Tool Router     │
                                    │                 │
                                    ├─────────────────┤
                                    │ task_tools      │──▶ TaskHandler
                                    │ sprint_tools    │──▶ SprintHandler
                                    │ query_tools     │──▶ QueryHandler
                                    │ content_tools   │──▶ ContentHandler
                                    │ context_tools   │──▶ ContextHandler
                                    │ token_tools     │──▶ TokenHandler
                                    │ submodule_tools │──▶ SubmoduleHandler
                                    │ dynamic_tools   │──▶ ToolDiscovery
                                    └─────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ RoadmapAdapter  │
                                    │                 │
                                    ├─────────────────┤
                                    │ YAML Backend    │ (Local Mode)
                                    │ SQLite Backend  │ (Cache)
                                    │ Delta Backend   │ (Remote Mode*)
                                    └─────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Storage Layer   │
                                    │ .vibey/roadmap/ │
                                    └─────────────────┘
```

## VibeyMCPServer Class

| Attribute | Type | Purpose |
|-----------|------|---------|
| `roadmap_root` | `Path` | Path to `.vibey/roadmap/` |
| `framework_root` | `Path` | Path to project root |
| `adapter` | `RoadmapAdapter` | Roadmap operations abstraction |
| `tool_discovery` | `ToolDiscovery` | Dynamic tool discovery |

### Server Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `__init__()` | Initialize server with paths | None |
| `run()` | Start MCP server on stdio | Async |
| `get_capabilities()` | Return MCP capabilities dict | Dict |
| `get_tools()` | Get all available tools | List[Dict] |
| `get_discovery_stats()` | Get tool discovery statistics | Dict |
| `handle_tool_call()` | Route and handle tool invocation | Dict |
| `_handle_dynamic_tool()` | Handle discovered tools | Dict |
| `_execute_agent_tool()` | Execute agent tool | Dict |
| `_execute_workflow_tool()` | Execute workflow tool | Dict |
| `_execute_handoff_tool()` | Execute handoff tool | Dict |

## Tool Categories Table

| Category | Module | Tools | Purpose |
|----------|--------|-------|---------|
| **Task** | `task_tools.py` | 3 | Task lifecycle (start, complete, query) |
| **Sprint** | `sprint_tools.py` | 4 | Sprint management (start, complete, query, refresh) |
| **Query** | `query_tools.py` | 5 | Roadmap queries and status checks |
| **Content** | `content_tools.py` | 7 | Content management (list, show, search) |
| **Context** | `context_tools.py` | 5 | Triangle Model context operations |
| **Token** | `token_tools.py` | 10 | Token estimation and tracking |
| **Submodule** | `submodule_tools.py` | 4 | Git submodule integration |
| **Agent** | Dynamic | 19 | Agent invocation via discovery |
| **Workflow** | Dynamic | 16 | Workflow execution via discovery |
| **Handoff** | Dynamic | 22 | Handoff template generation |

## Tool Routing Table

| Pattern | Handler | Category |
|---------|---------|----------|
| `vibey_*task*` | `handle_task_tool()` | Task |
| `vibey_*sprint*`, `vibey_*refresh*` | `handle_sprint_tool()` | Sprint |
| `vibey_*query*`, `vibey_*roadmap*` | `handle_query_tool()` | Query |
| `vibey_content_*` | `handle_content_tool()` | Content |
| `vibey_associate_artifact`, `vibey_get_ticket_*`, etc. | `handle_context_tool()` | Context |
| `vibey_*token*` | `handle_token_tool()` | Token |
| `vibey_submodule_*`, `vibey_task_*_cross_*` | `handle_submodule_tool()` | Submodule |
| `vibey_*` (dynamic) | `_handle_dynamic_tool()` | Agent/Workflow/Handoff |

## Server Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SERVER LIFECYCLE                                │
└─────────────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ├── VibeyMCPServer.__init__(roadmap_root, framework_root)
   ├── Create RoadmapAdapter(roadmap_root)
   └── Create ToolDiscovery(framework_root, cache_ttl=60)

2. STARTUP (async run())
   ├── from mcp.server.fastmcp import FastMCP
   ├── mcp = FastMCP("vibey-roadmap")
   ├── tools = self.get_tools()
   ├── For each tool: mcp.tool(name, description)(handler)
   └── await mcp.run_stdio_async()

3. TOOL CALL (handle_tool_call)
   ├── Log: tool_name, arguments
   ├── Route to category handler
   ├── Execute via adapter
   ├── Return {content, isError}
   └── Handle VibeyMCPError, Exception

4. SHUTDOWN
   └── Exit on stdin close
```

## MCP Capabilities

```python
{
    "tools": {
        "listChanged": True  # Supports tool list change notifications
    },
    "resources": {
        "subscribe": False   # Resources implemented (8 total)
    },
    "prompts": {
        "listChanged": False # Prompts implemented (4 total)
    }
}
```

## RoadmapAdapter Interface

| Method | Purpose | Parameters |
|--------|---------|------------|
| `start_task()` | Mark task in_progress | task_id |
| `complete_task()` | Mark task completed | task_id, actual_tokens |
| `query_task()` | Get task details | task_id |
| `start_sprint()` | Mark sprint in_progress | sprint_id |
| `complete_sprint()` | Mark sprint completed | sprint_id |
| `query_sprint()` | Get sprint details | sprint_id |
| `get_roadmap_status()` | Get roadmap overview | None |
| `refresh_progress()` | Recalculate progress | None |
| `list_tasks()` | List all tasks | filters |
| `list_sprints()` | List all sprints | filters |

## Dynamic Tool Discovery

| Component | File | Purpose |
|-----------|------|---------|
| `ToolDiscovery` | `discovery/__init__.py` | Main discovery coordinator |
| `AgentDiscovery` | `discovery/agents.py` | Discovers agents from YAML frontmatter |
| `WorkflowDiscovery` | `discovery/workflows.py` | Discovers workflows from YAML |
| `HandoffDiscovery` | `discovery/handoffs.py` | Discovers handoff templates |
| `ToolGenerator` | `discovery/generator.py` | Generates tool definitions |
| `FrontmatterParser` | `discovery/parser.py` | Parses YAML frontmatter |

### Discovery Configuration

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `root_dir` | `cwd()` | Framework root directory |
| `cache_ttl` | 60 | Cache refresh interval (seconds) |
| `tool_prefix` | "vibey" | Tool name prefix |

## Error Handling

| Error Type | Handler | Response |
|------------|---------|----------|
| `VibeyMCPError` | Caught and logged | `{content: "Error: message", isError: true}` |
| `Exception` | Caught with traceback | `{content: "Unexpected error: ...", isError: true}` |
| Unknown tool | No handler match | `{content: "Unknown tool: name", isError: true}` |

## Remote Mode Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REMOTE MODE ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────┘

  LOCAL                                REMOTE (DATABRICKS)
  ─────                                ───────────────────

┌─────────────────┐                 ┌─────────────────┐
│ VibeyMCPServer  │                 │ REST API        │
│                 │                 │ (Jobs API)      │
└────────┬────────┘                 └────────┬────────┘
         │                                   │
┌────────▼────────┐                 ┌────────▼────────┐
│ RoadmapAdapter  │                 │ RemoteAdapter   │
│ (Local)         │───── SWAP ─────▶│ (Remote)        │
└────────┬────────┘                 └────────┬────────┘
         │                                   │
┌────────▼────────┐                 ┌────────▼────────┐
│ YAML + SQLite   │                 │ Delta Lake      │
│ (Local Storage) │                 │ (Remote Storage)│
└─────────────────┘                 └─────────────────┘
```

### Remote Mode Requirements

| Requirement | Implementation | Priority |
|-------------|----------------|----------|
| **RemoteAdapter** | New adapter implementing RoadmapAdapter | P0 |
| **Mode Flag** | `--remote` flag or config setting | P0 |
| **Authentication** | OAuth/PAT for Databricks | P0 |
| **Caching** | Local cache for offline support | P1 |
| **Retry Logic** | Exponential backoff for network errors | P1 |
| **Offline Queue** | Queue changes when offline | P1 |

## Integration Points

| Integration | Protocol | Purpose |
|-------------|----------|---------|
| **Claude Desktop** | stdio | AI assistant integration |
| **Cursor** | stdio | IDE integration |
| **VS Code** | stdio | IDE integration |
| **Custom clients** | stdio | Any MCP-compatible client |

## Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `.vibey/config/mcp.yaml` | MCP server configuration | YAML |
| `.vibey/config/adapters.yaml` | Adapter configuration | YAML |
| `claude_desktop_config.json` | Claude Desktop MCP config | JSON |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Server architecture documented: PASS
- [x] Tool categories and routing documented: PASS (7+ categories)
- [x] Server lifecycle documented: PASS
- [x] RoadmapAdapter interface documented: PASS
- [x] Remote mode architecture documented: PASS

## References

- `vibey/mcp/server.py` (500+ lines) - Main server implementation
- `vibey/mcp/adapters/roadmap_adapter.py` - Adapter abstraction
- `vibey/mcp/discovery/` - Dynamic tool discovery
- `vibey/mcp/tools/` - Tool implementations
- `docs/architecture/adr/0005-mcp-integration.md` - MCP ADR
