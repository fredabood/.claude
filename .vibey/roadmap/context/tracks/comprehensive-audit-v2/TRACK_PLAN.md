# Comprehensive Repository Audit V2 - Track Plan

## Overview

This track combines two objectives:
1. **Refresh User Journey Audit outputs** - Update stale file inventories and documentation from Dec 12-19
2. **Execute Data Integrity Audit** - Validate project state integrity (originally Sprint 33 from CLI Dogfooding)

## Background

The User Journey Audit track (01KC2D0JKVT80AFQ6C1PA8CKJT) completed on Dec 19, 2024 with comprehensive file classification and documentation. Since then, significant development work has made these outputs stale:
- New files added to codebase
- File dependencies changed
- Documentation updated
- Database schema evolved

The Data Integrity Audit (originally Sprint 33) was triggered by discovering "Unified Architecture Migration" tasks marked complete but schema changes never executed.

## Track Structure

### Sprint 1: File Inventory Refresh
**Goal:** Update all User Journey Audit file classification outputs

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 1.1 | Scan repository for new files since Dec 12 | research | simple |
| 1.2 | Update FILE_INVENTORY.yaml with new entries | documentation | medium |
| 1.3 | Classify new files by category/subcategory | research | medium |
| 1.4 | Update FILE_REGISTRY.yaml with dependencies | documentation | medium |
| 1.5 | Update FILE_DEPENDENCY_GRAPH.yaml | documentation | complex |
| 1.6 | Generate delta report (files added/removed/moved) | documentation | simple |

### Sprint 2: Data Integrity Validation
**Goal:** Validate claimed task completions against actual state

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 2.1 | Audit completed migration tasks against database schema | research | medium |
| 2.2 | Audit completed file creation tasks against filesystem | research | medium |
| 2.3 | Cross-reference Unified Architecture Migration track status | research | complex |
| 2.4 | Audit git history against roadmap task claims | research | medium |
| 2.5 | Audit roadmap state for orphans and broken references | development | medium |
| 2.6 | Audit track/sprint completion status accuracy | research | medium |

### Sprint 3: Codebase Health Analysis
**Goal:** Assess overall codebase quality and test coverage

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 3.1 | Audit codebase for dead code and orphaned files | research | medium |
| 3.2 | Audit unit test coverage and health | research | medium |
| 3.3 | Run static analysis (ruff, mypy) and catalog issues | research | simple |
| 3.4 | Identify untested CLI commands and MCP tools | research | medium |
| 3.5 | Generate codebase health scorecard | documentation | medium |

### Sprint 4: Documentation Sync
**Goal:** Update all documentation to reflect current implementation

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 4.1 | Audit documentation accuracy and drift | research | medium |
| 4.2 | Run `vibey docs check-drift` and catalog discrepancies | research | simple |
| 4.3 | Update CLI_REFERENCE.md with new/changed commands | documentation | medium |
| 4.4 | Update MCP_REFERENCE.md with new/changed tools | documentation | medium |
| 4.5 | Update ADRs for recent architectural decisions | documentation | medium |
| 4.6 | Update user journeys with new features | documentation | medium |
| 4.7 | Update walkthroughs with current workflows | documentation | medium |
| 4.8 | Verify CLAUDE.md accuracy against codebase | documentation | simple |

### Sprint 5: Remediation & Reporting
**Goal:** Fix issues found and generate final audit report

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 5.1 | Remediate false completion statuses | development | complex |
| 5.2 | Fix orphan tasks and broken references | development | medium |
| 5.3 | Update stale documentation files | documentation | medium |
| 5.4 | Generate comprehensive audit report | documentation | medium |
| 5.5 | Create ongoing integrity monitoring recommendations | documentation | simple |

## Deliverables

1. **Updated FILE_INVENTORY.yaml** - Complete file classification
2. **Updated FILE_REGISTRY.yaml** - File metadata and dependencies
3. **Updated FILE_DEPENDENCY_GRAPH.yaml** - Import/dependency relationships
4. **Delta Report** - Changes since last audit (Dec 12-19)
5. **Data Integrity Report** - Validation findings and remediation
6. **Codebase Health Scorecard** - Quality metrics and recommendations
7. **Updated Documentation** - CLI/MCP references, ADRs, user guides
8. **Final Audit Report** - Comprehensive findings and next steps

## Success Criteria

- All file inventories refreshed with 100% coverage
- All completed tasks validated against actual state
- False completions identified and remediated
- Documentation drift reduced to <5%
- Codebase health score established as baseline

## Dependencies

- User Journey Audit track outputs (context files)
- Git history access
- Database access
- Static analysis tools (ruff, mypy, vulture)

## Estimated Scope

| Sprint | Tasks | Estimated Tokens |
|--------|-------|------------------|
| Sprint 1 | 6 | ~15,000 |
| Sprint 2 | 6 | ~20,000 |
| Sprint 3 | 5 | ~15,000 |
| Sprint 4 | 8 | ~20,000 |
| Sprint 5 | 5 | ~15,000 |
| **Total** | **30** | **~85,000** |

## Notes

- Sprint 2 incorporates the original Sprint 33 tasks from CLI Dogfooding track
- All sprints can run in parallel for research tasks
- Remediation (Sprint 5) depends on findings from Sprints 1-4
