# Test Audit Criteria

## Overview

This document defines the comprehensive audit criteria to be applied to every test file and the test suite as a whole. These criteria ensure consistent, objective assessment of test quality, coverage, and effectiveness.

**Version:** 1.0
**Created:** 2025-12-12
**Sprint:** Phase 1.4 - Test Suite Audit

---

## 1. Test Coverage Criteria

Coverage metrics quantify how much of the source code is exercised by tests.

### 1.1 Line Coverage
- **Definition**: Percentage of source lines executed by tests
- **Measurement**: pytest-cov with --cov-report
- **Target**: 80%+ for production code

### 1.2 Branch Coverage
- **Definition**: Percentage of code branches (if/else/switch) tested
- **Measurement**: pytest-cov with --cov-branch
- **Target**: 70%+ for production code

### 1.3 Function Coverage
- **Definition**: Percentage of functions/methods called by tests
- **Measurement**: Coverage report function analysis
- **Target**: 90%+ for public functions

### 1.4 Module Coverage
- **Definition**: Which modules have associated tests?
- **Measurement**: Test file to source file mapping
- **Target**: Every module with >50 lines should have tests

### Coverage Schema
```yaml
coverage:
  line_coverage_percent: float
  branch_coverage_percent: float
  function_coverage_percent: float
  statements:
    total: int
    covered: int
    missing: int
  branches:
    total: int
    covered: int
    missing: int
  functions:
    total: int
    covered: int
    missing: int
  uncovered_lines: [list of line ranges]
  overall_score: 0-100
```

---

## 2. Test Quality Criteria

Quality metrics assess how well tests are written and maintained.

### 2.1 Test Isolation
- **Definition**: Tests run independently without shared state
- **Assessment**: Check for global state, fixture scope, test order dependencies
- **Red Flags**: Tests that fail when run in isolation, tests that pass only in specific order

### 2.2 Determinism
- **Definition**: Tests produce consistent results on every run
- **Assessment**: Run tests multiple times, check for flaky behavior
- **Red Flags**: Random failures, time-dependent tests, external service dependencies

### 2.3 Speed
- **Definition**: Tests execute fast enough for CI/CD
- **Thresholds**:
  - Unit tests: <100ms each
  - Integration tests: <1s each
  - E2E tests: <10s each
- **Assessment**: pytest --durations output

### 2.4 Clarity
- **Definition**: Test names clearly describe what is being tested
- **Good Pattern**: `test_<function>_<scenario>_<expected_outcome>`
- **Example**: `test_validate_track_with_invalid_id_raises_validation_error`
- **Assessment**: Manual review of naming conventions

### 2.5 Assertions
- **Definition**: Tests have meaningful assertions that verify behavior
- **Metrics**: Assertion density (assertions per test)
- **Red Flags**: Tests with no assertions, tests that only check for no exceptions
- **Target**: At least 1 meaningful assertion per test

### Quality Schema
```yaml
test_quality:
  isolation:
    independent: true | false
    shared_state_issues: [list]
  determinism:
    flaky_tests: [list]
    external_dependencies: [list]
  speed:
    average_duration_ms: float
    slow_tests: [list with durations]
  clarity:
    descriptive_names: true | false
    poorly_named: [list]
  assertions:
    assertion_density: float
    weak_assertions: [list]
  overall_score: 0-100
```

---

## 3. Test Organization Criteria

Organization metrics assess how tests are structured and categorized.

### 3.1 Structure
- **Definition**: Test directory structure mirrors source code structure
- **Expected Pattern**: `tests/unit/cli/` tests `vibey/cli/`
- **Assessment**: Check source-to-test mapping

### 3.2 Naming Conventions
- **Test Files**: `test_<module>.py`
- **Test Classes**: `Test<Class>` (optional)
- **Test Functions**: `test_<function>_<scenario>`
- **Assessment**: Check for convention violations

### 3.3 Categorization
- **Categories**: unit, integration, e2e, fixtures
- **Location Rules**:
  - Unit tests: `tests/unit/`
  - Integration tests: `tests/integration/`
  - E2E tests: `tests/e2e/`
  - Fixtures: `tests/fixtures/`
- **Assessment**: Check test placement correctness

### 3.4 Fixture Organization
- **Definition**: Shared test utilities are reusable and well-organized
- **Expected**: Common fixtures in conftest.py at appropriate scope
- **Assessment**: Check for fixture duplication and reusability

### Organization Schema
```yaml
organization:
  structure:
    mirrors_source: true | false
    orphan_tests: [tests with no corresponding source]
    missing_test_files: [source files without tests]
  naming:
    convention_followed: true | false
    violations: [list]
  categorization:
    unit_tests: int
    integration_tests: int
    e2e_tests: int
    uncategorized: [list]
  fixtures:
    reusable: true | false
    duplicated: [list]
  overall_score: 0-100
```

---

## 4. Test Effectiveness Criteria

Effectiveness metrics assess how well tests catch bugs.

