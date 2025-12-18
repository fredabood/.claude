"""
Session management commands.

Provides session creation, management, and reporting functionality.
"""

from pathlib import Path
from typing import Optional

from vibey.cli.formatters import format_success, format_error


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

        status_msg = "✅ completed" if session.status == SessionStatus.COMPLETED else "⚠️ abandoned"
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

        print(f"🎯 Active Session: {session.name}")
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
        if session.commits:
            print(f"  Commits: {len(session.commits)} associated")

        return 0
    except Exception as e:
        print(format_error(f"Failed to get session status: {e}"))
        return 1


def session_show_cmd(session_id: str) -> int:
    """Show detailed information about a specific session."""
    from vibey.operations.roadmap.session_manager import SessionManager

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)
        session = manager.get_session(session_id)

        if not session:
            print(format_error(f"Session not found: {session_id}"))
            return 1

        status_icon = {
            "active": "🟢",
            "paused": "⏸️",
            "completed": "✅",
            "abandoned": "❌",
        }.get(session.status.value, "⚪")

        print(f"{status_icon} Session: {session.name}")
        print(f"\n  ID: {session.id}")
        print(f"  Status: {session.status.value}")
        print(f"  Created: {session.created}")
        if session.started:
            print(f"  Started: {session.started}")
        if session.paused:
            print(f"  Paused: {session.paused}")
        if session.ended:
            print(f"  Ended: {session.ended}")

        # Git info
        if session.branch or session.start_commit:
            print(f"\n  Git:")
            if session.branch:
                print(f"    Branch: {session.branch}")
            if session.start_commit:
                print(f"    Start Commit: {session.start_commit[:8]}")
            if session.end_commit:
                print(f"    End Commit: {session.end_commit[:8]}")

        # Goals
        if session.goals:
            print(f"\n  Goals:")
            for goal in session.goals:
                print(f"    - {goal}")

        # Summary
        if session.summary:
            print(f"\n  Summary: {session.summary}")

        # Associations
        if session.track_id or session.sprint_id or session.task_ids:
            print(f"\n  Roadmap:")
            if session.track_id:
                print(f"    Track: {session.track_id}")
            if session.sprint_id:
                print(f"    Sprint: {session.sprint_id}")
            if session.task_ids:
                print(f"    Tasks: {', '.join(session.task_ids)}")

        # Events summary
        if session.events:
            print(f"\n  Events ({len(session.events)} total):")
            for event in session.events[-5:]:
                print(f"    [{event.timestamp.strftime('%H:%M')}] {event.event_type.value}")
            if len(session.events) > 5:
                print(f"    ... and {len(session.events) - 5} more")

        # Decisions
        if session.decisions:
            print(f"\n  Decisions ({len(session.decisions)} total):")
            for decision in session.decisions[:3]:
                print(f"    - {decision.description[:60]}...")
            if len(session.decisions) > 3:
                print(f"    ... and {len(session.decisions) - 3} more")

        # Commits
        if session.commits:
            print(f"\n  Commits ({len(session.commits)} total):")
            for commit in session.commits[:5]:
                msg = commit.message[:50] if commit.message else "(no message)"
                print(f"    {commit.short_sha}: {msg}")
            if len(session.commits) > 5:
                print(f"    ... and {len(session.commits) - 5} more")

        # Stats
        if session.stats:
            print(f"\n  Statistics:")
            print(f"    Duration: {session.stats.duration_seconds // 60} minutes")
            print(f"    Events: {session.stats.events_count}")
            print(f"    Decisions: {session.stats.decisions_count}")
            print(f"    Commits: {session.stats.commits_count}")
            print(f"    Files Modified: {session.stats.files_modified}")
            print(f"    Tasks Worked: {session.stats.tasks_worked}")
            if session.stats.errors_count:
                print(f"    Errors: {session.stats.errors_count}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to show session: {e}"))
        return 1


