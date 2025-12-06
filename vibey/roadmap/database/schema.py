"""
SQLite schema definitions for roadmap database.

This module contains the DDL for creating the database schema.
Schema is populated in task-002.

Tables (27 total):
- Core Entities (4): roadmaps, tracks, sprints, tasks
- Relationships (4): external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on
- Quality & Gates (2): quality_gates, development_gates
- Supporting Data (7): deliverables, entity_deliverables, commits, entity_commits,
                       assigned_agents, standards, strategic_value
- Roadmap-Level (2): version_history, activity_log
- Summaries (3): track_summaries, sprint_summaries, task_summaries
- Sync & Validation (3): yaml_checksums, database_state, sync_conflicts
- Audit Trail (1): audit_trail
- Artifact System (1): artifacts
"""

import sqlite3
from typing import Optional
from pathlib import Path

from .connection import get_connection, transaction


# Schema version - increment on breaking changes
SCHEMA_VERSION = "1.0.0"


def get_schema_ddl() -> str:
    """
    Get the complete DDL for creating all tables.

    Returns:
        SQL string with CREATE TABLE statements

    Tables (27 total):
    - Core Entities (4): roadmaps, tracks, sprints, tasks
    - Relationships (4): external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on
    - Quality & Gates (2): quality_gates, development_gates
    - Supporting Data (7): deliverables, entity_deliverables, commits, entity_commits,
                          assigned_agents, standards, strategic_value
    - Roadmap-Level (2): version_history, activity_log
    - Summaries (3): track_summaries, sprint_summaries, task_summaries
    - Sync & Validation (3): yaml_checksums, database_state, sync_conflicts
    - Audit Trail (1): audit_trail
    - Artifact System (1): artifacts
    """
    return """
-- =============================================================================
-- CORE ENTITY TABLES (4)
-- =============================================================================

-- 1. roadmaps
CREATE TABLE IF NOT EXISTS roadmaps (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do', 'superseded'
    )),
    blocked INTEGER NOT NULL DEFAULT 0,

    -- Timestamps (ISO 8601)
    created TEXT NOT NULL,
    started TEXT,
    target_completion TEXT,
    completed TEXT,
    deployed TEXT,

    -- Version Strategy (JSON blob - rarely queried)
    version_strategy TEXT,

    -- Metadata (JSON)
    metadata TEXT
);

-- 2. tracks
CREATE TABLE IF NOT EXISTS tracks (
    -- Identity
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    name TEXT NOT NULL,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do', 'superseded'
    )),
    blocked INTEGER NOT NULL DEFAULT 0,
    priority TEXT CHECK (priority IN ('critical', 'high', 'medium', 'low')),

    -- Timestamps
    created TEXT NOT NULL,
    started TEXT,
    completed TEXT,

    -- Estimates
    estimated_duration TEXT,

    -- Authored data (JSON arrays) - these are NOT aggregated from children
    dependencies_json TEXT,  -- JSON array of external dependency descriptions
    standards_json TEXT,  -- JSON array of Standard objects (can inherit down)
    strategic_value_json TEXT,  -- JSON array of strategic value descriptions

    -- Note: commits, deliverables, assigned_agents, estimated_duration aggregate up from sprints via views

    -- Metadata (JSON)
    metadata TEXT
);

-- 3. sprints
CREATE TABLE IF NOT EXISTS sprints (
    -- Identity
    id TEXT PRIMARY KEY,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id),
    name TEXT NOT NULL,

    -- Status & Lifecycle
    status TEXT NOT NULL CHECK (status IN (
        'not_started', 'in_progress', 'paused',
        'completion_gate_check', 'completed',
        'production_gate_check', 'production_ready', 'deployed', 'wont_do', 'superseded'
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

    -- Content fields (for full YAML fidelity)
    description TEXT,
    goal TEXT,
    estimated_duration TEXT,
    notes TEXT,

    -- Authored data (JSON arrays) - these are NOT aggregated from children
    dependencies_json TEXT,  -- JSON array of external dependency descriptions
    standards_json TEXT,  -- JSON array of Standard objects (can inherit down)
    development_gates_json TEXT,  -- JSON array of DevelopmentGate objects
    success_criteria_json TEXT,  -- JSON array of success criterion strings
    risks_json TEXT,  -- JSON array of risk descriptions
    deliverables_json TEXT,  -- JSON array of Deliverable objects
    quality_gates_json TEXT,  -- JSON array of QualityGate objects
    progress_json TEXT,  -- JSON object for progress (for round-trip fidelity)
    tasks_json TEXT,  -- JSON array of task summaries (for round-trip fidelity)

    -- Metadata (JSON)
    metadata TEXT
);

-- 4. tasks
CREATE TABLE IF NOT EXISTS tasks (
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
        'completion_gate_check', 'completed', 'wont_do', 'superseded'
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

    -- Authored data (JSON arrays) - source of truth, aggregates up to sprints/tracks
    commits_json TEXT,  -- JSON array of GitCommit objects
    deliverables_json TEXT,  -- JSON array of Deliverable objects
    dependencies_json TEXT,  -- JSON array of external dependency descriptions
    standards_json TEXT,  -- JSON array of Standard objects (can inherit from sprint/track)
    assigned_agents_json TEXT,  -- JSON array of agent names working on this task
    estimated_duration TEXT,  -- Human/AI-provided time estimate

    -- Metadata (JSON)
    metadata TEXT
);

-- =============================================================================
-- RELATIONSHIP TABLES (4)
-- =============================================================================

-- 5. external_dependencies
-- External prerequisites (not roadmap entities)
CREATE TABLE IF NOT EXISTS external_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (roadmap, track, sprint, or task)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('roadmap', 'track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Dependency details
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK (status IN ('pending', 'resolved', 'blocked')),
    resolved_at TEXT,

    -- Metadata (JSON)
    metadata TEXT
);

-- 6. entity_blocks
-- "This entity blocks these other entities from starting"
CREATE TABLE IF NOT EXISTS entity_blocks (
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

-- 7. entity_blocked_by
-- "This entity is blocked by these other entities" (inverse of entity_blocks)
CREATE TABLE IF NOT EXISTS entity_blocked_by (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Blocked entity (waiting)
    blocked_type TEXT NOT NULL CHECK (blocked_type IN ('track', 'sprint', 'task')),
    blocked_id TEXT NOT NULL,

    -- Blocking entity (must complete first)
    blocker_type TEXT NOT NULL CHECK (blocker_type IN ('track', 'sprint', 'task')),
    blocker_id TEXT NOT NULL,

    -- Dependency business logic
    required_status TEXT DEFAULT 'completed',  -- Status blocker must reach to unblock (e.g., 'completed', 'production_ready')
    blocks_transition_to TEXT DEFAULT 'in_progress',  -- What transition this blocks (e.g., 'in_progress', 'completed')

    -- Context
    reason TEXT,

    UNIQUE(blocked_type, blocked_id, blocker_type, blocker_id)
);

-- 8. entity_depends_on
-- Same-level dependencies between sibling entities (soft dependencies)
CREATE TABLE IF NOT EXISTS entity_depends_on (
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

-- =============================================================================
-- QUALITY & GATES (2)
-- =============================================================================

-- 9. quality_gates
-- Quality gates at track AND sprint levels
CREATE TABLE IF NOT EXISTS quality_gates (
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

    -- Metadata (JSON)
    metadata TEXT
);

-- 10. development_gates
-- External development dependencies for sprints
CREATE TABLE IF NOT EXISTS development_gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id TEXT NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,

    -- Gate details
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'blocked')),
    resolved_at TEXT
);

-- =============================================================================
-- SUPPORTING DATA TABLES (7)
-- =============================================================================

-- 11. deliverables
CREATE TABLE IF NOT EXISTS deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Deliverable details
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    completed_at TEXT,

    -- Optional artifact reference
    artifact_path TEXT,
    artifact_url TEXT
);

-- 12. entity_deliverables (junction table for many-to-many)
CREATE TABLE IF NOT EXISTS entity_deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (track, sprint, or task)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Deliverable reference
    deliverable_id INTEGER NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,

    UNIQUE(owner_type, owner_id, deliverable_id)
);

-- 13. commits
CREATE TABLE IF NOT EXISTS commits (
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

-- 14. entity_commits (junction table for many-to-many)
CREATE TABLE IF NOT EXISTS entity_commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner (track, sprint, or task)
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Commit reference
    commit_id INTEGER NOT NULL REFERENCES commits(id) ON DELETE CASCADE,

    UNIQUE(owner_type, owner_id, commit_id)
);

-- 15. assigned_agents
CREATE TABLE IF NOT EXISTS assigned_agents (
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

-- 16. standards
CREATE TABLE IF NOT EXISTS standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint')),
    owner_id TEXT NOT NULL,

    -- Standard reference
    standard_name TEXT NOT NULL,
    standard_url TEXT,
    description TEXT
);

-- 17. strategic_value
CREATE TABLE IF NOT EXISTS strategic_value (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    value_statement TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);

-- =============================================================================
-- ROADMAP-LEVEL TABLES (2)
-- =============================================================================

-- 18. version_history
CREATE TABLE IF NOT EXISTS version_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,

    -- Version details
    version TEXT NOT NULL,
    released_at TEXT NOT NULL,
    description TEXT,

    -- Changes summary (JSON array)
    changes TEXT
);

-- 19. activity_log
CREATE TABLE IF NOT EXISTS activity_log (
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

    -- State snapshots for time-travel and debugging
    old_state TEXT,  -- JSON snapshot of entity before change
    new_state TEXT,  -- JSON snapshot of entity after change

    -- Additional data (JSON)
    metadata TEXT
);

-- =============================================================================
-- SUMMARY TABLES (3) - Denormalized for YAML Export
-- =============================================================================

-- 20. track_summaries (stored in roadmap.yaml under tracks[])
CREATE TABLE IF NOT EXISTS track_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,

    -- Summary fields (denormalized)
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT,

    UNIQUE(roadmap_id, track_id)
);

-- 21. sprint_summaries (stored in track.yaml under sprints[])
CREATE TABLE IF NOT EXISTS sprint_summaries (
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

-- 22. task_summaries (stored in sprint.yaml under tasks[])
CREATE TABLE IF NOT EXISTS task_summaries (
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

-- =============================================================================
-- SYNC & VALIDATION TABLES (3)
-- =============================================================================

-- 23. yaml_checksums
-- Tracks checksums of YAML files at time of database load
CREATE TABLE IF NOT EXISTS yaml_checksums (
    file_path TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,  -- SHA256 of file content at load time
    loaded_at TEXT NOT NULL,  -- When the file was loaded into DB
    file_size INTEGER,  -- File size in bytes at load time
    last_modified TEXT  -- File modification time at load time
);

-- 24. database_state
-- Tracks the overall state of the database for sync management
CREATE TABLE IF NOT EXISTS database_state (
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

-- Initialize singleton row for database_state
INSERT OR IGNORE INTO database_state (id, schema_version) VALUES (1, '1.0.0');

-- 25. sync_conflicts
-- Records detected conflicts between DB and YAML for resolution
CREATE TABLE IF NOT EXISTS sync_conflicts (
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

    -- Details (JSON)
    db_value TEXT,
    yaml_value TEXT,
    description TEXT
);

-- 26. audit_trail
-- Field-level change tracking for tracks, sprints, and tasks
-- Separate from activity_log which tracks roadmap-level events
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- When
    timestamp TEXT NOT NULL,

    -- What changed
    object_type TEXT NOT NULL CHECK (object_type IN ('track', 'sprint', 'task')),
    object_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,

    -- Who/why
    changed_by TEXT NOT NULL,
    reason TEXT NOT NULL,

    -- Context
    commit_sha TEXT,  -- Git commit SHA (short form)
    source TEXT NOT NULL CHECK (source IN ('cli', 'mcp', 'manual', 'automated', 'system'))
);

-- =============================================================================
-- ARTIFACT SYSTEM TABLES (1)
-- =============================================================================

-- 27. artifacts
-- First-class artifact entities for tracking code, docs, configs, etc.
-- Design reference: UNIFIED_TICKET_ARCHITECTURE.md Part 13.9
CREATE TABLE IF NOT EXISTS artifacts (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    -- File Location
    paths TEXT NOT NULL,  -- JSON array of file paths
    content_hash TEXT,
    last_verified TEXT,  -- ISO timestamp

    -- Classification
    artifact_type TEXT NOT NULL CHECK (artifact_type IN (
        'code', 'test', 'config', 'documentation', 'context',
        'agent', 'workflow', 'template', 'data', 'asset', 'schema', 'other'
    )),
    artifact_subtype TEXT,

    -- Provenance (JSON object with provenance_type and related fields)
    provenance TEXT NOT NULL,

    -- Relationships
    documents_artifact_id TEXT,  -- FK to artifact this documents
    depends_on_artifact_ids TEXT,  -- JSON array of artifact IDs

    -- State
    file_exists INTEGER NOT NULL DEFAULT 1,
    is_stale INTEGER NOT NULL DEFAULT 0,

    -- Staleness tracking (for documentation artifacts)
    documented_source_hash TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    -- Foreign keys
    FOREIGN KEY (documents_artifact_id) REFERENCES artifacts(id)
);
"""


