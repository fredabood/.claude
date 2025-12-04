-- =============================================================================
-- Migration 006: Unified Ticket Schema
-- =============================================================================
-- Adds unified tickets table with single-table inheritance and criteria table
-- for polymorphic completion targets.
--
-- This migration runs alongside the existing schema - it does not drop tables.
-- Data is copied from old tables to new unified structure.
-- =============================================================================

-- Version marker
-- Previous: 1.0.0 (27 tables with separate entity tables)
-- After: 2.0.0 (unified ticket schema with criteria)

-- =============================================================================
-- STEP 1: CREATE UNIFIED TICKETS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS tickets (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    ticket_type TEXT NOT NULL CHECK (ticket_type IN ('roadmap', 'track', 'sprint', 'task')),

    -- Hierarchy & Ordering (ULID system)
    parent_id TEXT REFERENCES tickets(id),
    sequence INTEGER DEFAULT 0,
    slug TEXT,

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do', 'superseded'
    )),
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL,

    -- Work Assignment (JSON)
    assigned_agents_json TEXT,
    priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    estimated_duration TEXT,

    -- Work Evidence (JSON)
    commits_json TEXT,

    -- Requirements (JSON)
    requirements_local_json TEXT,

    -- Deferral Flag
    deferred INTEGER DEFAULT 0,

    -- Metadata (JSON)
    metadata_json TEXT,

    -- Roadmap-specific
    version TEXT,
    version_strategy_json TEXT,
    activity_log_json TEXT,

    -- Track-specific
    strategic_value_json TEXT,

    -- Sprint-specific
    plan_file TEXT,
    goal TEXT,
    success_criteria_json TEXT,
    development_gates_json TEXT,
    blocked_reason TEXT,
    completion_gate_check_at TEXT,
    production_gate_check_at TEXT,
    production_ready_at TEXT,
    deployed_at TEXT,

    -- Task-specific
    task_type_detail TEXT CHECK (task_type_detail IN ('development', 'completion_gate', 'production_gate')),
    estimated_tokens INTEGER,
    actual_tokens INTEGER,
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex', 'high')),
    gate_info_json TEXT,
    audit_results_json TEXT,
    phase_label TEXT,

    -- Legacy reference columns (for migration tracking)
    legacy_sprint_id TEXT,
    legacy_track_id TEXT,
    legacy_roadmap_id TEXT
);

-- =============================================================================
-- STEP 2: CREATE CRITERIA TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS criteria (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    required INTEGER DEFAULT 1,

    -- UNIFIED BLOCKING: which transition does this block?
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed' CHECK (
        blocks_transition_to IN ('in_progress', 'completed', 'production_ready')
    ),

    -- Target (polymorphic via target_type)
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable', 'file_exists', 'test_passes',
        'test_coverage', 'threshold', 'manual', 'external'
    )),
    target_json TEXT NOT NULL,

    -- Cached state
    is_met INTEGER,
    last_checked TEXT
);

-- =============================================================================
-- STEP 3: CREATE INDEXES
-- =============================================================================

-- Ticket lookups
CREATE INDEX IF NOT EXISTS idx_tickets_parent ON tickets(parent_id);
CREATE INDEX IF NOT EXISTS idx_tickets_type ON tickets(ticket_type);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_sequence ON tickets(parent_id, sequence);

-- Legacy ID lookups (for migration)
CREATE INDEX IF NOT EXISTS idx_tickets_legacy_sprint ON tickets(legacy_sprint_id);
CREATE INDEX IF NOT EXISTS idx_tickets_legacy_track ON tickets(legacy_track_id);
CREATE INDEX IF NOT EXISTS idx_tickets_legacy_roadmap ON tickets(legacy_roadmap_id);

-- Criteria lookups
CREATE INDEX IF NOT EXISTS idx_criteria_ticket ON criteria(ticket_id);
CREATE INDEX IF NOT EXISTS idx_criteria_blocks_transition ON criteria(ticket_id, blocks_transition_to);
CREATE INDEX IF NOT EXISTS idx_criteria_target_type ON criteria(target_type);

-- =============================================================================
-- STEP 4: MIGRATE DATA FROM OLD TABLES
-- =============================================================================

