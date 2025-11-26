"""
SQLite triggers for automatic state management.

This module defines 40 triggers that handle:
- Timestamp management (auto-set started, completed, updated)
- Blocked flag computation (keep in sync with blocked_by entries)
- Auto-completion cascades (clear blockers, auto-start parents)
- Summary table synchronization
- Activity logging
- Validation (prevent invalid state transitions)

Architecture:
- SQLite is the source of truth
- Triggers ensure consistency automatically
- YAML is a read-only artifact generated on commit
"""

import sqlite3
from typing import Optional, List
from pathlib import Path

from .connection import get_connection


# =============================================================================
# TRIGGER DEFINITIONS
# =============================================================================

TRIGGER_DEFINITIONS = {
    # -------------------------------------------------------------------------
    # TIMESTAMP TRIGGERS (9 triggers)
    # Auto-set started and completed timestamps based on status changes
    # -------------------------------------------------------------------------

    # Auto-set started timestamp when status changes to in_progress
    "trg_task_started": """
        CREATE TRIGGER trg_task_started
        AFTER UPDATE OF status ON tasks
        WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
        BEGIN
            UPDATE tasks SET started = datetime('now') WHERE id = NEW.id;
        END
    """,

    "trg_sprint_started": """
        CREATE TRIGGER trg_sprint_started
        AFTER UPDATE OF status ON sprints
        WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
        BEGIN
            UPDATE sprints SET started = datetime('now') WHERE id = NEW.id;
        END
    """,

    "trg_track_started": """
        CREATE TRIGGER trg_track_started
        AFTER UPDATE OF status ON tracks
        WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
        BEGIN
            UPDATE tracks SET started = datetime('now') WHERE id = NEW.id;
        END
    """,

    # Auto-set completed timestamp when status changes to completed
    "trg_task_completed": """
        CREATE TRIGGER trg_task_completed
        AFTER UPDATE OF status ON tasks
        WHEN NEW.status = 'completed' AND NEW.completed IS NULL
        BEGIN
            UPDATE tasks SET completed = datetime('now') WHERE id = NEW.id;
        END
    """,

    "trg_sprint_completed": """
        CREATE TRIGGER trg_sprint_completed
        AFTER UPDATE OF status ON sprints
        WHEN NEW.status = 'completed' AND NEW.completed IS NULL
        BEGIN
            UPDATE sprints SET completed = datetime('now') WHERE id = NEW.id;
        END
    """,

    "trg_track_completed": """
        CREATE TRIGGER trg_track_completed
        AFTER UPDATE OF status ON tracks
        WHEN NEW.status = 'completed' AND NEW.completed IS NULL
        BEGIN
            UPDATE tracks SET completed = datetime('now') WHERE id = NEW.id;
        END
    """,

    # Auto-set roadmap started timestamp
    "trg_roadmap_started": """
        CREATE TRIGGER trg_roadmap_started
        AFTER UPDATE OF status ON roadmaps
        WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
        BEGIN
            UPDATE roadmaps SET started = datetime('now') WHERE id = NEW.id;
        END
    """,

    # Auto-set roadmap completed timestamp
    "trg_roadmap_completed": """
        CREATE TRIGGER trg_roadmap_completed
        AFTER UPDATE OF status ON roadmaps
        WHEN NEW.status = 'completed' AND NEW.completed IS NULL
        BEGIN
            UPDATE roadmaps SET completed = datetime('now') WHERE id = NEW.id;
        END
    """,

    # Auto-set roadmap deployed timestamp
    "trg_roadmap_deployed": """
        CREATE TRIGGER trg_roadmap_deployed
        AFTER UPDATE OF status ON roadmaps
        WHEN NEW.status = 'deployed' AND NEW.deployed IS NULL
        BEGIN
            UPDATE roadmaps SET deployed = datetime('now') WHERE id = NEW.id;
        END
    """,

    # -------------------------------------------------------------------------
    # BLOCKED FLAG TRIGGERS (6 triggers)
    # Keep blocked column in sync with entity_blocked_by entries
    # -------------------------------------------------------------------------

    # Task blocked flag
    "trg_task_blocked_by_insert": """
        CREATE TRIGGER trg_task_blocked_by_insert
        AFTER INSERT ON entity_blocked_by
        WHEN NEW.blocked_type = 'task'
        BEGIN
            UPDATE tasks SET blocked = 1 WHERE id = NEW.blocked_id;
        END
    """,

    "trg_task_blocked_by_delete": """
        CREATE TRIGGER trg_task_blocked_by_delete
        AFTER DELETE ON entity_blocked_by
        WHEN OLD.blocked_type = 'task'
        BEGIN
            UPDATE tasks
            SET blocked = (
                SELECT COUNT(*) > 0
                FROM entity_blocked_by
                WHERE blocked_type = 'task' AND blocked_id = OLD.blocked_id
            )
            WHERE id = OLD.blocked_id;
        END
    """,

    # Sprint blocked flag
    "trg_sprint_blocked_by_insert": """
        CREATE TRIGGER trg_sprint_blocked_by_insert
        AFTER INSERT ON entity_blocked_by
        WHEN NEW.blocked_type = 'sprint'
        BEGIN
            UPDATE sprints SET blocked = 1 WHERE id = NEW.blocked_id;
        END
    """,

    "trg_sprint_blocked_by_delete": """
        CREATE TRIGGER trg_sprint_blocked_by_delete
        AFTER DELETE ON entity_blocked_by
        WHEN OLD.blocked_type = 'sprint'
        BEGIN
            UPDATE sprints
            SET blocked = (
                SELECT COUNT(*) > 0
                FROM entity_blocked_by
                WHERE blocked_type = 'sprint' AND blocked_id = OLD.blocked_id
            )
            WHERE id = OLD.blocked_id;
        END
    """,

    # Track blocked flag
    "trg_track_blocked_by_insert": """
        CREATE TRIGGER trg_track_blocked_by_insert
        AFTER INSERT ON entity_blocked_by
        WHEN NEW.blocked_type = 'track'
        BEGIN
            UPDATE tracks SET blocked = 1 WHERE id = NEW.blocked_id;
        END
    """,

    "trg_track_blocked_by_delete": """
        CREATE TRIGGER trg_track_blocked_by_delete
        AFTER DELETE ON entity_blocked_by
        WHEN OLD.blocked_type = 'track'
        BEGIN
            UPDATE tracks
            SET blocked = (
                SELECT COUNT(*) > 0
                FROM entity_blocked_by
                WHERE blocked_type = 'track' AND blocked_id = OLD.blocked_id
            )
            WHERE id = OLD.blocked_id;
        END
    """,

    # -------------------------------------------------------------------------
    # AUTO-COMPLETION TRIGGERS (5 triggers)
    # Clear blockers when entities complete, auto-start parent entities
    # -------------------------------------------------------------------------

    # Clear blocking relationships when task completes
    "trg_clear_task_blocker": """
        CREATE TRIGGER trg_clear_task_blocker
        AFTER UPDATE OF status ON tasks
        WHEN NEW.status = 'completed'
        BEGIN
            DELETE FROM entity_blocked_by
            WHERE blocker_type = 'task' AND blocker_id = NEW.id;

            DELETE FROM entity_blocks
            WHERE blocker_type = 'task' AND blocker_id = NEW.id;
        END
    """,

    # Clear blocking relationships when sprint completes
    "trg_clear_sprint_blocker": """
        CREATE TRIGGER trg_clear_sprint_blocker
        AFTER UPDATE OF status ON sprints
        WHEN NEW.status = 'completed'
        BEGIN
            DELETE FROM entity_blocked_by
            WHERE blocker_type = 'sprint' AND blocker_id = NEW.id;

            DELETE FROM entity_blocks
            WHERE blocker_type = 'sprint' AND blocker_id = NEW.id;
        END
    """,

    # Clear blocking relationships when track completes
    "trg_clear_track_blocker": """
        CREATE TRIGGER trg_clear_track_blocker
        AFTER UPDATE OF status ON tracks
        WHEN NEW.status = 'completed'
        BEGIN
            DELETE FROM entity_blocked_by
            WHERE blocker_type = 'track' AND blocker_id = NEW.id;

            DELETE FROM entity_blocks
            WHERE blocker_type = 'track' AND blocker_id = NEW.id;
        END
    """,

    # Auto-start sprint when first task starts
    "trg_auto_start_sprint": """
        CREATE TRIGGER trg_auto_start_sprint
        AFTER UPDATE OF status ON tasks
        WHEN NEW.status = 'in_progress'
        BEGIN
            UPDATE sprints
            SET status = 'in_progress',
                started = COALESCE(started, datetime('now'))
            WHERE id = NEW.sprint_id
              AND status = 'not_started';
        END
    """,

    # Auto-start track when first sprint starts
    "trg_auto_start_track": """
        CREATE TRIGGER trg_auto_start_track
        AFTER UPDATE OF status ON sprints
        WHEN NEW.status = 'in_progress'
        BEGIN
            UPDATE tracks
            SET status = 'in_progress',
                started = COALESCE(started, datetime('now'))
            WHERE id = NEW.track_id
              AND status = 'not_started';
        END
    """,

    # -------------------------------------------------------------------------
    # SUMMARY TABLE TRIGGERS (11 triggers)
    # Keep denormalized summary tables in sync with source tables
    # -------------------------------------------------------------------------

    # Task summaries
    "trg_task_summary_insert": """
        CREATE TRIGGER trg_task_summary_insert
        AFTER INSERT ON tasks
        BEGIN
            INSERT INTO task_summaries (sprint_id, task_id, title, status, task_type, gate_info)
            VALUES (NEW.sprint_id, NEW.id, NEW.title, NEW.status, NEW.task_type, NEW.gate_info);
        END
    """,

    "trg_task_summary_update": """
        CREATE TRIGGER trg_task_summary_update
        AFTER UPDATE ON tasks
        BEGIN
            UPDATE task_summaries
            SET title = NEW.title,
                status = NEW.status,
                task_type = NEW.task_type,
                gate_info = NEW.gate_info
            WHERE task_id = NEW.id;
        END
    """,

    "trg_task_summary_delete": """
        CREATE TRIGGER trg_task_summary_delete
        AFTER DELETE ON tasks
        BEGIN
            DELETE FROM task_summaries WHERE task_id = OLD.id;
        END
    """,

    # Sprint summaries
    "trg_sprint_summary_insert": """
        CREATE TRIGGER trg_sprint_summary_insert
        AFTER INSERT ON sprints
        BEGIN
            INSERT INTO sprint_summaries (track_id, sprint_id, name, status, estimated_duration, tasks_count, started)
            VALUES (
                NEW.track_id,
                NEW.id,
                NEW.name,
                NEW.status,
                json_extract(NEW.metadata, '$.estimated_duration'),
                0,
                NEW.started
            );
        END
    """,

    "trg_sprint_summary_update": """
        CREATE TRIGGER trg_sprint_summary_update
        AFTER UPDATE ON sprints
        BEGIN
            UPDATE sprint_summaries
            SET name = NEW.name,
                status = NEW.status,
                estimated_duration = json_extract(NEW.metadata, '$.estimated_duration'),
                started = NEW.started
            WHERE sprint_id = NEW.id;
        END
    """,

    "trg_sprint_summary_task_count_insert": """
        CREATE TRIGGER trg_sprint_summary_task_count_insert
        AFTER INSERT ON tasks
        BEGIN
            UPDATE sprint_summaries
            SET tasks_count = (SELECT COUNT(*) FROM tasks WHERE sprint_id = NEW.sprint_id)
            WHERE sprint_id = NEW.sprint_id;
        END
    """,

    "trg_sprint_summary_task_count_delete": """
        CREATE TRIGGER trg_sprint_summary_task_count_delete
        AFTER DELETE ON tasks
        BEGIN
            UPDATE sprint_summaries
            SET tasks_count = (SELECT COUNT(*) FROM tasks WHERE sprint_id = OLD.sprint_id)
            WHERE sprint_id = OLD.sprint_id;
        END
    """,

    "trg_sprint_summary_delete": """
        CREATE TRIGGER trg_sprint_summary_delete
        AFTER DELETE ON sprints
        BEGIN
            DELETE FROM sprint_summaries WHERE sprint_id = OLD.id;
        END
    """,

    # Track summaries
    "trg_track_summary_insert": """
        CREATE TRIGGER trg_track_summary_insert
        AFTER INSERT ON tracks
        BEGIN
            INSERT INTO track_summaries (roadmap_id, track_id, name, status, priority)
            VALUES (NEW.roadmap_id, NEW.id, NEW.name, NEW.status, NEW.priority);
        END
    """,

    "trg_track_summary_update": """
        CREATE TRIGGER trg_track_summary_update
        AFTER UPDATE ON tracks
        BEGIN
            UPDATE track_summaries
            SET name = NEW.name,
                status = NEW.status,
                priority = NEW.priority
            WHERE track_id = NEW.id;
        END
    """,

    "trg_track_summary_delete": """
        CREATE TRIGGER trg_track_summary_delete
        AFTER DELETE ON tracks
        BEGIN
            DELETE FROM track_summaries WHERE track_id = OLD.id;
        END
    """,

    # -------------------------------------------------------------------------
    # ACTIVITY LOG TRIGGERS (6 triggers)
    # Log significant events to activity_log table
    # -------------------------------------------------------------------------

    # Task status changes
    "trg_activity_task_status": """
        CREATE TRIGGER trg_activity_task_status
        AFTER UPDATE OF status ON tasks
        WHEN OLD.status != NEW.status
        BEGIN
            INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id, actor)
            VALUES (
                NEW.roadmap_id,
                'task_status_change',
                'Task "' || NEW.title || '" changed from ' || OLD.status || ' to ' || NEW.status,
                datetime('now'),
                'task',
                NEW.id,
                NEW.assigned_agent
            );
        END
    """,

    # Sprint status changes
    "trg_activity_sprint_status": """
        CREATE TRIGGER trg_activity_sprint_status
        AFTER UPDATE OF status ON sprints
        WHEN OLD.status != NEW.status
        BEGIN
            INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
            VALUES (
                NEW.roadmap_id,
                'sprint_status_change',
                'Sprint "' || NEW.name || '" changed from ' || OLD.status || ' to ' || NEW.status,
                datetime('now'),
                'sprint',
                NEW.id
            );
        END
    """,

    # Track status changes
    "trg_activity_track_status": """
        CREATE TRIGGER trg_activity_track_status
        AFTER UPDATE OF status ON tracks
        WHEN OLD.status != NEW.status
        BEGIN
            INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
            VALUES (
                NEW.roadmap_id,
                'track_status_change',
                'Track "' || NEW.name || '" changed from ' || OLD.status || ' to ' || NEW.status,
                datetime('now'),
                'track',
                NEW.id
            );
        END
    """,

    # Task created
    "trg_activity_task_created": """
        CREATE TRIGGER trg_activity_task_created
        AFTER INSERT ON tasks
        BEGIN
            INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
            VALUES (
                NEW.roadmap_id,
                'task_created',
                'Task "' || NEW.title || '" created in sprint ' || NEW.sprint_id,
                datetime('now'),
                'task',
                NEW.id
            );
        END
    """,

    # Sprint created
    "trg_activity_sprint_created": """
        CREATE TRIGGER trg_activity_sprint_created
        AFTER INSERT ON sprints
        BEGIN
            INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
            VALUES (
                NEW.roadmap_id,
                'sprint_created',
                'Sprint "' || NEW.name || '" created in track ' || NEW.track_id,
                datetime('now'),
                'sprint',
                NEW.id
            );
        END
    """,

    # Track created
    "trg_activity_track_created": """
        CREATE TRIGGER trg_activity_track_created
        AFTER INSERT ON tracks
        BEGIN
            INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
            VALUES (
                NEW.roadmap_id,
                'track_created',
                'Track "' || NEW.name || '" created',
                datetime('now'),
                'track',
                NEW.id
            );
        END
    """,

    # -------------------------------------------------------------------------
    # VALIDATION TRIGGERS (3 triggers)
    # Prevent invalid state transitions
    # -------------------------------------------------------------------------

    # Prevent completing blocked tasks
    "trg_prevent_complete_blocked_task": """
        CREATE TRIGGER trg_prevent_complete_blocked_task
        BEFORE UPDATE OF status ON tasks
        WHEN NEW.status = 'completed'
          AND EXISTS (
            SELECT 1 FROM entity_blocked_by eb
            JOIN tasks t ON t.id = eb.blocker_id AND eb.blocker_type = 'task'
            WHERE eb.blocked_type = 'task'
              AND eb.blocked_id = NEW.id
              AND t.status != 'completed'
          )
        BEGIN
            SELECT RAISE(ABORT, 'Cannot complete task: unresolved blockers exist');
        END
    """,

    # Prevent completing sprints with incomplete tasks
    "trg_prevent_complete_sprint_incomplete": """
        CREATE TRIGGER trg_prevent_complete_sprint_incomplete
        BEFORE UPDATE OF status ON sprints
        WHEN NEW.status = 'completed'
          AND EXISTS (
            SELECT 1 FROM tasks
            WHERE sprint_id = NEW.id
              AND status NOT IN ('completed', 'wont_do')
          )
        BEGIN
            SELECT RAISE(ABORT, 'Cannot complete sprint: incomplete tasks exist');
        END
    """,

    # Prevent completing tracks with incomplete sprints
    "trg_prevent_complete_track_incomplete": """
        CREATE TRIGGER trg_prevent_complete_track_incomplete
        BEFORE UPDATE OF status ON tracks
        WHEN NEW.status = 'completed'
          AND EXISTS (
            SELECT 1 FROM sprints
            WHERE track_id = NEW.id
              AND status NOT IN ('completed', 'wont_do')
          )
        BEGIN
            SELECT RAISE(ABORT, 'Cannot complete track: incomplete sprints exist');
        END
    """,
}


