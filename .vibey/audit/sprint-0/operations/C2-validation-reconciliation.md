# C2: Validation and Reconciliation System Audit

**Task ID:** 01KFXKBNRTTGDAQXM20EM4024T
**Phase:** C2: Operations
**Date:** 2026-01-29

## Executive Summary

Complete audit of the Vibey validation and reconciliation system, covering field-level validation, entity integrity checks, cross-storage synchronization, and auto-repair capabilities. The system has 3 validators: `RoadmapValidator` (basic format), `AdvancedValidator` (integrity issues), and `OptimizedValidator` (incremental checks). Key finding: the system detects 4 issue types (circular dependencies, orphaned tasks, broken references, progress mismatches) and can auto-repair progress counters and broken references.

## Methodology

**Files Analyzed:**
- `vibey/operations/roadmap/validate.py:1-200` - Basic format validation
- `vibey/operations/roadmap/advanced_validator.py:1-200` - Integrity checking
- `vibey/operations/roadmap/auto_repair.py:1-200` - Repair operations
- `vibey/operations/roadmap/auto_sync.py:1-144` - YAML-SQLite sync
- `vibey/operations/roadmap/optimized_validator.py` - Incremental validation

## Findings

### 2. Validation Rules Table

| Level | Rule | Applies To | Error Type | Example |
|-------|------|------------|------------|---------|
| Field | Required fields present | All entities | ValidationError | Missing `id`, `name`, `status` |
| Field | Data type correctness | Task | ValidationError | `estimated_tokens` must be integer |
| Field | Enum values valid | Status fields | ValidationError | `status` must be in Status enum |
| Entity | No embedded tasks | Sprint | FormatError | Sprint should not contain `tasks` array |
| Entity | Task file exists | Sprint | Warning | Tasks in separate file |
| Entity | Metadata present | All entities | Warning | Missing `metadata.last_updated` |
| Cross-entity | Sprint reference valid | Task | BrokenReference | `sprint_id` points to existing sprint |
| Cross-entity | Track reference valid | Sprint | BrokenReference | `track_id` points to existing track |
| Cross-entity | Dependency reference valid | Task | BrokenReference | `depends_on` IDs exist |
| Business | No circular dependencies | Task | CircularDependency | A → B → C → A detected |
| Business | Progress counters accurate | Sprint/Track | ProgressMismatch | Claimed vs actual completion |
| Business | Status consistency | Task | StatusError | Completed but no completion timestamp |

### 3. Integrity Checks Table

| Check | Type | Frequency | Recovery |
|-------|------|-----------|----------|
| YAML parse validity | Format | On load | Reject invalid file |
| Required fields presence | Format | On load | Report missing fields |
| Database schema version | Cross-storage | On connect | Run migrations |
| YAML-SQLite timestamp sync | Cross-storage | On operation | Trigger db rebuild |
| Task-sprint reference | Referential | On validate | Flag orphaned tasks |
| Sprint-track reference | Referential | On validate | Flag missing references |
| Dependency target existence | Referential | On validate | Flag broken references |
| Progress counter accuracy | Business | On validate | Auto-repair available |
| Circular dependency detection | Business | On validate | Manual resolution |

### 4. Reconciliation Process Table

| Step | Detection | Resolution | Trigger |
|------|-----------|------------|---------|
| YAML modification check | Compare file mtime vs db mtime | Rebuild database from YAML | CLI command, auto on operation |
| Orphaned task detection | Task references non-existent sprint | Suggest valid sprints | Manual validation |
| Broken reference detection | Reference points to missing ID | Remove reference or fix ID | Manual or auto-repair |
| Progress mismatch detection | Count children vs stored count | Update stored count | Auto-repair |
| Circular dependency detection | DFS cycle detection | Manual dependency removal | Validation |
| Schema migration | Check db schema_version | Run migration scripts | On connect |

### 5. Repair Operations Table

| Operation | Problem | Fix | Side Effects |
|-----------|---------|-----|--------------|
| `repair_progress_counters()` | Claimed != actual completion | Update progress fields | Affects parent rollup |
| `remove_broken_references()` | Reference to missing entity | Remove from list field | May change blocked status |
| `auto_repair_all()` | Multiple issues | Batch repair safe issues | Progress + refs fixed |
| `db rebuild` | Stale database | Full rebuild from YAML | All queries refreshed |
| `ensure_synced()` | YAML newer than db | Trigger rebuild | Auto-sync |

### 6. Validation Flow Diagram (ASCII)