-- 4.1 Migrate roadmaps
INSERT OR IGNORE INTO tickets (
    id, name, description, ticket_type,
    parent_id, sequence, slug,
    status, created_at, started_at, completed_at, updated_at,
    assigned_agents_json, priority, estimated_duration,
    commits_json, deferred, metadata_json,
    version, version_strategy_json
)
SELECT
    id, name, NULL as description, 'roadmap' as ticket_type,
    NULL as parent_id, 0 as sequence, NULL as slug,
    status, created as created_at, started as started_at, completed as completed_at,
    COALESCE(created, datetime('now')) as updated_at,
    NULL as assigned_agents_json, NULL as priority, NULL as estimated_duration,
    NULL as commits_json, 0 as deferred, metadata as metadata_json,
    version, version_strategy as version_strategy_json
FROM roadmaps;

-- 4.2 Migrate tracks
INSERT OR IGNORE INTO tickets (
    id, name, description, ticket_type,
    parent_id, sequence, slug,
    status, created_at, started_at, completed_at, updated_at,
    assigned_agents_json, priority, estimated_duration,
    commits_json, deferred, metadata_json,
    strategic_value_json,
    legacy_roadmap_id
)
SELECT
    id, name, NULL as description, 'track' as ticket_type,
    roadmap_id as parent_id, 0 as sequence, NULL as slug,
    status, created as created_at, started as started_at, completed as completed_at,
    COALESCE(created, datetime('now')) as updated_at,
    NULL as assigned_agents_json, priority, estimated_duration,
    NULL as commits_json, 0 as deferred, metadata as metadata_json,
    strategic_value_json,
    roadmap_id as legacy_roadmap_id
FROM tracks;

-- 4.3 Migrate sprints
INSERT OR IGNORE INTO tickets (
    id, name, description, ticket_type,
    parent_id, sequence, slug,
    status, created_at, started_at, completed_at, updated_at,
    assigned_agents_json, priority, estimated_duration,
    commits_json, deferred, metadata_json,
    plan_file, goal, success_criteria_json, development_gates_json,
    blocked_reason, completion_gate_check_at, production_gate_check_at,
    production_ready_at, deployed_at,
    legacy_track_id, legacy_roadmap_id
)
SELECT
    id, name, NULL as description, 'sprint' as ticket_type,
    track_id as parent_id, 0 as sequence, NULL as slug,
    status, created as created_at, started as started_at, completed as completed_at,
    COALESCE(created, datetime('now')) as updated_at,
    NULL as assigned_agents_json, NULL as priority, NULL as estimated_duration,
    NULL as commits_json, 0 as deferred, metadata as metadata_json,
    plan_file, NULL as goal, NULL as success_criteria_json, development_gates_json,
    blocked_reason, completion_gate_check_at, production_gate_check_at,
    production_ready_at, deployed_at,
    track_id as legacy_track_id, roadmap_id as legacy_roadmap_id
FROM sprints;

-- 4.4 Migrate tasks
INSERT OR IGNORE INTO tickets (
    id, name, description, ticket_type,
    parent_id, sequence, slug,
    status, created_at, started_at, completed_at, updated_at,
    assigned_agents_json, priority, estimated_duration,
    commits_json, deferred, metadata_json,
    task_type_detail, estimated_tokens, actual_tokens,
    complexity, gate_info_json, audit_results_json, phase_label,
    legacy_sprint_id, legacy_track_id, legacy_roadmap_id
)
SELECT
    id, title as name, description, 'task' as ticket_type,
    sprint_id as parent_id, 0 as sequence, NULL as slug,
    status, created as created_at, started as started_at, completed as completed_at,
    COALESCE(created, datetime('now')) as updated_at,
    assigned_agents_json, priority, estimated_duration,
    commits_json, 0 as deferred, metadata as metadata_json,
    task_type as task_type_detail, estimated_tokens, actual_tokens,
    complexity, gate_info as gate_info_json, audit_results as audit_results_json, phase_label,
    sprint_id as legacy_sprint_id, track_id as legacy_track_id, roadmap_id as legacy_roadmap_id
FROM tasks;

-- =============================================================================
-- STEP 5: MIGRATE DEPENDENCY RELATIONSHIPS TO CRITERIA
-- =============================================================================

-- 5.1 Convert entity_blocked_by entries to CompletableTarget criteria
-- These are dependencies that block transition to in_progress
INSERT OR IGNORE INTO criteria (
    id, ticket_id, description, required,
    blocks_transition_to, target_type, target_json,
    is_met, last_checked
)
SELECT
    'dep-' || blocked_id || '-' || blocker_id as id,
    blocked_id as ticket_id,
    COALESCE(reason, 'Depends on ' || blocker_id) as description,
    1 as required,
    COALESCE(blocks_transition_to, 'in_progress') as blocks_transition_to,
    'completable' as target_type,
    json_object(
        'type', 'completable',
        'completable_id', blocker_id,
        'required_status', COALESCE(required_status, 'completed')
    ) as target_json,
    NULL as is_met,
    NULL as last_checked
