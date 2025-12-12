# Scripts & Project Configuration Audit Criteria

**Version:** 1.0
**Created:** 2025-12-12
**Track:** User Journey Audit & Documentation Coverage
**Sprint:** Phase 1.5 - Scripts & Project Config Audit

---

## 1. Overview

This document defines the comprehensive audit criteria for evaluating:
1. **Standalone Scripts** - Python scripts in the `scripts/` directory
2. **Project Configuration Files** - Root-level configuration (pyproject.toml, pytest.ini, etc.)

The criteria establish objective measures for code quality, relevance, and actionable recommendations.

---

## 2. Scripts Audit Criteria

### 2.1 Purpose & Relevance Assessment

Evaluates whether a script serves a valid, current purpose in the project.

```yaml
purpose_relevance:
  # Purpose Documentation
  purpose_documented: true | false
  purpose_description: string           # From docstring or comments
  actual_purpose: string                # From code analysis
  purpose_alignment: aligned | misaligned | unclear

  # Relevance Assessment
  still_relevant: true | false | unknown
  relevance_rationale: string

  # Usage Patterns
  usage_frequency: daily | weekly | monthly | rarely | never | unknown
  last_known_use: date | unknown
  user_type: developer | ci_cd | end_user | admin

  # Alternative Availability
  alternatives:
    cli_equivalent: string | null       # e.g., "vibey roadmap migrate"
    library_function: string | null     # e.g., "vibey.operations.roadmap.migrate()"
    external_tool: string | null        # e.g., "alembic migrate"
  has_alternative: true | false

  # Score (0-25, weight: 25%)
  relevance_score: 0-25
```

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 23-25 | Essential, actively used, no alternative exists |
| 18-22 | Useful, regularly used, may have partial alternative |
| 12-17 | Occasionally useful, rarely used, alternatives exist |
| 6-11 | Marginally useful, almost never used, better alternatives exist |
| 0-5 | Not useful, obsolete, or completely duplicated |

### 2.2 Code Quality Assessment

Evaluates the technical quality and maintainability of the script.

```yaml
code_quality:
  # Structure Analysis
  structure:
    total_lines: number
    blank_lines: number
    comment_lines: number
    code_lines: number
    functions_count: number
    classes_count: number
    has_main_block: true | false        # if __name__ == "__main__"

  # Documentation Quality
  documentation:
    module_docstring:
      present: true | false
      quality: comprehensive | adequate | minimal | none
      describes_usage: true | false
      describes_purpose: true | false
    function_docstrings:
      total: number
      documented: number
      coverage_percent: number
    inline_comments:
      count: number
      quality: adequate | sparse | excessive | none
    usage_example:
      present: true | false
      location: docstring | readme | inline | none

  # Error Handling
  error_handling:
    try_except_blocks: number
    specific_exceptions: [list]         # e.g., [FileNotFoundError, ValueError]
    generic_except: number              # Count of bare except or Exception
    error_messages: helpful | cryptic | none
    exit_codes: proper | improper | none
    graceful_failure: true | false

  # Argument Handling
  arguments:
    method: argparse | click | sys.argv | none | hardcoded
    arguments_documented: true | false
    help_text: present | comprehensive | minimal | missing
    validation: present | partial | none

  # Logging & Output
  logging:
    method: logging_module | print | both | none
    output_level: verbose | normal | quiet | none
    progress_indicators: true | false

  # Code Patterns
  patterns:
    uses_pathlib: true | false
    hardcoded_paths: [list]             # Paths that should be configurable
    hardcoded_values: [list]            # Magic numbers/strings
    type_hints: full | partial | none

  # Score (0-30, weight: 30%)
  quality_score: 0-30
```

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 27-30 | Excellent documentation, robust error handling, clean code |
| 21-26 | Good documentation, adequate error handling, maintainable |
| 15-20 | Basic documentation, some error handling, readable |
| 8-14 | Poor documentation, minimal error handling, hard to maintain |
| 0-7 | No documentation, no error handling, spaghetti code |

### 2.3 Integration Potential Assessment

Evaluates whether the script should be integrated into the CLI or library.

