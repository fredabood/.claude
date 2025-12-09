# SQL Dumper v2.0.0 Design Document

**Date:** 2025-12-09
**Sprint:** unified-arch-2 (Database Schema Migration)
**Task:** unified-arch-2-task-006
**Status:** Design Complete

---

## Overview

Update `vibey/roadmap/serialization/sql_dumper.py` (1121 lines) to support both v1.0.0 (27 tables) and v2.0.0 (2 tables) database schemas during the migration transition period.

---

## Current Architecture (v1.0.0)

### Dumper Functions:
```python
dump_roadmap(roadmap: Roadmap) -> None
dump_track(track: Track) -> None
dump_sprint(sprint: Sprint) -> None
dump_task(task: Task) -> None
```

### Write Pattern (Example - dump_track):
```sql
-- Insert main data
INSERT OR REPLACE INTO tracks (id, roadmap_id, name, status, ...) VALUES (?, ?, ?, ?, ...)

-- Insert related data
INSERT INTO sprints (id, track_id, ...) VALUES (?, ?, ...)
INSERT INTO entity_blocked_by (blocked_id, blocker_id, ...) VALUES (?, ?, ...)
INSERT INTO quality_gates (owner_type, owner_id, ...) VALUES ('track', ?, ...)
```

### Serialization Helpers:
- `_serialize_commits()` → JSON string
- `_serialize_deliverables()` → JSON string
- `_serialize_standards()` → JSON string
- `_serialize_sprint_summaries()` → JSON string
- `_serialize_task_summaries()` → JSON string

---

## Target Architecture (v2.0.0)

### New Dumper Functions:
```python
dump_roadmap_v2(roadmap: Roadmap) -> None
dump_track_v2(track: Track) -> None
dump_sprint_v2(sprint: Sprint) -> None
dump_task_v2(task: Task) -> None
dump_criteria(completable_id: str, criteria: List[Criterion]) -> None
```

### Write Pattern (Example - dump_track_v2):
```sql
-- Insert into completables table
INSERT OR REPLACE INTO completables (
    id, name, completable_type, ticket_type, parent_id, status,
    created_at, started_at, completed_at, priority,
    strategic_value_json, commits_json, assigned_agents_json,
    metadata_json, updated_at, sequence, legacy_roadmap_id
) VALUES (?, ?, 'ticket', 'track', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

-- Insert criteria (replaces blocked_by, depends_on, quality_gates, deliverables)
INSERT OR REPLACE INTO criteria (
    id, completable_id, description, required,
    blocks_transition_to, target_type, target_json,
    is_met, last_checked, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

---

## Implementation Strategy

### Phase 1: Schema Version Detection

Reuse detection function from sql_loader:

```python
from .sql_loader import detect_schema_version

def dump_roadmap(roadmap: Roadmap) -> None:
    """Dump roadmap to database (auto-detects schema version)."""
    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        dump_roadmap_v2(roadmap)
    else:
        dump_roadmap_v1(roadmap)
