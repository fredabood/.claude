# Documentation Audit Criteria
## Sprint 1.3 - Task 1

**Generated:** 2025-12-12
**Criteria Version:** 1.0
**Track:** User Journey Audit & Documentation Coverage

---

## Overview

This document defines the comprehensive audit criteria used to evaluate all documentation files in the vibey repository. Each documentation file is assessed across 5 primary dimensions, with a composite quality score calculated from weighted sub-scores.

---

## Audit Dimensions

### 1. Completeness (Weight: 20%)

Measures whether the documentation covers all aspects of its subject matter.

| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Topic Coverage | Does the doc cover all aspects of its subject? | 0-25 |
| Feature Coverage | For feature docs, are all features documented? | 0-25 |
| Example Coverage | Are sufficient examples provided? | 0-25 |
| Edge Cases | Are edge cases and error scenarios documented? | 0-25 |

**Scoring Rubric:**

- **100 (A)**: All topics covered, comprehensive examples, edge cases documented
- **80-99 (B)**: Most topics covered, good examples, some edge cases
- **70-79 (C)**: Core topics covered, basic examples, few edge cases
- **60-69 (D)**: Partial coverage, minimal examples, no edge cases
- **<60 (F)**: Major gaps, missing critical information

**YAML Schema:**
```yaml
completeness:
  topic_coverage: complete | partial | minimal
  topics_covered: [list of topics]
  topics_missing: [list of missing topics]
  feature_coverage_percent: float  # 0-100
  examples_provided: true | false
  example_count: int
  edge_cases_documented: true | false
  overall_score: 0-100
```

---

### 2. Correctness (Weight: 30%)

Measures whether the documentation is technically accurate and examples work as shown.

| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Technical Accuracy | Is the information technically correct? | 0-30 |
| Code Examples | Do code examples work when copied? | 0-30 |
| Command Examples | Do CLI commands work as documented? | 0-25 |
| API Accuracy | Do API references match actual implementation? | 0-15 |

**Scoring Rubric:**

- **100 (A)**: All information verified accurate, all examples tested and working
- **80-99 (B)**: Information appears accurate, most examples tested
- **70-79 (C)**: Information mostly accurate, examples not fully tested
- **60-69 (D)**: Some inaccuracies found, examples untested
- **<60 (F)**: Significant errors, examples broken

**YAML Schema:**
```yaml
correctness:
  technical_accuracy: verified | unverified | errors_found
  code_examples_tested: true | false
  code_examples_working: int / int  # working / total
  command_examples_tested: true | false
  command_examples_working: int / int
  api_matches_implementation: true | false | na
  errors_found:
    - location: "line/section"
      description: "error description"
      severity: critical | major | minor
  overall_score: 0-100
```

---

### 3. Currency (Weight: 20%)

Measures whether the documentation reflects the current state of the codebase.

| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Last Updated | When was the doc last updated? | 0-25 |
| Version Alignment | Does it reflect current version? | 0-30 |
| Deprecated Content | Any deprecated features still documented? | 0-25 |
| Stale References | Any references to removed functionality? | 0-20 |

**Scoring Rubric:**

- **100 (A)**: Updated within 30 days, reflects current version, no deprecated content
- **80-99 (B)**: Updated within 60 days, mostly current, minimal deprecated content
- **70-79 (C)**: Updated within 90 days, some outdated info
- **60-69 (D)**: Updated 3-6 months ago, significant outdated content
- **<60 (F)**: Older than 6 months or contains major stale information

**YAML Schema:**
```yaml
currency:
  last_updated: date
  last_verified: date | null
  reflects_current_version: true | false
  deprecated_content:
    present: true | false
    items:
      - feature: "feature name"
        deprecated_in: "version"
        replacement: "new feature" | null
  stale_references:
    present: true | false
    items:
      - reference: "what is referenced"
        status: removed | renamed | moved
  overall_score: 0-100
```

---

### 4. Accessibility (Weight: 15%)

Measures how accessible the documentation is to its target audience.

| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Target Audience | Is content appropriate for stated audience? | 0-25 |
| Structure | Is content well-organized with clear headings? | 0-25 |
| Navigation | Can users find what they need? | 0-25 |
| Prerequisites | Are prerequisites clearly stated? | 0-25 |

