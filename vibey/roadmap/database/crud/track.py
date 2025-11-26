"""
CRUD operations for track entities.

Provides create, read, update, delete operations for tracks table.
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


def create_track(
    id: str,
    roadmap_id: str,
    name: str,
    status: str,
    created: datetime,
    blocked: bool = False,
    priority: Optional[str] = None,
    started: Optional[datetime] = None,
    completed: Optional[datetime] = None,
    estimated_duration: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> str:
    """
    Create a new track.

    Args:
        id: Unique track identifier
        roadmap_id: Parent roadmap ID
        name: Human-readable name
        status: Current status
        created: Creation timestamp
        blocked: Whether track is blocked
        priority: Priority level (critical, high, medium, low)
        started: When track started
        completed: When track completed
        estimated_duration: Estimated duration string
        metadata: Additional metadata (stored as JSON)
        conn: Database connection
        db_path: Path to database file

    Returns:
        The created track's ID

    Raises:
        sqlite3.IntegrityError: If track with ID already exists or roadmap doesn't exist
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    conn.execute(
        """
        INSERT INTO tracks (
            id, roadmap_id, name, status, blocked, priority,
            created, started, completed, estimated_duration, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id,
            roadmap_id,
            name,
            status,
            1 if blocked else 0,
            priority,
            _serialize_datetime(created),
            _serialize_datetime(started),
            _serialize_datetime(completed),
            estimated_duration,
            _serialize_json(metadata),
        ),
    )

    return id


def get_track(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a track by ID.

    Args:
        id: Track identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with track data, or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM tracks WHERE id = ?",
        (id,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "roadmap_id": row["roadmap_id"],
        "name": row["name"],
        "status": row["status"],
        "blocked": bool(row["blocked"]),
        "priority": row["priority"],
        "created": _deserialize_datetime(row["created"]),
        "started": _deserialize_datetime(row["started"]),
        "completed": _deserialize_datetime(row["completed"]),
        "estimated_duration": row["estimated_duration"],
        "metadata": _deserialize_json(row["metadata"]),
    }


def update_track(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    **kwargs,
) -> bool:
    """
    Update a track.

    Args:
        id: Track identifier
        conn: Database connection
        db_path: Path to database file
        **kwargs: Fields to update

    Returns:
        True if track was updated, False if not found

    Raises:
        ValueError: If no update fields provided or unknown field
    """
    if not kwargs:
        raise ValueError("No update fields provided")

    if conn is None:
        conn = get_connection(db_path=db_path)

    updates = []
    values = []

    for key, value in kwargs.items():
        if key in ("created", "started", "completed"):
            updates.append(f"{key} = ?")
            values.append(_serialize_datetime(value))
        elif key == "metadata":
            updates.append("metadata = ?")
            values.append(_serialize_json(value))
        elif key == "blocked":
            updates.append("blocked = ?")
            values.append(1 if value else 0)
        elif key in ("name", "roadmap_id", "status", "priority", "estimated_duration"):
            updates.append(f"{key} = ?")
            values.append(value)
        else:
            raise ValueError(f"Unknown field: {key}")

    values.append(id)

    cursor = conn.execute(
        f"UPDATE tracks SET {', '.join(updates)} WHERE id = ?",
        values,
    )

    return cursor.rowcount > 0


def delete_track(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a track.

    Note: Due to CASCADE delete, this will also delete all sprints,
    tasks, and related data.

    Args:
        id: Track identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if track was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM tracks WHERE id = ?",
        (id,),
    )

    return cursor.rowcount > 0


def list_tracks_by_roadmap(
    roadmap_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all tracks for a roadmap.

    Args:
        roadmap_id: Parent roadmap ID
        status: Filter by status
        priority: Filter by priority
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of track dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM tracks WHERE roadmap_id = ?"
    params: List[Any] = [roadmap_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY created ASC"

    rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": row["id"],
            "roadmap_id": row["roadmap_id"],
            "name": row["name"],
            "status": row["status"],
            "blocked": bool(row["blocked"]),
            "priority": row["priority"],
            "created": _deserialize_datetime(row["created"]),
            "started": _deserialize_datetime(row["started"]),
            "completed": _deserialize_datetime(row["completed"]),
            "estimated_duration": row["estimated_duration"],
            "metadata": _deserialize_json(row["metadata"]),
        }
        for row in rows
    ]


def track_exists(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if a track exists.

    Args:
        id: Track identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if track exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT 1 FROM tracks WHERE id = ?",
        (id,),
    ).fetchone()

    return row is not None


def count_tracks(
    roadmap_id: Optional[str] = None,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Count tracks, optionally filtered.

    Args:
        roadmap_id: Filter by roadmap
        status: Filter by status
        conn: Database connection
        db_path: Path to database file

    Returns:
        Number of tracks
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT COUNT(*) FROM tracks"
    params: List[Any] = []
    conditions = []

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
