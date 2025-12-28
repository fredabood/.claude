# Task 7.4: Update QUALITY_METRICS_BASELINE with Final State - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJVATAXPPTMVV24CF3E5JXY |
| Sprint | Sprint 7: Final Synchronization |
| Type | documentation |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 1,500 |
| Dependencies | Task 7.3 (coverage matrix regeneration) |

## Objective

Capture the final quality metrics after all remediation work is complete, documenting any changes in test coverage, linting results, and type checking from the Sprint 5 baseline.

## Context

This task exists to resolve **artifact drift** in quality metrics:

- QUALITY_METRICS_BASELINE.md was created in Sprint 5
- Remediation work in Sprints 5-6 may have improved metrics
- New code/files in Sprints 4-6 affect overall quality scores

Without this update:
- Quality improvements from remediation would not be captured
- Final audit report would reference stale metrics
- Baseline for future audits would be incorrect

By updating AFTER all remediation, we capture the true quality state.

## Metrics to Capture

### 1. Test Coverage Metrics

```yaml
test_coverage:
  overall: X%
  by_module:
    cli: X%
    operations: X%
    roadmap: X%
    mcp: X%
    adapters: X%
    common: X%
  test_counts:
    total_tests: N
    passed: N
    failed: N
    skipped: N
```

### 2. Static Analysis Metrics

```yaml
static_analysis:
  ruff:
    total_issues: N
    by_category:
      errors: N
      warnings: N
      conventions: N
    issues_per_1k_loc: X
  mypy:
    total_errors: N
    files_checked: N
    files_with_errors: N
    coverage: X%
  vulture:
    dead_code_items: N
    false_positives: N
    confirmed_dead_code: N
```

### 3. Documentation Metrics

```yaml
documentation:
  docstring_coverage:
    overall: X%
    modules: X%
    classes: X%
    functions: X%
    public_apis: X%
  readme_present: boolean
  api_docs_generated: boolean
  changelog_current: boolean
```

### 4. Code Complexity Metrics

```yaml
complexity:
  cyclomatic:
    average: X
    max: X
    files_above_10: N
    files_above_20: N
  maintainability_index:
    average: X
    min: X
    files_below_20: N
  lines_of_code:
    total: N
    python: N
    tests: N
    ratio_test_to_code: X
```

## Implementation Steps

### Step 1: Run Test Coverage Analysis

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Run tests with coverage
pytest tests/ --cov=vibey --cov-report=term-missing --cov-report=json

