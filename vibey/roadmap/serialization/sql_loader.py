"""
SQLite loader for roadmap objects.

Loads entities from SQLite database and converts them to Python dataclass objects.
This is the parallel to yaml_loader.py for the SQLite backend.

Schema Reference:
- Core tables: roadmaps, tracks, sprints, tasks
- Relationships: external_dependencies (polymorphic), entity_blocks, entity_blocked_by, entity_depends_on
- Quality: quality_gates, development_gates
- Supporting: deliverables, entity_deliverables, commits, entity_commits
- Roadmap-level: version_history, activity_log
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from ..models import (
    Roadmap,
    Track,
    Sprint,
    Task,
    VersionStrategy,
    Progress,
    TrackSummary,
    Dependency,
    Blocker,
    VersionHistoryEntry,
    ActivityLogEntry,
    Metadata,
    TrackProgress,
    SprintSummary,
    TrackDependency,
    TrackBlocker,
    QualityGate,
    TrackMetadata,
    SprintProgress,
    SprintBlocker,
    TaskSummary,
    DevelopmentGate,
    SprintMetadata,
    GateInfo,
    AuditResults,
    TaskDependency,
    TaskBlocker,
    Deliverable,
    GitCommit,
    TaskMetadata,
    Status,
    TaskStatus,
    Priority,
    TaskType,
    GateStatus,
    DependencyType,
    DependencyStatus,
    Complexity,
    DeliverableType,
    ActivityType,
    VersionBumpTrigger,
)
from ..database import get_connection


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse datetime from SQLite string or passthrough."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # SQLite stores as ISO 8601
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    return value


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert sqlite3.Row to dict."""
    if row is None:
        return {}
    return dict(row)


