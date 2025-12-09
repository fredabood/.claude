# SQL Loader v2.0.0 Design Document

**Date:** 2025-12-09
**Sprint:** unified-arch-2 (Database Schema Migration)
**Task:** unified-arch-2-task-005
**Status:** Design Complete

---

## Overview

Update `vibey/roadmap/serialization/sql_loader.py` (1745 lines) to support both v1.0.0 (27 tables) and v2.0.0 (2 tables + 14 views) database schemas during the migration transition period.

---

## Current Architecture (v1.0.0)

### Schema (27 tables):
- **Core:** roadmaps, tracks, sprints, tasks
- **Relationships:** external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on
- **Quality:** quality_gates, development_gates
- **Supporting:** deliverables, entity_deliverables, commits, entity_commits, assigned_agents
- **Roadmap:** version_history, activity_log
- **Summaries:** track_summaries, sprint_summaries, task_summaries
- **Sync:** yaml_checksums, database_state, sync_conflicts
- **Audit:** audit_trail
- **Artifacts:** artifacts

### Loader Functions:
```python
load_roadmap(roadmap_id: str) -> Roadmap
load_track(track_id: str) -> Track
load_sprint(sprint_id: str) -> Sprint
load_task(task_id: str) -> Task
```

### Query Pattern (Example - load_track):
```sql
-- Main data
SELECT * FROM tracks WHERE id = ?

-- Related data
SELECT * FROM sprints WHERE track_id = ?
SELECT * FROM entity_blocked_by WHERE blocked_type = 'track' AND blocked_id = ?
SELECT * FROM entity_depends_on WHERE dependent_type = 'track' AND dependent_id = ?
SELECT * FROM quality_gates WHERE owner_type = 'track' AND owner_id = ?
```

---

## Target Architecture (v2.0.0)

### Schema (2 tables + 14 views):
- **completables** - Single table for all tickets (roadmaps, tracks, sprints, tasks) + artifacts
- **criteria** - Unified blocking system (replaces blocked_by, depends_on, deliverables, quality_gates)
- **Views:** v_roadmaps, v_tracks, v_sprints, v_tasks, v_artifacts, v_blocking_criteria, etc.

### New Loader Functions:
```python
load_roadmap_v2(roadmap_id: str) -> Roadmap
load_track_v2(track_id: str) -> Track
load_sprint_v2(sprint_id: str) -> Sprint
load_task_v2(task_id: str) -> Task
load_criteria(completable_id: str, blocks_transition: str = None) -> List[Criterion]
```

### Query Pattern (Example - load_track_v2):
```sql
-- Main data from completables (using view for convenience)
SELECT * FROM v_tracks WHERE id = ?

-- Or direct query with type discrimination:
SELECT * FROM completables
WHERE id = ? AND completable_type = 'ticket' AND ticket_type = 'track'

-- Criteria (replaces blocked_by, depends_on, quality_gates)
SELECT * FROM criteria WHERE completable_id = ?

-- Children (sprints under this track)
SELECT * FROM completables
WHERE parent_id = ? AND ticket_type = 'sprint'
ORDER BY sequence
```

---

## Implementation Strategy

### Phase 1: Schema Version Detection

Add version detector at module level:

```python
def detect_schema_version(conn=None) -> str:
    """
    Detect database schema version.

    Returns:
        '1.0.0' - Legacy 27-table schema
        '2.0.0' - Unified completables + criteria schema
    """
    if conn is None:
        conn = get_connection()

    # Check database_state table
    try:
        row = conn.execute(
            "SELECT schema_version FROM database_state WHERE id = 1"
        ).fetchone()
        if row:
            return row[0]
    except:
        pass

    # Fallback: Check for completables table
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {t[0] for t in tables}

    if 'completables' in table_names and 'criteria' in table_names:
        return '2.0.0'
    elif 'roadmaps' in table_names and 'tracks' in table_names:
        return '1.0.0'

    raise ValueError("Unknown schema version")
```

### Phase 2: V2 Loader Functions

Create parallel v2 loaders:

#### A. load_roadmap_v2()

