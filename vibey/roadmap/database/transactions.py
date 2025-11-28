"""
Transactional mutation layer for roadmap database.

This module provides atomic transactions that write to both activity_log and
entity tables, preventing drift between audit trail and current state.

Architecture:
    CLI Command → Mutation Function → BEGIN TRANSACTION
                                           ├── INSERT activity_log (event)
                                           ├── UPDATE entity tables (state)
                                           └── Existing triggers (cascades)
                                       COMMIT (or ROLLBACK on failure)

Usage:
    from vibey.roadmap.database.transactions import complete_task, update_task_status

    # All writes are atomic - either both activity_log and entity update succeed,
    # or both are rolled back
    complete_task(task_id="my-task-001", actor="claude")
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator

from .connection import get_connection


@contextmanager
def atomic_mutation(
    conn: Optional[sqlite3.Connection] = None,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for atomic activity_log + entity writes.

    Ensures that activity_log entries and entity table updates are committed
    together or rolled back together, preventing drift.

    Args:
        conn: Optional existing connection. If None, gets default connection.

    Yields:
        Database connection with active transaction

    Raises:
        Exception: Any exception during mutation causes rollback

    Example:
        with atomic_mutation() as conn:
            # Log the event
            conn.execute('''
                INSERT INTO activity_log (roadmap_id, event_type, ...)
                VALUES (?, ?, ...)
            ''', (...))

            # Update entity
            conn.execute('''
                UPDATE tasks SET status = ? WHERE id = ?
            ''', ('completed', task_id))

            # Triggers fire within this transaction
            # If anything fails, everything rolls back
    """
    if conn is None:
        conn = get_connection()

    # Start explicit transaction
    conn.execute("BEGIN TRANSACTION")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _now_iso() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _get_task_state(conn: sqlite3.Connection, task_id: str) -> Optional[Dict[str, Any]]:
    """Get current task state as JSON-serializable dict."""
    row = conn.execute(
        "SELECT id, status, blocked, started, completed FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "status": row[1],
        "blocked": bool(row[2]),
        "started": row[3],
        "completed": row[4],
    }


def _get_sprint_state(conn: sqlite3.Connection, sprint_id: str) -> Optional[Dict[str, Any]]:
    """Get current sprint state as JSON-serializable dict."""
    row = conn.execute(
        "SELECT id, status, blocked, started, completed FROM sprints WHERE id = ?",
        (sprint_id,)
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "status": row[1],
        "blocked": bool(row[2]),
        "started": row[3],
        "completed": row[4],
    }


def _get_track_state(conn: sqlite3.Connection, track_id: str) -> Optional[Dict[str, Any]]:
    """Get current track state as JSON-serializable dict."""
    row = conn.execute(
        "SELECT id, status, blocked, started, completed FROM tracks WHERE id = ?",
        (track_id,)
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "status": row[1],
        "blocked": bool(row[2]),
        "started": row[3],
        "completed": row[4],
    }


def _log_activity(
    conn: sqlite3.Connection,
    roadmap_id: str,
    event_type: str,
    event_description: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor: str = "system",
    old_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Insert activity log entry within current transaction.

    Returns:
        ID of inserted activity log entry
    """
    cursor = conn.execute("""
        INSERT INTO activity_log (
            roadmap_id, event_type, event_description, occurred_at,
            entity_type, entity_id, actor, old_state, new_state, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        roadmap_id,
        event_type,
        event_description,
        _now_iso(),
        entity_type,
        entity_id,
        actor,
        json.dumps(old_state) if old_state else None,
        json.dumps(new_state) if new_state else None,
        json.dumps(metadata) if metadata else None,
    ))
    return cursor.lastrowid


# =============================================================================
# Task Mutations
# =============================================================================

