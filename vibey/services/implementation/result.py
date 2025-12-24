"""
ExecutionResult - Captures outcomes from task execution.

This module provides the ExecutionResult dataclass for tracking the complete
outcome of executing a single task, including status, timing, resource usage,
artifacts produced, and any errors encountered.

Usage:
    from vibey.services.implementation.result import ExecutionResult, ExecutionStatus
    from datetime import datetime, timezone
    from pathlib import Path

    # Create a successful result
    result = ExecutionResult(
        task_id="01KCZF73PX9YNKWXKYVARY89N3",
        status=ExecutionStatus.SUCCESS,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        tokens_input=1500,
        tokens_output=500,
        files_modified=[Path("vibey/cli/commands.py")],
        commits=["abc123def"],
    )

    # Check status
    if result.succeeded:
        print(f"Task completed in {result.duration}")
    else:
        print(f"Task failed: {result.error_message}")

    # Serialize for storage
    data = result.to_dict()

Design Reference:
- Implementation Mode Track Sprint 1
- Task N6: Implement ExecutionResult for capturing outcomes
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# ENUMS
# =============================================================================


class ExecutionStatus(str, Enum):
    """
    Status of a task execution.

    Values:
        SUCCESS: Task completed successfully
        FAILURE: Task failed during execution
        BLOCKED: Task was blocked by dependencies or preconditions
        TIMEOUT: Task exceeded time limit
        CANCELLED: Task was cancelled by user or system
    """

    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# =============================================================================
# EXECUTION RESULT
# =============================================================================


@dataclass
class ExecutionResult:
    """
    Result of executing a single task.

    Captures the complete outcome of task execution including:
    - Status and timing information
    - Token usage for LLM calls
    - Artifacts produced (files modified/created, commits)
    - Output streams (stdout, stderr)
    - Error information if failed

    Attributes:
        task_id: ULID of the executed task
        status: Execution outcome status
        started_at: When execution began
        completed_at: When execution finished

        tokens_input: Input tokens consumed during execution
        tokens_output: Output tokens generated during execution

        files_modified: Paths to files that were modified
        files_created: Paths to files that were created
        commits: Git commit SHAs created during execution

        stdout: Standard output captured during execution
        stderr: Standard error captured during execution
        error_message: Error description if task failed

        agent_model: Model identifier used for execution
        exit_code: Process exit code (0 = success)

    Example:
        >>> result = ExecutionResult(
        ...     task_id="01KCZF73PX9YNKWXKYVARY89N3",
        ...     status=ExecutionStatus.SUCCESS,
        ...     started_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        ...     completed_at=datetime(2024, 1, 15, 10, 5, 30, tzinfo=timezone.utc),
        ...     tokens_input=1500,
        ...     tokens_output=500,
        ...     files_modified=[Path("src/main.py")],
        ...     commits=["abc123"],
        ... )
        >>> result.succeeded
        True
        >>> result.duration
        datetime.timedelta(seconds=330)
    """

    # Required fields
    task_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: datetime

    # Token usage
    tokens_input: int = 0
    tokens_output: int = 0

    # Artifacts
    files_modified: List[Path] = field(default_factory=list)
    files_created: List[Path] = field(default_factory=list)
    commits: List[str] = field(default_factory=list)

    # Output
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None

    # Metadata
    agent_model: str = "claude-sonnet-4-20250514"
    exit_code: int = 0

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def duration(self) -> timedelta:
        """
        Calculate execution duration.

        Returns:
            Time elapsed between started_at and completed_at.
        """
        return self.completed_at - self.started_at

    @property
    def succeeded(self) -> bool:
        """
        Check if execution was successful.

        Returns:
            True if status is SUCCESS, False otherwise.
        """
        return self.status == ExecutionStatus.SUCCESS

    @property
    def total_tokens(self) -> int:
        """
        Total tokens consumed (input + output).

        Returns:
            Sum of tokens_input and tokens_output.
        """
        return self.tokens_input + self.tokens_output

    @property
    def duration_seconds(self) -> float:
        """
        Calculate execution duration in seconds.

        Returns:
            Duration as floating-point seconds.
        """
        return self.duration.total_seconds()

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize for logging/storage.

        Converts the ExecutionResult to a dictionary suitable for
        YAML or JSON serialization.

        Returns:
            Dictionary representation of the result.

        Example:
            >>> result.to_dict()
            {
                'task_id': '01KCZF73PX9YNKWXKYVARY89N3',
                'status': 'success',
                'started_at': '2024-01-15T10:00:00+00:00',
                ...
            }
        """
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "tokens": {
                "input": self.tokens_input,
                "output": self.tokens_output,
                "total": self.total_tokens,
            },
            "artifacts": {
                "files_modified": [str(p) for p in self.files_modified],
                "files_created": [str(p) for p in self.files_created],
                "commits": self.commits,
            },
            "output": {
                "stdout": self.stdout,
                "stderr": self.stderr,
                "error_message": self.error_message,
            },
            "metadata": {
                "agent_model": self.agent_model,
                "exit_code": self.exit_code,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        """
        Deserialize from dictionary.

        Creates an ExecutionResult from a dictionary, typically loaded
        from YAML or JSON storage.

        Args:
            data: Dictionary representation of an ExecutionResult.

        Returns:
            ExecutionResult instance.

        Example:
            >>> data = {'task_id': '01KCZF...', 'status': 'success', ...}
            >>> result = ExecutionResult.from_dict(data)
        """
        # Parse timestamps
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        elif started_at is None:
            started_at = datetime.now(timezone.utc)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        elif completed_at is None:
            completed_at = datetime.now(timezone.utc)

        # Parse status
        status_str = data.get("status", "failure")
        try:
            status = ExecutionStatus(status_str)
        except ValueError:
            status = ExecutionStatus.FAILURE

        # Parse tokens (support both nested and flat formats)
        tokens = data.get("tokens", {})
        tokens_input = tokens.get("input", data.get("tokens_input", 0))
        tokens_output = tokens.get("output", data.get("tokens_output", 0))

        # Parse artifacts (support both nested and flat formats)
        artifacts = data.get("artifacts", {})
        files_modified_raw = artifacts.get(
            "files_modified", data.get("files_modified", [])
        )
        files_created_raw = artifacts.get(
            "files_created", data.get("files_created", [])
        )
        commits = artifacts.get("commits", data.get("commits", []))

        # Convert file paths
        files_modified = [Path(p) for p in files_modified_raw]
        files_created = [Path(p) for p in files_created_raw]

        # Parse output (support both nested and flat formats)
        output = data.get("output", {})
        stdout = output.get("stdout", data.get("stdout", ""))
        stderr = output.get("stderr", data.get("stderr", ""))
        error_message = output.get("error_message", data.get("error_message"))

        # Parse metadata (support both nested and flat formats)
        metadata = data.get("metadata", {})
        agent_model = metadata.get(
            "agent_model", data.get("agent_model", "claude-sonnet-4-20250514")
        )
        exit_code = metadata.get("exit_code", data.get("exit_code", 0))

        return cls(
            task_id=data.get("task_id", ""),
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            files_modified=files_modified,
            files_created=files_created,
            commits=commits,
            stdout=stdout,
            stderr=stderr,
            error_message=error_message,
            agent_model=agent_model,
            exit_code=exit_code,
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ExecutionStatus",
    "ExecutionResult",
]