```

### Phase 2: V2 Dumper Functions

Create parallel v2 dumpers:

#### A. dump_roadmap_v2()

```python
def dump_roadmap_v2(roadmap: Roadmap) -> None:
    """
    Dump roadmap to v2.0.0 schema (completables table).

    Args:
        roadmap: Roadmap object to save
    """
    conn = get_connection()

    with transaction(conn):
        # Insert into completables
        conn.execute("""
            INSERT OR REPLACE INTO completables (
                id, name, completable_type, ticket_type, status,
                created_at, started_at, completed_at,
                version, version_strategy_json, activity_log_json,
                metadata_json, updated_at, sequence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roadmap.id,
            roadmap.name,
            'ticket',
            'roadmap',
            roadmap.status.value,
            _format_datetime(roadmap.created),
            _format_datetime(roadmap.started),
            _format_datetime(roadmap.completed),
            roadmap.version,
            _serialize_version_strategy(roadmap.version_strategy),
            _serialize_activity_log(roadmap.activity_log),
            _serialize_metadata(roadmap.metadata),
            _format_datetime(datetime.now()),
            0
        ))

        # Convert dependencies → criteria
        if roadmap.dependencies:
            dump_criteria_from_dependencies(roadmap.id, roadmap.dependencies)

        # Note: Track summaries are children in v2, not stored in roadmap


def _serialize_version_strategy(vs) -> str:
    """Serialize VersionStrategy to JSON."""
    if vs is None:
        return json.dumps({})

    return json.dumps({
        'major_on': vs.major_on.value if hasattr(vs.major_on, 'value') else str(vs.major_on),
        'minor_on': vs.minor_on.value if hasattr(vs.minor_on, 'value') else str(vs.minor_on),
        'patch_on': vs.patch_on.value if hasattr(vs.patch_on, 'value') else str(vs.patch_on),
    })


def _serialize_activity_log(log: list) -> str:
    """Serialize activity log to JSON array."""
    if not log:
        return json.dumps([])

    return json.dumps([
        {
            'timestamp': _format_datetime(entry.timestamp),
            'type': entry.type.value if hasattr(entry.type, 'value') else str(entry.type),
            'description': entry.description,
            'context': entry.context,
        }
        for entry in log
    ])


def _serialize_metadata(meta) -> str:
    """Serialize Metadata to JSON."""
    if meta is None:
        return json.dumps({})

    return json.dumps({
        'created_by': meta.created_by,
        'framework_version': meta.framework_version,
        'schema_version': '2.0.0',
        'last_updated': _format_datetime(meta.last_updated),
        'purpose': meta.purpose,
        'description': meta.description,
    })
```

#### B. dump_track_v2()

```python
def dump_track_v2(track: Track) -> None:
    """
    Dump track to v2.0.0 schema (completables table).

    Args:
        track: Track object to save
    """
    conn = get_connection()

    with transaction(conn):
        # Insert into completables
        conn.execute("""
            INSERT OR REPLACE INTO completables (
                id, name, completable_type, ticket_type, parent_id, status,
                created_at, started_at, completed_at,
                priority, estimated_duration,
                strategic_value_json, commits_json, assigned_agents_json,
                requirements_local_json, metadata_json,
                updated_at, sequence, slug, legacy_roadmap_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            track.id,
            track.name,
            'ticket',
            'track',
            track.roadmap_id,
            track.status.value,
            _format_datetime(track.created),
            _format_datetime(track.started),
            _format_datetime(track.completed),
            track.priority.value if track.priority else None,
            track.estimated_duration,
            _serialize_strategic_value(track.strategic_value),
            _serialize_commits(track.commits),
            _serialize_assigned_agents(track.assigned_agents),
            _serialize_dependencies_as_requirements(track.dependencies),
            _serialize_track_metadata(track.metadata),
            _format_datetime(datetime.now()),
            0,  # sequence
            track.slug,
            track.roadmap_id
        ))

        # Convert blocked_by → CompletableTarget criteria (blocks IN_PROGRESS)
        if track.blocked_by:
            dump_criteria_from_blockers(
                track.id,
                track.blocked_by,
                blocks_transition='in_progress'
            )

        # Convert depends_on → CompletableTarget criteria (blocks COMPLETED, optional)
        if track.depends_on:
            dump_criteria_from_dependencies_v2(
                track.id,
                track.depends_on,
                blocks_transition='completed',
                required=False
            )

        # Convert quality_gates → ThresholdTarget criteria
        if track.quality_gates:
            dump_criteria_from_quality_gates(track.id, track.quality_gates)

        # Convert deliverables → FileExistsTarget criteria
        if track.deliverables:
            dump_criteria_from_deliverables(track.id, track.deliverables)


def _serialize_strategic_value(values: list) -> str:
    """Serialize strategic value list to JSON array."""
    if not values:
        return json.dumps([])
    return json.dumps(values)


def _serialize_assigned_agents(agents: list) -> str:
    """Serialize assigned agents to JSON array."""
    if not agents:
        return json.dumps([])
    return json.dumps(agents)


def _serialize_dependencies_as_requirements(deps: list) -> str:
    """Serialize external dependencies as requirements JSON."""
    if not deps:
        return json.dumps([])

    return json.dumps([
        {
            'type': dep.type,
            'name': dep.name,
            'status': dep.status,
            'required_for': dep.required_for,
        }
        for dep in deps
    ])


