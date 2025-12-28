# Comprehensive Repository Audit V2 - Track Plan

## Overview

This track combines three objectives:
1. **Refresh User Journey Audit outputs** - Update stale file inventories and documentation from Dec 12-19
2. **Execute Data Integrity Audit** - Validate project state integrity (originally Sprint 33 from CLI Dogfooding)
3. **Re-audit Module Quality** - Update module-level quality audits for all 7 primary categories

## Background

The User Journey Audit track (01KC2D0JKVT80AFQ6C1PA8CKJT) completed on Dec 19, 2024 with comprehensive file classification and documentation. Since then, significant development work has made these outputs stale:
- 141 commits to vibey/ package
- 320 Python files modified
- Database grew from 27 to 39 tables
- New CLI commands and MCP tools added
- Major refactoring (commands.py split, format standardization)

The Data Integrity Audit (originally Sprint 33) was triggered by discovering "Unified Architecture Migration" tasks marked complete but schema changes never executed.

## Option C: Full Parity Implementation

This plan implements Option C (Full Parity) with User Journey Audit outputs:
- **7 Sprints** (up from original 5)
- **52 Tasks** (up from original 30)
- Adds Sprint 1.5 (Module Quality Re-Audit) and Sprint 6 (Friction & Progress Tracking)

## Track Structure

### Sprint 1: File Inventory Refresh (9 tasks)
**Goal:** Update all User Journey Audit file classification outputs

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 1.1 | Scan repository for new files since Dec 12 | research | simple |
| 1.2 | Update FILE_INVENTORY.yaml with new entries | documentation | medium |
| 1.3 | Classify new files by category/subcategory | research | medium |
| 1.4 | Update FILE_REGISTRY.yaml with dependencies | documentation | medium |
| 1.5 | Update FILE_DEPENDENCY_GRAPH.yaml | documentation | complex |
| 1.6 | Generate delta report (files added/removed/moved) | documentation | simple |
| 1.7 | Update VIBEY_FILE_CLASSIFICATION.yaml with new files | documentation | medium |
| 1.8 | Update DOCS and TESTS file classification files | documentation | medium |
| 1.9 | Verify and update CLASSIFICATION_TAXONOMY.md | documentation | simple |

### Sprint 1.5: Module Quality Re-Audit (6 tasks) [NEW]
**Goal:** Update module quality audits to reflect current codebase state

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 1.5.1 | Re-audit CLI module quality (vibey/cli/) | audit | medium |
| 1.5.2 | Re-audit Operations module quality (vibey/operations/) | audit | medium |
| 1.5.3 | Re-audit Roadmap module quality (vibey/roadmap/) | audit | complex |
| 1.5.4 | Re-audit MCP and Adapters modules | audit | medium |
| 1.5.5 | Re-audit Common and Services modules | audit | medium |
| 1.5.6 | Generate cross-module dependency analysis | analysis | complex |

### Sprint 2: Data Integrity Validation (8 tasks)
**Goal:** Validate claimed task completions against actual state

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 2.1 | Audit completed migration tasks against database schema | research | medium |
| 2.2 | Audit completed file creation tasks against filesystem | research | medium |
| 2.3 | Cross-reference Unified Architecture Migration track status | research | complex |
| 2.4 | Audit git history against roadmap task claims | research | medium |
| 2.5 | Audit roadmap state for orphans and broken references | development | medium |
| 2.6 | Audit track/sprint completion status accuracy | research | medium |
| 2.7 | Update DATABASE_SCHEMA_DOCUMENTATION.md | documentation | medium |
| 2.8 | Update FILE_TO_ARTIFACT_MAPPING.yaml | documentation | medium |

### Sprint 3: Codebase Health Analysis (7 tasks)
**Goal:** Assess overall codebase quality and test coverage

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 3.1 | Audit codebase for dead code and orphaned files | research | medium |
| 3.2 | Audit unit test coverage and health | research | medium |
| 3.3 | Run static analysis (ruff, mypy) and catalog issues | research | simple |
| 3.4 | Identify untested CLI commands and MCP tools | research | medium |
| 3.5 | Generate codebase health scorecard | documentation | medium |
| 3.6 | Update SCRIPTS_FILE_CLASSIFICATION.yaml | documentation | simple |
| 3.7 | Update dead code report with new file coverage | documentation | medium |

