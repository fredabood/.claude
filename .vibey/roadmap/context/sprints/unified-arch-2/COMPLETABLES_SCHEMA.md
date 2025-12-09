# Unified Completables Table Schema Design

**Date:** 2025-12-09
**Sprint:** unified-arch-2 (Database Schema Migration)
**Task:** unified-arch-2-task-001
**Status:** Final Design

---

## Overview

This document specifies the **unified completables table** that replaces separate `roadmaps`, `tracks`, `sprints`, `tasks`, and `artifacts` tables with a single table using single-table inheritance.

**Key Design Decision:** Use TWO levels of type discrimination:
1. **Level 1: `completable_type`** - Distinguishes tickets from artifacts
2. **Level 2: `ticket_type`** - Distinguishes roadmap/track/sprint/task (tickets only)

---

## Table Schema

```sql
CREATE TABLE completables (
    -- =========================================================================
    -- IDENTITY & HIERARCHY (Shared by ALL completables)
    -- =========================================================================
    id TEXT PRIMARY KEY,                    -- ULID
    name TEXT NOT NULL,
    description TEXT,

    -- Type discrimination (2 levels)
    completable_type TEXT NOT NULL CHECK (completable_type IN ('ticket', 'artifact')),
    ticket_type TEXT CHECK (ticket_type IN ('roadmap', 'track', 'sprint', 'task')),

    -- Hierarchy
    parent_id TEXT REFERENCES completables(id),
    sequence INTEGER DEFAULT 0,
    slug TEXT,

    -- =========================================================================
    -- LIFECYCLE (Shared by ALL completables)
    -- =========================================================================
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed',
        'wont_do', 'superseded'
    )),

    -- Timestamps (ISO 8601)
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,

    -- =========================================================================
    -- TICKET-SPECIFIC FIELDS (NULL for artifacts)
    -- =========================================================================

    -- Work Assignment & Planning
    assigned_agents_json TEXT,             -- JSON array of agent IDs
    priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    estimated_duration TEXT,
    deferred INTEGER DEFAULT 0,

    -- Work Evidence
    commits_json TEXT,                     -- JSON array of GitCommit objects

    -- Requirements (local to this ticket, not inherited)
    requirements_local_json TEXT,          -- JSON array of Standard objects

    -- Metadata
    metadata_json TEXT,                    -- JSON object

    -- === ROADMAP-SPECIFIC (ticket_type='roadmap') ===
    version TEXT,                          -- e.g., "1.3.0"
    version_strategy_json TEXT,            -- JSON: major_on, minor_on, patch_on
    activity_log_json TEXT,                -- JSON array of ActivityLogEntry

    -- === TRACK-SPECIFIC (ticket_type='track') ===
    strategic_value_json TEXT,             -- JSON array of strategic value strings

    -- === SPRINT-SPECIFIC (ticket_type='sprint') ===
    plan_file TEXT,                        -- Path to sprint plan
    goal TEXT,                             -- Sprint goal statement
    success_criteria_json TEXT,            -- JSON array of success criteria strings
    development_gates_json TEXT,           -- JSON array of DevelopmentGate objects
    blocked_reason TEXT,                   -- Why sprint is blocked
    completion_gate_check_at TEXT,         -- ISO timestamp
    production_gate_check_at TEXT,         -- ISO timestamp
    production_ready_at TEXT,              -- ISO timestamp
    deployed_at TEXT,                      -- ISO timestamp

    -- === TASK-SPECIFIC (ticket_type='task') ===
    task_type_detail TEXT CHECK (task_type_detail IN ('development', 'completion_gate', 'production_gate')),
    estimated_tokens INTEGER,              -- Direct token estimate (any level)
    actual_tokens INTEGER,                 -- Actual tokens used
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex', 'high')),
    gate_info_json TEXT,                   -- JSON: GateInfo for gate tasks
    audit_results_json TEXT,               -- JSON: AuditResults for completed gates
    phase_label TEXT,                      -- e.g., "design", "implementation"

    -- =========================================================================
    -- ARTIFACT-SPECIFIC FIELDS (NULL for tickets)
    -- =========================================================================

    -- File References
    paths_json TEXT,                       -- JSON array of file paths
    content_hash TEXT,                     -- Git blob hash or similar

    -- Artifact Classification
    artifact_type TEXT CHECK (artifact_type IN ('code', 'documentation', 'test', 'config', 'data')),
    artifact_subtype TEXT,                 -- e.g., "module", "guide", "integration_test"

    -- Provenance
    provenance_json TEXT,                  -- JSON: created_by, created_at, source_tool, etc.

    -- Documentation Relationships
    documents_artifact_id TEXT REFERENCES completables(id),  -- What artifact does this document?
    depends_on_artifact_ids_json TEXT,     -- JSON array of artifact IDs this depends on

    -- =========================================================================
    -- LEGACY MIGRATION TRACKING (Temporary - remove after migration complete)
    -- =========================================================================
    legacy_sprint_id TEXT,
    legacy_track_id TEXT,
    legacy_roadmap_id TEXT,

    -- =========================================================================
    -- CONSTRAINTS
    -- =========================================================================
    CHECK (
        -- Tickets must have ticket_type
        (completable_type = 'ticket' AND ticket_type IS NOT NULL)
        OR
        -- Artifacts must NOT have ticket_type
        (completable_type = 'artifact' AND ticket_type IS NULL)
    ),

    CHECK (
        -- Roadmaps have no parent
        (ticket_type = 'roadmap' AND parent_id IS NULL)
        OR
        -- Non-roadmaps may have parent
        (ticket_type != 'roadmap')
    )
);
```