```python
def load_roadmap_v2(roadmap_id: str = "vibey-framework-v2") -> Roadmap:
    """Load roadmap from v2.0.0 schema (completables table)."""
    conn = get_connection()

    # Load from completables (or use v_roadmaps view)
    row = conn.execute(
        """SELECT * FROM completables
           WHERE id = ? AND completable_type = 'ticket' AND ticket_type = 'roadmap'""",
        (roadmap_id,)
    ).fetchone()

    if row is None:
        raise ValueError(f"Roadmap '{roadmap_id}' not found")

    data = _row_to_dict(row)

    # Parse version strategy from JSON
    vs_data = _parse_json(data.get('version_strategy_json'), {})
    version_strategy = VersionStrategy(
        major_on=VersionBumpTrigger(vs_data.get('major_on', 'roadmap_milestone')),
        minor_on=VersionBumpTrigger(vs_data.get('minor_on', 'track_completion')),
        patch_on=VersionBumpTrigger(vs_data.get('patch_on', 'sprint_production_ready')),
    )

    # Load progress from v_unified_roadmap_progress view
    progress_row = conn.execute(
        "SELECT * FROM v_unified_roadmap_progress WHERE roadmap_id = ?",
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
    else:
        progress = Progress(0, 0, 0, 0, 0, 0, 0)

    # Load track summaries (child tracks)
    track_rows = conn.execute(
        """SELECT id, name, status, priority
           FROM completables
           WHERE parent_id = ? AND ticket_type = 'track'
           ORDER BY sequence""",
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

    # Load criteria (external dependencies)
    criteria = load_criteria(roadmap_id, blocks_transition='completed')

    # Convert ExternalTarget criteria to Dependency objects
    dependencies = [
        Dependency(
            type='external',
            name=c.description,
            status='resolved' if c.is_met else 'pending',
            required_for=c.description,
        )
        for c in criteria
        if c.target_type == 'external'
    ]

    # Parse activity log from JSON
    activity_log_data = _parse_json(data.get('activity_log_json'), [])
    activity_log = [
        ActivityLogEntry(
            timestamp=_parse_datetime(entry.get('timestamp')),
            type=ActivityType(entry.get('type', 'other')),
            description=entry.get('description', ''),
            context=entry.get('context'),
        )
        for entry in activity_log_data
    ]

    # Parse metadata
    meta_data = _parse_json(data.get('metadata_json'), {})
    metadata = Metadata(
        created_by=meta_data.get('created_by', 'unknown'),
        framework_version=meta_data.get('framework_version', '1.0.0'),
        schema_version='2.0.0',
        last_updated=_parse_datetime(meta_data.get('last_updated')),
        purpose=meta_data.get('purpose'),
        description=meta_data.get('description'),
    )

    return Roadmap(
        id=data['id'],
        name=data['name'],
        version=data.get('version', '0.1.0'),
        status=Status(data['status']),
        created=_parse_datetime(data['created_at']),
        started=_parse_datetime(data.get('started_at')),
        completed=_parse_datetime(data.get('completed_at')),
        version_strategy=version_strategy,
        progress=progress,
        tracks=tracks,
        dependencies=dependencies,
        version_history=[],  # Stored separately in v2
        activity_log=activity_log,
        metadata=metadata,
    )
```

#### B. load_track_v2()

