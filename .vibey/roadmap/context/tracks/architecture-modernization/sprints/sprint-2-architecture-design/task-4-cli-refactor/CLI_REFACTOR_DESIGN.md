# CLI Refactor Design for First-Class Semantic Layer

**Sprint:** Architecture Design (Sprint 2)
**Task:** Design CLI Refactor for First-Class Semantic Layer
**Date:** 2025-12-17
**Status:** Complete

---

## Executive Summary

This document designs a CLI refactoring strategy that promotes semantic layer concepts to first-class status while maintaining backward compatibility. The design leverages the existing Unified Decorator Architecture (`vibey/unified/`) to ensure CLI/MCP parity.

---

## Design Goals

1. **Semantic First** - CLI structure mirrors domain model, not storage
2. **Unified Commands** - Single source of truth via `@unified_command`
3. **Backward Compatible** - Existing commands continue to work
4. **MCP Parity** - CLI and MCP have identical capabilities
5. **Progressive Migration** - No big-bang changes required

---

## New Command Hierarchy

### Top-Level Structure

```
vibey
├── ticket              # Unified ticket operations (NEW)
├── criteria            # Criterion management (NEW)
├── artifact            # Artifact management (existing)
├── db                  # Database operations (extracted)
├── roadmap             # Legacy/compatibility (alias)
├── deploy              # Deployment (unchanged)
├── docs                # Documentation (unchanged)
├── config              # Configuration (unchanged)
└── [other groups]      # Unchanged
```

### `ticket` Command Group (New)

Unified interface for all ticket types (roadmap, track, sprint, task).

```bash
# List tickets
vibey ticket list                          # All tickets
vibey ticket list --type track             # Only tracks
vibey ticket list --type sprint --parent <track-id>
vibey ticket list --status in_progress

# Show ticket details
vibey ticket show <id>                     # Any ticket by ID
vibey ticket show <id> --children          # Include children
vibey ticket show <id> --criteria          # Include criteria

# Lifecycle operations
vibey ticket start <id>                    # Start (sprint or task)
vibey ticket complete <id>                 # Complete any ticket
vibey ticket revert <id>                   # Revert to previous status

# Create tickets
vibey ticket create --type track --name "Feature X"
vibey ticket create --type sprint --parent <track-id> --name "Sprint 1"
vibey ticket create --type task --parent <sprint-id> --title "Task Title"

# Search and query
vibey ticket search "authentication"       # Full-text search
vibey ticket tree                          # Hierarchy view
vibey ticket tree <id>                     # Subtree from ID
```

**Implementation:**
```python
# vibey/unified/commands/ticket.py
from vibey.unified import unified_command, param, ParamType

@unified_command(
    name="ticket_start",
    description="Start working on a ticket",
    interfaces=["cli", "mcp"],
    cli_group="ticket",
    mcp_name="vibey_ticket_start"
)
@param("ticket_id", type=ParamType.STRING, required=True,
       help="Ticket ID (ULID)")
def ticket_start(ticket_id: str, root_dir=None):
    from vibey.operations.roadmap import start_item
    return start_item(root_dir, ticket_id)
```

### `criteria` Command Group (New)

First-class criterion management.

```bash
# List criteria for a ticket
vibey criteria list <ticket-id>

# Add criteria
vibey criteria add <ticket-id> --type file-exists --path "docs/README.md"
vibey criteria add <ticket-id> --type test-passes --pattern "test_*.py"
vibey criteria add <ticket-id> --type manual --description "Code review approved"
vibey criteria add <ticket-id> --type child-complete --child-id <child-id>

# Check criteria status
vibey criteria check <ticket-id>           # Check all criteria
vibey criteria check <ticket-id> --verbose # Detailed output

# Remove criteria
vibey criteria remove <ticket-id> <criterion-id>

# Override criteria (for inherited standards)
vibey criteria override <ticket-id> <criterion-id> --reason "Not applicable"
```

**Implementation:**
```python
# vibey/unified/commands/criteria.py
from vibey.unified import unified_command, param, ParamType

@unified_command(
    name="criteria_list",
    description="List criteria for a ticket",
    interfaces=["cli", "mcp"],
    cli_group="criteria",
    mcp_name="vibey_criteria_list"
)
@param("ticket_id", type=ParamType.STRING, required=True,
       help="Ticket ID")
def criteria_list(ticket_id: str, root_dir=None):
    from vibey.operations.roadmap import get_ticket_criteria
    return get_ticket_criteria(root_dir, ticket_id)
```

### `db` Command Group (Extracted)

Promote database operations from `roadmap db` to top-level.

```bash
# Current
vibey roadmap db status
vibey roadmap db rebuild
vibey roadmap db validate

# New (aliases to current)
vibey db status
vibey db rebuild
vibey db validate
```

### `roadmap` Group (Backward Compatibility)

Keep all existing commands working.

```bash
# These continue to work unchanged
vibey roadmap status
vibey roadmap show <id>
vibey roadmap start <id>
vibey roadmap complete <id>
vibey roadmap create-task --sprint <id> --title "..."

# Deprecation notice (Phase 2+)
# "vibey roadmap start" will print:
# DeprecationWarning: Use 'vibey ticket start' instead
```

---

## Backward Compatibility Strategy

### Phase 1: Additive (No Breaking Changes)

| Action | Impact |
|--------|--------|
| Add `ticket` group | New capability |
| Add `criteria` group | New capability |
| Extract `db` group | New aliases |
| Keep `roadmap` unchanged | Zero impact |

```python
# vibey/cli/main.py

# Add new groups alongside existing
cli.add_command(ticket_group)
cli.add_command(criteria_group)
cli.add_command(db_group)

# Keep roadmap unchanged
cli.add_command(roadmap_group)
```

