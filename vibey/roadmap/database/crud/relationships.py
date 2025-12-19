"""
CRUD operations for relationship and junction tables.

Provides operations for:
- Blocking relationships (entity_blocks, entity_blocked_by)
- Soft dependencies (entity_depends_on)
- Junction tables (entity_deliverables, entity_commits)
- Quality gates
- Dependency chain queries with recursive CTEs
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
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


# =============================================================================
# BLOCKING RELATIONSHIPS (entity_blocks, entity_blocked_by)
# =============================================================================

def add_blocker(
    blocker_type: str,
    blocker_id: str,
    blocked_type: str,
    blocked_id: str,
    reason: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Add a blocking relationship.

    Creates entries in both entity_blocks and entity_blocked_by for
    bidirectional query efficiency.

    Args:
        blocker_type: Type of blocking entity (track, sprint, task)
        blocker_id: ID of blocking entity
        blocked_type: Type of blocked entity (track, sprint, task)
        blocked_id: ID of blocked entity
        reason: Optional reason for blocking
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created entity_blocks row

    Raises:
        sqlite3.IntegrityError: If relationship already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    # Insert into entity_blocks
    cursor = conn.execute(
        """
        INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (blocker_type, blocker_id, blocked_type, blocked_id, reason),
    )
    blocks_id = cursor.lastrowid

    # Insert inverse into entity_blocked_by
    conn.execute(
        """
        INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (blocked_type, blocked_id, blocker_type, blocker_id, reason),
    )

    return blocks_id


def remove_blocker(
    blocker_type: str,
    blocker_id: str,
    blocked_type: str,
    blocked_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Remove a blocking relationship.

    Removes from both entity_blocks and entity_blocked_by.

    Args:
        blocker_type: Type of blocking entity
        blocker_id: ID of blocking entity
        blocked_type: Type of blocked entity
        blocked_id: ID of blocked entity
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if relationship was removed, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    # Remove from entity_blocks
    cursor = conn.execute(
        """
        DELETE FROM entity_blocks
        WHERE blocker_type = ? AND blocker_id = ? AND blocked_type = ? AND blocked_id = ?
        """,
        (blocker_type, blocker_id, blocked_type, blocked_id),
    )

    if cursor.rowcount == 0:
        return False

    # Remove from entity_blocked_by
    conn.execute(
        """
        DELETE FROM entity_blocked_by
        WHERE blocked_type = ? AND blocked_id = ? AND blocker_type = ? AND blocker_id = ?
        """,
        (blocked_type, blocked_id, blocker_type, blocker_id),
    )

    return True


def get_blockers(
    blocked_type: str,
    blocked_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all entities that block a given entity.

    Args:
        blocked_type: Type of blocked entity
        blocked_id: ID of blocked entity
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of blocker dictionaries with blocker_type, blocker_id, reason
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT blocker_type, blocker_id, reason
        FROM entity_blocked_by
        WHERE blocked_type = ? AND blocked_id = ?
        """,
        (blocked_type, blocked_id),
    ).fetchall()

    return [
        {
            "blocker_type": row["blocker_type"],
            "blocker_id": row["blocker_id"],
            "reason": row["reason"],
        }
        for row in rows
    ]


def get_blocked_by(
    blocker_type: str,
    blocker_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all entities blocked by a given entity.

    Args:
        blocker_type: Type of blocking entity
        blocker_id: ID of blocking entity
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of blocked entity dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT blocked_type, blocked_id, reason
        FROM entity_blocks
        WHERE blocker_type = ? AND blocker_id = ?
        """,
        (blocker_type, blocker_id),
    ).fetchall()

    return [
        {
            "blocked_type": row["blocked_type"],
            "blocked_id": row["blocked_id"],
            "reason": row["reason"],
        }
        for row in rows
    ]


def is_blocked(
    entity_type: str,
    entity_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if an entity is blocked by any other entity.

    Args:
        entity_type: Type of entity to check
        entity_id: ID of entity to check
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if entity has blockers
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        """
        SELECT 1 FROM entity_blocked_by
        WHERE blocked_type = ? AND blocked_id = ?
        LIMIT 1
        """,
        (entity_type, entity_id),
    ).fetchone()

    return row is not None


# =============================================================================
# SOFT DEPENDENCIES (entity_depends_on)
# =============================================================================

def add_dependency(
    dependent_type: str,
    dependent_id: str,
    dependency_type: str,
    dependency_id: str,
    reason: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Add a soft dependency relationship.

    Soft dependencies are ordering hints, not blocking constraints.

    Args:
        dependent_type: Type of dependent entity
        dependent_id: ID of dependent entity
        dependency_type: Type of dependency
        dependency_id: ID of dependency
        reason: Optional reason for dependency
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created row

    Raises:
        sqlite3.IntegrityError: If relationship already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        INSERT INTO entity_depends_on (dependent_type, dependent_id, dependency_type, dependency_id, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (dependent_type, dependent_id, dependency_type, dependency_id, reason),
    )

    return cursor.lastrowid


def remove_dependency(
    dependent_type: str,
    dependent_id: str,
    dependency_type: str,
    dependency_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Remove a soft dependency relationship.

    Args:
        dependent_type: Type of dependent entity
        dependent_id: ID of dependent entity
        dependency_type: Type of dependency
        dependency_id: ID of dependency
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if relationship was removed, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        DELETE FROM entity_depends_on
        WHERE dependent_type = ? AND dependent_id = ? AND dependency_type = ? AND dependency_id = ?
        """,
        (dependent_type, dependent_id, dependency_type, dependency_id),
    )

    return cursor.rowcount > 0


