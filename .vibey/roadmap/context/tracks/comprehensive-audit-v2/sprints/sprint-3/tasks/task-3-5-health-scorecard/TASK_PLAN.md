# Task 3.5: Generate Codebase Health Scorecard

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJKTRVZS618BM5ZZTQ34437 |
| Sprint | 3 - Codebase Health Analysis |
| Type | documentation |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~3,000 |
| Dependencies | Tasks 3.1, 3.2, 3.3, 3.4 (compile all metrics) |

---

## Objective

Compile all health metrics from Sprint 3 tasks into a comprehensive, weighted scorecard. Establish a quantitative baseline for ongoing codebase health monitoring, enabling trend analysis and regression detection in future audits.

---

## Commands

### 1. Gather Coverage Data

```bash
# Get overall coverage percentage
coverage report | tail -1

# Get coverage JSON for programmatic analysis
coverage json -o coverage_summary.json
```

### 2. Count Static Analysis Issues

```bash
# Count ruff issues
ruff check vibey/ --output-format=json 2>/dev/null | python -c "import json,sys; print(len(json.load(sys.stdin)))"

# Count mypy issues
mypy vibey/ --ignore-missing-imports 2>&1 | grep -E "^vibey/" | wc -l

# Get ruff statistics by rule
ruff check vibey/ --statistics 2>/dev/null | head -20
```

### 3. Count Dead Code Items

```bash
# Count vulture findings
vulture vibey/ --min-confidence 80 2>/dev/null | wc -l

# Count orphaned files (from Task 3.1 output)
wc -l < ORPHANED_FILES_LIST.txt
```

### 4. Count Untested Items

```bash
# From Task 3.4 outputs
grep -c "Untested" CLI_TEST_COVERAGE_MATRIX.md
grep -c "Untested" MCP_TEST_COVERAGE_MATRIX.md
```

### 5. Measure Codebase Size

```bash
# Total Python lines
find vibey/ -name "*.py" -exec wc -l {} + | tail -1

# Total test lines
find tests/ -name "*.py" -exec wc -l {} + | tail -1

# File count
find vibey/ -name "*.py" | wc -l
```

---

## Analysis Steps

### Step 1: Collect All Metrics

Gather data from Sprint 3 task outputs:

| Metric Source | Task | Data File |
|---------------|------|-----------|
| Dead code count | 3.1 | DEAD_CODE_REPORT.md |
| Orphaned files | 3.1 | ORPHANED_FILES_LIST.txt |
| Test coverage | 3.2 | TEST_COVERAGE_REPORT.md |
| Static analysis issues | 3.3 | STATIC_ANALYSIS_REPORT.md |
| Untested CLI commands | 3.4 | CLI_TEST_COVERAGE_MATRIX.md |
| Untested MCP tools | 3.4 | MCP_TEST_COVERAGE_MATRIX.md |

### Step 2: Calculate Weighted Scores

**Scoring Formula:**

```
Overall Score = Sum(Metric Score * Weight) / 100

Where each metric is scored 0-100:
- Test Coverage: Actual percentage
- Type Coverage: % of files with type hints
- Linting Score: 100 - (issues / statements * 100)
- Dead Code: 100 - (dead items / total items * 100)
- Documentation: % of public APIs documented
- Complexity: Based on average cyclomatic complexity
```

**Weight Distribution:**

| Metric | Weight | Rationale |
|--------|--------|-----------|
| Test Coverage | 25% | Core quality indicator |
| Linting Score | 20% | Code style and potential bugs |
| Type Coverage | 15% | Maintainability |
| Dead Code Cleanliness | 15% | Code hygiene |
| Documentation | 15% | Usability and maintainability |
| Complexity | 10% | Code understandability |

### Step 3: Score Each Module

Calculate per-module health scores:

| Module | Coverage | Types | Lint | Dead Code | Doc | Complexity | Overall |
|--------|----------|-------|------|-----------|-----|------------|---------|
| cli | ?% | ?% | ?% | ?% | ?% | ? | ? |
| operations | ?% | ?% | ?% | ?% | ?% | ? | ? |
| roadmap | ?% | ?% | ?% | ?% | ?% | ? | ? |
| mcp | ?% | ?% | ?% | ?% | ?% | ? | ? |
| adapters | ?% | ?% | ?% | ?% | ?% | ? | ? |
| common | ?% | ?% | ?% | ?% | ?% | ? | ? |

### Step 4: Identify Critical Issues

Flag issues requiring immediate attention:

- Test coverage below 50%
- Security-related linting issues
- Circular dependencies
- Critical dead code
- Type errors in core modules

### Step 5: Generate Trend Comparison

If Dec 12 baseline available, calculate deltas:

| Metric | Dec 12 | Current | Delta | Trend |
|--------|--------|---------|-------|-------|
| Coverage | X% | Y% | +N% | up arrow |
| Lint Issues | X | Y | -N | down arrow |

### Step 6: Create Recommendations

Prioritize improvements:

1. **Immediate (This Sprint)**: Critical issues
2. **Short-term (Next Sprint)**: High-priority gaps
3. **Medium-term (Q1 2025)**: Technical debt
4. **Long-term (2025)**: Architecture improvements

---

## Output Format

### CODEBASE_HEALTH_SCORECARD.md Structure

