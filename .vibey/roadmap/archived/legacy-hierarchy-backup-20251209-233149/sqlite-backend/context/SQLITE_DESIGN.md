# SQLite Backend Design Document

**Track:** sqlite-backend
**Sprint:** sqlite-backend-0 (Design & Schema)
**Version:** 1.0.0
**Date:** 2025-11-26
**Status:** Ready for Review

---

## Executive Summary

This document describes the design for replacing YAML as the working state for the Vibey roadmap system with SQLite. The database becomes the **single source of truth** for all roadmap operations, while YAML files remain as **read-only artifacts** for git versioning.

### Key Benefits

1. **Automatic Consistency** - Computed views eliminate manual counter updates
2. **Referential Integrity** - Foreign keys prevent orphan tasks and invalid references
3. **Atomic Operations** - Single transactions for complex multi-entity updates
4. **Fast Queries** - SQL queries vs parsing hundreds of YAML files
5. **Validation Enforcement** - Triggers prevent invalid state transitions

### Architecture Overview

**Source of Truth Hierarchy:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  REMOTE YAML (git repo)  =  Ultimate source of truth                   │
│                              Shared state across all collaborators      │
├─────────────────────────────────────────────────────────────────────────┤
│  LOCAL SQLite DB         =  Working state for current session          │
│                              Derived from YAML, synced back on commit   │
├─────────────────────────────────────────────────────────────────────────┤
│  Conflict Resolution     =  Git's merge process                        │
│                              After DB→YAML dump, standard git workflow  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WRITE PATH                                       │
│                                                                          │
│   vibey CLI ──▶ SQLite DB ──▶ (pre-commit) ──▶ YAML files ──▶ git push │
│                    │                                                     │
│              Session State                                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         READ PATH                                        │
│                                                                          │
│   git pull ──▶ YAML files ──▶ (post-merge) ──▶ SQLite DB (rebuilt)      │
│                     │                                                    │
│           Authoritative State                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Problem Statement

### Current State

The Vibey roadmap system stores all state in YAML files with a hierarchical structure:
- `roadmap.yaml` - Root with aggregated metrics
- `track.yaml` - Per-track progress and metadata
- `sprint.yaml` - Per-sprint progress and task summaries
- `task.yaml` - Individual task details

### Problems

1. **24 Computed Fields** require manual synchronization:
   - Progress counters (tasks_completed, completion_percent) at sprint, track, and roadmap levels
   - Blocked flags derived from blocked_by arrays
   - Recently fixed 262 validation errors caused by counter drift

2. **Denormalized Data** causes inconsistency:
   - Track summaries duplicated in roadmap.yaml
   - Sprint summaries duplicated in track.yaml
   - Task summaries duplicated in sprint.yaml

3. **No Referential Integrity**:
   - Orphan tasks can reference non-existent sprints
   - Blocking relationships can reference deleted entities
   - No enforcement of valid status transitions

4. **Performance**:
   - Queries require parsing all YAML files
   - No indexing capability
   - O(n) lookups for any search

### Root Cause

YAML is a serialization format, not a database. Using it as working state requires building database-like features (aggregations, integrity checks) in application code.

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              ROADMAP                                     │
│  id, name, version, status, timestamps                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               TRACK                                      │
│  id, roadmap_id(FK), name, status, priority, timestamps                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              SPRINT                                      │
│  id, track_id(FK), roadmap_id(FK), name, status, timestamps             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                               TASK                                       │
│  id, sprint_id(FK), track_id(FK), roadmap_id(FK)                        │
│  task_type, title, description, status, timestamps                      │
│  assigned_agent, priority, complexity, gate_info                        │
└─────────────────────────────────────────────────────────────────────────┘


Polymorphic Tables (owner_type + owner_id):
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  quality_gates     │  │   deliverables     │  │     commits        │
│  (track/sprint)    │  │  (track/sprint/    │  │  (track/sprint/    │
└────────────────────┘  │   task)            │  │   task)            │
                        └────────────────────┘  └────────────────────┘

