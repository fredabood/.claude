# Friction Log - Dec 12-28, 2025 Development Period

## Overview

This document catalogs development friction points discovered during the Dec 12-28, 2025 development period. Friction points are categorized by severity and resolution status.

**Last Updated**: 2025-12-29
**Track**: Comprehensive Repository Audit V2
**Sprint**: Sprint 6 - Friction & Progress Tracking

---

## Summary

| Severity | Count | Resolved | Unresolved |
|----------|-------|----------|------------|
| Critical | 2 | 1 | 1 |
| High | 5 | 2 | 3 |
| Medium | 4 | 1 | 3 |
| Low | 2 | 0 | 2 |
| **Total** | **13** | **4** | **9** |

---

## Critical Issues

### F001: O(n^2) recalculate_all Performance Bug
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: Performance

**Description**: The `sync_progress` / `recalculate_all` operation has O(n^2) complexity due to nested iteration over sprints and tasks. With 1876 tasks and 295 sprints, this causes significant delays (30-60+ seconds per rebuild).

**Impact**:
- Every CLI command that triggers sync experiences multi-second delays
- Database rebuild operations hang or timeout
- Developer productivity significantly impacted

**Root Cause**: The progress calculation iterates all tasks for each sprint, and all sprints for each track, without caching or indexing.

**Workaround**: Use `--no-sync` flag where available, but this skips critical validation.

**Recommended Fix**:
1. Add indexed task lookups by sprint_id
2. Cache progress calculations
3. Implement incremental updates instead of full recalculation

---

### F002: CLI Startup Failure - Missing Typing Imports
**Status**: RESOLVED (2025-12-29)
**Discovered**: Dec 29, 2025
**Category**: Code Quality

**Description**: The CLI failed to start with `NameError: name 'List' is not defined` in `vibey/cli/git_commands.py:3489`.

**Impact**: Complete CLI unavailability until fixed.

**Root Cause**: Function signature used `List[Dict[str, Any]]` without importing `List`, `Dict`, `Any` from `typing` module.

**Resolution**: Added missing imports: `from typing import Optional, List, Dict, Any`

**Commit**: af2403bf

---

## High Priority Issues

### F003: v2/v1 Format Compatibility Issues
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: Data Format

**Description**: The roadmap system has two YAML formats (v1 and v2) with different field names. The database loader expects v1 fields, but some files are in v2 format.

**Examples**:
- v1 uses `track_id`, v2 uses `parent_ref`
- v1 uses `started`, v2 uses `started_at`
- v1 uses `sprint_id`, v2 uses `parent_ref`

**Impact**:
- Files in v2 format are skipped during database load
- Foreign key constraint failures
- Tasks become orphaned when their sprint isn't loaded

**Recommended Fix**:
1. Standardize on one format
2. Add migration tool to convert between formats
3. Update database loader to handle both formats

---

### F004: create-sprint/create-task Use Slugs Instead of ULIDs
**Status**: Unresolved
**Discovered**: Dec 29, 2025
**Category**: CLI Bug

**Description**: The `create-sprint` and `create-task` commands populate `track_id` and `sprint_id` fields with slug values (e.g., "dogfooding-bugs") instead of ULID values.

**Impact**:
- Created sprints/tasks fail foreign key validation
- Files are skipped during database rebuild
- Manual correction required

**Root Cause**: CLI commands resolve track/sprint by name but write the slug instead of the resolved ULID.

**Recommended Fix**: Update create commands to resolve and use actual ULID values.

---

### F005: Database Rebuild Hangs/Timeouts
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: Performance

**Description**: Database rebuild operations frequently hang or timeout, requiring process termination.

**Impact**:
- Operations take 2+ minutes when they should complete in seconds
- Progress counters may become stale
- Developers must kill and retry operations

**Related To**: F001 (O(n^2) recalculate_all)

---