---

## Indexes

```sql
-- Hierarchy & Lookups
CREATE INDEX idx_completables_parent ON completables(parent_id);
CREATE INDEX idx_completables_type ON completables(completable_type);
CREATE INDEX idx_completables_ticket_type ON completables(ticket_type);
CREATE INDEX idx_completables_status ON completables(status);
CREATE INDEX idx_completables_sequence ON completables(parent_id, sequence);
CREATE INDEX idx_completables_slug ON completables(slug);

-- Artifact Lookups
CREATE INDEX idx_completables_artifact_type ON completables(artifact_type);
CREATE INDEX idx_completables_documents ON completables(documents_artifact_id);

-- Legacy Migration (temporary)
CREATE INDEX idx_completables_legacy_sprint ON completables(legacy_sprint_id);
CREATE INDEX idx_completables_legacy_track ON completables(legacy_track_id);
CREATE INDEX idx_completables_legacy_roadmap ON completables(legacy_roadmap_id);
```

---

## Type-Specific Views

To maintain backward compatibility with existing query code, create views that expose type-specific fields:

### v_roadmaps
```sql
CREATE VIEW v_roadmaps AS
SELECT
    id, name, description, status,
    created_at, updated_at, started_at, completed_at,
    version, version_strategy_json, activity_log_json,
    metadata_json
FROM completables
WHERE completable_type = 'ticket' AND ticket_type = 'roadmap';
```

### v_tracks
```sql
CREATE VIEW v_tracks AS
SELECT
    id, name, description, parent_id, sequence, slug,
    status, created_at, updated_at, started_at, completed_at,
    priority, estimated_duration, strategic_value_json,
    assigned_agents_json, commits_json, requirements_local_json,
    metadata_json
FROM completables
WHERE completable_type = 'ticket' AND ticket_type = 'track';
```

### v_sprints
```sql
CREATE VIEW v_sprints AS
SELECT
    id, name, description, parent_id, sequence, slug,
    status, created_at, updated_at, started_at, completed_at,
    plan_file, goal, success_criteria_json, development_gates_json,
    blocked_reason, completion_gate_check_at, production_gate_check_at,
    production_ready_at, deployed_at,
    assigned_agents_json, commits_json, requirements_local_json,
    metadata_json
FROM completables
WHERE completable_type = 'ticket' AND ticket_type = 'sprint';
```

### v_tasks
```sql
CREATE VIEW v_tasks AS
SELECT
    id, name, description, parent_id, sequence, slug,
    status, created_at, updated_at, started_at, completed_at,
    task_type_detail, priority, estimated_duration, estimated_tokens, actual_tokens,
    complexity, phase_label, deferred,
    gate_info_json, audit_results_json,
    assigned_agents_json, commits_json, requirements_local_json,
    metadata_json
FROM completables
WHERE completable_type = 'ticket' AND ticket_type = 'task';
```

