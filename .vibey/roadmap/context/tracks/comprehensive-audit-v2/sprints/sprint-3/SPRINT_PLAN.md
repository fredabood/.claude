# Sprint 3: Codebase Health Analysis - Detailed Plan

## Sprint Overview

| Field | Value |
|-------|-------|
| Sprint ID | 01KDJKTRVZS618BM5ZZTQ3442W |
| Track | Comprehensive Repository Audit V2 |
| Status | not_started |
| Tasks | 7 |
| Estimated Tokens | ~17,500 |
| Dependencies | Sprint 1 (File classifications) |

## Goal

Assess overall codebase quality, identify dead code and orphaned files, measure test coverage, and run static analysis tools. Generate a health scorecard establishing baseline metrics for ongoing monitoring.

---

## Task Details

### Task 3.1: Audit Codebase for Dead Code and Orphaned Files

**Task ID:** `01KDDE9NEKAH3BM9PRFPHNNCN9`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Use vulture and custom analysis to identify dead code (unused functions, classes, variables) and orphaned files (not imported anywhere).

#### Implementation Steps

1. **Run vulture dead code analysis**
   ```bash
   # Install vulture if needed
   pip install vulture

   # Run on vibey package
   vulture vibey/ --min-confidence 80 > dead_code_report.txt

   # Run with whitelist for known false positives
   vulture vibey/ --ignore-names "cli_*,test_*" --min-confidence 80
   ```

2. **Analyze vulture output**
   - Categorize by confidence level
   - Identify true dead code vs false positives
   - Note entry points that appear unused

3. **Find orphaned files**
   ```python
   # Files with no imports from other files
   from Sprint 1's FILE_DEPENDENCY_GRAPH.yaml:
   orphaned = [f for f in files if not imported_by[f] and not is_entry_point(f)]
   ```

4. **Generate cleanup recommendations**

#### Deliverables
- `DEAD_CODE_REPORT.md`
- `ORPHANED_FILES_LIST.txt`
- Cleanup recommendations with priority

#### Commands Reference
```bash
# Vulture with sorted output
vulture vibey/ --sort-by-size

# Check specific file
vulture vibey/cli/commands_legacy.py

# Generate whitelist
vulture vibey/ --make-whitelist > whitelist.py
```

---

### Task 3.2: Audit Unit Test Coverage and Health

**Task ID:** `01KDDE9NEKAH3BM9PRFPHNNCNA`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Measure test coverage across the codebase. Identify modules with low coverage and tests that are failing or skipped.

#### Implementation Steps

1. **Run pytest with coverage**
   ```bash
   pytest tests/ --cov=vibey --cov-report=html --cov-report=term-missing

   # Generate XML for analysis
   pytest tests/ --cov=vibey --cov-report=xml
   ```

2. **Analyze coverage by module**
   ```bash
   # Coverage per directory
   pytest tests/ --cov=vibey/cli --cov-report=term
   pytest tests/ --cov=vibey/operations --cov-report=term
   pytest tests/ --cov=vibey/roadmap --cov-report=term
   ```

3. **Identify coverage gaps**
   - Files with 0% coverage
   - Files with <50% coverage
   - Critical paths without tests

4. **Check test health**
   ```bash
   # Find skipped tests
   pytest tests/ --collect-only -q | grep "skip"

   # Find slow tests
   pytest tests/ --durations=20
   ```

#### Deliverables
- `TEST_COVERAGE_REPORT.md`
- Coverage by module breakdown
- Priority list for new tests

#### Coverage Targets
| Module | Current | Target |
|--------|---------|--------|
| cli | ?% | 70% |
| operations | ?% | 80% |
| roadmap | ?% | 75% |
| mcp | ?% | 60% |

---

### Task 3.3: Run Static Analysis and Catalog Issues

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34435`
**Type:** research | **Complexity:** simple | **Priority:** medium

#### Description
Run ruff (linting) and mypy (type checking) to catalog code quality issues.

#### Implementation Steps

1. **Run ruff linter**
   ```bash
   # Run ruff with all rules
   ruff check vibey/ --output-format=json > ruff_report.json

   # Summary by rule
   ruff check vibey/ --statistics

   # Auto-fix safe issues
   ruff check vibey/ --fix --unsafe-fixes
   ```

2. **Run mypy type checker**
   ```bash
   # Run mypy
   mypy vibey/ --ignore-missing-imports > mypy_report.txt

   # With strict mode
   mypy vibey/ --strict --ignore-missing-imports
   ```

3. **Categorize issues**
   - Critical (security, bugs)
   - Important (type errors)
   - Minor (style)

4. **Generate fix priority list**

#### Deliverables
- `STATIC_ANALYSIS_REPORT.md`
- `ruff_issues.json`
- `mypy_issues.txt`
- Priority fix list

---

### Task 3.4: Identify Untested CLI Commands and MCP Tools

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34436`
**Type:** research | **Complexity:** medium | **Priority:** medium

