"""
Session Reconstruction for audit and continuation.

Provides capabilities to:
- Reconstruct session timelines
- Extract decisions made during sessions
- Generate session reports
- Export session state for continuation

Sprint 3.2: Git Versioning for Vibe Coding Sessions
Task 7: Session Reconstruction
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from ...roadmap.models.session import (
    Session,
    SessionEvent,
    SessionEventType,
    Decision,
    SessionCommit,
    ContextSnapshot,
)

logger = logging.getLogger(__name__)


@dataclass
class SessionTimeline:
    """Chronological timeline of session activity."""
    session: Session
    events: List[SessionEvent] = field(default_factory=list)
    commits: List[SessionCommit] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        """Calculate session duration in seconds."""
        if not self.session.started:
            return 0
        end = self.session.ended or datetime.now(timezone.utc)
        return int((end - self.session.started).total_seconds())

    @property
    def duration_formatted(self) -> str:
        """Format duration as human-readable string."""
        total_secs = self.duration_seconds
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class SessionReconstructor:
    """Reconstructs session state for audit or continuation."""

    def __init__(self, roadmap_path: Path):
        """
        Initialize reconstructor.

        Args:
            roadmap_path: Path to .vibey/roadmap directory
        """
        self.roadmap_path = Path(roadmap_path)

    def _get_session_manager(self):
        """Get a SessionManager instance."""
        from .session_manager import SessionManager
        return SessionManager(self.roadmap_path)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        manager = self._get_session_manager()
        return manager.get_session(session_id)

    def get_session_timeline(self, session_id: str) -> Optional[SessionTimeline]:
        """
        Get chronological timeline of session events.

        Args:
            session_id: Session ULID

        Returns:
            SessionTimeline with events, commits, and decisions
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Sort events by timestamp
        events = sorted(session.events, key=lambda e: e.timestamp)
        commits = sorted(session.commits, key=lambda c: c.timestamp)
        decisions = sorted(session.decisions, key=lambda d: d.timestamp)

        return SessionTimeline(
            session=session,
            events=events,
            commits=commits,
            decisions=decisions,
        )

    def get_session_context_at(
        self,
        session_id: str,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """
        Reconstruct context state at a point in time.

        Args:
            session_id: Session ULID
            timestamp: Point in time to reconstruct

        Returns:
            Dictionary with reconstructed context state
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        # Start with initial context snapshot
        context = {}
        if session.context_snapshot:
            context = {
                "git_branch": session.context_snapshot.git_branch,
                "git_commit": session.context_snapshot.git_commit,
                "active_track_id": session.context_snapshot.active_track_id,
                "active_sprint_id": session.context_snapshot.active_sprint_id,
                "active_task_ids": list(session.context_snapshot.active_task_ids),
                "context_files": dict(session.context_snapshot.context_files),
            }

        # Apply events up to timestamp
        for event in sorted(session.events, key=lambda e: e.timestamp):
            if event.timestamp > timestamp:
                break

            # Update context based on event type
            if event.event_type == SessionEventType.TASK_START:
                task_id = event.task_id or event.data.get("task_id")
                if task_id and task_id not in context.get("active_task_ids", []):
                    context.setdefault("active_task_ids", []).append(task_id)

            elif event.event_type == SessionEventType.TASK_COMPLETE:
                task_id = event.task_id or event.data.get("task_id")
                if task_id and task_id in context.get("active_task_ids", []):
                    context["active_task_ids"].remove(task_id)

            elif event.event_type == SessionEventType.COMMIT_MADE:
                context["git_commit"] = event.commit_sha or event.data.get("commit_sha")

            elif event.event_type == SessionEventType.BRANCH_CHANGED:
                context["git_branch"] = event.data.get("branch")

            elif event.event_type == SessionEventType.FILE_MODIFIED:
                file_path = event.file_path or event.data.get("file_path")
                if file_path:
                    context.setdefault("modified_files", set()).add(file_path)

            elif event.event_type == SessionEventType.CONTEXT_UPDATED:
                context.update(event.data.get("context", {}))

        # Convert sets to lists for JSON serialization
        if "modified_files" in context:
            context["modified_files"] = list(context["modified_files"])

        context["timestamp"] = timestamp.isoformat()
        return context

    def get_decisions_made(self, session_id: str) -> List[Decision]:
        """
        Extract decisions made during session.

        Args:
            session_id: Session ULID

        Returns:
            List of Decision objects
        """
        session = self.get_session(session_id)
        if not session:
            return []

        return sorted(session.decisions, key=lambda d: d.timestamp)

    def generate_session_report(
        self,
        session_id: str,
        format: str = "markdown",
    ) -> str:
        """
        Generate human-readable session report.

        Args:
            session_id: Session ULID
            format: Output format ('markdown' or 'text')

        Returns:
            Formatted report string
        """
        timeline = self.get_session_timeline(session_id)
        if not timeline:
            return f"Session not found: {session_id}"

        session = timeline.session

        if format == "markdown":
            return self._generate_markdown_report(timeline)
        else:
            return self._generate_text_report(timeline)

    def _generate_markdown_report(self, timeline: SessionTimeline) -> str:
        """Generate markdown format report."""
        session = timeline.session
        lines = []

        # Header
        lines.append(f"# Session Report: {session.id[:8]}...")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append(f"- **Name:** {session.name}")
        lines.append(f"- **Status:** {session.status.value.capitalize()}")
        lines.append(f"- **Duration:** {timeline.duration_formatted}")

        if session.started:
            start_str = session.started.strftime("%Y-%m-%d %H:%M")
            end_str = session.ended.strftime("%H:%M") if session.ended else "ongoing"
            lines.append(f"- **Period:** {start_str} - {end_str}")

        if session.branch:
            lines.append(f"- **Branch:** {session.branch}")

        if session.summary:
            lines.append(f"- **Summary:** {session.summary}")

        lines.append("")

        # Goals
        if session.goals:
            lines.append("## Goals")
            for goal in session.goals:
                # Check if goal was achieved (look for goal_achieved events)
                achieved = any(
                    e.event_type == SessionEventType.GOAL_ACHIEVED and
                    e.data.get("goal") == goal
                    for e in timeline.events
                )
                checkbox = "[x]" if achieved else "[ ]"
                lines.append(f"- {checkbox} {goal}")
            lines.append("")

        # Tasks Worked On
        if session.task_ids:
            lines.append("## Tasks Worked On")
            for task_id in session.task_ids:
                # Check task completion status from events
                completed = any(
                    e.event_type == SessionEventType.TASK_COMPLETE and
                    (e.task_id == task_id or e.data.get("task_id") == task_id)
                    for e in timeline.events
                )
                status = "completed" if completed else "in progress"
                lines.append(f"- {task_id[:8]}... ({status})")
            lines.append("")

        # Commits Made
        if timeline.commits:
            lines.append("## Commits Made")
            for commit in timeline.commits:
                msg = commit.message[:60] if commit.message else "(no message)"
                if len(commit.message or "") > 60:
                    msg += "..."
                lines.append(f"- `{commit.short_sha}`: {msg}")
            lines.append("")

        # Key Decisions
        if timeline.decisions:
            lines.append("## Key Decisions")
            for i, decision in enumerate(timeline.decisions, 1):
                lines.append(f"{i}. **Decision:** {decision.description}")
                if decision.rationale:
                    lines.append(f"   - **Rationale:** {decision.rationale}")
                if decision.alternatives:
                    alts = ", ".join(
                        a.get("name", str(a)) if isinstance(a, dict) else str(a)
                        for a in decision.alternatives
                    )
                    lines.append(f"   - **Alternatives considered:** {alts}")
                lines.append("")

        # Timeline
        if timeline.events:
            lines.append("## Timeline")
            lines.append("")
            lines.append("| Time | Event | Details |")
            lines.append("|------|-------|---------|")

            for event in timeline.events:
                time_str = event.timestamp.strftime("%H:%M")
                event_name = event.event_type.value.replace("_", " ").title()

                # Extract key detail
                detail = ""
                if event.task_id:
                    detail = f"Task: {event.task_id[:8]}..."
                elif event.commit_sha:
                    detail = f"Commit: {event.commit_sha[:8]}"
                elif event.file_path:
                    detail = f"File: {event.file_path}"
                elif event.data:
                    # Get first interesting key
                    for key in ["message", "description", "name", "goal", "error"]:
                        if key in event.data:
                            val = str(event.data[key])[:40]
                            detail = f"{key}: {val}"
                            break

                lines.append(f"| {time_str} | {event_name} | {detail} |")

            lines.append("")

        # Statistics
        lines.append("## Statistics")
        lines.append(f"- Events logged: {len(timeline.events)}")
        lines.append(f"- Decisions made: {len(timeline.decisions)}")
        lines.append(f"- Commits associated: {len(timeline.commits)}")
        if session.stats:
            if session.stats.files_modified:
                lines.append(f"- Files modified: {session.stats.files_modified}")
            if session.stats.errors_count:
                lines.append(f"- Errors encountered: {session.stats.errors_count}")
        lines.append("")

        return "\n".join(lines)

    def _generate_text_report(self, timeline: SessionTimeline) -> str:
        """Generate plain text format report."""
        session = timeline.session
        lines = []

        lines.append(f"Session Report: {session.id}")
        lines.append("=" * 60)
        lines.append(f"Name: {session.name}")
        lines.append(f"Status: {session.status.value}")
        lines.append(f"Duration: {timeline.duration_formatted}")
        lines.append("")

        if session.goals:
            lines.append("Goals:")
            for goal in session.goals:
                lines.append(f"  - {goal}")
            lines.append("")

        if session.task_ids:
            lines.append("Tasks:")
            for task_id in session.task_ids:
                lines.append(f"  - {task_id}")
            lines.append("")

        if timeline.commits:
            lines.append("Commits:")
            for commit in timeline.commits:
                lines.append(f"  - {commit.short_sha}: {commit.message}")
            lines.append("")

        if timeline.decisions:
            lines.append("Decisions:")
            for decision in timeline.decisions:
                lines.append(f"  - {decision.description}")
            lines.append("")

        return "\n".join(lines)

    def export_for_continuation(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Export session state for continuation in new session.

        Args:
            session_id: Session ULID

        Returns:
            Dictionary with state needed to continue work
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        # Find incomplete tasks
        incomplete_tasks = []
        for task_id in session.task_ids:
            completed = any(
                e.event_type == SessionEventType.TASK_COMPLETE and
                (e.task_id == task_id or e.data.get("task_id") == task_id)
                for e in session.events
            )
            if not completed:
                incomplete_tasks.append(task_id)

        # Find incomplete goals
        incomplete_goals = []
        for goal in session.goals:
            achieved = any(
                e.event_type == SessionEventType.GOAL_ACHIEVED and
                e.data.get("goal") == goal
                for e in session.events
            )
            if not achieved:
                incomplete_goals.append(goal)

        # Get decisions that should be revisited
        revisit_decisions = [
            {
                "description": d.description,
                "rationale": d.rationale,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in session.decisions if d.revisit
        ]

        # Get last known context
        last_context = self.get_session_context_at(
            session_id,
            session.ended or datetime.now(timezone.utc)
        )

        return {
            "original_session_id": session_id,
            "original_session_name": session.name,
            "track_id": session.track_id,
            "sprint_id": session.sprint_id,
            "branch": session.branch,
            "last_commit": session.end_commit or session.start_commit,
            "incomplete_tasks": incomplete_tasks,
            "incomplete_goals": incomplete_goals,
            "revisit_decisions": revisit_decisions,
            "last_context": last_context,
            "continuation_suggested": True,
        }


def get_reconstructor(roadmap_path: Path) -> SessionReconstructor:
    """
    Factory function to create a SessionReconstructor.

    Args:
        roadmap_path: Path to .vibey/roadmap directory

    Returns:
        SessionReconstructor instance
    """
    return SessionReconstructor(roadmap_path)