def _serialize_track_metadata(meta) -> str:
    """Serialize TrackMetadata to JSON."""
    if meta is None:
        return json.dumps({})

    return json.dumps({
        'created_by': getattr(meta, 'created_by', None),
        'last_updated': _format_datetime(getattr(meta, 'last_updated', None)),
    })
```

#### C. dump_sprint_v2()

```python
def dump_sprint_v2(sprint: Sprint) -> None:
    """
    Dump sprint to v2.0.0 schema (completables table).

    Args:
        sprint: Sprint object to save
    """
    conn = get_connection()

    with transaction(conn):
        # Insert into completables
        conn.execute("""
            INSERT OR REPLACE INTO completables (
                id, name, description, completable_type, ticket_type, parent_id, status,
                created_at, started_at, completed_at,
                completion_gate_check_at, production_gate_check_at,
                production_ready_at, deployed_at,
                plan_file, goal, estimated_duration, blocked_reason,
                success_criteria_json, development_gates_json,
                commits_json, assigned_agents_json,
                requirements_local_json, metadata_json,
                updated_at, sequence, slug,
                legacy_track_id, legacy_roadmap_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sprint.id,
            sprint.name,
            sprint.description,
            'ticket',
            'sprint',
            sprint.track_id,  # parent_id for hierarchy
            sprint.status.value,
            _format_datetime(sprint.created),
            _format_datetime(sprint.started),
            _format_datetime(sprint.completed),
            _format_datetime(getattr(sprint, 'completion_gate_check_at', None)),
            _format_datetime(getattr(sprint, 'production_gate_check_at', None)),
            _format_datetime(getattr(sprint, 'production_ready_at', None)),
            _format_datetime(getattr(sprint, 'deployed_at', None)),
            sprint.plan_file,
            sprint.goal,
            sprint.estimated_duration,
            sprint.blocked_reason if sprint.blocked else None,
            _serialize_success_criteria(sprint.success_criteria),
            _serialize_development_gates(sprint.development_gates),
            _serialize_commits(sprint.commits),
            _serialize_assigned_agents(sprint.assigned_agents),
            _serialize_dependencies_as_requirements(sprint.dependencies),
            _serialize_sprint_metadata(sprint.metadata),
            _format_datetime(datetime.now()),
            0,  # sequence
            sprint.slug,
            sprint.track_id,
            sprint.roadmap_id
        ))

        # Convert blocked_by → criteria
        if sprint.blocked_by:
            dump_criteria_from_blockers(sprint.id, sprint.blocked_by, 'in_progress')

        # Convert depends_on → criteria
        if sprint.depends_on:
            dump_criteria_from_dependencies_v2(sprint.id, sprint.depends_on, 'completed', False)

        # Convert development_gates → criteria
        if sprint.development_gates:
            dump_criteria_from_development_gates(sprint.id, sprint.development_gates)

        # Convert deliverables → criteria
        if sprint.deliverables:
            dump_criteria_from_deliverables(sprint.id, sprint.deliverables)


def _serialize_success_criteria(criteria: list) -> str:
    """Serialize success criteria to JSON array."""
    if not criteria:
        return json.dumps([])
    return json.dumps(criteria)


def _serialize_development_gates(gates: list) -> str:
    """Serialize development gates to JSON array."""
    if not gates:
        return json.dumps([])

    return json.dumps([
        {
            'name': gate.name,
            'description': gate.description,
            'status': gate.status.value if hasattr(gate.status, 'value') else str(gate.status),
            'resolved_at': _format_datetime(getattr(gate, 'resolved_at', None)),
        }
        for gate in gates
    ])


def _serialize_sprint_metadata(meta) -> str:
    """Serialize SprintMetadata to JSON."""
    if meta is None:
        return json.dumps({})

    return json.dumps({
        'created_by': getattr(meta, 'created_by', None),
        'last_updated': _format_datetime(getattr(meta, 'last_updated', None)),
    })
```

#### D. dump_task_v2()

```python
def dump_task_v2(task: Task) -> None:
    """
    Dump task to v2.0.0 schema (completables table).

    Args:
        task: Task object to save
    """
    conn = get_connection()

    with transaction(conn):
        # Insert into completables
        conn.execute("""
            INSERT OR REPLACE INTO completables (
                id, name, description, completable_type, ticket_type, parent_id, status,
                created_at, started_at, completed_at,
                task_type_detail, priority, phase_label,
                estimated_tokens, actual_tokens, complexity,
                gate_info_json, audit_results_json,
                commits_json, assigned_agents_json,
                requirements_local_json, metadata_json,
                estimated_duration,
                updated_at, sequence, slug,
                legacy_sprint_id, legacy_track_id, legacy_roadmap_id,
                deferred
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.title,
            task.description,
            'ticket',
            'task',
            task.sprint_id,  # parent_id
            task.status.value,
            _format_datetime(task.created),
            _format_datetime(task.started),
            _format_datetime(task.completed),
            task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
            task.priority.value if task.priority else None,
            task.phase_label,
            task.estimated_tokens,
            task.actual_tokens,
            task.complexity.value if task.complexity else None,
            _serialize_gate_info(task.gate_info),
            _serialize_audit_results(task.audit_results),
            _serialize_commits(task.commits),
            _serialize_assigned_agents(task.assigned_agents),
            _serialize_dependencies_as_requirements(task.dependencies),
            _serialize_task_metadata(task.metadata),
            task.estimated_duration,
            _format_datetime(datetime.now()),
            0,  # sequence
            task.slug,
            task.sprint_id,
            task.track_id,
            task.roadmap_id,
            1 if getattr(task, 'deferred', False) else 0
        ))

        # Convert blocked_by → criteria
        if task.blocked_by:
            dump_criteria_from_blockers(task.id, task.blocked_by, 'in_progress')

        # Convert depends_on → criteria
        if task.depends_on:
            dump_criteria_from_dependencies_v2(task.id, task.depends_on, 'completed', False)

        # Convert deliverables → criteria
        if task.deliverables:
            dump_criteria_from_deliverables(task.id, task.deliverables)