def get_dependencies(
    dependent_type: str,
    dependent_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all dependencies for an entity.

    Args:
        dependent_type: Type of dependent entity
        dependent_id: ID of dependent entity
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of dependency dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT dependency_type, dependency_id, reason
        FROM entity_depends_on
        WHERE dependent_type = ? AND dependent_id = ?
        """,
        (dependent_type, dependent_id),
    ).fetchall()

    return [
        {
            "dependency_type": row["dependency_type"],
            "dependency_id": row["dependency_id"],
            "reason": row["reason"],
        }
        for row in rows
    ]


def get_dependents(
    dependency_type: str,
    dependency_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all entities that depend on a given entity.

    Args:
        dependency_type: Type of dependency
        dependency_id: ID of dependency
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of dependent entity dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT dependent_type, dependent_id, reason
        FROM entity_depends_on
        WHERE dependency_type = ? AND dependency_id = ?
        """,
        (dependency_type, dependency_id),
    ).fetchall()

    return [
        {
            "dependent_type": row["dependent_type"],
            "dependent_id": row["dependent_id"],
            "reason": row["reason"],
        }
        for row in rows
    ]


# =============================================================================
# JUNCTION TABLES (entity_deliverables, entity_commits)
# =============================================================================

def create_deliverable(
    description: str,
    status: str = "pending",
    artifact_path: Optional[str] = None,
    artifact_url: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Create a new deliverable.

    Args:
        description: Deliverable description
        status: Status (pending, in_progress, completed)
        artifact_path: Optional path to artifact
        artifact_url: Optional URL to artifact
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created deliverable
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        INSERT INTO deliverables (description, status, artifact_path, artifact_url)
        VALUES (?, ?, ?, ?)
        """,
        (description, status, artifact_path, artifact_url),
    )

    return cursor.lastrowid


def link_deliverable(
    owner_type: str,
    owner_id: str,
    deliverable_id: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Link a deliverable to an entity.

    Args:
        owner_type: Type of owner (track, sprint, task)
        owner_id: ID of owner
        deliverable_id: ID of deliverable
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created link

    Raises:
        sqlite3.IntegrityError: If link already exists or deliverable doesn't exist
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        INSERT INTO entity_deliverables (owner_type, owner_id, deliverable_id)
        VALUES (?, ?, ?)
        """,
        (owner_type, owner_id, deliverable_id),
    )

    return cursor.lastrowid


def unlink_deliverable(
    owner_type: str,
    owner_id: str,
    deliverable_id: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Unlink a deliverable from an entity.

    Args:
        owner_type: Type of owner
        owner_id: ID of owner
        deliverable_id: ID of deliverable
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if link was removed, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        DELETE FROM entity_deliverables
        WHERE owner_type = ? AND owner_id = ? AND deliverable_id = ?
        """,
        (owner_type, owner_id, deliverable_id),
    )

    return cursor.rowcount > 0


def get_deliverables(
    owner_type: str,
    owner_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all deliverables for an entity.

    Args:
        owner_type: Type of owner
        owner_id: ID of owner
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of deliverable dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT d.id, d.description, d.status, d.completed_at, d.artifact_path, d.artifact_url
        FROM deliverables d
        JOIN entity_deliverables ed ON d.id = ed.deliverable_id
        WHERE ed.owner_type = ? AND ed.owner_id = ?
        """,
        (owner_type, owner_id),
    ).fetchall()

    return [
        {
            "id": row["id"],
            "description": row["description"],
            "status": row["status"],
            "completed_at": _deserialize_datetime(row["completed_at"]),
            "artifact_path": row["artifact_path"],
            "artifact_url": row["artifact_url"],
        }
        for row in rows
    ]


