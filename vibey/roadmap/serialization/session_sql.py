"""
SQLite loader/dumper for session objects.

Provides fast query access to session data using the SQLite database
as a query cache alongside YAML files (source of truth).

Schema Reference:
- sessions: Main session table
- session_events: Event log
- session_tasks: Task associations
- session_commits: Git commit associations
- session_snapshots: Context snapshots
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from ..models.session import (
    Session,
    SessionStatus,
    SessionEvent,
    SessionEventType,
    Decision,
    ContextSnapshot,
    SessionCommit,
    SessionStats,
)
from ..database import get_connection


def _to_path(db_path: Optional[Union[str, Path]]) -> Optional[Path]:
    """Convert string or Path to Path object."""
    if db_path is None:
        return None
    if isinstance(db_path, Path):
        return db_path
    return Path(db_path)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse datetime from SQLite string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return value


def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime for SQLite storage."""
    if dt is None:
        return None
    return dt.isoformat()


def _parse_json(value: Optional[str], default: Any = None) -> Any:
    """Parse JSON string, returning default if None or invalid."""
    if value is None:
        return default if default is not None else {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default if default is not None else {}
    return value


def _dump_json(value: Any) -> Optional[str]:
    """Dump value to JSON string."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert sqlite3.Row to dict."""
    if row is None:
        return {}
    return dict(row)


# =============================================================================
# Session Loading
# =============================================================================

def load_session(session_id: str, db_path: Optional[str] = None) -> Optional[Session]:
    """
    Load a session from SQLite database.

    Args:
        session_id: Session ULID
        db_path: Optional database path (uses default if not provided)

    Returns:
        Session object or None if not found
    """
    conn = get_connection(_to_path(db_path))
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()

    if not row:
        return None

    # Load associated data
    events = _load_session_events(cursor, session_id)
    commits = _load_session_commits(cursor, session_id)
    task_ids = _load_session_task_ids(cursor, session_id)
    snapshot = _load_session_snapshot(cursor, session_id, "session_start")

    # Extract decisions from events
    decisions = []
    for event in events:
        if event.event_type == SessionEventType.DECISION_MADE:
            decisions.append(Decision.from_event(event))

    # Build stats
    stats = SessionStats(
        duration_seconds=row.get('duration_seconds', 0) or 0,
        events_count=row.get('events_count', 0) or 0,
        decisions_count=row.get('decisions_count', 0) or 0,
        commits_count=row.get('commits_count', 0) or 0,
        files_modified=row.get('files_modified', 0) or 0,
        tasks_worked=row.get('tasks_worked', 0) or 0,
        errors_count=row.get('errors_count', 0) or 0,
        token_usage=row.get('token_usage'),
    )

    return Session(
        id=row['id'],
        name=row['name'],
        status=SessionStatus(row['status']),
        created=_parse_datetime(row.get('created_at')),
        started=_parse_datetime(row.get('started_at')),
        paused=_parse_datetime(row.get('paused_at')),
        ended=_parse_datetime(row.get('ended_at')),
        roadmap_id=row.get('roadmap_id', ''),
        track_id=row.get('track_id'),
        sprint_id=row.get('sprint_id'),
        task_ids=task_ids,
        branch=row.get('branch'),
        start_commit=row.get('start_commit'),
        end_commit=row.get('end_commit'),
        commits=commits,
        goals=_parse_json(row.get('goals_json'), []),
        summary=row.get('summary'),
        context_snapshot=snapshot,
        events=events,
        decisions=decisions,
        stats=stats,
        metadata=_parse_json(row.get('metadata_json'), {}),
    )


def _load_session_events(cursor, session_id: str) -> List[SessionEvent]:
    """Load events for a session."""
    cursor.execute("""
        SELECT * FROM session_events
        WHERE session_id = ?
        ORDER BY timestamp
    """, (session_id,))

    events = []
    for row in cursor.fetchall():
        events.append(SessionEvent(
            id=row['id'],
            session_id=row['session_id'],
            timestamp=_parse_datetime(row['timestamp']),
            event_type=SessionEventType(row['event_type']),
            data=_parse_json(row.get('data_json'), {}),
            task_id=row.get('task_id'),
            commit_sha=row.get('commit_sha'),
            file_path=row.get('file_path'),
        ))

    return events


def _load_session_commits(cursor, session_id: str) -> List[SessionCommit]:
    """Load commits for a session."""
    cursor.execute("""
        SELECT * FROM session_commits
        WHERE session_id = ?
        ORDER BY committed_at
    """, (session_id,))

    commits = []
    for row in cursor.fetchall():
        commits.append(SessionCommit(
            session_id=row['session_id'],
            commit_sha=row['commit_sha'],
            short_sha=row.get('short_sha', row['commit_sha'][:7]),
            timestamp=_parse_datetime(row['committed_at']),
            message=row.get('message', ''),
            author=row.get('author'),
            files_changed=row.get('files_changed', 0),
            insertions=row.get('insertions', 0),
            deletions=row.get('deletions', 0),
        ))

    return commits


def _load_session_task_ids(cursor, session_id: str) -> List[str]:
    """Load task IDs for a session."""
    cursor.execute("""
        SELECT task_id FROM session_tasks
        WHERE session_id = ?
        ORDER BY associated_at
    """, (session_id,))

    return [row['task_id'] for row in cursor.fetchall()]


def _load_session_snapshot(
    cursor, session_id: str, snapshot_type: str
) -> Optional[ContextSnapshot]:
    """Load a context snapshot for a session."""
    cursor.execute("""
        SELECT * FROM session_snapshots
        WHERE session_id = ? AND snapshot_type = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id, snapshot_type))

    row = cursor.fetchone()
    if not row:
        return None

    return ContextSnapshot(
        id=row['id'],
        session_id=row['session_id'],
        timestamp=_parse_datetime(row['timestamp']),
        snapshot_type=row['snapshot_type'],
        git_branch=row.get('git_branch'),
        git_commit=row.get('git_commit'),
        git_dirty=bool(row.get('git_dirty', 0)),
        git_staged_files=_parse_json(row.get('git_staged_files_json'), []),
        git_modified_files=_parse_json(row.get('git_modified_files_json'), []),
        context_files=_parse_json(row.get('context_files_json'), {}),
        active_track_id=row.get('active_track_id'),
        active_sprint_id=row.get('active_sprint_id'),
        active_task_ids=_parse_json(row.get('active_task_ids_json'), []),
        environment=_parse_json(row.get('environment_json'), {}),
        config_hash=row.get('config_hash'),
    )


# =============================================================================
# Session Listing/Querying
# =============================================================================

def list_sessions(
    db_path: Optional[str] = None,
    status: Optional[SessionStatus] = None,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 50,
) -> List[Session]:
    """
    List sessions with optional filters.

    Args:
        db_path: Optional database path
        status: Filter by status
        track_id: Filter by track
        sprint_id: Filter by sprint
        since: Filter by created date (after)
        until: Filter by created date (before)
        limit: Maximum number of results

    Returns:
        List of Session objects
    """
    conn = get_connection(_to_path(db_path))
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    query = "SELECT id FROM sessions WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status.value)

    if track_id:
        query += " AND track_id = ?"
        params.append(track_id)

    if sprint_id:
        query += " AND sprint_id = ?"
        params.append(sprint_id)

    if since:
        query += " AND created_at >= ?"
        params.append(_format_datetime(since))

    if until:
        query += " AND created_at <= ?"
        params.append(_format_datetime(until))

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor = conn.cursor()
    cursor.execute(query, params)

    sessions = []
    for row in cursor.fetchall():
        session = load_session(row['id'], db_path)
        if session:
            sessions.append(session)

    return sessions


def get_active_session(db_path: Optional[str] = None) -> Optional[Session]:
    """Get the currently active session."""
    sessions = list_sessions(db_path, status=SessionStatus.ACTIVE, limit=1)
    return sessions[0] if sessions else None


def get_sessions_by_commit(
    commit_sha: str, db_path: Optional[str] = None
) -> List[Session]:
    """Get all sessions that contain a specific commit."""
    conn = get_connection(_to_path(db_path))
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT session_id FROM session_commits
        WHERE commit_sha = ?
    """, (commit_sha,))

    sessions = []
    for row in cursor.fetchall():
        session = load_session(row['session_id'], db_path)
        if session:
            sessions.append(session)

    return sessions


def get_sessions_by_task(task_id: str, db_path: Optional[str] = None) -> List[Session]:
    """Get all sessions that worked on a specific task."""
    conn = get_connection(_to_path(db_path))
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT session_id FROM session_tasks
        WHERE task_id = ?
    """, (task_id,))

    sessions = []
    for row in cursor.fetchall():
        session = load_session(row['session_id'], db_path)
        if session:
            sessions.append(session)

    return sessions


# =============================================================================
# Session Saving
# =============================================================================

def save_session(session: Session, db_path: Optional[str] = None) -> None:
    """
    Save a session to SQLite database.

    Args:
        session: Session object to save
        db_path: Optional database path
    """
    conn = get_connection(_to_path(db_path))
    cursor = conn.cursor()

    # Compute stats
    stats = session.compute_stats()

    # Upsert session
    cursor.execute("""
        INSERT OR REPLACE INTO sessions (
            id, name, status, created_at, started_at, paused_at, ended_at,
            roadmap_id, track_id, sprint_id,
            branch, start_commit, end_commit,
            goals_json, summary, token_usage,
            events_count, decisions_count, commits_count,
            files_modified, tasks_worked, errors_count, duration_seconds,
            metadata_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session.id,
        session.name,
        session.status.value,
        _format_datetime(session.created),
        _format_datetime(session.started),
        _format_datetime(session.paused),
        _format_datetime(session.ended),
        session.roadmap_id,
        session.track_id,
        session.sprint_id,
        session.branch,
        session.start_commit,
        session.end_commit,
        _dump_json(session.goals),
        session.summary,
        stats.token_usage,
        stats.events_count,
        stats.decisions_count,
        stats.commits_count,
        stats.files_modified,
        stats.tasks_worked,
        stats.errors_count,
        stats.duration_seconds,
        _dump_json(session.metadata),
        _format_datetime(datetime.now(timezone.utc)),
    ))

    # Save events
    for event in session.events:
        _save_event(cursor, event)

    # Save commits
    for commit in session.commits:
        _save_commit(cursor, commit)

    # Save task associations
    _save_task_associations(cursor, session.id, session.task_ids)

    # Save snapshot if present
    if session.context_snapshot:
        _save_snapshot(cursor, session.context_snapshot)

    conn.commit()


