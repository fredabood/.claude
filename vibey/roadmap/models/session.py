"""
Session models for tracking AI-assisted coding sessions.

Sessions are bounded periods of AI-assisted coding activity that can be
tracked, versioned, and potentially reproduced. They enable:
- Decision audit trails
- Session reconstruction
- Cross-session continuity
- Git commit associations

Version: 1.0.0
Sprint: 3.2 - Git Versioning for Vibe Coding Sessions
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionStatus(str, Enum):
    """Status enum for sessions."""

    ACTIVE = "active"          # Session is currently in use
    PAUSED = "paused"          # Session temporarily suspended
    COMPLETED = "completed"    # Session ended normally
    ABANDONED = "abandoned"    # Session ended without proper completion


class SessionEventType(str, Enum):
    """Types of events that can occur during a session."""

    # Session lifecycle events
    SESSION_START = "session_start"
    SESSION_PAUSE = "session_pause"
    SESSION_RESUME = "session_resume"
    SESSION_END = "session_end"

    # Goal events
    GOAL_SET = "goal_set"
    GOAL_ACHIEVED = "goal_achieved"

    # Task events (roadmap integration)
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_PAUSED = "task_paused"

    # Decision events (audit trail)
    DECISION_MADE = "decision_made"
    QUESTION_ASKED = "question_asked"

    # File events
    FILE_READ = "file_read"
    FILE_MODIFIED = "file_modified"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"

    # Git events
    COMMIT_MADE = "commit_made"
    BRANCH_CHANGED = "branch_changed"

    # Command events
    COMMAND_RUN = "command_run"

    # Error events
    ERROR_ENCOUNTERED = "error_encountered"
    ERROR_RESOLVED = "error_resolved"

    # Context events
    CONTEXT_LOADED = "context_loaded"
    CONTEXT_UPDATED = "context_updated"
    CONTEXT_SNAPSHOT = "context_snapshot"

    # Generic
    CUSTOM = "custom"
    NOTE = "note"


class DecisionCategory(str, Enum):
    """Categories for decisions made during sessions."""

    ARCHITECTURE = "architecture"      # Architectural decisions
    IMPLEMENTATION = "implementation"  # Implementation approach choices
    DESIGN = "design"                  # UI/UX or API design decisions
    PROCESS = "process"                # Workflow or process decisions
    TOOLING = "tooling"                # Tool or library choices
    TESTING = "testing"                # Testing strategy decisions
    DOCUMENTATION = "documentation"    # Documentation approach
    OTHER = "other"


class DecisionConfidence(str, Enum):
    """Confidence level for decisions."""

    LOW = "low"        # Uncertain, may need to revisit
    MEDIUM = "medium"  # Reasonably confident
    HIGH = "high"      # Very confident


@dataclass
class SessionEvent:
    """
    A discrete event that occurred during a session.

    Events form the audit trail of what happened during a session,
    enabling reconstruction and analysis.
    """

    id: str                              # ULID
    session_id: str                      # Parent session ULID
    timestamp: datetime                  # When the event occurred
    event_type: SessionEventType         # Type of event

    # Event-specific data (varies by event_type)
    data: Dict[str, Any] = field(default_factory=dict)

    # Optional associations
    task_id: Optional[str] = None        # Related roadmap task
    commit_sha: Optional[str] = None     # Related git commit
    file_path: Optional[str] = None      # Related file

    def __post_init__(self):
        """Validate event data."""
        if not self.id:
            raise ValueError("Event id is required")
        if not self.session_id:
            raise ValueError("Event session_id is required")
        if not self.timestamp:
            raise ValueError("Event timestamp is required")

        # Ensure timezone-aware timestamp
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


@dataclass
class Decision:
    """
    A decision made during a coding session.

    Decisions are specialized events that capture:
    - What was decided
    - What alternatives were considered
    - Why the decision was made
    - Confidence level and whether it should be revisited
    """

    id: str                              # ULID
    session_id: str                      # Parent session
    timestamp: datetime                  # When the decision was made
    description: str                     # What was decided

    # Decision context
    category: DecisionCategory = DecisionCategory.OTHER
    confidence: DecisionConfidence = DecisionConfidence.MEDIUM
    revisit: bool = False                # Flag if decision should be revisited

    # Rationale
    rationale: Optional[str] = None      # Why this decision was made
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    # Each alternative: {id, description, pros, cons, reason_rejected}

    # Traceability
    related_files: List[str] = field(default_factory=list)
    related_commits: List[str] = field(default_factory=list)
    related_tasks: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate decision data."""
        if not self.id:
            raise ValueError("Decision id is required")
        if not self.session_id:
            raise ValueError("Decision session_id is required")
        if not self.description:
            raise ValueError("Decision description is required")

        # Ensure timezone-aware timestamp
        if self.timestamp and self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

    def to_event(self) -> SessionEvent:
        """Convert decision to a SessionEvent for storage."""
        return SessionEvent(
            id=self.id,
            session_id=self.session_id,
            timestamp=self.timestamp,
            event_type=SessionEventType.DECISION_MADE,
            data={
                "description": self.description,
                "category": self.category.value,
                "confidence": self.confidence.value,
                "revisit": self.revisit,
                "rationale": self.rationale,
                "alternatives": self.alternatives,
            },
            task_id=self.related_tasks[0] if self.related_tasks else None,
            commit_sha=self.related_commits[0] if self.related_commits else None,
            file_path=self.related_files[0] if self.related_files else None,
        )

    @classmethod
    def from_event(cls, event: SessionEvent) -> "Decision":
        """Create a Decision from a SessionEvent."""
        if event.event_type != SessionEventType.DECISION_MADE:
            raise ValueError(f"Expected DECISION_MADE event, got {event.event_type}")

        data = event.data
        return cls(
            id=event.id,
            session_id=event.session_id,
            timestamp=event.timestamp,
            description=data.get("description", ""),
            category=DecisionCategory(data.get("category", "other")),
            confidence=DecisionConfidence(data.get("confidence", "medium")),
            revisit=data.get("revisit", False),
            rationale=data.get("rationale"),
            alternatives=data.get("alternatives", []),
            related_files=[event.file_path] if event.file_path else [],
            related_commits=[event.commit_sha] if event.commit_sha else [],
            related_tasks=[event.task_id] if event.task_id else [],
        )


