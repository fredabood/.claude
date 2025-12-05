"""
YAML loader for roadmap objects.

Loads YAML files and converts them to:
- Legacy dataclass objects (Roadmap, Track, Sprint, Task) for v1 format
- Pydantic models (RoadmapTicket, TrackTicket, SprintTicket, TaskTicket) for v2 format

Supports backward compatibility with v1 YAML format while migrating to v2.
"""

import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Union, Dict, Any, List, Tuple, Optional

import yaml

# New Pydantic models (unified ticket architecture)
from ..models.ticket.domain import (
    RoadmapTicket,
    TrackTicket,
    SprintTicket,
    TaskTicket,
    GateInfo as PydanticGateInfo,
    AuditResults as PydanticAuditResults,
    DevelopmentGate as PydanticDevelopmentGate,
    VersionStrategy as PydanticVersionStrategy,
    VersionHistoryEntry as PydanticVersionHistoryEntry,
    ActivityLogEntry as PydanticActivityLogEntry,
    PlatformDeployment as PydanticPlatformDeployment,
)
from ..models.ticket.ticket import GitCommit as PydanticGitCommit, Ticket
from ..models.ticket.completable import Criterion
from ..models.ticket.enums import (
    TicketStatus,
    TicketType,
    TaskType as PydanticTaskType,
    Priority as PydanticPriority,
    Complexity as PydanticComplexity,
    DeliverableType as PydanticDeliverableType,
    CriterionTargetType,
    GateStatus as PydanticGateStatus,
    ActivityType as PydanticActivityType,
)
from ..models.ticket.targets import (
    CompletableTarget,
    FileExistsTarget,
    ThresholdTarget,
)

# Legacy dataclass models
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


def _parse_datetime(value: Union[str, datetime, date, None]) -> Union[datetime, None]:
    """Parse datetime from string, date, or datetime - always returns timezone-aware datetime."""
    if value is None:
        return None

    # Handle date objects (YAML parses unquoted dates like 2025-11-23 as date)
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)

    if isinstance(value, datetime):
        # If naive datetime, make it timezone-aware (assume UTC)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    if isinstance(value, str):
        # Try ISO 8601 format
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        # If naive datetime, make it timezone-aware (assume UTC)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

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


logger = logging.getLogger(__name__)


# =============================================================================
# FORMAT DETECTION & MIGRATION HELPERS
# =============================================================================


def detect_yaml_format(data: Dict[str, Any]) -> str:
    """
    Detect if YAML data uses v1 (dataclass) or v2 (Pydantic) format.

    V2 format indicators:
    - 'criteria' field present (unified criterion system)
    - 'parent_ref' field present (explicit hierarchy)
    - Fields with '_local' suffix (e.g., commits_local)
    - 'ticket_type' field present

    Args:
        data: Parsed YAML data dictionary

    Returns:
        'v1' for legacy format, 'v2' for new Pydantic format
    """
    v2_indicators = [
        'criteria',
        'parent_ref',
        'ticket_type',
        'commits_local',
        'requirements_local',
        'assigned_agents',  # List in v2, assigned_agent (singular) in v1
    ]

    for indicator in v2_indicators:
        if indicator in data:
            return 'v2'

    # Check for nested structures that indicate v1 format
    if 'blocked_by' in data and isinstance(data.get('blocked_by'), list):
        # v1 uses blocked_by as a list of blockers
        # v2 converts these to criteria
        return 'v1'

    if 'depends_on' in data and isinstance(data.get('depends_on'), list):
        # Check if depends_on uses old DependencyStatus format
        deps = data.get('depends_on', [])
        if deps and isinstance(deps[0], dict) and 'blocker_id' in deps[0]:
            return 'v1'

    # Default to v1 for backward compatibility
    return 'v1'


def _convert_status_to_ticket_status(status_str: str) -> TicketStatus:
    """Convert legacy status string to TicketStatus enum."""
    if not status_str:
        return TicketStatus.NOT_STARTED
    status_mapping = {
        'not_started': TicketStatus.NOT_STARTED,
        'in_progress': TicketStatus.IN_PROGRESS,
        'completed': TicketStatus.COMPLETED,
        'blocked': TicketStatus.PAUSED,  # 'blocked' maps to PAUSED in v2
        'paused': TicketStatus.PAUSED,
        'wont_do': TicketStatus.WONT_DO,
        'cancelled': TicketStatus.WONT_DO,
        'superseded': TicketStatus.SUPERSEDED,
        'completion_gate_check': TicketStatus.COMPLETION_GATE_CHECK,
        'production_gate_check': TicketStatus.PRODUCTION_GATE_CHECK,
        'production_ready': TicketStatus.PRODUCTION_READY,
        'deployed': TicketStatus.DEPLOYED,
        'unknown': TicketStatus.NOT_STARTED,  # Map unknown to NOT_STARTED
    }
    return status_mapping.get(status_str, TicketStatus.NOT_STARTED)


def _convert_priority(priority_str: str) -> PydanticPriority:
    """Convert legacy priority string to Priority enum."""
    if not priority_str:
        return PydanticPriority.MEDIUM
    priority_mapping = {
        'low': PydanticPriority.LOW,
        'medium': PydanticPriority.MEDIUM,
        'high': PydanticPriority.HIGH,
        'critical': PydanticPriority.CRITICAL,
    }
    return priority_mapping.get(priority_str.lower(), PydanticPriority.MEDIUM)


def _convert_complexity(complexity_str: str) -> PydanticComplexity:
    """Convert legacy complexity string to Complexity enum."""
    if not complexity_str:
        return PydanticComplexity.MEDIUM
    # PydanticComplexity enum has: LOW, MEDIUM, HIGH, CRITICAL
    complexity_mapping = {
        'simple': PydanticComplexity.LOW,
        'low': PydanticComplexity.LOW,
        'medium': PydanticComplexity.MEDIUM,
        'complex': PydanticComplexity.HIGH,
        'high': PydanticComplexity.HIGH,
        'very_high': PydanticComplexity.CRITICAL,
        'critical': PydanticComplexity.CRITICAL,
    }
    return complexity_mapping.get(complexity_str.lower(), PydanticComplexity.MEDIUM)


