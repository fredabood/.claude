# Sprint 1.4: Test Suite Audit
## Comprehensive Task Plan

**Sprint ID:** Phase 1.4
**Track:** User Journey Audit & Documentation Coverage
**Duration:** 2 weeks
**Tasks:** 18
**Total Estimated Tokens:** 225,000

---

## Sprint Overview

This sprint performs a comprehensive audit of the entire test suite. Building on the file classifications from Sprint 1.1 and the code audit from Sprint 1.2, this audit assesses test quality, coverage, organization, and identifies gaps where code lacks adequate test coverage. The goal is to understand the current state of testing and produce a prioritized list of coverage gaps to address in Phase 5.

### Sprint Goals
1. Define comprehensive test audit criteria
2. Run and analyze coverage metrics
3. Audit every test directory and file
4. Map tests to source code they cover
5. Identify coverage gaps and testing anti-patterns
6. Produce actionable findings for test improvement

### Prerequisites
- Sprint 1.1 outputs: `FILE_REGISTRY.yaml`, `TESTS_FILE_CLASSIFICATION.yaml`
- Sprint 1.2 outputs: `CORE_LIBRARY_AUDIT_SUMMARY.md` (for test-to-code mapping)

### Key Deliverables
- `TEST_AUDIT_CRITERIA.md` - Test audit criteria definition
- `COVERAGE_ANALYSIS_REPORT.yaml` - Coverage metrics and analysis
- `AUDIT_TESTS_ROOT.yaml` - Root test files audit
- `AUDIT_TESTS_AGENTS.yaml` - Agents tests audit
- `AUDIT_TESTS_CLI.yaml` - CLI tests audit
- `AUDIT_TESTS_DOCS.yaml` - Docs tests audit
- `AUDIT_TESTS_E2E.yaml` - E2E tests audit
- `AUDIT_TESTS_FIXTURES.yaml` - Fixtures audit
- `AUDIT_TESTS_INTEGRATION.yaml` - Integration tests audit
- `AUDIT_TESTS_MCP.yaml` - MCP tests audit
- `AUDIT_TESTS_OPERATIONS.yaml` - Operations tests audit
- `AUDIT_TESTS_PLATFORM.yaml` - Platform tests audit
- `AUDIT_TESTS_ROADMAP.yaml` - Roadmap tests audit
- `AUDIT_TESTS_UNIT.yaml` - Unit tests audit
- `AUDIT_TESTS_UTILS.yaml` - Utils tests audit
- `AUDIT_TESTS_VALIDATION.yaml` - Validation tests audit
- `COVERAGE_GAP_ANALYSIS.yaml` - Coverage gaps identification
- `TEST_SUITE_AUDIT_SUMMARY.md` - Consolidated summary

---

## Task 1: Define Test Audit Criteria

**Type:** Documentation
**Complexity:** Simple
**Estimated Tokens:** 10,000
**Duration:** 1 day

### Objective
Document the comprehensive audit criteria checklist that will be applied to every test file and the test suite as a whole.

### Test Audit Criteria Framework

#### 1. Test Coverage
- **Line Coverage**: Percentage of source lines executed by tests
- **Branch Coverage**: Percentage of code branches tested
- **Function Coverage**: Percentage of functions called by tests
- **Module Coverage**: Which modules have tests?

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

#### 2. Test Quality
- **Test Isolation**: Do tests run independently?
- **Determinism**: Do tests produce consistent results?
- **Speed**: Are tests fast enough for CI?
- **Clarity**: Are test names descriptive?
- **Assertions**: Are assertions meaningful?

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
    assertion_density: float  # assertions per test
    weak_assertions: [list]  # e.g., just checking for no exceptions
  overall_score: 0-100
```

#### 3. Test Organization
- **Structure**: Is test directory structure consistent with source?
- **Naming**: Do test files follow naming conventions?
- **Categorization**: Are tests properly categorized (unit/integration/e2e)?
- **Fixtures**: Are fixtures well-organized and reusable?

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

#### 4. Test Effectiveness
- **Mutation Score**: Would tests catch bugs? (if available)
- **Edge Cases**: Are edge cases tested?
- **Error Paths**: Are error conditions tested?
- **Regression Prevention**: Do tests prevent regressions?

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

#### 5. Test Maintainability
- **DRY**: Is test code DRY (Don't Repeat Yourself)?
- **Documentation**: Are complex tests documented?
- **Setup/Teardown**: Is setup/teardown appropriate?
- **Mocking**: Is mocking used appropriately?

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
    over_mocked: [list]  # tests that mock too much
    under_mocked: [list] # tests with unnecessary real dependencies
  overall_score: 0-100
```

#### 6. Quality Score Calculation

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

**Grading Scale:**
- A: 90-100 (Excellent - Production ready)
- B: 80-89 (Good - Minor improvements needed)
- C: 70-79 (Adequate - Significant improvements needed)
- D: 60-69 (Poor - Major revision required)
- F: <60 (Failing - Critical testing gaps)

### Test Type Definitions

```yaml
test_types:
  unit:
    description: "Tests a single unit (function/class) in isolation"
    characteristics:
      - No external dependencies
      - Fast execution (< 100ms)
      - Mocks all collaborators
    location: tests/unit/

  integration:
    description: "Tests interaction between multiple components"
    characteristics:
      - May use real dependencies
      - Medium execution time
      - Tests component boundaries
    location: tests/integration/

  e2e:
    description: "Tests complete user workflows"
    characteristics:
      - Uses real system
      - Slow execution
      - Tests from user perspective
    location: tests/e2e/

  fixture:
    description: "Shared test data and utilities"
    characteristics:
      - Not tests themselves
      - Reusable across tests
    location: tests/fixtures/
```