```yaml
integration_potential:
  # CLI Migration Assessment
  cli_candidate:
    recommended: true | false
    confidence: high | medium | low
    reason: string
    suggested_command: string | null    # e.g., "vibey roadmap consolidate"
    suggested_subcommand: string | null # e.g., "vibey db migrate"
    command_group: string | null        # e.g., "roadmap", "db", "config"
    migration_effort: low | medium | high
    migration_blockers: [list]

  # Library Integration Assessment
  library_candidate:
    recommended: true | false
    reason: string
    suggested_location: string | null   # e.g., "vibey/operations/roadmap/migrate.py"
    integration_effort: low | medium | high

  # Standalone Justification
  standalone_justified:
    justified: true | false
    reason: string | null               # e.g., "One-time migration script"
    justification_category: one_time | special_permissions | experimental | temporary

  # Dependencies Analysis
  dependencies:
    internal_modules: [list]            # vibey.* imports
    external_packages: [list]           # Third-party imports
    standard_library: [list]            # stdlib imports
    circular_risk: true | false

  # Overlap with Existing Functionality
  overlap_analysis:
    cli_overlap: [list]                 # Existing CLI commands with similar functionality
    library_overlap: [list]             # Existing library functions with similar functionality
    overlap_percent: number             # Estimated percentage of duplicated functionality

  # Score (0-25, weight: 25%)
  integration_score: 0-25               # Higher = more suitable for integration
```

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 23-25 | Perfect CLI candidate, clear command design, low effort |
| 18-22 | Good CLI candidate, needs some adaptation |
| 12-17 | Possible candidate, significant refactoring needed |
| 6-11 | Poor candidate, better as library function or deprecated |
| 0-5 | Not suitable for integration, one-time or deprecated |

### 2.4 Maintenance & Security Assessment

Evaluates maintenance burden and security considerations.

```yaml
maintenance_status:
  # Modification History
  last_modified: date
  modification_count: number            # Git commits touching this file
  authors: [list]
  active_development: true | false

  # Technical Debt
  technical_debt:
    present: true | false
    severity: none | low | medium | high | critical
    items:
      - type: string                    # e.g., "hardcoded_path", "deprecated_api"
        description: string
        location: string                # Line number or function name
        fix_effort: low | medium | high

  # Testing Coverage
  testing:
    has_tests: true | false
    test_file: string | null
    test_coverage: number | unknown     # Percentage
    test_quality: adequate | minimal | none

  # Security Assessment
  security:
    file_operations: [list]             # read, write, delete operations
    database_operations: [list]         # SQL queries, ORM operations
    external_calls: [list]              # HTTP requests, subprocess calls
    environment_access: [list]          # os.environ, config file access
    sensitive_data_handling: true | false
    concerns: [list]                    # Security issues identified
    risk_level: none | low | medium | high | critical

  # Score (0-20, weight: 20%)
  maintenance_score: 0-20
```

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 18-20 | Well-maintained, tested, secure, minimal debt |
| 14-17 | Adequately maintained, some tests, no security issues |
| 10-13 | Maintenance needed, limited tests, minor concerns |
| 5-9 | High maintenance burden, no tests, some security concerns |
| 0-4 | Unmaintained, untested, security risks present |

### 2.5 Overall Script Quality Score

```yaml
overall_quality:
  # Component Scores
  purpose_relevance: 0-25       # Weight: 25%
  code_quality: 0-30            # Weight: 30%
  integration_potential: 0-25   # Weight: 25%
  maintenance_status: 0-20      # Weight: 20%

  # Calculated Total
  total: 0-100

  # Grade Assignment
  grade: A | B | C | D | F

  # Final Recommendation
  recommendation: migrate_to_cli | keep_as_script | deprecate_and_remove | refactor_first
  recommendation_rationale: string
  priority: critical | high | medium | low
```

**Grade Thresholds:**
| Grade | Score Range | Interpretation |
|-------|-------------|----------------|
| A | 90-100 | Excellent - well-designed, useful, well-maintained |
| B | 80-89 | Good - solid script, minor improvements possible |
| C | 70-79 | Acceptable - functional but needs attention |
| D | 60-69 | Poor - significant issues, consider deprecation |
| F | 0-59 | Failing - deprecate or rewrite required |

---

## 3. Project Configuration Audit Criteria

### 3.1 Completeness Assessment

```yaml
completeness:
  # Required vs Optional Fields
  required_fields:
    total: number
    present: number
    missing: [list]
    coverage_percent: number

  optional_fields:
    available: [list]
    used: [list]
    unused: [list]

  # Documentation
  settings_documented: true | false
  documentation_location: inline_comments | external_docs | none

  # Score (0-35, weight: 35%)
  completeness_score: 0-35
```

### 3.2 Correctness Assessment

```yaml
correctness:
  # Syntax Validation
  syntax_valid: true | false
  syntax_errors: [list]

  # Value Validation
  values_valid: true | false
  invalid_values:
    - field: string
      value: any
      issue: string
      expected: string

  # Internal Consistency
  consistency:
    internally_consistent: true | false
    issues: [list]

  # Cross-File Consistency
  cross_file_consistency:
    python_version_consistent: true | false
    versions_by_file: dict              # {file: version}
    package_versions_consistent: true | false
    conflicts: [list]

  # Score (0-40, weight: 40%)
  correctness_score: 0-40
```

### 3.3 Best Practices Assessment

