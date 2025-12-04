"""
Tests for criterion target types.
"""

import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    TestCoverageTarget,
    ThresholdTarget,
    ManualTarget,
    ExternalTarget,
)
from vibey.roadmap.models.ticket.support import TestResult
from vibey.roadmap.models.ticket.enums import (
    TicketStatus,
    ThresholdComparison,
    CriterionTargetType,
)


class TestCompletableTarget:
    """Tests for CompletableTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = CompletableTarget(completable_id="task-001")
        assert target.completable_id == "task-001"
        assert target.required_status == TicketStatus.COMPLETED
        assert target.current_status is None
        assert target.type == CriterionTargetType.COMPLETABLE

    def test_not_satisfied_when_no_status(self):
        """Test target is not satisfied when current_status is None."""
        target = CompletableTarget(completable_id="task-001")
        assert not target.is_satisfied()

    def test_satisfied_when_status_met(self):
        """Test target is satisfied when status meets requirement."""
        target = CompletableTarget(
            completable_id="task-001",
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.COMPLETED,
        )
        assert target.is_satisfied()

    def test_satisfied_when_status_exceeds(self):
        """Test target is satisfied when status exceeds requirement."""
        target = CompletableTarget(
            completable_id="task-001",
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.DEPLOYED,
        )
        assert target.is_satisfied()

    def test_not_satisfied_when_status_less(self):
        """Test target is not satisfied when status is less than required."""
        target = CompletableTarget(
            completable_id="task-001",
            required_status=TicketStatus.COMPLETED,
            current_status=TicketStatus.IN_PROGRESS,
        )
        assert not target.is_satisfied()

    def test_status_description(self):
        """Test status description."""
        target = CompletableTarget(
            completable_id="task-001",
            current_status=TicketStatus.IN_PROGRESS,
        )
        desc = target.get_status_description()
        assert "task-001" in desc
        assert "in_progress" in desc or "Waiting" in desc


class TestFileExistsTarget:
    """Tests for FileExistsTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = FileExistsTarget(paths=["README.md"])
        assert target.paths == ["README.md"]
        assert target.all_required
        assert target.type == CriterionTargetType.FILE_EXISTS

    def test_satisfied_with_existing_files(self):
        """Test satisfaction with existing files."""
        target = FileExistsTarget(
            paths=["file1.txt", "file2.txt"],
            existing_paths=["file1.txt", "file2.txt"],
            missing_paths=[],
        )
        assert target.is_satisfied()

    def test_not_satisfied_with_missing_files(self):
        """Test not satisfied with missing files."""
        target = FileExistsTarget(
            paths=["file1.txt", "file2.txt"],
            existing_paths=["file1.txt"],
            missing_paths=["file2.txt"],
        )
        assert not target.is_satisfied()

    def test_any_required_satisfied(self):
        """Test satisfaction when only any file required."""
        target = FileExistsTarget(
            paths=["file1.txt", "file2.txt"],
            all_required=False,
            existing_paths=["file1.txt"],
            missing_paths=["file2.txt"],
        )
        assert target.is_satisfied()

    def test_any_required_not_satisfied(self):
        """Test not satisfied when no files exist."""
        target = FileExistsTarget(
            paths=["file1.txt", "file2.txt"],
            all_required=False,
            existing_paths=[],
            missing_paths=["file1.txt", "file2.txt"],
        )
        assert not target.is_satisfied()

    def test_refresh_with_real_files(self):
        """Test refresh with real filesystem."""
        with TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")

            target = FileExistsTarget(
                paths=[str(test_file), str(Path(tmpdir) / "missing.txt")]
            )
            target.refresh()

            assert str(test_file) in target.existing_paths
            assert str(Path(tmpdir) / "missing.txt") in target.missing_paths

    def test_status_description(self):
        """Test status description."""
        target = FileExistsTarget(
            paths=["file.txt"],
            missing_paths=["file.txt"],
        )
        desc = target.get_status_description()
        assert "Missing" in desc or "file.txt" in desc


