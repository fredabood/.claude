# Quality Metrics Baseline

**Task:** 01KDJNKE2B2W5NJRTSRZWN4QT2
**Sprint:** Sprint 5 - Remediation & Reporting
**Generated:** 2025-12-28T23:10:00+00:00

---

## Executive Summary

This document establishes quality metrics baselines from the Comprehensive Repository Audit V2, enabling tracking of improvement over time.

---

## Baseline Metrics (December 28, 2025)

### Test Suite Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Total Tests | 4,754 | Growing |
| Test Files | 198 | - |
| Collection Errors | 1 | 0 |
| Skip Rate | 0.5% | <1% |
| Tests per Source File | 7.6 | >7 |

### Static Analysis Metrics

| Tool | Baseline | Target |
|------|----------|--------|
| Ruff Total Issues | 6,783 | <5,000 |
| F821 (undefined name) | 53 | 0 |
| F401 (unused import) | 85 | <50 |
| F841 (unused variable) | 71 | <50 |
| Style issues | 6,551 | <5,000 |
| Mypy errors | 133 | <100 |

### Dead Code Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Vulture findings | 31 | <20 |
| Unused variables | 24 | <15 |
| Unused imports | 5 | 0 |
| Misplaced test files | 27 | 0 |

### CLI Test Coverage

| Status | Count | Percentage |
|--------|-------|------------|
| Well-tested groups | 6 | 33% |
| Minimal coverage | 8 | 44% |
| No tests | 4 | 22% |

**Untested CLI Command Groups:**
- auth
- export
- submodule
- validate

### MCP Tool Coverage

| Metric | Baseline | Target |
|--------|----------|--------|
| Total Tools | 76 | - |
| Tested | 12 | >50 |
| Coverage | 16% | >50% |

**Untested Tool Categories:**
- Agent tools: 15
- Handoff tools: 17
- Workflow tools: 16
- Content tools: 7

### File Counts

| Category | Baseline |
|----------|----------|
| Python (vibey/) | 503 |
| Python (tests/) | 243 |
| Total Python | 746 |
| CLI Commands | ~203 |
| MCP Tools | 76 |
| Platform Adapters | 11 |
| Database Tables | 33 |

### Roadmap Health

| Metric | Baseline |
|--------|----------|
| Tracks | 53 |
| Sprints | 293 |
| Tasks | 1872 |
| Orphan entities | 0 |
| YAML/DB sync | 100% |
| Documentation drift | 0 files |

---

## Comparison with Original Baseline

### Dec 12 → Dec 28

| Metric | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| Python files | ~724 | 746 | +22 |
| Tests | ~2,681 | 4,754 | +2,073 (+77%) |
| Tracks | 28 | 53 | +25 (+89%) |
| Sprints | ~150 | 293 | +143 (+95%) |
| Tasks | ~900 | 1,872 | +972 (+108%) |
| MCP Tools | 47 | 76 | +29 (+62%) |

**Note:** Original Dec 12 baseline was from User Journey Audit track. Values are approximate.

---

## Grade Summary

| Category | Grade | Notes |
|----------|-------|-------|
| Test Suite | A | 4,754 tests excellent |
| Static Analysis | C+ | 53 F821 errors need fixing |
| Dead Code | B | Low vulture findings |
| CLI Coverage | B+ | 4 untested groups |
| MCP Coverage | D | Only 16% tested |
| Documentation | A | All current |
| Data Integrity | A | No orphans/broken refs |
| **Overall** | **B+** | Good health |

---

## Priority Actions

### Immediate
1. Fix F821 undefined name errors (53 issues)
2. Add auth CLI tests (security-critical)
3. Fix pytest collection error

### Short-term
4. Add MCP query tool tests
5. Move 27 misplaced test files
6. Run `ruff --fix` for auto-fixes

### Long-term
7. Increase MCP coverage to 50%
8. Reduce ruff issues below 5,000
9. Install type stubs (types-PyYAML)

---

## Tracking Schedule

| Frequency | Actions |
|-----------|---------|
| Weekly | Roadmap sync check, orphan detection |
| Monthly | Ruff/mypy counts, test count |
| Quarterly | Full health scorecard regeneration |

---

## Related Documents

| Document | Location |
|----------|----------|
| Codebase Health Scorecard | sprint-3/outputs/CODEBASE_HEALTH_SCORECARD.md |
| Static Analysis Report | sprint-3/outputs/STATIC_ANALYSIS_REPORT.md |
| CLI/MCP Coverage Audit | sprint-3/outputs/CLI_MCP_COVERAGE_AUDIT.md |
| Dead Code Audit | sprint-3/outputs/DEAD_CODE_AUDIT.md |
| Coverage Matrix | docs/journeys/COVERAGE_MATRIX.md |

---

*Baseline established: 2025-12-28T23:10:00+00:00*
