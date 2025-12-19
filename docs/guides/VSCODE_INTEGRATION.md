# VS Code Native MCP Integration Guide

This guide explains how to use Vibey Agent Framework with VS Code's native MCP support, available since VS Code 1.102 (July 2025).

## Overview

VS Code has **full native MCP support** without requiring any extension. This makes Vibey integration simple and powerful.

### Why VS Code Native MCP?

- **No extension required** - MCP is built into VS Code
- **Full MCP spec support** - Tools, Resources, Prompts, Sampling, Auth
- **Multiple transports** - stdio, HTTP, SSE, Unix sockets
- **Works with Copilot and Agent Mode** - Full AI assistant integration

## Quick Start

```bash
# 1. Install Vibey (if not already installed)
git clone https://github.com/anthropics/vibey.git && cd vibey && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# 2. Initialize Vibey in your project
cd your-project
vibey roadmap init

# 3. Deploy to VS Code
vibey deploy --platform vscode

# 4. Open project in VS Code - MCP is automatically detected!
code .
```

## What Gets Generated

When you run `vibey deploy --platform vscode`, the following files are created:

```
.vscode/
├── mcp.json             # MCP server configuration
├── VSCODE.md            # Context file with tool reference
├── README.md            # Installation instructions
└── .checksums.json      # Drift detection checksums
```

## Configuration File

The generated `.vscode/mcp.json` uses VS Code's native format:

```json
{
  "servers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"]
    }
  }
}
```

**Note:** VS Code uses `"servers"` (not `"mcpServers"` like Claude Desktop).

## VS Code MCP Features

VS Code's native MCP support includes:

| Feature | Status | Description |
|---------|--------|-------------|
| Tools | Full | All 46 Vibey tools available |
| Resources | Full | MCP resources supported |
| Prompts | Full | MCP prompts supported |
| Sampling | Full | Model sampling supported |
| Authentication | Full | OAuth and API key support |
| Roots | Full | Workspace roots supported |
| Elicitation | Full | User prompting supported |

## Available MCP Tools

### Roadmap Tools

| Tool | Description |
|------|-------------|
| `vibey_roadmap_status` | Get overall roadmap status |
| `vibey_start_task` | Mark a task as in-progress |
| `vibey_complete_task` | Mark a task as completed |
| `vibey_start_sprint` | Start a sprint |
| `vibey_complete_sprint` | Complete a sprint |
| `vibey_query_task` | Get task details |
| `vibey_query_sprint` | Get sprint details |
| `vibey_query_track` | Get track details |
| `vibey_list_blockers` | List all blockers |
| `vibey_list_dependencies` | List dependencies |
| `vibey_refresh_progress` | Recalculate metrics |

### Agent Tools

Each agent is exposed as an MCP tool:

- `vibey_coordinator` - Intelligent request router
- `vibey_web_developer` - Frontend/fullstack development
- `vibey_backend_engineer` - API and service development
- `vibey_test_engineer` - Testing and QA
- `vibey_security_reviewer` - Security audits
- `vibey_performance_engineer` - Performance optimization
- `vibey_infrastructure_engineer` - DevOps and IaC
- `vibey_ml_engineer` - Machine learning
- `vibey_database_specialist` - Database design
- `vibey_documentation_engineer` - Documentation
- `vibey_diagram_engineer` - Architecture diagrams
- `vibey_git_committer` - Git operations

### Workflow Tools

Multi-step workflows with the `vibey_workflow_` prefix:

- `vibey_workflow_sprint_planning` - Sprint planning
- `vibey_workflow_single_feature_development` - Feature development
- `vibey_workflow_weekly_sprint` - Weekly sprint execution
- `vibey_workflow_codebase_audit_discovery` - Codebase analysis
- `vibey_workflow_architecture_review` - Architecture review
- `vibey_workflow_logging_audit` - Logging audit
- `vibey_workflow_performance_optimization` - Performance tuning
- `vibey_workflow_frontend_security_hardening` - Security hardening
- `vibey_workflow_infrastructure_setup` - Infrastructure setup
- `vibey_workflow_ml_model_development` - ML model development

## Using with Copilot

VS Code's Copilot Chat can use MCP tools:

1. Open Copilot Chat (Cmd/Ctrl + Shift + I)
2. Reference Vibey tools: "@vibey check roadmap status"
3. Copilot will call the appropriate MCP tool

## Using with Agent Mode

VS Code's Agent Mode provides autonomous multi-step execution:

1. Enable Agent Mode in Copilot settings
2. Ask for complex tasks: "Plan and execute the next sprint"
3. Agent Mode will orchestrate multiple Vibey tool calls

## Requirements

- **VS Code 1.102 or later** (July 2025 release)
- **Python 3.9+**
- **Vibey framework installed**

## Installation

### Automatic (Recommended)

1. Run `vibey deploy --platform vscode`
2. Open project in VS Code
3. VS Code auto-detects `.vscode/mcp.json`
4. MCP server starts automatically

### Manual

1. Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {}
    }
  }
}
```

2. Reload VS Code window

## Usage Examples

### Check Roadmap Status

In Copilot Chat:
```
@vibey What's the current roadmap status?
```

### Start a Task

```
@vibey Start working on task infrastructure-1-task-003
```

### Run a Workflow

```
@vibey Use the sprint planning workflow to plan our next sprint
```

### Security Audit

```
@vibey Run the security hardening workflow on this project
```

## Zero-Drift Architecture

All generated files include SHA-256 checksums for drift detection:

```bash
# Validate no manual edits
vibey validate --platform vscode
```

## Regenerating Configuration

If you add new agents or workflows:

```bash
vibey deploy --platform vscode --clean
```

## Troubleshooting

### MCP Server Not Starting

1. Check VS Code version: Help > About (need 1.102+)
2. Verify Python: `which python`
3. Test server: `python -m framework.mcp.server`
4. Check Output panel: View > Output > MCP

### Tools Not Appearing

1. Reload window: Cmd/Ctrl + Shift + P > "Reload Window"
2. Check `.vscode/mcp.json` syntax
3. Verify server is in output panel

### Server Errors

1. Check Python environment: `which python`
2. Verify Vibey installed: `pip show vibey-framework`
3. Check MCP server logs in Output panel

## Comparison with Other Platforms

| Feature | VS Code | Continue | Windsurf |
|---------|---------|----------|----------|
| MCP Support | Native | Native | Native |
| Config Location | `.vscode/mcp.json` | `~/.continue/config.yaml` | `~/.codeium/windsurf/mcp_config.json` |
| Config Format | `servers` | `mcpServers` | `mcpServers` |
| Extension Required | No | Yes | IDE |
| Full MCP Spec | Yes | Yes | Yes |

## Resources

- [VS Code MCP Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [MCP Announcement Blog](https://code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support)
- [Vibey MCP Reference](../reference/MCP_REFERENCE.md)
