# Task 5.6: Update QUALITY_METRICS_BASELINE.md - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QT2 |
| Sprint | Sprint 5: Remediation & Reporting |
| Type | documentation |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 2,500 |
| Dependencies | Sprint 3 (Codebase Health Analysis) |

## Objective

Update the QUALITY_METRICS_BASELINE.md document with current measurements from Sprint 3's codebase health analysis. Compare current metrics with the Dec 12 baseline (if available) and document trends.

## Input Requirements

From Sprint 3 outputs:
1. `TEST_COVERAGE_REPORT.md` - pytest coverage results
2. `STATIC_ANALYSIS_REPORT.md` - ruff and mypy results
3. `DEAD_CODE_REPORT.md` - vulture analysis
4. `CODEBASE_HEALTH_SCORECARD.md` - overall health metrics
5. `CLI_TEST_COVERAGE_MATRIX.md` - CLI command test coverage
6. `MCP_TEST_COVERAGE_MATRIX.md` - MCP tool test coverage

## Quality Metrics to Include

### 1. Test Coverage
- Overall coverage percentage
- Coverage by module (cli, operations, roadmap, mcp)
- Lines covered vs total lines
- Branch coverage (if available)

### 2. Static Analysis (Linting)
- Ruff issue count by severity
- Ruff issue count by rule category
- Clean code percentage

### 3. Type Checking
- Mypy error count
- Type hint coverage percentage
- Modules with full type coverage

### 4. Documentation Coverage
- Docstring coverage for public APIs
- README completeness
- Inline comment density

### 5. Code Complexity
- Cyclomatic complexity average
- Files exceeding complexity threshold
- Function length distribution

### 6. Dead Code
- Unused functions/classes count
- Unused variables count
- Orphaned files count

## Implementation Steps

### Step 1: Gather Current Metrics

#### Test Coverage
```bash
# Run pytest with coverage
pytest tests/ --cov=vibey --cov-report=term-missing --cov-report=json

# Extract metrics
python3 -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
print(f\"Overall: {data['totals']['percent_covered']:.1f}%\")
print(f\"Lines: {data['totals']['covered_lines']}/{data['totals']['num_statements']}\")
"
```

#### Static Analysis (Ruff)
```bash
# Run ruff and count issues
ruff check vibey/ --statistics

# Get JSON output for detailed analysis
ruff check vibey/ --output-format=json > ruff_results.json

# Count by severity
python3 -c "
import json
with open('ruff_results.json') as f:
    issues = json.load(f)
print(f'Total issues: {len(issues)}')
"
```

#### Type Checking (Mypy)
```bash
# Run mypy
mypy vibey/ --ignore-missing-imports --show-error-codes 2>&1 | tee mypy_results.txt

# Count errors
grep -c "error:" mypy_results.txt
```

#### Dead Code (Vulture)
```bash
# Run vulture
vulture vibey/ --min-confidence 80 > vulture_results.txt

# Count findings
wc -l vulture_results.txt
```

### Step 2: Calculate Documentation Coverage

```python
#!/usr/bin/env python3
"""Calculate docstring coverage."""

import ast
from pathlib import Path

def check_docstrings(directory: str):
    """Count functions/classes with and without docstrings."""

    total_public = 0
    with_docstring = 0

    for py_file in Path(directory).rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue

        try:
            with open(py_file) as f:
                tree = ast.parse(f.read())
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private items
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue

                total_public += 1
                if ast.get_docstring(node):
                    with_docstring += 1

    coverage = (with_docstring / total_public * 100) if total_public > 0 else 0
    return {
        'total_public_items': total_public,
        'with_docstrings': with_docstring,
        'coverage_percent': round(coverage, 1)
    }

if __name__ == '__main__':
    result = check_docstrings('vibey/')
    print(f"Public items: {result['total_public_items']}")
    print(f"With docstrings: {result['with_docstrings']}")
    print(f"Coverage: {result['coverage_percent']}%")
```

### Step 3: Calculate Complexity Metrics

```bash
# Using radon for complexity (install if needed: pip install radon)
radon cc vibey/ -a -s

# Maintainability index
radon mi vibey/ -s

# Raw metrics
radon raw vibey/ -s
```