def _parse_json(value: Optional[str], default: Any = None) -> Any:
    """Parse JSON string, returning default if None or invalid."""
    if value is None:
        return default if default is not None else {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default if default is not None else {}
    return value



def load_roadmap(roadmap_id: str = "vibey-framework-v2") -> Roadmap:
    """
    Load a roadmap from SQLite database.

    Args:
        roadmap_id: ID of the roadmap to load

    Returns:
        Roadmap object

    Raises:
        ValueError: If roadmap doesn't exist
    """
    conn = get_connection()

    # Load main roadmap data
    row = conn.execute(
        "SELECT * FROM roadmaps WHERE id = ?",
        (roadmap_id,)
    ).fetchone()

    if row is None:
        raise ValueError(f"Roadmap '{roadmap_id}' not found")

    roadmap_data = _row_to_dict(row)

    # Parse version strategy from JSON
    vs_data = _parse_json(roadmap_data.get('version_strategy'), {
        'major_on': 'roadmap_milestone',
        'minor_on': 'track_completion',
        'patch_on': 'sprint_production_ready',
    })

    version_strategy = VersionStrategy(
        major_on=VersionBumpTrigger(vs_data.get('major_on', 'roadmap_milestone')),
        minor_on=VersionBumpTrigger(vs_data.get('minor_on', 'track_completion')),
        patch_on=VersionBumpTrigger(vs_data.get('patch_on', 'sprint_production_ready')),
    )

    # Load progress from computed view (if exists)
    progress = Progress(
        tracks_total=0, tracks_completed=0,
        sprints_total=0, sprints_completed=0,
        tasks_total=0, tasks_completed=0,
        completion_percent=0,
    )
    try:
        progress_row = conn.execute(
            "SELECT * FROM v_roadmap_progress WHERE roadmap_id = ?",
            (roadmap_id,)
        ).fetchone()
        if progress_row:
            prog_data = _row_to_dict(progress_row)
            progress = Progress(
                tracks_total=prog_data.get('tracks_total', 0),
                tracks_completed=prog_data.get('tracks_completed', 0),
                sprints_total=prog_data.get('sprints_total', 0),
                sprints_completed=prog_data.get('sprints_completed', 0),
                tasks_total=prog_data.get('tasks_total', 0),
                tasks_completed=prog_data.get('tasks_completed', 0),
                completion_percent=prog_data.get('completion_percent', 0),
            )
    except Exception:
        pass  # View may not exist

    # Load track summaries
    track_rows = conn.execute(
        "SELECT id, name, status, priority FROM tracks WHERE roadmap_id = ? ORDER BY id",
        (roadmap_id,)
    ).fetchall()

    tracks = [
        TrackSummary(
            id=t['id'],
            name=t['name'],
            status=Status(t['status']),
            priority=Priority(t['priority']) if t['priority'] else Priority.MEDIUM,
        )
        for t in track_rows
    ]

    # Load external dependencies (using polymorphic owner pattern)
    dep_rows = conn.execute(
        "SELECT * FROM external_dependencies WHERE owner_type = 'roadmap' AND owner_id = ? ORDER BY name",
        (roadmap_id,)
    ).fetchall()

    dependencies = [
        Dependency(
            type='external',
            name=d['name'],
            status=d['status'] or 'pending',
            required_for=d.get('description'),
        )
        for d in dep_rows
    ]

    # Load version history
    version_history = []
    try:
        vh_rows = conn.execute(
            "SELECT * FROM version_history WHERE roadmap_id = ? ORDER BY date DESC",
            (roadmap_id,)
        ).fetchall()
        version_history = [
            VersionHistoryEntry(
                version=vh['version'],
                date=_parse_datetime(vh['date']),
                milestone=vh['milestone'],
                git_tag=vh.get('git_tag'),
                description=vh.get('description'),
            )
            for vh in vh_rows
        ]
    except Exception:
        pass  # Table may not exist or be empty

    # Load activity log
    activity_log = []
    try:
        al_rows = conn.execute(
            "SELECT * FROM activity_log WHERE roadmap_id = ? ORDER BY timestamp DESC LIMIT 100",
            (roadmap_id,)
        ).fetchall()
        activity_log = [
            ActivityLogEntry(
                timestamp=_parse_datetime(al['timestamp']),
                type=ActivityType(al['type']),
                description=al['description'],
                context=al.get('context'),
            )
            for al in al_rows
        ]
    except Exception:
        pass

    # Parse metadata from JSON
    meta_data = _parse_json(roadmap_data.get('metadata'), {})

    metadata = Metadata(
        created_by=meta_data.get('created_by', 'unknown'),
        framework_version=meta_data.get('framework_version', '1.0.0'),
        schema_version=meta_data.get('schema_version', '2.1'),
        last_updated=_parse_datetime(meta_data.get('last_updated')),
        purpose=meta_data.get('purpose'),
        description=meta_data.get('description'),
    )

    # Handle missing start date for in-progress roadmaps
    status = Status(roadmap_data['status'])
    created = _parse_datetime(roadmap_data['created'])
    started = _parse_datetime(roadmap_data.get('started'))
    if status == Status.IN_PROGRESS and started is None:
        started = created  # Default to created date if in-progress but no start date

    # Create roadmap
    roadmap = Roadmap(
        id=roadmap_data['id'],
        name=roadmap_data['name'],
        version=roadmap_data['version'],
        version_strategy=version_strategy,
        status=status,
        blocked=bool(roadmap_data.get('blocked', False)),
        created=created,
        started=started,
        target_completion=_parse_datetime(roadmap_data.get('target_completion')),
        completed=_parse_datetime(roadmap_data.get('completed')),
        deployed=_parse_datetime(roadmap_data.get('deployed')),
        progress=progress,
        tracks=tracks,
        dependencies=dependencies,
        blocked_by=[],  # Roadmap-level blockers not stored in entity_blocks
        version_history=version_history,
        activity_log=activity_log,
        metadata=metadata,
        deployed_platforms=[],  # Not in current schema
        standards=[],  # Not in current schema
    )

    return roadmap


def load_track(track_id: str) -> Track:
    """
    Load a track from SQLite database.

    Args:
        track_id: ID of the track to load

    Returns:
        Track object
    """
    conn = get_connection()

    # Load main track data
    row = conn.execute(
        "SELECT * FROM tracks WHERE id = ?",
        (track_id,)
    ).fetchone()

    if row is None:
        raise ValueError(f"Track '{track_id}' not found")

    track_data = _row_to_dict(row)

    # Load progress from computed view
    progress = TrackProgress(
        sprints_total=0, sprints_completed=0,
        tasks_total=0, tasks_completed=0,
        completion_percent=0,
    )
    try:
        progress_row = conn.execute(
            "SELECT * FROM v_track_progress WHERE track_id = ?",
            (track_id,)
        ).fetchone()
        if progress_row:
            prog_data = _row_to_dict(progress_row)
            progress = TrackProgress(
                sprints_total=prog_data.get('sprints_total', 0),
                sprints_completed=prog_data.get('sprints_completed', 0),
                tasks_total=prog_data.get('tasks_total', 0),
                tasks_completed=prog_data.get('tasks_completed', 0),
                completion_percent=prog_data.get('completion_percent', 0),
            )
    except Exception:
        pass

    # Load sprint summaries
    sprint_rows = conn.execute(
        "SELECT id, name, status, started FROM sprints WHERE track_id = ? ORDER BY id",
        (track_id,)
    ).fetchall()

    sprints = []
    for s in sprint_rows:
        s_dict = _row_to_dict(s)
        # Get tasks count for this sprint
        task_count_row = conn.execute(
            "SELECT COUNT(*) as count FROM tasks WHERE sprint_id = ?",
            (s_dict['id'],)
        ).fetchone()
        tasks_count = task_count_row['count'] if task_count_row else 0

        sprints.append(SprintSummary(
            id=s_dict['id'],
            name=s_dict['name'],
            status=Status(s_dict['status']),
            estimated_duration=None,  # From metadata if needed
            tasks_count=tasks_count,
            started=_parse_datetime(s_dict.get('started')),
        ))

    # Load dependencies from entity_depends_on
    dep_rows = conn.execute(
        """SELECT * FROM entity_depends_on
           WHERE dependent_type = 'track' AND dependent_id = ?
           ORDER BY dependency_id""",
        (track_id,)
    ).fetchall()

    dependencies = []
    for d in dep_rows:
        d_dict = _row_to_dict(d)
        dependencies.append(TrackDependency(
            type=DependencyType(d_dict['dependency_type']),
            target_id=d_dict['dependency_id'],
            target_status='completed',
            reason=d_dict.get('reason', ''),
            optional=False,
        ))

    # Load blocks (what this track blocks) from entity_blocks
    blocks_rows = conn.execute(
        """SELECT * FROM entity_blocks
           WHERE blocker_type = 'track' AND blocker_id = ?
           ORDER BY blocked_id""",
        (track_id,)
    ).fetchall()

    blocks = []
    for b in blocks_rows:
        b_dict = _row_to_dict(b)
        blocks.append(TrackDependency(
            type=DependencyType(b_dict['blocked_type']),
            target_id=b_dict['blocked_id'],
            target_status='not_started',
            reason=b_dict.get('reason', ''),
        ))

    # Load dependencies (what blocks this track) from entity_blocked_by
    # Now includes business logic fields: required_status, blocks_transition_to
    blocker_rows = conn.execute(
        """SELECT * FROM entity_blocked_by
           WHERE blocked_type = 'track' AND blocked_id = ?
           ORDER BY blocker_id""",
        (track_id,)
    ).fetchall()

    blocked_by = []
    depends_on = []
    for b in blocker_rows:
        b_dict = _row_to_dict(b)
        # Create TrackBlocker for backward compatibility
        blocked_by.append(TrackBlocker(
            dependency_id=b_dict['blocker_id'],
            dependency_type=b_dict['blocker_type'],
            current_status='unknown',
            required_status=b_dict.get('required_status', 'completed'),
            blocking_since=None,
            estimated_resolution=None,
        ))
        # Create DependencyStatus with full business logic
        depends_on.append(DependencyStatus(
            blocker_id=b_dict['blocker_id'],
            blocker_type=b_dict['blocker_type'],
            required_status=b_dict.get('required_status', 'completed'),
            current_status='unknown',  # Would need status lookup
            blocks_transition_to=b_dict.get('blocks_transition_to', 'in_progress'),
            last_checked=None,
        ))

    # Load quality gates
    qg_rows = conn.execute(
        """SELECT * FROM quality_gates
           WHERE owner_type = 'track' AND owner_id = ?
           ORDER BY name""",
        (track_id,)
    ).fetchall()

    quality_gates = []
    for qg in qg_rows:
        qg_dict = _row_to_dict(qg)
        quality_gates.append(QualityGate(
            name=qg_dict['name'],
            threshold=qg_dict.get('threshold') or 0,
            blocking=bool(qg_dict.get('blocking', True)),
            status=GateStatus(qg_dict['status']) if qg_dict.get('status') else GateStatus.PENDING,
            description=qg_dict.get('description'),
            score=qg_dict.get('score'),
        ))

    # Parse metadata from JSON
    meta_data = _parse_json(track_data.get('metadata'), {})

    metadata = TrackMetadata(
        created_by=meta_data.get('created_by', 'unknown'),
        last_updated=_parse_datetime(meta_data.get('last_updated')),
        design_doc=meta_data.get('design_doc'),
        implementation_plan=meta_data.get('implementation_plan'),
        notes=meta_data.get('notes'),
    )

    # Handle missing dates for status validation
    status = Status(track_data['status'])
    created = _parse_datetime(track_data['created'])
    started = _parse_datetime(track_data.get('started'))
    completed = _parse_datetime(track_data.get('completed'))

    # Fix missing dates based on status
    if status == Status.IN_PROGRESS and started is None:
        started = created
    if status == Status.COMPLETED and completed is None:
        completed = started or created

    # Use stored blocked value from database
    blocked = bool(track_data.get('blocked', False))

    # depends_on is already populated from entity_blocked_by with full business logic
    # If blocked=True but no depends_on entries, create placeholder for validation
    if blocked and not depends_on:
        depends_on.append(DependencyStatus(
            blocker_id='unknown',
            blocker_type='external',
            required_status='resolved',
            current_status='pending',
            blocks_transition_to='in_progress',
            last_checked=None,
        ))

    # Create track
    track = Track(
        id=track_data['id'],
        name=track_data['name'],
        roadmap_id=track_data['roadmap_id'],
        status=status,
        blocked=blocked,  # Use stored value from database
        priority=Priority(track_data['priority']) if track_data.get('priority') else Priority.MEDIUM,
        created=created,
        started=started,
        completed=completed,
        estimated_duration=track_data.get('estimated_duration'),
        progress=progress,
        sprints=sprints,
        dependencies=dependencies,
        blocks=blocks,
        blocked_by=blocked_by,
        depends_on=depends_on,
        depended_on_by=[],
        quality_gates=quality_gates,
        assigned_agents=[],
        deliverables=[],
        strategic_value=[],
        commits=[],
        metadata=metadata,
        standards=[],
    )

    return track


def load_sprint(sprint_id: str) -> Sprint:
    """
    Load a sprint from SQLite database.

    Args:
        sprint_id: ID of the sprint to load

    Returns:
        Sprint object
    """
    conn = get_connection()

    # Load main sprint data
    row = conn.execute(
        "SELECT * FROM sprints WHERE id = ?",
        (sprint_id,)
    ).fetchone()

    if row is None:
        raise ValueError(f"Sprint '{sprint_id}' not found")

    sprint_data = _row_to_dict(row)

    # Load progress from computed view
    progress = SprintProgress(
        development_tasks_total=0, development_tasks_completed=0,
        completion_gate_tasks_total=0, completion_gate_tasks_completed=0,
        production_gate_tasks_total=0, production_gate_tasks_completed=0,
        tasks_total=0, tasks_completed=0,
        completion_percent=0,
    )
    try:
        progress_row = conn.execute(
            "SELECT * FROM v_sprint_progress WHERE sprint_id = ?",
            (sprint_id,)
        ).fetchone()
        if progress_row:
            prog_data = _row_to_dict(progress_row)
            progress = SprintProgress(
                development_tasks_total=prog_data.get('development_tasks_total', 0),
                development_tasks_completed=prog_data.get('development_tasks_completed', 0),
                completion_gate_tasks_total=prog_data.get('completion_gate_tasks_total', 0),
                completion_gate_tasks_completed=prog_data.get('completion_gate_tasks_completed', 0),
                production_gate_tasks_total=prog_data.get('production_gate_tasks_total', 0),
                production_gate_tasks_completed=prog_data.get('production_gate_tasks_completed', 0),
                tasks_total=prog_data.get('tasks_total', 0),
                tasks_completed=prog_data.get('tasks_completed', 0),
                completion_percent=prog_data.get('completion_percent', 0),
            )
    except Exception:
        pass

    # Load task summaries (including gate_info for gate tasks)
    task_rows = conn.execute(
        "SELECT id, title, status, task_type, gate_info FROM tasks WHERE sprint_id = ? ORDER BY id",
        (sprint_id,)
    ).fetchall()

    tasks = []
    for t in task_rows:
        task_type_str = t['task_type']
        gate_info = None

        # Parse gate_info from JSON if present
        gate_info_data = _parse_json(t['gate_info']) if t['gate_info'] else None
        if gate_info_data:
            gate_info = GateInfo(
                blocks_status=gate_info_data.get('blocks_status', 'completed'),
                threshold=gate_info_data.get('threshold', 0),
                is_blocking=gate_info_data.get('is_blocking', True),
                score=gate_info_data.get('score'),
            )
        elif task_type_str in ('completion_gate', 'production_gate'):
            # Gate tasks require gate_info - provide default if missing
            gate_info = GateInfo(
                blocks_status='completed',
                threshold=0,
                is_blocking=True,
                score=None,
            )

        tasks.append(TaskSummary(
            id=t['id'],
            title=t['title'],
            status=Status(t['status']),
            task_type=TaskType(task_type_str),
            gate_info=gate_info,
        ))

    # Load development gates
    # Note: development_gates table stores encoded gate info in name column
    # Format: "{type}:{target_id}:{target_status}"
    dev_gate_rows = conn.execute(
        """SELECT * FROM development_gates
           WHERE sprint_id = ?
           ORDER BY name""",
        (sprint_id,)
    ).fetchall()

    development_gates = []
    for dg in dev_gate_rows:
        dg_dict = _row_to_dict(dg)
        name = dg_dict.get('name', '')
        description = dg_dict.get('description', '')
        # Parse encoded name: "{type}:{target_id}:{target_status}"
        parts = name.split(':')
        if len(parts) >= 3:
            dep_type = parts[0]
            target_id = parts[1]
            target_status = parts[2]
        else:
            # Fallback for simple name format
            dep_type = 'sprint'
            target_id = name
            target_status = 'completed'
        development_gates.append(DevelopmentGate(
            type=DependencyType(dep_type) if dep_type in ('track', 'sprint', 'task') else DependencyType.SPRINT,
            target_id=target_id,
            target_status=target_status,
            reason=description,
        ))

    # Load blocks (what this sprint blocks)
    blocks_rows = conn.execute(
        """SELECT * FROM entity_blocks
           WHERE blocker_type = 'sprint' AND blocker_id = ?
           ORDER BY blocked_id""",
        (sprint_id,)
    ).fetchall()

    blocks = [
        DevelopmentGate(
            type=DependencyType(_row_to_dict(b)['blocked_type']),
            target_id=_row_to_dict(b)['blocked_id'],
            target_status='not_started',
            reason=_row_to_dict(b).get('reason', ''),
        )
        for b in blocks_rows
    ]

    # Load dependencies (what blocks this sprint) with business logic fields
    blocker_rows = conn.execute(
        """SELECT * FROM entity_blocked_by
           WHERE blocked_type = 'sprint' AND blocked_id = ?
           ORDER BY blocker_id""",
        (sprint_id,)
    ).fetchall()

    blocked_by = []
    depends_on_from_db = []
    for b in blocker_rows:
        b_dict = _row_to_dict(b)
        # Create SprintBlocker for backward compatibility
        blocked_by.append(SprintBlocker(
            dependency_id=b_dict['blocker_id'],
            dependency_type=b_dict['blocker_type'],
            current_status='unknown',
            required_status=b_dict.get('required_status', 'completed'),
            blocking_since=None,
            estimated_resolution=None,
        ))
        # Create DependencyStatus with full business logic
        depends_on_from_db.append(DependencyStatus(
            blocker_id=b_dict['blocker_id'],
            blocker_type=b_dict['blocker_type'],
            required_status=b_dict.get('required_status', 'completed'),
            current_status='unknown',
            blocks_transition_to=b_dict.get('blocks_transition_to', 'in_progress'),
            last_checked=None,
        ))

    # Load sprint-level quality gates
    qg_rows = conn.execute(
        """SELECT * FROM quality_gates
           WHERE owner_type = 'sprint' AND owner_id = ?
           ORDER BY name""",
        (sprint_id,)
    ).fetchall()

    quality_gates = []
    for qg in qg_rows:
        qg_dict = _row_to_dict(qg)
        quality_gates.append(QualityGate(
            name=qg_dict['name'],
            threshold=qg_dict.get('threshold') or 0,
            blocking=bool(qg_dict.get('blocking', True)),
            status=GateStatus(qg_dict['status']) if qg_dict.get('status') else GateStatus.PENDING,
            description=qg_dict.get('description'),
            score=qg_dict.get('score'),
        ))

    # Parse metadata from JSON
    meta_data = _parse_json(sprint_data.get('metadata'), {})

    metadata = SprintMetadata(
        last_updated=_parse_datetime(meta_data.get('last_updated')),
        estimated_duration=meta_data.get('estimated_duration'),
        actual_duration=meta_data.get('actual_duration'),
        estimated_tokens=meta_data.get('estimated_tokens'),
        actual_tokens=meta_data.get('actual_tokens'),
        agents_used=meta_data.get('agents_used'),
    )

    # Handle missing dates for status validation
    status = Status(sprint_data['status'])
    created = _parse_datetime(sprint_data['created'])
    started = _parse_datetime(sprint_data.get('started'))
    completed = _parse_datetime(sprint_data.get('completed'))
    production_ready_at = _parse_datetime(sprint_data.get('production_ready_at'))
    deployed_at = _parse_datetime(sprint_data.get('deployed_at'))

    # Fix missing dates based on status
    if status == Status.IN_PROGRESS and started is None:
        started = created
    if status == Status.COMPLETED and completed is None:
        completed = started or created
    if status == Status.PRODUCTION_READY and production_ready_at is None:
        production_ready_at = completed or started or created
    if status == Status.DEPLOYED and deployed_at is None:
        deployed_at = production_ready_at or completed or started or created

    # Use stored blocked value from database
    blocked = bool(sprint_data.get('blocked', False))

    # depends_on is already populated from entity_blocked_by with full business logic
    depends_on = depends_on_from_db
    # If blocked=True but no depends_on entries, create placeholder for validation
    if blocked and not depends_on:
        depends_on.append(DependencyStatus(
            blocker_id='unknown',
            blocker_type='external',
            required_status='resolved',
            current_status='pending',
            blocks_transition_to='in_progress',
            last_checked=None,
        ))

    # Create sprint
    sprint = Sprint(
        id=sprint_data['id'],
        name=sprint_data['name'],
        track_id=sprint_data['track_id'],
        roadmap_id=sprint_data.get('roadmap_id', 'vibey-framework-v2'),
        status=status,
        blocked=blocked,  # Use stored value from database
        blocked_reason=sprint_data.get('blocked_reason'),
        created=created,
        started=started,
        completion_gate_check_at=_parse_datetime(sprint_data.get('completion_gate_check_at')),
        completed=completed,
        production_gate_check_at=_parse_datetime(sprint_data.get('production_gate_check_at')),
        production_ready_at=production_ready_at,
        deployed_at=deployed_at,
        progress=progress,
        tasks=tasks,
        development_gates=development_gates,
        blocks=blocks,
        blocked_by=blocked_by,
        depends_on=depends_on,
        depended_on_by=[],
        plan_file=sprint_data.get('plan_file'),
        deliverables=[],
        commits=[],
        metadata=metadata,
        standards=[],
        quality_gates=quality_gates,
    )

    return sprint


def load_task(task_id: str) -> Task:
    """
    Load a single task from SQLite database.

    Args:
        task_id: ID of the task to load

    Returns:
        Task object
    """
    tasks = load_tasks_by_ids([task_id])
    if len(tasks) != 1:
        raise ValueError(f"Task '{task_id}' not found")
    return tasks[0]


def load_tasks_by_ids(task_ids: List[str]) -> List[Task]:
    """
    Load multiple tasks by their IDs.

    Args:
        task_ids: List of task IDs to load

    Returns:
        List of Task objects
    """
    if not task_ids:
        return []

    conn = get_connection()
    placeholders = ','.join('?' * len(task_ids))

    task_rows = conn.execute(
        f"SELECT * FROM tasks WHERE id IN ({placeholders}) ORDER BY id",
        task_ids
    ).fetchall()

    return [_load_task_from_row(conn, row) for row in task_rows]


def load_tasks_by_sprint(sprint_id: str) -> List[Task]:
    """
    Load all tasks for a sprint.

    Args:
        sprint_id: ID of the sprint

    Returns:
        List of Task objects
    """
    conn = get_connection()

    task_rows = conn.execute(
        "SELECT * FROM tasks WHERE sprint_id = ? ORDER BY id",
        (sprint_id,)
    ).fetchall()

    return [_load_task_from_row(conn, row) for row in task_rows]


def load_tasks_by_track(track_id: str) -> List[Task]:
    """
    Load all tasks for a track.

    Args:
        track_id: ID of the track

    Returns:
        List of Task objects
    """
    conn = get_connection()

    task_rows = conn.execute(
        "SELECT * FROM tasks WHERE track_id = ? ORDER BY sprint_id, id",
        (track_id,)
    ).fetchall()

    return [_load_task_from_row(conn, row) for row in task_rows]


def load_all_tasks(roadmap_id: str = "vibey-framework-v2") -> List[Task]:
    """
    Load all tasks for a roadmap.

    Args:
        roadmap_id: ID of the roadmap

    Returns:
        List of Task objects
    """
    conn = get_connection()

    task_rows = conn.execute(
        "SELECT * FROM tasks WHERE roadmap_id = ? ORDER BY track_id, sprint_id, id",
        (roadmap_id,)
    ).fetchall()

    return [_load_task_from_row(conn, row) for row in task_rows]


def _load_task_from_row(conn, row) -> Task:
    """Helper to load a single task from a database row."""
    task_data = _row_to_dict(row)
    task_id = task_data['id']

    # Parse gate_info from JSON if present
    gate_info = None
    gate_info_data = _parse_json(task_data.get('gate_info'))
    task_type_str = task_data['task_type']

    if gate_info_data:
        gate_info = GateInfo(
            blocks_status=gate_info_data.get('blocks_status', 'completed'),
            threshold=gate_info_data.get('threshold', 0),
            is_blocking=gate_info_data.get('is_blocking', True),
            score=gate_info_data.get('score'),
        )
    elif task_type_str in ('completion_gate', 'production_gate'):
        # Gate tasks require gate_info - provide default if missing
        gate_info = GateInfo(
            blocks_status='completed',
            threshold=0,
            is_blocking=True,
            score=None,
        )

    # Parse audit_results from JSON if present
    audit_results = None
    audit_data = _parse_json(task_data.get('audit_results'))
    if audit_data:
        audit_results = AuditResults(
            issues_found=audit_data.get('issues_found', 0),
            issues_fixed=audit_data.get('issues_fixed', 0),
            recommendations=audit_data.get('recommendations', []),
        )

    # Load dependencies from entity_depends_on
    dep_rows = conn.execute(
        """SELECT * FROM entity_depends_on
           WHERE dependent_type = 'task' AND dependent_id = ?
           ORDER BY dependency_id""",
        (task_id,)
    ).fetchall()

    dependencies = []
    for d in dep_rows:
        d_dict = _row_to_dict(d)
        dependencies.append(TaskDependency(
            type=DependencyType(d_dict['dependency_type']),
            target_id=d_dict['dependency_id'],
            target_status='completed',
            reason=d_dict.get('reason', ''),
        ))

    # Load blocks (what this task blocks)
    blocks_rows = conn.execute(
        """SELECT * FROM entity_blocks
           WHERE blocker_type = 'task' AND blocker_id = ?
           ORDER BY blocked_id""",
        (task_id,)
    ).fetchall()

    blocks = []
    for b in blocks_rows:
        b_dict = _row_to_dict(b)
        blocks.append(TaskDependency(
            type=DependencyType(b_dict['blocked_type']),
            target_id=b_dict['blocked_id'],
            target_status='not_started',
            reason=b_dict.get('reason', ''),
        ))

    # Load dependencies (what blocks this task) with business logic fields
    blocker_rows = conn.execute(
        """SELECT * FROM entity_blocked_by
           WHERE blocked_type = 'task' AND blocked_id = ?
           ORDER BY blocker_id""",
        (task_id,)
    ).fetchall()

    blocked_by = []
    depends_on = []
    for b in blocker_rows:
        b_dict = _row_to_dict(b)
        # Create TaskBlocker for backward compatibility
        blocked_by.append(TaskBlocker(
            dependency_id=b_dict['blocker_id'],
            dependency_type=b_dict['blocker_type'],
            current_status='unknown',
            required_status=b_dict.get('required_status', 'completed'),
            blocking_since=None,
            estimated_resolution=None,
        ))
        # Create DependencyStatus with full business logic
        depends_on.append(DependencyStatus(
            blocker_id=b_dict['blocker_id'],
            blocker_type=b_dict['blocker_type'],
            required_status=b_dict.get('required_status', 'completed'),
            current_status='unknown',
            blocks_transition_to=b_dict.get('blocks_transition_to', 'in_progress'),
            last_checked=None,
        ))

    # Load deliverables
    # Note: deliverables table stores type in description column, paths in artifact_path
    deliverable_rows = conn.execute(
        """SELECT d.* FROM deliverables d
           JOIN entity_deliverables ed ON d.id = ed.deliverable_id
           WHERE ed.owner_type = 'task' AND ed.owner_id = ?
           ORDER BY d.description""",
        (task_id,)
    ).fetchall()

    deliverables = []
    for d in deliverable_rows:
        d_dict = _row_to_dict(d)
        # Type is stored in description, paths in artifact_path
        type_str = d_dict.get('description', 'code')
        try:
            del_type = DeliverableType(type_str)
        except ValueError:
            del_type = DeliverableType.OTHER
        paths = d_dict.get('artifact_path', '').split('|') if d_dict.get('artifact_path') else []
        deliverables.append(Deliverable(
            type=del_type,
            paths=paths,
        ))

    # Parse metadata from JSON
    meta_data = _parse_json(task_data.get('metadata'), {})

    metadata = TaskMetadata(
        last_updated=_parse_datetime(meta_data.get('last_updated')),
        token_efficiency=meta_data.get('token_efficiency'),
        duration_hours=meta_data.get('duration_hours'),
    )

    # Handle missing dates for status validation
    status = TaskStatus(task_data['status'])
    created = _parse_datetime(task_data['created'])
    started = _parse_datetime(task_data.get('started'))
    completed = _parse_datetime(task_data.get('completed'))

    # Fix missing dates based on status
    if status == TaskStatus.IN_PROGRESS and started is None:
        started = created
    if status == TaskStatus.COMPLETED and completed is None:
        completed = started or created

    # Use stored blocked value from database
    blocked = bool(task_data.get('blocked', False))

    # depends_on is already populated from entity_blocked_by with full business logic
    # If blocked=True but no depends_on entries, create placeholder for validation
    if blocked and not depends_on:
        depends_on.append(DependencyStatus(
            blocker_id='unknown',
            blocker_type='external',
            required_status='resolved',
            current_status='pending',
            blocks_transition_to='in_progress',
            last_checked=None,
        ))

    # Create task
    task = Task(
        id=task_data['id'],
        sprint_id=task_data['sprint_id'],
        track_id=task_data['track_id'],
        roadmap_id=task_data.get('roadmap_id', 'vibey-framework-v2'),
        task_type=TaskType(task_data['task_type']),
        title=task_data['title'],
        description=task_data.get('description', ''),
        status=status,
        blocked=blocked,  # Use stored value from database
        created=created,
        started=started,
        completed=completed,
        assigned_agent=task_data.get('assigned_agent'),
        priority=Priority(task_data['priority']) if task_data.get('priority') else Priority.MEDIUM,
        phase_label=task_data.get('phase_label'),
        estimated_tokens=task_data.get('estimated_tokens') or 1,
        actual_tokens=task_data.get('actual_tokens'),
        complexity=Complexity(task_data['complexity']) if task_data.get('complexity') else Complexity.MEDIUM,
        gate_info=gate_info,
        audit_results=audit_results,
        dependencies=dependencies,
        blocks=blocks,
        blocked_by=blocked_by,
        depends_on=depends_on,
        depended_on_by=[],
        deliverables=deliverables,
        commits=[],
        metadata=metadata,
    )

    return task


# =============================================================================
# AUDIT TRAIL LOADER
# =============================================================================

def load_audit_trail(limit: Optional[int] = None) -> List[dict]:
    """
    Load audit trail entries from SQLite database.

    Args:
        limit: Maximum number of entries to load (None = all)

    Returns:
        List of audit trail entry dictionaries
    """
    conn = get_connection()

    query = "SELECT * FROM audit_trail ORDER BY timestamp ASC"
    if limit:
        query += f" LIMIT {limit}"

    rows = conn.execute(query).fetchall()

    entries = []
    for row in rows:
        entry = _row_to_dict(row)
        entries.append({
            'timestamp': entry['timestamp'],
            'object_type': entry['object_type'],
            'object_id': entry['object_id'],
            'field': entry['field'],
            'old_value': entry['old_value'],
            'new_value': entry['new_value'],
            'changed_by': entry['changed_by'],
            'reason': entry['reason'],
            'commit': entry.get('commit_sha'),
            'source': entry['source'],
        })

    return entries


def load_audit_trail_for_object(object_id: str) -> List[dict]:
    """
    Load audit trail entries for a specific object.

    Args:
        object_id: ID of the track/sprint/task

    Returns:
        List of audit trail entry dictionaries
    """
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM audit_trail WHERE object_id = ? ORDER BY timestamp ASC",
        (object_id,)
    ).fetchall()

    entries = []
    for row in rows:
        entry = _row_to_dict(row)
        entries.append({
            'timestamp': entry['timestamp'],
            'object_type': entry['object_type'],
            'object_id': entry['object_id'],
            'field': entry['field'],
            'old_value': entry['old_value'],
            'new_value': entry['new_value'],
            'changed_by': entry['changed_by'],
            'reason': entry['reason'],
            'commit': entry.get('commit_sha'),
            'source': entry['source'],
        })

    return entries


