# Artifact Tracking Improvements Design

**Generated:** 2025-12-12
**Sprint:** Phase 1.6 - Database Artifact Audit
**Task:** Design artifact tracking improvements

---

## Executive Summary

Based on the gap analysis from Tasks 1-8, this document designs schema improvements to enable complete artifact tracking in the vibey roadmap system. The design prioritizes:

1. **Critical:** Link artifacts to tasks/sprints/tracks
2. **High:** Enable test-to-code coverage tracking
3. **Medium:** Normalize artifact dependencies
4. **Low:** Add type-specific metadata extensions

**Estimated Implementation Effort:** 8-12 hours
**Breaking Changes:** None (additive only)

---

## Current State

### Existing Infrastructure

| Component | Status | Issue |
|-----------|--------|-------|
| `artifacts` table | Exists | Empty (0 rows) |
| `commits` table | Exists | Empty (0 rows) |
| `deliverables` table | Exists | Empty (0 rows) |
| `entity_commits` | Exists | Empty, unused |
| `entity_deliverables` | Exists | Empty, unused |
| `entity_artifacts` | **Missing** | Critical gap |
| Artifact views | 4 exist | No data to query |

### Key Gaps Identified

1. **No artifact-to-entity linking** - Cannot track which tasks produce artifacts
2. **No test-to-code relationship** - Cannot track test coverage at file level
3. **JSON-based dependencies** - Hard to query, no FK integrity
4. **Empty tables** - All artifact data structures unpopulated
5. **Missing metadata** - Quality scores, line counts, etc. not tracked

---

## Design: New Tables

### 1. entity_artifacts (Critical Priority)

Links artifacts to tracks, sprints, and tasks via polymorphic relationship.

```sql
CREATE TABLE entity_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Polymorphic owner
    owner_type TEXT NOT NULL CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT NOT NULL,

    -- Artifact reference
    artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Relationship semantics
    relationship_type TEXT NOT NULL DEFAULT 'produces'
        CHECK (relationship_type IN (
            'produces',    -- Entity created this artifact
            'consumes',    -- Entity uses this artifact as input
            'modifies',    -- Entity modified existing artifact
            'references'   -- Entity references but doesn't change
        )),

    -- Metadata
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    added_by TEXT,  -- 'user', 'agent:claude', 'system:import'
    notes TEXT,

    UNIQUE(owner_type, owner_id, artifact_id, relationship_type)
);

CREATE INDEX idx_entity_artifacts_owner ON entity_artifacts(owner_type, owner_id);
CREATE INDEX idx_entity_artifacts_artifact ON entity_artifacts(artifact_id);
CREATE INDEX idx_entity_artifacts_type ON entity_artifacts(relationship_type);
```

**Usage Examples:**
```sql
-- Find all artifacts produced by a task
SELECT a.* FROM artifacts a
JOIN entity_artifacts ea ON ea.artifact_id = a.id
WHERE ea.owner_type = 'task' AND ea.owner_id = '01KC8DT64C16YX90E1YCC8TXZ9'
AND ea.relationship_type = 'produces';

-- Find all tasks that produced code artifacts
SELECT t.* FROM tasks t
JOIN entity_artifacts ea ON ea.owner_type = 'task' AND ea.owner_id = t.id
JOIN artifacts a ON ea.artifact_id = a.id
WHERE a.artifact_type = 'code' AND ea.relationship_type = 'produces';
```

### 2. artifact_tests_code (High Priority)

Links test artifacts to the code artifacts they test.

```sql
CREATE TABLE artifact_tests_code (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Test artifact
    test_artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Code artifact being tested
    code_artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Relationship details
    coverage_type TEXT DEFAULT 'unit' CHECK (coverage_type IN (
        'unit',         -- Unit tests
        'integration',  -- Integration tests
        'e2e',          -- End-to-end tests
        'performance'   -- Performance tests
    )),

    -- Metadata
    discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    discovery_method TEXT,  -- 'filename_match', 'import_analysis', 'manual'

    UNIQUE(test_artifact_id, code_artifact_id)
);

CREATE INDEX idx_tests_code_test ON artifact_tests_code(test_artifact_id);
CREATE INDEX idx_tests_code_code ON artifact_tests_code(code_artifact_id);
```

**Usage Examples:**
```sql
-- Find untested code artifacts
SELECT a.* FROM artifacts a
WHERE a.artifact_type = 'code'
AND NOT EXISTS (
    SELECT 1 FROM artifact_tests_code tc
    WHERE tc.code_artifact_id = a.id
);

-- Find all tests for a code file
SELECT test.* FROM artifacts test
JOIN artifact_tests_code tc ON tc.test_artifact_id = test.id
WHERE tc.code_artifact_id = 'artifact-id';
```

### 3. artifact_dependencies (Medium Priority)

Normalized replacement for `depends_on_artifact_ids` JSON array.

