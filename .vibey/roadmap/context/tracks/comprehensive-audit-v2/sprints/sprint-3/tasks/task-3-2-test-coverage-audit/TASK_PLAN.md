# Task 3.2: Audit Unit Test Coverage and Health

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDDE9NEKAH3BM9PRFPHNNCNA |
| Sprint | 3 - Codebase Health Analysis |
| Type | research |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~2,500 |
| Dependencies | None (can run in parallel with other Sprint 3 tasks) |

---

## Objective

Measure comprehensive test coverage across the vibey codebase. Identify modules with insufficient coverage, locate skipped/xfail tests, verify test existence for CLI commands and MCP tools, and compare actual coverage against claims made in completed task documentation.

---

## Commands

### 1. Run Full Coverage Analysis

```bash
# Run pytest with full coverage report
pytest tests/ --cov=vibey --cov-report=term-missing --cov-report=html --cov-report=xml

# Output locations:
# - Terminal: immediate display
# - HTML: htmlcov/index.html (browsable report)
# - XML: coverage.xml (for programmatic analysis)
```

### 2. Coverage by Module

```bash
# CLI module coverage
pytest tests/ --cov=vibey/cli --cov-report=term-missing

# Operations module coverage
pytest tests/ --cov=vibey/operations --cov-report=term-missing

# Roadmap module coverage
pytest tests/ --cov=vibey/roadmap --cov-report=term-missing

# MCP module coverage
pytest tests/ --cov=vibey/mcp --cov-report=term-missing

# Adapters module coverage
pytest tests/ --cov=vibey/adapters --cov-report=term-missing

# Common utilities coverage
pytest tests/ --cov=vibey/common --cov-report=term-missing
```

### 3. Test Health Analysis

```bash
# Find skipped tests
pytest tests/ --collect-only -q 2>&1 | grep -E "skip|xfail"

# List all skipped tests with reasons
pytest tests/ -v --collect-only 2>&1 | grep -E "SKIP|XFAIL"

# Find slow tests (top 20)
pytest tests/ --durations=20

# Count total tests
pytest tests/ --collect-only -q 2>&1 | tail -1

# Run tests and show failures
pytest tests/ -x -v --tb=short
```

### 4. Generate Coverage Reports

```bash
# Generate JSON report for analysis
coverage json -o coverage.json

# Generate detailed XML report
coverage xml -o coverage_detailed.xml

# Show files with zero coverage
coverage report --show-missing --skip-covered | head -50
```

---

## Analysis Steps

### Step 1: Run Full Coverage Suite

1. Execute `pytest tests/ --cov=vibey --cov-report=term-missing --cov-report=xml`
2. Capture overall coverage percentage
3. Identify the number of statements covered vs missed

### Step 2: Module-Level Analysis

For each core module, record:

| Module | Statements | Covered | Missing | Coverage % |
|--------|------------|---------|---------|------------|
| vibey/cli | ? | ? | ? | ?% |
| vibey/operations | ? | ? | ? | ?% |
| vibey/roadmap | ? | ? | ? | ?% |
| vibey/mcp | ? | ? | ? | ?% |
| vibey/adapters | ? | ? | ? | ?% |
| vibey/common | ? | ? | ? | ?% |

### Step 3: Identify Zero-Coverage Files

List all files with 0% coverage:

```bash
coverage report --show-missing | grep " 0%"
```

Categorize by:
- **Critical**: Core functionality that must be tested
- **Important**: Secondary features needing tests
- **Low Priority**: Utility code, rarely used paths

### Step 4: Locate Skipped/XFail Tests

1. Count skipped tests
2. Document skip reasons
3. Identify tests marked xfail and their status

| Test | Skip/XFail | Reason | Added Date |
|------|------------|--------|------------|
| test_example | skip | Pending feature | 2024-12-01 |

### Step 5: Verify CLI Command Test Coverage

Cross-reference CLI_REFERENCE.md (203 commands) with test files:

```bash
# Count CLI test files
ls tests/cli/*.py | wc -l

# Check for command-specific tests
grep -r "def test_" tests/cli/ | wc -l
```

