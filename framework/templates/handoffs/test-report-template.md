# Test Report: {{ feature_name }}

**Created by:** {{ config.roles.test_engineer or 'Test Engineer' }}
**Date:** {{ report_date }}
**For:** {{ next_role }}

---

## Test Summary

**Feature:** {{ feature_name }}
**Test Framework:** {{ test_framework }}
**Test Files:** {{ test_files_count }} files created
**Total Tests:** {{ total_tests }} tests
**Pass Rate:** {{ tests_passed }}/{{ total_tests }} ({{ pass_rate_percentage }}%)
**Coverage:** {{ test_coverage }}%

**Status:** {{ test_status }}

---

## Test Files Created

{% for test_file in test_files %}
### {{ test_file.category }}

**File:** `{{ test_file.path }}`
**Tests:** {{ test_file.test_count }} tests
**Coverage:** {{ test_file.coverage }}%

**Test Cases:**
{% for test_case in test_file.test_cases %}
- {{ test_case.status }} {{ test_case.name }} - {{ test_case.description }}
{% endfor %}

{% endfor %}

---

## Test Coverage Report

{% if config.technology_stack.backend.language == 'python' %}
```
{{ coverage_report_output }}

Example:
----------- coverage: platform darwin, python 3.9.x -----------
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
{{ project_name }}/{{ module_name }}.py         XX      X    XX%
tests/test_{{ module_name }}.py                 XX      0   100%
---------------------------------------------------------
TOTAL                                           XX      X    XX%

Required minimum coverage: {{ config.coding_standards.test_coverage.minimum or 90 }}%
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```
{{ coverage_report_output }}

Example:
----------------------|---------|----------|---------|---------|-------------------
File                  | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
----------------------|---------|----------|---------|---------|-------------------
All files             |   {{ overall_coverage }}% |    {{ branch_coverage }}% |   {{ function_coverage }}% |   {{ line_coverage }}% |
 {{ module_name }}.ts |   {{ module_coverage }}% |    {{ module_branch_coverage }}% |   {{ module_function_coverage }}% |   {{ module_line_coverage }}% |
----------------------|---------|----------|---------|---------|-------------------

Required minimum coverage: {{ config.coding_standards.test_coverage.minimum or 90 }}%
```
{% elif config.technology_stack.backend.language == 'java' %}
```
{{ coverage_report_output }}

Example:
Package: {{ package_name }}
  {{ class_name }}.java                    XX%    (XX/XX lines)

OVERALL COVERAGE:                          XX%
```
{% elif config.technology_stack.backend.language == 'go' %}
```
{{ coverage_report_output }}

Example:
ok      {{ module_path }}    X.XXXs  coverage: XX.X% of statements

Required minimum coverage: {{ config.coding_standards.test_coverage.minimum or 90 }}%
```
{% endif %}

**Coverage Breakdown:**
- Line Coverage: {{ line_coverage }}%
- Branch Coverage: {{ branch_coverage }}%
- Function/Method Coverage: {{ function_coverage }}%

**Coverage Status:** {{ coverage_status }}

---

## Test Execution Results

{% if config.technology_stack.backend.language == 'python' %}
```bash
$ pytest {{ test_command_args }}

{{ test_execution_output }}

Example:
========================= test session starts ==========================
platform darwin -- Python 3.9.x, pytest-7.x.x, pluggy-1.x.x
collected XX items

tests/test_{{ module_name }}.py ........                        [100%]

