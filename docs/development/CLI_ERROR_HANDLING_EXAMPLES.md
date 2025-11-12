# CLI Error Handling Examples

**Date:** 2025-11-12
**Sprint:** interface-unification-2
**Purpose:** Show how to use unified error handling in CLI scripts

---

## Overview

The Vibey CLI now uses a unified error handling system that provides:
- Rich error context (codes, suggestions, hints, fix commands)
- Consistent formatting across all commands
- Platform-agnostic error definitions
- Easy testing and debugging

---

## Quick Start

### 1. Import Error Helpers

```python
from vibey.cli.roadmap_errors import (
    raise_roadmap_not_found,
    raise_track_not_found,
    raise_sprint_not_found,
    raise_task_not_found,
    render_cli_error,
)
from vibey.common import VibeyError
```

### 2. Raise Errors When Problems Occur

```python
def load_roadmap(directory: str):
    """Load roadmap from directory."""
    roadmap_file = Path(directory) / "roadmap.yaml"

    if not roadmap_file.exists():
        raise_roadmap_not_found(directory)

    # ... load roadmap
```

### 3. Catch and Render at Entry Point

```python
def main():
    try:
        roadmap = load_roadmap("/path/to/project")
        # ... do work
    except VibeyError as e:
        print(render_cli_error(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Migration Pattern

### String-Based to Exception-Based

**Before (Old Style):**
```python
from vibey.cli.roadmap_lib.error_messages import ErrorMessages

def find_track(track_id: str, available_tracks: List[str]):
    if track_id not in available_tracks:
        print(ErrorMessages.track_not_found(track_id, available_tracks))
        sys.exit(1)
    # ... continue
```

**After (New Style):**
```python
from vibey.cli.roadmap_errors import raise_track_not_found, render_cli_error
from vibey.common import VibeyError

def find_track(track_id: str, available_tracks: List[str]):
    """Find track by ID."""
    if track_id not in available_tracks:
        raise_track_not_found(track_id, available_tracks)
    # ... continue

# At entry point:
def main():
    try:
        track = find_track("backend-api", ["frontend", "infra"])
    except VibeyError as e:
        print(render_cli_error(e))
        sys.exit(1)
```

**Benefits:**
- ✅ Errors are catchable (not just printed)
- ✅ Error context available programmatically
- ✅ Testable (can assert specific error types)
- ✅ Consistent formatting
- ✅ Works across CLI, MCP, and API

---

## Complete Examples

### Example 1: Simple Command Script

```python
#!/usr/bin/env python3
"""
roadmap-show.py - Show roadmap status
"""

import sys
from pathlib import Path
from typing import Optional

from vibey.cli.roadmap_errors import (
    raise_roadmap_not_found,
    raise_track_not_found,
    render_cli_error,
)
from vibey.common import VibeyError


def load_roadmap(directory: Path):
    """Load roadmap from directory."""
    roadmap_file = directory / ".vibey" / "roadmap.yaml"

    if not roadmap_file.exists():
        raise_roadmap_not_found(str(directory))

    # ... load and return roadmap