### Deliverable
Create `TEST_AUDIT_CRITERIA.md` documenting:
1. All audit criteria with descriptions
2. Scoring methodology
3. YAML schema for audit outputs
4. Test type definitions
5. Examples of each rating level

### Acceptance Criteria
- [ ] All 5 criteria areas documented
- [ ] Scoring methodology is clear and objective
- [ ] Test type definitions clear
- [ ] YAML schema is complete
- [ ] Examples provided for clarity

---

## Task 2: Run Coverage Analysis

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1.5 days

### Objective
Run the test suite with coverage analysis and produce comprehensive coverage metrics.

### Steps

#### Step 1: Run Coverage Collection
```bash
# Run pytest with coverage
pytest --cov=vibey --cov-report=xml --cov-report=html --cov-report=json --cov-branch tests/

# Generate coverage report
coverage report --show-missing
```

#### Step 2: Parse Coverage Results
Extract from coverage JSON:
- Per-file coverage percentages
- Uncovered line numbers
- Branch coverage details
- Missing coverage by module

#### Step 3: Analyze Coverage Distribution

```yaml
coverage_distribution:
  by_module:
    vibey/cli:
      files: 15
      total_lines: 2500
      covered_lines: 2125
      line_coverage: 85%
      branch_coverage: 78%
    vibey/operations:
      files: 22
      total_lines: 5500
      covered_lines: 4125
      line_coverage: 75%
      branch_coverage: 68%
    # ... all modules

  by_coverage_level:
    excellent_90_plus:
      count: X
      files: [list]
    good_80_89:
      count: X
      files: [list]
    adequate_70_79:
      count: X
      files: [list]
    poor_60_69:
      count: X
      files: [list]
    critical_below_60:
      count: X
      files: [list]
    no_coverage:
      count: X
      files: [list]
```

### Output Format
```yaml
# COVERAGE_ANALYSIS_REPORT.yaml
coverage_analysis:
  generated_at: "2025-12-11T00:00:00Z"
  tool: pytest-cov

  summary:
    total_files: X
    total_statements: X
    covered_statements: X
    line_coverage_percent: X
    branch_coverage_percent: X
    function_coverage_percent: X

  by_module:
    - module: vibey/cli
      files:
        - path: vibey/cli/main.py
          statements: 360
          covered: 306
          missing: 54
          line_coverage: 85%
          branch_coverage: 78%
          uncovered_lines: [45-52, 120-135, 280-295]
        # ... all files
      summary:
        total_files: X
        line_coverage: X%
        branch_coverage: X%

    - module: vibey/operations
      # ... similar structure

  coverage_gaps:
    zero_coverage:
      - path: vibey/legacy/old_loader.py
        reason: "Deprecated code, not tested"
      - path: vibey/operations/experimental.py
        reason: "New code, tests not written yet"

    low_coverage_below_50:
      - path: vibey/operations/roadmap/bulk_ops.py
        coverage: 35%
        uncovered_areas: ["error handling", "edge cases"]

    missing_branch_coverage:
      - path: vibey/cli/commands.py
        line_coverage: 85%
        branch_coverage: 55%
        uncovered_branches: ["error paths", "fallback logic"]

  test_execution:
    total_tests: X
    passed: X
    failed: X
    skipped: X
    errors: X
    duration_seconds: X

  recommendations:
    priority_1:
      - "Add tests for vibey/operations/roadmap/bulk_ops.py"
      - "Improve branch coverage in vibey/cli/commands.py"
    priority_2:
      - "Decide fate of vibey/legacy/ (test or delete)"
```

### Acceptance Criteria
- [ ] Coverage collected for all vibey/ modules
- [ ] Per-file coverage data extracted
- [ ] Coverage distribution analyzed
- [ ] Gap analysis performed
- [ ] Recommendations generated

---

## Task 3: Audit tests/ Root Files

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Audit the test files directly in the tests/ root directory and the core test infrastructure.

### Files to Audit
Based on directory listing:
```
tests/
├── __init__.py                           # Package init
├── conftest.py                           # Pytest fixtures
├── README.md                             # Test documentation
├── test_deliverable_type_normalization.py  # 5,790 bytes
├── test_git_hooks.py                     # 18,085 bytes
├── test_package_installation.py          # 8,442 bytes
├── test_safe_yaml_editor.py              # 17,675 bytes
└── test_unified_errors.py                # 10,503 bytes
```

### Infrastructure Audit

#### conftest.py Analysis
```yaml
file: tests/conftest.py
purpose: Shared pytest fixtures and configuration
size_bytes: 3456

fixtures_defined:
  - name: temp_dir
    scope: function | class | module | session
    purpose: "Provides temporary directory"
    usage_count: X  # How many tests use this
  - name: sample_roadmap
    scope: function
    purpose: "Provides sample roadmap data"
    usage_count: X
  # ... all fixtures

configuration:
  pytest_plugins: [list]
  markers_defined: [list]
  hooks_implemented: [list]

quality_assessment:
  fixtures_reusable: true | false
  fixtures_documented: true | false
  scope_appropriate: true | false
  issues: [list]
```

#### Root Test Files Analysis
```yaml
file: tests/test_unified_errors.py
size_bytes: 10503
purpose: Test unified error handling system
tests_module: vibey.common.errors

test_inventory:
  total_tests: X
  test_functions:
    - name: test_error_creation
      purpose: "Tests error instantiation"
      assertions: X
      coverage_areas: ["error creation", "context data"]
    - name: test_error_rendering
      purpose: "Tests error message formatting"
      assertions: X
      coverage_areas: ["CLI rendering", "MCP rendering"]
    # ... all tests

coverage_analysis:
  module_covered: vibey.common.errors
  line_coverage: X%
  functions_tested: [list]
  functions_not_tested: [list]

quality_metrics:
  test_isolation: true | false
  deterministic: true | false
  average_duration_ms: X
  assertion_density: X
```

