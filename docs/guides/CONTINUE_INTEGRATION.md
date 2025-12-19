# Continue.dev Integration Guide

This guide explains how to use Vibey Agent Framework with [Continue.dev](https://continue.dev/), the open-source AI coding assistant that works in VS Code and JetBrains IDEs.

## Overview

Vibey provides seamless integration with Continue.dev through the `vibey deploy --platform continue` command. This generates the necessary configuration files and context documentation.

## Key Features

Continue.dev was the **first AI coding assistant with full MCP support** (December 2024), enabling direct access to all 46 Vibey MCP tools including:

- Roadmap management (tasks, sprints, tracks)
- Agent invocation (19 specialized agents)
- Workflow execution (16 structured workflows)
- Context queries (blockers, dependencies, progress)

## Quick Start

```bash
# 1. Install Vibey (if not already installed)
git clone https://github.com/anthropics/vibey.git && cd vibey && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# 2. Initialize Vibey in your project
cd your-project
vibey roadmap init

# 3. Deploy to Continue
vibey deploy --platform continue

# 4. Copy configuration to Continue
cp .continue/.continuerc.yaml ~/.continue/config.yaml
# Or merge with existing config
```

## What Gets Generated

When you run `vibey deploy --platform continue`, the following files are created:

```
.continue/
├── .continuerc.yaml     # MCP server configuration
├── CONTINUE.md          # Context file with tool reference
├── README.md            # Installation instructions
└── .checksums.json      # Drift detection checksums
```

## Configuration File

The generated `.continuerc.yaml` configures the Vibey MCP server:

```yaml
name: vibey-assistant
version: 1.0.0
schema: v1
mcpServers:
- name: Vibey Framework
  command: python
  args:
    - -m
    - framework.mcp.server
context:
  - provider: code
  - provider: docs
  - provider: diff
  - provider: terminal
rules:
  - Use Vibey MCP tools (prefixed with vibey_) for framework operations
  - Follow structured workflows for multi-step tasks
  - Validate quality gates before marking tasks complete
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

## IDE Setup

### VS Code

1. Install the [Continue extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue)
2. Copy the generated config: `cp .continue/.continuerc.yaml ~/.continue/config.yaml`
3. Reload VS Code
4. Open Continue panel (Cmd/Ctrl + L)

### JetBrains IDEs

1. Install the Continue plugin from JetBrains Marketplace
2. Copy the config: `cp .continue/.continuerc.yaml ~/.continue/config.yaml`
3. Restart your IDE
4. Open Continue panel

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

## Zero-Drift Architecture

All generated files include checksums for drift detection. The Vibey CI integration can validate that generated files haven't been manually edited:

```bash
vibey validate --platform continue
```

## Regenerating Configuration

If you add new agents or workflows to Vibey, regenerate the Continue configuration:

```bash
vibey deploy --platform continue --clean
```

The `--clean` flag removes existing files before regenerating.

## Troubleshooting

### MCP Server Not Connecting

1. Ensure Python is in your PATH
2. Verify Vibey is installed: `pip show vibey-framework`
3. Test the MCP server: `python -m framework.mcp.server`
4. Check Continue logs for connection errors

### Tools Not Appearing

1. Reload the Continue panel
2. Check that the MCP server is configured in `~/.continue/config.yaml`
3. Verify the server is listed in Continue's MCP status

## Resources

- [Continue.dev Documentation](https://docs.continue.dev/)
- [Continue MCP Setup](https://docs.continue.dev/customize/deep-dives/mcp)
- [Vibey MCP Reference](../reference/MCP_REFERENCE.md)
