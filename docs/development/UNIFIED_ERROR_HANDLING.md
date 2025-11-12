# Unified Error Handling System

**Created:** 2025-11-12
**Sprint:** interface-unification-2
**Status:** Implemented

---

## Overview

Vibey now has a unified error handling system that works across all interfaces:
- **CLI** (text-based terminal output)
- **MCP Server** (JSON-based protocol responses)
- **Direct Python API** (programmatic error handling)

This system provides:
- Consistent error definitions
- Rich error context (codes, suggestions, fix commands)
- Platform-specific rendering
- Easy extensibility

---

## Architecture

```
vibey/common/
├── errors.py       # Error definitions
├── renderers.py    # Platform-specific renderers
└── __init__.py     # Module exports
```

### Key Components

1. **VibeyError (base class)** - All errors inherit from this
2. **ErrorContext** - Rich metadata for errors
3. **ErrorRenderer** - Abstract base for platform renderers
4. **Platform Renderers**:
   - `CLIErrorRenderer` - Terminal output with ANSI colors
   - `MCPErrorRenderer` - JSON for MCP protocol
   - `PlainTextRenderer` - Plain text (logs, CI/CD)
   - `LogErrorRenderer` - Structured logging

---

## Error Categories

Errors are organized into logical categories:

| Category | Purpose | Examples |
|----------|---------|----------|
| `CONFIGURATION` | Config loading/validation | ConfigNotFoundError, ConfigValidationError |
| `ROADMAP` | Roadmap operations | RoadmapNotFoundError, TrackNotFoundError |
| `VALIDATION` | Data validation | ValidationError |
| `DEPENDENCY` | Dependency management | DependencyBlockedError, CircularDependencyError |
| `FILE_SYSTEM` | File operations | FileNotFoundError |
| `STATE` | State transitions | InvalidStateTransitionError, QualityGateNotPassedError |
| `CONCURRENCY` | Concurrent modifications | ConcurrentModificationError |

---

## Usage Examples

### 1. Raising Errors

```python
from vibey.common import RoadmapNotFoundError

def load_roadmap(directory: str):
    if not roadmap_exists(directory):
        raise RoadmapNotFoundError(searched_dir=directory)
    # ... load roadmap
```

### 2. Handling Errors (CLI)

```python
from vibey.common import RoadmapNotFoundError
from vibey.common.renderers import CLIErrorRenderer

try:
    roadmap = load_roadmap("/path/to/project")
except RoadmapNotFoundError as e:
    renderer = CLIErrorRenderer()
    print(renderer.render(e))
    sys.exit(1)
```

**Output:**
```
❌ ERROR Roadmap not found in /path/to/project

[ROADMAP_NOT_FOUND] (roadmap)

Suggestions:
  • Initialize roadmap: vibey roadmap init
  • Check you're in the correct directory
  • Verify .vibey/roadmap/ directory exists

💡 Roadmap systems require initialization

Quick fix:
  vibey roadmap init
```

### 3. Handling Errors (MCP)

```python
from vibey.common import TrackNotFoundError
from vibey.common.renderers import MCPErrorRenderer

try:
    track = get_track("backend-api")
except TrackNotFoundError as e:
    renderer = MCPErrorRenderer()
    return renderer.to_json(e)
```

**Output:**
```json
{
  "error": {
    "code": "TRACK_NOT_FOUND",
    "message": "Track 'backend-api' not found",
    "severity": "error",
    "category": "roadmap"
  },
  "details": {
    "suggestions": [
      "List all tracks: vibey roadmap list-tracks",
      "Check track ID spelling (case-sensitive, kebab-case)"
    ],
    "hint": "Track IDs use kebab-case (lowercase-with-hyphens)",
    "fix_command": null,
    "related_docs": null
  },
  "metadata": {
    "track_id": "backend-api",
    "available_tracks": null
  }
}
```

### 4. Multiple Errors

```python
from vibey.common import ValidationError
from vibey.common.renderers import CLIErrorRenderer

errors = [
    ValidationError("sprint", "backend-1", ["Missing name field", "Invalid date"]),
    ValidationError("task", "backend-1-task-001", ["Missing title"]),
]

renderer = CLIErrorRenderer()
print(renderer.render_multiple(errors))
```

