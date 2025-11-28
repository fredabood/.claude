"""
SQL Views for computed roadmap metrics.

This module defines 21 views that compute all progress aggregations automatically
from task data, replacing the 24 manually-maintained counter fields.

Views are organized into categories:
- Progress aggregation: v_sprint_progress, v_track_progress, v_roadmap_progress
- Blocking/dependency: v_blocked_entities, v_unblocked_tasks, v_dependency_chain
- Quality gates: v_quality_gate_summary, v_failing_quality_gates
- Activity/reporting: v_recent_activity, v_velocity_metrics
- Summary data: v_track_summary_data, v_sprint_summary_data, v_task_summary_data
- Data integrity validation: v_track_sprint_summaries
- Aggregation (sprint): v_sprint_commits, v_sprint_deliverables, v_sprint_assigned_agents, v_sprint_estimated_duration
- Aggregation (track): v_track_commits, v_track_deliverables, v_track_assigned_agents
"""

import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path

from .connection import get_connection


# =============================================================================
# VIEW DEFINITIONS
# =============================================================================

VIEW_DEFINITIONS = {
    # -------------------------------------------------------------------------
    # Progress Aggregation Views (must be created in order due to dependencies)
    # -------------------------------------------------------------------------

    "v_sprint_progress": """
        CREATE VIEW v_sprint_progress AS
        SELECT
            s.id AS sprint_id,
            s.track_id,
            s.roadmap_id,
            s.name AS sprint_name,
            s.status AS sprint_status,

            -- Development tasks
            COUNT(CASE WHEN t.task_type = 'development' THEN 1 END)
                AS development_tasks_total,
            COUNT(CASE WHEN t.task_type = 'development' AND t.status = 'completed' THEN 1 END)
                AS development_tasks_completed,

            -- Completion gate tasks
            COUNT(CASE WHEN t.task_type = 'completion_gate' THEN 1 END)
                AS completion_gate_tasks_total,
            COUNT(CASE WHEN t.task_type = 'completion_gate' AND t.status = 'completed' THEN 1 END)
                AS completion_gate_tasks_completed,

            -- Production gate tasks
            COUNT(CASE WHEN t.task_type = 'production_gate' THEN 1 END)
                AS production_gate_tasks_total,
            COUNT(CASE WHEN t.task_type = 'production_gate' AND t.status = 'completed' THEN 1 END)
                AS production_gate_tasks_completed,

            -- Total tasks
            COUNT(t.id) AS tasks_total,
            COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS tasks_completed,

            -- Completion percentage (avoid division by zero)
            CASE
                WHEN COUNT(t.id) = 0 THEN 0
                ELSE ROUND(
                    (COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0) / COUNT(t.id)
                )
            END AS completion_percent,

            -- Blocked calculation
            CASE
                WHEN EXISTS (
                    SELECT 1 FROM entity_blocked_by eb
                    WHERE eb.blocked_type = 'sprint' AND eb.blocked_id = s.id
                ) THEN 1
                ELSE 0
            END AS is_blocked

        FROM sprints s
        LEFT JOIN tasks t ON t.sprint_id = s.id
        GROUP BY s.id, s.track_id, s.roadmap_id, s.name, s.status
    """,

    "v_track_progress": """
        CREATE VIEW v_track_progress AS
        SELECT
            tr.id AS track_id,
            tr.roadmap_id,
            tr.name AS track_name,
            tr.status AS track_status,

            -- Sprint counts
            COUNT(DISTINCT s.id) AS sprints_total,
            COUNT(DISTINCT CASE WHEN s.status = 'completed' THEN s.id END) AS sprints_completed,

            -- Task aggregations (sum from sprint progress)
            COALESCE(SUM(sp.tasks_total), 0) AS tasks_total,
            COALESCE(SUM(sp.tasks_completed), 0) AS tasks_completed,

            -- Completion percentage
            CASE
                WHEN COALESCE(SUM(sp.tasks_total), 0) = 0 THEN 0
                ELSE ROUND(
                    (COALESCE(SUM(sp.tasks_completed), 0) * 100.0) / COALESCE(SUM(sp.tasks_total), 0)
                )
            END AS completion_percent,

            -- Blocked calculation
            CASE
                WHEN EXISTS (
                    SELECT 1 FROM entity_blocked_by eb
                    WHERE eb.blocked_type = 'track' AND eb.blocked_id = tr.id
                ) THEN 1
                ELSE 0
            END AS is_blocked

        FROM tracks tr
        LEFT JOIN sprints s ON s.track_id = tr.id
        LEFT JOIN v_sprint_progress sp ON sp.sprint_id = s.id
        GROUP BY tr.id, tr.roadmap_id, tr.name, tr.status
    """,

    "v_roadmap_progress": """
        CREATE VIEW v_roadmap_progress AS
        SELECT
            r.id AS roadmap_id,
            r.name AS roadmap_name,
            r.status AS roadmap_status,

            -- Track counts
            COUNT(DISTINCT tr.id) AS tracks_total,
            COUNT(DISTINCT CASE WHEN tr.status = 'completed' THEN tr.id END) AS tracks_completed,

            -- Sprint aggregations
            COALESCE(SUM(tp.sprints_total), 0) AS sprints_total,
            COALESCE(SUM(tp.sprints_completed), 0) AS sprints_completed,

            -- Task aggregations
            COALESCE(SUM(tp.tasks_total), 0) AS tasks_total,
            COALESCE(SUM(tp.tasks_completed), 0) AS tasks_completed,

            -- Completion percentage
            CASE
                WHEN COALESCE(SUM(tp.tasks_total), 0) = 0 THEN 0
                ELSE ROUND(
                    (COALESCE(SUM(tp.tasks_completed), 0) * 100.0) / COALESCE(SUM(tp.tasks_total), 0)
                )
            END AS completion_percent,

            -- Blocked calculation
            CASE
                WHEN EXISTS (
                    SELECT 1 FROM entity_blocked_by eb
                    WHERE eb.blocked_type = 'roadmap' AND eb.blocked_id = r.id
                ) THEN 1
                ELSE 0
            END AS is_blocked

        FROM roadmaps r
        LEFT JOIN tracks tr ON tr.roadmap_id = r.id
        LEFT JOIN v_track_progress tp ON tp.track_id = tr.id
        GROUP BY r.id, r.name, r.status
    """,

    # -------------------------------------------------------------------------
    # Blocking & Dependency Views
    # -------------------------------------------------------------------------

    "v_blocked_entities": """
        CREATE VIEW v_blocked_entities AS
        SELECT
            eb.blocked_type,
            eb.blocked_id,
            eb.blocker_type,
            eb.blocker_id,
            eb.reason,

            -- Blocker status (is the blocker resolved?)
            CASE eb.blocker_type
                WHEN 'task' THEN (SELECT status FROM tasks WHERE id = eb.blocker_id)
                WHEN 'sprint' THEN (SELECT status FROM sprints WHERE id = eb.blocker_id)
                WHEN 'track' THEN (SELECT status FROM tracks WHERE id = eb.blocker_id)
            END AS blocker_status,

            -- Is blocker completed?
            CASE eb.blocker_type
                WHEN 'task' THEN (SELECT status = 'completed' FROM tasks WHERE id = eb.blocker_id)
                WHEN 'sprint' THEN (SELECT status = 'completed' FROM sprints WHERE id = eb.blocker_id)
                WHEN 'track' THEN (SELECT status = 'completed' FROM tracks WHERE id = eb.blocker_id)
            END AS blocker_completed

        FROM entity_blocked_by eb
    """,

    "v_unblocked_tasks": """
        CREATE VIEW v_unblocked_tasks AS
        SELECT t.*
        FROM tasks t
        WHERE t.status = 'not_started'
          AND NOT EXISTS (
            SELECT 1
            FROM entity_blocked_by eb
            WHERE eb.blocked_type = 'task'
              AND eb.blocked_id = t.id
              AND (
                SELECT status FROM tasks WHERE id = eb.blocker_id
              ) != 'completed'
          )
          AND NOT EXISTS (
            SELECT 1
            FROM v_blocked_entities vb
            WHERE vb.blocked_type = 'sprint'
              AND vb.blocked_id = t.sprint_id
              AND vb.blocker_completed = 0
          )
    """,

    "v_dependency_chain": """
        CREATE VIEW v_dependency_chain AS
        WITH RECURSIVE deps AS (
            -- Base case: direct dependencies
            SELECT
                dependent_type,
                dependent_id,
                dependency_type,
                dependency_id,
                1 AS depth,
                dependent_id || ' -> ' || dependency_id AS chain
            FROM entity_depends_on

            UNION ALL

            -- Recursive case: transitive dependencies
            SELECT
                d.dependent_type,
                d.dependent_id,
                edo.dependency_type,
                edo.dependency_id,
                d.depth + 1,
                d.chain || ' -> ' || edo.dependency_id
            FROM deps d
            JOIN entity_depends_on edo
                ON edo.dependent_type = d.dependency_type
                AND edo.dependent_id = d.dependency_id
            WHERE d.depth < 10  -- Prevent infinite loops
        )
        SELECT * FROM deps
    """,

    # -------------------------------------------------------------------------
    # Quality Gate Views
    # -------------------------------------------------------------------------

    "v_quality_gate_summary": """
        CREATE VIEW v_quality_gate_summary AS
        SELECT
            qg.owner_type,
            qg.owner_id,

            -- Entity name for context
            CASE qg.owner_type
                WHEN 'track' THEN (SELECT name FROM tracks WHERE id = qg.owner_id)
                WHEN 'sprint' THEN (SELECT name FROM sprints WHERE id = qg.owner_id)
            END AS owner_name,

            -- Counts by status
            COUNT(*) AS gates_total,
            COUNT(CASE WHEN qg.status = 'passed' THEN 1 END) AS gates_passed,
            COUNT(CASE WHEN qg.status = 'failed' THEN 1 END) AS gates_failed,
            COUNT(CASE WHEN qg.status = 'not_run' THEN 1 END) AS gates_pending,

            -- Any blocking gates failed?
            COUNT(CASE WHEN qg.blocking = 1 AND qg.status = 'failed' THEN 1 END) AS blocking_failures,

            -- Overall pass rate
            CASE
                WHEN COUNT(*) = 0 THEN 100
                ELSE ROUND(
                    (COUNT(CASE WHEN qg.status = 'passed' THEN 1 END) * 100.0) / COUNT(*)
                )
            END AS pass_rate

        FROM quality_gates qg
        GROUP BY qg.owner_type, qg.owner_id
    """,

    "v_failing_quality_gates": """
        CREATE VIEW v_failing_quality_gates AS
        SELECT
            qg.owner_type,
            qg.owner_id,
            CASE qg.owner_type
                WHEN 'track' THEN (SELECT name FROM tracks WHERE id = qg.owner_id)
                WHEN 'sprint' THEN (SELECT name FROM sprints WHERE id = qg.owner_id)
            END AS owner_name,
            qg.name AS gate_name,
            qg.description,
            qg.threshold,
            qg.score,
            qg.blocking,
            qg.last_run_at

        FROM quality_gates qg
        WHERE qg.status = 'failed'
        ORDER BY qg.blocking DESC, qg.owner_type, qg.last_run_at DESC
    """,

    # -------------------------------------------------------------------------
    # Activity & Reporting Views
    # -------------------------------------------------------------------------

    "v_recent_activity": """
        CREATE VIEW v_recent_activity AS
        SELECT
            al.id,
            al.roadmap_id,
            al.event_type,
            al.event_description,
            al.occurred_at,
            al.entity_type,
            al.entity_id,
            al.actor,

            -- Entity name for context
            CASE al.entity_type
                WHEN 'task' THEN (SELECT title FROM tasks WHERE id = al.entity_id)
                WHEN 'sprint' THEN (SELECT name FROM sprints WHERE id = al.entity_id)
                WHEN 'track' THEN (SELECT name FROM tracks WHERE id = al.entity_id)
                ELSE NULL
            END AS entity_name

        FROM activity_log al
        ORDER BY al.occurred_at DESC
    """,

    "v_velocity_metrics": """
        CREATE VIEW v_velocity_metrics AS
        SELECT
            t.track_id,
            DATE(t.completed) AS completion_date,
            COUNT(*) AS tasks_completed,
            SUM(t.actual_tokens) AS tokens_used,
            AVG(
                JULIANDAY(t.completed) - JULIANDAY(t.started)
            ) * 24 AS avg_hours_per_task

        FROM tasks t
        WHERE t.status = 'completed'
          AND t.completed IS NOT NULL
        GROUP BY t.track_id, DATE(t.completed)
        ORDER BY completion_date DESC
    """,

    # -------------------------------------------------------------------------
    # Summary Data Views
    # -------------------------------------------------------------------------

    "v_track_summary_data": """
        CREATE VIEW v_track_summary_data AS
        SELECT
            tr.roadmap_id,
            tr.id AS track_id,
            tr.name,
            tr.status,
            tr.priority
        FROM tracks tr
    """,

    "v_sprint_summary_data": """
        CREATE VIEW v_sprint_summary_data AS
        SELECT
            s.track_id,
            s.id AS sprint_id,
            s.name,
            s.status,
            s.metadata AS estimated_duration,
            (SELECT COUNT(*) FROM tasks t WHERE t.sprint_id = s.id) AS tasks_count,
            s.started
        FROM sprints s
    """,

    "v_task_summary_data": """
        CREATE VIEW v_task_summary_data AS
        SELECT
            t.sprint_id,
            t.id AS task_id,
            t.title,
            t.status,
            t.task_type,
            t.gate_info
        FROM tasks t
    """,

    # -------------------------------------------------------------------------
    # Data Integrity Validation Views
    # -------------------------------------------------------------------------

    "v_track_sprint_summaries": """
        CREATE VIEW v_track_sprint_summaries AS
        SELECT
            s.track_id,
            s.id AS sprint_id,
            s.name,
            s.status,
            -- Extract estimated_duration from metadata JSON
            json_extract(s.metadata, '$.estimated_duration') AS estimated_duration,
            -- Compute tasks_count from actual tasks
            (SELECT COUNT(*) FROM tasks t WHERE t.sprint_id = s.id) AS tasks_count,
            s.started,
            s.completed
        FROM sprints s
        ORDER BY s.track_id, s.id
    """,

    # -------------------------------------------------------------------------
    # Aggregation Views (roll up authored data from child entities)
    # -------------------------------------------------------------------------

    "v_sprint_commits": """
        CREATE VIEW v_sprint_commits AS
        SELECT
            t.sprint_id,
            t.track_id,
            -- Aggregate all commits from tasks in this sprint as JSON array
            '[' || GROUP_CONCAT(
                CASE WHEN t.commits_json IS NOT NULL AND t.commits_json != '[]'
                THEN SUBSTR(t.commits_json, 2, LENGTH(t.commits_json) - 2)
                END
            ) || ']' AS commits_json,
            COUNT(CASE WHEN t.commits_json IS NOT NULL AND t.commits_json != '[]' THEN 1 END) AS tasks_with_commits
        FROM tasks t
        WHERE t.commits_json IS NOT NULL
        GROUP BY t.sprint_id, t.track_id
    """,

    "v_sprint_deliverables": """
        CREATE VIEW v_sprint_deliverables AS
        SELECT
            t.sprint_id,
            t.track_id,
            -- Aggregate all deliverables from tasks in this sprint as JSON array
            '[' || GROUP_CONCAT(
                CASE WHEN t.deliverables_json IS NOT NULL AND t.deliverables_json != '[]'
                THEN SUBSTR(t.deliverables_json, 2, LENGTH(t.deliverables_json) - 2)
                END
            ) || ']' AS deliverables_json,
            COUNT(CASE WHEN t.deliverables_json IS NOT NULL AND t.deliverables_json != '[]' THEN 1 END) AS tasks_with_deliverables
        FROM tasks t
        WHERE t.deliverables_json IS NOT NULL
        GROUP BY t.sprint_id, t.track_id
    """,

    "v_sprint_assigned_agents": """
        CREATE VIEW v_sprint_assigned_agents AS
        SELECT
            t.sprint_id,
            t.track_id,
            -- Get distinct agents assigned to tasks in this sprint
            '[' || GROUP_CONCAT(DISTINCT
                CASE WHEN t.assigned_agent IS NOT NULL
                THEN '"' || t.assigned_agent || '"'
                END
            ) || ']' AS assigned_agents_json,
            COUNT(DISTINCT t.assigned_agent) AS unique_agents
        FROM tasks t
        WHERE t.assigned_agent IS NOT NULL
        GROUP BY t.sprint_id, t.track_id
    """,

    "v_sprint_estimated_duration": """
        CREATE VIEW v_sprint_estimated_duration AS
        SELECT
            t.sprint_id,
            t.track_id,
            -- Sum estimated durations (assumes format like '2 hours', '1 day', etc.)
            -- For now, just concatenate as JSON array - parsing would require application logic
            '[' || GROUP_CONCAT(
                CASE WHEN t.estimated_duration IS NOT NULL
                THEN '"' || t.estimated_duration || '"'
                END
            ) || ']' AS estimated_durations_json,
            COUNT(CASE WHEN t.estimated_duration IS NOT NULL THEN 1 END) AS tasks_with_estimates
        FROM tasks t
        WHERE t.estimated_duration IS NOT NULL
        GROUP BY t.sprint_id, t.track_id
    """,

    "v_track_commits": """
        CREATE VIEW v_track_commits AS
        SELECT
            sc.track_id,
            -- Aggregate commits from all sprints in this track
            '[' || GROUP_CONCAT(
                CASE WHEN sc.commits_json IS NOT NULL AND sc.commits_json != '[]' AND sc.commits_json != '[null]'
                THEN SUBSTR(sc.commits_json, 2, LENGTH(sc.commits_json) - 2)
                END
            ) || ']' AS commits_json,
            SUM(sc.tasks_with_commits) AS total_tasks_with_commits
        FROM v_sprint_commits sc
        GROUP BY sc.track_id
    """,

    "v_track_deliverables": """
        CREATE VIEW v_track_deliverables AS
        SELECT
            sd.track_id,
            -- Aggregate deliverables from all sprints in this track
            '[' || GROUP_CONCAT(
                CASE WHEN sd.deliverables_json IS NOT NULL AND sd.deliverables_json != '[]' AND sd.deliverables_json != '[null]'
                THEN SUBSTR(sd.deliverables_json, 2, LENGTH(sd.deliverables_json) - 2)
                END
            ) || ']' AS deliverables_json,
            SUM(sd.tasks_with_deliverables) AS total_tasks_with_deliverables
        FROM v_sprint_deliverables sd
        GROUP BY sd.track_id
    """,

    "v_track_assigned_agents": """
        CREATE VIEW v_track_assigned_agents AS
        SELECT
            t.track_id,
            -- Get distinct agents assigned to any task in this track
            '[' || GROUP_CONCAT(DISTINCT
                CASE WHEN t.assigned_agent IS NOT NULL
                THEN '"' || t.assigned_agent || '"'
                END
            ) || ']' AS assigned_agents_json,
            COUNT(DISTINCT t.assigned_agent) AS unique_agents
        FROM tasks t
        WHERE t.assigned_agent IS NOT NULL
        GROUP BY t.track_id
    """,
}


