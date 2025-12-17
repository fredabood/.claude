# Contributor Journey

> **Note:** This document has been consolidated into action-oriented walkthroughs.
> See [GETTING_STARTED.md](../walkthroughs/GETTING_STARTED.md) for setup and
> [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

> From first contribution to framework maintainer

**Persona:** Chris the Contributor
**Duration:** Variable, project-based

---

## Journey Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONTRIBUTOR JOURNEY                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Orientation │ Setup       │ First PR    │ Continued   │ Maintainer          │
│ (2-4 hrs)   │ (1-2 hrs)   │ (variable)  │ Contrib     │ (long-term)         │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ - Read docs │ - Clone     │ - Pick      │ - Regular   │ - Review PRs        │
│ - Understand│   repo      │   issue     │   PRs       │ - Guide new         │
│   codebase  │ - Setup     │ - Implement │ - Test      │   contributors      │
│ - Find task │   env       │ - Test, PR  │   coverage  │ - Shape roadmap     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

---

## Phase 1: Orientation

**Duration:** 2-4 hours
**Goal:** Understand the framework architecture and contribution process

### Reading List

1. **README.md** - Project overview
2. **CLAUDE.md** - Framework context and conventions
3. **CONTRIBUTING.md** - Contribution guidelines
4. **docs/development/** - Development documentation

### Codebase Exploration

```bash
# Clone repository
git clone https://github.com/anthropics/vibey.git
cd vibey

# Explore structure
ls -la
ls vibey/          # Python package (ALL code)
ls .vibey/         # Framework data (roadmap, config)
ls docs/           # Documentation
ls tests/          # Test suite

# Read main entry point
cat vibey/cli/main.py | head -100
```

### Key Directories

```
vibey/
├── vibey/              # Python package (ALL code)
│   ├── cli/            # CLI commands
│   ├── operations/     # Core business logic
│   ├── mcp/            # MCP server
│   ├── roadmap/        # Roadmap models
│   └── common/         # Shared utilities
├── .vibey/             # Framework data
│   └── roadmap/        # Roadmap YAML + SQLite
├── docs/               # Documentation
└── tests/              # Test suite
```

### Key Files to Understand

| File | Purpose |
|------|---------|
| `vibey/cli/main.py` | CLI entry point, all commands |
| `vibey/operations/roadmap/*.py` | Core roadmap operations |
| `vibey/roadmap/models/*.py` | Data models |
| `CLAUDE.md` | Repository context |
| `pyproject.toml` | Package configuration |

---

## Phase 2: Development Setup

**Duration:** 1-2 hours
**Goal:** Get development environment working

### Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Verify installation
vibey --version
```

### Run Tests

```bash
# Run full test suite
pytest

# Run specific test file
pytest tests/roadmap/test_models.py

# Run with coverage
pytest --cov=vibey --cov-report=html
```

### Code Quality Tools

```bash
# Format code
black vibey tests

# Sort imports
isort vibey tests

# Type checking
mypy vibey

# Lint
ruff check vibey
```

### Git Hooks

```bash
# Install pre-commit hooks
vibey git hooks install

# Test hooks
git add .
git commit -m "test: Verify hooks working"
```

---

## Phase 3: First Contribution

**Duration:** Variable
**Goal:** Complete and merge first pull request

### Finding Work

1. **GitHub Issues** - Look for "good first issue" label
2. **Roadmap** - Check `.vibey/roadmap/` for tasks
3. **TODO comments** - Search codebase for TODOs
4. **Documentation gaps** - Improvements always welcome

### Checking the Roadmap

```bash
# View roadmap status
vibey roadmap status

# Find available tasks
vibey roadmap list tasks --status not_started

# See task details
vibey roadmap show task <task-id>
```

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-contribution

# Make changes...

# Run tests
pytest

# Run quality checks
black vibey && isort vibey && mypy vibey

# Commit with task reference
git add .
git commit -m "feat(scope): Add feature description

Task: 01KC2D0JK7READW9KAK1HBX4A5"

# Push and create PR
git push -u origin feature/my-contribution
gh pr create
```

### Commit Message Format

```
type(scope): description

[optional body]

Task: <task-id>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test changes
- `refactor:` - Code restructuring

### PR Checklist

- [ ] Tests pass locally
- [ ] Code formatted with black
- [ ] No type errors (mypy)
- [ ] Commit message references task
- [ ] Documentation updated if needed

---

## Phase 4: Continued Contribution

**Duration:** Ongoing
**Goal:** Become a regular contributor

### Increasing Scope

1. **Bug fixes** - Start here
2. **Small features** - After a few bug fixes
3. **Documentation** - Always valuable
4. **Test coverage** - Improve existing tests
5. **Major features** - After establishing trust

### Code Review

```bash
# Checkout PR for review
gh pr checkout <pr-number>

# Run tests
pytest

# Review changes
git diff main
```

### Staying Current

```bash
# Update main branch
git checkout main
git pull origin main

# Rebase feature branch
git checkout feature/my-branch
git rebase main
```

---

## Phase 5: Maintainer Path

**Duration:** Long-term
**Goal:** Help guide framework development

### Responsibilities

1. **Review PRs** - Help other contributors
2. **Triage issues** - Label and prioritize
3. **Update roadmap** - Plan future work
4. **Documentation** - Keep docs current
5. **Release management** - Version and publish

### Commands for Maintainers

```bash
# Validate entire roadmap
vibey roadmap validate --full

# Check for issues
vibey roadmap repair --dry-run

# Generate release notes
vibey roadmap summarize --type release --version <version>
```

---

## Command Reference

### Development Commands

| Command | Purpose |
|---------|---------|
| `pytest` | Run tests |
| `pytest --cov` | Run with coverage |
| `black vibey` | Format code |
| `mypy vibey` | Type checking |
| `ruff check vibey` | Linting |

### Roadmap Commands

| Command | Purpose |
|---------|---------|
| `vibey roadmap status` | Current status |
| `vibey roadmap show task` | Task details |
| `vibey roadmap validate` | Check integrity |

### Git Commands

| Command | Purpose |
|---------|---------|
| `vibey git hooks install` | Install hooks |
| `git commit` (with hooks) | Validated commits |

### Audit Trail Commands

| Command | Purpose |
|---------|---------|
| `vibey roadmap audit log` | View recent changes |
| `vibey roadmap audit show <id>` | History for specific item |

---

## Understanding Audit Logging

### How Your Changes Are Tracked

Vibey automatically tracks all changes to roadmap objects. When you:
- Start or complete a task
- Update status
- Add context or commits
- Make any roadmap modification

These changes are recorded in the audit trail with:
- **Who:** The user/system that made the change
- **When:** Timestamp of the change
- **What:** The specific modification
- **Why:** Context if provided

### Viewing Your Contribution History

```bash
# See recent changes you made
vibey roadmap audit log --limit 20

# View history for a specific task you worked on
vibey roadmap audit show <task-id>
```

### How Commits Are Linked

When you commit with the proper format:

```bash
git commit -m "feat(scope): Add feature

Task: 01KC2D0JK7READW9KAK1HBX4A5"
```

The git hooks automatically:
1. Validate the task ID exists
2. Link the commit to the task
3. Log the association in the audit trail

### Why Audit Trail Matters

For contributors, the audit trail:
- **Provides attribution** - Your work is properly credited
- **Supports debugging** - Track when issues were introduced
- **Enables rollback** - Understand state changes
- **Documents progress** - Show what was accomplished

---

## Testing Guide

### Test Organization

```
tests/
├── cli/              # CLI command tests
├── operations/       # Operation tests
├── roadmap/          # Model and serialization tests
└── mcp/              # MCP server tests
```

### Writing Tests

```python
# tests/operations/roadmap/test_my_feature.py

import pytest
from vibey.operations.roadmap.my_feature import my_function


class TestMyFunction:
    """Test suite for my_function."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = my_function("input")
        assert result == "expected"

    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            my_function(None)
```

### Running Specific Tests

```bash
# Single file
pytest tests/operations/roadmap/test_my_feature.py

# Single test
pytest tests/operations/roadmap/test_my_feature.py::TestMyFunction::test_basic_case

# By keyword
pytest -k "my_feature"
```

---

## Code Standards

### Python Style

- **Formatting:** Black (line length 88)
- **Imports:** isort with black profile
- **Types:** Full type hints required
- **Docstrings:** Google style

### Example

```python
def process_task(
    task_id: str,
    options: Optional[Dict[str, Any]] = None,
) -> TaskResult:
    """
    Process a task with given options.

    Args:
        task_id: The unique task identifier (ULID format)
        options: Optional processing options

    Returns:
        TaskResult containing status and metadata

    Raises:
        TaskNotFoundError: If task_id doesn't exist
        ValidationError: If options are invalid
    """
    # Implementation...
```

---

## Documentation Touchpoints

| Activity | Documents |
|----------|-----------|
| Getting started | CONTRIBUTING.md |
| Codebase overview | CLAUDE.md |
| CLI reference | docs/reference/CLI_REFERENCE.md |
| Architecture | docs/development/*.md |
| Test patterns | tests/README.md |

---

## Hands-On Tutorial

Make your first contribution with a step-by-step walkthrough:

**📚 [Contributor Walkthrough: Your First Vibey Contribution](../walkthroughs/WALKTHROUGH_CONTRIBUTOR.md)**

This walkthrough covers:
- Development environment setup
- Codebase navigation
- Test suite execution
- Pull request workflow
