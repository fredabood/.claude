# Contributing to Vibey

**Thank you for your interest in contributing to Vibey!** This guide will help you set up your development environment, understand the codebase, and submit high-quality contributions.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Code Standards](#code-standards)
5. [Adding Features](#adding-features)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation Requirements](#documentation-requirements)
8. [Git Workflow](#git-workflow)
9. [Pull Request Process](#pull-request-process)
10. [Release Process](#release-process)

---

## Getting Started

### Before Contributing

- Read the [Getting Started Guide](../guides/GETTING_STARTED.md) to understand how Vibey works
- Review the [CLI Reference](../reference/CLI_REFERENCE.md) to see existing features
- Check [open issues](https://github.com/your-org/vibey/issues) for what needs work
- Join our [Discord](https://discord.gg/vibey) to discuss ideas

### Ways to Contribute

We welcome contributions of all types:

- **Bug fixes** - Fix issues in the issue tracker
- **Features** - Add new CLI commands, MCP tools, or core functionality
- **Documentation** - Improve guides, add examples, fix typos
- **Tests** - Increase test coverage, add edge case tests
- **Examples** - Create example projects and roadmaps
- **Tooling** - Improve CI/CD, developer experience

---

## Development Setup

### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork

git clone https://github.com/YOUR-USERNAME/vibey.git
cd vibey

# Add upstream remote
git remote add upstream https://github.com/your-org/vibey.git
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Step 3: Install Development Dependencies

```bash
# Install Vibey in editable mode with all extras
pip install -e ".[dev,mcp,test]"

# Verify installation
vibey --version
pytest --version
```

### Step 4: Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

### Step 5: Run Tests

```bash
# Run full test suite
pytest

# Run with coverage
pytest --cov=vibey --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Step 6: Verify Setup

```bash
# Test CLI
vibey roadmap init --name "Test" --version "1.0.0"
vibey roadmap status

# Test MCP server
python -m framework.mcp.server --help

# Run linters
flake8 vibey/
mypy vibey/
black --check vibey/
```

If all steps succeed, you're ready to develop! 🚀

---

## Project Structure

### Directory Layout

```
vibey/
├── vibey/                          # Core Python package
│   ├── __init__.py
│   ├── cli/                        # CLI implementation
│   │   ├── main.py                 # Click CLI entry point
│   │   ├── commands.py             # Command implementations
│   │   └── formatters.py           # Output formatting
│   ├── common/                     # Shared utilities
│   │   ├── errors.py               # Error handling library
│   │   └── error_renderers.py     # Error output renderers
│   ├── roadmap/                    # Core roadmap models
│   │   ├── models.py               # Roadmap, Track, Sprint, Task
│   │   ├── serialization.py       # YAML serialization
│   │   └── validation.py          # Model validation
│   ├── operations/                 # Business logic
│   │   ├── roadmap/                # Roadmap operations
│   │   │   ├── init.py             # Initialize roadmap
│   │   │   ├── query.py            # Query operations
│   │   │   ├── update.py           # Update operations
│   │   │   └── context.py          # Context generation
│   │   ├── deployment.py           # Framework deployment
│   │   ├── docs.py                 # Documentation generation
│   │   └── config.py               # Configuration management
│   └── config/                     # Configuration loading
│       └── loader.py               # Config file loader
├── framework/                      # Framework files (agents, etc.)
│   ├── mcp/                        # MCP server
│   │   ├── server.py               # Main MCP server
│   │   ├── adapters/               # Core library adapters
│   │   │   └── roadmap_adapter.py
│   │   ├── tools/                  # MCP tools
│   │   │   ├── task_tools.py
│   │   │   ├── sprint_tools.py
│   │   │   └── query_tools.py
│   │   └── utils/                  # MCP utilities
│   │       ├── errors.py
│   │       └── validation.py
│   └── agents/                     # Agent definitions (markdown)
├── tests/                          # Test suite
│   ├── cli/                        # CLI tests
│   ├── roadmap/                    # Roadmap model tests
│   ├── operations/                 # Operations tests
│   └── mcp/                        # MCP server tests
├── docs/                           # Documentation
│   ├── guides/                     # User guides
│   ├── reference/                  # API/CLI reference
│   └── development/                # Developer docs
├── examples/                       # Example projects
├── .github/                        # GitHub Actions workflows
├── setup.py                        # Package setup
├── pyproject.toml                  # Project metadata
├── requirements.txt                # Core dependencies
├── requirements-dev.txt            # Dev dependencies
└── README.md                       # Project overview
```

### Key Files

| File | Purpose |
|------|---------|
| `vibey/cli/main.py` | CLI entry point using Click |
| `vibey/cli/commands.py` | Command implementations (call operations) |
| `vibey/operations/roadmap/*.py` | Core business logic |
| `vibey/roadmap/models.py` | Data models (Roadmap, Track, Sprint, Task) |
| `vibey/common/errors.py` | Unified error handling system |
| `framework/mcp/server.py` | MCP server implementation |
| `tests/cli/test_*.py` | CLI command tests |

---

## Code Standards

### Python Style

We follow **PEP 8** with some modifications:

- **Line length:** 100 characters (not 79)
- **Quotes:** Double quotes for strings
- **Imports:** Sorted with `isort`
- **Formatting:** Automated with `black`

### Formatting Tools

```bash
# Format code
black vibey/

# Sort imports
isort vibey/

# Check formatting
black --check vibey/
isort --check vibey/
```

### Type Hints

Use type hints for all public functions:

```python
# Good
def query_task_details(root_dir: Path, task_id: str) -> Dict[str, Any]:
    """Get detailed task information."""
    pass

# Bad (no type hints)
def query_task_details(root_dir, task_id):
    pass
```

Run `mypy` to check types:
```bash
mypy vibey/
```

### Docstrings

Use Google-style docstrings:

```python
def start_task(root_dir: Path, task_id: str) -> int:
    """
    Start a task (set status to in_progress).

    Args:
        root_dir: Project root directory containing .vibey/
        task_id: Task ID (e.g., 'sprint-1-task-001')

    Returns:
        Exit code (0 for success, 1 for error)

    Raises:
        TaskNotFoundError: If task doesn't exist
        TaskBlockedError: If task has unresolved dependencies

    Example:
        >>> start_task(Path.cwd(), "sprint-1-task-001")
        0
    """
    pass
```

### Error Handling

Use the unified error handling system:

```python
from vibey.common.errors import (
    VibeyError,
    TaskNotFoundError,
    InvalidStateTransitionError
)

def complete_task(task_id: str) -> int:
    """Complete a task."""
    try:
        task = load_task(task_id)

        if task.status != Status.IN_PROGRESS:
            raise InvalidStateTransitionError(
                message=f"Cannot complete task in status: {task.status}",
                current_state=task.status,
                target_state=Status.COMPLETED,
                valid_transitions=[Status.IN_PROGRESS],
                fix_suggestions=[
                    "Start the task first: vibey roadmap start {task_id}",
                    "Check task status: vibey roadmap show {task_id}"
                ]
            )

        task.status = Status.COMPLETED
        save_task(task)
        return 0

    except TaskNotFoundError as e:
        print(format_error(e))
        return 1
    except VibeyError as e:
        print(format_error(e))
        return 1
```

### Logging

Use Python's `logging` module:

```python
import logging

logger = logging.getLogger(__name__)

def complex_operation():
    logger.info("Starting complex operation")
    logger.debug("Debug details here")
    logger.warning("This might be an issue")
    logger.error("Operation failed")
```

---

## Adding Features

### Adding a New CLI Command

Follow these steps to add a new command to the Vibey CLI.

#### Step 1: Add Operation Logic

Create or edit a file in `vibey/operations/`:

```python
# vibey/operations/roadmap/archive.py

from pathlib import Path
from typing import Dict, Any

def archive_sprint(root_dir: Path, sprint_id: str) -> int:
    """
    Archive a completed sprint.

    Args:
        root_dir: Project root directory
        sprint_id: Sprint ID to archive

    Returns:
        Exit code (0 success, 1 error)
    """
    from vibey.roadmap.serialization import load_sprint
    from vibey.common.errors import SprintNotFoundError

    try:
        sprint = load_sprint(root_dir / ".vibey" / "roadmap" / sprint_id / "sprint.yaml")

        # Archive logic here
        archive_path = root_dir / ".vibey" / "archive" / f"{sprint_id}.yaml"
        # ... save to archive ...

        print(f"✅ Sprint {sprint_id} archived to {archive_path}")
        return 0

    except SprintNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
```

#### Step 2: Add Command Wrapper

Edit `vibey/cli/commands.py`:

```python
def roadmap_archive_cmd(sprint_id: str) -> int:
    """Archive a completed sprint."""
    from vibey.operations.roadmap.archive import archive_sprint

    root_dir = Path.cwd()
    return archive_sprint(root_dir, sprint_id)
```

#### Step 3: Add Click Command

Edit `vibey/cli/main.py`:

```python
@roadmap.command('archive')
@click.argument('sprint_id')
@click.pass_context
def roadmap_archive(ctx, sprint_id: str):
    """Archive a completed sprint"""
    from vibey.cli.commands import roadmap_archive_cmd

    exit_code = roadmap_archive_cmd(sprint_id)
    sys.exit(exit_code)
```

#### Step 4: Add Tests

Create `tests/cli/test_roadmap_archive.py`:

```python
import pytest
from pathlib import Path
from vibey.operations.roadmap.archive import archive_sprint

def test_archive_sprint_success(tmp_path):
    """Test archiving a completed sprint."""
    # Setup test roadmap
    # ... create sprint files ...

    # Archive sprint
    result = archive_sprint(tmp_path, "test-sprint-1")

    # Verify
    assert result == 0
    assert (tmp_path / ".vibey" / "archive" / "test-sprint-1.yaml").exists()

def test_archive_sprint_not_found(tmp_path):
    """Test archiving non-existent sprint."""
    result = archive_sprint(tmp_path, "nonexistent")
    assert result == 1
```

#### Step 5: Update Documentation

1. Add to `docs/reference/CLI_REFERENCE.md`:
   ```markdown
   ### `vibey roadmap archive`

   Archive a completed sprint.

   **Usage:**
   ```bash
   vibey roadmap archive SPRINT_ID
   ```

   **Examples:**
   ```bash
   vibey roadmap archive sprint-1
   ```
   ```

2. Add to `CHANGELOG.md`

---

### Adding a New MCP Tool

Follow these steps to add a new tool to the MCP server.

#### Step 1: Add Tool Definition

Edit or create a tools file (e.g., `framework/mcp/tools/archive_tools.py`):

```python
from typing import List, Dict, Any

def get_archive_tools() -> List[Dict[str, Any]]:
    """Get archive tool definitions."""
    return [
        {
            "name": "vibey_archive_sprint",
            "title": "Archive Sprint",
            "description": "Archive a completed sprint to .vibey/archive/",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sprint_id": {
                        "type": "string",
                        "description": "Sprint ID to archive"
                    }
                },
                "required": ["sprint_id"]
            }
        }
    ]
```

#### Step 2: Add Tool Handler

In the same file:

```python
async def handle_archive_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    adapter: RoadmapAdapter
) -> Dict[str, Any]:
    """Handle archive tool invocation."""

    if tool_name == "vibey_archive_sprint":
        sprint_id = arguments["sprint_id"]

        try:
            result = adapter.archive_sprint(sprint_id)

            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Sprint archived: {sprint_id}\n   Location: .vibey/archive/{sprint_id}.yaml"
                }],
                "isError": False
            }
        except Exception as e:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Error archiving sprint: {str(e)}"
                }],
                "isError": True
            }
```

#### Step 3: Add Method to Adapter

Edit `framework/mcp/adapters/roadmap_adapter.py`:

```python
class RoadmapAdapter:
    """Adapter that wraps Vibey core library for MCP."""

    def archive_sprint(self, sprint_id: str) -> Dict[str, Any]:
        """Archive a sprint."""
        from vibey.operations.roadmap.archive import archive_sprint

        result = archive_sprint(self.root_dir, sprint_id)
        if result != 0:
            raise VibeyMCPError(f"Failed to archive sprint {sprint_id}")

        return {"sprint_id": sprint_id, "status": "archived"}
```

#### Step 4: Register Tool in Server

Edit `framework/mcp/server.py`:

```python
from .tools.archive_tools import get_archive_tools, handle_archive_tool

class VibeyMCPServer:
    def get_tools(self):
        tools = []
        tools.extend(get_task_tools())
        tools.extend(get_sprint_tools())
        tools.extend(get_query_tools())
        tools.extend(get_archive_tools())  # Add this
        return tools

    async def handle_tool_call(self, tool_name, arguments):
        # Add routing
        if tool_name.startswith("vibey_archive"):
            return await handle_archive_tool(tool_name, arguments, self.adapter)
        # ... existing routing ...
```

#### Step 5: Add Tests

Create `tests/mcp/test_archive_tools.py`:

```python
import pytest
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter
from framework.mcp.tools.archive_tools import handle_archive_tool

@pytest.mark.asyncio
async def test_archive_sprint_success(test_roadmap):
    """Test archiving sprint via MCP."""
    adapter = RoadmapAdapter(str(test_roadmap))

    result = await handle_archive_tool(
        "vibey_archive_sprint",
        {"sprint_id": "test-sprint-1"},
        adapter
    )

    assert result["isError"] is False
    assert "archived" in result["content"][0]["text"].lower()
```

#### Step 6: Update Documentation

Add to `docs/guides/MCP_INTEGRATION.md`:

```markdown
### Archive Tools (1)

#### `vibey_archive_sprint`

Archive a completed sprint.

**Input:**
```json
{
  "sprint_id": "sprint-1"
}
```

**Output:**
```json
{
  "content": [{
    "type": "text",
    "text": "✅ Sprint archived: sprint-1\n   Location: .vibey/archive/sprint-1.yaml"
  }],
  "isError": false
}
```
```

---

## Testing Guidelines

### Test Organization

```
tests/
├── cli/                    # CLI command tests
│   ├── test_roadmap_cli.py
│   └── test_config_cli.py
├── operations/             # Business logic tests
│   ├── test_query.py
│   └── test_update.py
├── roadmap/                # Model tests
│   └── test_models.py
└── mcp/                    # MCP server tests
    ├── test_server.py
    └── test_tools.py
```

### Writing Tests

#### Unit Tests

Test individual functions in isolation:

```python
import pytest
from vibey.operations.roadmap.query import query_task_details

def test_query_task_details_success(tmp_path):
    """Test querying task details successfully."""
    # Setup
    setup_test_roadmap(tmp_path)

    # Execute
    result = query_task_details(tmp_path, "sprint-1-task-001")

    # Verify
    assert result["id"] == "sprint-1-task-001"
    assert result["status"] == "not_started"
    assert "description" in result

def test_query_task_details_not_found(tmp_path):
    """Test querying non-existent task."""
    setup_test_roadmap(tmp_path)

    result = query_task_details(tmp_path, "nonexistent")

    assert "error" in result
    assert "not found" in result["error"].lower()
```

#### Integration Tests

Test multiple components together:

```python
def test_complete_task_integration(tmp_path):
    """Test complete task workflow."""
    # Setup
    setup_test_roadmap(tmp_path)

    # Start task
    assert start_task(tmp_path, "sprint-1-task-001") == 0

    # Complete task
    assert complete_task(tmp_path, "sprint-1-task-001") == 0

    # Verify sprint progress updated
    sprint = load_sprint(tmp_path / ".vibey/roadmap/sprint-1/sprint.yaml")
    assert sprint.progress.tasks_completed == 1
```

#### CLI Tests

Test CLI commands end-to-end:

```python
from click.testing import CliRunner
from vibey.cli.main import cli

def test_roadmap_status_command():
    """Test roadmap status CLI command."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Initialize roadmap
        result = runner.invoke(cli, ['roadmap', 'init', '--name', 'Test', '--version', '1.0.0'])
        assert result.exit_code == 0

        # Check status
        result = runner.invoke(cli, ['roadmap', 'status'])
        assert result.exit_code == 0
        assert 'Test' in result.output
```

#### Async Tests (for MCP)

Test async MCP tools:

```python
import pytest

@pytest.mark.asyncio
async def test_mcp_start_task():
    """Test starting task via MCP."""
    adapter = RoadmapAdapter(str(test_path))

    result = await handle_task_tool(
        "vibey_start_task",
        {"task_id": "sprint-1-task-001"},
        adapter
    )

    assert result["isError"] is False
```

### Test Fixtures

Use pytest fixtures for common setup:

```python
@pytest.fixture
def test_roadmap(tmp_path):
    """Create a test roadmap."""
    # Create roadmap structure
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)

    # Create roadmap.yaml
    roadmap = Roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0"
    )
    save_roadmap(roadmap_dir / "roadmap.yaml", roadmap)

    return tmp_path

def test_with_roadmap(test_roadmap):
    """Test using the fixture."""
    result = query_roadmap_summary(test_roadmap)
    assert result["id"] == "test-roadmap"
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/cli/test_roadmap_cli.py

# Specific test
pytest tests/cli/test_roadmap_cli.py::test_roadmap_status

# With coverage
pytest --cov=vibey --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run only tests matching pattern
pytest -k "test_start"
```

### Coverage Requirements

- **Minimum:** 80% overall coverage
- **Target:** 90% overall coverage
- **Critical paths:** 100% coverage (error handling, state transitions)

Check coverage:
```bash
pytest --cov=vibey --cov-report=term-missing
# Shows lines not covered
```

---

## Documentation Requirements

### Code Documentation

Every public function/class must have:

1. **Docstring** (Google style)
2. **Type hints**
3. **Example usage** (in docstring or tests)

### User Documentation

When adding features, update:

1. **CLI Reference** (`docs/reference/CLI_REFERENCE.md`)
   - Command usage
   - Options and flags
   - Examples
   - Exit codes

2. **MCP Integration Guide** (`docs/guides/MCP_INTEGRATION.md`)
   - Tool definitions
   - Input/output schemas
   - Usage examples

3. **Getting Started** (`docs/guides/GETTING_STARTED.md`)
   - If feature affects onboarding workflow

4. **CHANGELOG.md**
   - Add entry under "Unreleased" section

### Example Documentation

For a new feature, add comprehensive examples:

```markdown
## Archive Sprint

Archive a completed sprint to preserve history.

### Usage

```bash
vibey roadmap archive sprint-1
```

### Examples

```bash
# Archive a sprint
vibey roadmap archive backend-api-1

# List archived sprints
ls .vibey/archive/

# Restore an archived sprint
vibey roadmap restore backend-api-1
```

### Output

```
✅ Sprint archived: backend-api-1
   Location: .vibey/archive/backend-api-1.yaml
   Size: 2.4 KB

To restore: vibey roadmap restore backend-api-1
```
```

---

## Git Workflow

### Branch Strategy

- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features
- **`feature/description`** - New features
- **`fix/description`** - Bug fixes
- **`docs/description`** - Documentation only

### Creating a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/archive-sprints

# Or fix branch
git checkout -b fix/task-completion-error
```

### Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code restructuring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks
- `ci:` - CI/CD changes

**Examples:**

```bash
# Feature
git commit -m "feat(cli): add archive command for sprints"

# Bug fix
git commit -m "fix(roadmap): handle missing task status field

Previously crashed when status field was missing.
Now defaults to 'not_started' with warning.

Fixes #123"

# Documentation
git commit -m "docs(mcp): add archive tool documentation"

# Breaking change
git commit -m "feat(api): change task status enum values

BREAKING CHANGE: Status values changed from 'started'
to 'in_progress'. Migrate with: vibey migrate status-enum"
```

### Keeping Branch Updated

```bash
# Update from upstream main
git fetch upstream
git rebase upstream/main

# Resolve conflicts if any
git add .
git rebase --continue

# Force push to your fork
git push --force-with-lease origin feature/archive-sprints
```

---

## Pull Request Process

### Before Submitting

1. **Run tests**
   ```bash
   pytest
   ```

2. **Check coverage**
   ```bash
   pytest --cov=vibey --cov-report=term-missing
   # Ensure added code is covered
   ```

3. **Run linters**
   ```bash
   black vibey/
   flake8 vibey/
   mypy vibey/
   ```

4. **Update documentation**
   - CLI reference
   - MCP guide (if applicable)
   - CHANGELOG.md

5. **Commit changes**
   ```bash
   git add .
   git commit -m "feat(cli): add archive command"
   ```

6. **Push to fork**
   ```bash
   git push origin feature/archive-sprints
   ```

### Creating Pull Request

1. Go to https://github.com/your-org/vibey/pulls
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in PR template:

   ```markdown
   ## Description

   Adds `vibey roadmap archive` command to archive completed sprints.

   ## Type of Change

   - [x] New feature
   - [ ] Bug fix
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing

   - [x] All tests pass
   - [x] Added new tests for archive functionality
   - [x] Coverage maintained at >90%

   ## Documentation

   - [x] CLI Reference updated
   - [x] CHANGELOG.md updated
   - [x] Examples added

   ## Checklist

   - [x] Code follows style guidelines
   - [x] Commits are well-formatted
   - [x] Branch is up-to-date with main
   - [x] No merge conflicts

   ## Screenshots (if applicable)

   ```bash
   $ vibey roadmap archive sprint-1
   ✅ Sprint archived: sprint-1
      Location: .vibey/archive/sprint-1.yaml
   ```

   ## Related Issues

   Closes #456
   ```

5. Click "Create Pull Request"

### Review Process

1. **Automated checks** run (CI/CD)
   - Tests must pass
   - Coverage must be maintained
   - Linters must pass

2. **Maintainer review**
   - Code quality
   - Architecture fit
   - Documentation completeness
   - Test coverage

3. **Address feedback**
   - Make requested changes
   - Push to same branch
   - PR updates automatically

4. **Approval and merge**
   - Once approved, maintainer merges
   - Branch is deleted automatically

---

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major (X.0.0):** Breaking changes
- **Minor (x.X.0):** New features, backward compatible
- **Patch (x.x.X):** Bug fixes, backward compatible

### Release Steps

**For Maintainers:**

1. **Update version**
   ```bash
   # Edit setup.py and vibey/cli/main.py
   VERSION = "2.6.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [2.6.0] - 2025-11-15

   ### Added
   - Archive command for sprints
   - New MCP archive tool

   ### Fixed
   - Task completion state validation

   ### Changed
   - Improved error messages
   ```

3. **Commit and tag**
   ```bash
   git add .
   git commit -m "chore: release v2.6.0"
   git tag -a v2.6.0 -m "Release version 2.6.0"
   git push origin main --tags
   ```

4. **GitHub Release**
   - Go to Releases → Draft new release
   - Select tag v2.6.0
   - Copy CHANGELOG section
   - Publish release

5. **PyPI Release** (if applicable)
   ```bash
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

---

## Code Review Guidelines

### For Contributors

- **Be responsive** - Address feedback promptly
- **Be patient** - Reviews take time
- **Ask questions** - If feedback is unclear, ask
- **Accept feedback** - Maintainers have context you may not

### For Reviewers

- **Be respectful** - Focus on code, not person
- **Be specific** - "This could be clearer" → "Extract this logic into a helper function"
- **Be constructive** - Suggest improvements, not just criticisms
- **Be timely** - Review within 2-3 business days

### Review Checklist

- [ ] Code follows style guide
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No unnecessary changes
- [ ] Performance is acceptable
- [ ] Error handling is robust
- [ ] Edge cases are handled

---

## Getting Help

### Where to Ask

- **Discord:** https://discord.gg/vibey - Real-time chat
- **GitHub Discussions:** For questions and ideas
- **GitHub Issues:** For bugs and feature requests
- **Email:** dev@vibey.dev - Private inquiries

### Common Questions

**Q: My PR was closed without merging. Why?**
A: PRs may be closed if:
- Not aligned with project goals
- Duplicate of existing PR
- No response to feedback for 30 days
- Significantly outdated

**Q: How long until my PR is reviewed?**
A: Usually 2-3 business days. Complex PRs may take longer.

**Q: Can I work on multiple features at once?**
A: Yes, but create separate branches and PRs for each.

**Q: I'm new to open source. Where should I start?**
A: Look for issues tagged `good-first-issue` or `help-wanted`.

---

## License

By contributing to Vibey, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Vibey! 🎉**

Your efforts help make project management better for everyone.

---

**Last Updated:** 2025-11-12
**Maintained By:** Vibey Framework Team
**License:** MIT
