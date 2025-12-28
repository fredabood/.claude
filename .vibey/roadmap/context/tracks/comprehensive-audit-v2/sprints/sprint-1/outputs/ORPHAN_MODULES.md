# Orphan Modules Report

**Generated:** 2025-12-28
**Audit Version:** comprehensive-audit-v2

## Summary

| Metric | Value |
|--------|-------|
| Total Orphan Modules | 93 |
| Database/Migration Scripts | 12 |
| Standalone CLI Scripts | 15 |
| Unused/Deprecated Code | 20+ |
| Test Fixtures | 5 |
| Prototype/Experimental | 10+ |

## Definition

Orphan modules are Python files that:
- Do NOT import any other vibey modules
- Are NOT imported by any other vibey modules
- Excludes `__init__.py` files (package markers)

## Categories

### Database Migration/Utility Scripts (12)
These are standalone scripts intended for one-time use:
- `vibey/roadmap/database/migrate_to_v2.py`
- `vibey/roadmap/database/yaml_remediation.py`
- `vibey/roadmap/database/test_triggers.py`
- `vibey/roadmap/database/round_trip_validation.py`
- `vibey/roadmap/database/test_views.py`
- `vibey/roadmap/database/compare_databases.py`
- `vibey/roadmap/database/migrations/add_token_columns.py`
- `vibey/roadmap/database/crud/task.py`
- `vibey/roadmap/database/crud/roadmap.py`
- `vibey/roadmap/database/crud/track.py`
- `vibey/roadmap/database/crud/test_relationships.py`
- `vibey/roadmap/database/crud/sprint.py`

**Status:** Expected orphans - migration/test utilities

### Standalone CLI Scripts (15)
These are standalone CLI entry points:
- `vibey/cli/validate-vibey-config.py`
- `vibey/cli/render-template.py`
- `vibey/cli/manage-project-context.py`
- `vibey/cli/roadmap-summarize.py`
- `vibey/cli/generate-agent.py`
- `vibey/cli/generate-config.py`
- `vibey/cli/roadmap-context.py`
- `vibey/cli/rollback-framework.py`
- `vibey/cli/validate-roadmap-format.py`
- `vibey/cli/update-config.py`
- `vibey/cli/check-version.py`
- `vibey/cli/migrate-dependency-cache.py`
- `vibey/cli/migrate-embedded-tasks.py`
- `vibey/cli/validate-config.py`
- `vibey/cli/roadmap-prepare.py`
- `vibey/cli/analyze-project-roadmap.py`

**Status:** Review needed - may be deprecated or need integration

### Unified Architecture (Prototype) (6)
New architecture modules not yet integrated:
- `vibey/unified/parity.py`
- `vibey/unified/registry.py`
- `vibey/unified/param.py`
- `vibey/unified/types.py`
- `vibey/unified/formatters/base.py`
- `vibey/unified/adapters/click_adapter.py`

**Status:** In development - will be integrated

### MCP Resources/Prompts (5)
MCP subsystems not yet wired:
- `vibey/mcp/resources/provider.py`
- `vibey/mcp/resources/types.py`
- `vibey/mcp/prompts/provider.py`
- `vibey/mcp/prompts/types.py`
- `vibey/mcp/discovery/discovery.py`

**Status:** Review needed - may need integration

### Other (Various)
- `vibey/roadmap/serialization/v1_to_v2.py` - Migration utility
- `vibey/roadmap/models/standard.py` - Possibly deprecated
- `vibey/roadmap/operations/migrate_to_criteria.py` - Migration utility
- `vibey/roadmap/validation/platform.py` - Platform validation
- `vibey/roadmap/standards/validators/*` - Custom validators

## Recommendations

1. **Archive or delete** deprecated CLI scripts
2. **Integrate** unified architecture modules when complete
3. **Wire up** MCP resources/prompts if needed
4. **Keep** migration utilities but document them
5. **Review** validators for integration opportunities

---

*Report generated: 2025-12-28*
