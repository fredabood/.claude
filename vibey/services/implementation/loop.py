"""
ImplementationLoop - Main execution loop for autonomous task processing.

This module provides the core execution loop for the autonomous implementation mode,
which processes tasks from the roadmap with minimal human intervention.

Key Features:
- Async execution with proper cancellation support
- Graceful interrupt handling (SIGINT, SIGTERM)
- State persistence for session resume capability
- Configurable stop conditions (max tasks, token budget, pause flag)

Usage:
    from vibey.services.implementation import (
        ImplementationLoop,
        TaskSelector,
        ImplementConfig,
    )
    from pathlib import Path

    # Configure the loop
    config = ImplementConfig(
        max_tasks=10,
        max_tokens=100000,
        state_path=Path(".vibey/implementation/state.yaml"),
    )

    # Create components
    selector = TaskSelector(roadmap_root=Path(".vibey/roadmap"))
    executor = MyTaskExecutor()  # Implement TaskExecutor protocol

    # Run the loop
    loop = ImplementationLoop(selector, executor, config)
    result = await loop.run()

    print(f"Completed: {result.tasks_completed}/{result.tasks_attempted}")

Design Reference:
- Implementation Mode Track Sprint 1
- ADR-0002: Flat Directory Structure
"""

import asyncio
import logging
import signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.services.implementation.selector import TaskSelector
from vibey.services.implementation.state import LoopState, LoopStatus, TaskResult

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class ImplementConfig:
    """
    Configuration for the implementation loop.

    This is a placeholder that will be expanded in Sprint 4 to include
    full configuration options such as:
    - Platform-specific settings
    - Token budget management
    - Retry policies
    - Logging configuration

    Attributes:
        max_tasks: Maximum number of tasks to execute in this session (None = unlimited)
        max_tokens: Maximum total tokens (input + output) to consume (None = unlimited)
        state_path: Path for persisting loop state (for resume capability)
        track_id: Optional track ULID to filter tasks by
        sprint_id: Optional sprint ULID to filter tasks by
        auto_save: Whether to automatically save state after each task
        save_interval: How often to save state (in seconds) during long tasks
    """

    max_tasks: Optional[int] = None
    max_tokens: Optional[int] = None
    state_path: Optional[Path] = None
    track_id: Optional[str] = None
    sprint_id: Optional[str] = None
    auto_save: bool = True
    save_interval: int = 60  # seconds


# =============================================================================
# TASK EXECUTOR PROTOCOL
# =============================================================================


@dataclass
class ExecutionResult:
    """
    Result from executing a single task.

    Attributes:
        success: Whether the task completed successfully
        tokens_input: Input tokens consumed during execution
        tokens_output: Output tokens generated during execution
        commits: Git commit SHAs created during execution
        error_message: Error description if task failed
        metadata: Additional execution metadata
    """

    success: bool = False
    tokens_input: int = 0
    tokens_output: int = 0
    commits: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TaskExecutor(Protocol):
    """
    Protocol for task execution implementations.

    This is a placeholder protocol that will be implemented in Sprint 2.
    Implementations should handle:
    - Loading task context
    - Invoking the AI agent with task instructions
    - Processing agent responses
    - Tracking commits and changes
    - Handling errors and retries

    Example implementation:
        class ClaudeTaskExecutor:
            async def execute(self, task: HierarchicalTicket) -> ExecutionResult:
                # Load context for the task
                context = self.load_context(task)

                # Execute via Claude API
                response = await self.client.complete(...)

                # Process results
                return ExecutionResult(
                    success=True,
                    tokens_input=response.usage.input_tokens,
                    tokens_output=response.usage.output_tokens,
                    commits=self.extract_commits(response),
                )
    """

    async def execute(self, task: HierarchicalTicket) -> ExecutionResult:
        """
        Execute a single task.

        Args:
            task: The HierarchicalTicket to execute.

        Returns:
            ExecutionResult with success status and resource usage.

        Raises:
            Exception: If execution fails catastrophically (not handled errors).
        """
        ...


# =============================================================================
# LOOP RESULT
# =============================================================================


