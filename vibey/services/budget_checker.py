"""
Budget Checker Service for runtime token budget enforcement.

This service implements the full budget enforcement system with:
- Per-direction settings (input, output, total)
- Three enforcement modes (warn, soft_stop, hard_stop)
- Threshold-based warnings
- Grace periods for over-budget situations
- Automatic mode escalation
- Hierarchical enforcement (optional)
- CLI/environment override mechanism

Usage:
    from vibey.services.budget_checker import BudgetChecker

    checker = BudgetChecker()

    # Check before starting a task
    result = checker.can_start_task(task)
    if not result.allowed:
        print(f"Cannot start: {result.reason}")

    # Check thresholds during execution
    warnings = checker.check_thresholds(task)
    for warning in warnings:
        print(f"Budget warning: {warning.direction} at {warning.ratio:.0%}")

    # Check if execution should stop
    if checker.should_stop(task, 'input'):
        raise BudgetExceededError("Input token budget exceeded")

Design Reference: Sprint 3 - Budget Enforcement
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

import yaml

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.ticket import Ticket, Tokens, TokenEnforcement
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class BudgetWarning:
    """
    Warning generated when a budget threshold is reached.

    Attributes:
        direction: Token direction ('input', 'output', or 'total')
        threshold: The threshold that was triggered (e.g., 0.8 for 80%)
        ratio: Current usage ratio (usage / budget)
        mode: Current effective enforcement mode
        grace_remaining: Remaining grace buffer if over budget (optional)
    """

    direction: str
    threshold: float
    ratio: float
    mode: str
    grace_remaining: Optional[float] = None


@dataclass
class CanStartResult:
    """
    Result of pre-start budget check.

    Attributes:
        allowed: Whether the task can start
        reason: Explanation if not allowed
        ancestor_id: ID of blocking ancestor (if any)
        warnings: List of warnings (task can start but with caveats)
    """

    allowed: bool
    reason: Optional[str] = None
    ancestor_id: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExecutionCheckResult:
    """
    Result of mid-execution budget check.

    Attributes:
        should_stop: Whether execution should stop
        mode: Current effective enforcement mode
        reason: Explanation if should stop
        ancestor_id: ID of blocking ancestor (if any)
        warnings: List of warnings generated
    """

    should_stop: bool
    mode: str = "warn"
    reason: Optional[str] = None
    ancestor_id: Optional[str] = None
    warnings: List[BudgetWarning] = field(default_factory=list)


# =============================================================================
# DEFAULT ENFORCEMENT CONFIGURATION
# =============================================================================

DEFAULT_ENFORCEMENT = {
    "mode": "warn",
    "thresholds": [0.8, 0.9, 1.0],
    "allow_override": True,
    "grace_percent": 0.0,
    "escalation": None,
    "require_children_sum_valid": False,
    "check_ancestors_during_execution": False,
    "block_new_children_when_exceeded": False,
}


# =============================================================================
# BUDGET CHECKER SERVICE
# =============================================================================


class BudgetChecker:
    """
    Runtime budget enforcement service.

    Provides methods for:
    - Pre-start checks (can_start_task)
    - Threshold checks during execution (check_thresholds)
    - Stop decision (should_stop)
    - Hierarchical enforcement (ancestor checks)

    Enforcement Resolution Order (per direction):
    1. Per-direction override on ticket (ticket.input_tokens.enforcement)
    2. Project defaults (.vibey/config/token_budgets.yaml)
    3. Built-in defaults (warn, [0.8, 0.9, 1.0])

    Override Mechanism:
    - CLI flag: --ignore-token-budget
    - Environment variable: VIBEY_IGNORE_TOKEN_BUDGET=1
    - Only works if enforcement.allow_override=True
    """

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize the budget checker.

        Args:
            root_dir: Root directory containing .vibey/ (defaults to cwd)
        """
        self.root_dir = root_dir or Path.cwd()
        self._project_config: Optional[Dict[str, Any]] = None
        self._config_loaded = False

    # =========================================================================
    # CONFIGURATION LOADING
    # =========================================================================

    def _load_project_config(self) -> Optional[Dict[str, Any]]:
        """Load project default configuration from token_budgets.yaml."""
        if self._config_loaded:
            return self._project_config

        config_path = self.root_dir / ".vibey" / "config" / "token_budgets.yaml"
        self._config_loaded = True

        if not config_path.exists():
            self._project_config = None
            return None

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
            self._project_config = config
            return config
        except Exception:
            self._project_config = None
            return None

    def _get_project_enforcement(self) -> Optional[Dict[str, Any]]:
        """Get enforcement settings from project config."""
        config = self._load_project_config()
        if config is None:
            return None
        return config.get("enforcement")

    # =========================================================================
    # ENFORCEMENT RESOLUTION
    # =========================================================================

    def get_enforcement(
        self,
        task: "Ticket",
        direction: str,
    ) -> "TokenEnforcement":
        """
        Resolve enforcement settings for a task and direction.

        Resolution order:
        1. Per-direction override on ticket (ticket.{direction}_tokens.enforcement)
        2. Project defaults (.vibey/config/token_budgets.yaml)
        3. Built-in defaults

        Args:
            task: The ticket to get enforcement for
            direction: Token direction ('input', 'output', or 'total')

        Returns:
            TokenEnforcement with resolved settings
        """
        from vibey.roadmap.models.ticket.ticket import TokenEnforcement

        # 1. Check per-direction override
        if direction == "input" and task.input_tokens and task.input_tokens.enforcement:
            return task.input_tokens.enforcement
        elif direction == "output" and task.output_tokens and task.output_tokens.enforcement:
            return task.output_tokens.enforcement
        elif direction == "total" and task.total_token_enforcement:
            return task.total_token_enforcement

        # 2. Check project defaults
        project_enforcement = self._get_project_enforcement()
        if project_enforcement:
            return TokenEnforcement(**project_enforcement)

        # 3. Built-in defaults
        return TokenEnforcement(**DEFAULT_ENFORCEMENT)

    def get_effective_mode(
        self,
        enforcement: "TokenEnforcement",
        usage_ratio: float,
    ) -> str:
        """
        Get the effective enforcement mode based on usage ratio and escalation.

        Checks escalation steps to determine if mode should be escalated
        based on current usage ratio.

        Args:
            enforcement: TokenEnforcement settings
            usage_ratio: Current usage ratio (usage / budget)

        Returns:
            Effective mode string ('warn', 'soft_stop', or 'hard_stop')
        """
        if not enforcement.escalation:
            return enforcement.mode

        effective_mode = enforcement.mode
        for step in sorted(enforcement.escalation, key=lambda s: s.at):
            if usage_ratio >= step.at:
                effective_mode = step.mode
        return effective_mode

    # =========================================================================
    # OVERRIDE CHECKING
    # =========================================================================

    def _is_override_active(self, enforcement: "TokenEnforcement") -> bool:
        """
        Check if budget override is active via CLI flag or environment variable.

        Args:
            enforcement: TokenEnforcement settings (must have allow_override=True)

        Returns:
            True if override is active and allowed
        """
        if not enforcement.allow_override:
            return False

        # Check environment variable
        if os.environ.get("VIBEY_IGNORE_TOKEN_BUDGET", "").strip() in ("1", "true", "True", "TRUE"):
            return True

        # CLI flag would be passed in via context - for now, check env only
        return False

    # =========================================================================
    # THRESHOLD CHECKS
    # =========================================================================

    def check_thresholds(self, task: "Ticket") -> List[BudgetWarning]:
        """
        Check all budget thresholds for a task.

        Generates warnings for each direction where usage has crossed
        a threshold defined in the enforcement settings.

        Args:
            task: The ticket to check

        Returns:
            List of BudgetWarning for each triggered threshold
        """
        warnings: List[BudgetWarning] = []

        for direction in ["input", "output"]:
            tokens = getattr(task, f"{direction}_tokens", None)
            if not tokens or not tokens.budget or tokens.usage is None:
                continue

            enforcement = self.get_enforcement(task, direction)
            ratio = tokens.usage / tokens.budget
            effective_mode = self.get_effective_mode(enforcement, ratio)

            # Check each threshold
            for threshold in enforcement.thresholds:
                if ratio >= threshold:
                    grace_remaining = None
                    if ratio >= 1.0:
                        grace_remaining = (1 + enforcement.grace_percent) - ratio

                    warnings.append(BudgetWarning(
                        direction=direction,
                        threshold=threshold,
                        ratio=ratio,
                        mode=effective_mode,
                        grace_remaining=grace_remaining,
                    ))

        return warnings

    # =========================================================================
    # STOP DECISION
    # =========================================================================

    def should_stop(self, task: "Ticket", direction: str) -> bool:
        """
        Determine if execution should stop due to budget exceeded.

        Only returns True for hard_stop mode when budget is exceeded
        beyond the grace period.

        Args:
            task: The ticket to check
            direction: Token direction to check ('input' or 'output')

        Returns:
            True if execution should stop
        """
        tokens = getattr(task, f"{direction}_tokens", None)
        if not tokens or not tokens.budget or tokens.usage is None:
            return False

        enforcement = self.get_enforcement(task, direction)

        # Check for override
        if self._is_override_active(enforcement):
            return False

        ratio = tokens.usage / tokens.budget
        effective_mode = self.get_effective_mode(enforcement, ratio)

        if effective_mode == "hard_stop":
            effective_limit = 1 + enforcement.grace_percent
            return ratio >= effective_limit

        return False

    # =========================================================================
    # PRE-START CHECKS
    # =========================================================================

    def _exceeds_own_budget(self, task: "Ticket") -> bool:
        """Check if task's own budget is already exceeded."""
        for direction in ["input", "output"]:
            tokens = getattr(task, f"{direction}_tokens", None)
            if tokens and tokens.budget and tokens.usage:
                if tokens.usage > tokens.budget:
                    return True

        # Check total budget
        if task.total_token_budget:
            input_usage = task.input_tokens.usage if task.input_tokens else 0
            output_usage = task.output_tokens.usage if task.output_tokens else 0
            total_usage = (input_usage or 0) + (output_usage or 0)
            if total_usage > task.total_token_budget:
                return True

        return False

    def can_start_task(
        self,
        task: Union["Ticket", "HierarchicalTicket"],
    ) -> CanStartResult:
        """
        Check if a task can be started based on budget constraints.

        Checks:
        1. Own budget headroom
        2. Ancestor budgets (if block_new_children_when_exceeded is enabled)

        Args:
            task: The ticket to check (can be Ticket or HierarchicalTicket)

        Returns:
            CanStartResult with allowed status and reasons
        """
        warnings: List[str] = []

        # Check override
        for direction in ["input", "output", "total"]:
            enforcement = self.get_enforcement(task, direction)
            if self._is_override_active(enforcement):
                return CanStartResult(
                    allowed=True,
                    warnings=["Budget enforcement is overridden"],
                )

        # Check own budget headroom
        if self._exceeds_own_budget(task):
            return CanStartResult(
                allowed=False,
                reason="Task budget already exceeded",
            )

        # Check ancestors if this is a hierarchical ticket
        if hasattr(task, "ancestors"):
            for ancestor in task.ancestors:
                # Check each direction
                for direction in ["input", "output", "total"]:
                    enforcement = self.get_enforcement(ancestor, direction)
                    if not enforcement.block_new_children_when_exceeded:
                        continue

                    if self._ancestor_exceeded(ancestor, direction):
                        return CanStartResult(
                            allowed=False,
                            reason=f"Ancestor {ancestor.id} {direction} budget exceeded",
                            ancestor_id=ancestor.id,
                        )

        return CanStartResult(allowed=True, warnings=warnings)

    def _ancestor_exceeded(
        self,
        ancestor: Union["Ticket", "HierarchicalTicket"],
        direction: str,
    ) -> bool:
        """Check if an ancestor's budget is exceeded."""
        # Use aggregated tokens if available (HierarchicalTicket)
        if hasattr(ancestor, f"{direction}_tokens_aggregated"):
            agg_tokens = getattr(ancestor, f"{direction}_tokens_aggregated")
            if agg_tokens and agg_tokens.budget and agg_tokens.usage:
                if agg_tokens.usage > agg_tokens.budget:
                    return True
        else:
            # Fallback to local tokens for regular Ticket
            tokens = getattr(ancestor, f"{direction}_tokens", None)
            if tokens and tokens.budget and tokens.usage:
                if tokens.usage > tokens.budget:
                    return True

        return False

    # =========================================================================
    # RUNTIME EXECUTION CHECKS
    # =========================================================================

    def check_during_execution(
        self,
        task: Union["Ticket", "HierarchicalTicket"],
        new_usage: int,
        direction: str,
    ) -> ExecutionCheckResult:
        """
        Check budget constraints during task execution.

        This is the main method to call when tracking token usage during
        task execution. It checks both the task's own budget and optionally
        ancestor budgets.

        Args:
            task: The ticket being executed
            new_usage: The new usage value (cumulative, not delta)
            direction: Token direction ('input' or 'output')

        Returns:
            ExecutionCheckResult with stop decision and warnings
        """
        enforcement = self.get_enforcement(task, direction)

        # Check for override
        if self._is_override_active(enforcement):
            return ExecutionCheckResult(
                should_stop=False,
                mode="warn",
                warnings=[BudgetWarning(
                    direction=direction,
                    threshold=0.0,
                    ratio=0.0,
                    mode="warn",
                    grace_remaining=None,
                )],
            )

        # Get budget for this direction
        tokens = getattr(task, f"{direction}_tokens", None)
        if not tokens or not tokens.budget:
            return ExecutionCheckResult(should_stop=False)

        # Calculate ratio with new usage
        ratio = new_usage / tokens.budget
        effective_mode = self.get_effective_mode(enforcement, ratio)

        # Check own budget
        result = self._check_own_budget(task, new_usage, direction, enforcement, ratio, effective_mode)
        if result.should_stop:
            return result

        # Check ancestors if enabled
        if enforcement.check_ancestors_during_execution and hasattr(task, "ancestors"):
            for ancestor in task.ancestors:
                ancestor_result = self._check_ancestor_budget(
                    ancestor, task, new_usage, direction
                )
                if ancestor_result.should_stop:
                    return ancestor_result

        # Generate warnings
        warnings = []
        for threshold in enforcement.thresholds:
            if ratio >= threshold:
                grace_remaining = None
                if ratio >= 1.0:
                    grace_remaining = (1 + enforcement.grace_percent) - ratio
                warnings.append(BudgetWarning(
                    direction=direction,
                    threshold=threshold,
                    ratio=ratio,
                    mode=effective_mode,
                    grace_remaining=grace_remaining,
                ))

        return ExecutionCheckResult(
            should_stop=False,
            mode=effective_mode,
            warnings=warnings,
        )

    def _check_own_budget(
        self,
        task: "Ticket",
        new_usage: int,
        direction: str,
        enforcement: "TokenEnforcement",
        ratio: float,
        effective_mode: str,
    ) -> ExecutionCheckResult:
        """Check if task's own budget requires stopping."""
        if effective_mode == "hard_stop":
            effective_limit = 1 + enforcement.grace_percent
            if ratio >= effective_limit:
                return ExecutionCheckResult(
                    should_stop=True,
                    mode=effective_mode,
                    reason=f"Task {direction} budget exceeded (grace exhausted)",
                )

        return ExecutionCheckResult(should_stop=False, mode=effective_mode)

    def _check_ancestor_budget(
        self,
        ancestor: Union["Ticket", "HierarchicalTicket"],
        child: Union["Ticket", "HierarchicalTicket"],
        child_new_usage: int,
        direction: str,
    ) -> ExecutionCheckResult:
        """
        Check if child's new usage would exceed ancestor's budget.

        Projects the new aggregated usage based on child's delta and
        checks against ancestor's budget and enforcement settings.

        Args:
            ancestor: The ancestor ticket to check
            child: The child ticket being updated
            child_new_usage: The new usage value for the child
            direction: Token direction to check

        Returns:
            ExecutionCheckResult with stop decision
        """
        # Get ancestor's aggregated tokens
        if hasattr(ancestor, f"{direction}_tokens_aggregated"):
            agg_tokens = getattr(ancestor, f"{direction}_tokens_aggregated")
        else:
            return ExecutionCheckResult(should_stop=False)

        if not agg_tokens or not agg_tokens.budget:
            return ExecutionCheckResult(should_stop=False)

        # Get current child usage
        child_tokens = getattr(child, f"{direction}_tokens", None)
        current_child_usage = child_tokens.usage if child_tokens and child_tokens.usage else 0

        # Calculate usage delta
        usage_delta = child_new_usage - current_child_usage

        # Project new aggregated usage
        current_agg_usage = agg_tokens.usage or 0
        projected_usage = current_agg_usage + usage_delta

        # Calculate ratio
        ratio = projected_usage / agg_tokens.budget

        # Get enforcement for ancestor
        enforcement = self.get_enforcement(ancestor, direction)
        effective_mode = self.get_effective_mode(enforcement, ratio)

        if effective_mode == "hard_stop":
            effective_limit = 1 + enforcement.grace_percent
            if ratio >= effective_limit:
                return ExecutionCheckResult(
                    should_stop=True,
                    mode=effective_mode,
                    reason=f"Would exceed ancestor {ancestor.id} {direction} budget",
                    ancestor_id=ancestor.id,
                )

        return ExecutionCheckResult(should_stop=False, mode=effective_mode)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def check_budget(
    task: "Ticket",
    root_dir: Optional[Path] = None,
) -> List[BudgetWarning]:
    """
    Convenience function to check all thresholds for a task.

    Args:
        task: The ticket to check
        root_dir: Optional root directory

    Returns:
        List of BudgetWarning for triggered thresholds
    """
    checker = BudgetChecker(root_dir=root_dir)
    return checker.check_thresholds(task)


def can_start(
    task: Union["Ticket", "HierarchicalTicket"],
    root_dir: Optional[Path] = None,
) -> CanStartResult:
    """
    Convenience function to check if a task can start.

    Args:
        task: The ticket to check
        root_dir: Optional root directory

    Returns:
        CanStartResult with allowed status
    """
    checker = BudgetChecker(root_dir=root_dir)
    return checker.can_start_task(task)


def should_stop_execution(
    task: "Ticket",
    direction: str,
    root_dir: Optional[Path] = None,
) -> bool:
    """
    Convenience function to check if execution should stop.

    Args:
        task: The ticket to check
        direction: Token direction ('input' or 'output')
        root_dir: Optional root directory

    Returns:
        True if execution should stop
    """
    checker = BudgetChecker(root_dir=root_dir)
    return checker.should_stop(task, direction)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "BudgetChecker",
    # Data models
    "BudgetWarning",
    "CanStartResult",
    "ExecutionCheckResult",
    # Convenience functions
    "check_budget",
    "can_start",
    "should_stop_execution",
]