========================== XX passed in X.XXs ==========================
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```bash
$ npm test {{ test_command_args }}

{{ test_execution_output }}

Example:
 PASS  tests/{{ module_name }}.test.ts
  ✓ test case 1 (X ms)
  ✓ test case 2 (X ms)

Test Suites: X passed, X total
Tests:       XX passed, XX total
Snapshots:   X total
Time:        X.XXXs
Ran all test suites.
```
{% elif config.technology_stack.backend.language == 'java' %}
```bash
$ mvn test {{ test_command_args }}

{{ test_execution_output }}

Example:
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running {{ package_name }}.{{ class_name }}Test
[INFO] Tests run: XX, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] Results:
[INFO]
[INFO] Tests run: XX, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
```
{% elif config.technology_stack.backend.language == 'go' %}
```bash
$ go test {{ test_command_args }}

{{ test_execution_output }}

Example:
PASS
coverage: XX.X% of statements
ok      {{ module_path }}    X.XXXs
```
{% endif %}

**Execution Time:** {{ execution_time }} seconds

---

{% if test_utilities_created %}
## Test Utilities Created

{% for utility in test_utilities %}
### {{ utility.name }}

**File:** `{{ utility.path }}`

**Purpose:** {{ utility.purpose }}

**Usage Example:**
{% if config.technology_stack.backend.language == 'python' %}
```python
{{ utility.usage_example }}
```
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
```typescript
{{ utility.usage_example }}
```
{% elif config.technology_stack.backend.language == 'java' %}
```java
{{ utility.usage_example }}
```
{% elif config.technology_stack.backend.language == 'go' %}
```go
{{ utility.usage_example }}
```
{% endif %}

{% endfor %}

---
{% endif %}

## Test Categories

### Unit Tests
**Count:** {{ unit_tests_count }}
**Coverage:** {{ unit_tests_coverage }}%
**Status:** {{ unit_tests_status }}

**Key Tests:**
{% for test in key_unit_tests %}
- {{ test.name }} - {{ test.description }}
{% endfor %}

### Integration Tests
**Count:** {{ integration_tests_count }}
**Coverage:** {{ integration_tests_coverage }}%
**Status:** {{ integration_tests_status }}

**Key Tests:**
{% for test in key_integration_tests %}
- {{ test.name }} - {{ test.description }}
{% endfor %}

{% if e2e_tests_count > 0 %}
### End-to-End Tests
**Count:** {{ e2e_tests_count }}
**Status:** {{ e2e_tests_status }}

**Key Tests:**
{% for test in key_e2e_tests %}
- {{ test.name }} - {{ test.description }}
{% endfor %}
{% endif %}

{% if performance_tests_count > 0 %}
### Performance Tests
**Count:** {{ performance_tests_count }}
**Status:** {{ performance_tests_status }}

**Key Metrics:**
{% for metric in performance_metrics %}
- {{ metric.name }}: {{ metric.value }} (threshold: {{ metric.threshold }})
{% endfor %}
{% endif %}

---

## Edge Cases Tested

### Null/Undefined Handling
{{ null_handling_tests }}

### Validation
{{ validation_tests }}

### Error Scenarios
{{ error_scenario_tests }}

### Boundary Conditions
{{ boundary_condition_tests }}

{% if config.project.type == 'web-app' %}
### Browser Compatibility (if applicable)
{{ browser_compatibility_tests }}
{% endif %}

---

## Quality Metrics

**Test Framework:** {{ test_framework }}
{% if config.technology_stack.backend.language == 'python' %}
- ✅ pytest best practices followed
- {{ '✅' if uses_fixtures else '❌' }} Fixtures used for test data
- {{ '✅' if uses_parametrize else '❌' }} Parametrize used for similar tests
- {{ '✅' if uses_markers else '❌' }} Test markers applied
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
- ✅ Jest/Vitest best practices followed
- {{ 'mocks_used' if uses_mocks else '❌' }} Properly mocked dependencies
- {{ 'arrange_act_assert' if uses_aaa_pattern else '❌' }} Arrange-Act-Assert pattern
- {{ 'describe_blocks' if uses_describe_blocks else '❌' }} Tests organized with describe blocks
{% elif config.technology_stack.backend.language == 'java' %}
- ✅ JUnit 5 (Jupiter) used
- {{ 'mockito_used' if uses_mockito else '❌' }} Properly mocked dependencies (Mockito)
- {{ 'display_names' if uses_display_names else '❌' }} Descriptive test names (@DisplayName)
- {{ 'nested_tests' if uses_nested_tests else '❌' }} Tests organized logically (@Nested)
{% elif config.technology_stack.backend.language == 'go' %}
- ✅ Go testing best practices followed
- {{ 'table_driven' if uses_table_driven else '❌' }} Table-driven tests used
- {{ 'subtests' if uses_subtests else '❌' }} Subtests for related cases
- {{ 'testify' if uses_testify else '❌' }} Testify assertions (if applicable)
{% endif %}