def _serialize_gate_info(info) -> Optional[str]:
    """Serialize gate info to JSON."""
    if info is None:
        return None

    return json.dumps({
        'gate_type': getattr(info, 'gate_type', None),
        'criteria': getattr(info, 'criteria', []),
        'status': getattr(info, 'status', 'pending'),
    })


def _serialize_audit_results(results) -> Optional[str]:
    """Serialize audit results to JSON."""
    if results is None:
        return None

    return json.dumps({
        'passed': getattr(results, 'passed', False),
        'issues': getattr(results, 'issues', []),
        'score': getattr(results, 'score', None),
    })


def _serialize_task_metadata(meta) -> str:
    """Serialize TaskMetadata to JSON."""
    if meta is None:
        return json.dumps({})

    return json.dumps({
        'created_by': getattr(meta, 'created_by', None),
        'last_updated': _format_datetime(getattr(meta, 'last_updated', None)),
        'token_efficiency': getattr(meta, 'token_efficiency', None),
        'duration_hours': getattr(meta, 'duration_hours', None),
    })
```

#### E. dump_criteria() and Helper Functions

```python
def dump_criteria(completable_id: str, criteria: List[Criterion]) -> None:
    """
    Dump criteria for a completable entity.

    Args:
        completable_id: ID of the completable (roadmap, track, sprint, task, artifact)
        criteria: List of Criterion objects to save
    """
    conn = get_connection()

    with transaction(conn):
        # Delete existing criteria for this completable
        conn.execute(
            "DELETE FROM criteria WHERE completable_id = ?",
            (completable_id,)
        )

        # Insert new criteria
        for criterion in criteria:
            target_json = _serialize_criterion_target(criterion.target, criterion.target_type)

            conn.execute("""
                INSERT INTO criteria (
                    id, completable_id, description, required,
                    blocks_transition_to, target_type, target_json,
                    is_met, last_checked, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                criterion.id,
                completable_id,
                criterion.description,
                1 if criterion.required else 0,
                criterion.blocks_transition_to,
                criterion.target_type,
                target_json,
                1 if criterion.is_met else (0 if criterion.is_met is False else None),
                _format_datetime(criterion.last_checked),
                _format_datetime(criterion.created_at),
                _format_datetime(criterion.updated_at or datetime.now()),
            ))


def _serialize_criterion_target(target, target_type: str) -> str:
    """
    Serialize criterion target based on target_type.

    Args:
        target: Target object (CompletableTarget, FileExistsTarget, etc.)
        target_type: Type of target ('completable', 'file_exists', etc.)

    Returns:
        JSON string of target configuration
    """
    if target_type == 'completable':
        return json.dumps({
            'type': 'completable',
            'completable_id': target.completable_id,
            'required_status': target.required_status.value if hasattr(target.required_status, 'value') else str(target.required_status),
        })

    elif target_type == 'file_exists':
        return json.dumps({
            'type': 'file_exists',
            'paths': target.paths,
            'all_required': target.all_required,
        })

    elif target_type == 'test_passes':
        return json.dumps({
            'type': 'test_passes',
            'test_command': target.test_command,
            'pass_threshold': target.pass_threshold,
        })

    elif target_type == 'threshold':
        return json.dumps({
            'type': 'threshold',
            'metric_name': target.metric_name,
            'threshold': target.threshold,
            'comparison': target.comparison,
        })

    elif target_type == 'manual':
        return json.dumps({
            'type': 'manual',
            'instructions': target.instructions,
            'approver': getattr(target, 'approver', None),
        })

    else:
        # Generic serialization for other types
        return json.dumps(target) if isinstance(target, dict) else json.dumps({})


def dump_criteria_from_blockers(completable_id: str, blockers: list, blocks_transition: str = 'in_progress') -> None:
    """
    Convert blocked_by list to CompletableTarget criteria.

    Args:
        completable_id: ID of blocked entity
        blockers: List of Blocker objects
        blocks_transition: Which transition to block (default: 'in_progress')
    """
    conn = get_connection()

    for blocker in blockers:
        criterion_id = f"crit-{completable_id}-{blocker.blocker_id}"
        target_json = json.dumps({
            'type': 'completable',
            'completable_id': blocker.blocker_id,
            'required_status': blocker.required_status.value if hasattr(blocker.required_status, 'value') else str(blocker.required_status),
        })

        conn.execute("""
            INSERT OR REPLACE INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id,
            completable_id,
            blocker.description or f"{blocker.blocker_type} {blocker.blocker_id} must complete",
            1,  # required=True for hard blockers
            blocks_transition,
            'completable',
            target_json,
            _format_datetime(datetime.now()),
            _format_datetime(datetime.now()),
        ))


