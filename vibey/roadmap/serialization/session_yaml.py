"""
YAML serialization for session objects.

Loads and saves Session, SessionEvent, Decision, and ContextSnapshot
objects to/from YAML files.

File Structure:
    .vibey/roadmap/sessions/
    ├── {session_id}.yaml      # Session with embedded events/decisions
    └── ...

Each session YAML file contains:
- Session metadata
- Embedded events (lightweight audit trail)
- Embedded decisions (important for review)
- Context snapshot references
"""

from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import yaml

from ..models.session import (
    Session,
    SessionStatus,
    SessionEvent,
    SessionEventType,
    Decision,
    DecisionCategory,
    DecisionConfidence,
    ContextSnapshot,
    SessionCommit,
    SessionStats,
)


def _parse_datetime(value: Union[str, datetime, date, None]) -> Optional[datetime]:
    """Parse datetime from string, date, or datetime - returns timezone-aware datetime."""
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    return value


def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat()


# =============================================================================
# Session Event Loading/Dumping
# =============================================================================

def _load_event(data: Dict[str, Any]) -> SessionEvent:
    """Load a SessionEvent from a dictionary."""
    return SessionEvent(
        id=data['id'],
        session_id=data['session_id'],
        timestamp=_parse_datetime(data['timestamp']),
        event_type=SessionEventType(data['event_type']),
        data=data.get('data', {}),
        task_id=data.get('task_id'),
        commit_sha=data.get('commit_sha'),
        file_path=data.get('file_path'),
    )


def _dump_event(event: SessionEvent) -> Dict[str, Any]:
    """Dump a SessionEvent to a dictionary."""
    return {
        'id': event.id,
        'session_id': event.session_id,
        'timestamp': _format_datetime(event.timestamp),
        'event_type': event.event_type.value,
        'data': event.data,
        'task_id': event.task_id,
        'commit_sha': event.commit_sha,
        'file_path': event.file_path,
    }


# =============================================================================
# Decision Loading/Dumping
# =============================================================================

def _load_decision(data: Dict[str, Any]) -> Decision:
    """Load a Decision from a dictionary."""
    return Decision(
        id=data['id'],
        session_id=data['session_id'],
        timestamp=_parse_datetime(data['timestamp']),
        description=data['description'],
        category=DecisionCategory(data.get('category', 'other')),
        confidence=DecisionConfidence(data.get('confidence', 'medium')),
        revisit=data.get('revisit', False),
        rationale=data.get('rationale'),
        alternatives=data.get('alternatives', []),
        related_files=data.get('related_files', []),
        related_commits=data.get('related_commits', []),
        related_tasks=data.get('related_tasks', []),
    )


def _dump_decision(decision: Decision) -> Dict[str, Any]:
    """Dump a Decision to a dictionary."""
    return {
        'id': decision.id,
        'session_id': decision.session_id,
        'timestamp': _format_datetime(decision.timestamp),
        'description': decision.description,
        'category': decision.category.value,
        'confidence': decision.confidence.value,
        'revisit': decision.revisit,
        'rationale': decision.rationale,
        'alternatives': decision.alternatives,
        'related_files': decision.related_files,
        'related_commits': decision.related_commits,
        'related_tasks': decision.related_tasks,
    }


# =============================================================================
# Context Snapshot Loading/Dumping
# =============================================================================

def _load_snapshot(data: Dict[str, Any]) -> ContextSnapshot:
    """Load a ContextSnapshot from a dictionary."""
    return ContextSnapshot(
        id=data['id'],
        session_id=data['session_id'],
        timestamp=_parse_datetime(data['timestamp']),
        snapshot_type=data['snapshot_type'],
        git_branch=data.get('git_branch'),
        git_commit=data.get('git_commit'),
        git_dirty=data.get('git_dirty', False),
        git_staged_files=data.get('git_staged_files', []),
        git_modified_files=data.get('git_modified_files', []),
        context_files=data.get('context_files', {}),
        active_track_id=data.get('active_track_id'),
        active_sprint_id=data.get('active_sprint_id'),
        active_task_ids=data.get('active_task_ids', []),
        environment=data.get('environment', {}),
        config_hash=data.get('config_hash'),
    )


