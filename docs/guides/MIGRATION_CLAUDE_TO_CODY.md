# Migration Guide: Claude Code to Sourcegraph Cody

This guide covers migrating your Vibey-powered project from Claude Code to Sourcegraph Cody.

## Overview

| Aspect | Claude Code | Cody |
|--------|-------------|------|
| MCP Support | Full | Via OpenCtx |
| Config Location | `.claude/` | `.cody/` |
| Context Files | `CLAUDE.md` | `CODY.md` |
| IDE Support | Terminal | VS Code, JetBrains |

## Important Notice

**Cody Free and Pro tiers sunset July 23, 2025.**

This integration targets **Cody Enterprise**. For non-enterprise use, Sourcegraph recommends [Amp](https://sourcegraph.com/amp).

## Why Cody Enterprise?

Cody Enterprise provides:
- **Code Graph** - Cross-repository understanding
- **Semantic Search** - Find code by meaning
- **Prompt Library** - Shared team templates
- **Admin Controls** - Enterprise governance
- **OpenCtx** - Native MCP support

## Migration Steps

### 1. Deploy Vibey for Cody

```bash
vibey deploy --platform cody
```

This creates:
- `.cody/mcp.json` - MCP server configuration (OpenCtx)
- `.cody/CODY.md` - Context for Cody
- `.cody/README.md` - Setup documentation

### 2. Install Cody Extension

**VS Code:**
1. Install "Sourcegraph Cody" from Extensions
2. Sign in with Sourcegraph Enterprise account
3. Restart VS Code

**JetBrains:**
1. Install "Sourcegraph Cody" from Plugins
2. Sign in with Sourcegraph Enterprise account
3. Restart IDE

### 3. Configure OpenCtx

Cody uses OpenCtx for MCP. The configuration in `.cody/mcp.json` is automatically detected.

Manual configuration (if needed):

**VS Code** (`settings.json`):
```json
{
  "cody.experimental.openctx": {
    "providers": {
      "vibey": {
        "command": "python",
        "args": ["-m", "framework.mcp.server"]
      }
    }
  }
}
```

### 4. Verify MCP Connection

1. Open Cody panel in your IDE
2. Ask: "What Vibey tools are available?"
3. Should list `vibey_roadmap_status` and other tools

## Configuration Comparison

### Claude Code

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

### Cody (OpenCtx)

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {}
    }
  }
}
```

Both use similar formats as Cody adopted the MCP standard via OpenCtx.

## Feature Mapping

| Claude Code | Cody |
|-------------|------|
| CLAUDE.md context | CODY.md context |
| Task subagents | Agent tools via MCP |
| Terminal interface | IDE panels |
| `/vibey` command | Cody chat |

## Enterprise Features

### Code Graph

Cody Enterprise provides cross-repository understanding:

```
@repo:other-service Explain how authentication works
```

### Context Mentions

Use @-mentions for precise context:
- `@file:path/to/file` - Include specific file
- `@symbol:functionName` - Include symbol definition
- `@repo:name` - Include repository context

### Prompt Library

Create shared prompts in Sourcegraph UI:
1. Go to Sourcegraph web interface
2. Navigate to Cody > Prompt Library
3. Create prompts using Vibey tools

Example prompt:
```
Use vibey_roadmap_status to show current sprint progress,
then summarize what tasks are blocking.
```

## Using Vibey Tools

### In Cody Chat

```
Check the project roadmap status using vibey_roadmap_status
```

```
Start task task-001 using vibey_start_task
```

### With Context

```
@file:.vibey/roadmap.yaml What's the status of the current sprint?
Use vibey_query_sprint if needed.
```

## Sourcegraph Integration

### Search + Cody

Combine Sourcegraph search with Cody:

1. Search for code: `repo:myrepo function:authenticate`
2. Select results
3. Ask Cody to explain or modify

### Batch Changes

Use Cody to help write batch change specs:

```
Help me write a batch change spec to update all files
that use the old API endpoint.
```

## Troubleshooting

### OpenCtx Not Connecting

1. Check Cody extension is updated
2. Verify `.cody/mcp.json` syntax
3. Check VS Code output panel for errors
4. Restart IDE

### Tools Not Available

1. Ensure OpenCtx experimental features are enabled
2. Check Python is in PATH
3. Verify `framework.mcp.server` module exists

### Enterprise Features Not Working

1. Verify Enterprise subscription is active
2. Check Sourcegraph instance connection
3. Contact Sourcegraph support

## Running Both Platforms

Maintain parallel deployments:

```bash
# Deploy to both
vibey deploy --platform claude-code
vibey deploy --platform cody

# Or deploy all
vibey deploy --platform all
```

Directories are separate:
- Claude Code: `.claude/`
- Cody: `.cody/`

## Migration Checklist

- [ ] Verify Cody Enterprise subscription
- [ ] Deploy Vibey for Cody
- [ ] Install Cody extension
- [ ] Configure OpenCtx if needed
- [ ] Test MCP connection
- [ ] Verify all tools work
- [ ] Create Prompt Library entries (optional)
- [ ] Document team workflow

## Best Practices

1. **Use Context Mentions** - Leverage @-syntax for precise context
2. **Create Team Prompts** - Share common workflows via Prompt Library
3. **Combine with Search** - Use Sourcegraph search + Cody together
4. **Enterprise Controls** - Set up admin policies for MCP tools

## Next Steps

After migration:

1. Train team on Cody interface
2. Create Prompt Library templates
3. Set up enterprise policies
4. Document Cody-specific workflows

---

For more information:
- [Cody Documentation](https://sourcegraph.com/docs/cody)
- [OpenCtx MCP Support](https://sourcegraph.com/docs/cody/capabilities/openctx)
- [Cody Enterprise](https://sourcegraph.com/cody/enterprise)
- [Vibey Framework Documentation](../README.md)
