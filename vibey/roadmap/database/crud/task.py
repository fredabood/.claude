"""
CRUD operations for task entities.

Provides create, read, update, delete operations for tasks table.
Complex nested objects (gate_info, audit_results, metadata) are stored as JSON.
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..connection import get_connection


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat()


def _deserialize_datetime(s: Optional[str]) -> Optional[datetime]:
    """Deserialize ISO 8601 string to datetime."""
    if s is None:
        return None
    return datetime.fromisoformat(s)


def _serialize_json(obj: Any) -> Optional[str]:
    """Serialize object to JSON string."""
    if obj is None:
        return None
    return json.dumps(obj, default=str)


def _deserialize_json(s: Optional[str]) -> Any:
    """Deserialize JSON string to object."""
    if s is None:
        return None
    return json.loads(s)


def create_task(
    id: str,
    sprint_id: str,
    track_id: str,
    roadmap_id: str,
    task_type: str,
    title: str,
    status: str,
    created: datetime,
    description: Optional[str] = None,
    blocked: bool = False,
    assigned_agent: Optional[str] = None,
    priority: Optional[str] = None,
    phase_label: Optional[str] = None,
    estimated_tokens: Optional[int] = None,
    actual_tokens: Optional[int] = None,
    complexity: Optional[str] = None,
    gate_info: Optional[Dict[str, Any]] = None,
    audit_results: Optional[Dict[str, Any]] = None,
    started: Optional[datetime] = None,
    completed: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> str:
    """
    Create a new task.

    Args:
        id: Unique task identifier (must be sprint-scoped, e.g., "sprint-1-task-001")
        sprint_id: Parent sprint ID
        track_id: Parent track ID
        roadmap_id: Parent roadmap ID
        task_type: Task type (development, completion_gate, production_gate)
        title: Task title
        status: Current status
        created: Creation timestamp
        description: Task description
        blocked: Whether task is blocked
        assigned_agent: Assigned agent name
        priority: Priority level
        phase_label: Phase label
        estimated_tokens: Estimated token count
        actual_tokens: Actual token count
        complexity: Complexity rating
        gate_info: Gate information for quality gate tasks (stored as JSON)
        audit_results: Audit results for gate tasks (stored as JSON)
        started: When task started
        completed: When task completed
        metadata: Additional metadata (stored as JSON)
        conn: Database connection
        db_path: Path to database file

    Returns:
        The created task's ID

    Raises:
        sqlite3.IntegrityError: If task with ID already exists or sprint doesn't exist
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    conn.execute(
        """
        INSERT INTO tasks (
            id, sprint_id, track_id, roadmap_id, task_type, title, description,
            status, blocked, created, started, completed,
            assigned_agent, priority, phase_label,
            estimated_tokens, actual_tokens, complexity,
            gate_info, audit_results, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id,
            sprint_id,
            track_id,
            roadmap_id,
            task_type,
            title,
            description,
            status,
            1 if blocked else 0,
            _serialize_datetime(created),
            _serialize_datetime(started),
            _serialize_datetime(completed),
            assigned_agent,
            priority,
            phase_label,
            estimated_tokens,
            actual_tokens,
            complexity,
            _serialize_json(gate_info),
            _serialize_json(audit_results),
            _serialize_json(metadata),
        ),
    )

    return id


def get_task(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a task by ID.

    Args:
        id: Task identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with task data, or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (id,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "sprint_id": row["sprint_id"],
        "track_id": row["track_id"],
        "roadmap_id": row["roadmap_id"],
        "task_type": row["task_type"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "blocked": bool(row["blocked"]),
        "created": _deserialize_datetime(row["created"]),
        "started": _deserialize_datetime(row["started"]),
        "completed": _deserialize_datetime(row["completed"]),
        "assigned_agent": row["assigned_agent"],
        "priority": row["priority"],
        "phase_label": row["phase_label"],
        "estimated_tokens": row["estimated_tokens"],
        "actual_tokens": row["actual_tokens"],
        "complexity": row["complexity"],
        "gate_info": _deserialize_json(row["gate_info"]),
        "audit_results": _deserialize_json(row["audit_results"]),
        "metadata": _deserialize_json(row["metadata"]),
    }


def update_task(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    **kwargs,
) -> bool:
    """
    Update a task.

    Args:
        id: Task identifier
        conn: Database connection
        db_path: Path to database file
        **kwargs: Fields to update

    Returns:
        True if task was updated, False if not found

    Raises:
        ValueError: If no update fields provided or unknown field
    """
    if not kwargs:
        raise ValueError("No update fields provided")

    if conn is None:
        conn = get_connection(db_path=db_path)

    updates = []
    values = []

    datetime_fields = ("created", "started", "completed")
    json_fields = ("gate_info", "audit_results", "metadata")
    string_fields = (
        "sprint_id", "track_id", "roadmap_id", "task_type", "title",
        "description", "status", "assigned_agent", "priority",
        "phase_label", "complexity"
    )
    int_fields = ("estimated_tokens", "actual_tokens")

    for key, value in kwargs.items():
        if key in datetime_fields:
            updates.append(f"{key} = ?")
            values.append(_serialize_datetime(value))
        elif key in json_fields:
            updates.append(f"{key} = ?")
            values.append(_serialize_json(value))
        elif key == "blocked":
            updates.append("blocked = ?")
            values.append(1 if value else 0)
        elif key in string_fields:
            updates.append(f"{key} = ?")
            values.append(value)
        elif key in int_fields:
            updates.append(f"{key} = ?")
            values.append(value)
        else:
            raise ValueError(f"Unknown field: {key}")

    values.append(id)

    cursor = conn.execute(
        f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
        values,
    )

    return cursor.rowcount > 0


def delete_task(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a task.

    Args:
        id: Task identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if task was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (id,),
    )

    return cursor.rowcount > 0


def list_tasks_by_sprint(
    sprint_id: str,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all tasks for a sprint.

    Args:
        sprint_id: Parent sprint ID
        status: Filter by status
        task_type: Filter by task type
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of task dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM tasks WHERE sprint_id = ?"
    params: List[Any] = [sprint_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    if task_type:
        query += " AND task_type = ?"
        params.append(task_type)

    query += " ORDER BY created ASC"

    rows = conn.execute(query, params).fetchall()

    return [_row_to_dict(row) for row in rows]


def list_tasks_by_track(
    track_id: str,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all tasks for a track.

    Args:
        track_id: Parent track ID
        status: Filter by status
        task_type: Filter by task type
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of task dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM tasks WHERE track_id = ?"
    params: List[Any] = [track_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    if task_type:
        query += " AND task_type = ?"
        params.append(task_type)

    query += " ORDER BY sprint_id, created ASC"

    rows = conn.execute(query, params).fetchall()

    return [_row_to_dict(row) for row in rows]


def list_tasks_by_roadmap(
    roadmap_id: str,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all tasks for a roadmap.

    Args:
        roadmap_id: Parent roadmap ID
        status: Filter by status
        task_type: Filter by task type
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of task dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM tasks WHERE roadmap_id = ?"
    params: List[Any] = [roadmap_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    if task_type:
        query += " AND task_type = ?"
        params.append(task_type)

    query += " ORDER BY track_id, sprint_id, created ASC"

    rows = conn.execute(query, params).fetchall()

    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    return {
        "id": row["id"],
        "sprint_id": row["sprint_id"],
        "track_id": row["track_id"],
        "roadmap_id": row["roadmap_id"],
        "task_type": row["task_type"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "blocked": bool(row["blocked"]),
        "created": _deserialize_datetime(row["created"]),
        "started": _deserialize_datetime(row["started"]),
        "completed": _deserialize_datetime(row["completed"]),
        "assigned_agent": row["assigned_agent"],
        "priority": row["priority"],
        "phase_label": row["phase_label"],
        "estimated_tokens": row["estimated_tokens"],
        "actual_tokens": row["actual_tokens"],
        "complexity": row["complexity"],
        "gate_info": _deserialize_json(row["gate_info"]),
        "audit_results": _deserialize_json(row["audit_results"]),
        "metadata": _deserialize_json(row["metadata"]),
    }


def task_exists(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if a task exists.

    Args:
        id: Task identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if task exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT 1 FROM tasks WHERE id = ?",
        (id,),
    ).fetchone()

    return row is not None


def count_tasks(
    sprint_id: Optional[str] = None,
    track_id: Optional[str] = None,
    roadmap_id: Optional[str] = None,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Count tasks, optionally filtered.

    Args:
        sprint_id: Filter by sprint
        track_id: Filter by track
        roadmap_id: Filter by roadmap
        status: Filter by status
        task_type: Filter by task type
        conn: Database connection
        db_path: Path to database file

    Returns:
        Number of tasks
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT COUNT(*) FROM tasks"
    params: List[Any] = []
    conditions = []

    if sprint_id:
        conditions.append("sprint_id = ?")
        params.append(sprint_id)

    if track_id:
        conditions.append("track_id = ?")
        params.append(track_id)

    if roadmap_id:
        conditions.append("roadmap_id = ?")
        params.append(roadmap_id)

    if status:
        conditions.append("status = ?")
        params.append(status)

    if task_type:
        conditions.append("task_type = ?")
        params.append(task_type)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    row = conn.execute(query, params).fetchone()
    return row[0]


def get_blocked_tasks(
    roadmap_id: Optional[str] = None,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all blocked tasks, optionally filtered by hierarchy.

    Args:
        roadmap_id: Filter by roadmap
        track_id: Filter by track
        sprint_id: Filter by sprint
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of blocked task dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM tasks WHERE blocked = 1"
    params: List[Any] = []

    if roadmap_id:
        query += " AND roadmap_id = ?"
        params.append(roadmap_id)

    if track_id:
        query += " AND track_id = ?"
        params.append(track_id)

    if sprint_id:
        query += " AND sprint_id = ?"
        params.append(sprint_id)

    query += " ORDER BY created ASC"

    rows = conn.execute(query, params).fetchall()

    return [_row_to_dict(row) for row in rows]
