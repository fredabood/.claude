# Contributing to Vibey Agent Framework

Thank you for your interest in contributing to Vibey! This guide will help you get started.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

---

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to make Vibey better.

---

## Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/vibey.git
cd vibey

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Install pre-commit hooks
pre-commit install

# 5. Verify setup
vibey --version
pytest tests/ -x -q
```

For detailed setup instructions, see **[Development Setup Guide](docs/development/SETUP.md)**.

---

## Development Setup

### Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **Git** 2.30+
- **SQLite** 3.35+ (usually included with Python)

### Detailed Setup

The complete development environment setup is documented in:

- **[docs/development/SETUP.md](docs/development/SETUP.md)** - Environment setup, IDE configuration, troubleshooting
- **[docs/development/CODING_STANDARDS.md](docs/development/CODING_STANDARDS.md)** - Code style, conventions, best practices

### Verify Your Setup

```bash
# Run the test suite
pytest tests/ -x -q

# Check code formatting
black --check vibey/ tests/
isort --check vibey/ tests/

# Type checking
mypy vibey/

# CLI works
vibey --help
vibey roadmap status
```

---

## How to Contribute

### Types of Contributions

| Type | Description | Good First Issue? |
|------|-------------|-------------------|
| Bug fixes | Fix issues in CLI, operations, or MCP server | Yes |
| Documentation | Improve guides, fix typos, add examples | Yes |
| Tests | Add test coverage, fix flaky tests | Yes |
| New features | Add CLI commands, MCP tools | Sometimes |
| Platform adapters | Add support for new AI platforms | No |
| Architecture | Core system changes | No |

### Finding Work

1. **Good First Issues** - Look for the `good-first-issue` label on GitHub
2. **Roadmap** - Check active sprints: `vibey roadmap status`
3. **Documentation** - Always welcome improvements
4. **Your Ideas** - Open an issue to discuss before implementing

### Understanding the Codebase

Before contributing, familiarize yourself with:

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Repository context and session guidelines |
| [README.md](README.md) | Project overview and quick start |
| [CHANGELOG.md](CHANGELOG.md) | Version history and recent changes |
| [docs/architecture/adr/](docs/architecture/adr/) | Architectural decisions |

---

## Development Workflow

### Project Structure

```
vibey/
├── vibey/                    # Python package (ALL code here)
│   ├── cli/                  # CLI commands (Click)
│   ├── operations/           # Core business logic
│   │   ├── roadmap/          # Roadmap operations
│   │   └── docs/             # Documentation generation
│   ├── mcp/                  # MCP server implementation
│   ├── adapters/             # Platform adapters (9 platforms)
│   ├── common/               # Shared utilities, errors
│   └── roadmap/              # Models and serialization
│
├── .vibey/                   # Framework data
│   ├── config/               # Modular configuration
│   └── roadmap/              # Roadmap system (YAML + SQLite)
│
├── docs/                     # Documentation
│   ├── development/          # SETUP.md, CODING_STANDARDS.md
│   ├── architecture/adr/     # Architectural Decision Records
│   ├── reference/            # CLI_REFERENCE.md, MCP_REFERENCE.md
│   └── guides/               # User guides
│
├── tests/                    # Test suite
└── pyproject.toml            # Project configuration
```

### Design Principles

1. **YAML Source of Truth** - All roadmap data in human-readable YAML files
2. **SQLite Query Cache** - Fast queries, regenerable from YAML
3. **CLI First** - `vibey` command is the primary interface
4. **MCP for AI** - Model Context Protocol for AI assistant integration
5. **Platform Agnostic** - Core operations shared across platforms

See [Architectural Decision Records](docs/architecture/adr/) for detailed rationale.

### Making Changes

#### Adding CLI Commands

```python
# vibey/cli/commands.py

@roadmap.command('my-command')
@click.argument('item_id')
@click.option('--format', '-f', type=click.Choice(['text', 'json']))
def my_command(item_id: str, format: str):
    """Short description for --help."""
    # Call operations layer
    result = my_operation(item_id)
    # Output result
    click.echo(format_output(result, format))
