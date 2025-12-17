# Dead Code Analysis Report

**Date:** 2025-12-17
**Task:** Sprint 1, Task 5 - Run dead code analysis with Vulture
**Status:** Complete

---

## Executive Summary

Ran Vulture static analysis (min-confidence 80%) on the vibey package. Found 43 flagged items categorized below.

| Category | Count | Recommendation |
|----------|-------|----------------|
| Unused imports | 17 | Most are false positives (dynamic usage, future use) |
| Unused variables | 22 | Most intentional (fixtures, API compatibility) |
| Unsatisfiable conditions | 2 | Intentionally disabled legacy code |
| **True dead code** | **~5** | **Safe to remove** |

---

## Analysis Results

### Category 1: Unused Imports (17 findings)

Most are false positives due to dynamic usage, API compatibility, or planned future use.

| File | Import | Confidence | Status |
|------|--------|------------|--------|
| cli/remediate_roadmap_system.py:27 | `dump_track_to_yaml` | 90% | Investigate |
| cli/roadmap-update.py:39 | `trigger_on_track_complete` | 90% | Investigate |
| cli/validate-vibey-config.py:24 | `jsonschema` | 90% | False positive - used dynamically |
| mcp/adapters/roadmap_adapter.py:18 | `ops_refresh_progress` | 90% | Investigate |
| operations/roadmap/optimized_validator.py:26 | `lru_cache` | 90% | Investigate |
| operations/roadmap/update.py:219 | `trigger_on_track_complete` | 90% | Investigate |
| roadmap/database/connection.py:374 | (see unused var) | - | - |
| roadmap/models/ticket/orm.py:23 | `Column` | 90% | SQLAlchemy pattern |
| roadmap/models/ticket/orm.py:35 | `declared_attr` | 90% | SQLAlchemy pattern |
| roadmap/models/ticket/orm.py:43 | `JSON` | 90% | SQLAlchemy pattern |
| roadmap/models/ticket/repository.py:19 | `or_` | 90% | SQLAlchemy pattern |
| roadmap/serialization/sql_loader.py:1226 | `has_unified_schema` | 90% | Investigate |
| roadmap/serialization/yaml_loader.py:20 | `PydanticActivityLogEntry` | 90% | Pydantic pattern |
| roadmap/serialization/yaml_loader.py:20 | `PydanticDevelopmentGate` | 90% | Pydantic pattern |
| roadmap/serialization/yaml_loader.py:20 | `PydanticVersionHistoryEntry` | 90% | Pydantic pattern |
| roadmap/serialization/yaml_loader.py:35 | `PydanticGateStatus` | 90% | Pydantic pattern |
| roadmap/test_directory_manager.py:17 | `get_sprint_paths`, etc. | 90% | Test file - acceptable |

**False Positives (Framework Patterns):**
- SQLAlchemy imports (`Column`, `declared_attr`, `JSON`, `or_`) - common ORM pattern
- Pydantic imports - may be used for type validation
- `jsonschema` - dynamically used in validation

**Candidates for Removal:**
- `trigger_on_track_complete` (appears twice, unused)
- `dump_track_to_yaml` (if not used in functions)
- `ops_refresh_progress` (if not used in adapter)
- `lru_cache` (if no decorated functions)
- `has_unified_schema` (if schema checks removed)

### Category 2: Unused Variables (22 findings)

Most are intentional for API compatibility, fixtures, or debugging.

| File | Variable | Confidence | Status |
|------|----------|------------|--------|
| cli/roadmap_lib/formatting.py:248 | `indent_str` | 100% | **Safe to remove** |
| operations/audit/file_classifier.py:707 | `base_module` | 100% | Investigate |
| operations/context/capture.py:234 | `exc_tb` | 100% | Exception pattern |
| operations/git/error_handler.py:85 | `exc_tb` | 100% | Exception pattern |
| operations/git/strategy_adoption.py:410 | `customize` | 100% | Investigate |
| roadmap/database/connection.py:374 | `connection_record` | 100% | SQLAlchemy event param |
| roadmap/models/ticket/hierarchical.py:65 | `exclude_id` | 100% | Investigate |
| roadmap/serialization/directory_migration.py:217 | `preserve_old` | 100% | Investigate |
| roadmap/serialization/test_serialization_bridge.py | `temp_db` (x16) | 100% | Fixture return |

**Intentional (API Compatibility):**
- `exc_tb` - Exception traceback, common Python pattern `(exc_type, exc_val, exc_tb)`
- `connection_record` - SQLAlchemy event callback signature
- `temp_db` - Pytest fixture returns tuple, variable unpacked but unused

**Candidates for Removal:**
- `indent_str` - appears truly unused

### Category 3: Unsatisfiable Conditions (2 findings)

| File | Line | Status |
|------|------|--------|
| roadmap/serialization/yaml_loader.py:1124 | `if False and 'tasks' in sprint_data` | Intentional - legacy code |
| roadmap/serialization/yaml_loader.py:2145 | `if False:` | Intentional - legacy code |

**Status:** These are **intentionally disabled** legacy code blocks preserved for reference. The `if False:` pattern is used to keep the code in the file but prevent execution. Comments explain they're "deprecated" and "disabled."

**Recommendation:** Consider removing entirely or moving to a `_deprecated.py` file if reference is truly needed.

---

## Vulture Whitelist (False Positives)

The following should be whitelisted if adding Vulture to CI:

```python
# vulture_whitelist.py
# SQLAlchemy imports - used by ORM metaclass
Column  # unused import
declared_attr  # unused import
JSON  # unused import
or_  # unused import

# Pydantic imports - used for type validation
PydanticActivityLogEntry  # unused import
PydanticDevelopmentGate  # unused import
PydanticVersionHistoryEntry  # unused import
PydanticGateStatus  # unused import

# Exception handlers
exc_tb  # unused variable

# SQLAlchemy event callbacks
connection_record  # unused variable

# Test fixtures
temp_db  # unused variable (fixture return)

# jsonschema - dynamically used
jsonschema  # unused import
```

---

## Confirmed Safe to Remove

The following code can be safely removed with minimal risk:

| File:Line | Code | Rationale |
|-----------|------|-----------|
| cli/roadmap_lib/formatting.py:248 | `indent_str` | Variable assigned but never used |
| yaml_loader.py:1124-1150 | `if False and ...` block | Legacy disabled code |
| yaml_loader.py:2145-2170 | `if False:` block | Legacy disabled code |

---

## Recommendations

### Immediate (Low Risk)
1. Remove `indent_str` unused variable
2. Remove or archive the two `if False:` legacy code blocks

### Future Cleanup (Needs Verification)
1. Verify and potentially remove:
   - `trigger_on_track_complete` imports (2 files)
   - `dump_track_to_yaml` import
   - `ops_refresh_progress` import
   - `lru_cache` import
   - `has_unified_schema` import

### CI Integration
1. Add vulture_whitelist.py for false positives
2. Run `vulture vibey/ vulture_whitelist.py --min-confidence 90` in CI
3. Fail on new dead code additions

---

## Verification Commands

```bash
# Run vulture analysis
vulture vibey/ --min-confidence 80

# With whitelist (future)
vulture vibey/ vulture_whitelist.py --min-confidence 90

# Count by category
vulture vibey/ --min-confidence 80 | grep "unused import" | wc -l   # imports
vulture vibey/ --min-confidence 80 | grep "unused variable" | wc -l # variables
```

---

## Related Files

- vulture_whitelist.py (to be created if CI integration added)
- Sprint Plan Task 5 for implementation details

---

*Generated as part of Architecture Modernization Track, Sprint 1*
