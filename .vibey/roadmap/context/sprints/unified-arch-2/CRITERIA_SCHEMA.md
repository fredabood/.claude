# Unified Criteria Table Schema Design

**Date:** 2025-12-09
**Sprint:** unified-arch-2 (Database Schema Migration)
**Task:** unified-arch-2-task-002
**Status:** Final Design

---

## Overview

This document specifies the **unified criteria table** that replaces separate arrays/tables for dependencies, blockers, deliverables, and quality gates with a single polymorphic criterion system.

**Key Design Decision:** Use criteria as the ONLY blocking mechanism. All requirements (dependencies, deliverables, gates) become criteria with different target types.

---

## Table Schema

```sql
CREATE TABLE criteria (
    -- =========================================================================
    -- IDENTITY
    -- =========================================================================
    id TEXT PRIMARY KEY,                    -- ULID

    -- =========================================================================
    -- OWNERSHIP
    -- =========================================================================
    completable_id TEXT NOT NULL REFERENCES completables(id) ON DELETE CASCADE,

    -- =========================================================================
    -- CRITERION DEFINITION
    -- =========================================================================
    description TEXT NOT NULL,              -- Human-readable description
    required INTEGER NOT NULL DEFAULT 1,    -- 0 = warning, 1 = blocking

    -- UNIFIED BLOCKING: which status transition does this block?
    blocks_transition_to TEXT NOT NULL DEFAULT 'completed' CHECK (
        blocks_transition_to IN ('in_progress', 'completed', 'production_ready', 'deployed')
    ),

    -- =========================================================================
    -- POLYMORPHIC TARGET (Criterion Target Type)
    -- =========================================================================
    target_type TEXT NOT NULL CHECK (target_type IN (
        'completable',          -- Depends on another completable (ticket or artifact)
        'file_exists',          -- File(s) must exist at path(s)
        'test_passes',          -- Test command must pass
        'test_coverage',        -- Code coverage must meet threshold
        'threshold',            -- Numeric metric must meet threshold
        'manual',               -- Manual verification required
        'external',             -- External system check
        'symbol_exists',        -- Symbol (function/class) must exist in code
        'command_exists'        -- Command must be available in environment
    )),

    -- Target configuration (JSON, schema varies by target_type)
    target_json TEXT NOT NULL,

    -- =========================================================================
    -- EVALUATION STATE (Cached)
    -- =========================================================================
    is_met INTEGER,                         -- NULL = not evaluated, 0 = not met, 1 = met
    last_checked TEXT,                      -- ISO 8601 timestamp of last evaluation

    -- =========================================================================
    -- METADATA
    -- =========================================================================
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

---

## Indexes

```sql
-- Lookups by completable
CREATE INDEX idx_criteria_completable ON criteria(completable_id);

-- Filter by transition type
CREATE INDEX idx_criteria_blocks_transition ON criteria(completable_id, blocks_transition_to);

-- Query by target type
CREATE INDEX idx_criteria_target_type ON criteria(target_type);

-- Find unmet criteria
CREATE INDEX idx_criteria_is_met ON criteria(completable_id, is_met);

