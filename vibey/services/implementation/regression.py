"""
RegressionDetector - Post-task validation for detecting regressions.

This module provides regression detection capabilities for the autonomous
implementation loop, enabling validation that task execution did not break
previously-passing criteria.

Key Features:
- Compare before/after criterion states
- Detect regressions (passing -> failing)
- Detect new failures (not in snapshot)
- Infer likely cause from changed files
- Support acknowledgment for known regressions
- Generate human-readable reports
- Configurable policy: block, warn, or ignore regressions
- Optional auto-rollback on regression

Configuration in .vibey/config/implement.yaml:
```yaml
regression:
  enabled: true
  policy: block  # block, warn, ignore
  auto_rollback_on_regression: false
  require_acknowledgment: true
```

Usage:
    from vibey.services.implementation import (
        RegressionDetector,
        RegressionConfig,
        Regression,
        RegressionReport,
    )

    # Create detector with configuration
    config = RegressionConfig()
    detector = RegressionDetector(config=config)

    # Capture pre-task snapshot
    before_snapshot = detector.capture_snapshot(task)

    # ... execute task ...

    # Detect regressions
    report = detector.detect_regressions(before_snapshot, task)

    if detector.should_block(report):
        print(detector.generate_report(report))

Design Reference:
- Implementation Mode Track Sprint 3
- Context System V2 Architecture
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class RegressionPolicy(str, Enum):
    """
    Policy for handling detected regressions.

    Attributes:
        BLOCK: Block execution, require acknowledgment or fix
        WARN: Warn but continue execution
        IGNORE: Ignore regressions entirely
    """
    BLOCK = "block"
    WARN = "warn"
    IGNORE = "ignore"


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class RegressionConfig:
    """
    Configuration for regression detection.

    Loaded from .vibey/config/implement.yaml under the 'regression' key.

    Attributes:
        enabled: Whether regression detection is enabled
        policy: How to handle detected regressions (block, warn, ignore)
        auto_rollback_on_regression: Whether to auto-rollback on regression
        require_acknowledgment: Whether regressions must be acknowledged to proceed
    """
    enabled: bool = True
    policy: RegressionPolicy = RegressionPolicy.BLOCK
    auto_rollback_on_regression: bool = False
    require_acknowledgment: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionConfig":
        """
        Create config from dictionary (parsed from YAML).

        Args:
            data: Dictionary with regression configuration

        Returns:
            RegressionConfig instance
        """
        policy_str = data.get("policy", "block")
        try:
            policy = RegressionPolicy(policy_str.lower())
        except ValueError:
            logger.warning(f"Invalid regression policy '{policy_str}', using 'block'")
            policy = RegressionPolicy.BLOCK

        return cls(
            enabled=data.get("enabled", True),
            policy=policy,
            auto_rollback_on_regression=data.get("auto_rollback_on_regression", False),
            require_acknowledgment=data.get("require_acknowledgment", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "policy": self.policy.value,
            "auto_rollback_on_regression": self.auto_rollback_on_regression,
            "require_acknowledgment": self.require_acknowledgment,
        }


# =============================================================================
# CONSTANTS
# =============================================================================

REPORT_HEADER = """
================================================================================
REGRESSION REPORT
================================================================================
"""

BLOCKING_HEADER = """
--------------------------------------------------------------------------------
BLOCKING REGRESSIONS (must be fixed before completing task)
--------------------------------------------------------------------------------
"""

ACKNOWLEDGED_HEADER = """
--------------------------------------------------------------------------------
ACKNOWLEDGED REGRESSIONS (known issues, will not block)
--------------------------------------------------------------------------------
"""

NEW_FAILURES_HEADER = """
--------------------------------------------------------------------------------
NEW FAILURES (criteria that were not in snapshot)
--------------------------------------------------------------------------------
"""


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class RegressionCriterionState:
    """
    Snapshot of a criterion's state for regression comparison.

    Captures the criterion ID, description, and satisfaction state
    for comparing before/after states in regression detection.

    Note: This is distinct from CriterionState in the snapshot module,
    which has more detailed tracking. This class is optimized for
    simple before/after comparison in regression detection.

    Attributes:
        criterion_id: Unique identifier of the criterion
        description: Human-readable description
        is_met: Whether the criterion was satisfied at snapshot time
        status_description: Detailed status from the target
    """

    criterion_id: str
    description: str
    is_met: bool
    status_description: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "criterion_id": self.criterion_id,
            "description": self.description,
            "is_met": self.is_met,
            "status_description": self.status_description,
        }


@dataclass
class RegressionSnapshot:
    """
    Snapshot of task criteria states for regression detection.

    Captures the complete state of all criteria for a task,
    allowing comparison after task execution to detect regressions.

    Note: This is distinct from CriterionSnapshot in the snapshot module,
    which is designed for detailed pre-task state capture. This class is
    optimized for lightweight before/after comparison.

    Attributes:
        task_id: ULID of the task
        captured_at: When the snapshot was taken
        criteria: List of criterion state snapshots
    """

    task_id: str
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    criteria: List[RegressionCriterionState] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "task_id": self.task_id,
            "captured_at": self.captured_at.isoformat(),
            "criteria": [c.to_dict() for c in self.criteria],
        }

    def get_criterion(self, criterion_id: str) -> Optional[RegressionCriterionState]:
        """Get a criterion state by ID."""
        for c in self.criteria:
            if c.criterion_id == criterion_id:
                return c
        return None


@dataclass
class Regression:
    """
    Record of a regression detected during post-task validation.

    A regression occurs when a criterion that was passing before
    task execution is now failing after execution.

    Attributes:
        criterion_ref: Reference to the regressed criterion (ID)
        before_state: State of criterion before task execution
        after_state: State of criterion after task execution
        likely_cause: Inferred cause of the regression (file, commit, etc.)
        is_acknowledged: Whether this regression is acknowledged/expected
        acknowledgment: Reason for acknowledgment if applicable
    """

    criterion_ref: str
    before_state: str
    after_state: str
    likely_cause: Optional[str] = None
    is_acknowledged: bool = False
    acknowledgment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "criterion_ref": self.criterion_ref,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "likely_cause": self.likely_cause,
            "is_acknowledged": self.is_acknowledged,
            "acknowledgment": self.acknowledgment,
        }

    def acknowledge(self, reason: str) -> None:
        """
        Acknowledge this regression with a reason.

        Args:
            reason: Explanation for why this regression is acceptable
        """
        self.is_acknowledged = True
        self.acknowledgment = reason
        logger.info(f"Acknowledged regression {self.criterion_ref}: {reason}")


@dataclass
class RegressionReport:
    """
    Report of regressions detected during post-task validation.

    Contains all regressions and new failures found when comparing
    a pre-task snapshot with the current state after task execution.

    Attributes:
        task_id: ULID of the task that was executed
        evaluated_at: When the report was generated
        total_criteria_checked: Number of criteria evaluated
        regressions: List of regressions detected
        new_failures: Criteria that failed but weren't in snapshot
    """

    task_id: str
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_criteria_checked: int = 0
    regressions: List[Regression] = field(default_factory=list)
    new_failures: List[str] = field(default_factory=list)

    @property
    def has_unacknowledged_regressions(self) -> bool:
        """
        Check if there are any unacknowledged regressions.

        Returns:
            True if any regression is not acknowledged
        """
        return any(not r.is_acknowledged for r in self.regressions)

    @property
    def blocking_regressions(self) -> List[Regression]:
        """
        Get regressions that block task completion.

        Returns:
            List of unacknowledged regressions
        """
        return [r for r in self.regressions if not r.is_acknowledged]

    @property
    def acknowledged_regressions(self) -> List[Regression]:
        """
        Get regressions that have been acknowledged.

        Returns:
            List of acknowledged regressions
        """
        return [r for r in self.regressions if r.is_acknowledged]

    @property
    def regression_count(self) -> int:
        """Total number of regressions."""
        return len(self.regressions)

    @property
    def blocking_count(self) -> int:
        """Number of blocking (unacknowledged) regressions."""
        return len(self.blocking_regressions)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "task_id": self.task_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "total_criteria_checked": self.total_criteria_checked,
            "regressions": [r.to_dict() for r in self.regressions],
            "new_failures": self.new_failures,
            "has_unacknowledged_regressions": self.has_unacknowledged_regressions,
            "blocking_count": self.blocking_count,
        }


# =============================================================================
# REGRESSION DETECTOR
# =============================================================================


class RegressionDetector:
    """
    Detects regressions in task criteria after execution.

    RegressionDetector captures the state of task criteria before execution
    and compares it with the state after execution to detect regressions
    (criteria that were passing but are now failing).

    Attributes:
        config: RegressionConfig for policy and behavior settings
        acknowledged_patterns: Patterns for auto-acknowledging known regressions
        reports_dir: Directory for storing regression reports

    Example:
        >>> config = RegressionConfig()
        >>> detector = RegressionDetector(config=config)
        >>> before = detector.capture_snapshot(task)
        >>> # ... execute task ...
        >>> report = detector.detect_regressions(before, task)
        >>> if detector.should_block(report):
        ...     print(detector.generate_report(report))
    """

    def __init__(
        self,
        config: Optional[RegressionConfig] = None,
        acknowledged_patterns: Optional[List[str]] = None,
        reports_dir: Optional[Path] = None,
    ):
        """
        Initialize the regression detector.

        Args:
            config: RegressionConfig for policy and behavior settings
            acknowledged_patterns: Regex patterns for auto-acknowledging
                regressions that match known acceptable patterns
            reports_dir: Directory for storing regression reports
        """
        self.config = config or RegressionConfig()
        self.acknowledged_patterns = acknowledged_patterns or []
        self.reports_dir = reports_dir or Path.cwd() / ".vibey" / "implementation" / "regressions"

    # =========================================================================
    # SNAPSHOT CAPTURE
    # =========================================================================

    def capture_snapshot(self, task: "HierarchicalTicket") -> RegressionSnapshot:
        """
        Capture the current state of task criteria.

        Creates a snapshot of all criteria states for later comparison.
        This should be called before task execution begins.

        Args:
            task: The HierarchicalTicket to snapshot

        Returns:
            RegressionSnapshot with current criteria states
        """
        snapshot = RegressionSnapshot(task_id=task.id)

        # Refresh criteria to get current state
        task.refresh_criteria()

        # Capture each criterion's state
        for criterion in task.all_criteria:
            criterion_snapshot = RegressionCriterionState(
                criterion_id=criterion.id,
                description=criterion.description,
                is_met=criterion.is_met,
                status_description=criterion.status_description,
            )
            snapshot.criteria.append(criterion_snapshot)

        logger.debug(
            f"Captured snapshot for task {task.id}: "
            f"{len(snapshot.criteria)} criteria"
        )

        return snapshot

    # =========================================================================
    # REGRESSION DETECTION
    # =========================================================================

    def detect_regressions(
        self,
        before: RegressionSnapshot,
        task: "HierarchicalTicket",
        changed_files: Optional[List[Path]] = None,
    ) -> RegressionReport:
        """
        Compare snapshot with current state to detect regressions.

        A regression is detected when:
        - Criterion was passing (is_met=True) in snapshot
        - Criterion is now failing (is_met=False) after execution

        Also detects new failures:
        - Criteria not in snapshot that are now failing

        Args:
            before: RegressionSnapshot captured before execution
            task: The HierarchicalTicket after execution
            changed_files: Optional list of files changed during execution

        Returns:
            RegressionReport with all detected issues
        """
        report = RegressionReport(task_id=task.id)

        # Refresh criteria to get current state
        task.refresh_criteria()

        # Track which snapshot criteria we've checked
        checked_ids = set()

        for criterion in task.all_criteria:
            report.total_criteria_checked += 1
            checked_ids.add(criterion.id)

            # Get snapshot state for this criterion
            before_snapshot = before.get_criterion(criterion.id)

            if before_snapshot is None:
                # Criterion wasn't in snapshot
                if not criterion.is_met:
                    report.new_failures.append(criterion.id)
                    logger.debug(
                        f"New failure detected: {criterion.id} "
                        f"({criterion.description})"
                    )
                continue

            # Check for regression: was passing, now failing
            if before_snapshot.is_met and not criterion.is_met:
                regression = Regression(
                    criterion_ref=criterion.id,
                    before_state=before_snapshot.status_description,
                    after_state=criterion.status_description,
                )

                # Try to infer the cause
                if changed_files:
                    regression.likely_cause = self.infer_cause(
                        regression, changed_files, criterion
                    )

                # Check if should be auto-acknowledged
                if self._should_auto_acknowledge(criterion.id):
                    regression.acknowledge("Matches known acceptable pattern")

                report.regressions.append(regression)
                logger.warning(
                    f"Regression detected: {criterion.id} - "
                    f"was '{before_snapshot.status_description}', "
                    f"now '{criterion.status_description}'"
                )

        # Check for criteria that were in snapshot but are now gone
        for snapshot_criterion in before.criteria:
            if snapshot_criterion.criterion_id not in checked_ids:
                logger.debug(
                    f"Criterion {snapshot_criterion.criterion_id} was in snapshot "
                    f"but not found in current task"
                )

        logger.info(
            f"Regression detection complete for task {task.id}: "
            f"{report.regression_count} regressions, "
            f"{len(report.new_failures)} new failures"
        )

        return report

    # =========================================================================
    # CAUSE INFERENCE
    # =========================================================================

    def infer_cause(
        self,
        regression: Regression,
        changed_files: List[Path],
        criterion: Optional[Any] = None,
    ) -> Optional[str]:
        """
        Infer what likely caused a regression.

        Analyzes the changed files and criterion to determine the
        most likely cause of the regression.

        Args:
            regression: The Regression to analyze
            changed_files: Files that were modified during task execution
            criterion: The actual criterion object (optional, for target analysis)

        Returns:
            String describing the likely cause, or None if unknown
        """
        if not changed_files:
            return None

        # Try to correlate with criterion target
        if criterion is not None:
            cause = self._infer_cause_from_target(criterion, changed_files)
            if cause:
                return cause

        # Generic inference: list changed files
        file_list = ", ".join(str(f) for f in changed_files[:3])
        if len(changed_files) > 3:
            file_list += f" (+{len(changed_files) - 3} more)"

        return f"Changes to: {file_list}"

    def _infer_cause_from_target(
        self,
        criterion: Any,
        changed_files: List[Path],
    ) -> Optional[str]:
        """
        Infer cause based on criterion target type.

        Different target types have different likely causes:
        - FileExistsTarget: file was deleted or renamed
        - TestPassesTarget: test file or tested code changed
        - ThresholdTarget: metric-affecting code changed
        """
        target = criterion.target if hasattr(criterion, "target") else None
        if target is None:
            return None

        target_type = type(target).__name__

        if target_type == "FileExistsTarget":
            # Check if the expected file was in changed files
            expected_path = getattr(target, "path", None)
            if expected_path:
                for changed in changed_files:
                    if str(changed).endswith(str(expected_path)):
                        return f"File '{expected_path}' was modified or deleted"
            return "Expected file may have been deleted or renamed"

        if target_type == "TestPassesTarget":
            # Look for test files in changes
            test_files = [
                f for f in changed_files
                if "test" in str(f).lower() or "_test" in str(f).lower()
            ]
            if test_files:
                return f"Test file changed: {test_files[0]}"

            # Look for source files that tests might cover
            pattern = getattr(target, "pattern", None)
            if pattern:
                matching = [f for f in changed_files if pattern in str(f)]
                if matching:
                    return f"Source file changed: {matching[0]}"

            return "Test or tested code was modified"

        if target_type == "ThresholdTarget":
            metric_name = getattr(target, "metric_name", "metric")
            return f"Changes may have affected {metric_name}"

        if target_type == "CompletableTarget":
            completable_id = getattr(target, "completable_id", None)
            if completable_id:
                return f"Dependency '{completable_id}' may have changed"

        return None

    def _should_auto_acknowledge(self, criterion_id: str) -> bool:
        """
        Check if a regression should be auto-acknowledged.

        Args:
            criterion_id: ID of the criterion to check

        Returns:
            True if criterion matches an acknowledged pattern
        """
        import re

        for pattern in self.acknowledged_patterns:
            try:
                if re.match(pattern, criterion_id):
                    return True
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")

        return False

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    def generate_report(self, report: RegressionReport) -> str:
        """
        Generate a human-readable report of regressions.

        Format includes:
        - Summary statistics
        - BLOCKING regressions (unacknowledged)
        - ACKNOWLEDGED regressions
        - New failures

        Args:
            report: RegressionReport to format

        Returns:
            Formatted string report
        """
        lines = [REPORT_HEADER.strip()]
        lines.append("")
        lines.append(f"Task: {report.task_id}")
        lines.append(f"Evaluated: {report.evaluated_at.isoformat()}")
        lines.append(f"Criteria Checked: {report.total_criteria_checked}")
        lines.append(f"Regressions: {report.regression_count}")
        lines.append(f"  - Blocking: {report.blocking_count}")
        lines.append(f"  - Acknowledged: {len(report.acknowledged_regressions)}")
        lines.append(f"New Failures: {len(report.new_failures)}")
        lines.append("")

        # Blocking regressions
        blocking = report.blocking_regressions
        if blocking:
            lines.append(BLOCKING_HEADER.strip())
            for reg in blocking:
                lines.append("")
                lines.append(f"Criterion: {reg.criterion_ref}")
                lines.append(f"  Before: {reg.before_state}")
                lines.append(f"  After:  {reg.after_state}")
                if reg.likely_cause:
                    lines.append(f"  Likely Cause: {reg.likely_cause}")
            lines.append("")

        # Acknowledged regressions
        acknowledged = report.acknowledged_regressions
        if acknowledged:
            lines.append(ACKNOWLEDGED_HEADER.strip())
            for reg in acknowledged:
                lines.append("")
                lines.append(f"Criterion: {reg.criterion_ref}")
                lines.append(f"  Before: {reg.before_state}")
                lines.append(f"  After:  {reg.after_state}")
                if reg.likely_cause:
                    lines.append(f"  Likely Cause: {reg.likely_cause}")
                lines.append(f"  Acknowledgment: {reg.acknowledgment}")
            lines.append("")

        # New failures
        if report.new_failures:
            lines.append(NEW_FAILURES_HEADER.strip())
            for failure_id in report.new_failures:
                lines.append(f"  - {failure_id}")
            lines.append("")

        # Final status
        lines.append("=" * 80)
        if report.has_unacknowledged_regressions:
            lines.append(
                f"STATUS: BLOCKED - {report.blocking_count} regression(s) must be resolved"
            )
        else:
            lines.append("STATUS: PASSED - No blocking regressions")
        lines.append("=" * 80)

        return "\n".join(lines)

    # =========================================================================
    # POLICY CHECKING
    # =========================================================================

    def should_block(self, report: RegressionReport) -> bool:
        """
        Check if regressions should block task completion based on policy.

        Args:
            report: RegressionReport to evaluate

        Returns:
            True if execution should be blocked
        """
        if not self.config.enabled:
            return False

        if not report.has_unacknowledged_regressions:
            return False

        if self.config.policy == RegressionPolicy.IGNORE:
            return False

        if self.config.policy == RegressionPolicy.WARN:
            # Warn policy only blocks on critical issues (none by default in criteria model)
            logger.warning(
                f"Regression detected (warn mode): {report.blocking_count} regression(s)"
            )
            return False

        # BLOCK policy
        if self.config.require_acknowledgment:
            return report.has_unacknowledged_regressions

        return report.blocking_count > 0

    def should_rollback(self, report: RegressionReport) -> bool:
        """
        Check if task should be rolled back due to regressions.

        Args:
            report: RegressionReport to evaluate

        Returns:
            True if auto-rollback should be triggered
        """
        if not self.config.enabled:
            return False

        if not self.config.auto_rollback_on_regression:
            return False

        return report.has_unacknowledged_regressions

    # =========================================================================
    # REPORT MANAGEMENT
    # =========================================================================

    def save_report(self, report: RegressionReport) -> Path:
        """
        Save a regression report to disk.

        Args:
            report: RegressionReport to save

        Returns:
            Path where the report was saved
        """
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.reports_dir / f"report_{report.task_id}.json"

        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        logger.debug(f"Saved regression report to {report_path}")
        return report_path

    def load_report(self, task_id: str) -> Optional[RegressionReport]:
        """
        Load a regression report from disk.

        Args:
            task_id: Task ID to load report for

        Returns:
            RegressionReport if exists, None otherwise
        """
        report_path = self.reports_dir / f"report_{task_id}.json"

        if not report_path.exists():
            return None

        try:
            with open(report_path, "r") as f:
                data = json.load(f)
            return self._dict_to_report(data)
        except Exception as e:
            logger.warning(f"Failed to load regression report: {e}")
            return None

    def get_latest_report(self) -> Optional[RegressionReport]:
        """
        Get the most recent regression report.

        Returns:
            Most recent RegressionReport, or None if no reports exist
        """
        if not self.reports_dir.exists():
            return None

        reports = list(self.reports_dir.glob("report_*.json"))
        if not reports:
            return None

        latest = max(reports, key=lambda p: p.stat().st_mtime)
        return self.load_report(latest.stem.replace("report_", ""))

    def list_reports(self, limit: int = 10) -> List[RegressionReport]:
        """
        List recent regression reports.

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of RegressionReport objects
        """
        if not self.reports_dir.exists():
            return []

        reports = list(self.reports_dir.glob("report_*.json"))
        reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        result = []
        for path in reports[:limit]:
            task_id = path.stem.replace("report_", "")
            report = self.load_report(task_id)
            if report:
                result.append(report)

        return result

    def acknowledge_regression(
        self,
        task_id: str,
        criterion_ref: Optional[str] = None,
        reason: str = "Acknowledged by user"
    ) -> bool:
        """
        Acknowledge regression(s) for a task.

        Args:
            task_id: Task ID
            criterion_ref: Specific criterion to acknowledge (all if None)
            reason: Reason for acknowledgment

        Returns:
            True if any regressions were acknowledged
        """
        report = self.load_report(task_id)
        if not report:
            logger.warning(f"No regression report found for task {task_id}")
            return False

        acknowledged = False

        for regression in report.regressions:
            if criterion_ref is None or regression.criterion_ref == criterion_ref:
                if not regression.is_acknowledged:
                    regression.acknowledge(reason)
                    acknowledged = True

        if acknowledged:
            self.save_report(report)

        return acknowledged

    def _dict_to_report(self, data: Dict[str, Any]) -> RegressionReport:
        """Convert dictionary to RegressionReport."""
        regressions = []
        for r_data in data.get("regressions", []):
            reg = Regression(
                criterion_ref=r_data["criterion_ref"],
                before_state=r_data["before_state"],
                after_state=r_data["after_state"],
                likely_cause=r_data.get("likely_cause"),
                is_acknowledged=r_data.get("is_acknowledged", False),
                acknowledgment=r_data.get("acknowledgment"),
            )
            regressions.append(reg)

        return RegressionReport(
            task_id=data["task_id"],
            evaluated_at=datetime.fromisoformat(data["evaluated_at"]),
            total_criteria_checked=data.get("total_criteria_checked", 0),
            regressions=regressions,
            new_failures=data.get("new_failures", []),
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "RegressionConfig",
    "RegressionPolicy",
    # Data models
    "RegressionCriterionState",
    "RegressionSnapshot",
    "Regression",
    "RegressionReport",
    # Main class
    "RegressionDetector",
]
