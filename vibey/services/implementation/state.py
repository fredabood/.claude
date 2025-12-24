"""
Loop State Management for Implementation Mode.

This module provides state tracking for autonomous task execution loops.
The LoopState class maintains mutable state that can be persisted to YAML
for session resume capability.

State File Location: .vibey/implementation/state.yaml

Key Features:
- Session tracking with ULID-based session IDs
- Progress counters (attempted, completed, failed, blocked)
- Token usage aggregation
- Task result history
- YAML serialization for persistence and resume

Usage:
    from vibey.services.implementation.state import LoopState, LoopStatus

    # Start a new execution session
    state = LoopState()
    assert state.status == LoopStatus.RUNNING

    # Track task execution
    state.current_task = "01KCZF73PX9YNKWXKYVARY89N3"
    state.tasks_attempted += 1

    # Record token usage
    state.tokens_input += 1500
    state.tokens_output += 500

    # Mark completion
    state.tasks_completed += 1
    state.current_task = None

    # Persist for resume
    state.save(Path(".vibey/implementation/state.yaml"))

Design Reference:
- Sprint 0: Planning & Design (Context System V2)
- ADR-0001: ULID Identifiers
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from ulid import ULID


# =============================================================================
# ENUMS
# =============================================================================


class LoopStatus(str, Enum):
    """
    Status of the execution loop.

    States:
    - RUNNING: Loop is actively processing tasks
    - PAUSED: Loop is temporarily suspended (can resume)
    - STOPPED: Loop was manually stopped (can restart)
    - COMPLETED: Loop finished processing all tasks
    """

    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TaskResult:
    """
    Result of a single task execution.

    Captures the outcome, timing, and resource usage for a task
    that was processed by the execution loop.

    Attributes:
        task_id: ULID of the executed task
        success: Whether the task completed successfully
        started_at: When task execution began
        ended_at: When task execution finished
        tokens_input: Input tokens consumed
        tokens_output: Output tokens generated
        error_message: Error details if task failed
        commits: Git commit SHAs created during task
    """

    task_id: str
    success: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    tokens_input: int = 0
    tokens_output: int = 0
    error_message: Optional[str] = None
    commits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "error_message": self.error_message,
            "commits": self.commits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskResult":
        """Create from dictionary (YAML deserialization)."""
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        elif started_at is None:
            started_at = datetime.now(timezone.utc)

        ended_at = data.get("ended_at")
        if isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))

        return cls(
            task_id=data.get("task_id", ""),
            success=data.get("success", False),
            started_at=started_at,
            ended_at=ended_at,
            tokens_input=data.get("tokens_input", 0),
            tokens_output=data.get("tokens_output", 0),
            error_message=data.get("error_message"),
            commits=data.get("commits", []),
        )

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds, if ended."""
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.tokens_input + self.tokens_output


# =============================================================================
# LOOP STATE
# =============================================================================


