# Sprint 5.1: Test Coverage Implementation

## Sprint Overview

**Goal:** Fill all test coverage gaps identified in Phase 1.4 Test Suite Audit, achieving 100% code coverage.

**Theme:** Test Completeness

**Estimated Duration:** 6-8 sessions

**Prerequisites:** Phase 4 completed (all features implemented)

---

## Background

Phase 1.4 audited the test suite and identified coverage gaps. This sprint systematically fills those gaps to achieve complete test coverage.

**Target Coverage:**
- Line coverage: 100%
- Branch coverage: 100%
- All modules covered

---

## Tasks

### Task 1: Prioritize coverage gaps

**Objective:** Using TEST_COVERAGE_GAPS.yaml from Phase 1, prioritize which gaps to fill first based on: code criticality, bug risk, complexity.

**Deliverables:**
- `TEST_PRIORITY.yaml` - Prioritized gap list

**Prioritization Criteria:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Criticality | 3x | Core business logic = high |
| Bug Risk | 2x | Complex code = high risk |
| Complexity | 1x | Simple to test = do first |

**Priority Formula:**
```
Priority = (Criticality * 3) + (Bug Risk * 2) - Complexity
```

**Output Format:**
```yaml
test_priority:
  - module: vibey/operations/roadmap/update.py
    current_coverage: 45%
    criticality: high
    bug_risk: high
    complexity: medium
    priority_score: 12
    estimated_tests: 15
    estimated_hours: 4

  - module: vibey/cli/commands.py
    current_coverage: 60%
    criticality: high
    bug_risk: medium
    complexity: high
    priority_score: 9
    estimated_tests: 25
    estimated_hours: 8
```

**Acceptance Criteria:**
- [ ] All gaps from Phase 1.4 included
- [ ] Priority scores calculated
- [ ] Sorted by priority
- [ ] Effort estimates provided

---

### Task 2: Write tests for vibey/common/

**Objective:** Fill all test coverage gaps in common module. Focus on error types, utility functions, edge cases.

**Deliverables:**
- `tests/common/test_errors.py`
- `tests/common/test_utils.py`
- Additional test files as needed

**Modules to Cover:**
- `vibey/common/errors.py` - Error types and rendering
- `vibey/common/utils.py` - Utility functions
- Any other common modules

**Test Focus Areas:**
1. Error instantiation and attributes
2. Error rendering for different targets
3. Utility function edge cases
4. Input validation
5. Error propagation

**Test Patterns:**
```python
class TestVibeyError:
    def test_error_creation(self):
        """Test error can be created with message."""

    def test_error_context(self):
        """Test error includes context."""

    def test_error_rendering_cli(self):
        """Test error renders correctly for CLI."""

    def test_error_rendering_mcp(self):
        """Test error renders correctly for MCP."""
```

**Acceptance Criteria:**
- [ ] All common modules at 100% coverage
- [ ] Edge cases tested
- [ ] Error paths tested
- [ ] Tests are fast and isolated

---

### Task 3: Write tests for vibey/cli/

**Objective:** Fill all test coverage gaps in CLI module. Focus on command behavior, error handling, output formatting.

**Deliverables:**
- `tests/cli/test_commands.py`
- `tests/cli/test_main.py`
- Additional test files as needed

**Modules to Cover:**
- `vibey/cli/main.py` - CLI entry point
- `vibey/cli/commands.py` - Command implementations
- `vibey/cli/roadmap_lib/` - CLI utilities

**Test Focus Areas:**
1. Command argument parsing
2. Command execution paths
3. Error handling and messages
4. Output formatting
5. Exit codes

**Test Patterns:**
```python
from click.testing import CliRunner

class TestRoadmapCommands:
    def test_roadmap_show_success(self, tmp_path):
        """Test roadmap show command succeeds."""
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'show'])
        assert result.exit_code == 0

    def test_roadmap_show_not_found(self, tmp_path):
        """Test roadmap show handles missing roadmap."""
        runner = CliRunner()
        result = runner.invoke(cli, ['roadmap', 'show'])
        assert result.exit_code == 1
        assert 'not found' in result.output.lower()
```

**Acceptance Criteria:**
- [ ] All CLI modules at 100% coverage
- [ ] All commands tested
- [ ] Error cases tested
- [ ] Output verified

---

### Task 4: Write tests for vibey/mcp/ and vibey/adapters/

**Objective:** Fill all test coverage gaps in MCP and adapter modules. Focus on protocol compliance, tool behavior, adapter contracts.

**Deliverables:**
- `tests/mcp/test_server.py`
- `tests/mcp/test_tools.py`
- `tests/adapters/test_*.py`

**Modules to Cover:**
- `vibey/mcp/server.py` - MCP server
- `vibey/mcp/tools.py` - MCP tools (if separate)
- `vibey/adapters/*.py` - Platform adapters

**Test Focus Areas:**
1. MCP protocol compliance
2. Tool request/response handling
3. Error responses
4. Adapter interface contracts
5. Cross-adapter consistency

