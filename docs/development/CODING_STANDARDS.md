# Coding Standards and Conventions

This document defines the coding standards for the Vibey project. Following these standards ensures consistency and maintainability.

---

## Python Style

### Formatting

| Tool | Configuration |
|------|---------------|
| **Formatter** | Black (line length: 88) |
| **Import Sorting** | isort (Black-compatible profile) |
| **Linting** | flake8 |
| **Type Checking** | mypy |

All tools are configured in `pyproject.toml` and `.pre-commit-config.yaml`.

### Type Hints

All public functions and methods should include type hints:

```python
# Good - complete type hints
def load_track(track_id: str) -> Track:
    """Load a track by ID."""
    ...

# Good - complex types
def find_tasks(
    status: Optional[str] = None,
    track_id: Optional[str] = None,
) -> list[Task]:
    """Find tasks matching criteria."""
    ...

# Good - generic types
def process_items(items: Sequence[T]) -> list[T]:
    """Process a sequence of items."""
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
        task_id: The unique task identifier (ULID format).
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

### Module Docstrings

Every module should have a docstring explaining its purpose:

```python
"""Roadmap query operations.

This module provides functions for querying roadmap data including
tracks, sprints, and tasks. All queries support both SQLite and YAML
backends.

Classes:
    QueryResult: Container for query results with metadata.

Functions:
    query_tracks: Query tracks by status, name, or other criteria.
    query_sprints: Query sprints within a track.
    query_tasks: Query tasks within a sprint.
"""
```

---

## File Organization

### Package Structure

```
vibey/
├── __init__.py              # Package exports
├── cli/                     # User-facing CLI
│   ├── __init__.py
│   ├── main.py              # Click entry point
│   └── commands.py          # Command implementations
├── operations/              # Business logic (no UI concerns)
│   ├── __init__.py
│   ├── roadmap/             # Roadmap operations
│   │   ├── __init__.py
│   │   ├── query.py         # Read operations
│   │   ├── update.py        # Write operations
│   │   └── context.py       # Context loading
│   └── docs/                # Doc generation
│       ├── __init__.py
│       ├── cli_introspector.py
│       └── mcp_introspector.py
├── common/                  # Shared utilities
│   ├── __init__.py
│   ├── errors.py            # Error types
│   └── utils.py             # Helper functions
└── roadmap/                 # Data models
    ├── __init__.py
    ├── models/              # Dataclasses
    │   ├── common.py
    │   ├── track.py
    │   ├── sprint.py
    │   └── task.py
    └── serialization/       # YAML/SQL loaders
        ├── yaml_loader.py
        └── sql_loader.py
```

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `yaml_loader.py` |
| Classes | PascalCase | `TaskStatus`, `RoadmapError` |
| Functions | snake_case | `load_track()`, `get_status()` |
| Constants | UPPER_SNAKE | `DEFAULT_STATUS`, `MAX_RETRIES` |
| Private | _prefix | `_internal_helper()`, `_cache` |
| Type vars | Single letter or descriptive | `T`, `ItemT` |

---

## Error Handling

### Error Class Hierarchy

```python
from vibey.common.errors import (
    VibeyError,           # Base class for all Vibey errors
    ConfigError,          # Configuration issues
    RoadmapError,         # Roadmap operations
    TaskNotFoundError,    # Specific: task doesn't exist
    SprintNotFoundError,  # Specific: sprint doesn't exist
    TrackNotFoundError,   # Specific: track doesn't exist
    ValidationError,      # Input validation failures
    StorageError,         # Database/file errors
)
```

### Error Patterns

**Raise specific errors with context:**

```python
# Good - specific error with context
if not task:
    raise TaskNotFoundError(
        task_id=task_id,
        message=f"Task {task_id} not found in database",
        context={"search_path": str(db_path)},
    )

# Bad - generic error
if not task:
    raise ValueError("Task not found")
```

**Catch and re-raise with context:**

```python
try:
    result = load_yaml(path)
except YAMLError as e:
    raise ConfigError(
        message=f"Invalid YAML in {path}",
        cause=e,
    )
```

**Error messages should:**
- Be specific about what went wrong
- Include relevant IDs and paths
- Suggest remediation when possible

```python
# Good - actionable error message
raise ValidationError(
    "Invalid status 'done'. Valid values: not_started, in_progress, completed"
)

# Bad - unhelpful error message
raise ValueError("Invalid status")
```

---

## Logging

### Logger Setup

```python
import logging

logger = logging.getLogger(__name__)
```

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info (function entry/exit, variable values) |
| INFO | Normal operation events (task completed, sprint started) |
| WARNING | Unexpected but handled situations (deprecated usage, fallback behavior) |
| ERROR | Errors that prevent operation (failed to load, missing required data) |

### Logging Patterns

```python
# DEBUG - detailed diagnostic
logger.debug(f"Loading track from {path}")
logger.debug(f"Query returned {len(results)} items")

# INFO - normal operations
logger.info(f"Track {track_id} loaded with {len(sprints)} sprints")
logger.info(f"Task {task_id} completed successfully")

# WARNING - handled issues
logger.warning(f"Deprecated field 'old_field' found in {path}")
logger.warning(f"Cache miss for {key}, falling back to database")