@dataclass
class LoopState:
    """
    Mutable state for the execution loop.

    Tracks all aspects of an autonomous execution session including:
    - Session identity and timing
    - Current execution status
    - Progress counters
    - Resource usage
    - Task execution history

    The state can be persisted to YAML for crash recovery and session resume.

    Attributes:
        session_id: Unique identifier for this execution session (ULID)
        started_at: When the session began
        ended_at: When the session ended (None if still running)
        current_task: ULID of task currently being executed
        status: Current loop status (running, paused, stopped, completed)
        tasks_attempted: Total tasks that execution was attempted on
        tasks_completed: Tasks that completed successfully
        tasks_failed: Tasks that failed during execution
        tasks_blocked: Tasks that were blocked and skipped
        tokens_input: Total input tokens consumed across all tasks
        tokens_output: Total output tokens generated across all tasks
        task_results: History of individual task execution results

    Example:
        >>> state = LoopState()
        >>> state.status
        <LoopStatus.RUNNING: 'running'>
        >>> state.current_task = "01KCZF73PX9YNKWXKYVARY89N3"
        >>> state.tasks_attempted += 1
        >>> state.save(Path(".vibey/implementation/state.yaml"))
    """

    # Session info
    session_id: str = field(default_factory=lambda: str(ULID()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    # Current execution
    current_task: Optional[str] = None
    status: LoopStatus = LoopStatus.RUNNING

    # Progress counters
    tasks_attempted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_blocked: int = 0

    # Resource usage
    tokens_input: int = 0
    tokens_output: int = 0

    # History
    task_results: List[TaskResult] = field(default_factory=list)

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def duration_seconds(self) -> Optional[float]:
        """
        Calculate session duration in seconds.

        Returns:
            Duration in seconds if session has ended, None otherwise.
        """
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    @property
    def elapsed_seconds(self) -> float:
        """
        Calculate elapsed time since session started.

        Returns:
            Elapsed time in seconds (uses current time if not ended).
        """
        end = self.ended_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.tokens_input + self.tokens_output

    @property
    def success_rate(self) -> Optional[float]:
        """
        Calculate task success rate.

        Returns:
            Success rate as float (0.0 to 1.0), None if no tasks attempted.
        """
        if self.tasks_attempted == 0:
            return None
        return self.tasks_completed / self.tasks_attempted

    @property
    def is_running(self) -> bool:
        """Check if the loop is actively running."""
        return self.status == LoopStatus.RUNNING

    @property
    def is_finished(self) -> bool:
        """Check if the loop has finished (stopped or completed)."""
        return self.status in (LoopStatus.STOPPED, LoopStatus.COMPLETED)

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert state to dictionary for YAML serialization.

        Returns:
            Dictionary representation of the state.
        """
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "current_task": self.current_task,
            "status": self.status.value,
            "progress": {
                "tasks_attempted": self.tasks_attempted,
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "tasks_blocked": self.tasks_blocked,
            },
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "total": self.total_tokens,
            },
            "task_results": [result.to_dict() for result in self.task_results],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopState":
        """
        Create LoopState from dictionary (YAML deserialization).

        Args:
            data: Dictionary representation of state.

        Returns:
            LoopState instance.
        """
        # Parse timestamps
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        elif started_at is None:
            started_at = datetime.now(timezone.utc)

        ended_at = data.get("ended_at")
        if isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))

        # Parse status
        status_str = data.get("status", "running")
        try:
            status = LoopStatus(status_str)
        except ValueError:
            status = LoopStatus.RUNNING

        # Parse progress
        progress = data.get("progress", {})

        # Parse tokens
        tokens = data.get("tokens", {})

        # Parse task results
        task_results_data = data.get("task_results", [])
        task_results = [TaskResult.from_dict(r) for r in task_results_data]

        return cls(
            session_id=data.get("session_id", str(ULID())),
            started_at=started_at,
            ended_at=ended_at,
            current_task=data.get("current_task"),
            status=status,
            tasks_attempted=progress.get("tasks_attempted", 0),
            tasks_completed=progress.get("tasks_completed", 0),
            tasks_failed=progress.get("tasks_failed", 0),
            tasks_blocked=progress.get("tasks_blocked", 0),
            tokens_input=tokens.get("input", 0),
            tokens_output=tokens.get("output", 0),
            task_results=task_results,
        )

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save(self, path: Path) -> None:
        """
        Persist state to file for resume.

        Creates parent directories if they don't exist.

        Args:
            path: Path to save state file (typically .vibey/implementation/state.yaml)

        Example:
            >>> state = LoopState()
            >>> state.save(Path(".vibey/implementation/state.yaml"))
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(
                self.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    @classmethod
    def load(cls, path: Path) -> "LoopState":
        """
        Load state from file.

        Args:
            path: Path to state file.

        Returns:
            LoopState instance loaded from file.

        Raises:
            FileNotFoundError: If state file doesn't exist.
            yaml.YAMLError: If file contains invalid YAML.

        Example:
            >>> state = LoopState.load(Path(".vibey/implementation/state.yaml"))
            >>> print(state.session_id)
            01KCZF73PX9YNKWXKYVARY89N3
        """
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        return cls.from_dict(data)

    @classmethod
    def load_or_create(cls, path: Path) -> "LoopState":
        """
        Load existing state or create new if file doesn't exist.

        Args:
            path: Path to state file.

        Returns:
            LoopState instance (loaded or new).

        Example:
            >>> state = LoopState.load_or_create(Path(".vibey/implementation/state.yaml"))
        """
        if path.exists():
            return cls.load(path)
        return cls()

    # =========================================================================
    # STATE TRANSITIONS
    # =========================================================================

    def pause(self) -> None:
        """Pause the execution loop."""
        if self.status == LoopStatus.RUNNING:
            self.status = LoopStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused execution loop."""
        if self.status == LoopStatus.PAUSED:
            self.status = LoopStatus.RUNNING

    def stop(self) -> None:
        """Stop the execution loop."""
        if self.status in (LoopStatus.RUNNING, LoopStatus.PAUSED):
            self.status = LoopStatus.STOPPED
            self.ended_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Mark the execution loop as completed."""
        self.status = LoopStatus.COMPLETED
        self.ended_at = datetime.now(timezone.utc)

    # =========================================================================
    # TASK TRACKING
    # =========================================================================

    def start_task(self, task_id: str) -> TaskResult:
        """
        Mark a task as started.

        Args:
            task_id: ULID of the task to start.

        Returns:
            TaskResult instance for tracking this execution.
        """
        self.current_task = task_id
        self.tasks_attempted += 1

        result = TaskResult(task_id=task_id)
        return result

    def complete_task(
        self,
        result: TaskResult,
        tokens_input: int = 0,
        tokens_output: int = 0,
        commits: Optional[List[str]] = None,
    ) -> None:
        """
        Mark a task as completed successfully.

        Args:
            result: TaskResult from start_task().
            tokens_input: Input tokens consumed.
            tokens_output: Output tokens generated.
            commits: Git commit SHAs created.
        """
        result.success = True
        result.ended_at = datetime.now(timezone.utc)
        result.tokens_input = tokens_input
        result.tokens_output = tokens_output
        if commits:
            result.commits = commits

        self.tasks_completed += 1
        self.tokens_input += tokens_input
        self.tokens_output += tokens_output
        self.task_results.append(result)
        self.current_task = None

    def fail_task(
        self,
        result: TaskResult,
        error_message: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
    ) -> None:
        """
        Mark a task as failed.

        Args:
            result: TaskResult from start_task().
            error_message: Description of what went wrong.
            tokens_input: Input tokens consumed before failure.
            tokens_output: Output tokens generated before failure.
        """
        result.success = False
        result.ended_at = datetime.now(timezone.utc)
        result.error_message = error_message
        result.tokens_input = tokens_input
        result.tokens_output = tokens_output

        self.tasks_failed += 1
        self.tokens_input += tokens_input
        self.tokens_output += tokens_output
        self.task_results.append(result)
        self.current_task = None

    def skip_blocked_task(self, task_id: str) -> None:
        """
        Record a task that was skipped due to blockers.

        Args:
            task_id: ULID of the blocked task.
        """
        self.tasks_blocked += 1

    # =========================================================================
    # SUMMARY
    # =========================================================================

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current state.

        Returns:
            Dictionary with state summary.
        """
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "progress": {
                "attempted": self.tasks_attempted,
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "blocked": self.tasks_blocked,
                "success_rate": (
                    round(self.success_rate, 4) if self.success_rate is not None else None
                ),
            },
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "total": self.total_tokens,
            },
            "current_task": self.current_task,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LoopState",
    "LoopStatus",
    "TaskResult",
]
