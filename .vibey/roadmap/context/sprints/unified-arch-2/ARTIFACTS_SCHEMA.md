# Artifacts Schema Design Decision

**Date:** 2025-12-09
**Sprint:** unified-arch-2 (Database Schema Migration)
**Task:** unified-arch-2-task-003
**Status:** Final Design

---

## Design Decision: No Separate Artifacts Table

**Decision:** Artifacts are stored in the **unified completables table**, not a separate artifacts table.

**Rationale:** Artifacts are a subtype of Completable (alongside Tickets), using single-table inheritance with the discriminator `completable_type = 'artifact'`.

---

## Why Unified Instead of Separate?

### Original Proposal (Separate Tables)
```sql
-- Tickets table (roadmaps, tracks, sprints, tasks)
CREATE TABLE tickets (...);

-- Separate artifacts table
CREATE TABLE artifacts (...);

-- Problem: Two identity spaces, complex polymorphic references
```

**Issues with Separate Tables:**
1. **Polymorphic References:** Criteria need to reference EITHER tickets OR artifacts
   - Requires union queries or multiple foreign keys
   - Complex to maintain referential integrity
2. **Duplicate Fields:** Both need `id`, `name`, `description`, `status`, `criteria`
3. **Schema Fragmentation:** Changes to completable semantics require updating 2 tables

### Chosen Design (Unified Table)
```sql
-- Single completables table for ALL completables
CREATE TABLE completables (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    completable_type TEXT NOT NULL CHECK (completable_type IN ('ticket', 'artifact')),

    -- Ticket fields (NULL for artifacts)
    ticket_type TEXT,
    assigned_agents_json TEXT,
    commits_json TEXT,
    ...

    -- Artifact fields (NULL for tickets)
    paths_json TEXT,
    content_hash TEXT,
    artifact_type TEXT,
    provenance_json TEXT,
    documents_artifact_id TEXT REFERENCES completables(id),
    depends_on_artifact_ids_json TEXT,
    ...
);
```

**Benefits:**
1. ✅ **Single Identity Space:** All ULIDs in one table, simple FKs
2. ✅ **Polymorphic References:** Criteria.completable_id can reference ANY completable
3. ✅ **Shared Semantics:** Status, criteria, lifecycle - all unified
4. ✅ **Simpler Queries:** `WHERE completable_type = 'artifact'` vs JOINs

---

## Artifact Storage in Completables Table

### Artifact-Specific Columns

From the **completables table schema** (Task 001):

```sql
-- ARTIFACT-SPECIFIC FIELDS (NULL for tickets)

-- File References
paths_json TEXT,                       -- JSON array of file paths
content_hash TEXT,                     -- Git blob hash or similar

-- Artifact Classification
artifact_type TEXT CHECK (artifact_type IN ('code', 'documentation', 'test', 'config', 'data')),
artifact_subtype TEXT,                 -- e.g., "module", "guide", "integration_test"

-- Provenance
provenance_json TEXT,                  -- JSON: created_by, created_at, source_tool, etc.

-- Documentation Relationships
documents_artifact_id TEXT REFERENCES completables(id),  -- What artifact does this document?
depends_on_artifact_ids_json TEXT,     -- JSON array of artifact IDs this depends on
```

### Example Artifact Row

```json
{
  "id": "01HXYZ...",
  "name": "User Authentication Module",
  "description": "Core authentication logic for user login/logout",
  "completable_type": "artifact",
  "ticket_type": null,  // Artifacts don't have ticket_type
  "parent_id": null,    // Artifacts don't have parents
  "status": "completed",
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-09T16:00:00Z",

  // Artifact fields
  "paths_json": "[\"src/auth/module.py\", \"src/auth/__init__.py\"]",
  "content_hash": "sha256:abc123...",
  "artifact_type": "code",
  "artifact_subtype": "module",
  "provenance_json": "{\"type\": \"TICKET_CREATED\", \"ticket_id\": \"task-456\", \"created_by\": \"claude\"}",
  "documents_artifact_id": null,
  "depends_on_artifact_ids_json": "[\"01ABC...\", \"01DEF...\"]",

  // Ticket fields (all NULL)
  "assigned_agents_json": null,
  "commits_json": null,
  "priority": null,
  "estimated_duration": null,
  "complexity": null
}
```

---

## Artifact Provenance Schema

Stored in `provenance_json` as JSON object:

### ProvenanceType: TICKET_CREATED
```json
{
  "type": "TICKET_CREATED",
  "ticket_id": "01TASK123",
  "created_by": "claude-opus-4-5",
  "created_at": "2025-12-09T16:00:00Z",
  "commit_sha": "abc123def456"
}
```

### ProvenanceType: PRE_EXISTING
```json
{
  "type": "PRE_EXISTING",
  "discovered_at": "2025-12-01T00:00:00Z",
  "initial_commit": "old123old456",
  "note": "Existed before roadmap tracking began"
}
```