def get_index_ddl() -> str:
    """
    Get the DDL for creating all indexes.

    Returns:
        SQL string with CREATE INDEX statements

    Index Categories:
    - Primary lookups: Foreign key relationships
    - Status queries: Filter by status
    - Blocking queries: Entity blocking relationships
    - Polymorphic queries: owner_type + owner_id
    - Time-based queries: Activity log, checksums
    """
    return """
-- =============================================================================
-- PRIMARY LOOKUP INDEXES
-- =============================================================================

-- Track lookups by roadmap
CREATE INDEX IF NOT EXISTS idx_tracks_roadmap ON tracks(roadmap_id);

-- Sprint lookups by track and roadmap
CREATE INDEX IF NOT EXISTS idx_sprints_track ON sprints(track_id);
CREATE INDEX IF NOT EXISTS idx_sprints_roadmap ON sprints(roadmap_id);

-- Task lookups by sprint, track, roadmap
CREATE INDEX IF NOT EXISTS idx_tasks_sprint ON tasks(sprint_id);
CREATE INDEX IF NOT EXISTS idx_tasks_track ON tasks(track_id);
CREATE INDEX IF NOT EXISTS idx_tasks_roadmap ON tasks(roadmap_id);

-- =============================================================================
-- STATUS INDEXES
-- =============================================================================

-- Quick status filtering
CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);
CREATE INDEX IF NOT EXISTS idx_sprints_status ON sprints(status);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Blocked entity lookup
CREATE INDEX IF NOT EXISTS idx_tracks_blocked ON tracks(blocked) WHERE blocked = 1;
CREATE INDEX IF NOT EXISTS idx_sprints_blocked ON sprints(blocked) WHERE blocked = 1;
CREATE INDEX IF NOT EXISTS idx_tasks_blocked ON tasks(blocked) WHERE blocked = 1;

-- =============================================================================
-- RELATIONSHIP TABLE INDEXES
-- =============================================================================

-- External dependencies by owner
CREATE INDEX IF NOT EXISTS idx_external_deps_owner ON external_dependencies(owner_type, owner_id);

-- Entity blocks - lookup by blocker and blocked
CREATE INDEX IF NOT EXISTS idx_entity_blocks_blocker ON entity_blocks(blocker_type, blocker_id);
CREATE INDEX IF NOT EXISTS idx_entity_blocks_blocked ON entity_blocks(blocked_type, blocked_id);

-- Entity blocked_by - lookup by blocked and blocker
CREATE INDEX IF NOT EXISTS idx_entity_blocked_by_blocked ON entity_blocked_by(blocked_type, blocked_id);
CREATE INDEX IF NOT EXISTS idx_entity_blocked_by_blocker ON entity_blocked_by(blocker_type, blocker_id);

-- Entity depends_on - lookup by dependent and dependency
CREATE INDEX IF NOT EXISTS idx_depends_on_dependent ON entity_depends_on(dependent_type, dependent_id);
CREATE INDEX IF NOT EXISTS idx_depends_on_dependency ON entity_depends_on(dependency_type, dependency_id);

-- =============================================================================
-- QUALITY GATE INDEXES
-- =============================================================================

-- Quality gates by owner and status
CREATE INDEX IF NOT EXISTS idx_quality_gates_owner ON quality_gates(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_quality_gates_status ON quality_gates(status);

-- Development gates by sprint
CREATE INDEX IF NOT EXISTS idx_dev_gates_sprint ON development_gates(sprint_id);

-- =============================================================================
-- SUPPORTING DATA INDEXES
-- =============================================================================

-- Entity deliverables by owner and deliverable
CREATE INDEX IF NOT EXISTS idx_entity_deliverables_owner ON entity_deliverables(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_entity_deliverables_deliverable ON entity_deliverables(deliverable_id);

-- Commits by hash (for deduplication)
CREATE INDEX IF NOT EXISTS idx_commits_hash ON commits(commit_hash);

-- Entity commits by owner and commit
CREATE INDEX IF NOT EXISTS idx_entity_commits_owner ON entity_commits(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_entity_commits_commit ON entity_commits(commit_id);

-- Assigned agents by owner
CREATE INDEX IF NOT EXISTS idx_assigned_agents_owner ON assigned_agents(owner_type, owner_id);

-- Standards by owner
CREATE INDEX IF NOT EXISTS idx_standards_owner ON standards(owner_type, owner_id);

-- Strategic value by track
CREATE INDEX IF NOT EXISTS idx_strategic_value_track ON strategic_value(track_id);

-- =============================================================================
-- ROADMAP-LEVEL INDEXES
-- =============================================================================

-- Version history by roadmap
CREATE INDEX IF NOT EXISTS idx_version_history_roadmap ON version_history(roadmap_id);

-- Activity log by roadmap, time, and entity
CREATE INDEX IF NOT EXISTS idx_activity_log_roadmap ON activity_log(roadmap_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_time ON activity_log(occurred_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_entity ON activity_log(entity_type, entity_id);

-- =============================================================================
-- SYNC & VALIDATION INDEXES
-- =============================================================================

-- Unresolved sync conflicts
CREATE INDEX IF NOT EXISTS idx_sync_conflicts_unresolved ON sync_conflicts(resolved_at) WHERE resolved_at IS NULL;

-- =============================================================================
-- AUDIT TRAIL INDEXES
-- =============================================================================

-- Audit trail by object (for history lookups)
CREATE INDEX IF NOT EXISTS idx_audit_trail_object ON audit_trail(object_type, object_id);

-- Audit trail by time (for recent changes)
CREATE INDEX IF NOT EXISTS idx_audit_trail_time ON audit_trail(timestamp);

-- Audit trail by field (for field-specific history)
CREATE INDEX IF NOT EXISTS idx_audit_trail_field ON audit_trail(object_id, field);

-- =============================================================================
-- ARTIFACT SYSTEM INDEXES
-- =============================================================================

-- Artifact type for filtering by category
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);

-- Documentation relationships (documents_artifact_id)
CREATE INDEX IF NOT EXISTS idx_artifacts_documents ON artifacts(documents_artifact_id);

-- Stale artifacts (partial index for efficient staleness queries)
CREATE INDEX IF NOT EXISTS idx_artifacts_stale ON artifacts(is_stale) WHERE is_stale = 1;

-- Artifact existence (for filtering existing vs deleted)
CREATE INDEX IF NOT EXISTS idx_artifacts_exists ON artifacts(file_exists) WHERE file_exists = 1;
"""


