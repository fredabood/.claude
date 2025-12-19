"""
Token Budget Enforcement for Context System V2.

This module provides token budget management to prevent loading too much
context when working with AI assistants. It includes:

- TokenBudget: Configuration for max tokens and thresholds
- TokenUsageTracker: Tracks current usage across context phases
- Estimation functions for files and text
- Prioritization logic for artifact selection within budget

Task: 01KCMGX8J70XCDJH51SYHVC6H4
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# TOKEN BUDGET CONFIGURATION
# =============================================================================


@dataclass
class TokenBudget:
    """Token budget configuration.

    Defines limits for context loading to prevent exceeding
    AI model context windows.

    Attributes:
        max_tokens: Maximum total tokens allowed for context
        reserved_tokens: Tokens reserved for AI response generation
        warning_threshold: Percentage at which to warn about high usage
        plan_budget_percent: Max percentage for plan context
        runtime_budget_percent: Max percentage for runtime context
        artifacts_budget_percent: Max percentage for artifact loading
    """

    max_tokens: int = 100000  # Default max tokens (GPT-4 style)
    reserved_tokens: int = 10000  # Reserved for AI response
    warning_threshold: float = 0.8  # Warn at 80% usage
    plan_budget_percent: float = 0.20  # 20% for plan context
    runtime_budget_percent: float = 0.15  # 15% for runtime context
    artifacts_budget_percent: float = 0.50  # 50% for artifacts/files

    @property
    def available_tokens(self) -> int:
        """Tokens available for context (after reserving response tokens)."""
        return self.max_tokens - self.reserved_tokens

    @property
    def plan_budget(self) -> int:
        """Tokens allocated for plan context."""
        return int(self.available_tokens * self.plan_budget_percent)

    @property
    def runtime_budget(self) -> int:
        """Tokens allocated for runtime context."""
        return int(self.available_tokens * self.runtime_budget_percent)

    @property
    def artifacts_budget(self) -> int:
        """Tokens allocated for artifacts."""
        return int(self.available_tokens * self.artifacts_budget_percent)


# =============================================================================
# TOKEN USAGE TRACKING
# =============================================================================


@dataclass
class TokenUsageTracker:
    """Tracks current token usage across context phases.

    Provides real-time tracking of token consumption for:
    - Plan context (goals, approach, constraints)
    - Runtime context (decisions, discoveries, blockers)
    - Loaded artifacts (files, documents, code)
    """

    plan_context: int = 0
    runtime_context: int = 0
    artifacts_loaded: int = 0
    system_prompt: int = 0

    # Track individual artifact usage for reporting
    artifact_breakdown: Dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Total tokens used across all categories."""
        return (
            self.plan_context
            + self.runtime_context
            + self.artifacts_loaded
            + self.system_prompt
        )

    def is_over_budget(self, budget: TokenBudget) -> bool:
        """Check if current usage exceeds budget."""
        return self.total > budget.available_tokens

    def add_artifact(self, artifact_id: str, tokens: int) -> None:
        """Track tokens for a specific artifact."""
        self.artifact_breakdown[artifact_id] = tokens
        self.artifacts_loaded += tokens

    def remove_artifact(self, artifact_id: str) -> None:
        """Remove an artifact from tracking."""
        if artifact_id in self.artifact_breakdown:
            self.artifacts_loaded -= self.artifact_breakdown[artifact_id]
            del self.artifact_breakdown[artifact_id]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan_context": self.plan_context,
            "runtime_context": self.runtime_context,
            "artifacts_loaded": self.artifacts_loaded,
            "system_prompt": self.system_prompt,
            "total": self.total,
            "artifact_count": len(self.artifact_breakdown),
        }