Relationship Tables:
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  entity_blocks     │  │ entity_blocked_by  │  │ entity_depends_on  │
│  (blocker blocks   │  │ (blocked waits for │  │ (soft dependency   │
│   blocked)         │  │  blocker)          │  │  ordering)         │
└────────────────────┘  └────────────────────┘  └────────────────────┘
```

### Table Summary

| Category | Tables | Count |
|----------|--------|-------|
| Core Entities | roadmaps, tracks, sprints, tasks | 4 |
| Relationships | entity_blocks, entity_blocked_by, entity_depends_on, external_dependencies | 4 |
| Quality & Gates | quality_gates (track/sprint), development_gates | 2 |
| Supporting Data | deliverables, entity_deliverables, commits, entity_commits, assigned_agents, standards, strategic_value | 7 |
| Roadmap-Level | version_history, activity_log | 2 |
| Summaries | track_summaries, sprint_summaries, task_summaries | 3 |
| Sync & Validation | yaml_checksums, database_state, sync_conflicts | 3 |
| **Total** | | **25** |

**Note:** Deliverables and commits use junction tables (entity_deliverables, entity_commits) to support many-to-many relationships (e.g., one commit can be linked to multiple tasks).

### 1:1 YAML Mapping

Every YAML field maps to a database column or table:

| YAML Location | SQLite Table |
|---------------|--------------|
| roadmap.yaml (root) | roadmaps |
| roadmap.yaml → tracks[] | track_summaries |
| roadmap.yaml → activity_log[] | activity_log |
| track.yaml (root) | tracks |
| track.yaml → sprints[] | sprint_summaries |
| track.yaml → quality_gates[] | quality_gates (owner_type='track') |
| sprint.yaml → quality_gates[] | quality_gates (owner_type='sprint') |
| track.yaml → blocks[] | entity_blocks (blocker_type='track') |
| sprint.yaml (root) | sprints |
| sprint.yaml → tasks[] | task_summaries |
| task.yaml (root) | tasks |
| task.yaml → deliverables[] | deliverables (owner_type='task') |

Full schema DDL available in `002-sqlite-schema-design.md`.

---

## Computed Views

Views replace all 24 manually-computed fields.

### Key Views

| View | Purpose | Replaces |
|------|---------|----------|
| `v_sprint_progress` | Sprint-level metrics | 9 progress fields in sprint.yaml |
| `v_track_progress` | Track-level metrics | 5 progress fields in track.yaml |
| `v_roadmap_progress` | Roadmap-level metrics | 7 progress fields in roadmap.yaml |
| `v_blocked_entities` | All blocked items with blockers | blocked flag computation |
| `v_unblocked_tasks` | Tasks ready to start | Query optimization |
| `v_dependency_chain` | Transitive dependency graph | Cycle detection |
| `v_quality_gate_summary` | Gate status by entity | Quality reporting |

### Example: Sprint Progress View

```sql
CREATE VIEW v_sprint_progress AS
SELECT
    s.id AS sprint_id,
    COUNT(t.id) AS tasks_total,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS tasks_completed,
    ROUND(
        (COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0) /
        NULLIF(COUNT(t.id), 0)
    ) AS completion_percent
FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY s.id;
```

Full view definitions in `003-computed-views-design.md`.

---

## Triggers

40 triggers handle automatic state management.

### Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Timestamp | 9 | Auto-set created, started, completed, updated |
| Blocked Flag | 6 | Keep blocked in sync with blocked_by entries |
| Auto-Completion | 5 | Clear blockers when entities complete, auto-start parents |
| Summary Tables | 11 | Keep denormalized summaries in sync |
| Activity Log | 6 | Log significant events for audit trail |
| Validation | 3 | Prevent invalid state (completing blocked tasks) |

### Example: Prevent Completing Blocked Task

```sql
CREATE TRIGGER trg_prevent_complete_blocked_task
BEFORE UPDATE OF status ON tasks
WHEN NEW.status = 'completed'
  AND EXISTS (
    SELECT 1 FROM entity_blocked_by eb
    JOIN tasks t ON t.id = eb.blocker_id AND eb.blocker_type = 'task'
    WHERE eb.blocked_type = 'task'
      AND eb.blocked_id = NEW.id
      AND t.status != 'completed'
  )
BEGIN
    SELECT RAISE(ABORT, 'Cannot complete task: unresolved blockers exist');
