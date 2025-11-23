# Migration Guide: Claude Code to GitHub Copilot

This guide helps you migrate from Claude Code to GitHub Copilot while maintaining your Vibey Agent Framework workflows.

## Overview

GitHub Copilot supports MCP (since July 2025) and custom agents (since October 2025), enabling full Vibey integration. Your existing workflows will work with some differences in interaction patterns.

## Prerequisites

- Existing Vibey setup in Claude Code
- GitHub Copilot subscription (Individual or Enterprise)
- VS Code with Copilot extension, or JetBrains IDE with Copilot plugin
- Optional: GitHub CLI with Copilot extension for MCP tools

## Migration Steps

### Step 1: Deploy Vibey for Copilot

From your project directory:

```bash
# Generate Copilot-specific configuration
vibey deploy --platform copilot
```

This creates:
```
.github/
├── copilot-instructions.md    # Repository-wide AI instructions
├── agents/                     # Custom agent profiles
│   ├── coordinator.md
│   ├── web-developer.md
│   └── ... (19 agents)
├── COPILOT.md                  # Context file
├── COPILOT_README.md           # Setup instructions
└── .checksums.json             # Drift detection
```

### Step 2: Commit Configuration

Copilot reads configuration from the repository:

```bash
git add .github/
git commit -m "feat: Add Vibey Copilot configuration"
git push
```

### Step 3: Open in IDE

1. Open your IDE (VS Code or JetBrains)
2. Ensure Copilot extension/plugin is active
3. Copilot automatically reads `.github/copilot-instructions.md`

### Step 4: Verify Integration

In Copilot Chat, try:
```
What Vibey tools are available in this project?
```

Copilot should reference the repository instructions and list available agents.

## Feature Mapping

### MCP Tools

MCP tools require Copilot CLI:

```bash
# Install GitHub CLI Copilot extension
gh extension install github/gh-copilot

# Use MCP tools
gh copilot suggest "use vibey_roadmap_status"
```

| Tool Category | Claude Code | Copilot CLI |
|--------------|-------------|-------------|
| Roadmap tools | Direct MCP | `gh copilot suggest "use vibey_*"` |
| Agent tools | Direct MCP | Via custom agents or CLI |
| Workflow tools | Direct MCP | Via custom agents or CLI |

### Custom Agents

Copilot's custom agents map to Vibey agents:

| Claude Code | Copilot | Usage |
|-------------|---------|-------|
| `vibey_coordinator` | `@coordinator` | `@coordinator Help me plan this feature` |
| `vibey_web_developer` | `@web-developer` | `@web-developer Create a React component` |
| `vibey_test_engineer` | `@test-engineer` | `@test-engineer Write tests for auth` |

### Context Files

| Claude Code | Copilot | Notes |
|-------------|---------|-------|
| `CLAUDE.md` | `copilot-instructions.md` | Repository instructions |
| `.claude/` | `.github/` | Configuration directory |
| N/A | `.github/agents/` | Custom agent profiles |

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

### Copilot (.github/copilot-instructions.md)

```markdown
# Vibey Agent Framework Instructions

This repository uses the Vibey Agent Framework...

## MCP Tools
When using Copilot CLI with MCP enabled:
- `vibey_roadmap_status` - Get overall roadmap status
- `vibey_start_task` / `vibey_complete_task` - Track tasks
...
```

**Key Difference:** Copilot uses markdown instructions rather than JSON config.

## Interaction Pattern Changes

### Chat Invocation

**Claude Code:**
```
Use the vibey_coordinator to route this request.
```

**Copilot (with custom agents):**
```
@coordinator Help me with this request.
```

### Workflow Execution

**Claude Code:**
```
Use vibey_workflow_sprint_planning to plan the next sprint.
```

**Copilot:**
```
Using the sprint planning workflow described in the repository instructions,
help me plan the next sprint.
```

Or with Copilot CLI:
```bash
gh copilot suggest "use vibey_workflow_sprint_planning"
```