### 4.1 Edge Case Coverage
- **Definition**: Tests cover boundary conditions and edge cases
- **Checklist**:
  - [ ] Empty inputs tested
  - [ ] Null/None values tested
  - [ ] Boundary values tested (0, -1, max, min)
  - [ ] Invalid inputs tested
  - [ ] Large inputs tested

### 4.2 Error Path Coverage
- **Definition**: Tests verify error conditions are handled correctly
- **Checklist**:
  - [ ] Exceptions raised for invalid input
  - [ ] Error messages are meaningful
  - [ ] Recovery paths work correctly
  - [ ] Error codes returned appropriately

### 4.3 Regression Prevention
- **Definition**: Tests prevent previously fixed bugs from recurring
- **Assessment**: Known bugs should have associated regression tests
- **Documentation**: Bug fixes should reference test that prevents recurrence

### 4.4 Mutation Testing (Optional)
- **Definition**: Would tests catch bugs if code was modified?
- **Tool**: mutmut or pytest-mutate
- **Metric**: Mutation score (% of mutants killed)
- **Target**: 70%+ mutation score

### Effectiveness Schema
```yaml
effectiveness:
  mutation_testing:
    available: true | false
    mutation_score: float | null
  edge_cases:
    boundary_values_tested: true | false
    null_handling_tested: true | false
    empty_input_tested: true | false
  error_paths:
    exceptions_tested: true | false
    error_codes_tested: true | false
    recovery_tested: true | false
  regression_prevention:
    known_bugs_with_tests: [list]
    regressions_caught: [list]
  overall_score: 0-100
```

---

## 5. Test Maintainability Criteria

Maintainability metrics assess how easy tests are to maintain.

### 5.1 DRY (Don't Repeat Yourself)
- **Definition**: Test code avoids duplication
- **Assessment**: Check for repeated setup, assertions, data
- **Solution**: Helper functions, fixtures, parameterized tests

### 5.2 Documentation
- **Definition**: Complex tests are documented
- **Requirements**:
  - Complex test logic explained
  - Test purpose clear from name or docstring
  - Magic numbers explained
- **Assessment**: Check for undocumented complex tests

### 5.3 Setup/Teardown
- **Definition**: Test setup and teardown are appropriate
- **Assessment**:
  - Setup not overly complex
  - Teardown cleans up properly
  - Scope is appropriate (function/class/module/session)

### 5.4 Mocking
- **Definition**: Mocking is used appropriately
- **Guidelines**:
  - Mock external dependencies (filesystem, network, time)
  - Don't mock the system under test
  - Don't over-mock (losing integration value)
- **Assessment**: Check for over/under mocking

### Maintainability Schema
```yaml
maintainability:
  dry:
    duplicated_code: [list]
    helper_functions_used: true | false
  documentation:
    complex_tests_documented: true | false
    undocumented_complex: [list]
  setup_teardown:
    appropriate: true | false
    issues: [list]
  mocking:
    appropriate_use: true | false
    over_mocked: [list]
    under_mocked: [list]
  overall_score: 0-100
```

---

## 6. Quality Score Calculation

### 6.1 Dimension Weights
```yaml
quality_score:
  coverage: 0-30           # 30% weight (most important)
  test_quality: 0-25       # 25% weight
  organization: 0-15       # 15% weight
  effectiveness: 0-20      # 20% weight
  maintainability: 0-10    # 10% weight
  total: 0-100
  grade: A | B | C | D | F
```

### 6.2 Per-Dimension Scoring

**Coverage Score (0-30)**:
- 30: Line coverage >= 90%, Branch >= 80%
- 24: Line coverage >= 80%, Branch >= 70%
- 18: Line coverage >= 70%, Branch >= 60%
- 12: Line coverage >= 50%, Branch >= 40%
- 6: Line coverage < 50%
- 0: No tests

**Test Quality Score (0-25)**:
- 25: All tests isolated, deterministic, fast, clear, well-asserted
- 20: Minor issues in 1 area
- 15: Issues in 2 areas
- 10: Issues in 3 areas
- 5: Issues in 4+ areas
- 0: Fundamentally broken tests

**Organization Score (0-15)**:
- 15: Mirrors source, follows conventions, well-categorized
- 12: Minor structure issues
- 9: Significant structure issues
- 6: Poor organization
- 3: Very poor organization
- 0: No organization

**Effectiveness Score (0-20)**:
- 20: Edge cases, error paths, regressions all covered
- 16: Good coverage with minor gaps
- 12: Moderate gaps
- 8: Significant gaps
- 4: Major gaps
- 0: No effective tests

**Maintainability Score (0-10)**:
- 10: DRY, documented, clean setup, appropriate mocking
- 8: Minor issues
- 6: Moderate issues
- 4: Significant issues
- 2: Major issues
- 0: Unmaintainable

### 6.3 Grading Scale

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A | 90-100 | Excellent - Production ready, exemplary tests |
| B | 80-89 | Good - Minor improvements needed |
| C | 70-79 | Adequate - Significant improvements needed |
| D | 60-69 | Poor - Major revision required |
| F | <60 | Failing - Critical testing gaps |

