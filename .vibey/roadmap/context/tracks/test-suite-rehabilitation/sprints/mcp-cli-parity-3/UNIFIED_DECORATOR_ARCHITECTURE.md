# Unified Decorator Architecture

## Overview

This document describes the unified decorator architecture implemented for CLI/MCP parity enforcement. The architecture provides a single source of truth for command definitions that automatically propagate to both CLI and MCP interfaces.

## Problem Statement

Before this implementation, Vibey had:
- **169 CLI commands** defined in Click
- **76 MCP tools** defined separately
- No automated way to ensure parity between interfaces
- Potential for drift as features were added to one interface but not the other

## Solution: Unified Command Decorator

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Unified Command Layer                      │
│                   vibey/unified/commands/                     │
│     @unified_command(interfaces=["cli", "mcp"])              │
└──────────────────────────────────────────────────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│     Click Adapter        │    │       MCP Adapter           │
│ vibey/unified/adapters/  │    │  vibey/unified/adapters/    │
│    click_adapter.py      │    │     mcp_adapter.py          │
└─────────────────────────┘    └─────────────────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│    CLI (Click Groups)   │    │    MCP (FastMCP Tools)      │
│   vibey/cli/main.py     │    │    vibey/mcp/server.py      │
└─────────────────────────┘    └─────────────────────────────┘
            │                                │
            └───────────────┬────────────────┘
                            ▼
              ┌─────────────────────────────┐
              │      Operations Layer        │
              │   vibey/operations/roadmap/  │
              └─────────────────────────────┘
```

## Core Components

### 1. Command Decorator (`vibey/unified/command.py`)

```python
@unified_command(
    name="start_task",
    description="Mark a task as in progress",
    interfaces=["cli", "mcp"],  # Default: both
    cli_group="roadmap",
    cli_name="start",
    mcp_name="vibey_start_task",
)
def start_task(task_id: str, force: bool = False):
    ...
```

Key features:
- `interfaces` parameter defaults to both ["cli", "mcp"]
- Can exclude from either interface: `interfaces=["cli"]` or `interfaces=["mcp"]`
- `exclusion_reason` documents why a command is single-interface

### 2. Parameter Decorator (`vibey/unified/param.py`)

```python
@param("task_id", type=ParamType.STRING, required=True, help="Task ID")
@param("force", type=ParamType.BOOLEAN, default=False, cli_short="-f", cli_is_flag=True)
```

Supports:
- Type mapping between Click and JSON Schema
- CLI-specific options (short flags, flag mode)
- Default values and help text

### 3. Type System (`vibey/unified/types.py`)

| Unified Type | Click Type | JSON Schema |
|-------------|------------|-------------|
| `STRING` | `click.STRING` | `{"type": "string"}` |
| `INTEGER` | `click.INT` | `{"type": "integer"}` |
| `BOOLEAN` | `click.BOOL` | `{"type": "boolean"}` |
| `PATH` | `click.Path()` | `{"type": "string"}` |
| `CHOICE` | `click.Choice([...])` | `{"enum": [...]}` |

### 4. Command Registry (`vibey/unified/registry.py`)

Singleton pattern storing all registered commands:
- `COMMAND_REGISTRY.register(spec)` - Register a command
- `COMMAND_REGISTRY.list_for_interface("cli")` - Get CLI commands
- `COMMAND_REGISTRY.list_for_interface("mcp")` - Get MCP tools

### 5. Adapters

**Click Adapter** (`click_adapter.py`):
- Generates Click commands from CommandSpec
- Handles parameter decorators, help text, groups
- Calls `register_unified_commands_to_click(cli_group)`

**MCP Adapter** (`mcp_adapter.py`):
- Generates MCP tool definitions with JSON Schema
- Provides async handler for tool calls
- Calls `get_unified_mcp_tools()`

## Parity Enforcement

### CLI Command: `vibey parity check`

```bash
$ vibey parity check
CLI/MCP Parity Report
=====================
Total unified commands: 16
  - Both interfaces: 16
  - CLI only: 0
  - MCP only: 0

Parity Status: PASS
```

### CI Workflow (`.github/workflows/parity-check.yml`)

- Runs on PRs affecting unified/cli/mcp paths
- Generates JSON report artifact
- Comments on PRs with parity status
- Supports strict mode for undocumented exclusions

## Migrated Commands

### Roadmap Commands (10)
- `roadmap_status` - Show roadmap status
- `roadmap_show` - Show item details
- `roadmap_start` - Start task/sprint
- `roadmap_complete` - Complete task/sprint
- `roadmap_list_tracks` - List tracks
- `roadmap_list_sprints` - List sprints
- `roadmap_list_tasks` - List tasks
- `roadmap_db_status` - Database status
- `roadmap_db_rebuild` - Rebuild database
- `roadmap_db_validate` - Validate database

### Deploy Commands (3)
- `deploy_list` - List platforms
- `deploy_run` - Deploy to platform
- `deploy_status` - Check deployment status

### Docs Commands (3)
- `docs_generate_cli` - Generate CLI reference
- `docs_generate_mcp` - Generate MCP reference
- `docs_check_drift` - Check documentation drift

## Success Metrics

- [x] 16 commands defined using unified decorator
- [x] Commands available in both CLI and MCP
- [x] Type mapping works correctly
- [x] Parity check CLI command functional
- [x] CI workflow configured
- [x] 39 tests passing

## Future Work

1. Migrate remaining 153 CLI commands to unified decorator
2. Migrate remaining 60 MCP-only tools
3. Add lint rule blocking non-unified command additions
4. Add parameter drift detection between interfaces

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `vibey/unified/__init__.py` | Package exports | 60 |
| `vibey/unified/command.py` | `@unified_command` decorator | 182 |
| `vibey/unified/param.py` | `@param` decorator | 134 |
| `vibey/unified/types.py` | Type mapping | 87 |
| `vibey/unified/registry.py` | Command registry | 151 |
| `vibey/unified/parity.py` | Parity checker | 254 |
| `vibey/unified/adapters/click_adapter.py` | Click adapter | 180 |
| `vibey/unified/adapters/mcp_adapter.py` | MCP adapter | 192 |
| `vibey/unified/formatters/base.py` | CommandResult | 109 |
| `vibey/unified/commands/roadmap.py` | Roadmap commands | 568 |
| `vibey/unified/commands/deploy.py` | Deploy commands | 160 |
| `vibey/unified/commands/docs.py` | Docs commands | 117 |
| `tests/unified/test_unified_command.py` | Tests | 592 |
| `.github/workflows/parity-check.yml` | CI workflow | 105 |

**Total: 3,136 lines of code**
