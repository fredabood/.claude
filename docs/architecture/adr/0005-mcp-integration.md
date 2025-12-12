# ADR-0005: MCP Protocol for AI Integration

## Status

Accepted

## Context

Vibey needs to integrate with multiple AI coding assistants (Claude Code, Goose, Cursor, etc.). Each platform has different integration mechanisms:

- Claude Code: CLAUDE.md file, slash commands
- Goose: MCP extensions
- Cursor: .cursorrules file
- VS Code: MCP servers

Options:
1. **Platform-specific integrations** for each assistant
2. **MCP (Model Context Protocol)** as unified interface
3. **REST API** as integration layer
4. **Custom protocol** designed for Vibey

## Decision

Use MCP (Model Context Protocol) as the primary integration mechanism for AI assistants.

**Components:**
- **Tools**: Actions the AI can perform (76+ tools)
- **Resources**: Data the AI can access (8 templates)
- **Prompts**: Pre-built prompts for common tasks (4 prompts)

```
┌─────────────────────┐
│   AI Assistant      │
│  (Claude/Goose/...) │
└──────────┬──────────┘
           │ MCP Protocol
           ▼
┌──────────────────────┐
│   Vibey MCP Server   │
│  - 76 Tools          │
│  - 8 Resources       │
│  - 4 Prompts         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Vibey Operations   │
│  (Roadmap, Deploy,   │
│   Docs, etc.)        │
└──────────────────────┘
```

## Consequences

### Positive

- **Platform agnostic**: Single implementation serves multiple AI platforms
- **Standard protocol**: MCP is emerging industry standard
- **Rich capabilities**: Tools, resources, and prompts cover all use cases
- **Introspectable**: Can auto-generate documentation from server
- **Testable**: MCP calls are structured and deterministic

### Negative

- **Protocol overhead**: JSON-RPC adds some latency
- **MCP adoption**: Not all platforms support MCP yet
- **Complexity**: Must maintain server alongside CLI
- **Debugging**: Protocol layer adds debugging complexity

### Neutral

- CLI and MCP share underlying operations (no duplication)
- Platform adapters still needed for non-MCP platforms
- Can fall back to platform-specific integrations where needed

## Implementation Details

### Tool Categories

| Category | Count | Examples |
|----------|-------|----------|
| Task | 3 | `vibey_start_task`, `vibey_complete_task` |
| Sprint | 4 | `vibey_start_sprint`, `vibey_refresh_progress` |
| Query | 5 | `vibey_roadmap_status`, `vibey_list_blockers` |
| Content | 7 | `vibey_content_list`, `vibey_content_show` |
| Agent | 19 | `vibey_test_engineer`, `vibey_web_developer` |
| Workflow | 16 | `vibey_workflow_feature_development` |
| Handoff | 22 | `vibey_handoff_api_spec` |

### Resource Templates

```
vibey://workflows/{id}           # Workflow content
vibey://workflows/{id}/steps     # Workflow steps
vibey://handoffs/{id}            # Handoff template
vibey://handoffs/{id}/variables  # Template variables
```

### Prompts

| Prompt | Purpose |
|--------|---------|
| `vibey_quality_gate_check` | Run quality gates |
| `vibey_security_scan` | Security analysis |
| `vibey_test_coverage` | Test coverage check |
| `vibey_doc_check` | Documentation check |

### Server Implementation

```python
from mcp.server import Server
from mcp.types import Tool, Resource, Prompt

server = Server("vibey-roadmap")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="vibey_start_task",
            description="Start working on a task",
            inputSchema={...}
        ),
        ...
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Any:
    if name == "vibey_start_task":
        return start_task(arguments["task_id"])
    ...
```

## Alternatives Considered

### Platform-specific Only

**Pros:**
- Maximum platform optimization
- No protocol overhead

**Cons:**
- Multiply maintenance effort by platforms
- Inconsistent capabilities

### REST API

**Pros:**
- Universal HTTP access
- Well-understood patterns

**Cons:**
- Requires hosting server
- More complex deployment
- Not designed for AI assistant integration

### Custom Protocol

**Pros:**
- Optimal for Vibey's needs
- No external dependencies

**Cons:**
- Non-standard
- AI assistants won't natively support

## References

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Anthropic MCP SDK](https://github.com/anthropics/mcp)
- Vibey MCP server in `vibey/mcp/`
- Auto-generated MCP reference in `docs/reference/MCP_REFERENCE.md`
