# Vibey MCP Server Design

**Version:** 1.0
**Date:** 2025-11-10
**Track:** mcp-server
**Status:** Planning Phase

---

## Executive Summary

This document defines the design for Vibey's Model Context Protocol (MCP) server, which will expose Vibey's roadmap management functionality through the standardized MCP interface. This enables integration with Claude Desktop, Goose, and any MCP-compatible AI assistant.

---

## Goals & Requirements

### Primary Goals

1. **Expose Roadmap Operations** - Make all roadmap state management operations available via MCP
2. **Claude Desktop Integration** - Enable seamless Vibey usage from Claude Desktop
3. **Foundation for Goose Port** - Provide MCP foundation that Goose can leverage
4. **Standards Compliance** - Full adherence to MCP 2025-06-18 specification

### Non-Goals

- **Not a replacement for CLI** - MCP server complements, doesn't replace `/vibey` commands
- **Not a web API** - MCP uses JSON-RPC, not REST
- **Not multi-tenant** - Designed for single project/repository context

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client (AI Assistant)                 │
│              (Claude Desktop, Goose, etc.)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ JSON-RPC 2.0
                         │ (stdio / HTTP+SSE)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Vibey MCP Server                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Tools     │  │  Resources   │  │   Prompts    │     │
│  │  (Actions)   │  │   (Data)     │  │ (Templates)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│                  ┌──────────────────┐                        │
│                  │  MCP Adapter     │                        │
│                  │  Layer           │                        │
│                  └────────┬─────────┘                        │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Existing Vibey Roadmap System                   │
│  ┌──────────────────────────────────────────────────┐       │
│  │  framework/roadmap/                              │       │
│  │  ├── models/ (Sprint, Track, Task, Roadmap)      │       │
│  │  ├── serialization/ (YAML loader/saver)          │       │
│  │  └── status.py (StatusManager)                   │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  framework/scripts/                              │       │
│  │  ├── roadmap-update.py                           │       │
│  │  ├── roadmap-query.py                            │       │
│  │  └── roadmap-sync-docs.py                        │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## MCP Primitives Design

### 1. Tools (Model-Controlled Actions)

Tools expose roadmap operations that modify state or perform actions.

#### Task Management Tools

**`vibey_start_task`**
```json
{
  "name": "vibey_start_task",
  "title": "Start Task",
  "description": "Mark a task as in progress",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "string",
        "description": "Task ID (e.g., 'mcp-server-1-task-001')"
      }
    },
    "required": ["task_id"]
  }
}
```

**`vibey_complete_task`**
```json
{
  "name": "vibey_complete_task",
  "title": "Complete Task",
  "description": "Mark a task as completed",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "string",
        "description": "Task ID (e.g., 'mcp-server-1-task-001')"
      },
      "actual_tokens": {
        "type": "integer",
        "description": "Actual tokens used (optional)"
      }
    },
    "required": ["task_id"]
  }
}
```

**`vibey_assign_task`**
```json
{
  "name": "vibey_assign_task",
  "title": "Assign Task",
  "description": "Assign a task to an agent",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "string",
        "description": "Task ID"
      },
      "agent": {
        "type": "string",
        "description": "Agent name (e.g., 'web-developer')"
      }
    },
    "required": ["task_id", "agent"]
  }
}
```

#### Sprint Management Tools

**`vibey_start_sprint`**
```json
{
  "name": "vibey_start_sprint",
  "title": "Start Sprint",
  "description": "Start a sprint",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sprint_id": {
        "type": "string",
        "description": "Sprint ID (e.g., 'mcp-server-1')"
      }
    },
    "required": ["sprint_id"]
  }
}
```

**`vibey_complete_sprint`**
```json
{
  "name": "vibey_complete_sprint",
  "title": "Complete Sprint",
  "description": "Mark a sprint as completed",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sprint_id": {
        "type": "string",
        "description": "Sprint ID"
      }
    },
    "required": ["sprint_id"]
  }
}
```