def _dump_snapshot(snapshot: ContextSnapshot) -> Dict[str, Any]:
    """Dump a ContextSnapshot to a dictionary."""
    return {
        'id': snapshot.id,
        'session_id': snapshot.session_id,
        'timestamp': _format_datetime(snapshot.timestamp),
        'snapshot_type': snapshot.snapshot_type,
        'git_branch': snapshot.git_branch,
        'git_commit': snapshot.git_commit,
        'git_dirty': snapshot.git_dirty,
        'git_staged_files': snapshot.git_staged_files,
        'git_modified_files': snapshot.git_modified_files,
        'context_files': snapshot.context_files,
        'active_track_id': snapshot.active_track_id,
        'active_sprint_id': snapshot.active_sprint_id,
        'active_task_ids': snapshot.active_task_ids,
        'environment': snapshot.environment,
        'config_hash': snapshot.config_hash,
    }


# =============================================================================
# Session Commit Loading/Dumping
# =============================================================================

def _load_commit(data: Dict[str, Any], session_id: str) -> SessionCommit:
    """Load a SessionCommit from a dictionary."""
    return SessionCommit(
        session_id=session_id,
        commit_sha=data['commit_sha'],
        short_sha=data.get('short_sha', data['commit_sha'][:7]),
        timestamp=_parse_datetime(data['timestamp']),
        message=data.get('message', ''),
        author=data.get('author'),
        files_changed=data.get('files_changed', 0),
        insertions=data.get('insertions', 0),
        deletions=data.get('deletions', 0),
    )


def _dump_commit(commit: SessionCommit) -> Dict[str, Any]:
    """Dump a SessionCommit to a dictionary."""
    return {
        'commit_sha': commit.commit_sha,
        'short_sha': commit.short_sha,
        'timestamp': _format_datetime(commit.timestamp),
        'message': commit.message,
        'author': commit.author,
        'files_changed': commit.files_changed,
        'insertions': commit.insertions,
        'deletions': commit.deletions,
    }


# =============================================================================
# Session Loading/Dumping
# =============================================================================

def load_session(data: Dict[str, Any]) -> Session:
    """
    Load a Session from a dictionary (typically from YAML).

    Args:
        data: Dictionary containing session data (with 'session' wrapper or flat)

    Returns:
        Session object
    """
    # Handle wrapped format {'session': {...}}
    if 'session' in data:
        session_data = data['session']
    else:
        session_data = data

    session_id = session_data['id']

    # Load events
    events = []
    for event_data in session_data.get('events', []):
        events.append(_load_event(event_data))

    # Load decisions
    decisions = []
    for decision_data in session_data.get('decisions', []):
        decisions.append(_load_decision(decision_data))

    # Load commits
    commits = []
    for commit_data in session_data.get('commits', []):
        commits.append(_load_commit(commit_data, session_id))

    # Load context snapshot
    snapshot = None
    if session_data.get('context_snapshot'):
        snapshot = _load_snapshot(session_data['context_snapshot'])

    # Load stats
    stats = None
    if session_data.get('stats'):
        stats_data = session_data['stats']
        stats = SessionStats(
            duration_seconds=stats_data.get('duration_seconds', 0),
            events_count=stats_data.get('events_count', 0),
            decisions_count=stats_data.get('decisions_count', 0),
            commits_count=stats_data.get('commits_count', 0),
            files_modified=stats_data.get('files_modified', 0),
            tasks_worked=stats_data.get('tasks_worked', 0),
            errors_count=stats_data.get('errors_count', 0),
            token_usage=stats_data.get('token_usage'),
        )

    return Session(
        id=session_id,
        name=session_data['name'],
        status=SessionStatus(session_data.get('status', 'active')),
        created=_parse_datetime(session_data.get('created')),
        started=_parse_datetime(session_data.get('started')),
        paused=_parse_datetime(session_data.get('paused')),
        ended=_parse_datetime(session_data.get('ended')),
        roadmap_id=session_data.get('roadmap_id', ''),
        track_id=session_data.get('track_id'),
        sprint_id=session_data.get('sprint_id'),
        task_ids=session_data.get('task_ids', []),
        branch=session_data.get('branch'),
        start_commit=session_data.get('start_commit'),
        end_commit=session_data.get('end_commit'),
        commits=commits,
        goals=session_data.get('goals', []),
        summary=session_data.get('summary'),
        context_snapshot=snapshot,
        events=events,
        decisions=decisions,
        stats=stats,
        metadata=session_data.get('metadata', {}),
    )


