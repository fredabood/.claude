"""
ContextCompactor - Token management through context compaction.

This module provides intelligent context compaction for the implementation loop,
reducing context size while preserving essential state for task continuity.

Compaction Strategy:
- Before: Full history, all file contents, detailed logs (~80k tokens)
- After: Session summary, task summaries, state snapshot (~2k tokens)

Preserves:
- Essential session state (session_id, status, progress counters)
- Summary of completed work (task names, statuses, changes)
- Critical errors and blockers
- Git commits and their associations

Removes:
- Verbose execution logs
- Transient file contents
- Intermediate reasoning steps
- Full stdout/stderr output

Usage:
    from vibey.services.implementation.compactor import ContextCompactor, CompactedContext

    # Configure compactor
    compactor = ContextCompactor(max_context_tokens=8000)

    # After each task, check if compaction needed
    if compactor.should_compact(current_token_count):
        context = compactor.compact(state, result)
        # Use context.session_summary for continuation

    # Or generate task summary for logging
    summary = compactor.summarize_task(task, result)

    # Build minimal context for next task
    continuation = compactor.build_continuation_context(state)

Design Reference:
- Context System V2 Track
- Task: Implement ContextCompactor for token management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from vibey.services.implementation.state import LoopState, TaskResult


# =============================================================================
# CONSTANTS
# =============================================================================

# Default token limit before compaction is triggered
DEFAULT_MAX_CONTEXT_TOKENS = 8000

# Approximate tokens per character (conservative estimate for English text)
# GPT-style tokenizers average ~4 chars per token, we use 3.5 for safety
CHARS_PER_TOKEN = 3.5

# Target token count after compaction
TARGET_COMPACTED_TOKENS = 2000


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TaskSummary:
    """
    Concise summary of a completed task.

    Captures the essential information about a task execution
    without the verbose details like full output logs.

    Attributes:
        task_id: ULID of the task
        name: Task title/name
        status: Final status (success/failure/blocked)
        changes: List of significant changes made
        commits: Git commit SHAs created
        notes: Important notes or error messages
        tokens_used: Total tokens consumed
    """

    task_id: str
    name: str
    status: str
    changes: List[str] = field(default_factory=list)
    commits: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    tokens_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "tokens_used": self.tokens_used,
        }
        if self.changes:
            result["changes"] = self.changes
        if self.commits:
            result["commits"] = self.commits
        if self.notes:
            result["notes"] = self.notes
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskSummary":
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id", ""),
            name=data.get("name", ""),
            status=data.get("status", "unknown"),
            changes=data.get("changes", []),
            commits=data.get("commits", []),
            notes=data.get("notes"),
            tokens_used=data.get("tokens_used", 0),
        )


@dataclass
class CompactedContext:
    """
    Compacted context for continuation between tasks.

    This is the minimal context needed to continue an execution
    session after compaction. It reduces ~80k tokens of full
    context to ~2k tokens of essential state.

    Attributes:
        session_summary: High-level session state summary
        task_summaries: Concise summaries of completed tasks
        state_snapshot: Serialized essential state
        total_tokens: Estimated token count of compacted context
        compacted_at: When compaction occurred
    """

    session_summary: str
    task_summaries: List[TaskSummary]
    state_snapshot: Dict[str, Any]
    total_tokens: int
    compacted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_summary": self.session_summary,
            "task_summaries": [ts.to_dict() for ts in self.task_summaries],
            "state_snapshot": self.state_snapshot,
            "total_tokens": self.total_tokens,
            "compacted_at": self.compacted_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompactedContext":
        """Create from dictionary."""
        compacted_at = data.get("compacted_at")
        if isinstance(compacted_at, str):
            compacted_at = datetime.fromisoformat(compacted_at.replace("Z", "+00:00"))
        elif compacted_at is None:
            compacted_at = datetime.utcnow()

        return cls(
            session_summary=data.get("session_summary", ""),
            task_summaries=[
                TaskSummary.from_dict(ts) for ts in data.get("task_summaries", [])
            ],
            state_snapshot=data.get("state_snapshot", {}),
            total_tokens=data.get("total_tokens", 0),
            compacted_at=compacted_at,
        )

    def to_context_string(self) -> str:
        """
        Convert to a string suitable for LLM context.

        Returns:
            Formatted string representation of the compacted context.
        """
        lines = [
            "=== Session Context (Compacted) ===",
            "",
            self.session_summary,
            "",
        ]

        if self.task_summaries:
            lines.append("=== Completed Tasks ===")
            for ts in self.task_summaries:
                lines.append(f"\n[{ts.status.upper()}] {ts.name} ({ts.task_id})")
                if ts.changes:
                    for change in ts.changes[:3]:  # Limit to 3 changes
                        lines.append(f"  - {change}")
                if ts.commits:
                    lines.append(f"  Commits: {', '.join(ts.commits[:3])}")
                if ts.notes:
                    lines.append(f"  Note: {ts.notes[:100]}...")
            lines.append("")

        lines.append("=== State Snapshot ===")
        snapshot = self.state_snapshot
        lines.append(f"Session: {snapshot.get('session_id', 'unknown')}")
        lines.append(f"Status: {snapshot.get('status', 'unknown')}")
        progress = snapshot.get("progress", {})
        lines.append(
            f"Progress: {progress.get('completed', 0)}/{progress.get('attempted', 0)} "
            f"tasks ({progress.get('failed', 0)} failed, {progress.get('blocked', 0)} blocked)"
        )
        tokens = snapshot.get("tokens", {})
        lines.append(f"Tokens used: {tokens.get('total', 0)}")

        return "\n".join(lines)


# =============================================================================
# CONTEXT COMPACTOR
# =============================================================================


class ContextCompactor:
    """
    Intelligent context compaction for token management.

    The ContextCompactor reduces context size while preserving
    essential state needed for task continuity. It's designed
    to work with the implementation loop to prevent context
    overflow during long-running sessions.

    Compaction is triggered when current token usage exceeds
    the configured threshold (default 8000 tokens).

    Attributes:
        max_context_tokens: Token threshold for triggering compaction

    Example:
        >>> compactor = ContextCompactor(max_context_tokens=8000)
        >>> if compactor.should_compact(current_tokens=10000):
        ...     context = compactor.compact(state, last_result)
        ...     print(f"Compacted to {context.total_tokens} tokens")
    """

    def __init__(self, max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS):
        """
        Initialize the context compactor.

        Args:
            max_context_tokens: Maximum tokens before compaction is needed.
                               Defaults to 8000.
        """
        self.max_context_tokens = max_context_tokens

    def compact(
        self,
        state: LoopState,
        result: Optional[TaskResult] = None,
    ) -> CompactedContext:
        """
        Compact context after task completion.

        Reduces full execution context to minimal state while
        preserving essential information for continuation.

        Args:
            state: Current loop state with task history
            result: Optional result from the most recent task

        Returns:
            CompactedContext with minimal token footprint
        """
        # Build session summary
        session_summary = self._build_session_summary(state)

        # Build task summaries from state history
        task_summaries = [
            self._task_result_to_summary(tr) for tr in state.task_results
        ]

        # Build state snapshot
        state_snapshot = self._build_state_snapshot(state)

        # Estimate total tokens
        context = CompactedContext(
            session_summary=session_summary,
            task_summaries=task_summaries,
            state_snapshot=state_snapshot,
            total_tokens=0,  # Will be calculated
        )

        # Calculate actual token count
        context.total_tokens = self.estimate_tokens(context.to_context_string())

        return context

    def summarize_task(
        self,
        task: Any,
        result: TaskResult,
    ) -> TaskSummary:
        """
        Generate a concise summary of a task execution.

        Creates a minimal summary capturing the essential
        outcome of task execution without verbose details.

        Args:
            task: The task object (with id, title attributes)
            result: The execution result

        Returns:
            TaskSummary with key information preserved
        """
        # Extract task name - handle both Task objects and dicts
        if hasattr(task, "title"):
            name = task.title
        elif isinstance(task, dict):
            name = task.get("title", task.get("name", "Unknown Task"))
        else:
            name = str(task)

        # Extract task ID
        if hasattr(task, "id"):
            task_id = task.id
        elif isinstance(task, dict):
            task_id = task.get("id", result.task_id)
        else:
            task_id = result.task_id

        # Determine status string
        status = "success" if result.success else "failure"

        # Build changes list from commits
        changes = []
        for commit in result.commits[:5]:  # Limit to 5 commits
            changes.append(f"Commit: {commit[:8]}")

        # Add error note if failed
        notes = None
        if not result.success and result.error_message:
            # Truncate error message
            notes = result.error_message[:200]

        return TaskSummary(
            task_id=task_id,
            name=name,
            status=status,
            changes=changes,
            commits=result.commits[:5],
            notes=notes,
            tokens_used=result.total_tokens,
        )

    def estimate_tokens(self, context: str) -> int:
        """
        Estimate token count for a string.

        Uses a conservative character-to-token ratio based on
        typical English text tokenization patterns.

        Args:
            context: String to estimate tokens for

        Returns:
            Estimated token count
        """
        if not context:
            return 0
        return int(len(context) / CHARS_PER_TOKEN)

    def should_compact(self, current_tokens: int) -> bool:
        """
        Determine if compaction is needed.

        Args:
            current_tokens: Current context token count

        Returns:
            True if compaction should be performed
        """
        return current_tokens > self.max_context_tokens

    def build_continuation_context(self, state: LoopState) -> str:
        """
        Build minimal context for the next task.

        Creates a compact context string that provides the
        essential state needed for continuing task execution.

        Args:
            state: Current loop state

        Returns:
            Minimal context string for continuation
        """
        lines = [
            "=== Implementation Session Context ===",
            "",
            f"Session ID: {state.session_id}",
            f"Status: {state.status.value}",
            f"Current task: {state.current_task or 'None'}",
            "",
            "=== Progress ===",
            f"Tasks attempted: {state.tasks_attempted}",
            f"Tasks completed: {state.tasks_completed}",
            f"Tasks failed: {state.tasks_failed}",
            f"Tasks blocked: {state.tasks_blocked}",
            "",
            "=== Resources ===",
            f"Tokens used: {state.total_tokens}",
            f"Elapsed time: {state.elapsed_seconds:.1f}s",
        ]

        # Add recent task outcomes (last 3)
        if state.task_results:
            lines.append("")
            lines.append("=== Recent Tasks ===")
            for tr in state.task_results[-3:]:
                status = "SUCCESS" if tr.success else "FAILED"
                lines.append(f"[{status}] {tr.task_id}")
                if not tr.success and tr.error_message:
                    lines.append(f"  Error: {tr.error_message[:80]}...")

        return "\n".join(lines)

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _build_session_summary(self, state: LoopState) -> str:
        """Build high-level session summary."""
        success_rate = state.success_rate
        rate_str = f"{success_rate * 100:.1f}%" if success_rate is not None else "N/A"

        return (
            f"Implementation session {state.session_id} is {state.status.value}. "
            f"Completed {state.tasks_completed} of {state.tasks_attempted} tasks "
            f"({rate_str} success rate). "
            f"Used {state.total_tokens} tokens over {state.elapsed_seconds:.1f} seconds. "
            f"Failed: {state.tasks_failed}, Blocked: {state.tasks_blocked}."
        )

    def _build_state_snapshot(self, state: LoopState) -> Dict[str, Any]:
        """Build minimal state snapshot."""
        return {
            "session_id": state.session_id,
            "status": state.status.value,
            "current_task": state.current_task,
            "progress": {
                "attempted": state.tasks_attempted,
                "completed": state.tasks_completed,
                "failed": state.tasks_failed,
                "blocked": state.tasks_blocked,
            },
            "tokens": {
                "input": state.tokens_input,
                "output": state.tokens_output,
                "total": state.total_tokens,
            },
        }

    def _task_result_to_summary(self, result: TaskResult) -> TaskSummary:
        """Convert TaskResult to TaskSummary."""
        return TaskSummary(
            task_id=result.task_id,
            name=f"Task {result.task_id}",  # TaskResult doesn't have name
            status="success" if result.success else "failure",
            changes=[f"Commit: {c[:8]}" for c in result.commits[:5]],
            commits=result.commits[:5],
            notes=result.error_message[:200] if result.error_message else None,
            tokens_used=result.total_tokens,
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CompactedContext",
    "ContextCompactor",
    "TaskSummary",
    "DEFAULT_MAX_CONTEXT_TOKENS",
    "TARGET_COMPACTED_TOKENS",
]