**No Flaky Tests:** {{ 'flaky_tests' if has_flaky_tests else 'no_flaky_tests' }}
**Deterministic:** {{ 'deterministic' if is_deterministic else 'not_deterministic' }}
**Fast Execution:** {{ 'fast' if is_fast else 'slow' }} ({{ execution_time }}s)

---

## Mocking Strategy

{% if config.project.type == 'api' or config.project.type == 'web-app' %}
**External APIs:** {{ api_mocking_strategy }}
**Database:** {{ database_mocking_strategy }}
**File System:** {{ filesystem_mocking_strategy }}
**Time/Dates:** {{ time_mocking_strategy }}

{% elif config.project.type == 'data-platform' %}
**Data Sources:** {{ data_source_mocking_strategy }}
**Storage:** {{ storage_mocking_strategy }}
**External APIs:** {{ api_mocking_strategy }}

{% elif config.project.type == 'ml' %}
**Model Training:** {{ model_training_mocking_strategy }}
**Data Loading:** {{ data_loading_mocking_strategy }}
**Feature Store:** {{ feature_store_mocking_strategy }}
**ML Platform ({{ config.ml_platform.experiment_tracking }}):** {{ ml_platform_mocking_strategy }}

{% endif %}

---

## Known Gaps

**Not Tested:**
{{ untested_code_list }}

**Reason:** {{ gap_reason }}

**Plan:** {{ gap_mitigation_plan }}

**Coverage Impact:** {{ gap_coverage_impact }}%

---

## Test Maintenance Notes

**Test Data Management:**
{{ test_data_management_notes }}

**Test Dependencies:**
{{ test_dependencies_notes }}

**Flakiness Prevention:**
{{ flakiness_prevention_notes }}

**Performance Considerations:**
{{ performance_considerations_notes }}

---

## Continuous Integration

**CI Platform:** {{ config.ci_cd.platform or 'GitHub Actions' }}

**Test Command:**
```bash
{{ ci_test_command }}
```

**Coverage Reporting:**
{{ coverage_reporting_method }}

**Failure Notifications:**
{{ failure_notification_method }}

---

## Ready for Next Step

- [{{ 'x' if all_tests_passing else ' ' }}] All tests passing
- [{{ 'x' if coverage_meets_threshold else ' ' }}] Coverage ≥ {{ config.coding_standards.test_coverage.minimum or 90 }}%
- [{{ 'x' if no_flaky_tests else ' ' }}] No flaky tests
- [{{ 'x' if test_utilities_created else ' ' }}] Test utilities created (if needed)
- [{{ 'x' if edge_cases_covered else ' ' }}] Edge cases covered
- [{{ 'x' if error_scenarios_tested else ' ' }}] Error scenarios tested
- [{{ 'x' if ci_integration_complete else ' ' }}] CI integration complete

**Overall Status:** {{ overall_readiness_status }}

**Next Agent:** {{ next_agent }}

**Handoff Location:** `{{ handoff_file_path }}`

---

## Appendix: Detailed Test List

{% for test_file in detailed_test_list %}
### {{ test_file.name }}

{% for test in test_file.tests %}
**{{ loop.index }}. {{ test.name }}**
- Description: {{ test.description }}
- Type: {{ test.type }}
- Execution Time: {{ test.execution_time }}ms
- Status: {{ test.status }}

{% endfor %}
{% endfor %}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
