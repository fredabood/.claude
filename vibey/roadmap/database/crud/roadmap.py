"""
CRUD operations for roadmap entities.

Provides create, read, update, delete operations for roadmaps table.
Complex nested objects (progress, metadata, version_strategy) are stored as JSON.
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


def create_roadmap(
    id: str,
    name: str,
    version: str,
    status: str,
    created: datetime,
    blocked: bool = False,
    started: Optional[datetime] = None,
    target_completion: Optional[datetime] = None,
    completed: Optional[datetime] = None,
    deployed: Optional[datetime] = None,
    version_strategy: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> str:
    """
    Create a new roadmap.

    Args:
        id: Unique roadmap identifier
        name: Human-readable name
        version: Semantic version string
        status: Current status (not_started, in_progress, completed, etc.)
        created: Creation timestamp
        blocked: Whether roadmap is blocked
        started: When roadmap started
        target_completion: Target completion date
        completed: When roadmap completed
        deployed: When roadmap deployed
        version_strategy: Version bump strategy (stored as JSON)
        metadata: Additional metadata (stored as JSON)
        conn: Database connection
        db_path: Path to database file

    Returns:
        The created roadmap's ID

    Raises:
        sqlite3.IntegrityError: If roadmap with ID already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    conn.execute(
        """
        INSERT INTO roadmaps (
            id, name, version, status, blocked, created, started,
            target_completion, completed, deployed, version_strategy, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id,
            name,
            version,
            status,
            1 if blocked else 0,
            _serialize_datetime(created),
            _serialize_datetime(started),
            _serialize_datetime(target_completion),
            _serialize_datetime(completed),
            _serialize_datetime(deployed),
            _serialize_json(version_strategy),
            _serialize_json(metadata),
        ),
    )

    return id


def get_roadmap(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a roadmap by ID.

    Args:
        id: Roadmap identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with roadmap data, or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM roadmaps WHERE id = ?",
        (id,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "version": row["version"],
        "status": row["status"],
        "blocked": bool(row["blocked"]),
        "created": _deserialize_datetime(row["created"]),
        "started": _deserialize_datetime(row["started"]),
        "target_completion": _deserialize_datetime(row["target_completion"]),
        "completed": _deserialize_datetime(row["completed"]),
        "deployed": _deserialize_datetime(row["deployed"]),
        "version_strategy": _deserialize_json(row["version_strategy"]),
        "metadata": _deserialize_json(row["metadata"]),
    }


def update_roadmap(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    **kwargs,
) -> bool:
    """
    Update a roadmap.

    Args:
        id: Roadmap identifier
        conn: Database connection
        db_path: Path to database file
        **kwargs: Fields to update (name, version, status, blocked, etc.)

    Returns:
        True if roadmap was updated, False if not found

    Raises:
        ValueError: If no update fields provided
    """
    if not kwargs:
        raise ValueError("No update fields provided")

    if conn is None:
        conn = get_connection(db_path=db_path)

    # Build update query
    updates = []
    values = []

    for key, value in kwargs.items():
        if key in ("created", "started", "target_completion", "completed", "deployed"):
            updates.append(f"{key} = ?")
            values.append(_serialize_datetime(value))
        elif key in ("version_strategy", "metadata"):
            updates.append(f"{key} = ?")
            values.append(_serialize_json(value))
        elif key == "blocked":
            updates.append("blocked = ?")
            values.append(1 if value else 0)
        elif key in ("name", "version", "status"):
            updates.append(f"{key} = ?")
            values.append(value)
        else:
            raise ValueError(f"Unknown field: {key}")

    values.append(id)

    cursor = conn.execute(
        f"UPDATE roadmaps SET {', '.join(updates)} WHERE id = ?",
        values,
    )

    return cursor.rowcount > 0


def delete_roadmap(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a roadmap.

    Note: Due to CASCADE delete, this will also delete all tracks,
    sprints, tasks, and related data.

    Args:
        id: Roadmap identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if roadmap was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM roadmaps WHERE id = ?",
        (id,),
    )

    return cursor.rowcount > 0


def list_roadmaps(
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List all roadmaps, optionally filtered by status.

    Args:
        status: Filter by status
        limit: Maximum number of results
        offset: Number of results to skip
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of roadmap dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM roadmaps"
    params: List[Any] = []

    if status:
        query += " WHERE status = ?"
        params.append(status)

    query += " ORDER BY created DESC"

    if limit:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "version": row["version"],
            "status": row["status"],
            "blocked": bool(row["blocked"]),
            "created": _deserialize_datetime(row["created"]),
            "started": _deserialize_datetime(row["started"]),
            "target_completion": _deserialize_datetime(row["target_completion"]),
            "completed": _deserialize_datetime(row["completed"]),
            "deployed": _deserialize_datetime(row["deployed"]),
            "version_strategy": _deserialize_json(row["version_strategy"]),
            "metadata": _deserialize_json(row["metadata"]),
        }
        for row in rows
    ]


def roadmap_exists(
    id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if a roadmap exists.

    Args:
        id: Roadmap identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if roadmap exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT 1 FROM roadmaps WHERE id = ?",
        (id,),
    ).fetchone()

    return row is not None


def count_roadmaps(
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Count roadmaps, optionally filtered by status.

    Args:
        status: Filter by status
        conn: Database connection
        db_path: Path to database file

    Returns:
        Number of roadmaps
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if status:
        row = conn.execute(
            "SELECT COUNT(*) FROM roadmaps WHERE status = ?",
            (status,),
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) FROM roadmaps").fetchone()

    return row[0]
