-- =============================================================================
-- Schema Version 2.0.0: Unified Completables + Criteria
-- =============================================================================
-- This schema implements the unified completables table design from:
-- - Task 001: COMPLETABLES_SCHEMA.md
-- - Task 002: CRITERIA_SCHEMA.md
-- - Task 003: ARTIFACTS_SCHEMA.md (artifacts in completables table)
--
-- Key Changes from 1.0.0:
-- 1. Separate entity tables → unified completables table
-- 2. Separate blocking systems → unified criteria table
-- 3. First-class artifact support (in completables)
-- 4. Single-table inheritance with 2-level discrimination
-- =============================================================================

-- =============================================================================
-- TABLE 1: COMPLETABLES (Unified Tickets + Artifacts)
-- =============================================================================

CREATE TABLE completables (
    -- =========================================================================
    -- IDENTITY & HIERARCHY
    -- =========================================================================
    id TEXT PRIMARY KEY,
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
    -- LIFECYCLE
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
    assigned_agents_json TEXT,
    priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    estimated_duration TEXT,
    deferred INTEGER DEFAULT 0,

    -- Work Evidence
    commits_json TEXT,

    -- Requirements (local to this ticket)
    requirements_local_json TEXT,

    -- Metadata
    metadata_json TEXT,

    -- === ROADMAP-SPECIFIC (ticket_type='roadmap') ===
    version TEXT,
    version_strategy_json TEXT,
    activity_log_json TEXT,

    -- === TRACK-SPECIFIC (ticket_type='track') ===
    strategic_value_json TEXT,

    -- === SPRINT-SPECIFIC (ticket_type='sprint') ===
    plan_file TEXT,
    goal TEXT,
    success_criteria_json TEXT,
    development_gates_json TEXT,
    blocked_reason TEXT,
    completion_gate_check_at TEXT,
    production_gate_check_at TEXT,
    production_ready_at TEXT,
    deployed_at TEXT,

    -- === TASK-SPECIFIC (ticket_type='task') ===
    task_type_detail TEXT CHECK (task_type_detail IN ('development', 'completion_gate', 'production_gate')),
    estimated_tokens INTEGER,
    actual_tokens INTEGER,
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex', 'high')),
    gate_info_json TEXT,
    audit_results_json TEXT,
    phase_label TEXT,

    -- =========================================================================
    -- ARTIFACT-SPECIFIC FIELDS (NULL for tickets)
    -- =========================================================================

    -- File References
    paths_json TEXT,
    content_hash TEXT,

    -- Artifact Classification
    artifact_type TEXT CHECK (artifact_type IN ('code', 'documentation', 'test', 'config', 'data')),
    artifact_subtype TEXT,

    -- Provenance
    provenance_json TEXT,

    -- Documentation Relationships
    documents_artifact_id TEXT REFERENCES completables(id),
    depends_on_artifact_ids_json TEXT,

    -- =========================================================================
    -- LEGACY MIGRATION TRACKING (remove after migration complete)
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
        (ticket_type != 'roadmap' OR ticket_type IS NULL)
    )
);

-- =============================================================================
-- TABLE 2: CRITERIA (Unified Blocking System)
-- =============================================================================

CREATE TABLE criteria (
    -- Identity
    id TEXT PRIMARY KEY,

    -- Ownership
    completable_id TEXT NOT NULL REFERENCES completables(id) ON DELETE CASCADE,

    -- Criterion Definition
    description TEXT NOT NULL,
    required INTEGER NOT NULL DEFAULT 1,

    -- Unified Blocking: which status transition does this block?
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed' CHECK (
        blocks_transition_to IN ('in_progress', 'completed', 'production_ready', 'deployed')
    ),

    -- Polymorphic Target
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable',
        'file_exists',
        'test_passes',
        'test_coverage',
        'threshold',
        'manual',
        'external',
        'symbol_exists',
        'command_exists'
    )),

    target_json TEXT NOT NULL,

    -- Evaluation State (cached)
    is_met INTEGER,
    last_checked TEXT,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =============================================================================
-- INDEXES: COMPLETABLES
-- =============================================================================

CREATE INDEX idx_completables_parent ON completables(parent_id);
CREATE INDEX idx_completables_type ON completables(completable_type);
CREATE INDEX idx_completables_ticket_type ON completables(ticket_type);
CREATE INDEX idx_completables_status ON completables(status);
CREATE INDEX idx_completables_sequence ON completables(parent_id, sequence);
CREATE INDEX idx_completables_slug ON completables(slug);

-- Artifact-specific indexes
CREATE INDEX idx_completables_artifact_type ON completables(artifact_type);
CREATE INDEX idx_completables_documents ON completables(documents_artifact_id);

-- Legacy migration indexes (temporary)
CREATE INDEX idx_completables_legacy_sprint ON completables(legacy_sprint_id);
CREATE INDEX idx_completables_legacy_track ON completables(legacy_track_id);
CREATE INDEX idx_completables_legacy_roadmap ON completables(legacy_roadmap_id);