# Views must be created in this order due to dependencies
VIEW_ORDER = [
    # Progress views (depend on each other)
    "v_sprint_progress",      # Base view - no dependencies
    "v_track_progress",       # Depends on v_sprint_progress
    "v_roadmap_progress",     # Depends on v_track_progress

    # Blocking/dependency views
    "v_blocked_entities",     # No dependencies
    "v_unblocked_tasks",      # Depends on v_blocked_entities
    "v_dependency_chain",     # No dependencies

    # Quality gate views
    "v_quality_gate_summary", # No dependencies
    "v_failing_quality_gates",# No dependencies

    # Activity/metrics views
    "v_recent_activity",      # No dependencies
    "v_velocity_metrics",     # No dependencies

    # Summary data views
    "v_track_summary_data",   # No dependencies
    "v_sprint_summary_data",  # No dependencies
    "v_task_summary_data",    # No dependencies

    # Data integrity validation
    "v_track_sprint_summaries",  # No dependencies

    # Aggregation views (roll up authored data from child entities)
    # Sprint-level aggregations (from tasks)
    "v_sprint_commits",           # Aggregates task commits to sprint
    "v_sprint_deliverables",      # Aggregates task deliverables to sprint
    "v_sprint_assigned_agents",   # Aggregates task agents to sprint
    "v_sprint_estimated_duration", # Aggregates task durations to sprint

    # Track-level aggregations (from sprints/tasks)
    "v_track_commits",            # Depends on v_sprint_commits
    "v_track_deliverables",       # Depends on v_sprint_deliverables
    "v_track_assigned_agents",    # Aggregates from tasks directly
]