# =============================================================================
# TOKEN ESTIMATION FUNCTIONS
# =============================================================================


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses a rough heuristic of ~4 characters per token, which is
    a reasonable approximation for English text and code.

    For more accurate estimation, consider using tiktoken or
    the specific tokenizer for your target model.

    Args:
        text: The text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Rough estimate: ~4 chars per token for English/code
    # This is conservative - actual may be fewer tokens
    return max(1, len(text) // 4)


def estimate_file_tokens(file_path: Path) -> int:
    """Estimate tokens for a file.

    Reads the file and estimates token count.
    Returns 0 if file doesn't exist or can't be read.

    Args:
        file_path: Path to the file

    Returns:
        Estimated token count, or 0 if file can't be read
    """
    try:
        if not file_path.exists():
            return 0
        if not file_path.is_file():
            return 0

        # Check file size first - skip very large files
        file_size = file_path.stat().st_size
        if file_size > 10_000_000:  # 10MB limit
            return file_size // 4  # Estimate without reading

        content = file_path.read_text(encoding="utf-8", errors="replace")
        return estimate_tokens(content)
    except (OSError, IOError, PermissionError):
        return 0


def estimate_yaml_tokens(data: Dict[str, Any]) -> int:
    """Estimate tokens for a YAML-serializable data structure.

    Converts the data to YAML format and estimates tokens.
    Useful for estimating context model sizes.

    Args:
        data: Dictionary to estimate

    Returns:
        Estimated token count
    """
    import yaml
    try:
        yaml_text = yaml.dump(data, default_flow_style=False)
        return estimate_tokens(yaml_text)
    except Exception:
        # Fallback: estimate based on string representation
        return estimate_tokens(str(data))


# =============================================================================
# BUDGET CHECKING
# =============================================================================


@dataclass
class BudgetCheckResult:
    """Result of a budget check operation."""

    within_budget: bool
    remaining_tokens: int
    usage_percent: float
    warning: bool
    message: str
    breakdown: Dict[str, int] = field(default_factory=dict)


def check_budget(
    usage: TokenUsageTracker,
    budget: TokenBudget,
) -> BudgetCheckResult:
    """Check if current usage is within budget.

    Returns detailed information about budget status including
    whether usage is within limits, remaining tokens, and warnings.

    Args:
        usage: Current token usage tracker
        budget: Token budget configuration

    Returns:
        BudgetCheckResult with status and details
    """
    remaining = budget.available_tokens - usage.total
    usage_percent = usage.total / budget.available_tokens if budget.available_tokens > 0 else 1.0
    warning = usage_percent > budget.warning_threshold
    within_budget = remaining > 0

    # Generate appropriate message
    if not within_budget:
        message = f"Over budget by {abs(remaining):,} tokens ({usage_percent:.1%} of limit)"
    elif warning:
        message = f"Warning: {usage_percent:.1%} of budget used, {remaining:,} tokens remaining"
    else:
        message = f"Within budget: {remaining:,} tokens remaining ({usage_percent:.1%} used)"

    return BudgetCheckResult(
        within_budget=within_budget,
        remaining_tokens=remaining,
        usage_percent=usage_percent,
        warning=warning,
        message=message,
        breakdown={
            "plan_context": usage.plan_context,
            "runtime_context": usage.runtime_context,
            "artifacts_loaded": usage.artifacts_loaded,
            "system_prompt": usage.system_prompt,
            "total": usage.total,
            "available": budget.available_tokens,
            "max_tokens": budget.max_tokens,
            "reserved": budget.reserved_tokens,
        },
    )


def can_load_artifact(
    artifact_tokens: int,
    usage: TokenUsageTracker,
    budget: TokenBudget,
) -> bool:
    """Check if an artifact can be loaded within budget.

    Args:
        artifact_tokens: Token count for the artifact to load
        usage: Current token usage
        budget: Token budget configuration

    Returns:
        True if artifact can be loaded within budget
    """
    projected_total = usage.total + artifact_tokens
    return projected_total <= budget.available_tokens


# =============================================================================
# ARTIFACT PRIORITIZATION
# =============================================================================


def prioritize_artifacts(
    artifacts: List[Dict[str, Any]],
    available_tokens: int,
) -> List[Dict[str, Any]]:
    """Prioritize artifacts to fit within token budget.

    Selects artifacts based on priority order:
    1. Required artifacts (must be loaded)
    2. Recently accessed artifacts
    3. Smaller token cost (fit more artifacts)

    Args:
        artifacts: List of artifact dicts with keys:
            - tokens_estimate: int - estimated tokens
            - required: bool - if artifact is required
            - last_accessed: float - timestamp of last access
            - artifact_id: str - unique identifier
        available_tokens: Maximum tokens to use

    Returns:
        List of artifacts that fit within budget, in priority order
    """
    if not artifacts:
        return []

    # Sort by priority:
    # 1. Required first (not a.get("required") puts required at front when sorted)
    # 2. Most recently accessed next (negative last_accessed for descending)
    # 3. Smaller files next (lower token count is better)
    sorted_artifacts = sorted(
        artifacts,
        key=lambda a: (
            not a.get("required", False),
            -a.get("last_accessed", 0),
            a.get("tokens_estimate", 0),
        )
    )

    selected = []
    total_tokens = 0

    for artifact in sorted_artifacts:
        tokens = artifact.get("tokens_estimate", 0)

        # Always include required artifacts even if over budget
        if artifact.get("required", False):
            selected.append(artifact)
            total_tokens += tokens
            continue

        # Include if within budget
        if total_tokens + tokens <= available_tokens:
            selected.append(artifact)
            total_tokens += tokens

    return selected


def calculate_artifact_priority_score(artifact: Dict[str, Any]) -> float:
    """Calculate a priority score for an artifact.

    Higher scores indicate higher priority for loading.

    Scoring factors:
    - Required: +1000 (always load)
    - Recency: scaled 0-100 based on last access
    - Size penalty: -0.001 per token (prefer smaller)

    Args:
        artifact: Artifact dict with metadata

    Returns:
        Priority score (higher is better)
    """
    score = 0.0

    # Required artifacts get highest priority
    if artifact.get("required", False):
        score += 1000.0

    # Recency bonus (last 24 hours = 100 points, older = less)
    last_accessed = artifact.get("last_accessed", 0)
    if last_accessed > 0:
        now = datetime.now(timezone.utc).timestamp()
        age_hours = (now - last_accessed) / 3600
        recency_score = max(0, 100 - age_hours)
        score += recency_score

    # Size penalty (smaller is better)
    tokens = artifact.get("tokens_estimate", 0)
    score -= tokens * 0.001

    return score


# =============================================================================
# BUDGET STATUS FORMATTING
# =============================================================================


def format_budget_status(
    usage: TokenUsageTracker,
    budget: TokenBudget,
) -> str:
    """Format budget status for display.

    Returns a multi-line string with budget status information
    suitable for CLI display.

    Args:
        usage: Current token usage
        budget: Token budget configuration

    Returns:
        Formatted status string
    """
    result = check_budget(usage, budget)

    lines = [
        "Token Budget Status",
        "=" * 40,
        "",
        f"Configuration:",
        f"  Max tokens:      {budget.max_tokens:>10,}",
        f"  Reserved:        {budget.reserved_tokens:>10,}",
        f"  Available:       {budget.available_tokens:>10,}",
        f"  Warning at:      {budget.warning_threshold:>10.0%}",
        "",
        f"Current Usage:",
        f"  Plan context:    {usage.plan_context:>10,}",
        f"  Runtime context: {usage.runtime_context:>10,}",
        f"  Artifacts:       {usage.artifacts_loaded:>10,}",
        f"  System prompt:   {usage.system_prompt:>10,}",
        f"  ───────────────────────────────────",
        f"  Total:           {usage.total:>10,}",
        "",
        f"Status: {result.message}",
    ]

    # Add artifact breakdown if any
    if usage.artifact_breakdown:
        lines.append("")
        lines.append("Artifact Breakdown:")
        for artifact_id, tokens in sorted(
            usage.artifact_breakdown.items(),
            key=lambda x: -x[1],
        )[:10]:  # Show top 10
            short_id = artifact_id[:20] + "..." if len(artifact_id) > 20 else artifact_id
            lines.append(f"  {short_id:<24} {tokens:>10,}")

        if len(usage.artifact_breakdown) > 10:
            remaining = len(usage.artifact_breakdown) - 10
            lines.append(f"  ... and {remaining} more artifacts")

    return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Configuration
    "TokenBudget",
    # Tracking
    "TokenUsageTracker",
    # Estimation
    "estimate_tokens",
    "estimate_file_tokens",
    "estimate_yaml_tokens",
    # Budget checking
    "BudgetCheckResult",
    "check_budget",
    "can_load_artifact",
    # Prioritization
    "prioritize_artifacts",
    "calculate_artifact_priority_score",
    # Formatting
    "format_budget_status",
]