```python
def load_track_v2(track_id: str) -> Track:
    """Load track from v2.0.0 schema (completables table)."""
    conn = get_connection()

    # Load from completables (or use v_tracks view)
    row = conn.execute(
        """SELECT * FROM v_tracks WHERE id = ?""",
        (track_id,)
    ).fetchone()

    if row is None:
        raise ValueError(f"Track '{track_id}' not found")

    data = _row_to_dict(row)

    # Load progress from v_unified_track_progress view
    progress_row = conn.execute(
        "SELECT * FROM v_unified_track_progress WHERE track_id = ?",
        (track_id,)
    ).fetchone()

    if progress_row:
        prog = _row_to_dict(progress_row)
        progress = TrackProgress(
            sprints_total=prog.get('sprints_total', 0),
            sprints_completed=prog.get('sprints_completed', 0),
            tasks_total=prog.get('tasks_total', 0),
            tasks_completed=prog.get('tasks_completed', 0),
            completion_percent=prog.get('completion_percent', 0),
        )
    else:
        progress = TrackProgress(0, 0, 0, 0, 0)

    # Load sprint summaries (child sprints)
    sprint_rows = conn.execute(
        """SELECT id, name, status, estimated_duration, started_at
           FROM completables
           WHERE parent_id = ? AND ticket_type = 'sprint'
           ORDER BY sequence""",
        (track_id,)
    ).fetchall()

    sprints = [
        SprintSummary(
            id=s['id'],
            name=s['name'],
            status=Status(s['status']),
            estimated_duration=s.get('estimated_duration'),
            tasks_count=0,  # Computed later
            started=_parse_datetime(s.get('started_at')),
        )
        for s in sprint_rows
    ]

    # Load blocked_by criteria
    blocked_by_criteria = conn.execute(
        """SELECT * FROM criteria
           WHERE completable_id = ? AND blocks_transition_to = 'in_progress'
           AND target_type = 'completable'""",
        (track_id,)
    ).fetchall()

    blocked_by = [
        TrackBlocker(
            blocker_id=json.loads(c['target_json']).get('completable_id'),
            blocker_type=DependencyType.TRACK,  # TODO: Infer from ID
            required_status=Status(json.loads(c['target_json']).get('required_status', 'completed')),
            description=c['description'],
        )
        for c in blocked_by_criteria
    ]

    # Load depends_on criteria
    depends_on_criteria = conn.execute(
        """SELECT * FROM criteria
           WHERE completable_id = ? AND blocks_transition_to = 'completed'
           AND target_type = 'completable' AND required = 0""",
        (track_id,)
    ).fetchall()

    depends_on = [
        TrackDependency(
            blocker_id=json.loads(c['target_json']).get('completable_id'),
            blocker_type=DependencyType.TRACK,
            required_status=Status(json.loads(c['target_json']).get('required_status', 'completed')),
            current_status=Status.NOT_STARTED,  # TODO: Query actual status
            description=c['description'],
            status=DependencyStatus.RESOLVED if c['is_met'] else DependencyStatus.PENDING,
        )
        for c in depends_on_criteria
    ]

    # Load quality gates (ThresholdTarget criteria)
    gate_criteria = conn.execute(
        """SELECT * FROM criteria
           WHERE completable_id = ? AND target_type = 'threshold'""",
        (track_id,)
    ).fetchall()

    quality_gates = [
        QualityGate(
            name=json.loads(c['target_json']).get('metric_name', 'Unknown'),
            description=c['description'],
            threshold=json.loads(c['target_json']).get('threshold', 100),
            blocking=bool(c['required']),
            status=GateStatus.PASSED if c['is_met'] else GateStatus.NOT_RUN,
        )
        for c in gate_criteria
    ]

    # Parse strategic value from JSON
    strategic_value_data = _parse_json(data.get('strategic_value_json'), [])

    # Parse metadata
    meta_data = _parse_json(data.get('metadata_json'), {})
    metadata = TrackMetadata(
        created_by=meta_data.get('created_by'),
        last_updated=_parse_datetime(meta_data.get('last_updated')),
    )

    # Parse commits from JSON
    commits_data = _parse_json(data.get('commits_json'), [])
    commits = [
        GitCommit(
            hash=c.get('hash', ''),
            message=c.get('message', ''),
            author=c.get('author'),
            timestamp=_parse_datetime(c.get('timestamp')),
        )
        for c in commits_data
    ]

    return Track(
        id=data['id'],
        roadmap_id=data.get('legacy_roadmap_id', data.get('parent_id')),
        name=data['name'],
        status=Status(data['status']),
        blocked=bool(blocked_by),
        priority=Priority(data['priority']) if data.get('priority') else Priority.MEDIUM,
        created=_parse_datetime(data['created_at']),
        started=_parse_datetime(data.get('started_at')),
        completed=_parse_datetime(data.get('completed_at')),
        estimated_duration=data.get('estimated_duration'),
        progress=progress,
        sprints=sprints,
        dependencies=[],  # External dependencies from criteria
        blocks=[],  # Computed from reverse query
        blocked_by=blocked_by,
        depends_on=depends_on,
        depended_on_by=[],  # Computed from reverse query
        quality_gates=quality_gates,
        assigned_agents=[],  # Parse from assigned_agents_json
        deliverables=[],  # From FileExistsTarget criteria
        strategic_value=strategic_value_data,
        commits=commits,
        standards=[],  # Parse from requirements_local_json
        metadata=metadata,
        slug=data.get('slug'),
    )
```