---

## 7. Test Type Definitions

### 7.1 Unit Tests
```yaml
unit_test:
  description: "Tests a single unit (function/class) in isolation"
  characteristics:
    - No external dependencies (filesystem, network, database)
    - Fast execution (< 100ms per test)
    - Mocks all collaborators
    - Tests single behavior
  location: tests/unit/
  example: "test_validate_track_id_format"
```

### 7.2 Integration Tests
```yaml
integration_test:
  description: "Tests interaction between multiple components"
  characteristics:
    - May use real dependencies
    - Medium execution time (< 1s per test)
    - Tests component boundaries
    - Verifies data flow between components
  location: tests/integration/
  example: "test_cli_loads_roadmap_from_filesystem"
```

### 7.3 End-to-End Tests
```yaml
e2e_test:
  description: "Tests complete user workflows"
  characteristics:
    - Uses real system components
    - Slow execution (< 10s per test)
    - Tests from user perspective
    - Validates entire user journey
  location: tests/e2e/
  example: "test_user_creates_roadmap_adds_task_completes_task"
```

### 7.4 Fixture Files
```yaml
fixture:
  description: "Shared test data and utilities"
  characteristics:
    - Not tests themselves
    - Reusable across test types
    - Provides realistic test data
  location: tests/fixtures/
  example: "sample_roadmap.yaml, conftest.py fixtures"
```

---

## 8. Per-File Audit Template

### 8.1 Standard Audit Output
```yaml
# AUDIT_TESTS_<DIRECTORY>.yaml
audit:
  directory: tests/<directory>/
  generated_at: "2025-12-12T00:00:00Z"
  criteria_version: "1.0"

  summary:
    files_audited: int
    total_tests: int
    total_assertions: int
    average_quality_score: float
    overall_grade: A | B | C | D | F

  files:
    - path: tests/<directory>/<file>.py
      size_bytes: int
      purpose: string
      tests_module: string  # What source module this tests

      test_inventory:
        total_tests: int
        test_functions:
          - name: string
            purpose: string
            assertions: int
            duration_ms: float
            coverage_areas: [list]

      metrics:
        coverage:
          # ... coverage schema
        quality:
          # ... quality schema
        organization:
          # ... organization schema
        effectiveness:
          # ... effectiveness schema
        maintainability:
          # ... maintainability schema

      quality_score:
        coverage: 0-30
        test_quality: 0-25
        organization: 0-15
        effectiveness: 0-20
        maintainability: 0-10
        total: 0-100
        grade: A | B | C | D | F

      issues:
        critical: [list]
        major: [list]
        minor: [list]

      recommendations: [list]
```

---

## 9. Grade Examples

### 9.1 Grade A Example (90-100)
```yaml
example_grade_a:
  file: tests/unit/roadmap/models/test_track.py
  characteristics:
    - 95% line coverage, 85% branch coverage
    - All tests isolated and deterministic
    - Clear naming: test_track_validate_with_missing_id_raises_error
    - High assertion density (3+ per test)
    - Edge cases covered (empty, null, invalid)
    - Error paths tested
    - DRY with good fixtures
    - Well-documented complex tests
  score: 92
  grade: A
```

### 9.2 Grade C Example (70-79)
```yaml
example_grade_c:
  file: tests/integration/test_cli_roadmap.py
  characteristics:
    - 65% line coverage, 50% branch coverage
    - Some tests have timing issues (flaky)
    - Naming inconsistent
    - Assertion density 1.5 per test
    - Few edge cases tested
    - Some error paths tested
    - Moderate duplication
    - No documentation for complex tests
  score: 74
  grade: C
```

### 9.3 Grade F Example (<60)
```yaml
example_grade_f:
  file: tests/test_legacy_importer.py
  characteristics:
    - 20% line coverage
    - Tests depend on global state
    - Poor naming: test1, test2, test_it_works
    - Few assertions, mostly checking "no exception"
    - No edge cases
    - No error handling tests
    - Lots of duplicated code
    - No documentation
  score: 35
  grade: F
```

---

## 10. Acceptance Criteria for This Document

- [x] All 5 criteria areas documented (Coverage, Quality, Organization, Effectiveness, Maintainability)
- [x] Scoring methodology is clear and objective
- [x] Test type definitions clear with characteristics
- [x] YAML schema is complete for all metrics
- [x] Examples provided for each grade level
- [x] Per-file audit template defined

---

## Appendix: Quick Reference

### Commands for Coverage Analysis
```bash
# Run with coverage
pytest --cov=vibey --cov-report=xml --cov-report=html --cov-branch tests/

# Generate missing lines report
coverage report --show-missing

# Export JSON for analysis
pytest --cov=vibey --cov-report=json tests/
```

### Test Categorization Heuristics
| Indicator | Likely Type |
|-----------|-------------|
| Uses mock extensively | Unit |
| Tests single function | Unit |
| Uses real filesystem | Integration |
| Uses real database | Integration |
| Tests CLI commands | Integration |
| Full workflow | E2E |
| Multiple user actions | E2E |
