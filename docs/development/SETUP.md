# Development Environment Setup

This guide walks you through setting up a complete development environment for contributing to Vibey.

## Overview

By the end of this guide, you'll have:
- Python virtual environment configured
- All dependencies installed
- Pre-commit hooks active
- IDE configured for the project
- Ability to run tests and CLI

---

## Prerequisites

### Required

| Tool | Version | Check Command |
|------|---------|---------------|
| **Python** | 3.9+ | `python --version` or `python3 --version` |
| **Git** | 2.x+ | `git --version` |
| **pip** | 21+ | `pip --version` or `pip3 --version` |

### Recommended

- **VS Code** or **PyCharm** - IDE with Python support
- **pyenv** - Python version management (optional)

---

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/fredabood/vibey.git
cd vibey

# Or clone via SSH
git clone git@github.com:fredabood/vibey.git
cd vibey
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (choose your platform)
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows CMD
# .venv\Scripts\Activate.ps1       # Windows PowerShell
```

### Step 3: Install Dependencies

```bash
# Install package with development dependencies
pip install -e ".[dev]"

# Verify CLI is available
vibey --version
# Expected: vibey, version 2.5.0
```

### Step 4: Verify Installation

```bash
# Run the test suite
pytest tests/ -v --tb=short

# Check roadmap status (uses the repo's own roadmap)
vibey roadmap status
```

---

## Platform-Specific Instructions

### macOS

#### Install Python (if needed)

```bash
# Using Homebrew
brew install python@3.11

# Or using pyenv (recommended for version management)
brew install pyenv
pyenv install 3.11.0
pyenv local 3.11.0
```

#### Complete Setup

```bash
git clone https://github.com/fredabood/vibey.git
cd vibey
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
vibey --version
```

### Linux (Ubuntu/Debian)

#### Install Python (if needed)

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

#### Complete Setup

```bash
git clone https://github.com/fredabood/vibey.git
cd vibey
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
vibey --version
```

### Windows

#### Install Python

1. Download from https://www.python.org/downloads/
2. Run installer, check "Add Python to PATH"
3. Open new terminal, verify: `python --version`

#### Complete Setup

```powershell
git clone https://github.com/fredabood/vibey.git
cd vibey
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
vibey --version
```

---

## Pre-commit Hooks

Vibey uses pre-commit hooks to ensure code quality before commits.

### Installation

```bash
# Install pre-commit (included in dev dependencies)
pip install pre-commit

# Install hooks for this repo
pre-commit install

# (Optional) Run on all files to verify
pre-commit run --all-files
```

### What Hooks Run

| Hook | Purpose |
|------|---------|
| `black` | Code formatting |
| `isort` | Import sorting |
| `flake8` | Linting |
| `mypy` | Type checking |

### Bypassing Hooks

For work-in-progress commits (use sparingly):

```bash
git commit --no-verify -m "wip: work in progress"
```

---

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

#### Interpreter Setup

1. **File** → **Settings** → **Project** → **Python Interpreter**
2. Click gear icon → **Add Interpreter** → **Add Local Interpreter**
3. Select **Existing** → Browse to `.venv/bin/python`

#### Test Runner

1. **File** → **Settings** → **Tools** → **Python Integrated Tools**
2. Default test runner: **pytest**

#### Code Style

1. **File** → **Settings** → **Editor** → **Code Style** → **Python**
2. Set line length to 88 (Black default)

---

## Verification Checklist

Run through this checklist to verify your setup:

```bash
# 1. Python version (should be 3.9+)
python --version

# 2. Virtual environment active (path should contain .venv)
which python

# 3. Package installed
vibey --version

# 4. Tests run (should show tests passing)
pytest tests/ -v --tb=short -q

# 5. CLI works (should show roadmap status)
vibey roadmap status

# 6. Pre-commit works (should show hooks passing)
pre-commit run --all-files
```

---

## Troubleshooting

### "vibey: command not found"

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Or run via Python module
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

### SQLite errors

```bash
# Check SQLite version (should be 3.x)
python -c "import sqlite3; print(sqlite3.sqlite_version)"

# If database is corrupted, rebuild
vibey roadmap db rebuild
```

### Import errors in tests

```bash
# Ensure package is installed in editable mode
pip uninstall vibey-framework
pip install -e ".[dev]"
```

---

## Common Development Tasks

### Running Specific Tests

```bash
# Run tests for a specific module
pytest tests/cli/ -v

# Run a specific test file
pytest tests/operations/roadmap/test_query.py -v

# Run tests matching a pattern
pytest tests/ -v -k "test_status"
```

### Generating Documentation

```bash
# Generate CLI reference
vibey docs generate-cli

# Generate MCP reference
vibey docs generate-mcp

# Check for documentation drift
vibey docs check-drift
```

### Working with the Roadmap

```bash
# Check current status
vibey roadmap status

# View available tasks
vibey roadmap status --available

# Start a task
vibey roadmap start <task-id>

# Complete a task
vibey roadmap complete <task-id>
```

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `VIBEY_LOG_LEVEL` | Logging verbosity | `INFO` |
| `VIBEY_DB_PATH` | SQLite database path | `.vibey/roadmap.db` |
| `VIBEY_CONFIG_PATH` | Config directory | `.vibey/config/` |

---

## Next Steps

After setting up your development environment:

1. **Read CONTRIBUTING.md** - Contribution guidelines
2. **Read CODING_STANDARDS.md** - Project conventions
3. **Browse docs/architecture/adr/** - Architectural decisions
4. **Check roadmap status** - Find tasks to work on
5. **Join discussions** - GitHub Issues for questions

---

## Related Documentation

- [Coding Standards](./CODING_STANDARDS.md)
- [Contributor Journey](../journeys/JOURNEY_CONTRIBUTOR.md)
- [Contributor Walkthrough](../walkthroughs/WALKTHROUGH_CONTRIBUTOR.md)
