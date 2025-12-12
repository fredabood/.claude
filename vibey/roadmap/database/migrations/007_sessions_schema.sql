-- =============================================================================
-- Migration 007: Session Tracking Schema
-- =============================================================================
-- Adds tables for tracking AI-assisted coding sessions, including:
-- - sessions: Main session entity
-- - session_events: Event log for audit trail
-- - session_commits: Git commit associations
-- - session_snapshots: Context snapshots for reconstruction
--
-- Sprint 3.2: Git Versioning for Vibe Coding Sessions
-- =============================================================================

-- =============================================================================
-- TABLE: SESSIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    -- Identity
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
        'active', 'paused', 'completed', 'abandoned'
    )),
    created_at TEXT NOT NULL,
    started_at TEXT,
    paused_at TEXT,
    ended_at TEXT,

    -- Roadmap associations
    roadmap_id TEXT NOT NULL,
    track_id TEXT,
    sprint_id TEXT,

    -- Git integration
    branch TEXT,
    start_commit TEXT,
    end_commit TEXT,

    -- Session content
    goals_json TEXT,           -- JSON array of goals
    summary TEXT,
    token_usage INTEGER,

    -- Statistics (cached)
    events_count INTEGER DEFAULT 0,
    decisions_count INTEGER DEFAULT 0,
    commits_count INTEGER DEFAULT 0,
    files_modified INTEGER DEFAULT 0,
    tasks_worked INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,

    -- Metadata
    metadata_json TEXT,

    -- Foreign keys (soft - sessions may outlive roadmap data)
    -- roadmap_id: References roadmap but not enforced
    -- track_id: References track but not enforced
    -- sprint_id: References sprint but not enforced

    -- Timestamps
    updated_at TEXT NOT NULL
);

-- =============================================================================
-- TABLE: SESSION_EVENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS session_events (
    -- Identity
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Event info
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'session_start', 'session_pause', 'session_resume', 'session_end',
        'goal_set', 'goal_achieved',
        'task_start', 'task_complete', 'task_paused',
        'decision_made', 'question_asked',
        'file_read', 'file_modified', 'file_created', 'file_deleted',
        'commit_made', 'branch_changed',
        'command_run',
        'error_encountered', 'error_resolved',
        'context_loaded', 'context_updated', 'context_snapshot',
        'custom', 'note'
    )),

    -- Event data (JSON)
    data_json TEXT,

    -- Associations
    task_id TEXT,
    commit_sha TEXT,
    file_path TEXT
);

-- =============================================================================
-- TABLE: SESSION_TASKS (Many-to-Many Association)
-- =============================================================================

CREATE TABLE IF NOT EXISTS session_tasks (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    associated_at TEXT NOT NULL,
    PRIMARY KEY (session_id, task_id)
);

-- =============================================================================
-- TABLE: SESSION_COMMITS
-- =============================================================================

CREATE TABLE IF NOT EXISTS session_commits (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    commit_sha TEXT NOT NULL,
    short_sha TEXT,
    committed_at TEXT NOT NULL,
    message TEXT,
    author TEXT,
    files_changed INTEGER DEFAULT 0,
    insertions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    PRIMARY KEY (session_id, commit_sha)
);

-- =============================================================================
-- TABLE: SESSION_SNAPSHOTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS session_snapshots (
    -- Identity
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Snapshot info
    timestamp TEXT NOT NULL,
    snapshot_type TEXT NOT NULL CHECK (snapshot_type IN (
        'session_start', 'checkpoint', 'session_end'
    )),

    -- Git state
    git_branch TEXT,
    git_commit TEXT,
    git_dirty INTEGER DEFAULT 0,
    git_staged_files_json TEXT,
    git_modified_files_json TEXT,

    -- Context state
    context_files_json TEXT,    -- {path: hash} mapping
    config_hash TEXT,

    -- Roadmap state
    active_track_id TEXT,
    active_sprint_id TEXT,
    active_task_ids_json TEXT,

    -- Environment
    environment_json TEXT
);

-- =============================================================================
-- INDEXES: SESSIONS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_roadmap_id ON sessions(roadmap_id);
CREATE INDEX IF NOT EXISTS idx_sessions_track_id ON sessions(track_id);
CREATE INDEX IF NOT EXISTS idx_sessions_sprint_id ON sessions(sprint_id);
CREATE INDEX IF NOT EXISTS idx_sessions_branch ON sessions(branch);

-- =============================================================================
-- INDEXES: SESSION_EVENTS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_session_events_type ON session_events(event_type);
CREATE INDEX IF NOT EXISTS idx_session_events_timestamp ON session_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_session_events_task ON session_events(task_id);

-- =============================================================================
-- INDEXES: SESSION_TASKS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_session_tasks_task ON session_tasks(task_id);

-- =============================================================================
-- INDEXES: SESSION_COMMITS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_session_commits_commit ON session_commits(commit_sha);
CREATE INDEX IF NOT EXISTS idx_session_commits_date ON session_commits(committed_at);

-- =============================================================================
-- INDEXES: SESSION_SNAPSHOTS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_session_snapshots_session ON session_snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_session_snapshots_type ON session_snapshots(snapshot_type);

-- =============================================================================
-- VIEWS: SESSION QUERIES
-- =============================================================================

-- View: Active Sessions
CREATE VIEW IF NOT EXISTS v_active_sessions AS
SELECT
    s.*,
    (SELECT COUNT(*) FROM session_events WHERE session_id = s.id) as total_events,
    (SELECT COUNT(*) FROM session_commits WHERE session_id = s.id) as total_commits,
    (SELECT COUNT(*) FROM session_tasks WHERE session_id = s.id) as total_tasks
FROM sessions s
WHERE s.status = 'active';

-- View: Session Timeline
CREATE VIEW IF NOT EXISTS v_session_timeline AS
SELECT
    e.session_id,
    e.timestamp,
    e.event_type,
    e.data_json,
    e.task_id,
    e.commit_sha,
    e.file_path,
    s.name as session_name,
    s.branch as session_branch
FROM session_events e
JOIN sessions s ON e.session_id = s.id
ORDER BY e.timestamp;

-- View: Session Summary
CREATE VIEW IF NOT EXISTS v_session_summary AS
SELECT
    s.id,
    s.name,
    s.status,
    s.created_at,
    s.ended_at,
    s.duration_seconds,
    s.events_count,
    s.decisions_count,
    s.commits_count,
    s.branch,
    s.track_id,
    s.sprint_id,
    (SELECT GROUP_CONCAT(task_id) FROM session_tasks WHERE session_id = s.id) as task_ids
FROM sessions s
ORDER BY s.created_at DESC;

-- View: Decisions by Session
CREATE VIEW IF NOT EXISTS v_session_decisions AS
SELECT
    e.id,
    e.session_id,
    e.timestamp,
    json_extract(e.data_json, '$.description') as description,
    json_extract(e.data_json, '$.category') as category,
    json_extract(e.data_json, '$.confidence') as confidence,
    json_extract(e.data_json, '$.rationale') as rationale,
    e.task_id,
    e.commit_sha,
    s.name as session_name
FROM session_events e
JOIN sessions s ON e.session_id = s.id
WHERE e.event_type = 'decision_made';

-- =============================================================================
-- UPDATE DATABASE VERSION
-- =============================================================================

UPDATE database_state SET
    schema_version = '2.1.0'
WHERE id = 1;
