# Task 002: Update Validator to Skip Excluded Paths

**Task ID:** dogfooding-bugs-06-task-002
**Bug Addressed:** #7 (Validator Doesn't Exclude context/sample_code Directories)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

After defining `VALIDATION_EXCLUDE_PATTERNS` (Task 001), the validator must be updated to actually skip files matching those patterns.

---

## Current Implementation

**File:** `vibey/operations/roadmap/optimized_validator.py`

```python
# Line 530-540
def _find_yaml_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
    """Find all YAML files to validate."""
    if patterns:
        yaml_files = []
        for pattern in patterns:
            yaml_files.extend(self.roadmap_dir.glob(pattern))
        return list(set(yaml_files))
    else:
        # Default: all YAML files in roadmap - NO FILTERING
        return list(self.roadmap_dir.rglob("*.yaml"))
```

---

## Implementation

### Update _find_yaml_files Method

```python
# vibey/operations/roadmap/optimized_validator.py

def _find_yaml_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
    """
    Find all YAML files to validate, excluding sample code and other non-roadmap files.

    Args:
        patterns: Optional list of glob patterns to validate (overrides default)

    Returns:
        List of Path objects for files to validate
    """
    if patterns:
        # Use custom patterns
        yaml_files = []
        for pattern in patterns:
            yaml_files.extend(self.roadmap_dir.glob(pattern))
        yaml_files = list(set(yaml_files))  # Remove duplicates
    else:
        # Default: all YAML files in roadmap
        yaml_files = list(self.roadmap_dir.rglob("*.yaml"))

    # Filter out excluded paths
    yaml_files = self._filter_excluded_paths(yaml_files)

    return yaml_files


def _filter_excluded_paths(self, file_paths: List[Path]) -> List[Path]:
    """
    Filter out files matching exclusion patterns.

    Args:
        file_paths: List of file paths to filter

    Returns:
        Filtered list with excluded paths removed
    """
    filtered = []

    for file_path in file_paths:
        # Get path relative to roadmap_dir for pattern matching
        try:
            rel_path = file_path.relative_to(self.roadmap_dir)
        except ValueError:
            # Not under roadmap_dir - skip filtering
            filtered.append(file_path)
            continue

        # Check against exclusion patterns
        excluded = False
        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            if self._matches_pattern(rel_path, pattern):
                excluded = True
                break

        if not excluded:
            filtered.append(file_path)

    return filtered


def _matches_pattern(self, path: Path, pattern: str) -> bool:
    """
    Check if a path matches an exclusion pattern.

    Supports glob patterns like:
    - **/context/sample_code/**
    - **/test_fixtures/**

    Args:
        path: Relative path to check
        pattern: Glob pattern to match against

    Returns:
        True if path matches pattern
    """
    # Convert path to string for pattern matching
    path_str = str(path)

    # Handle ** patterns by checking if any component matches
    if "**" in pattern:
        # Split pattern into segments
        pattern_parts = pattern.split("**")

        # For patterns like "**/context/sample_code/**"
        # Check if the key part exists in the path
        for part in pattern_parts:
            clean_part = part.strip("/")
            if clean_part and clean_part in path_str:
                # Additional check: ensure it's a path component match
                if f"/{clean_part}/" in f"/{path_str}/" or path_str.startswith(f"{clean_part}/"):
                    return True

    # Also support simple Path.match() for simpler patterns
    try:
        if path.match(pattern):
            return True
    except Exception:
        pass

    return False
```

### Alternative: Use fnmatch for Pattern Matching

```python
import fnmatch

def _filter_excluded_paths(self, file_paths: List[Path]) -> List[Path]:
    """Filter out files matching exclusion patterns using fnmatch."""
    filtered = []

    for file_path in file_paths:
        try:
            rel_path_str = str(file_path.relative_to(self.roadmap_dir))
        except ValueError:
            filtered.append(file_path)
            continue

        excluded = False
        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            # fnmatch handles ** patterns well
            if fnmatch.fnmatch(rel_path_str, pattern):
                excluded = True
                break
            # Also check with forward slashes normalized
            if fnmatch.fnmatch(rel_path_str.replace("\\", "/"), pattern):
                excluded = True
                break

        if not excluded:
            filtered.append(file_path)

    return filtered
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/optimized_validator.py` | Update `_find_yaml_files`, add `_filter_excluded_paths` |