### v_artifacts
```sql
CREATE VIEW v_artifacts AS
SELECT
    id, name, description, parent_id, sequence,
    status, created_at, updated_at,
    paths_json, content_hash, artifact_type, artifact_subtype,
    provenance_json, documents_artifact_id, depends_on_artifact_ids_json,
    metadata_json
FROM completables
WHERE completable_type = 'artifact';
```

---

## Field Allocation Strategy

### Main Table vs JSON
**Main table** - Fields queried frequently or used in JOINs/WHERE clauses:
- All identity fields (id, name, parent_id, sequence, slug)
- All lifecycle fields (status, timestamps)
- Type discriminators (completable_type, ticket_type)
- Common filters (priority, task_type_detail, complexity, artifact_type)

**JSON fields** - Complex objects rarely queried directly:
- Arrays (commits, assigned_agents, success_criteria, paths)
- Nested objects (version_strategy, provenance, gate_info)
- Standards/requirements (requirements_local_json)
- Metadata

### NULL Field Strategy
- Ticket-specific fields are NULL for artifacts
- Artifact-specific fields are NULL for tickets
- Type-specific fields (roadmap/track/sprint/task) are NULL for other ticket types
- Storage overhead is minimal (NULL uses 1 byte in SQLite)

---

## Migration Strategy

### Phase 1: Create New Table
1. Create `completables` table
2. Create indexes
3. Create views

### Phase 2: Migrate Data
1. **Roadmaps:** `completable_type='ticket', ticket_type='roadmap'`
2. **Tracks:** `completable_type='ticket', ticket_type='track'`
3. **Sprints:** `completable_type='ticket', ticket_type='sprint'`
4. **Tasks:** `completable_type='ticket', ticket_type='task'`
5. **Artifacts:** `completable_type='artifact'` (if any exist)

### Phase 3: Update Application Code
1. Update `sql_loader.py` to query from `completables` or views
2. Update `sql_dumper.py` to write to `completables`
3. Update ORM models to use unified table

### Phase 4: Clean Up
1. Verify all data migrated correctly
2. Drop old tables (roadmaps, tracks, sprints, tasks)
3. Remove legacy_*_id columns
4. Update schema version to 2.0.0

---

## Design Rationale

### Why Single-Table Inheritance?

**Pros:**
- Unified identity space (all ULIDs in one table)
- Simpler parent/child relationships (single FK)
- Enables polymorphic criteria targets (can reference any completable)
- Easier to implement artifact dependencies on tickets

**Cons:**
- Many NULL fields (mitigated: NULL uses 1 byte in SQLite)
- Type-specific queries need WHERE clauses (mitigated: views)
- Schema changes affect all types (mitigated: good design upfront)

**Alternative Considered:** Class Table Inheritance (separate tables + JOIN)
- Rejected: More complex queries, harder to implement polymorphic references

### Why Two-Level Discrimination?

Separating `completable_type` (ticket vs artifact) from `ticket_type` (roadmap/track/sprint/task) allows:
1. Clear distinction between work items (tickets) and file entities (artifacts)
2. Future extensibility (could add `report`, `metric`, etc. as completable types)
3. Type-specific field groups (ticket fields, artifact fields)

### Why Include Artifacts?

Artifacts need to be first-class entities to support:
- Documentation tracking (which files document which tickets)
- Artifact dependencies (code depends on config files)
- Criteria-based completion (task blocked until artifact exists)
- Provenance tracking (who created what, when, how)

---

## Compatibility Notes

### Existing Migration File
`vibey/roadmap/database/migrations/006_unified_ticket_schema.sql` implements a `tickets` table but does NOT include artifacts. This design extends that migration to:
1. Rename `tickets` → `completables`
2. Add `completable_type` discriminator
3. Add artifact-specific fields
4. Update views to filter by `completable_type`

### Schema Version
- Current: 1.0.0 (27 tables)
- After this migration: 2.0.0 (completables table)

---

## Next Steps

1. **Task 002:** Design criteria table schema
2. **Task 003:** Design artifacts table schema (if separate table preferred)
3. **Task 004:** Write migration script implementing this schema
4. **Task 005:** Update sql_loader.py
5. **Task 006:** Update sql_dumper.py
6. **Task 007:** Execute migration and validate

---

**Design Status:** ✅ Complete
**Reviewed By:** Claude Opus 4.5
**Approved:** 2025-12-09
