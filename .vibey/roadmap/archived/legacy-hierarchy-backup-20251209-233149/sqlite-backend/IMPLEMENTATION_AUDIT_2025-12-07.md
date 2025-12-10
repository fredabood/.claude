# sqlite-backend Track Implementation Audit

**Date:** 2025-12-07
**Status:** sqlite-backend track marked as "completed" (100% - 120 tasks)
**Finding:** Major architectural gaps between design and implementation

---

## Executive Summary

The sqlite-backend track was marked complete with 14 sprints and 120 tasks. However, a detailed audit reveals that while **model classes were implemented**, the **core architectural changes were not**:

| Component | Design Status | Implementation Status |
|-----------|---------------|----------------------|
| Model Classes (Pydantic) | Designed | **Implemented** |
| Unified Criterion System | Designed | **Models exist, not used** |
| FLAT Directory Structure | Designed | **Not implemented** |
| ULID Identity System | Designed | **Not implemented** |
| Unified Database Schema | Designed | **Not implemented** |
| Artifact System Integration | Designed | **Not integrated** |
| v2 YAML Format Migration | Designed | **Not performed** |

**Bottom Line:** The track delivered model scaffolding but not the architectural transformation described in the Sprint 6 design documents.

---

## Detailed Findings

### 1. Directory Structure

**Design (09-DESIGN-DECISIONS.md):**
```
.vibey/
├── roadmap.db
└── roadmap/
    ├── roadmap.yaml           # Summary only
    ├── tracks/                # FLAT - all track.yaml files
    ├── sprints/               # FLAT - all sprint.yaml files
    ├── tasks/                 # FLAT - all task.yaml files
    ├── artifacts/             # First-class artifact files
    └── context/               # Shared context files
```
- **~30 directories total**
- **4 levels maximum depth**
- **98% reduction from current structure**

**Current Implementation:**
```
.vibey/roadmap/
├── track-id/
│   ├── track.yaml
│   └── sprint-id/
│       ├── sprint.yaml
│       ├── context/
│       └── task-id/
│           └── task.yaml
```
- **1,300+ directories**
- **10+ levels deep**
- Nested track/sprint/task hierarchy

**Gap:** CRITICAL - Directory structure migration was never performed

---

### 2. Identity System

**Design (04-IDENTITY-SYSTEM.md):**
- Immutable ULID identifiers (e.g., `01HXYZ123ABC456`)
- `sequence` field for sibling ordering
- `slug` field for human-readable paths
- `.id` files mapping slug ↔ ULID
- Supports renaming without breaking references

**Current Implementation:**
- Slug-based IDs: `sqlite-backend-6-task-004`
- No ULID generation
- No `.id` mapping files
- No `sequence` field in YAML files

**Gap:** MAJOR - ULID system not implemented

---

### 3. Database Schema

**Design (05-DATABASE-SCHEMA.md):**
```sql
-- Unified completables table
CREATE TABLE completables (
    id TEXT PRIMARY KEY,        -- ULID
    type TEXT NOT NULL,         -- roadmap, track, sprint, task, artifact
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    parent_id TEXT REFERENCES completables(id),
    ...
);

-- Unified criteria table
CREATE TABLE criteria (
    id TEXT PRIMARY KEY,
    completable_id TEXT REFERENCES completables(id),
    blocks_transition_to TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_config TEXT,         -- JSON
    ...
);
```

**Current Implementation:**
```sql
-- Separate tables (NOT unified)
CREATE TABLE roadmaps (...);
CREATE TABLE tracks (...);
CREATE TABLE sprints (...);
CREATE TABLE tasks (...);

-- No criteria table
-- Legacy fields: blocked_by, depends_on, deliverables (JSON blobs)
```

**Gap:** CRITICAL - Database schema is legacy, not unified

---

### 4. Model Classes

**Design (02-CLASS-MODEL.md):**
- Layer 0: `Completable` with `criteria: List[Criterion]`
- Layer 1: `Ticket` with work semantics
- Layer 2: `HierarchicalTicket` with smart accessors
- Layer 3: Domain models (RoadmapTicket, TrackTicket, SprintTicket, TaskTicket)

**Current Implementation:**
Files exist at:
- `vibey/roadmap/models/ticket/completable.py` - **Implemented**
- `vibey/roadmap/models/ticket/ticket.py` - **Implemented**
- `vibey/roadmap/models/ticket/hierarchical.py` - **Implemented**
- `vibey/roadmap/models/ticket/domain.py` - **Implemented**
- `vibey/roadmap/models/ticket/artifact.py` - **Implemented**
- `vibey/roadmap/models/ticket/targets.py` - **Implemented**
- `vibey/roadmap/models/ticket/requirements.py` - **Implemented**

**Gap:** NONE for model classes - fully implemented

---

### 5. Serialization

**Design (06-SERIALIZATION.md & 07-IMPLEMENTATION-PLAN.md):**
- Sprint 8 was designated for "Serialization Migration"
- v2 YAML format with `criteria`, `parent_ref`, `ticket_type` fields
- Children represented as CompletableTarget criteria
- Dependencies as Criterion with `blocks_transition_to: in_progress`

**Current Implementation:**
- `yaml_loader.py` supports v1 and v2 detection
- `sql_loader.py` uses ONLY legacy dataclass models
- All YAML files remain in v1 format
- No migration performed

**Gap:** MAJOR - Data not migrated to v2 format

---

### 6. Artifact System

