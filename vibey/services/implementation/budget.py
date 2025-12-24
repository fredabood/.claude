"""
Token Budget Enforcement for Implementation Mode.

This module provides budget tracking and enforcement for token usage during
autonomous implementation sessions. It monitors both session-level and per-task
token consumption to prevent runaway costs.

Usage:
    from vibey.services.implementation.budget import TokenBudget, BudgetCheck
    from vibey.services.implementation.config import ImplementConfig

    # Create budget tracker
    config = ImplementConfig(
        max_tokens_per_session=100000,
        max_tokens_per_task=25000,
    )
    budget = TokenBudget(config)

    # Check if task can be executed
    estimated_tokens = 5000
    check = budget.check_budget(estimated_tokens)

    if check == BudgetCheck.ALLOWED:
        # Execute the task
        result = await executor.execute(task)
        budget.record_usage(result)
    elif check == BudgetCheck.WARNING:
        # Proceed with caution, near limit
        pass
    else:  # BudgetCheck.EXCEEDED
        # Stop execution, budget exhausted
        pass

    # Get remaining budget
    remaining = budget.remaining_budget()

    # Generate usage report
    report = budget.usage_report()

Design Reference:
- Implementation Mode Track
- Task ND: Implement token budget enforcement
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from vibey.services.implementation.config import ImplementConfig
    from vibey.services.implementation.result import ExecutionResult


# =============================================================================
# ENUMS
# =============================================================================


class BudgetCheck(str, Enum):
    """
    Result of a budget check operation.

    Values:
        ALLOWED: Within budget, task can proceed
        WARNING: Near limit (>80% consumed), proceed with caution
        EXCEEDED: Over budget, task should not proceed
    """

    ALLOWED = "allowed"
    WARNING = "warning"
    EXCEEDED = "exceeded"


# =============================================================================
# TOKEN BUDGET
# =============================================================================


@dataclass
class TokenBudget:
    """
    Token budget tracker for implementation sessions.

    Monitors token consumption at both session and per-task levels to enforce
    budgetary constraints and prevent excessive resource usage.

    The budget tracks:
    - Session-level token limits (total across all tasks)
    - Per-task token limits (for individual task execution)
    - Input vs output token breakdown for analysis

    Attributes:
        config: Implementation configuration with budget limits
        session_tokens_input: Total input tokens consumed this session
        session_tokens_output: Total output tokens consumed this session

    Example:
        >>> config = ImplementConfig(max_tokens_per_session=100000)
        >>> budget = TokenBudget(config)
        >>> budget.check_budget(5000)
        <BudgetCheck.ALLOWED: 'allowed'>
        >>> budget.remaining_budget()
        100000
    """

    config: "ImplementConfig"
    session_tokens_input: int = field(default=0)
    session_tokens_output: int = field(default=0)

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def session_tokens_total(self) -> int:
        """
        Total tokens consumed this session (input + output).

        Returns:
            Sum of input and output tokens.
        """
        return self.session_tokens_input + self.session_tokens_output

    @property
    def max_session_tokens(self) -> Optional[int]:
        """
        Maximum tokens allowed per session from config.

        Returns:
            Session token limit or None if unlimited.
        """
        return self.config.max_tokens_per_session

    @property
    def max_task_tokens(self) -> int:
        """
        Maximum tokens allowed per task from config.

        Returns:
            Per-task token limit.
        """
        return self.config.max_tokens_per_task

    @property
    def usage_percentage(self) -> float:
        """
        Calculate percentage of session budget consumed.

        Returns:
            Percentage (0-100+) of budget used. Returns 0.0 if unlimited.
        """
        if self.max_session_tokens is None:
            return 0.0
        if self.max_session_tokens <= 0:
            return 100.0
        return (self.session_tokens_total / self.max_session_tokens) * 100

    # =========================================================================
    # BUDGET CHECKING
    # =========================================================================

    def check_budget(self, estimated_tokens: int) -> BudgetCheck:
        """
        Check if budget allows task execution.

        Evaluates whether a task with the estimated token consumption can
        proceed given current budget constraints. Considers both session-level
        limits and per-task limits.

        Args:
            estimated_tokens: Estimated tokens the task will consume.

        Returns:
            BudgetCheck indicating whether to proceed:
            - ALLOWED: Within budget, safe to proceed
            - WARNING: Near limit (>80% consumed), proceed with caution
            - EXCEEDED: Over budget, should not proceed

        Example:
            >>> budget = TokenBudget(config)
            >>> budget.check_budget(5000)
            <BudgetCheck.ALLOWED: 'allowed'>
        """
        # Check per-task limit first
        if estimated_tokens > self.max_task_tokens:
            return BudgetCheck.EXCEEDED

        # If session limit is unlimited, always allowed
        if self.max_session_tokens is None:
            return BudgetCheck.ALLOWED

        # Calculate projected total after this task
        projected_total = self.session_tokens_total + estimated_tokens

        # Check if would exceed session limit
        if projected_total > self.max_session_tokens:
            return BudgetCheck.EXCEEDED

        # Check if we're already near the limit (>80%)
        current_percentage = self.usage_percentage
        if current_percentage >= 80:
            return BudgetCheck.WARNING

        # Check if this task would push us over 80%
        projected_percentage = (projected_total / self.max_session_tokens) * 100
        if projected_percentage >= 80:
            return BudgetCheck.WARNING

        return BudgetCheck.ALLOWED

    def check_task_budget(self, estimated_tokens: int) -> BudgetCheck:
        """
        Check if estimated tokens exceed per-task limit.

        This is a simpler check that only evaluates the per-task budget,
        ignoring session-level constraints.

        Args:
            estimated_tokens: Estimated tokens for the task.

        Returns:
            BudgetCheck for per-task limit only.
        """
        if estimated_tokens > self.max_task_tokens:
            return BudgetCheck.EXCEEDED
        if estimated_tokens > self.max_task_tokens * 0.8:
            return BudgetCheck.WARNING
        return BudgetCheck.ALLOWED

    # =========================================================================
    # USAGE TRACKING
    # =========================================================================

    def record_usage(self, result: "ExecutionResult") -> None:
        """
        Record token usage from execution result.

        Updates the session totals with tokens consumed during task execution.
        Should be called after each task completes.

        Args:
            result: ExecutionResult containing token usage information.

        Example:
            >>> result = await executor.execute(task)
            >>> budget.record_usage(result)
            >>> print(budget.session_tokens_total)
            2000
        """
        self.session_tokens_input += result.tokens_input
        self.session_tokens_output += result.tokens_output

    def record_tokens(self, tokens_input: int, tokens_output: int) -> None:
        """
        Record token usage directly.

        Alternative to record_usage() for cases where you have raw token counts
        instead of an ExecutionResult.

        Args:
            tokens_input: Number of input tokens consumed.
            tokens_output: Number of output tokens generated.
        """
        self.session_tokens_input += tokens_input
        self.session_tokens_output += tokens_output

    # =========================================================================
    # BUDGET CALCULATIONS
    # =========================================================================

    def remaining_budget(self) -> int:
        """
        Calculate remaining token budget.

        Returns the number of tokens that can still be consumed before
        hitting the session limit.

        Returns:
            Remaining tokens available. Returns max int if unlimited.
            Returns 0 if already exceeded.

        Example:
            >>> config = ImplementConfig(max_tokens_per_session=100000)
            >>> budget = TokenBudget(config)
            >>> budget.remaining_budget()
            100000
        """
        if self.max_session_tokens is None:
            # Return a very large number for "unlimited"
            return 2**31 - 1  # Max 32-bit signed int

        remaining = self.max_session_tokens - self.session_tokens_total
        return max(0, remaining)

    def remaining_budget_percentage(self) -> float:
        """
        Calculate remaining budget as percentage.

        Returns:
            Percentage (0-100) of budget remaining. Returns 100.0 if unlimited.
        """
        if self.max_session_tokens is None:
            return 100.0
        return max(0.0, 100.0 - self.usage_percentage)

    def can_execute_task(self, estimated_tokens: int) -> bool:
        """
        Simple boolean check if task can be executed.

        Convenience method that returns True for both ALLOWED and WARNING
        statuses.

        Args:
            estimated_tokens: Estimated tokens for the task.

        Returns:
            True if task can proceed (ALLOWED or WARNING), False if EXCEEDED.
        """
        check = self.check_budget(estimated_tokens)
        return check != BudgetCheck.EXCEEDED

    # =========================================================================
    # REPORTING
    # =========================================================================

    def usage_report(self) -> Dict[str, Any]:
        """
        Generate budget usage report.

        Creates a comprehensive report of token budget consumption including
        totals, limits, and remaining capacity.

        Returns:
            Dictionary containing:
            - session: Session token usage breakdown
            - limits: Configured budget limits
            - remaining: Remaining budget information
            - status: Current budget status

        Example:
            >>> budget.usage_report()
            {
                'session': {
                    'tokens_input': 1500,
                    'tokens_output': 500,
                    'tokens_total': 2000,
                },
                'limits': {
                    'max_tokens_per_session': 100000,
                    'max_tokens_per_task': 25000,
                },
                'remaining': {
                    'tokens': 98000,
                    'percentage': 98.0,
                },
                'status': {
                    'usage_percentage': 2.0,
                    'budget_check': 'allowed',
                    'is_unlimited': False,
                }
            }
        """
        remaining = self.remaining_budget()
        remaining_pct = self.remaining_budget_percentage()

        # Determine current status (check with 0 estimated tokens)
        current_status = self.check_budget(0)

        return {
            "session": {
                "tokens_input": self.session_tokens_input,
                "tokens_output": self.session_tokens_output,
                "tokens_total": self.session_tokens_total,
            },
            "limits": {
                "max_tokens_per_session": self.max_session_tokens,
                "max_tokens_per_task": self.max_task_tokens,
            },
            "remaining": {
                "tokens": remaining if self.max_session_tokens else None,
                "percentage": remaining_pct,
            },
            "status": {
                "usage_percentage": self.usage_percentage,
                "budget_check": current_status.value,
                "is_unlimited": self.max_session_tokens is None,
            },
        }

    def summary(self) -> str:
        """
        Generate a human-readable budget summary.

        Returns:
            Formatted string summarizing budget status.
        """
        if self.max_session_tokens is None:
            return (
                f"Tokens used: {self.session_tokens_total:,} "
                f"(input: {self.session_tokens_input:,}, "
                f"output: {self.session_tokens_output:,}) - No session limit"
            )

        return (
            f"Tokens used: {self.session_tokens_total:,} / "
            f"{self.max_session_tokens:,} "
            f"({self.usage_percentage:.1f}%) - "
            f"Remaining: {self.remaining_budget():,}"
        )

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def reset(self) -> None:
        """
        Reset session token counters.

        Clears all accumulated token usage. Useful when starting a new session.
        """
        self.session_tokens_input = 0
        self.session_tokens_output = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize budget state to dictionary.

        Returns:
            Dictionary suitable for state persistence.
        """
        return {
            "session_tokens_input": self.session_tokens_input,
            "session_tokens_output": self.session_tokens_output,
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Load budget state from dictionary.

        Restores token counters from persisted state.

        Args:
            state: Dictionary from to_dict() or similar.
        """
        self.session_tokens_input = state.get("session_tokens_input", 0)
        self.session_tokens_output = state.get("session_tokens_output", 0)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BudgetCheck",
    "TokenBudget",
]