### Per-File Audit Questions

For each root test file:
1. What module/functionality does this test?
2. Is the test in the right location (should it be in a subdirectory)?
3. How comprehensive is the coverage?
4. Are there any test quality issues?

### Output Format
```yaml
# AUDIT_TESTS_ROOT.yaml
audit:
  directory: tests/
  scope: root_files_only
  generated_at: "2025-12-11T00:00:00Z"
  criteria_version: "1.0"

  infrastructure:
    conftest:
      path: tests/conftest.py
      fixtures_count: X
      fixtures_documented: X / X
      quality_score: X
      issues: [list]
      recommendations: [list]

    init:
      path: tests/__init__.py
      purpose: "Package initialization"
      content: "Empty marker file"

    readme:
      path: tests/README.md
      purpose: "Test documentation"
      content_current: true | false

  test_files:
    - path: tests/test_unified_errors.py
      # ... full audit per template
    - path: tests/test_git_hooks.py
      # ... full audit
    # ... all root test files

  placement_analysis:
    correctly_placed: [list]
    should_move:
      - file: tests/test_unified_errors.py
        suggested_location: tests/unit/common/
        reason: "Unit test for specific module"

  summary:
    files_audited: 8
    total_tests: X
    average_quality_score: X
    grade_distribution:
      A: X
      B: X
      C: X
      D: X
      F: X
    infrastructure_health: good | adequate | poor
```

### Acceptance Criteria
- [ ] All root test files audited
- [ ] conftest.py fixtures documented
- [ ] Test placement analyzed
- [ ] Quality scores calculated

---

## Task 4: Audit tests/agents/ Test Files

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 8,000
**Duration:** 0.5 days

### Objective
Audit the agents test directory.

### Directory Contents
```
tests/agents/
├── __init__.py
├── test_agent_definitions.py
├── test_agent_loading.py
└── ...
```

### Audit Focus Areas

#### Agent Testing Coverage
- Are all agent types tested?
- Is agent loading/parsing tested?
- Are agent behaviors validated?
- Is agent configuration tested?

### Per-File Template
```yaml
file: tests/agents/test_agent_definitions.py
purpose: Test agent definition loading and validation
tests_module: vibey.agents (or framework/agents/)

agent_coverage:
  agents_tested: [list of agent names]
  agents_not_tested: [list]
  coverage_percent: X

test_categories:
  definition_parsing: X tests
  validation: X tests
  behavior: X tests
  configuration: X tests

quality_metrics:
  # ... standard quality metrics
```

### Output Format
```yaml
# AUDIT_TESTS_AGENTS.yaml
audit:
  directory: tests/agents/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/agents/test_agent_definitions.py
      # ... full audit
    # ... all files

  agent_test_coverage:
    total_agents: X
    agents_with_tests: X
    coverage_percent: X
    untested_agents: [list]

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
```

### Acceptance Criteria
- [ ] All agent test files audited
- [ ] Agent coverage analyzed
- [ ] Quality metrics calculated

---

## Task 5: Audit tests/cli/ Test Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Audit the CLI test directory, which tests the command-line interface.

### Directory Contents
```
tests/cli/
├── __init__.py
├── test_main.py
├── test_commands.py
├── test_roadmap_commands.py
├── roadmap_lib/
│   ├── test_display.py
│   ├── test_filesystem.py
│   └── ...
└── ... (26 files total)
```

### Audit Focus Areas

#### CLI Testing Requirements
- **Command Coverage**: Are all CLI commands tested?
- **Option Coverage**: Are all options/arguments tested?
- **Error Handling**: Are CLI errors tested?
- **Output Verification**: Is CLI output validated?

### CLI Command Coverage Analysis
```yaml
cli_command_coverage:
  top_level_commands:
    - command: vibey
      tested: true | false
      test_file: tests/cli/test_main.py
    - command: vibey roadmap
      tested: true | false
      test_file: tests/cli/test_roadmap_commands.py
    # ... all commands

  subcommands:
    vibey_roadmap:
      - subcommand: status
        tested: true | false
        options_tested: X / Y
      - subcommand: update
        tested: true | false
        options_tested: X / Y
      # ... all subcommands

  coverage_summary:
    commands_tested: X / Y
    command_coverage: X%
    options_tested: X / Y
    option_coverage: X%
```

### Per-File Template
```yaml
file: tests/cli/test_commands.py
purpose: Test CLI command implementations
tests_module: vibey.cli.commands

command_tests:
  - command: vibey roadmap status
    tests:
      - test_roadmap_status_success
      - test_roadmap_status_no_roadmap
      - test_roadmap_status_with_filters
    options_tested:
      - --format: tested
      - --verbose: not_tested
    error_cases_tested:
      - invalid_roadmap: true
      - permission_denied: false

click_testing:
  uses_click_testing: true | false
  runner_used: CliRunner
  isolated_filesystem: true | false

output_testing:
  exit_codes_verified: true | false
  stdout_verified: true | false
  stderr_verified: true | false
  json_output_verified: true | false

quality_metrics:
  # ... standard quality metrics
```