### Sprint 4: Documentation Sync (8 tasks)
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

### Sprint 5: Remediation & Reporting (9 tasks)
**Goal:** Fix issues found and generate final audit report

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 5.1 | Remediate false completion statuses | development | complex |
| 5.2 | Fix orphan tasks and broken references | development | medium |
| 5.3 | Update stale documentation files | documentation | medium |
| 5.4 | Generate comprehensive audit report | documentation | medium |
| 5.5 | Create ongoing integrity monitoring recommendations | documentation | simple |
| 5.6 | Regenerate AUDIT_PROGRESS_TRACKER.yaml | documentation | simple |
| 5.7 | Update COVERAGE_MATRIX.md with new file counts | documentation | medium |
| 5.8 | Update QUALITY_METRICS_BASELINE.md | documentation | medium |
| 5.9 | Generate comprehensive V2 audit summary report | documentation | complex |

### Sprint 6: Friction & Progress Tracking (5 tasks) [NEW]
**Goal:** Ensure audit outputs remain accurate and maintainable long-term

| Task | Title | Type | Complexity |
|------|-------|------|------------|
| 6.1 | Update FRICTION_LOG.md with current pain points | documentation | simple |
| 6.2 | Validate progress tracking accuracy | validation | medium |
| 6.3 | Document audit automation recommendations | documentation | medium |
| 6.4 | Specify monitoring dashboard requirements | documentation | medium |
| 6.5 | Define audit maintenance cadence and owners | documentation | simple |

## Deliverables

1. **Updated FILE_INVENTORY.yaml** - Complete file classification
2. **Updated FILE_REGISTRY.yaml** - File metadata and dependencies
3. **Updated FILE_DEPENDENCY_GRAPH.yaml** - Import/dependency relationships
4. **Updated *_FILE_CLASSIFICATION.yaml files** - Category-specific classifications
5. **Delta Report** - Changes since last audit (Dec 12-19)
6. **Data Integrity Report** - Validation findings and remediation
7. **Updated DATABASE_SCHEMA_DOCUMENTATION.md** - Current 39-table schema
8. **Updated MODULE_QUALITY_AUDIT_*.md files** - All 7 module categories
9. **CROSS_MODULE_DEPENDENCY_ANALYSIS.md** - Module coupling metrics
10. **Codebase Health Scorecard** - Quality metrics and recommendations
11. **Updated Documentation** - CLI/MCP references, ADRs, user guides
12. **Final Audit Report** - Comprehensive findings and next steps
13. **AUDIT_AUTOMATION_RECOMMENDATIONS.md** - CI/CD integration
14. **AUDIT_MAINTENANCE_SCHEDULE.md** - Ongoing maintenance plan

## Success Criteria

- All file inventories refreshed with 100% coverage
- All 7 module categories re-audited
- All completed tasks validated against actual state
- False completions identified and remediated
- Documentation drift reduced to <5%
- Codebase health score established as baseline
- Audit maintenance process defined and documented

## Dependencies

- User Journey Audit track outputs (context files)
- Git history access
- Database access
- Static analysis tools (ruff, mypy, vulture)

## Estimated Scope

| Sprint | Tasks | Estimated Tokens |
|--------|-------|------------------|
| Sprint 1 | 9 | ~20,000 |
| Sprint 1.5 | 6 | ~18,000 |
| Sprint 2 | 8 | ~25,000 |
| Sprint 3 | 7 | ~17,500 |
| Sprint 4 | 8 | ~20,000 |
| Sprint 5 | 9 | ~22,500 |
| Sprint 6 | 5 | ~15,000 |
| **Total** | **52** | **~138,000** |

## Notes

- Sprint 2 incorporates the original Sprint 33 tasks from CLI Dogfooding track
- Sprint 1.5 ensures module-level audits are current before health analysis
- Sprint 6 ensures sustainable maintenance of audit outputs
- Research tasks can run in parallel within sprints
- Remediation (Sprint 5) depends on findings from Sprints 1-4
- Sprint 6 depends on Sprint 5 completion
