# Windsurf Integration Guide

This guide explains how to use Vibey Agent Framework with [Windsurf](https://windsurf.com/), the "first agentic IDE" by Codeium.

## Overview

Vibey provides seamless integration with Windsurf through the `vibey deploy --platform windsurf` command. Windsurf's Cascade agent architecture makes it an excellent fit for Vibey's multi-agent workflows.

## Key Features

Windsurf uses the same MCP configuration format as Claude Desktop, enabling:

- Direct access to all 46 Vibey MCP tools
- Cascade agent integration for multi-step workflows
- Agentic workflow execution
- Free with your own API keys (BYOK)

## Quick Start

```bash
# 1. Install Vibey (if not already installed)
git clone https://github.com/anthropics/vibey.git && cd vibey && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# 2. Initialize Vibey in your project
cd your-project
vibey init

# 3. Deploy to Windsurf
vibey deploy --platform windsurf

# 4. Copy MCP configuration
# macOS/Linux
cp .windsurf/mcp_config.json ~/.codeium/windsurf/mcp_config.json

# Or merge with existing config
```

## What Gets Generated

When you run `vibey deploy --platform windsurf`, the following files are created:

```
.windsurf/
├── mcp_config.json      # MCP server configuration (Claude Desktop format)
├── WINDSURF.md          # Context file with tool reference
├── README.md            # Installation instructions
└── .checksums.json      # Drift detection checksums
```

## Configuration File

The generated `mcp_config.json` uses the Claude Desktop format:

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

## Cascade Agent Integration

Windsurf's Cascade agent is designed for multi-step autonomous operations, making it perfect for Vibey workflows:

### How It Works

1. **Vibey provides the orchestration** - Specialized agents, structured workflows, quality gates
2. **Cascade provides the execution** - Autonomous multi-step code generation
3. **Together** - Production-quality code with structured oversight

### Workflow Mapping

| Vibey Workflow | Cascade Usage |
|----------------|---------------|
| Sprint Planning | Cascade analyzes codebase, creates task breakdown |
| Feature Development | Cascade implements with quality checks |
| Performance Optimization | Cascade profiles and optimizes |
| Security Hardening | Cascade applies security best practices |

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

### Agent Tools

Each Vibey agent is available as an MCP tool:

- `vibey_coordinator` - Request routing
- `vibey_web_developer` - Frontend development
- `vibey_backend_engineer` - API development
- `vibey_test_engineer` - Testing
- `vibey_security_reviewer` - Security audits
- `vibey_performance_engineer` - Optimization
- `vibey_infrastructure_engineer` - DevOps
- `vibey_documentation_engineer` - Documentation

### Workflow Tools

Multi-step workflows with the `vibey_workflow_` prefix:

- `vibey_workflow_sprint_planning` - Plan sprints
- `vibey_workflow_single_feature_development` - Build features
- `vibey_workflow_weekly_sprint` - Execute sprints
- `vibey_workflow_architecture_review` - Review architecture
- `vibey_workflow_security_hardening` - Harden security

## Installation

### Step 1: Generate Configuration

```bash
vibey deploy --platform windsurf
```

### Step 2: Copy to Windsurf

```bash
# macOS
cp .windsurf/mcp_config.json ~/.codeium/windsurf/mcp_config.json

# Linux
cp .windsurf/mcp_config.json ~/.config/codeium/windsurf/mcp_config.json
```

### Step 3: Restart Windsurf

Restart Windsurf to pick up the new MCP configuration.

### Step 4: Verify

In Windsurf, open the Cascade panel and check that Vibey tools are available.

## Usage Examples

### Start a Feature Development Workflow

```
Use vibey_workflow_single_feature_development to implement user authentication.
The workflow will guide you through planning, implementation, testing, and documentation.
```

### Check Roadmap Status

```
Use vibey_roadmap_status to see current progress across all tracks.
```

### Security Audit

```
Use vibey_workflow_frontend_security_hardening to audit and fix security issues.
```

## Cascade + Vibey Best Practices

1. **Use Vibey for planning** - Start with `vibey_workflow_sprint_planning`
2. **Let Cascade execute** - Cascade handles the multi-step implementation
3. **Use Vibey for tracking** - Update task status with `vibey_start_task` and `vibey_complete_task`
4. **Quality gates** - Use Vibey's quality agents before completing tasks

## Zero-Drift Architecture

Generated files include checksums for drift detection:

```bash
vibey validate --platform windsurf
```

## Regenerating Configuration

```bash
vibey deploy --platform windsurf --clean
```

## Troubleshooting

### MCP Server Not Found

1. Verify Python is installed: `which python`
2. Verify Vibey is installed: `pip show vibey-framework`
3. Test server manually: `python -m framework.mcp.server`

### Tools Not Appearing in Cascade

1. Restart Windsurf after adding MCP config
2. Check the MCP config path is correct
3. Verify JSON syntax in `mcp_config.json`

## Resources

- [Windsurf Documentation](https://docs.windsurf.com/)
- [Codeium MCP Support](https://docs.windsurf.com/mcp)
- [Vibey MCP Reference](../reference/MCP_REFERENCE.md)