**`vibey_refresh_progress`**
```json
{
  "name": "vibey_refresh_progress",
  "title": "Refresh Progress",
  "description": "Recalculate all progress metrics and trigger status auto-progression",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

#### Query Tools

**`vibey_query_task`**
```json
{
  "name": "vibey_query_task",
  "title": "Query Task",
  "description": "Get detailed information about a task",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "string",
        "description": "Task ID"
      }
    },
    "required": ["task_id"]
  }
}
```

**`vibey_query_sprint`**
```json
{
  "name": "vibey_query_sprint",
  "title": "Query Sprint",
  "description": "Get detailed information about a sprint",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sprint_id": {
        "type": "string",
        "description": "Sprint ID"
      }
    },
    "required": ["sprint_id"]
  }
}
```

**`vibey_query_track`**
```json
{
  "name": "vibey_query_track",
  "title": "Query Track",
  "description": "Get detailed information about a track",
  "inputSchema": {
    "type": "object",
    "properties": {
      "track_id": {
        "type": "string",
        "description": "Track ID"
      }
    },
    "required": ["track_id"]
  }
}
```

**`vibey_list_blockers`**
```json
{
  "name": "vibey_list_blockers",
  "title": "List Blockers",
  "description": "List all current blockers across the roadmap",
  "inputSchema": {
    "type": "object",
    "properties": {
      "object_id": {
        "type": "string",
        "description": "Optional: filter by specific object ID"
      }
    }
  }
}
```

#### Documentation Tools

**`vibey_sync_docs`**
```json
{
  "name": "vibey_sync_docs",
  "title": "Sync Documentation",
  "description": "Synchronize roadmap documentation from .vibey to docs/",
  "inputSchema": {
    "type": "object",
    "properties": {
      "track_id": {
        "type": "string",
        "description": "Optional: sync specific track only"
      },
      "dry_run": {
        "type": "boolean",
        "description": "Preview changes without applying them",
        "default": false
      }
    }
  }
}
```

**`vibey_generate_docs`**
```json
{
  "name": "vibey_generate_docs",
  "title": "Generate Documentation",
  "description": "Generate markdown and TOC files from YAML",
  "inputSchema": {
    "type": "object",
    "properties": {
      "scope": {
        "type": "string",
        "enum": ["all", "track", "sprint", "task"],
        "description": "Generation scope"
      },
      "object_id": {
        "type": "string",
        "description": "Object ID (required if scope != 'all')"
      }
    },
    "required": ["scope"]
  }
}
```

### 2. Resources (Application-Controlled Data)

Resources expose roadmap data for reading without side effects.

#### Roadmap Resources

**`vibey://roadmap`**
- **Description:** Complete roadmap overview
- **MIME Type:** `application/json`
- **Content:** Full roadmap structure with all tracks, progress, and metadata

**`vibey://roadmap/tracks`**
- **Description:** List of all tracks
- **MIME Type:** `application/json`
- **Content:** Array of track summaries

**`vibey://roadmap/tracks/{track_id}`**
- **Description:** Detailed track information
- **MIME Type:** `application/json`
- **Content:** Complete track object with sprints and progress

**`vibey://roadmap/tracks/{track_id}/sprints/{sprint_id}`**
- **Description:** Detailed sprint information
- **MIME Type:** `application/json`
- **Content:** Complete sprint object with tasks and progress

**`vibey://roadmap/tracks/{track_id}/sprints/{sprint_id}/tasks/{task_id}`**
- **Description:** Detailed task information
- **MIME Type:** `application/json`
- **Content:** Complete task object with dependencies and status

#### Status Resources

**`vibey://roadmap/status`**
- **Description:** Current roadmap status summary
- **MIME Type:** `application/json`
- **Content:** Overall progress, active sprints, blockers, recent activity

**`vibey://roadmap/blockers`**
- **Description:** All current blockers
- **MIME Type:** `application/json`
- **Content:** List of unsatisfied dependencies across all objects

**`vibey://roadmap/activity`**
- **Description:** Recent roadmap activity
- **MIME Type:** `application/json`
- **Content:** Activity log with timestamps and events

#### Documentation Resources

**`vibey://docs/{track_id}`**
- **Description:** Track documentation (markdown)
- **MIME Type:** `text/markdown`
- **Content:** Generated markdown for track

**`vibey://docs/{track_id}/{sprint_id}`**
- **Description:** Sprint documentation (markdown)
- **MIME Type:** `text/markdown`
- **Content:** Generated markdown for sprint

**`vibey://docs/toc/{object_id}`**
- **Description:** Table of contents JSON
- **MIME Type:** `application/json`
- **Content:** Navigation TOC for specified object

### 3. Prompts (User-Controlled Templates)

Prompts provide structured templates for common roadmap operations.

**`start_new_sprint`**
```json
{
  "name": "start_new_sprint",
  "title": "Start New Sprint",
  "description": "Template for starting a sprint with task breakdown",
  "arguments": [
    {
      "name": "sprint_id",
      "description": "Sprint to start",
      "required": true
    }
  ]
}
```

