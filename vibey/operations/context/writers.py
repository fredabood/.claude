"""Context writers for persisting different types of context.

This module provides writer classes for storing context to the filesystem
with proper structure, indexing, and atomic writes.

Writers:
    - SessionContextWriter: Session tracking
    - TaskContextWriter: Task execution context
    - DecisionContextWriter: Decision records (ADRs)
    - SprintContextWriter: Sprint planning documents
"""

from __future__ import annotations

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import yaml


# Type variable for generic context writer
T = TypeVar("T")


@dataclass
class SessionContext:
    """Session context data structure."""

    id: str
    type: str = "development"  # development | research | maintenance
    started: str = ""
    ended: Optional[str] = None
    status: str = "active"  # active | completed | abandoned

    agent: Optional[str] = None
    user: Optional[str] = None

    goals: List[str] = field(default_factory=list)
    tasks_worked: List[Dict[str, Any]] = field(default_factory=list)
    decisions_made: List[Dict[str, Any]] = field(default_factory=list)
    artifacts_created: List[Dict[str, Any]] = field(default_factory=list)

    summary: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """Task context data structure."""

    task_id: str
    sprint_id: str
    track_id: str

    title: str
    description: str = ""

    sessions: List[Dict[str, Any]] = field(default_factory=list)
    commands_executed: List[Dict[str, Any]] = field(default_factory=list)
    files_modified: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    blockers_encountered: List[Dict[str, Any]] = field(default_factory=list)

    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionContext:
    """Decision record (ADR) data structure."""

    id: str
    title: str
    date: str
    status: str = "proposed"  # proposed | accepted | deprecated | superseded

    deciders: List[str] = field(default_factory=list)
    related_tasks: List[str] = field(default_factory=list)

    context: str = ""
    decision: str = ""
    consequences: str = ""
    alternatives: str = ""
    references: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SprintContext:
    """Sprint context data structure."""

    sprint_id: str
    name: str
    slug: str

    plan_content: str = ""
    artifacts: List[Dict[str, Any]] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexEntry:
    """Entry in the context index."""

    id: str
    type: str  # session | task | decision | sprint
    path: str
    created: str
    updated: str
    status: Optional[str] = None
    title: Optional[str] = None


@dataclass
class ContextIndex:
    """Master index for all context."""

    version: str = "1.0"
    created: str = ""
    last_updated: str = ""

    stats: Dict[str, int] = field(default_factory=dict)
    current: Dict[str, str] = field(default_factory=dict)
    recent_tasks: List[Dict[str, Any]] = field(default_factory=list)
    recent_decisions: List[Dict[str, Any]] = field(default_factory=list)