def load_audit_trail_field_history(object_id: str, field: str) -> List[dict]:
    """
    Load audit trail entries for a specific field on an object.

    Args:
        object_id: ID of the track/sprint/task
        field: Field name to get history for

    Returns:
        List of audit trail entry dictionaries
    """
    conn = get_connection()

    rows = conn.execute(
        "SELECT * FROM audit_trail WHERE object_id = ? AND field = ? ORDER BY timestamp ASC",
        (object_id, field)
    ).fetchall()

    entries = []
    for row in rows:
        entry = _row_to_dict(row)
        entries.append({
            'timestamp': entry['timestamp'],
            'object_type': entry['object_type'],
            'object_id': entry['object_id'],
            'field': entry['field'],
            'old_value': entry['old_value'],
            'new_value': entry['new_value'],
            'changed_by': entry['changed_by'],
            'reason': entry['reason'],
            'commit': entry.get('commit_sha'),
            'source': entry['source'],
        })

    return entries


# =============================================================================
# V2 TICKET LOADERS (Unified Schema)
# =============================================================================
# These functions load from the unified 'tickets' table and return
# Pydantic ticket models (TaskTicket, SprintTicket, TrackTicket, RoadmapTicket).

from ..database.connection import get_session, session_scope
from ..models.ticket.orm import (
    TicketORM,
    RoadmapTicketORM,
    TrackTicketORM,
    SprintTicketORM,
    TaskTicketORM,
    CriterionORM,
)
from ..models.ticket.domain import (
    TaskTicket,
    SprintTicket,
    TrackTicket,
    RoadmapTicket,
)
from ..database.schema import has_unified_schema