# =============================================================================
# VIEW MANAGEMENT FUNCTIONS
# =============================================================================

def create_views(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> None:
    """
    Create all computed views in the database.

    Views are created in dependency order.

    Args:
        conn: Database connection
        db_path: Path to database file
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    for view_name in VIEW_ORDER:
        ddl = VIEW_DEFINITIONS[view_name]
        conn.execute(ddl)


def drop_views(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> None:
    """
    Drop all computed views from the database.

    Views are dropped in reverse dependency order.

    Args:
        conn: Database connection
        db_path: Path to database file
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    for view_name in reversed(VIEW_ORDER):
        conn.execute(f"DROP VIEW IF EXISTS {view_name}")


def view_exists(
    view_name: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if a view exists in the database.

    Args:
        view_name: Name of the view
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if view exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'view' AND name = ?",
        (view_name,),
    ).fetchone()

    return row is not None


def get_view_names(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[str]:
    """
    Get all view names in the database.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of view names
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
    ).fetchall()

    return [row[0] for row in rows]


# =============================================================================
# QUERY HELPER FUNCTIONS
# =============================================================================

def get_sprint_progress(
    sprint_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get progress metrics for a sprint.

    Args:
        sprint_id: Sprint identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with progress metrics, or None if sprint not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM v_sprint_progress WHERE sprint_id = ?",
        (sprint_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_track_progress(
    track_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get progress metrics for a track.

    Args:
        track_id: Track identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with progress metrics, or None if track not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM v_track_progress WHERE track_id = ?",
        (track_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_roadmap_progress(
    roadmap_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get progress metrics for a roadmap.

    Args:
        roadmap_id: Roadmap identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with progress metrics, or None if roadmap not found
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM v_roadmap_progress WHERE roadmap_id = ?",
        (roadmap_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_blocked_entities(
    entity_type: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all blocked entities, optionally filtered by type.

    Args:
        entity_type: Filter by entity type (task, sprint, track)
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of blocked entity dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if entity_type:
        rows = conn.execute(
            "SELECT * FROM v_blocked_entities WHERE blocked_type = ?",
            (entity_type,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM v_blocked_entities").fetchall()

    return [dict(row) for row in rows]


def get_unblocked_tasks(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all tasks that are ready to start (not blocked).

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of unblocked task dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute("SELECT * FROM v_unblocked_tasks").fetchall()
    return [dict(row) for row in rows]


def get_dependency_chain(
    dependent_type: str,
    dependent_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get the full dependency chain for an entity.

    Args:
        dependent_type: Type of dependent entity
        dependent_id: ID of dependent entity
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of dependency chain entries with depth
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        """SELECT * FROM v_dependency_chain
           WHERE dependent_type = ? AND dependent_id = ?
           ORDER BY depth""",
        (dependent_type, dependent_id),
    ).fetchall()

    return [dict(row) for row in rows]


def get_quality_gate_summary(
    owner_type: str,
    owner_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get quality gate summary for a track or sprint.

    Args:
        owner_type: Owner type (track or sprint)
        owner_id: Owner identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with gate summary, or None if no gates
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT * FROM v_quality_gate_summary WHERE owner_type = ? AND owner_id = ?",
        (owner_type, owner_id),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_failing_quality_gates(
    owner_type: Optional[str] = None,
    owner_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get all failing quality gates, optionally filtered.

    Args:
        owner_type: Filter by owner type
        owner_id: Filter by owner ID
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of failing gate dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    query = "SELECT * FROM v_failing_quality_gates"
    params: List[Any] = []

    if owner_type and owner_id:
        query += " WHERE owner_type = ? AND owner_id = ?"
        params = [owner_type, owner_id]
    elif owner_type:
        query += " WHERE owner_type = ?"
        params = [owner_type]

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_recent_activity(
    roadmap_id: Optional[str] = None,
    limit: int = 50,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get recent activity, optionally filtered by roadmap.

    Args:
        roadmap_id: Filter by roadmap
        limit: Maximum number of entries
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of activity dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if roadmap_id:
        rows = conn.execute(
            "SELECT * FROM v_recent_activity WHERE roadmap_id = ? LIMIT ?",
            (roadmap_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM v_recent_activity LIMIT ?",
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_velocity_metrics(
    track_id: Optional[str] = None,
    days: int = 30,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get velocity metrics, optionally filtered by track.

    Args:
        track_id: Filter by track
        days: Number of days to include
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of velocity metric dictionaries
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if track_id:
        rows = conn.execute(
            """SELECT * FROM v_velocity_metrics
               WHERE track_id = ?
               AND completion_date >= DATE('now', ?)
               ORDER BY completion_date DESC""",
            (track_id, f"-{days} days"),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM v_velocity_metrics
               WHERE completion_date >= DATE('now', ?)
               ORDER BY completion_date DESC""",
            (f"-{days} days",),
        ).fetchall()

    return [dict(row) for row in rows]


def get_all_progress(
    roadmap_id: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get complete progress report for a roadmap.

    Returns roadmap, track, and sprint level progress in one call.

    Args:
        roadmap_id: Roadmap identifier
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with roadmap, tracks, and sprints progress
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    roadmap = get_roadmap_progress(roadmap_id, conn=conn)

    track_rows = conn.execute(
        "SELECT * FROM v_track_progress WHERE roadmap_id = ?",
        (roadmap_id,),
    ).fetchall()
    tracks = [dict(row) for row in track_rows]

    sprint_rows = conn.execute(
        "SELECT * FROM v_sprint_progress WHERE roadmap_id = ?",
        (roadmap_id,),
    ).fetchall()
    sprints = [dict(row) for row in sprint_rows]

    return {
        "roadmap": roadmap,
        "tracks": tracks,
        "sprints": sprints,
    }


def get_track_sprint_summaries(
    track_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Get computed sprint summaries for data integrity validation.

    This view computes sprint summaries directly from sprints and tasks tables,
    useful for comparing against embedded YAML summaries to detect drift.

    Args:
        track_id: Filter by track (optional)
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of sprint summary dictionaries with:
        - track_id, sprint_id, name, status
        - estimated_duration (from metadata)
        - tasks_count (computed from tasks table)
        - started, completed timestamps
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    if track_id:
        rows = conn.execute(
            "SELECT * FROM v_track_sprint_summaries WHERE track_id = ?",
            (track_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM v_track_sprint_summaries").fetchall()

    return [dict(row) for row in rows]
