# Codebase Health Scorecard

**Task:** 01KDJKTRVZS618BM5ZZTQ34437
**Sprint:** Sprint 3 - Codebase Health Analysis
**Generated:** 2025-12-28T21:55:00+00:00

---

## Overall Health Grade: B+

The codebase demonstrates **good overall health** with strong test coverage but opportunities for improvement in static analysis hygiene and MCP tool testing.

---

## Summary Metrics

| Category | Score | Status |
|----------|-------|--------|
| Test Coverage | A | 4,754 tests, 7.6 tests/file |
| Static Analysis | C+ | 6,783 ruff issues, 133 mypy errors |
| Dead Code | B | 31 vulture findings |
| CLI Test Coverage | B+ | 4/18 command groups untested |
| MCP Test Coverage | D | 16% coverage (12/76 tools) |
| Code Organization | B- | 27 misplaced test files |

---

## Detailed Metrics

### Test Suite Health (Grade: A)

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 4,754 | Excellent |
| Test Files | 198 | Good |
| Collection Errors | 1 | Minor issue |
| Skipped/Xfail | 26 (0.5%) | Healthy |
| Test-to-Code Ratio | 7.6 tests/source file | Good |

**Key Findings:**
- Comprehensive test suite with nearly 5,000 tests
- One collection error in `test_directory_migration.py`
- Low skip rate indicates tests are actively maintained

### Static Analysis (Grade: C+)

| Tool | Issues | Priority |
|------|--------|----------|
| Ruff Total | 6,783 | Mixed |
| - F821 (undefined-name) | 53 | High - Runtime errors |
| - F401 (unused-import) | 85 | Medium |
| - F841 (unused-variable) | 71 | Low |
| - Style issues | 6,551 | Low - Auto-fixable |
| Mypy Errors | 133 | Low - Missing stubs |

**Key Findings:**
- 53 potential runtime errors (F821) require immediate attention
- 1,352 issues are auto-fixable with `ruff --fix`
- Most mypy errors are missing type stubs (install `types-PyYAML`)

### Dead Code Analysis (Grade: B)

| Metric | Value |
|--------|-------|
| Vulture Findings | 31 |
| Unused Variables | 24 |
| Unused Imports | 5 |
| Unsatisfiable Conditions | 2 |
| Standalone CLI Scripts | 13 |
| Misplaced Test Files | 27 |

**Key Findings:**
- Low dead code count relative to codebase size
- 27 test files inside `vibey/` should be moved to `tests/`
- 13 standalone CLI scripts need review for consolidation

### CLI Command Coverage (Grade: B+)

| Status | Command Groups |
|--------|----------------|
| Well-Tested | artifact, audit, git, planned, roadmap, session |
| Minimal | config, content, context, deploy, docs, implement, parity |
| **No Tests** | auth, export, submodule, validate |

**Key Findings:**
- 4 command groups have zero test coverage
- `auth` commands are security-critical and need tests

### MCP Tool Coverage (Grade: D)

| Metric | Value |
|--------|-------|
| Total Tools | 76 |
| Tested | 12 (16%) |
| Untested | 64 (84%) |

**Untested by Category:**
- Agent tools: 15
- Handoff tools: 17
- Workflow tools: 16
- Content tools: 7
- Query tools: 4
- Task tools: 4
- Sprint tools: 1

---

## Baseline Metrics (Dec 28, 2025)

| Metric | Baseline |
|--------|----------|
| Python files (vibey/) | 503 |
| Python files (tests/) | 243 |
| Total tests | 4,754 |
| Ruff issues | 6,783 |
| Mypy errors | 133 |
| Vulture findings | 31 |
| CLI commands | ~203 |
| MCP tools | 76 |
| Tested MCP tools | 12 |

---

## Priority Actions

### Immediate (High)

1. **Fix F821 errors** (53 undefined names) - Potential runtime failures
2. **Add auth CLI tests** - Security-critical with no coverage
3. **Fix collection error** in `test_directory_migration.py`

### Short-term (Medium)

4. **Add MCP query tool tests** - Core operations for AI assistants
5. **Move misplaced test files** to tests/ directory
6. **Remove unused imports** (auto-fix with ruff)

### Long-term (Low)

7. **Fix style issues** - Batch with `ruff --fix`
8. **Add MCP agent/workflow tests** - Integration test approach
9. **Consolidate standalone CLI scripts**
10. **Install type stubs** (types-PyYAML)

---

## Health Trend Tracking

This scorecard establishes the baseline for ongoing health monitoring. Recommended tracking:

| Metric | Baseline | Target |
|--------|----------|--------|
| Ruff issues | 6,783 | <5,000 |
| F821 errors | 53 | 0 |
| MCP coverage | 16% | >50% |
| CLI coverage | 78% | >90% |
| Test count | 4,754 | Growing |

---

## Related Reports

| Report | Path |
|--------|------|
| Static Analysis | sprint-3/outputs/STATIC_ANALYSIS_REPORT.md |
| Test Coverage | sprint-3/outputs/TEST_COVERAGE_AUDIT.md |
| CLI/MCP Coverage | sprint-3/outputs/CLI_MCP_COVERAGE_AUDIT.md |
| Dead Code | sprint-3/outputs/DEAD_CODE_AUDIT.md |
| Script Classification | sprint-3/outputs/SCRIPTS_FILE_CLASSIFICATION.yaml |

---

*Report generated: 2025-12-28T21:55:00+00:00*