```markdown
# Codebase Health Scorecard

**Generated:** [Date]
**Baseline:** Dec 12, 2024
**Sprint:** 3 - Codebase Health Analysis

---

## Overall Score: [Grade] ([Score]/100)

| Grade | Range | Description |
|-------|-------|-------------|
| A+ | 95-100 | Excellent |
| A | 90-94 | Very Good |
| B+ | 85-89 | Good |
| B | 80-84 | Above Average |
| C+ | 75-79 | Average |
| C | 70-74 | Below Average |
| D | 60-69 | Needs Work |
| F | <60 | Critical |

---

## Metric Breakdown

| Metric | Raw Score | Weight | Weighted Score |
|--------|-----------|--------|----------------|
| Test Coverage | X% | 25% | Y |
| Linting Score | X% | 20% | Y |
| Type Coverage | X% | 15% | Y |
| Dead Code Cleanliness | X% | 15% | Y |
| Documentation | X% | 15% | Y |
| Complexity | X | 10% | Y |
| **Total** | | **100%** | **[Score]** |

---

## Module Health

| Module | Coverage | Types | Lint | Dead | Doc | Overall | Grade |
|--------|----------|-------|------|------|-----|---------|-------|
| cli | X% | X% | X% | X% | X% | X | C+ |
| operations | X% | X% | X% | X% | X% | X | B |
| roadmap | X% | X% | X% | X% | X% | X | B- |
| mcp | X% | X% | X% | X% | X% | X | C |
| adapters | X% | X% | X% | X% | X% | X | C- |
| common | X% | X% | X% | X% | X% | X | B+ |

---

## Key Metrics Summary

### Test Coverage
- Overall: X%
- Statements Covered: Y / Z
- Modules Below Target: [list]

### Dead Code
- Total Items Flagged: X
- True Dead Code: Y
- Orphaned Files: Z

### Static Analysis
- Ruff Issues: X (Y critical, Z warnings)
- Mypy Errors: X

### Untested Interfaces
- CLI Commands without Tests: X / 203 (Y%)
- MCP Tools without Tests: X / 76 (Y%)

### Circular Dependencies
- Count: X
- Critical: Y

---

## Critical Issues

### Severity: Critical (Address Immediately)
1. [Issue with description and location]

### Severity: High (Address This Sprint)
1. [Issue with description and location]

### Severity: Medium (Plan for Next Sprint)
1. [Issue with description and location]

---

## Trends (vs Dec 12 Baseline)

| Metric | Dec 12 | Current | Change | Status |
|--------|--------|---------|--------|--------|
| Test Coverage | X% | Y% | +Z% | improving |
| Lint Issues | X | Y | -Z | improving |
| Dead Code | X | Y | -Z | improving |
| Type Coverage | X% | Y% | +Z% | improving |

---

## Recommendations

### Immediate Actions (P0)
1. [Action with expected impact]

### Short-term (1-2 Sprints)
1. [Action with expected impact]

### Medium-term (Q1 2025)
1. [Action with expected impact]

---

## Monitoring Plan

### Quarterly Health Checks
- Re-run this scorecard quarterly
- Track trends over time
- Set improvement targets

### Automated Monitoring
- Integrate coverage into CI/CD
- Add linting to pre-commit hooks
- Track metrics in dashboards

---

## Appendix: Raw Data Sources

| Report | Location |
|--------|----------|
| Dead Code Report | sprint-3/outputs/DEAD_CODE_REPORT.md |
| Test Coverage Report | sprint-3/outputs/TEST_COVERAGE_REPORT.md |
| Static Analysis Report | sprint-3/outputs/STATIC_ANALYSIS_REPORT.md |
| CLI Test Matrix | sprint-3/outputs/CLI_TEST_COVERAGE_MATRIX.md |
| MCP Test Matrix | sprint-3/outputs/MCP_TEST_COVERAGE_MATRIX.md |
```

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `CODEBASE_HEALTH_SCORECARD.md` | `sprint-3/outputs/` | Comprehensive health scorecard |
| `health_metrics.json` | `sprint-3/outputs/` | Machine-readable metrics data |
| `trends_comparison.md` | `sprint-3/outputs/` | Dec 12 vs current comparison (if baseline exists) |

---

## Acceptance Criteria

- [ ] All metrics from Tasks 3.1-3.4 compiled
- [ ] Overall weighted score calculated (0-100)
- [ ] Letter grade assigned (A+ through F)
- [ ] Per-module health scores calculated
- [ ] Critical issues identified and prioritized
- [ ] Trend comparison with Dec 12 baseline (if available)
- [ ] Actionable recommendations provided
- [ ] Quarterly monitoring plan established
- [ ] Scorecard serves as baseline for future audits

---

## Scoring Reference

### Test Coverage Scoring
| Coverage | Score |
|----------|-------|
| 90%+ | 100 |
| 80-89% | 90 |
| 70-79% | 80 |
| 60-69% | 70 |
| 50-59% | 60 |
| 40-49% | 50 |
| <40% | 40 |

### Linting Score Calculation
```
Score = 100 - (issues / statements * 1000)
Minimum score: 0
Maximum score: 100
```

### Dead Code Cleanliness
```
Score = 100 - (dead_items / total_items * 100)
```

---

## Notes

- This is the synthesis task that depends on all other Sprint 3 tasks
- The scorecard establishes the official baseline for future comparisons
- Consider automating scorecard generation for CI/CD integration
- Review and refine weights based on team priorities
