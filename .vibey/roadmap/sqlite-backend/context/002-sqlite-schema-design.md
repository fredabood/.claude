# SQLite Database Schema Design

**Task:** sqlite-backend-0-task-002
**Status:** In Progress
**Date:** 2025-11-26

## Design Principles

1. **1:1 YAML Mapping** - Every YAML field has a corresponding DB column/table
2. **Tasks as Source of Truth** - All aggregations computed from tasks
3. **Computed Views** - Progress metrics calculated automatically
4. **Referential Integrity** - Foreign keys enforce valid relationships
5. **Polymorphic Quality Gates** - Gates apply to tracks, sprints, AND tasks

---

## Core Entity Tables

### 1. roadmaps

```sql
CREATE TABLE roadmaps (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do'
    )),
    blocked INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created TEXT NOT NULL,  -- ISO 8601
    started TEXT,
    target_completion TEXT,
    completed TEXT,
    deployed TEXT,

    -- Version Strategy (JSON blob - rarely queried)
    version_strategy TEXT,  -- JSON

    -- Metadata
    metadata TEXT  -- JSON
);
```

### 2. tracks

```sql
CREATE TABLE tracks (
    -- Identity
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    name TEXT NOT NULL,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do'
    )),
    blocked INTEGER NOT NULL DEFAULT 0,
    priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),

    -- Timestamps
    created TEXT NOT NULL,
    started TEXT,
    completed TEXT,

    -- Estimates
    estimated_duration TEXT,

    -- Metadata
    metadata TEXT  -- JSON
);
```

### 3. sprints

```sql
CREATE TABLE sprints (
    -- Identity
    id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id),
    name TEXT NOT NULL,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do'
    )),
    blocked INTEGER NOT NULL DEFAULT 0,
    blocked_reason TEXT,

    -- Timestamps
    created TEXT NOT NULL,
    started TEXT,
    completion_gate_check_at TEXT,
    completed TEXT,
    production_gate_check_at TEXT,
    production_ready_at TEXT,
    deployed_at TEXT,

    -- References
    plan_file TEXT,

    -- Metadata
    metadata TEXT  -- JSON
);
```

### 4. tasks

```sql
CREATE TABLE tasks (
    -- Identity
    id TEXT PRIMARY KEY,
    sprint_id TEXT NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id),
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id),

    -- Classification
    task_type TEXT NOT NULL CHECK (task_type IN (
        'development', 'completion_gate', 'production_gate'
    )),
    title TEXT NOT NULL,
    description TEXT,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed', 'wont_do'
    )),
    blocked INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created TEXT NOT NULL,
    started TEXT,
    completed TEXT,

    -- Assignment & Prioritization
    assigned_agent TEXT,
    priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    phase_label TEXT,

    -- Estimation
    estimated_tokens INTEGER,
    actual_tokens INTEGER,
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex')),

    -- Gate-specific (for completion_gate and production_gate tasks)
    gate_info TEXT,  -- JSON
    audit_results TEXT,  -- JSON

    -- Metadata
    metadata TEXT  -- JSON
);
```

---

## Relationship Tables

### 5. external_dependencies

External prerequisites (not roadmap entities).

```sql
CREATE TABLE external_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (roadmap, track, sprint, or task)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('roadmap', 'track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Dependency details
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK (status IN ('pending', 'resolved', 'blocked')),
    resolved_at TEXT,

    -- Metadata
    metadata TEXT  -- JSON
);

CREATE INDEX idx_external_deps_owner ON external_dependencies(owner_type, owner_id);
```

### 6. entity_blocks

"This entity blocks these other entities from starting."

```sql
CREATE TABLE entity_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Blocker (the entity doing the blocking)
    blocker_type TEXT NOT NULL CHECK (blocker_type IN ('track', 'sprint', 'task')),
    blocker_id TEXT NOT NULL,

    -- Blocked (the entity being blocked)
    blocked_type TEXT NOT NULL CHECK (blocked_type IN ('track', 'sprint', 'task')),
    blocked_id TEXT NOT NULL,

    -- Context
    reason TEXT,

    UNIQUE(blocker_type, blocker_id, blocked_type, blocked_id)
);

CREATE INDEX idx_entity_blocks_blocker ON entity_blocks(blocker_type, blocker_id);
CREATE INDEX idx_entity_blocks_blocked ON entity_blocks(blocked_type, blocked_id);
```

