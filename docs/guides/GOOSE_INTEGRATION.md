# Goose Integration Guide

> **Version:** 1.0.0
> **Last Updated:** 2025-11-22

This guide explains how to integrate Vibey with [Goose](https://block.github.io/goose/), Block's open-source AI coding assistant.

## Overview

Vibey provides **46 MCP tools** to Goose:
- **19 agent tools** - Specialized AI assistants (test-engineer, web-developer, etc.)
- **16 workflow tools** - Multi-step processes (feature-development, sprint-planning, etc.)
- **11 roadmap tools** - Project management (status, tasks, sprints)

## Prerequisites

- **Goose** installed ([installation guide](https://block.github.io/goose/docs/getting-started))
- **Python 3.11+** with virtual environment
- **Vibey repository** cloned locally

## Quick Start

### 1. Clone Vibey

```bash
git clone https://github.com/yourusername/vibey.git
cd vibey
```

### 2. Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Verify MCP Server

```bash
# Test the server starts correctly
python scripts/run-mcp-server.py
# Should output: "Vibey MCP Server running..."
# Press Ctrl+C to stop
```

### 4. Configure Goose

Edit `~/.config/goose/config.yaml`:

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
    description: Vibey Agent Framework - 46 tools for development
```

**Important:** Use absolute paths, not relative paths.

### 5. Restart Goose

```bash
# If Goose is running, restart it
goose session --new
```

### 6. Verify Integration

In a Goose session:

```
> What tools are available from vibey?
```

Goose should list 46 tools starting with `vibey_`.

## Configuration Options

### Basic Configuration

```yaml
extensions:
  vibey:
    name: vibey
    type: stdio
    cmd: /path/to/.venv/bin/python
    args:
      - /path/to/scripts/run-mcp-server.py
    enabled: true
    timeout: 300
```

### With Environment Variables

```yaml
extensions:
  vibey:
    name: vibey
    type: stdio
    cmd: /path/to/.venv/bin/python
    args:
      - /path/to/scripts/run-mcp-server.py
    enabled: true
    timeout: 300
    envs:
      VIBEY_ROADMAP_ROOT: /path/to/project/.vibey/roadmap
      VIBEY_LOG_LEVEL: INFO
```

### Multiple Projects

You can configure Vibey for different projects:

```yaml
extensions:
  vibey-project-a:
    name: vibey-project-a
    type: stdio
    cmd: /path/to/.venv/bin/python
    args:
      - /path/to/scripts/run-mcp-server.py
      - --roadmap-root
      - /path/to/project-a/.vibey/roadmap
    enabled: true

  vibey-project-b:
    name: vibey-project-b
    type: stdio
    cmd: /path/to/.venv/bin/python
    args:
      - /path/to/scripts/run-mcp-server.py
      - --roadmap-root
      - /path/to/project-b/.vibey/roadmap
    enabled: false  # Disable when not needed
```

## Using Vibey Tools

### Agent Tools

Invoke specialized agents:

```
> Use vibey_test_engineer to write tests for my login function

> Ask vibey_security_reviewer to check my authentication code

> Have vibey_documentation_engineer update the README
```

### Workflow Tools

Run multi-step workflows:

```
> Start vibey_workflow_feature_development for a user dashboard

> Run vibey_workflow_sprint_planning for next week
```

### Roadmap Tools

Manage your project:

```
> Show vibey_roadmap_status

> Use vibey_start_task to begin task-001

> Complete task-001 with vibey_complete_task
```

## Tool Reference

### Core Roadmap Tools

| Tool | Description |
|------|-------------|
| `vibey_roadmap_status` | Get overall roadmap progress |
| `vibey_query_track` | Query a specific track |
| `vibey_query_sprint` | Query a specific sprint |
| `vibey_query_task` | Query a specific task |
| `vibey_start_task` | Start a task |
| `vibey_complete_task` | Complete a task |
| `vibey_start_sprint` | Start a sprint |
| `vibey_complete_sprint` | Complete a sprint |
| `vibey_list_blockers` | List blockers |
| `vibey_list_dependencies` | List dependencies |
| `vibey_refresh_progress` | Recalculate progress |

### Agent Tools (19)

| Tool | Type | Description |
|------|------|-------------|
| `vibey_test_engineer` | quality | Write automated tests |
| `vibey_security_reviewer` | quality | Security audits |
| `vibey_performance_engineer` | quality | Performance optimization |
| `vibey_web_developer` | development | Frontend development |
| `vibey_backend_engineer` | development | API development |
| `vibey_database_specialist` | development | Database design |
| `vibey_infrastructure_engineer` | development | DevOps/IaC |
| `vibey_ml_engineer` | development | Machine learning |
| `vibey_sprint_planning` | planning | Sprint planning |
| `vibey_researcher` | planning | Research tasks |
| `vibey_architecture_agent` | architecture | System design |
| `vibey_documentation_engineer` | documentation | Write docs |
| `vibey_diagram_engineer` | documentation | Create diagrams |
| `vibey_git_committer` | documentation | Git commits |
| `vibey_coordinator` | core | Orchestration |
| ... | ... | ... |

### Workflow Tools (16)

| Tool | Type | Description |
|------|------|-------------|
| `vibey_workflow_feature_development` | development | Full feature lifecycle |
| `vibey_workflow_sprint_planning` | planning | Plan a sprint |
| `vibey_workflow_security_audit` | quality | Security review |
| `vibey_workflow_performance_optimization` | quality | Performance tuning |
| `vibey_workflow_frontend_production_deployment` | deployment | Deploy frontend |
| ... | ... | ... |

## Example Sessions

### Feature Development

```
You: I need to add a user profile page to my React app

Goose: I'll help you develop this feature. Let me start with the
       feature development workflow.

       [Calls vibey_workflow_feature_development]

       Based on the workflow, here's the plan:
       1. Requirements Analysis - Let me clarify the requirements
       2. Technical Design - I'll create a component structure
       3. Implementation - Build the profile components
       4. Testing - Write unit and integration tests
       5. Documentation - Update the docs

       Let's start with step 1...
```

### Code Review

```
You: Review my authentication code for security issues

Goose: I'll use the security reviewer agent to analyze your code.

       [Calls vibey_security_reviewer]

       Security Review Results:
       - Found 2 high-severity issues
       - Found 3 medium-severity issues

       High Severity:
       1. Password stored in plain text (line 45)
       2. SQL injection vulnerability (line 78)
       ...
```

### Project Status

```
You: What's the status of our roadmap?

Goose: [Calls vibey_roadmap_status]

       📊 Roadmap: My Project

       **Progress:** 75% complete
       **Active Tracks:** 3
       **Blocked Tasks:** 1

       Active Work:
       - Sprint 5: Feature Development (80% complete)
       - Task: Implement user dashboard (in progress)
```

## Troubleshooting

### Tools Not Appearing

1. **Check configuration path:**
   ```bash
   cat ~/.config/goose/config.yaml
   ```

2. **Verify Python path:**
   ```bash
   which python  # Should match config
   /path/to/.venv/bin/python --version
   ```

3. **Test server manually:**
   ```bash
   /path/to/.venv/bin/python /path/to/scripts/run-mcp-server.py
   ```

4. **Check Goose logs:**
   ```bash
   goose session --debug
   ```

### Server Errors

**"Module not found" errors:**
```bash
cd /path/to/vibey
.venv/bin/pip install -r requirements.txt
```

**"Permission denied":**
```bash
chmod +x scripts/run-mcp-server.py
```

### Slow Responses

- First call may be slow (tool discovery)
- Subsequent calls use cache
- Typical latency: 20-50ms per call

### Wrong Project Data

Ensure `--roadmap-root` points to correct project:
```yaml
args:
  - /path/to/scripts/run-mcp-server.py
  - --roadmap-root
  - /path/to/your-project/.vibey/roadmap
```

## Advanced Configuration

### Custom Tool Prefix

By default, tools use `vibey_` prefix. To customize:

```python
# In scripts/run-mcp-server.py
server = VibeyMCPServer(
    roadmap_root=".vibey/roadmap",
    tool_prefix="myproject"  # Tools become myproject_*
)
```

### Filtering Tools

To expose only certain tools, modify the server configuration.

### Logging

Enable debug logging:
```yaml
envs:
  VIBEY_LOG_LEVEL: DEBUG
```

Logs appear in Goose output.

## Best Practices

1. **Use absolute paths** in Goose config
2. **Keep Vibey updated** for latest tools
3. **Initialize roadmap** for project management features
4. **Use workflows** for complex tasks
5. **Leverage agents** for specialized work

## Related Documentation

- [Frontmatter Schema Reference](../reference/FRONTMATTER_SCHEMA.md)
- [Recipe Development Guide](./RECIPE_DEVELOPMENT.md)
- [Migration Guide](./MIGRATION_CLAUDE_TO_GOOSE.md)
- [Cross-LLM Testing](../../.vibey/roadmap/goose-port/goose-port-4/context/CROSS_LLM_TESTING.md)

## Support

- **Issues:** GitHub Issues
- **Documentation:** docs/ directory
- **Examples:** examples/ directory