def create_commit(
    commit_hash: str,
    commit_message: Optional[str] = None,
    author: Optional[str] = None,
    committed_at: Optional[datetime] = None,
    branch: Optional[str] = None,
    pr_number: Optional[int] = None,
    pr_url: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Create a new commit record.

    Args:
        commit_hash: Git commit hash
        commit_message: Commit message
        author: Commit author
        committed_at: Commit timestamp
        branch: Branch name
        pr_number: PR number if applicable
        pr_url: PR URL if applicable
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created commit

    Raises:
        sqlite3.IntegrityError: If commit hash already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        INSERT INTO commits (commit_hash, commit_message, author, committed_at, branch, pr_number, pr_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (commit_hash, commit_message, author, _serialize_datetime(committed_at), branch, pr_number, pr_url),
    )

    return cursor.lastrowid


def get_commit_by_hash(
    commit_hash: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a commit by its hash.

    Args:
        commit_hash: Git commit hash
        conn: Database connection
        db_path: Path to database file

    Returns:
        Commit dictionary or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM commits WHERE commit_hash = ?",
        (commit_hash,),
    ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "commit_hash": row["commit_hash"],
        "commit_message": row["commit_message"],
        "author": row["author"],
        "committed_at": _deserialize_datetime(row["committed_at"]),
        "branch": row["branch"],
        "pr_number": row["pr_number"],
        "pr_url": row["pr_url"],
    }


def link_commit(
    owner_type: str,
    owner_id: str,
    commit_id: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Link a commit to an entity.

    Args:
        owner_type: Type of owner (track, sprint, task)
        owner_id: ID of owner
        commit_id: ID of commit
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created link

    Raises:
        sqlite3.IntegrityError: If link already exists or commit doesn't exist
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        INSERT INTO entity_commits (owner_type, owner_id, commit_id)
        VALUES (?, ?, ?)
        """,
        (owner_type, owner_id, commit_id),
    )

    return cursor.lastrowid


def unlink_commit(
    owner_type: str,
    owner_id: str,
    commit_id: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Unlink a commit from an entity.

    Args:
        owner_type: Type of owner
        owner_id: ID of owner
        commit_id: ID of commit
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if link was removed, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        DELETE FROM entity_commits
        WHERE owner_type = ? AND owner_id = ? AND commit_id = ?
        """,
        (owner_type, owner_id, commit_id),
    )

    return cursor.rowcount > 0


def get_commits(
    owner_type: str,
    owner_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all commits for an entity.

    Args:
        owner_type: Type of owner
        owner_id: ID of owner
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of commit dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT c.id, c.commit_hash, c.commit_message, c.author, c.committed_at,
               c.branch, c.pr_number, c.pr_url
        FROM commits c
        JOIN entity_commits ec ON c.id = ec.commit_id
        WHERE ec.owner_type = ? AND ec.owner_id = ?
        ORDER BY c.committed_at DESC
        """,
        (owner_type, owner_id),
    ).fetchall()

    return [
        {
            "id": row["id"],
            "commit_hash": row["commit_hash"],
            "commit_message": row["commit_message"],
            "author": row["author"],
            "committed_at": _deserialize_datetime(row["committed_at"]),
            "branch": row["branch"],
            "pr_number": row["pr_number"],
            "pr_url": row["pr_url"],
        }
        for row in rows
    ]


# =============================================================================
# QUALITY GATES
# =============================================================================

def add_quality_gate(
    owner_type: str,
    owner_id: str,
    name: str,
    threshold: int = 100,
    blocking: bool = True,
    description: Optional[str] = None,
    status: str = "not_run",
    score: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Add a quality gate to a track or sprint.

    Args:
        owner_type: Type of owner (track or sprint only)
        owner_id: ID of owner
        name: Gate name
        threshold: Pass threshold (0-100)
        blocking: Whether gate is blocking
        description: Gate description
        status: Gate status (not_run, running, passed, failed, superseded)
        score: Current score
        metadata: Additional metadata
        conn: Database connection
        db_path: Path to database file

    Returns:
        ID of the created gate

    Raises:
        ValueError: If owner_type is not 'track' or 'sprint'
    """
    if owner_type not in ("track", "sprint"):
        raise ValueError("Quality gates can only be added to tracks or sprints")

    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        """
        INSERT INTO quality_gates (
            owner_type, owner_id, name, description, threshold, blocking, status, score, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            owner_type, owner_id, name, description, threshold,
            1 if blocking else 0, status, score, _serialize_json(metadata)
        ),
    )

    return cursor.lastrowid


def update_quality_gate(
    gate_id: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    **kwargs,
) -> bool:
    """
    Update a quality gate.

    Args:
        gate_id: ID of the gate
        conn: Database connection
        db_path: Path to database file
        **kwargs: Fields to update (status, score, last_run_at, last_run_by, etc.)

    Returns:
        True if gate was updated, False if not found
    """
    if not kwargs:
        raise ValueError("No update fields provided")

    if conn is None:
        conn = get_connection(db_path=db_path)

    updates = []
    values = []

    for key, value in kwargs.items():
        if key in ("last_run_at",):
            updates.append(f"{key} = ?")
            values.append(_serialize_datetime(value))
        elif key == "metadata":
            updates.append("metadata = ?")
            values.append(_serialize_json(value))
        elif key == "blocking":
            updates.append("blocking = ?")
            values.append(1 if value else 0)
        elif key in ("name", "description", "status", "last_run_by"):
            updates.append(f"{key} = ?")
            values.append(value)
        elif key in ("threshold", "score"):
            updates.append(f"{key} = ?")
            values.append(value)
        else:
            raise ValueError(f"Unknown field: {key}")

    values.append(gate_id)

    cursor = conn.execute(
        f"UPDATE quality_gates SET {', '.join(updates)} WHERE id = ?",
        values,
    )

    return cursor.rowcount > 0


def remove_quality_gate(
    gate_id: int,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Remove a quality gate.

    Args:
        gate_id: ID of the gate
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if gate was removed, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM quality_gates WHERE id = ?",
        (gate_id,),
    )

    return cursor.rowcount > 0


def list_quality_gates(
    owner_type: str,
    owner_id: str,
    status: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    List quality gates for an entity.

    Args:
        owner_type: Type of owner (track or sprint)
        owner_id: ID of owner
        status: Filter by status
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of quality gate dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM quality_gates WHERE owner_type = ? AND owner_id = ?"
    params: List[Any] = [owner_type, owner_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": row["id"],
            "owner_type": row["owner_type"],
            "owner_id": row["owner_id"],
            "name": row["name"],
            "description": row["description"],
            "threshold": row["threshold"],
            "blocking": bool(row["blocking"]),
            "status": row["status"],
            "score": row["score"],
            "last_run_at": _deserialize_datetime(row["last_run_at"]),
            "last_run_by": row["last_run_by"],
            "metadata": _deserialize_json(row["metadata"]),
        }
        for row in rows
    ]


def get_blocking_gates(
    owner_type: str,
    owner_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get blocking quality gates that haven't passed.

    Args:
        owner_type: Type of owner
        owner_id: ID of owner
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of blocking gates that need to pass
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT * FROM quality_gates
        WHERE owner_type = ? AND owner_id = ?
        AND blocking = 1 AND status != 'passed'
        """,
        (owner_type, owner_id),
    ).fetchall()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "threshold": row["threshold"],
            "status": row["status"],
            "score": row["score"],
        }
        for row in rows
    ]


