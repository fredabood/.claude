# GitHub Copilot Integration Guide

This guide explains how to use Vibey Agent Framework with [GitHub Copilot](https://github.com/features/copilot), GitHub's AI pair programmer available in VS Code, JetBrains IDEs, and other editors.

## Overview

Vibey provides integration with GitHub Copilot through the `vibey deploy --platform copilot` command. This generates repository instructions, custom agent profiles, and context documentation.

## Key Features

GitHub Copilot supports:
- **Repository Instructions** (`.github/copilot-instructions.md`) - Project-specific guidelines
- **Custom Agent Profiles** (`.github/agents/*.md`) - Specialized agent behaviors
- **MCP via Copilot CLI** - Access to MCP tools through the command line

This enables access to all 46 Vibey MCP tools including:
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
vibey init

# 3. Deploy to Copilot
vibey deploy --platform copilot
```

## What Gets Generated

When you run `vibey deploy --platform copilot`, the following files are created:

```
.github/
├── copilot-instructions.md    # Repository-level AI instructions
├── agents/                     # Custom agent profiles
│   ├── coordinator.md
│   ├── web-developer.md
│   ├── backend-engineer.md
│   ├── test-engineer.md
│   └── ... (19 agent profiles)
├── COPILOT.md                  # Context file with tool reference
├── COPILOT_README.md           # Installation instructions
└── .checksums.json             # Drift detection checksums
```

## Configuration Files

### copilot-instructions.md

The repository instructions file provides project-wide guidelines for Copilot:

```markdown
# Vibey Agent Framework Instructions

This repository uses the **Vibey Agent Framework** for intelligent workflow management.

## Framework Overview

Vibey provides:
- **19 specialized agents** for different development tasks
- **16 structured workflows** for multi-step processes
- **46 MCP tools** for roadmap and task management
- **Quality gates** for code review and security

## Available Agents

- **Coordinator**: Intelligent request router
- **Web Developer**: Frontend/fullstack development
- **Backend Engineer**: API and service development
...
```

### Custom Agent Profiles

Each agent gets its own profile in `.github/agents/`:

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
The agent follows structured workflows and quality gates.
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

- GitHub Copilot subscription (Individual or Enterprise)
- VS Code with Copilot extension, or JetBrains IDE with Copilot plugin
- Optional: Copilot CLI for MCP support

### Installation

1. Deploy Vibey to Copilot: `vibey deploy --platform copilot`
2. Commit the `.github/` directory to your repository
3. Open the project in your IDE
4. Copilot will automatically read the repository instructions

### Using Custom Agents

In Copilot Chat, you can reference custom agents using `@agent-name`:

```
@web-developer Help me create a responsive navigation component
```

## MCP via Copilot CLI

For advanced MCP tool access, install the Copilot CLI:

```bash
# Install GitHub CLI if not already installed
brew install gh

# Install Copilot CLI extension
gh extension install github/gh-copilot

# Use MCP tools via CLI
gh copilot suggest "use vibey_roadmap_status to check project progress"
```

## Usage Examples

### Start a Sprint

In Copilot Chat:
```
Using the vibey framework, help me plan the next sprint using the sprint planning workflow.
```

### Check Roadmap Status

```
@coordinator What's the current roadmap status? Use the vibey_roadmap_status tool.
```

### Develop a Feature

```
@backend-engineer Help me implement user authentication using the single feature development workflow.
```

## Repository Instructions Best Practices

The generated `copilot-instructions.md` follows GitHub's best practices:

1. **Clear project context** - Explains what framework is used
2. **Available tools** - Lists MCP tools and their purposes
3. **Workflow guidance** - Explains structured approaches
4. **Quality expectations** - Sets standards for code quality

## Zero-Drift Architecture

All generated files include checksums for drift detection. The Vibey CI integration can validate that generated files haven't been manually edited:

```bash
vibey validate --platform copilot
```

## Regenerating Configuration

If you add new agents or workflows to Vibey, regenerate the Copilot configuration:

```bash
vibey deploy --platform copilot --clean
```

The `--clean` flag removes existing files before regenerating.

## Comparison with Other Platforms

| Feature | Copilot | Cursor | Continue |
|---------|---------|--------|----------|
| MCP Support | CLI | Native | Native |
| Repo Instructions | .github/copilot-instructions.md | .cursorrules | .continuerc |
| Custom Agents | .github/agents/*.md | N/A | N/A |
| IDE Support | VS Code, JetBrains, Vim | Cursor | VS Code, JetBrains |

## Troubleshooting

### Instructions Not Being Applied

1. Verify `.github/copilot-instructions.md` exists
2. Ensure the file is committed to the repository
3. Restart your IDE
4. Check that Copilot has access to the repository

### Custom Agents Not Appearing

1. Verify `.github/agents/` directory exists with agent files
2. Ensure files are committed to the repository
3. Try `@` mention to see available agents
4. Restart Copilot Chat

### MCP Tools Not Available

1. MCP tools require Copilot CLI
2. Install: `gh extension install github/gh-copilot`
3. Test: `gh copilot --help`

## Resources

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Copilot Custom Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
- [Vibey MCP Reference](../reference/MCP_REFERENCE.md)
