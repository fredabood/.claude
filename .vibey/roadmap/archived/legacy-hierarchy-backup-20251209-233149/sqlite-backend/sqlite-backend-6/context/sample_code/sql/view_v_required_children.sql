-- Add new fields to tickets table
ALTER TABLE tickets ADD COLUMN priority TEXT;
ALTER TABLE tickets ADD COLUMN deferred INTEGER DEFAULT 0;
ALTER TABLE tickets ADD COLUMN estimated_duration_local TEXT;
ALTER TABLE tickets ADD COLUMN actual_duration_local TEXT;

-- Index for priority-based queries
CREATE INDEX idx_tickets_priority ON tickets(priority) WHERE priority IS NOT NULL;

-- View for required vs deferred children
CREATE VIEW v_required_children AS
SELECT
    parent.id AS parent_id,
    child.id AS child_id,
    child.deferred
FROM tickets parent
JOIN criteria c ON c.ticket_id = parent.id
JOIN tickets child ON json_extract(c.target_data, '$.completable_id') = child.id
WHERE c.target_type = 'completable';
