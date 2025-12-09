-- Add ordering fields to tickets table
ALTER TABLE tickets ADD COLUMN parent_id TEXT REFERENCES tickets(id);
ALTER TABLE tickets ADD COLUMN sequence INTEGER DEFAULT 0;
ALTER TABLE tickets ADD COLUMN slug TEXT;

-- Index for sibling queries
CREATE INDEX idx_tickets_parent_sequence ON tickets(parent_id, sequence);

-- View for sibling navigation
CREATE VIEW v_ticket_siblings AS
SELECT
    t1.id,
    t1.parent_id,
    t1.sequence,
    LAG(t1.id) OVER (PARTITION BY t1.parent_id ORDER BY t1.sequence) as prev_sibling_id,
    LEAD(t1.id) OVER (PARTITION BY t1.parent_id ORDER BY t1.sequence) as next_sibling_id
FROM tickets t1;
