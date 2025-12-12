# Artifact Relationship Model Analysis

**Generated:** 2025-12-12
**Sprint:** Phase 1.6 - Database Artifact Audit
**Task:** Analyze artifact relationship model

## Executive Summary

The vibey roadmap database implements a sophisticated relationship model with:
- **Hierarchical relationships** between core entities (roadmap → track → sprint → task)
- **Polymorphic relationship tables** for cross-entity relationships (blocking, dependencies, artifacts)
- **Self-referential relationships** in artifacts table for documentation lineage
- **Dual storage patterns** (normalized tables + embedded JSON) for commits and deliverables

**Key Finding:** Most relationship tables are designed but unpopulated, indicating planned functionality not yet implemented.

---

## 1. Hierarchical Relationships (Parent-Child)

### Core Entity Hierarchy

```
Roadmap (1)
    └── Track (41 total)
           └── Sprint (206 total)
                  └── Task (1549 total)
```

### Implementation

| Parent | Child | FK Column | Cardinality |
|--------|-------|-----------|-------------|
| roadmaps | tracks | track.roadmap_id | 1:N |
| tracks | sprints | sprint.track_id | 1:N |
| sprints | tasks | task.sprint_id | 1:N |
| tracks | tasks | task.track_id | 1:N (denormalized) |

**Notes:**
- Tasks have both `sprint_id` and `track_id` for efficient querying
- All FKs are TEXT type (ULIDs) matching the parent's id
- CASCADE delete behavior not explicitly defined in schema

---

## 2. Polymorphic Relationship Tables

### 2.1 Blocking Relationships

#### entity_blocks
Tracks which entities block other entities.

| Column | Type | Purpose |
|--------|------|---------|
| blocker_type | TEXT | CHECK IN (track, sprint, task) |
| blocker_id | TEXT | ID of blocking entity |
| blocked_type | TEXT | CHECK IN (track, sprint, task) |
| blocked_id | TEXT | ID of blocked entity |
| reason | TEXT | Why the block exists |

**Usage:** 0 rows (empty)

#### entity_blocked_by
Inverse of blocks with business logic.

| Column | Type | Purpose |
|--------|------|---------|
| blocked_type | TEXT | Entity waiting on blocker |
| blocked_id | TEXT | ID of waiting entity |
| blocker_type | TEXT | Entity that must complete |
| blocker_id | TEXT | ID of blocking entity |
| required_status | TEXT | Status blocker must reach (default: completed) |
| blocks_transition_to | TEXT | What transition is blocked (default: in_progress) |
| reason | TEXT | Explanation |

**Usage:** 0 rows (empty)

**Triggers Attached:**
- `trg_task_blocked_by_insert` - Sets task.blocked = 1
- `trg_task_blocked_by_delete` - Recalculates task.blocked
- `trg_sprint_blocked_by_insert/delete` - Same for sprints
- `trg_track_blocked_by_insert/delete` - Same for tracks

### 2.2 Dependency Relationships

#### entity_depends_on
Soft dependencies between entities.

| Column | Type | Purpose |
|--------|------|---------|
| dependent_type | TEXT | Entity that needs the other |
| dependent_id | TEXT | ID of dependent entity |
| dependency_type | TEXT | Entity that is needed |
| dependency_id | TEXT | ID of dependency |
| reason | TEXT | Explanation |

**Usage:** 0 rows (empty)

**Difference from entity_blocked_by:**
- `entity_blocked_by` = hard block (prevents progress)
- `entity_depends_on` = soft dependency (informational)

### 2.3 External Dependencies

#### external_dependencies
Dependencies on things outside the roadmap system.

| Column | Type | Purpose |
|--------|------|---------|
| owner_type | TEXT | CHECK IN (roadmap, track, sprint, task) |
| owner_id | TEXT | ID of owning entity |
| name | TEXT | Dependency name |
| description | TEXT | Details |
| status | TEXT | CHECK IN (pending, resolved, blocked) |
| resolved_at | TEXT | When resolved |
| metadata | TEXT | JSON for extra data |

**Usage:** 0 rows (empty)

