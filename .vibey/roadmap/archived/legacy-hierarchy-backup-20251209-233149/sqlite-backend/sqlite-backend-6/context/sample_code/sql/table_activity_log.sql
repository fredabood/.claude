-- Add to existing schema from Part 7

-- Unified activity log table (replaces separate audit_trail)
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,

    -- Entity tracking
    entity_type TEXT,
    entity_id TEXT,

    -- Field change tracking
    field TEXT,
    old_value TEXT,
    new_value TEXT,

    -- Attribution
    changed_by TEXT,
    commit_sha TEXT,

    -- Additional context (JSON)
    context TEXT
);

CREATE INDEX idx_activity_log_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_log_timestamp ON activity_log(timestamp DESC);
CREATE INDEX idx_activity_log_type ON activity_log(type);

-- Reverse dependency view
CREATE VIEW v_reverse_dependencies AS
SELECT
    json_extract(c.target_data, '$.completable_id') AS blocked_ticket_id,
    c.ticket_id AS blocking_ticket_id,
    c.blocks_transition_to,
    c.description
FROM criteria c
WHERE c.target_type = 'completable';

-- Index for reverse dependency lookups
CREATE INDEX idx_criteria_completable_target ON criteria(
    json_extract(target_data, '$.completable_id')
) WHERE target_type = 'completable';
