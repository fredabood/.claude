"""
SQLite schema definitions for roadmap database.

This module contains the DDL for creating the database schema.
Schema is populated in task-002.

Tables (26 total):
- Core Entities (4): roadmaps, tracks, sprints, tasks
- Relationships (4): external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on
- Quality & Gates (2): quality_gates, development_gates
- Supporting Data (7): deliverables, entity_deliverables, commits, entity_commits,
                       assigned_agents, standards, strategic_value
- Roadmap-Level (2): version_history, activity_log
- Summaries (3): track_summaries, sprint_summaries, task_summaries
- Sync & Validation (3): yaml_checksums, database_state, sync_conflicts
- Audit Trail (1): audit_trail
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

    Tables (26 total):
    - Core Entities (4): roadmaps, tracks, sprints, tasks
    - Relationships (4): external_dependencies, entity_blocks, entity_blocked_by, entity_depends_on
    - Quality & Gates (2): quality_gates, development_gates
    - Supporting Data (7): deliverables, entity_deliverables, commits, entity_commits,
                          assigned_agents, standards, strategic_value
    - Roadmap-Level (2): version_history, activity_log
    - Summaries (3): track_summaries, sprint_summaries, task_summaries
    - Sync & Validation (3): yaml_checksums, database_state, sync_conflicts
    - Audit Trail (1): audit_trail
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

    -- Authored data (JSON arrays) - these are NOT aggregated from children
    dependencies_json TEXT,  -- JSON array of external dependency descriptions
    standards_json TEXT,  -- JSON array of Standard objects (can inherit down)
    development_gates_json TEXT,  -- JSON array of DevelopmentGate objects

    -- Note: commits, deliverables, assigned_agents, estimated_duration aggregate up from tasks via views

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
"""


def create_schema(
    conn: Optional[sqlite3.Connection] = None,
    db_path: Optional[Path] = None,
    base_dir: Optional[Path] = None,
) -> None:
    """
    Create the database schema.

    Args:
        conn: Existing connection to use.
        db_path: Direct path to database file.
        base_dir: Base directory containing .vibey folder.

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
