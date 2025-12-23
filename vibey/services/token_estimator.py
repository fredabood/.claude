"""
Token Estimation Service for the Vibey Agent Framework.

This service provides intelligent token estimation for tasks based on:
- Task type (development, documentation, testing, research, etc.)
- Complexity level (low, medium, high, critical)
- Description analysis (length, keyword patterns)
- Historical data from completed tasks with calibration

The service generates TokenEstimate objects that get wrapped in Tokens
objects on the Ticket model.

Usage:
    from vibey.services.token_estimator import TokenEstimator, CalibrationManager

    # Basic estimation without calibration
    estimator = TokenEstimator()
    result = estimator.estimate_from_description(
        description="Implement OAuth2 authentication flow",
        task_type="development",
        complexity="high"
    )

    # Estimation with historical calibration
    calibration_manager = CalibrationManager()
    calibration_manager.collect_historical_data()  # Gather from completed tasks
    calibration_manager.compute_calibration_factors()
    calibration_manager.save_calibration()

    calibrated_estimator = TokenEstimator(calibration_manager=calibration_manager)
    result = calibrated_estimator.estimate_task(task)

Design Reference: Sprint 2 - Estimation Algorithms
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import yaml
from pydantic import BaseModel, Field

from vibey.roadmap.models.ticket import (
    TokenEstimate,
    Tokens,
    TaskType,
    Complexity,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket import TaskTicket


# =============================================================================
# BASE ESTIMATION FACTORS
# =============================================================================

# Estimation Profiles: Token ranges by task type
# Based on task characteristics:
# - development: High output (code), medium input (context)
# - documentation: High output (docs), low input
# - testing: Medium output (tests), medium input (code to test)
# - research: Low output (findings), high input (exploration)
# - review: Low output (comments), high input (code to review)
# - infrastructure: Variable, depends on scope
# - design: Medium output (specs), low input
# - gate: Minimal tokens (validation only)

ESTIMATION_PROFILES: Dict[str, Dict[str, tuple[int, int]]] = {
    # Task type: {input: (min, max), output: (min, max)}
    "development": {
        "input_range": (5000, 50000),    # Medium input (context reading)
        "output_range": (2000, 20000),   # High output (code generation)
    },
    "documentation": {
        "input_range": (2000, 20000),    # Low input
        "output_range": (3000, 30000),   # High output (docs)
    },
    "testing": {
        "input_range": (3000, 30000),    # Medium input (code to test)
        "output_range": (2000, 15000),   # Medium output (tests)
    },
    "research": {
        "input_range": (10000, 100000),  # High input (exploration)
        "output_range": (1000, 10000),   # Low output (findings)
    },
    "review": {
        "input_range": (5000, 50000),    # High input (code to review)
        "output_range": (500, 5000),     # Low output (comments)
    },
    "infrastructure": {
        "input_range": (3000, 40000),    # Variable, depends on scope
        "output_range": (2000, 25000),   # Variable, depends on scope
    },
    "design": {
        "input_range": (2000, 15000),    # Low input
        "output_range": (3000, 20000),   # Medium output (specs)
    },
    "gate": {
        "input_range": (1000, 5000),     # Minimal (validation only)
        "output_range": (500, 2000),     # Minimal (gate result)
    },
}

# Legacy format for backward compatibility
# These represent typical token counts for medium complexity tasks
TASK_TYPE_BASE_TOKENS: Dict[str, Dict[str, int]] = {
    task_type: {
        "input_target": (profile["input_range"][0] + profile["input_range"][1]) // 2,
        "output_target": (profile["output_range"][0] + profile["output_range"][1]) // 2,
    }
    for task_type, profile in ESTIMATION_PROFILES.items()
}

# Complexity multipliers as specified in the task:
# simple=0.5, medium=1.0, complex=2.0, very_complex=4.0
# These are applied to the base ranges
COMPLEXITY_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "simple": {
        "factor": 0.5,          # Half the base estimate
        "min_factor": 0.8,      # 80% of scaled target for min
        "target_factor": 1.0,   # Base target (after complexity scaling)
        "max_factor": 1.3,      # 130% of scaled target for max
    },
    "low": {  # Alias for simple
        "factor": 0.5,
        "min_factor": 0.8,
        "target_factor": 1.0,
        "max_factor": 1.3,
    },
    "medium": {
        "factor": 1.0,          # Base estimate
        "min_factor": 0.7,      # 70% of target for min
        "target_factor": 1.0,   # Base target
        "max_factor": 1.5,      # 150% of target for max
    },
    "complex": {
        "factor": 2.0,          # Double the base estimate
        "min_factor": 0.6,      # 60% of scaled target for min
        "target_factor": 1.0,   # Base target (after complexity scaling)
        "max_factor": 2.0,      # 200% of scaled target for max
    },
    "high": {  # Alias for complex
        "factor": 2.0,
        "min_factor": 0.6,
        "target_factor": 1.0,
        "max_factor": 2.0,
    },
    "very_complex": {
        "factor": 4.0,          # Quadruple the base estimate
        "min_factor": 0.5,      # 50% of scaled target for min
        "target_factor": 1.0,   # Base target (after complexity scaling)
        "max_factor": 2.5,      # 250% of scaled target for max
    },
    "critical": {  # Alias for very_complex
        "factor": 4.0,
        "min_factor": 0.5,
        "target_factor": 1.0,
        "max_factor": 2.5,
    },
}

# Default values for unknown task types
DEFAULT_BASE_TOKENS: Dict[str, int] = {
    "input_target": 10000,
    "output_target": 5000,
}

# Default estimation profile for unknown task types
DEFAULT_ESTIMATION_PROFILE: Dict[str, tuple[int, int]] = {
    "input_range": (5000, 50000),
    "output_range": (2000, 20000),
}

# Default complexity when not specified
DEFAULT_COMPLEXITY = "medium"

# Default calibration file location
DEFAULT_CALIBRATION_PATH = Path(".vibey/config/token_calibration.yaml")


# =============================================================================
# CALIBRATION DATA MODELS
# =============================================================================


@dataclass
class CalibrationDataPoint:
    """
    A single data point from a completed task for calibration analysis.

    Captures the estimate vs actual usage for accuracy calculation.
    """

    task_id: str
    task_type: str
    complexity: str
    input_estimate_target: Optional[int]
    input_actual_usage: Optional[int]
    output_estimate_target: Optional[int]
    output_actual_usage: Optional[int]
    completed_at: Optional[datetime] = None

    @property
    def input_accuracy(self) -> Optional[float]:
        """Calculate input accuracy ratio (usage/estimate)."""
        if self.input_estimate_target and self.input_actual_usage:
            return self.input_actual_usage / self.input_estimate_target
        return None

    @property
    def output_accuracy(self) -> Optional[float]:
        """Calculate output accuracy ratio (usage/estimate)."""
        if self.output_estimate_target and self.output_actual_usage:
            return self.output_actual_usage / self.output_estimate_target
        return None


@dataclass
class CalibrationFactor:
    """
    Calibration adjustment factors for a task_type + complexity combination.

    Factors are applied as multipliers to base estimates:
    - factor > 1.0: Estimates were too low, increase
    - factor < 1.0: Estimates were too high, decrease
    - factor = 1.0: Estimates were accurate
    """

    task_type: str
    complexity: str
    input_factor: float = 1.0
    output_factor: float = 1.0
    sample_count: int = 0
    mean_input_accuracy: float = 1.0
    mean_output_accuracy: float = 1.0
    std_dev_input: float = 0.0
    std_dev_output: float = 0.0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "task_type": self.task_type,
            "complexity": self.complexity,
            "input_factor": round(self.input_factor, 4),
            "output_factor": round(self.output_factor, 4),
            "sample_count": self.sample_count,
            "mean_input_accuracy": round(self.mean_input_accuracy, 4),
            "mean_output_accuracy": round(self.mean_output_accuracy, 4),
            "std_dev_input": round(self.std_dev_input, 4),
            "std_dev_output": round(self.std_dev_output, 4),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationFactor":
        """Create from dictionary (YAML deserialization)."""
        last_updated = data.get("last_updated")
        if last_updated and isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated)
        return cls(
            task_type=data["task_type"],
            complexity=data["complexity"],
            input_factor=data.get("input_factor", 1.0),
            output_factor=data.get("output_factor", 1.0),
            sample_count=data.get("sample_count", 0),
            mean_input_accuracy=data.get("mean_input_accuracy", 1.0),
            mean_output_accuracy=data.get("mean_output_accuracy", 1.0),
            std_dev_input=data.get("std_dev_input", 0.0),
            std_dev_output=data.get("std_dev_output", 0.0),
            last_updated=last_updated,
        )


@dataclass
class CalibrationData:
    """
    Complete calibration data with factors and metadata.

    Stored in .vibey/config/token_calibration.yaml
    """

    version: str = "1.0.0"
    factors: Dict[str, CalibrationFactor] = field(default_factory=dict)
    total_tasks_analyzed: int = 0
    last_calibration: Optional[datetime] = None
    alerts: List[str] = field(default_factory=list)

    def get_factor(self, task_type: str, complexity: str) -> Optional[CalibrationFactor]:
        """Get calibration factor for a specific task_type + complexity."""
        key = f"{task_type}:{complexity}"
        return self.factors.get(key)

    def set_factor(self, factor: CalibrationFactor) -> None:
        """Set calibration factor for a task_type + complexity."""
        key = f"{factor.task_type}:{factor.complexity}"
        self.factors[key] = factor

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "calibration": {
                "version": self.version,
                "total_tasks_analyzed": self.total_tasks_analyzed,
                "last_calibration": self.last_calibration.isoformat() if self.last_calibration else None,
                "alerts": self.alerts,
                "factors": [f.to_dict() for f in self.factors.values()],
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalibrationData":
        """Create from dictionary (YAML deserialization)."""
        cal_data = data.get("calibration", data)
        last_cal = cal_data.get("last_calibration")
        if last_cal and isinstance(last_cal, str):
            last_cal = datetime.fromisoformat(last_cal)

        instance = cls(
            version=cal_data.get("version", "1.0.0"),
            total_tasks_analyzed=cal_data.get("total_tasks_analyzed", 0),
            last_calibration=last_cal,
            alerts=cal_data.get("alerts", []),
        )

        # Load factors
        for factor_data in cal_data.get("factors", []):
            factor = CalibrationFactor.from_dict(factor_data)
            instance.set_factor(factor)

        return instance


# =============================================================================
# CALIBRATION MANAGER
# =============================================================================


class CalibrationManager:
    """
    Manages historical data calibration for token estimation.

    The calibration process:
    1. Collect historical data from completed tasks
    2. Group by task_type and complexity
    3. Calculate mean, median, std dev for estimate accuracy
    4. Compute adjustment factors
    5. Store calibration data in .vibey/config/token_calibration.yaml

    Continuous learning:
    - Call update_from_completed_task() after each task completion
    - Monitors for consistently off estimates and generates alerts
    """

    # Threshold for generating alerts about estimation accuracy
    ACCURACY_ALERT_THRESHOLD = 0.5  # Alert if estimates are off by more than 50%
    MIN_SAMPLES_FOR_ALERT = 5  # Need at least N samples before alerting

    def __init__(
        self,
        root_dir: Optional[Path] = None,
        calibration_path: Optional[Path] = None,
    ):
        """
        Initialize calibration manager.

        Args:
            root_dir: Root directory containing .vibey/ (defaults to cwd)
            calibration_path: Path to calibration YAML (defaults to .vibey/config/token_calibration.yaml)
        """
        self.root_dir = root_dir or Path.cwd()
        self.calibration_path = calibration_path or (self.root_dir / DEFAULT_CALIBRATION_PATH)
        self.data_points: List[CalibrationDataPoint] = []
        self.calibration_data: CalibrationData = CalibrationData()

        # Try to load existing calibration
        if self.calibration_path.exists():
            self.load_calibration()

    def collect_historical_data(self) -> int:
        """
        Collect historical data from completed tasks.

        Scans .vibey/roadmap/tasks/ for completed tasks with token estimates
        and actual usage data.

        Returns:
            Number of data points collected
        """
        tasks_dir = self.root_dir / ".vibey" / "roadmap" / "tasks"
        if not tasks_dir.exists():
            return 0

        self.data_points = []
        collected = 0

        for task_file in tasks_dir.glob("*.yaml"):
            try:
                with open(task_file, "r") as f:
                    task_data = yaml.safe_load(f)

                # Handle nested 'task' key
                if "task" in task_data:
                    task_data = task_data["task"]

                # Only process completed tasks
                status = task_data.get("status", "")
                if status not in ["completed", "production_ready"]:
                    continue

                # Extract token data
                data_point = self._extract_data_point(task_data)
                if data_point:
                    self.data_points.append(data_point)
                    collected += 1

            except Exception as e:
                # Skip tasks that can't be parsed
                continue

        return collected

    def _extract_data_point(self, task_data: Dict[str, Any]) -> Optional[CalibrationDataPoint]:
        """
        Extract calibration data point from a completed task.

        Args:
            task_data: Task dictionary from YAML

        Returns:
            CalibrationDataPoint if valid data exists, None otherwise
        """
        task_id = task_data.get("id", "unknown")
        task_type = task_data.get("task_type", "development")
        complexity = task_data.get("complexity", "medium")

        # Handle enum values
        if hasattr(task_type, "value"):
            task_type = task_type.value
        if hasattr(complexity, "value"):
            complexity = complexity.value

        # Extract input tokens
        input_tokens = task_data.get("input_tokens", {})
        if isinstance(input_tokens, dict):
            input_estimate = input_tokens.get("estimate", {})
            input_estimate_target = None
            if isinstance(input_estimate, dict):
                input_estimate_target = input_estimate.get("target")
            input_usage = input_tokens.get("usage")
        else:
            input_estimate_target = None
            input_usage = None

        # Extract output tokens
        output_tokens = task_data.get("output_tokens", {})
        if isinstance(output_tokens, dict):
            output_estimate = output_tokens.get("estimate", {})
            output_estimate_target = None
            if isinstance(output_estimate, dict):
                output_estimate_target = output_estimate.get("target")
            output_usage = output_tokens.get("usage")
        else:
            output_estimate_target = None
            output_usage = None

        # Need at least some data to be useful
        has_input_data = input_estimate_target and input_usage
        has_output_data = output_estimate_target and output_usage
        if not (has_input_data or has_output_data):
            return None

        # Parse completed timestamp
        completed_str = task_data.get("completed")
        completed_at = None
        if completed_str:
            try:
                if isinstance(completed_str, str):
                    completed_at = datetime.fromisoformat(completed_str.replace("Z", "+00:00"))
                elif isinstance(completed_str, datetime):
                    completed_at = completed_str
            except (ValueError, TypeError):
                pass

        return CalibrationDataPoint(
            task_id=task_id,
            task_type=str(task_type).lower(),
            complexity=str(complexity).lower(),
            input_estimate_target=input_estimate_target,
            input_actual_usage=input_usage,
            output_estimate_target=output_estimate_target,
            output_actual_usage=output_usage,
            completed_at=completed_at,
        )

    def compute_calibration_factors(self) -> Dict[str, CalibrationFactor]:
        """
        Compute calibration factors from collected data points.

        Groups data by task_type + complexity and calculates:
        - Mean accuracy (usage/estimate)
        - Standard deviation
        - Adjustment factor (reciprocal of mean accuracy)

        Returns:
            Dictionary of calibration factors keyed by "task_type:complexity"
        """
        # Group data points by task_type:complexity
        groups: Dict[str, List[CalibrationDataPoint]] = {}
        for dp in self.data_points:
            key = f"{dp.task_type}:{dp.complexity}"
            if key not in groups:
                groups[key] = []
            groups[key].append(dp)

        # Calculate factors for each group
        now = datetime.now(timezone.utc)
        factors: Dict[str, CalibrationFactor] = {}

        for key, points in groups.items():
            task_type, complexity = key.split(":", 1)

            # Collect accuracy ratios
            input_accuracies = [p.input_accuracy for p in points if p.input_accuracy is not None]
            output_accuracies = [p.output_accuracy for p in points if p.output_accuracy is not None]

            # Calculate statistics
            mean_input = statistics.mean(input_accuracies) if input_accuracies else 1.0
            mean_output = statistics.mean(output_accuracies) if output_accuracies else 1.0
            std_input = statistics.stdev(input_accuracies) if len(input_accuracies) > 1 else 0.0
            std_output = statistics.stdev(output_accuracies) if len(output_accuracies) > 1 else 0.0

            # Calculate adjustment factor (inverse of accuracy)
            # If estimates are 80% of actual (accuracy=1.25), multiply by 1.25 to fix
            # Clamp to reasonable bounds [0.25, 4.0]
            input_factor = max(0.25, min(4.0, mean_input))
            output_factor = max(0.25, min(4.0, mean_output))

            factor = CalibrationFactor(
                task_type=task_type,
                complexity=complexity,
                input_factor=input_factor,
                output_factor=output_factor,
                sample_count=len(points),
                mean_input_accuracy=mean_input,
                mean_output_accuracy=mean_output,
                std_dev_input=std_input,
                std_dev_output=std_output,
                last_updated=now,
            )
            factors[key] = factor

        # Update calibration data
        self.calibration_data.factors = factors
        self.calibration_data.total_tasks_analyzed = len(self.data_points)
        self.calibration_data.last_calibration = now

        # Check for alerts
        self._check_for_alerts()

        return factors

    def _check_for_alerts(self) -> None:
        """Check calibration factors for significant estimation errors."""
        alerts = []

        for key, factor in self.calibration_data.factors.items():
            if factor.sample_count < self.MIN_SAMPLES_FOR_ALERT:
                continue

            # Check if estimates are consistently off
            input_off = abs(factor.mean_input_accuracy - 1.0)
            output_off = abs(factor.mean_output_accuracy - 1.0)

            if input_off > self.ACCURACY_ALERT_THRESHOLD:
                direction = "underestimating" if factor.mean_input_accuracy > 1.0 else "overestimating"
                alerts.append(
                    f"Input tokens {direction} by {input_off*100:.0f}% for {key} "
                    f"(n={factor.sample_count})"
                )

            if output_off > self.ACCURACY_ALERT_THRESHOLD:
                direction = "underestimating" if factor.mean_output_accuracy > 1.0 else "overestimating"
                alerts.append(
                    f"Output tokens {direction} by {output_off*100:.0f}% for {key} "
                    f"(n={factor.sample_count})"
                )

        self.calibration_data.alerts = alerts

    def update_from_completed_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Update calibration with a newly completed task.

        Call this after each task completion to enable continuous learning.

        Args:
            task_data: Completed task dictionary

        Returns:
            True if calibration was updated, False otherwise
        """
        data_point = self._extract_data_point(task_data)
        if not data_point:
            return False

        self.data_points.append(data_point)
        self.compute_calibration_factors()
        return True

    def get_calibration_factor(
        self,
        task_type: str,
        complexity: str,
    ) -> Optional[CalibrationFactor]:
        """
        Get calibration factor for a task_type + complexity combination.

        Args:
            task_type: Task type (development, testing, etc.)
            complexity: Complexity level (simple, medium, complex, very_complex)

        Returns:
            CalibrationFactor if available, None otherwise
        """
        key = f"{task_type.lower()}:{complexity.lower()}"
        return self.calibration_data.factors.get(key)

    def get_confidence_boost(self, task_type: str, complexity: str) -> float:
        """
        Get confidence boost based on calibration sample size.

        More historical data = higher confidence in estimates.

        Args:
            task_type: Task type
            complexity: Complexity level

        Returns:
            Confidence boost value (0.0 to 0.2)
        """
        factor = self.get_calibration_factor(task_type, complexity)
        if not factor:
            return 0.0

        # Scale based on sample count (max boost at 20+ samples)
        sample_boost = min(factor.sample_count / 20.0, 1.0) * 0.15

        # Reduce boost if high variance
        variance_penalty = min((factor.std_dev_input + factor.std_dev_output) / 2.0, 0.1)

        return max(0.0, sample_boost - variance_penalty)

    def save_calibration(self, path: Optional[Path] = None) -> None:
        """
        Save calibration data to YAML file.

        Args:
            path: Optional path override (defaults to self.calibration_path)
        """
        path = path or self.calibration_path

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(
                self.calibration_data.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    def load_calibration(self, path: Optional[Path] = None) -> bool:
        """
        Load calibration data from YAML file.

        Args:
            path: Optional path override (defaults to self.calibration_path)

        Returns:
            True if loaded successfully, False otherwise
        """
        path = path or self.calibration_path

        if not path.exists():
            return False

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            self.calibration_data = CalibrationData.from_dict(data)
            return True
        except Exception:
            return False

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of calibration state.

        Returns:
            Dictionary with calibration summary
        """
        return {
            "calibration_path": str(self.calibration_path),
            "total_tasks_analyzed": self.calibration_data.total_tasks_analyzed,
            "last_calibration": (
                self.calibration_data.last_calibration.isoformat()
                if self.calibration_data.last_calibration
                else None
            ),
            "factor_count": len(self.calibration_data.factors),
            "alerts": self.calibration_data.alerts,
            "data_points_in_memory": len(self.data_points),
        }


# =============================================================================
# ESTIMATION RESULT
# =============================================================================


class EstimationResult(BaseModel):
    """
    Result of token estimation for a task.

    Contains separate estimates for input and output tokens, along with
    a confidence score indicating how reliable the estimate is based on
    available data.

    Confidence levels:
    - 0.0-0.3: Low confidence (sparse data, unknown task type)
    - 0.3-0.6: Medium confidence (basic estimation, some uncertainty)
    - 0.6-0.9: Good confidence (well-understood task type and complexity)
    - 0.9-1.0: High confidence (historical data available)
    """

    input_estimate: TokenEstimate = Field(
        description="Estimated tokens for input (context, reading)"
    )
    output_estimate: TokenEstimate = Field(
        description="Estimated tokens for output (generation, writing)"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score 0.0-1.0 based on available data"
    )

    # Metadata about the estimation
    task_type_used: Optional[str] = Field(
        default=None,
        description="Task type used for estimation"
    )
    complexity_used: Optional[str] = Field(
        default=None,
        description="Complexity level used for estimation"
    )
    description_factor: float = Field(
        default=1.0,
        description="Multiplier applied based on description analysis"
    )
    calibration_applied: bool = Field(
        default=False,
        description="Whether historical calibration was applied"
    )
    calibration_input_factor: float = Field(
        default=1.0,
        description="Calibration factor applied to input estimate"
    )
    calibration_output_factor: float = Field(
        default=1.0,
        description="Calibration factor applied to output estimate"
    )
    calibration_sample_count: int = Field(
        default=0,
        description="Number of historical samples used for calibration"
    )

    @property
    def total_estimate(self) -> TokenEstimate:
        """Combined input + output estimate."""
        return TokenEstimate(
            min=(self.input_estimate.min or 0) + (self.output_estimate.min or 0),
            target=(self.input_estimate.target or 0) + (self.output_estimate.target or 0),
            max=(self.input_estimate.max or 0) + (self.output_estimate.max or 0),
        )

    @property
    def confidence_label(self) -> str:
        """Human-readable confidence label."""
        if self.confidence >= 0.9:
            return "high"
        elif self.confidence >= 0.6:
            return "good"
        elif self.confidence >= 0.3:
            return "medium"
        else:
            return "low"


# =============================================================================
# TOKEN ESTIMATOR SERVICE
# =============================================================================


class TokenEstimator:
    """
    Service for estimating token usage based on task characteristics.

    The estimator uses a multi-factor approach:
    1. Base tokens from task type (development, documentation, etc.)
    2. Complexity multipliers (low, medium, high, critical)
    3. Description analysis (length, keyword patterns)
    4. Historical calibration (when CalibrationManager is provided)

    Thread Safety: This class is stateless and thread-safe when no
    CalibrationManager is provided. With a CalibrationManager, thread
    safety depends on the manager's state.
    """

    def __init__(
        self,
        task_type_tokens: Optional[Dict[str, Dict[str, int]]] = None,
        complexity_multipliers: Optional[Dict[str, Dict[str, float]]] = None,
        default_complexity: str = DEFAULT_COMPLEXITY,
        calibration_manager: Optional[CalibrationManager] = None,
    ):
        """
        Initialize the token estimator with optional custom factors.

        Args:
            task_type_tokens: Custom base tokens by task type
            complexity_multipliers: Custom complexity multipliers
            default_complexity: Default complexity when not specified
            calibration_manager: Optional CalibrationManager for historical calibration
        """
        self.task_type_tokens = task_type_tokens or TASK_TYPE_BASE_TOKENS.copy()
        self.complexity_multipliers = complexity_multipliers or COMPLEXITY_MULTIPLIERS.copy()
        self.default_complexity = default_complexity
        self.calibration_manager = calibration_manager

    def estimate_task(self, task: "TaskTicket") -> EstimationResult:
        """
        Estimate tokens for a task based on its type and complexity.

        Extracts task_type and complexity from the task object, then
        delegates to estimate_from_description for the actual calculation.

        Args:
            task: TaskTicket instance to estimate

        Returns:
            EstimationResult with separate input/output estimates
        """
        # Extract task type (handle enum or string)
        task_type = task.task_type
        if hasattr(task_type, 'value'):
            task_type = task_type.value

        # Extract complexity (handle enum or string)
        complexity = getattr(task, 'complexity', None)
        if complexity is None:
            complexity = self.default_complexity
        elif hasattr(complexity, 'value'):
            complexity = complexity.value

        # Get description
        description = getattr(task, 'description', '') or ''

        return self.estimate_from_description(
            description=description,
            task_type=str(task_type),
            complexity=str(complexity),
        )

    def estimate_from_description(
        self,
        description: str,
        task_type: str,
        complexity: str,
    ) -> EstimationResult:
        """
        Estimate tokens from task description and metadata.

        This is the core estimation method that calculates token estimates
        based on:
        - ESTIMATION_PROFILES for base token ranges by task type
        - Complexity multipliers (simple=0.5, medium=1.0, complex=2.0, very_complex=4.0)
        - Description analysis for additional adjustments
        - Historical calibration (when CalibrationManager is provided)

        The estimation algorithm:
        1. Get input/output ranges from ESTIMATION_PROFILES for the task type
        2. Calculate target as midpoint of the range
        3. Apply complexity factor to scale the target
        4. Apply description factor for additional adjustments
        5. Calculate min/max based on complexity-specific variance factors
        6. Apply calibration factors from historical data (if available)

        Args:
            description: Task description text
            task_type: Type of task (development, documentation, etc.)
            complexity: Complexity level (simple, medium, complex, very_complex)

        Returns:
            EstimationResult with confidence score
        """
        # Normalize inputs
        task_type_lower = task_type.lower().strip()
        complexity_lower = complexity.lower().strip()

        # Get estimation profile for task type (uses ESTIMATION_PROFILES)
        profile = ESTIMATION_PROFILES.get(
            task_type_lower,
            DEFAULT_ESTIMATION_PROFILE.copy()
        )

        # Get complexity multipliers
        multipliers = self.complexity_multipliers.get(
            complexity_lower,
            self.complexity_multipliers.get(self.default_complexity, COMPLEXITY_MULTIPLIERS["medium"])
        )

        # Get the complexity factor (simple=0.5, medium=1.0, complex=2.0, very_complex=4.0)
        complexity_factor = multipliers.get("factor", 1.0)

        # Analyze description for additional factors
        description_factor, description_confidence = self._analyze_description(description)

        # Get calibration factors if available
        calibration_applied = False
        calibration_input_factor = 1.0
        calibration_output_factor = 1.0
        calibration_sample_count = 0
        calibration_confidence_boost = 0.0

        if self.calibration_manager:
            cal_factor = self.calibration_manager.get_calibration_factor(
                task_type_lower, complexity_lower
            )
            if cal_factor:
                calibration_applied = True
                calibration_input_factor = cal_factor.input_factor
                calibration_output_factor = cal_factor.output_factor
                calibration_sample_count = cal_factor.sample_count
                calibration_confidence_boost = self.calibration_manager.get_confidence_boost(
                    task_type_lower, complexity_lower
                )

        # Calculate input estimate using the profile ranges
        input_range = profile["input_range"]
        input_base_target = (input_range[0] + input_range[1]) // 2  # Midpoint
        input_target = int(input_base_target * complexity_factor * description_factor * calibration_input_factor)
        # Scale min/max based on complexity variance
        input_min = int(input_target * multipliers["min_factor"])
        input_max = int(input_target * multipliers["max_factor"])
        # Ensure min doesn't go below profile minimum
        input_min = max(input_min, int(input_range[0] * complexity_factor * 0.5))
        input_estimate = TokenEstimate(
            min=input_min,
            target=input_target,
            max=input_max,
        )

        # Calculate output estimate using the profile ranges
        output_range = profile["output_range"]
        output_base_target = (output_range[0] + output_range[1]) // 2  # Midpoint
        output_target = int(output_base_target * complexity_factor * description_factor * calibration_output_factor)
        # Scale min/max based on complexity variance
        output_min = int(output_target * multipliers["min_factor"])
        output_max = int(output_target * multipliers["max_factor"])
        # Ensure min doesn't go below profile minimum
        output_min = max(output_min, int(output_range[0] * complexity_factor * 0.5))
        output_estimate = TokenEstimate(
            min=output_min,
            target=output_target,
            max=output_max,
        )

        # Calculate confidence score
        confidence = self._calculate_confidence(
            task_type=task_type_lower,
            complexity=complexity_lower,
            description=description,
            description_confidence=description_confidence,
        )

        # Add calibration confidence boost
        confidence = min(1.0, confidence + calibration_confidence_boost)

        return EstimationResult(
            input_estimate=input_estimate,
            output_estimate=output_estimate,
            confidence=confidence,
            task_type_used=task_type_lower,
            complexity_used=complexity_lower,
            description_factor=description_factor,
            calibration_applied=calibration_applied,
            calibration_input_factor=calibration_input_factor,
            calibration_output_factor=calibration_output_factor,
            calibration_sample_count=calibration_sample_count,
        )

    def apply_estimates(self, task: Any, result: EstimationResult) -> None:
        """
        Apply estimation result to task.

        Creates Tokens objects with estimates if they don't exist,
        or updates existing estimate fields. This method modifies
        the task in place.

        Args:
            task: Task object to update (must have input_tokens/output_tokens fields)
            result: EstimationResult to apply
        """
        # Apply input estimate
        if task.input_tokens is None:
            task.input_tokens = Tokens(estimate=result.input_estimate)
        else:
            # Create new Tokens with updated estimate (Pydantic models are immutable)
            task.input_tokens = task.input_tokens.model_copy(
                update={"estimate": result.input_estimate}
            )

        # Apply output estimate
        if task.output_tokens is None:
            task.output_tokens = Tokens(estimate=result.output_estimate)
        else:
            task.output_tokens = task.output_tokens.model_copy(
                update={"estimate": result.output_estimate}
            )

    def _analyze_description(self, description: str) -> tuple[float, float]:
        """
        Analyze description to determine additional estimation factors.

        Considers:
        - Description length (longer descriptions → more complex tasks)
        - Keyword patterns (integration, migration, refactor → higher estimates)
        - Code blocks (indicates technical detail)

        Returns:
            Tuple of (multiplier_factor, confidence_contribution)
        """
        if not description:
            return 1.0, 0.0  # No adjustment, no confidence boost

        desc_lower = description.lower()
        factor = 1.0
        confidence = 0.0

        # Length-based adjustment (longer descriptions often mean more work)
        desc_length = len(description)
        if desc_length > 2000:
            factor *= 1.3  # Very detailed description
            confidence += 0.1
        elif desc_length > 1000:
            factor *= 1.15  # Detailed description
            confidence += 0.05
        elif desc_length > 500:
            factor *= 1.05  # Moderate description
            confidence += 0.02
        elif desc_length < 100:
            factor *= 0.9   # Brief description, might be simpler
            confidence -= 0.1

        # Keyword patterns that indicate higher complexity
        high_complexity_keywords = [
            "integration", "migrate", "migration", "refactor", "refactoring",
            "authentication", "authorization", "security", "encryption",
            "database", "schema", "api", "framework", "architecture",
            "performance", "optimization", "scalability", "concurrent",
            "distributed", "microservice", "kubernetes", "docker",
        ]

        keyword_matches = sum(1 for kw in high_complexity_keywords if kw in desc_lower)
        if keyword_matches >= 5:
            factor *= 1.4
            confidence += 0.1
        elif keyword_matches >= 3:
            factor *= 1.2
            confidence += 0.05
        elif keyword_matches >= 1:
            factor *= 1.1
            confidence += 0.02

        # Code blocks indicate technical detail
        if "```" in description:
            factor *= 1.1  # Has code examples
            confidence += 0.05

        # File references indicate scope
        file_extensions = [".py", ".js", ".ts", ".yaml", ".json", ".md"]
        file_matches = sum(1 for ext in file_extensions if ext in desc_lower)
        if file_matches >= 5:
            factor *= 1.2  # Multiple files to modify
            confidence += 0.05
        elif file_matches >= 2:
            factor *= 1.1
            confidence += 0.02

        # Clamp confidence contribution
        confidence = max(-0.2, min(0.3, confidence))

        return factor, confidence

    def _calculate_confidence(
        self,
        task_type: str,
        complexity: str,
        description: str,
        description_confidence: float,
    ) -> float:
        """
        Calculate overall confidence score for the estimate.

        Factors:
        - Known task type: +0.3
        - Known complexity: +0.2
        - Has description: +0.1
        - Description quality: +/- 0.3
        - Base confidence: 0.2

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.2  # Base confidence

        # Known task type (check ESTIMATION_PROFILES)
        if task_type in ESTIMATION_PROFILES:
            confidence += 0.3
        else:
            confidence += 0.1  # Unknown type uses defaults

        # Known complexity
        if complexity in self.complexity_multipliers:
            confidence += 0.2
        else:
            confidence += 0.1  # Unknown complexity uses defaults

        # Has description
        if description and len(description) > 50:
            confidence += 0.1

        # Description quality contribution
        confidence += description_confidence

        # Clamp to valid range
        return max(0.0, min(1.0, confidence))

    def get_supported_task_types(self) -> list[str]:
        """Get list of supported task types from ESTIMATION_PROFILES."""
        return list(ESTIMATION_PROFILES.keys())

    def get_supported_complexities(self) -> list[str]:
        """Get list of supported complexity levels."""
        return list(self.complexity_multipliers.keys())


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def estimate_tokens(
    description: str,
    task_type: str = "development",
    complexity: str = "medium",
) -> EstimationResult:
    """
    Convenience function to estimate tokens without creating an estimator.

    Args:
        description: Task description
        task_type: Type of task
        complexity: Complexity level

    Returns:
        EstimationResult with estimates and confidence
    """
    estimator = TokenEstimator()
    return estimator.estimate_from_description(
        description=description,
        task_type=task_type,
        complexity=complexity,
    )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Main classes
    "TokenEstimator",
    "EstimationResult",
    # Calibration classes
    "CalibrationManager",
    "CalibrationData",
    "CalibrationFactor",
    "CalibrationDataPoint",
    # Convenience functions
    "estimate_tokens",
    # Configuration constants
    "ESTIMATION_PROFILES",
    "TASK_TYPE_BASE_TOKENS",
    "COMPLEXITY_MULTIPLIERS",
    "DEFAULT_BASE_TOKENS",
    "DEFAULT_ESTIMATION_PROFILE",
    "DEFAULT_COMPLEXITY",
    "DEFAULT_CALIBRATION_PATH",
]