class TestTestPassesTarget:
    """Tests for TestPassesTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = TestPassesTarget(test_command="pytest")
        assert target.test_command == "pytest"
        assert target.pass_threshold == 100.0
        assert target.type == CriterionTargetType.TEST_PASSES

    def test_not_satisfied_when_no_result(self):
        """Test not satisfied when no test result."""
        target = TestPassesTarget(test_command="pytest")
        assert not target.is_satisfied()

    def test_satisfied_when_tests_pass(self):
        """Test satisfied when tests pass at threshold."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
        )
        target = TestPassesTarget(
            test_command="pytest",
            pass_threshold=100.0,
            last_result=result,
        )
        assert target.is_satisfied()

    def test_not_satisfied_when_below_threshold(self):
        """Test not satisfied when below threshold."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=False,
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
        )
        target = TestPassesTarget(
            test_command="pytest",
            pass_threshold=90.0,
            last_result=result,
        )
        assert not target.is_satisfied()  # 80% < 90%

    def test_satisfied_at_threshold(self):
        """Test satisfied at exactly threshold."""
        result = TestResult(
            run_at=datetime.now(),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=9,
            failed_tests=1,
        )
        target = TestPassesTarget(
            test_command="pytest",
            pass_threshold=90.0,
            last_result=result,
        )
        assert target.is_satisfied()  # 90% >= 90%


class TestTestCoverageTarget:
    """Tests for TestCoverageTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = TestCoverageTarget(coverage_threshold=80.0)
        assert target.coverage_threshold == 80.0
        assert target.type == CriterionTargetType.TEST_COVERAGE

    def test_not_satisfied_when_no_coverage(self):
        """Test not satisfied when no coverage measured."""
        target = TestCoverageTarget(coverage_threshold=80.0)
        assert not target.is_satisfied()

    def test_satisfied_when_coverage_met(self):
        """Test satisfied when coverage meets threshold."""
        target = TestCoverageTarget(
            coverage_threshold=80.0,
            current_coverage=85.0,
        )
        assert target.is_satisfied()

    def test_not_satisfied_when_coverage_below(self):
        """Test not satisfied when coverage below threshold."""
        target = TestCoverageTarget(
            coverage_threshold=80.0,
            current_coverage=75.0,
        )
        assert not target.is_satisfied()


class TestThresholdTarget:
    """Tests for ThresholdTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = ThresholdTarget(metric_name="quality_score", threshold=80.0)
        assert target.metric_name == "quality_score"
        assert target.threshold == 80.0
        assert target.comparison == ThresholdComparison.GTE
        assert target.type == CriterionTargetType.THRESHOLD

    def test_gte_comparison(self):
        """Test >= comparison."""
        target = ThresholdTarget(
            metric_name="score",
            threshold=80.0,
            comparison=ThresholdComparison.GTE,
            current_value=80.0,
        )
        assert target.is_satisfied()

        target.current_value = 79.0
        assert not target.is_satisfied()

    def test_gt_comparison(self):
        """Test > comparison."""
        target = ThresholdTarget(
            metric_name="score",
            threshold=80.0,
            comparison=ThresholdComparison.GT,
            current_value=80.0,
        )
        assert not target.is_satisfied()

        target.current_value = 81.0
        assert target.is_satisfied()

    def test_eq_comparison(self):
        """Test == comparison."""
        target = ThresholdTarget(
            metric_name="score",
            threshold=80.0,
            comparison=ThresholdComparison.EQ,
            current_value=80.0,
        )
        assert target.is_satisfied()

        target.current_value = 81.0
        assert not target.is_satisfied()

    def test_lte_comparison(self):
        """Test <= comparison."""
        target = ThresholdTarget(
            metric_name="score",
            threshold=80.0,
            comparison=ThresholdComparison.LTE,
            current_value=80.0,
        )
        assert target.is_satisfied()

        target.current_value = 81.0
        assert not target.is_satisfied()

    def test_lt_comparison(self):
        """Test < comparison."""
        target = ThresholdTarget(
            metric_name="score",
            threshold=80.0,
            comparison=ThresholdComparison.LT,
            current_value=80.0,
        )
        assert not target.is_satisfied()

        target.current_value = 79.0
        assert target.is_satisfied()

    def test_status_description(self):
        """Test status description."""
        target = ThresholdTarget(
            metric_name="coverage",
            threshold=80.0,
            comparison=ThresholdComparison.GTE,
            current_value=75.0,
        )
        desc = target.get_status_description()
        assert "coverage" in desc
        assert "75.0" in desc or "80" in desc


class TestManualTarget:
    """Tests for ManualTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = ManualTarget()
        assert not target.assessed
        assert target.met is None
        assert target.type == CriterionTargetType.MANUAL

    def test_not_satisfied_when_not_assessed(self):
        """Test not satisfied when not assessed."""
        target = ManualTarget()
        assert not target.is_satisfied()

    def test_not_satisfied_when_rejected(self):
        """Test not satisfied when assessed but rejected."""
        target = ManualTarget(assessed=True, met=False)
        assert not target.is_satisfied()

    def test_satisfied_when_approved(self):
        """Test satisfied when assessed and approved."""
        target = ManualTarget(assessed=True, met=True)
        assert target.is_satisfied()

    def test_assess_method(self):
        """Test the assess method."""
        target = ManualTarget()
        target.assess(met=True, assessed_by="reviewer@example.com", evidence="LGTM")

        assert target.assessed
        assert target.met
        assert target.assessed_by == "reviewer@example.com"
        assert target.evidence == "LGTM"
        assert target.assessed_at is not None

    def test_status_description_awaiting(self):
        """Test status description when awaiting assessment."""
        target = ManualTarget(assessor="tech-lead")
        desc = target.get_status_description()
        assert "Awaiting" in desc or "assessment" in desc.lower()
        assert "tech-lead" in desc

    def test_status_description_approved(self):
        """Test status description when approved."""
        target = ManualTarget(assessed=True, met=True, assessed_by="reviewer")
        desc = target.get_status_description()
        assert "approved" in desc.lower() or "reviewer" in desc


