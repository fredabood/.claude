"""
Development session commands.

Commands for tracking coding sessions - starting, ending, pausing, resuming,
and reporting on development sessions.
"""

from pathlib import Path
from typing import Optional

from vibey.cli.formatters import format_error, format_success


def session_start_cmd(
    name: Optional[str] = None,
    goals: Optional[list] = None,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    task_ids: Optional[list] = None,
) -> int:
    """Start a new coding session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.start_session(
            name=name,
            goals=goals,
            track_id=track_id,
            sprint_id=sprint_id,
            task_ids=task_ids,
        )

        print(format_success(f"Session started: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {session.status.value}")
        if session.branch:
            print(f"  Branch: {session.branch}")
        if session.goals:
            print(f"  Goals:")
            for goal in session.goals:
                print(f"    - {goal}")
        if session.track_id:
            print(f"  Track: {session.track_id}")
        if session.sprint_id:
            print(f"  Sprint: {session.sprint_id}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to start session: {e}"))
        return 1


def session_end_cmd(
    session_id: Optional[str] = None,
    summary: Optional[str] = None,
    status: str = "completed",
) -> int:
    """End the current or specified session."""
    from vibey.operations.roadmap.session_manager import SessionManager
    from vibey.roadmap.models.session import SessionStatus

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session_status = SessionStatus.COMPLETED if status == "completed" else SessionStatus.ABANDONED
        session = manager.end_session(
            session_id=session_id,
            summary=summary,
            status=session_status,
        )

        status_msg = "completed" if session.status == SessionStatus.COMPLETED else "abandoned"
        print(format_success(f"Session ended: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {status_msg}")
        if session.summary:
            print(f"  Summary: {session.summary}")
        if session.stats:
            print(f"\n  Statistics:")
            print(f"    Duration: {session.stats.duration_seconds // 60} minutes")
            print(f"    Events: {session.stats.events_count}")
            print(f"    Decisions: {session.stats.decisions_count}")
            print(f"    Commits: {session.stats.commits_count}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to end session: {e}"))
        return 1


def session_pause_cmd(session_id: Optional[str] = None) -> int:
    """Pause the current or specified session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.pause_session(session_id=session_id)

        print(format_success(f"Session paused: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {session.status.value}")
        print(f"  Paused at: {session.paused}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to pause session: {e}"))
        return 1


def session_resume_cmd(session_id: str) -> int:
    """Resume a paused session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.resume_session(session_id=session_id)

        print(format_success(f"Session resumed: {session.id}"))
        print(f"\n  Name: {session.name}")
        print(f"  Status: {session.status.value}")
        if session.branch:
            print(f"  Branch: {session.branch}")

        return 0
    except ValueError as e:
        print(format_error(str(e)))
        return 1
    except Exception as e:
        print(format_error(f"Failed to resume session: {e}"))
        return 1


def session_status_cmd() -> int:
    """Show the current active session status."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.get_active_session()

        if not session:
            print("No active session.")
            print("\nStart a new session with: vibey session start")
            return 0

        print(f"Active Session: {session.name}")
        print(f"\n  ID: {session.id}")
        print(f"  Status: {session.status.value}")
        print(f"  Started: {session.started}")
        if session.branch:
            print(f"  Branch: {session.branch}")
        if session.goals:
            print(f"  Goals:")
            for goal in session.goals:
                print(f"    - {goal}")
        if session.track_id:
            print(f"  Track: {session.track_id}")
        if session.sprint_id:
            print(f"  Sprint: {session.sprint_id}")
        if session.task_ids:
            print(f"  Tasks: {len(session.task_ids)} associated")
        if session.events:
            print(f"  Events: {len(session.events)} logged")
        if session.decisions:
            print(f"  Decisions: {len(session.decisions)} recorded")

        return 0
    except Exception as e:
        print(format_error(f"Failed to get session status: {e}"))
        return 1


# Import remaining session commands from commands.py
# These will be fully extracted in a later phase
def session_show_cmd(session_id: str) -> int:
    """Show detailed session information."""
    from vibey.cli.commands import session_show_cmd as impl
    return impl(session_id)


def session_list_cmd(
    status: Optional[str] = None,
    limit: int = 10,
    show_all: bool = False,
) -> int:
    """List sessions."""
    from vibey.cli.commands import session_list_cmd as impl
    return impl(status=status, limit=limit, show_all=show_all)


def session_report_cmd(session_id: str, format: str = "markdown", output: Optional[str] = None) -> int:
    """Generate session report."""
    from vibey.cli.commands import session_report_cmd as impl
    return impl(session_id, format=format, output=output)


def session_timeline_cmd(session_id: str) -> int:
    """Show session timeline."""
    from vibey.cli.commands import session_timeline_cmd as impl
    return impl(session_id)


def session_export_cmd(session_id: str, output: Optional[str] = None) -> int:
    """Export session data."""
    from vibey.cli.commands import session_export_cmd as impl
    return impl(session_id, output=output)


def session_decisions_cmd(session_id: str) -> int:
    """Show session decisions."""
    from vibey.cli.commands import session_decisions_cmd as impl
    return impl(session_id)