# =============================================================================
# DEPENDENCY CHAIN QUERIES (Recursive CTEs)
# =============================================================================

def get_dependency_chain(
    entity_type: str,
    entity_id: str,
    max_depth: int = 10,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get the transitive dependency chain for an entity using recursive CTE.

    Traverses entity_depends_on to find all direct and indirect dependencies.

    Args:
        entity_type: Type of entity
        entity_id: ID of entity
        max_depth: Maximum depth to traverse (default 10)
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of dependencies with depth level
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        WITH RECURSIVE dep_chain(dependent_type, dependent_id, dependency_type, dependency_id, depth) AS (
            -- Base case: direct dependencies
            SELECT dependent_type, dependent_id, dependency_type, dependency_id, 1
            FROM entity_depends_on
            WHERE dependent_type = ? AND dependent_id = ?

            UNION ALL

            -- Recursive case: dependencies of dependencies
            SELECT e.dependent_type, e.dependent_id, e.dependency_type, e.dependency_id, dc.depth + 1
            FROM entity_depends_on e
            JOIN dep_chain dc ON e.dependent_type = dc.dependency_type AND e.dependent_id = dc.dependency_id
            WHERE dc.depth < ?
        )
        SELECT DISTINCT dependency_type, dependency_id, MIN(depth) as depth
        FROM dep_chain
        GROUP BY dependency_type, dependency_id
        ORDER BY depth, dependency_type, dependency_id
        """,
        (entity_type, entity_id, max_depth),
    ).fetchall()

    return [
        {
            "dependency_type": row["dependency_type"],
            "dependency_id": row["dependency_id"],
            "depth": row["depth"],
        }
        for row in rows
    ]


def get_blocking_chain(
    entity_type: str,
    entity_id: str,
    max_depth: int = 10,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get the transitive blocking chain for an entity using recursive CTE.

    Traverses entity_blocked_by to find all direct and indirect blockers.

    Args:
        entity_type: Type of entity
        entity_id: ID of entity
        max_depth: Maximum depth to traverse
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of blockers with depth level
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        WITH RECURSIVE block_chain(blocked_type, blocked_id, blocker_type, blocker_id, depth) AS (
            -- Base case: direct blockers
            SELECT blocked_type, blocked_id, blocker_type, blocker_id, 1
            FROM entity_blocked_by
            WHERE blocked_type = ? AND blocked_id = ?

            UNION ALL

            -- Recursive case: blockers of blockers
            SELECT e.blocked_type, e.blocked_id, e.blocker_type, e.blocker_id, bc.depth + 1
            FROM entity_blocked_by e
            JOIN block_chain bc ON e.blocked_type = bc.blocker_type AND e.blocked_id = bc.blocker_id
            WHERE bc.depth < ?
        )
        SELECT DISTINCT blocker_type, blocker_id, MIN(depth) as depth
        FROM block_chain
        GROUP BY blocker_type, blocker_id
        ORDER BY depth, blocker_type, blocker_id
        """,
        (entity_type, entity_id, max_depth),
    ).fetchall()

    return [
        {
            "blocker_type": row["blocker_type"],
            "blocker_id": row["blocker_id"],
            "depth": row["depth"],
        }
        for row in rows
    ]