def _convert_task_type(task_type_str: str) -> PydanticTaskType:
    """Convert legacy task_type string to TaskType enum."""
    if not task_type_str:
        return PydanticTaskType.DEVELOPMENT
    # PydanticTaskType enum has: DEVELOPMENT, DOCUMENTATION, TESTING, RESEARCH, REVIEW, INFRASTRUCTURE, GATE
    type_mapping = {
        'development': PydanticTaskType.DEVELOPMENT,
        'completion_gate': PydanticTaskType.GATE,
        'production_gate': PydanticTaskType.GATE,
        'quality_gate': PydanticTaskType.GATE,
        'gate': PydanticTaskType.GATE,
        'documentation': PydanticTaskType.DOCUMENTATION,
        'testing': PydanticTaskType.TESTING,
        'research': PydanticTaskType.RESEARCH,
        'review': PydanticTaskType.REVIEW,
        'refactor': PydanticTaskType.DEVELOPMENT,  # Map refactor to development
        'refactoring': PydanticTaskType.DEVELOPMENT,  # Map refactoring to development
        'infrastructure': PydanticTaskType.INFRASTRUCTURE,
    }
    return type_mapping.get(task_type_str.lower(), PydanticTaskType.DEVELOPMENT)


# =============================================================================
# CRITERION CREATION HELPERS
# =============================================================================


def _create_dependency_criterion(
    dep_data: Dict[str, Any],
    index: int,
    description_prefix: str = "Dependency"
) -> Criterion:
    """
    Create a Criterion from legacy depends_on or blocked_by data.

    Legacy format:
        depends_on:
          - blocker_id: task-001
            blocker_type: task
            required_status: completed
            blocks_transition_to: in_progress

    New format (Criterion with CompletableTarget):
        criteria:
          - id: dep-task-001
            description: "Depends on task-001 completing"
            blocks_transition_to: in_progress
            target:
              type: completable
              completable_id: task-001
              required_status: completed
    """
    blocker_id = dep_data.get('blocker_id', dep_data.get('dependency_id', f'unknown-{index}'))
    blocker_type = dep_data.get('blocker_type', dep_data.get('dependency_type', 'task'))
    required_status_str = dep_data.get('required_status', 'completed')
    blocks_to_str = dep_data.get('blocks_transition_to', 'in_progress')

    # Convert strings to enums
    required_status = _convert_status_to_ticket_status(required_status_str)
    blocks_to = _convert_status_to_ticket_status(blocks_to_str)

    # Get cached current status if available
    current_status_str = dep_data.get('current_status')
    current_status = _convert_status_to_ticket_status(current_status_str) if current_status_str else None

    target = CompletableTarget(
        completable_id=blocker_id,
        required_status=required_status,
        current_status=current_status,
        last_checked=_parse_datetime(dep_data.get('last_checked')),
    )

    return Criterion(
        id=f"dep-{blocker_id}",
        description=f"{description_prefix}: {blocker_type} {blocker_id} must be {required_status.value}",
        blocks_transition_to=blocks_to,
        target=target,
        required=True,
    )


def _create_subtask_criterion(
    task_id: str,
    current_status: Optional[TicketStatus] = None
) -> Criterion:
    """
    Create a Criterion for a subtask (child that blocks completion).

    In the v2 model, the parent-child hierarchy is established via
    CompletableTarget criteria that block COMPLETED status.
    """
    target = CompletableTarget(
        completable_id=task_id,
        required_status=TicketStatus.COMPLETED,
        current_status=current_status,
    )

    return Criterion(
        id=f"subtask-{task_id}",
        description=f"Subtask {task_id} must complete",
        blocks_transition_to=TicketStatus.COMPLETED,
        target=target,
        required=True,
    )


def _create_deliverable_criterion(
    deliverable_data: Union[str, Dict[str, Any]],
    index: int
) -> Criterion:
    """
    Create a Criterion from legacy deliverable data.

    Legacy format:
        deliverables:
          - type: code
            paths:
              - vibey/roadmap/models/ticket.py

    New format (Criterion with FileExistsTarget):
        criteria:
          - id: deliverable-0
            description: "Code deliverable must exist"
            blocks_transition_to: completed
            target:
              type: file_exists
              paths: ["vibey/roadmap/models/ticket.py"]
              all_required: true
    """
    if isinstance(deliverable_data, str):
        # Old string format - just a path
        paths = [deliverable_data]
        deliverable_type = PydanticDeliverableType.OTHER
    else:
        paths = deliverable_data.get('paths', [])
        type_str = deliverable_data.get('type', 'other')

        # Map deliverable type (PydanticDeliverableType has: CODE, TEST, DOCUMENTATION, CONFIG, DESIGN, OTHER)
        type_mapping = {
            'code': PydanticDeliverableType.CODE,
            'test': PydanticDeliverableType.TEST,
            'documentation': PydanticDeliverableType.DOCUMENTATION,
            'config': PydanticDeliverableType.CONFIG,
            'configuration': PydanticDeliverableType.CONFIG,
            'database': PydanticDeliverableType.OTHER,  # No DATABASE type, map to OTHER
            'design': PydanticDeliverableType.DESIGN,
            'other': PydanticDeliverableType.OTHER,
        }
        deliverable_type = type_mapping.get(type_str.lower(), PydanticDeliverableType.OTHER)

    target = FileExistsTarget(
        paths=paths,
        all_required=True,
        deliverable_type=deliverable_type,
    )

    return Criterion(
        id=f"deliverable-{index}",
        description=f"Deliverable: {', '.join(paths[:2])}{'...' if len(paths) > 2 else ''}",
        blocks_transition_to=TicketStatus.COMPLETED,
        target=target,
        required=True,
    )


def _create_quality_gate_criterion(
    gate_data: Dict[str, Any],
    index: int
) -> Criterion:
    """
    Create a Criterion from legacy quality gate data.

    Legacy format:
        quality_gates:
          - name: Code Coverage
            threshold: 80
            blocking: true
            score: 85

    New format (Criterion with ThresholdTarget):
        criteria:
          - id: gate-code-coverage
            description: "Code Coverage must meet threshold"
            blocks_transition_to: completed
            target:
              type: threshold
              metric_name: Code Coverage
              threshold: 80
              current_value: 85
    """
    name = gate_data.get('name', f'Gate {index}')
    threshold = gate_data.get('threshold', 100)
    is_blocking = gate_data.get('blocking', True)
    current_value = gate_data.get('score')

    target = ThresholdTarget(
        metric_name=name,
        threshold=float(threshold),
        current_value=float(current_value) if current_value is not None else None,
    )

    # Determine which transition this blocks
    gate_status_str = gate_data.get('status', 'not_run')
    if gate_status_str in ('production_gate', 'production_gate_check'):
        blocks_to = TicketStatus.PRODUCTION_READY
    else:
        blocks_to = TicketStatus.COMPLETED

    return Criterion(
        id=f"gate-{name.lower().replace(' ', '-').replace('_', '-')}",
        description=f"Quality gate: {name} >= {threshold}",
        blocks_transition_to=blocks_to,
        target=target,
        required=is_blocking,
    )


