# Sprint 2.5: Contributor Experience & Project Docs

## Sprint Overview

| Field | Value |
|-------|-------|
| **Sprint ID** | `01KC81GRE3GXVPVSCMD19FC4Z7` |
| **Sprint Name** | Phase 2.5: Contributor Experience & Project Docs |
| **Track** | User Journey Audit |
| **Status** | Not Started |
| **Total Tasks** | 7 |
| **Focus Area** | Documentation accuracy and contributor onboarding |

## Sprint Objective

Update README, CHANGELOG, CONTRIBUTING, and CLAUDE.md to accurately reflect the current project state. Create comprehensive contributor documentation including development setup guides, coding standards, and architectural decision records (ADRs). The goal is to ensure any new contributor can onboard successfully and understand the project's architecture, conventions, and history.

---

## Task Inventory

| # | Task ID | Title | Complexity | Est. Tokens |
|---|---------|-------|------------|-------------|
| 1 | `01KC81GRE3GXVPVSCMD19FC4Z8` | Audit and update README.md | Medium | 15,000 |
| 2 | `01KC81GRE4ZAJR0ZP9RCQCJ79S` | Audit and update CHANGELOG.md | Medium | 12,000 |
| 3 | `01KC81GRE4ZAJR0ZP9RCQCJ79T` | Create comprehensive CONTRIBUTING.md | Medium | 18,000 |
| 4 | `01KC81GRE4ZAJR0ZP9RCQCJ79V` | Create development environment setup guide | Medium | 12,000 |
| 5 | `01KC81GRE4ZAJR0ZP9RCQCJ79W` | Document coding standards and conventions | Medium | 10,000 |
| 6 | `01KC81GRE4ZAJR0ZP9RCQCJ79X` | Create architectural decision records (ADRs) | Medium | 15,000 |
| 7 | `01KC81GRE4ZAJR0ZP9RCQCJ79Y` | Update CLAUDE.md with current state | Medium | 15,000 |

**Total Estimated Tokens:** 97,000

---

## Task Dependencies

```
Task 1 (README.md) ─────────────────────────────────────┐
                                                        │
Task 2 (CHANGELOG.md) ──────────────────────────────────┤
                                                        ├──► Task 7 (CLAUDE.md)
Task 4 (Dev Setup) ─────► Task 3 (CONTRIBUTING.md) ─────┤
                                                        │
Task 5 (Coding Standards) ──► Task 3 (CONTRIBUTING.md) ─┤
                                                        │
Task 6 (ADRs) ──────────────────────────────────────────┘
```

**Execution Order:**
1. Tasks 1, 2, 4, 5, 6 can run in parallel (independent research/documentation)
2. Task 3 depends on Tasks 4 and 5 (references dev setup and coding standards)
3. Task 7 runs last (synthesizes all other documentation updates)

---

## Task 1: Audit and Update README.md

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE3GXVPVSCMD19FC4Z8` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 15,000 |

### Objective
Comprehensive update of README to accurately reflect current project state: features, installation, examples, and links.

### Current State Analysis

The current README.md (14,768 bytes) includes:
- Version 2.5.0 header with platform status
- pip installation instructions
- Platform-agnostic architecture description
- Quick start guide
- CLI command examples

**Issues to Address:**
1. **Version accuracy** - Verify 2.5.0 is correct or update
2. **Feature list completeness** - Missing roadmap system features
3. **Installation verification** - Test pip install actually works
4. **Example accuracy** - Verify all CLI commands shown actually work
5. **Link validity** - Check all documentation links resolve
6. **Platform status** - Update Claude Code/Goose/Cursor status

### Implementation Plan

#### Phase 1: Audit Current Content (30 min)
```bash
# Check current README sections
grep -n "^##" README.md

# Verify pip package exists
pip index versions vibey-framework 2>/dev/null || echo "Package not on PyPI"

# Test documented commands
vibey --help
vibey deploy --help
vibey roadmap --help
```

#### Phase 2: Feature Inventory (1 hour)
Document all current features by examining:

1. **CLI Commands** - Walk `vibey/cli/commands.py`
2. **MCP Tools** - Check `vibey/mcp/server.py`
3. **Roadmap System** - Document track/sprint/task management
4. **Platform Adapters** - List supported platforms
5. **Configuration System** - Document `.vibey/config/` structure

#### Phase 3: Update Sections

**Section: What's New**
```markdown
## What's New in v2.6.0

### Roadmap System Enhancements
- **SQLite Backend** - High-performance database storage
- **YAML Round-Trip** - Lossless serialization
- **Activity Logging** - Audit trail for all changes
- **Git Integration** - Pre-commit/post-commit hooks

### MCP Server Improvements
- **MCP Resources** - Workflow and handoff discovery
- **MCP Prompts** - Quality gate integration
- **Auto-Setup** - Platform-specific installation

### CLI Improvements
- **Auto-Progress** - Automatic status updates
- **Batch Operations** - Multi-item updates
- **Context Management** - Sprint/task context loading
```

**Section: Installation**
```markdown
## Installation

### Prerequisites
- Python 3.9 or later
- Git (for version control integration)
- SQLite 3.x (included with Python)