END;
```

Full trigger definitions in `004-triggers-design.md`.

---

## YAML Synchronization

### Architecture Decision

- **SQLite = Source of Truth** (all writes)
- **YAML = Read-only Artifact** (git versioning only)

This eliminates bidirectional sync complexity.

### Workflows

**Normal Work:**
```
vibey CLI → SQLite DB → (pre-commit) → YAML dump → git commit
```

**After Git Pull:**
```
git pull → YAML files → (post-merge) → SQLite rebuild
```

### Deterministic Output

YAML dumps must be 100% deterministic:
- Fixed key ordering (defined per entity type)
- Sorted arrays (by ID or natural key)
- Consistent timestamp format (ISO 8601)
- Explicit null for optional fields

### Git Hooks

| Hook | Trigger | Action |
|------|---------|--------|
| pre-commit | Before commit | `vibey roadmap dump` |
| post-merge | After pull/merge | `vibey roadmap rebuild` |
| post-checkout | After branch switch | `vibey roadmap rebuild` |

Full sync strategy in `005-yaml-sync-strategy.md`.

---

## CLI Commands

### New Commands

| Command | Purpose |
|---------|---------|
| `vibey roadmap dump` | Export DB → YAML |
| `vibey roadmap rebuild` | Import YAML → DB |
| `vibey roadmap status` | Show sync status |
| `vibey roadmap db init` | Initialize database |
| `vibey roadmap db backup` | Backup database |

### Existing Commands

All existing `vibey roadmap` commands will operate on SQLite:
- `vibey roadmap status` → Query views
- `vibey roadmap update-task` → SQL UPDATE
- `vibey roadmap add-task` → SQL INSERT
- `vibey roadmap query` → SQL SELECT

---

## Migration Plan

### Phase 1: Implementation (Sprint 1-2)

1. Create database module (`vibey/roadmap/database/`)
2. Implement schema creation and migrations
3. Implement CRUD operations
4. Update CLI commands to use database

### Phase 2: Integration (Sprint 3)

1. Implement dump/rebuild commands
2. Add git hook integration
3. Update existing CLI commands
4. Test roundtrip (DB → YAML → DB)

### Phase 3: Validation (Sprint 4)

1. Build computed DB from task files
2. Build declared DB from YAML counters
3. Compare and generate audit report
4. Remediate until zero discrepancies

### Migration Steps for Existing Users

```bash
# 1. Backup current YAML files
git stash

# 2. Initialize database from existing YAML
vibey roadmap db init

# 3. Verify data integrity
vibey roadmap validate

# 4. Install git hooks
vibey roadmap hooks install

# 5. Normal workflow continues
```

---

## Performance Considerations

### Indexing Strategy

```sql
-- Primary lookups
CREATE INDEX idx_tasks_sprint ON tasks(sprint_id);
CREATE INDEX idx_sprints_track ON sprints(track_id);
CREATE INDEX idx_tracks_roadmap ON tracks(roadmap_id);

-- Status queries
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_sprints_status ON sprints(status);

-- Blocking queries
CREATE INDEX idx_blocked_by ON entity_blocked_by(blocked_type, blocked_id);
```

### Expected Performance

| Operation | YAML | SQLite |
|-----------|------|--------|
| Query all blocked tasks | O(n) file parse | O(log n) index lookup |
| Calculate sprint progress | O(n) task parse | Single view query |
| Find task by ID | O(n) directory scan | O(1) primary key |
| Add new task | Write file | INSERT + triggers |

### Concurrency

- Use WAL mode for better read concurrency
- Short transactions for writes
- Single writer, multiple readers

---

## Security Considerations

### Integration with git-integration-5

The SQLite backend complements the roadmap integrity protection track:

| Concern | SQLite Backend | git-integration-5 |
|---------|----------------|-------------------|
| Data Consistency | ✅ Computed views, triggers | N/A |
| Referential Integrity | ✅ Foreign keys | N/A |
| Unauthorized Changes | N/A | ✅ Signing/verification |
| --no-verify Bypass | N/A | ✅ Server-side enforcement |

git-integration-5 is blocked on sqlite-backend because:
1. SQLite can serve as the manifest for integrity verification
2. Checksums can be computed from deterministic YAML dumps
3. Activity log provides audit trail for signing

### Database Security

- Database file permissions (0600)
- No sensitive data stored (roadmap is project metadata)
- Backups encrypted if needed

---

## Testing Strategy

### Unit Tests

- Schema creation
- CRUD operations
- View computations
- Trigger behavior

### Integration Tests

- CLI commands with database
- Git hook integration
- Multi-entity transactions

### Roundtrip Tests

```python
def test_yaml_roundtrip():
    """DB → YAML → DB produces identical state."""
    create_test_entities()
    dump_db_to_yaml()
    clear_db()
    rebuild_db_from_yaml()
    assert db_state == original_state
```

### Performance Tests

- Query latency benchmarks
- Bulk import timing
- Concurrent access patterns

---

## Appendix: Design Documents

| Document | Content |
|----------|---------|
| `001-data-model-analysis.md` | Current YAML schema analysis |
| `002-sqlite-schema-design.md` | Complete DDL for 20 tables |
| `003-computed-views-design.md` | 13 view definitions |
| `004-triggers-design.md` | 40 trigger definitions |
| `005-yaml-sync-strategy.md` | Dump/rebuild strategy |

---

## Approval

**Design Review Status:** Ready for Review

**Reviewers:**
- [ ] Architecture review
- [ ] Implementation feasibility
- [ ] Performance concerns
- [ ] Security review

**Approval Date:** _Pending_

---

**Document Version:** 1.0.0
**Author:** Claude Code (architecture-agent)
**Last Updated:** 2025-11-26