### 2.4 Artifact Relationships

#### entity_commits
Links entities to git commits.

| Column | Type | Purpose |
|--------|------|---------|
| owner_type | TEXT | CHECK IN (track, sprint, task) |
| owner_id | TEXT | ID of owning entity |
| commit_id | INTEGER | FK to commits table |

**Usage:** 0 rows (empty)
**Alternative:** tasks.commits_json, sprints use views

#### entity_deliverables
Links entities to deliverables.

| Column | Type | Purpose |
|--------|------|---------|
| owner_type | TEXT | CHECK IN (track, sprint, task) |
| owner_id | TEXT | ID of owning entity |
| deliverable_id | INTEGER | FK to deliverables table |

**Usage:** 0 rows (empty)
**Alternative:** tasks.deliverables_json, sprints.deliverables_json

---

## 3. Self-Referential Relationships

### artifacts Table

The artifacts table supports two types of self-referential relationships:

#### 3.1 Documentation Lineage
| Column | Type | Purpose |
|--------|------|---------|
| documents_artifact_id | TEXT | FK to artifacts(id) this documents |
| documented_source_hash | TEXT | Hash of source at documentation time |
| is_stale | INTEGER | 1 if documented_source_hash != current source hash |

**Use Case:** Track which documentation artifacts document which code artifacts, enabling staleness detection.

#### 3.2 Dependency Graph
| Column | Type | Purpose |
|--------|------|---------|
| depends_on_artifact_ids | TEXT | JSON array of artifact IDs |

**Use Case:** Track code dependencies between artifacts (e.g., module A imports module B).

**Usage:** 0 rows (artifacts table is empty)

---

## 4. Ownership Patterns

### Direct Ownership (FK-based)
```
Task → Sprint (task.sprint_id)
Task → Track (task.track_id)
Sprint → Track (sprint.track_id)
Track → Roadmap (track.roadmap_id)
```

### Polymorphic Ownership (type + id pairs)
```
entity_commits: owner_type + owner_id → commits
entity_deliverables: owner_type + owner_id → deliverables
external_dependencies: owner_type + owner_id → external_dependencies
```

### Embedded Ownership (JSON columns)
```
tasks.commits_json → embedded commit objects
tasks.deliverables_json → embedded deliverable objects
sprints.deliverables_json → embedded deliverable objects
sprints.plan_file → embedded path string
```

---

## 5. Aggregation via Views

### View Hierarchy
```
v_sprint_commits ← aggregates tasks.commits_json by sprint
    ↓
v_track_commits ← aggregates v_sprint_commits by track

v_sprint_deliverables ← aggregates tasks.deliverables_json by sprint
    ↓
v_track_deliverables ← aggregates v_sprint_deliverables by track
```

**Purpose:** Roll up task-level artifacts to sprint and track levels without duplicating data.

---

## 6. Relationship Pattern Analysis

### Pattern 1: Dual Storage (JSON + Normalized)

**Tables Affected:** commits, deliverables

| Storage | Mechanism | Pros | Cons |
|---------|-----------|------|------|
| Normalized | commits, deliverables + entity_* tables | Query flexibility, referential integrity | More complex inserts |
| Embedded JSON | tasks.commits_json, tasks.deliverables_json | Simple inserts, self-contained | Query complexity, no FK integrity |

**Current State:** Only JSON columns are used; normalized tables are empty.

### Pattern 2: Polymorphic Relationships

**Tables Using This Pattern:**
- entity_blocks (blocker_type, blocked_type)
- entity_blocked_by (blocked_type, blocker_type)
- entity_depends_on (dependent_type, dependency_type)
- entity_commits (owner_type)
- entity_deliverables (owner_type)
- external_dependencies (owner_type)

**Implementation:** All use CHECK constraints to validate type values.

### Pattern 3: Missing Artifact-to-Entity Links

**Gap Identified:** The artifacts table has no direct relationship to tracks, sprints, or tasks.

