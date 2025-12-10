# Task 003: Add Unit Test for Exclusion Patterns

**Task ID:** dogfooding-bugs-06-task-003
**Bug Addressed:** #7 (Validator Doesn't Exclude context/sample_code Directories)
**Complexity:** Low
**Type:** Testing

---

## Problem Statement

After implementing exclusion patterns (Tasks 001-002), comprehensive unit tests are needed to:

1. Verify patterns are correctly defined
2. Test filtering logic works
3. Ensure no regression in validation
4. Prevent false positives from sample code

---

## Test Cases

### 1. Pattern Definition Tests

```python
# tests/operations/roadmap/test_validation_exclusions.py

import pytest
from pathlib import Path
from vibey.operations.roadmap.optimized_validator import (
    VALIDATION_EXCLUDE_PATTERNS,
    VALIDATION_EXCLUDE_DESCRIPTIONS,
    OptimizedValidator,
    ValidationProfile,
)


class TestExclusionPatterns:
    """Tests for VALIDATION_EXCLUDE_PATTERNS constant."""

    def test_patterns_constant_exists(self):
        """VALIDATION_EXCLUDE_PATTERNS is defined."""
        assert VALIDATION_EXCLUDE_PATTERNS is not None
        assert isinstance(VALIDATION_EXCLUDE_PATTERNS, list)

    def test_patterns_not_empty(self):
        """At least one exclusion pattern exists."""
        assert len(VALIDATION_EXCLUDE_PATTERNS) > 0

    def test_all_patterns_are_strings(self):
        """All patterns are strings."""
        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            assert isinstance(pattern, str), f"Pattern {pattern} is not a string"

    def test_patterns_use_glob_syntax(self):
        """All patterns use valid glob syntax."""
        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            # Should contain ** for directory matching
            assert "**" in pattern or "*" in pattern, f"Pattern {pattern} missing glob wildcards"

    def test_sample_code_pattern_exists(self):
        """Pattern for sample_code directories exists."""
        sample_code_patterns = [p for p in VALIDATION_EXCLUDE_PATTERNS if "sample_code" in p]
        assert len(sample_code_patterns) >= 1, "Missing sample_code exclusion pattern"

    def test_descriptions_match_patterns(self):
        """Each pattern has a description."""
        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            assert pattern in VALIDATION_EXCLUDE_DESCRIPTIONS, \
                f"Missing description for pattern: {pattern}"

    def test_descriptions_are_helpful(self):
        """Descriptions explain why files are excluded."""
        for pattern, desc in VALIDATION_EXCLUDE_DESCRIPTIONS.items():
            assert len(desc) > 10, f"Description too short for {pattern}"
            assert isinstance(desc, str)
```

### 2. Filtering Logic Tests

```python
class TestFilterExcludedPaths:
    """Tests for _filter_excluded_paths method."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create validator instance."""
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)
        return OptimizedValidator(tmp_path, ValidationProfile.STANDARD)

    def test_excludes_sample_code_directory(self, validator):
        """Files in context/sample_code/ are excluded."""
        roadmap_dir = validator.roadmap_dir
        paths = [
            roadmap_dir / "tracks" / "track_123.yaml",
            roadmap_dir / "old-track" / "context" / "sample_code" / "yaml" / "test.yaml",
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 1
        assert "sample_code" not in str(filtered[0])

    def test_excludes_test_fixtures(self, validator):
        """Files in test_fixtures/ are excluded."""
        roadmap_dir = validator.roadmap_dir
        paths = [
            roadmap_dir / "tracks" / "track_123.yaml",
            roadmap_dir / "test_fixtures" / "fixture.yaml",
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 1
        assert "test_fixtures" not in str(filtered[0])

    def test_preserves_valid_paths(self, validator):
        """Valid roadmap files are not excluded."""
        roadmap_dir = validator.roadmap_dir
        valid_paths = [
            roadmap_dir / "tracks" / "track_123.yaml",
            roadmap_dir / "sprints" / "sprint_456.yaml",
            roadmap_dir / "tasks" / "task_789.yaml",
            roadmap_dir / "roadmap.yaml",
        ]

        filtered = validator._filter_excluded_paths(valid_paths)

        assert len(filtered) == len(valid_paths)
        assert set(filtered) == set(valid_paths)

    def test_handles_deeply_nested_exclusions(self, validator):
        """Deeply nested sample_code directories are excluded."""
        roadmap_dir = validator.roadmap_dir
        deep_path = roadmap_dir / "track" / "sprint" / "context" / "sample_code" / "yaml" / "nested" / "file.yaml"
        paths = [
            roadmap_dir / "tracks" / "track_123.yaml",
            deep_path,
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 1
        assert deep_path not in filtered

    def test_handles_empty_list(self, validator):
        """Empty input returns empty output."""
        filtered = validator._filter_excluded_paths([])
        assert filtered == []

    def test_handles_all_excluded(self, validator):
        """All files excluded returns empty list."""
        roadmap_dir = validator.roadmap_dir
        paths = [
            roadmap_dir / "context" / "sample_code" / "a.yaml",
            roadmap_dir / "test_fixtures" / "b.yaml",
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 0
```

### 3. Integration Tests