### F006: Foreign Key Constraint Failures
**Status**: Partially Resolved
**Discovered**: Dec 2025
**Category**: Data Integrity

**Description**: Database rebuild reports foreign key constraint failures, causing files to be skipped.

**Common Errors**:
```
tasks/XXXXX.yaml: Unknown sprint_id: YYYYY
sprints/XXXXX.yaml: FOREIGN KEY constraint failed
```

**Impact**: Data is partially loaded, leading to incomplete roadmap state.

**Root Cause**: Combination of v2/v1 format issues and slug usage in references.

---

### F007: Sprint Status Transition Requirements
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: Workflow

**Description**: Completing a sprint requires it to be in `completion_gate_check` status first, but no clear documentation or tooling exists for transitioning through required states.

**Impact**: Cannot complete sprints using normal CLI workflow.

**Error Message**: `Cannot complete sprint: Sprint must be in completion_gate_check status first`

---

## Medium Priority Issues

### F008: Piped Input Confirmation Problems
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: CLI UX

**Description**: CLI commands that require confirmation don't work correctly when input is piped or in non-interactive mode.

**Impact**: Automation and scripting workflows are blocked.

**Recommended Fix**: Add `--yes` or `--force` flags to bypass confirmation prompts.

---

### F009: Status Command Ignores v2 Format Embedded Data
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: CLI Bug

**Description**: The `roadmap status` command shows "Sprints: 0 complete" for tracks with v2 format even when track YAML has completed sprints embedded.

**Impact**: Misleading status display.

---

### F010: Legacy v2 Format File Warnings
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: Maintenance

**Description**: Database rebuild reports "Found X legacy v2 format file(s)!" with recommendation to run cleanup, but cleanup command behavior is unclear.

**Impact**: Confusing warnings without clear remediation path.

---

### F011: Sprint Tasks Show in Wrong Sprint
**Status**: Unresolved
**Discovered**: Dec 29, 2025
**Category**: Data Integrity

**Description**: When viewing sprint details, tasks from other sprints may appear due to database resolution issues with slug-based references.

**Impact**: Confusing sprint views with incorrect task associations.

---

## Low Priority Issues

### F012: Dirty Flag Always Set After Operations
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: State Management

**Description**: Database shows "Dirty Flag: Yes" after most operations, even when no actual changes occurred.

**Impact**: Unnecessary warnings about uncommitted changes.

---

### F013: Error Log Location Not Obvious
**Status**: Unresolved
**Discovered**: Dec 2025
**Category**: UX

**Description**: Error logs are written to `.vibey/roadmap/rebuild-errors.log` but users may not notice the path in output.

**Impact**: Error details may be missed.

---

## Resolved Issues Log

| ID | Issue | Resolution Date | Resolution |
|----|-------|-----------------|------------|
| F002 | Missing typing imports | 2025-12-29 | Added imports to git_commands.py |
| F006 | FK constraint (partial) | 2025-12-29 | Fixed specific file references |

---

## Recommendations

### Immediate Actions (High Impact, Low Effort)
1. **Add --yes flags** to confirmation prompts for automation support
2. **Standardize on v1 format** for all YAML files
3. **Fix create-sprint/create-task** to use ULIDs instead of slugs

### Short-term Improvements
1. **Index tasks by sprint_id** to improve recalculate_all performance
2. **Add format migration tool** for v2 to v1 conversion
3. **Document sprint lifecycle** and status transitions

### Long-term Improvements
1. **Implement incremental progress updates** instead of full recalculation
2. **Add comprehensive database integrity checks** on startup
3. **Create automated test suite** for CLI commands

---

## Appendix: Related Tracks

- **CLI Dogfooding Bug Fixes** (01KC39XSXJ39N12HWJ93F77KQ9): Contains fixes for many of these issues
- **Sprint 35**: Fixes F002 (Missing Typing Imports)
- **Sprint 33-34**: Address additional status and reconcile bugs
