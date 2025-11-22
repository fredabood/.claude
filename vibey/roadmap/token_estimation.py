"""
Token estimation utilities for roadmap system.

This module provides utilities for estimating, tracking, and analyzing
token usage for AI-assisted development tasks.

Token-Based Effort Estimation
============================

WHY TOKENS INSTEAD OF TIME?
- Token usage is a better predictor of effort than wall time
- Same task may take 5 minutes or 5 hours depending on context window
- Tokens correlate directly with API costs
- Enables budgeting and efficiency tracking

SIZE CATEGORIES (S/M/L/XL/XXL):
- Small (S): <10K tokens - Quick fixes, simple changes
- Medium (M): 10K-30K tokens - Feature additions, moderate refactors
- Large (L): 30K-75K tokens - Complex features, significant changes
- X-Large (XL): 75K-150K tokens - Major features, architectural changes
- XX-Large (XXL): 150K+ tokens - Should be split into multiple tasks

ESTIMATION APPROACH:
1. Use complexity + task type to estimate base tokens
2. Adjust based on description length and keywords
3. Use historical data when available
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models.common import Complexity, SizeCategory


@dataclass
class TokenEstimate:
    """Result of a token estimation."""

    estimated_tokens: int
    size_category: SizeCategory
    confidence: float  # 0.0-1.0
    rationale: str
    factors: Dict[str, int]  # Breakdown of estimate

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "estimated_tokens": self.estimated_tokens,
            "size_category": self.size_category.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "factors": self.factors,
        }


@dataclass
class TokenUsageStats:
    """Statistics about token usage for a sprint/track."""

    total_estimated: int
    total_actual: int
    avg_efficiency: float  # actual/estimated ratio
    tasks_over_estimate: int
    tasks_under_estimate: int
    size_distribution: Dict[str, int]  # Size category -> count


class TokenEstimator:
    """Estimate token usage for tasks based on various factors."""

    # Base token estimates by complexity
    COMPLEXITY_BASE = {
        Complexity.SIMPLE: 5_000,
        Complexity.MEDIUM: 20_000,
        Complexity.COMPLEX: 50_000,
    }

    # Multipliers by task type
    TASK_TYPE_MULTIPLIERS = {
        "development": 1.0,
        "testing": 0.8,  # Tests tend to be more structured
        "documentation": 0.6,  # Docs require less iteration
        "refactoring": 1.2,  # Refactoring often involves more context
        "bug_fix": 0.7,  # Bug fixes are usually focused
        "feature": 1.3,  # Features involve more exploration
        "migration": 1.5,  # Migrations are context-heavy
        "investigation": 0.5,  # Research is reading-heavy
    }

    # Keywords that indicate higher token usage
    HIGH_COMPLEXITY_KEYWORDS = {
        "complex", "refactor", "architecture", "migration", "comprehensive",
        "integrate", "redesign", "overhaul", "major", "system-wide",
    }

    # Keywords that indicate lower token usage
    LOW_COMPLEXITY_KEYWORDS = {
        "simple", "quick", "minor", "small", "trivial", "fix", "update",
        "typo", "rename", "move", "delete", "cleanup",
    }

    def __init__(self, historical_data: Optional[Dict[str, int]] = None):
        """Initialize with optional historical data.

        Args:
            historical_data: Dict mapping task_type to average actual tokens
        """
        self.historical_data = historical_data or {}

    def estimate_from_complexity(self, complexity: Complexity) -> int:
        """Estimate tokens from complexity level."""
        return self.COMPLEXITY_BASE.get(complexity, 20_000)

    def estimate_from_description(self, description: str, title: str = "") -> TokenEstimate:
        """Estimate tokens from task description and title.

        Args:
            description: Task description text
            title: Task title (optional)

        Returns:
            TokenEstimate with estimated tokens and metadata
        """
        combined_text = f"{title} {description}".lower()
        factors = {}

        # Base estimate from text length
        word_count = len(combined_text.split())
        if word_count < 20:
            base_tokens = 5_000
            factors["word_count_factor"] = 5_000
        elif word_count < 50:
            base_tokens = 15_000
            factors["word_count_factor"] = 15_000
        elif word_count < 100:
            base_tokens = 30_000
            factors["word_count_factor"] = 30_000
        else:
            base_tokens = 50_000
            factors["word_count_factor"] = 50_000

        # Adjust for complexity keywords
        high_count = sum(1 for kw in self.HIGH_COMPLEXITY_KEYWORDS if kw in combined_text)
        low_count = sum(1 for kw in self.LOW_COMPLEXITY_KEYWORDS if kw in combined_text)

        keyword_adjustment = (high_count - low_count) * 5_000
        factors["keyword_adjustment"] = keyword_adjustment

        estimated = max(2_000, base_tokens + keyword_adjustment)
        size_category = SizeCategory.from_tokens(estimated)

        # Confidence based on description quality
        confidence = min(0.8, 0.4 + (word_count / 200))

        rationale = f"Based on {word_count} words, {high_count} high-complexity and {low_count} low-complexity keywords"

        return TokenEstimate(
            estimated_tokens=estimated,
            size_category=size_category,
            confidence=confidence,
            rationale=rationale,
            factors=factors,
        )

    def estimate_from_task(
        self,
        title: str,
        description: str,
        complexity: Complexity,
        task_type: str = "development",
    ) -> TokenEstimate:
        """Comprehensive token estimation combining all factors.

        Args:
            title: Task title
            description: Task description
            complexity: Task complexity level
            task_type: Type of task (development, testing, etc.)

        Returns:
            TokenEstimate with estimated tokens and full breakdown
        """
        factors = {}

        # Base from complexity
        complexity_base = self.COMPLEXITY_BASE.get(complexity, 20_000)
        factors["complexity_base"] = complexity_base

        # Task type multiplier
        type_multiplier = self.TASK_TYPE_MULTIPLIERS.get(task_type, 1.0)
        factors["task_type_multiplier"] = int(type_multiplier * 100)

        # Description analysis
        desc_estimate = self.estimate_from_description(description, title)
        factors.update(desc_estimate.factors)

        # Historical adjustment
        historical_avg = self.historical_data.get(task_type)
        if historical_avg:
            historical_factor = historical_avg / 20_000  # Normalize to medium
            factors["historical_adjustment"] = int(historical_avg)
        else:
            historical_factor = 1.0

        # Combine factors
        estimated = int(
            (complexity_base * type_multiplier + desc_estimate.estimated_tokens)
            / 2  # Average complexity and description estimates
            * historical_factor
        )

        # Ensure reasonable bounds
        estimated = max(2_000, min(200_000, estimated))

        size_category = SizeCategory.from_tokens(estimated)

        # Confidence based on available data
        confidence = desc_estimate.confidence
        if historical_avg:
            confidence = min(0.95, confidence + 0.15)

        rationale = (
            f"Complexity: {complexity.value} ({complexity_base:,} base), "
            f"Type: {task_type} ({type_multiplier}x), "
            f"Description analysis: {desc_estimate.rationale}"
        )
        if historical_avg:
            rationale += f", Historical avg: {historical_avg:,}"

        return TokenEstimate(
            estimated_tokens=estimated,
            size_category=size_category,
            confidence=confidence,
            rationale=rationale,
            factors=factors,
        )

    def estimate_sprint_tokens(
        self,
        tasks: List[dict],
    ) -> Tuple[int, Dict[str, int]]:
        """Estimate total tokens for a sprint.

        Args:
            tasks: List of task dictionaries with title, description, complexity, task_type

        Returns:
            Tuple of (total_estimated_tokens, breakdown_by_task_id)
        """
        breakdown = {}
        total = 0

        for task in tasks:
            task_id = task.get("id", "unknown")
            estimate = self.estimate_from_task(
                title=task.get("title", ""),
                description=task.get("description", ""),
                complexity=Complexity(task.get("complexity", "medium")),
                task_type=task.get("task_type", "development"),
            )
            breakdown[task_id] = estimate.estimated_tokens
            total += estimate.estimated_tokens

        return total, breakdown


class TokenTracker:
    """Track actual token usage during execution."""

    def __init__(self):
        """Initialize token tracker."""
        self._usage_log: List[Dict] = []

    def record_usage(
        self,
        task_id: str,
        tokens: int,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Record token usage for a task.

        Args:
            task_id: Task identifier
            tokens: Number of tokens used
            session_id: Optional session identifier
            notes: Optional notes about the usage
        """
        self._usage_log.append({
            "task_id": task_id,
            "tokens": tokens,
            "session_id": session_id,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_task_usage(self, task_id: str) -> int:
        """Get total token usage for a task."""
        return sum(
            entry["tokens"]
            for entry in self._usage_log
            if entry["task_id"] == task_id
        )

    def get_usage_log(self) -> List[Dict]:
        """Get the full usage log."""
        return self._usage_log.copy()

    def calculate_efficiency(
        self,
        task_id: str,
        estimated_tokens: int,
    ) -> Optional[float]:
        """Calculate token efficiency for a task.

        Args:
            task_id: Task identifier
            estimated_tokens: Originally estimated tokens

        Returns:
            Efficiency ratio (actual/estimated), or None if no usage recorded
        """
        actual = self.get_task_usage(task_id)
        if actual == 0 or estimated_tokens == 0:
            return None
        return actual / estimated_tokens


def convert_time_to_tokens(duration_str: str) -> int:
    """Convert a time-based estimate to tokens.

    Assumes approximately 10K tokens per hour for AI-assisted development.

    Args:
        duration_str: Time estimate like "2 hours", "1-2 weeks", etc.

    Returns:
        Estimated tokens
    """
    duration_lower = duration_str.lower().strip()

    # Extract number
    import re
    numbers = re.findall(r"[\d.]+", duration_lower)
    if not numbers:
        return 20_000  # Default to medium

    # Take average if range (e.g., "1-2 hours" -> 1.5)
    if len(numbers) >= 2:
        value = (float(numbers[0]) + float(numbers[1])) / 2
    else:
        value = float(numbers[0])

    # Determine unit and convert to hours
    if "minute" in duration_lower:
        hours = value / 60
    elif "hour" in duration_lower:
        hours = value
    elif "day" in duration_lower:
        hours = value * 6  # ~6 productive hours per day
    elif "week" in duration_lower:
        hours = value * 30  # ~30 productive hours per week
    elif "month" in duration_lower:
        hours = value * 120  # ~120 productive hours per month
    else:
        hours = value  # Assume hours if no unit

    # 10K tokens per hour estimate
    tokens = int(hours * 10_000)

    # Apply reasonable bounds
    return max(2_000, min(500_000, tokens))


def categorize_by_tokens(tokens: int) -> str:
    """Get human-readable size category from token count.

    Args:
        tokens: Number of tokens

    Returns:
        Size category string (S/M/L/XL/XXL)
    """
    return SizeCategory.from_tokens(tokens).value


def get_token_budget_recommendation(sprint_tasks: int) -> int:
    """Get recommended token budget for a sprint.

    Args:
        sprint_tasks: Number of tasks in the sprint

    Returns:
        Recommended token budget
    """
    # Base: 20K per task (medium estimate)
    # Plus 20% overhead for context and iterations
    base = sprint_tasks * 20_000
    overhead = int(base * 0.2)
    return base + overhead


def analyze_token_efficiency(
    tasks: List[Dict],
) -> TokenUsageStats:
    """Analyze token efficiency across tasks.

    Args:
        tasks: List of task dicts with estimated_tokens and actual_tokens

    Returns:
        TokenUsageStats with analysis results
    """
    total_estimated = 0
    total_actual = 0
    over_count = 0
    under_count = 0
    size_dist: Dict[str, int] = {cat.value: 0 for cat in SizeCategory}
    efficiencies = []

    for task in tasks:
        estimated = task.get("estimated_tokens", 0)
        actual = task.get("actual_tokens")

        if estimated > 0:
            total_estimated += estimated
            size = SizeCategory.from_tokens(estimated)
            size_dist[size.value] += 1

        if actual is not None and actual > 0:
            total_actual += actual
            if estimated > 0:
                efficiency = actual / estimated
                efficiencies.append(efficiency)
                if actual > estimated:
                    over_count += 1
                else:
                    under_count += 1

    avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 1.0

    return TokenUsageStats(
        total_estimated=total_estimated,
        total_actual=total_actual,
        avg_efficiency=avg_efficiency,
        tasks_over_estimate=over_count,
        tasks_under_estimate=under_count,
        size_distribution=size_dist,
    )
