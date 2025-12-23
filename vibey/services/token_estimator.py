"""
Token Estimation Service for the Vibey Agent Framework.

This service provides intelligent token estimation for tasks based on:
- Task type (development, documentation, testing, research, etc.)
- Complexity level (low, medium, high, critical)
- Description analysis (length, keyword patterns)
- Historical data from completed tasks (future enhancement)

The service generates TokenEstimate objects that get wrapped in Tokens
objects on the Ticket model.

Usage:
    from vibey.services.token_estimator import TokenEstimator

    estimator = TokenEstimator()

    # Estimate from task object
    result = estimator.estimate_task(task)
    estimator.apply_estimates(task, result)

    # Estimate from description only
    result = estimator.estimate_from_description(
        description="Implement OAuth2 authentication flow",
        task_type="development",
        complexity="high"
    )

Design Reference: Sprint 2 - Estimation Algorithms
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

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

# Base token estimates by task type (for target, with min/max multipliers)
# These represent typical token counts for medium complexity tasks
TASK_TYPE_BASE_TOKENS: Dict[str, Dict[str, int]] = {
    "development": {
        "input_target": 15000,    # Reading code, understanding context
        "output_target": 8000,    # Writing code, tests, docs
    },
    "documentation": {
        "input_target": 8000,     # Reading existing docs/code
        "output_target": 12000,   # Writing documentation
    },
    "testing": {
        "input_target": 10000,    # Reading code to test
        "output_target": 6000,    # Writing test code
    },
    "research": {
        "input_target": 20000,    # Reading many sources
        "output_target": 5000,    # Summary/recommendations
    },
    "review": {
        "input_target": 12000,    # Reading code to review
        "output_target": 3000,    # Review comments
    },
    "infrastructure": {
        "input_target": 12000,    # Config files, dependencies
        "output_target": 6000,    # Config changes, scripts
    },
    "gate": {
        "input_target": 5000,     # Gate check artifacts
        "output_target": 2000,    # Gate status/report
    },
}

# Complexity multipliers for min/target/max
COMPLEXITY_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "low": {
        "min_factor": 0.5,      # 50% of target for min
        "target_factor": 1.0,   # Base target
        "max_factor": 1.5,      # 150% of target for max
    },
    "medium": {
        "min_factor": 0.6,      # 60% of target for min
        "target_factor": 1.3,   # 30% higher than base
        "max_factor": 2.0,      # 200% of target for max
    },
    "high": {
        "min_factor": 0.7,      # 70% of target for min
        "target_factor": 2.0,   # Double the base
        "max_factor": 3.0,      # 300% of target for max
    },
    "critical": {
        "min_factor": 0.8,      # 80% of target for min
        "target_factor": 3.0,   # Triple the base
        "max_factor": 5.0,      # 500% of target for max
    },
}

# Default values for unknown task types
DEFAULT_BASE_TOKENS: Dict[str, int] = {
    "input_target": 10000,
    "output_target": 5000,
}

# Default complexity when not specified
DEFAULT_COMPLEXITY = "medium"


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
    4. Historical data (future enhancement)

    Thread Safety: This class is stateless and thread-safe.
    """

    def __init__(
        self,
        task_type_tokens: Optional[Dict[str, Dict[str, int]]] = None,
        complexity_multipliers: Optional[Dict[str, Dict[str, float]]] = None,
        default_complexity: str = DEFAULT_COMPLEXITY,
    ):
        """
        Initialize the token estimator with optional custom factors.

        Args:
            task_type_tokens: Custom base tokens by task type
            complexity_multipliers: Custom complexity multipliers
            default_complexity: Default complexity when not specified
        """
        self.task_type_tokens = task_type_tokens or TASK_TYPE_BASE_TOKENS.copy()
        self.complexity_multipliers = complexity_multipliers or COMPLEXITY_MULTIPLIERS.copy()
        self.default_complexity = default_complexity

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
        - Base tokens for the task type
        - Complexity multipliers for min/target/max range
        - Description analysis for additional adjustments

        Args:
            description: Task description text
            task_type: Type of task (development, documentation, etc.)
            complexity: Complexity level (low, medium, high, critical)

        Returns:
            EstimationResult with confidence score
        """
        # Normalize inputs
        task_type_lower = task_type.lower().strip()
        complexity_lower = complexity.lower().strip()

        # Get base tokens for task type
        base_tokens = self.task_type_tokens.get(
            task_type_lower,
            DEFAULT_BASE_TOKENS.copy()
        )

        # Get complexity multipliers
        multipliers = self.complexity_multipliers.get(
            complexity_lower,
            self.complexity_multipliers.get(self.default_complexity, COMPLEXITY_MULTIPLIERS["medium"])
        )

        # Analyze description for additional factors
        description_factor, description_confidence = self._analyze_description(description)

        # Calculate input estimate
        input_target = int(base_tokens["input_target"] * multipliers["target_factor"] * description_factor)
        input_estimate = TokenEstimate(
            min=int(input_target * multipliers["min_factor"]),
            target=input_target,
            max=int(input_target * multipliers["max_factor"]),
        )

        # Calculate output estimate
        output_target = int(base_tokens["output_target"] * multipliers["target_factor"] * description_factor)
        output_estimate = TokenEstimate(
            min=int(output_target * multipliers["min_factor"]),
            target=output_target,
            max=int(output_target * multipliers["max_factor"]),
        )

        # Calculate confidence score
        confidence = self._calculate_confidence(
            task_type=task_type_lower,
            complexity=complexity_lower,
            description=description,
            description_confidence=description_confidence,
        )

        return EstimationResult(
            input_estimate=input_estimate,
            output_estimate=output_estimate,
            confidence=confidence,
            task_type_used=task_type_lower,
            complexity_used=complexity_lower,
            description_factor=description_factor,
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

        # Known task type
        if task_type in self.task_type_tokens:
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
        """Get list of supported task types."""
        return list(self.task_type_tokens.keys())

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
    # Convenience functions
    "estimate_tokens",
    # Configuration constants
    "TASK_TYPE_BASE_TOKENS",
    "COMPLEXITY_MULTIPLIERS",
    "DEFAULT_BASE_TOKENS",
    "DEFAULT_COMPLEXITY",
]