@dataclass
class LoopResult:
    """
    Summary result from an execution loop session.

    This is returned by ImplementationLoop.run() and provides a complete
    summary of what happened during the execution session.

    Attributes:
        session_id: Unique identifier for this execution session
        status: Final loop status (completed, stopped, paused)
        started_at: When the session began
        ended_at: When the session ended
        tasks_attempted: Total tasks that execution was attempted on
        tasks_completed: Tasks that completed successfully
        tasks_failed: Tasks that failed during execution
        tasks_blocked: Tasks that were blocked and skipped
        tokens_input: Total input tokens consumed
        tokens_output: Total output tokens generated
        task_results: Individual results for each task attempted
        stop_reason: Why the loop stopped (max_tasks, max_tokens, signal, no_tasks, error)
    """

    session_id: str = ""
    status: LoopStatus = LoopStatus.COMPLETED
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    tasks_attempted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_blocked: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    task_results: List[TaskResult] = field(default_factory=list)
    stop_reason: str = ""

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.tokens_input + self.tokens_output

    @property
    def success_rate(self) -> Optional[float]:
        """Success rate as float (0.0 to 1.0), None if no tasks attempted."""
        if self.tasks_attempted == 0:
            return None
        return self.tasks_completed / self.tasks_attempted

    @property
    def duration_seconds(self) -> Optional[float]:
        """Duration of the session in seconds."""
        if self.started_at is None or self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "tasks_attempted": self.tasks_attempted,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_blocked": self.tasks_blocked,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "total_tokens": self.total_tokens,
            "success_rate": self.success_rate,
            "duration_seconds": self.duration_seconds,
            "stop_reason": self.stop_reason,
            "task_results": [r.to_dict() for r in self.task_results],
        }


# =============================================================================
# IMPLEMENTATION LOOP
# =============================================================================


