"""
Criterion target types for the unified ticket architecture.

This module defines the polymorphic target types that determine how
criterion satisfaction is evaluated. Each target type corresponds to
a different way of checking if a criterion is met.

Target Types:
- CompletableTarget: Another Completable must reach a status
- FileExistsTarget: File(s) must exist at path(s)
- TestPassesTarget: Test command must pass
- TestCoverageTarget: Test coverage must meet threshold
- ThresholdTarget: Metric must meet threshold
- ManualTarget: Human assessment required
- ExternalTarget: External system check

Design Reference: sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from vibey.roadmap.models.ticket.enums import (
    CriterionTargetType,
    TicketStatus,
    ThresholdComparison,
)
from vibey.roadmap.models.ticket.support import TestResult


class CriterionTarget(BaseModel, ABC):
    """
    Abstract base for all criterion target types.

    Each target type defines how to check if a criterion is satisfied.
    Target types are polymorphic - stored with a type discriminator.
    """

    @abstractmethod
    def is_satisfied(self) -> bool:
        """Check if this target's condition is met."""
        ...

    @abstractmethod
    def get_status_description(self) -> str:
        """Get human-readable description of current status."""
        ...

    def refresh(self) -> None:
        """
        Update cached state from external sources.

        Override in subclasses that cache state (e.g., file existence,
        test results, external system status).
        """
        pass


class CompletableTarget(CriterionTarget):
    """
    Criterion met when another Completable reaches required status.

    This target type creates parent-child relationships. The parent is
    the Completable containing the criterion with this target. The child
    is the Completable referenced by completable_id.

    Used for:
    - Dependencies (blocks_transition_to=IN_PROGRESS)
    - Subtask completion (blocks_transition_to=COMPLETED)
    - Cross-track dependencies
    """

    type: Literal[CriterionTargetType.COMPLETABLE] = CriterionTargetType.COMPLETABLE

    completable_id: str = Field(description="ID of the target Completable")
    required_status: TicketStatus = Field(
        default=TicketStatus.COMPLETED,
        description="Status the target must reach"
    )

    # Cached state (updated by sync operations)
    current_status: Optional[TicketStatus] = Field(
        default=None,
        description="Cached current status of target"
    )
    last_checked: Optional[datetime] = Field(
        default=None,
        description="When status was last verified"
    )

    def is_satisfied(self) -> bool:
        """Check if target has reached required status."""
        if self.current_status is None:
            return False
        return self._status_gte(self.current_status, self.required_status)

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if self.current_status is None:
            return f"Waiting for {self.completable_id} (status unknown)"
        if self.is_satisfied():
            return f"{self.completable_id} is {self.current_status.value}"
        return f"Waiting for {self.completable_id} to be {self.required_status.value} (currently {self.current_status.value})"

    @staticmethod
    def _status_gte(current: TicketStatus, required: TicketStatus) -> bool:
        """Check if current status is >= required in progression order."""
        order = TicketStatus.progression_order()
        try:
            current_idx = order.index(current)
            required_idx = order.index(required)
            return current_idx >= required_idx
        except ValueError:
            # Terminal status - check exact match
            return current == required


class FileExistsTarget(CriterionTarget):
    """
    Criterion met when file(s) exist at specified path(s).

    Supports glob patterns for flexible file matching.
    Can require all files or just any one file.
    """

    type: Literal[CriterionTargetType.FILE_EXISTS] = CriterionTargetType.FILE_EXISTS

    paths: List[str] = Field(
        min_length=1,
        description="File paths or glob patterns to check"
    )
    all_required: bool = Field(
        default=True,
        description="If True, all paths must exist. If False, any one is sufficient."
    )

    # Cached state
    existing_paths: List[str] = Field(
        default_factory=list,
        description="Paths that currently exist"
    )
    missing_paths: List[str] = Field(
        default_factory=list,
        description="Paths that are missing"
    )
    last_checked: Optional[datetime] = Field(
        default=None,
        description="When paths were last checked"
    )

    def is_satisfied(self) -> bool:
        """Check if required files exist."""
        if self.all_required:
            return len(self.missing_paths) == 0 and len(self.existing_paths) > 0
        return len(self.existing_paths) > 0

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if self.is_satisfied():
            return f"All {len(self.existing_paths)} required files exist"
        if self.missing_paths:
            return f"Missing files: {', '.join(self.missing_paths[:3])}{'...' if len(self.missing_paths) > 3 else ''}"
        return "Files not yet checked"

    def refresh(self) -> None:
        """Check filesystem for file existence."""
        self.existing_paths = []
        self.missing_paths = []

        for path_pattern in self.paths:
            path = Path(path_pattern)
            # Handle glob patterns
            if '*' in path_pattern or '?' in path_pattern:
                matches = list(Path('.').glob(path_pattern))
                if matches:
                    self.existing_paths.extend(str(m) for m in matches)
                else:
                    self.missing_paths.append(path_pattern)
            else:
                if path.exists():
                    self.existing_paths.append(str(path))
                else:
                    self.missing_paths.append(str(path))

        self.last_checked = datetime.now()


