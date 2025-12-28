# Dead Code & Orphaned Files Audit

**Task:** 01KDDE9NEKAH3BM9PRFPHNNCN9
**Sprint:** Sprint 3 - Codebase Health Analysis
**Generated:** 2025-12-28T21:45:00+00:00

---

## Executive Summary

Found **31 dead code instances** via vulture, **13 standalone CLI scripts** that may be orphaned, and **27 test files** incorrectly located inside the `vibey/` package instead of `tests/`.

---

## Vulture Dead Code Analysis

| Metric | Value |
|--------|-------|
| Total Findings | 31 |
| Unused Variables | 24 |
| Unused Imports | 5 |
| Unsatisfiable Conditions | 2 |

### By Category

#### Unused Variables (24)

| File | Line | Variable | Confidence |
|------|------|----------|------------|
| vibey/adapters/pm/base.py | 330 | native_item | 100% |
| vibey/cli/roadmap_lib/formatting.py | 248 | indent_str | 100% |
| vibey/operations/audit/file_classifier.py | 707 | base_module | 100% |
| vibey/operations/context/capture.py | 234 | exc_tb | 100% |
| vibey/operations/git/error_handler.py | 84 | exc_tb | 100% |
| vibey/operations/git/strategy_adoption.py | 410 | customize | 100% |
| vibey/roadmap/database/connection.py | 374 | connection_record | 100% |
| vibey/roadmap/models/ticket/hierarchical.py | 67 | exclude_id | 100% |
| vibey/services/implementation/loop.py | 797 | frame | 100% |
| vibey/roadmap/serialization/test_serialization_bridge.py | (16 instances) | temp_db | 100% |

#### Unused Imports (5)

| File | Line | Import | Confidence |
|------|------|--------|------------|
| vibey/cli/error_handler.py | 40 | VibeyValidationError | 90% |
| vibey/cli/roadmap-update.py | 37 | trigger_on_track_complete | 90% |
| vibey/cli/roadmap_commands/start.py | 11 | cli_error | 90% |
| vibey/cli/validate-vibey-config.py | 23 | jsonschema | 90% |
| vibey/operations/roadmap/update.py | 255 | trigger_on_track_complete | 90% |

#### Unsatisfiable Conditions (2)

| File | Line | Issue |
|------|------|-------|
| vibey/roadmap/serialization/yaml_loader.py | 1350 | if condition always false |
| vibey/roadmap/serialization/yaml_loader.py | 2483 | if condition always false |

---

## Standalone CLI Scripts (Potential Orphans)

Found 13 standalone scripts in `vibey/cli/` that follow the legacy `kebab-case.py` naming pattern:

| Script | Status |
|--------|--------|
| check-version.py | Review needed |
| generate-agent.py | Review needed |
| generate-config.py | Review needed |
| render-template.py | Review needed |
| roadmap-context.py | Review needed |
| roadmap-init.py | Review needed |
| roadmap-prepare.py | Review needed |
| roadmap-query.py | Review needed |
| roadmap-summarize.py | Review needed |
| roadmap-update.py | Actively used |
| rollback-framework.py | Review needed |
| update-config.py | Review needed |
| validate-config.py | Review needed |

**Recommendation:** Review each script to determine if it's:
- Still needed → migrate to Click command module
- No longer needed → delete

---

## Test Files in Wrong Location

Found **27 test files** inside `vibey/` instead of `tests/`:

### vibey/roadmap/database/

- test_connection.py
- test_triggers.py
- test_views.py
- test_schema.py
- crud/test_relationships.py
- crud/test_crud.py

### vibey/roadmap/serialization/

- test_serialization_bridge.py

### vibey/roadmap/

- test_toc_generator.py
- test_id_generator.py

### vibey/roadmap/models/

- test_common.py

### vibey/roadmap/standards/validators/

- test_run.py

### vibey/mcp/tests/

- test_sprint_tools.py
- test_validation.py
- test_query_tools.py
- test_task_tools.py

### vibey/cli/tests/

- test_cli_cache_integration.py
- test_progress_tracking.py
- test_roadmap_cache.py
- test_roadmap_scripts.py
- test_persistent_cache.py
- test_formatting.py
- test_roadmap_integration.py
- test_e2e_roadmap_workflow.py

### vibey/adapters/gemini/tests/

- test_context_generator.py
- test_adapter.py
- test_orchestration.py
- test_e2e.py
- test_command_generator.py

**Impact:** These tests may not be discovered by pytest running on `tests/` directory.

---

## File Inventory

| Category | Count |
|----------|-------|
| Python files in vibey/ | 503 |
| Python files in tests/ | 243 |
| Standalone CLI scripts | 38 |
| Test files in wrong location | 27 |

---

## Cleanup Recommendations

### High Priority

1. **Move misplaced test files** to tests/ directory
   - Will improve test discoverability
   - Fix pytest collection

2. **Remove unused imports** (5 files)
   - Safe to auto-fix with ruff

### Medium Priority

3. **Review unsatisfiable conditions** in yaml_loader.py
   - May indicate logic bugs

4. **Review standalone CLI scripts** for consolidation
   - Migrate needed scripts to Click modules
   - Delete obsolete scripts

### Low Priority

5. **Clean up unused variables** (24 instances)
   - Many are intentional (exc_tb for exception context)
   - temp_db fixtures may be needed for side effects

---

---

## Baseline Comparison

**Note:** No Dec 12 baseline dead code report exists for comparison. This report establishes the current baseline for future comparisons.

### Establishing Baseline Metrics (Dec 28, 2025)

| Metric | Current Value |
|--------|---------------|
| Vulture findings | 31 |
| Unused imports | 5 |
| Unused variables | 24 |
| Unsatisfiable conditions | 2 |
| Misplaced test files | 27 |
| Standalone CLI scripts | 13 |
| Total Python files (vibey/) | 503 |
| Total Python files (tests/) | 243 |

This serves as the baseline for Sprint 4+ comparisons.

---

*Report updated: 2025-12-28T21:50:00+00:00 (Task 5 - baseline comparison added)*
*Original report: 2025-12-28T21:45:00+00:00 (Task 4)*