def get_views_ddl() -> str:
    """
    Get the DDL for creating artifact-related views.

    Returns:
        SQL string with CREATE VIEW statements

    Views:
    1. v_orphan_artifacts - Artifacts not referenced by any criterion
    2. v_documentation_graph - Links between docs and their sources
    3. v_stale_documentation - Documentation that needs updating
    4. v_artifact_criteria - Which criteria reference each artifact

    Note: Views referencing the criteria table require the unified ticket
    schema to be present. Views are created with IF NOT EXISTS to be
    idempotent.
    """
    return """
-- =============================================================================
-- ARTIFACT SYSTEM VIEWS
-- =============================================================================

-- 1. v_orphan_artifacts
-- Artifacts that exist but are not referenced by any criterion
-- Note: Requires criteria table from unified ticket schema
-- If criteria table doesn't exist, this view will show all existing artifacts
CREATE VIEW IF NOT EXISTS v_orphan_artifacts AS
SELECT a.*
FROM artifacts a
WHERE a.file_exists = 1
  AND NOT EXISTS (
    SELECT 1 FROM criteria c
    WHERE c.target_type = 'artifact'
      AND json_extract(c.target_data, '$.artifact_id') = a.id
  );

-- 2. v_documentation_graph
-- Links between documentation artifacts and their source artifacts
-- Shows the relationship between docs and what they document
CREATE VIEW IF NOT EXISTS v_documentation_graph AS
SELECT
    doc.id AS doc_id,
    doc.name AS doc_name,
    doc.artifact_type AS doc_type,
    doc.is_stale,
    src.id AS source_id,
    src.name AS source_name,
    src.artifact_type AS source_type,
    src.content_hash AS source_hash,
    doc.documented_source_hash AS documented_hash,
    CASE
        WHEN src.content_hash IS NOT NULL
             AND doc.documented_source_hash IS NOT NULL
             AND src.content_hash != doc.documented_source_hash THEN 1
        ELSE 0
    END AS needs_update
FROM artifacts doc
JOIN artifacts src ON doc.documents_artifact_id = src.id
WHERE doc.documents_artifact_id IS NOT NULL;

-- 3. v_stale_documentation
-- Documentation artifacts that need updating
-- Either explicitly marked stale or source hash has changed
CREATE VIEW IF NOT EXISTS v_stale_documentation AS
SELECT * FROM v_documentation_graph
WHERE needs_update = 1 OR is_stale = 1;

-- 4. v_artifact_criteria
-- Which criteria reference each artifact
-- Useful for understanding what completion criteria depend on artifacts
-- Note: Requires criteria table from unified ticket schema
CREATE VIEW IF NOT EXISTS v_artifact_criteria AS
SELECT
    a.id AS artifact_id,
    a.name AS artifact_name,
    a.artifact_type,
    c.id AS criterion_id,
    c.description AS criterion_description,
    c.ticket_id,
    c.blocks_transition_to
FROM artifacts a
JOIN criteria c ON json_extract(c.target_data, '$.artifact_id') = a.id
WHERE c.target_type = 'artifact'
  AND a.file_exists = 1;
"""


