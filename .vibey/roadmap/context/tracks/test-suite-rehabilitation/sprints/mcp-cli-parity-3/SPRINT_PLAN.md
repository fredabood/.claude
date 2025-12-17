# Sprint 3: MCP/CLI Parity & Integration Tests

## Sprint Goal

Implement automated CLI/MCP parity enforcement to ensure commands are defined once and automatically propagate to both interfaces.

## Approach Selected

**Unified Decorator Pattern** - Single `@unified_command` decorator that:
1. Registers commands in a central registry
2. Adapters generate Click commands and MCP tools from registry
3. Commands default to both interfaces, can explicitly exclude either
4. CI enforcement via `vibey parity check`

### Why This Approach?

Evaluated three approaches:

| Approach | Pros | Cons |
|----------|------|------|
| **Unified Decorator** (Selected) | Type-safe, IDE support, familiar decorator pattern | New code to maintain |
| Schema-Driven | Language agnostic, easy validation | No IDE support, runtime errors |
| MCP-wraps-CLI | Minimal new code | Performance overhead, limited by Click capabilities |

## Implementation Summary

### Core Framework
- `@unified_command` decorator with `interfaces` parameter
- `@param` decorator for parameter specifications
- `ParamType` enum with Click/JSON Schema type mapping
- `CommandRegistry` singleton for discovery

### Adapters
- Click adapter generates Click commands from specs
- MCP adapter generates tool definitions with JSON Schema

### Parity Enforcement
- `vibey parity check` CLI command
- `vibey parity report` for detailed output
- GitHub Actions workflow for CI enforcement

## Tasks Completed

### Task 01KCMKG7Z740QY2CCWTFRZ6P2D: Implement MCP/CLI parity enforcement

**Status:** Completed

**Deliverables:**
1. `vibey/unified/` package (15 files, 2,544 lines)
2. 16 commands migrated to unified decorator
3. 39 comprehensive tests
4. CI workflow for automated enforcement

**Commit:** `b510eaf0` - feat(01KCMKG7Z740QY2CCWTFRZ6P2D): Implement CLI/MCP parity enforcement

## Remaining Sprint Tasks

The following tasks from Sprint 3 remain:
- Add integration tests for unified commands
- Migrate remaining CLI commands
- Add lint rule blocking non-unified additions

## Key Decisions Made

1. **Interface selection via `interfaces` parameter** - Defaults to both, can exclude either
2. **Decorators applied bottom-up** - `@param` before `@unified_command`
3. **Registry pattern** - Central singleton for command discovery
4. **Operations layer unchanged** - Unified commands call existing operations
5. **Backwards compatible** - Old commands continue working during migration

## Files Changed

### New Files (20)
- `vibey/unified/` - Complete unified command framework
- `tests/unified/` - Comprehensive test suite
- `.github/workflows/parity-check.yml` - CI enforcement

### Modified Files (2)
- `vibey/cli/main.py` - Load unified commands, add parity group
- `vibey/mcp/server.py` - Load unified tools

## Metrics

- **Lines added:** 3,136
- **Tests:** 39 passing
- **Commands migrated:** 16
- **Coverage:** Core framework fully covered

## Next Steps

1. Complete remaining Sprint 3 integration test tasks
2. Migrate more commands incrementally
3. Add stricter lint enforcement
