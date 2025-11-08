"""
YAML loader for roadmap objects.

Loads YAML files and converts them to Python dataclass objects.
"""

from datetime import datetime
from pathlib import Path
from typing import Union, Dict, Any, List

import yaml

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
    Complexity,
    DeliverableType,
    ActivityType,
    VersionBumpTrigger,
)


def _parse_datetime(value: Union[str, datetime, None]) -> Union[datetime, None]:
    """Parse datetime from string or passthrough."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Try ISO 8601 format
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value


def _map_complexity(value: str) -> str:
    """Map old complexity values to new enum values (backward compatibility)."""
    mapping = {
        'low': 'simple',
        'high': 'complex',
        # 'medium' stays the same
    }
    return mapping.get(value, value)


def load_roadmap(file_path: Union[str, Path]) -> Roadmap:
    """
    Load a roadmap from YAML file.

    Args:
        file_path: Path to roadmap.yaml

    Returns:
        Roadmap object

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValueError: If data is invalid
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'roadmap' not in data:
        raise ValueError("Missing 'roadmap' root key")

    roadmap_data = data['roadmap']

    # Parse version strategy
    vs_data = roadmap_data['version_strategy']
    version_strategy = VersionStrategy(
        major_on=VersionBumpTrigger(vs_data['major_on']),
        minor_on=VersionBumpTrigger(vs_data['minor_on']),
        patch_on=VersionBumpTrigger(vs_data['patch_on']),
    )

    # Parse progress
    prog_data = roadmap_data['progress']
    progress = Progress(
        tracks_total=prog_data['tracks_total'],
        tracks_completed=prog_data['tracks_completed'],
        sprints_total=prog_data['sprints_total'],
        sprints_completed=prog_data['sprints_completed'],
        tasks_total=prog_data['tasks_total'],
        tasks_completed=prog_data['tasks_completed'],
        completion_percent=prog_data['completion_percent'],
    )

    # Parse tracks
    tracks = [
        TrackSummary(
            id=t['id'],
            name=t['name'],
            status=Status(t['status']),
            priority=Priority(t['priority']),
        )
        for t in roadmap_data['tracks']
    ]

    # Parse dependencies
    dependencies = [
        Dependency(
            type=d['type'],
            name=d['name'],
            status=d['status'],
            required_for=d.get('required_for'),
        )
        for d in roadmap_data.get('dependencies', [])
    ]

    # Parse blockers
    blocked_by = [
        Blocker(
            dependency_id=b['dependency_id'],
            dependency_type=b['dependency_type'],
            current_status=b['current_status'],
            required_status=b['required_status'],
            blocking_since=_parse_datetime(b['blocking_since']),
            estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
        )
        for b in roadmap_data.get('blocked_by', [])
    ]

    # Parse version history
    version_history = [
        VersionHistoryEntry(
            version=vh['version'],
            date=_parse_datetime(vh['date']),
            milestone=vh['milestone'],
            git_tag=vh.get('git_tag'),
            description=vh.get('description'),
        )
        for vh in roadmap_data.get('version_history', [])
    ]

    # Parse activity log
    activity_log = [
        ActivityLogEntry(
            timestamp=_parse_datetime(al['timestamp']),
            type=ActivityType(al['type']),
            description=al['description'],
            context=al.get('context'),
        )
        for al in roadmap_data.get('activity_log', [])
    ]

    # Parse metadata
    meta_data = roadmap_data['metadata']
    metadata = Metadata(
        created_by=meta_data['created_by'],
        framework_version=meta_data['framework_version'],
        schema_version=meta_data['schema_version'],
        last_updated=_parse_datetime(meta_data['last_updated']),
        purpose=meta_data.get('purpose'),
        description=meta_data.get('description'),
    )

    # Create roadmap
    roadmap = Roadmap(
        id=roadmap_data['id'],
        name=roadmap_data['name'],
        version=roadmap_data['version'],
        version_strategy=version_strategy,
        status=Status(roadmap_data['status']),
        blocked=roadmap_data['blocked'],
        created=_parse_datetime(roadmap_data['created']),
        started=_parse_datetime(roadmap_data.get('started')),
        target_completion=_parse_datetime(roadmap_data.get('target_completion')),
        completed=_parse_datetime(roadmap_data.get('completed')),
        deployed=_parse_datetime(roadmap_data.get('deployed')),
        progress=progress,
        tracks=tracks,
        dependencies=dependencies,
        blocked_by=blocked_by,
        version_history=version_history,
        activity_log=activity_log,
        metadata=metadata,
    )

    return roadmap


