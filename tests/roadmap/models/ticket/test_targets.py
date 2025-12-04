"""
Tests for criterion target types.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from dataclasses import dataclass

from vibey.roadmap.models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    TestCoverageTarget,
    ThresholdTarget,
    ManualTarget,
    ExternalTarget,
)
from vibey.roadmap.models.ticket.support import (
    TestResult,
    RefreshContext,
    TicketRegistry,
    TestRunner,
    MetricsSource,
    HttpClient,
)
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


# --- Mock implementations for testing refresh() ---

class MockTicketRegistry:
    """Mock implementation of TicketRegistry for testing."""

    def __init__(self):
        self.tickets = {}

    def set_status(self, ticket_id: str, status: str):
        """Set the status for a ticket."""
        self.tickets[ticket_id] = status

    def get_ticket(self, ticket_id: str) -> Optional[dict]:
        """Get ticket by ID."""
        if ticket_id in self.tickets:
            return {"id": ticket_id, "status": self.tickets[ticket_id]}
        return None

    def get_ticket_status(self, ticket_id: str) -> Optional[str]:
        """Get ticket status by ID."""
        return self.tickets.get(ticket_id)


class MockTestRunner:
    """Mock implementation of TestRunner for testing."""

    def __init__(self, results: dict = None):
        self.results = results or {}
        self.calls = []

    def run(self, command: str) -> TestResult:
        """Run a test command and return results."""
        self.calls.append(command)
        if command in self.results:
            return self.results[command]
        # Default: all tests pass
        return TestResult(
            run_at=datetime.now(timezone.utc),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
            coverage_percent=100.0,
        )


class MockMetricsSource:
    """Mock implementation of MetricsSource for testing."""

    def __init__(self, metrics: dict = None):
        self.metrics = metrics or {}

    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get metric value."""
        return self.metrics.get(metric_name)


class MockHttpClient:
    """Mock implementation of HttpClient for testing."""

    def __init__(self, responses: dict = None):
        self.responses = responses or {}
        self.calls = []

    def get(self, url: str) -> dict:
        """GET request."""
        self.calls.append(url)
        if url in self.responses:
            return self.responses[url]
        return {"status": "unknown"}


class TestIsAutomatic:
    """Tests for is_automatic property on all target types."""

    def test_completable_target_is_automatic(self):
        """CompletableTarget should be automatic."""
        target = CompletableTarget(completable_id="task-001")
        assert target.is_automatic is True

    def test_file_exists_target_is_automatic(self):
        """FileExistsTarget should be automatic."""
        target = FileExistsTarget(paths=["README.md"])
        assert target.is_automatic is True

    def test_test_passes_target_is_automatic(self):
        """TestPassesTarget should be automatic."""
        target = TestPassesTarget(test_command="pytest")
        assert target.is_automatic is True

    def test_test_coverage_target_is_automatic(self):
        """TestCoverageTarget should be automatic."""
        target = TestCoverageTarget(coverage_threshold=80.0)
        assert target.is_automatic is True

    def test_threshold_target_is_automatic(self):
        """ThresholdTarget should be automatic."""
        target = ThresholdTarget(metric_name="score", threshold=80.0)
        assert target.is_automatic is True

    def test_manual_target_is_not_automatic(self):
        """ManualTarget should NOT be automatic."""
        target = ManualTarget()
        assert target.is_automatic is False

    def test_external_target_is_automatic(self):
        """ExternalTarget should be automatic."""
        target = ExternalTarget(system_name="CI")
        assert target.is_automatic is True


class TestRefreshContext:
    """Tests for RefreshContext creation and usage."""

    def test_create_empty_context(self):
        """Can create RefreshContext with no arguments."""
        context = RefreshContext()
        assert context.ticket_registry is None
        assert context.test_runner is None
        assert context.metrics is None
        assert context.http_client is None
        assert context.activity_log == []

    def test_create_context_with_mocks(self):
        """Can create RefreshContext with mock implementations."""
        registry = MockTicketRegistry()
        runner = MockTestRunner()
        metrics = MockMetricsSource()
        http = MockHttpClient()

        context = RefreshContext(
            ticket_registry=registry,
            test_runner=runner,
            metrics=metrics,
            http_client=http,
        )

        assert context.ticket_registry is registry
        assert context.test_runner is runner
        assert context.metrics is metrics
        assert context.http_client is http