class TestPassesTarget(CriterionTarget):
    """
    Criterion met when a test command passes.

    For coverage requirements, use TestCoverageTarget instead.
    This keeps test pass/fail separate from coverage metrics.
    """

    type: Literal[CriterionTargetType.TEST_PASSES] = CriterionTargetType.TEST_PASSES

    test_command: str = Field(
        description="Command to run tests (e.g., 'pytest tests/test_foo.py')"
    )
    pass_threshold: float = Field(
        default=100.0,
        ge=0,
        le=100,
        description="Percentage of tests that must pass"
    )

    # Cached state (latest result)
    last_result: Optional[TestResult] = Field(
        default=None,
        description="Result of last test execution"
    )

    def is_satisfied(self) -> bool:
        """Check if tests pass at required threshold."""
        if self.last_result is None:
            return False
        return self.last_result.pass_rate >= self.pass_threshold

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if self.last_result is None:
            return f"Tests not yet run: {self.test_command}"
        if self.is_satisfied():
            return f"Tests passing: {self.last_result.pass_rate}% >= {self.pass_threshold}%"
        return f"Tests failing: {self.last_result.pass_rate}% < {self.pass_threshold}%"


class TestCoverageTarget(CriterionTarget):
    """
    Criterion met when test coverage meets a threshold.

    Separate from TestPassesTarget to allow independent tracking
    of pass rate vs coverage requirements.
    """

    type: Literal[CriterionTargetType.TEST_COVERAGE] = CriterionTargetType.TEST_COVERAGE

    coverage_threshold: float = Field(
        ge=0,
        le=100,
        description="Minimum coverage percentage required"
    )
    test_command: Optional[str] = Field(
        default=None,
        description="Command to run coverage (if different from default)"
    )

    # Cached state
    current_coverage: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Current coverage percentage"
    )
    last_result: Optional[TestResult] = Field(
        default=None,
        description="Result of last test execution with coverage"
    )

    def is_satisfied(self) -> bool:
        """Check if coverage meets threshold."""
        if self.current_coverage is None:
            return False
        return self.current_coverage >= self.coverage_threshold

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if self.current_coverage is None:
            return f"Coverage not yet measured (threshold: {self.coverage_threshold}%)"
        if self.is_satisfied():
            return f"Coverage met: {self.current_coverage}% >= {self.coverage_threshold}%"
        return f"Coverage insufficient: {self.current_coverage}% < {self.coverage_threshold}%"


class ThresholdTarget(CriterionTarget):
    """
    Criterion met when a metric meets a threshold.

    Generic threshold target for any numeric metric (coverage,
    performance scores, code quality metrics, etc.).
    """

    type: Literal[CriterionTargetType.THRESHOLD] = CriterionTargetType.THRESHOLD

    metric_name: str = Field(
        description="Name of the metric (e.g., 'coverage', 'lint_score')"
    )
    threshold: float = Field(
        description="Threshold value to compare against"
    )
    comparison: ThresholdComparison = Field(
        default=ThresholdComparison.GTE,
        description="How to compare current value to threshold"
    )

    # Current value
    current_value: Optional[float] = Field(
        default=None,
        description="Current value of the metric"
    )
    last_checked: Optional[datetime] = Field(
        default=None,
        description="When metric was last measured"
    )

    def is_satisfied(self) -> bool:
        """Check if metric meets threshold."""
        if self.current_value is None:
            return False
        return self.comparison.compare(self.current_value, self.threshold)

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        threshold_desc = self.comparison.description(self.threshold)
        if self.current_value is None:
            return f"{self.metric_name} not yet measured (need {threshold_desc})"
        if self.is_satisfied():
            return f"{self.metric_name}: {self.current_value} meets {threshold_desc}"
        return f"{self.metric_name}: {self.current_value} does not meet {threshold_desc}"