# Extract coverage summary
python3 -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
    print(f\"Overall coverage: {data['totals']['percent_covered']:.2f}%\")
    for module, info in data['files'].items():
        print(f\"  {module}: {info['summary']['percent_covered']:.2f}%\")
"
```

### Step 2: Run Static Analysis Tools

```bash
# Ruff linting
ruff check vibey/ --output-format=json > ruff_results.json 2>/dev/null || true
python3 -c "
import json
with open('ruff_results.json') as f:
    issues = json.load(f)
    print(f'Ruff issues: {len(issues)}')
"

# MyPy type checking
mypy vibey/ --json-report mypy_report 2>/dev/null || true
python3 -c "
import json
import os
if os.path.exists('mypy_report/json'):
    # Parse mypy JSON report
    pass
print('MyPy analysis complete')
"

# Vulture dead code detection
vulture vibey/ --min-confidence 80 > vulture_results.txt 2>/dev/null || true
wc -l < vulture_results.txt
```

### Step 3: Calculate Documentation Metrics

```bash
# Use interrogate or pydocstyle for docstring coverage
pip install interrogate

# Generate docstring coverage report
interrogate vibey/ -vv --generate-badge .
interrogate vibey/ -f json -o docstring_coverage.json

# Parse results
python3 -c "
import json
with open('docstring_coverage.json') as f:
    data = json.load(f)
    print(f\"Docstring coverage: {data['summary']['coverage']:.2f}%\")
"
```

### Step 4: Calculate Complexity Metrics

```bash
# Use radon for complexity analysis
pip install radon

# Cyclomatic complexity
radon cc vibey/ -a -s --json > complexity_cc.json

# Maintainability index
radon mi vibey/ -s --json > complexity_mi.json

# Raw metrics (LOC)
radon raw vibey/ -s --json > complexity_raw.json

# Parse results
python3 -c "
import json
with open('complexity_cc.json') as f:
    data = json.load(f)
    complexities = []
    for filepath, functions in data.items():
        for func in functions:
            complexities.append(func['complexity'])
    avg = sum(complexities) / len(complexities) if complexities else 0
    print(f'Average cyclomatic complexity: {avg:.2f}')
    print(f'Max complexity: {max(complexities) if complexities else 0}')
"
```

### Step 5: Compare with Sprint 5 Baseline

```bash
# Load Sprint 5 baseline
SPRINT5_BASELINE=".vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-5/outputs/QUALITY_METRICS_BASELINE.md"

# Extract key metrics from Sprint 5 for comparison
# (Manual extraction or scripted parsing)
```

Generate comparison:

```python
def compare_baselines(sprint5_metrics, sprint7_metrics):
    """Compare quality metrics between sprints."""

    comparison = []

    metric_pairs = [
        ('test_coverage.overall', 'Test Coverage'),
        ('static_analysis.ruff.total_issues', 'Ruff Issues'),
        ('static_analysis.mypy.total_errors', 'MyPy Errors'),
        ('documentation.docstring_coverage.overall', 'Docstring Coverage'),
        ('complexity.cyclomatic.average', 'Avg Cyclomatic Complexity'),
    ]

    for metric_path, display_name in metric_pairs:
        sprint5_val = get_nested(sprint5_metrics, metric_path, 'N/A')
        sprint7_val = get_nested(sprint7_metrics, metric_path, 'N/A')

        if isinstance(sprint5_val, (int, float)) and isinstance(sprint7_val, (int, float)):
            delta = sprint7_val - sprint5_val
            trend = 'improved' if delta > 0 else 'declined' if delta < 0 else 'unchanged'
        else:
            delta = 'N/A'
            trend = 'unknown'

        comparison.append({
            'metric': display_name,
            'sprint5': sprint5_val,
            'sprint7': sprint7_val,
            'delta': delta,
            'trend': trend
        })

    return comparison
```

### Step 6: Generate Final QUALITY_METRICS_BASELINE.md

```markdown
# Quality Metrics Baseline - Final (Sprint 7)

**Generated:** [Date]
**Audit Track:** Comprehensive Repository Audit V2
**Sprint:** 7 - Final Synchronization

## Executive Summary

This baseline represents the **final quality state** after completing all audit
and remediation work. Previous baseline was captured in Sprint 5; this update
reflects any improvements from Sprints 5-6 remediation work.

## Test Coverage

| Module | Coverage | Sprint 5 | Delta |
|--------|----------|----------|-------|
| Overall | X% | Y% | +Z% |
| cli | X% | Y% | +Z% |
| operations | X% | Y% | +Z% |
| roadmap | X% | Y% | +Z% |
| mcp | X% | Y% | +Z% |
| adapters | X% | Y% | +Z% |
| common | X% | Y% | +Z% |

### Test Summary

| Metric | Count |
|--------|-------|
| Total Tests | N |
| Passed | N |
| Failed | N |
| Skipped | N |

## Static Analysis

### Ruff Linting

| Metric | Value | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Total Issues | N | M | +/-X |
| Errors | N | M | +/-X |
| Warnings | N | M | +/-X |
| Issues per 1k LOC | X | Y | +/-Z |

### MyPy Type Checking

| Metric | Value | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Total Errors | N | M | +/-X |
| Files Checked | N | M | +/-X |
| Files with Errors | N | M | +/-X |
| Type Coverage | X% | Y% | +/-Z% |

### Vulture Dead Code

| Metric | Value | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Dead Code Items | N | M | +/-X |
| False Positives | N | M | +/-X |
| Confirmed Dead | N | M | +/-X |

## Documentation Quality

| Metric | Value | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Docstring Coverage | X% | Y% | +/-Z% |
| Module Docstrings | X% | Y% | +/-Z% |
| Class Docstrings | X% | Y% | +/-Z% |
| Function Docstrings | X% | Y% | +/-Z% |
| Public API Documented | X% | Y% | +/-Z% |

## Code Complexity

### Cyclomatic Complexity

| Metric | Value | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Average | X | Y | +/-Z |
| Maximum | X | Y | +/-Z |
| Files > 10 | N | M | +/-X |
| Files > 20 | N | M | +/-X |

### Maintainability Index

| Metric | Value | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Average | X | Y | +/-Z |
| Minimum | X | Y | +/-Z |
| Files < 20 (poor) | N | M | +/-X |

### Lines of Code

| Metric | Count | Sprint 5 | Delta |
|--------|-------|----------|-------|
| Total LOC | N | M | +/-X |
| Python Code | N | M | +/-X |
| Test Code | N | M | +/-X |
| Test/Code Ratio | X | Y | +/-Z |

## Remediation Impact

Summary of quality changes from Sprint 5-6 remediation:

| Area | Before (Sprint 5) | After (Sprint 7) | Improvement |
|------|-------------------|------------------|-------------|
| ... | ... | ... | ... |

## Known Issues

[List any known quality issues that remain unresolved]

## Recommendations

Based on final metrics:

1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]
```

### Step 7: Export Machine-Readable Metrics

```yaml
# quality_metrics_final.yaml
metadata:
  generated: "2024-12-28T..."
  sprint: 7
  track: comprehensive-audit-v2

test_coverage:
  overall: X
  by_module: {...}

static_analysis:
  ruff: {...}
  mypy: {...}
  vulture: {...}

documentation: {...}

complexity: {...}

comparison_with_sprint5:
  improved: [list of improved metrics]
  declined: [list of declined metrics]
  unchanged: [list of unchanged metrics]
```

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| QUALITY_METRICS_BASELINE.md | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Final quality baseline |
| quality_metrics_final.yaml | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Machine-readable metrics |
| QUALITY_DELTA_SUMMARY.md | `.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-7/outputs/` | Changes from Sprint 5 |

## Acceptance Criteria

- [ ] Test coverage measured for all modules
- [ ] Ruff linting analysis complete
- [ ] MyPy type checking analysis complete
- [ ] Vulture dead code analysis complete
- [ ] Docstring coverage calculated
- [ ] Code complexity metrics captured
- [ ] Comparison with Sprint 5 baseline documented
- [ ] Delta explained for changed metrics
- [ ] Machine-readable YAML exported
- [ ] Known issues documented
- [ ] Recommendations provided

## Estimated Time

| Activity | Duration |
|----------|----------|
| Run test coverage | 10 minutes |
| Run static analysis (ruff, mypy, vulture) | 15 minutes |
| Calculate documentation metrics | 10 minutes |
| Calculate complexity metrics | 10 minutes |
| Compare with Sprint 5 | 10 minutes |
| Generate QUALITY_METRICS_BASELINE.md | 15 minutes |
| Export YAML and summary | 10 minutes |
| **Total** | **~80 minutes** |

## Notes

- This task depends on Tasks 7.1, 7.2, and 7.3 completing first
- Sprint 5 baseline should be preserved (not overwritten)
- New baseline goes in Sprint 7 outputs
- Some metrics may require tool installation (pytest-cov, interrogate, radon)
- If any tool fails, document as "N/A" and explain
- Metrics may not change significantly if no remediation occurred
- Focus on documenting delta, even if delta is zero
