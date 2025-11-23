# Migration Guide: Claude Code to Replit

This guide covers migrating your Vibey-powered project from Claude Code to Replit.

## Overview

| Aspect | Claude Code | Replit |
|--------|-------------|--------|
| MCP Support | Full | Native (early adopter) |
| Config Location | `.claude/` | `.replit-vibey/` |
| Environment | Local terminal | Web-based IDE |
| Setup | Local install | Fork template |

## Why Replit?

Replit offers unique advantages:
- **Zero Setup** - No local installation required
- **Native MCP** - Replit shipped MCP support early
- **Collaboration** - Real-time multiplayer editing
- **Accessibility** - Works from any browser
- **Education** - Strong presence in learning environments

## Migration Steps

### 1. Deploy Vibey for Replit

```bash
vibey deploy --platform replit
```

This creates:
- `.replit-vibey/mcp.json` - MCP server configuration
- `.replit-vibey/REPLIT.md` - Context for Replit AI
- `.replit-vibey/README.md` - Setup documentation

### 2. Create Replit Project

Option A: **Fork Template** (Recommended)
1. Visit the Vibey Replit template
2. Click **Fork**
3. Your project is ready

Option B: **Import from GitHub**
1. Create new Replit
2. Import from your repository
3. Copy `.replit-vibey/` contents

### 3. Configure Replit Environment

Create or update `.replit` file:

```toml
run = "python -m framework.mcp.server"

[nix]
channel = "stable-24_05"

[env]
PYTHONPATH = "${REPL_HOME}"
```

### 4. Install Dependencies

In Replit Shell:
```bash
pip install pyyaml jinja2
```

Or add to `pyproject.toml`:
```toml
[tool.poetry.dependencies]
python = "^3.9"
pyyaml = "^6.0"
jinja2 = "^3.1"
```

### 5. Verify MCP Connection

1. Open Replit AI panel
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

### Replit

```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "REPLIT": "1"
      }
    }
  }
}
```

The `REPLIT` environment variable enables web-specific behaviors.

## Feature Mapping

| Claude Code | Replit |
|-------------|--------|
| CLAUDE.md context | REPLIT.md context |
| Local filesystem | Replit workspace |
| Task subagents | Agent tools via MCP |
| Terminal commands | Shell tab |

## Web Environment Considerations

### File Persistence
- All files persist in your Replit workspace
- No local filesystem access
- Use Replit's file browser

### Python Runtime
- Full Python 3.9+ available in browser
- Some packages may have limitations
- Nix packages for system dependencies

### Real-time Collaboration
- Multiple users can edit simultaneously
- Share workspace URL for collaboration
- Comments and chat built-in

## Using Vibey Tools in Replit

### Via Replit AI

```
Use vibey_roadmap_status to check project progress
```

### Via Shell

```bash
# Start MCP server manually if needed
python -m framework.mcp.server
```

## Template Distribution

Create a forkable template:

1. Set up your Vibey project in Replit
2. Go to **Settings > Template**
3. Enable **Make this Repl a template**
4. Share the template URL

## Troubleshooting

### MCP Server Won't Start

1. Check Python path: `which python`
2. Verify dependencies: `pip list | grep yaml`
3. Check error logs in Shell

### Tools Not Available

1. Restart the Replit
2. Check `mcp.json` syntax
3. Verify `framework.mcp.server` module exists

### Slow Performance

- Replit free tier has resource limits
- Consider Replit Pro for better performance
- Optimize large file operations

## Running Both Platforms

You can maintain both deployments:

```bash
# Deploy to both
vibey deploy --platform claude-code
vibey deploy --platform replit
```

Each uses its own directory:
- Claude Code: `.claude/`
- Replit: `.replit-vibey/`

## Best Practices

1. **Use Templates** - Share via forkable templates
2. **Document Setup** - Include Replit-specific README
3. **Test in Browser** - Verify web compatibility
4. **Leverage Multiplayer** - Use for team workflows

## Next Steps

After migration:

1. Fork or create Replit project
2. Install dependencies
3. Verify MCP tools work
4. Share template with team

---

For more information:
- [Replit Documentation](https://docs.replit.com)
- [Replit MCP Blog Post](https://blog.replit.com/everything-you-need-to-know-about-mcp)
- [Vibey Framework Documentation](../README.md)