**Design (03-ARTIFACT-SYSTEM.md):**
- Artifacts are first-class entities (extend Completable)
- `ArtifactProvenance` tracking origin
- `documents_artifact_id` for staleness detection
- `artifacts` table in database
- `ArtifactTarget` criterion type

**Current Implementation:**
- `Artifact` class exists (`vibey/roadmap/models/ticket/artifact.py`)
- `ArtifactProvenance` implemented
- No `artifacts` table in database
- No artifact registry integration
- Artifacts not referenced by any criteria

**Gap:** MAJOR - Artifact system not integrated

---

### 7. Operations Layer

**Design (07-IMPLEMENTATION-PLAN.md Sprint 9):**
- All operations migrated to use criteria
- `can_transition_to()` as single check for all transitions
- Computed blocking from criteria

**Current Implementation:**
- `vibey/operations/roadmap/*.py` uses legacy models
- `RoadmapBackend` protocol uses `Roadmap, Track, Sprint, Task`
- `sql_loader.py` returns legacy dataclasses
- No criterion-based operations

**Gap:** MAJOR - Operations not migrated

---

## What WAS Implemented

1. **Pydantic Model Classes** - Complete layer 0-3 hierarchy
2. **CriterionTarget Types** - CompletableTarget, FileExistsTarget, ThresholdTarget, etc.
3. **Requirement System** - CriterionTemplate, RequirementResolver, InheritMode
4. **Artifact Entity** - Provenance tracking, staleness detection
5. **StatusManager** - Auto-progression (Sprint 13 Task 011)
6. **ActivityLog Integration** - Lifecycle event logging (Sprint 13 Task 010)
7. **Basic SQLite Sync** - Round-trip YAML ↔ SQLite (legacy schema)

---

## What Was NOT Implemented

1. **FLAT Directory Structure** - 1,300+ dirs → ~30 dirs migration
2. **ULID Identity System** - Immutable IDs with sequence/slug
3. **Unified Database Schema** - completables + criteria tables
4. **v2 YAML Format Migration** - criteria-based YAML
5. **Artifact Table & Registry** - Database integration
6. **Criterion-Based Operations** - Using Criterion for all blocking
7. **Semantic Layer Abstraction** - Pluggable providers (Jira, GitHub)

---

## Root Cause Analysis

The GAP_ANALYSIS.md file (dated during Sprint 6) listed 23 gaps and marked all as "RESOLVED". However, "resolved" meant "design documented" not "implementation complete".

The implementation sprints (7-13) focused on:
- Fixing bugs in existing SQLite sync
- Round-trip validation with legacy schema
- CLI command enhancements
- Auto-progression features

They did NOT execute the fundamental architectural changes:
- Schema migration
- Directory restructuring
- ULID adoption
- v2 format migration

---

## Recommendations

### Option A: Complete the Designed Architecture
Create new sprints to implement:
1. **Directory Migration Sprint** - Flatten to tracks/sprints/tasks/
2. **Schema Migration Sprint** - Create unified completables + criteria tables
3. **ULID Migration Sprint** - Generate ULIDs, create .id files
4. **v2 Format Sprint** - Convert all YAML to criteria-based format
5. **Operations Migration Sprint** - Refactor operations to use new models

Estimated effort: 5 sprints

### Option B: Document Current State as V1
Accept that the current implementation is "V1" of the SQLite backend:
1. Update design documents to reflect actual implementation
2. Mark unified architecture as "future V2"
3. Create separate track for V2 migration

### Option C: Hybrid Approach
1. Keep current directory structure (nested is actually fine for small roadmaps)
2. Migrate to unified schema + v2 format (most value)
3. Skip ULID (slug-based IDs work for single-user)

---

## Files Reviewed

### Design Documents (Sprint 6 Context)
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/00-INDEX.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/01-DESIGN-PRINCIPLES.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/02-CLASS-MODEL.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/03-ARTIFACT-SYSTEM.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/04-IDENTITY-SYSTEM.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/05-DATABASE-SCHEMA.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/06-SERIALIZATION.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/07-IMPLEMENTATION-PLAN.md`
- `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/09-DESIGN-DECISIONS.md`

### Implementation Files
- `vibey/roadmap/models/ticket/completable.py` - Criterion, Completable
- `vibey/roadmap/models/ticket/hierarchical.py` - HierarchicalTicket
- `vibey/roadmap/models/ticket/domain.py` - RoadmapTicket, TrackTicket, SprintTicket, TaskTicket
- `vibey/roadmap/models/ticket/artifact.py` - Artifact, ArtifactProvenance
- `vibey/roadmap/models/ticket/targets.py` - CriterionTarget subtypes
- `vibey/roadmap/serialization/yaml_loader.py` - v1/v2 format detection
- `vibey/roadmap/serialization/sql_loader.py` - Legacy model loading
- `vibey/roadmap/serialization/backend.py` - Backend abstraction
- `vibey/operations/roadmap/status_manager.py` - Auto-progression

### Database Schema
- `.vibey/roadmap.db` - Current SQLite database (legacy schema)

---

## Conclusion

The sqlite-backend track delivered valuable model scaffolding (Pydantic classes implementing the unified ticket architecture). However, the **production system still uses the legacy architecture**:

- Legacy database schema
- Nested directory structure
- Slug-based identifiers
- v1 YAML format
- Dataclass-based operations

The new model classes are available but not used by the actual roadmap system. A follow-up track is needed to migrate the production system to use the new architecture.

---

**Audit performed by:** Claude Code
**Date:** 2025-12-07
