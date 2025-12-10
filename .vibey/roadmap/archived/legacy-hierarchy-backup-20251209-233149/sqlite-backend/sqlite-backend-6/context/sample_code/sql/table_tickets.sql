-- Single-table inheritance for all ticket types
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    ticket_type TEXT NOT NULL CHECK (ticket_type IN (
        'roadmap', 'track', 'sprint', 'task'
    )),

    -- Common fields
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'not_started',

    -- Hierarchy
    parent_ref TEXT,

    -- Lifecycle timestamps
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL,

    -- Type-specific fields (JSON)
    semantic_fields TEXT,  -- JSON object for domain-specific data

    -- Work tracking (JSON arrays)
    commits_local TEXT,
    assigned_agents_local TEXT,
    requirements_local TEXT,

    FOREIGN KEY (parent_ref) REFERENCES tickets(id)
);

-- Unified criteria table with polymorphic target
CREATE TABLE criteria (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    description TEXT NOT NULL,

    -- THE key field for unified blocking
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed',

    -- Optionality
    required INTEGER NOT NULL DEFAULT 1,

    -- Target type discriminator
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable', 'file_exists', 'test_passes',
        'threshold', 'manual', 'external'
    )),

    -- Target data (JSON for type-specific config and state)
    target_data TEXT NOT NULL,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

-- Index for finding children
CREATE INDEX idx_criteria_children ON criteria(target_type, ticket_id)
WHERE target_type = 'completable';

-- Index for blocking checks
CREATE INDEX idx_criteria_blocking ON criteria(ticket_id, blocks_transition_to);

-- View for progress calculation
CREATE VIEW v_ticket_progress AS
SELECT
    t.id AS ticket_id,
    c.blocks_transition_to,
    COUNT(*) AS total_criteria,
    SUM(CASE WHEN c.is_met THEN 1 ELSE 0 END) AS met_criteria,
    ROUND(100.0 * SUM(CASE WHEN c.is_met THEN 1 ELSE 0 END) / COUNT(*), 1) AS progress
FROM tickets t
LEFT JOIN criteria c ON c.ticket_id = t.id
GROUP BY t.id, c.blocks_transition_to;