#### C. load_criteria()

```python
def load_criteria(completable_id: str, blocks_transition: str = None) -> List[Criterion]:
    """
    Load criteria for a completable entity.

    Args:
        completable_id: ID of the completable (roadmap, track, sprint, task, artifact)
        blocks_transition: Filter by transition blocked (in_progress, completed, production_ready)

    Returns:
        List of Criterion objects
    """
    conn = get_connection()

    if blocks_transition:
        rows = conn.execute(
            """SELECT * FROM criteria
               WHERE completable_id = ? AND blocks_transition_to = ?""",
            (completable_id, blocks_transition)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM criteria WHERE completable_id = ?",
            (completable_id,)
        ).fetchall()

    criteria = []
    for row in rows:
        data = _row_to_dict(row)
        target_json = _parse_json(data['target_json'], {})

        # Parse target based on target_type
        if data['target_type'] == 'completable':
            target = CompletableTarget(
                type='completable',
                completable_id=target_json.get('completable_id'),
                required_status=Status(target_json.get('required_status', 'completed')),
            )
        elif data['target_type'] == 'file_exists':
            target = FileExistsTarget(
                type='file_exists',
                paths=target_json.get('paths', []),
                all_required=target_json.get('all_required', True),
            )
        elif data['target_type'] == 'test_passes':
            target = TestPassesTarget(
                type='test_passes',
                test_command=target_json.get('test_command'),
                pass_threshold=target_json.get('pass_threshold', 100),
            )
        elif data['target_type'] == 'threshold':
            target = ThresholdTarget(
                type='threshold',
                metric_name=target_json.get('metric_name'),
                threshold=target_json.get('threshold'),
                comparison=target_json.get('comparison', '>='),
            )
        elif data['target_type'] == 'manual':
            target = ManualTarget(
                type='manual',
                instructions=target_json.get('instructions'),
                approver=target_json.get('approver'),
            )
        else:
            # Generic target for other types
            target = target_json

        criterion = Criterion(
            id=data['id'],
            description=data['description'],
            required=bool(data['required']),
            blocks_transition_to=data['blocks_transition_to'],
            target_type=data['target_type'],
            target=target,
            is_met=bool(data['is_met']) if data['is_met'] is not None else None,
            last_checked=_parse_datetime(data.get('last_checked')),
            created_at=_parse_datetime(data['created_at']),
            updated_at=_parse_datetime(data.get('updated_at')),
        )

        criteria.append(criterion)

    return criteria
```

### Phase 3: Dispatcher Functions

Update existing functions to dispatch based on schema version:

```python
def load_roadmap(roadmap_id: str = "vibey-framework-v2") -> Roadmap:
    """
    Load roadmap from database (auto-detects schema version).

    Args:
        roadmap_id: ID of the roadmap to load

    Returns:
        Roadmap object
    """
    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        return load_roadmap_v2(roadmap_id)
    else:
        return load_roadmap_v1(roadmap_id)  # Rename current function


def load_track(track_id: str) -> Track:
    """Load track from database (auto-detects schema version)."""
    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        return load_track_v2(track_id)
    else:
        return load_track_v1(track_id)


def load_sprint(sprint_id: str) -> Sprint:
    """Load sprint from database (auto-detects schema version)."""
    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        return load_sprint_v2(sprint_id)
    else:
        return load_sprint_v1(sprint_id)


def load_task(task_id: str) -> Task:
    """Load task from database (auto-detects schema version)."""
    conn = get_connection()
    version = detect_schema_version(conn)

    if version == '2.0.0':
        return load_task_v2(task_id)
    else:
        return load_task_v1(task_id)
```