-- =============================================================================
-- INDEXES: CRITERIA
-- =============================================================================

CREATE INDEX idx_criteria_completable ON criteria(completable_id);
CREATE INDEX idx_criteria_blocks_transition ON criteria(completable_id, blocks_transition_to);
CREATE INDEX idx_criteria_target_type ON criteria(target_type);
CREATE INDEX idx_criteria_is_met ON criteria(completable_id, is_met);
CREATE INDEX idx_criteria_last_checked ON criteria(last_checked);

-- =============================================================================
-- VIEWS: TYPE-SPECIFIC VIEWS
-- =============================================================================

-- View 1: Roadmaps
CREATE VIEW v_roadmaps AS
SELECT
    id, name, description, status,
    created_at, updated_at, started_at, completed_at,
    version, version_strategy_json, activity_log_json,
    metadata_json
FROM completables
WHERE completable_type = 'ticket' AND ticket_type = 'roadmap';

-- View 2: Tracks
CREATE VIEW v_tracks AS
SELECT
    id, name, description, parent_id, sequence, slug,
    status, created_at, updated_at, started_at, completed_at,
    priority, estimated_duration, strategic_value_json,
    assigned_agents_json, commits_json, requirements_local_json,
    metadata_json
FROM completables
WHERE completable_type = 'ticket' AND ticket_type = 'track';

-- View 3: Sprints
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

-- View 4: Tasks
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

-- View 5: Artifacts
CREATE VIEW v_artifacts AS
SELECT
    id, name, description, parent_id, sequence,
    status, created_at, updated_at,
    paths_json, content_hash, artifact_type, artifact_subtype,
    provenance_json, documents_artifact_id, depends_on_artifact_ids_json,
    metadata_json
FROM completables
WHERE completable_type = 'artifact';

-- =============================================================================
-- VIEWS: CRITERIA CONVENIENCE VIEWS
-- =============================================================================

-- View 6: Blocking Criteria
CREATE VIEW v_blocking_criteria AS
SELECT
    c.*,
    comp.name as completable_name,
    comp.status as completable_status
FROM criteria c
JOIN completables comp ON c.completable_id = comp.id
WHERE c.required = 1
  AND c.is_met != 1;

-- View 7: Dependency Graph
CREATE VIEW v_dependency_graph AS
SELECT
    c.completable_id as from_id,
    json_extract(c.target_json, '$.completable_id') as to_id,
    c.description as edge_label,
    c.blocks_transition_to as blocks_status,
    c.is_met
FROM criteria c
WHERE c.target_type = 'completable';

-- View 8: Pending Evaluations
CREATE VIEW v_pending_evaluations AS
SELECT *
FROM criteria
WHERE is_met IS NULL
   OR last_checked IS NULL
   OR datetime(last_checked) < datetime('now', '-1 hour');

-- =============================================================================
-- VIEWS: ARTIFACT QUERIES
-- =============================================================================

-- View 9: Orphan Artifacts
CREATE VIEW v_orphan_artifacts AS
SELECT a.*
FROM completables a
WHERE a.completable_type = 'artifact'
  AND NOT EXISTS (
      SELECT 1 FROM criteria c
      WHERE c.target_type = 'completable'
        AND json_extract(c.target_json, '$.completable_id') = a.id
  );

-- View 10: Stale Documentation
CREATE VIEW v_stale_documentation AS
SELECT
    doc.id as doc_id,
    doc.name as doc_name,
    doc.updated_at as doc_updated_at,
    target.id as target_id,
    target.name as target_name,
    target.updated_at as target_updated_at
FROM completables doc
JOIN completables target ON doc.documents_artifact_id = target.id
WHERE doc.completable_type = 'artifact'
  AND doc.artifact_type = 'documentation'
  AND datetime(doc.updated_at) < datetime(target.updated_at);

-- View 11: Artifact Dependency Graph
CREATE VIEW v_artifact_dependency_graph AS
SELECT
    a.id as from_artifact_id,
    a.name as from_artifact_name,
    dep_id.value as to_artifact_id,
    t.name as to_artifact_name,
    a.artifact_type as from_type,
    t.artifact_type as to_type
FROM completables a
JOIN json_each(a.depends_on_artifact_ids_json) dep_id
JOIN completables t ON dep_id.value = t.id
WHERE a.completable_type = 'artifact'
  AND a.depends_on_artifact_ids_json IS NOT NULL;

-- =============================================================================
-- VIEWS: PROGRESS AGGREGATION
-- =============================================================================