# ERROR - failures
logger.error(f"Failed to load track: {e}")
logger.error(f"Database connection failed: {e}", exc_info=True)
```

---

## Testing Conventions

### Test File Organization

```
tests/
├── conftest.py              # Shared fixtures
├── cli/
│   ├── test_main.py
│   └── test_commands.py
├── operations/
│   └── roadmap/
│       ├── test_query.py
│       └── test_update.py
└── roadmap/
    ├── test_models.py
    └── serialization/
        └── test_yaml_loader.py
```

### Test Naming

```python
def test_load_track_returns_track_object():
    """load_track should return Track instance."""
    ...

def test_load_track_raises_when_not_found():
    """load_track should raise TaskNotFoundError for missing ID."""
    ...

def test_load_track_handles_empty_sprints():
    """load_track should return Track with empty sprints list."""
    ...
```

### Fixture Patterns

```python
@pytest.fixture
def sample_track() -> Track:
    """Create a sample track for testing."""
    return Track(
        id="01KC0000000000000000000001",
        name="Test Track",
        status="in_progress",
    )

@pytest.fixture
def temp_roadmap_dir(tmp_path) -> Path:
    """Create temporary roadmap directory structure."""
    tracks_dir = tmp_path / "tracks"
    sprints_dir = tmp_path / "sprints"
    tasks_dir = tmp_path / "tasks"

    tracks_dir.mkdir()
    sprints_dir.mkdir()
    tasks_dir.mkdir()

    return tmp_path
```

### Test Class Organization

```python
class TestLoadTrack:
    """Tests for load_track function."""

    def test_returns_track_for_valid_id(self, sample_track):
        """Should return Track for valid ID."""
        ...

    def test_raises_for_missing_id(self):
        """Should raise TrackNotFoundError for missing ID."""
        ...

    def test_loads_sprints_when_present(self, temp_roadmap_dir):
        """Should include sprints in loaded Track."""
        ...
```

---

## CLI Conventions

### Command Structure

```python
@click.command('command-name')
@click.option('--option', '-o', help='Description of option')
@click.option('--flag', is_flag=True, help='Boolean flag')
@click.argument('item_id')
@click.pass_context
def command_name(ctx, option: str, flag: bool, item_id: str):
    """Brief description of what this command does.

    Detailed description with examples if needed.

    Examples:
        vibey roadmap command-name item-123
        vibey roadmap command-name item-123 --option value
    """
    ...
```

### Output Conventions

```python
# Success messages
click.echo(f"Completed task: {task.title}")
click.echo(click.style("Success!", fg="green"))

# Error messages
click.echo(click.style(f"Error: {message}", fg="red"), err=True)

# Warnings
click.echo(click.style(f"Warning: {message}", fg="yellow"))

# Tables (for status output)
click.echo(f"{'ID':<30} {'Status':<15} {'Title'}")
click.echo("-" * 60)
for task in tasks:
    click.echo(f"{task.id:<30} {task.status:<15} {task.title}")
```

---

## Data Models

### Dataclass Patterns

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Task:
    """Represents a single task in a sprint.

    Attributes:
        id: Unique ULID identifier.
        title: Task title.
        status: Current status (not_started, in_progress, completed).
        sprint_id: Parent sprint's ULID.
        created: Creation timestamp.
        started: When task was started (None if not started).
        completed: When task was completed (None if not completed).
    """
    id: str
    title: str
    status: str
    sprint_id: str
    created: datetime
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    description: Optional[str] = None
    metadata: dict = field(default_factory=dict)
```

### Enum Usage

```python
from enum import Enum

class TaskStatus(str, Enum):
    """Valid task statuses."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

    def __str__(self) -> str:
        return self.value
```

---

## Configuration

### YAML Files

```yaml
# Use 2-space indentation
# Use snake_case for keys
# Include comments for complex sections

sprint:
  id: 01KC0000000000000000000001
  name: "Phase 1: Implementation"
  status: in_progress
  # Progress is computed, not stored
  progress:
    tasks_total: 5
    tasks_completed: 2
```

### Constants

```python
# Define in a constants module or at module level
DEFAULT_STATUS = "not_started"
VALID_STATUSES = ["not_started", "in_progress", "completed", "blocked"]
MAX_TITLE_LENGTH = 200
ULID_LENGTH = 26
```

---

## Documentation Comments

### When to Add Comments

- **Complex algorithms** - Explain the approach
- **Non-obvious decisions** - Explain why, not what
- **External dependencies** - Note API quirks
- **Performance considerations** - Explain optimizations

### Comment Patterns

```python
# Good - explains why
# Use case-insensitive comparison because task IDs from CLI
# may have different casing than stored values
if task_id.lower() == stored_id.lower():
    ...

# Bad - explains what (obvious from code)
# Check if task_id equals stored_id
if task_id == stored_id:
    ...
```

---

## Import Organization

```python
# Standard library
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

# Third-party
import click
import yaml
from sqlalchemy import select

# Local - absolute imports preferred
from vibey.common.errors import VibeyError
from vibey.roadmap.models import Task, Sprint, Track

# Relative imports only within same package
from .query import query_tasks
from .update import update_task_status
```

---

## Related Documentation

- [Development Setup](./SETUP.md)
- [ADR Index](../architecture/adr/README.md)
- [Contributor Journey](../journeys/JOURNEY_CONTRIBUTOR.md)