### Phase 2: Deprecation Warnings

```python
# After Phase 1 is stable (future version)

@roadmap_group.command("start")
@click.pass_context
def roadmap_start(ctx, item_id):
    click.echo(
        "DeprecationWarning: 'vibey roadmap start' is deprecated. "
        "Use 'vibey ticket start' instead.",
        err=True
    )
    # Delegate to new implementation
    return ticket_start(item_id)
```

### Phase 3: Removal (Major Version)

```python
# In version 3.0.0 (future)
# Remove deprecated roadmap commands
# Keep only:
#   - roadmap status (overview)
#   - roadmap init (initialization)
```

---

## MCP Parity Design

### Unified Command → Dual Interface

```python
@unified_command(
    name="ticket_start",
    interfaces=["cli", "mcp"],  # Both by default
    cli_group="ticket",
    mcp_name="vibey_ticket_start"
)
def ticket_start(ticket_id: str, root_dir=None):
    ...
```

### CLI-Only Commands

```python
@unified_command(
    name="wizard",
    interfaces=["cli"],  # CLI only
    cli_group="ticket"
)
def ticket_wizard():
    # Interactive wizard - not suitable for MCP
    ...
```

### MCP-Only Commands

```python
@unified_command(
    name="agent_context",
    interfaces=["mcp"],  # MCP only
    mcp_name="vibey_agent_context"
)
def agent_context(session_id: str):
    # Agent-specific context - not useful in CLI
    ...
```

### Parity Enforcement

```bash
# Run parity check
vibey parity check

# Output:
# CLI/MCP Parity Report
# =====================
# Unified commands: 85
#   - Both interfaces: 75
#   - CLI only: 8
#   - MCP only: 2
#
# Status: PASS (all exclusions documented)
```

---

## Migration Timeline

### Phase 1: Foundation (This Sprint)

- [x] Design complete (this document)
- [ ] Implement `ticket` group skeleton
- [ ] Implement `criteria` group skeleton
- [ ] Add `db` aliases
- [ ] Update parity checker

### Phase 2: Command Migration (Next Sprint)

- [ ] Migrate `start`/`complete`/`show` to unified
- [ ] Implement `criteria` operations
- [ ] Add `ticket list` and `ticket search`
- [ ] Add deprecation warnings

### Phase 3: Stabilization (Future)

- [ ] Monitor usage of deprecated commands
- [ ] Update documentation
- [ ] Plan removal timeline

### Phase 4: Cleanup (Major Version)

- [ ] Remove deprecated commands
- [ ] Simplify `roadmap` group
- [ ] Update all documentation

---

## Command Mapping Reference

### Lifecycle Commands

| Current | New | Unified Name |
|---------|-----|--------------|
| `roadmap start <id>` | `ticket start <id>` | `ticket_start` |
| `roadmap complete <id>` | `ticket complete <id>` | `ticket_complete` |
| `roadmap revert <id>` | `ticket revert <id>` | `ticket_revert` |
| `roadmap show <id>` | `ticket show <id>` | `ticket_show` |

### Creation Commands

| Current | New | Unified Name |
|---------|-----|--------------|
| `roadmap create-track` | `ticket create --type track` | `ticket_create` |
| `roadmap create-sprint` | `ticket create --type sprint` | `ticket_create` |
| `roadmap create-task` | `ticket create --type task` | `ticket_create` |

### Query Commands

| Current | New | Unified Name |
|---------|-----|--------------|
| `roadmap status` | `ticket status` | `ticket_status` |
| (missing) | `ticket list` | `ticket_list` |
| (missing) | `ticket search` | `ticket_search` |
| (missing) | `ticket tree` | `ticket_tree` |

### Criteria Commands (All New)

| Command | Unified Name |
|---------|--------------|
| `criteria list` | `criteria_list` |
| `criteria add` | `criteria_add` |
| `criteria check` | `criteria_check` |
| `criteria remove` | `criteria_remove` |
| `criteria override` | `criteria_override` |

---

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `vibey/unified/commands/ticket.py` | Ticket unified commands |
| `vibey/unified/commands/criteria.py` | Criteria unified commands |
| `vibey/cli/ticket.py` | CLI ticket group |
| `vibey/cli/criteria.py` | CLI criteria group |
| `vibey/cli/db.py` | CLI db group (extracted) |

### Modified Files

| File | Change |
|------|--------|
| `vibey/cli/main.py` | Add new groups |
| `vibey/mcp/server.py` | Add new tools from registry |
| `vibey/unified/registry.py` | Register new commands |

### Unchanged Files

| File | Reason |
|------|--------|
| `vibey/cli/commands.py` | Keep for backward compat |
| `vibey/operations/roadmap/` | Operations unchanged |

---

## Success Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| New structure designed | ✅ Complete | Command hierarchy above |
| Backward compatibility addressed | ✅ Complete | Phased migration plan |
| MCP parity maintained | ✅ Complete | Unified decorator design |
| Migration timeline defined | ✅ Complete | 4-phase timeline |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users resist new commands | Medium | Low | Keep old commands forever |
| Migration introduces bugs | Medium | Medium | Extensive testing |
| MCP parity drift | Low | High | CI enforcement |
| Performance regression | Low | Medium | Benchmark tests |

---

## References

- Sprint 2 Task 1: SEMANTIC_LAYER_SPEC.md
- Sprint 2 Task 3: CLI_ARCHITECTURE_ANALYSIS.md
- Plan File: Unified Decorator Architecture (`curried-tinkering-pancake.md`)
- Unified Module: `vibey/unified/`