def load_track(file_path: Union[str, Path]) -> Track:
    """
    Load a track from YAML file.

    Args:
        file_path: Path to track YAML file

    Returns:
        Track object
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'track' not in data:
        raise ValueError("Missing 'track' root key")

    track_data = data['track']

    # Parse progress
    prog_data = track_data['progress']
    progress = TrackProgress(
        sprints_total=prog_data['sprints_total'],
        sprints_completed=prog_data['sprints_completed'],
        tasks_total=prog_data['tasks_total'],
        tasks_completed=prog_data['tasks_completed'],
        completion_percent=prog_data['completion_percent'],
    )

    # Parse sprints
    sprints = [
        SprintSummary(
            id=s['id'],
            name=s['name'],
            status=Status(s['status']),
            estimated_duration=s.get('estimated_duration'),
            tasks_count=s.get('tasks_count'),
            started=_parse_datetime(s.get('started')),
        )
        for s in track_data['sprints']
    ]

    # Parse dependencies
    dependencies = [
        TrackDependency(
            type=DependencyType(d['type']),
            target_id=d['target_id'],
            target_status=d['target_status'],
            reason=d['reason'],
            optional=d.get('optional', False),
        )
        for d in track_data.get('dependencies', [])
    ]

    # Parse blocks
    blocks = [
        TrackDependency(
            type=DependencyType(b['type']),
            target_id=b['target_id'],
            target_status=b['at_status'],
            reason=b['reason'],
        )
        for b in track_data.get('blocks', [])
    ]

    # Parse blockers
    blocked_by = [
        TrackBlocker(
            dependency_id=b['dependency_id'],
            dependency_type=b['dependency_type'],
            current_status=b['current_status'],
            required_status=b['required_status'],
            blocking_since=_parse_datetime(b['blocking_since']),
            estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
        )
        for b in track_data.get('blocked_by', [])
    ]

    # Parse quality gates
    quality_gates = [
        QualityGate(
            name=qg['name'],
            threshold=qg['threshold'],
            blocking=qg['blocking'],
            status=GateStatus(qg['status']),
            description=qg.get('description'),
            score=qg.get('score'),
        )
        for qg in track_data.get('quality_gates', [])
    ]

    # Parse metadata
    meta_data = track_data['metadata']
    metadata = TrackMetadata(
        created_by=meta_data['created_by'],
        last_updated=_parse_datetime(meta_data['last_updated']),
        design_doc=meta_data.get('design_doc'),
        implementation_plan=meta_data.get('implementation_plan'),
        notes=meta_data.get('notes'),
    )

    # Create track
    track = Track(
        id=track_data['id'],
        name=track_data['name'],
        roadmap_id=track_data['roadmap_id'],
        status=Status(track_data['status']),
        blocked=track_data['blocked'],
        priority=Priority(track_data['priority']),
        created=_parse_datetime(track_data['created']),
        started=_parse_datetime(track_data.get('started')),
        completed=_parse_datetime(track_data.get('completed')),
        estimated_duration=track_data.get('estimated_duration'),
        progress=progress,
        sprints=sprints,
        dependencies=dependencies,
        blocks=blocks,
        blocked_by=blocked_by,
        quality_gates=quality_gates,
        assigned_agents=track_data.get('assigned_agents', []),
        deliverables=track_data.get('deliverables', []),
        strategic_value=track_data.get('strategic_value', []),
        metadata=metadata,
    )

    return track


def load_sprint(file_path: Union[str, Path]) -> Sprint:
    """
    Load a sprint from YAML file.

    Args:
        file_path: Path to sprint YAML file

    Returns:
        Sprint object
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'sprint' not in data:
        raise ValueError("Missing 'sprint' root key")

    sprint_data = data['sprint']

    # Parse progress (backward compatible with old format)
    prog_data = sprint_data['progress']

    # For old format (no gate breakdown), assume all tasks are development tasks
    tasks_total = prog_data['tasks_total']
    tasks_completed = prog_data['tasks_completed']

    progress = SprintProgress(
        development_tasks_total=prog_data.get('development_tasks_total', tasks_total),
        development_tasks_completed=prog_data.get('development_tasks_completed', tasks_completed),
        completion_gate_tasks_total=prog_data.get('completion_gate_tasks_total', 0),
        completion_gate_tasks_completed=prog_data.get('completion_gate_tasks_completed', 0),
        production_gate_tasks_total=prog_data.get('production_gate_tasks_total', 0),
        production_gate_tasks_completed=prog_data.get('production_gate_tasks_completed', 0),
        tasks_total=tasks_total,
        tasks_completed=tasks_completed,
        completion_percent=prog_data['completion_percent'],
    )

    # Parse tasks (backward compatible - old format uses task_summaries dict)
    if 'tasks' in sprint_data:
        # New format: list of tasks
        tasks = [
            TaskSummary(
                id=t['id'],
                title=t['title'],
                status=Status(t['status']),
                task_type=TaskType(t['task_type']),
                gate_info=t.get('gate_info'),
            )
            for t in sprint_data['tasks']
        ]
    else:
        # Old format: task_summaries dict - create minimal TaskSummary objects
        tasks = []
        if 'task_summaries' in sprint_data:
            for task_id, task_data in sprint_data['task_summaries'].items():
                tasks.append(TaskSummary(
                    id=task_id,
                    title=task_data.get('summary', 'Unknown'),
                    status=Status.COMPLETED,  # Old format doesn't track status
                    task_type=TaskType.DEVELOPMENT,  # Assume development
                    gate_info=None,
                ))

    # Parse development gates
    development_gates = [
        DevelopmentGate(
            type=DependencyType(dg['type']),
            target_id=dg['target_id'],
            target_status=dg['target_status'],
            reason=dg['reason'],
        )
        for dg in sprint_data.get('development_gates', [])
    ]

    # Parse blocks
    blocks = [
        DevelopmentGate(
            type=DependencyType(b['type']),
            target_id=b['target_id'],
            target_status=b['at_status'],
            reason=b['reason'],
        )
        for b in sprint_data.get('blocks', [])
    ]

    # Parse blockers
    blocked_by = [
        SprintBlocker(
            dependency_id=b['dependency_id'],
            dependency_type=b['dependency_type'],
            current_status=b['current_status'],
            required_status=b['required_status'],
            blocking_since=_parse_datetime(b['blocking_since']),
            estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
        )
        for b in sprint_data.get('blocked_by', [])
    ]

    # Parse metadata
    meta_data = sprint_data['metadata']
    metadata = SprintMetadata(
        last_updated=_parse_datetime(meta_data['last_updated']),
        estimated_duration=meta_data.get('estimated_duration'),
        actual_duration=meta_data.get('actual_duration'),
        estimated_tokens=meta_data.get('estimated_tokens'),
        actual_tokens=meta_data.get('actual_tokens'),
        agents_used=meta_data.get('agents_used'),
    )

    # Create sprint (backward compatible - many fields optional in old format)
    sprint = Sprint(
        id=sprint_data['id'],
        name=sprint_data['name'],
        track_id=sprint_data['track_id'],
        roadmap_id=sprint_data['roadmap_id'],
        status=Status(sprint_data['status']),
        blocked=sprint_data.get('blocked', False),
        created=_parse_datetime(sprint_data.get('created', datetime.now())),
        started=_parse_datetime(sprint_data.get('started')),
        completion_gate_check_at=_parse_datetime(sprint_data.get('completion_gate_check_at')),
        completed=_parse_datetime(sprint_data.get('completed')),
        production_gate_check_at=_parse_datetime(sprint_data.get('production_gate_check_at')),
        production_ready_at=_parse_datetime(sprint_data.get('production_ready_at')),
        deployed_at=_parse_datetime(sprint_data.get('deployed_at')),
        progress=progress,
        tasks=tasks,
        development_gates=development_gates,
        blocks=blocks,
        blocked_by=blocked_by,
        plan_file=sprint_data.get('plan_file'),
        deliverables=sprint_data.get('deliverables', []),
        metadata=metadata,
    )

    return sprint