def detect_circular_dependencies(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Tuple[str, str, str, str]]:
    """
    Detect circular dependencies in entity_depends_on.

    Uses recursive CTE to find cycles. A cycle exists if we can follow
    dependencies from A and eventually arrive back at A.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of (type1, id1, type2, id2) tuples representing circular dependencies
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    # Simpler approach: for each dependency relationship A->B,
    # check if there's a path from B back to A
    rows = conn.execute(
        """
        WITH RECURSIVE reachable(start_type, start_id, current_type, current_id, depth) AS (
            -- Start from each entity that has dependencies
            SELECT DISTINCT
                dependent_type, dependent_id,
                dependent_type, dependent_id,
                0
            FROM entity_depends_on

            UNION

            -- Follow the dependency chain
            SELECT
                r.start_type, r.start_id,
                e.dependency_type, e.dependency_id,
                r.depth + 1
            FROM reachable r
            JOIN entity_depends_on e
                ON e.dependent_type = r.current_type AND e.dependent_id = r.current_id
            WHERE r.depth < 20
        )
        -- Find cycles: starting entity is reachable from itself with depth > 0
        SELECT DISTINCT r1.start_type, r1.start_id, r2.current_type, r2.current_id
        FROM reachable r1
        JOIN reachable r2
            ON r1.start_type = r2.start_type AND r1.start_id = r2.start_id
        WHERE r2.current_type = r1.start_type AND r2.current_id = r1.start_id
        AND r2.depth > 0
        """,
    ).fetchall()

    return [
        (row["start_type"], row["start_id"], row["current_type"], row["current_id"])
        for row in rows
    ]


def detect_circular_blockers(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Tuple[str, str, str, str]]:
    """
    Detect circular blocking relationships in entity_blocked_by.

    Uses recursive CTE to find cycles. A cycle exists if we can follow
    blockers from A and eventually arrive back at A.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of (type1, id1, type2, id2) tuples representing circular blockers
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    # For each blocked entity, follow the blocker chain and check if we return to start
    rows = conn.execute(
        """
        WITH RECURSIVE reachable(start_type, start_id, current_type, current_id, depth) AS (
            -- Start from each entity that is blocked
            SELECT DISTINCT
                blocked_type, blocked_id,
                blocked_type, blocked_id,
                0
            FROM entity_blocked_by

            UNION

            -- Follow the blocker chain
            SELECT
                r.start_type, r.start_id,
                e.blocker_type, e.blocker_id,
                r.depth + 1
            FROM reachable r
            JOIN entity_blocked_by e
                ON e.blocked_type = r.current_type AND e.blocked_id = r.current_id
            WHERE r.depth < 20
        )
        -- Find cycles: starting entity is reachable from itself with depth > 0
        SELECT DISTINCT r1.start_type, r1.start_id, r2.current_type, r2.current_id
        FROM reachable r1
        JOIN reachable r2
            ON r1.start_type = r2.start_type AND r1.start_id = r2.start_id
        WHERE r2.current_type = r1.start_type AND r2.current_id = r1.start_id
        AND r2.depth > 0
        """,
    ).fetchall()

    return [
        (row["start_type"], row["start_id"], row["current_type"], row["current_id"])
        for row in rows
    ]


# =============================================================================
# CONTEXT SYSTEM V2 - TICKET COMMIT LINKS
# =============================================================================


