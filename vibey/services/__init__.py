"""
Services Layer - High-level operations for CLI and MCP.

This module provides adapter-agnostic services that enable swapping PM tools
without changing CLI or MCP code.

Core Services:
- TicketService: All ticket CRUD and workflow operations

Usage:
    from vibey.services import TicketService

    # Use default adapter
    service = TicketService()

    # Use specific adapter
    from vibey.adapters.pm import PMAdapterRegistry
    jira_adapter = PMAdapterRegistry.get("jira")
    service = TicketService(adapter=jira_adapter)

    # Operations
    projects = service.list_projects()
    task = service.get_ticket("TASK-123")
    service.start("TASK-123")
    service.complete("TASK-123")
"""

from vibey.services.ticket_service import TicketService, TicketServiceError
from vibey.services.token_estimator import (
    TokenEstimator,
    EstimationResult,
    estimate_tokens,
)
from vibey.services.budget_validator import (
    BudgetValidator,
    BudgetValidationError,
    validate_budget_hierarchy,
)
from vibey.services.token_tracker import (
    TokenTracker,
    TokenDelta,
    CommitUsage,
    track_usage,
    get_task_usage,
)
from vibey.services.budget_checker import (
    BudgetChecker,
    BudgetWarning,
    CanStartResult,
    ExecutionCheckResult,
    check_budget,
    can_start,
    should_stop_execution,
)
from vibey.services.auto_estimation import (
    AutoEstimationTrigger,
    AutoEstimationConfig,
    load_auto_estimation_config,
    save_auto_estimation_config,
    on_task_created,
    on_task_status_change,
    on_calibration_updated,
    estimate_task_tokens,
)

__all__ = [
    "TicketService",
    "TicketServiceError",
    "TokenEstimator",
    "EstimationResult",
    "estimate_tokens",
    "BudgetValidator",
    "BudgetValidationError",
    "validate_budget_hierarchy",
    "TokenTracker",
    "TokenDelta",
    "CommitUsage",
    "track_usage",
    "get_task_usage",
    "BudgetChecker",
    "BudgetWarning",
    "CanStartResult",
    "ExecutionCheckResult",
    "check_budget",
    "can_start",
    "should_stop_execution",
    # Auto-estimation
    "AutoEstimationTrigger",
    "AutoEstimationConfig",
    "load_auto_estimation_config",
    "save_auto_estimation_config",
    "on_task_created",
    "on_task_status_change",
    "on_calibration_updated",
    "estimate_task_tokens",
]
