"""
Session Manager for AI-assisted coding sessions.

Manages the lifecycle of coding sessions, including:
- Starting and ending sessions
- Logging events and decisions
- Associating commits and tasks
- Capturing context snapshots
- Synchronizing YAML and SQLite storage

This is the primary interface for session tracking operations.
"""

import hashlib
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from ulid import ULID

from ...roadmap.models.session import (
    Session,
    SessionStatus,
    SessionEvent,
    SessionEventType,
    Decision,
    DecisionCategory,
    DecisionConfidence,
    ContextSnapshot,
    SessionCommit,
)
from ...roadmap.serialization.session_yaml import (
    load_session_from_file,
    save_session_to_file,
    get_session_path,
    get_sessions_directory,
    list_session_files,
)
from ...roadmap.serialization.session_sql import (
    load_session as sql_load_session,
    save_session as sql_save_session,
    list_sessions as sql_list_sessions,
    get_active_session as sql_get_active_session,
    ensure_session_tables,
)


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session lifecycle and operations.

    Uses dual storage (YAML + SQLite):
    - YAML files are the source of truth (git-friendly)
    - SQLite provides fast queries (cache)
    """

    def __init__(self, roadmap_path: Path, db_path: Optional[Path] = None):
        """
        Initialize SessionManager.

        Args:
            roadmap_path: Path to .vibey/roadmap directory
            db_path: Optional SQLite database path (default: roadmap_path/../roadmap.db)
        """
        self.roadmap_path = Path(roadmap_path)
        self.sessions_dir = get_sessions_directory(self.roadmap_path)
        self.db_path = db_path or (self.roadmap_path.parent / "roadmap.db")

        # Ensure sessions directory exists
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Ensure SQLite tables exist
        try:
            ensure_session_tables(str(self.db_path))
        except Exception as e:
            logger.warning(f"Could not ensure session tables: {e}")

    # =========================================================================
    # Session Lifecycle
    # =========================================================================

    def start_session(
        self,
        name: Optional[str] = None,
        goals: Optional[List[str]] = None,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
        roadmap_id: str = "vibey-framework-v2",
    ) -> Session:
        """
        Start a new coding session.

        Args:
            name: Human-readable session name (auto-generated if not provided)
            goals: List of session goals
            track_id: Associated track ID
            sprint_id: Associated sprint ID
            task_ids: Initial task IDs to associate
            roadmap_id: Parent roadmap ID

        Returns:
            New Session object

        Raises:
            ValueError: If there's already an active session
        """
        # Check for existing active session
        active = self.get_active_session()
        if active:
            raise ValueError(
                f"Cannot start new session: session '{active.name}' ({active.id}) is already active. "
                f"End it first with session_manager.end_session()"
            )

        # Generate session ID and name
        session_id = str(ULID())
        now = datetime.now(timezone.utc)

        if not name:
            name = f"Session {now.strftime('%Y-%m-%d %H:%M')}"

        # Capture git state
        git_state = self._capture_git_state()

        # Create session
        session = Session(
            id=session_id,
            name=name,
            status=SessionStatus.ACTIVE,
            created=now,
            started=now,
            roadmap_id=roadmap_id,
            track_id=track_id,
            sprint_id=sprint_id,
            task_ids=task_ids or [],
            branch=git_state.get("branch"),
            start_commit=git_state.get("commit"),
            goals=goals or [],
            metadata={
                "python_version": sys.version,
                "vibey_version": self._get_vibey_version(),
                "platform": sys.platform,
            },
        )

        # Capture context snapshot
        snapshot = self._capture_context_snapshot(session_id, "session_start")
        session.context_snapshot = snapshot

        # Log session start event
        start_event = SessionEvent(
            id=str(ULID()),
            session_id=session_id,
            timestamp=now,
            event_type=SessionEventType.SESSION_START,
            data={
                "name": name,
                "goals": goals or [],
                "git_branch": git_state.get("branch"),
                "git_commit": git_state.get("commit"),
            },
        )
        session.add_event(start_event)

        # Save to both storages
        self._save_session(session)

        logger.info(f"Started session: {session_id} ({name})")
        return session

    def end_session(
        self,
        session_id: Optional[str] = None,
        summary: Optional[str] = None,
        status: SessionStatus = SessionStatus.COMPLETED,
    ) -> Session:
        """
        End a coding session.

        Args:
            session_id: Session ID to end (None = active session)
            summary: Optional session summary
            status: End status (completed or abandoned)

        Returns:
            Updated Session object

        Raises:
            ValueError: If session not found or not active
        """
        # Get session
        if session_id:
            session = self.get_session(session_id)
        else:
            session = self.get_active_session()

        if not session:
            raise ValueError("No session to end")

        if session.status not in (SessionStatus.ACTIVE, SessionStatus.PAUSED):
            raise ValueError(f"Session {session.id} is not active (status: {session.status})")

        now = datetime.now(timezone.utc)

        # Capture end git state
        git_state = self._capture_git_state()

        # Update session
        session.status = status
        session.ended = now
        session.end_commit = git_state.get("commit")
        session.summary = summary

        # Compute final stats
        session.stats = session.compute_stats()

        # Log session end event
        end_event = SessionEvent(
            id=str(ULID()),
            session_id=session.id,
            timestamp=now,
            event_type=SessionEventType.SESSION_END,
            data={
                "status": status.value,
                "summary": summary,
                "git_commit": git_state.get("commit"),
                "duration_seconds": session.duration_seconds,
                "events_count": len(session.events),
                "decisions_count": len(session.decisions),
                "commits_count": len(session.commits),
            },
        )
        session.add_event(end_event)

        # Save to both storages
        self._save_session(session)

        logger.info(f"Ended session: {session.id} ({status.value})")
        return session

    def pause_session(self, session_id: Optional[str] = None) -> Session:
        """Pause the active session."""
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            raise ValueError("No session to pause")

        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session.id} is not active")

        now = datetime.now(timezone.utc)
        session.status = SessionStatus.PAUSED
        session.paused = now

        # Log pause event
        pause_event = SessionEvent(
            id=str(ULID()),
            session_id=session.id,
            timestamp=now,
            event_type=SessionEventType.SESSION_PAUSE,
            data={"paused_at": now.isoformat()},
        )
        session.add_event(pause_event)

        self._save_session(session)
        logger.info(f"Paused session: {session.id}")
        return session

    def resume_session(self, session_id: str) -> Session:
        """Resume a paused session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != SessionStatus.PAUSED:
            raise ValueError(f"Session {session.id} is not paused")

        # Check for other active sessions
        active = self.get_active_session()
        if active and active.id != session_id:
            raise ValueError(f"Cannot resume: session {active.id} is already active")

        now = datetime.now(timezone.utc)
        session.status = SessionStatus.ACTIVE
        session.paused = None

        # Log resume event
        resume_event = SessionEvent(
            id=str(ULID()),
            session_id=session.id,
            timestamp=now,
            event_type=SessionEventType.SESSION_RESUME,
            data={"resumed_at": now.isoformat()},
        )
        session.add_event(resume_event)

        self._save_session(session)
        logger.info(f"Resumed session: {session.id}")
        return session

    # =========================================================================
    # Session Queries
    # =========================================================================

    def get_active_session(self) -> Optional[Session]:
        """Get the currently active session."""
        # Try SQLite first (faster)
        try:
            session = sql_get_active_session(str(self.db_path))
            if session:
                return session
        except Exception:
            pass

        # Fall back to YAML
        for path in list_session_files(self.roadmap_path):
            try:
                session = load_session_from_file(path)
                if session.status == SessionStatus.ACTIVE:
                    return session
            except Exception:
                continue

        return None

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        # Try YAML first (source of truth)
        path = get_session_path(self.roadmap_path, session_id)
        if path.exists():
            try:
                return load_session_from_file(path)
            except Exception as e:
                logger.warning(f"Failed to load session from YAML: {e}")

        # Fall back to SQLite
        try:
            return sql_load_session(session_id, str(self.db_path))
        except Exception:
            return None

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Session]:
        """List sessions with optional filters."""
        try:
            return sql_list_sessions(
                db_path=str(self.db_path),
                status=status,
                track_id=track_id,
                sprint_id=sprint_id,
                since=since,
                until=until,
                limit=limit,
            )
        except Exception as e:
            logger.warning(f"Failed to list sessions from SQLite: {e}")
            # Fall back to YAML
            sessions = []
            for path in list_session_files(self.roadmap_path):
                try:
                    session = load_session_from_file(path)
                    if status and session.status != status:
                        continue
                    if track_id and session.track_id != track_id:
                        continue
                    if sprint_id and session.sprint_id != sprint_id:
                        continue
                    sessions.append(session)
                except Exception:
                    continue
            return sessions[:limit]

    # =========================================================================
    # Event Logging
    # =========================================================================

    def log_event(
        self,
        event_type: SessionEventType,
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        commit_sha: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> SessionEvent:
        """
        Log an event to the active session.

        Args:
            event_type: Type of event
            data: Event-specific data
            session_id: Session ID (None = active session)
            task_id: Related task ID
            commit_sha: Related commit SHA
            file_path: Related file path

        Returns:
            Created SessionEvent

        Raises:
            ValueError: If no active session
        """
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            raise ValueError("No active session to log event to")

        event = SessionEvent(
            id=str(ULID()),
            session_id=session.id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            data=data,
            task_id=task_id,
            commit_sha=commit_sha,
            file_path=file_path,
        )

        session.add_event(event)
        self._save_session(session)

        return event

    def log_decision(
        self,
        description: str,
        rationale: Optional[str] = None,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        category: DecisionCategory = DecisionCategory.OTHER,
        confidence: DecisionConfidence = DecisionConfidence.MEDIUM,
        related_files: Optional[List[str]] = None,
        related_tasks: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> Decision:
        """
        Log a decision to the active session.

        Args:
            description: What was decided
            rationale: Why this decision was made
            alternatives: List of alternatives considered
            category: Decision category
            confidence: Confidence level
            related_files: Related file paths
            related_tasks: Related task IDs
            session_id: Session ID (None = active session)

        Returns:
            Created Decision

        Raises:
            ValueError: If no active session
        """
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            raise ValueError("No active session to log decision to")

        decision = Decision(
            id=str(ULID()),
            session_id=session.id,
            timestamp=datetime.now(timezone.utc),
            description=description,
            category=category,
            confidence=confidence,
            rationale=rationale,
            alternatives=alternatives or [],
            related_files=related_files or [],
            related_commits=[],
            related_tasks=related_tasks or [],
        )

        session.add_decision(decision)
        self._save_session(session)

        return decision

    # =========================================================================
    # Associations
    # =========================================================================

    def associate_task(
        self, task_id: str, session_id: Optional[str] = None
    ) -> None:
        """Associate a task with the session."""
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            raise ValueError("No active session")

        session.add_task(task_id)

        # Log task association event
        event = SessionEvent(
            id=str(ULID()),
            session_id=session.id,
            timestamp=datetime.now(timezone.utc),
            event_type=SessionEventType.TASK_START,
            data={"task_id": task_id},
            task_id=task_id,
        )
        session.add_event(event)

        # Save session with both task and event
        self._save_session(session)

    def associate_commit(
        self,
        commit_sha: str,
        message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Associate a git commit with the session."""
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            raise ValueError("No active session")

        # Get commit details if not provided
        if not message:
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%s", commit_sha],
                    capture_output=True,
                    text=True,
                    cwd=str(self.roadmap_path.parent.parent),
                )
                message = result.stdout.strip() if result.returncode == 0 else ""
            except Exception:
                message = ""

        # Get commit stats
        stats = self._get_commit_stats(commit_sha)

        commit = SessionCommit(
            session_id=session.id,
            commit_sha=commit_sha,
            short_sha=commit_sha[:7],
            timestamp=datetime.now(timezone.utc),
            message=message,
            author=stats.get("author"),
            files_changed=stats.get("files_changed", 0),
            insertions=stats.get("insertions", 0),
            deletions=stats.get("deletions", 0),
        )

        session.add_commit(commit)

        # Log commit event
        event = SessionEvent(
            id=str(ULID()),
            session_id=session.id,
            timestamp=datetime.now(timezone.utc),
            event_type=SessionEventType.COMMIT_MADE,
            data={
                "commit_sha": commit_sha,
                "message": message,
                "files_changed": stats.get("files_changed", 0),
            },
            commit_sha=commit_sha,
        )
        session.add_event(event)

        # Save session with both commit and event
        self._save_session(session)

    # =========================================================================
    # Context Snapshots
    # =========================================================================

    def capture_snapshot(
        self, session_id: Optional[str] = None, snapshot_type: str = "checkpoint"
    ) -> ContextSnapshot:
        """Capture a context snapshot for the session."""
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            raise ValueError("No active session")

        snapshot = self._capture_context_snapshot(session.id, snapshot_type)

        # Log snapshot event
        self.log_event(
            SessionEventType.CONTEXT_SNAPSHOT,
            data={
                "snapshot_id": snapshot.id,
                "snapshot_type": snapshot_type,
                "git_commit": snapshot.git_commit,
            },
        )

        return snapshot

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _save_session(self, session: Session) -> None:
        """Save session to both YAML and SQLite."""
        # Save to YAML (source of truth)
        path = get_session_path(self.roadmap_path, session.id)
        try:
            save_session_to_file(session, path)
        except Exception as e:
            logger.error(f"Failed to save session to YAML: {e}")
            raise

        # Save to SQLite (cache)
        try:
            sql_save_session(session, str(self.db_path))
        except Exception as e:
            logger.warning(f"Failed to save session to SQLite: {e}")

    def _capture_git_state(self) -> Dict[str, Any]:
        """Capture current git state."""
        repo_path = self.roadmap_path.parent.parent
        state = {}

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            if result.returncode == 0:
                state["branch"] = result.stdout.strip()

            # Get current commit
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            if result.returncode == 0:
                state["commit"] = result.stdout.strip()

            # Check if dirty
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            state["dirty"] = bool(result.stdout.strip()) if result.returncode == 0 else False

            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            if result.returncode == 0:
                state["staged_files"] = [f for f in result.stdout.strip().split("\n") if f]

            # Get modified files
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            if result.returncode == 0:
                state["modified_files"] = [f for f in result.stdout.strip().split("\n") if f]

        except Exception as e:
            logger.warning(f"Failed to capture git state: {e}")

        return state

    def _capture_context_snapshot(
        self, session_id: str, snapshot_type: str
    ) -> ContextSnapshot:
        """Capture a full context snapshot."""
        git_state = self._capture_git_state()
        now = datetime.now(timezone.utc)

        # Hash context files
        context_files = {}
        claude_md = self.roadmap_path.parent.parent / "CLAUDE.md"
        if claude_md.exists():
            context_files[str(claude_md)] = self._hash_file(claude_md)

        # Hash config files
        config_dir = self.roadmap_path.parent / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                context_files[str(config_file)] = self._hash_file(config_file)

        # Get active roadmap items (simplified - would integrate with roadmap system)
        active_track_id = None
        active_sprint_id = None
        active_task_ids = []

        return ContextSnapshot(
            id=str(ULID()),
            session_id=session_id,
            timestamp=now,
            snapshot_type=snapshot_type,
            git_branch=git_state.get("branch"),
            git_commit=git_state.get("commit"),
            git_dirty=git_state.get("dirty", False),
            git_staged_files=git_state.get("staged_files", []),
            git_modified_files=git_state.get("modified_files", []),
            context_files=context_files,
            active_track_id=active_track_id,
            active_sprint_id=active_sprint_id,
            active_task_ids=active_task_ids,
            environment={
                "python_version": sys.version,
                "platform": sys.platform,
                "cwd": os.getcwd(),
            },
            config_hash=self._hash_config_dir(),
        )

    def _hash_file(self, path: Path) -> str:
        """Hash a file's contents."""
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return ""

    def _hash_config_dir(self) -> Optional[str]:
        """Hash all config files for change detection."""
        config_dir = self.roadmap_path.parent / "config"
        if not config_dir.exists():
            return None

        hasher = hashlib.sha256()
        for config_file in sorted(config_dir.glob("*.yaml")):
            try:
                with open(config_file, "rb") as f:
                    hasher.update(f.read())
            except Exception:
                pass

        return hasher.hexdigest()[:16]

    def _get_commit_stats(self, commit_sha: str) -> Dict[str, Any]:
        """Get statistics for a git commit."""
        repo_path = self.roadmap_path.parent.parent
        stats = {}

        try:
            # Get author
            result = subprocess.run(
                ["git", "log", "-1", "--format=%an <%ae>", commit_sha],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            if result.returncode == 0:
                stats["author"] = result.stdout.strip()

            # Get diff stats
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--numstat", "-r", commit_sha],
                capture_output=True,
                text=True,
                cwd=str(repo_path),
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.strip().split("\n") if l]
                stats["files_changed"] = len(lines)
                insertions = 0
                deletions = 0
                for line in lines:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        try:
                            insertions += int(parts[0]) if parts[0] != "-" else 0
                            deletions += int(parts[1]) if parts[1] != "-" else 0
                        except ValueError:
                            pass
                stats["insertions"] = insertions
                stats["deletions"] = deletions

        except Exception as e:
            logger.warning(f"Failed to get commit stats: {e}")

        return stats

    def _get_vibey_version(self) -> str:
        """Get vibey version."""
        try:
            from vibey import __version__
            return __version__
        except Exception:
            return "unknown"