```python
class TestValidatorExclusion:
    """Integration tests for validator exclusion."""

    @pytest.fixture
    def roadmap_with_samples(self, tmp_path):
        """Create roadmap structure with sample code."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"

        # Create valid files
        tracks_dir = roadmap_dir / "tracks"
        tracks_dir.mkdir(parents=True)
        (tracks_dir / "track_123.yaml").write_text(
            "track:\n  id: track_123\n  name: Test\n  status: not_started"
        )

        sprints_dir = roadmap_dir / "sprints"
        sprints_dir.mkdir()
        (sprints_dir / "sprint_456.yaml").write_text(
            "sprint:\n  id: sprint_456\n  track_id: track_123\n  name: S1\n  status: not_started"
        )

        # Create sample code (invalid YAML that should be skipped)
        sample_dir = roadmap_dir / "sqlite-backend" / "context" / "sample_code" / "yaml"
        sample_dir.mkdir(parents=True)
        (sample_dir / "block_001.yaml").write_text("not: valid: yaml: [[[")
        (sample_dir / "block_002.yaml").write_text("123")  # Not a dict
        (sample_dir / "block_003.yaml").write_text("")  # Empty

        return tmp_path

    def test_validate_skips_sample_code(self, roadmap_with_samples):
        """Full validation skips sample_code files."""
        import os
        os.chdir(roadmap_with_samples)

        validator = OptimizedValidator(roadmap_with_samples, ValidationProfile.STANDARD)
        report = validator.validate()

        # Should only validate track and sprint
        assert report.total_files == 2
        assert report.valid_files == 2
        assert report.invalid_files == 0

    def test_validate_reports_exclusion_stats(self, roadmap_with_samples):
        """Validation can report excluded file count (optional)."""
        import os
        os.chdir(roadmap_with_samples)

        validator = OptimizedValidator(roadmap_with_samples, ValidationProfile.STANDARD)
        report = validator.validate()

        # Basic assertions - exclusion worked
        assert report.invalid_files == 0
        # The sample code files were silently excluded

    def test_quick_profile_also_excludes(self, roadmap_with_samples):
        """Quick validation profile also excludes sample code."""
        import os
        os.chdir(roadmap_with_samples)

        validator = OptimizedValidator(roadmap_with_samples, ValidationProfile.QUICK)
        report = validator.validate()

        assert report.invalid_files == 0

    def test_thorough_profile_also_excludes(self, roadmap_with_samples):
        """Thorough validation profile also excludes sample code."""
        import os
        os.chdir(roadmap_with_samples)

        validator = OptimizedValidator(roadmap_with_samples, ValidationProfile.THOROUGH)
        report = validator.validate()

        assert report.invalid_files == 0
```

### 4. Edge Case Tests

```python
class TestExclusionEdgeCases:
    """Edge case tests for exclusion logic."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create validator instance."""
        (tmp_path / ".vibey" / "roadmap").mkdir(parents=True)
        return OptimizedValidator(tmp_path, ValidationProfile.STANDARD)

    def test_partial_match_not_excluded(self, validator):
        """Files with 'sample' but not 'sample_code' are not excluded."""
        roadmap_dir = validator.roadmap_dir
        paths = [
            roadmap_dir / "tracks" / "sample_track.yaml",  # Not excluded
            roadmap_dir / "sample" / "other.yaml",  # Not in sample_code
        ]

        filtered = validator._filter_excluded_paths(paths)

        # Neither should be excluded
        assert len(filtered) == 2

    def test_case_sensitivity(self, validator):
        """Pattern matching handles case correctly."""
        roadmap_dir = validator.roadmap_dir
        paths = [
            roadmap_dir / "context" / "Sample_Code" / "file.yaml",  # Different case
            roadmap_dir / "context" / "sample_code" / "file.yaml",  # Exact match
        ]

        filtered = validator._filter_excluded_paths(paths)

        # At least the exact match should be excluded
        assert paths[1] not in filtered

    def test_path_with_spaces(self, validator):
        """Paths with spaces are handled correctly."""
        roadmap_dir = validator.roadmap_dir
        paths = [
            roadmap_dir / "my track" / "context" / "sample_code" / "file.yaml",
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 0  # Should be excluded

    def test_windows_path_separators(self, validator):
        """Windows-style paths are handled (if applicable)."""
        # This test ensures cross-platform compatibility
        roadmap_dir = validator.roadmap_dir

        # Create path that might have backslashes on Windows
        path = roadmap_dir / "context" / "sample_code" / "test.yaml"

        filtered = validator._filter_excluded_paths([path])

        assert len(filtered) == 0
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/operations/roadmap/test_validation_exclusions.py` | All exclusion pattern tests |

---

## Success Criteria

- [ ] All pattern definition tests pass
- [ ] All filtering logic tests pass
- [ ] All integration tests pass
- [ ] All edge case tests pass
- [ ] Tests run in CI pipeline
- [ ] No false positives from sample code in test results

---

## Dependencies

- Tasks 001-002 (implementation complete)

---

## Notes

These tests serve as:
1. **Verification** that Bug #7 is fixed
2. **Regression prevention** for future changes
3. **Documentation** of expected exclusion behavior
4. **Specification** for pattern matching rules

Key test scenarios:
- Exact pattern matches
- Deeply nested directories
- Edge cases (empty, all excluded)
- Cross-platform path handling
- All validation profiles