def load_task_ticket(task_id: str) -> Optional[TaskTicket]:
    """
    Load a task from the unified tickets table.

    Args:
        task_id: ID of the task to load

    Returns:
        TaskTicket Pydantic model, or None if not found

    Raises:
        RuntimeError: If unified schema is not present
    """
    with session_scope() as session:
        orm_task = session.query(TaskTicketORM).get(task_id)
        if orm_task is None:
            return None
        return orm_task.to_pydantic()


def load_sprint_ticket(sprint_id: str) -> Optional[SprintTicket]:
    """
    Load a sprint from the unified tickets table.

    Args:
        sprint_id: ID of the sprint to load

    Returns:
        SprintTicket Pydantic model, or None if not found
    """
    with session_scope() as session:
        orm_sprint = session.query(SprintTicketORM).get(sprint_id)
        if orm_sprint is None:
            return None
        return orm_sprint.to_pydantic()


def load_track_ticket(track_id: str) -> Optional[TrackTicket]:
    """
    Load a track from the unified tickets table.

    Args:
        track_id: ID of the track to load

    Returns:
        TrackTicket Pydantic model, or None if not found
    """
    with session_scope() as session:
        orm_track = session.query(TrackTicketORM).get(track_id)
        if orm_track is None:
            return None
        return orm_track.to_pydantic()


