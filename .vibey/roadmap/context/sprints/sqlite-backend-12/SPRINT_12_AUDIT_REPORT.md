# Sprint 12 Audit Report: Sprint 6 Design vs Current Codebase

**Date:** 2025-12-06
**Task:** sqlite-backend-12-task-001
**Purpose:** Comprehensive audit comparing Sprint 6 unified ticket architecture design against current codebase implementation

---

## Executive Summary

The Sprint 6 design documents (`sqlite-backend-6/context/architecture/`) define a comprehensive unified ticket architecture with criteria-based completion. The **Pydantic models are fully implemented**, but the **database schema and serialization integration are incomplete**.

| Component | Design Status | Implementation Status |
|-----------|--------------|----------------------|
| Pydantic Models (Completable, Criterion) | Complete | **✅ IMPLEMENTED** |
| 8 Target Types | Complete | **✅ IMPLEMENTED** |
| Enums (CriterionTargetType, etc.) | Complete | **✅ IMPLEMENTED** |
| YAML Loader (criteria parsing) | Complete | **✅ IMPLEMENTED** |
| YAML Dumper (criteria serialization) | Complete | **✅ IMPLEMENTED** |
| Database Schema (criteria tables) | Complete | **❌ NOT IMPLEMENTED** |
| SQL Loader (criteria loading) | Complete | **❌ NOT IMPLEMENTED** |
| SQL Dumper (criteria persistence) | Complete | **❌ NOT IMPLEMENTED** |
| CLI Integration (can_transition_to) | Complete | **❌ NOT IMPLEMENTED** |
| Pre-commit Hook (verify_completion_claims) | Complete | **❌ NOT IMPLEMENTED** |

---

## Detailed Findings

### 1. Pydantic Models ✅ IMPLEMENTED

**Location:** `vibey/roadmap/models/ticket/`

| File | Class | Status |
|------|-------|--------|
| `completable.py` | `Completable` | ✅ Full implementation with `can_transition_to()`, `progress_for_transition()`, criteria management |
| `completable.py` | `Criterion` | ✅ Full implementation with `blocks_transition_to`, `target`, `is_met` |
| `targets.py` | `CompletableTarget` | ✅ Dependency on other Completables |
| `targets.py` | `FileExistsTarget` | ✅ File existence checks |
| `targets.py` | `TestPassesTarget` | ✅ Test command pass/fail |
| `targets.py` | `TestCoverageTarget` | ✅ Coverage thresholds |
| `targets.py` | `ThresholdTarget` | ✅ Generic metric thresholds |
| `targets.py` | `ManualTarget` | ✅ Human assessment |
| `targets.py` | `ExternalTarget` | ✅ External system checks |
| `targets.py` | `ArtifactTarget` | ✅ Artifact entity verification |

**Key Methods Implemented:**
- `Completable.can_transition_to(status)` → `(bool, List[str])`
- `Completable.progress_for_transition(status)` → `Progress`
- `Criterion.is_met` → computed from `target.is_satisfied()`
- `CriterionTarget.refresh(context)` → update cached state

### 2. Enums ✅ IMPLEMENTED

**Location:** `vibey/roadmap/models/ticket/enums.py`

All enums from Sprint 6 design are present:
- `CriterionTargetType` (completable, file_exists, test_passes, test_coverage, threshold, manual, external, artifact)
- `ThresholdComparison` (gte, gt, eq, lte, lt) with `compare()` method
- `InheritMode` (inherit, override, skip)
- `EnforcementMode` (blocking, warning, audit)
- `TicketStatus` with `progression_order()` and `precedes()`

### 3. YAML Serialization ✅ IMPLEMENTED

**Location:** `vibey/roadmap/serialization/yaml_loader.py`

**Conversion functions (legacy → criteria):**
- `_legacy_dependency_to_criterion()` (line 283) - depends_on/blocked_by → CompletableTarget
- `_subtask_to_criterion()` (line 336) - child items → CompletableTarget blocking COMPLETED
- `_legacy_deliverable_to_criterion()` (line 361) - deliverables → FileExistsTarget
- `_legacy_quality_gate_to_criterion()` (line 420) - quality_gates → ThresholdTarget

**Native v2 parsing:**
- Direct `criteria` field parsing for TaskTicket (line 1716)
- Direct `criteria` field parsing for SprintTicket (line 1917)
- Direct `criteria` field parsing for TrackTicket (line 2130)
- Direct `criteria` field parsing for RoadmapTicket (line 2294)

**Location:** `vibey/roadmap/serialization/yaml_dumper.py`

- `_dump_criterion()` (line 1032) - Serialize Criterion to dict
- All ticket types include `'criteria': [_dump_criterion(c) for c in entity.criteria]`

### 4. Database Schema ❌ NOT IMPLEMENTED

**Current Schema Analysis:**

The current database has **26 tables** but uses the **legacy pattern**:

```sql
-- LEGACY TABLES (still in use):
entity_blocked_by     -- Should be: criteria with CompletableTarget
entity_depends_on     -- Should be: criteria with CompletableTarget
entity_blocks         -- Should be: criteria with CompletableTarget
quality_gates         -- Should be: criteria with ThresholdTarget
deliverables          -- Should be: criteria with FileExistsTarget
entity_deliverables   -- Junction table for deliverables
```

**MISSING TABLES (from Sprint 6 design):**