class TestCompletableTargetRefresh:
    """Tests for CompletableTarget.refresh()."""

    def test_refresh_with_no_context(self):
        """Refresh with no context should be a no-op."""
        target = CompletableTarget(completable_id="task-001")
        target.refresh()  # Should not raise
        assert target.current_status is None

    def test_refresh_with_empty_context(self):
        """Refresh with empty context should be a no-op."""
        target = CompletableTarget(completable_id="task-001")
        context = RefreshContext()
        target.refresh(context)
        assert target.current_status is None

    def test_refresh_updates_status(self):
        """Refresh should update current_status from registry."""
        registry = MockTicketRegistry()
        registry.set_status("task-001", "completed")
        context = RefreshContext(ticket_registry=registry)

        target = CompletableTarget(completable_id="task-001")
        target.refresh(context)

        assert target.current_status == TicketStatus.COMPLETED
        assert target.last_checked is not None

    def test_refresh_with_unknown_ticket(self):
        """Refresh with unknown ticket should leave status as None."""
        registry = MockTicketRegistry()
        context = RefreshContext(ticket_registry=registry)

        target = CompletableTarget(completable_id="unknown-task")
        target.refresh(context)

        assert target.current_status is None


class TestFileExistsTargetRefresh:
    """Tests for FileExistsTarget.refresh()."""

    def test_refresh_updates_paths(self):
        """Refresh should update existing/missing paths."""
        with TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "exists.txt"
            test_file.write_text("test")

            target = FileExistsTarget(
                paths=[str(test_file), str(Path(tmpdir) / "missing.txt")]
            )

            # Context is optional for FileExistsTarget (uses filesystem directly)
            target.refresh()

            assert str(test_file) in target.existing_paths
            assert str(Path(tmpdir) / "missing.txt") in target.missing_paths
            assert target.last_checked is not None


class TestTestPassesTargetRefresh:
    """Tests for TestPassesTarget.refresh()."""

    def test_refresh_with_no_context(self):
        """Refresh with no context should be a no-op."""
        target = TestPassesTarget(test_command="pytest")
        target.refresh()
        assert target.last_result is None

    def test_refresh_runs_tests(self):
        """Refresh should run test command via test runner."""
        runner = MockTestRunner()
        context = RefreshContext(test_runner=runner)

        target = TestPassesTarget(test_command="pytest tests/")
        target.refresh(context)

        assert "pytest tests/" in runner.calls
        assert target.last_result is not None
        assert target.last_result.passed


class TestTestCoverageTargetRefresh:
    """Tests for TestCoverageTarget.refresh()."""

    def test_refresh_updates_coverage(self):
        """Refresh should update coverage from test result."""
        result = TestResult(
            run_at=datetime.now(timezone.utc),
            duration_seconds=1.0,
            passed=True,
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
            coverage_percent=85.5,
        )
        runner = MockTestRunner(results={"pytest --cov": result})
        context = RefreshContext(test_runner=runner)

        target = TestCoverageTarget(
            coverage_threshold=80.0,
            test_command="pytest --cov"
        )
        target.refresh(context)

        assert target.current_coverage == 85.5
        assert target.is_satisfied()


class TestThresholdTargetRefresh:
    """Tests for ThresholdTarget.refresh()."""

    def test_refresh_with_no_context(self):
        """Refresh with no context should be a no-op."""
        target = ThresholdTarget(metric_name="score", threshold=80.0)
        target.refresh()
        assert target.current_value is None

    def test_refresh_updates_value(self):
        """Refresh should update value from metrics source."""
        metrics = MockMetricsSource(metrics={"coverage": 92.5})
        context = RefreshContext(metrics=metrics)

        target = ThresholdTarget(metric_name="coverage", threshold=80.0)
        target.refresh(context)

        assert target.current_value == 92.5
        assert target.last_checked is not None
        assert target.is_satisfied()


class TestManualTargetRefresh:
    """Tests for ManualTarget.refresh()."""

    def test_refresh_is_noop(self):
        """Refresh on ManualTarget should be a no-op."""
        target = ManualTarget(assessor="reviewer")
        context = RefreshContext()

        # Should not raise or change state
        target.refresh(context)

        assert not target.assessed
        assert target.met is None


class TestExternalTargetRefresh:
    """Tests for ExternalTarget.refresh()."""

    def test_refresh_with_no_context(self):
        """Refresh with no context should be a no-op."""
        target = ExternalTarget(system_name="CI", endpoint="http://ci/status")
        target.refresh()
        assert target.current_status is None

    def test_refresh_updates_status(self):
        """Refresh should update status from HTTP response."""
        http = MockHttpClient(responses={
            "http://ci/status": {"status": "success"}
        })
        context = RefreshContext(http_client=http)

        target = ExternalTarget(
            system_name="CI",
            endpoint="http://ci/status"
        )
        target.refresh(context)

        assert target.current_status == "success"
        assert target.last_checked is not None
        assert target.is_satisfied()

    def test_refresh_with_custom_status_field(self):
        """Refresh should use custom status_field."""
        http = MockHttpClient(responses={
            "http://scanner/result": {"result": "clean", "details": {}}
        })
        context = RefreshContext(http_client=http)

        target = ExternalTarget(
            system_name="Scanner",
            endpoint="http://scanner/result",
            expected_status="clean",
            status_field="result"
        )
        target.refresh(context)

        assert target.current_status == "clean"
        assert target.is_satisfied()