-- Find stale criteria (need re-evaluation)
CREATE INDEX idx_criteria_last_checked ON criteria(last_checked);
```

---

## Target Type Schemas

Each `target_type` has a specific JSON schema for `target_json`:

### 1. CompletableTarget (dependencies)

**Purpose:** Blocks until another completable reaches required status

```json
{
  "type": "completable",
  "completable_id": "01HXYZ...",        // ULID of the target completable
  "required_status": "completed",        // Status the target must reach
  "cascade_deferred": false              // If target is deferred, is this criterion waived?
}
```

**Example Use Cases:**
- Sprint blocked until previous sprint completes
- Task blocked until dependency task completes
- Artifact blocked until source code artifact exists

**Replaces:**
- `blocked_by` arrays
- `depends_on` arrays
- `entity_blocked_by` table

---

### 2. FileExistsTarget (deliverables)

**Purpose:** Blocks until file(s) exist at specified path(s)

```json
{
  "type": "file_exists",
  "paths": ["src/module.py", "tests/test_module.py"],
  "all_required": true,                  // true = all must exist, false = any must exist
  "deliverable_type": "code"             // For categorization (code, docs, test, config)
}
```

**Example Use Cases:**
- Task blocked until code file created
- Task blocked until documentation written
- Sprint blocked until all deliverables produced

**Replaces:**
- `deliverables` arrays
- `entity_deliverables` table

---

### 3. TestPassesTarget (quality gates)

**Purpose:** Blocks until test command passes

```json
{
  "type": "test_passes",
  "test_command": "pytest tests/integration/",
  "pass_threshold": 100,                 // Percentage of tests that must pass
  "timeout_seconds": 300,
  "working_directory": null              // Optional: run from specific directory
}
```

**Example Use Cases:**
- Sprint completion blocked until all tests pass
- Production deployment blocked until integration tests pass

**Replaces:**
- `quality_gates` arrays
- `development_gates` arrays

---

### 4. TestCoverageTarget (coverage gates)

**Purpose:** Blocks until code coverage meets threshold

```json
{
  "type": "test_coverage",
  "source_command": "pytest --cov=src tests/",
  "coverage_type": "line",               // line, branch, function
  "overall_threshold": 80,               // Overall coverage %
  "per_file_threshold": null,            // Optional: per-file minimum
  "exclude_patterns": ["*/test_*.py"]
}
```

**Example Use Cases:**
- Production deployment blocked until 90% coverage
- Sprint completion blocked until new code has 80% coverage

**Replaces:**
- Custom quality gate configurations

---

### 5. ThresholdTarget (numeric metrics)

**Purpose:** Blocks until numeric metric meets threshold

```json
{
  "type": "threshold",
  "metric_name": "bundle_size_kb",
  "threshold": 500,
  "comparison": "less_than",             // less_than, less_than_or_equal, greater_than, etc.
  "current_value": null,                 // Cached from last check
  "evaluation_command": "stat -f %z dist/bundle.js"
}
```

**Example Use Cases:**
- Production deployment blocked if bundle size exceeds 500KB
- Performance criterion: response time < 200ms

**Replaces:**
- Custom performance gates

---

### 6. ManualTarget (manual verification)

**Purpose:** Blocks until human manually verifies completion

```json
{
  "type": "manual",
  "assessor": "product-owner",           // Who must verify
  "instructions": "Review UI mockups for accessibility compliance",
  "assessed": false,                     // Has assessor reviewed?
  "met": false,                          // Assessor's verdict
  "assessed_at": null,                   // When assessed
  "notes": null                          // Assessor's notes
}
```

**Example Use Cases:**
- Production deployment blocked until product owner approves
- Design review required before implementation

**Replaces:**
- Manual approval workflows

---

### 7. ExternalTarget (external system checks)

**Purpose:** Blocks until external system returns expected status

```json
{
  "type": "external",
  "system_name": "jira",
  "endpoint": "https://jira.example.com/rest/api/2/issue/PROJ-123",
  "expected_status": "Done",
  "auth_method": "bearer_token",         // How to authenticate
  "status_path": "$.fields.status.name"  // JSON path to status field
}
```

**Example Use Cases:**
- Vibey sprint blocked until Jira epic completes
- Deployment blocked until security scan passes in external tool

**Replaces:**
- External dependency tracking

---

### 8. SymbolExistsTarget (code structure validation)

**Purpose:** Blocks until specific symbol (function/class) exists in code

```json
{
  "type": "symbol_exists",
  "file_path": "src/api/routes.py",
  "symbol_name": "create_user_endpoint",
  "symbol_type": "function",             // function, class, method, variable
  "signature": null                      // Optional: expected signature
}
```

**Example Use Cases:**
- Refactoring task blocked until new API endpoint exists
- Migration blocked until legacy function removed

**Replaces:**
- Code structure gates

---

### 9. CommandExistsTarget (environment validation)

**Purpose:** Blocks until command is available in environment

```json
{
  "type": "command_exists",
  "command": "docker",
  "version_constraint": ">=20.0.0",      // Optional semver constraint
  "check_command": "docker --version"
}
```

**Example Use Cases:**
- Infrastructure task blocked until kubectl installed
- Build task blocked until Node.js >= 18 available

**Replaces:**
- Environment prerequisite checks

---

## Criterion Lifecycle

```
Created (is_met=NULL)
    ↓
