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


def _serialize_commits(commits: list) -> Optional[str]:
    """Serialize commits list to JSON."""
    if not commits:
        return None
    return json.dumps([
        {
            'sha': getattr(c, 'sha', getattr(c, 'commit_hash', None)),
            'message': getattr(c, 'message', getattr(c, 'commit_message', None)),
            'author': getattr(c, 'author', None),
            'committed_at': _format_datetime(getattr(c, 'committed_at', None)),
            'task_id': getattr(c, 'task_id', None),
            'sprint_id': getattr(c, 'sprint_id', None),
        }
        for c in commits
    ])


def _serialize_deliverables(deliverables: list) -> Optional[str]:
    """Serialize deliverables list to JSON."""
    if not deliverables:
        return None
    return json.dumps([
        {
            'type': getattr(d, 'type', 'code').value if hasattr(getattr(d, 'type', None), 'value') else str(getattr(d, 'type', 'code')),
            'paths': getattr(d, 'paths', []),
        }
        for d in deliverables
    ])


def _serialize_standards(standards: list) -> Optional[str]:
    """Serialize standards list to JSON."""
    if not standards:
        return None
    return json.dumps([
        {
            'id': getattr(s, 'id', None),
            'name': getattr(s, 'name', None),
            'description': getattr(s, 'description', None),
            'level': getattr(s, 'level', 'recommended').value if hasattr(getattr(s, 'level', None), 'value') else str(getattr(s, 'level', 'recommended')),
            'status': getattr(s, 'status', 'active').value if hasattr(getattr(s, 'status', None), 'value') else str(getattr(s, 'status', 'active')),
        }
        for s in standards
    ])


def _serialize_sprint_summaries(sprints: list) -> Optional[str]:
    """Serialize sprint summaries list to JSON."""
    if not sprints:
        return None
    return json.dumps([
        {
            'id': s.id,
            'name': s.name,
            'status': s.status.value if hasattr(s.status, 'value') else str(s.status),
            'estimated_duration': getattr(s, 'estimated_duration', None),
            'tasks_count': getattr(s, 'tasks_count', None),
        }
        for s in sprints
    ])


def _serialize_task_summaries(tasks: list) -> Optional[str]:
    """Serialize task summaries list to JSON."""
    if not tasks:
        return None
    return json.dumps([
        {
            'id': t.id,
            'title': t.title,
            'status': t.status.value if hasattr(t.status, 'value') else str(t.status),
            'task_type': t.task_type.value if hasattr(t.task_type, 'value') else str(t.task_type),
        }
        for t in tasks
    ])


