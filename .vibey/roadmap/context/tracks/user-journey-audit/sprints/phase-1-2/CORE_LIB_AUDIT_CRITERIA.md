# Core Library Audit Criteria
## Version 1.0

**Created:** 2025-12-12
**Sprint:** Phase 1.2 - Core Library Audit
**Track:** User Journey Audit & Documentation Coverage

---

## Overview

This document defines the comprehensive audit criteria used to evaluate every file in the `vibey/` package. Each file is assessed across five dimensions, with a weighted scoring system that produces an overall quality grade.

---

## 1. Architectural Relevance (25% Weight)

Evaluates how well the file fits within the current system architecture.

### Criteria

| Field | Values | Description |
|-------|--------|-------------|
| `alignment` | `aligned`, `partial`, `misaligned`, `deprecated` | How well the file aligns with current architecture |
| `placement_correct` | `true`, `false` | Is the file in the correct module? |
| `single_responsibility` | `true`, `false` | Does the file have a focused purpose? |
| `layer` | `presentation`, `business_logic`, `data`, `infrastructure` | What architectural layer does it belong to? |

### Scoring

| Score | Criteria |
|-------|----------|
| 25 | Fully aligned, correct placement, single responsibility |
| 20 | Aligned but minor placement or responsibility issues |
| 15 | Partially aligned, some architectural concerns |
| 10 | Misaligned but still functional |
| 5 | Deprecated or scheduled for removal |
| 0 | Should be deleted |

### YAML Schema

```yaml
architectural_relevance:
  alignment: aligned | partial | misaligned | deprecated
  placement_correct: true | false
  single_responsibility: true | false
  layer: presentation | business_logic | data | infrastructure
  notes: string
  score: 0-25
```

---

## 2. Documentation Status (25% Weight)

Evaluates the quality and completeness of documentation.

### Criteria

| Field | Values | Description |
|-------|--------|-------------|
| `module_docstring` | `present`, `missing`, `incomplete` | Does the file have a module-level docstring? |
| `class_docstrings` | count and percentage | Docstring coverage for classes |
| `function_docstrings` | count and percentage | Docstring coverage for functions |
| `type_hints` | `full`, `partial`, `none` | Type annotation coverage |
| `inline_comments` | `adequate`, `sparse`, `none` | Comment quality for complex sections |

### Scoring

| Score | Criteria |
|-------|----------|
| 25 | Module docstring present, 100% class/function docs, full type hints |
| 20 | Module docstring present, >80% coverage, full/partial type hints |
| 15 | Module docstring present, >60% coverage, partial type hints |
| 10 | Missing module docstring or <60% coverage |
| 5 | Minimal documentation |
| 0 | No documentation |

### YAML Schema

```yaml
documentation_status:
  module_docstring: present | missing | incomplete
  class_docstrings:
    total: int
    documented: int
    coverage_percent: float
  function_docstrings:
    total: int
    documented: int
    coverage_percent: float
  type_hints:
    present: true | false
    coverage: full | partial | none
  inline_comments: adequate | sparse | none
  overall_score: 0-100
  score: 0-25
```

---

## 3. Test Coverage (25% Weight)

Evaluates the extent and quality of test coverage.

### Criteria

| Field | Values | Description |
|-------|--------|-------------|
| `has_tests` | `true`, `false` | Does a corresponding test file exist? |
| `test_files` | list of paths | Paths to relevant test files |
| `line_coverage_percent` | 0-100 or null | Percentage of lines covered |
| `branch_coverage_percent` | 0-100 or null | Percentage of branches covered |
| `critical_paths_tested` | `true`, `false`, `unknown` | Are critical code paths tested? |

### Scoring

| Score | Criteria |
|-------|----------|
| 25 | Has tests, >90% line coverage, >80% branch coverage, critical paths tested |
| 20 | Has tests, >75% line coverage, >60% branch coverage |
| 15 | Has tests, >50% line coverage |
| 10 | Has tests but low coverage |
| 5 | Has some tests but significant gaps |
| 0 | No tests |

