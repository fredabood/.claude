# Migration Guide: Claude Code to Cursor

This guide helps you migrate from Claude Code to Cursor while maintaining your Vibey Agent Framework workflows.

## Overview

Both Claude Code and Cursor have native MCP support, making migration straightforward. Your existing Vibey framework, agents, and workflows will work identically in Cursor.

## Prerequisites

- Existing Vibey setup in Claude Code
- Cursor IDE installed (with MCP support, Nov 2024+)
- Python 3.9+

## Migration Steps

### Step 1: Deploy Vibey for Cursor

From your project directory:

```bash
# Generate Cursor-specific configuration
vibey deploy --platform cursor
```

This creates:
```
.cursor/
├── mcp.json          # MCP server configuration
├── CURSOR.md         # Context file
├── README.md         # Setup instructions
└── .checksums.json   # Drift detection

.cursorrules          # Project AI rules (in project root)
```

### Step 2: Open Project in Cursor

1. Open Cursor IDE
2. Open your project folder (File → Open Folder)
3. Cursor automatically detects `.cursor/mcp.json`
4. The Vibey MCP server starts automatically

### Step 3: Verify MCP Connection

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Navigate to the MCP section
3. Verify "vibey" server shows as connected
4. Test with: "Use vibey_roadmap_status to show project status"

## Feature Mapping

### MCP Tools (Identical)

All 46 Vibey MCP tools work identically:

| Tool Category | Claude Code | Cursor |
|--------------|-------------|--------|
| Roadmap tools | `vibey_roadmap_status` | `vibey_roadmap_status` |
| Agent tools | `vibey_coordinator` | `vibey_coordinator` |
| Workflow tools | `vibey_workflow_*` | `vibey_workflow_*` |

### Context Files

| Claude Code | Cursor | Notes |
|-------------|--------|-------|
| `CLAUDE.md` | `CURSOR.md` | Platform-specific context |
| `.claude/` | `.cursor/` | Configuration directory |
| N/A | `.cursorrules` | Project AI rules |

### Interaction Patterns

| Feature | Claude Code | Cursor |
|---------|-------------|--------|
| Chat | Claude Code chat | Composer (Cmd/Ctrl + K) |
| Inline | Cmd + K | Cmd + K |
| Agent invocation | MCP tools | MCP tools |
| Context | CLAUDE.md auto-read | CURSOR.md + .cursorrules |

## Configuration Comparison

### Claude Code (.claude/settings.json)

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"]
    }
  }
}
```

### Cursor (.cursor/mcp.json)

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"]
    }
  }
}
```

**Note:** The format is identical (Claude Desktop format).

## .cursorrules Benefits

Cursor supports `.cursorrules` for project-wide AI behavior. Vibey generates this automatically:

```markdown
# Vibey Agent Framework Rules

This project uses the Vibey Agent Framework...

## MCP Tools
- `vibey_roadmap_status` - Check roadmap progress
- `vibey_start_task` / `vibey_complete_task` - Manage tasks

## Available Agents
- `vibey_coordinator` - Intelligent request router
- `vibey_web_developer` - Web Developer
...
```

This ensures Cursor's AI always knows about Vibey tools.

## Workflow Migration

### Sprint Planning

**Claude Code:**
```
Use the vibey_workflow_sprint_planning tool to plan the next sprint.
```

**Cursor (identical):**
```
Use the vibey_workflow_sprint_planning tool to plan the next sprint.
```

### Feature Development

**Claude Code:**
```
Use vibey_workflow_single_feature_development for the auth feature.
```

**Cursor (identical):**
```
Use vibey_workflow_single_feature_development for the auth feature.
```

## Keeping Both Platforms

You can use both Claude Code and Cursor simultaneously:

```bash
# Deploy to both platforms
vibey deploy --platform claude-code
vibey deploy --platform cursor
```

Both will use the same:
- `.vibey/` source of truth
- `framework/agents/*.md` definitions
- `framework/workflows/*.md` definitions
- MCP server (`framework/mcp/server.py`)

## Troubleshooting

### MCP Server Not Starting

1. Verify Python is in PATH: `which python`
2. Test server manually: `python -m framework.mcp.server`
3. Check Cursor MCP logs for errors
4. Ensure no other process is using the MCP port

### Tools Not Appearing

1. Restart Cursor
2. Verify `.cursor/mcp.json` exists and is valid JSON
3. Check that `python -m framework.mcp.server` runs without errors
4. Look for connection status in Cursor's MCP settings

### .cursorrules Not Applied

1. Verify `.cursorrules` is in project root (not in `.cursor/`)
2. File must not be empty
3. Restart Cursor to reload rules

### Roadmap Data Not Found

1. Ensure `.vibey/roadmap/` exists
2. Run `vibey roadmap status` to verify roadmap is initialized
3. Check file permissions

## What Doesn't Transfer

| Feature | Claude Code | Cursor | Notes |
|---------|-------------|--------|-------|
| Chat history | Stored locally | Stored locally | Not transferable |
| Custom prompts | Claude-specific | Cursor-specific | Recreate in Cursor |
| Shortcuts | Claude bindings | Cursor bindings | Reconfigure |

## Best Practices

1. **Keep .vibey/ as source of truth** - Never edit generated files directly
2. **Regenerate on changes** - Run `vibey deploy --platform cursor` after framework updates
3. **Use .cursorrules** - Leverage Cursor's project rules feature
4. **Version control** - Commit both `.cursor/` and `.cursorrules`

## Rollback

To go back to Claude Code only:

```bash
# Remove Cursor config (optional)
rm -rf .cursor/
rm .cursorrules

# Continue using Claude Code
vibey deploy --platform claude-code
```

## Next Steps

1. Explore Cursor's Composer for complex multi-file edits
2. Try Cursor's inline editing (Cmd + K in editor)
3. Use `.cursorrules` for team-wide AI standards
4. Consider Cursor's multi-model support (Claude, GPT-4, etc.)

## Resources

- [Cursor Documentation](https://docs.cursor.com/)
- [Cursor MCP Setup](https://docs.cursor.com/context/model-context-protocol)
- [Vibey Cursor Integration](./CURSOR_INTEGRATION.md)