### Output Format
```yaml
# AUDIT_TESTS_CLI.yaml
audit:
  directory: tests/cli/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/cli/test_main.py
      # ... full audit
    - path: tests/cli/test_commands.py
      # ... full audit
    # ... all files

  cli_coverage:
    commands:
      total: X
      tested: X
      coverage_percent: X
    options:
      total: X
      tested: X
      coverage_percent: X
    error_cases:
      total: X
      tested: X
      coverage_percent: X

  testing_patterns:
    click_runner_used: true | false
    isolated_filesystem: true | false
    output_capture: true | false

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    cli_fully_tested: true | false
```

### Acceptance Criteria
- [ ] All CLI test files audited
- [ ] Command coverage calculated
- [ ] Option coverage calculated
- [ ] Error case coverage assessed

---

## Task 6: Audit tests/docs/ Test Files

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 6,000
**Duration:** 0.5 days

### Objective
Audit the docs test directory, which tests documentation-related functionality.

### Directory Contents
```
tests/docs/
├── __init__.py
├── test_doc_generation.py
├── test_doc_validation.py
└── ...
```

### Audit Focus Areas

#### Documentation Testing
- Is doc generation tested?
- Is doc validation tested?
- Are doc links verified?
- Is doc freshness checked?

### Output Format
```yaml
# AUDIT_TESTS_DOCS.yaml
audit:
  directory: tests/docs/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/docs/[file]
      # ... full audit

  documentation_test_coverage:
    generation_tested: true | false
    validation_tested: true | false
    link_checking: true | false
    freshness_checking: true | false

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
```

### Acceptance Criteria
- [ ] All docs test files audited
- [ ] Documentation testing coverage assessed

---

## Task 7: Audit tests/e2e/ Test Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 12,000
**Duration:** 1 day

### Objective
Audit the end-to-end test directory, which tests complete user workflows.

### Directory Contents
```
tests/e2e/
├── __init__.py
├── test_user_workflows.py
├── test_roadmap_lifecycle.py
├── test_cli_e2e.py
└── ... (8 files)
```

### Audit Focus Areas

#### E2E Test Requirements
- **User Journeys**: Are key user journeys tested?
- **Real Environment**: Do tests use real system?
- **Data Integrity**: Is data flow validated end-to-end?
- **Error Recovery**: Are recovery scenarios tested?

### User Journey Coverage
```yaml
user_journey_coverage:
  journeys_identified:
    - journey: "New user installs and creates first roadmap"
      tested: true | false
      test_file: tests/e2e/test_user_workflows.py
    - journey: "Developer adds track and completes sprint"
      tested: true | false
      test_file: tests/e2e/test_roadmap_lifecycle.py
    # ... all journeys

  coverage_summary:
    journeys_tested: X / Y
    coverage_percent: X
```

### Per-File Template
```yaml
file: tests/e2e/test_roadmap_lifecycle.py
purpose: Test complete roadmap lifecycle end-to-end
test_scope: e2e

workflows_tested:
  - workflow: "Create roadmap → Add track → Add sprint → Complete tasks"
    steps_tested: X / Y
    assertions: X
    duration_seconds: X
  - workflow: "Import existing roadmap → Migrate → Verify"
    steps_tested: X / Y

environment:
  uses_real_filesystem: true | false
  uses_real_database: true | false
  cleanup_implemented: true | false

quality_metrics:
  isolation: true | false  # Can run independently
  deterministic: true | false
  duration_seconds: X
  timeout_configured: true | false
```

### Output Format
```yaml
# AUDIT_TESTS_E2E.yaml
audit:
  directory: tests/e2e/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/e2e/[file]
      # ... full audit

  user_journey_coverage:
    identified_journeys: X
    tested_journeys: X
    coverage_percent: X
    untested_journeys: [list]

  e2e_test_health:
    total_e2e_tests: X
    average_duration: X seconds
    flaky_tests: [list]
    timeout_issues: [list]

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    user_journeys_adequate: true | false
```

### Acceptance Criteria
- [ ] All E2E test files audited
- [ ] User journey coverage analyzed
- [ ] Test health assessed
- [ ] Flaky tests identified

---

## Task 8: Audit tests/fixtures/ Test Files

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 6,000
**Duration:** 0.5 days

### Objective
Audit the fixtures directory, which contains shared test data and utilities.

### Directory Contents
```
tests/fixtures/
├── __init__.py
├── sample_roadmap.yaml
├── sample_config.yaml
└── ...
```

### Audit Focus Areas

#### Fixture Quality
- **Organization**: Are fixtures well-organized?
- **Documentation**: Are fixtures documented?
- **Reusability**: Are fixtures reusable?
- **Currency**: Are fixtures up-to-date?

### Fixture Analysis
```yaml
fixture_analysis:
  data_fixtures:
    - name: sample_roadmap.yaml
      purpose: "Sample roadmap for testing"
      used_by: [list of test files]
      schema_valid: true | false
      realistic: true | false

  code_fixtures:
    - name: helpers.py
      purpose: "Test helper functions"
      functions: [list]
      used_by: [list of test files]

  fixture_health:
    total_fixtures: X
    documented: X
    used: X
    unused: [list]  # Dead fixtures
    duplicated: [list]  # Fixtures that duplicate each other
```

### Output Format
```yaml
# AUDIT_TESTS_FIXTURES.yaml
audit:
  directory: tests/fixtures/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/fixtures/[file]
      type: data | code
      purpose: string
      used_by: [list]
      quality_assessment:
        documented: true | false
        current: true | false
        realistic: true | false

  fixture_inventory:
    data_fixtures: X
    code_fixtures: X
    total: X

  usage_analysis:
    heavily_used: [fixtures used by > 10 tests]
    unused: [fixtures with no usage]

  recommendations:
    cleanup: [unused fixtures to remove]
    consolidate: [duplicated fixtures to merge]
    document: [undocumented fixtures]

  summary:
    files_audited: X
    fixture_health: good | adequate | poor
```

