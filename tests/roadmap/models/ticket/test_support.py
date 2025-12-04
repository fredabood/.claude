"""
Tests for support classes (Progress, TestResult).
"""

import pytest
from datetime import datetime

from vibey.roadmap.models.ticket.support import Progress, TestResult


class TestProgress:
    """Tests for Progress class."""

    def test_basic_progress(self):
        """Test basic progress creation."""
        progress = Progress(total=10, completed=5)
        assert progress.total == 10
        assert progress.completed == 5
        assert progress.completion_percent == 50.0
        assert progress.remaining == 5
        assert not progress.is_complete

    def test_complete_progress(self):
        """Test fully complete progress."""
        progress = Progress(total=5, completed=5)
        assert progress.completion_percent == 100.0
        assert progress.remaining == 0
        assert progress.is_complete

    def test_zero_total_progress(self):
        """Test progress with zero total (edge case)."""
        progress = Progress(total=0, completed=0)
        assert progress.completion_percent == 100.0
        assert progress.remaining == 0
        assert progress.is_complete

    def test_progress_with_optional_fields(self):
        """Test progress with in_progress and blocked counts."""
        progress = Progress(total=10, completed=3, in_progress=2, blocked=1)
        assert progress.total == 10
        assert progress.completed == 3
        assert progress.in_progress == 2
        assert progress.blocked == 1
        assert progress.completion_percent == 30.0

    def test_progress_str(self):
        """Test string representation."""
        progress = Progress(total=10, completed=3)
        assert str(progress) == "3/10 (30.0%)"

    def test_progress_repr(self):
        """Test repr representation."""
        progress = Progress(total=10, completed=3)
        assert "completed=3" in repr(progress)
        assert "total=10" in repr(progress)


class TestTestResult:
    """Tests for TestResult class."""

    def test_basic_test_result(self):
        """Test basic test result creation."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.5,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
        )
        assert result.passed
        assert result.pass_rate == 100.0
        assert result.fail_rate == 0.0
        assert not result.has_failures

    def test_failed_test_result(self):
        """Test result with failures."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=2.0,
            passed=False,
            total_tests=10,
            passed_tests=7,
            failed_tests=3,
        )
        assert not result.passed
        assert result.pass_rate == 70.0
        assert result.fail_rate == 30.0
        assert result.has_failures

    def test_test_result_with_coverage(self):
        """Test result with coverage."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=5.0,
            passed=True,
            total_tests=50,
            passed_tests=50,
            failed_tests=0,
            coverage_percent=85.5,
        )
        assert result.has_coverage
        assert result.coverage_percent == 85.5
        assert result.meets_coverage_threshold(80.0)
        assert not result.meets_coverage_threshold(90.0)

    def test_test_result_without_coverage(self):
        """Test result without coverage measurement."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
        )
        assert not result.has_coverage
        assert not result.meets_coverage_threshold(80.0)

    def test_pass_threshold(self):
        """Test pass threshold checking."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=False,
            total_tests=10,
            passed_tests=9,
            failed_tests=1,
        )
        assert result.meets_pass_threshold(90.0)
        assert not result.meets_pass_threshold(95.0)

    def test_zero_tests(self):
        """Test result with zero tests (edge case)."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=0.1,
            passed=True,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
        )
        assert result.pass_rate == 100.0
        assert result.fail_rate == 0.0

    def test_str_representation(self):
        """Test string representation."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
        )
        assert "PASSED" in str(result)
        assert "10/10" in str(result)

    def test_str_with_coverage(self):
        """Test string representation with coverage."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
            coverage_percent=85.0,
        )
        assert "85.0% coverage" in str(result)

    def test_commit_sha_optional(self):
        """Test that commit_sha is optional."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=True,
            total_tests=5,
            passed_tests=5,
            failed_tests=0,
            commit_sha="abc123",
        )
        assert result.commit_sha == "abc123"