### ProvenanceType: GENERATED
```json
{
  "type": "GENERATED",
  "source_tool": "sphinx",
  "source_files": ["src/module.py", "src/api.py"],
  "generation_command": "sphinx-build -b html docs/ dist/",
  "generated_at": "2025-12-09T15:00:00Z"
}
```

### ProvenanceType: EXTERNAL
```json
{
  "type": "EXTERNAL",
  "source": "npm",
  "package_name": "lodash",
  "version": "4.17.21",
  "installed_at": "2025-11-15T12:00:00Z"
}
```

### ProvenanceType: FRAMEWORK
```json
{
  "type": "FRAMEWORK",
  "component_type": "agent",
  "framework_version": "1.3.0",
  "note": "Vibey framework component"
}
```

---

## Artifact Types and Subtypes

### CODE Artifacts
```json
{
  "artifact_type": "code",
  "artifact_subtype": "module"   // or: "class", "function", "test"
}
```

**Examples:**
- `src/auth/module.py` - module
- `src/models/user.py` - class
- `tests/test_auth.py` - test

### DOCUMENTATION Artifacts
```json
{
  "artifact_type": "documentation",
  "artifact_subtype": "guide"   // or: "readme", "api_doc", "changelog"
}
```

**Examples:**
- `README.md` - readme
- `docs/api/reference.md` - api_doc
- `docs/guides/quickstart.md` - guide

### CONFIG Artifacts
```json
{
  "artifact_type": "config",
  "artifact_subtype": "yaml"   // or: "json", "toml", "env"
}
```

**Examples:**
- `.vibey/config/agents.yaml` - yaml
- `package.json` - json

### TEST Artifacts
```json
{
  "artifact_type": "test",
  "artifact_subtype": "integration_test"   // or: "unit_test", "e2e_test"
}
```

### DATA Artifacts
```json
{
  "artifact_type": "data",
  "artifact_subtype": "migration"   // or: "schema", "fixture"
}
```

---

## Documentation Relationships

### documents_artifact_id Field

Links documentation artifacts to what they document:

```sql
-- Guide that documents the auth module
INSERT INTO completables (
    id, name, completable_type, artifact_type, artifact_subtype,
    paths_json, documents_artifact_id
) VALUES (
    '01GUIDE123',
    'Authentication Guide',
    'artifact',
    'documentation',
    'guide',
    '["docs/guides/auth.md"]',
    '01MODULE456'  -- Points to auth module artifact
);
```

**Enables Queries:**
- "What documents this module?" → Find artifacts where `documents_artifact_id = module_id`
- "What does this guide document?" → Join to artifact via `documents_artifact_id`
- "Which modules lack documentation?" → Artifacts with no `documents_artifact_id` references

---

## Artifact Dependencies

### depends_on_artifact_ids_json Field

Tracks artifact-to-artifact dependencies:

```json
{
  "id": "01CONFIG123",
  "name": "Database Config",
  "artifact_type": "config",
  "depends_on_artifact_ids_json": "[\"01SCHEMA456\", \"01MIGRATION789\"]"
}
```

**Use Cases:**
- Config depends on schema definitions
- Tests depend on fixtures
- Generated docs depend on source code
- Compiled assets depend on source files

**Enables Queries:**
- "What depends on this artifact?" → Search `depends_on_artifact_ids_json` LIKE '%artifact_id%'
- "Dependency tree for artifact" → Recursive query following dependencies
- "Impact analysis" → Find all dependents when artifact changes

---

## Views for Artifact Queries

### v_artifacts
Type-specific view (already defined in Task 001):

```sql
CREATE VIEW v_artifacts AS
SELECT
    id, name, description, parent_id, sequence,
    status, created_at, updated_at,
    paths_json, content_hash, artifact_type, artifact_subtype,
    provenance_json, documents_artifact_id, depends_on_artifact_ids_json,
    metadata_json
FROM completables
WHERE completable_type = 'artifact';
```

### v_orphan_artifacts
Artifacts not referenced by any criterion:

```sql
CREATE VIEW v_orphan_artifacts AS
SELECT a.*
FROM completables a
WHERE a.completable_type = 'artifact'
  AND NOT EXISTS (
      SELECT 1 FROM criteria c
      WHERE c.target_type = 'completable'
        AND json_extract(c.target_json, '$.completable_id') = a.id
  );
```

### v_stale_documentation
Documentation that may need updates:

```sql
CREATE VIEW v_stale_documentation AS
SELECT
    doc.id as doc_id,
    doc.name as doc_name,
    doc.updated_at as doc_updated_at,
    target.id as target_id,
    target.name as target_name,
    target.updated_at as target_updated_at
FROM completables doc
JOIN completables target ON doc.documents_artifact_id = target.id
WHERE doc.completable_type = 'artifact'
  AND doc.artifact_type = 'documentation'
  AND datetime(doc.updated_at) < datetime(target.updated_at);
```

### v_artifact_dependency_graph
Graph edges for dependencies:

