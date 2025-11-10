"""
Unit tests for MetricsCollector test utility.

Tests the functionality of tracking and validating success metrics.
"""

import pytest
from pathlib import Path
from tests.utils import MetricsCollector, Metric
import json


@pytest.mark.unit
class TestMetricsCollector:
    """Test MetricsCollector utility."""

    def test_init(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        assert len(collector.metrics) == 0

    def test_track_metric(self):
        """Test tracking a metric."""
        collector = MetricsCollector()
        collector.track("test_metric", 100, unit="count")

        assert "test_metric" in collector.metrics
        metric = collector.get_metric("test_metric")
        assert metric.value == 100
        assert metric.unit == "count"

    def test_track_multiple_metrics(self):
        """Test tracking multiple metrics."""
        collector = MetricsCollector()
        collector.track("metric1", 100)
        collector.track("metric2", 200)
        collector.track("metric3", 300)

        assert len(collector.metrics) == 3

    def test_get_metric(self):
        """Test retrieving a metric."""
        collector = MetricsCollector()
        collector.track("test", 42)

        metric = collector.get_metric("test")
        assert metric is not None
        assert metric.value == 42

    def test_get_nonexistent_metric(self):
        """Test retrieving nonexistent metric returns None."""
        collector = MetricsCollector()
        metric = collector.get_metric("missing")
        assert metric is None

    def test_get_all_metrics(self):
        """Test retrieving all metrics."""
        collector = MetricsCollector()
        collector.track("m1", 1)
        collector.track("m2", 2)

        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) == 2
        assert "m1" in all_metrics
        assert "m2" in all_metrics

    def test_track_with_threshold(self):
        """Test tracking metric with threshold."""
        collector = MetricsCollector()
        collector.track("coverage", 95, unit="percentage", threshold=90)

        metric = collector.get_metric("coverage")
        assert metric.threshold == 90
        assert metric.meets_threshold()

    def test_metric_meets_threshold_true(self):
        """Test metric meets threshold."""
        metric = Metric("test", 100, threshold=90)
        assert metric.meets_threshold()

    def test_metric_meets_threshold_false(self):
        """Test metric does not meet threshold."""
        metric = Metric("test", 80, threshold=90)
        assert not metric.meets_threshold()

    def test_metric_no_threshold(self):
        """Test metric with no threshold always passes."""
        metric = Metric("test", 50)
        assert metric.meets_threshold()

    def test_assert_metric_exact_value(self):
        """Test asserting exact metric value."""
        collector = MetricsCollector()
        collector.track("count", 42)

        assert collector.assert_metric("count", expected_value=42)
        assert not collector.assert_metric("count", expected_value=43)

    def test_assert_metric_min_value(self):
        """Test asserting minimum metric value."""
        collector = MetricsCollector()
        collector.track("score", 85)

        assert collector.assert_metric("score", min_value=80)
        assert not collector.assert_metric("score", min_value=90)

    def test_assert_metric_max_value(self):
        """Test asserting maximum metric value."""
        collector = MetricsCollector()
        collector.track("time", 45)

        assert collector.assert_metric("time", max_value=60)
        assert not collector.assert_metric("time", max_value=30)

    def test_assert_metric_range(self):
        """Test asserting metric within range."""
        collector = MetricsCollector()
        collector.track("value", 50)

        assert collector.assert_metric("value", min_value=40, max_value=60)
        assert not collector.assert_metric("value", min_value=60, max_value=80)

    def test_assert_nonexistent_metric(self):
        """Test asserting nonexistent metric returns False."""
        collector = MetricsCollector()
        assert not collector.assert_metric("missing", expected_value=100)

    def test_export_metrics(self, temp_dir):
        """Test exporting metrics to JSON."""
        collector = MetricsCollector()
        collector.track("m1", 100, unit="count", threshold=90)
        collector.track("m2", 80, unit="percent", threshold=85)

        output_file = temp_dir / "metrics.json"
        export_data = collector.export_metrics(output_file)

        assert output_file.exists()
        assert "metrics" in export_data
        assert "m1" in export_data["metrics"]
        assert "m2" in export_data["metrics"]

        # Verify file content
        with open(output_file) as f:
            data = json.load(f)
        assert data["metrics"]["m1"]["value"] == 100
        assert data["metrics"]["m1"]["meets_threshold"] is True
        assert data["metrics"]["m2"]["meets_threshold"] is False

    def test_export_metrics_without_file(self):
        """Test exporting metrics without writing to file."""
        collector = MetricsCollector()
        collector.track("test", 42)

        export_data = collector.export_metrics()

        assert "metrics" in export_data
        assert "test" in export_data["metrics"]

    def test_calculate_success_rate_all_pass(self):
        """Test success rate calculation when all pass."""
        collector = MetricsCollector()
        collector.track("m1", 95, threshold=90)
        collector.track("m2", 100, threshold=90)
        collector.track("m3", 92, threshold=90)

        success_rate = collector.calculate_success_rate()
        assert success_rate == 100.0

    def test_calculate_success_rate_some_fail(self):
        """Test success rate calculation with failures."""
        collector = MetricsCollector()
        collector.track("m1", 95, threshold=90)  # Pass
        collector.track("m2", 80, threshold=90)  # Fail
        collector.track("m3", 92, threshold=90)  # Pass

        success_rate = collector.calculate_success_rate()
        assert success_rate == pytest.approx(66.67, 0.01)

    def test_calculate_success_rate_no_thresholds(self):
        """Test success rate is 100% when no thresholds."""
        collector = MetricsCollector()
        collector.track("m1", 100)
        collector.track("m2", 200)

        success_rate = collector.calculate_success_rate()
        assert success_rate == 100.0

    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()
        collector.track("m1", 100)
        collector.track("m2", 200)

        assert len(collector.metrics) == 2

        collector.reset()

        assert len(collector.metrics) == 0

    def test_metric_with_string_value(self):
        """Test tracking metric with string value."""
        collector = MetricsCollector()
        collector.track("status", "passed", unit="state")

        metric = collector.get_metric("status")
        assert metric.value == "passed"
        assert metric.unit == "state"

    def test_track_overwrites_existing_metric(self):
        """Test tracking same metric name overwrites previous."""
        collector = MetricsCollector()
        collector.track("count", 10)
        collector.track("count", 20)

        metric = collector.get_metric("count")
        assert metric.value == 20