```
                    ┌─────────────────────┐
                    │   Input: File(s)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  1. YAML Parsing    │
                    │  (yaml.safe_load)   │
                    └──────────┬──────────┘
                               │ Parse OK?
              ┌────────────────┼────────────────┐
              │ No             │ Yes            │
              ▼                ▼                │
    ┌─────────────────┐  ┌─────────────────┐   │
    │ Report Parse    │  │ 2. Schema Check │   │
    │ Error, Abort    │  │ (required fields)│   │
    └─────────────────┘  └────────┬────────┘   │
                                  │            │
                         ┌────────▼────────┐   │
                         │ 3. Type Check   │   │
                         │ (data types)    │   │
                         └────────┬────────┘   │
                                  │            │
                         ┌────────▼────────┐   │
                         │ 4. Reference    │   │
                         │ Integrity       │   │
                         └────────┬────────┘   │
                                  │            │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Check Sprint    │    │ Check Dependency│    │ Check Progress  │
│ References      │    │ References      │    │ Counters        │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                         ┌──────▼──────┐
                         │ 5. Circular │
                         │ Dependency  │
                         │ Detection   │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │ 6. Generate │
                         │ Report      │
                         └──────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              │ Issues?         │ No issues       │
              ▼                 ▼                 │
    ┌─────────────────┐  ┌─────────────────┐     │
    │ 7a. Auto-Repair │  │ 7b. Return OK   │     │
    │ (if safe)       │  │                 │     │
    └────────┬────────┘  └─────────────────┘     │
             │                                   │
             ▼                                   │
    ┌─────────────────┐                         │
    │ 8. Report       │                         │
    │ Remaining Issues│◄────────────────────────┘
    └─────────────────┘
```

### 7. Remote Consistency Strategy

| Scenario | Validation | Conflict Resolution | Consistency Model |
|----------|------------|---------------------|-------------------|
| Concurrent task completion | Re-validate on sync | Last-write-wins with timestamp | Eventual |
| Progress counter drift | Recompute from children | Server-computed truth | Strong |
| Orphaned task created | Validate before accept | Reject or create missing parent | Strong |
| Circular dependency introduced | DFS on merge | Reject conflicting change | Strong |
| Schema version mismatch | Compare versions | Run migrations | Strong |
| Stale cache detection | Compare checksums | Invalidate and refetch | Eventual |
| Split-brain scenario | Detect via timestamps | Manual merge required | Manual |

### 8. Offline Queue Strategy

| Change Type | Queue Format | Sync Order | Conflict Risk |
|-------------|--------------|------------|---------------|
| Task status change | `{entity_id, status, timestamp}` | FIFO by timestamp | Low (idempotent) |
| Progress update | `{entity_id, delta, timestamp}` | FIFO, then recompute | Medium |
| Dependency addition | `{source_id, target_id, type}` | FIFO, validate on sync | High (circular) |
| Entity creation | `{entity_type, data, parent_id}` | Parents before children | Medium |
| Entity deletion | `{entity_id, entity_type}` | Children before parents | High |
| Commit mapping | `{task_id, commit_sha, message}` | FIFO | Low |

**Offline Queue Implementation:**
```
┌─────────────────────────────────────────────────────────────┐
│                    OFFLINE QUEUE                            │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Change1 │→ │ Change2 │→ │ Change3 │→ │ Change4 │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│  On Reconnect:                                              │
│  1. Pull remote changes since last_sync_timestamp          │
│  2. Rebase local queue onto remote HEAD                    │
│  3. Validate each local change (reject if conflict)        │
│  4. Push valid changes to remote                           │
│  5. Report conflicts for manual resolution                  │
└─────────────────────────────────────────────────────────────┘
```

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Validation is pure logic | Reuse validators for remote | S | High |
| Auto-repair modifies files | Add remote repair endpoint | M | Medium |
| YAML-SQLite sync uses timestamps | Extend to YAML-Delta sync | M | Critical |
| DFS cycle detection is CPU-bound | Run on server for large graphs | S | Medium |
| Progress recompute is recursive | Implement as server-side stored procedure | M | High |
| Offline queue not implemented | Design queue schema for Delta Lake | L | Critical |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Validation rules table covers all 4 levels: PASS (Field, Entity, Cross-entity, Business)
- [x] Integrity checks table lists >= 4 check types: PASS (9 check types)
- [x] ASCII validation flow diagram present: PASS (8-step flowchart)
- [x] Remote consistency strategy addresses offline scenarios: PASS (7 scenarios + offline queue)

## References

- `vibey/operations/roadmap/validate.py:20-128` - RoadmapValidator class
- `vibey/operations/roadmap/advanced_validator.py:28-110` - Issue dataclasses
- `vibey/operations/roadmap/advanced_validator.py:116-200` - detect_circular_dependencies()
- `vibey/operations/roadmap/auto_repair.py:29-90` - repair_progress_counters()
- `vibey/operations/roadmap/auto_repair.py:93-173` - remove_broken_references()
- `vibey/operations/roadmap/auto_sync.py:10-56` - check_sync_needed()
- `vibey/operations/roadmap/auto_sync.py:93-143` - get_sync_status()
