-- ═══════════════════════════════════════════════════════════════════════════
-- ARTIFACT TABLE (independent of tickets)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    -- File location
    paths TEXT NOT NULL,  -- JSON array of file paths
    content_hash TEXT,    -- SHA256 of concatenated contents
    last_verified TEXT,   -- ISO timestamp

    -- Classification
    artifact_type TEXT NOT NULL,
    artifact_subtype TEXT,

    -- Provenance (JSON object)
    provenance TEXT NOT NULL,

    -- Relationships
    documents_artifact_id TEXT,  -- For documentation: what does this document?
    depends_on_artifact_ids TEXT,  -- JSON array

    -- State
    exists INTEGER NOT NULL DEFAULT 1,
    is_stale INTEGER NOT NULL DEFAULT 0,

    -- For staleness tracking (docs only)
    documented_source_hash TEXT,  -- Hash of source when doc was updated

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (documents_artifact_id) REFERENCES artifacts(id)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX idx_artifacts_subtype ON artifacts(artifact_subtype);
CREATE INDEX idx_artifacts_documents ON artifacts(documents_artifact_id);
CREATE INDEX idx_artifacts_exists ON artifacts(exists);
CREATE INDEX idx_artifacts_stale ON artifacts(is_stale) WHERE is_stale = 1;

-- Provenance-based indexes
CREATE INDEX idx_artifacts_provenance_type ON artifacts(
    json_extract(provenance, '$.provenance_type')
);
CREATE INDEX idx_artifacts_created_by_ticket ON artifacts(
    json_extract(provenance, '$.created_by_ticket_id')
);

-- ═══════════════════════════════════════════════════════════════════════════
-- UPDATED CRITERIA TABLE (add artifact_id column)
-- ═══════════════════════════════════════════════════════════════════════════

-- Add artifact reference to criteria (for ArtifactTarget)
ALTER TABLE criteria ADD COLUMN artifact_id TEXT REFERENCES artifacts(id);
ALTER TABLE criteria ADD COLUMN artifact_verification TEXT;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEWS
-- ═══════════════════════════════════════════════════════════════════════════

-- Orphan artifacts (not referenced by any criterion)
CREATE VIEW v_orphan_artifacts AS
SELECT a.*
FROM artifacts a
LEFT JOIN criteria c ON c.artifact_id = a.id
WHERE c.id IS NULL
  AND a.exists = 1;

-- Documentation graph (what documents what)
CREATE VIEW v_documentation_graph AS
SELECT
    doc.id AS documentation_id,
    doc.name AS documentation_name,
    doc.paths AS documentation_paths,
    doc.is_stale,
    doc.documented_source_hash,
    src.id AS source_id,
    src.name AS source_name,
    src.paths AS source_paths,
    src.content_hash AS source_current_hash,
    CASE
        WHEN src.content_hash != doc.documented_source_hash THEN 1
        ELSE 0
    END AS needs_update
FROM artifacts doc
JOIN artifacts src ON doc.documents_artifact_id = src.id
WHERE doc.artifact_type IN ('documentation', 'context');

-- Stale documentation needing update
CREATE VIEW v_stale_documentation AS
SELECT *
FROM v_documentation_graph
WHERE needs_update = 1 OR is_stale = 1;

-- Artifact provenance summary
CREATE VIEW v_artifact_provenance AS
SELECT
    json_extract(provenance, '$.provenance_type') AS provenance_type,
    artifact_type,
    COUNT(*) AS count
FROM artifacts
WHERE exists = 1
GROUP BY json_extract(provenance, '$.provenance_type'), artifact_type;

-- Framework components
CREATE VIEW v_framework_components AS
SELECT *
FROM artifacts
WHERE artifact_type IN ('agent', 'workflow', 'template')
  AND exists = 1;

-- Artifacts by ticket (including all descendants)
CREATE VIEW v_ticket_artifacts AS
SELECT
    t.id AS ticket_id,
    t.ticket_type,
    c.artifact_id,
    a.name AS artifact_name,
    a.artifact_type,
    a.is_stale,
    c.blocks_transition_to
FROM tickets t
JOIN criteria c ON c.ticket_id = t.id
JOIN artifacts a ON a.id = c.artifact_id
WHERE c.artifact_id IS NOT NULL;