# Trigger categories for organized management
TRIGGER_CATEGORIES = {
    "timestamp": [
        "trg_task_started",
        "trg_sprint_started",
        "trg_track_started",
        "trg_task_completed",
        "trg_sprint_completed",
        "trg_track_completed",
        "trg_roadmap_started",
        "trg_roadmap_completed",
        "trg_roadmap_deployed",
    ],
    "blocked_flag": [
        "trg_task_blocked_by_insert",
        "trg_task_blocked_by_delete",
        "trg_sprint_blocked_by_insert",
        "trg_sprint_blocked_by_delete",
        "trg_track_blocked_by_insert",
        "trg_track_blocked_by_delete",
    ],
    "auto_completion": [
        "trg_clear_task_blocker",
        "trg_clear_sprint_blocker",
        "trg_clear_track_blocker",
        "trg_auto_start_sprint",
        "trg_auto_start_track",
    ],
    "summary_tables": [
        "trg_task_summary_insert",
        "trg_task_summary_update",
        "trg_task_summary_delete",
        "trg_sprint_summary_insert",
        "trg_sprint_summary_update",
        "trg_sprint_summary_task_count_insert",
        "trg_sprint_summary_task_count_delete",
        "trg_sprint_summary_delete",
        "trg_track_summary_insert",
        "trg_track_summary_update",
        "trg_track_summary_delete",
    ],
    "activity_log": [
        "trg_activity_task_status",
        "trg_activity_sprint_status",
        "trg_activity_track_status",
        "trg_activity_task_created",
        "trg_activity_sprint_created",
        "trg_activity_track_created",
    ],
    "validation": [
        "trg_prevent_complete_blocked_task",
        "trg_prevent_complete_sprint_incomplete",
        "trg_prevent_complete_track_incomplete",
    ],
}


