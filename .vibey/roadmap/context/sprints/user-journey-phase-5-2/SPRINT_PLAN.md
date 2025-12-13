# Sprint 5.2: Documentation Sync (Post-Testing)

## Sprint Overview

**Goal:** Update documentation after Test Coverage Implementation to reflect new test files and coverage metrics.

**Theme:** Documentation Checkpoint

**Estimated Duration:** 1 session

**Prerequisites:** Phase 5.1 (Test Coverage Implementation) completed

---

## Background

Phase 5.1 added significant test coverage across all modules. This checkpoint updates documentation to reflect:
- New test files added
- Coverage metrics achieved
- Testing patterns established

---

## Tasks

### Task 1: Update file inventory with new test files

**Objective:** Add all new test files from Phase 5.1 to Phase 1 file inventory.

**Deliverables:**
- Updated file inventory

**Test Files to Add:**
- `tests/common/test_errors.py`
- `tests/common/test_utils.py`
- `tests/cli/test_commands.py`
- `tests/cli/test_main.py`
- `tests/mcp/test_server.py`
- `tests/adapters/test_*.py`
- `tests/operations/roadmap/test_*.py`
- `tests/operations/context/test_*.py`
- `tests/roadmap/models/test_*.py`
- `tests/roadmap/serialization/test_*.py`

**Acceptance Criteria:**
- [ ] All new test files added
- [ ] Line counts accurate
- [ ] Categories correct

---

### Task 2: Update test suite audit with coverage data

**Objective:** Update Phase 1.4 Test Suite Audit deliverables with new coverage metrics.

**Deliverables:**
- Updated test audit documents

**Updates Required:**
1. Update TEST_COVERAGE_GAPS.yaml:
   - Mark all gaps as filled
   - Update coverage percentages

2. Update TEST_SUITE_AUDIT.md:
   - Add section on Phase 5.1 coverage work
   - Include final coverage metrics
   - Document test patterns used

3. Create COVERAGE_FINAL_REPORT.md:
   - Module-by-module coverage
   - Any exclusions and justifications
   - Comparison: before vs after

**Acceptance Criteria:**
- [ ] Coverage gaps marked complete
- [ ] Final metrics documented
- [ ] Before/after comparison

---

### Task 3: Update Contributor Walkthrough with test info

**Objective:** Add testing guidance and coverage requirements to Contributor walkthrough.

**Deliverables:**
- Updated `docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md`

**New Content:**

```markdown
## Testing Your Changes

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vibey --cov-report=term-missing

# Run specific module tests
pytest tests/operations/roadmap/
```

### Coverage Requirements
- All new code must have tests
- Coverage must not decrease
- CI will block PRs that reduce coverage

### Test Patterns
- Use fixtures from `tests/conftest.py`
- Follow existing test structure
- Include edge cases and error paths

### Before Submitting
1. Run full test suite
2. Check coverage report
3. Ensure no coverage regression
```

**Acceptance Criteria:**
- [ ] Testing section added
- [ ] Commands accurate
- [ ] Requirements clear
- [ ] Patterns documented

---

### Task 4: Update CLI Reference with test commands

**Objective:** Document test-related CLI commands and flags added in Phase 5.1.

**Deliverables:**
- Updated `docs/reference/CLI_REFERENCE.md`

**Commands to Document (if implemented):**

```bash
# Test running commands
vibey test [--coverage] [--unit] [--integration]
# Run test suite with options

vibey coverage report [--format html|term|json]
# Generate coverage report

vibey coverage check [--threshold PERCENT]
# Check coverage meets threshold
```

**Note:** If test commands are not exposed via CLI, document pytest equivalents and reference them.

**Acceptance Criteria:**
- [ ] Test commands documented (or pytest equivalents)
- [ ] Coverage options explained
- [ ] Examples provided

---

### Task 5: Update MCP Reference with test-related tools

**Objective:** Document any test/coverage-related MCP tools or resources.

**Deliverables:**
- Updated `docs/reference/MCP_REFERENCE.md`

**Tools/Resources to Document (if implemented):**

```yaml
# Tools
vibey_test_run:
  description: Run test suite
  parameters:
    - scope: unit|integration|all
    - coverage: boolean

vibey_coverage_report:
  description: Get coverage report
  parameters:
    - format: json|summary

# Resources
vibey://coverage/current:
  description: Current test coverage metrics
vibey://tests/status:
  description: Latest test run status
```

**Note:** If no test-related MCP tools exist, document that testing is CLI-only.

**Acceptance Criteria:**
- [ ] Test-related MCP tools documented (or noted as CLI-only)
- [ ] Coverage resources documented
- [ ] Cross-reference to CLI Reference

---

### Task 6: Update User Journeys with testing workflows

**Objective:** Add testing workflows to relevant user journeys.

**Deliverables:**
- Updated journey files

**Journeys to Update:**

| Journey | New Content |
|---------|-------------|
| Contributor | "Running tests before submitting" workflow |
| Active Developer | "Checking test coverage" workflow |
| Project Lead | "Reviewing test coverage reports" workflow |

**Acceptance Criteria:**
- [ ] Testing workflows added to 3 journeys
- [ ] Commands accurate
- [ ] Flows complete

---

### Task 7: Update Coverage Matrix with test features

**Objective:** Ensure coverage matrix reflects all test-related commands and features.

**Deliverables:**
- Updated `docs/journeys/COVERAGE_MATRIX.md`

**New Features to Map:**

| Feature | CLI Commands | MCP Tools | Relevant Journeys |
|---------|--------------|-----------|-------------------|
| Test Running | test, pytest | vibey_test_run | Contributor, Active Developer |
| Coverage Reporting | coverage report, coverage check | vibey_coverage_report | Active Developer, Project Lead |

**Acceptance Criteria:**
- [ ] All test commands in matrix
- [ ] MCP tools mapped (or noted as N/A)
- [ ] Commands mapped to journeys
- [ ] Coverage statistics updated

---

## Task Dependencies

```
Task 1 (File Inventory) - first
    ↓
Tasks 2-7 - can run in parallel
```

---

## Success Criteria

**Phase 1 Updates:**
- [ ] File inventory includes all test files
- [ ] Test Suite Audit (1.4) updated with final metrics

**Phase 2 Updates:**
- [ ] CLI Reference includes test commands
- [ ] MCP Reference includes test tools (or documents CLI-only)
- [ ] User Journeys include testing workflows
- [ ] Contributor Walkthrough includes testing guidance
- [ ] Coverage Matrix maps test features

---

## Notes

This is a lightweight checkpoint focused on keeping documentation current with test coverage work.