def dump_criteria_from_dependencies_v2(completable_id: str, dependencies: list, blocks_transition: str = 'completed', required: bool = False) -> None:
    """
    Convert depends_on list to CompletableTarget criteria.

    Args:
        completable_id: ID of dependent entity
        dependencies: List of Dependency objects
        blocks_transition: Which transition to block (default: 'completed')
        required: Whether these are hard requirements (default: False for soft dependencies)
    """
    conn = get_connection()

    for dep in dependencies:
        criterion_id = f"dep-{completable_id}-{dep.blocker_id}"
        target_json = json.dumps({
            'type': 'completable',
            'completable_id': dep.blocker_id,
            'required_status': dep.required_status.value if hasattr(dep.required_status, 'value') else str(dep.required_status),
        })

        conn.execute("""
            INSERT OR REPLACE INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                is_met, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id,
            completable_id,
            dep.description or f"Depends on {dep.blocker_type} {dep.blocker_id}",
            1 if required else 0,
            blocks_transition,
            'completable',
            target_json,
            1 if dep.status == 'resolved' else 0 if dep.status == 'pending' else None,
            _format_datetime(datetime.now()),
            _format_datetime(datetime.now()),
        ))


def dump_criteria_from_deliverables(completable_id: str, deliverables: list) -> None:
    """
    Convert deliverables to FileExistsTarget criteria.

    Args:
        completable_id: ID of entity with deliverables
        deliverables: List of Deliverable objects
    """
    conn = get_connection()

    for idx, deliverable in enumerate(deliverables):
        criterion_id = f"file-{completable_id}-{idx}"
        paths = getattr(deliverable, 'paths', [])

        if not paths:
            continue

        target_json = json.dumps({
            'type': 'file_exists',
            'paths': paths,
            'all_required': True,
        })

        conn.execute("""
            INSERT OR REPLACE INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id,
            completable_id,
            f"Deliverable: {' '.join(paths)}",
            1,  # required=True for deliverables
            'completed',
            'file_exists',
            target_json,
            _format_datetime(datetime.now()),
            _format_datetime(datetime.now()),
        ))