def create_ticket_commit_link(
    ticket_id: str,
    commit_sha: str,
    reference_type: str,
    link_source: str,
    linked_at: Optional[datetime] = None,
    aggregate_confidence: float = 0.0,
    file_overlap_signal: Optional[Dict[str, Any]] = None,
    message_ref_signal: Optional[Dict[str, Any]] = None,
    manual_signal: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Tuple[str, str]:
    """
    Create a ticket-commit link.

    Args:
        ticket_id: The ticket/task ID (ULID)
        commit_sha: The git commit SHA
        reference_type: Type of reference (task_reference, completion_claim)
        link_source: Where the link originated (pre_commit_hook, post_commit, manual)
        linked_at: When the link was created (defaults to now)
        aggregate_confidence: Combined confidence score (0.0 to 1.0)
        file_overlap_signal: JSON for FileOverlapSignal
        message_ref_signal: JSON for MessageRefSignal
        manual_signal: JSON for ManualSignal
        conn: Database connection
        db_path: Path to database file

    Returns:
        Tuple of (ticket_id, commit_sha) as the composite key

    Raises:
        sqlite3.IntegrityError: If link already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if linked_at is None:
        linked_at = datetime.now()

    conn.execute(
        """
        INSERT INTO ticket_commit_links (
            ticket_id, commit_sha, reference_type, aggregate_confidence,
            linked_at, link_source, file_overlap_signal, message_ref_signal, manual_signal
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            commit_sha,
            reference_type,
            aggregate_confidence,
            _serialize_datetime(linked_at),
            link_source,
            _serialize_json(file_overlap_signal),
            _serialize_json(message_ref_signal),
            _serialize_json(manual_signal),
        ),
    )

    return (ticket_id, commit_sha)


def get_ticket_commit_link(
    ticket_id: str,
    commit_sha: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a specific ticket-commit link.

    Args:
        ticket_id: The ticket/task ID
        commit_sha: The git commit SHA
        conn: Database connection
        db_path: Path to database file

    Returns:
        Link dictionary or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM ticket_commit_links WHERE ticket_id = ? AND commit_sha = ?",
        (ticket_id, commit_sha),
    ).fetchone()

    if row is None:
        return None

    return {
        "ticket_id": row["ticket_id"],
        "commit_sha": row["commit_sha"],
        "reference_type": row["reference_type"],
        "aggregate_confidence": row["aggregate_confidence"],
        "linked_at": _deserialize_datetime(row["linked_at"]),
        "link_source": row["link_source"],
        "file_overlap_signal": _deserialize_json(row["file_overlap_signal"]),
        "message_ref_signal": _deserialize_json(row["message_ref_signal"]),
        "manual_signal": _deserialize_json(row["manual_signal"]),
    }


def get_commits_for_ticket(
    ticket_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all commits linked to a ticket.

    Args:
        ticket_id: The ticket/task ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of link dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT * FROM ticket_commit_links WHERE ticket_id = ? ORDER BY linked_at DESC",
        (ticket_id,),
    ).fetchall()

    return [
        {
            "ticket_id": row["ticket_id"],
            "commit_sha": row["commit_sha"],
            "reference_type": row["reference_type"],
            "aggregate_confidence": row["aggregate_confidence"],
            "linked_at": _deserialize_datetime(row["linked_at"]),
            "link_source": row["link_source"],
            "file_overlap_signal": _deserialize_json(row["file_overlap_signal"]),
            "message_ref_signal": _deserialize_json(row["message_ref_signal"]),
            "manual_signal": _deserialize_json(row["manual_signal"]),
        }
        for row in rows
    ]


def get_tickets_for_commit(
    commit_sha: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all tickets linked to a commit.

    Args:
        commit_sha: The git commit SHA
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of link dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT * FROM ticket_commit_links WHERE commit_sha = ? ORDER BY linked_at DESC",
        (commit_sha,),
    ).fetchall()

    return [
        {
            "ticket_id": row["ticket_id"],
            "commit_sha": row["commit_sha"],
            "reference_type": row["reference_type"],
            "aggregate_confidence": row["aggregate_confidence"],
            "linked_at": _deserialize_datetime(row["linked_at"]),
            "link_source": row["link_source"],
            "file_overlap_signal": _deserialize_json(row["file_overlap_signal"]),
            "message_ref_signal": _deserialize_json(row["message_ref_signal"]),
            "manual_signal": _deserialize_json(row["manual_signal"]),
        }
        for row in rows
    ]


def delete_ticket_commit_link(
    ticket_id: str,
    commit_sha: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a ticket-commit link.

    Args:
        ticket_id: The ticket/task ID
        commit_sha: The git commit SHA
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if link was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM ticket_commit_links WHERE ticket_id = ? AND commit_sha = ?",
        (ticket_id, commit_sha),
    )

    return cursor.rowcount > 0


# =============================================================================
# CONTEXT SYSTEM V2 - TICKET ARTIFACT ASSOCIATIONS
# =============================================================================