### 7. entity_blocked_by

"This entity is blocked by these other entities."
Note: This is the inverse of entity_blocks, stored for query efficiency.

```sql
CREATE TABLE entity_blocked_by (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Blocked entity (waiting)
    blocked_type TEXT NOT NULL CHECK (blocked_type IN ('track', 'sprint', 'task')),
    blocked_id TEXT NOT NULL,

    -- Blocking entity (must complete first)
    blocker_type TEXT NOT NULL CHECK (blocker_type IN ('track', 'sprint', 'task')),
    blocker_id TEXT NOT NULL,

    -- Context
    reason TEXT,

    UNIQUE(blocked_type, blocked_id, blocker_type, blocker_id)
);

CREATE INDEX idx_entity_blocked_by_blocked ON entity_blocked_by(blocked_type, blocked_id);
CREATE INDEX idx_entity_blocked_by_blocker ON entity_blocked_by(blocker_type, blocker_id);
```

### 8. entity_depends_on

Same-level dependencies between sibling entities.

```sql
CREATE TABLE entity_depends_on (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Dependent entity (needs the other)
    dependent_type TEXT NOT NULL CHECK (dependent_type IN ('track', 'sprint', 'task')),
    dependent_id TEXT NOT NULL,

    -- Dependency (needed by the other)
    dependency_type TEXT NOT NULL CHECK (dependency_type IN ('track', 'sprint', 'task')),
    dependency_id TEXT NOT NULL,

    -- Context
    reason TEXT,

    UNIQUE(dependent_type, dependent_id, dependency_type, dependency_id)
);

CREATE INDEX idx_depends_on_dependent ON entity_depends_on(dependent_type, dependent_id);
CREATE INDEX idx_depends_on_dependency ON entity_depends_on(dependency_type, dependency_id);
```

---

## Quality Gates (Track and Sprint Level)

### 9. quality_gates

Quality gates at track AND sprint levels (matches actual Vibey usage).

Note: The schema/model defines quality_gates on tracks, but CLI and actual YAML
files use them primarily at the sprint level. SQLite supports both.

```sql
CREATE TABLE quality_gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (track or sprint only - not tasks)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint')),
    owner_id TEXT NOT NULL,

    -- Gate definition
    name TEXT NOT NULL,
    description TEXT,
    threshold INTEGER NOT NULL DEFAULT 100,  -- Pass threshold (percentage)
    blocking INTEGER NOT NULL DEFAULT 1,  -- Is this gate blocking?

    -- Gate status
    status TEXT NOT NULL DEFAULT 'not_run' CHECK (status IN (
        'not_run', 'running', 'passed', 'failed', 'superseded'
    )),
    score INTEGER,  -- Actual score achieved

    -- Audit trail
    last_run_at TEXT,
    last_run_by TEXT,

    -- Metadata
    metadata TEXT  -- JSON
);

CREATE INDEX idx_quality_gates_owner ON quality_gates(owner_type, owner_id);
CREATE INDEX idx_quality_gates_status ON quality_gates(status);
```

---

## Supporting Data Tables

### 10. deliverables

Deliverables can be associated with multiple tasks (many-to-many).

```sql
CREATE TABLE deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Deliverable details
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    completed_at TEXT,

    -- Optional artifact reference
    artifact_path TEXT,
    artifact_url TEXT
);

-- Junction table for many-to-many relationship
CREATE TABLE entity_deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (track, sprint, or task)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Deliverable reference
    deliverable_id INTEGER NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,

    UNIQUE(owner_type, owner_id, deliverable_id)
);

CREATE INDEX idx_entity_deliverables_owner ON entity_deliverables(owner_type, owner_id);
CREATE INDEX idx_entity_deliverables_deliverable ON entity_deliverables(deliverable_id);
```

### 11. commits

Commits can be associated with multiple tasks (many-to-many).
A single commit often touches multiple tasks.

