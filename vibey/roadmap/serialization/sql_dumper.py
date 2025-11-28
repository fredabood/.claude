"""
SQLite dumper for roadmap objects.

Saves Python dataclass objects to SQLite database.
This is the parallel to yaml_dumper.py for the SQLite backend.

Note: This version focuses on core entity tables (roadmaps, tracks, sprints, tasks).
Auxiliary tables (version_history, activity_log, etc.) are handled separately or
stored as JSON within the entity tables.
"""

import json
from datetime import datetime
from typing import List, Optional

from ..models import (
    Roadmap,
    Track,
    Sprint,
    Task,
)
from ..database import get_connection, transaction, disable_triggers_for_bulk_operations, enable_triggers_for_bulk_operations


def _format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO 8601 string for SQLite."""
    if dt is None:
        return None
    return dt.isoformat() + 'Z' if dt.tzinfo is None else dt.isoformat()


def save_roadmap(roadmap: Roadmap, db_path: Optional['Path'] = None):
    """
    Save a roadmap to SQLite database.

    This saves only the roadmap entity itself.
    Use save_full_roadmap() to save the entire hierarchy.

    Args:
        roadmap: Roadmap object to save
        db_path: Optional path to database file
    """
    from pathlib import Path
    with transaction(db_path=db_path) as conn:
        # Encode version_strategy and metadata as JSON
        version_strategy_json = json.dumps({
            'major_on': roadmap.version_strategy.major_on.value,
            'minor_on': roadmap.version_strategy.minor_on.value,
            'patch_on': roadmap.version_strategy.patch_on.value,
        })

        metadata_json = json.dumps({
            'created_by': roadmap.metadata.created_by,
            'framework_version': roadmap.metadata.framework_version,
            'schema_version': roadmap.metadata.schema_version,
            'last_updated': _format_datetime(roadmap.metadata.last_updated),
            'purpose': roadmap.metadata.purpose,
            'description': roadmap.metadata.description,
        })

        # Upsert roadmap
        conn.execute("""
            INSERT OR REPLACE INTO roadmaps (
                id, name, version, status, blocked,
                version_strategy,
                created, started, target_completion, completed, deployed,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roadmap.id,
            roadmap.name,
            roadmap.version,
            roadmap.status.value,
            int(roadmap.blocked),
            version_strategy_json,
            _format_datetime(roadmap.created),
            _format_datetime(roadmap.started),
            _format_datetime(roadmap.target_completion),
            _format_datetime(roadmap.completed),
            _format_datetime(roadmap.deployed),
            metadata_json,
        ))

        # Save external dependencies
        conn.execute("DELETE FROM external_dependencies WHERE owner_type = 'roadmap' AND owner_id = ?", (roadmap.id,))
        for dep in roadmap.dependencies:
            conn.execute("""
                INSERT INTO external_dependencies (owner_type, owner_id, name, description, status)
                VALUES ('roadmap', ?, ?, ?, ?)
            """, (roadmap.id, dep.name, dep.required_for, dep.status))

        # Save version history
        conn.execute("DELETE FROM version_history WHERE roadmap_id = ?", (roadmap.id,))
        for vh in roadmap.version_history:
            conn.execute("""
                INSERT INTO version_history (roadmap_id, version, date, milestone, git_tag, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (roadmap.id, vh.version, _format_datetime(vh.date), vh.milestone, vh.git_tag, vh.description))

        # Save activity log
        conn.execute("DELETE FROM activity_log WHERE roadmap_id = ?", (roadmap.id,))
        for al in roadmap.activity_log:
            conn.execute("""
                INSERT INTO activity_log (roadmap_id, timestamp, type, description, context)
                VALUES (?, ?, ?, ?, ?)
            """, (roadmap.id, _format_datetime(al.timestamp), al.type.value, al.description, al.context))


def save_track(track: Track, db_path: Optional['Path'] = None):
    """
    Save a track to SQLite database.

    This saves only the track entity itself.
    Child sprints and tasks must be saved separately.

    Args:
        track: Track object to save
        db_path: Optional path to database file
    """
    from pathlib import Path
    with transaction(db_path=db_path) as conn:
        # Encode metadata as JSON
        metadata_json = json.dumps({
            'created_by': getattr(track.metadata, 'created_by', None),
            'last_updated': _format_datetime(track.metadata.last_updated),
            'design_doc': track.metadata.design_doc,
            'implementation_plan': track.metadata.implementation_plan,
            'notes': track.metadata.notes,
        })

        # Upsert track
        conn.execute("""
            INSERT OR REPLACE INTO tracks (
                id, name, roadmap_id, status, blocked, priority,
                created, started, completed, estimated_duration,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track.id,
            track.name,
            track.roadmap_id,
            track.status.value,
            int(track.blocked),
            track.priority.value,
            _format_datetime(track.created),
            _format_datetime(track.started),
            _format_datetime(track.completed),
            track.estimated_duration,
            metadata_json,
        ))

        # Save external dependencies
        conn.execute("DELETE FROM external_dependencies WHERE owner_type = 'track' AND owner_id = ?", (track.id,))
        for dep in track.dependencies:
            conn.execute("""
                INSERT INTO external_dependencies (owner_type, owner_id, name, description, status)
                VALUES ('track', ?, ?, ?, ?)
            """, (track.id, dep.target_id, dep.reason, 'pending'))

        # Save blocking relationships
        conn.execute("DELETE FROM entity_blocks WHERE blocker_type = 'track' AND blocker_id = ?", (track.id,))
        for block in track.blocks:
            conn.execute("""
                INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id, reason)
                VALUES ('track', ?, ?, ?, ?)
            """, (track.id, block.type.value, block.target_id, block.reason))

        conn.execute("DELETE FROM entity_blocked_by WHERE blocked_type = 'track' AND blocked_id = ?", (track.id,))
        for blocker in track.blocked_by:
            conn.execute("""
                INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, reason)
                VALUES ('track', ?, ?, ?, ?)
            """, (track.id, blocker.dependency_type, blocker.dependency_id, None))

        # Save quality gates
        conn.execute("DELETE FROM quality_gates WHERE owner_type = 'track' AND owner_id = ?", (track.id,))
        for qg in track.quality_gates:
            conn.execute("""
                INSERT INTO quality_gates (owner_type, owner_id, name, threshold, status, blocking)
                VALUES ('track', ?, ?, ?, ?, ?)
            """, (track.id, qg.name, qg.threshold, qg.status.value, int(qg.blocking)))