### Step 4: Compile Baseline Document

```markdown
# Quality Metrics Baseline

**Last Updated**: December 28, 2024
**Baseline Reference**: December 12, 2024 (User Journey Audit)

## Executive Summary

| Category | Current | Target | Status |
|----------|---------|--------|--------|
| Test Coverage | XX% | 75% | On/Off Track |
| Type Coverage | XX% | 80% | On/Off Track |
| Lint Score | XX% clean | 95% | On/Off Track |
| Doc Coverage | XX% | 70% | On/Off Track |
| Dead Code | XX items | <50 | On/Off Track |

## Detailed Metrics

### 1. Test Coverage

#### Overall Coverage
| Metric | Dec 12 | Dec 28 | Change | Target |
|--------|--------|--------|--------|--------|
| Line Coverage | ?% | XX% | +/-X% | 75% |
| Branch Coverage | ?% | XX% | +/-X% | 70% |

#### Coverage by Module
| Module | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| vibey/cli | ?% | XX% | +/-X% |
| vibey/operations | ?% | XX% | +/-X% |
| vibey/roadmap | ?% | XX% | +/-X% |
| vibey/mcp | ?% | XX% | +/-X% |
| vibey/common | ?% | XX% | +/-X% |
| vibey/adapters | ?% | XX% | +/-X% |

#### Test Health
| Metric | Count |
|--------|-------|
| Total Tests | XXX |
| Passing | XXX |
| Failing | X |
| Skipped | X |
| Slow Tests (>1s) | X |

### 2. Static Analysis (Linting)

#### Ruff Results
| Category | Dec 12 | Dec 28 | Change |
|----------|--------|--------|--------|
| Total Issues | ? | XX | +/-X |
| Errors (E) | ? | X | +/-X |
| Warnings (W) | ? | X | +/-X |
| Style (S) | ? | X | +/-X |
| Complexity (C) | ? | X | +/-X |

#### Issue Breakdown
| Rule Code | Description | Count |
|-----------|-------------|-------|
| E501 | Line too long | X |
| F401 | Unused import | X |
| ... | ... | X |

### 3. Type Checking (Mypy)

#### Mypy Results
| Metric | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| Total Errors | ? | XX | +/-X |
| Type Errors | ? | XX | +/-X |
| Import Errors | ? | X | +/-X |

#### Type Coverage by Module
| Module | Typed Functions | Total | Coverage |
|--------|-----------------|-------|----------|
| cli | XX | XX | XX% |
| operations | XX | XX | XX% |
| roadmap | XX | XX | XX% |
| mcp | XX | XX | XX% |

### 4. Documentation Coverage

#### Docstring Coverage
| Module | With Docstring | Total Public | Coverage |
|--------|----------------|--------------|----------|
| cli | XX | XX | XX% |
| operations | XX | XX | XX% |
| roadmap | XX | XX | XX% |
| mcp | XX | XX | XX% |
| **Total** | **XXX** | **XXX** | **XX%** |

### 5. Code Complexity

#### Cyclomatic Complexity
| Rating | Files | % of Total |
|--------|-------|------------|
| A (1-5) | XX | XX% |
| B (6-10) | XX | XX% |
| C (11-20) | XX | XX% |
| D (21-30) | X | X% |
| F (31+) | X | X% |

#### Most Complex Functions
| Function | File | Complexity |
|----------|------|------------|
| function_name | file.py | XX |
| ... | ... | ... |

#### Maintainability Index
| Rating | Files | % of Total |
|--------|-------|------------|
| A (20-100) | XX | XX% |
| B (10-19) | XX | XX% |
| C (0-9) | X | X% |

### 6. Dead Code Analysis

#### Vulture Results
| Category | Dec 12 | Dec 28 | Change |
|----------|--------|--------|--------|
| Unused Functions | ? | X | +/-X |
| Unused Classes | ? | X | +/-X |
| Unused Variables | ? | X | +/-X |
| Unused Imports | ? | X | +/-X |
| **Total** | **?** | **XX** | **+/-X** |

## Trends and Analysis

### Improvements Since Dec 12
1. [Improvement 1]
2. [Improvement 2]

### Areas Needing Attention
1. [Area 1] - Current: X%, Target: Y%
2. [Area 2] - Current: X%, Target: Y%

### Recommendations
1. Increase test coverage in vibey/mcp module (currently lowest)
2. Address mypy type errors in cli module
3. Remove identified dead code items
4. Add docstrings to undocumented public APIs

## Monitoring Recommendations

### Weekly Checks
- [ ] Run pytest --cov and verify coverage not decreasing
- [ ] Run ruff check and address new issues

### Monthly Checks
- [ ] Run mypy and review type coverage
- [ ] Run vulture for dead code analysis
- [ ] Update this baseline document

### Quarterly Reviews
- [ ] Full quality audit comparison
- [ ] Update targets based on progress
- [ ] Review complexity trends
```

