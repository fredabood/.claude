# Contributor Walkthrough: Your First Vibey Contribution

> **Time Required:** 60 minutes
> **Difficulty:** Advanced
> **Prerequisites:** Git, Python 3.9+, development environment

## Overview

This walkthrough guides you through making your first contribution to the Vibey framework. You'll set up your development environment, understand the codebase structure, make a change, and submit a pull request.

### What You'll Learn

- How to set up the development environment
- How to navigate the codebase structure
- How to run tests and validate changes
- How to submit a quality pull request

### What You'll Build

A complete contribution workflow from fork to merged PR.

---

## Prerequisites

### Required

- [ ] Git installed
- [ ] Python 3.9+ installed
- [ ] GitHub account
- [ ] Familiarity with pull request workflow

### Verify Prerequisites

```bash
# Check Git
git --version
# Expected: git version 2.x.x

# Check Python
python3 --version
# Expected: Python 3.9.x or higher

# Check pip
pip3 --version
# Expected: pip 21.x or higher
```

---

## Step 1: Fork and Clone

### Goal

Get a local copy of the repository for development.

### Instructions

1. Fork the repository on GitHub:
   - Go to https://github.com/fredabood/vibey
   - Click "Fork" button
   - Wait for fork to complete

2. Clone your fork:

   ```bash
   git clone https://github.com/YOUR-USERNAME/vibey.git
   cd vibey
   ```

3. Add upstream remote:

   ```bash
   git remote add upstream https://github.com/fredabood/vibey.git
   git fetch upstream
   ```

4. Verify remotes:

   ```bash
   git remote -v
   ```

   **Expected Output:**
   ```
   origin    https://github.com/YOUR-USERNAME/vibey.git (fetch)
   origin    https://github.com/YOUR-USERNAME/vibey.git (push)
   upstream  https://github.com/fredabood/vibey.git (fetch)
   upstream  https://github.com/fredabood/vibey.git (push)
   ```

### Checkpoint

> **Verify:** Both `origin` (your fork) and `upstream` (main repo) are configured

---

## Step 2: Set Up Development Environment

### Goal

Create a working development environment with all dependencies.

### Instructions

1. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

   **Expected Output:**
   ```
   Successfully installed vibey-2.5.0 ...
   ```

3. Verify installation:

   ```bash
   vibey --version
   ```

   **Expected Output:**
   ```
   Vibey Agent Framework v2.5.0
   ```

4. Initialize Vibey in the repo:

   ```bash
   # The repo already has .vibey/ but verify it works
   vibey roadmap status
   ```

### Checkpoint

> **Verify:** `vibey roadmap status` shows the project's roadmap

### Troubleshooting

<details>
<summary>Problem: "No module named vibey"</summary>

**Symptom:** Import errors when running vibey

**Cause:** Package not installed in editable mode

**Solution:**
```bash
# Make sure you're in the repo root with setup.py/pyproject.toml
pip install -e .
```
</details>

---

## Step 3: Understand the Codebase

### Goal

Navigate the project structure and understand where different components live.

### Instructions

1. Review the project structure:

   ```
   vibey/                    # Repository root
   ├── vibey/                # Python package (ALL code)
   │   ├── cli/              # CLI commands (main.py, commands.py)
   │   ├── operations/       # Core business logic
   │   │   ├── roadmap/      # Roadmap operations
   │   │   └── docs/         # Documentation generation
   │   ├── mcp/              # MCP server implementation
   │   ├── common/           # Shared utilities, errors
   │   └── roadmap/          # Roadmap models
   │
   ├── framework/            # Content files (agents, workflows)
   ├── docs/                 # Documentation
   ├── tests/                # Test suite
   └── .vibey/               # Vibey data (roadmap, config)
   ```

2. Read key files:

   ```bash
   # Main entry point
   cat vibey/cli/main.py | head -50

   # Core roadmap operations
   ls vibey/operations/roadmap/

   # Data models
   ls vibey/roadmap/models/
   ```

3. Read CLAUDE.md for context:

   ```bash
   cat CLAUDE.md | head -100
   ```

### Checkpoint

> **Verify:** You understand where CLI commands, operations, and models are located

---

## Step 4: Run the Test Suite

### Goal

Ensure all tests pass before making changes.

### Instructions

1. Run the full test suite:

   ```bash
   pytest tests/ -v
   ```

   **Expected Output:**
   ```
   ==================== test session starts ====================
   collected XXX items

   tests/... PASSED
   ...

   ==================== XXX passed in X.XXs ====================
   ```

2. Run tests for a specific module:

   ```bash
   pytest tests/roadmap/ -v
   ```

3. Run tests with coverage:

   ```bash
   pytest tests/ --cov=vibey --cov-report=term-missing
   ```

### Checkpoint