-- View 12: Roadmap Progress
CREATE VIEW v_unified_roadmap_progress AS
SELECT
    r.id as roadmap_id,
    COUNT(DISTINCT CASE WHEN t.ticket_type = 'track' THEN t.id END) as tracks_total,
    COUNT(DISTINCT CASE WHEN t.ticket_type = 'track' AND t.status = 'completed' THEN t.id END) as tracks_completed,
    COUNT(DISTINCT CASE WHEN t.ticket_type = 'sprint' THEN t.id END) as sprints_total,
    COUNT(DISTINCT CASE WHEN t.ticket_type = 'sprint' AND t.status = 'completed' THEN t.id END) as sprints_completed,
    COUNT(DISTINCT CASE WHEN t.ticket_type = 'task' THEN t.id END) as tasks_total,
    COUNT(DISTINCT CASE WHEN t.ticket_type = 'task' AND t.status = 'completed' THEN t.id END) as tasks_completed,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN t.ticket_type = 'task' THEN t.id END) > 0
        THEN ROUND(100.0 * COUNT(DISTINCT CASE WHEN t.ticket_type = 'task' AND t.status = 'completed' THEN t.id END)
             / COUNT(DISTINCT CASE WHEN t.ticket_type = 'task' THEN t.id END), 0)
        ELSE 0
    END as completion_percent
FROM completables r
LEFT JOIN completables t ON (
    t.legacy_roadmap_id = r.id
    OR t.parent_id = r.id
    OR EXISTS (
        SELECT 1 FROM completables p WHERE t.parent_id = p.id AND p.parent_id = r.id
    )
    OR EXISTS (
        SELECT 1 FROM completables p1
        JOIN completables p2 ON p1.parent_id = p2.id
        WHERE t.parent_id = p1.id AND p2.parent_id = r.id
    )
)
WHERE r.completable_type = 'ticket' AND r.ticket_type = 'roadmap'
GROUP BY r.id;

-- View 13: Track Progress
CREATE VIEW v_unified_track_progress AS
SELECT
    t.id as track_id,
    COUNT(DISTINCT CASE WHEN c.ticket_type = 'sprint' THEN c.id END) as sprints_total,
    COUNT(DISTINCT CASE WHEN c.ticket_type = 'sprint' AND c.status = 'completed' THEN c.id END) as sprints_completed,
    COUNT(DISTINCT CASE WHEN c.ticket_type = 'task' THEN c.id END) as tasks_total,
    COUNT(DISTINCT CASE WHEN c.ticket_type = 'task' AND c.status = 'completed' THEN c.id END) as tasks_completed,
    CASE
        WHEN COUNT(DISTINCT CASE WHEN c.ticket_type = 'task' THEN c.id END) > 0
        THEN ROUND(100.0 * COUNT(DISTINCT CASE WHEN c.ticket_type = 'task' AND c.status = 'completed' THEN c.id END)
             / COUNT(DISTINCT CASE WHEN c.ticket_type = 'task' THEN c.id END), 0)
        ELSE 0
    END as completion_percent
FROM completables t
LEFT JOIN completables sprint ON sprint.parent_id = t.id AND sprint.ticket_type = 'sprint'
LEFT JOIN completables c ON (c.parent_id = t.id OR c.parent_id = sprint.id)
WHERE t.completable_type = 'ticket' AND t.ticket_type = 'track'
GROUP BY t.id;

-- View 14: Sprint Progress
CREATE VIEW v_unified_sprint_progress AS
SELECT
    s.id as sprint_id,
    COUNT(CASE WHEN t.task_type_detail = 'development' THEN 1 END) as development_tasks_total,
    COUNT(CASE WHEN t.task_type_detail = 'development' AND t.status = 'completed' THEN 1 END) as development_tasks_completed,
    COUNT(CASE WHEN t.task_type_detail = 'completion_gate' THEN 1 END) as completion_gate_tasks_total,
    COUNT(CASE WHEN t.task_type_detail = 'completion_gate' AND t.status = 'completed' THEN 1 END) as completion_gate_tasks_completed,
    COUNT(CASE WHEN t.task_type_detail = 'production_gate' THEN 1 END) as production_gate_tasks_total,
    COUNT(CASE WHEN t.task_type_detail = 'production_gate' AND t.status = 'completed' THEN 1 END) as production_gate_tasks_completed,
    COUNT(*) as tasks_total,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as tasks_completed,
    CASE
        WHEN COUNT(*) > 0
        THEN ROUND(100.0 * COUNT(CASE WHEN t.status = 'completed' THEN 1 END) / COUNT(*), 0)
        ELSE 0
    END as completion_percent
FROM completables s
LEFT JOIN completables t ON t.parent_id = s.id AND t.completable_type = 'ticket' AND t.ticket_type = 'task'
WHERE s.completable_type = 'ticket' AND s.ticket_type = 'sprint'
GROUP BY s.id;

-- =============================================================================
-- DATABASE STATE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS database_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    schema_version TEXT NOT NULL,
    migration_timestamp TEXT NOT NULL,
    last_validated TEXT
);

-- Initialize database state
INSERT OR REPLACE INTO database_state (id, schema_version, migration_timestamp)
VALUES (1, '2.0.0', datetime('now'));