```sql
-- DESIGN: Unified completables table (single-table inheritance)
CREATE TABLE completables (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    completable_type TEXT NOT NULL,  -- 'ticket' or 'artifact'
    ticket_type TEXT,  -- 'roadmap', 'track', 'sprint', 'task'
    ...
);

-- DESIGN: Criteria table
CREATE TABLE criteria (
    id TEXT PRIMARY KEY,
    completable_id TEXT NOT NULL REFERENCES completables(id),
    description TEXT NOT NULL,
    blocks_transition_to TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_data TEXT NOT NULL,  -- JSON for polymorphic target
    required INTEGER DEFAULT 1,
    is_met INTEGER DEFAULT 0,  -- cached
    last_checked TEXT
);
```

**Current Reality:**
- Separate tables: `roadmaps`, `tracks`, `sprints`, `tasks`
- NO `criteria` table
- NO `criterion_targets` table or JSON storage
- Legacy tables: `quality_gates`, `entity_blocked_by`, `deliverables`

### 5. SQL Loader ❌ NOT IMPLEMENTED

**Location:** `vibey/roadmap/serialization/sql_loader.py`

- Line 1218 imports `CriterionORM` but it doesn't exist
- No functions to load criteria from database
- No functions to reconstruct Criterion objects from SQL

**Required Implementation:**
```python
def sql_load_criteria(completable_id: str) -> List[Criterion]:
    """Load all criteria for a Completable from database."""
    ...

def sql_load_criterion(criterion_id: str) -> Optional[Criterion]:
    """Load a single criterion by ID."""
    ...
```

### 6. SQL Dumper ❌ NOT IMPLEMENTED

**Location:** `vibey/roadmap/serialization/sql_dumper.py`

- Line 660 imports `CriterionORM` but it doesn't exist
- No functions to persist criteria to database
- No functions to serialize targets to JSON

**Required Implementation:**
```python
def sql_dump_criterion(criterion: Criterion, completable_id: str) -> None:
    """Persist a Criterion to the criteria table."""
    ...

def sql_dump_criteria(criteria: List[Criterion], completable_id: str) -> None:
    """Persist all criteria for a Completable."""
    ...
```

### 7. CLI Integration ❌ NOT IMPLEMENTED

**Location:** `vibey/cli/commands.py`, `vibey/operations/roadmap/update.py`

- Status updates do NOT call `can_transition_to()` before changing status
- No validation that criteria are met before completing tasks
- `vibey roadmap complete <id>` bypasses criteria checks entirely

**Required Integration:**
```python
def complete_task(task_id: str) -> Result:
    task = load_task(task_id)
    can_complete, blocking = task.can_transition_to(TicketStatus.COMPLETED)
    if not can_complete:
        return Error(f"Cannot complete: {blocking}")
    # Proceed with completion
```

### 8. Pre-commit Hook ❌ NOT IMPLEMENTED

**Design Reference:** `sqlite-backend-6/context/sample_code/models/func_verify_completion_claims.py`

No pre-commit hook exists to:
- Parse commit messages for "Completes: task-id" claims
- Verify that claimed tasks have all criteria met
- Block commits that falsely claim completion

---

## Migration Path

### Phase 1: Schema (Tasks 002-003)
1. Add `criteria` table with polymorphic `target_type` and `target_data` JSON
2. Create indexes for `completable_id` and `blocks_transition_to`
3. Keep legacy tables temporarily for backward compatibility

### Phase 2: Serialization (Tasks 004-008)
1. Update YAML format to include native `criteria` sections
2. Implement `sql_load_criteria()` and `sql_dump_criteria()`
3. Test round-trip: YAML → SQLite → YAML integrity

### Phase 3: Migration (Task 009)
1. Convert `entity_blocked_by` → CompletableTarget criteria
2. Convert `entity_depends_on` → CompletableTarget criteria
3. Convert `quality_gates` → ThresholdTarget criteria
4. Convert `deliverables` → FileExistsTarget criteria

### Phase 4: Enforcement (Tasks 010-012)
1. Integrate `can_transition_to()` in CLI status updates
2. Implement `verify_completion_claims()` in pre-commit hook
3. End-to-end validation

### Phase 5: Gap Closure (Tasks 013-015)
1. Migrate all quality_gates to ThresholdTarget criteria
2. Implement Requirements cascade for standards enforcement
3. Implement computed progress from criteria (replaces manual counters)

---

## Appendix: File References

### Architecture Documents
- `sqlite-backend-6/context/architecture/01-DESIGN-PRINCIPLES.md`
- `sqlite-backend-6/context/architecture/02-CLASS-MODEL.md`
- `sqlite-backend-6/context/architecture/05-DATABASE-SCHEMA.md`
- `sqlite-backend-6/context/architecture/06-SERIALIZATION.md`

### Sample Code (from design)
- `sqlite-backend-6/context/sample_code/models/completable.py`
- `sqlite-backend-6/context/sample_code/models/criterion.py`
- `sqlite-backend-6/context/sample_code/models/func_verify_completion_claims.py`

### Current Implementation
- `vibey/roadmap/models/ticket/completable.py` ✅
- `vibey/roadmap/models/ticket/targets.py` ✅
- `vibey/roadmap/models/ticket/enums.py` ✅
- `vibey/roadmap/serialization/yaml_loader.py` ✅
- `vibey/roadmap/serialization/yaml_dumper.py` ✅
- `vibey/roadmap/serialization/sql_loader.py` ❌ (needs criteria)
- `vibey/roadmap/serialization/sql_dumper.py` ❌ (needs criteria)

### Database Schema
- Current: 26 tables, NO criteria table
- Design: unified completables + criteria tables