@dataclass
class ContextSnapshot:
    """
    Point-in-time capture of session context state.

    Snapshots enable session reconstruction by recording
    the full state at key points (session start, end, checkpoints).
    """

    id: str                              # ULID
    session_id: str                      # Parent session
    timestamp: datetime                  # When snapshot was taken
    snapshot_type: str                   # "session_start", "checkpoint", "session_end"

    # Git state
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    git_dirty: bool = False
    git_staged_files: List[str] = field(default_factory=list)
    git_modified_files: List[str] = field(default_factory=list)

    # Context files (path -> hash mapping)
    context_files: Dict[str, str] = field(default_factory=dict)

    # Roadmap state
    active_track_id: Optional[str] = None
    active_sprint_id: Optional[str] = None
    active_task_ids: List[str] = field(default_factory=list)

    # Environment
    environment: Dict[str, Any] = field(default_factory=dict)
    # Includes: python_version, vibey_version, platform, etc.

    # Configuration hash for change detection
    config_hash: Optional[str] = None

    def __post_init__(self):
        """Validate snapshot data."""
        if not self.id:
            raise ValueError("Snapshot id is required")
        if not self.session_id:
            raise ValueError("Snapshot session_id is required")

        # Ensure timezone-aware timestamp
        if self.timestamp and self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


@dataclass
class SessionCommit:
    """
    A git commit associated with a session.

    Links commits to the session they were made in,
    enabling audit of what code changes happened during which session.
    """

    session_id: str                      # Parent session
    commit_sha: str                      # Full SHA
    short_sha: str                       # Short SHA (7 chars)
    timestamp: datetime                  # Commit timestamp
    message: str                         # Commit message
    author: Optional[str] = None         # Commit author
    files_changed: int = 0               # Number of files changed
    insertions: int = 0                  # Lines added
    deletions: int = 0                   # Lines removed

    def __post_init__(self):
        """Validate commit data."""
        if not self.session_id:
            raise ValueError("SessionCommit session_id is required")
        if not self.commit_sha:
            raise ValueError("SessionCommit commit_sha is required")

        # Ensure timezone-aware timestamp
        if self.timestamp and self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)


@dataclass
class SessionStats:
    """
    Aggregate statistics for a session.

    Computed from session events and commits.
    """

    duration_seconds: int = 0            # Total session duration
    events_count: int = 0                # Number of events logged
    decisions_count: int = 0             # Number of decisions made
    commits_count: int = 0               # Number of commits
    files_modified: int = 0              # Unique files modified
    tasks_worked: int = 0                # Number of tasks touched
    errors_count: int = 0                # Errors encountered
    token_usage: Optional[int] = None    # Estimated tokens used (if tracked)