def create_ticket_artifact_association(
    ticket_id: str,
    artifact_id: str,
    association_source: str,
    added_at: Optional[datetime] = None,
    added_by: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Tuple[str, str]:
    """
    Create a ticket-artifact association.

    Args:
        ticket_id: The ticket/task ID (ULID)
        artifact_id: The artifact ID (ULID)
        association_source: How this association was created
        added_at: When the association was created (defaults to now)
        added_by: Who/what created this association
        conn: Database connection
        db_path: Path to database file

    Returns:
        Tuple of (ticket_id, artifact_id) as the composite key

    Raises:
        sqlite3.IntegrityError: If association already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if added_at is None:
        added_at = datetime.now()

    conn.execute(
        """
        INSERT INTO ticket_artifact_associations (
            ticket_id, artifact_id, association_source, added_at, added_by
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            artifact_id,
            association_source,
            _serialize_datetime(added_at),
            added_by,
        ),
    )

    return (ticket_id, artifact_id)


def get_ticket_artifact_association(
    ticket_id: str,
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a specific ticket-artifact association.

    Args:
        ticket_id: The ticket/task ID
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        Association dictionary or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM ticket_artifact_associations WHERE ticket_id = ? AND artifact_id = ?",
        (ticket_id, artifact_id),
    ).fetchone()

    if row is None:
        return None

    return {
        "ticket_id": row["ticket_id"],
        "artifact_id": row["artifact_id"],
        "association_source": row["association_source"],
        "added_at": _deserialize_datetime(row["added_at"]),
        "added_by": row["added_by"],
    }


def get_artifacts_for_ticket(
    ticket_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all artifacts associated with a ticket.

    Args:
        ticket_id: The ticket/task ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of association dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT * FROM ticket_artifact_associations WHERE ticket_id = ? ORDER BY added_at DESC",
        (ticket_id,),
    ).fetchall()

    return [
        {
            "ticket_id": row["ticket_id"],
            "artifact_id": row["artifact_id"],
            "association_source": row["association_source"],
            "added_at": _deserialize_datetime(row["added_at"]),
            "added_by": row["added_by"],
        }
        for row in rows
    ]


def get_tickets_for_artifact(
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all tickets associated with an artifact.

    Args:
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of association dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT * FROM ticket_artifact_associations WHERE artifact_id = ? ORDER BY added_at DESC",
        (artifact_id,),
    ).fetchall()

    return [
        {
            "ticket_id": row["ticket_id"],
            "artifact_id": row["artifact_id"],
            "association_source": row["association_source"],
            "added_at": _deserialize_datetime(row["added_at"]),
            "added_by": row["added_by"],
        }
        for row in rows
    ]


def delete_ticket_artifact_association(
    ticket_id: str,
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a ticket-artifact association.

    Args:
        ticket_id: The ticket/task ID
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if association was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM ticket_artifact_associations WHERE ticket_id = ? AND artifact_id = ?",
        (ticket_id, artifact_id),
    )

    return cursor.rowcount > 0


# =============================================================================
# CONTEXT SYSTEM V2 - COMMIT ARTIFACT CHANGES
# =============================================================================


def create_commit_artifact_change(
    commit_sha: str,
    artifact_id: str,
    change_type: str,
    recorded_at: Optional[datetime] = None,
    previous_path: Optional[str] = None,
    lines_added: Optional[int] = None,
    lines_removed: Optional[int] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Tuple[str, str]:
    """
    Create a commit-artifact change record.

    Args:
        commit_sha: The git commit SHA
        artifact_id: The artifact ID (ULID)
        change_type: Type of change (added, modified, deleted, renamed)
        recorded_at: When this change was recorded (defaults to now)
        previous_path: For renames, the path before the rename
        lines_added: Number of lines added
        lines_removed: Number of lines removed
        conn: Database connection
        db_path: Path to database file

    Returns:
        Tuple of (commit_sha, artifact_id) as the composite key

    Raises:
        sqlite3.IntegrityError: If change record already exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if recorded_at is None:
        recorded_at = datetime.now()

    conn.execute(
        """
        INSERT INTO commit_artifact_changes (
            commit_sha, artifact_id, change_type, previous_path,
            lines_added, lines_removed, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            commit_sha,
            artifact_id,
            change_type,
            previous_path,
            lines_added,
            lines_removed,
            _serialize_datetime(recorded_at),
        ),
    )

    return (commit_sha, artifact_id)


def get_commit_artifact_change(
    commit_sha: str,
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get a specific commit-artifact change record.

    Args:
        commit_sha: The git commit SHA
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        Change dictionary or None if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM commit_artifact_changes WHERE commit_sha = ? AND artifact_id = ?",
        (commit_sha, artifact_id),
    ).fetchone()

    if row is None:
        return None

    return {
        "commit_sha": row["commit_sha"],
        "artifact_id": row["artifact_id"],
        "change_type": row["change_type"],
        "previous_path": row["previous_path"],
        "lines_added": row["lines_added"],
        "lines_removed": row["lines_removed"],
        "recorded_at": _deserialize_datetime(row["recorded_at"]),
    }