### Via pip
```bash
pip install vibey-framework
```

### From Source (Development)
```bash
git clone https://github.com/fredabood/vibey.git
cd vibey
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```
```

**Section: Quick Start**
Update with verified, working commands:
```markdown
## Quick Start

### 1. Initialize Project
```bash
cd your-project
vibey init
```

### 2. View Roadmap Status
```bash
vibey roadmap status
```

### 3. Start Working on a Task
```bash
vibey roadmap start <task-id>
```

### 4. Complete a Task
```bash
vibey roadmap complete <task-id>
```
```

#### Phase 4: Link Verification
```python
# Script: verify_readme_links.py
import re
import os
from pathlib import Path

def verify_links(readme_path: str) -> dict:
    """Verify all relative links in README resolve."""
    content = Path(readme_path).read_text()

    # Find all markdown links
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

    results = {'valid': [], 'broken': []}
    base_dir = Path(readme_path).parent

    for text, url in links:
        if url.startswith('http'):
            # Skip external links (could add HTTP check)
            continue

        # Remove anchor
        path = url.split('#')[0]
        if not path:
            continue

        full_path = base_dir / path
        if full_path.exists():
            results['valid'].append((text, url))
        else:
            results['broken'].append((text, url))

    return results
```

### Deliverables
1. Updated `README.md` with accurate content
2. `docs/reference/README_AUDIT.md` - Audit findings and changes made
3. All links verified working
4. All CLI examples tested

### Success Criteria
- [ ] Version number matches latest release
- [ ] All documented features actually exist
- [ ] pip install instructions work
- [ ] All CLI examples execute successfully
- [ ] All internal links resolve
- [ ] Platform status is accurate

---

## Task 2: Audit and Update CHANGELOG.md

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE4ZAJR0ZP9RCQCJ79S` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 12,000 |

### Objective
Review git history since last changelog entry and ensure CHANGELOG accurately reflects all releases, breaking changes, and notable updates.

### Current State Analysis

The current CHANGELOG.md (16,765 bytes) shows:
- Last entry: `[1.3.0] - 2025-11-09`
- Format: Keep a Changelog + Semantic Versioning
- Sections: Added, Changed, Improved, Fixed

**Gap Analysis:**
- 50+ commits since 2025-11-09 not documented
- Multiple feature additions not logged
- Bug fixes not cataloged
- No [Unreleased] section content

### Implementation Plan

#### Phase 1: Git History Analysis (45 min)

```bash
# Get all commits since last changelog entry
git log --oneline --since="2025-11-09" > /tmp/commits_since_1.3.0.txt

# Categorize by conventional commit type
git log --oneline --since="2025-11-09" | grep "^[a-f0-9]* feat" > /tmp/features.txt
git log --oneline --since="2025-11-09" | grep "^[a-f0-9]* fix" > /tmp/fixes.txt
git log --oneline --since="2025-11-09" | grep "^[a-f0-9]* refactor" > /tmp/refactors.txt
git log --oneline --since="2025-11-09" | grep "^[a-f0-9]* docs" > /tmp/docs.txt
```

#### Phase 2: Categorize Changes

**Features (feat:) - Map to "Added":**
```markdown
### Added

**Roadmap System:**
- SQLite backend with 26-table schema
- YAML round-trip serialization (lossless)
- Activity logging and audit trail
- Auto-progress track/sprint/task status
- Batch operations for bulk updates

**MCP Server:**
- MCP Resources architecture (workflows, handoffs)
- MCP Prompts for quality gates
- Auto-setup for Claude Code and JetBrains

**Git Integration:**
- Pre-commit hook for roadmap validation
- Post-commit hook for status updates
- Bypass detection and warning system

**User Journey Audit:**
- Comprehensive codebase audit (Phase 1 complete)
- File classification taxonomy
- Artifact inventory tooling
```

**Fixes (fix:) - Map to "Fixed":**
```markdown
### Fixed

- YAML task status field placement
- Track/sprint/task ID reference consistency
- Database dump synchronization
- Flat structure migration paths
- CLI auto-progress display issues
```

**Refactors (refactor:) - Map to "Changed":**
```markdown
### Changed

- Consolidated 13 platform port tracks into single track
- Migrated to flat directory structure
- Extracted 1,306 embedded tasks to standalone files
- Updated path resolution for ULID-based IDs
```

#### Phase 3: Structure Updates

**Add [Unreleased] Section:**
```markdown
## [Unreleased]

### Added
- User Journey Audit track (Phase 1 complete, Phase 2 in progress)
- Comprehensive sprint planning documentation

### Changed
- Roadmap system uses flat ULID-based file structure

### Fixed
- CLI edit command appending instead of updating
- Auto-progress track name display
```

**Determine Version Bump:**
Based on changes:
- New features (roadmap system, MCP) → Minor version bump
- No breaking changes → Not major
- Recommendation: `2.6.0` or `1.4.0` depending on versioning strategy

#### Phase 4: Format Verification