---

## Testing Strategy

```python
from pathlib import Path
import tempfile
import os


def test_validator_excludes_sample_code(tmp_path):
    """Validator skips context/sample_code directories."""
    # Create directory structure
    roadmap_dir = tmp_path / ".vibey" / "roadmap"

    # Create valid roadmap file
    tracks_dir = roadmap_dir / "tracks"
    tracks_dir.mkdir(parents=True)
    (tracks_dir / "track_123.yaml").write_text("track:\n  id: track_123\n  name: Test\n  status: not_started")

    # Create sample code file (should be excluded)
    sample_dir = roadmap_dir / "some-track" / "context" / "sample_code" / "yaml"
    sample_dir.mkdir(parents=True)
    (sample_dir / "invalid.yaml").write_text("not valid yaml structure")

    # Run validator
    from vibey.operations.roadmap.optimized_validator import OptimizedValidator, ValidationProfile

    os.chdir(tmp_path)
    validator = OptimizedValidator(tmp_path, ValidationProfile.STANDARD)
    report = validator.validate()

    # Should only validate the track file, not the sample code
    assert report.total_files == 1
    assert report.invalid_files == 0


def test_filter_excluded_paths():
    """_filter_excluded_paths filters correctly."""
    from vibey.operations.roadmap.optimized_validator import OptimizedValidator, ValidationProfile

    validator = OptimizedValidator(Path("/fake"), ValidationProfile.STANDARD)
    validator.roadmap_dir = Path("/fake/.vibey/roadmap")

    # Create test paths
    paths = [
        Path("/fake/.vibey/roadmap/tracks/track_123.yaml"),
        Path("/fake/.vibey/roadmap/sprints/sprint_456.yaml"),
        Path("/fake/.vibey/roadmap/old-track/context/sample_code/yaml/test.yaml"),
        Path("/fake/.vibey/roadmap/test_fixtures/fixture.yaml"),
    ]

    # Filter
    filtered = validator._filter_excluded_paths(paths)

    # Only first two should remain
    assert len(filtered) == 2
    assert paths[0] in filtered
    assert paths[1] in filtered
    assert paths[2] not in filtered
    assert paths[3] not in filtered


def test_validator_still_validates_real_files(tmp_path):
    """Validator still validates real roadmap files."""
    # Create structure
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    (roadmap_dir / "tracks").mkdir(parents=True)
    (roadmap_dir / "sprints").mkdir()
    (roadmap_dir / "tasks").mkdir()

    # Create valid files
    (roadmap_dir / "tracks" / "track_123.yaml").write_text(
        "track:\n  id: track_123\n  name: Test Track\n  status: not_started"
    )
    (roadmap_dir / "sprints" / "sprint_456.yaml").write_text(
        "sprint:\n  id: sprint_456\n  track_id: track_123\n  name: Sprint 1\n  status: not_started"
    )

    # Create invalid sample code (should be excluded)
    sample_dir = roadmap_dir / "context" / "sample_code"
    sample_dir.mkdir(parents=True)
    (sample_dir / "bad.yaml").write_text("this is not valid")

    # Validate
    from vibey.operations.roadmap.optimized_validator import OptimizedValidator, ValidationProfile
    import os

    os.chdir(tmp_path)
    validator = OptimizedValidator(tmp_path, ValidationProfile.STANDARD)
    report = validator.validate()

    # Should validate 2 files, both valid
    assert report.total_files == 2
    assert report.valid_files == 2
    assert report.invalid_files == 0
```

---

## Success Criteria

- [ ] `_find_yaml_files()` calls `_filter_excluded_paths()`
- [ ] `_filter_excluded_paths()` filters based on `VALIDATION_EXCLUDE_PATTERNS`
- [ ] Sample code files are NOT validated
- [ ] Real roadmap files ARE still validated
- [ ] No regression in validation performance (<10% overhead)

---

## Dependencies

- Task 001 (VALIDATION_EXCLUDE_PATTERNS constant defined)

---

## Notes

The pattern matching needs to handle:
1. Files deep in nested directories (`**/context/sample_code/**`)
2. Cross-platform path separators (`/` vs `\`)
3. Both relative and absolute paths

Using `fnmatch` is simpler and more reliable than manual pattern parsing.