def get_artifacts_changed_by_commit(
    commit_sha: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all artifacts changed by a commit.

    Args:
        commit_sha: The git commit SHA
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of change dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT * FROM commit_artifact_changes WHERE commit_sha = ? ORDER BY recorded_at DESC",
        (commit_sha,),
    ).fetchall()

    return [
        {
            "commit_sha": row["commit_sha"],
            "artifact_id": row["artifact_id"],
            "change_type": row["change_type"],
            "previous_path": row["previous_path"],
            "lines_added": row["lines_added"],
            "lines_removed": row["lines_removed"],
            "recorded_at": _deserialize_datetime(row["recorded_at"]),
        }
        for row in rows
    ]


def get_commits_changing_artifact(
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all commits that changed an artifact.

    Args:
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of change dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT * FROM commit_artifact_changes WHERE artifact_id = ? ORDER BY recorded_at DESC",
        (artifact_id,),
    ).fetchall()

    return [
        {
            "commit_sha": row["commit_sha"],
            "artifact_id": row["artifact_id"],
            "change_type": row["change_type"],
            "previous_path": row["previous_path"],
            "lines_added": row["lines_added"],
            "lines_removed": row["lines_removed"],
            "recorded_at": _deserialize_datetime(row["recorded_at"]),
        }
        for row in rows
    ]


def delete_commit_artifact_change(
    commit_sha: str,
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a commit-artifact change record.

    Args:
        commit_sha: The git commit SHA
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if change was deleted, False if not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    cursor = conn.execute(
        "DELETE FROM commit_artifact_changes WHERE commit_sha = ? AND artifact_id = ?",
        (commit_sha, artifact_id),
    )

    return cursor.rowcount > 0


# =============================================================================
# CONTEXT SYSTEM V2 - TRIANGLE QUERIES
# =============================================================================


def get_ticket_commit_artifacts(
    ticket_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all commit-artifact relationships for a ticket (triangle query).

    This is the full picture: which commits touched which artifacts for this ticket.

    Args:
        ticket_id: The ticket/task ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of triangle relationship dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT
            tcl.ticket_id,
            tcl.commit_sha,
            tcl.reference_type,
            tcl.aggregate_confidence AS link_confidence,
            tcl.link_source,
            cac.artifact_id,
            cac.change_type,
            cac.lines_added,
            cac.lines_removed,
            taa.association_source AS direct_association_source
        FROM ticket_commit_links tcl
        JOIN commit_artifact_changes cac ON tcl.commit_sha = cac.commit_sha
        LEFT JOIN ticket_artifact_associations taa
            ON tcl.ticket_id = taa.ticket_id AND cac.artifact_id = taa.artifact_id
        WHERE tcl.ticket_id = ?
        ORDER BY tcl.linked_at DESC, cac.recorded_at DESC
        """,
        (ticket_id,),
    ).fetchall()

    return [
        {
            "ticket_id": row["ticket_id"],
            "commit_sha": row["commit_sha"],
            "reference_type": row["reference_type"],
            "link_confidence": row["link_confidence"],
            "link_source": row["link_source"],
            "artifact_id": row["artifact_id"],
            "change_type": row["change_type"],
            "lines_added": row["lines_added"],
            "lines_removed": row["lines_removed"],
            "direct_association_source": row["direct_association_source"],
        }
        for row in rows
    ]


def get_artifact_ticket_commits(
    artifact_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all ticket-commit relationships that touched an artifact (reverse triangle query).

    This shows which tickets and commits affected this artifact.

    Args:
        artifact_id: The artifact ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of triangle relationship dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """
        SELECT
            tcl.ticket_id,
            tcl.commit_sha,
            tcl.reference_type,
            tcl.aggregate_confidence AS link_confidence,
            tcl.link_source,
            cac.artifact_id,
            cac.change_type,
            cac.lines_added,
            cac.lines_removed,
            taa.association_source AS direct_association_source
        FROM commit_artifact_changes cac
        JOIN ticket_commit_links tcl ON cac.commit_sha = tcl.commit_sha
        LEFT JOIN ticket_artifact_associations taa
            ON tcl.ticket_id = taa.ticket_id AND cac.artifact_id = taa.artifact_id
        WHERE cac.artifact_id = ?
        ORDER BY cac.recorded_at DESC, tcl.linked_at DESC
        """,
        (artifact_id,),
    ).fetchall()

    return [
        {
            "ticket_id": row["ticket_id"],
            "commit_sha": row["commit_sha"],
            "reference_type": row["reference_type"],
            "link_confidence": row["link_confidence"],
            "link_source": row["link_source"],
            "artifact_id": row["artifact_id"],
            "change_type": row["change_type"],
            "lines_added": row["lines_added"],
            "lines_removed": row["lines_removed"],
            "direct_association_source": row["direct_association_source"],
        }
        for row in rows
    ]
