"""
Structured Logging for Implementation Mode Execution.

This module provides the ExecutionLogger class for recording execution events
to a JSONL activity log. Events include session start/end, task start/complete/error,
and resource usage tracking.

Log File Location: .vibey/implementation/activity.jsonl

Each line is a complete JSON object representing one execution event:
- session_start: Loop session began
- session_end: Loop session ended with summary
- task_start: Task execution began
- task_complete: Task finished successfully
- task_error: Task failed with error details

Usage:
    from vibey.services.implementation.logging import ExecutionLogger
    from pathlib import Path

    logger = ExecutionLogger(Path(".vibey/implementation/activity.jsonl"))

    # Start a session
    logger.start_session(session_id="01KC...")

    # Log task events
    logger.log_task_start(task)
    logger.log_task_complete(task, result)
    # or
    logger.log_task_error(task, exception)

    # End session
    logger.end_session(state)

Design Reference:
- Implementation Mode Track Sprint 1
- Task N8: Implement structured logging for execution
- Pattern: vibey/operations/roadmap/jsonl_activity_log.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.services.implementation.result import ExecutionResult, ExecutionStatus
from vibey.services.implementation.state import LoopState


# =============================================================================
# CROSS-PLATFORM FILE LOCKING
# =============================================================================

if sys.platform == "win32":
    import msvcrt

    def _lock_file(f) -> None:
        """Lock file on Windows."""
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(f) -> None:
        """Unlock file on Windows."""
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock_file(f) -> None:
        """Lock file on Unix."""
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock_file(f) -> None:
        """Unlock file on Unix."""
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


# =============================================================================
# EVENT TYPES
# =============================================================================


class ExecutionEventType:
    """Event types for execution logging."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    TASK_BLOCKED = "task_blocked"


# =============================================================================
# EXECUTION LOGGER
# =============================================================================


