"""
Execution stage versioning for task implementation.

This module provides versioning capabilities for the EXECUTION stage of
task implementation, capturing state snapshots at key points:
- Execution start
- Checkpoints during execution
- Execution completion
- Rollback events

Key Components:
- ExecutionEventType: Types of execution events
- ExecutionSnapshot: Snapshot of execution state at a point in time
- ExecutionEvent: Event in the execution timeline
- ExecutionVersioner: Service for versioning execution stages

Design Reference:
- Implementation Mode Track Sprint
- Task: Implement ExecutionVersioner for execution stage versioning
"""

import logging
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import yaml

from vibey.services.implementation.versioning.core import (
    ContentVersion,
    ContentVersioner,
    VersionStage,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.services.implementation.context import TaskContext
    from vibey.services.implementation.result import ExecutionResult
    from vibey.services.implementation.state import LoopState

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class ExecutionEventType(str, Enum):
    """
    Type of execution event.

    Values:
        START: Execution began
        CHECKPOINT: Intermediate state capture
        COMPLETE: Execution finished (success or failure)
        ROLLBACK: Reverted to previous state
        PAUSE: Execution paused
        RESUME: Execution resumed after pause
    """

    START = "start"
    CHECKPOINT = "checkpoint"
    COMPLETE = "complete"
    ROLLBACK = "rollback"
    PAUSE = "pause"
    RESUME = "resume"


# =============================================================================
# EXECUTION SNAPSHOT
# =============================================================================


@dataclass
class ExecutionSnapshot:
    """
    Snapshot of execution state at a point in time.

    Captures the complete state of task execution including:
    - Event type and timing
    - Current status and progress
    - Resource usage (tokens, duration)
    - Git state (branch, commits, files)
    - Criteria status snapshot

    Attributes:
        ticket_id: ID of the ticket being executed
        event_type: Type of execution event
        timestamp: When this snapshot was taken
        status: Current execution status
        progress_percent: Percentage of task completion (0.0-100.0)
        current_step: Current step being executed
        tokens_input: Input tokens consumed so far
        tokens_output: Output tokens generated so far
        duration_so_far: Time elapsed since execution start
        branch: Current git branch name
        commits: List of commit SHAs created during execution
        files_modified: List of files modified during execution
        criteria_snapshot: Map of criterion_id to status string

    Example:
        >>> snapshot = ExecutionSnapshot(
        ...     ticket_id="01KCZF73PX9YNKWXKYVARY89N3",
        ...     event_type=ExecutionEventType.START,
        ...     timestamp=datetime.now(timezone.utc),
        ...     status="in_progress",
        ...     progress_percent=0.0,
        ... )
    """

    ticket_id: str
    event_type: ExecutionEventType
    timestamp: datetime

    # State
    status: str
    progress_percent: float
    current_step: Optional[str] = None

    # Resources
    tokens_input: int = 0
    tokens_output: int = 0
    duration_so_far: timedelta = field(default_factory=lambda: timedelta())

    # Git state
    branch: Optional[str] = None
    commits: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)

    # Criteria
    criteria_snapshot: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for YAML serialization.
        """
        return {
            "ticket_id": self.ticket_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "resources": {
                "tokens_input": self.tokens_input,
                "tokens_output": self.tokens_output,
                "duration_seconds": self.duration_so_far.total_seconds(),
            },
            "git": {
                "branch": self.branch,
                "commits": self.commits,
                "files_modified": self.files_modified,
            },
            "criteria_snapshot": self.criteria_snapshot,
        }

    def to_yaml(self) -> str:
        """
        Serialize to YAML for versioning.

        Returns:
            YAML string representation.
        """
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionSnapshot":
        """
        Create ExecutionSnapshot from dictionary.

        Args:
            data: Dictionary with snapshot data.

        Returns:
            ExecutionSnapshot instance.
        """
        # Parse timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Parse event type
        event_type_str = data.get("event_type", "checkpoint")
        try:
            event_type = ExecutionEventType(event_type_str)
        except ValueError:
            event_type = ExecutionEventType.CHECKPOINT

        # Parse resources (support both nested and flat formats)
        resources = data.get("resources", {})
        tokens_input = resources.get("tokens_input", data.get("tokens_input", 0))
        tokens_output = resources.get("tokens_output", data.get("tokens_output", 0))
        duration_seconds = resources.get(
            "duration_seconds", data.get("duration_seconds", 0)
        )
        duration_so_far = timedelta(seconds=duration_seconds)

        # Parse git state (support both nested and flat formats)
        git = data.get("git", {})
        branch = git.get("branch", data.get("branch"))
        commits = git.get("commits", data.get("commits", []))
        files_modified = git.get("files_modified", data.get("files_modified", []))

        return cls(
            ticket_id=data.get("ticket_id", ""),
            event_type=event_type,
            timestamp=timestamp,
            status=data.get("status", "unknown"),
            progress_percent=data.get("progress_percent", 0.0),
            current_step=data.get("current_step"),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            duration_so_far=duration_so_far,
            branch=branch,
            commits=commits,
            files_modified=files_modified,
            criteria_snapshot=data.get("criteria_snapshot", {}),
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "ExecutionSnapshot":
        """
        Deserialize from YAML.

        Args:
            yaml_str: YAML string representation.

        Returns:
            ExecutionSnapshot instance.
        """
        data = yaml.safe_load(yaml_str)
        if data is None:
            data = {}
        return cls.from_dict(data)

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.tokens_input + self.tokens_output


# =============================================================================
# EXECUTION EVENT
# =============================================================================


@dataclass
class ExecutionEvent:
    """
    Event in execution timeline.

    Represents a single event in the timeline of task execution,
    with a reference to the full version for detailed state.

    Attributes:
        event_type: Type of execution event
        timestamp: When this event occurred
        version_id: ID of the ContentVersion with full state
        summary: Human-readable summary of the event
    """

    event_type: ExecutionEventType
    timestamp: datetime
    version_id: str
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "version_id": self.version_id,
            "summary": self.summary,
        }


# =============================================================================
# EXECUTION VERSIONER
# =============================================================================


class ExecutionVersioner:
    """
    Versioning for the EXECUTION stage of ticket implementation.

    ExecutionVersioner captures state snapshots at key points during
    task execution, enabling:
    - Audit trail of execution progress
    - Rollback to previous states
    - Performance analysis
    - Debugging failed executions

    Attributes:
        versioner: The core ContentVersioner for storage

    Example:
        >>> versioner = ContentVersioner(Path(".vibey/roadmap/versions"))
        >>> exec_versioner = ExecutionVersioner(versioner)
        >>> version = exec_versioner.version_execution_start(
        ...     ticket=task,
        ...     context=context,
        ...     author="claude-code",
        ... )
    """

    def __init__(self, versioner: ContentVersioner):
        """
        Initialize ExecutionVersioner.

        Args:
            versioner: The ContentVersioner for storage operations.
        """
        self.versioner = versioner

    def _get_current_branch(self) -> Optional[str]:
        """Get the current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _get_current_commit(self) -> Optional[str]:
        """Get the current git commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _extract_criteria_snapshot(
        self, ticket: "HierarchicalTicket"
    ) -> Dict[str, str]:
        """
        Extract current criteria status from ticket.

        Args:
            ticket: The ticket to extract criteria from.

        Returns:
            Dictionary mapping criterion descriptions to status strings.
        """
        snapshot = {}
        try:
            for criterion in ticket.all_criteria:
                key = criterion.description[:80] if criterion.description else "unknown"
                status = "met" if criterion.is_met else "not_met"
                snapshot[key] = status
        except Exception as e:
            logger.debug(f"Could not extract criteria snapshot: {e}")
        return snapshot

    def version_execution_start(
        self,
        ticket: "HierarchicalTicket",
        context: "TaskContext",
        author: str,
    ) -> ContentVersion:
        """
        Capture state at execution start.

        Records:
        - Task state (planned -> in_progress)
        - Initial context provided
        - Criterion snapshot (from regression prevention)
        - Git state (branch, commit)
        - Timestamp

        Args:
            ticket: The ticket being executed
            context: The task context for execution
            author: Agent ID or user starting execution

        Returns:
            The created ContentVersion.
        """
        # Create snapshot
        snapshot = ExecutionSnapshot(
            ticket_id=ticket.id,
            event_type=ExecutionEventType.START,
            timestamp=datetime.now(timezone.utc),
            status=ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status),
            progress_percent=0.0,
            current_step="Initializing execution",
            tokens_input=0,
            tokens_output=0,
            duration_so_far=timedelta(),
            branch=self._get_current_branch(),
            commits=[c for c in [self._get_current_commit()] if c],
            files_modified=[str(f) for f in context.relevant_files],
            criteria_snapshot=self._extract_criteria_snapshot(ticket),
        )

        # Create version with snapshot as content
        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.EXECUTION,
            content=snapshot.to_yaml(),
            author=author,
            change_summary=f"Execution started for task: {ticket.name}",
            metadata={
                "event_type": ExecutionEventType.START.value,
                "task_name": ticket.name,
                "max_tokens": context.max_tokens,
            },
        )

    def version_execution_checkpoint(
        self,
        ticket: "HierarchicalTicket",
        state: "LoopState",
        progress: float,
        author: str,
        current_step: Optional[str] = None,
    ) -> ContentVersion:
        """
        Capture intermediate execution checkpoint.

        Called:
        - At configured intervals
        - Before risky operations
        - On pause/resume

        Args:
            ticket: The ticket being executed
            state: Current loop state with progress info
            progress: Completion percentage (0.0-100.0)
            author: Agent ID or user creating checkpoint
            current_step: Optional description of current step

        Returns:
            The created ContentVersion.
        """
        # Calculate duration
        duration = timedelta(seconds=state.elapsed_seconds) if hasattr(state, 'elapsed_seconds') else timedelta()

        # Create snapshot
        snapshot = ExecutionSnapshot(
            ticket_id=ticket.id,
            event_type=ExecutionEventType.CHECKPOINT,
            timestamp=datetime.now(timezone.utc),
            status=state.status.value if hasattr(state.status, "value") else str(state.status),
            progress_percent=progress,
            current_step=current_step,
            tokens_input=state.tokens_input,
            tokens_output=state.tokens_output,
            duration_so_far=duration,
            branch=self._get_current_branch(),
            commits=[r.commits[0] if r.commits else "" for r in state.task_results if r.commits],
            files_modified=[],  # Would need to track from git diff
            criteria_snapshot=self._extract_criteria_snapshot(ticket),
        )

        # Create version with snapshot as content
        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.EXECUTION,
            content=snapshot.to_yaml(),
            author=author,
            change_summary=f"Checkpoint at {progress:.1f}% progress",
            metadata={
                "event_type": ExecutionEventType.CHECKPOINT.value,
                "progress_percent": progress,
                "tokens_total": state.total_tokens,
            },
        )

    def version_execution_complete(
        self,
        ticket: "HierarchicalTicket",
        result: "ExecutionResult",
        author: str,
    ) -> ContentVersion:
        """
        Capture state at execution completion.

        Records:
        - Final status (success/failure/blocked)
        - All commits made
        - Files modified
        - Tokens consumed
        - Duration
        - Criterion states (post-execution)

        Args:
            ticket: The ticket that was executed
            result: The execution result
            author: Agent ID or user completing execution

        Returns:
            The created ContentVersion.
        """
        # Create snapshot
        snapshot = ExecutionSnapshot(
            ticket_id=ticket.id,
            event_type=ExecutionEventType.COMPLETE,
            timestamp=datetime.now(timezone.utc),
            status=result.status.value if hasattr(result.status, "value") else str(result.status),
            progress_percent=100.0 if result.succeeded else 0.0,
            current_step="Execution complete",
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            duration_so_far=result.duration,
            branch=self._get_current_branch(),
            commits=result.commits,
            files_modified=[str(f) for f in result.files_modified],
            criteria_snapshot=self._extract_criteria_snapshot(ticket),
        )

        # Determine change summary based on result
        if result.succeeded:
            summary = f"Execution completed successfully: {ticket.name}"
        else:
            error_msg = result.error_message or "Unknown error"
            summary = f"Execution failed: {error_msg[:100]}"

        # Create version with snapshot as content
        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.EXECUTION,
            content=snapshot.to_yaml(),
            author=author,
            change_summary=summary,
            metadata={
                "event_type": ExecutionEventType.COMPLETE.value,
                "succeeded": result.succeeded,
                "duration_seconds": result.duration_seconds,
                "total_tokens": result.total_tokens,
                "commits_count": len(result.commits),
                "files_modified_count": len(result.files_modified),
            },
        )

    def version_execution_rollback(
        self,
        ticket: "HierarchicalTicket",
        rollback_to: str,
        reason: str,
        author: str,
    ) -> ContentVersion:
        """
        Record rollback event in version history.

        This creates a new version that records the rollback event,
        linking to the version being rolled back to.

        Args:
            ticket: The ticket being rolled back
            rollback_to: Version ID to rollback to
            reason: Reason for the rollback
            author: Agent ID or user performing rollback

        Returns:
            The created ContentVersion recording the rollback.
        """
        # Create snapshot for rollback event
        snapshot = ExecutionSnapshot(
            ticket_id=ticket.id,
            event_type=ExecutionEventType.ROLLBACK,
            timestamp=datetime.now(timezone.utc),
            status=ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status),
            progress_percent=0.0,  # Reset after rollback
            current_step=f"Rolled back to version {rollback_to[:12]}",
            tokens_input=0,
            tokens_output=0,
            duration_so_far=timedelta(),
            branch=self._get_current_branch(),
            commits=[],
            files_modified=[],
            criteria_snapshot=self._extract_criteria_snapshot(ticket),
        )

        # Create version with snapshot as content
        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.EXECUTION,
            content=snapshot.to_yaml(),
            author=author,
            change_summary=f"Rollback to {rollback_to[:12]}: {reason}",
            metadata={
                "event_type": ExecutionEventType.ROLLBACK.value,
                "rollback_to_version": rollback_to,
                "rollback_reason": reason,
            },
        )

    def version_execution_pause(
        self,
        ticket: "HierarchicalTicket",
        state: "LoopState",
        author: str,
        reason: Optional[str] = None,
    ) -> ContentVersion:
        """
        Record pause event in version history.

        Args:
            ticket: The ticket being paused
            state: Current loop state
            author: Agent ID or user pausing execution
            reason: Optional reason for pausing

        Returns:
            The created ContentVersion.
        """
        duration = timedelta(seconds=state.elapsed_seconds) if hasattr(state, 'elapsed_seconds') else timedelta()

        snapshot = ExecutionSnapshot(
            ticket_id=ticket.id,
            event_type=ExecutionEventType.PAUSE,
            timestamp=datetime.now(timezone.utc),
            status="paused",
            progress_percent=0.0,  # Would need to be calculated
            current_step="Execution paused",
            tokens_input=state.tokens_input,
            tokens_output=state.tokens_output,
            duration_so_far=duration,
            branch=self._get_current_branch(),
            commits=[],
            files_modified=[],
            criteria_snapshot=self._extract_criteria_snapshot(ticket),
        )

        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.EXECUTION,
            content=snapshot.to_yaml(),
            author=author,
            change_summary=f"Execution paused{': ' + reason if reason else ''}",
            metadata={
                "event_type": ExecutionEventType.PAUSE.value,
                "pause_reason": reason,
            },
        )

    def version_execution_resume(
        self,
        ticket: "HierarchicalTicket",
        author: str,
    ) -> ContentVersion:
        """
        Record resume event in version history.

        Args:
            ticket: The ticket being resumed
            author: Agent ID or user resuming execution

        Returns:
            The created ContentVersion.
        """
        snapshot = ExecutionSnapshot(
            ticket_id=ticket.id,
            event_type=ExecutionEventType.RESUME,
            timestamp=datetime.now(timezone.utc),
            status="in_progress",
            progress_percent=0.0,  # Would need to be calculated from previous checkpoint
            current_step="Execution resumed",
            tokens_input=0,
            tokens_output=0,
            duration_so_far=timedelta(),
            branch=self._get_current_branch(),
            commits=[],
            files_modified=[],
            criteria_snapshot=self._extract_criteria_snapshot(ticket),
        )

        return self.versioner.create_version(
            ticket_id=ticket.id,
            stage=VersionStage.EXECUTION,
            content=snapshot.to_yaml(),
            author=author,
            change_summary="Execution resumed",
            metadata={
                "event_type": ExecutionEventType.RESUME.value,
            },
        )

    def get_execution_timeline(
        self,
        ticket_id: str,
    ) -> List[ExecutionEvent]:
        """
        Get timeline of execution events from versions.

        Args:
            ticket_id: ID of the ticket to get timeline for

        Returns:
            List of ExecutionEvents sorted by timestamp (oldest first).
        """
        # Get all execution versions for this ticket
        versions = self.versioner.get_history(ticket_id, VersionStage.EXECUTION)

        events: List[ExecutionEvent] = []
        for version in versions:
            # Extract event type from metadata
            event_type_str = version.metadata.get("event_type", "checkpoint")
            try:
                event_type = ExecutionEventType(event_type_str)
            except ValueError:
                event_type = ExecutionEventType.CHECKPOINT

            events.append(
                ExecutionEvent(
                    event_type=event_type,
                    timestamp=version.timestamp,
                    version_id=version.version_id,
                    summary=version.change_summary or "No summary",
                )
            )

        # Already sorted by timestamp from get_history
        return events

    def get_latest_checkpoint(self, ticket_id: str) -> Optional[ExecutionSnapshot]:
        """
        Get most recent checkpoint for ticket.

        Args:
            ticket_id: ID of the ticket to get checkpoint for

        Returns:
            Most recent ExecutionSnapshot, or None if no checkpoints exist.
        """
        current = self.versioner.get_current(ticket_id, VersionStage.EXECUTION)
        if current is None:
            return None

        return ExecutionSnapshot.from_yaml(current.content)

    def get_snapshot_at_version(
        self, ticket_id: str, version_id: str
    ) -> Optional[ExecutionSnapshot]:
        """
        Get snapshot at a specific version.

        Args:
            ticket_id: ID of the ticket
            version_id: ID of the version to retrieve

        Returns:
            ExecutionSnapshot at that version, or None if not found.
        """
        version = self.versioner.get_version(
            ticket_id, VersionStage.EXECUTION, version_id
        )
        if version is None:
            return None

        return ExecutionSnapshot.from_yaml(version.content)

    def get_execution_summary(self, ticket_id: str) -> Dict[str, Any]:
        """
        Get summary of execution for a ticket.

        Provides aggregate statistics across all execution events.

        Args:
            ticket_id: ID of the ticket

        Returns:
            Dictionary with execution summary statistics.
        """
        timeline = self.get_execution_timeline(ticket_id)

        if not timeline:
            return {
                "has_execution_history": False,
                "event_count": 0,
            }

        # Find start and end events
        start_event = next(
            (e for e in timeline if e.event_type == ExecutionEventType.START),
            None,
        )
        complete_event = next(
            (e for e in reversed(timeline) if e.event_type == ExecutionEventType.COMPLETE),
            None,
        )

        # Get latest snapshot for token/commit info
        latest_snapshot = self.get_latest_checkpoint(ticket_id)

        return {
            "has_execution_history": True,
            "event_count": len(timeline),
            "started_at": start_event.timestamp.isoformat() if start_event else None,
            "completed_at": complete_event.timestamp.isoformat() if complete_event else None,
            "checkpoint_count": sum(
                1 for e in timeline if e.event_type == ExecutionEventType.CHECKPOINT
            ),
            "rollback_count": sum(
                1 for e in timeline if e.event_type == ExecutionEventType.ROLLBACK
            ),
            "tokens_total": latest_snapshot.total_tokens if latest_snapshot else 0,
            "commits_count": len(latest_snapshot.commits) if latest_snapshot else 0,
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ExecutionEventType",
    "ExecutionEvent",
    "ExecutionSnapshot",
    "ExecutionVersioner",
]