def session_list_cmd(
    status: Optional[str] = None,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 20,
) -> int:
    """List sessions with optional filters."""
    from datetime import datetime, timezone
    from vibey.operations.roadmap.session_manager import SessionManager
    from vibey.roadmap.models.session import SessionStatus

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        manager = SessionManager(roadmap_path)

        # Parse filters
        status_filter = SessionStatus(status) if status else None
        since_filter = None
        if since:
            try:
                since_filter = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                import re
                match = re.match(r'^(\d+)([dwmh])$', since.lower())
                if match:
                    from datetime import timedelta
                    amount = int(match.group(1))
                    unit = match.group(2)
                    delta = {
                        'h': timedelta(hours=amount),
                        'd': timedelta(days=amount),
                        'w': timedelta(weeks=amount),
                        'm': timedelta(days=amount * 30),
                    }.get(unit, timedelta(days=7))
                    since_filter = datetime.now(timezone.utc) - delta

        sessions = manager.list_sessions(
            status=status_filter,
            track_id=track_id,
            sprint_id=sprint_id,
            since=since_filter,
            limit=limit,
        )

        if not sessions:
            print("No sessions found.")
            if status or track_id or sprint_id or since:
                print("\nTry removing filters or start a new session with: vibey session start")
            return 0

        print(f"📋 Sessions ({len(sessions)} found)")
        print("=" * 70)

        status_icons = {
            "active": "🟢",
            "paused": "⏸️",
            "completed": "✅",
            "abandoned": "❌",
        }

        for session in sessions:
            icon = status_icons.get(session.status.value, "⚪")
            created = session.created.strftime("%Y-%m-%d %H:%M") if session.created else "unknown"
            print(f"\n{icon} {session.name}")
            print(f"   ID: {session.id}")
            print(f"   Created: {created} | Status: {session.status.value}")
            if session.track_id:
                print(f"   Track: {session.track_id}")
            if session.branch:
                print(f"   Branch: {session.branch}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to list sessions: {e}"))
        return 1


def session_report_cmd(session_id: str, format: str = "markdown", output: Optional[str] = None) -> int:
    """Generate a session report."""
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        report = reconstructor.generate_session_report(session_id, format=format)

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            print(format_success(f"Report written to: {output}"))
        else:
            print(report)

        return 0
    except Exception as e:
        print(format_error(f"Failed to generate report: {e}"))
        return 1


def session_timeline_cmd(session_id: str) -> int:
    """Show session timeline."""
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        timeline = reconstructor.get_session_timeline(session_id)

        if not timeline:
            print(format_error(f"Session not found: {session_id}"))
            return 1

        session = timeline.session
        print(f"📋 Session Timeline: {session.name}")
        print(f"   Duration: {timeline.duration_formatted}")
        print("=" * 60)

        for event in timeline.events:
            time_str = event.timestamp.strftime("%H:%M:%S")
            event_name = event.event_type.value.replace("_", " ").title()

            icons = {
                "session_start": "🟢",
                "session_end": "🔴",
                "session_pause": "⏸️",
                "session_resume": "▶️",
                "task_start": "📋",
                "task_complete": "✅",
                "commit_made": "📝",
                "decision_made": "🤔",
                "file_modified": "📄",
                "error_encountered": "❌",
            }
            icon = icons.get(event.event_type.value, "•")

            detail = ""
            if event.task_id:
                detail = f" (task: {event.task_id[:8]}...)"
            elif event.commit_sha:
                detail = f" ({event.commit_sha[:8]})"
            elif event.file_path:
                detail = f" ({event.file_path})"

            print(f"  {time_str} {icon} {event_name}{detail}")

        return 0
    except Exception as e:
        print(format_error(f"Failed to show timeline: {e}"))
        return 1


def session_export_cmd(session_id: str, output: Optional[str] = None) -> int:
    """Export session for continuation."""
    import json
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        export_data = reconstructor.export_for_continuation(session_id)

        if not export_data:
            print(format_error(f"Session not found: {session_id}"))
            return 1

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(export_data, indent=2, default=str))
            print(format_success(f"Export written to: {output}"))
        else:
            print(json.dumps(export_data, indent=2, default=str))

        return 0
    except Exception as e:
        print(format_error(f"Failed to export session: {e}"))
        return 1


def session_decisions_cmd(session_id: str) -> int:
    """Show decisions made in a session."""
    from vibey.operations.roadmap.session_reconstruction import SessionReconstructor

    root_dir = Path.cwd()
    roadmap_path = root_dir / ".vibey" / "roadmap"

    if not roadmap_path.exists():
        print(format_error("Roadmap not found. Run 'vibey roadmap init' first."))
        return 1

    try:
        reconstructor = SessionReconstructor(roadmap_path)
        decisions = reconstructor.get_decisions_made(session_id)

        if not decisions:
            print("No decisions recorded in this session.")
            return 0

        print(f"🤔 Decisions Made ({len(decisions)} total)")
        print("=" * 60)

        for i, decision in enumerate(decisions, 1):
            time_str = decision.timestamp.strftime("%Y-%m-%d %H:%M")
            print(f"\n{i}. {decision.description}")
            print(f"   Time: {time_str}")
            print(f"   Category: {decision.category.value}")
            print(f"   Confidence: {decision.confidence.value}")

            if decision.rationale:
                print(f"   Rationale: {decision.rationale}")

            if decision.alternatives:
                alts = ", ".join(
                    a.get("name", str(a)) if isinstance(a, dict) else str(a)
                    for a in decision.alternatives
                )
                print(f"   Alternatives: {alts}")

            if decision.revisit:
                print("   ⚠️  Marked for revisit")

        return 0
    except Exception as e:
        print(format_error(f"Failed to show decisions: {e}"))
        return 1