FROM entity_blocked_by
WHERE blocked_type IN ('track', 'sprint', 'task');

-- =============================================================================
-- STEP 6: CREATE AGGREGATION VIEWS
-- =============================================================================

-- 6.1 View for child completion status
CREATE VIEW IF NOT EXISTS v_ticket_children AS
SELECT
    t.id as parent_id,
    t.ticket_type as parent_type,
    c.id as child_id,
    c.ticket_type as child_type,
    c.status as child_status,
    c.deferred as child_deferred
FROM tickets t
JOIN tickets c ON c.parent_id = t.id;

-- 6.2 View for aggregated commits (from children)
CREATE VIEW IF NOT EXISTS v_ticket_commits_aggregated AS
WITH RECURSIVE descendants AS (
    -- Base: start with the ticket itself
    SELECT id, id as root_id, commits_json
    FROM tickets

    UNION ALL

    -- Recursive: add all children
    SELECT t.id, d.root_id, t.commits_json
    FROM tickets t
    JOIN descendants d ON t.parent_id = d.id
)
SELECT
    root_id as ticket_id,
    json_group_array(json(c.value)) as commits_aggregated_json
FROM descendants d
CROSS JOIN json_each(COALESCE(d.commits_json, '[]')) c
WHERE d.commits_json IS NOT NULL AND d.commits_json != '[]'
GROUP BY root_id;

-- 6.3 View for effective standards (inherited from ancestors)
CREATE VIEW IF NOT EXISTS v_ticket_standards_effective AS
WITH RECURSIVE ancestors AS (
    -- Base: the ticket itself
    SELECT id, id as descendant_id, requirements_local_json, 0 as depth
    FROM tickets

    UNION ALL

    -- Recursive: add ancestors
    SELECT t.id, a.descendant_id, t.requirements_local_json, a.depth + 1
    FROM tickets t
    JOIN ancestors a ON a.id = t.parent_id
    WHERE t.parent_id IS NOT NULL
)
SELECT
    descendant_id as ticket_id,
    json_group_array(json(s.value)) as standards_effective_json
FROM ancestors a
CROSS JOIN json_each(COALESCE(a.requirements_local_json, '[]')) s
WHERE a.requirements_local_json IS NOT NULL AND a.requirements_local_json != '[]'
GROUP BY descendant_id;

-- 6.4 View for roadmap progress
CREATE VIEW IF NOT EXISTS v_unified_roadmap_progress AS
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
FROM tickets r
LEFT JOIN tickets t ON (
    t.legacy_roadmap_id = r.id
    OR t.parent_id = r.id
    OR EXISTS (
        SELECT 1 FROM tickets p WHERE t.parent_id = p.id AND p.parent_id = r.id
    )
    OR EXISTS (
        SELECT 1 FROM tickets p1
        JOIN tickets p2 ON p1.parent_id = p2.id
        WHERE t.parent_id = p1.id AND p2.parent_id = r.id
    )
)
WHERE r.ticket_type = 'roadmap'
GROUP BY r.id;

-- 6.5 View for track progress
CREATE VIEW IF NOT EXISTS v_unified_track_progress AS
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
FROM tickets t
LEFT JOIN tickets sprint ON sprint.parent_id = t.id AND sprint.ticket_type = 'sprint'
LEFT JOIN tickets c ON (c.parent_id = t.id OR c.parent_id = sprint.id)
WHERE t.ticket_type = 'track'
GROUP BY t.id;

-- 6.6 View for sprint progress
CREATE VIEW IF NOT EXISTS v_unified_sprint_progress AS
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
FROM tickets s
LEFT JOIN tickets t ON t.parent_id = s.id AND t.ticket_type = 'task'
WHERE s.ticket_type = 'sprint'
GROUP BY s.id;

-- 6.7 View for required children (for CompletableTarget blocking)
CREATE VIEW IF NOT EXISTS v_ticket_required_children AS
SELECT
    c.ticket_id as parent_id,
    json_extract(c.target_json, '$.completable_id') as child_id,
    c.blocks_transition_to,
    t.deferred as child_deferred,
    t.status as child_status,
    json_extract(c.target_json, '$.required_status') as required_status
FROM criteria c
JOIN tickets t ON json_extract(c.target_json, '$.completable_id') = t.id
WHERE c.target_type = 'completable';

-- =============================================================================
-- STEP 7: UPDATE SCHEMA VERSION
-- =============================================================================

UPDATE database_state SET schema_version = '2.0.0' WHERE id = 1;