def _parse_completes_from_message(message: str) -> List[str]:
    """
    Extract ticket IDs that this commit completes from the commit message.

    Supports patterns:
    - "Completes: task-id" or "Completes: task-id, task-id2"
    - "Closes: task-id" or "Closes #task-id"
    - "Fixes: task-id" or "Fixes #task-id"
    - "chore(task-id): Mark task complete" (task reference in conventional commit)

    Args:
        message: Git commit message

    Returns:
        List of ticket IDs found in the message
    """
    import re

    ticket_ids = set()

    # Pattern 1: "Completes: id1, id2" or "Completes id1"
    # Match task IDs which typically have format: track-sprint-task-number
    completes_match = re.search(r'Completes:?\s*([\w\-,\s]+?)(?:\n|$)', message, re.IGNORECASE)
    if completes_match:
        # Extract hyphenated identifiers (e.g., sqlite-backend-8-task-007)
        # Pattern matches 2-5 parts separated by hyphens
        ids = re.findall(r'\b([\w]+-[\w]+(?:-[\w]+){0,3})\b', completes_match.group(1))
        ticket_ids.update(ids)

    # Pattern 2: "Closes: id" or "Closes #id"
    closes_matches = re.findall(r'Closes:?\s*#?([\w\-]+(?:-[\w\-]+)*)', message, re.IGNORECASE)
    ticket_ids.update(closes_matches)

    # Pattern 3: "Fixes: id" or "Fixes #id"
    fixes_matches = re.findall(r'Fixes:?\s*#?([\w\-]+(?:-[\w\-]+)*)', message, re.IGNORECASE)
    ticket_ids.update(fixes_matches)

    # Pattern 4: Conventional commit with task ID: "chore(task-id): ..."
    # Look for task IDs in parentheses after common prefixes
    conventional_match = re.search(r'^(?:feat|fix|chore|docs|refactor|test)\(([\w\-]+)\):', message)
    if conventional_match:
        task_ref = conventional_match.group(1)
        # Only include if it looks like a task ID (has dashes)
        if '-' in task_ref:
            ticket_ids.add(task_ref)

    # Filter out common false positives
    filtered = [
        tid for tid in ticket_ids
        if len(tid) > 3  # Avoid short matches
        and not tid.lower() in ('task', 'sprint', 'track', 'roadmap')  # Avoid generic words
    ]

    return sorted(filtered)


