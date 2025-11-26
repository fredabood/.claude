"""
CRUD operations for sprint entities.

Provides create, read, update, delete operations for sprints table.
Complex nested objects (metadata) are stored as JSON.
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


def create_sprint(
    id: str,
    track_id: str,
    roadmap_id: str,
    name: str,
    status: str,
    created: datetime,
    blocked: bool = False,
    blocked_reason: Optional[str] = None,
    started: Optional[datetime] = None,
    completion_gate_check_at: Optional[datetime] = None,
    completed: Optional[datetime] = None,
    production_gate_check_at: Optional[datetime] = None,
    production_ready_at: Optional[datetime] = None,
    deployed_at: Optional[datetime] = None,
    plan_file: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> str:
    """
    Create a new sprint.

    Args:
        id: Unique sprint identifier (must be track-scoped, e.g., "track-1")
        track_id: Parent track ID
        roadmap_id: Parent roadmap ID
        name: Human-readable name
        status: Current status
        created: Creation timestamp
        blocked: Whether sprint is blocked
        blocked_reason: Reason for blocking
        started: When sprint started
        completion_gate_check_at: When completion gate check started
        completed: When sprint completed
        production_gate_check_at: When production gate check started
        production_ready_at: When sprint became production ready
        deployed_at: When sprint was deployed
        plan_file: Path to sprint plan file
        metadata: Additional metadata (stored as JSON)
        conn: Database connection
        db_path: Path to database file

    Returns:
        The created sprint's ID

    Raises:
        sqlite3.IntegrityError: If sprint with ID already exists or track doesn't exist
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    conn.execute(
        """
        INSERT INTO sprints (
            id, track_id, roadmap_id, name, status, blocked, blocked_reason,
            created, started, completion_gate_check_at, completed,
            production_gate_check_at, production_ready_at, deployed_at,
            plan_file, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id,
            track_id,
            roadmap_id,
            name,
            status,
            1 if blocked else 0,
            blocked_reason,
            _serialize_datetime(created),
            _serialize_datetime(started),
            _serialize_datetime(completion_gate_check_at),
            _serialize_datetime(completed),
            _serialize_datetime(production_gate_check_at),
            _serialize_datetime(production_ready_at),
            _serialize_datetime(deployed_at),
            plan_file,
            _serialize_json(metadata),
        ),
    )

    return id


def get_sprint(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a sprint by ID.

    Args:
        id: Sprint identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with sprint data, or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM sprints WHERE id = ?",
        (id,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "track_id": row["track_id"],
        "roadmap_id": row["roadmap_id"],
        "name": row["name"],
        "status": row["status"],
        "blocked": bool(row["blocked"]),
        "blocked_reason": row["blocked_reason"],
        "created": _deserialize_datetime(row["created"]),
        "started": _deserialize_datetime(row["started"]),
        "completion_gate_check_at": _deserialize_datetime(row["completion_gate_check_at"]),
        "completed": _deserialize_datetime(row["completed"]),
        "production_gate_check_at": _deserialize_datetime(row["production_gate_check_at"]),
        "production_ready_at": _deserialize_datetime(row["production_ready_at"]),
        "deployed_at": _deserialize_datetime(row["deployed_at"]),
        "plan_file": row["plan_file"],
        "metadata": _deserialize_json(row["metadata"]),
    }


def update_sprint(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    **kwargs,
) -> bool:
    """
    Update a sprint.

    Args:
        id: Sprint identifier
        conn: Database connection
        db_path: Path to database file
        **kwargs: Fields to update

    Returns:
        True if sprint was updated, False if not found

    Raises:
        ValueError: If no update fields provided or unknown field
    """
    if not kwargs:
        raise ValueError("No update fields provided")

    if conn is None:
        conn = get_connection(db_path=db_path)

    updates = []
    values = []

    datetime_fields = (
        "created", "started", "completion_gate_check_at", "completed",
        "production_gate_check_at", "production_ready_at", "deployed_at"
    )

    for key, value in kwargs.items():
        if key in datetime_fields:
            updates.append(f"{key} = ?")
            values.append(_serialize_datetime(value))
        elif key == "metadata":
            updates.append("metadata = ?")
            values.append(_serialize_json(value))
        elif key == "blocked":
            updates.append("blocked = ?")
            values.append(1 if value else 0)
        elif key in ("name", "track_id", "roadmap_id", "status", "blocked_reason", "plan_file"):
            updates.append(f"{key} = ?")
            values.append(value)
        else:
            raise ValueError(f"Unknown field: {key}")

    values.append(id)

    cursor = conn.execute(
        f"UPDATE sprints SET {', '.join(updates)} WHERE id = ?",
        values,
    )

    return cursor.rowcount > 0


def delete_sprint(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a sprint.

    Note: Due to CASCADE delete, this will also delete all tasks
    and related data.

    Args:
        id: Sprint identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if sprint was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM sprints WHERE id = ?",
        (id,),
    )

    return cursor.rowcount > 0


def list_sprints_by_track(
    track_id: str,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all sprints for a track.

    Args:
        track_id: Parent track ID
        status: Filter by status
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of sprint dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM sprints WHERE track_id = ?"
    params: List[Any] = [track_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created ASC"

    rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": row["id"],
            "track_id": row["track_id"],
            "roadmap_id": row["roadmap_id"],
            "name": row["name"],
            "status": row["status"],
            "blocked": bool(row["blocked"]),
            "blocked_reason": row["blocked_reason"],
            "created": _deserialize_datetime(row["created"]),
            "started": _deserialize_datetime(row["started"]),
            "completion_gate_check_at": _deserialize_datetime(row["completion_gate_check_at"]),
            "completed": _deserialize_datetime(row["completed"]),
            "production_gate_check_at": _deserialize_datetime(row["production_gate_check_at"]),
            "production_ready_at": _deserialize_datetime(row["production_ready_at"]),
            "deployed_at": _deserialize_datetime(row["deployed_at"]),
            "plan_file": row["plan_file"],
            "metadata": _deserialize_json(row["metadata"]),
        }
        for row in rows
    ]


def list_sprints_by_roadmap(
    roadmap_id: str,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all sprints for a roadmap.

    Args:
        roadmap_id: Parent roadmap ID
        status: Filter by status
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of sprint dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM sprints WHERE roadmap_id = ?"
    params: List[Any] = [roadmap_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY track_id, created ASC"

    rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": row["id"],
            "track_id": row["track_id"],
            "roadmap_id": row["roadmap_id"],
            "name": row["name"],
            "status": row["status"],
            "blocked": bool(row["blocked"]),
            "blocked_reason": row["blocked_reason"],
            "created": _deserialize_datetime(row["created"]),
            "started": _deserialize_datetime(row["started"]),
            "completion_gate_check_at": _deserialize_datetime(row["completion_gate_check_at"]),
            "completed": _deserialize_datetime(row["completed"]),
            "production_gate_check_at": _deserialize_datetime(row["production_gate_check_at"]),
            "production_ready_at": _deserialize_datetime(row["production_ready_at"]),
            "deployed_at": _deserialize_datetime(row["deployed_at"]),
            "plan_file": row["plan_file"],
            "metadata": _deserialize_json(row["metadata"]),
        }
        for row in rows
    ]


def sprint_exists(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if a sprint exists.

    Args:
        id: Sprint identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if sprint exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT 1 FROM sprints WHERE id = ?",
        (id,),
    ).fetchone()

    return row is not None


def count_sprints(
    track_id: Optional[str] = None,
    roadmap_id: Optional[str] = None,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Count sprints, optionally filtered.

    Args:
        track_id: Filter by track
        roadmap_id: Filter by roadmap
        status: Filter by status
        conn: Database connection
        db_path: Path to database file

    Returns:
        Number of sprints
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT COUNT(*) FROM sprints"
    params: List[Any] = []
    conditions = []

    if track_id:
        conditions.append("track_id = ?")
        params.append(track_id)

    if roadmap_id:
        conditions.append("roadmap_id = ?")
        params.append(roadmap_id)

    if status:
        conditions.append("status = ?")
        params.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    row = conn.execute(query, params).fetchone()
    return row[0]