### Acceptance Criteria
- [ ] All fixture files audited
- [ ] Usage analysis completed
- [ ] Unused fixtures identified
- [ ] Documentation status assessed

---

## Task 9: Audit tests/integration/ Test Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Audit the integration test directory, which tests component interactions.

### Directory Contents
```
tests/integration/
├── __init__.py
├── test_cli_operations.py
├── test_roadmap_persistence.py
├── test_sqlite_integration.py
└── ... (20 files)
```

### Audit Focus Areas

#### Integration Test Requirements
- **Component Boundaries**: Are component interactions tested?
- **Data Flow**: Is data flow between components validated?
- **External Systems**: Are external system interactions tested?
- **Error Propagation**: Are errors propagated correctly?

### Integration Points Analysis
```yaml
integration_points:
  - components: [CLI, Operations]
    tested: true | false
    test_files: [tests/integration/test_cli_operations.py]
  - components: [Operations, SQLite]
    tested: true | false
    test_files: [tests/integration/test_sqlite_integration.py]
  - components: [MCP, Operations]
    tested: true | false
    test_files: [tests/integration/test_mcp_operations.py]
  # ... all integration points

  coverage_summary:
    integration_points_identified: X
    integration_points_tested: X
    coverage_percent: X
```

### Per-File Template
```yaml
file: tests/integration/test_sqlite_integration.py
purpose: Test SQLite database integration
test_scope: integration
components_tested: [roadmap models, SQLite, serialization]

integration_scenarios:
  - scenario: "Save roadmap to SQLite → Load from SQLite → Verify equality"
    tested: true
    assertions: X
  - scenario: "Concurrent writes → Verify integrity"
    tested: false

external_dependencies:
  - dependency: SQLite
    real: true
    mocked: false
  - dependency: filesystem
    real: true
    mocked: false

quality_metrics:
  isolation: true | false
  cleanup: true | false
  deterministic: true | false
```

### Output Format
```yaml
# AUDIT_TESTS_INTEGRATION.yaml
audit:
  directory: tests/integration/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/integration/[file]
      # ... full audit

  integration_coverage:
    component_pairs_identified: X
    component_pairs_tested: X
    coverage_percent: X
    untested_integrations: [list]

  external_dependencies:
    sqlite: tested | not_tested
    filesystem: tested | not_tested
    git: tested | not_tested

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    integration_adequate: true | false
```

### Acceptance Criteria
- [ ] All integration test files audited
- [ ] Integration point coverage analyzed
- [ ] External dependencies identified
- [ ] Quality metrics calculated

---

## Task 10: Audit tests/mcp/ Test Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Audit the MCP test directory, which tests MCP server functionality.

### Directory Contents
```
tests/mcp/
├── __init__.py
├── test_server.py
├── test_tools.py
├── test_resources.py
└── ... (9 files)
```

### Audit Focus Areas

#### MCP Testing Requirements
- **Protocol Compliance**: Are MCP protocol responses tested?
- **Tool Coverage**: Are all MCP tools tested?
- **Error Responses**: Are MCP errors properly formatted?
- **Schema Validation**: Are tool schemas validated?

### MCP Coverage Analysis
```yaml
mcp_coverage:
  server:
    initialization: tested | not_tested
    capabilities: tested | not_tested
    error_handling: tested | not_tested

  tools:
    - tool: roadmap_query
      tested: true | false
      scenarios_tested: [list]
    - tool: roadmap_update
      tested: true | false
      scenarios_tested: [list]
    # ... all tools

  resources:
    - resource: roadmap_file
      tested: true | false
    # ... all resources

  coverage_summary:
    tools_tested: X / Y
    resources_tested: X / Y
    protocol_compliance_tested: true | false
```

### Output Format
```yaml
# AUDIT_TESTS_MCP.yaml
audit:
  directory: tests/mcp/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/mcp/[file]
      # ... full audit

  mcp_coverage:
    server: X%
    tools: X%
    resources: X%
    protocol: X%

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    mcp_fully_tested: true | false
```

### Acceptance Criteria
- [ ] All MCP test files audited
- [ ] Tool coverage calculated
- [ ] Protocol compliance assessed

---

## Task 11: Audit tests/operations/ Test Files

**Type:** Research
**Complexity:** Complex
**Estimated Tokens:** 18,000
**Duration:** 1.5 days

### Objective
Audit the operations test directory, which tests core business logic.

### Directory Contents
```
tests/operations/
├── __init__.py
├── roadmap/
│   ├── test_query.py
│   ├── test_update.py
│   └── ...
├── docs/
├── git/
└── ... (7 subdirectories)
```

### Audit Focus Areas

#### Operations Testing Requirements
- **Business Logic**: Is core business logic thoroughly tested?
- **Edge Cases**: Are edge cases covered?
- **Error Handling**: Are operation errors tested?
- **Data Validation**: Is input validation tested?

### Operations Coverage Analysis
```yaml
operations_coverage:
  roadmap_operations:
    query:
      file: tests/operations/roadmap/test_query.py
      functions_tested: X / Y
      coverage: X%
    update:
      file: tests/operations/roadmap/test_update.py
      functions_tested: X / Y
      coverage: X%
    create:
      tested: true | false
    delete:
      tested: true | false

  docs_operations:
    generator: tested | not_tested
    validator: tested | not_tested

  git_operations:
    hooks: tested | not_tested
    integration: tested | not_tested
```

