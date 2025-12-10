"""
Unit tests for validation exclusion patterns.

Tests Bug #7: Validator Doesn't Exclude context/sample_code Directories
"""

import pytest
from pathlib import Path


class TestExclusionPatternsDefined:
    """Tests for VALIDATION_EXCLUDE_PATTERNS constant."""

    def test_exclude_patterns_exist(self):
        """VALIDATION_EXCLUDE_PATTERNS constant exists and is valid."""
        from vibey.operations.roadmap.optimized_validator import VALIDATION_EXCLUDE_PATTERNS

        assert isinstance(VALIDATION_EXCLUDE_PATTERNS, list)
        assert len(VALIDATION_EXCLUDE_PATTERNS) > 0

    def test_patterns_are_strings(self):
        """All patterns should be strings."""
        from vibey.operations.roadmap.optimized_validator import VALIDATION_EXCLUDE_PATTERNS

        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            assert isinstance(pattern, str)

    def test_patterns_use_glob_syntax(self):
        """Patterns should use glob syntax with **."""
        from vibey.operations.roadmap.optimized_validator import VALIDATION_EXCLUDE_PATTERNS

        # At least some patterns should use ** for directory matching
        assert any("**" in p for p in VALIDATION_EXCLUDE_PATTERNS)

    def test_sample_code_pattern_exists(self):
        """Sample code directories are covered by patterns."""
        from vibey.operations.roadmap.optimized_validator import VALIDATION_EXCLUDE_PATTERNS

        assert any("sample_code" in p for p in VALIDATION_EXCLUDE_PATTERNS)

    def test_descriptions_match_patterns(self):
        """Each pattern has a description."""
        from vibey.operations.roadmap.optimized_validator import (
            VALIDATION_EXCLUDE_PATTERNS,
            VALIDATION_EXCLUDE_DESCRIPTIONS
        )

        for pattern in VALIDATION_EXCLUDE_PATTERNS:
            assert pattern in VALIDATION_EXCLUDE_DESCRIPTIONS, \
                f"Missing description for pattern: {pattern}"


class TestFilterExcludedPaths:
    """Tests for _filter_excluded_paths method."""

    def test_filter_sample_code_directory(self):
        """Sample code directories are filtered out."""
        from vibey.operations.roadmap.optimized_validator import OptimizedValidator, ValidationProfile

        validator = OptimizedValidator.__new__(OptimizedValidator)
        validator.roadmap_dir = Path("/fake/.vibey/roadmap")

        paths = [
            Path("/fake/.vibey/roadmap/tracks/track_123.yaml"),
            Path("/fake/.vibey/roadmap/old-track/context/sample_code/yaml/test.yaml"),
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 1
        assert paths[0] in filtered
        assert paths[1] not in filtered

    def test_filter_test_fixtures(self):
        """Test fixtures are filtered out."""
        from vibey.operations.roadmap.optimized_validator import OptimizedValidator, ValidationProfile

        validator = OptimizedValidator.__new__(OptimizedValidator)
        validator.roadmap_dir = Path("/fake/.vibey/roadmap")

        paths = [
            Path("/fake/.vibey/roadmap/sprints/sprint_456.yaml"),
            Path("/fake/.vibey/roadmap/test_fixtures/fixture.yaml"),
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 1
        assert paths[0] in filtered
        assert paths[1] not in filtered

    def test_keeps_valid_roadmap_files(self):
        """Valid roadmap files are not filtered."""
        from vibey.operations.roadmap.optimized_validator import OptimizedValidator, ValidationProfile

        validator = OptimizedValidator.__new__(OptimizedValidator)
        validator.roadmap_dir = Path("/fake/.vibey/roadmap")

        paths = [
            Path("/fake/.vibey/roadmap/tracks/track_123.yaml"),
            Path("/fake/.vibey/roadmap/sprints/sprint_456.yaml"),
            Path("/fake/.vibey/roadmap/tasks/task_789.yaml"),
            Path("/fake/.vibey/roadmap/roadmap.yaml"),
        ]

        filtered = validator._filter_excluded_paths(paths)

        assert len(filtered) == 4
        for p in paths:
            assert p in filtered