```sql
CREATE TABLE artifact_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Dependent artifact (needs the other)
    dependent_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Dependency artifact (needed by dependent)
    dependency_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,

    -- Dependency type
    dependency_type TEXT NOT NULL DEFAULT 'imports' CHECK (dependency_type IN (
        'imports',      -- Python import
        'includes',     -- Config include
        'extends',      -- Inheritance/extension
        'references',   -- Documentation reference
        'requires'      -- General requirement
    )),

    -- Source tracking
    discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    discovery_method TEXT,  -- 'ast_analysis', 'grep', 'manual'

    UNIQUE(dependent_id, dependency_id, dependency_type)
);

CREATE INDEX idx_deps_dependent ON artifact_dependencies(dependent_id);
CREATE INDEX idx_deps_dependency ON artifact_dependencies(dependency_id);
```

**Migration from JSON:**
```sql
-- Migration script (run once after table creation)
INSERT INTO artifact_dependencies (dependent_id, dependency_id, dependency_type, discovery_method)
SELECT
    a.id,
    json_each.value,
    'requires',
    'json_migration'
FROM artifacts a, json_each(a.depends_on_artifact_ids)
WHERE a.depends_on_artifact_ids IS NOT NULL
AND a.depends_on_artifact_ids != '[]';
```

---

## Design: Column Additions

### artifacts Table Extensions

```sql
-- Quality metrics (from audits)
ALTER TABLE artifacts ADD COLUMN quality_score INTEGER CHECK (quality_score BETWEEN 0 AND 100);
ALTER TABLE artifacts ADD COLUMN quality_grade TEXT CHECK (quality_grade IN ('A', 'B', 'C', 'D', 'F'));

-- Audit linkage
ALTER TABLE artifacts ADD COLUMN audited_by_task_id TEXT;
ALTER TABLE artifacts ADD COLUMN audited_at TEXT;
```

### Provenance JSON Schema Extension

Document the expected structure of the `provenance` JSON field:

```json
{
  "provenance_type": "manual|generated|ai_created|migrated",
  "created_by": {
    "type": "user|agent|system",
    "id": "identifier",
    "name": "human-readable name"
  },
  "task_context": {
    "task_id": "ULID",
    "sprint_id": "ULID",
    "track_id": "ULID"
  },
  "git_context": {
    "commit_sha": "abc123",
    "branch": "main",
    "committed_at": "ISO timestamp"
  },
  "generation_context": {
    "template_used": "path/to/template",
    "source_artifacts": ["artifact-id-1", "artifact-id-2"],
    "script": "script that generated"
  }
}
```

---

## Design: New Views

### v_task_artifacts
```sql
CREATE VIEW v_task_artifacts AS
SELECT
    t.id as task_id,
    t.title as task_title,
    t.status as task_status,
    t.sprint_id,
    t.track_id,
    ea.relationship_type,
    a.id as artifact_id,
    a.name as artifact_name,
    a.artifact_type,
    a.artifact_subtype,
    a.paths,
    a.quality_score,
    a.quality_grade,
    a.is_stale,
    a.file_exists
FROM tasks t
JOIN entity_artifacts ea ON ea.owner_type = 'task' AND ea.owner_id = t.id
JOIN artifacts a ON ea.artifact_id = a.id;
```

### v_sprint_artifact_summary
```sql
CREATE VIEW v_sprint_artifact_summary AS
SELECT
    s.id as sprint_id,
    s.name as sprint_name,
    s.status as sprint_status,
    COUNT(DISTINCT ea.artifact_id) as total_artifacts,
    COUNT(DISTINCT CASE WHEN a.artifact_type = 'code' THEN a.id END) as code_artifacts,
    COUNT(DISTINCT CASE WHEN a.artifact_type = 'test' THEN a.id END) as test_artifacts,
    COUNT(DISTINCT CASE WHEN a.artifact_type = 'documentation' THEN a.id END) as doc_artifacts,
    AVG(a.quality_score) as avg_quality_score,
    SUM(CASE WHEN a.is_stale = 1 THEN 1 ELSE 0 END) as stale_count
FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
LEFT JOIN entity_artifacts ea ON ea.owner_type = 'task' AND ea.owner_id = t.id
LEFT JOIN artifacts a ON ea.artifact_id = a.id
GROUP BY s.id, s.name, s.status;
```

### v_untested_code
```sql
CREATE VIEW v_untested_code AS
SELECT
    a.*,
    'untested' as coverage_status
FROM artifacts a
WHERE a.artifact_type = 'code'
AND NOT EXISTS (
    SELECT 1 FROM artifact_tests_code tc
    WHERE tc.code_artifact_id = a.id
);
```

### v_undocumented_code
```sql
CREATE VIEW v_undocumented_code AS
SELECT
    a.*,
    'undocumented' as documentation_status
FROM artifacts a
WHERE a.artifact_type = 'code'
AND NOT EXISTS (
    SELECT 1 FROM artifacts doc
    WHERE doc.documents_artifact_id = a.id
    AND doc.artifact_type = 'documentation'
);
```

