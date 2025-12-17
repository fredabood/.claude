# Cursor Integration Guide

This guide explains how to use Vibey Agent Framework with [Cursor](https://cursor.com/), the AI-first code editor built on VS Code.

## Overview

Vibey provides seamless integration with Cursor through the `vibey deploy --platform cursor` command. This generates the necessary configuration files and context documentation.

## Key Features

Cursor has **native MCP support** (since November 2024), using the same configuration format as Claude Desktop. This enables direct access to all 46 Vibey MCP tools including:

- Roadmap management (tasks, sprints, tracks)
- Agent invocation (19 specialized agents)
- Workflow execution (16 structured workflows)
- Context queries (blockers, dependencies, progress)

Cursor also supports `.cursorrules` for project-specific AI behavior customization.

## Quick Start

```bash
# 1. Install Vibey (if not already installed)
git clone https://github.com/anthropics/vibey.git
cd vibey
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Initialize Vibey in your project
cd your-project
vibey init

# 3. Deploy to Cursor
vibey deploy --platform cursor
```

## What Gets Generated

When you run `vibey deploy --platform cursor`, the following files are created:

```
.cursor/
├── mcp.json             # MCP server configuration
├── CURSOR.md            # Context file with tool reference
├── README.md            # Installation instructions
└── .checksums.json      # Drift detection checksums

.cursorrules             # Project AI rules (in project root)
```

## Configuration File

The generated `mcp.json` uses the Claude Desktop format:

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

## .cursorrules File

The generated `.cursorrules` file provides project-specific AI guidelines:

```markdown
# Vibey Agent Framework Rules

This project uses the Vibey Agent Framework for intelligent workflow management.

## MCP Tools

Use Vibey MCP tools (prefixed with `vibey_`) for framework operations:
- `vibey_roadmap_status` - Check roadmap progress
- `vibey_start_task` / `vibey_complete_task` - Manage tasks
- `vibey_start_sprint` / `vibey_complete_sprint` - Manage sprints

## Available Agents

- `vibey_coordinator` - Intelligent request router
- `vibey_web_developer` - Web Developer
- `vibey_backend_engineer` - Backend Engineer
...
```

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

Each agent is available as an MCP tool with the `vibey_` prefix:

| Tool | Description |
|------|-------------|
| `vibey_coordinator` | Intelligent request router |
| `vibey_web_developer` | Frontend/fullstack development |
| `vibey_backend_engineer` | API and service development |
| `vibey_test_engineer` | Testing and QA |
| `vibey_security_reviewer` | Security audits |
| `vibey_performance_engineer` | Performance optimization |
| `vibey_infrastructure_engineer` | DevOps and IaC |
| `vibey_ml_engineer` | Machine learning |
| `vibey_database_specialist` | Database design |
| `vibey_documentation_engineer` | Documentation |
| `vibey_diagram_engineer` | Architecture diagrams |
| `vibey_git_committer` | Git operations |

### Workflow Tools

Each workflow is available with the `vibey_workflow_` prefix:

| Tool | Description |
|------|-------------|
| `vibey_workflow_sprint_planning` | Sprint planning workflow |
| `vibey_workflow_single_feature_development` | Feature development |
| `vibey_workflow_weekly_sprint` | Weekly sprint execution |
| `vibey_workflow_codebase_audit_discovery` | Codebase analysis |
| `vibey_workflow_architecture_review` | Architecture review |
| `vibey_workflow_logging_audit` | Logging audit |
| `vibey_workflow_performance_optimization` | Performance tuning |
| `vibey_workflow_security_hardening` | Security hardening |

## Setup

### Prerequisites

- Cursor IDE (with MCP support, November 2024+)
- Python 3.9+
- Vibey framework installed

### Installation

1. Deploy Vibey to Cursor: `vibey deploy --platform cursor`
2. Open the project in Cursor
3. The MCP server will start automatically
4. Access tools via Composer (Cmd/Ctrl + K)

### Verify MCP Connection

1. Open Cursor Settings
2. Navigate to MCP section
3. Verify "vibey" server is listed and connected

## Usage Examples

### Start a Sprint

```
Use the vibey_workflow_sprint_planning tool to plan the next sprint.
```

### Check Roadmap Status

```
Use vibey_roadmap_status to show the current state of all tracks.
```

### Develop a Feature

```
Use vibey_workflow_single_feature_development to implement the user authentication feature.
```

### Using .cursorrules

Cursor automatically reads `.cursorrules` and applies the guidelines to all AI interactions. This ensures the AI assistant:

- Uses Vibey MCP tools appropriately
- Follows structured workflows
- Validates quality gates
- References roadmap status

## Zero-Drift Architecture

All generated files include checksums for drift detection. The Vibey CI integration can validate that generated files haven't been manually edited:

```bash
vibey validate --platform cursor
```

## Regenerating Configuration

If you add new agents or workflows to Vibey, regenerate the Cursor configuration:

```bash
vibey deploy --platform cursor --clean
```

The `--clean` flag removes existing files before regenerating.

## Comparison with Other Platforms

| Feature | Cursor | Continue | VS Code |
|---------|--------|----------|---------|
| MCP Support | Native | Native | Native |
| Config Format | mcpServers | mcpServers | servers |
| Project Rules | .cursorrules | .continuerc | tasks.json |
| IDE Base | VS Code | Extension | VS Code |

## Troubleshooting

### MCP Server Not Connecting

1. Ensure Python is in your PATH
2. Verify Vibey is installed: `pip show vibey-framework`
3. Test the MCP server: `python -m framework.mcp.server`
4. Check Cursor MCP settings for connection status

### Tools Not Appearing

1. Restart Cursor
2. Check that `.cursor/mcp.json` exists
3. Verify the MCP server configuration is correct
4. Check Cursor logs for errors

### .cursorrules Not Being Applied

1. Verify `.cursorrules` is in the project root
2. Ensure the file is not empty
3. Restart Cursor to reload rules

## Resources

- [Cursor Documentation](https://docs.cursor.com/)
- [Cursor MCP Setup](https://docs.cursor.com/context/model-context-protocol)
- [Vibey MCP Reference](../reference/MCP_REFERENCE.md)