### Output Format
```yaml
# AUDIT_TESTS_OPERATIONS.yaml
audit:
  directory: tests/operations/
  generated_at: "2025-12-11T00:00:00Z"

  subdirectories:
    - name: roadmap
      files: X
      tests: X
      coverage: X%
    - name: docs
      files: X
      tests: X
      coverage: X%
    # ... all subdirs

  files:
    - path: tests/operations/[file]
      # ... full audit

  operations_coverage:
    total_operations: X
    tested_operations: X
    coverage_percent: X
    critical_untested: [list]

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    business_logic_adequate: true | false
```

### Acceptance Criteria
- [ ] All operations test files audited
- [ ] Per-operation coverage calculated
- [ ] Critical operations identified
- [ ] Quality metrics assessed

---

## Task 12: Audit tests/platform/ Test Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 10,000
**Duration:** 0.5 days

### Objective
Audit the platform test directory, which tests platform compatibility.

### Directory Contents
```
tests/platform/
├── __init__.py
├── test_detection.py
├── test_paths.py
├── test_compat.py
└── ... (16 files)
```

### Audit Focus Areas

#### Platform Testing Requirements
- **OS Compatibility**: Are different OS scenarios tested?
- **Path Handling**: Are platform-specific paths tested?
- **Feature Detection**: Is capability detection tested?

### Platform Coverage Analysis
```yaml
platform_coverage:
  operating_systems:
    linux: tested | mocked | not_tested
    macos: tested | mocked | not_tested
    windows: tested | mocked | not_tested

  features:
    path_handling: tested | not_tested
    symlinks: tested | not_tested
    file_locking: tested | not_tested

  compatibility_matrix:
    feature: [linux, macos, windows]
    tests: [X, X, X]  # Number of tests per platform
```

### Output Format
```yaml
# AUDIT_TESTS_PLATFORM.yaml
audit:
  directory: tests/platform/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/platform/[file]
      # ... full audit

  platform_coverage:
    os_tested: [list]
    os_mocked: [list]
    features_tested: [list]
    features_not_tested: [list]

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    cross_platform_ready: true | false
```

### Acceptance Criteria
- [ ] All platform test files audited
- [ ] OS coverage analyzed
- [ ] Feature coverage assessed

---

## Task 13: Audit tests/roadmap/ Test Files

**Type:** Research
**Complexity:** Complex
**Estimated Tokens:** 18,000
**Duration:** 1.5 days

### Objective
Audit the roadmap test directory, which tests roadmap models and serialization.

### Directory Contents
```
tests/roadmap/
├── __init__.py
├── models/
│   ├── test_track.py
│   ├── test_sprint.py
│   ├── test_task.py
│   └── ...
├── serialization/
│   ├── test_yaml_loader.py
│   ├── test_sql_loader.py
│   └── ...
└── ... (12 files/dirs)
```

### Audit Focus Areas

#### Model Testing Requirements
- **Model Validation**: Are model validators tested?
- **Relationships**: Are model relationships tested?
- **Serialization**: Is round-trip serialization tested?
- **Schema Evolution**: Is schema migration tested?

### Model Coverage Analysis
```yaml
model_coverage:
  models:
    - model: Track
      file: tests/roadmap/models/test_track.py
      validation_tested: true | false
      relationships_tested: true | false
      edge_cases_tested: true | false
    - model: Sprint
      # ... similar
    - model: Task
      # ... similar

  serialization:
    yaml:
      loader_tested: true | false
      dumper_tested: true | false
      round_trip_tested: true | false
    sql:
      loader_tested: true | false
      dumper_tested: true | false
      round_trip_tested: true | false
```

### Output Format
```yaml
# AUDIT_TESTS_ROADMAP.yaml
audit:
  directory: tests/roadmap/
  generated_at: "2025-12-11T00:00:00Z"

  subdirectories:
    - name: models
      files: X
      tests: X
    - name: serialization
      files: X
      tests: X

  files:
    - path: tests/roadmap/[file]
      # ... full audit

  model_coverage:
    models_with_tests: X / Y
    validation_coverage: X%
    relationship_coverage: X%

  serialization_coverage:
    yaml_coverage: X%
    sql_coverage: X%
    round_trip_verified: true | false

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    data_integrity_assured: true | false
```

### Acceptance Criteria
- [ ] All roadmap test files audited
- [ ] Model coverage calculated
- [ ] Serialization coverage calculated
- [ ] Round-trip testing verified

---

## Task 14: Audit tests/unit/ Test Files

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Audit the unit test directory, which contains isolated unit tests.

### Directory Contents
```
tests/unit/
├── __init__.py
├── test_utils.py
├── test_errors.py
├── cli/
├── operations/
└── ... (16 files/dirs)
```

### Audit Focus Areas

#### Unit Test Requirements
- **Isolation**: Are tests truly isolated?
- **Mocking**: Is mocking used appropriately?
- **Speed**: Are unit tests fast?
- **Coverage**: Is unit coverage comprehensive?

### Unit Test Analysis
```yaml
unit_test_analysis:
  isolation_assessment:
    truly_isolated: X / Y tests
    has_external_dependencies: [list of tests]

  mocking_assessment:
    appropriate_mocking: X / Y tests
    over_mocked: [list]  # Tests that mock too much
    under_mocked: [list]  # Tests with unnecessary real deps

  speed_assessment:
    average_duration_ms: X
    slow_tests: [tests > 100ms]
    total_suite_duration: X seconds
```

### Output Format
```yaml
# AUDIT_TESTS_UNIT.yaml
audit:
  directory: tests/unit/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/unit/[file]
      # ... full audit

  unit_test_health:
    total_tests: X
    isolated: X
    fast: X
    well_mocked: X

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
    average_duration_ms: X
    unit_test_suite_healthy: true | false
```

