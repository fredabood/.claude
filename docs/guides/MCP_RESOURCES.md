# MCP Resources User Guide

This guide explains how to use Vibey's MCP Resources feature to access framework content through the Model Context Protocol.

## Overview

Vibey exposes its content as MCP Resources, allowing AI assistants and other MCP clients to directly access:

- **Workflows** - Development workflows with steps, quality gates, and inputs
- **Handoffs** - Agent-to-agent communication templates with variables
- **Agents** - Specialized agent definitions (coming soon)

Resources use a URI scheme that provides structured access to content at various levels of detail.

## Resource URI Scheme

All Vibey resources use the `vibey://` URI scheme.

### Workflow Resources

| URI Pattern | Description | MIME Type |
|-------------|-------------|-----------|
| `vibey://workflows/{id}` | Full workflow content | `text/markdown` |
| `vibey://workflows/{id}/steps` | Workflow steps as JSON | `application/json` |
| `vibey://workflows/{id}/quality-gates` | Quality gates as JSON | `application/json` |
| `vibey://workflows/{id}/inputs` | Input definitions as JSON | `application/json` |

### Handoff Resources

| URI Pattern | Description | MIME Type |
|-------------|-------------|-----------|
| `vibey://handoffs/{id}` | Full handoff template | `text/markdown` |
| `vibey://handoffs/{id}/variables` | Variable schema (JSON Schema) | `application/json` |
| `vibey://handoffs/{id}/metadata` | Handoff metadata as JSON | `application/json` |
| `vibey://handoffs/{id}/rendered` | Rendered template with samples | `text/markdown` |

## Usage Examples

### List All Resources

Request all available resources:

```json
{
  "jsonrpc": "2.0",
  "method": "resources/list",
  "id": 1
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "resources": [
      {
        "uri": "vibey://workflows/sprint-planning",
        "name": "Sprint Planning Workflow",
        "description": "Plan and organize sprint work"
      },
      {
        "uri": "vibey://handoffs/code-review",
        "name": "Code Review Handoff",
        "description": "Template for code review handoffs"
      }
    ]
  },
  "id": 1
}
```

### Read a Workflow

Get full workflow content:

```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "vibey://workflows/sprint-planning"
  },
  "id": 2
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "contents": [
      {
        "uri": "vibey://workflows/sprint-planning",
        "mimeType": "text/markdown",
        "text": "---\nid: sprint-planning\nname: Sprint Planning\n..."
      }
    ]
  },
  "id": 2
}
```

### Get Workflow Steps

Access structured step data:

```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "vibey://workflows/sprint-planning/steps"
  },
  "id": 3
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "contents": [
      {
        "uri": "vibey://workflows/sprint-planning/steps",
        "mimeType": "application/json",
        "text": "{\"workflow_id\": \"sprint-planning\", \"steps\": [{\"order\": 1, \"name\": \"Review Backlog\", \"agent\": \"project-manager\"}]}"
      }
    ]
  },
  "id": 3
}
```

### Get Handoff Variable Schema

Access variable definitions as JSON Schema:

```json
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "vibey://handoffs/code-review/variables"
  },
  "id": 4
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "contents": [
      {
        "uri": "vibey://handoffs/code-review/variables",
        "mimeType": "application/json",
        "text": "{\"type\": \"object\", \"properties\": {\"pr_url\": {\"type\": \"string\", \"description\": \"Pull request URL\"}, \"reviewer\": {\"type\": \"string\", \"description\": \"Reviewer name\"}}, \"required\": [\"pr_url\"]}"
      }
    ]
  },
  "id": 4
}
```

### List Resource Templates

Get URI patterns for all resource types:

```json
{
  "jsonrpc": "2.0",
  "method": "resources/templates/list",
  "id": 5
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "resourceTemplates": [
      {
        "uriTemplate": "vibey://workflows/{workflow_id}",
        "name": "Workflow Content",
        "description": "Full workflow markdown content"
      },
      {
        "uriTemplate": "vibey://workflows/{workflow_id}/steps",
        "name": "Workflow Steps",
        "description": "Workflow steps as JSON"
      },
      {
        "uriTemplate": "vibey://handoffs/{handoff_id}",
        "name": "Handoff Template",
        "description": "Full handoff template content"
      },
      {
        "uriTemplate": "vibey://handoffs/{handoff_id}/variables",
        "name": "Handoff Variables",
        "description": "Variable schema as JSON Schema"
      }
    ]
  },
  "id": 5
}
```

## Resource Discovery Workflow

A typical workflow for discovering and using resources:

1. **List templates** to understand available resource types
2. **List resources** to see specific available items
3. **Read resource** to get content for specific items

```python
# Example using an MCP client
async def discover_and_read():
    # Get available templates
    templates = await client.list_resource_templates()

    # Get all workflow resources
    resources = await client.list_resources()
    workflows = [r for r in resources if "workflow" in r["uri"]]

    # Read a specific workflow
    for workflow in workflows:
        content = await client.read_resource(workflow["uri"])
        print(f"Workflow: {workflow['name']}")
        print(content["contents"][0]["text"])
```

## Server Capabilities

The Vibey MCP server announces these resource capabilities:

```json
{
  "resources": {
    "subscribe": true,
    "listChanged": true
  }
}
```

- **subscribe**: Clients can subscribe to resource changes (future)
- **listChanged**: Server will notify when resource list changes

## Error Handling

### Resource Not Found

If a resource doesn't exist:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Resource not found: vibey://workflows/unknown"
  },
  "id": 1
}
```

### Invalid URI

If the URI scheme is invalid:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "No provider found for URI: invalid://resource"
  },
  "id": 1
}
```

## Integration with AI Assistants

### Claude Code Integration

When using with Claude Code, resources can be accessed through MCP tool calls:

```
// List available workflows
MCP: resources/list

// Read sprint planning workflow
MCP: resources/read {"uri": "vibey://workflows/sprint-planning"}

// Get quality gates for a workflow
MCP: resources/read {"uri": "vibey://workflows/sprint-planning/quality-gates"}
```

### Use Cases

**1. Workflow Selection**
AI assistants can list and compare workflows to recommend the best one for a task.

**2. Quality Gate Verification**
Read quality gate definitions to understand and enforce quality requirements.

**3. Handoff Preparation**
Access handoff templates and their variable schemas to prepare structured handoffs.

**4. Dynamic Workflow Execution**
Read workflow steps to understand and execute development processes.

## Extending Resources

The resource system is extensible. New resource providers can be added for:

- Agent definitions
- Quality gate configurations
- Project templates
- Custom content types

See the developer documentation for details on creating custom resource providers.
