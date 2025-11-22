"""
YAML loader for roadmap objects.

Loads YAML files and converts them to Python dataclass objects.
"""

from datetime import datetime, timezone
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
    DependencyStatus,
    PlatformDeployment,
    Standard,
    StandardType,
    EnforcementMode,
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
        'very_high': 'complex',  # Map very_high to complex (closest match)
        # 'medium' stays the same
    }
    return mapping.get(value, value)


def _map_task_type(value: str) -> str:
    """Map old task_type values to new enum values (backward compatibility)."""
    mapping = {
        'quality_gate': 'completion_gate',  # Old generic quality_gate -> completion_gate
        # 'development', 'completion_gate', 'production_gate' stay the same
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

    # Parse version strategy (optional, defaults to milestone-based versioning)
    vs_data = roadmap_data.get('version_strategy', {
        'major_on': 'roadmap_milestone',
        'minor_on': 'track_completion',
        'patch_on': 'sprint_production_ready'
    })
    version_strategy = VersionStrategy(
        major_on=VersionBumpTrigger(vs_data['major_on']),
        minor_on=VersionBumpTrigger(vs_data['minor_on']),
        patch_on=VersionBumpTrigger(vs_data['patch_on']),
    )

    # Parse progress
    prog_data = roadmap_data['progress']
    progress = Progress(
        tracks_total=prog_data.get('tracks_total', 0),
        tracks_completed=prog_data.get('tracks_completed', 0),
        sprints_total=prog_data.get('sprints_total', 0),
        sprints_completed=prog_data.get('sprints_completed', 0),
        tasks_total=prog_data.get('tasks_total', 0),
        tasks_completed=prog_data.get('tasks_completed', 0),
        completion_percent=prog_data.get('completion_percent', 0),
    )

    # Parse tracks
    tracks = [
        TrackSummary(
            id=t['id'],
            name=t['name'],
            status=Status(t.get('status', 'not_started')),
            priority=Priority(t.get('priority', 'medium')),
        )
        for t in roadmap_data.get('tracks', [])
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

    # Parse metadata (optional for test fixtures)
    meta_data = roadmap_data.get('metadata', {
        'created_by': 'unknown',
        'framework_version': '1.0.0',
        'schema_version': '2.1',
        'last_updated': '2025-01-01T00:00:00+00:00'
    })
    metadata = Metadata(
        created_by=meta_data.get('created_by', 'unknown'),
        framework_version=meta_data.get('framework_version', '1.0.0'),
        schema_version=meta_data.get('schema_version', '2.1'),
        last_updated=_parse_datetime(meta_data.get('last_updated', '2025-01-01T00:00:00+00:00')),
        purpose=meta_data.get('purpose'),
        description=meta_data.get('description'),
    )

    # Parse deployed platforms
    deployed_platforms = [
        PlatformDeployment(
            platform=p['platform'],
            context_window=p['context_window'],
            deployed_at=p['deployed_at'],  # Unix timestamp (integer)
            deployed_by=p['deployed_by'],
            primary=p.get('primary', False),
        )
        for p in roadmap_data.get('deployed_platforms', [])
    ]

    # Parse standards (backward compatible - defaults to empty list)
    from ..models import StandardOverride

    standards = []
    for s in roadmap_data.get('standards', []):
        standard = Standard(
            id=s['id'],
            name=s['name'],
            description=s['description'],
            type=StandardType(s['type']),
            enforcement=EnforcementMode(s['enforcement']),
            validation=s['validation'],
            enabled=s.get('enabled', True),
            created=_parse_datetime(s['created']),
        )

        # Parse overrides (backward compatible - defaults to empty list)
        for override_data in s.get('overrides', []):
            override = StandardOverride(
                overridden_at=_parse_datetime(override_data['overridden_at']),
                overridden_by=override_data['overridden_by'],
                reason=override_data['reason'],
                target_id=override_data['target_id'],
                expires_at=_parse_datetime(override_data.get('expires_at')),
            )
            standard.overrides.append(override)

        standards.append(standard)

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
        deployed_platforms=deployed_platforms,
        standards=standards,
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

    # Parse dependencies (backward compatible with simple string format)
    dependencies = []
    for d in track_data.get('dependencies', []):
        if isinstance(d, str):
            # Simple format: just a track ID
            dependencies.append(TrackDependency(
                type=DependencyType.TRACK,
                target_id=d,
                target_status='completed',
                reason='Dependency on track completion',
                optional=False,
            ))
        elif isinstance(d, dict):
            # Structured format
            dependencies.append(TrackDependency(
                type=DependencyType(d['type']),
                target_id=d['target_id'],
                target_status=d['target_status'],
                reason=d['reason'],
                optional=d.get('optional', False),
            ))

    # Parse blocks (backward compatible with simple string format)
    blocks = []
    for b in track_data.get('blocks', []):
        if isinstance(b, str):
            # Simple format: just a track ID
            blocks.append(TrackDependency(
                type=DependencyType.TRACK,
                target_id=b,
                target_status='not_started',
                reason='Blocks track from starting',
            ))
        elif isinstance(b, dict):
            # Structured format
            blocks.append(TrackDependency(
                type=DependencyType(b['type']),
                target_id=b['target_id'],
                target_status=b['at_status'],
                reason=b['reason'],
            ))

    # Parse blockers (backward compatible with simple string format)
    blocked_by = []
    for b in track_data.get('blocked_by', []):
        if isinstance(b, str):
            # Simple format: just a track ID (legacy format, usually empty in practice)
            # We'll create a minimal blocker entry
            from datetime import datetime, timezone
            blocked_by.append(TrackBlocker(
                dependency_id=b,
                dependency_type='track',
                current_status='unknown',
                required_status='completed',
                blocking_since=datetime.now(timezone.utc),
                estimated_resolution=None,
            ))
        elif isinstance(b, dict):
            # Structured format
            blocked_by.append(TrackBlocker(
                dependency_id=b['dependency_id'],
                dependency_type=b['dependency_type'],
                current_status=b['current_status'],
                required_status=b['required_status'],
                blocking_since=_parse_datetime(b['blocking_since']),
                estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
            ))

    # Parse depends_on (new cached dependency tracking, backward compatible with simple strings)
    depends_on = []
    for d in track_data.get('depends_on', []):
        if isinstance(d, str):
            # Simple format: just a track ID
            from datetime import datetime, timezone
            depends_on.append(DependencyStatus(
                blocker_id=d,
                blocker_type='track',
                required_status='completed',
                current_status='unknown',  # Would need to be looked up
                blocks_transition_to='completed',
                last_checked=datetime.now(timezone.utc),
            ))
        elif isinstance(d, dict):
            # Structured format
            depends_on.append(DependencyStatus(
                blocker_id=d['blocker_id'],
                blocker_type=d['blocker_type'],
                required_status=d['required_status'],
                current_status=d['current_status'],
                blocks_transition_to=d.get('blocks_transition_to', 'completed'),
                last_checked=_parse_datetime(d['last_checked']),
            ))

    # Parse depended_on_by (reverse index)
    depended_on_by = track_data.get('depended_on_by', [])

    # Compute blocked status from depends_on (override YAML value for consistency)
    computed_blocked = any(not dep.is_satisfied() for dep in depends_on)

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

    # Parse commits (sprint completion commits)
    # Note: Only commits with sprint_id are sprint completion commits
    # General track commits without sprint_id are skipped
    from vibey.roadmap.models import SprintCompletionCommit
    commits = []
    for c in track_data.get('commits', []):
        # Skip commits without sprint_id (they're general commits, not sprint completions)
        if 'sprint_id' not in c:
            continue
        commits.append(SprintCompletionCommit(
            sprint_id=c['sprint_id'],
            sha=c['sha'],
            message=c['message'],
            date=_parse_datetime(c['date']),
            author=c['author'],
        ))

    # Parse metadata
    meta_data = track_data['metadata']
    metadata = TrackMetadata(
        created_by=meta_data['created_by'],
        last_updated=_parse_datetime(meta_data['last_updated']),
        design_doc=meta_data.get('design_doc'),
        implementation_plan=meta_data.get('implementation_plan'),
        notes=meta_data.get('notes'),
    )

    # Parse standards (backward compatible - defaults to empty list)
    from ..models import StandardOverride

    standards = []
    for s in track_data.get('standards', []):
        standard = Standard(
            id=s['id'],
            name=s['name'],
            description=s['description'],
            type=StandardType(s['type']),
            enforcement=EnforcementMode(s['enforcement']),
            validation=s['validation'],
            enabled=s.get('enabled', True),
            created=_parse_datetime(s['created']),
        )

        # Parse overrides (backward compatible - defaults to empty list)
        for override_data in s.get('overrides', []):
            override = StandardOverride(
                overridden_at=_parse_datetime(override_data['overridden_at']),
                overridden_by=override_data['overridden_by'],
                reason=override_data['reason'],
                target_id=override_data['target_id'],
                expires_at=_parse_datetime(override_data.get('expires_at')),
            )
            standard.overrides.append(override)

        standards.append(standard)

    # Create track
    track = Track(
        id=track_data['id'],
        name=track_data['name'],
        roadmap_id=track_data['roadmap_id'],
        status=Status(track_data['status']),
        blocked=computed_blocked,  # Use computed value instead of YAML value
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
        depends_on=depends_on,
        depended_on_by=depended_on_by,
        quality_gates=quality_gates,
        assigned_agents=track_data.get('assigned_agents', []),
        deliverables=track_data.get('deliverables', []),
        strategic_value=track_data.get('strategic_value', []),
        commits=commits,
        metadata=metadata,
        standards=standards,
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

    # Parse progress (backward compatible with old format and missing progress)
    prog_data = sprint_data.get('progress', {})

    # For old format (no gate breakdown), assume all tasks are development tasks
    # If progress section is completely missing, create minimal progress
    tasks_total = prog_data.get('tasks_total', 0)
    tasks_completed = prog_data.get('tasks_completed', 0)

    # Calculate completion_percent if missing
    if 'completion_percent' in prog_data:
        completion_percent = prog_data['completion_percent']
    elif tasks_total > 0:
        completion_percent = int((tasks_completed / tasks_total) * 100)
    else:
        completion_percent = 0

    progress = SprintProgress(
        development_tasks_total=prog_data.get('development_tasks_total', tasks_total),
        development_tasks_completed=prog_data.get('development_tasks_completed', tasks_completed),
        completion_gate_tasks_total=prog_data.get('completion_gate_tasks_total', 0),
        completion_gate_tasks_completed=prog_data.get('completion_gate_tasks_completed', 0),
        production_gate_tasks_total=prog_data.get('production_gate_tasks_total', 0),
        production_gate_tasks_completed=prog_data.get('production_gate_tasks_completed', 0),
        tasks_total=tasks_total,
        tasks_completed=tasks_completed,
        completion_percent=completion_percent,
    )

    # Parse tasks (backward compatible - multiple formats supported)
    if 'tasks' in sprint_data:
        tasks = []
        for t in sprint_data['tasks']:
            # Handle multiple field name variations (backward compatibility)
            title = t.get('title') or t.get('name', 'Unknown')  # 'title' or 'name'
            status = Status(t.get('status', 'not_started'))  # Default to not_started if missing
            task_type_str = t.get('task_type') or t.get('type', 'development')  # 'task_type' or 'type'
            task_type = TaskType(task_type_str)

            tasks.append(TaskSummary(
                id=t['id'],
                title=title,
                status=status,
                task_type=task_type,
                gate_info=t.get('gate_info'),
            ))
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

    # Parse blocks (backward compatible with simple string format)
    blocks = []
    for b in sprint_data.get('blocks', []):
        if isinstance(b, str):
            # Simple format: just a sprint/track ID
            blocks.append(DevelopmentGate(
                type=DependencyType.SPRINT,
                target_id=b,
                target_status='not_started',
                reason='Blocks sprint from starting',
            ))
        elif isinstance(b, dict):
            # Structured format
            blocks.append(DevelopmentGate(
                type=DependencyType(b['type']),
                target_id=b['target_id'],
                target_status=b['at_status'],
                reason=b['reason'],
            ))

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

    # Parse depends_on (new cached dependency tracking)
    depends_on = [
        DependencyStatus(
            blocker_id=d.get('blocker_id', d.get('dependency_id', 'unknown')),  # Backward compat
            blocker_type=d.get('blocker_type', d.get('dependency_type', 'track')),  # Backward compat
            required_status=d.get('required_status', d.get('target_status', 'completed')),  # Backward compat
            current_status=d.get('current_status', 'not_started'),  # Default
            blocks_transition_to=d.get('blocks_transition_to', 'completed'),  # Default to soft blocker for sprints
            last_checked=_parse_datetime(d.get('last_checked', datetime.now())),
        )
        for d in sprint_data.get('depends_on', [])
    ]

    # Parse depended_on_by (reverse index)
    depended_on_by = sprint_data.get('depended_on_by', [])

    # Compute blocked status from depends_on (override YAML value for consistency)
    computed_blocked = any(not dep.is_satisfied() for dep in depends_on)

    # Parse commits (task completion commits)
    # Note: Only commits with task_id are task completion commits
    # General sprint commits without task_id are skipped
    from vibey.roadmap.models import TaskCompletionCommit
    commits = []
    for c in sprint_data.get('commits', []):
        # Skip commits without task_id (they're general commits, not task completions)
        if 'task_id' not in c:
            continue
        commits.append(TaskCompletionCommit(
            task_id=c['task_id'],
            sha=c['sha'],
            message=c['message'],
            date=_parse_datetime(c['date']),
            author=c['author'],
        ))

    # Parse metadata (defensive coding - handle case where metadata might not be a dict)
    meta_data = sprint_data.get('metadata')
    if not meta_data or not isinstance(meta_data, dict):
        # Fallback to empty dict if metadata is missing or not a dict
        from datetime import timezone
        meta_data = {'last_updated': datetime.now(timezone.utc).isoformat()}

    metadata = SprintMetadata(
        last_updated=_parse_datetime(meta_data['last_updated']),
        estimated_duration=meta_data.get('estimated_duration'),
        actual_duration=meta_data.get('actual_duration'),
        estimated_tokens=meta_data.get('estimated_tokens'),
        actual_tokens=meta_data.get('actual_tokens'),
        agents_used=meta_data.get('agents_used'),
    )

    # Parse standards (backward compatible - defaults to empty list)
    from ..models import StandardOverride

    standards = []
    for s in sprint_data.get('standards', []):
        standard = Standard(
            id=s['id'],
            name=s['name'],
            description=s['description'],
            type=StandardType(s['type']),
            enforcement=EnforcementMode(s['enforcement']),
            validation=s['validation'],
            enabled=s.get('enabled', True),
            created=_parse_datetime(s['created']),
        )

        # Parse overrides (backward compatible - defaults to empty list)
        for override_data in s.get('overrides', []):
            override = StandardOverride(
                overridden_at=_parse_datetime(override_data['overridden_at']),
                overridden_by=override_data['overridden_by'],
                reason=override_data['reason'],
                target_id=override_data['target_id'],
                expires_at=_parse_datetime(override_data.get('expires_at')),
            )
            standard.overrides.append(override)

        standards.append(standard)

    # Create sprint (backward compatible - many fields optional in old format)
    sprint = Sprint(
        id=sprint_data['id'],
        name=sprint_data['name'],
        track_id=sprint_data['track_id'],
        roadmap_id=sprint_data.get('roadmap_id', 'vibey-framework-v2'),  # Default if missing
        status=Status(sprint_data['status']),
        blocked=computed_blocked,  # Use computed value instead of YAML value
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
        depends_on=depends_on,
        depended_on_by=depended_on_by,
        plan_file=sprint_data.get('plan_file'),
        deliverables=sprint_data.get('deliverables', []),
        commits=commits,
        metadata=metadata,
        standards=standards,
    )

    return sprint


def load_task(file_path: Union[str, Path]) -> Task:
    """
    Load a single task from YAML file.

    Args:
        file_path: Path to task YAML file

    Returns:
        Task object
    """
    tasks = load_tasks(file_path)
    if len(tasks) != 1:
        raise ValueError(f"Expected 1 task, found {len(tasks)}")
    return tasks[0]


def load_tasks(file_path: Union[str, Path]) -> List[Task]:
    """
    Load tasks from YAML file or hierarchical directory.

    Supports both formats:
    - Legacy: single file with {'tasks': [...]} (flat structure)
    - Hierarchical: directory with task subdirectories containing task.yaml

    Args:
        file_path: Path to tasks file or sprint directory

    Returns:
        List of Task objects
    """
    file_path = Path(file_path)

    # Check if this is a directory (hierarchical structure)
    if file_path.is_dir():
        # Load tasks from hierarchical structure
        tasks_data = []
        for item in file_path.iterdir():
            # Skip non-directories and special directories
            if not item.is_dir() or item.name.startswith('.') or item.name == 'context':
                continue

            task_file = item / "task.yaml"
            if task_file.exists():
                with open(task_file, 'r') as f:
                    task_yaml = yaml.safe_load(f)
                    if task_yaml and 'task' in task_yaml:
                        tasks_data.append(task_yaml['task'])
    else:
        # Legacy flat structure
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        # Tasks can be a list or dict with 'tasks'/'task' key
        if isinstance(data, list):
            tasks_data = data
        elif 'task' in data:
            # Single task file (hierarchical structure)
            tasks_data = [data['task']]
        elif 'tasks' in data:
            # Multiple tasks file (legacy structure)
            tasks_data = data['tasks']
        else:
            raise ValueError("Invalid tasks file format")

    tasks = []
    for task_data in tasks_data:
        # Parse gate info if present (backward compatible with field name variations)
        gate_info = None
        if 'gate_info' in task_data and task_data['gate_info']:
            gi_data = task_data['gate_info']
            # Determine blocks_status (default based on task_type if missing)
            blocks_status = gi_data.get('blocks_status')
            if not blocks_status:
                # Infer from task_type: completion_gate -> 'completed', production_gate -> 'production_ready'
                task_type = task_data.get('task_type', 'development')
                if task_type == 'completion_gate':
                    blocks_status = 'completed'
                elif task_type == 'production_gate':
                    blocks_status = 'production_ready'
                else:
                    blocks_status = 'completed'  # Default

            gate_info = GateInfo(
                blocks_status=blocks_status,
                threshold=gi_data['threshold'],
                is_blocking=gi_data.get('is_blocking', gi_data.get('blocking', True)),  # Support both field names
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

        # Parse dependencies (backward compatible with simple string format)
        dependencies = []
        for d in task_data.get('dependencies', []):
            if isinstance(d, str):
                # Simple string format (legacy) - assume task dependency
                dependencies.append(TaskDependency(
                    type=DependencyType.TASK,
                    target_id=d,
                    target_status='completed',
                    reason='Dependency on task completion',
                ))
            elif isinstance(d, dict):
                # Structured format (old format uses 'at_status', new uses 'target_status')
                dependencies.append(TaskDependency(
                    type=DependencyType(d['type']),
                    target_id=d['target_id'],
                    target_status=d.get('target_status', d.get('at_status', 'completed')),
                    reason=d.get('reason', ''),
                ))
            else:
                raise ValueError(f"Invalid dependencies format: {d}")

        # Parse blocks (backward compatible with simple string format)
        blocks = []
        for b in task_data.get('blocks', []):
            if isinstance(b, str):
                # Simple string format (legacy) - assume task dependency
                blocks.append(TaskDependency(
                    type=DependencyType.TASK,
                    target_id=b,
                    target_status='not_started',  # Blocks the target from starting
                    reason='Blocks task from starting',
                ))
            elif isinstance(b, dict):
                # Structured format
                blocks.append(TaskDependency(
                    type=DependencyType(b['type']),
                    target_id=b['target_id'],
                    target_status=b['at_status'],
                    reason=b['reason'],
                ))
            else:
                raise ValueError(f"Invalid blocks format: {b}")

        # Parse blockers (backward compatible with simple string format)
        blocked_by = []
        for b in task_data.get('blocked_by', []):
            if isinstance(b, str):
                # Simple string format (legacy) - assume task blocker
                blocked_by.append(TaskBlocker(
                    dependency_id=b,
                    dependency_type='task',
                    current_status='unknown',
                    required_status='completed',
                    blocking_since=datetime.now(timezone.utc),
                    estimated_resolution=None,
                ))
            elif isinstance(b, dict):
                # Structured format
                blocked_by.append(TaskBlocker(
                    dependency_id=b['dependency_id'],
                    dependency_type=b['dependency_type'],
                    current_status=b['current_status'],
                    required_status=b['required_status'],
                    blocking_since=_parse_datetime(b['blocking_since']),
                    estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
                ))
            else:
                raise ValueError(f"Invalid blocked_by format: {b}")

        # Parse depends_on (new cached dependency tracking)
        # Backward compatible: supports simple string format and optional cache fields
        depends_on = []
        for d in task_data.get('depends_on', []):
            if isinstance(d, str):
                # Simple string format (legacy) - assume task dependency
                depends_on.append(DependencyStatus(
                    blocker_id=d,
                    blocker_type='task',
                    required_status='completed',
                    current_status='unknown',
                    blocks_transition_to='in_progress',
                    last_checked=datetime.now(timezone.utc),
                ))
            elif isinstance(d, dict):
                # Structured format with optional cache fields
                depends_on.append(DependencyStatus(
                    blocker_id=d['blocker_id'],
                    blocker_type=d['blocker_type'],
                    required_status=d['required_status'],
                    current_status=d.get('current_status', 'unknown'),  # Default to 'unknown' if not cached
                    blocks_transition_to=d.get('blocks_transition_to', 'in_progress'),  # Default to hard blocker
                    last_checked=_parse_datetime(d.get('last_checked')) if d.get('last_checked') else datetime.now(timezone.utc),  # Default to now
                ))
            else:
                raise ValueError(f"Invalid depends_on format: {d}")

        # Parse depended_on_by (reverse index)
        depended_on_by = task_data.get('depended_on_by', [])

        # Compute blocked status from depends_on (override YAML value for consistency)
        computed_blocked = any(not dep.is_satisfied() for dep in depends_on)

        # Parse deliverables (backward compatible - handle both old string format and new structured format)
        deliverables = []
        # Type aliases for backward compatibility
        deliverable_type_aliases = {
            "configuration": "config"  # Map legacy "configuration" to "config"
        }
        for d in task_data.get('deliverables', []):
            if isinstance(d, str):
                # Old format: just a string path - infer type as "code"
                deliverables.append(Deliverable(
                    type=DeliverableType.CODE,
                    paths=[d],
                ))
            elif isinstance(d, dict):
                # Check if structured format (has 'type' and 'paths' fields)
                if 'type' in d and 'paths' in d:
                    # New format: structured with type and paths
                    # Normalize type value using aliases (e.g., "configuration" → "config")
                    deliverable_type = deliverable_type_aliases.get(d['type'], d['type'])
                    deliverables.append(Deliverable(
                        type=DeliverableType(deliverable_type),
                        paths=d['paths'],
                    ))
                else:
                    # Malformed dict format (YAML dict syntax): convert to string
                    # Example: {'Forensic audit report': 'standards-system'} → "Forensic audit report: standards-system"
                    for key, value in d.items():
                        deliverable_str = f"{key}: {value}" if value else key
                        deliverables.append(Deliverable(
                            type=DeliverableType.CODE,
                            paths=[deliverable_str],
                        ))
            # Skip any other format (invalid)

        # Parse commits
        commits = []
        for c in task_data.get('commits', []):
            # Handle both old format (no platform) and new format (with platform)
            if 'platform' not in c:
                # Legacy commit without platform tracking - skip or migrate
                # For now, we'll skip legacy commits to enforce platform requirement
                continue

            commits.append(GitCommit(
                sha=c['sha'],
                message=c['message'],
                date=_parse_datetime(c['date']),
                author=c['author'],
                platform=c['platform'],  # REQUIRED field
                submitted_at=c['submitted_at'],  # Unix timestamp (integer)
            ))

        # Parse metadata (backward compatible - last_updated is optional)
        if 'metadata' in task_data:
            meta_data = task_data['metadata']
            metadata = TaskMetadata(
                last_updated=_parse_datetime(meta_data.get('last_updated')) if meta_data.get('last_updated') else datetime.now(timezone.utc),
                token_efficiency=meta_data.get('token_efficiency'),
                duration_hours=meta_data.get('duration_hours'),
            )
        else:
            # Old format: minimal metadata
            metadata = TaskMetadata(
                last_updated=datetime.now(timezone.utc),
                token_efficiency=None,
                duration_hours=None,
            )

        # Create task (backward compatible - many fields optional in old format)
        task = Task(
            id=task_data['id'],
            sprint_id=task_data['sprint_id'],
            track_id=task_data['track_id'],
            roadmap_id=task_data.get('roadmap_id', 'vibey-framework-v2'),  # Default to main roadmap
            task_type=TaskType(_map_task_type(task_data.get('task_type') or task_data.get('type', 'development'))),
            title=task_data.get('title') or task_data.get('name', 'Unknown'),
            description=task_data.get('description', ''),
            status=TaskStatus(task_data.get('status', 'not_started')),
            blocked=computed_blocked,  # Use computed value instead of YAML value
            created=_parse_datetime(task_data.get('created', datetime.now())),
            started=_parse_datetime(task_data.get('started')),
            completed=_parse_datetime(task_data.get('completed')),
            assigned_agent=task_data.get('assigned_agent'),
            priority=Priority(task_data.get('priority', 'medium')),
            phase_label=task_data.get('phase_label'),
            estimated_tokens=task_data.get('estimated_tokens') or 1,  # Default to 1 if missing or null
            actual_tokens=task_data.get('actual_tokens'),
            complexity=Complexity(_map_complexity(task_data.get('complexity', 'medium'))),
            gate_info=gate_info,
            audit_results=audit_results,
            dependencies=dependencies,
            blocks=blocks,
            blocked_by=blocked_by,
            depends_on=depends_on,
            depended_on_by=depended_on_by,
            deliverables=deliverables,
            commits=commits,
            metadata=metadata,
        )

        tasks.append(task)

    return tasks