def dump_criteria_from_quality_gates(completable_id: str, gates: list) -> None:
    """
    Convert quality gates to ThresholdTarget criteria.

    Args:
        completable_id: ID of entity with quality gates
        gates: List of QualityGate objects
    """
    conn = get_connection()

    for gate in gates:
        criterion_id = f"gate-{completable_id}-{gate.name.lower().replace(' ', '-')}"
        target_json = json.dumps({
            'type': 'threshold',
            'metric_name': gate.name,
            'threshold': gate.threshold,
            'comparison': '>=',
        })

        conn.execute("""
            INSERT OR REPLACE INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                is_met, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id,
            completable_id,
            gate.description or gate.name,
            1 if gate.blocking else 0,
            'completed',
            'threshold',
            target_json,
            1 if gate.status == 'passed' else 0 if gate.status == 'failed' else None,
            _format_datetime(datetime.now()),
            _format_datetime(datetime.now()),
        ))


def dump_criteria_from_development_gates(completable_id: str, gates: list) -> None:
    """
    Convert development gates to ExternalTarget criteria.

    Args:
        completable_id: ID of sprint with development gates
        gates: List of DevelopmentGate objects
    """
    conn = get_connection()

    for gate in gates:
        criterion_id = f"devgate-{completable_id}-{gate.name.lower().replace(' ', '-')}"
        target_json = json.dumps({
            'type': 'external',
            'name': gate.name,
            'description': gate.description,
        })

        conn.execute("""
            INSERT OR REPLACE INTO criteria (
                id, completable_id, description, required,
                blocks_transition_to, target_type, target_json,
                is_met, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            criterion_id,
            completable_id,
            gate.description or gate.name,
            1,  # required=True for development gates
            'in_progress',
            'external',
            target_json,
            1 if gate.status == 'resolved' else 0 if gate.status == 'pending' else None,
            _format_datetime(datetime.now()),
            _format_datetime(datetime.now()),
        ))
```

### Phase 3: Dispatcher Functions

```python
def dump_roadmap(roadmap: Roadmap) -> None:
    """Dump roadmap to database (auto-detects schema version)."""
    from .sql_loader import detect_schema_version

    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        dump_roadmap_v2(roadmap)
    else:
        dump_roadmap_v1(roadmap)


def dump_track(track: Track) -> None:
    """Dump track to database (auto-detects schema version)."""
    from .sql_loader import detect_schema_version

    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        dump_track_v2(track)
    else:
        dump_track_v1(track)


def dump_sprint(sprint: Sprint) -> None:
    """Dump sprint to database (auto-detects schema version)."""
    from .sql_loader import detect_schema_version

    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        dump_sprint_v2(sprint)
    else:
        dump_sprint_v1(sprint)


def dump_task(task: Task) -> None:
    """Dump task to database (auto-detects schema version)."""
    from .sql_loader import detect_schema_version

    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        dump_task_v2(task)
    else:
        dump_task_v1(task)