def save_roadmap(roadmap: Roadmap, db_path: Optional['Path'] = None):
    """
    Save a roadmap to SQLite database.

    This saves only the roadmap entity itself.
    Use save_full_roadmap() to save the entire hierarchy.

    Args:
        roadmap: Roadmap object to save
        db_path: Optional path to database file
    """
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
    with transaction(db_path=db_path) as conn:
        # Encode metadata as JSON
        metadata_json = json.dumps({
            'created_by': getattr(track.metadata, 'created_by', None),
            'last_updated': _format_datetime(track.metadata.last_updated),
            'design_doc': track.metadata.design_doc,
            'implementation_plan': track.metadata.implementation_plan,
            'notes': track.metadata.notes,
        })

        # Serialize authored data
        dependencies_json = json.dumps([
            {'target_id': d.target_id, 'reason': d.reason}
            for d in track.dependencies
        ]) if track.dependencies else None
        standards_json = _serialize_standards(track.standards)
        strategic_value_json = json.dumps(track.strategic_value) if track.strategic_value else None

        # Upsert track
        conn.execute("""
            INSERT OR REPLACE INTO tracks (
                id, name, roadmap_id, status, blocked, priority,
                created, started, completed, estimated_duration,
                dependencies_json, standards_json, strategic_value_json,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            dependencies_json,
            standards_json,
            strategic_value_json,
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

        # Save dependencies with business logic fields from depends_on
        conn.execute("DELETE FROM entity_blocked_by WHERE blocked_type = 'track' AND blocked_id = ?", (track.id,))
        for dep in track.depends_on:
            conn.execute("""
                INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, required_status, blocks_transition_to, reason)
                VALUES ('track', ?, ?, ?, ?, ?, ?)
            """, (track.id, dep.blocker_type, dep.blocker_id, dep.required_status, dep.blocks_transition_to, None))

        # Save quality gates
        conn.execute("DELETE FROM quality_gates WHERE owner_type = 'track' AND owner_id = ?", (track.id,))
        for qg in track.quality_gates:
            conn.execute("""
                INSERT INTO quality_gates (owner_type, owner_id, name, description, threshold, status, blocking, score)
                VALUES ('track', ?, ?, ?, ?, ?, ?, ?)
            """, (track.id, qg.name, qg.description, qg.threshold, qg.status.value, int(qg.blocking), qg.score))


def save_sprint(sprint: Sprint, db_path: Optional['Path'] = None):
    """
    Save a sprint to SQLite database.

    This saves only the sprint entity itself.
    Child tasks must be saved separately.

    Args:
        sprint: Sprint object to save
        db_path: Optional path to database file
    """
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

        # Serialize authored data
        # Note: Sprint has deliverables as list of strings in YAML
        dependencies_json = None  # Sprint dependencies are in depends_on, not external
        standards_json = _serialize_standards(sprint.standards) if hasattr(sprint, 'standards') else None
        development_gates_json = json.dumps([
            {
                'type': dg.type.value if hasattr(dg.type, 'value') else str(dg.type),
                'target_id': dg.target_id,
                'target_status': dg.target_status,
                'reason': dg.reason,
            }
            for dg in sprint.development_gates
        ]) if sprint.development_gates else None

        # Upsert sprint
        conn.execute("""
            INSERT OR REPLACE INTO sprints (
                id, name, track_id, roadmap_id, status, blocked, blocked_reason,
                created, started, completed,
                plan_file, dependencies_json, standards_json, development_gates_json,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            dependencies_json,
            standards_json,
            development_gates_json,
            metadata_json,
        ))

        # Save blocking relationships
        conn.execute("DELETE FROM entity_blocks WHERE blocker_type = 'sprint' AND blocker_id = ?", (sprint.id,))
        for block in sprint.blocks:
            conn.execute("""
                INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id, reason)
                VALUES ('sprint', ?, ?, ?, ?)
            """, (sprint.id, block.type.value, block.target_id, block.reason))

        # Save dependencies with business logic fields from depends_on
        conn.execute("DELETE FROM entity_blocked_by WHERE blocked_type = 'sprint' AND blocked_id = ?", (sprint.id,))
        for dep in sprint.depends_on:
            conn.execute("""
                INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, required_status, blocks_transition_to, reason)
                VALUES ('sprint', ?, ?, ?, ?, ?, ?)
            """, (sprint.id, dep.blocker_type, dep.blocker_id, dep.required_status, dep.blocks_transition_to, None))

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

        # Save sprint-level quality gates
        conn.execute("DELETE FROM quality_gates WHERE owner_type = 'sprint' AND owner_id = ?", (sprint.id,))
        for qg in sprint.quality_gates:
            conn.execute("""
                INSERT INTO quality_gates (owner_type, owner_id, name, description, threshold, status, blocking, score)
                VALUES ('sprint', ?, ?, ?, ?, ?, ?, ?)
            """, (sprint.id, qg.name, qg.description, qg.threshold, qg.status.value, int(qg.blocking), qg.score))


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
    with transaction(db_path=db_path) as conn:
        for task in tasks:
            # Encode metadata as JSON
            metadata_json = json.dumps({
                'last_updated': _format_datetime(task.metadata.last_updated),
                'token_efficiency': task.metadata.token_efficiency,
                'duration_hours': task.metadata.duration_hours,
            })

            # Encode gate_info if present (handle both dict and object)
            gate_info_json = None
            if task.gate_info:
                if isinstance(task.gate_info, dict):
                    gate_info_json = json.dumps(task.gate_info)
                else:
                    gate_info_json = json.dumps({
                        'blocks_status': task.gate_info.blocks_status,
                        'threshold': task.gate_info.threshold,
                        'is_blocking': task.gate_info.is_blocking,
                        'score': getattr(task.gate_info, 'score', None),
                    })

            # Encode audit_results if present (handle both dict and object)
            audit_results_json = None
            if task.audit_results:
                if isinstance(task.audit_results, dict):
                    audit_results_json = json.dumps(task.audit_results)
                else:
                    audit_results_json = json.dumps({
                        'issues_found': task.audit_results.issues_found,
                        'issues_fixed': task.audit_results.issues_fixed,
                        'recommendations': task.audit_results.recommendations,
                    })

            # Serialize authored data (source of truth - aggregates up to sprints/tracks)
            commits_json = _serialize_commits(task.commits)
            deliverables_json = _serialize_deliverables(task.deliverables)
            # Dependencies are external blockers, different from depends_on (roadmap entities)
            dependencies_json = json.dumps([
                {'target_id': d.target_id, 'reason': d.reason}
                for d in task.dependencies
            ]) if hasattr(task, 'dependencies') and task.dependencies else None
            standards_json = _serialize_standards(task.standards) if hasattr(task, 'standards') and task.standards else None
            # assigned_agent is singular in model, but we store as JSON array for consistency
            assigned_agents_json = json.dumps([task.assigned_agent]) if task.assigned_agent else None
            # estimated_duration from metadata if available
            estimated_duration = getattr(task.metadata, 'estimated_duration', None) if task.metadata else None

            # Upsert task
            conn.execute("""
                INSERT OR REPLACE INTO tasks (
                    id, sprint_id, track_id, roadmap_id, task_type,
                    title, description, status, blocked,
                    created, started, completed,
                    assigned_agent, priority, phase_label,
                    estimated_tokens, actual_tokens, complexity,
                    gate_info, audit_results,
                    commits_json, deliverables_json, dependencies_json, standards_json,
                    assigned_agents_json, estimated_duration,
                    deferred,
                    metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                commits_json,
                deliverables_json,
                dependencies_json,
                standards_json,
                assigned_agents_json,
                estimated_duration,
                int(getattr(task, 'deferred', False)),
                metadata_json,
            ))

            # Save blocking relationships
            conn.execute("DELETE FROM entity_blocks WHERE blocker_type = 'task' AND blocker_id = ?", (task.id,))
            for block in task.blocks:
                conn.execute("""
                    INSERT INTO entity_blocks (blocker_type, blocker_id, blocked_type, blocked_id, reason)
                    VALUES ('task', ?, ?, ?, ?)
                """, (task.id, block.type.value, block.target_id, block.reason))

            # Save dependencies with business logic fields from depends_on
            conn.execute("DELETE FROM entity_blocked_by WHERE blocked_type = 'task' AND blocked_id = ?", (task.id,))
            for dep in task.depends_on:
                conn.execute("""
                    INSERT INTO entity_blocked_by (blocked_type, blocked_id, blocker_type, blocker_id, required_status, blocks_transition_to, reason)
                    VALUES ('task', ?, ?, ?, ?, ?, ?)
                """, (task.id, dep.blocker_type, dep.blocker_id, dep.required_status, dep.blocks_transition_to, None))

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


# =============================================================================
# V2 TICKET DUMPERS (Unified Schema)
# =============================================================================
# These functions save Pydantic ticket models to the unified 'tickets' table
# using SQLAlchemy ORM.

from pathlib import Path
from typing import Union

from ..database.connection import session_scope
from ..models.ticket.orm import (
    TicketORM,
    RoadmapTicketORM,
    TrackTicketORM,
    SprintTicketORM,
    TaskTicketORM,
)
from ..models.ticket.domain import (
    TaskTicket,
    SprintTicket,
    TrackTicket,
    RoadmapTicket,
)


def save_task_ticket(
    task: TaskTicket,
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a TaskTicket to the unified tickets table.

    Args:
        task: TaskTicket Pydantic model to save
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        orm_task = TaskTicketORM.from_pydantic(task)
        session.merge(orm_task)


def save_sprint_ticket(
    sprint: SprintTicket,
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a SprintTicket to the unified tickets table.

    Args:
        sprint: SprintTicket Pydantic model to save
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        orm_sprint = SprintTicketORM.from_pydantic(sprint)
        session.merge(orm_sprint)


def save_track_ticket(
    track: TrackTicket,
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a TrackTicket to the unified tickets table.

    Args:
        track: TrackTicket Pydantic model to save
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        orm_track = TrackTicketORM.from_pydantic(track)
        session.merge(orm_track)


def save_roadmap_ticket(
    roadmap: RoadmapTicket,
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a RoadmapTicket to the unified tickets table.

    Args:
        roadmap: RoadmapTicket Pydantic model to save
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        orm_roadmap = RoadmapTicketORM.from_pydantic(roadmap)
        session.merge(orm_roadmap)


def save_ticket(
    ticket: Union[TaskTicket, SprintTicket, TrackTicket, RoadmapTicket],
    db_path: Optional[Path] = None,
) -> None:
    """
    Save any ticket type to the unified tickets table.

    Dispatches to the appropriate save function based on ticket type.

    Args:
        ticket: Any Pydantic ticket model to save
        db_path: Optional path to database file
    """
    if isinstance(ticket, TaskTicket):
        save_task_ticket(ticket, db_path=db_path)
    elif isinstance(ticket, SprintTicket):
        save_sprint_ticket(ticket, db_path=db_path)
    elif isinstance(ticket, TrackTicket):
        save_track_ticket(ticket, db_path=db_path)
    elif isinstance(ticket, RoadmapTicket):
        save_roadmap_ticket(ticket, db_path=db_path)
    else:
        raise TypeError(f"Unknown ticket type: {type(ticket)}")


def save_sprint_with_tasks(
    sprint: SprintTicket,
    tasks: List[TaskTicket],
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a sprint and its tasks in a single transaction.

    All saves are atomic - either all succeed or all fail.

    Args:
        sprint: SprintTicket to save
        tasks: List of TaskTickets to save
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        # Save sprint
        orm_sprint = SprintTicketORM.from_pydantic(sprint)
        session.merge(orm_sprint)

        # Save all tasks
        for task in tasks:
            orm_task = TaskTicketORM.from_pydantic(task)
            session.merge(orm_task)


def save_track_with_sprints(
    track: TrackTicket,
    sprints: List[SprintTicket],
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a track and its sprints in a single transaction.

    All saves are atomic - either all succeed or all fail.

    Args:
        track: TrackTicket to save
        sprints: List of SprintTickets to save
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        # Save track
        orm_track = TrackTicketORM.from_pydantic(track)
        session.merge(orm_track)

        # Save all sprints
        for sprint in sprints:
            orm_sprint = SprintTicketORM.from_pydantic(sprint)
            session.merge(orm_sprint)


def save_full_roadmap_tickets(
    roadmap: RoadmapTicket,
    tracks: List[TrackTicket],
    sprints: List[SprintTicket],
    tasks: List[TaskTicket],
    db_path: Optional[Path] = None,
) -> None:
    """
    Save a complete roadmap hierarchy to the unified tickets table.

    All saves are atomic - either all succeed or all fail.

    Args:
        roadmap: RoadmapTicket to save
        tracks: List of all TrackTickets
        sprints: List of all SprintTickets
        tasks: List of all TaskTickets
        db_path: Optional path to database file
    """
    with session_scope(db_path=db_path) as session:
        # Save in order: roadmap -> tracks -> sprints -> tasks
        orm_roadmap = RoadmapTicketORM.from_pydantic(roadmap)
        session.merge(orm_roadmap)

        for track in tracks:
            orm_track = TrackTicketORM.from_pydantic(track)
            session.merge(orm_track)

        for sprint in sprints:
            orm_sprint = SprintTicketORM.from_pydantic(sprint)
            session.merge(orm_sprint)

        for task in tasks:
            orm_task = TaskTicketORM.from_pydantic(task)
            session.merge(orm_task)


def delete_ticket(
    ticket_id: str,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a ticket from the unified tickets table.

    Args:
        ticket_id: ID of the ticket to delete
        db_path: Optional path to database file

    Returns:
        True if ticket was deleted, False if not found
    """
    with session_scope(db_path=db_path) as session:
        orm_ticket = session.get(TicketORM, ticket_id)
        if orm_ticket is None:
            return False
        session.delete(orm_ticket)
        return True


def delete_tickets_by_parent(
    parent_id: str,
    db_path: Optional[Path] = None,
) -> int:
    """
    Delete all child tickets of a parent.

    Args:
        parent_id: ID of the parent ticket
        db_path: Optional path to database file

    Returns:
        Number of tickets deleted
    """
    with session_scope(db_path=db_path) as session:
        result = session.query(TicketORM).filter(
            TicketORM.parent_id == parent_id
        ).delete()
        return result


# =============================================================================
# CRITERIA DUMPERS (Legacy Schema)
# =============================================================================
# These functions persist criteria to the polymorphic criteria table
# that references legacy entities (roadmaps, tracks, sprints, tasks, artifacts).

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from ..models.ticket.completable import Criterion
from ..database import get_connection
from pathlib import Path


def dump_criterion(
    criterion: Criterion,
    completable_type: str,
    completable_id: str,
    db_path: Optional[Path] = None,
) -> None:
    """
    Persist a single criterion to the database.

    Args:
        criterion: Criterion Pydantic model
        completable_type: Type of owner entity ('roadmap', 'track', 'sprint', 'task', 'artifact')
        completable_id: ID of owner entity
        db_path: Optional path to database file
    """
    conn = get_connection(db_path=db_path)
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT OR REPLACE INTO criteria (
            id, completable_type, completable_id, description, required,
            blocks_transition_to, target_type, target_json,
            is_met, last_checked, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            criterion.id,
            completable_type,
            completable_id,
            criterion.description,
            1 if criterion.required else 0,
            criterion.blocks_transition_to.value,
            criterion.target.type.value,
            criterion.target.model_dump_json(),
            1 if criterion.is_met else (0 if criterion.is_met is False else None),
            criterion.target.last_checked.isoformat() if criterion.target.last_checked else None,
            now,  # created_at
            now,  # updated_at
        )
    )
    conn.commit()