### 5. Custom Error Context

```python
from vibey.common.errors import VibeyError, ErrorCategory, ErrorSeverity

class CustomError(VibeyError):
    def __init__(self, detail: str):
        super().__init__(
            message=f"Custom operation failed: {detail}",
            code="CUSTOM_ERROR",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check the documentation",
                "Contact support",
            ],
            hint="This is a custom error example",
            fix_command="vibey custom-fix",
            related_docs="docs/custom.md",
            metadata={"detail": detail},
        )
```

---

## Migrating Existing Code

### Before (Old Error Handling)

```python
# roadmap_lib/error_messages.py
def roadmap_not_found(searched_dir: str) -> str:
    return CLIHelpFormatter.format_error_with_suggestion(
        error=f"Roadmap not found in {searched_dir}",
        suggestions=[...],
        hint="..."
    )

# In CLI code
if not roadmap_exists(dir):
    print(ErrorMessages.roadmap_not_found(dir))
    sys.exit(1)
```

### After (Unified Error Handling)

```python
# Raise structured exception
from vibey.common import RoadmapNotFoundError

if not roadmap_exists(dir):
    raise RoadmapNotFoundError(searched_dir=dir)

# Handle with renderer
from vibey.common.renderers import CLIErrorRenderer

try:
    load_roadmap(dir)
except RoadmapNotFoundError as e:
    renderer = CLIErrorRenderer()
    print(renderer.render(e))
    sys.exit(1)
```

**Benefits:**
- ✅ Exceptions are catchable (not just strings)
- ✅ Rich metadata available programmatically
- ✅ Works across CLI, MCP, and API
- ✅ Type-safe error handling
- ✅ Testable

---

## Standard Error Types

### Configuration Errors

```python
from vibey.common import ConfigNotFoundError, ConfigValidationError

# Config not found
raise ConfigNotFoundError(searched_paths=[
    ".vibey/config/",
    ".claude/project-config.yaml",
])

# Validation failed
raise ConfigValidationError(
    validation_errors=["Missing project name", "Invalid tech stack"],
    config_file=".vibey/config/project.yaml",
)
```

### Roadmap Errors

```python
from vibey.common import (
    RoadmapNotFoundError,
    TrackNotFoundError,
    SprintNotFoundError,
    TaskNotFoundError,
)

raise RoadmapNotFoundError(searched_dir="/path/to/project")
raise TrackNotFoundError("backend-api", available_tracks=["frontend", "infra"])
raise SprintNotFoundError("backend-1", track_id="backend-api")
raise TaskNotFoundError("backend-1-task-001", sprint_id="backend-1")
```

### Dependency Errors

```python
from vibey.common import DependencyBlockedError, CircularDependencyError

# Blocked by dependency
raise DependencyBlockedError(
    object_id="backend-2",
    object_type="sprint",
    blocker_id="backend-1",
    blocker_type="sprint",
    required_status="completed",
    current_status="in_progress",
)

# Circular dependency
raise CircularDependencyError(
    dependency_chain=["backend-1", "frontend-1", "backend-2", "backend-1"]
)
```

### State Errors

```python
from vibey.common import InvalidStateTransitionError, QualityGateNotPassedError

# Invalid transition
raise InvalidStateTransitionError(
    object_id="backend-1",
    current_status="not_started",
    attempted_status="completed",
    valid_transitions=["in_progress"],
)

# Quality gate not passed
raise QualityGateNotPassedError(
    object_id="backend-1",
    gate_type="completion",
    incomplete_gates=["Security Audit", "Code Review"],
)
```

---

## Error Context Fields

Every error has rich context:

```python
error.context.code              # "ROADMAP_NOT_FOUND"
error.context.message           # "Roadmap not found in..."
error.context.category          # ErrorCategory.ROADMAP
error.context.severity          # ErrorSeverity.ERROR
error.context.suggestions       # ["Initialize roadmap", ...]
error.context.hint              # "Roadmap systems require..."
error.context.fix_command       # "vibey roadmap init"
error.context.related_docs      # "docs/..."
error.context.metadata          # {"searched_dir": "..."}
```