class ManualTarget(CriterionTarget):
    """
    Criterion met when manually assessed by a human.

    Used for subjective assessments, reviews, approvals, etc.
    """

    type: Literal[CriterionTargetType.MANUAL] = CriterionTargetType.MANUAL

    assessor: Optional[str] = Field(
        default=None,
        description="Who should assess (role or name)"
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Instructions for assessment"
    )

    # Assessment state
    assessed: bool = Field(
        default=False,
        description="Whether assessment has been completed"
    )
    met: Optional[bool] = Field(
        default=None,
        description="Assessment result (True=passed, False=failed)"
    )
    assessed_at: Optional[datetime] = Field(
        default=None,
        description="When assessment was completed"
    )
    assessed_by: Optional[str] = Field(
        default=None,
        description="Who performed the assessment"
    )
    evidence: Optional[str] = Field(
        default=None,
        description="Notes, links, or evidence for assessment"
    )

    def is_satisfied(self) -> bool:
        """Check if manual assessment passed."""
        return self.assessed and self.met is True

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if not self.assessed:
            who = f" by {self.assessor}" if self.assessor else ""
            return f"Awaiting manual assessment{who}"
        if self.met:
            return f"Manually approved by {self.assessed_by or 'unknown'}"
        return f"Manually rejected by {self.assessed_by or 'unknown'}"

    def assess(
        self,
        met: bool,
        assessed_by: str,
        evidence: Optional[str] = None
    ) -> None:
        """Record a manual assessment."""
        self.assessed = True
        self.met = met
        self.assessed_by = assessed_by
        self.evidence = evidence
        self.assessed_at = datetime.now()


class ExternalTarget(CriterionTarget):
    """
    Criterion met when external system reports success.

    Used for CI/CD checks, security scanners, external APIs, etc.
    """

    type: Literal[CriterionTargetType.EXTERNAL] = CriterionTargetType.EXTERNAL

    system_name: str = Field(
        description="Name of external system (e.g., 'CI', 'Security Scanner')"
    )
    endpoint: Optional[str] = Field(
        default=None,
        description="API endpoint to check status"
    )
    expected_status: str = Field(
        default="success",
        description="Status value that indicates success"
    )

    # Cached state
    current_status: Optional[str] = Field(
        default=None,
        description="Current status from external system"
    )
    last_checked: Optional[datetime] = Field(
        default=None,
        description="When status was last checked"
    )
    response_data: Optional[dict] = Field(
        default=None,
        description="Raw response data from external system"
    )

    def is_satisfied(self) -> bool:
        """Check if external system reports expected status."""
        return self.current_status == self.expected_status

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if self.current_status is None:
            return f"Waiting for {self.system_name} check"
        if self.is_satisfied():
            return f"{self.system_name}: {self.current_status}"
        return f"{self.system_name}: {self.current_status} (expected: {self.expected_status})"


# Union type for all target types (for Pydantic discriminated union)
AnyTarget = Annotated[
    Union[
        CompletableTarget,
        FileExistsTarget,
        TestPassesTarget,
        TestCoverageTarget,
        ThresholdTarget,
        ManualTarget,
        ExternalTarget,
    ],
    Field(discriminator="type"),
]


def create_target(
    target_type: CriterionTargetType,
    config: dict,
) -> CriterionTarget:
    """
    Factory function to create a CriterionTarget from type and config.

    Used by RequirementInstantiator to create targets from templates.

    Args:
        target_type: The type of target to create
        config: Configuration dictionary for the target

    Returns:
        A CriterionTarget instance of the appropriate type

    Raises:
        ValueError: If target_type is not recognized
    """
    target_classes = {
        CriterionTargetType.COMPLETABLE: CompletableTarget,
        CriterionTargetType.FILE_EXISTS: FileExistsTarget,
        CriterionTargetType.TEST_PASSES: TestPassesTarget,
        CriterionTargetType.TEST_COVERAGE: TestCoverageTarget,
        CriterionTargetType.THRESHOLD: ThresholdTarget,
        CriterionTargetType.MANUAL: ManualTarget,
        CriterionTargetType.EXTERNAL: ExternalTarget,
    }

    target_class = target_classes.get(target_type)
    if target_class is None:
        raise ValueError(f"Unknown target type: {target_type}")

    return target_class(**config)


# Export all classes
__all__ = [
    # Base class
    "CriterionTarget",
    # Target types
    "CompletableTarget",
    "FileExistsTarget",
    "TestPassesTarget",
    "TestCoverageTarget",
    "ThresholdTarget",
    "ManualTarget",
    "ExternalTarget",
    # Union type
    "AnyTarget",
    # Factory function
    "create_target",
]