```sql
CREATE TABLE commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Commit details
    commit_hash TEXT NOT NULL UNIQUE,
    commit_message TEXT,
    author TEXT,
    committed_at TEXT,

    -- Optional PR/branch info
    branch TEXT,
    pr_number INTEGER,
    pr_url TEXT
);

-- Junction table for many-to-many relationship
CREATE TABLE entity_commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (track, sprint, or task)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Commit reference
    commit_id INTEGER NOT NULL REFERENCES commits(id) ON DELETE CASCADE,

    UNIQUE(owner_type, owner_id, commit_id)
);

CREATE INDEX idx_entity_commits_owner ON entity_commits(owner_type, owner_id);
CREATE INDEX idx_entity_commits_commit ON entity_commits(commit_id);
CREATE INDEX idx_commits_hash ON commits(commit_hash);
```

### 12. assigned_agents

```sql
CREATE TABLE assigned_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (tracks can have multiple agents)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Agent details
    agent_name TEXT NOT NULL,
    role TEXT,  -- Optional role description
    assigned_at TEXT,

    UNIQUE(owner_type, owner_id, agent_name)
);

CREATE INDEX idx_assigned_agents_owner ON assigned_agents(owner_type, owner_id);
```

### 13. standards

```sql
CREATE TABLE standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint')),
    owner_id TEXT NOT NULL,

    -- Standard reference
    standard_name TEXT NOT NULL,
    standard_url TEXT,
    description TEXT
);

CREATE INDEX idx_standards_owner ON standards(owner_type, owner_id);
```

### 14. strategic_value

```sql
CREATE TABLE strategic_value (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    value_statement TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX idx_strategic_value_track ON strategic_value(track_id);
```

### 15. development_gates

External development dependencies for sprints.

```sql
CREATE TABLE development_gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,

    -- Gate details
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'blocked')),
    resolved_at TEXT
);

CREATE INDEX idx_dev_gates_sprint ON development_gates(sprint_id);
```

---

## Roadmap-Level Tables

### 16. version_history

```sql
CREATE TABLE version_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,

    -- Version details
    version TEXT NOT NULL,
    released_at TEXT NOT NULL,
    description TEXT,

    -- Changes summary
    changes TEXT  -- JSON array of change descriptions
);

CREATE INDEX idx_version_history_roadmap ON version_history(roadmap_id);
```

### 17. activity_log

```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,

    -- Event details
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    occurred_at TEXT NOT NULL,

    -- Context
    entity_type TEXT,  -- track, sprint, task, or null for roadmap-level
    entity_id TEXT,
    actor TEXT,  -- Who/what caused the event

    -- Additional data
    metadata TEXT  -- JSON
);

CREATE INDEX idx_activity_log_roadmap ON activity_log(roadmap_id);
CREATE INDEX idx_activity_log_time ON activity_log(occurred_at);
CREATE INDEX idx_activity_log_entity ON activity_log(entity_type, entity_id);
```

---

## Summary Tables (Denormalized for YAML Export)

These tables store denormalized summaries that appear in parent YAML files.
They are populated by triggers when entities change.

### 18. track_summaries

Stored in roadmap.yaml under `tracks:` array.

```sql
CREATE TABLE track_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,

    -- Summary fields (denormalized)
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT,

    UNIQUE(roadmap_id, track_id)
);
```

### 19. sprint_summaries

Stored in track.yaml under `sprints:` array.

```sql
CREATE TABLE sprint_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    sprint_id TEXT NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,

    -- Summary fields (denormalized)
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    estimated_duration TEXT,
    tasks_count INTEGER NOT NULL DEFAULT 0,
    started TEXT,

    UNIQUE(track_id, sprint_id)
);
```

### 20. task_summaries

Stored in sprint.yaml under `tasks:` array.

```sql
CREATE TABLE task_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,

    -- Summary fields (denormalized)
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    task_type TEXT NOT NULL,
    gate_info TEXT,  -- JSON (for gate tasks)

    UNIQUE(sprint_id, task_id)
);
```

---

## Sync & Validation Tables

These tables support the YAML synchronization system and integrity validation.

### 21. yaml_checksums

Tracks checksums of YAML files at time of database load.
Used to detect manual YAML edits before dumping.

```sql
CREATE TABLE yaml_checksums (
    file_path TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,  -- SHA256 of file content at load time
    loaded_at TEXT NOT NULL,  -- When the file was loaded into DB
    file_size INTEGER,  -- File size in bytes at load time
    last_modified TEXT  -- File modification time at load time
);
```