# All trigger names in creation order
TRIGGER_ORDER = [
    # Timestamp triggers first (no dependencies)
    "trg_task_started",
    "trg_sprint_started",
    "trg_track_started",
    "trg_task_completed",
    "trg_sprint_completed",
    "trg_track_completed",
    "trg_roadmap_started",
    "trg_roadmap_completed",
    "trg_roadmap_deployed",
    # Blocked flag triggers
    "trg_task_blocked_by_insert",
    "trg_task_blocked_by_delete",
    "trg_sprint_blocked_by_insert",
    "trg_sprint_blocked_by_delete",
    "trg_track_blocked_by_insert",
    "trg_track_blocked_by_delete",
    # Auto-completion triggers
    "trg_clear_task_blocker",
    "trg_clear_sprint_blocker",
    "trg_clear_track_blocker",
    "trg_auto_start_sprint",
    "trg_auto_start_track",
    # Summary table triggers
    "trg_task_summary_insert",
    "trg_task_summary_update",
    "trg_task_summary_delete",
    "trg_sprint_summary_insert",
    "trg_sprint_summary_update",
    "trg_sprint_summary_task_count_insert",
    "trg_sprint_summary_task_count_delete",
    "trg_sprint_summary_delete",
    "trg_track_summary_insert",
    "trg_track_summary_update",
    "trg_track_summary_delete",
    # Activity log triggers
    "trg_activity_task_status",
    "trg_activity_sprint_status",
    "trg_activity_track_status",
    "trg_activity_task_created",
    "trg_activity_sprint_created",
    "trg_activity_track_created",
    # Validation triggers last (enforce constraints)
    "trg_prevent_complete_blocked_task",
    "trg_prevent_complete_sprint_incomplete",
    "trg_prevent_complete_track_incomplete",
]