Pending Evaluation (is_met=NULL, last_checked=NULL)
    ↓
Evaluated (is_met=0|1, last_checked=timestamp)
    ↓
Met (is_met=1) ────→ Unblocked
    ↓
Stale (last_checked too old)
    ↓
Re-evaluated
```

---

## Transition Blocking Logic

### How Criteria Block Transitions

1. **Transition Requested:** Ticket tries to transition to new status
2. **Filter Criteria:** Get all criteria where `blocks_transition_to = target_status`
3. **Filter Required:** Get subset where `required = 1`
4. **Check Met:** For each required criterion, check `is_met`
5. **Block if Unmet:** If any `is_met = 0`, transition blocked

### Example: Task Completion

```sql
-- Can task transition to 'completed'?
SELECT description, target_type, is_met
FROM criteria
WHERE completable_id = 'task-123'
  AND blocks_transition_to = 'completed'
  AND required = 1
  AND is_met != 1;

-- If query returns rows, transition blocked
-- Return descriptions as blocking reasons
```

---

## Criterion Evaluation

### Evaluation Workflow

```python
def evaluate_criterion(criterion: Criterion) -> bool:
    """Evaluate criterion and cache result."""
    target_data = json.loads(criterion.target_json)

    # Dispatch by target_type
    if criterion.target_type == 'completable':
        is_met = evaluate_completable_target(target_data)
    elif criterion.target_type == 'file_exists':
        is_met = evaluate_file_exists_target(target_data)
    elif criterion.target_type == 'test_passes':
        is_met = evaluate_test_passes_target(target_data)
    # ... etc

    # Cache result
    update_criterion(
        criterion.id,
        is_met=is_met,
        last_checked=datetime.now(UTC)
    )

    return is_met
```

### Re-evaluation Strategy

**Trigger Conditions:**
1. **On-demand:** User manually triggers re-evaluation
2. **On-status-change:** When completable target changes status
3. **Periodic:** Cron job checks stale criteria (last_checked > 1 hour ago)
4. **Pre-transition:** Before allowing status transition

---

## Migration Strategy

### Phase 1: Create Criteria Table
```sql
CREATE TABLE criteria (...);
CREATE INDEXES ...;
```

### Phase 2: Migrate Existing Blocking Data

#### Convert blocked_by to CompletableTarget criteria
```sql
INSERT INTO criteria (id, completable_id, description, blocks_transition_to, target_type, target_json, ...)
SELECT
    'dep-' || blocked_id || '-' || blocker_id,
    blocked_id,
    COALESCE(reason, 'Depends on ' || blocker_id),
    COALESCE(blocks_transition_to, 'in_progress'),
    'completable',
    json_object(
        'type', 'completable',
        'completable_id', blocker_id,
        'required_status', COALESCE(required_status, 'completed'),
        'cascade_deferred', 0
    ),
    ...
FROM entity_blocked_by;
```

#### Convert deliverables to FileExistsTarget criteria
```sql
INSERT INTO criteria (id, completable_id, description, blocks_transition_to, target_type, target_json, ...)
SELECT
    'del-' || entity_id || '-' || row_number,
    entity_id,
    'Deliverable: ' || path,
    'completed',
    'file_exists',
    json_object(
        'type', 'file_exists',
        'paths', json_array(path),
        'all_required', 1,
        'deliverable_type', type
    ),
    ...