def load_roadmap_ticket(roadmap_id: str = "vibey-framework-v2") -> Optional[RoadmapTicket]:
    """
    Load a roadmap from the unified tickets table.

    Args:
        roadmap_id: ID of the roadmap to load

    Returns:
        RoadmapTicket Pydantic model, or None if not found
    """
    with session_scope() as session:
        orm_roadmap = session.query(RoadmapTicketORM).get(roadmap_id)
        if orm_roadmap is None:
            return None
        return orm_roadmap.to_pydantic()


def load_task_ticket_with_ancestors(task_id: str) -> Optional[TaskTicket]:
    """
    Load a task with its ancestor chain (sprint, track, roadmap).

    This eagerly loads the parent hierarchy so that inherited properties
    like standards_effective work correctly.

    Args:
        task_id: ID of the task to load

    Returns:
        TaskTicket with ancestors loaded, or None if not found
    """
    with session_scope() as session:
        # Query with eager loading of parent relationships
        orm_task = session.query(TaskTicketORM).get(task_id)
        if orm_task is None:
            return None

        # Walk up the hierarchy to trigger lazy loading within session
        current = orm_task
        while current.parent is not None:
            current = current.parent

        return orm_task.to_pydantic()


def load_sprint_ticket_with_children(sprint_id: str) -> Optional[SprintTicket]:
    """
    Load a sprint with all its child tasks.

    This eagerly loads children so that aggregated properties
    like commits_aggregated work correctly.

    Args:
        sprint_id: ID of the sprint to load

    Returns:
        SprintTicket with children loaded, or None if not found
    """
    with session_scope() as session:
        orm_sprint = session.query(SprintTicketORM).get(sprint_id)
        if orm_sprint is None:
            return None

        # Access children to trigger lazy loading within session
        _ = list(orm_sprint.children)

        return orm_sprint.to_pydantic()