---

## Testing Errors

```python
import pytest
from vibey.common import RoadmapNotFoundError

def test_roadmap_not_found_error():
    with pytest.raises(RoadmapNotFoundError) as exc_info:
        raise RoadmapNotFoundError(searched_dir="/test")

    error = exc_info.value
    assert error.context.code == "ROADMAP_NOT_FOUND"
    assert error.context.category == ErrorCategory.ROADMAP
    assert "/test" in error.context.message
    assert len(error.context.suggestions) > 0

def test_error_rendering():
    from vibey.common.renderers import CLIErrorRenderer

    error = RoadmapNotFoundError(searched_dir="/test")
    renderer = CLIErrorRenderer(use_colors=False)
    output = renderer.render(error)

    assert "ROADMAP_NOT_FOUND" in output
    assert "Suggestions:" in output
    assert "vibey roadmap init" in output
```

---

## Adding New Error Types

1. **Define error class** in `vibey/common/errors.py`:

```python
class MyCustomError(VibeyError):
    """Custom error for specific use case."""

    def __init__(self, param1: str, param2: int):
        super().__init__(
            message=f"Custom error: {param1} ({param2})",
            code="MY_CUSTOM_ERROR",
            category=ErrorCategory.UNKNOWN,  # or create new category
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Suggestion 1",
                "Suggestion 2",
            ],
            hint="Helpful hint for users",
            fix_command="vibey fix-command",
            related_docs="docs/custom.md",
            metadata={"param1": param1, "param2": param2},
        )
```

2. **Export in `__init__.py`**:

```python
from vibey.common.errors import MyCustomError

__all__ = [
    # ... existing exports
    "MyCustomError",
]
```

3. **Use in your code**:

```python
from vibey.common import MyCustomError

raise MyCustomError(param1="value", param2=42)
```

---

## Best Practices

### 1. Use Specific Error Types

❌ **Bad:**
```python
raise Exception("Track not found")
```

✅ **Good:**
```python
from vibey.common import TrackNotFoundError
raise TrackNotFoundError("backend-api")
```

### 2. Provide Context

❌ **Bad:**
```python
raise RoadmapNotFoundError("")
```

✅ **Good:**
```python
raise RoadmapNotFoundError(searched_dir=project_root)
```

### 3. Catch Specific Errors

❌ **Bad:**
```python
try:
    load_roadmap()
except Exception:
    pass
```

✅ **Good:**
```python
try:
    load_roadmap()
except RoadmapNotFoundError as e:
    renderer.render(e)
    sys.exit(1)
except ValidationError as e:
    log.error(f"Validation failed: {e}")
    raise
```

### 4. Use Appropriate Renderer

```python
# CLI output
renderer = CLIErrorRenderer()

# MCP protocol
renderer = MCPErrorRenderer()

# Log files
renderer = PlainTextRenderer()

# Structured logs
renderer = LogErrorRenderer()
```

---

## Migration Checklist

- [ ] Replace string-based errors with VibeyError subclasses
- [ ] Add error context (suggestions, hints, fix commands)
- [ ] Use appropriate renderer for output
- [ ] Update tests to catch specific error types
- [ ] Document new error codes
- [ ] Update user-facing documentation

---

## Related Files

- `vibey/common/errors.py` - Error definitions
- `vibey/common/renderers.py` - Platform renderers
- `vibey/common/__init__.py` - Module exports
- `vibey/config/loader.py` - Example migration (ConfigLoadError)
- `vibey/roadmap/validation/validator.py` - Example migration (ValidationError)

---

## Next Steps (Sprint 2)

1. ✅ Create unified error library
2. ✅ Create platform renderers
3. ⏳ Migrate `config/loader.py` to use unified errors
4. ⏳ Migrate `roadmap_lib/error_messages.py` to use unified errors
5. ⏳ Update CLI commands to use unified errors
6. ⏳ Add integration tests

---

**Document Version:** 1.0
**Created:** 2025-11-12
**Sprint:** interface-unification-2
**Status:** Implementation complete, migration in progress