FROM entity_deliverables;
```

#### Convert quality_gates to TestPassesTarget criteria
```sql
INSERT INTO criteria (id, completable_id, description, blocks_transition_to, target_type, target_json, ...)
SELECT
    'gate-' || entity_id || '-' || gate_name,
    entity_id,
    description,
    status_to_block,
    'test_passes',
    json_object(
        'type', 'test_passes',
        'test_command', test_command,
        'pass_threshold', pass_threshold
    ),
    ...
FROM quality_gates;
```

### Phase 3: Drop Old Tables/Columns
After migration verified:
- Drop `entity_blocked_by` table
- Drop `entity_depends_on` table
- Drop `entity_deliverables` table
- Drop `quality_gates` table
- Drop JSON columns: `dependencies_json`, `deliverables_json`, etc.

---

## Design Rationale

### Why Unified Criteria?

**Before (Fragmented):**
- `blocked_by` array - tracks dependencies
- `depends_on` array - tracks prerequisites
- `deliverables` array - tracks required files
- `quality_gates` array - tracks test requirements
- **Problem:** 4 different systems, inconsistent semantics

**After (Unified):**
- `criteria` table - ALL requirements
- **Benefit:** Single evaluation system, consistent blocking logic

### Why Polymorphic Targets?

**Alternative:** Separate tables for each target type
- `dependency_criteria`
- `deliverable_criteria`
- `test_criteria`
- **Problem:** Schema fragmentation, complex queries

**Chosen:** Single `criteria` table with `target_type` discriminator
- **Benefit:** Simpler schema, easier to add new target types

### Why Cache Evaluation State?

**Without Caching:**
- Re-evaluate criteria on every status check
- **Problem:** Slow (file I/O, subprocess calls, network requests)

**With Caching:**
- Store `is_met` + `last_checked`
- Re-evaluate periodically or on-demand
- **Benefit:** Fast status checks, explicit re-evaluation control

---

## Compatibility Notes

### Existing Migration File
`vibey/roadmap/database/migrations/006_unified_ticket_schema.sql` implements a `criteria` table similar to this design. This spec extends that with:
1. Additional target types (symbol_exists, command_exists)
2. `required` field (0 = warning, 1 = blocking)
3. `updated_at` timestamp
4. More detailed target_json schemas

### Schema Version
- Current: 1.0.0 (27 tables, separate blocking systems)
- After this migration: 2.0.0 (unified criteria)

---

## Views for Convenience

### v_blocking_criteria
All criteria currently blocking a completable:
```sql
CREATE VIEW v_blocking_criteria AS
SELECT
    c.*,
    comp.name as completable_name,
    comp.status as completable_status
FROM criteria c
JOIN completables comp ON c.completable_id = comp.id
WHERE c.required = 1
  AND c.is_met != 1;
```

### v_dependency_graph
Completable dependencies as graph edges:
```sql
CREATE VIEW v_dependency_graph AS
SELECT
    c.completable_id as from_id,
    json_extract(c.target_json, '$.completable_id') as to_id,
    c.description as edge_label,
    c.blocks_transition_to as blocks_status,
    c.is_met
FROM criteria c
WHERE c.target_type = 'completable';
```

### v_pending_evaluations
Criteria needing re-evaluation:
```sql
CREATE VIEW v_pending_evaluations AS
SELECT *
FROM criteria
WHERE is_met IS NULL
   OR last_checked IS NULL
   OR datetime(last_checked) < datetime('now', '-1 hour');
```

---

## Next Steps

1. **Task 003:** Design artifacts table schema (if separate from completables)
2. **Task 004:** Write migration script implementing this schema
3. **Task 005:** Update sql_loader.py to load criteria
4. **Task 006:** Update sql_dumper.py to save criteria
5. **Task 007:** Implement criterion evaluation logic

---

**Design Status:** ✅ Complete
**Reviewed By:** Claude Opus 4.5
**Approved:** 2025-12-09