```

#### Adding MCP Tools

```python
# vibey/mcp/server.py

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Any:
    if name == "vibey_my_tool":
        return await my_tool_handler(arguments)
```

#### Adding Operations

```python
# vibey/operations/roadmap/my_operation.py

def my_operation(item_id: str) -> Result:
    """Operation description.

    Args:
        item_id: ULID identifier for the item.

    Returns:
        Result object with operation outcome.

    Raises:
        ItemNotFoundError: If item doesn't exist.
    """
    # Implementation
```

### Testing Your Changes

```bash
# Run specific tests
pytest tests/path/to/test.py -v

# Run with coverage
pytest tests/ --cov=vibey --cov-report=term-missing

# Run type checking
mypy vibey/

# Format code
black vibey/ tests/
isort vibey/ tests/
```

See [Coding Standards](docs/development/CODING_STANDARDS.md) for testing conventions.

---

## Submitting Changes

### Branch Naming

```bash
git checkout -b feat/add-new-command     # New feature
git checkout -b fix/cli-error-handling   # Bug fix
git checkout -b docs/update-readme       # Documentation
git checkout -b refactor/simplify-loader # Refactoring
```

### Commit Messages

Format: `type(scope): description`

```bash
# Good examples
git commit -m "feat(cli): add batch update command"
git commit -m "fix(roadmap): handle missing sprint gracefully"
git commit -m "docs: update CONTRIBUTING with new workflow"
git commit -m "test(mcp): add tool introspection tests"

# Types: feat, fix, docs, test, refactor, chore
```

### Pre-commit Checks

Pre-commit hooks run automatically:

```bash
# Manual run
pre-commit run --all-files

# Skip hooks (emergency only)
git commit --no-verify -m "message"
```

### Pull Request Process

1. **Create PR** from your branch to `main`
2. **Fill out template**:
   ```markdown
   ## Summary
   Brief description of changes.

   ## Changes
   - Change 1
   - Change 2

   ## Testing
   How was this tested?

   ## Checklist
   - [ ] Tests pass
   - [ ] Code formatted
   - [ ] Documentation updated
   ```
3. **Address feedback** from reviewers
4. **Merge** after approval

---

## Release Process

### Version Numbering

Format: `MAJOR.MINOR.PATCH` (Semantic Versioning)

- **MAJOR** - Breaking changes to CLI or API
- **MINOR** - New features, backward compatible
- **PATCH** - Bug fixes, documentation

### Pre-Release Checklist

- [ ] All tests passing (`pytest tests/`)
- [ ] Code formatted (`black --check vibey/`)
- [ ] Type hints pass (`mypy vibey/`)
- [ ] CHANGELOG.md updated
- [ ] Documentation current
- [ ] CLI reference regenerated (`vibey docs generate-cli`)
- [ ] MCP reference regenerated (`vibey docs generate-mcp`)

### Creating a Release

```bash
# 1. Update CHANGELOG.md with release notes
# 2. Update version in pyproject.toml
# 3. Commit changes
git commit -m "chore: prepare release v2.6.0"

# 4. Tag release
git tag -a v2.6.0 -m "Release v2.6.0"

# 5. Push
git push origin main --tags
```

---

## Getting Help

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - Questions, ideas
- **Documentation** - Start with [README.md](README.md)

### Useful Commands

```bash
# Project status
vibey roadmap status

# CLI help
vibey --help
vibey roadmap --help

# Run tests
pytest tests/ -v

# Check documentation drift
vibey docs check-drift
```

---

## Additional Resources

- [Development Setup Guide](docs/development/SETUP.md)
- [Coding Standards](docs/development/CODING_STANDARDS.md)
- [Architectural Decision Records](docs/architecture/adr/)
- [CLI Reference](docs/reference/CLI_REFERENCE.md)
- [MCP Reference](docs/reference/MCP_REFERENCE.md)
- [Contributor Walkthrough](docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md)

---

Thank you for contributing!