> **Verify:** Test suite passes (or note any pre-existing failures)

### Troubleshooting

<details>
<summary>Problem: Tests fail with import errors</summary>

**Symptom:** `ModuleNotFoundError` during tests

**Cause:** Package not installed or wrong Python environment

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall in development mode
pip install -e ".[dev]"
```
</details>

---

## Step 5: Create a Feature Branch

### Goal

Set up a branch for your contribution.

### Instructions

1. Sync with upstream:

   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. Create feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

   **Naming conventions:**
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `docs/` - Documentation updates
   - `refactor/` - Code refactoring

3. Verify branch:

   ```bash
   git branch
   ```

   **Expected Output:**
   ```
   * feature/your-feature-name
     main
   ```

### Checkpoint

> **Verify:** You're on your new feature branch

---

## Step 6: Make Your Changes

### Goal

Implement your contribution following project conventions.

### Instructions

1. **Follow code standards:**
   - Python 3.9+ compatibility
   - Type hints for functions
   - Docstrings for modules and functions
   - Error handling with clear messages

2. **Example: Add a new CLI command**

   Edit `vibey/cli/main.py`:

   ```python
   @roadmap.command('your-command')
   @click.option('--option', '-o', help='Description')
   @click.pass_context
   def your_command(ctx, option: str):
       """Brief description of what this command does."""
       # Implementation here
       click.echo(f"Result: {option}")
   ```

3. **Example: Add a new operation**

   Create `vibey/operations/roadmap/your_feature.py`:

   ```python
   """Your feature module.

   Brief description of what this module does.
   """
   from typing import Optional
   from vibey.roadmap.models import Track, Sprint, Task

   def your_function(param: str) -> Optional[str]:
       """Do something useful.

       Args:
           param: Description of parameter

       Returns:
           Description of return value
       """
       # Implementation
       return result
   ```

4. **Write tests for your changes:**

   Create `tests/operations/roadmap/test_your_feature.py`:

   ```python
   """Tests for your_feature module."""
   import pytest
   from vibey.operations.roadmap.your_feature import your_function

   class TestYourFunction:
       """Tests for your_function."""

       def test_basic_case(self):
           """Test the basic use case."""
           result = your_function("input")
           assert result == "expected"

       def test_edge_case(self):
           """Test edge cases."""
           result = your_function("")
           assert result is None
   ```

### Checkpoint

> **Verify:** Your changes are complete and follow conventions

---

## Step 7: Validate Your Changes

### Goal

Ensure your changes work correctly and don't break existing functionality.

### Instructions

1. Run your new tests:

   ```bash
   pytest tests/path/to/your_tests.py -v
   ```

2. Run the full test suite:

   ```bash
   pytest tests/ -v
   ```

3. Test manually:

   ```bash
   # For CLI changes
   vibey roadmap your-command --option value

   # For operations
   python3 -c "from vibey.operations.roadmap.your_feature import your_function; print(your_function('test'))"
   ```

4. Check for linting issues:

   ```bash
   # If flake8 is installed
   flake8 vibey/
   ```

### Checkpoint

> **Verify:** All tests pass and manual testing works

---

## Testing Requirements

Before submitting your contribution, ensure your changes meet testing requirements:

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vibey --cov-report=term-missing

# Run specific module tests
pytest tests/operations/roadmap/

# Run integration tests
pytest tests/integration/ -v
```

### Coverage Requirements

- **All new code must have tests** - No PR may add untested code
- **Coverage must not decrease** - CI will block PRs that reduce coverage
- **90% threshold** - CI enforces minimum 90% coverage

### Test Patterns

- **Use fixtures** from `tests/conftest.py` for common setup
- **Follow existing structure** - Mirror the module layout in tests/
- **Include edge cases** - Empty inputs, invalid data, error paths
- **Test error handling** - Verify exceptions are raised correctly

### Before Submitting

1. Run full test suite: `pytest`
2. Check coverage: `pytest --cov=vibey`
3. Verify no coverage regression
4. Run integration tests: `pytest tests/integration/`

### CI Checks

When you submit a PR, CI will automatically:
- Run all tests across Python 3.10, 3.11, 3.12
- Enforce 90% coverage threshold
- Run lint checks (ruff)
- Run type checks (mypy)
- Run security scan (bandit)

See `docs/development/TEST_MAINTENANCE.md` for detailed testing guidance.

---

## Step 8: Commit Your Changes

### Goal

Create clear, well-documented commits.

### Instructions

1. Stage your changes:

   ```bash
   git add vibey/cli/main.py
   git add vibey/operations/roadmap/your_feature.py
   git add tests/operations/roadmap/test_your_feature.py
   ```