# =============================================================================
# TRIGGER MANAGEMENT FUNCTIONS
# =============================================================================

def create_triggers(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    categories: Optional[List[str]] = None,
) -> int:
    """
    Create triggers in the database.

    Args:
        conn: Database connection
        db_path: Path to database file
        categories: Optional list of categories to create (default: all)
                   Options: timestamp, blocked_flag, auto_completion,
                           summary_tables, activity_log, validation

    Returns:
        Number of triggers created
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    created = 0

    if categories:
        # Create only specified categories
        triggers_to_create = []
        for category in categories:
            if category in TRIGGER_CATEGORIES:
                triggers_to_create.extend(TRIGGER_CATEGORIES[category])
    else:
        # Create all triggers in order
        triggers_to_create = TRIGGER_ORDER

    for trigger_name in triggers_to_create:
        if trigger_name in TRIGGER_DEFINITIONS:
            ddl = TRIGGER_DEFINITIONS[trigger_name]
            conn.execute(ddl)
            created += 1

    return created


def drop_triggers(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    categories: Optional[List[str]] = None,
) -> int:
    """
    Drop triggers from the database.

    Args:
        conn: Database connection
        db_path: Path to database file
        categories: Optional list of categories to drop (default: all)

    Returns:
        Number of triggers dropped
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    dropped = 0

    if categories:
        triggers_to_drop = []
        for category in categories:
            if category in TRIGGER_CATEGORIES:
                triggers_to_drop.extend(TRIGGER_CATEGORIES[category])
    else:
        triggers_to_drop = list(reversed(TRIGGER_ORDER))

    for trigger_name in triggers_to_drop:
        conn.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
        dropped += 1

    return dropped