### YAML Schema

```yaml
test_coverage:
  has_tests: true | false
  test_files: [list of test file paths]
  line_coverage_percent: float | null
  branch_coverage_percent: float | null
  critical_paths_tested: true | false | unknown
  gaps: [list of untested areas]
  score: 0-25
```

---

## 4. Access Patterns (Not Scored - Informational)

Documents how the code is accessed but doesn't contribute to quality score.

### Criteria

| Field | Values | Description |
|-------|--------|-------------|
| `cli_accessible` | `true`, `false` | Is this accessible via CLI commands? |
| `cli_commands` | list | Which CLI commands use this code? |
| `mcp_accessible` | `true`, `false` | Is this accessible via MCP tools? |
| `mcp_tools` | list | Which MCP tools use this code? |
| `internal_only` | `true`, `false` | Is this internal-only code? |
| `entry_points` | list | What are the entry points? |

### YAML Schema

```yaml
access_patterns:
  cli_accessible: true | false
  cli_commands: [list of CLI commands]
  mcp_accessible: true | false
  mcp_tools: [list of MCP tools]
  internal_only: true | false
  entry_points: [list of entry points]
```

---

## 5. Best Practices Compliance (25% Weight)

Evaluates adherence to coding best practices.

### Criteria

| Field | Values | Description |
|-------|--------|-------------|
| `error_handling` | `good`, `adequate`, `poor` | Quality of exception handling |
| `logging` | `appropriate`, `excessive`, `missing` | Logging practices |
| `security_issues` | list or empty | Any security anti-patterns |
| `performance_concerns` | list or empty | Any performance issues |
| `code_style_compliant` | `true`, `false` | Follows project conventions |

### Scoring

| Score | Criteria |
|-------|----------|
| 25 | Good error handling, appropriate logging, no issues, compliant style |
| 20 | Adequate practices with minor issues |
| 15 | Some best practice violations |
| 10 | Multiple violations but functional |
| 5 | Significant best practice issues |
| 0 | Major violations requiring immediate attention |

### YAML Schema

```yaml
best_practices:
  error_handling: good | adequate | poor
  logging: appropriate | excessive | missing
  security_issues: [list or empty]
  performance_concerns: [list or empty]
  code_style_compliant: true | false
  violations: [list of specific violations]
  score: 0-25
```

---

## Quality Score Calculation

### Formula

```
total_score = architectural_relevance.score +
              documentation_status.score +
              test_coverage.score +
              best_practices.score
```

### Grade Mapping

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A | 90-100 | Excellent - Production quality |
| B | 80-89 | Good - Minor improvements needed |
| C | 70-79 | Adequate - Some work needed |
| D | 60-69 | Needs Improvement - Significant work needed |
| F | <60 | Failing - Major issues |

### YAML Schema

```yaml
quality_score:
  architectural_relevance: 0-25
  documentation_status: 0-25
  test_coverage: 0-25
  best_practices: 0-25
  total: 0-100
  grade: A | B | C | D | F
```

---

## Complete File Audit Schema