**Test Patterns:**
```python
class TestMCPServer:
    def test_tool_discovery(self):
        """Test server exposes correct tools."""

    def test_tool_invocation(self):
        """Test tool can be invoked correctly."""

    def test_tool_error_handling(self):
        """Test tool returns proper error response."""

class TestAdapter:
    def test_adapter_interface(self):
        """Test adapter implements required interface."""
```

**Acceptance Criteria:**
- [ ] MCP server at 100% coverage
- [ ] All tools tested
- [ ] All adapters tested
- [ ] Protocol compliance verified

---

### Task 5: Write tests for vibey/operations/

**Objective:** Fill all test coverage gaps in operations module. Focus on business logic correctness, edge cases, error handling.

**Deliverables:**
- `tests/operations/roadmap/test_*.py`
- `tests/operations/context/test_*.py`
- `tests/operations/discovery/test_*.py`

**Modules to Cover:**
- `vibey/operations/roadmap/` - Roadmap operations
- `vibey/operations/context/` - Context operations
- `vibey/operations/discovery/` - Discovery operations
- `vibey/operations/docs/` - Documentation operations

**Test Focus Areas:**
1. Business logic correctness
2. State transitions
3. Edge cases and boundaries
4. Error conditions
5. Concurrent access (if applicable)

**Test Patterns:**
```python
class TestRoadmapUpdate:
    def test_start_task(self, roadmap_fixture):
        """Test starting a task updates status correctly."""

    def test_start_already_started(self, roadmap_fixture):
        """Test starting already-started task raises error."""

    def test_complete_task(self, roadmap_fixture):
        """Test completing task updates status and timestamps."""

    def test_complete_not_started(self, roadmap_fixture):
        """Test completing not-started task raises error."""
```

**Acceptance Criteria:**
- [ ] All operations modules at 100% coverage
- [ ] Business logic fully tested
- [ ] Edge cases covered
- [ ] Error paths tested

---

### Task 6: Write tests for vibey/roadmap/

**Objective:** Fill all test coverage gaps in roadmap module. Focus on model validation, serialization round-trips, query correctness.

**Deliverables:**
- `tests/roadmap/models/test_*.py`
- `tests/roadmap/serialization/test_*.py`
- `tests/roadmap/test_database.py`

**Modules to Cover:**
- `vibey/roadmap/models/` - Data models
- `vibey/roadmap/serialization/` - YAML/SQL serialization
- `vibey/roadmap/database.py` - Database operations

**Test Focus Areas:**
1. Model validation
2. Serialization round-trips (YAML → Python → YAML)
3. Database round-trips (Python → SQL → Python)
4. Query correctness
5. Constraint enforcement

**Test Patterns:**
```python
class TestTrackModel:
    def test_track_creation(self):
        """Test track can be created with required fields."""

    def test_track_validation(self):
        """Test track validates required fields."""

    def test_track_serialization_roundtrip(self):
        """Test track survives YAML serialization."""

class TestSQLLoader:
    def test_load_tracks(self, db_fixture):
        """Test tracks load correctly from database."""

    def test_load_with_relations(self, db_fixture):
        """Test related entities load correctly."""
```

**Acceptance Criteria:**
- [ ] All model tests complete
- [ ] All serializers tested
- [ ] Round-trip tests pass
- [ ] Database operations tested

---

### Task 7: Verify 100% coverage achieved

**Objective:** Run full coverage report and verify 100% line and branch coverage. Document any intentional exclusions.

**Deliverables:**
- `COVERAGE_REPORT.md` - Final coverage report
- Updated `.coveragerc` with exclusions

**Verification Steps:**
1. Run full test suite with coverage
2. Generate HTML and terminal reports
3. Review any uncovered lines
4. Either add tests or document exclusion
5. Verify branch coverage

**Coverage Commands:**
```bash
# Run tests with coverage
pytest --cov=vibey --cov-report=html --cov-report=term-missing

# Check for uncovered lines
coverage report --show-missing

# Fail if below threshold
pytest --cov=vibey --cov-fail-under=100
```

**Acceptable Exclusions:**
- `# pragma: no cover` for:
  - Defensive code that can't be reached in tests
  - Platform-specific code on other platforms
  - Debug/development code

**Acceptance Criteria:**
- [ ] 100% line coverage achieved
- [ ] 100% branch coverage achieved
- [ ] Any exclusions documented and justified
- [ ] Coverage report generated
- [ ] CI configured to enforce

---

## Task Dependencies

```
Task 1 (Prioritize)
    ↓
Tasks 2-6 (Write tests) - order by priority from Task 1
    ↓
Task 7 (Verify) - after all tests written
```

---

## Success Criteria

- [ ] Coverage gaps prioritized
- [ ] vibey/common/ at 100%
- [ ] vibey/cli/ at 100%
- [ ] vibey/mcp/ and vibey/adapters/ at 100%
- [ ] vibey/operations/ at 100%
- [ ] vibey/roadmap/ at 100%
- [ ] Overall coverage verified at 100%

---

## File Changes Summary

**New/Updated Test Files:**
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

**Updated Config:**
- `.coveragerc` - Coverage configuration
- `pyproject.toml` - Test configuration

---

## Notes

This is the largest sprint in terms of effort. Consider splitting across multiple sessions with clear module boundaries.