def trigger_exists(
    trigger_name: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Check if a trigger exists in the database.

    Args:
        trigger_name: Name of the trigger
        conn: Database connection
        db_path: Path to database file

    Returns:
        True if trigger exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'trigger' AND name = ?",
        (trigger_name,),
    ).fetchone()

    return row is not None


def get_trigger_names(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> List[str]:
    """
    Get all trigger names in the database.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        List of trigger names
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'trigger' ORDER BY name"
    ).fetchall()

    return [row[0] for row in rows]


def get_triggers_by_category(
    category: str,
) -> List[str]:
    """
    Get trigger names for a specific category.

    Args:
        category: Category name

    Returns:
        List of trigger names in that category, or empty if invalid category
    """
    return TRIGGER_CATEGORIES.get(category, [])


def validate_triggers(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> dict:
    """
    Validate that all expected triggers exist.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        Dictionary with validation results:
        - valid: bool
        - expected: int
        - found: int
        - missing: List[str]
        - extra: List[str]
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    existing = set(get_trigger_names(conn=conn))
    expected = set(TRIGGER_ORDER)

    missing = expected - existing
    extra = existing - expected

    return {
        "valid": len(missing) == 0,
        "expected": len(expected),
        "found": len(existing & expected),
        "missing": sorted(missing),
        "extra": sorted(extra),
    }


def disable_triggers_for_bulk_operations(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Temporarily disable triggers for bulk operations.

    This drops all activity_log and summary_table triggers to improve
    performance during bulk imports. Call enable_triggers_for_bulk_operations()
    after the bulk operation to recreate them.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        Number of triggers disabled
    """
    return drop_triggers(
        conn=conn,
        db_path=db_path,
        categories=["activity_log", "summary_tables"],
    )


def enable_triggers_for_bulk_operations(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> int:
    """
    Re-enable triggers after bulk operations.

    This recreates the activity_log and summary_table triggers that were
    disabled for bulk operations.

    Args:
        conn: Database connection
        db_path: Path to database file

    Returns:
        Number of triggers enabled
    """
    return create_triggers(
        conn=conn,
        db_path=db_path,
        categories=["activity_log", "summary_tables"],
    )


def rebuild_summary_tables(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
) -> None:
    """
    Rebuild all summary tables from source data.

    Useful after bulk operations to ensure summaries are accurate.

    Args:
        conn: Database connection
        db_path: Path to database file
    """
    if conn is None:
        conn = get_connection(db_path=db_path)

    # Clear existing summaries
    conn.execute("DELETE FROM task_summaries")
    conn.execute("DELETE FROM sprint_summaries")
    conn.execute("DELETE FROM track_summaries")

    # Rebuild task summaries
    conn.execute("""
        INSERT INTO task_summaries (sprint_id, task_id, title, status, task_type, gate_info)
        SELECT sprint_id, id, title, status, task_type, gate_info
        FROM tasks
    """)

    # Rebuild sprint summaries
    conn.execute("""
        INSERT INTO sprint_summaries (track_id, sprint_id, name, status, estimated_duration, tasks_count, started)
        SELECT
            s.track_id,
            s.id,
            s.name,
            s.status,
            json_extract(s.metadata, '$.estimated_duration'),
            (SELECT COUNT(*) FROM tasks WHERE sprint_id = s.id),
            s.started
        FROM sprints s
    """)

    # Rebuild track summaries
    conn.execute("""
        INSERT INTO track_summaries (roadmap_id, track_id, name, status, priority)
        SELECT roadmap_id, id, name, status, priority
        FROM tracks
    """)