### 22. database_state

Tracks the overall state of the database for sync management.

```sql
CREATE TABLE database_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Singleton row

    -- Sync state
    last_yaml_load TEXT,  -- When DB was last rebuilt from YAML
    last_yaml_dump TEXT,  -- When DB was last dumped to YAML
    is_dirty INTEGER NOT NULL DEFAULT 0,  -- Has uncommitted changes

    -- Source tracking
    source_commit TEXT,  -- Git commit hash DB was built from
    source_branch TEXT,  -- Git branch at time of load

    -- Schema version for migrations
    schema_version TEXT NOT NULL DEFAULT '1.0.0'
);

-- Initialize singleton row
INSERT INTO database_state (id, schema_version) VALUES (1, '1.0.0');
```

### 23. sync_conflicts

Records detected conflicts between DB and YAML for resolution.

```sql
CREATE TABLE sync_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Conflict details
    file_path TEXT NOT NULL,
    conflict_type TEXT NOT NULL CHECK (conflict_type IN (
        'yaml_modified',      -- YAML changed after DB load
        'db_modified',        -- DB has changes not in YAML
        'both_modified',      -- Both changed (merge conflict)
        'file_deleted',       -- YAML file was deleted
        'integrity_error'     -- Computed values don't match
    )),

    -- Context
    detected_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution TEXT CHECK (resolution IN ('use_db', 'use_yaml', 'merged', 'ignored')),

    -- Details
    db_value TEXT,  -- JSON of DB state
    yaml_value TEXT,  -- JSON of YAML state
    description TEXT
);

CREATE INDEX idx_sync_conflicts_unresolved ON sync_conflicts(resolved_at) WHERE resolved_at IS NULL;
```

---

## Table Count Summary

| Category | Tables | Purpose |
|----------|--------|---------|
| Core Entities | 4 | roadmaps, tracks, sprints, tasks |
| Relationships | 4 | external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on |
| Quality & Gates | 2 | quality_gates, development_gates |
| Supporting Data | 5 + 2 junction | deliverables, commits, entity_deliverables, entity_commits, assigned_agents, standards, strategic_value |
| Roadmap-Level | 2 | version_history, activity_log |
| Summaries | 3 | track_summaries, sprint_summaries, task_summaries |
| Sync & Validation | 3 | yaml_checksums, database_state, sync_conflicts |
| **Total** | **25** | |

---

## Foreign Key Relationships

```
roadmaps
    ├── tracks (roadmap_id)
    │       ├── sprints (track_id)
    │       │       └── tasks (sprint_id)
    │       ├── sprint_summaries (track_id)
    │       └── strategic_value (track_id)
    ├── track_summaries (roadmap_id)
    ├── version_history (roadmap_id)
    └── activity_log (roadmap_id)

Polymorphic relationships (owner_type + owner_id):
    - external_dependencies
    - quality_gates
    - deliverables
    - commits
    - assigned_agents
    - standards

Blocking relationships (blocker/blocked types + ids):
    - entity_blocks
    - entity_blocked_by
    - entity_depends_on
```

---

## YAML ↔ SQLite Field Mapping

### Complete Field Mapping