class ImplementationLoop:
    """
    Main execution loop for autonomous task processing.

    The ImplementationLoop coordinates task selection, execution, and state
    management for autonomous implementation mode. It processes tasks in
    priority order until a stop condition is met.

    Stop Conditions:
    - No more executable tasks available
    - Maximum task count reached (config.max_tasks)
    - Token budget exhausted (config.max_tokens)
    - Manual pause requested (state.status == PAUSED)
    - Signal received (SIGINT, SIGTERM)

    Attributes:
        selector: TaskSelector for finding executable tasks
        executor: TaskExecutor for running individual tasks
        config: ImplementConfig with execution parameters
        state: LoopState tracking execution progress

    Example:
        >>> loop = ImplementationLoop(selector, executor, config)
        >>> result = await loop.run()
        >>> print(f"Completed {result.tasks_completed} tasks")
        >>> print(f"Used {result.total_tokens} tokens")
    """

    def __init__(
        self,
        selector: TaskSelector,
        executor: TaskExecutor,
        config: ImplementConfig,
        state: Optional[LoopState] = None,
    ):
        """
        Initialize the implementation loop.

        Args:
            selector: TaskSelector for finding next executable task
            executor: TaskExecutor for running individual tasks
            config: ImplementConfig with execution parameters
            state: Optional existing LoopState (for resume), creates new if None
        """
        self.selector = selector
        self.executor = executor
        self.config = config

        # Load or create state
        if state is not None:
            self.state = state
        elif config.state_path and config.state_path.exists():
            self.state = LoopState.load(config.state_path)
            logger.info(f"Resumed session: {self.state.session_id}")
        else:
            self.state = LoopState()
            logger.info(f"Started new session: {self.state.session_id}")

        # Signal handling
        self._shutdown_requested = False
        self._original_sigint = None
        self._original_sigterm = None

        # Current task tracking for cancellation
        self._current_task_future: Optional[asyncio.Task] = None

    # =========================================================================
    # MAIN EXECUTION LOOP
    # =========================================================================

    async def run(self) -> LoopResult:
        """
        Main execution loop.

        Processes tasks in priority order until a stop condition is met.
        Handles interrupts gracefully and persists state for resume.

        Returns:
            LoopResult with summary of execution session.

        Example:
            >>> result = await loop.run()
            >>> if result.status == LoopStatus.COMPLETED:
            ...     print("All tasks completed!")
            >>> elif result.stop_reason == "signal":
            ...     print("Interrupted by user")
        """
        self._install_signal_handlers()

        try:
            # Ensure loop is in running state
            if self.state.status == LoopStatus.PAUSED:
                self.state.resume()
            elif self.state.status in (LoopStatus.STOPPED, LoopStatus.COMPLETED):
                # Reset for new run
                self.state = LoopState()

            self.state.status = LoopStatus.RUNNING
            self._save_state()

            logger.info(
                f"Starting execution loop (session={self.state.session_id}, "
                f"max_tasks={self.config.max_tasks}, max_tokens={self.config.max_tokens})"
            )

            stop_reason = ""

            while not self._should_stop():
                # Check for shutdown signal
                if self._shutdown_requested:
                    stop_reason = "signal"
                    logger.info("Shutdown requested, stopping loop")
                    break

                # Get next executable task
                task = self.selector.get_next_task(
                    track_id=self.config.track_id,
                    sprint_id=self.config.sprint_id,
                )

                if task is None:
                    stop_reason = "no_tasks"
                    logger.info("No more executable tasks")
                    break

                # Check stop conditions before executing
                should_stop, reason = self._check_stop_conditions()
                if should_stop:
                    stop_reason = reason
                    break

                # Execute the task
                logger.info(f"Executing task: {task.id} - {task.name}")
                result = await self._execute_task(task)
                self._handle_result(task, result)

                # Auto-save after each task
                if self.config.auto_save:
                    self._save_state()

            # Determine final status
            if stop_reason == "":
                # Normal completion
                stop_reason = "completed"
                self.state.complete()
            elif stop_reason == "signal":
                self.state.stop()
            elif stop_reason == "paused":
                self.state.pause()
            elif stop_reason in ("max_tasks", "max_tokens"):
                self.state.stop()
            else:
                self.state.stop()

            self._save_state()
            return self._to_result(stop_reason)

        except asyncio.CancelledError:
            logger.info("Loop cancelled")
            self.state.stop()
            self._save_state()
            return self._to_result("cancelled")

        except Exception as e:
            logger.exception(f"Loop failed with error: {e}")
            self.state.stop()
            self._save_state()
            result = self._to_result("error")
            result.task_results.append(
                TaskResult(
                    task_id="loop",
                    success=False,
                    error_message=str(e),
                )
            )
            return result

        finally:
            self._restore_signal_handlers()

    # =========================================================================
    # STOP CONDITIONS
    # =========================================================================

    def _should_stop(self) -> bool:
        """
        Check if the loop should stop.

        Returns:
            True if any stop condition is met.
        """
        should_stop, _ = self._check_stop_conditions()
        return should_stop

    def _check_stop_conditions(self) -> tuple[bool, str]:
        """
        Check all stop conditions.

        Returns:
            Tuple of (should_stop: bool, reason: str)
        """
        # Check shutdown signal
        if self._shutdown_requested:
            return True, "signal"

        # Check pause state
        if self.state.status == LoopStatus.PAUSED:
            return True, "paused"

        # Check max tasks
        if self.config.max_tasks is not None:
            if self.state.tasks_attempted >= self.config.max_tasks:
                logger.info(f"Max tasks reached: {self.config.max_tasks}")
                return True, "max_tasks"

        # Check token budget
        if self.config.max_tokens is not None:
            if self.state.total_tokens >= self.config.max_tokens:
                logger.info(f"Token budget exhausted: {self.state.total_tokens}")
                return True, "max_tokens"

        return False, ""

    # =========================================================================
    # TASK EXECUTION
    # =========================================================================

    async def _execute_task(self, task: HierarchicalTicket) -> ExecutionResult:
        """
        Execute a single task with cancellation support.

        Args:
            task: The task to execute.

        Returns:
            ExecutionResult from the executor.
        """
        try:
            # Create cancellable task
            self._current_task_future = asyncio.create_task(
                self.executor.execute(task)
            )
            result = await self._current_task_future
            return result

        except asyncio.CancelledError:
            logger.info(f"Task {task.id} was cancelled")
            return ExecutionResult(
                success=False,
                error_message="Task cancelled by shutdown signal",
            )

        except Exception as e:
            logger.exception(f"Task {task.id} failed: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
            )

        finally:
            self._current_task_future = None

    def _handle_result(self, task: HierarchicalTicket, result: ExecutionResult) -> None:
        """
        Update state based on task execution result.

        Args:
            task: The task that was executed.
            result: The execution result.
        """
        # Create task result tracking
        task_result = self.state.start_task(task.id)

        if result.success:
            self.state.complete_task(
                task_result,
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
                commits=result.commits,
            )
            logger.info(
                f"Task {task.id} completed successfully "
                f"(tokens: {result.tokens_input}+{result.tokens_output})"
            )
        else:
            self.state.fail_task(
                task_result,
                error_message=result.error_message or "Unknown error",
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
            )
            logger.warning(f"Task {task.id} failed: {result.error_message}")

    # =========================================================================
    # SIGNAL HANDLING
    # =========================================================================

    def _install_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown."""
        try:
            loop = asyncio.get_running_loop()

            # Store original handlers
            self._original_sigint = signal.getsignal(signal.SIGINT)
            self._original_sigterm = signal.getsignal(signal.SIGTERM)

            # Install new handlers using loop.add_signal_handler for async safety
            loop.add_signal_handler(signal.SIGINT, self._handle_signal, signal.SIGINT)
            loop.add_signal_handler(signal.SIGTERM, self._handle_signal, signal.SIGTERM)

            logger.debug("Signal handlers installed")

        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            # Fall back to traditional signal handling
            self._original_sigint = signal.signal(signal.SIGINT, self._sync_signal_handler)
            self._original_sigterm = signal.signal(signal.SIGTERM, self._sync_signal_handler)
            logger.debug("Fallback signal handlers installed")

        except RuntimeError:
            # Not in an async context yet
            logger.debug("Cannot install signal handlers outside async context")

    def _restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        try:
            loop = asyncio.get_running_loop()

            # Remove our handlers
            loop.remove_signal_handler(signal.SIGINT)
            loop.remove_signal_handler(signal.SIGTERM)

            # Restore original handlers
            if self._original_sigint is not None:
                signal.signal(signal.SIGINT, self._original_sigint)
            if self._original_sigterm is not None:
                signal.signal(signal.SIGTERM, self._original_sigterm)

            logger.debug("Signal handlers restored")

        except (NotImplementedError, RuntimeError, ValueError):
            # Restore fallback handlers
            if self._original_sigint is not None:
                try:
                    signal.signal(signal.SIGINT, self._original_sigint)
                except (ValueError, TypeError):
                    pass
            if self._original_sigterm is not None:
                try:
                    signal.signal(signal.SIGTERM, self._original_sigterm)
                except (ValueError, TypeError):
                    pass

    def _handle_signal(self, sig: signal.Signals) -> None:
        """
        Handle shutdown signals.

        Args:
            sig: The signal received.
        """
        logger.info(f"Received signal {sig.name}, requesting shutdown")
        self._shutdown_requested = True

        # Cancel current task if running
        if self._current_task_future is not None and not self._current_task_future.done():
            self._current_task_future.cancel()

    def _sync_signal_handler(self, sig: int, frame: Any) -> None:
        """
        Synchronous signal handler (fallback for Windows).

        Args:
            sig: Signal number.
            frame: Current stack frame.
        """
        self._handle_signal(signal.Signals(sig))

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def _save_state(self) -> None:
        """Persist current state to disk."""
        if self.config.state_path is not None:
            try:
                self.state.save(self.config.state_path)
                logger.debug(f"State saved to {self.config.state_path}")
            except Exception as e:
                logger.warning(f"Failed to save state: {e}")

    def _to_result(self, stop_reason: str) -> LoopResult:
        """
        Convert current state to a LoopResult.

        Args:
            stop_reason: Why the loop stopped.

        Returns:
            LoopResult summary of the session.
        """
        return LoopResult(
            session_id=self.state.session_id,
            status=self.state.status,
            started_at=self.state.started_at,
            ended_at=self.state.ended_at or datetime.now(timezone.utc),
            tasks_attempted=self.state.tasks_attempted,
            tasks_completed=self.state.tasks_completed,
            tasks_failed=self.state.tasks_failed,
            tasks_blocked=self.state.tasks_blocked,
            tokens_input=self.state.tokens_input,
            tokens_output=self.state.tokens_output,
            task_results=list(self.state.task_results),
            stop_reason=stop_reason,
        )

    # =========================================================================
    # PUBLIC CONTROL METHODS
    # =========================================================================

    def pause(self) -> None:
        """
        Request the loop to pause.

        The loop will stop after the current task completes and can be
        resumed later by loading the saved state.
        """
        logger.info("Pause requested")
        self.state.pause()
        self._save_state()

    def request_shutdown(self) -> None:
        """
        Request graceful shutdown.

        Similar to receiving SIGINT/SIGTERM but callable programmatically.
        """
        logger.info("Shutdown requested programmatically")
        self._shutdown_requested = True

        # Cancel current task if running
        if self._current_task_future is not None and not self._current_task_future.done():
            self._current_task_future.cancel()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def run_implementation_loop(
    roadmap_root: Path,
    executor: TaskExecutor,
    config: Optional[ImplementConfig] = None,
) -> LoopResult:
    """
    Convenience function to run the implementation loop.

    Creates a TaskSelector and ImplementationLoop with the given configuration
    and runs until completion.

    Args:
        roadmap_root: Path to .vibey/roadmap directory
        executor: TaskExecutor implementation
        config: Optional configuration (uses defaults if not provided)

    Returns:
        LoopResult with execution summary

    Example:
        >>> result = await run_implementation_loop(
        ...     roadmap_root=Path(".vibey/roadmap"),
        ...     executor=my_executor,
        ...     config=ImplementConfig(max_tasks=5),
        ... )
    """
    if config is None:
        config = ImplementConfig()

    selector = TaskSelector(roadmap_root)
    loop = ImplementationLoop(selector, executor, config)

    return await loop.run()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ImplementConfig",
    "ExecutionResult",
    "TaskExecutor",
    "LoopResult",
    "ImplementationLoop",
    "run_implementation_loop",
]