```python
# Script: validate_changelog.py
import re
from pathlib import Path

def validate_changelog(path: str) -> list:
    """Validate CHANGELOG follows Keep a Changelog format."""
    content = Path(path).read_text()
    issues = []

    # Check header
    if not content.startswith('# Changelog'):
        issues.append("Missing '# Changelog' header")

    # Check version format [X.Y.Z] - YYYY-MM-DD
    versions = re.findall(r'\[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})', content)
    if not versions:
        issues.append("No properly formatted version entries")

    # Check for [Unreleased] section
    if '[Unreleased]' not in content:
        issues.append("Missing [Unreleased] section")

    # Check section headers
    required_sections = ['Added', 'Changed', 'Fixed']
    for section in required_sections:
        if f'### {section}' not in content:
            issues.append(f"Missing '### {section}' section")

    return issues
```

### Deliverables
1. Updated `CHANGELOG.md` with all changes since 1.3.0
2. Properly formatted [Unreleased] section
3. Version recommendation for next release

### Success Criteria
- [ ] All commits since 1.3.0 categorized
- [ ] Follows Keep a Changelog format
- [ ] Semantic versioning compliance
- [ ] [Unreleased] section maintained
- [ ] No duplicate entries

---

## Task 3: Create Comprehensive CONTRIBUTING.md

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE4ZAJR0ZP9RCQCJ79T` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 18,000 |

### Objective
Write detailed contribution guide covering development setup, coding standards, testing requirements, PR process, and review criteria.

### Current State Analysis

The current CONTRIBUTING.md (14,768 bytes) includes:
- Code of conduct
- Getting started / prerequisites
- Development setup (fork, clone, install)
- Basic contribution guidelines

**Issues to Address:**
1. **Outdated paths** - References `framework/scripts/` (moved)
2. **Missing roadmap integration** - No mention of roadmap system
3. **Incomplete PR process** - Missing template and review criteria
4. **No testing guide** - Missing pytest instructions
5. **Missing commit conventions** - Conventional commits not documented

### Implementation Plan

#### Phase 1: Structure Design

```markdown
# Contributing to Vibey

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Commit Guidelines](#commit-guidelines)
9. [Pull Request Process](#pull-request-process)
10. [Review Criteria](#review-criteria)
11. [Roadmap Contribution](#roadmap-contribution)
12. [Getting Help](#getting-help)
```

#### Phase 2: Section Content

**Quick Start Section:**
```markdown
## Quick Start

Want to contribute quickly? Here's the fastest path:

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Create a branch: `git checkout -b feat/your-feature`
5. Make changes and add tests
6. Run tests: `pytest`
7. Commit with conventional format: `git commit -m "feat: add feature"`
8. Push and create PR

See sections below for detailed guidance.
```

**Development Setup Section:**
```markdown
## Development Setup

### Prerequisites
- Python 3.9+
- Git
- SQLite 3.x (included with Python)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vibey.git
cd vibey

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify installation
vibey --version
pytest --collect-only
```

### IDE Setup

**VS Code:**
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

**PyCharm:**
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment → `.venv/bin/python`
3. Enable pytest as test runner
```

**Project Structure Section:**
```markdown
## Project Structure

```
vibey/
├── vibey/                 # Python package (ALL code lives here)
│   ├── cli/               # CLI commands (Click-based)
│   ├── operations/        # Core business logic
│   │   ├── roadmap/       # Roadmap operations
│   │   └── docs/          # Documentation generation
│   ├── mcp/               # MCP server implementation
│   ├── adapters/          # Platform adapters
│   ├── common/            # Shared utilities, errors
│   └── roadmap/           # Models and serialization
│
├── framework/             # Content files ONLY (no Python)
│   ├── agents/            # Agent definitions
│   ├── workflows/         # Workflow definitions
│   └── templates/         # Jinja2 templates
│
├── docs/                  # Documentation
│   ├── guides/            # User guides
│   └── reference/         # API reference
│
├── tests/                 # Test suite
│   ├── cli/               # CLI tests
│   ├── operations/        # Operations tests
│   └── roadmap/           # Roadmap tests
│
└── .vibey/                # Roadmap data (not code)
    ├── roadmap/           # Tracks, sprints, tasks
    └── config/            # Project configuration
```

**Key Principle:** Python code goes in `vibey/`. Content/data goes in `framework/` or `.vibey/`.
```

**Commit Guidelines Section:**
```markdown
## Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes nor adds |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

### Scopes
| Scope | Description |
|-------|-------------|
| `cli` | CLI commands |
| `mcp` | MCP server |
| `roadmap` | Roadmap system |
| `operations` | Core operations |
| `docs` | Documentation |

### Examples
```bash
feat(cli): add batch update command
fix(roadmap): correct status field placement in YAML
docs(guides): update MCP integration guide
refactor(operations): extract common validation logic
test(cli): add integration tests for roadmap commands
```
```

**Pull Request Process Section:**
```markdown
## Pull Request Process

### Before Creating PR
1. [ ] Tests pass locally: `pytest`
2. [ ] Code formatted: `black vibey/ tests/`
3. [ ] Types checked: `mypy vibey/`
4. [ ] Docs updated if needed
5. [ ] CHANGELOG.md updated for user-facing changes

### PR Template
Use this template when creating PRs:

```markdown
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How were changes tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No breaking changes (or documented)
```

### Review Process
1. Create PR against `main` branch
2. Automated checks must pass
3. At least one maintainer review required
4. Address review feedback
5. Maintainer merges when approved
```

**Roadmap Contribution Section:**
```markdown
## Roadmap Contribution

Vibey uses its own roadmap system for project management.

### Working on a Task

```bash
# Find available tasks
vibey roadmap status --available

# Start working on a task
vibey roadmap start <task-id>

# Complete a task
vibey roadmap complete <task-id>
```

### Proposing New Work

1. Check existing tracks: `vibey roadmap status`
2. Open GitHub issue describing the work
3. Maintainers will create track/sprint/tasks if approved
4. You can then pick up tasks from the sprint

### Bug Reports

For bugs found during development:
```bash
# Log to dogfooding track
vibey roadmap create-task \
  --sprint dogfooding-bugs-XX \
  --title "Bug description" \
  --description "Details..."
```
```

### Deliverables
1. Complete rewrite of `CONTRIBUTING.md`
2. Cross-references to Task 4 (dev setup) and Task 5 (coding standards)
3. PR template file at `.github/PULL_REQUEST_TEMPLATE.md`

### Success Criteria
- [ ] All sections complete with accurate content
- [ ] Paths reference current structure
- [ ] Commands verified working
- [ ] Links to related docs
- [ ] PR template created

---

## Task 4: Create Development Environment Setup Guide

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE4ZAJR0ZP9RCQCJ79V` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 12,000 |

### Objective
Step-by-step guide for setting up local development: Python version, venv, dependencies, pre-commit hooks, IDE setup.

### Implementation Plan

#### Phase 1: Create Guide Structure

**File:** `docs/development/SETUP.md`

```markdown
# Development Environment Setup

## Overview

This guide walks you through setting up a complete development environment
for contributing to Vibey. By the end, you'll have:

- Python virtual environment configured
- All dependencies installed
- Pre-commit hooks active
- IDE configured for the project
- Ability to run tests and CLI

## Prerequisites

### Required
- **Python 3.9+** - Check: `python --version`
- **Git** - Check: `git --version`
- **pip** - Check: `pip --version`

### Recommended
- **VS Code** or **PyCharm** - IDE with Python support
- **pyenv** - Python version management (optional but helpful)

## Step-by-Step Setup
```

#### Phase 2: Platform-Specific Instructions

**macOS Section:**
```markdown
### macOS

#### Install Python (if needed)
```bash
# Using Homebrew
brew install python@3.11

# Or using pyenv
brew install pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

#### Clone and Setup
```bash
# Clone repository
git clone https://github.com/fredabood/vibey.git
cd vibey

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Verify activation (should show .venv path)
which python

# Install package with dev dependencies
pip install -e ".[dev]"

# Verify CLI works
vibey --version
```
```

**Linux Section:**
```markdown
### Linux (Ubuntu/Debian)

#### Install Python (if needed)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

#### Clone and Setup
```bash
git clone https://github.com/fredabood/vibey.git
cd vibey
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
vibey --version
```
```

**Windows Section:**
```markdown
### Windows

#### Install Python
1. Download from https://www.python.org/downloads/
2. Run installer, check "Add Python to PATH"
3. Open new terminal, verify: `python --version`

#### Clone and Setup
```powershell
git clone https://github.com/fredabood/vibey.git
cd vibey
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
vibey --version
```
```

#### Phase 3: Pre-commit Hooks

```markdown
## Pre-commit Hooks

Vibey uses pre-commit hooks to ensure code quality before commits.

### Installation
```bash
# Install pre-commit
pip install pre-commit

# Install hooks for this repo
pre-commit install

# (Optional) Run on all files
pre-commit run --all-files
```

### What Hooks Run
| Hook | Purpose |
|------|---------|
| `black` | Code formatting |
| `isort` | Import sorting |
| `flake8` | Linting |
| `mypy` | Type checking |
| `pytest` | Quick tests |

### Bypassing Hooks
For work-in-progress commits (use sparingly):
```bash
git commit --no-verify -m "wip: work in progress"
```
```

#### Phase 4: IDE Configuration

```markdown
## IDE Configuration

### VS Code

#### Recommended Extensions
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- GitLens (eamodio.gitlens)

#### Workspace Settings
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "editor.formatOnSave": true,
  "editor.rulers": [88, 120],
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "python.analysis.typeCheckingMode": "basic"
}
```

### PyCharm

1. **Interpreter Setup**
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Add Local Interpreter
   - Select `.venv/bin/python`

2. **Test Runner**
   - File → Settings → Tools → Python Integrated Tools
   - Default test runner: pytest

3. **Code Style**
   - File → Settings → Editor → Code Style → Python
   - Set line length to 88 (Black default)
```

#### Phase 5: Verification Checklist

```markdown
## Verification Checklist

Run through this checklist to verify your setup:

```bash
# 1. Python version
python --version
# Expected: Python 3.9+

# 2. Virtual environment active
which python
# Expected: .../vibey/.venv/bin/python

# 3. Package installed
vibey --version
# Expected: vibey X.Y.Z

# 4. Tests run
pytest tests/ -v --tb=short
# Expected: All tests pass (or known failures)

# 5. CLI works
vibey roadmap status
# Expected: Track status output

# 6. Pre-commit works
pre-commit run --all-files
# Expected: All hooks pass
```

## Troubleshooting

### "vibey: command not found"
```bash
# Ensure venv is activated
source .venv/bin/activate

# Or run via Python
python -m vibey --version
```

### "ModuleNotFoundError"
```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

### Pre-commit hook fails
```bash
# Update hooks
pre-commit autoupdate

# Clear cache and retry
pre-commit clean
pre-commit run --all-files
```
```

### Deliverables
1. `docs/development/SETUP.md` - Complete setup guide
2. Platform-specific instructions (macOS, Linux, Windows)
3. IDE configuration files (`.vscode/settings.json.example`)
4. Troubleshooting section

### Success Criteria
- [ ] Instructions tested on macOS
- [ ] Instructions tested on Linux (or verified)
- [ ] Instructions tested on Windows (or verified)
- [ ] All commands execute successfully
- [ ] Troubleshooting covers common issues

---

## Task 5: Document Coding Standards and Conventions

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE4ZAJR0ZP9RCQCJ79W` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 10,000 |

### Objective
Document project-specific coding standards: file organization, naming conventions, docstring format, error handling patterns.

### Implementation Plan

#### Phase 1: Analyze Existing Patterns

Examine codebase to document actual conventions:
```bash
# Find docstring patterns
grep -r '"""' vibey/ | head -20

# Find error handling patterns
grep -r 'raise.*Error' vibey/ | head -20

# Find naming conventions
ls vibey/**/*.py
```

#### Phase 2: Create Standards Document

**File:** `docs/development/CODING_STANDARDS.md`

```markdown
# Coding Standards and Conventions

## Overview

This document defines the coding standards for the Vibey project.
Following these standards ensures consistency and maintainability.

## Python Style

### Formatting
- **Formatter:** Black (line length: 88)
- **Import Sorting:** isort (Black-compatible profile)
- **Linting:** flake8

### Type Hints
All public functions and methods should include type hints:

```python
# Good
def load_track(track_id: str) -> Track:
    """Load a track by ID."""
    ...

# Also good (complex types)
def find_tasks(
    status: Optional[str] = None,
    track_id: Optional[str] = None,
) -> list[Task]:
    """Find tasks matching criteria."""
    ...
```

### Docstrings
Use Google-style docstrings:

```python
def update_task_status(
    task_id: str,
    new_status: str,
    reason: Optional[str] = None,
) -> Task:
    """Update a task's status.

    Args:
        task_id: The unique task identifier (ULID).
        new_status: Target status (not_started, in_progress, completed).
        reason: Optional explanation for the status change.

    Returns:
        The updated Task object.

    Raises:
        TaskNotFoundError: If task_id doesn't exist.
        InvalidStatusError: If new_status is invalid.

    Example:
        >>> task = update_task_status("01ABC...", "completed")
        >>> task.status
        'completed'
    """
```

## File Organization

### Package Structure
```
vibey/
├── __init__.py          # Package exports
├── cli/                 # User-facing CLI
│   ├── __init__.py
│   ├── main.py          # Click entry point
│   └── commands.py      # Command implementations
├── operations/          # Business logic (no UI)
│   ├── __init__.py
│   ├── roadmap/         # Roadmap operations
│   │   ├── __init__.py
│   │   ├── query.py     # Read operations
│   │   ├── update.py    # Write operations
│   │   └── context.py   # Context loading
│   └── docs/            # Doc generation
├── common/              # Shared utilities
│   ├── __init__.py
│   ├── errors.py        # Error types
│   └── utils.py         # Helpers
└── roadmap/             # Data models
    ├── __init__.py
    ├── models/          # Dataclasses
    └── serialization/   # YAML/SQL loaders
```

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `yaml_loader.py` |
| Classes | PascalCase | `TaskStatus` |
| Functions | snake_case | `load_track()` |
| Constants | UPPER_SNAKE | `DEFAULT_STATUS` |
| Private | _prefix | `_internal_helper()` |

## Error Handling

### Error Class Hierarchy
```python
from vibey.common.errors import (
    VibeyError,           # Base class
    ConfigError,          # Configuration issues
    RoadmapError,         # Roadmap operations
    TaskNotFoundError,    # Specific roadmap errors
    ValidationError,      # Input validation
)
```

### Error Pattern
```python
# Raise specific errors with context
if not task:
    raise TaskNotFoundError(
        task_id=task_id,
        message=f"Task {task_id} not found in database",
        context={"search_path": str(db_path)},
    )

# Catch and re-raise with context
try:
    result = load_yaml(path)
except YAMLError as e:
    raise ConfigError(
        message=f"Invalid YAML in {path}",
        cause=e,
    )
```

### Error Messages
- Be specific about what went wrong
- Include relevant IDs and paths
- Suggest remediation when possible

```python
# Good
raise ValidationError(
    "Invalid status 'done'. Valid values: not_started, in_progress, completed"
)

# Bad
raise ValueError("Invalid status")
```

## Logging

### Logger Setup
```python
import logging

logger = logging.getLogger(__name__)
```

### Log Levels
| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info |
| INFO | Normal operation events |
| WARNING | Unexpected but handled situations |
| ERROR | Errors that prevent operation |

### Logging Pattern
```python
logger.debug(f"Loading track from {path}")
logger.info(f"Track {track_id} loaded with {len(sprints)} sprints")
logger.warning(f"Deprecated field 'old_field' in {path}")
logger.error(f"Failed to load track: {e}")
```

## Testing Conventions

### Test File Organization
```
tests/
├── conftest.py          # Shared fixtures
├── cli/
│   ├── test_commands.py
│   └── test_main.py
├── operations/
│   └── roadmap/
│       ├── test_query.py
│       └── test_update.py
└── roadmap/
    └── test_models.py
```

### Test Naming
```python
def test_load_track_returns_track_object():
    """load_track should return Track instance."""
    ...

def test_load_track_raises_when_not_found():
    """load_track should raise TaskNotFoundError for missing ID."""
    ...
```

### Fixtures
```python
@pytest.fixture
def sample_track() -> Track:
    """Create a sample track for testing."""
    return Track(
        id="test-track-001",
        name="Test Track",
        status="in_progress",
    )

@pytest.fixture
def temp_roadmap_dir(tmp_path) -> Path:
    """Create temporary roadmap directory structure."""
    ...
```
```

### Deliverables
1. `docs/development/CODING_STANDARDS.md` - Complete standards document
2. Examples for each convention
3. Reference to linting configuration

### Success Criteria
- [ ] Documents actual patterns used in codebase
- [ ] Includes examples for all conventions
- [ ] Covers error handling, logging, testing
- [ ] Consistent with Black/flake8/mypy configuration

---

## Task 6: Create Architectural Decision Records (ADRs)

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE4ZAJR0ZP9RCQCJ79X` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 15,000 |

### Objective
Document key architectural decisions in ADR format. Include context, decision, and consequences for major design choices.

### Implementation Plan

#### Phase 1: Identify Key Decisions

Major architectural decisions to document:
1. **ULID for IDs** - Why ULIDs instead of UUIDs or integers
2. **Flat directory structure** - Why flat instead of hierarchical
3. **SQLite + YAML dual storage** - Why both formats
4. **Click for CLI** - Why Click over argparse/typer
5. **MCP integration** - Why MCP for AI assistant integration
6. **Unified error handling** - Why custom error hierarchy
7. **Platform adapter pattern** - Why adapters for multi-platform

#### Phase 2: Create ADR Directory and Template

```bash
mkdir -p docs/architecture/adr
```

**File:** `docs/architecture/adr/0000-template.md`
```markdown
# ADR-NNNN: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue that we're seeing that motivates this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Drawback 1
- Drawback 2

### Neutral
- Side effect 1

## References
- Link to related issues, PRs, or documents
```

#### Phase 3: Write ADRs

**ADR-0001: Use ULIDs for Entity Identifiers**
```markdown
# ADR-0001: Use ULIDs for Entity Identifiers

## Status
Accepted

## Context
The roadmap system needs unique identifiers for tracks, sprints, and tasks.
Options considered:
- Auto-incrementing integers
- UUIDs (v4)
- ULIDs
- Slug-based IDs (human-readable)

Requirements:
- Globally unique without coordination
- Sortable by creation time
- Usable in filenames
- Reasonably short

## Decision
Use ULIDs (Universally Unique Lexicographically Sortable Identifiers) for all
entity identifiers.

Format: `01KC81GRE3GXVPVSCMD19FC4Z7` (26 characters, Crockford Base32)

## Consequences

### Positive
- Time-sortable: IDs sort chronologically by default
- URL/filename safe: No special characters
- Decentralized: Can generate without database
- Short enough: 26 chars vs 36 for UUID
- Monotonic: Multiple IDs in same millisecond sort consistently

### Negative
- Less human-readable than slugs
- Requires ULID library dependency
- Existing slug-based references need migration

### Neutral
- Similar length to UUIDs in practice (no dashes)

## References
- ULID Spec: https://github.com/ulid/spec
- Migration PR: #XXX
```

**ADR-0002: Flat Directory Structure**
```markdown
# ADR-0002: Flat Directory Structure for Roadmap Files

## Status
Accepted

## Context
Original structure was hierarchical:
```
.vibey/roadmap/
└── track-name/
    └── track.yaml
    └── sprint-name/
        └── sprint.yaml
        └── task-name/
            └── task.yaml
```

Problems:
- 40 tracks × 10 sprints × 10 tasks = 4,000 directories
- Expensive `git status` (directory traversal)
- Complex path resolution
- Difficult to rename tracks/sprints

## Decision
Use flat structure with ULID-based filenames:
```
.vibey/roadmap/
├── tracks/
│   └── 01KC2D0JK9JKQXGQW6MQEB0JZP.yaml
├── sprints/
│   └── 01KC2D0JKVT80AFQ6C1PA8CKJD.yaml
└── tasks/
    └── 01KC2D0JK7READW9KAK1HBX4B8.yaml
```

## Consequences

### Positive
- 98% reduction in directories
- Fast git operations
- Simple file lookup by ID
- Easy rename/restructure

### Negative
- Lose visual hierarchy in file explorer
- Need ID-to-name lookup for humans
- Migration complexity

### Neutral
- Files still contain parent references (track_id, sprint_id)
```

**ADR-0003: SQLite + YAML Dual Storage**
```markdown
# ADR-0003: SQLite + YAML Dual Storage

## Status
Accepted

## Context
Roadmap data needs:
- Version control (for collaboration)
- Fast queries (for CLI/MCP)
- Human readability (for debugging)
- Relationship integrity (for consistency)

Single-format options:
- YAML only: Slow queries, no relationships
- SQLite only: Binary, poor diff, merge conflicts

## Decision
Maintain both SQLite and YAML representations:
- YAML files as source of truth (version controlled)
- SQLite database as query cache (regenerable)
- Sync on: CLI operations, git hooks, explicit rebuild

## Consequences

### Positive
- Git-friendly YAML for collaboration
- Fast SQLite queries for operations
- Human-readable audit trail
- Can rebuild database from YAML

### Negative
- Sync complexity
- Potential for drift
- Storage duplication

### Neutral
- Database is gitignored (regenerated locally)
```

**Additional ADRs to create:**
- ADR-0004: Click Framework for CLI
- ADR-0005: MCP Protocol for AI Integration
- ADR-0006: Unified Error Handling Architecture
- ADR-0007: Platform Adapter Pattern

### Deliverables
1. `docs/architecture/adr/` directory
2. ADR template (0000-template.md)
3. 7+ ADR documents covering major decisions
4. Index file listing all ADRs

### Success Criteria
- [ ] ADR directory created
- [ ] Template file established
- [ ] At least 5 ADRs documenting major decisions
- [ ] Each ADR follows consistent format
- [ ] Index file for discovery

---

## Task 7: Update CLAUDE.md with Current State

### Task Details
| Field | Value |
|-------|-------|
| **Task ID** | `01KC81GRE4ZAJR0ZP9RCQCJ79Y` |
| **Type** | Documentation |
| **Complexity** | Medium |
| **Estimated Tokens** | 15,000 |

### Objective
Comprehensive update of CLAUDE.md to accurately reflect current architecture, file structure, and development practices.

### Current State Analysis

The current CLAUDE.md (21,617 bytes) includes:
- Quick Start section
- Framework components overview
- Repository structure
- Development state (outdated - references Nov 11)
- Platform compatibility notes
- Working on this repository guidelines
- Code standards
- Git workflow

**Issues to Address:**
1. **Outdated dates** - References November 2025 updates
2. **Session context** - Shows old sprint status
3. **File structure** - May not reflect flat migration
4. **Missing features** - No mention of recent MCP/roadmap work
5. **Stale paths** - Some paths may have changed

### Implementation Plan

#### Phase 1: Gather Current State

```bash
# Get current version
vibey --version

# Get current track status
sqlite3 .vibey/roadmap.db "
SELECT COUNT(*) as tracks,
       SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
FROM tracks;
"

# Get recent activity
git log --oneline -10

# Get file counts
find vibey/ -name "*.py" | wc -l
find docs/ -name "*.md" | wc -l
```

#### Phase 2: Update Sections

**Quick Start Section:**
```markdown
## Quick Start

Every session working on this repository:

1. **Read this file** (CLAUDE.md) - Framework repository context
2. **Check current roadmap status**: `vibey roadmap status`
3. **Review recent commits**: `git log --oneline -10`
4. **Check for active tasks**: `vibey roadmap status --available`
```

**Current Development State:**
```markdown
## Current Development State

### Framework Status: Production Ready

**Version:** 2.6.0 (or current version)
**Last Updated:** 2025-12-12

**Recent Accomplishments:**
- User Journey Audit Phase 1 complete (6 sprints, 72 tasks)
- MCP Resources and Prompts implemented
- Flat directory structure migration complete
- SQLite backend operational
- Activity logging and audit trail active

**Active Work:**
- User Journey Audit Phase 2 (documentation auto-generation)
- CLI reference guide automation
- MCP server reference guide

**Track Summary:**
| Status | Count |
|--------|-------|
| Completed | XX |
| In Progress | XX |
| Not Started | XX |
```

**Repository Structure:**
```markdown
## Repository Structure

```
vibey/                          # Repository root
├── .vibey/                     # Vibey framework data
│   ├── config/                 # Modular configuration
│   ├── roadmap/                # Roadmap system (flat structure)
│   │   ├── tracks/             # Track YAML files
│   │   ├── sprints/            # Sprint YAML files
│   │   ├── tasks/              # Task YAML files
│   │   └── context/            # Sprint context docs
│   └── roadmap.db              # SQLite database cache
│
├── vibey/                      # Python package
│   ├── cli/                    # CLI (Click-based)
│   ├── operations/             # Business logic
│   │   ├── roadmap/            # Roadmap operations
│   │   ├── git/                # Git integration
│   │   └── docs/               # Doc generation
│   ├── mcp/                    # MCP server
│   ├── common/                 # Shared (errors, utils)
│   └── roadmap/                # Models, serialization
│
├── framework/                  # Content (no Python)
│   ├── agents/                 # Agent definitions
│   └── workflows/              # Workflow definitions
│
├── docs/                       # Documentation
│   ├── guides/                 # User guides
│   ├── development/            # Dev guides (NEW)
│   └── architecture/           # ADRs (NEW)
│
└── tests/                      # Test suite
```
```

**Session Context Section:**
```markdown
## Session Context

**Last Major Update:** 2025-12-12
**Current Phase:** User Journey Audit Phase 2
**Active Sprint:** Phase 2.5 - Contributor Experience

**Key Files Recently Changed:**
- Documentation: README.md, CHANGELOG.md, CONTRIBUTING.md
- Guides: docs/development/SETUP.md, docs/development/CODING_STANDARDS.md
- Architecture: docs/architecture/adr/*.md

**Roadmap System:**
- Use `vibey roadmap status` for current state
- Use `vibey roadmap context <id>` for task details
- SQLite database at `.vibey/roadmap.db`
```

#### Phase 3: Cross-Reference Updates

Ensure CLAUDE.md references:
- New CONTRIBUTING.md sections
- Development setup guide
- Coding standards document
- ADR directory

#### Phase 4: Validation

```bash
# Check all mentioned files exist
grep -oE '\b[a-zA-Z0-9_/-]+\.(md|py|yaml)\b' CLAUDE.md | sort -u | while read f; do
  [ -f "$f" ] || echo "Missing: $f"
done

# Verify commands work
vibey roadmap status
vibey --version
```

### Deliverables
1. Updated `CLAUDE.md` with current state
2. All paths verified existing
3. All commands verified working
4. Cross-references to new documentation

### Success Criteria
- [ ] Version and dates accurate
- [ ] File structure matches reality
- [ ] All mentioned files exist
- [ ] All CLI commands work
- [ ] Links to other docs correct
- [ ] Session context current

---

## Sprint Execution Strategy

### Recommended Order

```
Week 1:
├── Task 1 (README.md) ──────────┐
├── Task 2 (CHANGELOG.md) ───────┤
├── Task 4 (Dev Setup) ──────────┤ (Parallel)
├── Task 5 (Coding Standards) ───┤
└── Task 6 (ADRs) ───────────────┘

Week 2:
├── Task 3 (CONTRIBUTING.md) ──── (Depends on 4, 5)
└── Task 7 (CLAUDE.md) ────────── (Synthesizes all)
```

### Parallel Execution Notes

Tasks 1, 2, 4, 5, 6 are independent and can be worked on simultaneously.
Task 3 should wait for Tasks 4 and 5 to be complete (references their content).
Task 7 should be last as it synthesizes all other documentation updates.

### Quality Gates

Before marking sprint complete:
- [ ] All documentation files pass link validation
- [ ] All CLI examples tested and working
- [ ] All paths in docs verified existing
- [ ] Cross-references between docs consistent
- [ ] Git commit history clean

---

## Appendix A: File Checklist

### Files to Create
- [ ] `docs/development/SETUP.md`
- [ ] `docs/development/CODING_STANDARDS.md`
- [ ] `docs/architecture/adr/0000-template.md`
- [ ] `docs/architecture/adr/0001-ulid-identifiers.md`
- [ ] `docs/architecture/adr/0002-flat-directory.md`
- [ ] `docs/architecture/adr/0003-dual-storage.md`
- [ ] `docs/architecture/adr/0004-click-cli.md`
- [ ] `docs/architecture/adr/0005-mcp-integration.md`
- [ ] `docs/architecture/adr/0006-error-handling.md`
- [ ] `docs/architecture/adr/0007-platform-adapters.md`
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`

### Files to Update
- [ ] `README.md`
- [ ] `CHANGELOG.md`
- [ ] `CONTRIBUTING.md`
- [ ] `CLAUDE.md`

---

## Appendix B: Validation Scripts

### Link Checker
```python
#!/usr/bin/env python3
"""Check all internal links in documentation."""

import re
from pathlib import Path

def check_links(docs_dir: Path) -> dict:
    results = {"valid": [], "broken": []}

    for md_file in docs_dir.rglob("*.md"):
        content = md_file.read_text()
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for text, url in links:
            if url.startswith("http"):
                continue

            target = (md_file.parent / url.split("#")[0]).resolve()
            if target.exists():
                results["valid"].append((md_file, url))
            else:
                results["broken"].append((md_file, url, str(target)))

    return results

if __name__ == "__main__":
    results = check_links(Path("."))

    if results["broken"]:
        print("Broken links found:")
        for source, url, target in results["broken"]:
            print(f"  {source}: {url} -> {target}")
    else:
        print("All links valid!")
```

### Command Validator
```bash
#!/bin/bash
# Validate all CLI commands mentioned in docs

commands=(
    "vibey --version"
    "vibey roadmap status"
    "vibey roadmap status --available"
    "pytest --collect-only"
)

for cmd in "${commands[@]}"; do
    echo -n "Testing: $cmd ... "
    if $cmd >/dev/null 2>&1; then
        echo "OK"
    else
        echo "FAILED"
    fi
done
```

---

## References

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [ADR GitHub Organization](https://adr.github.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
