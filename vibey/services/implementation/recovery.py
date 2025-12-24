"""
ErrorRecovery - Error recovery and retry logic for task execution.

This module provides error classification and recovery strategies for the
autonomous implementation loop, enabling resilient task execution with
appropriate retry and skip behaviors.

Key Features:
- Error classification (transient vs permanent)
- Configurable retry limits per task
- Recovery action determination (retry, skip, stop, wait)
- Blocked task tracking with error reasons

Usage:
    from vibey.services.implementation import (
        ErrorRecovery,
        RecoveryAction,
        ErrorSeverity,
    )
    from vibey.services.implementation.loop import ImplementConfig

    config = ImplementConfig(max_tasks=10)
    recovery = ErrorRecovery(config)

    # Handle an error
    action = recovery.handle_error(task, error, result)

    if action == RecoveryAction.RETRY:
        # Retry the task
        ...
    elif action == RecoveryAction.SKIP:
        # Mark blocked and continue
        ...
    elif action == RecoveryAction.STOP:
        # Stop execution loop
        ...
    elif action == RecoveryAction.WAIT:
        # Wait before retrying (rate limit)
        ...

Design Reference:
- Implementation Mode Track Sprint 1
- Task N9: Implement error recovery and retry logic
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.loop import ExecutionResult, ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_MAX_RETRIES = 3
"""Default maximum retry attempts per task."""

DEFAULT_RATE_LIMIT_WAIT_SECONDS = 60
"""Default wait time in seconds when rate limited."""


# =============================================================================
# ENUMS
# =============================================================================


class RecoveryAction(str, Enum):
    """
    Action to take after an error.

    Values:
        RETRY: Retry the task immediately (if retries remaining)
        SKIP: Mark task as blocked and continue to next task
        STOP: Stop the execution loop entirely
        WAIT: Wait before retrying (typically for rate limits)
    """

    RETRY = "retry"
    SKIP = "skip"
    STOP = "stop"
    WAIT = "wait"


class ErrorSeverity(str, Enum):
    """
    Severity classification for errors.

    Values:
        TRANSIENT: Temporary error that may succeed on retry (timeout, rate limit, network)
        PERMANENT: Persistent error unlikely to succeed on retry (validation, auth, not found)
    """

    TRANSIENT = "transient"
    PERMANENT = "permanent"


# =============================================================================
# BLOCKED TASK TRACKING
# =============================================================================


@dataclass
class BlockedTask:
    """
    Record of a task that was blocked due to an error.

    Attributes:
        task_id: ULID of the blocked task
        task_name: Human-readable name of the task
        reason: Description of why the task was blocked
        error_type: Type name of the exception that caused blocking
        blocked_at: When the task was marked blocked
        retry_count: Number of retries attempted before blocking
    """

    task_id: str
    task_name: str
    reason: str
    error_type: str
    blocked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "reason": self.reason,
            "error_type": self.error_type,
            "blocked_at": self.blocked_at.isoformat(),
            "retry_count": self.retry_count,
        }


# =============================================================================
# ERROR RECOVERY
# =============================================================================


class ErrorRecovery:
    """
    Error recovery and retry logic for task execution.

    Handles error classification, retry tracking, and determines appropriate
    recovery actions for failed tasks in the implementation loop.

    Attributes:
        config: Implementation loop configuration
        max_retries: Maximum retry attempts per task (defaults to 3)
        retry_counts: Mapping of task_id to retry attempt count
        blocked_tasks: List of tasks that were blocked due to errors
        rate_limit_wait: Seconds to wait when rate limited

    Example:
        >>> recovery = ErrorRecovery(config)
        >>> action = recovery.handle_error(task, error, result)
        >>> if action == RecoveryAction.RETRY:
        ...     # Retry task
        >>> elif action == RecoveryAction.SKIP:
        ...     # Continue to next task
    """

    def __init__(
        self,
        config: "ImplementConfig",
        max_retries: int = DEFAULT_MAX_RETRIES,
        rate_limit_wait: int = DEFAULT_RATE_LIMIT_WAIT_SECONDS,
    ):
        """
        Initialize error recovery handler.

        Args:
            config: ImplementConfig with execution parameters
            max_retries: Maximum retry attempts per task (default 3)
            rate_limit_wait: Seconds to wait when rate limited (default 60)
        """
        self.config = config
        self.max_retries = max_retries
        self.rate_limit_wait = rate_limit_wait
        self.retry_counts: Dict[str, int] = {}
        self.blocked_tasks: List[BlockedTask] = []

    # =========================================================================
    # MAIN HANDLER
    # =========================================================================

    def handle_error(
        self,
        task: "HierarchicalTicket",
        error: Exception,
        result: "ExecutionResult",
    ) -> RecoveryAction:
        """
        Determine recovery action for a failed task.

        Analyzes the error type and task state to determine the best
        recovery strategy:
        - RETRY: Retry if transient error and retries remaining
        - WAIT: Wait and retry for rate limits
        - SKIP: Mark blocked and continue to next task
        - STOP: Stop loop for fatal errors

        Args:
            task: The HierarchicalTicket that failed
            error: The exception that was raised
            result: The ExecutionResult from the failed execution

        Returns:
            RecoveryAction indicating how to proceed
        """
        task_id = task.id
        severity = self.classify_error(error)

        logger.debug(
            f"Handling error for task {task_id}: {type(error).__name__} "
            f"(severity={severity.value})"
        )

        # Check for rate limit - special handling
        if self._is_rate_limit_error(error):
            if self.should_retry(task_id):
                self.record_attempt(task_id)
                logger.info(
                    f"Task {task_id} hit rate limit, will wait {self.rate_limit_wait}s "
                    f"(attempt {self.retry_counts[task_id]}/{self.max_retries})"
                )
                return RecoveryAction.WAIT
            else:
                self.mark_blocked(task, f"Rate limited after {self.max_retries} retries")
                return RecoveryAction.SKIP

        # Check for fatal errors that should stop the loop
        if self._is_fatal_error(error):
            logger.error(f"Fatal error for task {task_id}: {error}")
            return RecoveryAction.STOP

        # Transient errors - retry if attempts remaining
        if severity == ErrorSeverity.TRANSIENT:
            if self.should_retry(task_id):
                self.record_attempt(task_id)
                logger.info(
                    f"Task {task_id} failed with transient error, retrying "
                    f"(attempt {self.retry_counts[task_id]}/{self.max_retries})"
                )
                return RecoveryAction.RETRY
            else:
                self.mark_blocked(
                    task,
                    f"Transient error after {self.max_retries} retries: {error}",
                )
                return RecoveryAction.SKIP

        # Permanent errors - skip immediately
        self.mark_blocked(task, f"Permanent error: {error}")
        return RecoveryAction.SKIP

    # =========================================================================
    # RETRY TRACKING
    # =========================================================================

    def should_retry(self, task_id: str) -> bool:
        """
        Check if task has retries remaining.

        Args:
            task_id: ULID of the task to check

        Returns:
            True if retry count is below max_retries
        """
        return self.retry_counts.get(task_id, 0) < self.max_retries

    def record_attempt(self, task_id: str) -> None:
        """
        Record a retry attempt for a task.

        Increments the retry counter for the given task.

        Args:
            task_id: ULID of the task being retried
        """
        current = self.retry_counts.get(task_id, 0)
        self.retry_counts[task_id] = current + 1
        logger.debug(f"Recorded attempt {self.retry_counts[task_id]} for task {task_id}")

    def get_retry_count(self, task_id: str) -> int:
        """
        Get current retry count for a task.

        Args:
            task_id: ULID of the task

        Returns:
            Number of retry attempts made
        """
        return self.retry_counts.get(task_id, 0)

    def reset_retry_count(self, task_id: str) -> None:
        """
        Reset retry count for a task.

        Called when a task succeeds to clear any retry history.

        Args:
            task_id: ULID of the task
        """
        if task_id in self.retry_counts:
            del self.retry_counts[task_id]
            logger.debug(f"Reset retry count for task {task_id}")

    # =========================================================================
    # BLOCKED TASK MANAGEMENT
    # =========================================================================

    def mark_blocked(self, task: "HierarchicalTicket", reason: str) -> None:
        """
        Mark a task as blocked with an error reason.

        Creates a BlockedTask record and adds it to the blocked list.
        This allows the loop to continue with other tasks while
        tracking what was skipped and why.

        Args:
            task: The HierarchicalTicket to mark as blocked
            reason: Description of why the task was blocked
        """
        blocked = BlockedTask(
            task_id=task.id,
            task_name=task.name,
            reason=reason,
            error_type=self._get_error_type_from_reason(reason),
            retry_count=self.retry_counts.get(task.id, 0),
        )
        self.blocked_tasks.append(blocked)

        logger.warning(
            f"Task {task.id} ({task.name}) blocked: {reason} "
            f"(after {blocked.retry_count} retries)"
        )

    def get_blocked_tasks(self) -> List[BlockedTask]:
        """
        Get all tasks that were blocked during this session.

        Returns:
            List of BlockedTask records
        """
        return list(self.blocked_tasks)

    def clear_blocked_tasks(self) -> None:
        """Clear the blocked tasks list."""
        self.blocked_tasks.clear()

    # =========================================================================
    # ERROR CLASSIFICATION
    # =========================================================================

    def classify_error(self, error: Exception) -> ErrorSeverity:
        """
        Classify error as transient or permanent.

        Transient errors (may succeed on retry):
        - TimeoutError, asyncio.TimeoutError
        - ConnectionError, OSError with network-related messages
        - Rate limit errors (HTTP 429)
        - Temporary server errors (HTTP 500, 502, 503, 504)

        Permanent errors (unlikely to succeed on retry):
        - ValueError, TypeError, KeyError
        - Authentication errors (HTTP 401, 403)
        - Not found errors (HTTP 404)
        - Validation errors

        Args:
            error: The exception to classify

        Returns:
            ErrorSeverity indicating transient or permanent
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Timeout errors are transient
        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return ErrorSeverity.TRANSIENT

        # Connection/network errors are transient
        if isinstance(error, (ConnectionError, OSError)):
            if any(
                keyword in error_msg
                for keyword in ["connection", "network", "refused", "reset", "timeout"]
            ):
                return ErrorSeverity.TRANSIENT

        # Check for HTTP status codes in error message
        if "429" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
            return ErrorSeverity.TRANSIENT

        if any(code in error_msg for code in ["500", "502", "503", "504"]):
            return ErrorSeverity.TRANSIENT

        if any(code in error_msg for code in ["401", "403", "404"]):
            return ErrorSeverity.PERMANENT

        # Type/value errors are usually permanent
        if isinstance(error, (ValueError, TypeError, KeyError, AttributeError)):
            return ErrorSeverity.PERMANENT

        # Check for validation-related errors
        if "validation" in error_msg or "invalid" in error_msg:
            return ErrorSeverity.PERMANENT

        # Check for authentication/authorization errors
        if "auth" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
            return ErrorSeverity.PERMANENT

        # Check for not found errors
        if "not found" in error_msg or "does not exist" in error_msg:
            return ErrorSeverity.PERMANENT

        # Check for common transient keywords
        if any(
            keyword in error_msg
            for keyword in ["timeout", "temporary", "retry", "again", "overload", "busy"]
        ):
            return ErrorSeverity.TRANSIENT

        # Default to transient for unknown errors (safer to retry)
        logger.debug(
            f"Unknown error type {error_type}, defaulting to TRANSIENT: {error}"
        )
        return ErrorSeverity.TRANSIENT

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """
        Check if error is a rate limit error.

        Args:
            error: The exception to check

        Returns:
            True if this appears to be a rate limit error
        """
        error_msg = str(error).lower()
        return any(
            keyword in error_msg
            for keyword in ["429", "rate limit", "too many requests", "quota exceeded"]
        )

    def _is_fatal_error(self, error: Exception) -> bool:
        """
        Check if error should stop the entire loop.

        Fatal errors indicate a systemic problem that won't be resolved
        by continuing with other tasks.

        Args:
            error: The exception to check

        Returns:
            True if the loop should stop
        """
        error_msg = str(error).lower()

        # Authentication issues affect all tasks
        if "api key" in error_msg or "invalid key" in error_msg:
            return True

        # Missing required configuration
        if "missing configuration" in error_msg or "not configured" in error_msg:
            return True

        # Keyboard interrupt should always stop
        if isinstance(error, KeyboardInterrupt):
            return True

        # System exit should always stop
        if isinstance(error, SystemExit):
            return True

        return False

    def _get_error_type_from_reason(self, reason: str) -> str:
        """
        Extract error type from reason string.

        Args:
            reason: The blocking reason string

        Returns:
            Error type name or "Unknown"
        """
        # Try to extract from common patterns
        if ": " in reason:
            # Pattern: "Permanent error: SomeError(message)"
            after_colon = reason.split(": ", 1)[1]
            if "(" in after_colon:
                return after_colon.split("(")[0]
            # Pattern: "Permanent error: message"
            return "Error"

        return "Unknown"

    async def wait_for_rate_limit(self) -> None:
        """
        Wait the configured time for rate limit cooldown.

        This is an async method that should be called when
        handle_error returns RecoveryAction.WAIT.
        """
        logger.info(f"Waiting {self.rate_limit_wait} seconds for rate limit cooldown")
        await asyncio.sleep(self.rate_limit_wait)

    # =========================================================================
    # SUMMARY
    # =========================================================================

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recovery activity during this session.

        Returns:
            Dictionary with retry and blocked task statistics
        """
        total_retries = sum(self.retry_counts.values())
        tasks_with_retries = len(self.retry_counts)

        return {
            "total_retries": total_retries,
            "tasks_with_retries": tasks_with_retries,
            "blocked_count": len(self.blocked_tasks),
            "blocked_tasks": [bt.to_dict() for bt in self.blocked_tasks],
            "retry_counts": dict(self.retry_counts),
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RecoveryAction",
    "ErrorSeverity",
    "BlockedTask",
    "ErrorRecovery",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RATE_LIMIT_WAIT_SECONDS",
]