class TestExternalTarget:
    """Tests for ExternalTarget."""

    def test_basic_creation(self):
        """Test basic target creation."""
        target = ExternalTarget(system_name="CI")
        assert target.system_name == "CI"
        assert target.expected_status == "success"
        assert target.type == CriterionTargetType.EXTERNAL

    def test_not_satisfied_when_no_status(self):
        """Test not satisfied when no status."""
        target = ExternalTarget(system_name="CI")
        assert not target.is_satisfied()

    def test_satisfied_when_status_matches(self):
        """Test satisfied when status matches expected."""
        target = ExternalTarget(
            system_name="CI",
            expected_status="success",
            current_status="success",
        )
        assert target.is_satisfied()

    def test_not_satisfied_when_status_differs(self):
        """Test not satisfied when status differs."""
        target = ExternalTarget(
            system_name="CI",
            expected_status="success",
            current_status="failed",
        )
        assert not target.is_satisfied()

    def test_custom_expected_status(self):
        """Test with custom expected status."""
        target = ExternalTarget(
            system_name="Security Scanner",
            expected_status="clean",
            current_status="clean",
        )
        assert target.is_satisfied()

    def test_status_description(self):
        """Test status description."""
        target = ExternalTarget(
            system_name="CI",
            current_status="running",
            expected_status="success",
        )
        desc = target.get_status_description()
        assert "CI" in desc
        assert "running" in desc or "success" in desc


class TestTargetSerialization:
    """Tests for JSON/YAML serialization of targets."""

    def test_completable_target_serialization(self):
        """Test CompletableTarget serialization."""
        target = CompletableTarget(
            completable_id="task-001",
            current_status=TicketStatus.IN_PROGRESS,
        )
        data = target.model_dump()
        assert data["completable_id"] == "task-001"
        assert data["type"] == "completable"

        # Reconstruct
        reconstructed = CompletableTarget(**data)
        assert reconstructed.completable_id == "task-001"

    def test_manual_target_serialization(self):
        """Test ManualTarget serialization."""
        target = ManualTarget(
            assessor="reviewer",
            assessed=True,
            met=True,
        )
        data = target.model_dump()
        assert data["type"] == "manual"
        assert data["assessed"]
        assert data["met"]

    def test_threshold_target_serialization(self):
        """Test ThresholdTarget serialization."""
        target = ThresholdTarget(
            metric_name="coverage",
            threshold=80.0,
            comparison=ThresholdComparison.GTE,
        )
        data = target.model_dump()
        assert data["metric_name"] == "coverage"
        assert data["threshold"] == 80.0
        assert data["comparison"] == "gte"