**Scoring Rubric:**

- **100 (A)**: Clear audience targeting, excellent structure, easy navigation
- **80-99 (B)**: Good targeting, good structure, navigation mostly clear
- **70-79 (C)**: Adequate targeting, basic structure, navigation OK
- **60-69 (D)**: Unclear audience, poor structure, hard to navigate
- **<60 (F)**: No clear audience, disorganized, difficult to use

**YAML Schema:**
```yaml
accessibility:
  target_audience: [new_users | developers | contributors | operators | admins]
  reading_level: beginner | intermediate | advanced
  structure:
    has_toc: true | false
    clear_headings: true | false
    logical_flow: true | false
    sections_count: int
  prerequisites_stated: true | false
  prerequisites_list: [list of prerequisites]
  navigation:
    internal_links_working: int / int  # working / total
    external_links_working: int / int
    broken_links: [list of broken links]
  overall_score: 0-100
```

---

### 5. Maintainability (Weight: 15%)

Measures how easy the documentation is to maintain and keep current.

| Criterion | Description | Score Range |
|-----------|-------------|-------------|
| Single Source of Truth | Is information duplicated elsewhere? | 0-30 |
| Auto-Generation Potential | Could this be auto-generated? | 0-30 |
| Update Frequency | How often does this need updating? | 0-20 |
| Code Dependencies | What code changes require doc updates? | 0-20 |

**Scoring Rubric:**

- **100 (A)**: Single source of truth, auto-generated, clear dependencies
- **80-99 (B)**: Minimal duplication, can be auto-generated, dependencies documented
- **70-79 (C)**: Some duplication, partial auto-generation possible
- **60-69 (D)**: Significant duplication, manual updates required
- **<60 (F)**: Highly duplicated, maintenance burden, unclear dependencies

**YAML Schema:**
```yaml
maintainability:
  duplicated_elsewhere: true | false
  duplicate_locations: [list of paths]
  auto_generation:
    candidate: true | false
    source: "source of truth for generation" | null
    method: "how to generate" | null
    currently_generated: true | false
  update_frequency: high | medium | low | static
  code_dependencies:
    - file: "path to code file"
      relationship: documents | references | configures
      impact: high | medium | low  # when code changes, how much doc update
  overall_score: 0-100
```

---

## Quality Score Calculation

### Formula

```
Total Score = (Completeness × 0.20) + (Correctness × 0.30) +
              (Currency × 0.20) + (Accessibility × 0.15) +
              (Maintainability × 0.15)
```

### Grading Scale

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A | 90-100 | Excellent - Production quality, exemplary documentation |
| B | 80-89 | Good - Minor improvements needed, solid documentation |
| C | 70-79 | Adequate - Significant improvements needed, usable |
| D | 60-69 | Poor - Major revision required, barely usable |
| F | <60 | Failing - Rewrite required, may mislead users |

### Score Summary Schema

```yaml
quality_score:
  completeness: 0-20       # score × 0.20
  correctness: 0-30        # score × 0.30
  currency: 0-20           # score × 0.20
  accessibility: 0-15      # score × 0.15
  maintainability: 0-15    # score × 0.15
  total: 0-100
  grade: A | B | C | D | F
```

---

## Documentation Categories

### Category-Specific Criteria

Different documentation types have additional criteria:

#### 1. Getting Started / Tutorials
```yaml
getting_started_specific:
  time_to_complete_stated: true | false
  time_to_complete_realistic: true | false
  hands_on_examples: true | false
  progressive_difficulty: true | false
  end_state_clear: true | false
```

#### 2. API/CLI Reference
```yaml
reference_specific:
  coverage_percent: float  # % of API/CLI documented
  signature_accuracy: verified | unverified | errors
  parameter_descriptions: complete | partial | minimal
  return_value_documented: true | false
  error_conditions_documented: true | false
```

#### 3. Conceptual / Architecture
```yaml
conceptual_specific:
  diagrams_included: true | false
  diagrams_current: true | false
  terminology_defined: true | false
  relationships_explained: true | false
```

#### 4. How-To Guides
```yaml
howto_specific:
  goal_stated: true | false
  prerequisites_listed: true | false
  step_by_step: true | false
  verification_steps: true | false
  troubleshooting_included: true | false
```