def dump_criteria(
    criteria: List[Criterion],
    completable_type: str,
    completable_id: str,
    db_path: Optional[Path] = None,
    replace_existing: bool = True,
) -> int:
    """
    Persist multiple criteria for a completable entity.

    Args:
        criteria: List of Criterion Pydantic models
        completable_type: Type of owner entity
        completable_id: ID of owner entity
        db_path: Optional path to database file
        replace_existing: If True, delete existing criteria before inserting

    Returns:
        Number of criteria inserted
    """
    conn = get_connection(db_path=db_path)
    now = datetime.now(timezone.utc).isoformat()

    if replace_existing:
        conn.execute(
            "DELETE FROM criteria WHERE completable_type = ? AND completable_id = ?",
            (completable_type, completable_id)
        )

    for criterion in criteria:
        conn.execute(
            """
            INSERT OR REPLACE INTO criteria (
                id, completable_type, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                is_met, last_checked, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                criterion.id,
                completable_type,
                completable_id,
                criterion.description,
                1 if criterion.required else 0,
                criterion.blocks_transition_to.value,
                criterion.target.type.value,
                criterion.target.model_dump_json(),
                1 if criterion.is_met else (0 if criterion.is_met is False else None),
                criterion.target.last_checked.isoformat() if criterion.target.last_checked else None,
                now,
                now,
            )
        )

    conn.commit()
    return len(criteria)


def delete_criterion(
    criterion_id: str,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Delete a single criterion.

    Args:
        criterion_id: ID of criterion to delete
        db_path: Optional path to database file

    Returns:
        True if deleted, False if not found
    """
    conn = get_connection(db_path=db_path)
    cursor = conn.execute(
        "DELETE FROM criteria WHERE id = ?",
        (criterion_id,)
    )
    conn.commit()
    return cursor.rowcount > 0


def delete_criteria_for_completable(
    completable_type: str,
    completable_id: str,
    db_path: Optional[Path] = None,
) -> int:
    """
    Delete all criteria for a completable entity.

    Args:
        completable_type: Type of owner entity
        completable_id: ID of owner entity
        db_path: Optional path to database file

    Returns:
        Number of criteria deleted
    """
    conn = get_connection(db_path=db_path)
    cursor = conn.execute(
        "DELETE FROM criteria WHERE completable_type = ? AND completable_id = ?",
        (completable_type, completable_id)
    )
    conn.commit()
    return cursor.rowcount


def update_criterion_met_status(
    criterion_id: str,
    is_met: bool,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Update the is_met cached status for a criterion.

    Args:
        criterion_id: ID of criterion
        is_met: New met status
        db_path: Optional path to database file

    Returns:
        True if updated, False if not found
    """
    conn = get_connection(db_path=db_path)
    now = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        """
        UPDATE criteria
        SET is_met = ?, last_checked = ?, updated_at = ?
        WHERE id = ?
        """,
        (1 if is_met else 0, now, now, criterion_id)
    )
    conn.commit()
    return cursor.rowcount > 0


def bulk_update_criteria_met_status(
    updates: List[Dict[str, Any]],
    db_path: Optional[Path] = None,
) -> int:
    """
    Bulk update is_met status for multiple criteria.

    Args:
        updates: List of dicts with 'criterion_id' and 'is_met' keys
        db_path: Optional path to database file

    Returns:
        Number of criteria updated
    """
    conn = get_connection(db_path=db_path)
    now = datetime.now(timezone.utc).isoformat()
    updated = 0

    for update in updates:
        cursor = conn.execute(
            """
            UPDATE criteria
            SET is_met = ?, last_checked = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                1 if update['is_met'] else 0,
                now,
                now,
                update['criterion_id']
            )
        )
        updated += cursor.rowcount

    conn.commit()
    return updated