def dump_session(session: Session) -> Dict[str, Any]:
    """
    Dump a Session to a dictionary (for YAML serialization).

    Args:
        session: Session object to dump

    Returns:
        Dictionary suitable for YAML output
    """
    session_data = {
        'id': session.id,
        'name': session.name,
        'status': session.status.value,
        'created': _format_datetime(session.created),
        'started': _format_datetime(session.started),
        'paused': _format_datetime(session.paused),
        'ended': _format_datetime(session.ended),
        'roadmap_id': session.roadmap_id,
        'track_id': session.track_id,
        'sprint_id': session.sprint_id,
        'task_ids': session.task_ids,
        'branch': session.branch,
        'start_commit': session.start_commit,
        'end_commit': session.end_commit,
        'commits': [_dump_commit(c) for c in session.commits],
        'goals': session.goals,
        'summary': session.summary,
        'context_snapshot': _dump_snapshot(session.context_snapshot) if session.context_snapshot else None,
        'events': [_dump_event(e) for e in session.events],
        'decisions': [_dump_decision(d) for d in session.decisions],
        'metadata': session.metadata,
    }

    # Add stats if present
    if session.stats:
        session_data['stats'] = {
            'duration_seconds': session.stats.duration_seconds,
            'events_count': session.stats.events_count,
            'decisions_count': session.stats.decisions_count,
            'commits_count': session.stats.commits_count,
            'files_modified': session.stats.files_modified,
            'tasks_worked': session.stats.tasks_worked,
            'errors_count': session.stats.errors_count,
            'token_usage': session.stats.token_usage,
        }

    return {'session': session_data}


# =============================================================================
# File Operations
# =============================================================================

def load_session_from_file(path: Path) -> Session:
    """
    Load a Session from a YAML file.

    Args:
        path: Path to the session YAML file

    Returns:
        Session object

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file content is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Session file not found: {path}")

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty session file: {path}")

    return load_session(data)


def save_session_to_file(session: Session, path: Path) -> None:
    """
    Save a Session to a YAML file.

    Args:
        session: Session object to save
        path: Path to save the file to
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    data = dump_session(session)

    with open(path, 'w') as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


def get_sessions_directory(roadmap_path: Path) -> Path:
    """Get the sessions directory path for a roadmap."""
    return roadmap_path / "sessions"


def list_session_files(roadmap_path: Path) -> List[Path]:
    """
    List all session YAML files in the roadmap.

    Args:
        roadmap_path: Path to .vibey/roadmap directory

    Returns:
        List of paths to session YAML files
    """
    sessions_dir = get_sessions_directory(roadmap_path)
    if not sessions_dir.exists():
        return []

    return sorted(sessions_dir.glob("*.yaml"), reverse=True)


def load_all_sessions(roadmap_path: Path) -> List[Session]:
    """
    Load all sessions from a roadmap directory.

    Args:
        roadmap_path: Path to .vibey/roadmap directory

    Returns:
        List of Session objects, sorted by created date (newest first)
    """
    sessions = []
    for path in list_session_files(roadmap_path):
        try:
            session = load_session_from_file(path)
            sessions.append(session)
        except Exception as e:
            # Log but don't fail - allow partial loading
            import logging
            logging.warning(f"Failed to load session from {path}: {e}")

    # Sort by created date, newest first
    sessions.sort(key=lambda s: s.created or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return sessions


def get_session_path(roadmap_path: Path, session_id: str) -> Path:
    """Get the path for a session file."""
    return get_sessions_directory(roadmap_path) / f"{session_id}.yaml"