### v_artifact_health
```sql
CREATE VIEW v_artifact_health AS
SELECT
    a.id,
    a.name,
    a.artifact_type,
    a.quality_score,
    a.quality_grade,
    a.is_stale,
    a.file_exists,
    CASE
        WHEN a.file_exists = 0 THEN 'missing'
        WHEN a.is_stale = 1 THEN 'stale'
        WHEN a.quality_grade IN ('D', 'F') THEN 'poor_quality'
        WHEN a.artifact_type = 'code' AND NOT EXISTS (
            SELECT 1 FROM artifact_tests_code tc WHERE tc.code_artifact_id = a.id
        ) THEN 'untested'
        ELSE 'healthy'
    END as health_status
FROM artifacts a;
```

---

## Migration Strategy

### Phase 1: Schema Additions (Non-Breaking)

1. Create `entity_artifacts` table
2. Create `artifact_tests_code` table
3. Create `artifact_dependencies` table
4. Add quality columns to `artifacts`
5. Create new views

**Script:**
```sql
-- migrations/001_artifact_tracking.sql

-- 1. entity_artifacts
CREATE TABLE IF NOT EXISTS entity_artifacts (...);

-- 2. artifact_tests_code
CREATE TABLE IF NOT EXISTS artifact_tests_code (...);

-- 3. artifact_dependencies
CREATE TABLE IF NOT EXISTS artifact_dependencies (...);

-- 4. Quality columns (SQLite doesn't support ADD COLUMN IF NOT EXISTS)
-- Check if column exists first in application code
ALTER TABLE artifacts ADD COLUMN quality_score INTEGER;
ALTER TABLE artifacts ADD COLUMN quality_grade TEXT;
ALTER TABLE artifacts ADD COLUMN audited_by_task_id TEXT;
ALTER TABLE artifacts ADD COLUMN audited_at TEXT;

-- 5. Views (use CREATE OR REPLACE pattern)
DROP VIEW IF EXISTS v_task_artifacts;
CREATE VIEW v_task_artifacts AS ...;
```

### Phase 2: Data Population

1. Import file inventory from Sprint 1.1 into `artifacts` table
2. Link artifacts to tasks via `entity_artifacts`
3. Populate `artifact_tests_code` via filename matching
4. Migrate JSON dependencies to `artifact_dependencies`

**Import Strategy:**
```python
def import_artifacts_from_inventory(inventory_path: str, db_path: str):
    """Import file inventory into artifacts table."""
    with open(inventory_path) as f:
        inventory = yaml.safe_load(f)

    conn = sqlite3.connect(db_path)
    for file_info in inventory['files']:
        # Map file type to artifact type
        artifact_type = map_file_type(file_info['type'])

        # Generate ULID
        artifact_id = ulid.new().str

        conn.execute("""
            INSERT INTO artifacts (id, name, paths, artifact_type, created_at, updated_at, provenance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            artifact_id,
            file_info['path'].split('/')[-1],
            json.dumps([file_info['path']]),
            artifact_type,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            json.dumps({'provenance_type': 'migrated', 'source': 'phase-1-1-inventory'})
        ))
    conn.commit()
```

### Phase 3: Cleanup (Optional)

Once data is fully migrated to normalized tables:

1. Deprecate `depends_on_artifact_ids` JSON column
2. Migrate any remaining JSON data
3. Consider removing JSON columns in future version

---

## Implementation Checklist

### Critical (Must Have)

- [ ] Create `entity_artifacts` table
- [ ] Create `v_task_artifacts` view
- [ ] Import Sprint 1.1 file inventory to `artifacts`
- [ ] Link context files to tasks via `entity_artifacts`

### High Priority

- [ ] Create `artifact_tests_code` table
- [ ] Create `v_untested_code` view
- [ ] Auto-discover test-to-code relationships
- [ ] Add quality columns to `artifacts`

### Medium Priority

- [ ] Create `artifact_dependencies` table
- [ ] Migrate JSON dependencies
- [ ] Create `v_artifact_health` view
- [ ] Create `v_sprint_artifact_summary` view

### Nice to Have

- [ ] Create `v_undocumented_code` view
- [ ] Add artifact versioning
- [ ] Create import dependency extraction script

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration breaks existing code | Low | High | Additive changes only, no deletions |
| Import script creates duplicates | Medium | Medium | Use UNIQUE constraints, check existence |
| Performance with large artifact counts | Low | Medium | Proper indexes defined |
| JSON column deprecation breaks queries | Low | High | Keep JSON columns, add normalized in parallel |

---

## Success Criteria

After implementation:

1. **Query "What artifacts did task X produce?"** - Works via v_task_artifacts
2. **Query "What code has no tests?"** - Works via v_untested_code
3. **Query "What's the overall artifact health?"** - Works via v_artifact_health
4. **Import file inventory** - All 856 files from Sprint 1.1 as artifacts
5. **Link to roadmap work** - Context files linked to producing tasks