@dataclass
class Session:
    """
    A bounded period of AI-assisted coding activity.

    Sessions are the fundamental unit of work in vibe coding.
    They track what context was used, what decisions were made,
    and what code changes occurred during a coding session.

    Lifecycle:
    - Created: Session initialized but not yet active
    - Active: Session is currently in use
    - Paused: Session temporarily suspended
    - Completed: Session ended normally
    - Abandoned: Session ended without proper completion
    """

    # Identity
    id: str                              # ULID, globally unique
    name: str                            # Human-readable name

    # Lifecycle
    status: SessionStatus = SessionStatus.ACTIVE
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started: Optional[datetime] = None   # When work actually began
    paused: Optional[datetime] = None    # When paused (if paused)
    ended: Optional[datetime] = None     # When session ended

    # Roadmap associations
    roadmap_id: str = ""                 # Parent roadmap ID
    track_id: Optional[str] = None       # Associated track
    sprint_id: Optional[str] = None      # Associated sprint
    task_ids: List[str] = field(default_factory=list)  # Tasks worked on

    # Git integration
    branch: Optional[str] = None         # Git branch name
    start_commit: Optional[str] = None   # Commit SHA at session start
    end_commit: Optional[str] = None     # Commit SHA at session end
    commits: List[SessionCommit] = field(default_factory=list)

    # Context
    goals: List[str] = field(default_factory=list)  # Session goals
    summary: Optional[str] = None        # Session summary (auto or manual)
    context_snapshot: Optional[ContextSnapshot] = None  # Start snapshot

    # Events and decisions
    events: List[SessionEvent] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)

    # Statistics
    stats: Optional[SessionStats] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Includes: environment, model, agent_version, etc.

    def __post_init__(self):
        """Validate session data."""
        if not self.id:
            raise ValueError("Session id is required")
        if not self.name:
            raise ValueError("Session name is required")

        # Ensure timezone-aware timestamps
        if self.created and self.created.tzinfo is None:
            self.created = self.created.replace(tzinfo=timezone.utc)
        if self.started and self.started.tzinfo is None:
            self.started = self.started.replace(tzinfo=timezone.utc)
        if self.paused and self.paused.tzinfo is None:
            self.paused = self.paused.replace(tzinfo=timezone.utc)
        if self.ended and self.ended.tzinfo is None:
            self.ended = self.ended.replace(tzinfo=timezone.utc)

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status == SessionStatus.ACTIVE

    @property
    def is_ended(self) -> bool:
        """Check if session has ended."""
        return self.status in (SessionStatus.COMPLETED, SessionStatus.ABANDONED)

    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate session duration in seconds."""
        if not self.started:
            return None

        end_time = self.ended or datetime.now(timezone.utc)

        # Ensure both are timezone-aware
        start = self.started
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        return int((end_time - start).total_seconds())

    def add_event(self, event: SessionEvent) -> None:
        """Add an event to the session."""
        self.events.append(event)

    def add_decision(self, decision: Decision) -> None:
        """Add a decision to the session."""
        self.decisions.append(decision)
        # Also add as event for timeline
        self.events.append(decision.to_event())

    def add_commit(self, commit: SessionCommit) -> None:
        """Add a commit to the session."""
        self.commits.append(commit)

    def add_task(self, task_id: str) -> None:
        """Associate a task with this session."""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)

    def set_goal(self, goal: str) -> None:
        """Add a goal to the session."""
        if goal not in self.goals:
            self.goals.append(goal)

    def compute_stats(self) -> SessionStats:
        """Compute aggregate statistics for the session."""
        files = set()
        for commit in self.commits:
            files.add(commit.files_changed)  # This is count, not the files

        # Count unique files from file events
        file_events = [e for e in self.events if e.event_type in (
            SessionEventType.FILE_MODIFIED,
            SessionEventType.FILE_CREATED,
        )]
        file_paths = set(e.file_path for e in file_events if e.file_path)

        errors = [e for e in self.events if e.event_type == SessionEventType.ERROR_ENCOUNTERED]

        return SessionStats(
            duration_seconds=self.duration_seconds or 0,
            events_count=len(self.events),
            decisions_count=len(self.decisions),
            commits_count=len(self.commits),
            files_modified=len(file_paths),
            tasks_worked=len(self.task_ids),
            errors_count=len(errors),
            token_usage=self.metadata.get("token_usage"),
        )