def _save_event(cursor, event: SessionEvent) -> None:
    """Save a session event."""
    cursor.execute("""
        INSERT OR REPLACE INTO session_events (
            id, session_id, timestamp, event_type, data_json,
            task_id, commit_sha, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event.id,
        event.session_id,
        _format_datetime(event.timestamp),
        event.event_type.value,
        _dump_json(event.data),
        event.task_id,
        event.commit_sha,
        event.file_path,
    ))


def _save_commit(cursor, commit: SessionCommit) -> None:
    """Save a session commit."""
    cursor.execute("""
        INSERT OR REPLACE INTO session_commits (
            session_id, commit_sha, short_sha, committed_at,
            message, author, files_changed, insertions, deletions
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        commit.session_id,
        commit.commit_sha,
        commit.short_sha,
        _format_datetime(commit.timestamp),
        commit.message,
        commit.author,
        commit.files_changed,
        commit.insertions,
        commit.deletions,
    ))


def _save_task_associations(cursor, session_id: str, task_ids: List[str]) -> None:
    """Save session-task associations."""
    # Remove existing associations
    cursor.execute("DELETE FROM session_tasks WHERE session_id = ?", (session_id,))

    # Add current associations
    now = _format_datetime(datetime.now(timezone.utc))
    for task_id in task_ids:
        cursor.execute("""
            INSERT INTO session_tasks (session_id, task_id, associated_at)
            VALUES (?, ?, ?)
        """, (session_id, task_id, now))


