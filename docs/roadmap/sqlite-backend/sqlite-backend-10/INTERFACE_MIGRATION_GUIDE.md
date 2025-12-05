# Interface Migration Guide - Sprint 10

This guide documents the Sprint 10 interface changes for standards inheritance display in CLI and MCP tools.

## Overview

Sprint 10 introduces **inheritance chain visualization** for the standards system. Standards can be defined at three levels (roadmap, track, sprint) and cascade down the hierarchy. The updated interfaces now clearly show:

- Which level each standard comes from (source level)
- Which specific entity defined it (source ID)
- Whether standards are overridden and why

## Standards Inheritance Model

```
roadmap
├── track
│   ├── sprint
│   │   └── task (inherits from all above)
│   └── task (inherits from roadmap + track)
└── task (inherits from roadmap only)
```

**Key rules:**
1. Standards cascade DOWN the hierarchy (children inherit from parents)
2. More specific standards override less specific ones (by ID)
3. Per-item overrides can bypass specific standards
4. Disabled standards are excluded from resolution

## CLI Changes

### Standards Display in `vibey roadmap show`

The `show` command now displays standards grouped by inheritance source:

```bash
$ vibey roadmap show sqlite-backend-10-task-001

📋 Standards: 3 standards (🔴 1 blocking, 🟡 1 warning, 🟢 1 audit [1 from roadmap, 2 from track])

   Standards Applied (by inheritance level):
   🗺️  roadmap (inherited from roadmap):
     • commit-required: Commit Required
       Type: commit_check | 🔴 BLOCKING
       Source: vibey-framework-v2

   🛤️  track (inherited from track):
     • test-coverage: Test Coverage
       Type: test_run | 🟡 WARNING
       Source: sqlite-backend
     • doc-required: Documentation Required
       Type: file_check | 🟢 AUDIT
       Source: sqlite-backend
```

### Standards Formatter Functions

Updated functions in `vibey/cli/roadmap_lib/standards_formatter.py`:

| Function | Change |
|----------|--------|
| `get_standards_for_item()` | Now returns `ResolvedStandard` objects with source info |
| `format_standards_summary()` | New `show_inheritance` parameter for source breakdown |
| `print_standards_list()` | Groups standards by source level with headers |
| `get_standards_compliance_data()` | Returns `inheritance` dict with source counts |

### New Data Fields

The `ResolvedStandard` object includes:

```python
class ResolvedStandard:
    standard: Standard          # The actual standard
    source_level: str           # "roadmap", "track", or "sprint"
    source_id: str              # ID of defining entity
    is_overridden: bool         # Whether bypassed by override
    override_reason: str        # Why overridden (if applicable)
```

## MCP Changes

### New Tool: `vibey_query_standards`

Query effective standards for any roadmap item with inheritance chain:

```json
{
  "name": "vibey_query_standards",
  "arguments": {
    "item_id": "sqlite-backend-10-task-001",
    "show_inheritance": true
  }
}
```

**Response format:**

```
📋 Standards for 'sqlite-backend-10-task-001' (3 total)

**Enforcement Breakdown:**
- 🔴 1 Blocking
- 🟡 1 Warning
- 🟢 1 Audit

**Inheritance Chain:**
- 🗺️  1 from roadmap
- 🛤️  2 from track
- ⚠️  0 overridden

**🗺️ From Roadmap:**
- commit-required: Commit Required
  Type: commit_check | 🔴 blocking
  Source: vibey-framework-v2

**🛤️ From Track:**
- test-coverage: Test Coverage
  Type: test_run | 🟡 warning
  Source: sqlite-backend
- doc-required: Documentation Required
  Type: file_check | 🟢 audit
  Source: sqlite-backend
```

### RoadmapAdapter Changes

New method `query_standards()` in `vibey/mcp/adapters/roadmap_adapter.py`:

```python
def query_standards(self, item_id: str) -> Dict[str, Any]:
    """
    Query effective standards with inheritance information.

    Returns:
        {
            "total": int,
            "blocking_count": int,
            "warning_count": int,
            "audit_count": int,
            "inheritance": {
                "roadmap": int,
                "track": int,
                "sprint": int,
                "overridden": int
            },
            "standards": [
                {
                    "id": str,
                    "name": str,
                    "type": str,
                    "enforcement": str,
                    "source_level": str,
                    "source_id": str,
                    "is_overridden": bool,
                    "override_reason": str | None
                }
            ]
        }
    """
```

## Migration Steps

### For CLI Users

No migration required. The display is automatically enhanced with inheritance information.

### For MCP Integrations

1. **Use new tool**: Call `vibey_query_standards` instead of manually parsing standards
2. **Handle new fields**: The response includes `source_level`, `source_id`, `is_overridden`
3. **Inheritance breakdown**: Use the `inheritance` dict for summary statistics

### For Custom Tools

If you have custom tooling that queries standards:

```python
# Old approach (still works)
from vibey.cli.roadmap_lib.standards_formatter import get_standards_for_item
standards = get_standards_for_item(root_dir, item_id)

# Now returns ResolvedStandard objects:
for resolved in standards:
    print(f"Standard: {resolved.standard.id}")
    print(f"  From: {resolved.source_level} ({resolved.source_id})")
    print(f"  Overridden: {resolved.is_overridden}")
```

## Breaking Changes

None. All changes are backward compatible:

- `get_standards_for_item()` now returns `ResolvedStandard` instead of `Standard`, but `ResolvedStandard.standard` provides the original object
- Display functions accept both `Standard` and `ResolvedStandard` lists
- JSON output includes additional fields but no fields were removed

## Related Files

| File | Purpose |
|------|---------|
| `vibey/cli/roadmap_lib/standards_formatter.py` | CLI display formatting |
| `vibey/mcp/tools/query_tools.py` | MCP tool definitions |
| `vibey/mcp/adapters/roadmap_adapter.py` | MCP-to-operations bridge |
| `vibey/roadmap/standards/resolver.py` | Core inheritance resolution |
| `vibey/operations/roadmap/standards_enforcement.py` | Standards query operations |

## Troubleshooting

### Standards not showing inheritance info

Ensure you're using the updated `standards_formatter.py`. The inheritance information comes from `ResolvedStandard` objects returned by `StandardsResolver`.

### MCP tool not found

The `vibey_query_standards` tool requires MCP server restart after update. Check that `get_query_tools()` includes the new tool definition.

### Override not working

Overrides must be defined in the standard itself with a matching `target_id`. Check:

```yaml
standards:
  - id: commit-required
    overrides:
      - target_id: sqlite-backend-10-task-001
        reason: "Exempt from commit check during docs task"
```
