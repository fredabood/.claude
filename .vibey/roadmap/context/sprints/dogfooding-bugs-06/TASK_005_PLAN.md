# Task 005: Add Startup Check to Warn if Duplicate Exists

**Task ID:** dogfooding-bugs-06-task-005
**Bug Addressed:** #14 (Duplicate roadmap.yaml Files Existed at Two Locations)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

Even though Bug #14 is fixed, we should add a startup check to warn users if a duplicate `roadmap.yaml` file appears at the old location. This provides:

1. Early detection of configuration issues
2. Clear guidance on the correct location
3. Prevention of data integrity problems

---

## Implementation

### Add Duplicate Detection Function

```python
# vibey/cli/roadmap_lib/filesystem.py

def check_for_duplicate_roadmap(self) -> Optional[str]:
    """
    Check if a duplicate roadmap.yaml exists at the old location.

    The canonical location is: .vibey/roadmap/roadmap.yaml
    The old location was: .vibey/roadmap.yaml

    Returns:
        Warning message if duplicate exists, None otherwise
    """
    old_location = self.vibey_dir / "roadmap.yaml"
    new_location = self.roadmap_root / "roadmap.yaml"

    if old_location.exists() and new_location.exists():
        return (
            f"⚠️  WARNING: Duplicate roadmap.yaml files detected!\n"
            f"   Old location (deprecated): {old_location}\n"
            f"   Current location: {new_location}\n"
            f"\n"
            f"   Please delete the old file: rm {old_location}\n"
            f"   The canonical location is: {new_location}"
        )

    if old_location.exists() and not new_location.exists():
        return (
            f"⚠️  WARNING: roadmap.yaml at deprecated location!\n"
            f"   Found at: {old_location}\n"
            f"   Should be at: {new_location}\n"
            f"\n"
            f"   Please move the file: mv {old_location} {new_location}"
        )

    return None
```

### Add Startup Check to CLI

```python
# vibey/cli/commands.py (or appropriate location)

def _check_roadmap_location_warning(root_dir: Path = None):
    """
    Check for duplicate roadmap.yaml and print warning if found.

    Called at CLI startup for roadmap commands.
    """
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    root = root_dir or Path.cwd()

    try:
        fs = FileSystemManager(root)
        warning = fs.check_for_duplicate_roadmap()

        if warning:
            import click
            click.echo(warning, err=True)
            click.echo("", err=True)  # Blank line for readability

    except Exception:
        # Don't fail startup due to check errors
        pass


# Call from roadmap command group entry point
# vibey/cli/main.py

@cli.group()
@click.option(
    '--backend', '-b',
    type=click.Choice(['auto', 'sqlite', 'yaml'], case_sensitive=False),
    default=None,
    help='Storage backend: auto (default), sqlite, or yaml'
)
@click.pass_context
def roadmap(ctx, backend: Optional[str]):
    """Manage roadmap system..."""
    ctx.ensure_object(dict)
    ctx.obj['BACKEND'] = backend

    # Add startup check
    _check_roadmap_location_warning()
```

### Alternative: Add to FileSystemManager __init__

```python
# vibey/cli/roadmap_lib/filesystem.py

class FileSystemManager:
    """Manages file system operations for roadmap."""

    def __init__(self, root_dir: Path, warn_on_duplicate: bool = True):
        """
        Initialize FileSystemManager.

        Args:
            root_dir: Repository root directory
            warn_on_duplicate: If True, warn about duplicate roadmap.yaml
        """
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.roadmap_root = self.vibey_dir / "roadmap"

        # ... existing initialization ...

        # Check for duplicate roadmap.yaml
        if warn_on_duplicate:
            warning = self.check_for_duplicate_roadmap()
            if warning:
                import sys
                print(warning, file=sys.stderr)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/roadmap_lib/filesystem.py` | Add `check_for_duplicate_roadmap()` method |
| `vibey/cli/main.py` or `vibey/cli/commands.py` | Add startup check call |

---

## Testing Strategy

```python
# tests/cli/test_duplicate_roadmap_warning.py

import pytest
from pathlib import Path
import tempfile
import os


class TestDuplicateRoadmapWarning:
    """Tests for duplicate roadmap.yaml detection."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temp project structure."""
        vibey_dir = tmp_path / ".vibey"
        roadmap_dir = vibey_dir / "roadmap"
        roadmap_dir.mkdir(parents=True)
        return tmp_path

    def test_no_warning_when_only_new_location(self, temp_project):
        """No warning when only new location exists."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        # Create only at new location
        (temp_project / ".vibey" / "roadmap" / "roadmap.yaml").write_text("roadmap: {}")

        fs = FileSystemManager(temp_project)
        warning = fs.check_for_duplicate_roadmap()

        assert warning is None

    def test_warning_when_both_locations_exist(self, temp_project):
        """Warning when both old and new locations exist."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        # Create at both locations
        (temp_project / ".vibey" / "roadmap.yaml").write_text("roadmap: {}")
        (temp_project / ".vibey" / "roadmap" / "roadmap.yaml").write_text("roadmap: {}")

        fs = FileSystemManager(temp_project)
        warning = fs.check_for_duplicate_roadmap()

        assert warning is not None
        assert "Duplicate" in warning or "duplicate" in warning
        assert "deprecated" in warning.lower()

    def test_warning_when_only_old_location(self, temp_project):
        """Warning when only old location exists."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        # Create only at old location
        (temp_project / ".vibey" / "roadmap.yaml").write_text("roadmap: {}")

        fs = FileSystemManager(temp_project)
        warning = fs.check_for_duplicate_roadmap()

        assert warning is not None
        assert "deprecated" in warning.lower()
        assert "move" in warning.lower() or "mv" in warning

    def test_no_warning_when_neither_exists(self, temp_project):
        """No warning when no roadmap.yaml exists (new project)."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager(temp_project)
        warning = fs.check_for_duplicate_roadmap()

        assert warning is None

    def test_warning_includes_fix_command(self, temp_project):
        """Warning includes command to fix the issue."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        (temp_project / ".vibey" / "roadmap.yaml").write_text("roadmap: {}")
        (temp_project / ".vibey" / "roadmap" / "roadmap.yaml").write_text("roadmap: {}")

        fs = FileSystemManager(temp_project)
        warning = fs.check_for_duplicate_roadmap()

        assert "rm " in warning or "delete" in warning.lower()
```

---

## Success Criteria

- [ ] `check_for_duplicate_roadmap()` method implemented
- [ ] Warning shown when duplicate exists at old location
- [ ] Warning shown when file only at old location
- [ ] No warning for correct configuration
- [ ] Warning includes actionable fix instructions
- [ ] Warning printed to stderr (not stdout)
- [ ] Check doesn't crash CLI on errors

---

## Dependencies

- Task 004 (verification tests)

---

## Notes

The warning should be:
1. **Non-blocking** - Don't prevent CLI from running
2. **Clear** - Explain the problem and solution
3. **Actionable** - Include the exact command to fix
4. **Visible** - Print to stderr so it shows even with redirects

Example output:
```
⚠️  WARNING: Duplicate roadmap.yaml files detected!
   Old location (deprecated): /path/to/.vibey/roadmap.yaml
   Current location: /path/to/.vibey/roadmap/roadmap.yaml

   Please delete the old file: rm /path/to/.vibey/roadmap.yaml
   The canonical location is: /path/to/.vibey/roadmap/roadmap.yaml
```