---

## Complete Audit Output Schema

```yaml
# Per-file audit output
audit_result:
  file: "path/to/file.md"
  size_bytes: int
  lines: int
  purpose: "brief description"
  category: getting_started | reference | conceptual | howto | operations | historical
  target_audience: [list]

  completeness:
    # ... all completeness fields
    overall_score: 0-100

  correctness:
    # ... all correctness fields
    overall_score: 0-100

  currency:
    # ... all currency fields
    overall_score: 0-100

  accessibility:
    # ... all accessibility fields
    overall_score: 0-100

  maintainability:
    # ... all maintainability fields
    overall_score: 0-100

  quality_score:
    completeness: 0-20
    correctness: 0-30
    currency: 0-20
    accessibility: 0-15
    maintainability: 0-15
    total: 0-100
    grade: A | B | C | D | F

  findings:
    - type: critical | major | minor
      category: completeness | correctness | currency | accessibility | maintainability
      description: "description of finding"
      location: "section/line"
      recommendation: "how to fix"

  recommendations:
    immediate: [list of quick fixes]
    short_term: [list of improvements]
    long_term: [list of strategic changes]
```

---

## Audit Process

### Step 1: Initial Assessment
1. Read the document completely
2. Identify purpose and target audience
3. Note document structure

### Step 2: Completeness Check
1. List topics covered
2. Identify missing topics
3. Count examples
4. Check for edge case coverage

### Step 3: Correctness Verification
1. Review technical claims
2. Test code examples (where feasible)
3. Verify command examples
4. Check API/CLI accuracy against implementation

### Step 4: Currency Assessment
1. Check last modified date
2. Compare to current version
3. Identify deprecated content
4. Find stale references

### Step 5: Accessibility Review
1. Assess structure and organization
2. Test navigation and links
3. Verify prerequisites are stated
4. Evaluate reading level

### Step 6: Maintainability Analysis
1. Check for duplication
2. Identify auto-generation candidates
3. Document code dependencies

### Step 7: Score Calculation
1. Score each dimension (0-100)
2. Apply weights
3. Calculate total score
4. Assign grade

### Step 8: Findings and Recommendations
1. List all findings by severity
2. Provide specific recommendations
3. Prioritize improvements

---

## Examples

### Example: High-Quality Documentation (Grade A)

```yaml
file: docs/getting-started/QUICK_START.md
quality_score:
  completeness: 18      # 90 × 0.20
  correctness: 27       # 90 × 0.30
  currency: 19          # 95 × 0.20
  accessibility: 14     # 93 × 0.15
  maintainability: 13   # 87 × 0.15
  total: 91
  grade: A

findings: []  # No significant issues

recommendations:
  short_term:
    - "Consider adding troubleshooting section"
```

### Example: Needs Improvement (Grade D)

```yaml
file: docs/CONFIGURATION.md
quality_score:
  completeness: 12      # 60 × 0.20
  correctness: 18       # 60 × 0.30
  currency: 10          # 50 × 0.20
  accessibility: 10     # 67 × 0.15
  maintainability: 9    # 60 × 0.15
  total: 59
  grade: F

findings:
  - type: critical
    category: currency
    description: "References deprecated config format"
    location: "Section 2.3"
    recommendation: "Update to modular config system"
  - type: major
    category: correctness
    description: "Example config does not work"
    location: "Line 45"
    recommendation: "Fix YAML syntax error"

recommendations:
  immediate:
    - "Fix broken example"
    - "Remove deprecated references"
  short_term:
    - "Rewrite to reflect current config system"
```

---

## Verification Requirements

Before marking Task 1 complete, verify:

- [x] All 5 audit dimensions documented with detailed criteria
- [x] Scoring methodology is clear and objective
- [x] YAML schemas are complete and consistent
- [x] Category-specific criteria defined
- [x] Examples provided at each quality level
- [x] Audit process steps defined
- [x] Output schema is comprehensive

---

## References

- Sprint 1.2: `CORE_LIBRARY_AUDIT_SUMMARY.md` (code audit for cross-reference)
- Sprint 1.1: `FILE_REGISTRY.yaml` (file inventory)
- Sprint 1.1: `DOCS_FILE_CLASSIFICATION.yaml` (documentation file list)