### Acceptance Criteria
- [ ] All unit test files audited
- [ ] Isolation verified
- [ ] Speed analyzed
- [ ] Mocking assessed

---

## Task 15: Audit tests/utils/ Test Files

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 6,000
**Duration:** 0.5 days

### Objective
Audit the utils test directory, which tests utility functions.

### Directory Contents
```
tests/utils/
├── __init__.py
├── test_helpers.py
├── test_formatters.py
└── ... (9 files)
```

### Output Format
```yaml
# AUDIT_TESTS_UTILS.yaml
audit:
  directory: tests/utils/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/utils/[file]
      # ... full audit

  utility_coverage:
    utility_functions_tested: X / Y
    coverage_percent: X

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
```

### Acceptance Criteria
- [ ] All utils test files audited
- [ ] Utility function coverage calculated

---

## Task 16: Audit tests/validation/ Test Files

**Type:** Research
**Complexity:** Simple
**Estimated Tokens:** 6,000
**Duration:** 0.5 days

### Objective
Audit the validation test directory, which tests validation logic.

### Directory Contents
```
tests/validation/
├── __init__.py
├── test_schema_validation.py
├── test_config_validation.py
└── ...
```

### Audit Focus Areas

#### Validation Testing Requirements
- **Schema Validation**: Are all schemas tested?
- **Error Messages**: Are validation errors tested?
- **Edge Cases**: Are boundary cases tested?

### Output Format
```yaml
# AUDIT_TESTS_VALIDATION.yaml
audit:
  directory: tests/validation/
  generated_at: "2025-12-11T00:00:00Z"

  files:
    - path: tests/validation/[file]
      # ... full audit

  validation_coverage:
    schemas_tested: X / Y
    error_cases_tested: X / Y
    boundary_cases_tested: X / Y

  summary:
    files_audited: X
    total_tests: X
    average_quality_score: X
```

### Acceptance Criteria
- [ ] All validation test files audited
- [ ] Schema coverage calculated
- [ ] Error case coverage assessed

---

## Task 17: Identify Test Coverage Gaps

**Type:** Research
**Complexity:** Medium
**Estimated Tokens:** 15,000
**Duration:** 1 day

### Objective
Synthesize all audit findings to identify comprehensive test coverage gaps.

### Gap Analysis Framework

#### Code Without Tests
```yaml
untested_code:
  files_with_no_tests:
    - path: vibey/legacy/old_loader.py
      lines: 450
      reason: "Deprecated, consider removal"
      priority: low
    - path: vibey/operations/experimental/new_feature.py
      lines: 200
      reason: "New code, tests not written"
      priority: high

  functions_with_no_tests:
    - file: vibey/operations/roadmap/query.py
      function: get_track_history
      lines: 45-89
      complexity: medium
      priority: high

  branches_not_covered:
    - file: vibey/cli/commands.py
      line: 120
      branch: "else branch for invalid input"
      priority: medium
```

#### Critical Paths Not Tested
```yaml
critical_paths:
  - path: "User creates roadmap → Saves to SQLite → Reloads"
    tested: partial
    missing: "Reload verification"
    priority: critical

  - path: "Error in update → Rollback → State intact"
    tested: false
    missing: "Entire path"
    priority: critical
```

#### Test Quality Gaps
```yaml
quality_gaps:
  flaky_tests:
    - test: tests/e2e/test_concurrent_access.py::test_parallel_writes
      flakiness_rate: 15%
      root_cause: "Race condition in setup"

  slow_tests:
    - test: tests/integration/test_large_roadmap.py::test_1000_tasks
      duration: 45s
      acceptable: false
      recommendation: "Mock or reduce test data"

  poorly_isolated:
    - test: tests/unit/test_config.py::test_load_config
      issue: "Reads real filesystem"
      recommendation: "Mock filesystem"
```

### Output Format
```yaml
# COVERAGE_GAP_ANALYSIS.yaml
gap_analysis:
  generated_at: "2025-12-11T00:00:00Z"

  summary:
    total_coverage_percent: X
    target_coverage_percent: 100
    gap_percent: X

    files_without_tests: X
    functions_without_tests: X
    critical_paths_untested: X

  untested_code:
    # ... as above

  critical_paths:
    # ... as above

  quality_gaps:
    # ... as above

  prioritized_remediation:
    critical:
      - item: "Add tests for transaction rollback"
        effort: "2 days"
        impact: "Data integrity assurance"
      - item: "Test error recovery paths"
        effort: "1 day"
        impact: "Production reliability"

    high:
      - item: "Increase branch coverage in CLI"
        effort: "3 days"
        impact: "CLI reliability"

    medium:
      - item: "Fix flaky E2E tests"
        effort: "2 days"
        impact: "CI reliability"

    low:
      - item: "Add tests for deprecated code or delete"
        effort: "1 day"
        impact: "Code cleanliness"
```

### Acceptance Criteria
- [ ] All untested code identified
- [ ] Critical paths assessed
- [ ] Quality gaps documented
- [ ] Remediation prioritized

---

## Task 18: Generate Test Suite Audit Summary

**Type:** Documentation
**Complexity:** Medium
**Estimated Tokens:** 20,000
**Duration:** 1.5 days

### Objective
Consolidate all test audit findings into a comprehensive summary report.