```sql
CREATE VIEW v_artifact_dependency_graph AS
SELECT
    a.id as from_artifact_id,
    a.name as from_artifact_name,
    dep_id.value as to_artifact_id,
    t.name as to_artifact_name,
    a.artifact_type as from_type,
    t.artifact_type as to_type
FROM completables a
JOIN json_each(a.depends_on_artifact_ids_json) dep_id
JOIN completables t ON dep_id.value = t.id
WHERE a.completable_type = 'artifact'
  AND a.depends_on_artifact_ids_json IS NOT NULL;
```

---

## Implicit FileExistsTarget Criterion

All artifacts have an **implicit criterion** that the file(s) must exist:

```python
# When artifact is created
artifact = Artifact(
    id="01ABC...",
    paths=["src/module.py"],
    ...
)

# Implicitly creates criterion:
criterion = Criterion(
    id="fileexists-01ABC...",
    completable_id="01ABC...",
    description="File must exist: src/module.py",
    blocks_transition_to="completed",
    required=True,
    target_type="file_exists",
    target_json=json.dumps({
        "type": "file_exists",
        "paths": ["src/module.py"],
        "all_required": True
    })
)
```

**Result:** Artifact status automatically reflects file existence:
- File exists → criterion met → artifact can be COMPLETED
- File missing → criterion not met → artifact cannot reach COMPLETED

---

## Migration Strategy

### Phase 1: Artifacts Already in Completables
No migration needed! Artifacts go directly into the completables table from day one.

### Phase 2: Migrate Existing Artifact References (if any)
If the old database had artifact references:

```sql
-- Migrate old artifact references to completables
INSERT INTO completables (
    id, name, completable_type, artifact_type, artifact_subtype,
    paths_json, content_hash, provenance_json, status, created_at, updated_at
)
SELECT
    id, name, 'artifact', artifact_type, artifact_subtype,
    json_array(file_path), content_hash,
    json_object('type', 'PRE_EXISTING', 'discovered_at', datetime('now')),
    'completed', created_at, updated_at
FROM old_artifacts_table;
```

### Phase 3: Create Views
```sql
CREATE VIEW v_artifacts AS ...;
CREATE VIEW v_orphan_artifacts AS ...;
CREATE VIEW v_stale_documentation AS ...;
CREATE VIEW v_artifact_dependency_graph AS ...;
```

---

## Comparison: Separate vs Unified

| Aspect | Separate Artifacts Table | Unified Completables Table |
|--------|-------------------------|----------------------------|
| **Identity Space** | Two separate ID systems | Single ULID space |
| **Polymorphic References** | Complex (union/multiple FKs) | Simple (single FK) |
| **Criteria Targets** | `criteria.target_artifact_id` + `criteria.target_ticket_id` | `criteria.completable_id` |
| **Schema Maintenance** | Update 2 tables | Update 1 table |
| **Query Complexity** | UNIONs to query all completables | Single SELECT with WHERE |
| **Storage Overhead** | Duplicate columns (id, name, status) | NULLs for inapplicable fields |
| **Extensibility** | Add table for each new type | Add discriminator value |

**Winner:** Unified completables table ✅

---

## Design Validation

### ✅ Criteria Can Reference Artifacts
```sql
-- Criterion: Task blocked until documentation exists
INSERT INTO criteria (
    id, completable_id, description, blocks_transition_to,
    target_type, target_json
) VALUES (
    'crit-123',
    'task-456',
    'Documentation must exist before task completion',
    'completed',
    'completable',
    '{"type": "completable", "completable_id": "artifact-doc-789", "required_status": "completed"}'
);
```

### ✅ Artifacts Can Have Criteria
```sql
-- Criterion: Artifact blocked until tests pass
INSERT INTO criteria (
    id, completable_id, description, blocks_transition_to,
    target_type, target_json
) VALUES (
    'crit-999',
    'artifact-module-111',
    'Module tests must pass',
    'completed',
    'test_passes',
    '{"type": "test_passes", "test_command": "pytest tests/test_module.py", "pass_threshold": 100}'
);
```

### ✅ Unified Queries Work
```sql
-- Find all incomplete work items (tickets AND artifacts)
SELECT id, name, completable_type, ticket_type, artifact_type
FROM completables
WHERE status != 'completed';

-- Find all criteria blocking any completable
SELECT c.description, comp.name, comp.completable_type
FROM criteria c
JOIN completables comp ON c.completable_id = comp.id
WHERE c.is_met = 0;
```

---

## Conclusion

**Artifacts do NOT need a separate table.** They are stored in the unified `completables` table with:
- `completable_type = 'artifact'`
- Artifact-specific fields populated
- Ticket-specific fields set to NULL

This design:
1. ✅ Enables polymorphic criteria references
2. ✅ Maintains single identity space
3. ✅ Simplifies queries and schema
4. ✅ Supports all artifact use cases (provenance, documentation, dependencies)

**Schema Version:** 2.0.0 (unified completables)

---

**Design Status:** ✅ Complete
**Decision:** No separate artifacts table - use completables table
**Reviewed By:** Claude Opus 4.5
**Approved:** 2025-12-09