### Task Management

**Claude Code (direct MCP):**
```
Use vibey_start_task with task_id="feature-123"
```

**Copilot CLI:**
```bash
gh copilot suggest "start task feature-123 using vibey_start_task"
```

## Custom Agent Profiles

Vibey generates `.github/agents/*.md` for each agent:

```markdown
# Web Developer

Build modern, responsive user interfaces.

## Capabilities

- frontend
- ui component
- react component
- user interface
- responsive design

## MCP Tool

Invoke via MCP: `vibey_web_developer`

## Usage

Use this agent for web developer-related tasks.
```

Reference in Copilot Chat:
```
@web-developer Create a dashboard component with charts
```

## Keeping Both Platforms

You can use both Claude Code and Copilot:

```bash
# Deploy to both
vibey deploy --platform claude-code
vibey deploy --platform copilot
```

Both share:
- `.vibey/` source of truth
- `framework/agents/*.md` definitions
- `framework/workflows/*.md` definitions

## Key Differences

| Aspect | Claude Code | Copilot |
|--------|-------------|---------|
| MCP Access | Native, direct | Via CLI or Agent Mode |
| Custom Agents | N/A | `.github/agents/*.md` |
| Instructions | `CLAUDE.md` | `copilot-instructions.md` |
| Tool Invocation | Direct tool calls | Natural language + CLI |
| Multi-model | Claude only | Multiple models |
| Enterprise | N/A | GitHub Enterprise integration |

## Troubleshooting

### Instructions Not Being Read

1. Verify `.github/copilot-instructions.md` exists
2. Ensure file is committed to repository
3. Restart your IDE
4. Check Copilot has repository access

### Custom Agents Not Available

1. Verify `.github/agents/` directory exists
2. Ensure agent files have correct format
3. Commit files to repository
4. Try `@` mention to see available agents

### MCP Tools Not Working

1. MCP requires Copilot CLI: `gh extension install github/gh-copilot`
2. Verify Python is in PATH
3. Test: `python -m framework.mcp.server`
4. Use `gh copilot --help` to verify CLI installation

### Roadmap Data Issues

1. Ensure `.vibey/roadmap/` exists
2. Run `vibey roadmap status` locally first
3. MCP tools need local access to `.vibey/`

## What Doesn't Transfer

| Feature | Claude Code | Copilot | Notes |
|---------|-------------|---------|-------|
| Chat history | Local | Cloud | Not transferable |
| Direct MCP | Native | CLI only | Different interaction |
| Model choice | Claude | Multi-model | Different capabilities |

## Best Practices

1. **Use custom agents** - Reference `@agent-name` in Copilot Chat
2. **Leverage instructions** - Keep `copilot-instructions.md` comprehensive
3. **CLI for MCP** - Use `gh copilot` for direct tool access
4. **Keep .vibey/ synced** - Ensure roadmap data is current
5. **Version control** - Commit all `.github/` files

## Enterprise Considerations

For GitHub Enterprise:

1. **Organization instructions** - Set org-level defaults
2. **Team agents** - Share custom agents across repos
3. **Policy compliance** - Review Copilot policies
4. **SSO integration** - Configure authentication

See [Enterprise Deployment Guide](./COPILOT_ENTERPRISE_DEPLOYMENT.md) for details.

## Rollback

To return to Claude Code only:

```bash
# Remove Copilot config (optional)
rm -rf .github/copilot-instructions.md
rm -rf .github/agents/
rm .github/COPILOT.md

# Continue using Claude Code
vibey deploy --platform claude-code
```

## Next Steps

1. Explore Copilot's multi-model capabilities
2. Set up custom agents for your team
3. Configure organization-level instructions
4. Consider GitHub Enterprise for team features

## Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Copilot Custom Agents](https://docs.github.com/en/copilot/customizing-copilot/custom-agents)
- [Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
- [Vibey Copilot Integration](./COPILOT_INTEGRATION.md)
