# CLI Documentation Audit Report

**Date:** 2025-12-17
**Task:** Sprint 1, Task 3 - Update documentation for CLI command variations
**Status:** Complete

---

## Executive Summary

Found and fixed documentation discrepancies between user-facing guides and actual CLI implementation.

| Category | Issues Found | Issues Fixed |
|----------|--------------|--------------|
| Non-existent commands | 1 | 1 |
| Invalid options | 1 | 1 |
| Files updated | - | 8 |

---

## Issues Found and Fixed

### Issue 1: Non-existent Command `list-blockers`

**Problem:** Documentation referenced `vibey roadmap list-blockers` which doesn't exist.

**Correct Command:** `vibey roadmap db query blocked`

**Files Fixed:**
- `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md` (3 occurrences)
- `docs/journeys/JOURNEY_PROJECT_LEAD.md` (5 occurrences)
- `docs/journeys/COVERAGE_MATRIX.md` (1 occurrence)
- `docs/walkthroughs/TROUBLESHOOTING.md` (1 occurrence)
- `docs/walkthroughs/DAILY_WORKFLOW.md` (1 occurrence)
- `docs/walkthroughs/ROADMAP_MANAGEMENT.md` (1 occurrence)
- `docs/walkthroughs/WALKTHROUGH_PROJECT_LEAD.md` (2 occurrences)
- `docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md` (3 occurrences)

### Issue 2: Invalid Option `--filter`

**Problem:** Documentation showed `vibey roadmap status --filter in_progress`

**Finding:** `roadmap status` doesn't have a `--filter` option.

**Correct Alternatives:**
- `vibey roadmap db query progress --by status` (for status breakdown)
- `vibey roadmap status --track <id>` (for specific track)

**Files Fixed:**
- `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md`

---

## Not Fixed (Lower Priority)

The following files contain references to non-existent commands but are in archived or context directories:

| File | Status |
|------|--------|
| `docs/archived/JOURNEY_*.md` | Archived - intentionally not updated |
| `docs/roadmap/context/*/` | Sprint context - historical record |
| `docs/development/ROADMAP_EXAMPLES.md` | May contain hypothetical examples |

---

## Verification

All fixed files now reference only commands that exist in the CLI:

```bash
# Verify list-blockers is not in active docs
grep -rn "list-blockers" docs/walkthroughs/ docs/journeys/ | grep -v archived
# Result: 0 matches
```

---

## Documentation System Observations

1. **CLI_REFERENCE.md** - Auto-generated, always accurate
2. **Walkthroughs/Journeys** - Manually written, prone to drift
3. **Recommendation:** Add CI check for command existence in docs

---

## Related Tasks

- Task 4 (Standardize syntax) should address remaining context files
- Consider adding `vibey docs check-examples` to validate commands in markdown

---

*Generated as part of Architecture Modernization Track, Sprint 1*