### Step 6: Verify MCP Tool Test Coverage

Cross-reference MCP_REFERENCE.md (76 tools) with test files:

```bash
# Count MCP test files
ls tests/mcp/*.py 2>/dev/null | wc -l

# Check for tool-specific tests
grep -r "def test_" tests/mcp/ 2>/dev/null | wc -l
```

### Step 7: Compare with Task Claims

Review completed task documentation for coverage claims:
- Check if claimed "added tests" actually exist
- Verify claimed coverage percentages match actual

---

## Output Format

### TEST_COVERAGE_REPORT.md Structure

```markdown
# Test Coverage Analysis Report

## Executive Summary
- Overall Coverage: X%
- Total Statements: Y
- Covered Statements: Z
- Tests Collected: N
- Tests Passed: N
- Tests Skipped: N
- Tests Failed: N

## Coverage by Module

| Module | Statements | Coverage | Target | Status |
|--------|------------|----------|--------|--------|
| cli | X | Y% | 70% | [OK/BELOW] |
| operations | X | Y% | 80% | [OK/BELOW] |
| roadmap | X | Y% | 75% | [OK/BELOW] |
| mcp | X | Y% | 60% | [OK/BELOW] |
| adapters | X | Y% | 50% | [OK/BELOW] |
| common | X | Y% | 80% | [OK/BELOW] |

## Files with Zero Coverage
| File | Statements | Priority | Notes |
|------|------------|----------|-------|
| vibey/path/file.py | X | Critical | Core feature |

## Files with Low Coverage (<50%)
| File | Coverage | Missing Lines | Priority |
|------|----------|---------------|----------|
| ... | ...      | ...           | ...      |

## Skipped Tests
| Test | File | Reason | Skip Date |
|------|------|--------|-----------|
| ... | ... | ... | ... |

## XFail Tests
| Test | File | Reason | Status |
|------|------|--------|--------|
| ... | ... | ... | [strict/not strict] |

## Slow Tests (>1s)
| Test | Duration | File |
|------|----------|------|
| ... | ...s     | ...  |

## CLI Command Test Coverage
- Total Commands: 203
- Commands with Tests: X
- Commands without Tests: Y
- Coverage: Z%

## MCP Tool Test Coverage
- Total Tools: 76
- Tools with Tests: X
- Tools without Tests: Y
- Coverage: Z%

## Recommendations
1. Priority 1: Add tests for zero-coverage critical files
2. Priority 2: Increase coverage for modules below target
3. Priority 3: Review and resolve skipped tests
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `TEST_COVERAGE_REPORT.md` | `sprint-3/outputs/` | Comprehensive coverage analysis |
| `coverage.xml` | `sprint-3/outputs/` | XML coverage data for tools |
| `coverage.json` | `sprint-3/outputs/` | JSON coverage for programmatic use |
| `htmlcov/` | `sprint-3/outputs/` | Browsable HTML coverage report |

---

## Coverage Targets

Reference targets from SPRINT_PLAN.md:

| Module | Target Coverage | Rationale |
|--------|-----------------|-----------|
| cli | 70% | High user-facing, critical |
| operations | 80% | Core business logic |
| roadmap | 75% | Data integrity important |
| mcp | 60% | External interface |
| adapters | 50% | Platform-specific, harder to test |
| common | 80% | Shared utilities |

---

## Acceptance Criteria

- [ ] Full coverage report generated (`pytest --cov`)
- [ ] Coverage measured for each core module
- [ ] Files with 0% coverage identified and categorized
- [ ] Skipped/xfail tests documented with reasons
- [ ] Slow tests (>1s) identified
- [ ] CLI command test coverage calculated
- [ ] MCP tool test coverage calculated
- [ ] Coverage compared against module targets
- [ ] Priority list generated for adding new tests

---

## Notes

- Coordinate with Task 3.4 (untested CLI/MCP) for detailed gap analysis
- Test results feed into Task 3.5 (health scorecard)
- If tests fail, document failures but continue coverage analysis
- Consider both unit and integration test coverage
