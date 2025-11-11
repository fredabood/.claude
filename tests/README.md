# Vibey Framework Test Suite

Comprehensive test suite for the Vibey Agent Framework.

## Overview

This test suite validates the Vibey framework before multi-platform expansion. It includes unit tests, integration tests for all 7 user journeys, E2E tests, and platform-specific tests.

## Test Structure

```
tests/
├── conftest.py                    # Shared pytest fixtures
├── unit/                          # Unit tests (60% coverage target)
│   ├── test_repo_builder.py      # RepoBuilder utility tests
│   ├── test_state_validator.py   # StateValidator utility tests
│   └── test_metrics_collector.py # MetricsCollector utility tests
├── integration/                   # Integration tests (30% coverage target)
│   ├── test_journey1_first_time_setup.py
│   ├── test_journey2_sprint_planning.py
│   ├── test_journey3_feature_development.py
│   ├── test_journey4_quality_assurance.py
│   ├── test_journey5_framework_management.py
│   ├── test_journey6_multi_platform.py
│   └── test_journey7_roadmap_driven.py
├── e2e/                           # E2E tests (10% coverage target)
│   ├── test_complete_sprint.py
│   ├── test_quality_gates.py
│   └── test_multi_agent.py
├── platform/                      # Platform-specific tests
│   ├── test_claude_code.py
│   └── test_platform_parity.py
├── utils/                         # Test utilities
│   ├── repo_builder.py           # Create mock repositories
│   ├── state_validator.py        # Validate repository state
│   ├── git_validator.py          # Validate git history
│   └── metrics_collector.py      # Track success metrics
└── fixtures/
    ├── mock-repos/               # Mock repository templates
    ├── expected-states/          # Expected state definitions
    └── git-histories/            # Expected commit patterns
```

## Test Utilities

### RepoBuilder

Create realistic mock repositories for testing:

```python
from tests.utils import RepoBuilder

builder = RepoBuilder(temp_dir)
repo = builder.create_web_app_repo()
builder.add_vibey_framework(repo)
builder.init_git(repo)
```

### StateValidator

Validate repository state against expectations:

```python
from tests.utils import StateValidator

validator = StateValidator()
result = validator.validate_directory_structure(repo.path, expected)
assert result.passed
```

### GitValidator

Validate git history and commits:

```python
from tests.utils import GitValidator

validator = GitValidator()
commits = validator.get_commit_history(repo.path)
assert validator.validate_commit_message(commits[0])
```

### MetricsCollector

Track and validate success metrics:

```python
from tests.utils import MetricsCollector

metrics = MetricsCollector()
metrics.track("test_coverage", 95, threshold=90)
assert metrics.calculate_success_rate() == 100
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test categories:
```bash
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m e2e                     # E2E tests only
pytest -m platform                # Platform tests only
```

### Run with coverage:
```bash
pytest --cov=framework --cov=scripts --cov-report=html
```

### Run tests in parallel:
```bash
pytest -n auto
```

### Run slow tests:
```bash
pytest -m slow
```

### Skip git-dependent tests:
```bash
pytest -m "not requires_git"
```

## Test Markers

- `@pytest.mark.unit` - Unit tests for individual functions/classes
- `@pytest.mark.integration` - Integration tests for workflows
- `@pytest.mark.e2e` - End-to-end tests for complete journeys
- `@pytest.mark.platform` - Platform-specific tests
- `@pytest.mark.slow` - Tests that take significant time
- `@pytest.mark.requires_git` - Tests that require git installation

## Coverage Goals

- **Overall:** >90% code coverage
- **Unit tests:** 60% of total tests (120 tests)
- **Integration tests:** 30% of total tests (60 tests)
- **E2E tests:** 10% of total tests (20 tests)

## Success Metrics

Each test suite tracks specific success metrics:

- **Journey 1 (First-Time Setup):**
  - setup_completion_rate: 100%
  - avg_setup_time: <15 minutes
  - configuration_accuracy: 100%

- **Journey 2 (Sprint Planning):**
  - sprint_completion_rate: 100%
  - quality_gate_pass_rate: 100%
  - task_estimation_accuracy: >85%

- **Platform Parity:**
  - platform_parity_score: >95%
  - deployment_success_rate: 100%
  - agent_equivalence: 100%

## Writing New Tests

1. Use appropriate test markers
2. Use test utilities for setup
3. Include docstrings explaining what is tested
4. Track relevant success metrics
5. Follow AAA pattern (Arrange, Act, Assert)

Example:

```python
import pytest
from tests.utils import RepoBuilder, StateValidator

@pytest.mark.unit
def test_vibey_deployment(temp_dir):
    """Test Vibey framework deployment to repository."""
    # Arrange
    builder = RepoBuilder(temp_dir)
    repo = builder.create_web_app_repo()

    # Act
    builder.add_vibey_framework(repo)

    # Assert
    validator = StateValidator()
    expected = {"directories": [".claude"], "files": ["CLAUDE.md"]}
    result = validator.validate_directory_structure(repo.path, expected)
    assert result.passed
```

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Pushes to main
- Daily at midnight

See `.github/workflows/test.yml` for configuration.

## Test Data

### Mock Repositories

Three realistic repository templates:
- **web-app:** React + Node.js + PostgreSQL
- **api-service:** FastAPI + MongoDB
- **ml-project:** Python + Jupyter + TensorFlow

### Expected States

YAML files defining expected repository states:
- `after-deployment.yaml` - After Vibey initialization
- `after-sprint-planning.yaml` - After creating sprint plan
- `after-feature-complete.yaml` - After feature completion

## Troubleshooting

**Import errors:**
```bash
pip install -r requirements-test.txt
```

**Git tests failing:**
Ensure git is installed and configured:
```bash
git --version
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```

**Coverage not reaching 90%:**
Check which files are not covered:
```bash
pytest --cov=framework --cov-report=term-missing
```

## Documentation

- [Testing Plan](../docs/VIBEY_TESTING_PLAN.md) - Overall testing strategy
- [User Journeys](../docs/VIBEY_USER_JOURNEYS.md) - User journey specifications

## Contributing

When adding new framework features:
1. Write tests first (TDD)
2. Ensure >90% coverage for new code
3. Add integration tests if feature spans modules
4. Update expected states if deployment changes
5. Document new success metrics