def save_sprint(sprint: Sprint, db_path: Optional['Path'] = None):
    """
    Save a sprint to SQLite database.

    This saves only the sprint entity itself.
    Child tasks must be saved separately.

    Args:
        sprint: Sprint object to save
        db_path: Optional path to database file
    """
    from pathlib import Path
    with transaction(db_path=db_path) as conn:
        # Encode metadata as JSON
        metadata_json = json.dumps({
            'last_updated': _format_datetime(sprint.metadata.last_updated),
            'estimated_duration': sprint.metadata.estimated_duration,
            'actual_duration': sprint.metadata.actual_duration,
            'estimated_tokens': sprint.metadata.estimated_tokens,
            'actual_tokens': sprint.metadata.actual_tokens,
            'agents_used': sprint.metadata.agents_used,
        })

        # Upsert sprint
        conn.execute("""
            INSERT OR REPLACE INTO sprints (
                id, name, track_id, roadmap_id, status, blocked, blocked_reason,
                created, started, completed,
                plan_file, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sprint.id,
            sprint.name,
            sprint.track_id,
            sprint.roadmap_id,
            sprint.status.value,
            int(sprint.blocked),
            sprint.blocked_reason,
            _format_datetime(sprint.created),
            _format_datetime(sprint.started),
            _format_datetime(sprint.completed),
            sprint.plan_file,
            metadata_json,
        ))

        # Save blocking relationships
        conn.execute("DELETE FROM entity_blocks WHERE blocker_type = 'sprint' AND blocker_id = ?", (sprint.id,))
        for block in sprint.blocks:
            conn.execute("""
                INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id, reason)
                VALUES ('sprint', ?, ?, ?, ?)
            """, (sprint.id, block.type.value, block.target_id, block.reason))

        conn.execute("DELETE FROM entity_blocked_by WHERE blocked_type = 'sprint' AND blocked_id = ?", (sprint.id,))
        for blocker in sprint.blocked_by:
            conn.execute("""
                INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, reason)
                VALUES ('sprint', ?, ?, ?, ?)
            """, (sprint.id, blocker.dependency_type, blocker.dependency_id, None))

        # Save development gates
        # Note: development_gates table has (name, description, status) columns
        # We encode DevelopmentGate model data into these columns
        conn.execute("DELETE FROM development_gates WHERE sprint_id = ?", (sprint.id,))
        for dg in sprint.development_gates:
            # Encode gate info: name="{type}:{target_id}", description="{reason}"
            name = f"{dg.type.value}:{dg.target_id}:{dg.target_status}"
            conn.execute("""
                INSERT INTO development_gates (sprint_id, name, description, status)
                VALUES (?, ?, ?, 'pending')
            """, (sprint.id, name, dg.reason or ''))


def save_task(task: Task):
    """
    Save a single task to SQLite database.

    Args:
        task: Task object to save
    """
    save_tasks([task])


def save_tasks(tasks: List[Task], db_path: Optional['Path'] = None):
    """
    Save multiple tasks to SQLite database.

    Args:
        tasks: List of Task objects to save
        db_path: Optional path to database file
    """
    from pathlib import Path
    with transaction(db_path=db_path) as conn:
        for task in tasks:
            # Encode metadata as JSON
            metadata_json = json.dumps({
                'last_updated': _format_datetime(task.metadata.last_updated),
                'token_efficiency': task.metadata.token_efficiency,
                'duration_hours': task.metadata.duration_hours,
            })

            # Encode gate_info if present
            gate_info_json = None
            if task.gate_info:
                gate_info_json = json.dumps({
                    'blocks_status': task.gate_info.blocks_status,
                    'threshold': task.gate_info.threshold,
                    'is_blocking': task.gate_info.is_blocking,
                    'score': task.gate_info.score,
                })

            # Encode audit_results if present
            audit_results_json = None
            if task.audit_results:
                audit_results_json = json.dumps({
                    'issues_found': task.audit_results.issues_found,
                    'issues_fixed': task.audit_results.issues_fixed,
                    'recommendations': task.audit_results.recommendations,
                })

            # Upsert task
            conn.execute("""
                INSERT OR REPLACE INTO tasks (
                    id, sprint_id, track_id, roadmap_id, task_type,
                    title, description, status, blocked,
                    created, started, completed,
                    assigned_agent, priority, phase_label,
                    estimated_tokens, actual_tokens, complexity,
                    gate_info, audit_results, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.sprint_id,
                task.track_id,
                task.roadmap_id,
                task.task_type.value,
                task.title,
                task.description,
                task.status.value,
                int(task.blocked),
                _format_datetime(task.created),
                _format_datetime(task.started),
                _format_datetime(task.completed),
                task.assigned_agent,
                task.priority.value,
                task.phase_label,
                task.estimated_tokens,
                task.actual_tokens,
                task.complexity.value,
                gate_info_json,
                audit_results_json,
                metadata_json,
            ))

            # Save blocking relationships
            conn.execute("DELETE FROM entity_blocks WHERE blocker_type = 'task' AND blocker_id = ?", (task.id,))
            for block in task.blocks:
                conn.execute("""
                    INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id, reason)
                    VALUES ('task', ?, ?, ?, ?)
                """, (task.id, block.type.value, block.target_id, block.reason))

            conn.execute("DELETE FROM entity_blocked_by WHERE blocked_type = 'task' AND blocked_id = ?", (task.id,))
            for blocker in task.blocked_by:
                conn.execute("""
                    INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, reason)
                    VALUES ('task', ?, ?, ?, ?)
                """, (task.id, blocker.dependency_type, blocker.dependency_id, None))

            # Save deliverables
            # Note: deliverables table has (description, status, artifact_path) columns
            # We encode Deliverable model data: description="{type}", artifact_path=paths joined
            conn.execute("DELETE FROM deliverables WHERE id IN (SELECT deliverable_id FROM entity_deliverables WHERE owner_type = 'task' AND owner_id = ?)", (task.id,))
            conn.execute("DELETE FROM entity_deliverables WHERE owner_type = 'task' AND owner_id = ?", (task.id,))
            for d in task.deliverables:
                # Insert deliverable: description holds type, artifact_path holds paths
                cursor = conn.execute("""
                    INSERT INTO deliverables (description, status, artifact_path)
                    VALUES (?, 'pending', ?)
                """, (d.type.value, '|'.join(d.paths) if d.paths else None))
                deliverable_id = cursor.lastrowid

                # Link to task
                conn.execute("""
                    INSERT INTO entity_deliverables (deliverable_id, owner_type, owner_id)
                    VALUES (?, 'task', ?)
                """, (deliverable_id, task.id))