2. Commit with a clear message:

   ```bash
   git commit -m "feat(roadmap): add your-command for doing X

   - Add your_function to operations/roadmap
   - Add CLI command 'vibey roadmap your-command'
   - Add tests for new functionality

   Closes #123"
   ```

   **Commit message format:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `refactor:` - Code restructuring
   - `test:` - Test additions

3. View your commit:

   ```bash
   git log -1
   ```

### Checkpoint

> **Verify:** Commit is created with clear message

---

## Step 9: Push and Create PR

### Goal

Submit your contribution for review.

### Instructions

1. Push your branch:

   ```bash
   git push origin feature/your-feature-name
   ```

2. Create pull request:
   - Go to your fork on GitHub
   - Click "Compare & pull request"
   - Fill in the PR template:

   ```markdown
   ## Summary
   - Brief description of changes

   ## Changes Made
   - List specific changes

   ## Testing
   - How was this tested?
   - Test results

   ## Related Issues
   - Closes #123
   ```

3. Wait for CI checks:
   - Tests must pass
   - Lint checks must pass
   - Documentation drift checks must pass

### Checkpoint

> **Verify:** PR is created and CI checks are running

---

## Step 10: Respond to Review

### Goal

Address feedback and get your PR merged.

### Instructions

1. **If changes requested:**

   ```bash
   # Make changes locally
   git add .
   git commit -m "fix: address review feedback"
   git push origin feature/your-feature-name
   ```

2. **If conflicts with main:**

   ```bash
   git fetch upstream
   git rebase upstream/main
   # Resolve conflicts if any
   git push origin feature/your-feature-name --force-with-lease
   ```

3. **After approval:**
   - Maintainer will merge
   - Delete your feature branch:

   ```bash
   git checkout main
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

### Checkpoint

> **Verify:** PR is merged and branch is cleaned up

---

## Step 11: Understand How Your Changes Are Tracked

### Goal

Learn how the audit trail captures your contributions.

### Instructions

1. View recent audit entries after your PR is merged:

   ```bash
   vibey roadmap audit log --limit 10
   ```

   **Expected Output:**
   ```
   Audit Trail (last 10 entries)
   =============================
   2025-12-12 16:30 | commit linked | Task: 01KC2D → abc123f "fix: your contribution"
   2025-12-12 16:25 | status: in_progress → completed | Task: 01KC2D
   ```

2. Check your task's complete history:

   ```bash
   vibey roadmap audit show <task-id>
   ```

   **Expected Output:**
   ```
   Audit History for Task: 01KC2D0JK7READW9KAK1HBX4A5
   ================================================
   2025-12-12 16:30 | commit: abc123f linked
   2025-12-12 16:25 | completed
   2025-12-12 14:00 | started
   2025-12-12 13:45 | created via roadmap create-task
   ```

### What Gets Tracked

- **Task lifecycle:** created → started → completed
- **Commit links:** SHA, message, timestamp
- **Context additions:** Notes you added during work
- **Status changes:** All transitions with timestamps

### Why This Matters

- **Attribution:** Your work is credited to you
- **Traceability:** Changes can be traced to specific commits
- **Transparency:** Project history is visible to all
- **Quality:** Enables debugging and rollback if needed

### Checkpoint

> **Verify:** You understand how your contributions are tracked in the audit trail

---

## Summary

### What You Accomplished

- Set up a local development environment
- Understood the codebase structure
- Created and tested a contribution
- Submitted a quality pull request
- Learned the review process

### Commands Used

| Command | Purpose |
|---------|---------|
| `git clone` | Clone repository |
| `git remote add` | Add upstream |
| `pip install -e .` | Install in dev mode |
| `pytest` | Run tests |
| `git checkout -b` | Create branch |
| `git push` | Push changes |

### Next Steps

1. **Find Issues:** Check [GitHub Issues](https://github.com/fredabood/vibey/issues) for good first issues
2. **Join Discussion:** Participate in issue discussions
3. **Review PRs:** Help review other contributions
4. **Deep Dive:** Read the [CLI Reference](../reference/CLI_REFERENCE.md) and [MCP Reference](../reference/MCP_REFERENCE.md)

---

## Quick Reference

### Development Workflow

```bash
# Setup (one time)
git clone https://github.com/YOUR-USERNAME/vibey.git
cd vibey
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Before each contribution
git fetch upstream
git checkout main
git merge upstream/main
git checkout -b feature/your-feature

# Make changes, then
pytest tests/ -v
git add .
git commit -m "feat: your change"
git push origin feature/your-feature
# Create PR on GitHub
```

### Related Documentation

- [CLI Reference](../reference/CLI_REFERENCE.md)
- [MCP Reference](../reference/MCP_REFERENCE.md)
- [Contributor Journey](../journeys/JOURNEY_CONTRIBUTOR.md)
- [User Personas](../personas/USER_PERSONAS.md#chris)
