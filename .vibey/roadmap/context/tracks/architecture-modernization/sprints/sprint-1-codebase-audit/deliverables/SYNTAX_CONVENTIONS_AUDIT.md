# Syntax Conventions Audit Report

**Date:** 2025-12-17
**Task:** Sprint 1, Task 4 - Standardize command syntax across documentation
**Status:** Complete

---

## Executive Summary

Established and enforced consistent command syntax conventions across all documentation. Fixed additional non-existent command references discovered during syntax audit.

| Category | Issues Found | Issues Fixed |
|----------|--------------|--------------|
| Syntax inconsistencies | 0 (already consistent) | N/A |
| Non-existent commands/options | 9 | 9 |
| Outdated command counts | 5 | 5 |
| Files updated | - | 8 |

---

## Syntax Conventions (Established)

The following conventions are now consistently used across all documentation:

### Argument Types

| Pattern | Meaning | Example |
|---------|---------|---------|
| `<arg>` | Required positional argument | `<task-id>`, `<track-id>` |
| `[arg]` | Optional positional argument | `[<commit-sha>]` |
| `--flag` | Required/optional flag | `--verbose`, `--help` |
| `[--flag]` | Optional flag (in syntax docs) | `[--json]` |
| `--option <value>` | Option with value | `--format <format>` |
| `{opt1\|opt2}` | Choice between values | `{tracks\|sprints\|tasks}` |

### Naming Conventions

| Entity | Pattern | Example |
|--------|---------|---------|
| IDs | `<entity-id>` | `<task-id>`, `<sprint-id>`, `<track-id>` |
| Generic ID | `<id>` | Used when entity type is clear from context |
| Files | `<file>` or `<path>` | `--output <file>` |
| Values | Descriptive | `--format <format>`, `--limit <n>` |

---

## Issues Found and Fixed

### Issue 1: Non-existent `--filter` Option (Additional)

**Problem:** REPORTING_AND_STATUS.md still referenced `--filter` after Task 3.

**Files Fixed:**
- `docs/walkthroughs/REPORTING_AND_STATUS.md` (2 occurrences)
- `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md` (1 occurrence)

**Correction:** `vibey roadmap status --filter in_progress` → `vibey roadmap db query progress --by status`

### Issue 2: Non-existent `vibey roadmap history` Command

**Problem:** Documentation referenced `vibey roadmap history` which doesn't exist.

**Correct Command:** `vibey roadmap audit log` (all changes) or `vibey roadmap audit show <id>` (item history)

**Files Fixed:**
- `docs/walkthroughs/REPORTING_AND_STATUS.md` (4 occurrences)
- `docs/walkthroughs/COVERAGE_MATRIX.md` (1 occurrence)

### Issue 3: Non-existent `vibey roadmap get-field` Command

**Problem:** Documentation referenced `vibey roadmap get-field` which doesn't exist.

**Correct Approach:** Use `vibey roadmap show <id>` to view all item details.

**Files Fixed:**
- `docs/walkthroughs/REPORTING_AND_STATUS.md` (3 occurrences)
- `docs/walkthroughs/COVERAGE_MATRIX.md` (1 occurrence)

### Issue 4: Outdated CLI Command Count

**Problem:** Documentation stated "169 CLI commands" but actual count is 203.

**Files Fixed:**
- `CLAUDE.md` (2 occurrences)
- `README.md` (3 occurrences)

---

## Syntax Audit Results

All active documentation files now use consistent syntax:

### Files Verified

| File Category | Files Checked | Status |
|---------------|---------------|--------|
| Reference docs | CLI_REFERENCE.md, MCP_REFERENCE.md, ROADMAP_SYSTEM.md | Consistent |
| Walkthroughs | 8 files | Consistent (after fixes) |
| Journeys | 5 files | Consistent (after fixes) |
| Root docs | README.md, CLAUDE.md | Consistent (after fixes) |

### Auto-Generated Consistency

`CLI_REFERENCE.md` is auto-generated from Click introspection, ensuring:
- 100% accurate command signatures
- Consistent syntax patterns
- No documentation drift

---

## Not Fixed (Lower Priority)

| File Location | Status |
|---------------|--------|
| `docs/roadmap/context/` | Historical sprint context - not updated |
| `docs/archived/` | Archived - intentionally not updated |
| ROADMAP_SYSTEM.md syntax examples | Using valid `[--option]` syntax for optional args |

---

## Verification

```bash
# Verify no more non-existent commands in active docs
grep -rn "roadmap history\|roadmap get-field\|roadmap list-blockers" \
  docs/walkthroughs/ docs/journeys/ docs/reference/
# Result: 0 matches (context dirs excluded)

# Verify CLI count is updated
grep "203" CLAUDE.md README.md | wc -l
# Result: 5 matches
```

---

## Recommendations

### Implemented
1. Syntax conventions documented in this file
2. Non-existent commands fixed in active documentation
3. CLI command count updated across all root documentation

### Future Improvements
1. Add CI check for non-existent commands in documentation
2. Consider adding `vibey docs validate-commands` to check examples
3. Auto-update command count in docs when CLI changes

---

## Related Tasks

- Task 3 (Documentation audit) - Fixed initial `list-blockers` and `--filter` issues
- This task extends that work with comprehensive syntax standardization

---

*Generated as part of Architecture Modernization Track, Sprint 1*
