# Vibey Framework Testing Guide

Comprehensive guide for testing the Vibey Agent Framework.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Running Tests](#running-tests)
- [Test Utilities](#test-utilities)
- [Coverage Reporting](#coverage-reporting)
- [CI/CD Integration](#ci-cd-integration)
- [Best Practices](#best-practices)

## Overview

The Vibey framework test suite validates framework functionality before multi-platform expansion. It includes:

- **200+ tests** across unit, integration, E2E, and platform categories
- **4 test utilities** for repository creation, state validation, git validation, and metrics tracking
- **>90% code coverage** requirement
- **Automated CI/CD** testing on all PRs and commits

### Why Testing Matters

Before expanding to multiple platforms (Goose, Aider, Continue, Windsurf, JetBrains), we need to:
1. **Validate Claude Code** as the reference implementation
2. **Establish baseline** for platform parity (100% = Claude Code)
3. **Prevent regressions** as we add features
4. **Ensure quality** across all user journeys

## Getting Started

### Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

This installs:
- pytest - Testing framework
- pytest-cov - Coverage reporting
- pytest-mock - Mocking utilities
- pytest-xdist - Parallel execution
- GitPython - Git operations
- PyYAML - YAML parsing

### Verify Installation

```bash
pytest --version
pytest --collect-only  # See all available tests
```

### Run Your First Test

```bash
pytest tests/unit/test_repo_builder.py -v
```

You should see all tests passing with green checkmarks.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures (temp_dir, etc.)
├── README.md                   # Quick reference
│
├── unit/                       # 120 tests (60% of total)
│   ├── test_repo_builder.py
│   ├── test_state_validator.py
│   ├── test_metrics_collector.py
│   ├── test_git_validator.py
│   ├── test_config.py
│   ├── test_roadmap.py
│   └── test_sprint_state.py
│
├── integration/                # 60 tests (30% of total)
│   ├── test_journey1_first_time_setup.py
│   ├── test_journey2_sprint_planning.py
│   ├── test_journey3_feature_development.py
│   ├── test_journey4_quality_assurance.py
│   ├── test_journey5_framework_management.py
│   ├── test_journey6_multi_platform.py
│   └── test_journey7_roadmap_driven.py
│
├── e2e/                        # 20 tests (10% of total)
│   ├── test_complete_sprint.py
│   ├── test_quality_gates.py
│   └── test_multi_agent.py
│
├── platform/                   # Platform-specific
│   ├── test_claude_code.py
│   └── test_platform_parity.py
│
├── utils/                      # Test utilities
│   ├── __init__.py
│   ├── repo_builder.py
│   ├── state_validator.py
│   ├── git_validator.py
│   └── metrics_collector.py
│
└── fixtures/                   # Test data
    ├── mock-repos/
    ├── expected-states/
    └── git-histories/
```

## Writing Tests

### Test Template

```python
import pytest
from tests.utils import RepoBuilder, StateValidator, MetricsCollector

@pytest.mark.unit  # Use appropriate marker
def test_feature_name(temp_dir):
    """Test description explaining what is being tested."""
    # Arrange - Set up test data
    builder = RepoBuilder(temp_dir)
    repo = builder.create_web_app_repo()
    metrics = MetricsCollector()

    # Act - Perform the action being tested
    builder.add_vibey_framework(repo)

    # Assert - Verify the results
    validator = StateValidator()
    expected = {"directories": [".claude"], "files": [".claude/CLAUDE.md"]}
    result = validator.validate_directory_structure(repo.path, expected)
    assert result.passed

    # Track metrics (optional)
    metrics.track("deployment_time", 5.2, unit="seconds", threshold=10)
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit          # Unit test (fast, isolated)
@pytest.mark.integration   # Integration test (multiple components)
@pytest.mark.e2e           # End-to-end test (full workflow)
@pytest.mark.platform      # Platform-specific test
@pytest.mark.slow          # Takes >1 second
@pytest.mark.requires_git  # Needs git installed
```

### Using Fixtures

Common fixtures from `conftest.py`:

```python
def test_with_temp_dir(temp_dir):
    """temp_dir provides clean temporary directory."""
    assert temp_dir.exists()
    # Directory cleaned up automatically after test

def test_with_mock_repo(mock_repo_path):
    """mock_repo_path provides path for mock repository."""
    repo = RepoBuilder(mock_repo_path.parent).create_web_app_repo()
    assert repo.path.exists()

def test_with_config(vibey_test_config):
    """vibey_test_config provides test configuration."""
    assert vibey_test_config["test_mode"] is True
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/unit/test_repo_builder.py

# Run specific test
pytest tests/unit/test_repo_builder.py::TestRepoBuilder::test_init

# Run specific marker
pytest -m unit
pytest -m integration
pytest -m "unit or integration"
pytest -m "not slow"
```

### Running Integration Tests

Integration tests validate complete user journeys:

```bash
# Run all integration tests
pytest -m integration

# Run specific journey
pytest tests/integration/test_journey1_first_time_setup.py

# Run Journey 1-3 (core workflows)
pytest tests/integration/test_journey1*.py tests/integration/test_journey2*.py tests/integration/test_journey3*.py

# Run with verbose output to see each test
pytest -m integration -v

# Run integration tests with coverage
pytest -m integration --cov=framework --cov-report=html
```

**Journey Tests:**
- **Journey 1:** First-Time Setup (10 tests) - Vibey initialization workflow
- **Journey 2:** Sprint Planning (10 tests) - Sprint creation and planning
- **Journey 3:** Feature Development (10 tests) - Code implementation and review
- **Journey 4:** Quality Assurance (8 tests) - Quality gate execution
- **Journey 5:** Framework Management (7 tests) - Configuration updates
- **Journey 6:** Multi-Platform (8 tests) - Platform parity validation
- **Journey 7:** Roadmap-Driven (7 tests) - Roadmap system workflows

**Expected Runtime:**
- Unit tests: <30 seconds
- Integration tests: 1-3 minutes
- E2E tests: 2-4 minutes
- Platform tests: <1 minute
- All tests: 4-8 minutes

### Running E2E Tests

End-to-end tests validate complete workflows:

```bash
# Run all E2E tests
pytest -m e2e

# Run specific E2E test file
pytest tests/e2e/test_complete_sprint.py

# Run E2E tests with verbose output
pytest -m e2e -v

# Skip slow E2E tests
pytest -m "e2e and not slow"
```

**E2E Tests:**
- **Complete Sprint** (7 tests) - Full sprint lifecycle
- **Quality Gates** (7 tests) - Gate enforcement workflows
- **Multi-Agent** (6 tests) - Agent orchestration

### Running Platform Tests

Platform-specific tests validate platform features and parity:

```bash
# Run all platform tests
pytest -m platform

# Run Claude Code tests
pytest tests/platform/test_claude_code.py

# Run platform parity validation
pytest tests/platform/test_platform_parity.py

# Check platform parity score
pytest tests/platform/test_platform_parity.py::TestPlatformParity::test_05_overall_platform_parity_score -v
```

**Platform Tests:**
- **Claude Code** (8 tests) - Platform-specific features
- **Goose** (6 tests) - Simulated Goose platform
- **Platform Parity** (8 tests) - Cross-platform validation (>95% threshold)

### Parallel Execution

Speed up test execution with parallel workers:

```bash
# Auto-detect CPU count
pytest -n auto

# Use specific number of workers
pytest -n 4

# Run integration tests in parallel
pytest -m integration -n 4
```

### Coverage Reporting

```bash
# Run with coverage
pytest --cov=framework --cov=scripts

# Generate HTML report
pytest --cov=framework --cov=scripts --cov-report=html

# View missing lines
pytest --cov=framework --cov=scripts --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=framework --cov=scripts --cov-fail-under=90
```

### Filtering Tests

```bash
# Run tests matching name pattern
pytest -k "test_create"

# Run tests in specific directory
pytest tests/unit/

# Run last failed tests
pytest --lf

# Run failed tests first, then remaining
pytest --ff
```

### Debugging

```bash
# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Increase verbosity
pytest -vv
```

## Test Utilities

### RepoBuilder

Create realistic mock repositories:

```python
from tests.utils import RepoBuilder

builder = RepoBuilder(temp_dir)

# Create web application
repo = builder.create_web_app_repo(name="my-app")
# Creates: React + Node.js + PostgreSQL structure

# Create API service
repo = builder.create_api_service_repo(name="my-api")
# Creates: FastAPI + MongoDB structure

# Create ML project
repo = builder.create_ml_project_repo(name="my-ml")
# Creates: Python + Jupyter + TensorFlow structure

# Deploy Vibey framework
builder.add_vibey_framework(repo)
# Adds: .claude/ directory with configs

# Initialize git
builder.init_git(repo, initial_commit=True)
# Creates: Git repo with initial commit
```

### StateValidator

Validate repository state:

```python
from tests.utils import StateValidator

validator = StateValidator()

# Validate directory structure
expected = {
    "directories": ["src", "tests", ".claude"],
    "files": ["README.md", "package.json"]
}
result = validator.validate_directory_structure(repo.path, expected)
assert result.passed
for error in result.errors:
    print(f"Error: {error}")

# Validate YAML structure
schema = {
    "required_keys": ["project", "framework"],
    "key_types": {"project": "dict", "framework": "dict"}
}
result = validator.validate_yaml_structure(yaml_file, schema)

# Validate git state
expected = {"branch": "main", "clean": True}
result = validator.validate_git_state(repo.path, expected)

# Validate file content
result = validator.validate_file_content(
    file_path,
    contains=["VIBEY_FRAMEWORK_MANAGED", "Project Type:"]
)
```

### GitValidator

Validate git history:

```python
from tests.utils import GitValidator

validator = GitValidator()

# Get commit history
commits = validator.get_commit_history(repo.path, count=10)

# Validate commit message format
assert validator.validate_commit_message(commits[0])  # Conventional commits

# Validate commit order
expected_order = [
    "feat:.*framework",
    "test:.*unit tests",
    "docs:.*readme"
]
assert validator.validate_commit_order(commits, expected_order)

# Validate files changed
assert validator.validate_file_changes(
    commits[0],
    expected_files=["*.py", "tests/*.py"]
)

# Validate branch state
assert validator.validate_branch_state(repo.path, "main")
```

### MetricsCollector

Track success metrics:

```python
from tests.utils import MetricsCollector

metrics = MetricsCollector()

# Track metrics
metrics.track("deployment_time", 8.5, unit="seconds", threshold=10)
metrics.track("test_coverage", 95, unit="percentage", threshold=90)
metrics.track("success_rate", 100, unit="percentage", threshold=100)

# Assert metrics
assert metrics.assert_metric("deployment_time", max_value=10)
assert metrics.assert_metric("test_coverage", min_value=90)
assert metrics.assert_metric("success_rate", expected_value=100)

# Calculate success rate
success_rate = metrics.calculate_success_rate()
assert success_rate >= 95

# Export metrics
metrics.export_metrics(Path("test-results/metrics.json"))
```

## Coverage Reporting

### Configuration

Coverage is configured in `.coveragerc`:

```ini
[run]
source = framework, scripts
omit = */tests/*, */venv/*
branch = True

[report]
precision = 2
show_missing = True
fail_under = 90

[html]
directory = htmlcov
```

### View Coverage Reports

```bash
# Generate and view HTML report
pytest --cov=framework --cov=scripts --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Interpreting Coverage

- **Green (100%):** Fully covered
- **Yellow (50-99%):** Partially covered
- **Red (0-49%):** Poorly covered
- **Missing lines:** Highlighted in red

### Improving Coverage

```bash
# Find uncovered lines
pytest --cov=framework --cov=scripts --cov-report=term-missing

# Focus on specific module
pytest --cov=framework.roadmap --cov-report=term-missing tests/unit/test_roadmap.py
```

## CI/CD Integration

### GitHub Actions Workflow

The test suite runs automatically via GitHub Actions on:
- **Pull requests** to main branch
- **Pushes** to main branch
- **Daily schedule** at midnight UTC

**Test Matrix:**
- Python versions: 3.8, 3.9, 3.10, 3.11
- Operating systems: Ubuntu, macOS
- Test suites: Unit, Integration, E2E, Platform

**Workflow jobs:**
1. **Test** - Run full test suite on matrix
2. **Coverage Check** - Enforce >90% threshold
3. **Lint** - Code quality checks (Black, isort, Flake8)
4. **Security** - Bandit security scan
5. **Summary** - Test results summary

**View the workflow:** `.github/workflows/test.yml`

**Artifacts uploaded:**
- Coverage reports (HTML)
- Test results (XML)
- Retention: 30 days

### Pre-commit Hooks

Run tests and checks before committing:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Test Matrix

Tests run across:
- Python 3.8, 3.9, 3.10, 3.11
- Ubuntu, macOS, Windows
- Multiple pytest versions

## Best Practices

### DO

✅ **Use descriptive test names**
```python
def test_vibey_deployment_creates_claude_directory():
    """Good: Clear what is being tested"""
    pass
```

✅ **Follow AAA pattern** (Arrange, Act, Assert)
```python
# Arrange
repo = builder.create_web_app_repo()
# Act
builder.add_vibey_framework(repo)
# Assert
assert (repo.path / ".claude").exists()
```

✅ **Test one thing per test**
```python
def test_deployment_creates_config():
    """Tests only config creation"""
    pass

def test_deployment_creates_readme():
    """Tests only README creation"""
    pass
```

✅ **Use fixtures for setup**
```python
def test_with_fixture(temp_dir, mock_repo_path):
    """Fixtures handle setup and teardown"""
    pass
```

✅ **Track metrics for integration/e2e tests**
```python
metrics = MetricsCollector()
metrics.track("journey_time", duration, threshold=900)
```

### DON'T

❌ **Use vague test names**
```python
def test_it_works():  # Bad: What works?
    pass
```

❌ **Test multiple things in one test**
```python
def test_everything():  # Bad: Too broad
    # Tests 10 different things
    pass
```

❌ **Use hard-coded paths**
```python
repo_path = "/tmp/my-repo"  # Bad: Use fixtures
```

❌ **Ignore test failures**
```python
try:
    assert result
except:
    pass  # Bad: Never hide failures
```

❌ **Write slow tests without marking**
```python
def test_slow_operation():  # Bad: Missing @pytest.mark.slow
    time.sleep(10)
```

### Writing Good Assertions

```python
# Specific assertions
assert result.passed  # Good
assert result  # Bad: Unclear what's being tested

# Include helpful messages
assert len(errors) == 0, f"Unexpected errors: {errors}"

# Use pytest's built-in assertions
assert value in collection  # Good
self.assertTrue(value in collection)  # Bad: Less informative failures
```

### Test Organization

```python
# Group related tests in classes
class TestRepoBuilder:
    """Test RepoBuilder utility."""

    def test_create_web_app(self):
        pass

    def test_create_api_service(self):
        pass

    def test_add_vibey_framework(self):
        pass
```

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Solution: Install test dependencies
pip install -r requirements-test.txt
```

**Git tests failing:**
```bash
# Solution: Configure git
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```

**Coverage below 90%:**
```bash
# Solution: Find uncovered code
pytest --cov=framework --cov-report=term-missing
# Then write tests for uncovered lines
```

**Tests are slow:**
```bash
# Solution: Run in parallel
pytest -n auto

# Or skip slow tests during development
pytest -m "not slow"
```

**Fixtures not found:**
```bash
# Solution: Check conftest.py is in test directory
# Ensure __init__.py files exist in test directories
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Vibey Testing Plan](../VIBEY_TESTING_PLAN.md)
- [Vibey User Journeys](../VIBEY_USER_JOURNEYS.md)
- [Test README](../../tests/README.md)

## Getting Help

- Check test output for specific error messages
- Review relevant test utility documentation
- Look at similar existing tests for patterns
- Run tests with `-vv` for maximum verbosity
- Use `--pdb` to debug test failures interactively

## Contributing

When contributing to Vibey:

1. **Write tests first** (TDD approach)
2. **Ensure >90% coverage** for new code
3. **Use appropriate test markers**
4. **Follow naming conventions**
5. **Document complex test scenarios**
6. **Track relevant metrics**
7. **Run full test suite** before submitting PR

---

**Framework Version:** 1.3.0
**Test Framework Version:** 1.0.0
**Last Updated:** 2025-11-10
**Status:** Production Ready
