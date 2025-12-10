-- View for reverse dependency lookup ("who depends on ticket X?")
CREATE VIEW v_reverse_dependencies AS
SELECT
    json_extract(c.target_data, '$.completable_id') AS blocked_ticket_id,
    c.ticket_id AS blocking_ticket_id,
    c.blocks_transition_to,
    c.description
FROM criteria c
WHERE c.target_type = 'completable';

-- Index for fast lookups
CREATE INDEX idx_criteria_completable_id ON criteria(
    json_extract(target_data, '$.completable_id')
) WHERE target_type = 'completable';