def create_schema(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    include_views: bool = False,
) -> None:
    """
    Create the database schema.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.
        include_views: Whether to create artifact views. Views that reference
            the criteria table require the unified ticket schema to be present.
            Default False to avoid errors when criteria table doesn't exist.

    Raises:
        sqlite3.Error: If schema creation fails

    Note:
        executescript() auto-commits, so we don't wrap in a transaction.
        IF NOT EXISTS clauses make this idempotent.
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    # executescript() auto-commits after each statement
    # Use IF NOT EXISTS for idempotency
    conn.executescript(get_schema_ddl())
    conn.executescript(get_index_ddl())

    # Views are optional - some require criteria table from unified ticket schema
    if include_views:
        conn.executescript(get_views_ddl())


def schema_exists(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> bool:
    """
    Check if the schema has been created.

    Checks for the existence of the database_state table,
    which is created as part of schema initialization.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        True if schema exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='database_state'"
    ).fetchone()

    return result is not None


def get_schema_version(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Get the current schema version from the database.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        Schema version string, or None if not set
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    if not schema_exists(conn):
        return None

    result = conn.execute(
        "SELECT schema_version FROM database_state WHERE id = 1"
    ).fetchone()

    return result[0] if result else None


def drop_all_tables(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> None:
    """
    Drop all tables from the database.

    WARNING: This is destructive and cannot be undone.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    # Get all table names
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    # Disable foreign keys temporarily
    conn.execute("PRAGMA foreign_keys = OFF")

    try:
        with transaction(conn) as txn:
            for (table_name,) in tables:
                txn.execute(f"DROP TABLE IF EXISTS {table_name}")
    finally:
        # Re-enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")


# Expected tables in the schema
EXPECTED_TABLES = [
    # Core Entities (4)
    "roadmaps",
    "tracks",
    "sprints",
    "tasks",
    # Relationships (4)
    "external_dependencies",
    "entity_blocks",
    "entity_blocked_by",
    "entity_depends_on",
    # Quality & Gates (2)
    "quality_gates",
    "development_gates",
    # Supporting Data (7)
    "deliverables",
    "entity_deliverables",
    "commits",
    "entity_commits",
    "assigned_agents",
    "standards",
    "strategic_value",
    # Roadmap-Level (2)
    "version_history",
    "activity_log",
    # Summaries (3)
    "track_summaries",
    "sprint_summaries",
    "task_summaries",
    # Sync & Validation (3)
    "yaml_checksums",
    "database_state",
    "sync_conflicts",
    # Audit Trail (1)
    "audit_trail",
    # Artifact System (1)
    "artifacts",
    # Criteria System (1) - Sprint 12
    "criteria",
]


def get_table_names(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> list[str]:
    """
    Get a list of all table names in the database.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        List of table names
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    return [row[0] for row in result]


def get_index_names(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> list[str]:
    """
    Get a list of all index names in the database.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        List of index names
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    return [row[0] for row in result]


def validate_schema(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> dict[str, any]:
    """
    Validate that the schema is complete and correct.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        Dictionary with validation results:
        - valid: True if schema is valid
        - table_count: Number of tables
        - index_count: Number of indexes
        - missing_tables: Tables missing from schema
        - extra_tables: Tables not in expected list
        - schema_version: Current schema version
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    tables = set(get_table_names(conn))
    expected = set(EXPECTED_TABLES)

    missing = expected - tables
    extra = tables - expected

    result = {
        "valid": len(missing) == 0 and len(extra) == 0,
        "table_count": len(tables),
        "index_count": len(get_index_names(conn)),
        "missing_tables": list(missing),
        "extra_tables": list(extra),
        "schema_version": get_schema_version(conn),
    }

    return result


# =============================================================================
# UNIFIED SCHEMA (v2.0)
# =============================================================================


def get_unified_schema_ddl() -> str:
    """
    Get DDL for the unified ticket schema.

    This creates the `tickets` and `criteria` tables for the unified model.
    Part of schema version 2.0.0.

    Returns:
        SQL DDL string
    """
    return """
-- =============================================================================
-- UNIFIED TICKET SCHEMA
-- =============================================================================

-- Tickets table (single-table inheritance)
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

-- Criteria table (polymorphic targets)
-- Criteria can be attached to any completable entity (roadmap, track, sprint, task, artifact)
CREATE TABLE IF NOT EXISTS criteria (
    id TEXT PRIMARY KEY,

    -- Polymorphic owner (any completable entity)
    completable_type TEXT NOT NULL CHECK (completable_type IN (
        'roadmap', 'track', 'sprint', 'task', 'artifact'
    )),
    completable_id TEXT NOT NULL,

    description TEXT NOT NULL,
    required INTEGER DEFAULT 1,

    -- UNIFIED BLOCKING: which transition does this block?
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed' CHECK (
        blocks_transition_to IN ('in_progress', 'completed', 'production_ready')
    ),

    -- Target (polymorphic via target_type + target_json)
    -- All 8 target types from Sprint 6 design
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable',     -- Another completable must reach status
        'file_exists',     -- File(s) must exist at path(s)
        'test_passes',     -- Test command must pass
        'test_coverage',   -- Test coverage must meet threshold
        'threshold',       -- Generic metric threshold (e.g., quality gates)
        'manual',          -- Human assessment required
        'external',        -- External system check
        'artifact'         -- Artifact entity must exist and be valid
    )),
    target_json TEXT NOT NULL,  -- JSON with target-specific fields

    -- Cached state (updated by refresh operations)
    is_met INTEGER,
    last_checked TEXT,

    -- Audit
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- =============================================================================
-- UNIFIED INDEXES
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
CREATE INDEX IF NOT EXISTS idx_criteria_completable ON criteria(completable_type, completable_id);
CREATE INDEX IF NOT EXISTS idx_criteria_blocks_transition ON criteria(completable_type, completable_id, blocks_transition_to);
CREATE INDEX IF NOT EXISTS idx_criteria_target_type ON criteria(target_type);
CREATE INDEX IF NOT EXISTS idx_criteria_is_met ON criteria(is_met) WHERE is_met = 0;  -- Find unmet criteria
"""


def get_unified_views_ddl() -> str:
    """
    Get DDL for unified schema aggregation views.

    Returns:
        SQL DDL string
    """
    return """
-- =============================================================================
-- UNIFIED AGGREGATION VIEWS
-- =============================================================================

-- View for child completion status
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

-- View for aggregated commits (from children)
CREATE VIEW IF NOT EXISTS v_ticket_commits_aggregated AS
WITH RECURSIVE descendants AS (
    SELECT id, id as root_id, commits_json
    FROM tickets
    UNION ALL
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

-- View for unified roadmap progress
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
LEFT JOIN tickets t ON t.legacy_roadmap_id = r.id OR t.parent_id = r.id
WHERE r.ticket_type = 'roadmap'
GROUP BY r.id;

-- View for unified track progress
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

-- View for unified sprint progress
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

-- View for required children (for CompletableTarget blocking)
CREATE VIEW IF NOT EXISTS v_ticket_required_children AS
SELECT
    c.completable_type as parent_type,
    c.completable_id as parent_id,
    json_extract(c.target_json, '$.completable_id') as child_id,
    c.blocks_transition_to,
    t.deferred as child_deferred,
    t.status as child_status,
    json_extract(c.target_json, '$.required_status') as required_status
FROM criteria c
JOIN tickets t ON json_extract(c.target_json, '$.completable_id') = t.id
WHERE c.target_type = 'completable';

-- View for criteria evaluation status by completable
CREATE VIEW IF NOT EXISTS v_criteria_status AS
SELECT
    c.completable_type,
    c.completable_id,
    c.blocks_transition_to,
    COUNT(*) as total_criteria,
    SUM(CASE WHEN c.is_met = 1 THEN 1 ELSE 0 END) as met_criteria,
    SUM(CASE WHEN c.is_met = 0 OR c.is_met IS NULL THEN 1 ELSE 0 END) as unmet_criteria,
    CASE
        WHEN COUNT(*) = 0 THEN 100
        ELSE ROUND(100.0 * SUM(CASE WHEN c.is_met = 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
    END as completion_percent
FROM criteria c
WHERE c.required = 1
GROUP BY c.completable_type, c.completable_id, c.blocks_transition_to;

-- View for blocking criteria (unmet required criteria)
CREATE VIEW IF NOT EXISTS v_blocking_criteria AS
SELECT
    c.*,
    json_extract(c.target_json, '$.completable_id') as target_completable_id,
    json_extract(c.target_json, '$.required_status') as target_required_status
FROM criteria c
WHERE c.required = 1
  AND (c.is_met = 0 OR c.is_met IS NULL);
"""


def create_unified_schema(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
    include_views: bool = True,
) -> None:
    """
    Create the unified ticket schema.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.
        include_views: Whether to create aggregation views.
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    conn.executescript(get_unified_schema_ddl())
    if include_views:
        conn.executescript(get_unified_views_ddl())


def run_migration(
    migration_name: str,
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> bool:
    """
    Run a specific migration by name.

    Args:
        migration_name: Name of migration file (e.g., "006_unified_ticket_schema.sql")
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        True if migration succeeded

    Raises:
        FileNotFoundError: If migration file doesn't exist
        sqlite3.Error: If migration fails
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    # Find migration file
    migrations_dir = Path(__file__).parent / "migrations"
    migration_path = migrations_dir / migration_name

    if not migration_path.exists():
        raise FileNotFoundError(f"Migration not found: {migration_path}")

    # Read and execute migration
    migration_sql = migration_path.read_text()
    conn.executescript(migration_sql)

    return True


def has_unified_schema(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> bool:
    """
    Check if the unified ticket schema exists.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        True if tickets and criteria tables exist
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    tables = set(get_table_names(conn))
    return "tickets" in tables and "criteria" in tables


# Expected tables for unified schema validation
EXPECTED_UNIFIED_TABLES = [
    "tickets",
    "criteria",
]


# =============================================================================
# CRITERIA TABLE (can be added to existing schema without full migration)
# =============================================================================


def get_criteria_table_ddl() -> str:
    """
    Get DDL for just the criteria table.

    This can be added to the existing legacy schema (roadmaps, tracks, sprints, tasks)
    without requiring a full migration to the unified tickets table.

    The criteria table uses polymorphic references (completable_type + completable_id)
    to attach criteria to any entity type.

    Returns:
        SQL DDL string for criteria table and indexes
    """
    return """
-- =============================================================================
-- CRITERIA TABLE (Sprint 12 - Unified Ticket Architecture)
-- =============================================================================

-- Criteria can be attached to any completable entity (roadmap, track, sprint, task, artifact)
-- This replaces the separate quality_gates, entity_blocked_by, deliverables tables
-- with a unified criterion-based blocking system.
CREATE TABLE IF NOT EXISTS criteria (
    id TEXT PRIMARY KEY,

    -- Polymorphic owner (any completable entity)
    completable_type TEXT NOT NULL CHECK (completable_type IN (
        'roadmap', 'track', 'sprint', 'task', 'artifact'
    )),
    completable_id TEXT NOT NULL,

    description TEXT NOT NULL,
    required INTEGER DEFAULT 1,

    -- UNIFIED BLOCKING: which transition does this block?
    -- IN_PROGRESS = dependency (must be met before starting)
    -- COMPLETED = success criteria (must be met before completing)
    -- PRODUCTION_READY = production gate (must be met before deploying)
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed' CHECK (
        blocks_transition_to IN ('in_progress', 'completed', 'production_ready')
    ),

    -- Target (polymorphic via target_type + target_json)
    -- All 8 target types from Sprint 6 design
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable',     -- Another completable must reach status
        'file_exists',     -- File(s) must exist at path(s)
        'test_passes',     -- Test command must pass
        'test_coverage',   -- Test coverage must meet threshold
        'threshold',       -- Generic metric threshold (e.g., quality gates)
        'manual',          -- Human assessment required
        'external',        -- External system check
        'artifact'         -- Artifact entity must exist and be valid
    )),
    target_json TEXT NOT NULL,  -- JSON with target-specific fields

    -- Cached state (updated by refresh operations)
    is_met INTEGER,
    last_checked TEXT,

    -- Audit
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- =============================================================================
-- CRITERIA INDEXES
-- =============================================================================

-- Primary lookup: find all criteria for a completable
CREATE INDEX IF NOT EXISTS idx_criteria_completable ON criteria(completable_type, completable_id);

-- Transition-specific lookup: find criteria blocking a specific transition
CREATE INDEX IF NOT EXISTS idx_criteria_blocks_transition ON criteria(completable_type, completable_id, blocks_transition_to);

-- Target type lookup: find all criteria of a specific type
CREATE INDEX IF NOT EXISTS idx_criteria_target_type ON criteria(target_type);

-- Unmet criteria lookup: find blocking criteria efficiently
CREATE INDEX IF NOT EXISTS idx_criteria_is_met ON criteria(is_met) WHERE is_met = 0;

-- =============================================================================
-- CRITERIA VIEWS
-- =============================================================================

-- View for criteria evaluation status by completable
CREATE VIEW IF NOT EXISTS v_criteria_status AS
SELECT
    c.completable_type,
    c.completable_id,
    c.blocks_transition_to,
    COUNT(*) as total_criteria,
    SUM(CASE WHEN c.is_met = 1 THEN 1 ELSE 0 END) as met_criteria,
    SUM(CASE WHEN c.is_met = 0 OR c.is_met IS NULL THEN 1 ELSE 0 END) as unmet_criteria,
    CASE
        WHEN COUNT(*) = 0 THEN 100
        ELSE ROUND(100.0 * SUM(CASE WHEN c.is_met = 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
    END as completion_percent
FROM criteria c
WHERE c.required = 1
GROUP BY c.completable_type, c.completable_id, c.blocks_transition_to;

-- View for blocking criteria (unmet required criteria)
CREATE VIEW IF NOT EXISTS v_blocking_criteria AS
SELECT
    c.*,
    json_extract(c.target_json, '$.completable_id') as target_completable_id,
    json_extract(c.target_json, '$.required_status') as target_required_status
FROM criteria c
WHERE c.required = 1
  AND (c.is_met = 0 OR c.is_met IS NULL);

-- View for CompletableTarget dependencies (who depends on what)
CREATE VIEW IF NOT EXISTS v_completable_dependencies AS
SELECT
    c.completable_type as dependent_type,
    c.completable_id as dependent_id,
    c.description,
    c.blocks_transition_to,
    json_extract(c.target_json, '$.completable_id') as dependency_id,
    json_extract(c.target_json, '$.required_status') as required_status,
    json_extract(c.target_json, '$.current_status') as current_status,
    c.is_met
FROM criteria c
WHERE c.target_type = 'completable';

-- View for reverse dependencies (who depends on this entity)
CREATE VIEW IF NOT EXISTS v_reverse_dependencies AS
SELECT
    json_extract(c.target_json, '$.completable_id') as dependency_id,
    c.completable_type as dependent_type,
    c.completable_id as dependent_id,
    c.description,
    c.blocks_transition_to,
    json_extract(c.target_json, '$.required_status') as required_status,
    c.is_met
FROM criteria c
WHERE c.target_type = 'completable';
"""


def create_criteria_table(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> None:
    """
    Create just the criteria table and related views.

    This adds criteria support to the existing legacy schema without
    requiring a full migration to the unified tickets table.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    conn.executescript(get_criteria_table_ddl())


def has_criteria_table(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> bool:
    """
    Check if the criteria table exists.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

    Returns:
        True if criteria table exists
    """
    if conn is None:
        conn = get_connection(db_path=db_path, base_dir=base_dir)

    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='criteria'"
    ).fetchone()

    return result is not None
