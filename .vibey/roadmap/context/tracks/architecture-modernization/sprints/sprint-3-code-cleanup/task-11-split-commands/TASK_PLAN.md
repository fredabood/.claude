# Task Plan: Split commands.py into Logical Modules

## Overview

Split the 6190-line `vibey/cli/commands.py` into separate modules organized by command group. This improves maintainability, enables parallel development, and reduces cognitive load.

## Current State

### Commands.py Analysis

| Prefix | Count | Line Range (approx) |
|--------|-------|---------------------|
| roadmap_* | 19 | 52-1630 |
| db_* | 11 | 2957-4236 |
| session_* | 11 | 4869-5393 |
| context_* | 7 | 5742-6190 |
| discover_* | 6 | 5446-5718 |
| config_* | 6 | 2399-2448 |
| checkpoint_* | 6 | 2022-2144 |
| edit_* | 4 | 2144-2373 |
| audit_* | 4 | 2469-2603 |
| create_* | 3 | 229-720 |
| validate_* | 3 | 2791-2874 |
| migrate_* | 4 | 2448-4869 |
| hooks (install/uninstall/check) | 3 | 1836-1924 |
| Other (deploy, docs, activity, etc.) | ~5 | scattered |
| Private helpers (_*) | 14 | scattered |

### Existing Modularization

Already extracted:
- `vibey/cli/roadmap_commands/` - 27 modules with specialized commands
- `vibey/cli/roadmap_lib/` - 18 library modules with shared utilities

## Target Structure

```
vibey/cli/
├── commands/                    # NEW: Command modules directory
│   ├── __init__.py              # Export all command functions
│   ├── roadmap.py               # roadmap_* commands (~1600 lines)
│   ├── db.py                    # db_* commands (~1300 lines)
│   ├── session.py               # session_* commands (~500 lines)
│   ├── context.py               # context_* commands (~450 lines)
│   ├── discover.py              # discover_* commands (~270 lines)
│   ├── checkpoint.py            # checkpoint_* commands (~150 lines)
│   ├── edit.py                  # edit_* commands (~250 lines)
│   ├── config.py                # config_* commands (~50 lines)
│   ├── audit.py                 # audit_* + activity_* commands (~200 lines)
│   ├── validate.py              # validate_* commands (~100 lines)
│   ├── migrate.py               # migrate_* commands (~600 lines)
│   ├── hooks.py                 # install/uninstall/check hooks (~100 lines)
│   ├── deploy.py                # deploy_cmd (~20 lines)
│   ├── docs.py                  # docs_* commands (~20 lines)
│   └── helpers.py               # Shared private helpers (_* functions)
├── commands.py                  # DEPRECATED: Re-exports for backwards compat
├── main.py                      # Click groups (unchanged)
└── ...
```

## Implementation Steps

### Phase 1: Setup & Infrastructure

1. **Create `vibey/cli/commands/` directory structure**
   - Create `__init__.py` with all exports
   - Create empty module files for each command group

2. **Identify shared helpers**
   - List all `_*` private functions used across command groups
   - Determine which belong in `helpers.py` vs staying local

### Phase 2: Extract Command Groups (order by independence)

3. **Extract `checkpoint.py`** (least dependencies, ~150 lines)
   - `checkpoint_create_cmd`, `checkpoint_list_cmd`, `checkpoint_verify_cmd`
   - `checkpoint_restore_cmd`, `checkpoint_clean_cmd`, `checkpoint_compare_cmd`

4. **Extract `hooks.py`** (~100 lines)
   - `install_hooks_cmd`, `uninstall_hooks_cmd`, `check_hooks_cmd`

5. **Extract `config.py`** (~50 lines)
   - `config_show_cmd`, `config_validate_cmd`, `config_generate_cmd`
   - `config_migrate_cmd`, `config_rollback_cmd`, `config_update_cmd`

6. **Extract `deploy.py`** (~20 lines)
   - `deploy_cmd`

7. **Extract `docs.py`** (~20 lines)
   - `docs_generate_cmd`

8. **Extract `edit.py`** (~250 lines)
   - `edit_file_cmd`, `edit_bulk_cmd`, `edit_validate_cmd`, `edit_rollback_cmd`