def load_tickets_by_type(ticket_type: str) -> List:
    """
    Load all tickets of a specific type.

    Args:
        ticket_type: Type of tickets to load ('roadmap', 'track', 'sprint', 'task')

    Returns:
        List of Pydantic ticket models
    """
    type_map = {
        'roadmap': RoadmapTicketORM,
        'track': TrackTicketORM,
        'sprint': SprintTicketORM,
        'task': TaskTicketORM,
    }

    if ticket_type not in type_map:
        raise ValueError(f"Unknown ticket type: {ticket_type}")

    orm_class = type_map[ticket_type]

    with session_scope() as session:
        orm_tickets = session.query(orm_class).all()
        return [t.to_pydantic() for t in orm_tickets]


def load_tickets_by_parent(parent_id: str) -> List:
    """
    Load all child tickets for a parent.

    Args:
        parent_id: ID of the parent ticket

    Returns:
        List of Pydantic ticket models (children)
    """
    with session_scope() as session:
        orm_children = session.query(TicketORM).filter(
            TicketORM.parent_id == parent_id
        ).all()
        return [c.to_pydantic() for c in orm_children]


def load_tasks_by_sprint_ticket(sprint_id: str) -> List[TaskTicket]:
    """
    Load all task tickets for a sprint.

    Args:
        sprint_id: ID of the sprint

    Returns:
        List of TaskTicket models
    """
    with session_scope() as session:
        orm_tasks = session.query(TaskTicketORM).filter(
            TaskTicketORM.parent_id == sprint_id
        ).order_by(TaskTicketORM.sequence).all()
        return [t.to_pydantic() for t in orm_tasks]


def load_sprints_by_track_ticket(track_id: str) -> List[SprintTicket]:
    """
    Load all sprint tickets for a track.

    Args:
        track_id: ID of the track

    Returns:
        List of SprintTicket models
    """
    with session_scope() as session:
        orm_sprints = session.query(SprintTicketORM).filter(
            SprintTicketORM.parent_id == track_id
        ).order_by(SprintTicketORM.sequence).all()
        return [s.to_pydantic() for s in orm_sprints]


def load_tracks_by_roadmap_ticket(roadmap_id: str = "vibey-framework-v2") -> List[TrackTicket]:
    """
    Load all track tickets for a roadmap.

    Args:
        roadmap_id: ID of the roadmap

    Returns:
        List of TrackTicket models
    """
    with session_scope() as session:
        orm_tracks = session.query(TrackTicketORM).filter(
            TrackTicketORM.parent_id == roadmap_id
        ).order_by(TrackTicketORM.sequence).all()
        return [t.to_pydantic() for t in orm_tracks]