```

### Phase 4: Rename Existing Functions

Rename all current dumper functions to add `_v1` suffix:
- `dump_roadmap()` → `dump_roadmap_v1()`
- `dump_track()` → `dump_track_v1()`
- `dump_sprint()` → `dump_sprint_v1()`
- `dump_task()` → `dump_task_v1()`

---

## Implementation Checklist

### Core Functions:
- [ ] Rename existing functions to `*_v1()`
- [ ] Create `dump_roadmap_v2()`
- [ ] Create `dump_track_v2()`
- [ ] Create `dump_sprint_v2()`
- [ ] Create `dump_task_v2()`
- [ ] Create `dump_criteria()` function
- [ ] Add dispatcher functions that call v1 or v2 based on detected version

### Helper Functions:
- [ ] `_serialize_version_strategy()` - Serialize VersionStrategy → JSON
- [ ] `_serialize_activity_log()` - Serialize activity log → JSON array
- [ ] `_serialize_metadata()` - Serialize Metadata → JSON
- [ ] `_serialize_strategic_value()` - Serialize strategic value → JSON array
- [ ] `_serialize_success_criteria()` - Serialize success criteria → JSON array
- [ ] `_serialize_development_gates()` - Serialize development gates → JSON
- [ ] `_serialize_gate_info()` - Serialize GateInfo → JSON
- [ ] `_serialize_audit_results()` - Serialize AuditResults → JSON
- [ ] `_serialize_criterion_target()` - Serialize target based on target_type

### Criteria Conversion Functions:
- [ ] `dump_criteria_from_blockers()` - blocked_by → CompletableTarget
- [ ] `dump_criteria_from_dependencies_v2()` - depends_on → CompletableTarget (soft)
- [ ] `dump_criteria_from_deliverables()` - deliverables → FileExistsTarget
- [ ] `dump_criteria_from_quality_gates()` - quality_gates → ThresholdTarget
- [ ] `dump_criteria_from_development_gates()` - development_gates → ExternalTarget

---

## Testing Strategy

### Unit Tests:
1. Test `dump_roadmap_v2()` writes to completables table
2. Test `dump_track_v2()` writes to completables + criteria
3. Test `dump_criteria_from_blockers()` creates CompletableTarget criteria
4. Test `dump_criteria_from_deliverables()` creates FileExistsTarget criteria
5. Test dispatcher functions route to correct version

### Integration Tests:
1. Dump roadmap to v2 database
2. Load roadmap back and compare
3. Dump track with criteria to v2 database
4. Verify criteria rows created correctly
5. Test round-trip: YAML → Domain Model → v2 DB → Domain Model → YAML

### Migration Validation:
1. Load from YAML
2. Dump to v2 database
3. Load from v2 database
4. Compare loaded data to original
5. Verify no data loss

---

## Estimated Effort

- **Dispatcher functions:** ~100 lines
- **V2 dumper functions:** ~600 lines (4 dumpers × ~150 lines each)
- **Helper serialization functions:** ~300 lines
- **Criteria conversion functions:** ~400 lines
- **Refactoring existing code:** ~100 lines
- **Tests:** ~300 lines

**Total:** ~1,800 new lines of code

**Time Estimate:** 12-16 hours for full implementation + testing

---

## Migration Path

### Before Migration (v1.0.0 database):
```python
dump_track(track)
# → Calls dump_track_v1() (current implementation)
# → Writes to tracks, sprints, entity_blocked_by, quality_gates tables
```

### After Migration (v2.0.0 database):
```python
dump_track(track)
# → Calls dump_track_v2() (new implementation)
# → Writes to completables table (with ticket_type='track')
# → Writes to criteria table (converted from blocked_by, quality_gates, etc.)
```

### User Code:
**No changes required** - dispatcher functions handle version detection transparently.

---

## Conclusion

This design maintains full backward compatibility while adding v2 schema support. The dispatcher pattern allows seamless migration without breaking existing code.

**Key Features:**
- Automatic schema version detection
- Transparent routing to v1 or v2 dumpers
- Comprehensive criteria conversion from legacy blocking systems
- Full round-trip integrity (YAML → Domain → DB → Domain → YAML)

**Next Steps:**
1. Implement Phase 4 (rename existing functions)
2. Implement Phase 2 (v2 dumpers)
3. Implement criteria conversion helpers
4. Implement Phase 3 (dispatchers)
5. Write tests
6. Validate with migration script

**Design Status:** ✅ Complete
**Implementation Status:** ⏳ Pending
**Reviewed By:** Claude Opus 4.5
**Approved:** 2025-12-09
