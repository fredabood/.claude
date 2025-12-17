# Task 9: Implement CI Test Coverage Enforcement

## Task Metadata
- **ID:** `01KCMKDJ7JYGHGSYME2V7EEG6Q`
- **Sprint:** Sprint 3: MCP/CLI Parity & Integration Tests
- **Priority:** High
- **Complexity:** Medium
- **Type:** DevOps/Testing
- **Estimated Effort:** 2-3 hours

## Objective
Configure CI to enforce minimum test coverage thresholds and block PRs that drop coverage below acceptable levels.

## Current State Analysis

### Existing CI Configuration
- Location: `.github/workflows/`
- Current test workflow: May exist, needs audit
- Coverage reporting: May not be configured

### Target Coverage Thresholds
| Module | Target |
|--------|--------|
| `vibey/unified/` | 95% |
| `vibey/cli/` | 90% |
| `vibey/mcp/` | 90% |
| `vibey/operations/` | 90% |
| Overall | 85% |

## Implementation Steps

### Step 1: Configure pytest-cov
**File:** `pyproject.toml`
```toml
[tool.pytest.ini_options]
addopts = "--cov=vibey --cov-report=xml --cov-report=term-missing"
testpaths = ["tests"]

[tool.coverage.run]
source = ["vibey"]
branch = true
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/conftest.py",
]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"
```

### Step 2: Create/Update Test Workflow
**File:** `.github/workflows/test.yml`
```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=vibey \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=85 \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
          verbose: true

      - name: Coverage Report Summary
        if: always()
        run: |
          echo "## Coverage Report" >> $GITHUB_STEP_SUMMARY
          echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
          coverage report >> $GITHUB_STEP_SUMMARY
          echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
```

### Step 3: Add Coverage Badge to README
**File:** `README.md` (add to badges section)
```markdown
[![codecov](https://codecov.io/gh/owner/vibey/branch/main/graph/badge.svg)](https://codecov.io/gh/owner/vibey)
```

### Step 4: Create Module-Specific Coverage Checks
**File:** `.github/workflows/coverage-check.yml`
```yaml
name: Coverage Check

on:
  pull_request:
    branches: [main]

jobs:
  coverage-check:
    name: Check Coverage Thresholds
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Check unified module coverage (95%)
        run: |
          pytest tests/unified/ \
            --cov=vibey/unified \
            --cov-fail-under=95 \
            --cov-report=term-missing

      - name: Check CLI coverage (90%)
        run: |
          pytest tests/cli/ \
            --cov=vibey/cli \
            --cov-fail-under=90 \
            --cov-report=term-missing

      - name: Check MCP coverage (90%)
        run: |
          pytest tests/mcp/ \
            --cov=vibey/mcp \
            --cov-fail-under=90 \
            --cov-report=term-missing

      - name: Check operations coverage (90%)
        run: |
          pytest tests/operations/ \
            --cov=vibey/operations \
            --cov-fail-under=90 \
            --cov-report=term-missing
```

### Step 5: Add Coverage Comment to PRs
**File:** `.github/workflows/test.yml` (add step)
```yaml
      - name: Comment PR with coverage
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');

            // Parse coverage report
            const output = require('child_process')
              .execSync('coverage report --format=markdown')
              .toString();

            const body = `## Test Coverage Report

            ${output}

            <details>
            <summary>Coverage by module</summary>

            Run \`pytest --cov=vibey --cov-report=html\` locally for detailed report.
            </details>
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

### Step 6: Configure Branch Protection
Update GitHub repository settings:
1. Go to Settings → Branches → Branch protection rules
2. Add rule for `main` branch
3. Enable "Require status checks to pass"
4. Select "test" job as required
5. Enable "Require branches to be up to date"

### Step 7: Create Local Coverage Script
**File:** `scripts/check-coverage.sh`
```bash
#!/bin/bash
set -e

echo "Running coverage check..."

# Overall coverage
pytest tests/ --cov=vibey --cov-fail-under=85 --cov-report=term-missing

echo ""
echo "Module-specific coverage:"
echo "========================="

# Unified module (95%)
echo "Unified module (target: 95%):"
pytest tests/unified/ --cov=vibey/unified --cov-report=term | grep TOTAL

# CLI module (90%)
echo "CLI module (target: 90%):"
pytest tests/cli/ --cov=vibey/cli --cov-report=term | grep TOTAL

# MCP module (90%)
echo "MCP module (target: 90%):"
pytest tests/mcp/ --cov=vibey/mcp --cov-report=term | grep TOTAL

# Operations module (90%)
echo "Operations module (target: 90%):"
pytest tests/operations/ --cov=vibey/operations --cov-report=term | grep TOTAL

echo ""
echo "Coverage check complete!"
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | Modify | Add coverage configuration |
| `.github/workflows/test.yml` | Create/Modify | Main test workflow |
| `.github/workflows/coverage-check.yml` | Create | Module-specific checks |
| `scripts/check-coverage.sh` | Create | Local coverage script |
| `README.md` | Modify | Add coverage badge |

## Acceptance Criteria

- [ ] `pyproject.toml` has coverage configuration
- [ ] CI runs tests with coverage on every PR
- [ ] Coverage report uploaded to Codecov (or similar)
- [ ] PRs show coverage summary in comments
- [ ] PRs blocked if coverage drops below 85%
- [ ] Module-specific thresholds enforced
- [ ] Branch protection configured
- [ ] Local coverage script works

## Test Execution
```bash
# Run local coverage check
./scripts/check-coverage.sh

# Generate HTML report
pytest tests/ --cov=vibey --cov-report=html
open htmlcov/index.html
```

## Dependencies
- pytest-cov
- coverage
- codecov-action (GitHub Action)

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Coverage gaming (trivial tests) | Code review for test quality |
| Flaky tests | Retry logic in CI |
| Slow test runs | Parallel test execution |
| Coverage report parsing | Use standard XML format |