def load_tasks(file_path: Union[str, Path]) -> List[Task]:
    """
    Load tasks from YAML file.

    Args:
        file_path: Path to tasks YAML file

    Returns:
        List of Task objects
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    # Tasks can be a list or dict with 'tasks' key
    if isinstance(data, list):
        tasks_data = data
    elif 'tasks' in data:
        tasks_data = data['tasks']
    else:
        raise ValueError("Invalid tasks file format")

    tasks = []
    for task_data in tasks_data:
        # Parse gate info if present
        gate_info = None
        if 'gate_info' in task_data and task_data['gate_info']:
            gi_data = task_data['gate_info']
            gate_info = GateInfo(
                blocks_status=gi_data['blocks_status'],
                threshold=gi_data['threshold'],
                is_blocking=gi_data['is_blocking'],
                score=gi_data.get('score'),
            )

        # Parse audit results if present
        audit_results = None
        if 'audit_results' in task_data and task_data['audit_results']:
            ar_data = task_data['audit_results']
            audit_results = AuditResults(
                issues_found=ar_data['issues_found'],
                issues_fixed=ar_data['issues_fixed'],
                recommendations=ar_data.get('recommendations', []),
            )

        # Parse dependencies (backward compatible - old format uses 'at_status')
        dependencies = [
            TaskDependency(
                type=DependencyType(d['type']),
                target_id=d['target_id'],
                target_status=d.get('target_status', d.get('at_status', 'completed')),
                reason=d.get('reason', ''),
            )
            for d in task_data.get('dependencies', [])
        ]

        # Parse blocks
        blocks = [
            TaskDependency(
                type=DependencyType(b['type']),
                target_id=b['target_id'],
                target_status=b['at_status'],
                reason=b['reason'],
            )
            for b in task_data.get('blocks', [])
        ]

        # Parse blockers
        blocked_by = [
            TaskBlocker(
                dependency_id=b['dependency_id'],
                dependency_type=b['dependency_type'],
                current_status=b['current_status'],
                required_status=b['required_status'],
                blocking_since=_parse_datetime(b['blocking_since']),
                estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
            )
            for b in task_data.get('blocked_by', [])
        ]

        # Parse deliverables
        deliverables = [
            Deliverable(
                type=DeliverableType(d['type']),
                paths=d['paths'],
            )
            for d in task_data.get('deliverables', [])
        ]

        # Parse commits
        commits = [
            GitCommit(
                sha=c['sha'],
                message=c['message'],
                date=_parse_datetime(c['date']),
                author=c['author'],
            )
            for c in task_data.get('commits', [])
        ]

        # Parse metadata (backward compatible)
        if 'metadata' in task_data:
            meta_data = task_data['metadata']
            metadata = TaskMetadata(
                last_updated=_parse_datetime(meta_data['last_updated']),
                token_efficiency=meta_data.get('token_efficiency'),
                duration_hours=meta_data.get('duration_hours'),
            )
        else:
            # Old format: minimal metadata
            metadata = TaskMetadata(
                last_updated=datetime.now(),
                token_efficiency=None,
                duration_hours=None,
            )

        # Create task (backward compatible - many fields optional in old format)
        task = Task(
            id=task_data['id'],
            sprint_id=task_data['sprint_id'],
            track_id=task_data['track_id'],
            roadmap_id=task_data['roadmap_id'],
            task_type=TaskType(task_data.get('task_type', 'development')),
            title=task_data.get('title', task_data.get('name', 'Unknown')),
            description=task_data.get('description', ''),
            status=TaskStatus(task_data.get('status', 'not_started')),
            blocked=task_data.get('blocked', False),
            created=_parse_datetime(task_data.get('created', datetime.now())),
            started=_parse_datetime(task_data.get('started')),
            completed=_parse_datetime(task_data.get('completed')),
            assigned_agent=task_data.get('assigned_agent'),
            priority=Priority(task_data.get('priority', 'medium')),
            phase_label=task_data.get('phase_label'),
            estimated_tokens=task_data.get('estimated_tokens', 1),  # Minimum 1 for validation
            actual_tokens=task_data.get('actual_tokens'),
            complexity=Complexity(_map_complexity(task_data.get('complexity', 'medium'))),
            gate_info=gate_info,
            audit_results=audit_results,
            dependencies=dependencies,
            blocks=blocks,
            blocked_by=blocked_by,
            deliverables=deliverables,
            commits=commits,
            metadata=metadata,
        )

        tasks.append(task)

    return tasks
