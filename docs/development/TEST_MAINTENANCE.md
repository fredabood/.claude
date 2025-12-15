# Test Maintenance Guide

This guide documents procedures for maintaining and extending the Vibey test suite.

## Test Organization

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── roadmap/            # Roadmap module tests
│   ├── operations/         # Operations module tests
│   └── cli/                # CLI module tests
├── integration/            # Cross-module integration tests
│   ├── test_cli_workflows.py
│   ├── test_mcp_workflows.py
│   └── test_cross_module.py
└── conftest.py             # Shared fixtures
```

## When to Add Tests

### Required (Always)

1. **New code paths** - Every new function, method, or class needs tests
2. **Bug fixes** - Add a regression test that fails before the fix
3. **New features** - Tests for all public APIs and edge cases
4. **Refactoring** - Ensure existing tests still pass; add new ones if behavior changes

### Coverage Rules

- **No PR may reduce coverage** - CI will fail if coverage drops
- **New code must have 100% coverage** - All branches and lines
- **Exclusions require justification** - Document why with `# pragma: no cover`

## How to Handle Coverage Drops

### Step 1: Identify Uncovered Code

```bash
# Run tests with coverage report
pytest --cov=vibey --cov-report=term-missing

# Generate HTML report for detailed view
pytest --cov=vibey --cov-report=html
open htmlcov/index.html
```

### Step 2: Add Missing Tests

Create tests for the uncovered lines. Focus on:
- Branch conditions (if/else paths)
- Error handling paths
- Edge cases

### Step 3: Mark Unreachable Code

If code is truly unreachable (defensive coding), add:

```python
# This branch handles a case that can't occur in practice
if impossible_condition:  # pragma: no cover
    raise RuntimeError("This should never happen")
```

### Step 4: Document in PR

Explain any coverage exclusions in the PR description.

## Test Review Criteria

### Structure

- [ ] Tests are in the correct directory (unit vs integration)
- [ ] Test names are descriptive (`test_<what>_<condition>`)
- [ ] Fixtures used appropriately (not duplicated across tests)
- [ ] Test classes group related tests

### Quality

- [ ] Tests are isolated (no shared mutable state)
- [ ] Tests are deterministic (no flaky tests)
- [ ] Edge cases covered (empty inputs, boundaries, errors)
- [ ] Error paths tested (exceptions, validation failures)

### Performance

- [ ] Tests run quickly (< 100ms each for unit tests)
- [ ] No unnecessary I/O (use mocks or fixtures)
- [ ] Fixtures are efficient (setup once, reuse)
- [ ] Slow tests marked with `@pytest.mark.slow`

## Running Tests Locally

### Full Test Suite

```bash
# All tests with coverage
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=vibey --cov-report=html
```

### Specific Tests

```bash
# Single file
pytest tests/unit/roadmap/test_models.py

# Single test class
pytest tests/unit/roadmap/test_models.py::TestTask

# Single test method
pytest tests/unit/roadmap/test_models.py::TestTask::test_create

# By pattern
pytest -k "test_create"
```

### Integration Tests Only

```bash
pytest tests/integration/ -v
```

### Watch Mode (with pytest-watch)

```bash
pip install pytest-watch
ptw tests/unit/
```

## Writing Good Tests

### Test Structure (AAA Pattern)

```python
def test_task_status_transition():
    # Arrange - set up test data
    task = Task(id="task-001", status="not_started")

    # Act - perform the action
    task.start()

    # Assert - verify the result
    assert task.status == "in_progress"
    assert task.started is not None
```

### Using Fixtures

```python
@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test-task-001",
        title="Test Task",
        status="not_started"
    )

def test_task_completion(sample_task):
    sample_task.start()
    sample_task.complete()
    assert sample_task.status == "completed"
```

### Testing Exceptions

```python
def test_invalid_transition_raises():
    task = Task(id="task-001", status="not_started")

    with pytest.raises(InvalidTransitionError) as exc_info:
        task.complete()  # Can't complete without starting

    assert "must be started first" in str(exc_info.value)
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result.success
```

### Parameterized Tests

```python
@pytest.mark.parametrize("status,expected", [
    ("not_started", False),
    ("in_progress", False),
    ("completed", True),
])
def test_is_complete(status, expected):
    task = Task(id="task-001", status=status)
    assert task.is_complete == expected
```

## CI Integration

### Test Workflow

Tests run automatically on:
- Push to `main`
- Pull requests to `main`

### Coverage Requirements

- Minimum coverage: 90% (configurable in `pyproject.toml`)
- CI fails if coverage drops below threshold

### Quality Gates

- Lint check (ruff)
- Type check (mypy)
- Security scan (bandit)
- Doc freshness check

## Troubleshooting

### Common Issues

**"Test not found"**
- Check test file starts with `test_`
- Check test function starts with `test_`
- Check test class starts with `Test`

**"Import error"**
- Ensure `__init__.py` exists in test directories
- Check PYTHONPATH includes project root
- Install package in dev mode: `pip install -e ".[dev]"`

**"Fixture not found"**
- Check fixture is defined in same file or `conftest.py`
- Check fixture name matches parameter name
- Check `conftest.py` is in test path

**"Async test not running"**
- Add `@pytest.mark.asyncio` decorator
- Ensure `pytest-asyncio` is installed
- Check `asyncio_mode` in `pyproject.toml`

### Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

## Adding New Test Categories

1. Create directory under `tests/`
2. Add `__init__.py`
3. Add tests following naming conventions
4. Update `pytest.ini` or `pyproject.toml` if needed
5. Add to CI workflow if separate job needed

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