### Step 5: Generate Comparison Tables

Create comparison with Dec 12 baseline:

```python
#!/usr/bin/env python3
"""Compare current metrics with baseline."""

baseline_dec_12 = {
    'test_coverage': None,  # Fill from original audit if available
    'lint_issues': None,
    'mypy_errors': None,
    'dead_code': None,
    'doc_coverage': None
}

current_dec_28 = {
    'test_coverage': 0,  # Fill with actual
    'lint_issues': 0,
    'mypy_errors': 0,
    'dead_code': 0,
    'doc_coverage': 0
}

def compare_metrics():
    for metric, baseline in baseline_dec_12.items():
        current = current_dec_28[metric]
        if baseline is not None:
            change = current - baseline
            trend = "improved" if change < 0 else "regressed"
            print(f"{metric}: {baseline} -> {current} ({change:+d}, {trend})")
        else:
            print(f"{metric}: {current} (no baseline)")
```

## Validation Checklist

- [ ] Test coverage measured with pytest --cov
- [ ] Ruff static analysis complete
- [ ] Mypy type checking complete
- [ ] Vulture dead code analysis complete
- [ ] Documentation coverage calculated
- [ ] Complexity metrics generated
- [ ] All metrics compared with Dec 12 baseline (where available)
- [ ] QUALITY_METRICS_BASELINE.md updated
- [ ] Trends and recommendations documented

## Deliverables

1. **QUALITY_METRICS_BASELINE.md**
   - All current metrics
   - Comparison with Dec 12 baseline
   - Module-level breakdowns
   - Recommendations

2. **QUALITY_METRICS.yaml**
   - Machine-readable metrics
   ```yaml
   quality_metrics:
     date: 2024-12-28
     baseline_date: 2024-12-12
     test_coverage:
       overall: XX.X
       by_module:
         cli: XX.X
         operations: XX.X
         roadmap: XX.X
         mcp: XX.X
     lint_issues:
       total: XX
       by_severity: {...}
     mypy_errors: XX
     dead_code_items: XX
     doc_coverage: XX.X
   ```

3. **Raw Tool Outputs**
   - coverage.json
   - ruff_results.json
   - mypy_results.txt
   - vulture_results.txt

## Output Location

```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/
```

## Acceptance Criteria

- [ ] All five quality metric categories measured
- [ ] Comparison with Dec 12 baseline documented (or noted as unavailable)
- [ ] Module-level breakdowns included
- [ ] Trends clearly identified
- [ ] Actionable recommendations provided
- [ ] Document is complete and ready for review

## Estimated Time

- Run test coverage: 15 minutes
- Run static analysis: 10 minutes
- Run type checking: 10 minutes
- Run dead code analysis: 10 minutes
- Calculate doc coverage: 15 minutes
- Calculate complexity: 10 minutes
- Compile document: 45 minutes
- Review and validate: 15 minutes
- **Total: ~2 hours**

## Notes

- Dec 12 baseline may not have all metrics - document what's available
- Some metrics may show regression due to new code without tests
- Focus on trends rather than absolute values
- Consider automating metric collection for ongoing monitoring
- Sprint 3 CODEBASE_HEALTH_SCORECARD.md may have pre-computed values
