# Migration Guide: Claude Code to Goose

> **Version:** 1.0.0
> **Last Updated:** 2025-11-22

This guide helps you migrate from using Vibey with Claude Code to using it with Goose.

## Overview

Vibey now supports both Claude Code and Goose through a unified MCP server. The same 46 tools work on both platforms.

| Feature | Claude Code | Goose |
|---------|-------------|-------|
| Protocol | MCP | MCP |
| Tools | 46 | 46 |
| Roadmap | ✅ | ✅ |
| Agents | ✅ | ✅ |
| Workflows | ✅ | ✅ |
| Recipes | N/A | ✅ |

## Migration Steps

### Step 1: Verify Prerequisites

**Already have from Claude Code:**
- Vibey repository cloned
- Python virtual environment
- `.vibey/` directory with roadmap

**Need for Goose:**
- Goose installed
- Updated Vibey (with MCP server)

### Step 2: Update Vibey

```bash
cd /path/to/vibey
git pull origin main
.venv/bin/pip install -r requirements.txt
```

### Step 3: Test MCP Server

```bash
.venv/bin/python scripts/run-mcp-server.py
# Should start without errors
# Press Ctrl+C to stop
```

### Step 4: Configure Goose

Create or edit `~/.config/goose/config.yaml`:

```yaml
extensions:
  vibey:
    name: vibey
    type: stdio
    cmd: /absolute/path/to/vibey/.venv/bin/python
    args:
      - /absolute/path/to/vibey/scripts/run-mcp-server.py
    enabled: true
    timeout: 300
    description: Vibey Agent Framework
```

### Step 5: Keep Claude Code Configuration

You can use both! Keep your `.mcp.json` for Claude Code:

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

### Step 6: Verify on Goose

```bash
goose session

> What's the roadmap status?
# Should return your roadmap data
```

## Feature Comparison

### Invoking Agents

**Claude Code:**
```
Use the test engineer to write tests for my code
```

**Goose:**
```
Use vibey_test_engineer to write tests for my code
```

Both work - Goose may be more explicit about tool names.

### Running Workflows

**Claude Code:**
```
Run the feature development workflow
```

**Goose:**
```
Run vibey_workflow_feature_development for my feature
```

### Checking Roadmap

**Claude Code:**
```
What's the project status?
```

**Goose:**
```
Call vibey_roadmap_status
```

## What Stays the Same

### 1. Roadmap Data

Your `.vibey/roadmap/` directory works identically:
- Same tracks, sprints, tasks
- Same YAML format
- Same progress tracking

### 2. Agent Definitions

All `framework/agents/*.md` files work on both platforms.

### 3. Workflow Definitions

All `framework/workflows/*.md` files work on both platforms.

### 4. Tool Names

Same `vibey_` prefixed names on both platforms.

## What's Different

### 1. Recipes (Goose Only)

Goose supports recipes - predefined tool sequences:

```bash
# Export recipes from workflows
vibey export --platform goose --output ./exports

# Use in Goose
> Run the feature-development recipe
```

### 2. LLM Choice

| Platform | LLM |
|----------|-----|
| Claude Code | Claude only |
| Goose | Claude, GPT-4, Gemini, local models |

### 3. Configuration Location

| Platform | Config File |
|----------|-------------|
| Claude Code | `.mcp.json` (project root) |
| Goose | `~/.config/goose/config.yaml` |

## Migration Checklist

- [ ] Updated Vibey to latest version
- [ ] Installed Goose
- [ ] Tested MCP server locally
- [ ] Created Goose configuration
- [ ] Verified tools appear in Goose
- [ ] Tested roadmap status
- [ ] Tested agent invocation
- [ ] (Optional) Exported recipes
- [ ] (Optional) Kept Claude Code config

## Troubleshooting

### "No tools found"

1. Check config paths are absolute
2. Verify Python path is correct
3. Restart Goose after config change

### "Different results between platforms"

Both use the same MCP server, so results should be identical. If different:
1. Check you're pointing to same Vibey installation
2. Verify roadmap root is the same
3. Check for cached data

### "Roadmap not found"

Ensure `--roadmap-root` points to your project:
```yaml
args:
  - /path/to/scripts/run-mcp-server.py
  - --roadmap-root
  - /path/to/your-project/.vibey/roadmap
```

### "Claude Code stopped working"

Check `.mcp.json` wasn't modified. You can use both simultaneously.

## Using Both Platforms

You can use Vibey on both platforms simultaneously:

```
Project/
├── .mcp.json           # Claude Code config
├── .vibey/
│   └── roadmap/        # Shared roadmap data
└── ...

~/.config/goose/
└── config.yaml         # Goose config (points to same Vibey)
```

**Benefits:**
- Use Claude for some tasks, Goose for others
- Test LLM differences
- Gradual migration

## Advanced: Per-Project Switching

### Option 1: Environment Variable

```yaml
# Goose config
extensions:
  vibey:
    cmd: /path/to/.venv/bin/python
    args:
      - /path/to/scripts/run-mcp-server.py
    envs:
      VIBEY_ROADMAP_ROOT: ${PROJECT_ROOT}/.vibey/roadmap
```

### Option 2: Multiple Extensions

```yaml
extensions:
  vibey-project-a:
    enabled: true
    args:
      - --roadmap-root
      - /path/to/project-a/.vibey/roadmap

  vibey-project-b:
    enabled: false
    args:
      - --roadmap-root
      - /path/to/project-b/.vibey/roadmap
```

Toggle `enabled` based on current project.

## Rollback

If you need to go back to Claude Code only:

1. Remove Goose extension config
2. Continue using `.mcp.json`
3. Vibey works unchanged

## FAQ

**Q: Do I need to migrate my roadmap data?**
A: No, the same roadmap works on both platforms.

**Q: Will my sprint progress transfer?**
A: Yes, it's the same data.

**Q: Can I use different LLMs for different tasks?**
A: Yes! Use Goose for LLM flexibility, Claude Code for Claude-specific features.

**Q: Is one platform better?**
A: Depends on your needs:
- Claude Code: Best Claude integration, VS Code native
- Goose: LLM flexibility, recipes, CLI-focused

**Q: Do I lose any features?**
A: No features are lost. Goose adds recipes.

## Related Documentation

- [Goose Integration Guide](./GOOSE_INTEGRATION.md)
- [Recipe Development Guide](./RECIPE_DEVELOPMENT.md)
- [Frontmatter Schema](../reference/FRONTMATTER_SCHEMA.md)