```yaml
# Template for auditing a single file
file_audit:
  # File identification
  path: string                    # Relative path from repo root
  purpose: string                 # Brief description of file's purpose
  lines: int                      # Line count
  size_bytes: int                 # File size
  last_modified: datetime         # Last modification timestamp

  # Complexity metrics (for Python files)
  complexity_metrics:
    cyclomatic_complexity_avg: float
    cyclomatic_complexity_max: int
    functions: int
    classes: int

  # Audit dimensions
  architectural_relevance:
    alignment: aligned | partial | misaligned | deprecated
    placement_correct: true | false
    single_responsibility: true | false
    layer: presentation | business_logic | data | infrastructure
    notes: string
    score: 0-25

  documentation_status:
    module_docstring: present | missing | incomplete
    class_docstrings:
      total: int
      documented: int
      coverage_percent: float
    function_docstrings:
      total: int
      documented: int
      coverage_percent: float
    type_hints:
      present: true | false
      coverage: full | partial | none
    inline_comments: adequate | sparse | none
    score: 0-25

  test_coverage:
    has_tests: true | false
    test_files: [list]
    line_coverage_percent: float | null
    branch_coverage_percent: float | null
    critical_paths_tested: true | false | unknown
    gaps: [list]
    score: 0-25

  access_patterns:
    cli_accessible: true | false
    cli_commands: [list]
    mcp_accessible: true | false
    mcp_tools: [list]
    internal_only: true | false
    entry_points: [list]

  best_practices:
    error_handling: good | adequate | poor
    logging: appropriate | excessive | missing
    security_issues: [list]
    performance_concerns: [list]
    code_style_compliant: true | false
    violations: [list]
    score: 0-25

  # Quality assessment
  quality_score:
    architectural_relevance: 0-25
    documentation_status: 0-25
    test_coverage: 0-25
    best_practices: 0-25
    total: 0-100
    grade: A | B | C | D | F

  # Findings and recommendations
  findings:
    - type: critical | major | minor | info
      description: string
      location: string
      recommendation: string

  recommendations: [list of actionable items]
```

---

## Module Summary Schema

```yaml
# Template for module-level summary
module_summary:
  module: string                  # Module path (e.g., vibey/cli)
  total_files: int
  total_lines: int

  scores:
    average_quality: float
    min_quality: int
    max_quality: int
    median_quality: int

  grade_distribution:
    A: int
    B: int
    C: int
    D: int
    F: int

  documentation_coverage:
    module_docstrings_percent: float
    function_docstrings_percent: float
    type_hints_percent: float

  test_coverage:
    files_with_tests: string      # "X/Y" format
    average_line_coverage: float
    files_needing_tests: [list]

  critical_findings: [list]
  priority_remediation: [list of ordered actions]
```

---

## Rating Examples

### Grade A Example (Score 95)
```yaml
file_audit:
  path: vibey/roadmap/models/task.py
  quality_score:
    architectural_relevance: 25    # Aligned, correct placement, single purpose
    documentation_status: 23       # Full module doc, 95% function docs, full types
    test_coverage: 22              # 92% line, 85% branch coverage
    best_practices: 25             # Good error handling, clean code
    total: 95
    grade: A
```

### Grade C Example (Score 72)
```yaml
file_audit:
  path: vibey/legacy/old_helper.py
  quality_score:
    architectural_relevance: 15    # Partially aligned, needs refactoring
    documentation_status: 18       # Has module doc, 70% coverage, partial types
    test_coverage: 15              # 55% line coverage, gaps in error paths
    best_practices: 24             # Good practices but minor issues
    total: 72
    grade: C
```

### Grade F Example (Score 45)
```yaml
file_audit:
  path: vibey/temp/scratch.py
  quality_score:
    architectural_relevance: 5     # Deprecated, should be removed
    documentation_status: 10       # Missing module doc, sparse function docs
    test_coverage: 5               # Few tests, many gaps
    best_practices: 25             # Ironically well-written but unused
    total: 45
    grade: F
```

---

## Audit Process

1. **Read the file** - Understand purpose and structure
2. **Check Sprint 1.1 classification** - Reference FILE_REGISTRY.yaml for context
3. **Evaluate each criterion** - Apply scoring consistently
4. **Identify findings** - Document issues found
5. **Generate recommendations** - Prioritize actionable improvements
6. **Calculate quality score** - Sum dimension scores
7. **Assign grade** - Map total to letter grade

---

## References

- Sprint 1.1 outputs: `FILE_REGISTRY.yaml`, `VIBEY_FILE_CLASSIFICATION.yaml`
- CLAUDE.md for project context
- Python best practices: PEP 8, PEP 257, PEP 484