def get_track(roadmap, track_id: str):
    """Get track from roadmap."""
    available_tracks = [t.id for t in roadmap.tracks]

    if track_id not in available_tracks:
        raise_track_not_found(track_id, available_tracks)

    return roadmap.get_track(track_id)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Show roadmap status")
    parser.add_argument("--track", help="Show specific track")
    parser.add_argument("--dir", default=".", help="Roadmap directory")
    args = parser.parse_args()

    try:
        # Load roadmap
        roadmap = load_roadmap(Path(args.dir))

        # Get track if specified
        if args.track:
            track = get_track(roadmap, args.track)
            print(f"Track: {track.name}")
            # ... display track info
        else:
            print(f"Roadmap: {roadmap.name}")
            # ... display roadmap info

    except VibeyError as e:
        # Unified error handling
        print(render_cli_error(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Example 2: With Validation

```python
#!/usr/bin/env python3
"""
roadmap-validate.py - Validate roadmap structure
"""

import sys
from pathlib import Path
from typing import List

from vibey.cli.roadmap_errors import (
    raise_roadmap_not_found,
    raise_validation_failed,
    render_cli_error,
)
from vibey.common import VibeyError


def validate_roadmap(roadmap_dir: Path) -> List[str]:
    """
    Validate roadmap structure.

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check roadmap.yaml exists
    if not (roadmap_dir / "roadmap.yaml").exists():
        raise_roadmap_not_found(str(roadmap_dir))

    # Validate structure
    if not (roadmap_dir / "tracks").is_dir():
        errors.append("Missing tracks/ directory")

    if not (roadmap_dir / "sprints").is_dir():
        errors.append("Missing sprints/ directory")

    # ... more validation

    return errors


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate roadmap")
    parser.add_argument("--dir", default=".vibey/roadmap", help="Roadmap directory")
    args = parser.parse_args()

    try:
        roadmap_dir = Path(args.dir)
        errors = validate_roadmap(roadmap_dir)

        if errors:
            # Raise validation error with all issues
            raise_validation_failed(
                object_type="roadmap",
                object_id=str(roadmap_dir),
                errors=errors
            )

        print("✅ Roadmap validation passed")
        sys.exit(0)

    except VibeyError as e:
        print(render_cli_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Example 3: With Dependency Checking

```python
#!/usr/bin/env python3
"""
roadmap-start.py - Start a sprint
"""

import sys
from pathlib import Path

from vibey.cli.roadmap_errors import (
    raise_sprint_not_found,
    raise_dependency_blocked,
    raise_invalid_status_transition,
    render_cli_error,
)
from vibey.common import VibeyError


def check_dependencies(sprint):
    """Check if sprint dependencies are satisfied."""
    for dep in sprint.dependencies:
        blocker = get_dependency(dep.blocker_id)

        if blocker.status != dep.required_status:
            raise_dependency_blocked(
                object_id=sprint.id,
                object_type="sprint",
                blocker_id=blocker.id,
                blocker_type="sprint",
                required_status=dep.required_status,
                current_status=blocker.status,
            )


def start_sprint(sprint_id: str):
    """Start a sprint."""
    sprint = get_sprint(sprint_id)

    if not sprint:
        raise_sprint_not_found(sprint_id)

    # Check current status
    if sprint.status != "not_started":
        raise_invalid_status_transition(
            object_id=sprint_id,
            current_status=sprint.status,
            attempted_status="in_progress",
            valid_transitions=["not_started"],
        )

    # Check dependencies
    check_dependencies(sprint)

    # Start sprint
    sprint.status = "in_progress"
    sprint.save()

    print(f"✅ Started sprint: {sprint.name}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Start a sprint")
    parser.add_argument("sprint_id", help="Sprint ID to start")
    args = parser.parse_args()

    try:
        start_sprint(args.sprint_id)
    except VibeyError as e:
        print(render_cli_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Testing Error Handling

### Test 1: Assert Specific Error Type

```python
import pytest
from vibey.common import TrackNotFoundError
from vibey.cli.roadmap_errors import raise_track_not_found


def test_track_not_found():
    """Test TrackNotFoundError is raised correctly."""
    with pytest.raises(TrackNotFoundError) as exc_info:
        raise_track_not_found("backend", ["frontend", "infra"])

    error = exc_info.value
    assert error.context.code == "TRACK_NOT_FOUND"
    assert "backend" in error.context.message
    assert "frontend" in error.context.metadata["available_tracks"]
```

### Test 2: Test Error Rendering

```python
from vibey.cli.roadmap_errors import raise_roadmap_not_found, render_cli_error
from vibey.common import RoadmapNotFoundError


def test_roadmap_error_rendering():
    """Test error renders correctly for CLI."""
    try:
        raise_roadmap_not_found("/test/path")
    except RoadmapNotFoundError as e:
        output = render_cli_error(e)

        assert "ROADMAP_NOT_FOUND" in output
        assert "/test/path" in output
        assert "vibey roadmap init" in output
        assert "Suggestions:" in output
```

### Test 3: Test Command with Error

```python
from unittest.mock import patch
from vibey.common import VibeyError


def test_command_handles_error(capsys):
    """Test command handles VibeyError correctly."""
    with patch('your_module.load_roadmap', side_effect=RoadmapNotFoundError("/path")):
        with pytest.raises(SystemExit) as exc_info:
            main()  # Your command's main() function

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "ROADMAP_NOT_FOUND" in captured.out
        assert "/path" in captured.out
```

---

## Error Rendering Options

### 1. CLI with Colors (Default)

```python
from vibey.cli.roadmap_errors import render_cli_error
from vibey.common.renderers import CLIErrorRenderer

# With colors (default)
renderer = CLIErrorRenderer(use_colors=True)
print(renderer.render(error))
```

### 2. Plain Text (No Colors)

```python
from vibey.common.renderers import PlainTextRenderer

# For logs, CI/CD, or environments without color support
renderer = PlainTextRenderer()
print(renderer.render(error))
```

### 3. Logging Format

```python
import logging
from vibey.common.renderers import LogErrorRenderer

renderer = LogErrorRenderer()
log_entry = renderer.render(error)
logging.error(log_entry["message"], extra=log_entry)
```

---

## Common Patterns

### Pattern: Try-Except at Entry Point

```python
def main():
    try:
        # Main logic here
        result = do_work()
        print(result)
        sys.exit(0)
    except VibeyError as e:
        # Handle all Vibey errors
        print(render_cli_error(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        # Unexpected errors
        print(f"Unexpected error: {e}")
        sys.exit(1)
```

### Pattern: Catch Specific Error Types

```python
from vibey.common import (
    RoadmapNotFoundError,
    TrackNotFoundError,
    DependencyBlockedError,
)

try:
    track = get_track(track_id)
except RoadmapNotFoundError as e:
    print(render_cli_error(e))
    print("\nHint: Run 'vibey roadmap init' first")
    sys.exit(1)
except TrackNotFoundError as e:
    print(render_cli_error(e))
    # Maybe offer to create the track?
    sys.exit(1)
except DependencyBlockedError as e:
    print(render_cli_error(e))
    # Maybe show dependency graph?
    sys.exit(1)
```

### Pattern: Collect Multiple Errors

```python
from typing import List
from vibey.common import VibeyError, ValidationError
from vibey.cli.roadmap_errors import render_cli_errors

def validate_all_sprints(sprints) -> List[VibeyError]:
    """Validate multiple sprints, collecting all errors."""
    errors = []

    for sprint in sprints:
        try:
            validate_sprint(sprint)
        except VibeyError as e:
            errors.append(e)

    return errors

# Usage
errors = validate_all_sprints(sprints)
if errors:
    print(render_cli_errors(errors))
    sys.exit(1)
```

---

## Migration Checklist

When migrating a CLI script to unified error handling:

- [ ] Import error helpers from `vibey.cli.roadmap_errors`
- [ ] Replace `print(ErrorMessages.*)` with `raise_*()`
- [ ] Add `try/except VibeyError` at entry point
- [ ] Use `render_cli_error()` to format errors
- [ ] Update tests to assert specific error types
- [ ] Remove old `error_messages.py` imports (if fully migrated)
- [ ] Test error output in terminal
- [ ] Verify suggestions and fix commands are helpful

---

## Benefits Summary

**For Users:**
- ✅ Consistent, helpful error messages
- ✅ Clear suggestions for fixing issues
- ✅ Quick fix commands when available
- ✅ Links to relevant documentation

**For Developers:**
- ✅ Type-safe error handling
- ✅ Testable error behavior
- ✅ Rich error context for debugging
- ✅ Platform-agnostic (works in CLI, MCP, API)
- ✅ Easy to add new error types

---

**Document Version:** 1.0
**Created:** 2025-11-12
**Sprint:** interface-unification-2
**Related:** UNIFIED_ERROR_HANDLING.md
