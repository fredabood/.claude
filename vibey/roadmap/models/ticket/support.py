"""
Support classes for the unified ticket architecture.

This module contains utility classes used by the core completion model:
- Progress: Tracks progress toward state transitions
- TestResult: Captures test execution results
- RefreshContext: Context for automatic criterion refresh operations

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Protocol

from pydantic import BaseModel, Field, computed_field


# Protocol for ticket registry lookup (avoids circular imports)
class TicketRegistry(Protocol):
    """Protocol for looking up tickets by ID."""

    def get_ticket(self, ticket_id: str) -> Optional[Any]:
        """Get a ticket by ID, returns None if not found."""
        ...

    def get_ticket_status(self, ticket_id: str) -> Optional[str]:
        """Get the status of a ticket by ID."""
        ...


class TestRunner(Protocol):
    """Protocol for running test commands."""

    def run(self, command: str) -> "TestResult":
        """Run a test command and return results."""
        ...


class MetricsSource(Protocol):
    """Protocol for querying metrics values."""

    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get current value of a metric."""
        ...


class HttpClient(Protocol):
    """Protocol for HTTP requests to external systems."""

    def get(self, url: str) -> dict:
        """GET request, returns JSON response."""
        ...


class Progress(BaseModel):
    """
    Progress tracking toward a state transition.

    Used to track how many criteria are met for a specific transition
    (e.g., IN_PROGRESS, COMPLETED, PRODUCTION_READY).
    """

    total: int = Field(ge=0, description="Total number of criteria for this transition")
    completed: int = Field(ge=0, description="Number of criteria that are met")
    in_progress: int = Field(default=0, ge=0, description="Number of criteria being worked on")
    blocked: int = Field(default=0, ge=0, description="Number of criteria that are blocked")

    @computed_field
    @property
    def completion_percent(self) -> float:
        """Percentage of criteria that are met."""
        if self.total == 0:
            return 100.0
        return round(self.completed / self.total * 100, 1)

    @computed_field
    @property
    def remaining(self) -> int:
        """Number of criteria not yet met."""
        return self.total - self.completed

    @property
    def is_complete(self) -> bool:
        """True if all criteria are met."""
        return self.completed >= self.total

    def __str__(self) -> str:
        """Human-readable progress string."""
        return f"{self.completed}/{self.total} ({self.completion_percent}%)"

    def __repr__(self) -> str:
        return f"Progress(completed={self.completed}, total={self.total}, percent={self.completion_percent})"


class TestResult(BaseModel):
    """
    Result of a test execution.

    Captures detailed information about a test run for TestPassesTarget
    and TestCoverageTarget criteria.
    """

    # Execution metadata
    run_at: datetime = Field(description="When the test was executed")
    duration_seconds: float = Field(ge=0, description="How long the test took")
    commit_sha: Optional[str] = Field(default=None, description="Git commit at time of test")

    # Pass/fail results
    passed: bool = Field(description="Whether the test suite passed overall")
    total_tests: int = Field(ge=0, description="Total number of tests")
    passed_tests: int = Field(ge=0, description="Number of tests that passed")
    failed_tests: int = Field(ge=0, description="Number of tests that failed")
    skipped_tests: int = Field(default=0, ge=0, description="Number of tests skipped")
    error_tests: int = Field(default=0, ge=0, description="Number of tests with errors")

    # Coverage (optional)
    coverage_percent: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Test coverage percentage (if measured)"
    )

    # Output (truncated for storage)
    output: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Test output (truncated)"
    )
    error_output: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error output (truncated)"
    )

    @computed_field
    @property
    def pass_rate(self) -> float:
        """Percentage of tests that passed."""
        if self.total_tests == 0:
            return 100.0
        return round(self.passed_tests / self.total_tests * 100, 1)

    @computed_field
    @property
    def fail_rate(self) -> float:
        """Percentage of tests that failed."""
        if self.total_tests == 0:
            return 0.0
        return round(self.failed_tests / self.total_tests * 100, 1)

    @property
    def has_failures(self) -> bool:
        """True if any tests failed."""
        return self.failed_tests > 0 or self.error_tests > 0

    @property
    def has_coverage(self) -> bool:
        """True if coverage was measured."""
        return self.coverage_percent is not None

    def meets_pass_threshold(self, threshold: float) -> bool:
        """Check if pass rate meets the given threshold."""
        return self.pass_rate >= threshold

    def meets_coverage_threshold(self, threshold: float) -> bool:
        """Check if coverage meets the given threshold."""
        if self.coverage_percent is None:
            return False
        return self.coverage_percent >= threshold

    def __str__(self) -> str:
        """Human-readable result string."""
        status = "PASSED" if self.passed else "FAILED"
        result = f"{status}: {self.passed_tests}/{self.total_tests} tests"
        if self.coverage_percent is not None:
            result += f" ({self.coverage_percent}% coverage)"
        return result


@dataclass
class RefreshContext:
    """
    Context for automatic criterion refresh operations.

    Provides access to external systems needed to evaluate
    automatic criterion targets:
    - ticket_registry: Look up ticket status for CompletableTarget
    - test_runner: Run test commands for TestPassesTarget
    - metrics: Query metrics for ThresholdTarget
    - http_client: Make HTTP requests for ExternalTarget
    """

    ticket_registry: Optional[TicketRegistry] = None
    test_runner: Optional[TestRunner] = None
    metrics: Optional[MetricsSource] = None
    http_client: Optional[HttpClient] = None

    # Activity log entries generated during refresh
    activity_log: List[Any] = field(default_factory=list)

    def __post_init__(self):
        """Ensure activity_log is initialized."""
        if self.activity_log is None:
            self.activity_log = []


# Export all classes
__all__ = [
    "Progress",
    "TestResult",
    "RefreshContext",
    "TicketRegistry",
    "TestRunner",
    "MetricsSource",
    "HttpClient",
]