### Report Structure
```markdown
# Test Suite Audit Summary

## Executive Summary
- Total test files audited: X
- Total tests: X
- Line coverage: X%
- Branch coverage: X%
- Average quality score: X/100
- Critical gaps: X

## Coverage Overview

### Coverage Metrics
| Metric          | Current | Target | Gap   |
|-----------------|---------|--------|-------|
| Line Coverage   | X%      | 100%   | X%    |
| Branch Coverage | X%      | 100%   | X%    |
| Function Coverage | X%    | 100%   | X%    |

### Coverage by Module
| Module          | Files | Tests | Line % | Branch % | Grade |
|-----------------|-------|-------|--------|----------|-------|
| vibey/cli       | X     | X     | X%     | X%       | X     |
| vibey/operations| X     | X     | X%     | X%       | X     |
| vibey/roadmap   | X     | X     | X%     | X%       | X     |
| ...             |       |       |        |          |       |

## Test Organization

### Test Distribution
| Type        | Count | Percentage |
|-------------|-------|------------|
| Unit        | X     | X%         |
| Integration | X     | X%         |
| E2E         | X     | X%         |
| Other       | X     | X%         |

### Directory Analysis
| Directory       | Files | Tests | Avg Score | Issues |
|-----------------|-------|-------|-----------|--------|
| tests/ (root)   | X     | X     | X         | X      |
| tests/agents    | X     | X     | X         | X      |
| tests/cli       | X     | X     | X         | X      |
| ...             |       |       |           |        |

## Test Quality

### Quality Score Distribution
| Grade | Count | Percentage |
|-------|-------|------------|
| A     | X     | X%         |
| B     | X     | X%         |
| C     | X     | X%         |
| D     | X     | X%         |
| F     | X     | X%         |

### Test Health Issues
- Flaky tests: X
- Slow tests (>1s): X
- Poorly isolated: X
- Missing assertions: X

## Coverage Gaps

### Critical Gaps
1. [Gap 1 with impact and remediation]
2. [Gap 2 with impact and remediation]

### Untested Code
- Files with no tests: X
- Functions with no tests: X
- Estimated lines untested: X

## Test Effectiveness

### Mutation Testing (if available)
- Mutation score: X%
- Mutants killed: X / Y
- Surviving mutants: X

### Regression Prevention
- Known bugs with tests: X
- Regressions caught in last month: X

## Remediation Roadmap

### Immediate (Week 1)
1. [Critical coverage gaps]
2. [Fix flaky tests]

### Short-term (Month 1)
1. [Increase coverage to X%]
2. [Add missing integration tests]

### Long-term (Quarter 1)
1. [Achieve 100% coverage]
2. [Implement mutation testing]

## Appendix
- Individual directory audit reports
- Full test listing with scores
- Coverage report details
```

### Acceptance Criteria
- [ ] All directory audits synthesized
- [ ] Coverage metrics calculated
- [ ] Quality analysis complete
- [ ] Gaps prioritized
- [ ] Remediation roadmap created
- [ ] Report is actionable

---

## Sprint Dependencies

```
Task 1 (Criteria) ──┬──> Task 2 (Coverage Analysis)
                    │
Task 2 ─────────────┼──> Task 3-16 (Directory Audits)
                    │
                    └──> All audits in parallel

Task 3 (Root) ──────┐
Task 4 (Agents) ────┤
Task 5 (CLI) ───────┤
Task 6 (Docs) ──────┤
Task 7 (E2E) ───────┤
Task 8 (Fixtures) ──┼──> Task 17 (Gap Analysis) ──> Task 18 (Summary)
Task 9 (Integration)┤
Task 10 (MCP) ──────┤
Task 11 (Operations)┤
Task 12 (Platform) ─┤
Task 13 (Roadmap) ──┤
Task 14 (Unit) ─────┤
Task 15 (Utils) ────┤
Task 16 (Validation)┘
```

## Sprint Success Criteria

1. **Completeness**
   - [ ] Every test file audited
   - [ ] Coverage metrics collected
   - [ ] All directories analyzed

2. **Accuracy**
   - [ ] Coverage numbers verified
   - [ ] Test categorization correct
   - [ ] Gap analysis accurate

3. **Actionability**
   - [ ] Coverage gaps prioritized
   - [ ] Quality issues identified
   - [ ] Remediation roadmap created

4. **Quality**
   - [ ] Consistent audit criteria
   - [ ] Objective scoring
   - [ ] Useful recommendations

---

## Output Directory Structure

```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/
├── SPRINT_PLAN.md                    # This document
├── TEST_AUDIT_CRITERIA.md            # Task 1 output
├── COVERAGE_ANALYSIS_REPORT.yaml     # Task 2 output
├── AUDIT_TESTS_ROOT.yaml             # Task 3 output
├── AUDIT_TESTS_AGENTS.yaml           # Task 4 output
├── AUDIT_TESTS_CLI.yaml              # Task 5 output
├── AUDIT_TESTS_DOCS.yaml             # Task 6 output
├── AUDIT_TESTS_E2E.yaml              # Task 7 output
├── AUDIT_TESTS_FIXTURES.yaml         # Task 8 output
├── AUDIT_TESTS_INTEGRATION.yaml      # Task 9 output
├── AUDIT_TESTS_MCP.yaml              # Task 10 output
├── AUDIT_TESTS_OPERATIONS.yaml       # Task 11 output
├── AUDIT_TESTS_PLATFORM.yaml         # Task 12 output
├── AUDIT_TESTS_ROADMAP.yaml          # Task 13 output
├── AUDIT_TESTS_UNIT.yaml             # Task 14 output
├── AUDIT_TESTS_UTILS.yaml            # Task 15 output
├── AUDIT_TESTS_VALIDATION.yaml       # Task 16 output
├── COVERAGE_GAP_ANALYSIS.yaml        # Task 17 output
├── TEST_SUITE_AUDIT_SUMMARY.md       # Task 18 output
└── SPRINT_COMPLETION_REPORT.md       # Final summary
```
