# Test Coverage Audit

**Task:** 01KDDE9NEKAH3BM9PRFPHNNCNA
**Sprint:** Sprint 3 - Codebase Health Analysis
**Generated:** 2025-12-28T21:35:00+00:00

---

## Executive Summary

The test suite is **comprehensive** with 4,754 tests across 198 test files. Test health is good with only 26 skipped/xfail markers and 1 collection error.

---

## Test Suite Metrics

| Metric | Value |
|--------|-------|
| Total Tests Collected | 4,754 |
| Test Files | 198 |
| Collection Errors | 1 |
| Skipped/Xfail Markers | 26 |
| Test-to-Code Ratio | ~7.6 tests per source file |

---

## Test Distribution by Module

| Module | Test Files | Coverage Area |
|--------|------------|---------------|
| cli | 29+ | CLI commands and roadmap_lib |
| integration | 28+ | End-to-end workflows |
| roadmap | 16+ | Roadmap models and serialization |
| mcp | 11+ | MCP server and tools |
| operations | 12+ | Core operations |
| platform | 18+ | Platform configurations |
| adapters | 10+ | Platform adapters |
| common | 6+ | Shared utilities |
| e2e | 8+ | End-to-end tests |
| core | 5+ | Core functionality |
| agents | 5+ | Agent tests |

---

## Collection Errors

### Error 1: test_directory_migration.py
```
ERROR tests/roadmap/serialization/test_directory_migration.py
```
**Action Required:** Fix import or syntax error in this test file.

---

## Pytest Warnings

| Warning | Count | Description |
|---------|-------|-------------|
| PytestCollectionWarning | 4 | Classes with `__init__` named `Test*` |

### Affected Classes
- `TestPassesTarget` in `vibey/roadmap/models/ticket/targets.py`
- `TestRepo` in `tests/utils/repo_builder.py`
- `TestRunValidator` in `vibey/roadmap/standards/validators/test_run.py`

**Recommendation:** Rename non-test classes to avoid `Test` prefix.

---

## Skipped/Xfail Tests (26 total)

These tests are intentionally marked as skipped or expected to fail:
- Some may be placeholders for future functionality
- Some may be failing due to environment issues
- Review to ensure none are hiding real bugs

---

## Coverage Gaps Analysis

### Modules Needing Coverage Review

Based on Sprint 1.5 module audit:

| Module | Files | Lines | Test Files | Gap Risk |
|--------|-------|-------|------------|----------|
| CLI | 123 | 52,159 | 29 | Medium |
| Operations | 115 | 52,236 | 12 | High |
| Services | 46 | 28,649 | ~5 | High |
| Roadmap | 100 | 55,298 | 16 | Medium |

### Recommendations

1. **Operations module** needs more test coverage (12 test files for 115 source files)
2. **Services module** (new) needs comprehensive testing
3. **CLI roadmap_lib** appears well-tested

---

## Test Health Indicators

| Indicator | Status | Notes |
|-----------|--------|-------|
| Tests Run | GOOD | 4,754 tests |
| Collection | WARNING | 1 error |
| Skipped | GOOD | Only 26 (~0.5%) |
| Warnings | LOW | 4 naming warnings |

---

## Recommendations

1. **Fix collection error** in `test_directory_migration.py`
2. **Rename non-test classes** to avoid `Test` prefix
3. **Increase Operations coverage** - critical module with low test ratio
4. **Add Services module tests** - new module with no coverage
5. **Run full coverage report** when collection error is fixed

---

*Report generated: 2025-12-28T21:35:00+00:00*
