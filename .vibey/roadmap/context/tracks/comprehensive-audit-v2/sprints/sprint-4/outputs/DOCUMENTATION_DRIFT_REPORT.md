# Documentation Drift Report

**Task:** 01KDJKTRVZS618BM5ZZTQ34438
**Sprint:** Sprint 4 - Documentation Sync
**Generated:** 2025-12-28T22:00:00+00:00

---

## Executive Summary

Documentation drift detected in **2 reference files**. Both CLI and MCP references are out of sync with the current implementation.

---

## Drift Detection Results

### CLI Reference

| Status | File |
|--------|------|
| DRIFT DETECTED | docs/reference/CLI_REFERENCE.md |

**Command to fix:**
```bash
vibey docs generate-cli -o docs/reference/CLI_REFERENCE.md
```

### MCP Reference

| Status | File |
|--------|------|
| DRIFT DETECTED | docs/reference/MCP_REFERENCE.md |

**Command to fix:**
```bash
vibey docs generate-mcp -o docs/reference/MCP_REFERENCE.md
```

---

## Updates Needed

### High Priority
1. Regenerate CLI_REFERENCE.md to match implementation
2. Regenerate MCP_REFERENCE.md to match implementation

### To Verify After Regeneration
3. ADR documents - check for new architectural decisions
4. User journeys - verify workflows are current
5. Walkthroughs - verify step-by-step instructions
6. CLAUDE.md - verify statistics and commands

---

## Resolution Plan

| Step | Action | Task |
|------|--------|------|
| 1 | Run `vibey docs check-drift --fix` | Task 1 |
| 2 | Run `vibey docs check-mcp-drift --fix` | Task 1 |
| 3 | Review generated CLI_REFERENCE.md | Task 3 |
| 4 | Review generated MCP_REFERENCE.md | Task 4 |
| 5 | Update ADRs if needed | Task 5 |
| 6 | Update user journeys | Task 6 |
| 7 | Update walkthroughs | Task 7 |
| 8 | Verify CLAUDE.md | Task 8 |

---

*Report generated: 2025-12-28T22:00:00+00:00*
