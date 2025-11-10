"""
Metrics collector utility for tracking test success metrics.

This module provides tools for collecting, tracking, and validating
success metrics during testing.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Metric:
    """Represents a tracked metric."""

    name: str
    value: Any
    unit: Optional[str] = None
    threshold: Optional[float] = None

    def meets_threshold(self) -> bool:
        """Check if metric meets threshold."""
        if self.threshold is None:
            return True

        try:
            return float(self.value) >= self.threshold
        except (ValueError, TypeError):
            return False


class MetricsCollector:
    """
    Collect and track success metrics.

    This class provides methods to track metrics, validate thresholds,
    and export results for reporting.
    """

    def __init__(self):
        """Initialize MetricsCollector."""
        self.metrics: Dict[str, Metric] = {}

    def track(
        self,
        name: str,
        value: Any,
        unit: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> None:
        """
        Track a metric value.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement (optional)
            threshold: Minimum acceptable value (optional)
        """
        self.metrics[name] = Metric(
            name=name,
            value=value,
            unit=unit,
            threshold=threshold
        )

    def get_metric(self, name: str) -> Optional[Metric]:
        """
        Get a tracked metric.

        Args:
            name: Metric name

        Returns:
            Metric object or None if not found
        """
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """
        Get all tracked metrics.

        Returns:
            Dictionary of all metrics
        """
        return self.metrics.copy()

    def assert_metric(
        self,
        name: str,
        expected_value: Optional[Any] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> bool:
        """
        Assert metric meets expectations.

        Args:
            name: Metric name
            expected_value: Exact expected value (optional)
            min_value: Minimum acceptable value (optional)
            max_value: Maximum acceptable value (optional)

        Returns:
            True if assertions pass, False otherwise
        """
        metric = self.get_metric(name)
        if metric is None:
            return False

        if expected_value is not None:
            if metric.value != expected_value:
                return False

        if min_value is not None:
            try:
                if float(metric.value) < min_value:
                    return False
            except (ValueError, TypeError):
                return False

        if max_value is not None:
            try:
                if float(metric.value) > max_value:
                    return False
            except (ValueError, TypeError):
                return False

        return True

    def export_metrics(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export metrics to JSON format.

        Args:
            output_path: Path to write JSON file (optional)

        Returns:
            Dictionary of metrics
        """
        export_data = {
            "metrics": {
                name: {
                    "value": metric.value,
                    "unit": metric.unit,
                    "threshold": metric.threshold,
                    "meets_threshold": metric.meets_threshold()
                }
                for name, metric in self.metrics.items()
            }
        }

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)

        return export_data

    def calculate_success_rate(self) -> float:
        """
        Calculate overall success rate based on threshold metrics.

        Returns:
            Success rate as percentage (0-100)
        """
        threshold_metrics = [
            m for m in self.metrics.values() if m.threshold is not None
        ]

        if not threshold_metrics:
            return 100.0

        passed = sum(1 for m in threshold_metrics if m.meets_threshold())
        return (passed / len(threshold_metrics)) * 100

    def reset(self) -> None:
        """Reset all tracked metrics."""
        self.metrics.clear()
