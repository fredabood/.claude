# Extending Vibey

> **Time Required:** 30 minutes
> **Difficulty:** Advanced
> **Prerequisites:** Python experience, Vibey installed, understanding of core concepts

---

## Overview

This walkthrough covers extending Vibey functionality: creating platform adapters, custom MCP tools, managing content, and working with artifacts.

---

## Platform Adapters

Vibey deploys to AI assistant platforms via adapters. Each adapter transforms Vibey's unified configuration into platform-specific formats.

### Adapter Architecture

```
vibey/adapters/
├── base.py           # Base adapter class
├── claudecode.py     # Claude Code adapter
├── cursor.py         # Cursor adapter
├── copilot.py        # GitHub Copilot adapter
├── vscode.py         # VS Code adapter
├── goose.py          # Goose adapter
├── gemini.py         # Gemini adapter
├── aider.py          # Aider adapter
├── continue.py       # Continue adapter
└── windsurf.py       # Windsurf adapter
```

### Creating a New Adapter

1. Create adapter file in `vibey/adapters/`:

```python
# vibey/adapters/myplatform.py
from vibey.adapters.base import BaseAdapter

class MyPlatformAdapter(BaseAdapter):
    """Adapter for MyPlatform AI assistant."""

    name = "myplatform"
    display_name = "My Platform"
    config_path = ".myplatform/config.json"

    def generate_config(self, context):
        """Generate platform-specific configuration."""
        return {
            "context": context.to_dict(),
            "settings": self.get_settings()
        }

    def deploy(self, config):
        """Deploy configuration to platform."""
        # Write config to config_path
        pass
```

2. Register adapter in `vibey/adapters/__init__.py`

3. Test deployment:

```bash
vibey deploy list  # Should show new platform
vibey deploy run --platform myplatform
```

---

## Content Management

The content system stores reusable text, templates, and documentation.

### List Content

```bash
vibey content list
```

Shows all content items with types and descriptions.

### Create Content

```bash
vibey content create \
  --type template \
  --name "sprint-planning" \
  --description "Template for sprint planning documents"
```

### View Content

```bash
vibey content show <content-id>
```

### Edit Content

```bash
vibey content edit <content-id>
```

Opens content in your configured editor.

### Search Content

```bash
vibey content search "sprint template"
```

Searches content by keyword.

### Validate Content

```bash
vibey content validate
```

Validates all content for proper formatting and references.

### Delete Content

```bash
vibey content delete <content-id>
```

---

## Artifact Management

Artifacts track files associated with roadmap items.

### List Artifacts

```bash
vibey artifact list
```

Shows all tracked artifacts.

### Show Artifact Details

```bash
vibey artifact show <artifact-id>
```

### Adopt Artifact

Link an existing file to a roadmap item:

```bash
vibey artifact adopt \
  --file "docs/design.md" \
  --task <task-id>
```

### Find Orphan Artifacts

Find artifacts not linked to any roadmap item:

```bash
vibey artifact orphans
```

### Find Stale Artifacts

Find artifacts whose source files have changed:

```bash
vibey artifact stale
```

### Refresh Artifact

Update artifact metadata from source file:

```bash
vibey artifact refresh <artifact-id>
```

### Check Artifact Impact

See which roadmap items are affected by an artifact:

```bash
vibey artifact impact <artifact-id>
```

### Delete Artifact

```bash
vibey artifact delete <artifact-id>
```

---

## MCP Tool Development

Vibey's MCP server exposes tools for AI assistants.

### MCP Architecture

```
vibey/mcp/
├── server.py         # MCP server entry point
├── tools/            # Tool implementations
│   ├── task.py       # Task operations
│   ├── sprint.py     # Sprint operations
│   ├── track.py      # Track operations
│   ├── query.py      # Query tools
│   └── workflow.py   # Workflow handoffs
├── resources/        # Resource implementations
└── prompts/          # Prompt implementations
```

### Available Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| Task | `task_start`, `task_complete`, `task_query` | Task lifecycle |
| Sprint | `sprint_query`, `vibey_refresh_progress` | Sprint management |
| Query | `roadmap_status`, `vibey_list_blockers` | Roadmap queries |
| Content | `vibey_content_*` | Content CRUD |
| Workflow | `vibey_handoff_*` | Task transitions |
| Agent | `vibey_*_agent` | Specialized agents |

### MCP Content Tools

| Tool | Purpose |
|------|---------|
| `vibey_content_create` | Create new content |
| `vibey_content_list` | List all content |
| `vibey_content_show` | View content details |
| `vibey_content_search` | Search content |
| `vibey_content_update` | Update content |
| `vibey_content_delete` | Delete content |
| `vibey_content_validate` | Validate content |

### MCP Agent Tools

Specialized agent tools for AI coordination:

| Tool | Purpose |
|------|---------|
| `vibey_architecture_agent` | Architecture decisions |
| `vibey_backend_engineer` | Backend development |
| `vibey_frontend_engineer` | Frontend development |
| `vibey_database_specialist` | Database operations |
| `vibey_documentation_engineer` | Documentation |
| `vibey_qa_engineer` | Quality assurance |
| `vibey_security_engineer` | Security review |
| `vibey_ml_engineer` | ML/AI development |
| `vibey_infrastructure_engineer` | Infrastructure |
| `vibey_platform_engineer` | Platform operations |
| `vibey_product_manager` | Product decisions |
| `vibey_roadmap_manager` | Roadmap operations |
| `vibey_standards_agent` | Standards enforcement |
| `vibey_swarm_coordinator` | Multi-agent coordination |
| `vibey_technical_writer` | Technical writing |
| `vibey_git_committer` | Git operations |
| `vibey_diagram_engineer` | Diagram creation |
| `vibey_coordinator` | General coordination |
| `vibey_documentation_maintenance_engineer` | Doc maintenance |

### Creating Custom MCP Tools

1. Create tool module in `vibey/mcp/tools/`:

```python
# vibey/mcp/tools/custom.py
from mcp.types import Tool

def register_custom_tools(server):
    """Register custom tools with MCP server."""

    @server.tool()
    async def my_custom_tool(param: str) -> str:
        """My custom tool description."""
        # Implementation
        return f"Result: {param}"
```

2. Register in `vibey/mcp/server.py`

3. Test via MCP client:

```json
{
  "tool": "my_custom_tool",
  "arguments": {"param": "test"}
}
```

---

## Command Reference

### Content Commands
```bash
vibey content create --type <type> --name <name>
vibey content list
vibey content show <id>
vibey content edit <id>
vibey content search <query>
vibey content validate
vibey content delete <id>
```

### Artifact Commands
```bash
vibey artifact list
vibey artifact show <id>
vibey artifact adopt --file <path> --task <id>
vibey artifact orphans
vibey artifact stale
vibey artifact refresh <id>
vibey artifact impact <id>
vibey artifact delete <id>
```

---

## See Also

- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - System design
- [MCP Reference](../reference/MCP_REFERENCE.md) - All MCP tools
- [CLI Reference](../reference/CLI_REFERENCE.md) - All CLI commands
- [Deployment](./DEPLOYMENT.md) - Platform deployment