class ExecutionLogger:
    """
    Structured logger for implementation mode execution events.

    Logs events to a JSONL file with atomic writes and file locking
    for concurrent safety. Each event includes a timestamp, session ID,
    and event-specific details.

    Attributes:
        log_path: Path to the JSONL activity log file
        session_id: Current session ID (set via start_session)

    Example:
        >>> logger = ExecutionLogger(Path(".vibey/implementation/activity.jsonl"))
        >>> logger.start_session("01KC2D0JK9JKQXGQW6MQEB0JZP")
        >>> logger.log_task_start(task)
        >>> logger.log_task_complete(task, result)
        >>> logger.end_session(state)
    """

    def __init__(self, activity_log_path: Path):
        """
        Initialize the execution logger.

        Args:
            activity_log_path: Path to the JSONL activity log file.
                Parent directories will be created if they don't exist.
        """
        self.log_path = Path(activity_log_path)
        self.session_id: Optional[str] = None

        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # SESSION LIFECYCLE
    # =========================================================================

    def start_session(self, session_id: str) -> None:
        """
        Log session start event.

        Args:
            session_id: Unique identifier for this execution session (ULID)
        """
        self.session_id = session_id
        self._log(
            {
                "event": ExecutionEventType.SESSION_START,
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def end_session(self, state: LoopState) -> None:
        """
        Log session end with summary.

        Args:
            state: Final loop state containing execution summary
        """
        event = {
            "event": ExecutionEventType.SESSION_END,
            "session_id": self.session_id or state.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "status": state.status.value,
                "started_at": state.started_at.isoformat(),
                "ended_at": (
                    state.ended_at.isoformat() if state.ended_at else None
                ),
                "duration_seconds": (
                    round(state.elapsed_seconds, 2)
                ),
                "progress": {
                    "tasks_attempted": state.tasks_attempted,
                    "tasks_completed": state.tasks_completed,
                    "tasks_failed": state.tasks_failed,
                    "tasks_blocked": state.tasks_blocked,
                    "success_rate": (
                        round(state.success_rate, 4)
                        if state.success_rate is not None
                        else None
                    ),
                },
                "tokens": {
                    "input": state.tokens_input,
                    "output": state.tokens_output,
                    "total": state.total_tokens,
                },
            },
        }
        self._log(event)
        self.session_id = None

    # =========================================================================
    # TASK EVENTS
    # =========================================================================

    def log_task_start(self, task: HierarchicalTicket) -> None:
        """
        Log task execution start.

        Args:
            task: The task ticket being executed
        """
        self._log(
            {
                "event": ExecutionEventType.TASK_START,
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task.id,
                "task_name": task.name,
                "task_status": task.status.value if task.status else None,
            }
        )

    def log_task_complete(
        self,
        task: HierarchicalTicket,
        result: ExecutionResult,
    ) -> None:
        """
        Log task completion with result.

        Args:
            task: The completed task ticket
            result: Execution result with status, timing, and resource usage
        """
        self._log(
            {
                "event": ExecutionEventType.TASK_COMPLETE,
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task.id,
                "task_name": task.name,
                "status": result.status.value,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat(),
                "duration_seconds": round(result.duration_seconds, 2),
                "tokens_input": result.tokens_input,
                "tokens_output": result.tokens_output,
                "tokens_total": result.total_tokens,
                "files_modified": [str(p) for p in result.files_modified],
                "files_created": [str(p) for p in result.files_created],
                "commits": result.commits,
                "agent_model": result.agent_model,
            }
        )

    def log_task_error(
        self,
        task: HierarchicalTicket,
        error: Exception,
    ) -> None:
        """
        Log task execution error.

        Args:
            task: The task that failed
            error: The exception that occurred
        """
        self._log(
            {
                "event": ExecutionEventType.TASK_ERROR,
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task.id,
                "task_name": task.name,
                "error_type": type(error).__name__,
                "error_message": str(error),
            }
        )

    def log_task_blocked(
        self,
        task: HierarchicalTicket,
        blocking_reasons: List[str],
    ) -> None:
        """
        Log task blocked due to unmet dependencies.

        Args:
            task: The blocked task
            blocking_reasons: List of reasons why the task is blocked
        """
        self._log(
            {
                "event": ExecutionEventType.TASK_BLOCKED,
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task.id,
                "task_name": task.name,
                "blocking_reasons": blocking_reasons,
            }
        )

    # =========================================================================
    # INTERNAL LOGGING
    # =========================================================================

    def _log(self, event: Dict[str, Any]) -> None:
        """
        Append event to JSONL activity log.

        Uses atomic write pattern: write to temp file, then rename.
        Falls back to direct append with file locking if rename fails.

        Args:
            event: Dictionary representing the event to log
        """
        json_line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))

        # Try atomic append (write to temp, append to log)
        try:
            self._atomic_append(json_line)
        except OSError:
            # Fallback to locked append
            self._locked_append(json_line)

    def _atomic_append(self, json_line: str) -> None:
        """
        Append using atomic write pattern.

        Writes to a temp file first, then appends to the main log.
        This helps prevent corruption on crashes.

        Args:
            json_line: JSON string to append (without newline)
        """
        # Write to temp file first
        fd, temp_path = tempfile.mkstemp(
            suffix=".jsonl",
            prefix="vibey_exec_",
            dir=self.log_path.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json_line + "\n")

            # Now append to the actual log with locking
            with open(self.log_path, "a", encoding="utf-8") as f:
                _lock_file(f)
                try:
                    # Read temp file and append
                    with open(temp_path, "r", encoding="utf-8") as temp_f:
                        f.write(temp_f.read())
                finally:
                    _unlock_file(f)
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _locked_append(self, json_line: str) -> None:
        """
        Append with file locking (fallback).

        Args:
            json_line: JSON string to append (without newline)
        """
        with open(self.log_path, "a", encoding="utf-8") as f:
            try:
                _lock_file(f)
                f.write(json_line + "\n")
            finally:
                _unlock_file(f)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ExecutionLogger",
    "ExecutionEventType",
]