#### Description
Cross-reference CLI commands (203) and MCP tools (76) with test files to identify gaps.

#### Implementation Steps

1. **Extract all CLI commands**
   ```bash
   vibey --help 2>&1 | grep -E "^\s+\w+" > cli_commands.txt

   # Or from code
   grep -r "@click.command\|@click.group" vibey/cli/ | wc -l
   ```

2. **Extract all MCP tools**
   ```python
   # From MCP server registration
   grep -r "@server.tool\|def tool_" vibey/mcp/ | wc -l
   ```

3. **Find corresponding tests**
   ```bash
   # For each command, check if test exists
   for cmd in $(cat cli_commands.txt); do
     if grep -r "test_$cmd\|$cmd" tests/cli/; then
       echo "TESTED: $cmd"
     else
       echo "UNTESTED: $cmd"
     fi
   done
   ```

4. **Generate test gap report**

#### Deliverables
- `CLI_TEST_COVERAGE_MATRIX.md`
- `MCP_TEST_COVERAGE_MATRIX.md`
- Priority list for new tests

---

### Task 3.5: Generate Codebase Health Scorecard

**Task ID:** `01KDJKTRVZS618BM5ZZTQ34437`
**Type:** documentation | **Complexity:** medium | **Priority:** high

#### Description
Compile all metrics from Tasks 3.1-3.4 into a comprehensive health scorecard.

#### Scorecard Template
```markdown
# Codebase Health Scorecard
**Generated:** Dec 28, 2024
**Baseline:** Dec 12, 2024

## Overall Score: B+ (82/100)

### Code Quality Metrics

| Metric | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Test Coverage | 68% | 25% | 17.0 |
| Type Coverage | 45% | 15% | 6.75 |
| Linting Score | 92% | 20% | 18.4 |
| Dead Code | 95% clean | 15% | 14.25 |
| Documentation | 65% | 15% | 9.75 |
| Complexity | Low | 10% | 8.0 |

### Module Health

| Module | Coverage | Types | Lint | Overall |
|--------|----------|-------|------|---------|
| cli | 55% | 40% | 90% | C+ |
| operations | 72% | 50% | 95% | B |
| roadmap | 68% | 55% | 88% | B- |
| mcp | 45% | 35% | 92% | C |

### Critical Issues
1. [Issue 1 with severity]
2. [Issue 2 with severity]

### Recommendations
1. [Priority 1 action]
2. [Priority 2 action]

### Trends (if Dec 12 baseline available)
- Coverage: +5% ↑
- Lint issues: -12% ↓
- Dead code: -3% ↓
```

#### Deliverables
- `CODEBASE_HEALTH_SCORECARD.md`
- Comparison with Dec 12 if available
- Quarterly monitoring recommendations

---

### Task 3.6: Update SCRIPTS_FILE_CLASSIFICATION.yaml

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QSY`
**Type:** documentation | **Complexity:** simple | **Priority:** medium

#### Description
Update the scripts file classification with any new utility, build, or automation scripts added since Dec 12.

#### Implementation Steps

1. **Count current scripts**
   ```bash
   find scripts -name "*.py" -o -name "*.sh" | wc -l
   ```

2. **Compare with classification file**
   - Original: 54 scripts

3. **Add new entries with taxonomy**
   ```yaml
   - path: scripts/audit/dead_code_check.py
     category: SCRIPTS
     subcategory: audit
     purpose: Run vulture dead code analysis
     added: 2024-12-20
   ```

#### Deliverables
- Updated `SCRIPTS_FILE_CLASSIFICATION.yaml`
- Count change documented

---

### Task 3.7: Update Dead Code Report with New File Coverage

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QSZ`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Re-run vulture after file classifications are updated. Compare with original Dec 12 report.

#### Implementation Steps

1. **Run vulture on full codebase**
2. **Compare with Dec 12 baseline (if available)**
3. **Document new dead code introduced**
4. **Document previously flagged code now used**

#### Deliverables
- Updated dead code report
- Before/after comparison
- Recommendations

---

## Sprint Execution Order

```
Task 3.1 (dead code) ──┬──> Task 3.7 (dead code update)
Task 3.2 (coverage)   ─┤
Task 3.3 (static)     ─┼──> Task 3.5 (scorecard)
Task 3.4 (untested)   ─┤
Task 3.6 (scripts)    ─┘
```

## Output Location

```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-3/outputs/
```

## Success Criteria

- [ ] All 7 tasks completed
- [ ] Vulture dead code analysis complete
- [ ] Test coverage measured
- [ ] Static analysis run (ruff, mypy)
- [ ] Health scorecard generated
- [ ] Baseline established for monitoring
