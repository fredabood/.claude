# Task 001: Add VALIDATION_EXCLUDE_PATTERNS Constant

**Task ID:** dogfooding-bugs-06-task-001
**Bug Addressed:** #7 (Validator Doesn't Exclude context/sample_code Directories)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The `validate-fast` command validates ALL YAML files in the roadmap directory, including sample code snippets in `context/sample_code/` directories that are NOT valid roadmap objects. This causes false positives.

**Example Error:**
```
❌ .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/sample_code/yaml/block_044.yaml
   • YAML root must be a dictionary
```

---

## Current Implementation

**File:** `vibey/operations/roadmap/optimized_validator.py`

```python
# Line 530-540
def _find_yaml_files(self, patterns: Optional[List[str]] = None) -> List[Path]:
    """Find all YAML files to validate."""
    if patterns:
        # Use custom patterns
        yaml_files = []
        for pattern in patterns:
            yaml_files.extend(self.roadmap_dir.glob(pattern))
        return list(set(yaml_files))  # Remove duplicates
    else:
        # Default: all YAML files in roadmap
        return list(self.roadmap_dir.rglob("*.yaml"))  # NO EXCLUSIONS!
```

---

## Implementation

### Add VALIDATION_EXCLUDE_PATTERNS Constant

```python
# vibey/operations/roadmap/optimized_validator.py

# Add near top of file, after imports (around line 30)

# ============================================================================
# Validation Exclusion Patterns
# ============================================================================

VALIDATION_EXCLUDE_PATTERNS = [
    "**/context/sample_code/**",       # Sample code snippets for documentation
    "**/context/samples/**",           # Alternative sample directory
    "**/test_fixtures/**",             # Test fixtures
    "**/.backup/**",                   # Backup directories
    "**/.archive/**",                  # Archived content
    "**/archived/**",                  # Another archive pattern
    "**/.git/**",                      # Git internals (should not be in roadmap anyway)
]

# Human-readable descriptions for documentation
VALIDATION_EXCLUDE_DESCRIPTIONS = {
    "**/context/sample_code/**": "Sample YAML snippets used in documentation",
    "**/context/samples/**": "Alternative sample code directory",
    "**/test_fixtures/**": "Test fixture files not meant for validation",
    "**/.backup/**": "Backup directories",
    "**/.archive/**": "Archived content not in active roadmap",
    "**/archived/**": "Archived tracks/sprints",
    "**/.git/**": "Git internal files",
}
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/optimized_validator.py` | Add constant at module level |

---

## Design Considerations

### Pattern Format

Use glob patterns compatible with `pathlib.Path.match()`:
- `**` matches any directory depth
- `*` matches any characters in a single path component
- Patterns are relative to the roadmap directory

### Extensibility

The list should be easy to extend for future exclusions:
- Sample documentation
- Test fixtures
- Backup/archive directories
- Migration artifacts

### Documentation

Include `VALIDATION_EXCLUDE_DESCRIPTIONS` for user documentation and help output.

---

## Testing Strategy

```python
def test_exclude_patterns_defined():
    """VALIDATION_EXCLUDE_PATTERNS constant exists and is valid."""
    from vibey.operations.roadmap.optimized_validator import VALIDATION_EXCLUDE_PATTERNS

    assert isinstance(VALIDATION_EXCLUDE_PATTERNS, list)
    assert len(VALIDATION_EXCLUDE_PATTERNS) > 0

    # All patterns should be strings
    for pattern in VALIDATION_EXCLUDE_PATTERNS:
        assert isinstance(pattern, str)
        assert "**" in pattern  # Should use glob syntax


def test_exclude_patterns_covers_sample_code():
    """Sample code directories are excluded."""
    from vibey.operations.roadmap.optimized_validator import VALIDATION_EXCLUDE_PATTERNS

    # Check that sample_code pattern exists
    assert any("sample_code" in p for p in VALIDATION_EXCLUDE_PATTERNS)


def test_exclude_descriptions_match():
    """Each pattern has a description."""
    from vibey.operations.roadmap.optimized_validator import (
        VALIDATION_EXCLUDE_PATTERNS,
        VALIDATION_EXCLUDE_DESCRIPTIONS
    )

    for pattern in VALIDATION_EXCLUDE_PATTERNS:
        assert pattern in VALIDATION_EXCLUDE_DESCRIPTIONS, f"Missing description for {pattern}"
```

---

## Success Criteria

- [ ] `VALIDATION_EXCLUDE_PATTERNS` constant defined at module level
- [ ] Patterns cover `context/sample_code/` directories
- [ ] Patterns use valid glob syntax
- [ ] `VALIDATION_EXCLUDE_DESCRIPTIONS` provides human-readable explanations
- [ ] Patterns are extensible for future needs

---

## Dependencies

None - This is a foundational task.

---

## Notes

This task defines the constant only. Task 002 will implement the actual filtering logic that uses these patterns.

The patterns follow Python's `pathlib` glob syntax which is used by the existing `rglob()` call in `_find_yaml_files()`.
