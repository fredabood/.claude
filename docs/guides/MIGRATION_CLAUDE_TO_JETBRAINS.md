# Migration Guide: Claude Code to JetBrains AI Assistant

This guide covers migrating your Vibey-powered project from Claude Code to JetBrains AI Assistant.

## Overview

| Aspect | Claude Code | JetBrains AI |
|--------|-------------|--------------|
| MCP Support | Full | Full (2025+) |
| Config Location | `.claude/` | `.idea/ai/` |
| Config Format | JSON dict | JSON array |
| Context Files | `CLAUDE.md` | `JETBRAINS.md` |
| IDE Integration | Terminal | Native IDE |

## Supported JetBrains IDEs

- IntelliJ IDEA (Ultimate/Community)
- PyCharm (Professional/Community)
- WebStorm
- GoLand
- PhpStorm
- Rider
- RubyMine
- DataGrip
- CLion

## Migration Steps

### 1. Deploy Vibey for JetBrains

```bash
vibey deploy --platform jetbrains
```

This creates:
- `.idea/ai/mcp-servers.json` - MCP server configuration
- `.idea/ai/JETBRAINS.md` - Context for AI Assistant
- `.idea/ai/README.md` - Setup documentation

### 2. Verify Deployment

```bash
ls -la .idea/ai/
```

Expected output:
```
mcp-servers.json
JETBRAINS.md
README.md
.checksums.json
```

### 3. Configure Your IDE

1. Open your project in JetBrains IDE
2. Go to **Settings/Preferences**
3. Navigate to **Tools > AI Assistant**
4. Enable MCP integration
5. Restart the IDE

### 4. Verify MCP Connection

1. Open AI Assistant panel
2. Ask: "What Vibey tools are available?"
3. The assistant should list `vibey_roadmap_status`, agents, and workflows

## Configuration Differences

### Claude Code (`claude_desktop_config.json`)

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

### JetBrains (`mcp-servers.json`)

```json
{
  "servers": [
    {
      "name": "vibey",
      "displayName": "Vibey Agent Framework",
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "enabled": true
    }
  ]
}
```

Key differences:
- JetBrains uses `servers` array instead of `mcpServers` dict
- Each server has `name`, `displayName`, and `enabled` fields
- Additional metadata supported for IDE integration

## Feature Mapping

| Claude Code | JetBrains AI |
|-------------|--------------|
| CLAUDE.md context | JETBRAINS.md context |
| `/vibey` command | AI Assistant panel |
| Task subagents | Agent tools via MCP |
| Slash commands | IDE-native commands |

## Using Vibey Tools

### Roadmap Management

```
Use vibey_roadmap_status to check the project status
```

### Starting Tasks

```
Use vibey_start_task to begin work on task-001
```

### Agent Invocation

```
Use vibey_test_engineer to write tests for the new feature
```

## IDE-Specific Features

JetBrains AI Assistant provides:

- **Code Context**: Automatic file context from editor
- **Refactoring**: AI-assisted code transformations
- **Documentation**: Inline doc generation
- **Debugging**: AI-powered debug assistance
- **Git Integration**: Commit message suggestions

## Troubleshooting

### MCP Server Not Found

1. Check Python is in PATH
2. Verify `framework.mcp.server` module exists
3. Check IDE logs: **Help > Diagnostic Tools > Debug Log Settings**

### Tools Not Available

1. Restart IDE after config changes
2. Check `.idea/ai/mcp-servers.json` syntax
3. Verify server is `"enabled": true`

### Context Not Loading

1. Ensure `JETBRAINS.md` exists in `.idea/ai/`
2. Check file permissions
3. Re-run `vibey deploy --platform jetbrains`

## Running Both Platforms

You can maintain both Claude Code and JetBrains deployments:

```bash
# Deploy to both
vibey deploy --platform claude-code
vibey deploy --platform jetbrains

# Or deploy all
vibey deploy --platform all
```

Each platform uses its own directory:
- Claude Code: `.claude/`
- JetBrains: `.idea/ai/`

## Best Practices

1. **Keep deployments synced**: Redeploy after framework changes
2. **Use platform strengths**: Leverage IDE integration in JetBrains
3. **Test tooling**: Verify MCP tools work after migration
4. **Document differences**: Note any platform-specific behaviors

## Next Steps

After migration:

1. Test all Vibey tools in AI Assistant
2. Verify roadmap operations work
3. Test agent and workflow invocations
4. Configure IDE-specific settings as needed

---

For more information:
- [JetBrains AI Assistant Docs](https://www.jetbrains.com/help/idea/ai-assistant.html)
- [Vibey Framework Documentation](../README.md)
