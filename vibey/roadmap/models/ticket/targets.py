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
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from vibey.roadmap.models.ticket.enums import (
    CriterionTargetType,
    DeliverableType,
    TicketStatus,
    ThresholdComparison,
)
from vibey.roadmap.models.ticket.artifact_enums import ArtifactVerification
from vibey.roadmap.models.ticket.support import RefreshContext, TestResult


class CriterionTarget(BaseModel, ABC):
    """
    Abstract base for all criterion target types.

    Each target type defines how to check if a criterion is satisfied.
    Target types are polymorphic - stored with a type discriminator.
    """

    @property
    @abstractmethod
    def is_automatic(self) -> bool:
        """
        Can this target auto-evaluate without human intervention?

        Automatic targets can refresh their state from external sources.
        Non-automatic targets (ManualTarget) require explicit human action.
        """
        ...

    @abstractmethod
    def is_satisfied(self) -> bool:
        """Check if this target's condition is met."""
        ...

    @abstractmethod
    def get_status_description(self) -> str:
        """Get human-readable description of current status."""
        ...

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """
        Update cached state from external sources.

        Override in subclasses that cache state (e.g., file existence,
        test results, external system status).

        Args:
            context: Optional context providing access to external systems
                    (ticket registry, test runner, metrics source, HTTP client)
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

    @property
    def is_automatic(self) -> bool:
        """CompletableTarget is automatic - can check ticket status."""
        return True

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """Update current_status from ticket registry."""
        if context is None or context.ticket_registry is None:
            return

        status_str = context.ticket_registry.get_ticket_status(self.completable_id)
        if status_str is not None:
            try:
                self.current_status = TicketStatus(status_str)
            except ValueError:
                pass  # Keep existing status if invalid
        self.last_checked = datetime.now(timezone.utc)

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
    deliverable_type: DeliverableType = Field(
        default=DeliverableType.OTHER,
        description="Classification of the deliverable (code, test, documentation, etc.)"
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

    @property
    def is_automatic(self) -> bool:
        """FileExistsTarget is automatic - can check filesystem."""
        return True

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

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
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

        self.last_checked = datetime.now(timezone.utc)


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

    @property
    def is_automatic(self) -> bool:
        """TestPassesTarget is automatic - can run test command."""
        return True

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """Run test command and update last_result."""
        if context is None or context.test_runner is None:
            return

        self.last_result = context.test_runner.run(self.test_command)

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

    @property
    def is_automatic(self) -> bool:
        """TestCoverageTarget is automatic - can run coverage command."""
        return True

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """Run test command with coverage and update current_coverage."""
        if context is None or context.test_runner is None or self.test_command is None:
            return

        self.last_result = context.test_runner.run(self.test_command)
        if self.last_result and self.last_result.coverage_percent is not None:
            self.current_coverage = self.last_result.coverage_percent

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

    @property
    def is_automatic(self) -> bool:
        """ThresholdTarget is automatic - can query metrics source."""
        return True

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """Query metrics source and update current_value."""
        if context is None or context.metrics is None:
            return

        value = context.metrics.get_metric(self.metric_name)
        if value is not None:
            self.current_value = value
            self.last_checked = datetime.now(timezone.utc)

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

    @property
    def is_automatic(self) -> bool:
        """ManualTarget is NOT automatic - requires human assessment."""
        return False

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """No-op for manual targets - must use assess() method."""
        pass  # Manual targets cannot auto-refresh

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
    status_field: str = Field(
        default="status",
        description="Field name in response containing status"
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

    @property
    def is_automatic(self) -> bool:
        """ExternalTarget is automatic - can query external endpoint."""
        return True

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """Query external endpoint and update current_status."""
        if context is None or context.http_client is None or self.endpoint is None:
            return

        try:
            response = context.http_client.get(self.endpoint)
            self.response_data = response
            if self.status_field in response:
                self.current_status = str(response[self.status_field])
            self.last_checked = datetime.now(timezone.utc)
        except Exception:
            # Leave current_status unchanged on error
            pass

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


class ArtifactTarget(CriterionTarget):
    """
    Criterion met when an Artifact entity meets verification requirements.

    This target type references first-class Artifact entities and supports
    multiple verification modes:
    - EXISTS: Files in artifact.paths[] exist
    - NOT_STALE: Files exist AND documentation is not stale
    - HASH_UNCHANGED: Content hasn't changed since criterion was created

    Used for:
    - Code deliverables
    - Documentation that must track source changes
    - Ensuring no unexpected file modifications
    """

    type: Literal[CriterionTargetType.ARTIFACT] = CriterionTargetType.ARTIFACT

    artifact_id: str = Field(
        description="ID of the referenced Artifact entity"
    )
    verification: ArtifactVerification = Field(
        default=ArtifactVerification.EXISTS,
        description="How to verify the artifact criterion is satisfied"
    )

    # Cached state (denormalized from Artifact for performance)
    artifact_exists: bool = Field(
        default=False,
        description="Whether artifact files exist"
    )
    artifact_hash: Optional[str] = Field(
        default=None,
        description="Current content hash of artifact"
    )
    artifact_is_stale: bool = Field(
        default=False,
        description="Whether documentation artifact is stale"
    )
    last_checked: Optional[datetime] = Field(
        default=None,
        description="When artifact state was last verified"
    )

    # For HASH_UNCHANGED mode - stored hash at criterion creation
    expected_hash: Optional[str] = Field(
        default=None,
        description="Expected hash for HASH_UNCHANGED verification"
    )

    @property
    def is_automatic(self) -> bool:
        """ArtifactTarget is automatic - can refresh from artifact registry."""
        return True

    def refresh(self, context: Optional[RefreshContext] = None) -> None:
        """
        Update cached state from artifact registry.

        Requires context.artifact_registry to be set.
        """
        if context is None:
            return

        # Get artifact from registry
        artifact_registry = getattr(context, 'artifact_registry', None)
        if artifact_registry is None:
            return

        artifact = artifact_registry.get(self.artifact_id)
        if artifact is None:
            self.artifact_exists = False
            self.artifact_hash = None
            self.artifact_is_stale = False
            self.last_checked = datetime.now(timezone.utc)
            return

        # Update cached state from artifact
        self.artifact_exists = artifact.exists
        self.artifact_hash = artifact.content_hash
        self.artifact_is_stale = artifact.is_stale
        self.last_checked = datetime.now(timezone.utc)

    def is_satisfied(self) -> bool:
        """
        Check if artifact meets verification requirements.

        Verification modes:
        - EXISTS: Files exist
        - NOT_STALE: Files exist AND not stale
        - HASH_UNCHANGED: Files exist AND hash matches expected
        """
        if self.verification == ArtifactVerification.EXISTS:
            return self.artifact_exists

        elif self.verification == ArtifactVerification.NOT_STALE:
            return self.artifact_exists and not self.artifact_is_stale

        elif self.verification == ArtifactVerification.HASH_UNCHANGED:
            if not self.artifact_exists:
                return False
            if self.expected_hash is None:
                # No expected hash set - satisfied if exists
                return True
            return self.artifact_hash == self.expected_hash

        return False

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        if not self.artifact_exists:
            return f"Artifact {self.artifact_id} does not exist"

        if self.verification == ArtifactVerification.EXISTS:
            return f"Artifact {self.artifact_id} exists"

        elif self.verification == ArtifactVerification.NOT_STALE:
            if self.artifact_is_stale:
                return f"Artifact {self.artifact_id} is stale"
            return f"Artifact {self.artifact_id} exists and is current"

        elif self.verification == ArtifactVerification.HASH_UNCHANGED:
            if self.expected_hash is None:
                return f"Artifact {self.artifact_id} exists (no hash check)"
            if self.artifact_hash == self.expected_hash:
                return f"Artifact {self.artifact_id} content unchanged"
            return f"Artifact {self.artifact_id} content has changed"

        return f"Artifact {self.artifact_id}: unknown verification mode"

    def capture_expected_hash(self) -> None:
        """
        Capture current artifact hash as expected hash.

        Call this when creating a HASH_UNCHANGED criterion to set
        the baseline hash.
        """
        self.expected_hash = self.artifact_hash


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
        ArtifactTarget,
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
        CriterionTargetType.ARTIFACT: ArtifactTarget,
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
    "ArtifactTarget",
    # Union type
    "AnyTarget",
    # Factory function
    "create_target",
]