def _convert_legacy_commits(commits_data: List[Dict[str, Any]]) -> List[PydanticGitCommit]:
    """
    Convert legacy commit data to GitCommit objects.

    Handles both v1 format (simple fields) and v2 format (with completes_tickets).
    Extracts completes_tickets from message if not explicitly provided.
    Sets platform to "legacy" for commits without platform field.

    Args:
        commits_data: List of commit dictionaries from YAML

    Returns:
        List of GitCommit Pydantic models
    """
    commits = []
    for c in commits_data:
        # Skip commits without required fields
        if 'sha' not in c or 'message' not in c:
            continue

        # Get completes_tickets: from YAML if present, else parse from message
        completes_tickets = c.get('completes_tickets', [])
        if not completes_tickets:
            completes_tickets = _parse_completes_from_message(c['message'])

        # Platform defaults to "legacy" for old commits without platform
        platform = c.get('platform')
        if platform is None:
            platform = "legacy"

        commit = PydanticGitCommit(
            sha=c['sha'],
            message=c['message'],
            date=_parse_datetime(c.get('date')) or datetime.now(timezone.utc),
            author=c.get('author', 'unknown'),
            platform=platform,
            submitted_at=_parse_datetime(c.get('submitted_at')),
            completes_tickets=completes_tickets,
            # File changes (v2 fields)
            files_added=c.get('files_added', []),
            files_modified=c.get('files_modified', []),
            files_deleted=c.get('files_deleted', []),
            # Artifact links (v2 fields)
            creates_artifacts=c.get('creates_artifacts', []),
            modifies_artifacts=c.get('modifies_artifacts', []),
            deletes_artifacts=c.get('deletes_artifacts', []),
        )
        commits.append(commit)
    return commits


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
            # Structured format (at_status is optional, default to 'not_started')
            blocks.append(TrackDependency(
                type=DependencyType(b['type']),
                target_id=b['target_id'],
                target_status=b.get('at_status', b.get('target_status', 'not_started')),
                reason=b.get('reason', 'Blocks target from starting'),
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

    # Parse metadata (backward compatible - defaults provided for missing fields)
    meta_data = track_data.get('metadata', {})
    metadata = TrackMetadata(
        created_by=meta_data.get('created_by', 'unknown'),
        last_updated=_parse_datetime(meta_data.get('last_updated', '2025-01-01T00:00:00+00:00')),
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
            # Handle string format (new schema: just task IDs)
            if isinstance(t, str):
                # Task ID string - create minimal TaskSummary
                tasks.append(TaskSummary(
                    id=t,
                    title=t,  # Use ID as placeholder title
                    status=Status.NOT_STARTED,  # Will be loaded from task.yaml
                    task_type=TaskType.DEVELOPMENT,
                    gate_info=None,
                ))
            else:
                # Dict format (old embedded schema)
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

    # Parse blockers (backward compatible with simple string format)
    blocked_by = []
    for b in sprint_data.get('blocked_by', []):
        if isinstance(b, str):
            # Simple string format (legacy) - sprint ID as blocker
            blocked_by.append(SprintBlocker(
                dependency_id=b,
                dependency_type='sprint',
                current_status='not_started',
                required_status='completed',
                blocking_since=None,
                estimated_resolution=None,
            ))
        elif isinstance(b, dict):
            # Structured format with full blocker info
            blocked_by.append(SprintBlocker(
                dependency_id=b['dependency_id'],
                dependency_type=b.get('dependency_type', 'sprint'),
                current_status=b.get('current_status', 'not_started'),
                required_status=b.get('required_status', 'completed'),
                blocking_since=_parse_datetime(b.get('blocking_since')),
                estimated_resolution=_parse_datetime(b.get('estimated_resolution')),
            ))

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

    # Handle estimated_duration/actual_duration at both sprint level and metadata level
    # Sprint-level takes precedence (backward compatibility)
    estimated_duration = sprint_data.get('estimated_duration') or meta_data.get('estimated_duration')
    actual_duration = sprint_data.get('actual_duration') or meta_data.get('actual_duration')

    metadata = SprintMetadata(
        last_updated=_parse_datetime(meta_data['last_updated']),
        estimated_duration=estimated_duration,
        actual_duration=actual_duration,
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
        blocked_reason=sprint_data.get('blocked_reason'),
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
        description=sprint_data.get('description'),
        goal=sprint_data.get('goal'),
        success_criteria=sprint_data.get('success_criteria', []),
        risks=sprint_data.get('risks', []),
        notes=sprint_data.get('notes'),
        assigned_agents=sprint_data.get('assigned_agents', []),
        quality_gates=sprint_data.get('quality_gates', []),
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
        # Extract sprint_id and track_id from directory path:
        # .vibey/roadmap/{track_id}/{sprint_id}/{task_id}/task.yaml
        sprint_id = file_path.name
        track_id = file_path.parent.name

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
                        task_data = task_yaml['task']
                        # Inject sprint_id and track_id from path if not present
                        if 'sprint_id' not in task_data:
                            task_data['sprint_id'] = sprint_id
                        if 'track_id' not in task_data:
                            task_data['track_id'] = track_id
                        tasks_data.append(task_data)
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


# =============================================================================
# AUDIT TRAIL LOADER
# =============================================================================

def load_audit_trail(roadmap_dir: Union[str, Path]) -> List[dict]:
    """
    Load audit trail from audit-trail.yaml file.

    Args:
        roadmap_dir: Path to the roadmap directory containing audit-trail.yaml

    Returns:
        List of audit trail entry dictionaries
    """
    roadmap_dir = Path(roadmap_dir)
    audit_file = roadmap_dir / 'audit-trail.yaml'

    if not audit_file.exists():
        return []

    with open(audit_file, 'r') as f:
        data = yaml.safe_load(f) or {}

    entries = []
    for entry in data.get('audit_log', []):
        entries.append({
            'timestamp': entry['timestamp'],
            'object_type': entry['object_type'],
            'object_id': entry['object_id'],
            'field': entry['field'],
            'old_value': entry.get('old_value'),
            'new_value': entry.get('new_value'),
            'changed_by': entry['changed_by'],
            'reason': entry['reason'],
            'commit': entry.get('commit'),
            'source': entry.get('source', 'cli'),
        })

    return entries


def load_audit_trail_metadata(roadmap_dir: Union[str, Path]) -> dict:
    """
    Load audit trail metadata from audit-trail.yaml file.

    Args:
        roadmap_dir: Path to the roadmap directory containing audit-trail.yaml

    Returns:
        Metadata dictionary
    """
    roadmap_dir = Path(roadmap_dir)
    audit_file = roadmap_dir / 'audit-trail.yaml'

    if not audit_file.exists():
        return {}

    with open(audit_file, 'r') as f:
        data = yaml.safe_load(f) or {}

    return data.get('metadata', {})


# =============================================================================
# V2 PYDANTIC MODEL LOADERS (Unified Ticket Architecture)
# =============================================================================


def load_task_ticket(file_path: Union[str, Path]) -> TaskTicket:
    """
    Load a task from YAML file and return as TaskTicket (Pydantic model).

    This is the v2 loader that returns the new unified ticket architecture model.
    It supports both v1 (legacy) and v2 YAML formats.

    Args:
        file_path: Path to task.yaml file

    Returns:
        TaskTicket object (Pydantic model)

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        ValueError: If data is invalid
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'task' not in data:
        raise ValueError("Missing 'task' root key")

    task_data = data['task']
    format_version = detect_yaml_format(task_data)

    if format_version == 'v2':
        # Direct v2 format - use as-is
        return _load_task_ticket_v2(task_data)
    else:
        # v1 format - migrate to v2
        logger.debug(f"Loading v1 format task {task_data.get('id')}, migrating to v2")
        return _migrate_task_to_ticket(task_data)


def _load_task_ticket_v2(task_data: Dict[str, Any]) -> TaskTicket:
    """Load TaskTicket from v2 format YAML data."""
    # Parse criteria (v2 native format)
    criteria = []
    for c in task_data.get('criteria', []):
        target_type = CriterionTargetType(c['target']['type'])
        target_config = {k: v for k, v in c['target'].items() if k != 'type'}

        from ..models.ticket.targets import create_target
        target = create_target(target_type, target_config)

        criterion = Criterion(
            id=c['id'],
            description=c['description'],
            blocks_transition_to=_convert_status_to_ticket_status(c.get('blocks_transition_to', 'completed')),
            target=target,
            required=c.get('required', True),
        )
        criteria.append(criterion)

    # Parse commits
    commits = _convert_legacy_commits(task_data.get('commits', []))

    # Parse gate_info if present
    gate_info_v2 = None
    if 'gate_info' in task_data and task_data['gate_info']:
        gi = task_data['gate_info']
        gate_info_v2 = GateInfo(
            blocks_status=_convert_status_to_ticket_status(gi.get('blocks_status', 'completed')),
            threshold=gi.get('threshold', 100),
            is_blocking=gi.get('is_blocking', True),
            score=gi.get('score'),
            evaluated_at=_parse_datetime(gi.get('evaluated_at')),
        )

    # Parse audit_results if present
    audit_results_v2 = None
    if 'audit_results' in task_data and task_data['audit_results']:
        ar = task_data['audit_results']
        audit_results_v2 = AuditResults(
            issues_found=ar.get('issues_found', 0),
            issues_fixed=ar.get('issues_fixed', 0),
            recommendations=ar.get('recommendations', []),
            audit_type=ar.get('audit_type', 'general'),
            audited_at=_parse_datetime(ar.get('audited_at')) or datetime.now(timezone.utc),
        )

    return TaskTicket(
        id=task_data['id'],
        name=task_data.get('name', task_data.get('title', 'Untitled')),
        description=task_data.get('description'),
        criteria=criteria,
        parent_ref=task_data['parent_ref'],
        status=_convert_status_to_ticket_status(task_data.get('status', 'not_started')),
        created_at=_parse_datetime(task_data.get('created_at')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(task_data.get('started_at')),
        completed_at=_parse_datetime(task_data.get('completed_at')),
        updated_at=_parse_datetime(task_data.get('updated_at')) or datetime.now(timezone.utc),
        assigned_agents=task_data.get('assigned_agents', []),
        priority=_convert_priority(task_data.get('priority', 'medium')),
        commits=commits,
        estimated_duration=task_data.get('estimated_duration'),
        metadata=task_data.get('metadata', {}),
        sequence=task_data.get('sequence', 0),
        slug=task_data.get('slug', ''),
        sprint_id=task_data['sprint_id'],
        track_id=task_data['track_id'],
        roadmap_id=task_data['roadmap_id'],
        task_type_detail=_convert_task_type(task_data.get('task_type_detail', 'development')),
        title=task_data.get('title', task_data.get('name', 'Untitled')),
        phase_label=task_data.get('phase_label'),
        assigned_agent=task_data.get('assigned_agent'),
        estimated_tokens=task_data.get('estimated_tokens', 1),
        actual_tokens=task_data.get('actual_tokens'),
        complexity=_convert_complexity(task_data.get('complexity', 'medium')),
        gate_info=gate_info_v2,
        audit_results=audit_results_v2,
    )


def _migrate_task_to_ticket(task_data: Dict[str, Any]) -> TaskTicket:
    """
    Migrate v1 task data to TaskTicket (v2 model).

    Converts legacy fields to unified ticket architecture:
    - depends_on/blocked_by → stored in metadata (tasks are leaf nodes, no CompletableTarget)
    - deliverables → criteria with FileExistsTarget
    - assigned_agent → assigned_agents list
    - status → TicketStatus enum
    - created/started/completed → _at suffix timestamps
    """
    criteria = []

    # NOTE: TaskTicket is a leaf node and CANNOT have CompletableTarget criteria.
    # depends_on and blocked_by are preserved in metadata for reference but not
    # converted to criteria. The blocking logic is handled at the Sprint level.

    # Convert deliverables to file exists criteria
    for i, deliverable in enumerate(task_data.get('deliverables', [])):
        criterion = _create_deliverable_criterion(deliverable, i)
        criteria.append(criterion)

    # Parse commits
    commits = _convert_legacy_commits(task_data.get('commits', []))

    # Parse gate_info
    gate_info_v2 = None
    if 'gate_info' in task_data and task_data['gate_info']:
        gi = task_data['gate_info']
        blocks_status_str = gi.get('blocks_status', 'completed')
        gate_info_v2 = PydanticGateInfo(
            blocks_status=_convert_status_to_ticket_status(blocks_status_str),
            threshold=gi.get('threshold', 100),
            is_blocking=gi.get('is_blocking', gi.get('blocking', True)),
            score=gi.get('score'),
        )

    # Parse audit_results
    audit_results_v2 = None
    if 'audit_results' in task_data and task_data['audit_results']:
        ar = task_data['audit_results']
        audit_results_v2 = PydanticAuditResults(
            issues_found=ar.get('issues_found', 0),
            issues_fixed=ar.get('issues_fixed', 0),
            recommendations=ar.get('recommendations', []),
            audit_type=ar.get('audit_type', 'general'),
        )

    # Build assigned_agents list from singular assigned_agent
    assigned_agents = []
    if task_data.get('assigned_agent'):
        assigned_agents = [task_data['assigned_agent']]

    # Get parent references
    sprint_id = task_data.get('sprint_id', '')
    track_id = task_data.get('track_id', '')
    roadmap_id = task_data.get('roadmap_id', 'vibey-framework-v2')

    return TaskTicket(
        id=task_data['id'],
        name=task_data.get('title', task_data.get('name', 'Untitled')),
        description=task_data.get('description'),
        criteria=criteria,
        parent_ref=sprint_id,  # Task's parent is the sprint
        status=_convert_status_to_ticket_status(task_data.get('status', 'not_started')),
        created_at=_parse_datetime(task_data.get('created')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(task_data.get('started')),
        completed_at=_parse_datetime(task_data.get('completed')),
        updated_at=_parse_datetime(task_data.get('metadata', {}).get('last_updated')) or datetime.now(timezone.utc),
        assigned_agents=assigned_agents,
        priority=_convert_priority(task_data.get('priority', 'medium')),
        commits=commits,
        metadata=task_data.get('metadata', {}),
        sequence=0,  # Will be set by hierarchy computation
        slug='',
        sprint_id=sprint_id,
        track_id=track_id,
        roadmap_id=roadmap_id,
        task_type_detail=_convert_task_type(task_data.get('task_type', 'development')),
        title=task_data.get('title', task_data.get('name', 'Untitled')),
        phase_label=task_data.get('phase_label'),
        assigned_agent=task_data.get('assigned_agent'),
        estimated_tokens=task_data.get('estimated_tokens', 1) or 1,
        actual_tokens=task_data.get('actual_tokens'),
        complexity=_convert_complexity(task_data.get('complexity', 'medium')),
        gate_info=gate_info_v2,
        audit_results=audit_results_v2,
    )


def load_sprint_ticket(file_path: Union[str, Path]) -> SprintTicket:
    """
    Load a sprint from YAML file and return as SprintTicket (Pydantic model).

    This is the v2 loader that returns the new unified ticket architecture model.
    It supports both v1 (legacy) and v2 YAML formats.

    Args:
        file_path: Path to sprint.yaml file

    Returns:
        SprintTicket object (Pydantic model)
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'sprint' not in data:
        raise ValueError("Missing 'sprint' root key")

    sprint_data = data['sprint']
    format_version = detect_yaml_format(sprint_data)

    if format_version == 'v2':
        return _load_sprint_ticket_v2(sprint_data)
    else:
        logger.debug(f"Loading v1 format sprint {sprint_data.get('id')}, migrating to v2")
        return _migrate_sprint_to_ticket(sprint_data)


def _load_sprint_ticket_v2(sprint_data: Dict[str, Any]) -> SprintTicket:
    """Load SprintTicket from v2 format YAML data."""
    # Parse criteria
    criteria = []
    for c in sprint_data.get('criteria', []):
        target_type = CriterionTargetType(c['target']['type'])
        target_config = {k: v for k, v in c['target'].items() if k != 'type'}

        from ..models.ticket.targets import create_target
        target = create_target(target_type, target_config)

        criterion = Criterion(
            id=c['id'],
            description=c['description'],
            blocks_transition_to=_convert_status_to_ticket_status(c.get('blocks_transition_to', 'completed')),
            target=target,
            required=c.get('required', True),
        )
        criteria.append(criterion)

    # Parse development gates
    dev_gates = []
    for dg in sprint_data.get('development_gates', []):
        dev_gates.append(DevelopmentGate(
            name=dg['name'],
            description=dg.get('description'),
            status=GateStatus(dg.get('status', 'not_started')),
            resolved_at=_parse_datetime(dg.get('resolved_at')),
            blocking=dg.get('blocking', True),
            resolver=dg.get('resolver'),
        ))

    # Parse commits
    commits = _convert_legacy_commits(sprint_data.get('commits', []))

    return SprintTicket(
        id=sprint_data['id'],
        name=sprint_data['name'],
        description=sprint_data.get('description'),
        criteria=criteria,
        parent_ref=sprint_data['parent_ref'],
        status=_convert_status_to_ticket_status(sprint_data.get('status', 'not_started')),
        created_at=_parse_datetime(sprint_data.get('created_at')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(sprint_data.get('started_at')),
        completed_at=_parse_datetime(sprint_data.get('completed_at')),
        updated_at=_parse_datetime(sprint_data.get('updated_at')) or datetime.now(timezone.utc),
        assigned_agents=sprint_data.get('assigned_agents', []),
        priority=_convert_priority(sprint_data.get('priority', 'medium')),
        commits=commits,
        estimated_duration=sprint_data.get('estimated_duration'),
        metadata=sprint_data.get('metadata', {}),
        sequence=sprint_data.get('sequence', 0),
        slug=sprint_data.get('slug', ''),
        track_id=sprint_data['track_id'],
        roadmap_id=sprint_data['roadmap_id'],
        completion_gate_check_at=_parse_datetime(sprint_data.get('completion_gate_check_at')),
        production_gate_check_at=_parse_datetime(sprint_data.get('production_gate_check_at')),
        production_ready_at=_parse_datetime(sprint_data.get('production_ready_at')),
        deployed_at=_parse_datetime(sprint_data.get('deployed_at')),
        plan_file=sprint_data.get('plan_file'),
        goal=sprint_data.get('goal'),
        success_criteria_text=sprint_data.get('success_criteria_text', []),
        risks=sprint_data.get('risks', []),
        estimated_tokens=sprint_data.get('estimated_tokens'),
        actual_tokens=sprint_data.get('actual_tokens'),
        development_gates=dev_gates,
    )


def _migrate_sprint_to_ticket(sprint_data: Dict[str, Any]) -> SprintTicket:
    """
    Migrate v1 sprint data to SprintTicket (v2 model).

    Converts legacy fields:
    - tasks → criteria with CompletableTarget
    - depends_on → criteria (dependency)
    - quality_gates → criteria with ThresholdTarget
    """
    criteria = []

    # Convert depends_on to dependency criteria
    for i, dep in enumerate(sprint_data.get('depends_on', [])):
        if isinstance(dep, dict):
            criterion = _create_dependency_criterion(dep, i)
            criteria.append(criterion)
        elif isinstance(dep, str):
            target = CompletableTarget(
                completable_id=dep,
                required_status=TicketStatus.COMPLETED,
            )
            criteria.append(Criterion(
                id=f"dep-{dep}",
                description=f"Depends on {dep} completing",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=target,
                required=True,
            ))

    # Convert tasks to subtask criteria
    # In v1, tasks is a list of task summaries or IDs
    for task in sprint_data.get('tasks', []):
        if isinstance(task, dict):
            task_id = task.get('id', '')
            task_status_str = task.get('status', 'not_started')
            task_status = _convert_status_to_ticket_status(task_status_str)
        elif isinstance(task, str):
            task_id = task
            task_status = None
        else:
            continue

        if task_id:
            criterion = _create_subtask_criterion(task_id, task_status)
            criteria.append(criterion)

    # Convert quality_gates to threshold criteria
    for i, qg in enumerate(sprint_data.get('quality_gates', [])):
        if isinstance(qg, dict):
            criterion = _create_quality_gate_criterion(qg, i)
            criteria.append(criterion)

    # Convert deliverables to file exists criteria
    for i, deliverable in enumerate(sprint_data.get('deliverables', [])):
        if isinstance(deliverable, str):
            target = FileExistsTarget(paths=[deliverable], all_required=True)
            criteria.append(Criterion(
                id=f"deliverable-{i}",
                description=f"Deliverable: {deliverable}",
                blocks_transition_to=TicketStatus.COMPLETED,
                target=target,
                required=True,
            ))

    # Parse development gates
    dev_gates = []
    for dg in sprint_data.get('development_gates', []):
        if isinstance(dg, dict):
            dev_gates.append(DevelopmentGate(
                name=dg.get('name', f'Gate'),
                description=dg.get('description'),
                status=GateStatus(dg.get('status', 'not_started')),
                blocking=dg.get('blocking', True),
            ))

    # Parse commits
    commits = _convert_legacy_commits(sprint_data.get('commits', []))

    # Get parent references
    track_id = sprint_data.get('track_id', '')
    roadmap_id = sprint_data.get('roadmap_id', 'vibey-framework-v2')

    return SprintTicket(
        id=sprint_data['id'],
        name=sprint_data['name'],
        description=sprint_data.get('description'),
        criteria=criteria,
        parent_ref=track_id,  # Sprint's parent is the track
        status=_convert_status_to_ticket_status(sprint_data.get('status', 'not_started')),
        created_at=_parse_datetime(sprint_data.get('created')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(sprint_data.get('started')),
        completed_at=_parse_datetime(sprint_data.get('completed')),
        updated_at=_parse_datetime(sprint_data.get('metadata', {}).get('last_updated')) or datetime.now(timezone.utc),
        assigned_agents=sprint_data.get('assigned_agents', []),
        priority=_convert_priority(sprint_data.get('priority', 'medium')),
        commits=commits,
        estimated_duration=sprint_data.get('metadata', {}).get('estimated_duration'),
        metadata=sprint_data.get('metadata', {}),
        sequence=0,
        slug='',
        track_id=track_id,
        roadmap_id=roadmap_id,
        completion_gate_check_at=_parse_datetime(sprint_data.get('completion_gate_check_at')),
        production_gate_check_at=_parse_datetime(sprint_data.get('production_gate_check_at')),
        production_ready_at=_parse_datetime(sprint_data.get('production_ready_at')),
        deployed_at=_parse_datetime(sprint_data.get('deployed_at')),
        plan_file=sprint_data.get('plan_file'),
        goal=sprint_data.get('goal'),
        success_criteria_text=sprint_data.get('success_criteria', []),
        risks=sprint_data.get('risks', []),
        estimated_tokens=sprint_data.get('metadata', {}).get('estimated_tokens'),
        actual_tokens=sprint_data.get('metadata', {}).get('actual_tokens'),
        development_gates=dev_gates,
    )


def load_track_ticket(file_path: Union[str, Path]) -> TrackTicket:
    """
    Load a track from YAML file and return as TrackTicket (Pydantic model).

    Args:
        file_path: Path to track.yaml file

    Returns:
        TrackTicket object (Pydantic model)
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'track' not in data:
        raise ValueError("Missing 'track' root key")

    track_data = data['track']
    format_version = detect_yaml_format(track_data)

    if format_version == 'v2':
        return _load_track_ticket_v2(track_data)
    else:
        logger.debug(f"Loading v1 format track {track_data.get('id')}, migrating to v2")
        return _migrate_track_to_ticket(track_data)


def _load_track_ticket_v2(track_data: Dict[str, Any]) -> TrackTicket:
    """Load TrackTicket from v2 format YAML data."""
    # Parse criteria
    criteria = []
    for c in track_data.get('criteria', []):
        target_type = CriterionTargetType(c['target']['type'])
        target_config = {k: v for k, v in c['target'].items() if k != 'type'}

        from ..models.ticket.targets import create_target
        target = create_target(target_type, target_config)

        criterion = Criterion(
            id=c['id'],
            description=c['description'],
            blocks_transition_to=_convert_status_to_ticket_status(c.get('blocks_transition_to', 'completed')),
            target=target,
            required=c.get('required', True),
        )
        criteria.append(criterion)

    # Parse commits
    commits = _convert_legacy_commits(track_data.get('commits', []))

    return TrackTicket(
        id=track_data['id'],
        name=track_data['name'],
        description=track_data.get('description'),
        criteria=criteria,
        parent_ref=track_data['parent_ref'],
        status=_convert_status_to_ticket_status(track_data.get('status', 'not_started')),
        created_at=_parse_datetime(track_data.get('created_at')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(track_data.get('started_at')),
        completed_at=_parse_datetime(track_data.get('completed_at')),
        updated_at=_parse_datetime(track_data.get('updated_at')) or datetime.now(timezone.utc),
        assigned_agents=track_data.get('assigned_agents', []),
        priority=_convert_priority(track_data.get('priority', 'medium')),
        commits=commits,
        estimated_duration=track_data.get('estimated_duration'),
        metadata=track_data.get('metadata', {}),
        sequence=track_data.get('sequence', 0),
        slug=track_data.get('slug', ''),
        roadmap_id=track_data['roadmap_id'],
        strategic_value=track_data.get('strategic_value', []),
    )


def _migrate_track_to_ticket(track_data: Dict[str, Any]) -> TrackTicket:
    """
    Migrate v1 track data to TrackTicket (v2 model).

    Converts legacy fields:
    - sprints → criteria with CompletableTarget
    - depends_on → criteria (dependency)
    - quality_gates → criteria with ThresholdTarget
    """
    criteria = []

    # Convert depends_on to dependency criteria
    for i, dep in enumerate(track_data.get('depends_on', [])):
        if isinstance(dep, dict):
            criterion = _create_dependency_criterion(dep, i)
            criteria.append(criterion)
        elif isinstance(dep, str):
            target = CompletableTarget(
                completable_id=dep,
                required_status=TicketStatus.COMPLETED,
            )
            criteria.append(Criterion(
                id=f"dep-{dep}",
                description=f"Depends on {dep} completing",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=target,
                required=True,
            ))

    # Convert sprints to subtask criteria
    for sprint in track_data.get('sprints', []):
        if isinstance(sprint, dict):
            sprint_id = sprint.get('id', '')
            sprint_status_str = sprint.get('status', 'not_started')
            sprint_status = _convert_status_to_ticket_status(sprint_status_str)
        elif isinstance(sprint, str):
            sprint_id = sprint
            sprint_status = None
        else:
            continue

        if sprint_id:
            target = CompletableTarget(
                completable_id=sprint_id,
                required_status=TicketStatus.COMPLETED,
                current_status=sprint_status,
            )
            criteria.append(Criterion(
                id=f"sprint-{sprint_id}",
                description=f"Sprint {sprint_id} must complete",
                blocks_transition_to=TicketStatus.COMPLETED,
                target=target,
                required=True,
            ))

    # Convert quality_gates to threshold criteria
    for i, qg in enumerate(track_data.get('quality_gates', [])):
        if isinstance(qg, dict):
            criterion = _create_quality_gate_criterion(qg, i)
            criteria.append(criterion)

    # Parse commits
    commits = _convert_legacy_commits(track_data.get('commits', []))

    # Get parent reference
    roadmap_id = track_data.get('roadmap_id', 'vibey-framework-v2')

    return TrackTicket(
        id=track_data['id'],
        name=track_data['name'],
        description=track_data.get('metadata', {}).get('notes'),
        criteria=criteria,
        parent_ref=roadmap_id,  # Track's parent is the roadmap
        status=_convert_status_to_ticket_status(track_data.get('status', 'not_started')),
        created_at=_parse_datetime(track_data.get('created')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(track_data.get('started')),
        completed_at=_parse_datetime(track_data.get('completed')),
        updated_at=_parse_datetime(track_data.get('metadata', {}).get('last_updated')) or datetime.now(timezone.utc),
        assigned_agents=track_data.get('assigned_agents', []),
        priority=_convert_priority(track_data.get('priority', 'medium')),
        commits=commits,
        estimated_duration=track_data.get('estimated_duration'),
        metadata=track_data.get('metadata', {}),
        sequence=0,
        slug='',
        roadmap_id=roadmap_id,
        strategic_value=track_data.get('strategic_value', []),
    )


def load_roadmap_ticket(file_path: Union[str, Path]) -> RoadmapTicket:
    """
    Load a roadmap from YAML file and return as RoadmapTicket (Pydantic model).

    Args:
        file_path: Path to roadmap.yaml file

    Returns:
        RoadmapTicket object (Pydantic model)
    """
    file_path = Path(file_path)

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if 'roadmap' not in data:
        raise ValueError("Missing 'roadmap' root key")

    roadmap_data = data['roadmap']
    format_version = detect_yaml_format(roadmap_data)

    if format_version == 'v2':
        return _load_roadmap_ticket_v2(roadmap_data)
    else:
        logger.debug(f"Loading v1 format roadmap {roadmap_data.get('id')}, migrating to v2")
        return _migrate_roadmap_to_ticket(roadmap_data)


def _load_roadmap_ticket_v2(roadmap_data: Dict[str, Any]) -> RoadmapTicket:
    """Load RoadmapTicket from v2 format YAML data."""
    # Parse criteria
    criteria = []
    for c in roadmap_data.get('criteria', []):
        target_type = CriterionTargetType(c['target']['type'])
        target_config = {k: v for k, v in c['target'].items() if k != 'type'}

        from ..models.ticket.targets import create_target
        target = create_target(target_type, target_config)

        criterion = Criterion(
            id=c['id'],
            description=c['description'],
            blocks_transition_to=_convert_status_to_ticket_status(c.get('blocks_transition_to', 'completed')),
            target=target,
            required=c.get('required', True),
        )
        criteria.append(criterion)

    # Parse version history
    version_history = []
    for vh in roadmap_data.get('version_history', []):
        version_history.append(VersionHistoryEntry(
            version=vh['version'],
            released_at=_parse_datetime(vh['released_at']) or datetime.now(timezone.utc),
            milestone=vh.get('milestone'),
            git_tag=vh.get('git_tag'),
            description=vh.get('description'),
        ))

    # Parse activity log
    activity_log = []
    for al in roadmap_data.get('activity_log', []):
        activity_log.append(ActivityLogEntry(
            timestamp=_parse_datetime(al['timestamp']) or datetime.now(timezone.utc),
            action=PydanticActivityType(al['action']),
            ticket_id=al.get('ticket_id'),
            actor=al.get('actor'),
            details=al.get('details'),
            context=al.get('context'),
        ))

    # Parse deployed platforms
    deployed_platforms = []
    for p in roadmap_data.get('deployed_platforms', []):
        deployed_platforms.append(PydanticPlatformDeployment(
            platform=p['platform'],
            context_window=p.get('context_window'),
            deployed_at=_parse_datetime(p.get('deployed_at')),
            primary=p.get('primary', False),
            version=p.get('version'),
        ))

    # Parse version strategy
    version_strategy = None
    if 'version_strategy' in roadmap_data and roadmap_data['version_strategy']:
        vs = roadmap_data['version_strategy']
        version_strategy = PydanticVersionStrategy(
            scheme=vs.get('scheme', 'semver'),
            auto_bump=vs.get('auto_bump', False),
            major_triggers=vs.get('major_triggers', []),
            minor_triggers=vs.get('minor_triggers', []),
            patch_triggers=vs.get('patch_triggers', []),
        )

    # Parse commits
    commits = _convert_legacy_commits(roadmap_data.get('commits', []))

    return RoadmapTicket(
        id=roadmap_data['id'],
        name=roadmap_data['name'],
        description=roadmap_data.get('description'),
        criteria=criteria,
        parent_ref=None,  # Roadmap has no parent
        status=_convert_status_to_ticket_status(roadmap_data.get('status', 'not_started')),
        created_at=_parse_datetime(roadmap_data.get('created_at')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(roadmap_data.get('started_at')),
        completed_at=_parse_datetime(roadmap_data.get('completed_at')),
        updated_at=_parse_datetime(roadmap_data.get('updated_at')) or datetime.now(timezone.utc),
        assigned_agents=roadmap_data.get('assigned_agents', []),
        priority=_convert_priority(roadmap_data.get('priority', 'medium')),
        commits=commits,
        estimated_duration=roadmap_data.get('estimated_duration'),
        metadata=roadmap_data.get('metadata', {}),
        sequence=0,
        slug='',
        version=roadmap_data.get('version', '0.1.0'),
        version_strategy=version_strategy,
        version_history=version_history,
        target_completion=_parse_datetime(roadmap_data.get('target_completion')),
        deployed_at=_parse_datetime(roadmap_data.get('deployed_at')),
        deployed_platforms=deployed_platforms,
        activity_log=activity_log,
    )


def _migrate_roadmap_to_ticket(roadmap_data: Dict[str, Any]) -> RoadmapTicket:
    """
    Migrate v1 roadmap data to RoadmapTicket (v2 model).

    Converts legacy fields:
    - tracks → criteria with CompletableTarget
    - dependencies → criteria
    - version_strategy (old format) → new VersionStrategy
    """
    criteria = []

    # Convert dependencies to dependency criteria
    for i, dep in enumerate(roadmap_data.get('dependencies', [])):
        if isinstance(dep, dict):
            target = CompletableTarget(
                completable_id=dep.get('name', f'dep-{i}'),
                required_status=TicketStatus.COMPLETED,
            )
            criteria.append(Criterion(
                id=f"dep-{i}",
                description=f"Dependency: {dep.get('name', 'unknown')}",
                blocks_transition_to=TicketStatus.IN_PROGRESS,
                target=target,
                required=True,
            ))

    # Convert tracks to subtask criteria
    for track in roadmap_data.get('tracks', []):
        if isinstance(track, dict):
            track_id = track.get('id', '')
            track_status_str = track.get('status', 'not_started')
            track_status = _convert_status_to_ticket_status(track_status_str)
        elif isinstance(track, str):
            track_id = track
            track_status = None
        else:
            continue

        if track_id:
            target = CompletableTarget(
                completable_id=track_id,
                required_status=TicketStatus.COMPLETED,
                current_status=track_status,
            )
            criteria.append(Criterion(
                id=f"track-{track_id}",
                description=f"Track {track_id} must complete",
                blocks_transition_to=TicketStatus.COMPLETED,
                target=target,
                required=True,
            ))

    # Parse version history
    version_history = []
    for vh in roadmap_data.get('version_history', []):
        version_history.append(VersionHistoryEntry(
            version=vh.get('version', '0.0.0'),
            released_at=_parse_datetime(vh.get('date')) or datetime.now(timezone.utc),
            milestone=vh.get('milestone'),
            git_tag=vh.get('git_tag'),
            description=vh.get('description'),
        ))

    # Parse activity log
    activity_log = []
    for al in roadmap_data.get('activity_log', []):
        # Map old activity type to new
        activity_type_str = al.get('type', 'system')
        try:
            activity_type = PydanticActivityType(activity_type_str)
        except ValueError:
            activity_type = PydanticActivityType.SYSTEM

        activity_log.append(ActivityLogEntry(
            timestamp=_parse_datetime(al.get('timestamp')) or datetime.now(timezone.utc),
            action=activity_type,
            details=al.get('description'),
            context=al.get('context'),
        ))

    # Parse deployed platforms
    deployed_platforms = []
    for p in roadmap_data.get('deployed_platforms', []):
        deployed_platforms.append(PydanticPlatformDeployment(
            platform=p.get('platform', 'unknown'),
            context_window=p.get('context_window'),
            deployed_at=datetime.fromtimestamp(p['deployed_at'], tz=timezone.utc) if isinstance(p.get('deployed_at'), int) else _parse_datetime(p.get('deployed_at')),
            primary=p.get('primary', False),
        ))

    # Parse version strategy (old format)
    version_strategy = None
    if 'version_strategy' in roadmap_data and roadmap_data['version_strategy']:
        vs = roadmap_data['version_strategy']
        version_strategy = PydanticVersionStrategy(
            scheme='semver',
            auto_bump=False,
            major_triggers=[vs.get('major_on', 'roadmap_milestone')],
            minor_triggers=[vs.get('minor_on', 'track_completion')],
            patch_triggers=[vs.get('patch_on', 'sprint_production_ready')],
        )

    # Parse commits
    commits = _convert_legacy_commits(roadmap_data.get('commits', []))

    return RoadmapTicket(
        id=roadmap_data['id'],
        name=roadmap_data['name'],
        description=roadmap_data.get('metadata', {}).get('description'),
        criteria=criteria,
        parent_ref=None,  # Roadmap has no parent
        status=_convert_status_to_ticket_status(roadmap_data.get('status', 'not_started')),
        created_at=_parse_datetime(roadmap_data.get('created')) or datetime.now(timezone.utc),
        started_at=_parse_datetime(roadmap_data.get('started')),
        completed_at=_parse_datetime(roadmap_data.get('completed')),
        updated_at=_parse_datetime(roadmap_data.get('metadata', {}).get('last_updated')) or datetime.now(timezone.utc),
        assigned_agents=[],
        priority=Priority.HIGH,
        commits=commits,
        metadata=roadmap_data.get('metadata', {}),
        sequence=0,
        slug='',
        version=roadmap_data.get('version', '0.1.0'),
        version_strategy=version_strategy,
        version_history=version_history,
        target_completion=_parse_datetime(roadmap_data.get('target_completion')),
        deployed_at=_parse_datetime(roadmap_data.get('deployed')),
        deployed_platforms=deployed_platforms,
        activity_log=activity_log,
    )