9. **Extract `validate.py`** (~100 lines)
   - `validate_docs_cmd`, `validate_assets_cmd`, `validate_structure_cmd`

10. **Extract `audit.py`** (~200 lines)
    - `audit_log_cmd`, `audit_show_cmd`, `audit_suspicious_cmd`, `audit_report_cmd`
    - `activity_cmd`

11. **Extract `discover.py`** (~270 lines)
    - `discover_run_cmd`, `discover_show_cmd`, `discover_status_cmd`
    - `discover_history_cmd`, `discover_diff_cmd`, `discover_refresh_cmd`

12. **Extract `context.py`** (~450 lines)
    - `context_init_cmd`, `context_list_cmd`, `context_show_cmd`
    - `context_archive_cmd`, `context_clean_cmd`, `context_export_cmd`
    - `context_search_cmd`

13. **Extract `session.py`** (~500 lines)
    - `session_start_cmd`, `session_end_cmd`, `session_pause_cmd`
    - `session_resume_cmd`, `session_status_cmd`, `session_show_cmd`
    - `session_list_cmd`, `session_report_cmd`, `session_timeline_cmd`
    - `session_export_cmd`, `session_decisions_cmd`

14. **Extract `migrate.py`** (~600 lines)
    - `migrate_to_roadmap_cmd`, `migrate_embedded_tasks_cmd`
    - `extract_embedded_cmd`, `migrate_format_cmd`, `migrate_docs_cmd`
    - Helper: `_count_field_changes`, `_migrate_entity_to_v2`

15. **Extract `db.py`** (~1300 lines)
    - `db_init_cmd`, `db_rebuild_cmd`, `db_dump_cmd`, `db_status_cmd`
    - `db_backup_cmd`, `db_query_blocked_cmd`, `db_query_progress_cmd`
    - `db_query_deps_cmd`, `db_query_stats_cmd`, `db_validate_cmd`, `db_config_cmd`
    - Helpers: `_normalize_status`, `_load_roadmap_to_db_flat`, `_load_roadmap_to_db`

16. **Extract `roadmap.py`** (~1600 lines)
    - All remaining `roadmap_*` and `create_*` commands
    - `reconcile_cmd`, `bulk_complete_sprint_cmd`, `auto_progress_cmd`
    - Helpers: `_slugify`, `_resolve_id`, `_get_roadmap_id`, etc.

### Phase 3: Backwards Compatibility & Cleanup

17. **Update `commands.py` to re-export**
    ```python
    # commands.py - DEPRECATED, use vibey.cli.commands.* directly
    from vibey.cli.commands import *  # noqa: F401, F403

    import warnings
    warnings.warn(
        "vibey.cli.commands is deprecated. Import from vibey.cli.commands.* directly.",
        DeprecationWarning,
        stacklevel=2
    )
    ```

18. **Update `main.py` imports**
    - Change from `from .commands import *` to specific imports from modules

19. **Run tests and verify all commands work**
    - `pytest tests/cli/`
    - Manual CLI smoke tests

20. **Update any external references**
    - Check for imports in other modules
    - Update documentation if needed

## Success Criteria

- [ ] `commands.py` reduced from 6190 lines to <100 lines (re-exports only)
- [ ] All 96 command functions moved to appropriate modules
- [ ] All CLI commands continue to work: `vibey --help` shows all commands
- [ ] All tests pass: `pytest tests/cli/ -v`
- [ ] No import cycles introduced
- [ ] Backwards compatibility maintained via re-exports

## Dependencies

- No blocking dependencies
- Build on existing `roadmap_commands/` and `roadmap_lib/` patterns

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Import cycles | Extract helpers first, use lazy imports if needed |
| Broken tests | Run tests after each module extraction |
| External dependencies | Search for imports and update incrementally |
| Missing exports | Verify `__init__.py` exports all public functions |

## Estimated Complexity

- **Complexity**: Complex
- **Files to create**: 16 new modules
- **Files to modify**: `commands.py`, `main.py`
- **Test coverage**: Existing CLI tests should catch regressions