def update_task_status(
    task_id: str,
    new_status: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Update task status with atomic activity log write.

    Args:
        task_id: Task ID to update
        new_status: New status value (not_started, in_progress, completed, etc.)
        actor: Who/what is making the change
        conn: Optional existing connection

    Returns:
        True if task was found and updated

    Raises:
        ValueError: If task not found
    """
    with atomic_mutation(conn) as txn:
        # Get current state for audit
        old_state = _get_task_state(txn, task_id)
        if old_state is None:
            raise ValueError(f"Task '{task_id}' not found")

        # Get roadmap_id for activity log
        row = txn.execute(
            "SELECT roadmap_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        roadmap_id = row[0] if row else "unknown"

        # Update task
        now = _now_iso()
        started = now if new_status == "in_progress" and not old_state.get("started") else None
        completed = now if new_status == "completed" else None

        if started:
            txn.execute(
                "UPDATE tasks SET status = ?, started = ? WHERE id = ?",
                (new_status, started, task_id)
            )
        elif completed:
            txn.execute(
                "UPDATE tasks SET status = ?, completed = ? WHERE id = ?",
                (new_status, completed, task_id)
            )
        else:
            txn.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (new_status, task_id)
            )

        # Get new state for audit
        new_state = _get_task_state(txn, task_id)

        # Log activity
        _log_activity(
            txn,
            roadmap_id=roadmap_id,
            event_type="task_status_change",
            event_description=f"Task {task_id} status changed from {old_state['status']} to {new_status}",
            entity_type="task",
            entity_id=task_id,
            actor=actor,
            old_state=old_state,
            new_state=new_state,
        )

        return True


def complete_task(
    task_id: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Mark task as completed with atomic activity log write.

    Args:
        task_id: Task ID to complete
        actor: Who/what is completing the task
        conn: Optional existing connection

    Returns:
        True if task was completed
    """
    return update_task_status(task_id, "completed", actor, conn)


def start_task(
    task_id: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Mark task as in_progress with atomic activity log write.

    Args:
        task_id: Task ID to start
        actor: Who/what is starting the task
        conn: Optional existing connection

    Returns:
        True if task was started
    """
    return update_task_status(task_id, "in_progress", actor, conn)


# =============================================================================
# Sprint Mutations
# =============================================================================

def update_sprint_status(
    sprint_id: str,
    new_status: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Update sprint status with atomic activity log write.

    Args:
        sprint_id: Sprint ID to update
        new_status: New status value
        actor: Who/what is making the change
        conn: Optional existing connection

    Returns:
        True if sprint was found and updated

    Raises:
        ValueError: If sprint not found
    """
    with atomic_mutation(conn) as txn:
        # Get current state for audit
        old_state = _get_sprint_state(txn, sprint_id)
        if old_state is None:
            raise ValueError(f"Sprint '{sprint_id}' not found")

        # Get roadmap_id for activity log
        row = txn.execute(
            "SELECT roadmap_id FROM sprints WHERE id = ?", (sprint_id,)
        ).fetchone()
        roadmap_id = row[0] if row else "unknown"

        # Update sprint
        now = _now_iso()
        started = now if new_status == "in_progress" and not old_state.get("started") else None
        completed = now if new_status == "completed" else None

        if started:
            txn.execute(
                "UPDATE sprints SET status = ?, started = ? WHERE id = ?",
                (new_status, started, sprint_id)
            )
        elif completed:
            txn.execute(
                "UPDATE sprints SET status = ?, completed = ? WHERE id = ?",
                (new_status, completed, sprint_id)
            )
        else:
            txn.execute(
                "UPDATE sprints SET status = ? WHERE id = ?",
                (new_status, sprint_id)
            )

        # Get new state for audit
        new_state = _get_sprint_state(txn, sprint_id)

        # Log activity
        _log_activity(
            txn,
            roadmap_id=roadmap_id,
            event_type="sprint_status_change",
            event_description=f"Sprint {sprint_id} status changed from {old_state['status']} to {new_status}",
            entity_type="sprint",
            entity_id=sprint_id,
            actor=actor,
            old_state=old_state,
            new_state=new_state,
        )

        return True


def complete_sprint(
    sprint_id: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Mark sprint as completed with atomic activity log write."""
    return update_sprint_status(sprint_id, "completed", actor, conn)


def start_sprint(
    sprint_id: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Mark sprint as in_progress with atomic activity log write."""
    return update_sprint_status(sprint_id, "in_progress", actor, conn)


# =============================================================================
# Track Mutations
# =============================================================================

def update_track_status(
    track_id: str,
    new_status: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Update track status with atomic activity log write.

    Args:
        track_id: Track ID to update
        new_status: New status value
        actor: Who/what is making the change
        conn: Optional existing connection

    Returns:
        True if track was found and updated

    Raises:
        ValueError: If track not found
    """
    with atomic_mutation(conn) as txn:
        # Get current state for audit
        old_state = _get_track_state(txn, track_id)
        if old_state is None:
            raise ValueError(f"Track '{track_id}' not found")

        # Get roadmap_id for activity log
        row = txn.execute(
            "SELECT roadmap_id FROM tracks WHERE id = ?", (track_id,)
        ).fetchone()
        roadmap_id = row[0] if row else "unknown"

        # Update track
        now = _now_iso()
        started = now if new_status == "in_progress" and not old_state.get("started") else None
        completed = now if new_status == "completed" else None

        if started:
            txn.execute(
                "UPDATE tracks SET status = ?, started = ? WHERE id = ?",
                (new_status, started, track_id)
            )
        elif completed:
            txn.execute(
                "UPDATE tracks SET status = ?, completed = ? WHERE id = ?",
                (new_status, completed, track_id)
            )
        else:
            txn.execute(
                "UPDATE tracks SET status = ? WHERE id = ?",
                (new_status, track_id)
            )

        # Get new state for audit
        new_state = _get_track_state(txn, track_id)

        # Log activity
        _log_activity(
            txn,
            roadmap_id=roadmap_id,
            event_type="track_status_change",
            event_description=f"Track {track_id} status changed from {old_state['status']} to {new_status}",
            entity_type="track",
            entity_id=track_id,
            actor=actor,
            old_state=old_state,
            new_state=new_state,
        )

        return True


def complete_track(
    track_id: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Mark track as completed with atomic activity log write."""
    return update_track_status(track_id, "completed", actor, conn)


def start_track(
    track_id: str,
    actor: str = "system",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Mark track as in_progress with atomic activity log write."""
    return update_track_status(track_id, "in_progress", actor, conn)