| YAML Location | SQLite Table | Notes |
|---------------|--------------|-------|
| roadmap.yaml (root) | roadmaps | 1:1 mapping |
| roadmap.yaml → tracks[] | track_summaries | Denormalized |
| roadmap.yaml → dependencies[] | external_dependencies | owner_type='roadmap' |
| roadmap.yaml → blocked_by[] | entity_blocked_by | blocked_type='roadmap' |
| roadmap.yaml → version_history[] | version_history | |
| roadmap.yaml → activity_log[] | activity_log | |
| track.yaml (root) | tracks | 1:1 mapping |
| track.yaml → sprints[] | sprint_summaries | Denormalized |
| track.yaml → quality_gates[] | quality_gates | owner_type='track' |
| sprint.yaml → quality_gates[] | quality_gates | owner_type='sprint' |
| track.yaml → deliverables[] | deliverables | owner_type='track' |
| track.yaml → commits[] | commits | owner_type='track' |
| track.yaml → assigned_agents[] | assigned_agents | owner_type='track' |
| track.yaml → strategic_value[] | strategic_value | |
| track.yaml → standards[] | standards | owner_type='track' |
| track.yaml → blocks[] | entity_blocks | blocker_type='track' |
| track.yaml → blocked_by[] | entity_blocked_by | blocked_type='track' |
| track.yaml → depends_on[] | entity_depends_on | dependent_type='track' |
| track.yaml → depended_on_by[] | (inverse query) | Query entity_depends_on |
| sprint.yaml (root) | sprints | 1:1 mapping |
| sprint.yaml → tasks[] | task_summaries | Denormalized |
| sprint.yaml → development_gates[] | development_gates | |
| sprint.yaml → deliverables[] | deliverables | owner_type='sprint' |
| sprint.yaml → commits[] | commits | owner_type='sprint' |
| sprint.yaml → standards[] | standards | owner_type='sprint' |
| sprint.yaml → blocks[] | entity_blocks | blocker_type='sprint' |
| sprint.yaml → blocked_by[] | entity_blocked_by | blocked_type='sprint' |
| sprint.yaml → depends_on[] | entity_depends_on | dependent_type='sprint' |
| sprint.yaml → depended_on_by[] | (inverse query) | Query entity_depends_on |
| task.yaml (root) | tasks | 1:1 mapping |
| task.yaml → deliverables[] | deliverables | owner_type='task' |
| task.yaml → commits[] | commits | owner_type='task' |
| task.yaml → dependencies[] | external_dependencies | owner_type='task' |
| task.yaml → blocks[] | entity_blocks | blocker_type='task' |
| task.yaml → blocked_by[] | entity_blocked_by | blocked_type='task' |

---

## Design Decisions

### 1. Polymorphic Tables vs Separate Tables

**Decision:** Use polymorphic tables (owner_type + owner_id) for:
- deliverables (tracks, sprints, tasks)
- commits (tracks, sprints, tasks)
- external_dependencies (all levels)

**Note:** quality_gates is polymorphic for track/sprint only (not tasks) to match actual Vibey usage where gates appear in both track.yaml and sprint.yaml files.

**Rationale:**
- Reduces table count
- Unified queries across entity types
- Matches YAML structure flexibility
- Well-indexed for performance

### 2. Separate Blocking Tables

**Decision:** Maintain separate tables for blocks, blocked_by, depends_on

**Semantic Distinction:**

| Relationship | Enforcement | Sets `blocked` flag? | Use Case |
|--------------|-------------|---------------------|----------|
| `blocks/blocked_by` | **Hard** - triggers prevent completion | Yes | "Task B cannot complete until Task A completes" |
| `depends_on/depended_on_by` | **Soft** - ordering suggestion | No | "Sprint 2 should start after Sprint 1" |

**Key Difference:**
- `blocks/blocked_by`: System-enforced constraints. Triggers will ABORT attempts to complete a blocked entity.
- `depends_on`: Advisory ordering. The system won't prevent violations, but views can surface out-of-order work.

**Rationale for keeping separate:**
- Clear semantic distinction (hard vs soft)
- Different enforcement behavior
- blocked_by is stored as inverse of blocks for query efficiency
- depends_on is typically same-level (sprint→sprint, task→task)

**Note:** If an entity has both `blocked_by` AND `depends_on` relationships, the `blocked_by` takes precedence for enforcement.

### 3. Summary Tables

**Decision:** Store denormalized summaries in dedicated tables

**Rationale:**
- Fast YAML export without joins
- Populated by triggers on entity changes
- Matches YAML structure exactly
- Clear separation of computed vs stored

### 4. JSON Columns

**Decision:** Use JSON for complex nested objects that aren't queried:
- gate_info, audit_results
- metadata
- version_strategy
- changes (in version_history)

**Rationale:**
- Flexibility for evolving schemas
- These fields are read/write as blobs
- Rarely filtered or joined on

---

## Next Steps

1. **Task 3:** Design computed views for progress aggregations
2. **Task 4:** Design triggers for automatic updates
3. **Task 5:** Design YAML synchronization strategy

---

**Schema Version:** 1.0.0
**Tables:** 20
**Full 1:1 YAML Mapping:** ✓