**Expected Pattern (not implemented):**
```sql
-- Option A: Polymorphic table
CREATE TABLE entity_artifacts (
    owner_type TEXT CHECK (owner_type IN ('track', 'sprint', 'task')),
    owner_id TEXT,
    artifact_id TEXT REFERENCES artifacts(id)
);

-- Option B: JSON column in entities
ALTER TABLE tasks ADD artifact_ids TEXT; -- JSON array
```

---

## 7. Gap Analysis

### Unpopulated Tables

| Table | Rows | Impact |
|-------|------|--------|
| artifacts | 0 | No file tracking |
| commits | 0 | Git integration unused |
| deliverables | 0 | Normalized deliverables unused |
| entity_commits | 0 | Commit linking unused |
| entity_deliverables | 0 | Deliverable linking unused |
| entity_blocks | 0 | Block tracking unused |
| entity_blocked_by | 0 | Blocked-by tracking unused |
| entity_depends_on | 0 | Dependency tracking unused |
| external_dependencies | 0 | External dep tracking unused |

### Missing Relationships

1. **Artifacts ↔ Entities:** No way to link artifacts to tasks/sprints/tracks
2. **Artifacts ↔ Commits:** No provenance linking artifacts to commits that created them
3. **Context Files ↔ Entities:** Context files not tracked in schema at all

### Inconsistent Patterns

1. **Dual Storage:** JSON columns vs normalized tables for same data (commits, deliverables)
2. **Mixed ID Types:** INTEGER autoincrement (commits, deliverables) vs TEXT ULID (artifacts, entities)
3. **Missing Context Integration:** Rich context file structure in filesystem not reflected in DB

---

## 8. Recommendations

### Short-Term (Data Population)
1. Implement CLI commands to populate `entity_blocked_by` and `entity_depends_on`
2. Migrate JSON deliverables to normalized tables OR delete normalized tables
3. Add artifact tracking from file audits to `artifacts` table

### Medium-Term (Schema Enhancement)
1. Add `entity_artifacts` polymorphic table linking artifacts to entities
2. Add `provenance.commit_id` to artifacts to track creation commits
3. Add `context_files` table to track context directory contents

### Long-Term (Pattern Consistency)
1. Choose ONE storage pattern for commits/deliverables (recommend normalized)
2. Implement views that present consistent interface regardless of storage
3. Add triggers to sync JSON ↔ normalized if dual pattern is kept

---

## Appendix: Relationship Diagram

```
                    ┌──────────────┐
                    │   roadmaps   │
                    └──────┬───────┘
                           │ 1:N
                    ┌──────▼───────┐
                    │    tracks    │───────────────┐
                    └──────┬───────┘               │
                           │ 1:N                   │
                    ┌──────▼───────┐               │
                    │   sprints    │───────────────┤
                    └──────┬───────┘               │
                           │ 1:N                   │
                    ┌──────▼───────┐               │
                    │    tasks     │───────────────┤
                    └──────────────┘               │
                                                   │
    ┌──────────────────────────────────────────────┘
    │ Polymorphic Relationships (via owner_type/owner_id)
    ▼
┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐
│ entity_commits  │  │entity_deliverables│  │external_dependencies│
│   (0 rows)      │  │    (0 rows)     │  │      (0 rows)      │
└────────┬────────┘  └────────┬────────┘  └────────────────────┘
         │                    │
         ▼                    ▼
   ┌──────────┐         ┌──────────────┐
   │ commits  │         │ deliverables │
   │ (0 rows) │         │   (0 rows)   │
   └──────────┘         └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Blocking/Dependency Relationships (entity ↔ entity)        │
├─────────────────┬───────────────────┬──────────────────────┤
│ entity_blocks   │ entity_blocked_by │ entity_depends_on    │
│   (0 rows)      │    (0 rows)       │     (0 rows)         │
└─────────────────┴───────────────────┴──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Standalone Artifact Registry                                │
├─────────────────────────────────────────────────────────────┤
│ artifacts (0 rows)                                          │
│   ├── documents_artifact_id → artifacts(id) [self-ref]      │
│   └── depends_on_artifact_ids → JSON array of artifact IDs  │
│                                                             │
│ NO LINK TO tracks/sprints/tasks                             │
└─────────────────────────────────────────────────────────────┘
```