```yaml
best_practices:
  # Standard Compliance
  follows_standard: true | false
  standard_name: string                 # e.g., "PEP 621", "pytest best practices"
  compliance_level: full | partial | none
  deviations: [list]

  # Security
  security:
    sensitive_data_exposed: true | false
    should_be_gitignored: true | false
    concerns: [list]

  # Maintainability
  maintainability:
    easy_to_understand: true | false
    well_organized: true | false
    issues: [list]

  # Modern Practices
  modern_practices:
    uses_modern_format: true | false    # e.g., pyproject.toml vs setup.py
    deprecated_patterns: [list]
    recommended_updates: [list]

  # Score (0-25, weight: 25%)
  best_practices_score: 0-25
```

### 3.4 Overall Configuration Quality Score

```yaml
config_quality:
  # Component Scores
  completeness: 0-35            # Weight: 35%
  correctness: 0-40             # Weight: 40%
  best_practices: 0-25          # Weight: 25%

  # Calculated Total
  total: 0-100

  # Grade Assignment
  grade: A | B | C | D | F

  # Recommendations
  recommendations:
    immediate: [list]           # Fix now
    short_term: [list]          # Fix soon
    long_term: [list]           # Consider for future
```

---

## 4. Decision Framework

### 4.1 CLI Migration Decision Matrix

| Criterion | Migrate to CLI | Keep as Script | Deprecate |
|-----------|----------------|----------------|-----------|
| Usage Frequency | Weekly+ | Monthly or less | Never |
| Has CLI Equivalent | No | Partial | Yes (exact) |
| General Utility | High | Medium | Low/None |
| Migration Effort | Low-Medium | High | N/A |
| User Benefit | Significant | Marginal | None |

### 4.2 Migration Decision Flow

```
START
  │
  ├─ Is script still needed? ─── NO ──> DEPRECATE
  │         │
  │        YES
  │         │
  ├─ Does CLI equivalent exist? ─── YES (exact) ──> DEPRECATE
  │         │
  │        NO / PARTIAL
  │         │
  ├─ Is it used regularly? ─── NO ──> KEEP AS SCRIPT (document)
  │         │
  │        YES
  │         │
  ├─ Is general utility high? ─── NO ──> KEEP AS SCRIPT
  │         │
  │        YES
  │         │
  ├─ Is migration effort reasonable? ─── NO ──> KEEP AS SCRIPT (plan migration)
  │         │
  │        YES
  │         │
  └─────────────────────────────────────> MIGRATE TO CLI
```

### 4.3 Priority Assignment

| Priority | Criteria |
|----------|----------|
| Critical | Security issue, breaking functionality, blocking development |
| High | Frequently used, significant user benefit from migration |
| Medium | Occasionally used, moderate benefit from changes |
| Low | Rarely used, minimal impact from changes |

---

## 5. Output YAML Schema

### 5.1 Individual Script Audit

```yaml
# AUDIT_{SCRIPT_NAME}.yaml
audit:
  file: string                          # Full path
  generated_at: datetime
  criteria_version: "1.0"

  metadata:
    size_bytes: number
    lines: number
    last_modified: date
    executable: boolean
    shebang: present | missing

  purpose_relevance:
    # ... as defined above

  code_quality:
    # ... as defined above

  integration_potential:
    # ... as defined above

  maintenance_status:
    # ... as defined above

  overall_quality:
    # ... as defined above
```

### 5.2 Configuration File Audit

```yaml
# AUDIT_PROJECT_CONFIG.yaml
audit:
  scope: project_configuration_files
  generated_at: datetime
  criteria_version: "1.0"

  files:
    - path: string
      config_type: string               # python_project, testing, coverage, etc.

      completeness:
        # ... as defined above

      correctness:
        # ... as defined above

      best_practices:
        # ... as defined above

      config_quality:
        # ... as defined above

  cross_file_analysis:
    consistency:
      python_version_consistent: boolean
      versions_found: dict
    redundancy:
      duplicated_settings: [list]
    gaps:
      missing_configs: [list]

  summary:
    files_audited: number
    average_quality_score: number
    grade_distribution:
      A: number
      B: number
      C: number
      D: number
      F: number
    critical_issues: [list]
    recommendations: [list]
```

---

## 6. Configuration Files to Audit

| File | Purpose | Config Type |
|------|---------|-------------|
| pyproject.toml | Python project configuration | python_project |
| pytest.ini | Pytest configuration | testing |
| MANIFEST.in | Package distribution manifest | packaging |

**Note:** Additional config files (.coveragerc, .pre-commit-config.yaml, .gitignore) may be present. The audit will cover all root-level configuration files found.

---

## 7. Acceptance Criteria for This Document

- [x] Scripts audit criteria documented with 4 dimensions
- [x] Configuration audit criteria documented with 3 dimensions
- [x] Scoring methodology clearly defined
- [x] YAML schemas provided for all outputs
- [x] Decision framework for CLI migration defined
- [x] Priority assignment criteria defined

---

## 8. References

- Sprint 1.5 Task Plan: SPRINT_PLAN.md
- Sprint 1.2 Output: CORE_LIBRARY_AUDIT_SUMMARY.md (for CLI capability reference)
- Sprint 1.1 Output: FILE_REGISTRY.yaml (for complete file inventory)
