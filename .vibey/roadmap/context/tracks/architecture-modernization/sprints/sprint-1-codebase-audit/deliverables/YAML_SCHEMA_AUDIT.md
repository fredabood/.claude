# YAML Schema Versions Audit

**Date:** 2025-12-17
**Task:** Sprint 1, Task 6 - Audit YAML schema versions before cleanup
**Status:** Complete

---

## Executive Summary

The codebase has a well-defined schema versioning system across two layers:
1. **Database schema** - SQLite migrations with version tracking (current: 2.1.0)
2. **YAML format** - v1 (dataclass) vs v2 (Pydantic) format detection

| Component | Current Version | Migration Path |
|-----------|-----------------|----------------|
| SQLite Database | 2.1.0 | Automatic via migrations |
| YAML Format | v2 (flat) | Auto-detection supports both |
| Config Schemas | 1.0.0 | Separate system |

---

## Schema Components

### 1. Database Schema Versioning

**Location:** `vibey/roadmap/database/`

**Current Version:** 2.1.0 (stored in `database_state` table)

**Migration History:**
| Migration | Version | Purpose |
|-----------|---------|---------|
| 006_unified_ticket_schema.sql | 2.0.0 | Unified ticket system |
| 007_sessions_schema.sql | 2.1.0 | Sessions support |

**Version Tracking:**
```sql
SELECT * FROM database_state;
-- id: 1
-- schema_version: 2.1.0
-- migration_timestamp: 2025-12-17T18:50:51
```

**Key Files:**
- `vibey/roadmap/database/migrations/` - SQL migration scripts
- `vibey/roadmap/database/migrate_to_v2.py` - Migration runner
- `vibey/roadmap/database/__init__.py` - Exports `get_schema_version()`

### 2. YAML Format Versioning

**Location:** `vibey/roadmap/serialization/`

**Current Format:** v2 (flat structure)

**Format Detection Function:**
```python
def detect_yaml_format(data: Dict[str, Any]) -> str:
    """
    Detect if YAML data uses v1 (dataclass) or v2 (Pydantic) format.

    V2 format indicators:
    - 'criteria' field present (unified criterion system)
    - 'parent_ref' field present (explicit hierarchy)
    - Fields with '_local' suffix (e.g., commits_local)
    - 'ticket_type' field present
    """
```

**File Structure Versions:**

| Version | Structure | Example |
|---------|-----------|---------|
| v1 (Legacy) | Nested directories | `<track>/<sprint>/<task>/task.yaml` |
| v2 (Current) | Flat ULID directories | `tasks/01KC2D0JK06MN77ZHAGAHF5VKD.yaml` |

**YAML File Format:**
```yaml
# Current v2 format (no explicit version field)
task:
  id: 01KC2D0JK06MN77ZHAGAHF5VKD
  sprint_id: 01KC7TNS0SC0FX8TPGN9SG4J1B
  track_id: 01KC7TNS0SC0FX8TPGN9SG4J14
  roadmap_id: vibey-framework-v2
  task_type: development
  title: Create AiderAdapter class
  status: completed
  blocked: false
```

### 3. Config Schema Versioning

**Location:** `vibey/config/schemas/`

**Current Version:** 1.0.0

**Schema Files:**
| File | Purpose |
|------|---------|
| `project.yaml` | Project configuration schema |
| `framework.yaml` | Framework settings schema |
| `agents.yaml` | Agent configuration schema |
| `quality-gates.yaml` | Quality gate definitions |

**Example:**
```yaml
# vibey/config/schemas/project.yaml
schema_version: "1.0.0"
type: object
properties:
  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
```

---

## Legacy Code Paths

### Still Present (for backward compatibility)

| Location | Purpose | Status |
|----------|---------|--------|
| `yaml_loader.py:detect_yaml_format()` | Auto-detect v1/v2 | Active |
| `yaml_loader.py:1124` | `if False:` legacy task embedding | Disabled |
| `yaml_loader.py:2145` | `if False:` legacy task conversion | Disabled |
| `yaml_dumper.py` | v1/v2 dual support | Active (writes v2) |

### Confirmed Removed

| Component | Status |
|-----------|--------|
| v1 nested directory loading | Removed (files migrated) |
| Hierarchical slug-based IDs | Replaced by ULIDs |
| Embedded tasks in sprints | Deprecated (standalone files) |

---

## Backward Compatibility Assessment

### Currently Supported

1. **Auto-detection** - Loaders detect v1 vs v2 format automatically
2. **Default v2 output** - All writes use v2 format
3. **Migration path** - `migrate_to_v2.py` exists for database

### Migration Requirements

| From | To | Migration |
|------|-----|-----------|
| v1 YAML | v2 YAML | Manual or via directory_migration.py |
| DB 2.0.0 | DB 2.1.0 | Automatic via 007_sessions_schema.sql |
| Config 0.x | Config 1.0.0 | N/A (new system) |

### External Tool Considerations

| Tool | Uses YAML? | Impact |
|------|------------|--------|
| Git hooks | No | None |
| MCP Server | No (uses SQLite) | None |
| CLI | No (uses operations layer) | None |
| Tests | Yes (fixtures) | May need updates |

---

## Schema Evolution History

```
Timeline:
├── Pre-2024: v1 (nested directories, slug IDs)
│   └── Structure: <track>/<sprint>/<task>/
│
├── 2024-Q4: v2 migration begins
│   ├── ADR-0001: ULID identifiers adopted
│   ├── ADR-0002: Flat directory structure
│   └── Database: unified_ticket_schema (2.0.0)
│
└── 2025-Q1: Current state
    ├── Database: 2.1.0 (sessions support)
    ├── YAML: v2 format only (v1 detection kept)
    └── Config: 1.0.0 (new system)
```

---

## Recommendations

### Safe to Remove

1. **Disabled legacy code blocks** (`if False:`) - These are preserved for reference but could be archived
2. **v1 format detection** - If no v1 files remain, detection code is dead

### Keep for Now

1. **Format auto-detection** - Low cost, high safety benefit
2. **Database migrations** - Essential for schema upgrades
3. **Config schema versioning** - Active and separate concern

### Future Improvements

1. **Add explicit `format_version` to YAML files** - Clearer than auto-detection
2. **Archive v1 loader code** - Move to `_deprecated.py` if needed for reference
3. **Document migration procedures** - Create `MIGRATION_GUIDE.md`

---

## Verification Commands

```bash
# Check database schema version
sqlite3 .vibey/roadmap.db "SELECT schema_version FROM database_state;"

# Verify all YAML files use v2 format (have entity wrapper)
head -1 .vibey/roadmap/tracks/*.yaml | grep "track:" | wc -l

# Check for any v1-style nested structures
find .vibey/roadmap -type d -name "*-task-*" | wc -l  # Should be 0

# Verify config schema versions
grep "schema_version" vibey/config/schemas/*.yaml
```

---

## Related Files

- ADR-0001: ULID Identifiers
- ADR-0002: Flat Directory Structure
- ADR-0003: Dual Storage (SQLite + YAML)

---

*Generated as part of Architecture Modernization Track, Sprint 1*
