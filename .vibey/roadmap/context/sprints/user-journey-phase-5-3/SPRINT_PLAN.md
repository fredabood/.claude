# Sprint 5.3: Integration Tests & CI Enforcement

## Sprint Overview

**Goal:** Implement end-to-end integration tests and configure CI to enforce quality gates.

**Theme:** Quality Enforcement & Automation

**Estimated Duration:** 4-5 sessions

**Prerequisites:** Phase 5.1 (Test Coverage) completed

---

## Background

Phase 5.1 achieved unit test coverage. This sprint adds:
1. Integration tests that exercise full workflows
2. CI configuration to enforce coverage and quality
3. Quality gates that block PRs failing standards

---

## Tasks

### Task 1: Design integration test strategy

**Objective:** Design integration test approach: what flows to test end-to-end, test data management, isolation strategy, performance considerations.

**Deliverables:**
- `INTEGRATION_TEST_STRATEGY.md` - Strategy document

**Strategy Components:**

1. **Test Scope:**
   - CLI → Operations → Storage flows
   - MCP → Operations → Storage flows
   - Cross-module interactions

2. **Test Data Management:**
   - Fixtures for common scenarios
   - Isolated test databases
   - Cleanup strategies

3. **Isolation:**
   - Process isolation for CLI tests
   - Database isolation per test
   - File system isolation (tmp directories)

4. **Performance:**
   - Acceptable test duration
   - Parallelization strategy
   - Slow test marking

**Key Flows to Test:**

| Flow | Description |
|------|-------------|
| Roadmap Lifecycle | Create track → sprints → tasks → complete |
| Session Workflow | Start session → work → capture context → end |
| Discovery Flow | Discover → version → diff → refresh |
| Audit Flow | Make changes → query audit → generate report |

**Acceptance Criteria:**
- [ ] Strategy documented
- [ ] Key flows identified
- [ ] Data management approach
- [ ] Isolation strategy
- [ ] Performance targets

---

### Task 2: Implement CLI integration tests

**Objective:** Write integration tests that exercise full CLI workflows: roadmap create → update → query → export flows.

**Deliverables:**
- `tests/integration/test_cli_workflows.py`

**Test Workflows:**

```python
class TestRoadmapWorkflow:
    """End-to-end roadmap management via CLI."""

    def test_full_roadmap_lifecycle(self, isolated_env):
        """Test complete roadmap lifecycle."""
        runner = CliRunner()

        # Initialize roadmap
        result = runner.invoke(cli, ['init'])
        assert result.exit_code == 0

        # Create track
        result = runner.invoke(cli, [
            'roadmap', 'create-track',
            '-n', 'Test Track',
            '--description', 'Test'
        ])
        assert result.exit_code == 0

        # Create sprint
        result = runner.invoke(cli, [
            'roadmap', 'create-sprint',
            '-t', track_id,
            '-n', 'Sprint 1'
        ])
        assert result.exit_code == 0

        # Create task
        result = runner.invoke(cli, [
            'roadmap', 'create-task',
            '-s', sprint_id,
            '--title', 'Task 1'
        ])
        assert result.exit_code == 0

        # Start task
        result = runner.invoke(cli, [
            'roadmap', 'start', task_slug
        ])
        assert result.exit_code == 0

        # Complete task
        result = runner.invoke(cli, [
            'roadmap', 'complete', task_slug
        ])
        assert result.exit_code == 0

        # Verify final state
        result = runner.invoke(cli, [
            'roadmap', 'show', '--format', 'json'
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['progress']['tasks_completed'] == 1
```

**Acceptance Criteria:**
- [ ] Roadmap lifecycle tested
- [ ] All CRUD operations tested
- [ ] Status transitions tested
- [ ] Error cases tested

---

### Task 3: Implement MCP integration tests

**Objective:** Write integration tests that exercise MCP server: tool invocation flows, resource access, error handling.

**Deliverables:**
- `tests/integration/test_mcp_workflows.py`

**Test Scenarios:**

```python
class TestMCPWorkflows:
    """End-to-end MCP server workflows."""

    async def test_tool_invocation_flow(self, mcp_server):
        """Test invoking tools via MCP protocol."""
        # Connect to server
        client = await mcp_server.connect()

        # List available tools
        tools = await client.list_tools()
        assert 'vibey_roadmap_show' in [t.name for t in tools]

        # Invoke tool
        result = await client.call_tool(
            'vibey_roadmap_show',
            {'format': 'json'}
        )
        assert result.success

    async def test_resource_access(self, mcp_server):
        """Test accessing resources via MCP."""
        client = await mcp_server.connect()

        # List resources
        resources = await client.list_resources()
        assert len(resources) > 0

        # Read resource
        content = await client.read_resource(
            'vibey://roadmap/current'
        )
        assert content is not None

    async def test_error_handling(self, mcp_server):
        """Test MCP error responses."""
        client = await mcp_server.connect()

        # Invalid tool
        with pytest.raises(MCPError):
            await client.call_tool('invalid_tool', {})

        # Invalid parameters
        with pytest.raises(MCPError):
            await client.call_tool(
                'vibey_roadmap_show',
                {'invalid_param': 'value'}
            )
```

**Acceptance Criteria:**
- [ ] Tool invocation tested
- [ ] Resource access tested
- [ ] Error handling tested
- [ ] Protocol compliance verified

---

### Task 4: Implement cross-module integration tests