**`complete_task_checklist`**
```json
{
  "name": "complete_task_checklist",
  "title": "Complete Task Checklist",
  "description": "Guided checklist for marking a task complete",
  "arguments": [
    {
      "name": "task_id",
      "description": "Task to complete",
      "required": true
    }
  ]
}
```

**`roadmap_status_report`**
```json
{
  "name": "roadmap_status_report",
  "title": "Roadmap Status Report",
  "description": "Generate a comprehensive roadmap status report",
  "arguments": [
    {
      "name": "detail_level",
      "description": "Report detail level (summary/detailed/comprehensive)",
      "required": false
    }
  ]
}
```

**`debug_blocker`**
```json
{
  "name": "debug_blocker",
  "title": "Debug Blocker",
  "description": "Analyze and troubleshoot a blocked object",
  "arguments": [
    {
      "name": "object_id",
      "description": "ID of blocked object",
      "required": true
    }
  ]
}
```

---

## Implementation Strategy

### Phase 1: Core MCP Server (Sprint 1)

**Deliverables:**
- Basic MCP server scaffold using Python SDK
- JSON-RPC 2.0 transport (stdio)
- Capability negotiation
- Server initialization and lifecycle
- Basic tool registration (3-4 tools)

**Python Stack:**
- `mcp` - Official Python SDK
- `pydantic` - Schema validation
- Standard library for JSON-RPC

**File Structure:**
```
framework/mcp/
├── __init__.py
├── server.py              # Main MCP server
├── adapters/
│   ├── __init__.py
│   ├── roadmap_adapter.py # Adapter to existing roadmap system
│   └── tools_adapter.py   # Tool execution adapter
├── tools/
│   ├── __init__.py
│   ├── task_tools.py      # Task management tools
│   ├── sprint_tools.py    # Sprint management tools
│   └── query_tools.py     # Query tools
├── resources/
│   ├── __init__.py
│   └── roadmap_resources.py
└── prompts/
    ├── __init__.py
    └── roadmap_prompts.py
```

### Phase 2: Roadmap Tools (Sprint 2)

**Deliverables:**
- Complete task management tools (start, complete, assign)
- Complete sprint management tools (start, complete, refresh)
- Query tools (task, sprint, track, blockers)
- Error handling and validation
- Integration tests

### Phase 3: Resources & Subscriptions (Sprint 3)

**Deliverables:**
- All roadmap resources (roadmap, tracks, sprints, tasks)
- Status resources (status, blockers, activity)
- Documentation resources (markdown, TOCs)
- Resource subscriptions (notify on changes)
- Performance optimization

### Phase 4: Testing & Documentation (Sprint 4)

**Deliverables:**
- Comprehensive test suite
- Claude Desktop integration guide
- MCP server configuration examples
- Performance benchmarks
- Production readiness checklist

---

## Integration Points

### With Existing Roadmap System

The MCP server will use the existing Python modules:

1. **Models** (`framework/roadmap/models/`)
   - Import Sprint, Track, Task, Roadmap classes
   - Use existing validation and business logic

2. **Serialization** (`framework/roadmap/serialization/`)
   - Use `yaml_loader.py` for reading state
   - Use `yaml_saver.py` for writing state

3. **Status Management** (`framework/scripts/roadmap-lib/status.py`)
   - Use StatusManager for auto-progression
   - Leverage existing can_progress checks

4. **Scripts** (`framework/scripts/`)
   - Wrap existing roadmap-update.py functionality
   - Wrap existing roadmap-query.py functionality
   - Wrap existing roadmap-sync-docs.py functionality

**Adapter Pattern:**
```python
class RoadmapAdapter:
    """Adapter layer between MCP server and Vibey roadmap system."""

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        self.root = Path(roadmap_root)
        self.fs = FileSystemManager(self.root)

    def start_task(self, task_id: str) -> dict:
        """Start a task (wraps roadmap-update.py logic)."""
        # Load task
        task = load_task(self.fs.get_task_path(task_id))

        # Update status
        task.status = Status.IN_PROGRESS
        task.started = datetime.now(timezone.utc)

        # Save
        save_task(task, self.fs.get_task_path(task_id))

        # Update sprint progress
        update_sprint_progress(self.fs, task.sprint_id)

        return {"success": True, "task_id": task_id}
```

### With Claude Desktop

Users will configure the MCP server in Claude Desktop's configuration:

**`claude_desktop_config.json`:**
```json
{
  "mcpServers": {
    "vibey": {
      "command": "python",
      "args": ["/path/to/vibey/framework/mcp/server.py"],
      "cwd": "/path/to/project"
    }
  }
}
```