def save_full_roadmap(
    roadmap: Roadmap,
    tracks: List[Track],
    sprints: List[Sprint],
    tasks: List[Task],
    db_path: Optional['Path'] = None,
):
    """
    Save a complete roadmap hierarchy to SQLite database.

    This performs a bulk save with triggers disabled for performance,
    then rebuilds summary tables.

    Args:
        roadmap: Roadmap object
        tracks: List of all Track objects
        sprints: List of all Sprint objects
        tasks: List of all Task objects
        db_path: Optional path to database file
    """
    from pathlib import Path
    with transaction(db_path=db_path) as conn:
        # Disable triggers for bulk operations
        disable_triggers_for_bulk_operations(conn)

        try:
            # Clear existing data (cascade will handle children)
            conn.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap.id,))

        finally:
            # Re-enable triggers
            enable_triggers_for_bulk_operations(conn)

    # Save in order: roadmap -> tracks -> sprints -> tasks
    save_roadmap(roadmap, db_path=db_path)

    for track in tracks:
        save_track(track, db_path=db_path)

    for sprint in sprints:
        save_sprint(sprint, db_path=db_path)

    save_tasks(tasks, db_path=db_path)

    # Rebuild summary tables based on actual data
    with transaction(db_path=db_path) as conn:
        from ..database import rebuild_summary_tables
        rebuild_summary_tables(conn)