class ContextWriter(ABC, Generic[T]):
    """Abstract base class for context writers.

    Provides common functionality for all context writers:
    - Atomic file writes using temp file + rename
    - Directory structure management
    - Index file updates
    - Archival to history directories

    Subclasses must implement:
    - _get_current_dir(): Return path to current/active contexts
    - _get_history_dir(): Return path to archived contexts
    - _context_to_dict(): Convert context to dict for YAML serialization
    - _dict_to_context(): Convert dict to context object
    """

    def __init__(
        self,
        context_dir: Optional[Path] = None,
        file_extension: str = ".yaml",
    ):
        """Initialize the context writer.

        Args:
            context_dir: Base context directory. Defaults to .vibey/context/
            file_extension: File extension for context files
        """
        self.context_dir = context_dir or Path(".vibey/context")
        self.file_extension = file_extension
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure all required directories exist."""
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self._get_current_dir().mkdir(parents=True, exist_ok=True)
        self._get_history_dir().mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def _get_current_dir(self) -> Path:
        """Get directory for current/active contexts."""
        pass

    @abstractmethod
    def _get_history_dir(self) -> Path:
        """Get directory for archived contexts."""
        pass

    @abstractmethod
    def _context_to_dict(self, context: T) -> Dict[str, Any]:
        """Convert context object to dictionary for serialization."""
        pass

    @abstractmethod
    def _dict_to_context(self, data: Dict[str, Any]) -> T:
        """Convert dictionary to context object."""
        pass

    @abstractmethod
    def _get_context_id(self, context: T) -> str:
        """Get the ID from a context object."""
        pass

    def _get_filepath(self, context_id: str, current: bool = True) -> Path:
        """Get file path for a context ID."""
        base_dir = self._get_current_dir() if current else self._get_history_dir()
        return base_dir / f"{context_id}{self.file_extension}"

    def _atomic_write(self, filepath: Path, content: str) -> None:
        """Atomically write content to file using temp + rename pattern."""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first
        fd, temp_path = tempfile.mkstemp(
            suffix=self.file_extension,
            dir=filepath.parent,
        )
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            # Atomic rename
            shutil.move(temp_path, filepath)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def write(self, context: T, path: Optional[Path] = None) -> Path:
        """Write context to storage.

        Args:
            context: Context object to write
            path: Optional explicit path (defaults to standard location)

        Returns:
            Path to the written file
        """
        context_id = self._get_context_id(context)
        filepath = path or self._get_filepath(context_id, current=True)

        data = self._context_to_dict(context)
        content = yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        self._atomic_write(filepath, content)
        self._update_index(context_id, filepath, data)

        return filepath

    def read(self, context_id: str, current: bool = True) -> Optional[T]:
        """Read context by ID.

        Args:
            context_id: ID of the context to read
            current: If True, look in current dir; if False, look in history

        Returns:
            Context object or None if not found
        """
        filepath = self._get_filepath(context_id, current=current)

        if not filepath.exists():
            # Try the other location
            alt_path = self._get_filepath(context_id, current=not current)
            if alt_path.exists():
                filepath = alt_path
            else:
                return None

        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
            return self._dict_to_context(data)
        except Exception:
            return None

    def update(self, context_id: str, updates: Dict[str, Any]) -> Optional[Path]:
        """Update existing context with new values.

        Args:
            context_id: ID of the context to update
            updates: Dictionary of updates to apply

        Returns:
            Path to updated file, or None if context not found
        """
        context = self.read(context_id)
        if context is None:
            return None

        # Apply updates to context
        data = self._context_to_dict(context)
        data.update(updates)

        # Update timestamp if metadata exists
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()

        filepath = self._get_filepath(context_id)
        content = yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        self._atomic_write(filepath, content)
        return filepath

    def archive(self, context_id: str) -> Optional[Path]:
        """Archive context to history directory.

        Args:
            context_id: ID of the context to archive

        Returns:
            Path to archived file, or None if context not found
        """
        current_path = self._get_filepath(context_id, current=True)
        if not current_path.exists():
            return None

        # Get monthly bucket for history
        now = datetime.now(timezone.utc)
        month_bucket = now.strftime("%Y-%m")
        history_path = self._get_history_dir() / month_bucket / f"{context_id}{self.file_extension}"
        history_path.parent.mkdir(parents=True, exist_ok=True)

        # Move to history
        shutil.move(str(current_path), str(history_path))

        return history_path

    def list_current(self) -> List[str]:
        """List all current context IDs."""
        current_dir = self._get_current_dir()
        if not current_dir.exists():
            return []

        return [
            f.stem
            for f in current_dir.glob(f"*{self.file_extension}")
            if f.is_file()
        ]

    def list_history(self, limit: int = 50) -> List[str]:
        """List archived context IDs.

        Args:
            limit: Maximum number to return

        Returns:
            List of context IDs, most recent first
        """
        history_dir = self._get_history_dir()
        if not history_dir.exists():
            return []

        # Collect all files from monthly buckets
        files = []
        for bucket in sorted(history_dir.iterdir(), reverse=True):
            if bucket.is_dir():
                for f in bucket.glob(f"*{self.file_extension}"):
                    if f.is_file():
                        files.append((f.stat().st_mtime, f.stem))

        # Sort by modification time, most recent first
        files.sort(reverse=True)
        return [f[1] for f in files[:limit]]

    def _update_index(
        self,
        context_id: str,
        filepath: Path,
        data: Dict[str, Any],
    ) -> None:
        """Update the master index file.

        This is a no-op in the base class. The ContextManager
        handles index updates across all writers.
        """
        pass


class SessionContextWriter(ContextWriter[SessionContext]):
    """Writer for session context."""

    def _get_current_dir(self) -> Path:
        return self.context_dir / "sessions" / "current"

    def _get_history_dir(self) -> Path:
        return self.context_dir / "sessions" / "history"

    def _context_to_dict(self, context: SessionContext) -> Dict[str, Any]:
        return {"session": asdict(context)}

    def _dict_to_context(self, data: Dict[str, Any]) -> SessionContext:
        session_data = data.get("session", data)
        return SessionContext(**{
            k: v for k, v in session_data.items()
            if k in SessionContext.__dataclass_fields__
        })

    def _get_context_id(self, context: SessionContext) -> str:
        return context.id

    def start_session(
        self,
        session_id: str,
        session_type: str = "development",
        agent: Optional[str] = None,
        user: Optional[str] = None,
        goals: Optional[List[str]] = None,
    ) -> SessionContext:
        """Start a new session and write it.

        Args:
            session_id: Unique session ID (ULID)
            session_type: Type of session
            agent: AI agent identity
            user: Human user identity
            goals: Initial session goals

        Returns:
            Created SessionContext
        """
        now = datetime.now(timezone.utc).isoformat()
        context = SessionContext(
            id=session_id,
            type=session_type,
            started=now,
            status="active",
            agent=agent,
            user=user,
            goals=goals or [],
            metadata={
                "created": now,
                "git_branch": self._get_git_branch(),
                "git_commit_start": self._get_git_commit(),
            },
        )
        self.write(context)
        return context

    def end_session(
        self,
        session_id: str,
        status: str = "completed",
        summary: Optional[str] = None,
    ) -> Optional[Path]:
        """End a session and archive it.

        Args:
            session_id: Session ID to end
            status: Final status (completed | abandoned)
            summary: Session summary

        Returns:
            Path to archived session, or None if not found
        """
        now = datetime.now(timezone.utc).isoformat()
        updates = {
            "ended": now,
            "status": status,
            "summary": summary,
        }

        # Update the session
        self.update(session_id, updates)

        # Archive it
        return self.archive(session_id)

    def add_task_worked(
        self,
        session_id: str,
        task_id: str,
        title: str,
        started: Optional[str] = None,
    ) -> bool:
        """Add a task to the session's worked tasks list.

        Returns:
            True if successful, False otherwise
        """
        context = self.read(session_id)
        if context is None:
            return False

        now = datetime.now(timezone.utc).isoformat()
        context.tasks_worked.append({
            "id": task_id,
            "title": title,
            "started": started or now,
            "completed": None,
        })

        self.write(context)
        return True

    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else None
        except Exception:
            return None


class TaskContextWriter(ContextWriter[TaskContext]):
    """Writer for task context."""

    def _get_current_dir(self) -> Path:
        return self.context_dir / "tasks" / "current"

    def _get_history_dir(self) -> Path:
        return self.context_dir / "tasks" / "completed"

    def _context_to_dict(self, context: TaskContext) -> Dict[str, Any]:
        return {"task_context": asdict(context)}

    def _dict_to_context(self, data: Dict[str, Any]) -> TaskContext:
        task_data = data.get("task_context", data)
        return TaskContext(**{
            k: v for k, v in task_data.items()
            if k in TaskContext.__dataclass_fields__
        })

    def _get_context_id(self, context: TaskContext) -> str:
        return context.task_id

    def start_task(
        self,
        task_id: str,
        sprint_id: str,
        track_id: str,
        title: str,
        description: str = "",
        session_id: Optional[str] = None,
    ) -> TaskContext:
        """Start tracking context for a task.

        Args:
            task_id: Task ID (ULID)
            sprint_id: Parent sprint ID
            track_id: Parent track ID
            title: Task title
            description: Task description
            session_id: Optional session ID to link

        Returns:
            Created TaskContext
        """
        now = datetime.now(timezone.utc).isoformat()
        context = TaskContext(
            task_id=task_id,
            sprint_id=sprint_id,
            track_id=track_id,
            title=title,
            description=description,
            sessions=[{
                "session_id": session_id,
                "started": now,
                "ended": None,
            }] if session_id else [],
            metadata={
                "created": now,
            },
        )
        self.write(context)
        return context

    def add_command(
        self,
        task_id: str,
        command: str,
        duration_ms: int,
        status: str = "success",
    ) -> bool:
        """Add a command execution to task context.

        Returns:
            True if successful, False otherwise
        """
        context = self.read(task_id)
        if context is None:
            return False

        now = datetime.now(timezone.utc).isoformat()
        context.commands_executed.append({
            "command": command,
            "timestamp": now,
            "duration_ms": duration_ms,
            "status": status,
        })

        self.write(context)
        return True

    def add_file_modified(
        self,
        task_id: str,
        path: str,
        action: str = "modified",
    ) -> bool:
        """Add a file modification to task context.

        Args:
            task_id: Task ID
            path: File path
            action: Action taken (created | modified | deleted)

        Returns:
            True if successful, False otherwise
        """
        context = self.read(task_id)
        if context is None:
            return False

        now = datetime.now(timezone.utc).isoformat()
        context.files_modified.append({
            "path": path,
            "action": action,
            "timestamp": now,
        })

        self.write(context)
        return True

    def complete_task(self, task_id: str) -> Optional[Path]:
        """Complete a task and archive its context.

        Returns:
            Path to archived context, or None if not found
        """
        return self.archive(task_id)


class DecisionContextWriter(ContextWriter[DecisionContext]):
    """Writer for decision records (ADRs)."""

    def __init__(self, context_dir: Optional[Path] = None):
        # Decisions use .md extension
        super().__init__(context_dir, file_extension=".md")

    def _get_current_dir(self) -> Path:
        # Decisions use monthly buckets directly (no current/history split)
        now = datetime.now(timezone.utc)
        return self.context_dir / "decisions" / now.strftime("%Y-%m")

    def _get_history_dir(self) -> Path:
        # Same as current for decisions
        return self.context_dir / "decisions"

    def _context_to_dict(self, context: DecisionContext) -> Dict[str, Any]:
        # For decisions, we generate markdown directly
        return asdict(context)

    def _dict_to_context(self, data: Dict[str, Any]) -> DecisionContext:
        return DecisionContext(**{
            k: v for k, v in data.items()
            if k in DecisionContext.__dataclass_fields__
        })

    def _get_context_id(self, context: DecisionContext) -> str:
        return context.id

    def _get_filepath(self, context_id: str, current: bool = True) -> Path:
        """Decisions use sequence-slug naming in monthly buckets."""
        base_dir = self._get_current_dir()
        return base_dir / f"{context_id}.md"

    def write(self, context: DecisionContext, path: Optional[Path] = None) -> Path:
        """Write decision as markdown ADR format."""
        context_id = self._get_context_id(context)
        filepath = path or self._get_filepath(context_id)

        # Generate markdown content
        content = self._generate_adr_markdown(context)

        self._atomic_write(filepath, content)
        return filepath

    def read(self, context_id: str, current: bool = True) -> Optional[DecisionContext]:
        """Read decision - searches all monthly buckets."""
        decisions_dir = self.context_dir / "decisions"
        if not decisions_dir.exists():
            return None

        # Search all monthly buckets
        for bucket in sorted(decisions_dir.iterdir(), reverse=True):
            if bucket.is_dir():
                filepath = bucket / f"{context_id}.md"
                if filepath.exists():
                    return self._parse_adr_markdown(filepath)

        return None

    def _generate_adr_markdown(self, context: DecisionContext) -> str:
        """Generate ADR markdown from context."""
        lines = [
            f"# {context.id}. {context.title}",
            "",
            f"Date: {context.date}",
            f"Status: {context.status}",
        ]

        if context.deciders:
            lines.append(f"Deciders: {', '.join(context.deciders)}")

        if context.related_tasks:
            lines.append(f"Related Tasks: {', '.join(context.related_tasks)}")

        lines.extend([
            "",
            "## Context",
            "",
            context.context or "*(To be filled)*",
            "",
            "## Decision",
            "",
            context.decision or "*(To be filled)*",
            "",
            "## Consequences",
            "",
            context.consequences or "*(To be filled)*",
            "",
        ])

        if context.alternatives:
            lines.extend([
                "## Alternatives Considered",
                "",
                context.alternatives,
                "",
            ])

        if context.references:
            lines.extend([
                "## References",
                "",
            ])
            for ref in context.references:
                lines.append(f"- {ref}")
            lines.append("")

        return "\n".join(lines)

    def _parse_adr_markdown(self, filepath: Path) -> Optional[DecisionContext]:
        """Parse ADR markdown into context object."""
        try:
            with open(filepath) as f:
                content = f.read()

            # Parse title line
            lines = content.split("\n")
            title_line = lines[0] if lines else ""

            # Extract ID and title from "# 0001. Title"
            if title_line.startswith("# "):
                parts = title_line[2:].split(". ", 1)
                adr_id = parts[0] if parts else filepath.stem
                title = parts[1] if len(parts) > 1 else ""
            else:
                adr_id = filepath.stem
                title = ""

            # Parse metadata (Date, Status, etc.)
            date = ""
            status = "proposed"
            deciders = []
            related_tasks = []

            for line in lines[1:20]:  # Check first 20 lines for metadata
                if line.startswith("Date: "):
                    date = line[6:]
                elif line.startswith("Status: "):
                    status = line[8:]
                elif line.startswith("Deciders: "):
                    deciders = [d.strip() for d in line[10:].split(",")]
                elif line.startswith("Related Tasks: "):
                    related_tasks = [t.strip() for t in line[15:].split(",")]

            return DecisionContext(
                id=adr_id,
                title=title,
                date=date,
                status=status,
                deciders=deciders,
                related_tasks=related_tasks,
            )
        except Exception:
            return None

    def list_current(self) -> List[str]:
        """List all decision IDs across all monthly buckets."""
        decisions_dir = self.context_dir / "decisions"
        if not decisions_dir.exists():
            return []

        ids = []
        for bucket in sorted(decisions_dir.iterdir(), reverse=True):
            if bucket.is_dir():
                for f in bucket.glob("*.md"):
                    ids.append(f.stem)

        return ids

    def get_next_sequence(self) -> int:
        """Get the next ADR sequence number."""
        ids = self.list_current()
        max_seq = 0

        for adr_id in ids:
            # Extract sequence from "0001-slug"
            parts = adr_id.split("-", 1)
            if parts and parts[0].isdigit():
                max_seq = max(max_seq, int(parts[0]))

        return max_seq + 1

    def create_decision(
        self,
        title: str,
        context_text: str = "",
        decision_text: str = "",
        status: str = "proposed",
        deciders: Optional[List[str]] = None,
    ) -> DecisionContext:
        """Create a new decision record.

        Args:
            title: Decision title
            context_text: Context/background
            decision_text: The decision made
            status: Decision status
            deciders: List of decision makers

        Returns:
            Created DecisionContext
        """
        # Generate ID
        seq = self.get_next_sequence()
        slug = title.lower().replace(" ", "-")[:50]
        adr_id = f"{seq:04d}-{slug}"

        now = datetime.now(timezone.utc)
        context = DecisionContext(
            id=adr_id,
            title=title,
            date=now.strftime("%Y-%m-%d"),
            status=status,
            deciders=deciders or [],
            context=context_text,
            decision=decision_text,
        )

        self.write(context)
        return context


class SprintContextWriter(ContextWriter[SprintContext]):
    """Writer for sprint context/planning documents."""

    def _get_current_dir(self) -> Path:
        return self.context_dir / "sprints"

    def _get_history_dir(self) -> Path:
        # Sprints don't have history - they stay in place
        return self.context_dir / "sprints"

    def _context_to_dict(self, context: SprintContext) -> Dict[str, Any]:
        return {"sprint_context": asdict(context)}

    def _dict_to_context(self, data: Dict[str, Any]) -> SprintContext:
        sprint_data = data.get("sprint_context", data)
        return SprintContext(**{
            k: v for k, v in sprint_data.items()
            if k in SprintContext.__dataclass_fields__
        })

    def _get_context_id(self, context: SprintContext) -> str:
        return context.slug

    def _get_filepath(self, context_id: str, current: bool = True) -> Path:
        """Sprint context goes in sprint-specific directory."""
        sprint_dir = self._get_current_dir() / context_id
        sprint_dir.mkdir(parents=True, exist_ok=True)
        return sprint_dir / "context.yaml"

    def get_sprint_dir(self, sprint_slug: str) -> Path:
        """Get the directory for a sprint's context."""
        sprint_dir = self._get_current_dir() / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)
        return sprint_dir

    def write_plan(self, sprint_slug: str, plan_content: str) -> Path:
        """Write a sprint plan document.

        Args:
            sprint_slug: Sprint slug
            plan_content: Markdown content of the sprint plan

        Returns:
            Path to the plan file
        """
        sprint_dir = self.get_sprint_dir(sprint_slug)
        plan_path = sprint_dir / "SPRINT_PLAN.md"

        self._atomic_write(plan_path, plan_content)
        return plan_path

    def add_artifact(
        self,
        sprint_slug: str,
        artifact_name: str,
        content: str,
    ) -> Path:
        """Add an artifact to a sprint's context.

        Args:
            sprint_slug: Sprint slug
            artifact_name: Name of the artifact file
            content: Artifact content

        Returns:
            Path to the artifact file
        """
        sprint_dir = self.get_sprint_dir(sprint_slug)
        artifact_path = sprint_dir / artifact_name

        self._atomic_write(artifact_path, content)
        return artifact_path

    def list_current(self) -> List[str]:
        """List all sprint slugs with context."""
        sprints_dir = self._get_current_dir()
        if not sprints_dir.exists():
            return []

        return [
            d.name
            for d in sprints_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def list_artifacts(self, sprint_slug: str) -> List[str]:
        """List artifacts in a sprint's context directory.

        Returns:
            List of artifact filenames
        """
        sprint_dir = self._get_current_dir() / sprint_slug
        if not sprint_dir.exists():
            return []

        return [
            f.name
            for f in sprint_dir.iterdir()
            if f.is_file()
        ]


class ContextManager:
    """Central manager for all context types.

    Provides unified access to all context writers and manages
    the master index file.
    """

    def __init__(self, context_dir: Optional[Path] = None):
        """Initialize the context manager.

        Args:
            context_dir: Base context directory. Defaults to .vibey/context/
        """
        self.context_dir = context_dir or Path(".vibey/context")
        self._ensure_dirs()

        # Initialize writers
        self.sessions = SessionContextWriter(self.context_dir)
        self.tasks = TaskContextWriter(self.context_dir)
        self.decisions = DecisionContextWriter(self.context_dir)
        self.sprints = SprintContextWriter(self.context_dir)

    def _ensure_dirs(self) -> None:
        """Ensure the context directory structure exists."""
        self.context_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        for subdir in [
            "sessions/current",
            "sessions/history",
            "tasks/current",
            "tasks/completed",
            "decisions",
            "sprints",
            "agents",
            "exports",
        ]:
            (self.context_dir / subdir).mkdir(parents=True, exist_ok=True)

    @property
    def index_path(self) -> Path:
        """Path to the master index file."""
        return self.context_dir / "index.yaml"

    @property
    def config_path(self) -> Path:
        """Path to the config file."""
        return self.context_dir / "config.yaml"

    def update_index(self) -> None:
        """Regenerate the master index file."""
        now = datetime.now(timezone.utc).isoformat()

        # Gather stats
        sessions_current = self.sessions.list_current()
        sessions_history = self.sessions.list_history()
        tasks_current = self.tasks.list_current()
        tasks_completed = self.tasks.list_history()
        decisions = self.decisions.list_current()

        index = {
            "context": {
                "version": "1.0",
                "created": now if not self.index_path.exists() else None,
                "last_updated": now,
                "stats": {
                    "sessions_active": len(sessions_current),
                    "sessions_total": len(sessions_current) + len(sessions_history),
                    "tasks_active": len(tasks_current),
                    "tasks_total": len(tasks_current) + len(tasks_completed),
                    "decisions_total": len(decisions),
                },
                "current": {
                    "session_id": sessions_current[0] if sessions_current else None,
                },
                "recent_tasks": [
                    {"id": tid, "status": "in_progress"}
                    for tid in tasks_current[:5]
                ],
                "recent_decisions": [
                    {"id": did}
                    for did in decisions[:5]
                ],
            }
        }

        # Preserve created date if exists
        if self.index_path.exists():
            try:
                with open(self.index_path) as f:
                    existing = yaml.safe_load(f)
                if existing and "context" in existing:
                    index["context"]["created"] = existing["context"].get("created", now)
            except Exception:
                index["context"]["created"] = now

        content = yaml.dump(index, default_flow_style=False, sort_keys=False)

        # Atomic write
        fd, temp_path = tempfile.mkstemp(suffix=".yaml", dir=self.context_dir)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            shutil.move(temp_path, self.index_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def init_config(self) -> Path:
        """Initialize the config file with defaults."""
        if self.config_path.exists():
            return self.config_path

        config = {
            "context_config": {
                "version": "1.0",
                "retention": {
                    "sessions": {
                        "active_max": 1,
                        "history_days": 90,
                        "archive_format": "yaml",
                    },
                    "tasks": {
                        "completed_days": 180,
                        "archive_monthly": True,
                    },
                    "decisions": {
                        "keep_forever": True,
                    },
                },
                "cleanup": {
                    "enabled": True,
                    "schedule": "weekly",
                    "dry_run_first": True,
                },
            }
        }

        content = yaml.dump(config, default_flow_style=False, sort_keys=False)

        fd, temp_path = tempfile.mkstemp(suffix=".yaml", dir=self.context_dir)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            shutil.move(temp_path, self.config_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

        return self.config_path


# Module-level convenience function
_manager: Optional[ContextManager] = None


def get_context_manager(context_dir: Optional[Path] = None) -> ContextManager:
    """Get or create the global context manager.

    Args:
        context_dir: Optional context directory path

    Returns:
        ContextManager instance
    """
    global _manager
    if _manager is None or context_dir is not None:
        _manager = ContextManager(context_dir)
    return _manager