**Objective:** Write tests that exercise interactions between modules: CLI → operations → roadmap → storage flows.

**Deliverables:**
- `tests/integration/test_cross_module.py`

**Test Scenarios:**

```python
class TestCrossModuleIntegration:
    """Tests that exercise multiple modules together."""

    def test_cli_to_database_roundtrip(self, isolated_env):
        """Test data flows correctly from CLI to database."""
        # Create via CLI
        runner = CliRunner()
        runner.invoke(cli, ['roadmap', 'create-task', ...])

        # Verify in database
        db = Database(isolated_env / '.vibey' / 'roadmap.db')
        task = db.get_task(task_id)
        assert task is not None
        assert task.status == 'not_started'

        # Verify in YAML
        yaml_path = isolated_env / '.vibey' / 'roadmap' / 'tasks' / f'{task_id}.yaml'
        assert yaml_path.exists()
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data['task']['status'] == 'not_started'

    def test_audit_trail_integration(self, isolated_env):
        """Test audit trail records all changes."""
        # Make changes via CLI
        runner = CliRunner()
        runner.invoke(cli, ['roadmap', 'start', task_slug])

        # Verify audit entry
        manager = AuditTrailManager(isolated_env)
        entries = manager.get_object_history(task_id)
        assert len(entries) == 1
        assert entries[0].field == 'status'
        assert entries[0].new_value == 'in_progress'
```

**Acceptance Criteria:**
- [ ] CLI → DB flows tested
- [ ] Audit integration tested
- [ ] Context integration tested
- [ ] Session integration tested

---

### Task 5: Configure CI coverage enforcement

**Objective:** Update CI configuration to: run full test suite, generate coverage report, fail if coverage drops below threshold (100% line, 100% branch).

**Deliverables:**
- `.github/workflows/test.yml` - Updated workflow
- `pyproject.toml` - Coverage configuration

**CI Configuration:**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov=vibey \
                 --cov-report=xml \
                 --cov-report=term-missing \
                 --cov-fail-under=100

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
```

**Acceptance Criteria:**
- [ ] CI runs on push and PR
- [ ] Coverage report generated
- [ ] Fails below 100% threshold
- [ ] Coverage uploaded to service

---

### Task 6: Configure CI quality gates

**Objective:** Add CI quality gates: lint checks, type checks, doc freshness checks, no new warnings. Fail PR if gates fail.

**Deliverables:**
- Updated `.github/workflows/quality.yml`

**Quality Gates:**

```yaml
# .github/workflows/quality.yml
name: Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install ruff
      - run: ruff check vibey/ tests/

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install mypy
      - run: mypy vibey/

  docs-freshness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check CLI docs match implementation
        run: |
          python scripts/check_cli_docs.py

  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: pytest tests/integration/
```

**Acceptance Criteria:**
- [ ] Lint check configured
- [ ] Type check configured
- [ ] Doc freshness check configured
- [ ] Integration tests in CI
- [ ] All gates block PR on failure

---

### Task 7: Document test maintenance procedures

**Objective:** Create guide for maintaining tests: when to add tests, how to handle coverage drops, test review criteria.

**Deliverables:**
- `docs/development/TEST_MAINTENANCE.md`

**Guide Content:**

```markdown
# Test Maintenance Guide

## When to Add Tests

### Required
- All new code paths
- Bug fixes (regression test)
- New features

### Coverage Rules
- No PR may reduce coverage
- New code must have 100% coverage
- Exclusions require justification

## How to Handle Coverage Drops

1. Identify uncovered code in CI output
2. Add missing tests
3. If code is unreachable, add `# pragma: no cover`
4. Document reason in PR

## Test Review Criteria

### Structure
- [ ] Tests are in correct directory
- [ ] Test names are descriptive
- [ ] Fixtures used appropriately

### Quality
- [ ] Tests are isolated
- [ ] Tests are deterministic
- [ ] Edge cases covered
- [ ] Error paths tested

### Performance
- [ ] Tests run quickly (< 100ms each)
- [ ] No unnecessary I/O
- [ ] Fixtures are efficient

## Running Tests Locally

```bash
# All tests
pytest

# With coverage
pytest --cov=vibey --cov-report=html

# Integration only
pytest tests/integration/

# Specific module
pytest tests/operations/roadmap/
```
```

**Acceptance Criteria:**
- [ ] Guide complete
- [ ] Examples provided
- [ ] Commands documented
- [ ] Review criteria clear

---

## Task Dependencies

```
Task 1 (Strategy)
    ↓
Tasks 2, 3, 4 (Integration tests) - can run in parallel
    ↓
Tasks 5, 6 (CI) - can run in parallel
    ↓
Task 7 (Documentation)
```

---

## Success Criteria

- [ ] Integration test strategy documented
- [ ] CLI integration tests complete
- [ ] MCP integration tests complete
- [ ] Cross-module tests complete
- [ ] CI coverage enforcement working
- [ ] CI quality gates working
- [ ] Test maintenance guide complete

---

## File Changes Summary

**New Files:**
- `tests/integration/test_cli_workflows.py`
- `tests/integration/test_mcp_workflows.py`
- `tests/integration/test_cross_module.py`
- `docs/development/TEST_MAINTENANCE.md`
- `.github/workflows/test.yml`
- `.github/workflows/quality.yml`

**Modified Files:**
- `pyproject.toml` - Test configuration

---

## Notes

This sprint establishes the quality enforcement infrastructure that will maintain code quality going forward.