### Phase 4: Rename Existing Functions

Rename all current loader functions to add `_v1` suffix:
- `load_roadmap()` → `load_roadmap_v1()`
- `load_track()` → `load_track_v1()`
- `load_sprint()` → `load_sprint_v1()`
- `load_task()` → `load_task_v1()`

This preserves all existing logic while creating space for v2 loaders.

---

## Implementation Checklist

### Core Functions:
- [ ] Add `detect_schema_version()` function
- [ ] Rename existing functions to `*_v1()`
- [ ] Create `load_roadmap_v2()`
- [ ] Create `load_track_v2()`
- [ ] Create `load_sprint_v2()`
- [ ] Create `load_task_v2()`
- [ ] Create `load_criteria()` helper function
- [ ] Add dispatcher functions that call v1 or v2 based on detected version

### Helper Functions:
- [ ] `_completable_row_to_roadmap()` - Convert completables row → Roadmap
- [ ] `_completable_row_to_track()` - Convert completables row → Track
- [ ] `_completable_row_to_sprint()` - Convert completables row → Sprint
- [ ] `_completable_row_to_task()` - Convert completables row → Task
- [ ] `_criterion_row_to_object()` - Convert criteria row → Criterion
- [ ] `_parse_criterion_target()` - Parse target_json based on target_type

### Data Model Updates:
- [ ] Add Criterion class to models (if not exists)
- [ ] Add CriterionTarget subclasses (CompletableTarget, FileExistsTarget, etc.)
- [ ] Update Track/Sprint/Task to include `criteria: List[Criterion]` field

---

## Testing Strategy

### Unit Tests:
1. Test `detect_schema_version()` with v1 database
2. Test `detect_schema_version()` with v2 database
3. Test `load_roadmap_v2()` returns valid Roadmap
4. Test `load_track_v2()` returns valid Track
5. Test `load_criteria()` returns valid Criterion objects
6. Test dispatcher functions route to correct version

### Integration Tests:
1. Load roadmap from v1 database (backward compatibility)
2. Load roadmap from v2 database (new functionality)
3. Load track with criteria from v2 database
4. Verify progress views work correctly
5. Verify criteria conversion (blocked_by → CompletableTarget)

### Migration Validation:
1. Run migration script (migrate_to_v2.py)
2. Load all tracks using new loaders
3. Compare loaded data to YAML source of truth
4. Verify no data loss during migration

---

## Estimated Effort

- **Schema detection:** ~50 lines
- **V2 loader functions:** ~800 lines (4 loaders × ~200 lines each)
- **Helper functions:** ~200 lines
- **Dispatcher updates:** ~100 lines
- **Refactoring existing code:** ~200 lines
- **Tests:** ~300 lines

**Total:** ~1,650 new lines of code

**Time Estimate:** 15-20 hours for full implementation + testing

---

## Migration Path

### Before Migration (v1.0.0 database):
```python
roadmap = load_roadmap("vibey-framework-v2")
# → Calls load_roadmap_v1() (current implementation)
```

### After Migration (v2.0.0 database):
```python
roadmap = load_roadmap("vibey-framework-v2")
# → Calls load_roadmap_v2() (new implementation)
```

### User Code:
**No changes required** - dispatcher functions handle version detection transparently.

---

## Conclusion

This design maintains full backward compatibility while adding v2 schema support. The dispatcher pattern allows seamless migration without breaking existing code.

**Next Steps:**
1. Implement Phase 1 (schema detection)
2. Implement Phase 4 (rename existing functions)
3. Implement Phase 2 (v2 loaders)
4. Implement Phase 3 (dispatchers)
5. Write tests
6. Validate with migration script

**Design Status:** ✅ Complete
**Implementation Status:** ⏳ Pending
**Reviewed By:** Claude Opus 4.5
**Approved:** 2025-12-09