# =============================================================================
# AUDIT TRAIL DUMPER
# =============================================================================

def save_audit_trail_entry(
    entry: dict,
    db_path: Optional['Path'] = None,
):
    """
    Save a single audit trail entry to SQLite database.

    Args:
        entry: Dictionary with audit trail entry data
        db_path: Optional path to database file
    """
    with transaction(db_path=db_path) as conn:
        conn.execute("""
            INSERT INTO audit_trail (
                timestamp, object_type, object_id, field,
                old_value, new_value, changed_by, reason,
                commit_sha, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry['timestamp'],
            entry['object_type'],
            entry['object_id'],
            entry['field'],
            entry.get('old_value'),
            entry.get('new_value'),
            entry['changed_by'],
            entry['reason'],
            entry.get('commit'),
            entry['source'],
        ))


def save_audit_trail(
    entries: List[dict],
    db_path: Optional['Path'] = None,
    clear_existing: bool = False,
):
    """
    Save audit trail entries to SQLite database.

    Args:
        entries: List of audit trail entry dictionaries
        db_path: Optional path to database file
        clear_existing: If True, clear all existing entries first
    """
    with transaction(db_path=db_path) as conn:
        if clear_existing:
            conn.execute("DELETE FROM audit_trail")

        for entry in entries:
            conn.execute("""
                INSERT INTO audit_trail (
                    timestamp, object_type, object_id, field,
                    old_value, new_value, changed_by, reason,
                    commit_sha, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry['timestamp'],
                entry['object_type'],
                entry['object_id'],
                entry['field'],
                entry.get('old_value'),
                entry.get('new_value'),
                entry['changed_by'],
                entry['reason'],
                entry.get('commit'),
                entry['source'],
            ))
