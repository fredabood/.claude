"""
Token Tracker Service for runtime token usage tracking.

This service tracks actual token usage during task execution and persists
the usage data to task YAML files. It supports:
- Recording token usage from API calls
- Tracking budget remaining
- Git commit integration with per-commit usage logs
- Checkpoint management for delta calculations

Usage:
    from vibey.services.token_tracker import TokenTracker

    # Initialize tracker for a task
    tracker = TokenTracker(task_id="01KCYA0G5135Z8B8ENFD841B13")

    # Record usage during execution
    tracker.record_usage(input_tokens=1500, output_tokens=500)
    tracker.record_usage(input_tokens=2000, output_tokens=800)

    # Check remaining budget
    input_remaining, output_remaining = tracker.get_remaining_budget()

    # Save usage to task YAML
    tracker.save()

    # Git commit integration
    tracker.on_commit("abc123def456")

Design Reference: Sprint 3 - Budget Enforcement
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TokenDelta:
    """
    Token usage delta between checkpoints.

    Represents the change in token usage since the last checkpoint
    (typically a git commit).
    """

    input: int = 0
    output: int = 0

    @property
    def total(self) -> int:
        """Total tokens in this delta."""
        return self.input + self.output


@dataclass
class CommitUsage:
    """
    Token usage record for a git commit.

    Stores both the delta (usage since last commit) and cumulative
    (total usage up to this commit) token counts.
    """

    sha: str
    input_delta: int
    output_delta: int
    cumulative_input: int
    cumulative_output: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ticket_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "commit": self.sha,
            "ticket_id": self.ticket_id,
            "timestamp": self.timestamp.isoformat(),
            "tokens": {
                "input": {
                    "delta": self.input_delta,
                    "cumulative": self.cumulative_input,
                },
                "output": {
                    "delta": self.output_delta,
                    "cumulative": self.cumulative_output,
                },
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommitUsage":
        """Create from dictionary (YAML deserialization)."""
        tokens = data.get("tokens", {})
        input_tokens = tokens.get("input", {})
        output_tokens = tokens.get("output", {})

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            sha=data.get("commit", ""),
            ticket_id=data.get("ticket_id"),
            input_delta=input_tokens.get("delta", 0),
            output_delta=output_tokens.get("delta", 0),
            cumulative_input=input_tokens.get("cumulative", 0),
            cumulative_output=output_tokens.get("cumulative", 0),
            timestamp=timestamp,
        )


# =============================================================================
# TOKEN TRACKER SERVICE
# =============================================================================


class TokenTracker:
    """
    Runtime token usage tracker for task execution.

    Tracks accumulated token usage during task execution and provides
    methods for:
    - Recording usage from API calls
    - Checking remaining budget
    - Persisting usage to task YAML
    - Git commit integration with per-commit usage logs

    Thread Safety: This class is NOT thread-safe. Use separate instances
    per thread or add external synchronization if needed.

    State Management:
    - Usage is accumulated in memory during execution
    - Call save() to persist to task YAML
    - Commit checkpoints track delta since last commit
    """

    def __init__(
        self,
        task_id: str,
        root_dir: Optional[Path] = None,
    ):
        """
        Initialize token tracker for a task.

        Args:
            task_id: ID of the task to track (ULID format)
            root_dir: Root directory containing .vibey/ (defaults to cwd)
        """
        self.task_id = task_id
        self.root_dir = root_dir or Path.cwd()

        # Accumulated usage (in memory during execution)
        self._input_accumulated: int = 0
        self._output_accumulated: int = 0

        # Commit checkpoint tracking
        self._last_commit_input: int = 0
        self._last_commit_output: int = 0
        self._commit_history: List[CommitUsage] = []

        # Load existing usage from task if available
        self._load_existing_usage()

    def _get_task_path(self) -> Path:
        """Get path to task YAML file."""
        return self.root_dir / ".vibey" / "roadmap" / "tasks" / f"{self.task_id}.yaml"

    def _get_commits_dir(self) -> Path:
        """Get path to commits directory."""
        return self.root_dir / ".vibey" / "context" / "commits"

    def _get_commit_usage_path(self, sha: str) -> Path:
        """Get path to usage.yaml for a specific commit."""
        return self._get_commits_dir() / sha / "usage.yaml"

    def _load_existing_usage(self) -> None:
        """Load existing usage from task YAML if available."""
        task_path = self._get_task_path()
        if not task_path.exists():
            return

        try:
            with open(task_path, "r") as f:
                data = yaml.safe_load(f)

            # Handle nested 'task' key
            if "task" in data:
                data = data["task"]

            # Load input usage
            input_tokens = data.get("input_tokens", {})
            if isinstance(input_tokens, dict):
                usage = input_tokens.get("usage")
                if usage is not None:
                    self._input_accumulated = usage
                    self._last_commit_input = usage

            # Load output usage
            output_tokens = data.get("output_tokens", {})
            if isinstance(output_tokens, dict):
                usage = output_tokens.get("usage")
                if usage is not None:
                    self._output_accumulated = usage
                    self._last_commit_output = usage

        except Exception:
            # If we can't load, start fresh
            pass

    def _load_task(self) -> Dict[str, Any]:
        """
        Load task data from YAML file.

        Returns:
            Task dictionary from YAML

        Raises:
            FileNotFoundError: If task file doesn't exist
        """
        task_path = self._get_task_path()
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")

        with open(task_path, "r") as f:
            data = yaml.safe_load(f)

        # Handle nested 'task' key
        if "task" in data:
            return data["task"]
        return data

    def _save_task(self, task_data: Dict[str, Any]) -> None:
        """
        Save task data to YAML file.

        Args:
            task_data: Task dictionary to save
        """
        task_path = self._get_task_path()
        task_path.parent.mkdir(parents=True, exist_ok=True)

        # Wrap in 'task' key for v2 format
        data = {"task": task_data}

        with open(task_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        """
        Record token usage from an API call.

        Accumulates usage during execution. Call save() to persist.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        if input_tokens < 0:
            raise ValueError("input_tokens must be non-negative")
        if output_tokens < 0:
            raise ValueError("output_tokens must be non-negative")

        self._input_accumulated += input_tokens
        self._output_accumulated += output_tokens

    def get_accumulated_usage(self) -> Tuple[int, int]:
        """
        Get current accumulated usage.

        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        return (self._input_accumulated, self._output_accumulated)

    def get_remaining_budget(self) -> Tuple[Optional[int], Optional[int]]:
        """
        Get remaining budget for each direction.

        Returns:
            Tuple of (input_remaining, output_remaining).
            None if no budget set for that direction.
        """
        try:
            task = self._load_task()
        except FileNotFoundError:
            return (None, None)

        input_remaining: Optional[int] = None
        output_remaining: Optional[int] = None

        # Check input budget
        input_tokens = task.get("input_tokens", {})
        if isinstance(input_tokens, dict):
            budget = input_tokens.get("budget")
            if budget is not None:
                input_remaining = budget - self._input_accumulated

        # Check output budget
        output_tokens = task.get("output_tokens", {})
        if isinstance(output_tokens, dict):
            budget = output_tokens.get("budget")
            if budget is not None:
                output_remaining = budget - self._output_accumulated

        return (input_remaining, output_remaining)

    def is_over_budget(self) -> Tuple[bool, bool]:
        """
        Check if usage exceeds budget for each direction.

        Returns:
            Tuple of (input_over, output_over) booleans.
            False if no budget set for that direction.
        """
        input_remaining, output_remaining = self.get_remaining_budget()

        input_over = input_remaining is not None and input_remaining < 0
        output_over = output_remaining is not None and output_remaining < 0

        return (input_over, output_over)

    def get_budget_ratio(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get usage as a ratio of budget for each direction.

        Returns:
            Tuple of (input_ratio, output_ratio).
            None if no budget set for that direction.
            Ratio > 1.0 means over budget.
        """
        try:
            task = self._load_task()
        except FileNotFoundError:
            return (None, None)

        input_ratio: Optional[float] = None
        output_ratio: Optional[float] = None

        # Check input budget
        input_tokens = task.get("input_tokens", {})
        if isinstance(input_tokens, dict):
            budget = input_tokens.get("budget")
            if budget is not None and budget > 0:
                input_ratio = self._input_accumulated / budget

        # Check output budget
        output_tokens = task.get("output_tokens", {})
        if isinstance(output_tokens, dict):
            budget = output_tokens.get("budget")
            if budget is not None and budget > 0:
                output_ratio = self._output_accumulated / budget

        return (input_ratio, output_ratio)

    def save(self) -> None:
        """
        Persist accumulated usage to task YAML.

        Updates task.input_tokens.usage and task.output_tokens.usage.
        Creates Tokens objects if they don't exist.
        """
        try:
            task = self._load_task()
        except FileNotFoundError:
            # Create minimal task structure
            task = {
                "id": self.task_id,
                "format_version": "v2",
            }

        # Update input tokens
        input_tokens = task.get("input_tokens", {})
        if not isinstance(input_tokens, dict):
            input_tokens = {}
        input_tokens["usage"] = self._input_accumulated
        task["input_tokens"] = input_tokens

        # Update output tokens
        output_tokens = task.get("output_tokens", {})
        if not isinstance(output_tokens, dict):
            output_tokens = {}
        output_tokens["usage"] = self._output_accumulated
        task["output_tokens"] = output_tokens

        # Update metadata timestamp
        metadata = task.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
        task["metadata"] = metadata

        self._save_task(task)

    # =========================================================================
    # GIT COMMIT INTEGRATION
    # =========================================================================

    def get_delta_since_last_commit(self) -> TokenDelta:
        """
        Get usage since last commit checkpoint.

        Returns:
            TokenDelta with input and output deltas
        """
        return TokenDelta(
            input=self._input_accumulated - self._last_commit_input,
            output=self._output_accumulated - self._last_commit_output,
        )

    def mark_commit_checkpoint(self, commit_sha: str) -> CommitUsage:
        """
        Mark current usage as checkpoint after commit.

        Records the delta since last checkpoint and updates the
        checkpoint to current values.

        Args:
            commit_sha: Git commit SHA

        Returns:
            CommitUsage record for this checkpoint
        """
        delta = self.get_delta_since_last_commit()

        usage_record = CommitUsage(
            sha=commit_sha,
            ticket_id=self.task_id,
            input_delta=delta.input,
            output_delta=delta.output,
            cumulative_input=self._input_accumulated,
            cumulative_output=self._output_accumulated,
        )

        self._commit_history.append(usage_record)

        # Update checkpoint to current values
        self._last_commit_input = self._input_accumulated
        self._last_commit_output = self._output_accumulated

        return usage_record

    def _record_commit_usage(self, commit_sha: str, usage_record: CommitUsage) -> None:
        """
        Record per-commit usage to .vibey/context/commits/<sha>/usage.yaml.

        Args:
            commit_sha: Git commit SHA
            usage_record: CommitUsage record to save
        """
        usage_path = self._get_commit_usage_path(commit_sha)
        usage_path.parent.mkdir(parents=True, exist_ok=True)

        with open(usage_path, "w") as f:
            yaml.dump(
                usage_record.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def on_commit(self, commit_sha: str) -> CommitUsage:
        """
        Handle git commit event.

        Called by post-commit hook. Records usage delta and updates ticket.

        Steps:
        1. Save current usage to task YAML
        2. Record per-commit usage breakdown
        3. Mark commit checkpoint

        Args:
            commit_sha: Git commit SHA

        Returns:
            CommitUsage record for this commit
        """
        # Save current usage to task
        self.save()

        # Mark checkpoint and get usage record
        usage_record = self.mark_commit_checkpoint(commit_sha)

        # Record per-commit usage
        self._record_commit_usage(commit_sha, usage_record)

        return usage_record

    def get_commit_history(self) -> List[CommitUsage]:
        """
        Get history of commit checkpoints.

        Returns:
            List of CommitUsage records in chronological order
        """
        return list(self._commit_history)

    def load_commit_usage(self, commit_sha: str) -> Optional[CommitUsage]:
        """
        Load usage record for a specific commit.

        Args:
            commit_sha: Git commit SHA

        Returns:
            CommitUsage record if found, None otherwise
        """
        usage_path = self._get_commit_usage_path(commit_sha)
        if not usage_path.exists():
            return None

        try:
            with open(usage_path, "r") as f:
                data = yaml.safe_load(f)
            return CommitUsage.from_dict(data)
        except Exception:
            return None

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def reset(self) -> None:
        """
        Reset accumulated usage to zero.

        Use with caution - this does NOT update the task YAML.
        Call save() after reset to persist the change.
        """
        self._input_accumulated = 0
        self._output_accumulated = 0
        self._last_commit_input = 0
        self._last_commit_output = 0
        self._commit_history = []

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of current tracking state.

        Returns:
            Dictionary with tracking summary
        """
        input_remaining, output_remaining = self.get_remaining_budget()
        input_ratio, output_ratio = self.get_budget_ratio()
        input_over, output_over = self.is_over_budget()
        delta = self.get_delta_since_last_commit()

        return {
            "task_id": self.task_id,
            "accumulated": {
                "input": self._input_accumulated,
                "output": self._output_accumulated,
                "total": self._input_accumulated + self._output_accumulated,
            },
            "remaining": {
                "input": input_remaining,
                "output": output_remaining,
            },
            "ratio": {
                "input": round(input_ratio, 4) if input_ratio is not None else None,
                "output": round(output_ratio, 4) if output_ratio is not None else None,
            },
            "over_budget": {
                "input": input_over,
                "output": output_over,
            },
            "delta_since_last_commit": {
                "input": delta.input,
                "output": delta.output,
            },
            "commit_checkpoints": len(self._commit_history),
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def track_usage(
    task_id: str,
    input_tokens: int,
    output_tokens: int,
    root_dir: Optional[Path] = None,
) -> TokenTracker:
    """
    Convenience function to record usage and save in one call.

    Args:
        task_id: Task ID to track
        input_tokens: Input tokens to record
        output_tokens: Output tokens to record
        root_dir: Optional root directory

    Returns:
        TokenTracker instance (already saved)
    """
    tracker = TokenTracker(task_id, root_dir=root_dir)
    tracker.record_usage(input_tokens, output_tokens)
    tracker.save()
    return tracker


def get_task_usage(
    task_id: str,
    root_dir: Optional[Path] = None,
) -> Tuple[int, int]:
    """
    Convenience function to get current usage for a task.

    Args:
        task_id: Task ID to check
        root_dir: Optional root directory

    Returns:
        Tuple of (input_usage, output_usage)
    """
    tracker = TokenTracker(task_id, root_dir=root_dir)
    return tracker.get_accumulated_usage()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "TokenTracker",
    # Data models
    "TokenDelta",
    "CommitUsage",
    # Convenience functions
    "track_usage",
    "get_task_usage",
]