def _save_snapshot(cursor, snapshot: ContextSnapshot) -> None:
    """Save a context snapshot."""
    cursor.execute("""
        INSERT OR REPLACE INTO session_snapshots (
            id, session_id, timestamp, snapshot_type,
            git_branch, git_commit, git_dirty,
            git_staged_files_json, git_modified_files_json,
            context_files_json, config_hash,
            active_track_id, active_sprint_id, active_task_ids_json,
            environment_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        snapshot.id,
        snapshot.session_id,
        _format_datetime(snapshot.timestamp),
        snapshot.snapshot_type,
        snapshot.git_branch,
        snapshot.git_commit,
        1 if snapshot.git_dirty else 0,
        _dump_json(snapshot.git_staged_files),
        _dump_json(snapshot.git_modified_files),
        _dump_json(snapshot.context_files),
        snapshot.config_hash,
        snapshot.active_track_id,
        snapshot.active_sprint_id,
        _dump_json(snapshot.active_task_ids),
        _dump_json(snapshot.environment),
    ))


# =============================================================================
# Session Deletion
# =============================================================================

def delete_session(session_id: str, db_path: Optional[str] = None) -> bool:
    """
    Delete a session and all related data from SQLite.

    Args:
        session_id: Session ULID
        db_path: Optional database path

    Returns:
        True if session was deleted, False if not found
    """
    conn = get_connection(_to_path(db_path))
    cursor = conn.cursor()

    # Check if session exists
    cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
    if not cursor.fetchone():
        return False

    # Delete session (cascades to events, commits, tasks, snapshots)
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()

    return True


# =============================================================================
# Database Migration
# =============================================================================

def ensure_session_tables(db_path: Optional[str] = None) -> None:
    """
    Ensure session tables exist in the database.

    Runs the session schema migration if tables don't exist.
    """
    conn = get_connection(_to_path(db_path))
    cursor = conn.cursor()

    # Check if sessions table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='sessions'
    """)

    if not cursor.fetchone():
        # Run migration
        migration_path = Path(__file__).parent.parent / "database" / "migrations" / "007_sessions_schema.sql"
        if migration_path.exists():
            with open(migration_path) as f:
                cursor.executescript(f.read())
            conn.commit()
