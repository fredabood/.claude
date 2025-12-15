"""
Tests for vibey.roadmap.token_estimation module.

Tests token estimation and tracking utilities.
"""

import pytest
from datetime import datetime, timezone

from vibey.roadmap.token_estimation import (
    TokenEstimate,
    TokenUsageStats,
    TokenEstimator,
    TokenTracker,
    convert_time_to_tokens,
    categorize_by_tokens,
    get_token_budget_recommendation,
    analyze_token_efficiency,
)
from vibey.roadmap.models.common import Complexity, SizeCategory


class TestTokenEstimate:
    """Test TokenEstimate dataclass."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        estimate = TokenEstimate(
            estimated_tokens=20000,
            size_category=SizeCategory.MEDIUM,
            confidence=0.8,
            rationale="Test rationale",
            factors={"base": 10000, "adjustment": 10000},
        )
        d = estimate.to_dict()
        assert d["estimated_tokens"] == 20000
        assert d["size_category"] == "M"
        assert d["confidence"] == 0.8
        assert d["rationale"] == "Test rationale"
        assert d["factors"]["base"] == 10000


class TestTokenEstimator:
    """Test TokenEstimator class."""

    @pytest.fixture
    def estimator(self):
        """Create a TokenEstimator instance."""
        return TokenEstimator()

    def test_estimate_from_complexity_simple(self, estimator):
        """Test estimate for simple complexity."""
        tokens = estimator.estimate_from_complexity(Complexity.SIMPLE)
        assert tokens == 5000

    def test_estimate_from_complexity_medium(self, estimator):
        """Test estimate for medium complexity."""
        tokens = estimator.estimate_from_complexity(Complexity.MEDIUM)
        assert tokens == 20000

    def test_estimate_from_complexity_complex(self, estimator):
        """Test estimate for complex complexity."""
        tokens = estimator.estimate_from_complexity(Complexity.COMPLEX)
        assert tokens == 50000

    def test_estimate_from_short_description(self, estimator):
        """Test estimate from short description."""
        estimate = estimator.estimate_from_description("Fix a bug")
        assert estimate.estimated_tokens > 0
        assert estimate.confidence < 0.6

    def test_estimate_from_long_description(self, estimator):
        """Test estimate from long description."""
        long_desc = " ".join(["word"] * 100)
        estimate = estimator.estimate_from_description(long_desc)
        assert estimate.estimated_tokens >= 30000

    def test_high_complexity_keywords_increase_estimate(self, estimator):
        """Test high complexity keywords increase estimate."""
        simple = estimator.estimate_from_description("simple update")
        complex_desc = estimator.estimate_from_description(
            "major refactor architecture redesign"
        )
        assert complex_desc.estimated_tokens > simple.estimated_tokens

    def test_low_complexity_keywords_decrease_estimate(self, estimator):
        """Test low complexity keywords decrease estimate."""
        base = estimator.estimate_from_description("implement feature")
        simple = estimator.estimate_from_description("simple minor fix typo cleanup")
        assert simple.estimated_tokens < base.estimated_tokens

    def test_estimate_from_task(self, estimator):
        """Test comprehensive task estimation."""
        estimate = estimator.estimate_from_task(
            title="Add user authentication",
            description="Implement OAuth2 login with Google and GitHub providers",
            complexity=Complexity.COMPLEX,
            task_type="feature",
        )
        assert estimate.estimated_tokens > 0
        assert estimate.size_category is not None
        assert "complexity_base" in estimate.factors

    def test_task_type_multiplier_testing(self, estimator):
        """Test testing task type has lower multiplier."""
        dev = estimator.estimate_from_task(
            title="Implement feature",
            description="Add new functionality",
            complexity=Complexity.MEDIUM,
            task_type="development",
        )
        test = estimator.estimate_from_task(
            title="Implement feature",
            description="Add new functionality",
            complexity=Complexity.MEDIUM,
            task_type="testing",
        )
        # Testing typically requires fewer tokens
        assert test.estimated_tokens < dev.estimated_tokens

    def test_historical_data_adjustment(self):
        """Test historical data affects estimates."""
        estimator_with_history = TokenEstimator(
            historical_data={"development": 40000}
        )
        estimate = estimator_with_history.estimate_from_task(
            title="Task",
            description="Description",
            complexity=Complexity.MEDIUM,
            task_type="development",
        )
        assert estimate.confidence > 0.5  # Higher confidence with historical data

    def test_estimate_sprint_tokens(self, estimator):
        """Test estimating sprint tokens."""
        tasks = [
            {
                "id": "task-001",
                "title": "Task 1",
                "description": "Simple task",
                "complexity": "simple",
                "task_type": "development",
            },
            {
                "id": "task-002",
                "title": "Task 2",
                "description": "Medium task",
                "complexity": "medium",
                "task_type": "testing",
            },
        ]
        total, breakdown = estimator.estimate_sprint_tokens(tasks)
        assert total > 0
        assert "task-001" in breakdown
        assert "task-002" in breakdown
        assert breakdown["task-001"] + breakdown["task-002"] == total


class TestTokenTracker:
    """Test TokenTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create a TokenTracker instance."""
        return TokenTracker()

    def test_record_usage(self, tracker):
        """Test recording token usage."""
        tracker.record_usage("task-001", 5000)
        assert tracker.get_task_usage("task-001") == 5000

    def test_record_multiple_usages(self, tracker):
        """Test recording multiple usages for same task."""
        tracker.record_usage("task-001", 5000)
        tracker.record_usage("task-001", 3000)
        assert tracker.get_task_usage("task-001") == 8000

    def test_record_with_session(self, tracker):
        """Test recording with session ID."""
        tracker.record_usage("task-001", 5000, session_id="session-1")
        log = tracker.get_usage_log()
        assert log[0]["session_id"] == "session-1"

    def test_record_with_notes(self, tracker):
        """Test recording with notes."""
        tracker.record_usage("task-001", 5000, notes="Initial pass")
        log = tracker.get_usage_log()
        assert log[0]["notes"] == "Initial pass"

    def test_get_task_usage_no_usage(self, tracker):
        """Test getting usage for task with no records."""
        assert tracker.get_task_usage("nonexistent") == 0

    def test_get_usage_log(self, tracker):
        """Test getting usage log."""
        tracker.record_usage("task-001", 5000)
        tracker.record_usage("task-002", 3000)
        log = tracker.get_usage_log()
        assert len(log) == 2
        assert log[0]["task_id"] == "task-001"

    def test_calculate_efficiency_normal(self, tracker):
        """Test calculating efficiency."""
        tracker.record_usage("task-001", 8000)
        efficiency = tracker.calculate_efficiency("task-001", 10000)
        assert efficiency == 0.8

    def test_calculate_efficiency_over_estimate(self, tracker):
        """Test calculating efficiency over estimate."""
        tracker.record_usage("task-001", 15000)
        efficiency = tracker.calculate_efficiency("task-001", 10000)
        assert efficiency == 1.5

    def test_calculate_efficiency_no_usage(self, tracker):
        """Test calculating efficiency with no usage."""
        efficiency = tracker.calculate_efficiency("task-001", 10000)
        assert efficiency is None

    def test_calculate_efficiency_zero_estimate(self, tracker):
        """Test calculating efficiency with zero estimate."""
        tracker.record_usage("task-001", 5000)
        efficiency = tracker.calculate_efficiency("task-001", 0)
        assert efficiency is None


class TestConvertTimeToTokens:
    """Test convert_time_to_tokens function."""

    def test_minutes(self):
        """Test converting minutes."""
        tokens = convert_time_to_tokens("30 minutes")
        assert 4000 <= tokens <= 6000  # ~5K for 30 min

    def test_hours(self):
        """Test converting hours."""
        tokens = convert_time_to_tokens("2 hours")
        assert 18000 <= tokens <= 22000  # ~20K for 2 hours

    def test_days(self):
        """Test converting days."""
        tokens = convert_time_to_tokens("1 day")
        assert 50000 <= tokens <= 70000  # ~60K for 1 day

    def test_weeks(self):
        """Test converting weeks."""
        tokens = convert_time_to_tokens("1 week")
        assert 250000 <= tokens <= 350000  # ~300K for 1 week

    def test_range(self):
        """Test converting time range."""
        tokens = convert_time_to_tokens("1-2 hours")
        # Average of 1 and 2 hours = 1.5 hours
        assert 13000 <= tokens <= 17000

    def test_no_unit(self):
        """Test with no unit assumes hours."""
        tokens = convert_time_to_tokens("2")
        assert 18000 <= tokens <= 22000

    def test_no_number(self):
        """Test with no number defaults to medium."""
        tokens = convert_time_to_tokens("sometime")
        assert tokens == 20000


class TestCategorizeByTokens:
    """Test categorize_by_tokens function."""

    def test_small(self):
        """Test small category."""
        assert categorize_by_tokens(5000) == "S"

    def test_medium(self):
        """Test medium category."""
        assert categorize_by_tokens(20000) == "M"

    def test_large(self):
        """Test large category."""
        assert categorize_by_tokens(50000) == "L"

    def test_xlarge(self):
        """Test x-large category."""
        assert categorize_by_tokens(100000) == "XL"

    def test_xxlarge(self):
        """Test xx-large category."""
        assert categorize_by_tokens(200000) == "XXL"


class TestGetTokenBudgetRecommendation:
    """Test get_token_budget_recommendation function."""

    def test_single_task(self):
        """Test budget for single task."""
        budget = get_token_budget_recommendation(1)
        # 20K base + 20% overhead = 24K
        assert budget == 24000

    def test_multiple_tasks(self):
        """Test budget for multiple tasks."""
        budget = get_token_budget_recommendation(5)
        # 100K base + 20% overhead = 120K
        assert budget == 120000

    def test_zero_tasks(self):
        """Test budget for zero tasks."""
        budget = get_token_budget_recommendation(0)
        assert budget == 0


class TestAnalyzeTokenEfficiency:
    """Test analyze_token_efficiency function."""

    def test_with_complete_data(self):
        """Test analysis with complete data."""
        tasks = [
            {"estimated_tokens": 10000, "actual_tokens": 8000},
            {"estimated_tokens": 20000, "actual_tokens": 25000},
            {"estimated_tokens": 15000, "actual_tokens": 15000},
        ]
        stats = analyze_token_efficiency(tasks)
        assert stats.total_estimated == 45000
        assert stats.total_actual == 48000
        assert stats.tasks_over_estimate == 1
        assert stats.tasks_under_estimate == 2

    def test_with_missing_actual(self):
        """Test analysis with missing actual tokens."""
        tasks = [
            {"estimated_tokens": 10000, "actual_tokens": 8000},
            {"estimated_tokens": 20000, "actual_tokens": None},
        ]
        stats = analyze_token_efficiency(tasks)
        assert stats.total_estimated == 30000
        assert stats.total_actual == 8000

    def test_empty_tasks(self):
        """Test analysis with no tasks."""
        stats = analyze_token_efficiency([])
        assert stats.total_estimated == 0
        assert stats.total_actual == 0
        assert stats.avg_efficiency == 1.0

    def test_size_distribution(self):
        """Test size distribution is calculated."""
        tasks = [
            {"estimated_tokens": 5000},  # Small
            {"estimated_tokens": 20000},  # Medium
            {"estimated_tokens": 50000},  # Large
        ]
        stats = analyze_token_efficiency(tasks)
        assert stats.size_distribution["S"] == 1
        assert stats.size_distribution["M"] == 1
        assert stats.size_distribution["L"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