### With Goose

Goose has native MCP support. The Vibey MCP server becomes a Goose extension:

**`goose.yaml`:**
```yaml
extensions:
  vibey:
    type: mcp
    server:
      command: python
      args:
        - /path/to/vibey/framework/mcp/server.py
      cwd: /path/to/project
```

---

## Security Considerations

### Human-in-the-Loop

Per MCP spec: "For trust & safety and security, there SHOULD always be a human in the loop with the ability to deny tool invocations."

**Implementation:**
- All state-modifying tools (start_task, complete_task, etc.) require confirmation
- Query tools (read-only) do not require confirmation
- MCP clients (Claude Desktop, Goose) handle confirmation UI

### Validation

- **Input validation:** All tool inputs validated against JSON schemas
- **State validation:** Leverage existing Sprint/Track/Task `__post_init__` validation
- **Authorization:** MCP server operates in single-project context (no multi-tenant concerns)

### Error Handling

- **Structured errors:** Return `isError: true` with descriptive messages
- **Rollback:** State changes are atomic (YAML file operations)
- **Logging:** Comprehensive logging for debugging

---

## Testing Strategy

### Unit Tests

- Test each tool handler independently
- Mock file system operations
- Validate input/output schemas
- Test error conditions

### Integration Tests

- Test MCP server lifecycle (init, capabilities, shutdown)
- Test tool invocation flow (request → handler → response)
- Test resource retrieval flow
- Test subscriptions and notifications

### End-to-End Tests

- Test with MCP Inspector (official debugging tool)
- Test with Claude Desktop integration
- Test with sample roadmap data
- Performance benchmarks

---

## Performance Considerations

### Caching

- Cache loaded YAML files (invalidate on write)
- Cache generated TOC/markdown (regenerate on state change)
- Cache resource lists (update on changes)

### Optimization

- Lazy-load resources (don't load all tracks upfront)
- Use subscriptions for change notifications (avoid polling)
- Batch operations where possible

### Scalability

- Designed for single project (not multi-tenant)
- Expected scale: 10-50 tracks, 100-500 sprints, 500-2000 tasks
- Response time target: <100ms for queries, <500ms for mutations

---

## Documentation Requirements

### User Documentation

1. **Installation Guide** - How to install and configure MCP server
2. **Claude Desktop Integration** - Step-by-step setup for Claude Desktop
3. **Tool Reference** - Complete reference of all tools with examples
4. **Resource Reference** - Complete reference of all resources
5. **Troubleshooting Guide** - Common issues and solutions

### Developer Documentation

1. **Architecture Overview** - System design and components
2. **Adapter Pattern** - How to extend the adapter layer
3. **Adding New Tools** - Guide for adding tools
4. **Testing Guide** - How to run and write tests
5. **Contributing Guide** - How to contribute to MCP server

---

## Success Criteria

### Sprint 1 (MCP Protocol Integration)

- ✅ MCP server scaffold running
- ✅ Capability negotiation working
- ✅ 3-4 basic tools functional
- ✅ stdio transport working
- ✅ Unit tests passing

### Sprint 2 (Roadmap Tools Implementation)

- ✅ All task management tools complete
- ✅ All sprint management tools complete
- ✅ All query tools complete
- ✅ Integration tests passing
- ✅ Error handling comprehensive

### Sprint 3 (Resources & Subscriptions)

- ✅ All roadmap resources accessible
- ✅ All status resources accessible
- ✅ Documentation resources accessible
- ✅ Subscriptions working
- ✅ Performance benchmarks met

### Sprint 4 (Testing & Documentation)

- ✅ Test coverage >80%
- ✅ Claude Desktop integration tested
- ✅ All documentation complete
- ✅ Production readiness checklist passed
- ✅ Zero critical bugs

---

## Open Questions

1. **HTTP Transport:** Should we support HTTP+SSE in addition to stdio? (Answer: Phase 2, not MVP)
2. **Authentication:** Do we need OAuth 2.1? (Answer: No, single-project context)
3. **Multi-Project:** Should one MCP server handle multiple projects? (Answer: No, single project per server)
4. **Prompt Templates:** How complex should prompt templates be? (Answer: Start simple, iterate)

---

## Next Steps

1. **Review this design** - Get feedback from stakeholders
2. **Create Sprint 1 task breakdown** - Detailed task list for first sprint
3. **Set up development environment** - Install MCP Python SDK, set up testing
4. **Start implementation** - Begin with server scaffold and basic tools

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Next Review:** Before Sprint 1 begins
**Status:** Ready for Implementation
