# Dogfooding Bugs Track - Consolidation Analysis

**Date:** 2025-12-10
**Original Sprints:** 15
**Proposed Sprints:** 7

---

## Dependency Graph

```
Bug #6 (SQLAlchemy) ──────┐
                         ├──► ALL CLI COMMANDS BLOCKED
Bug #8 (blocked field) ──┘

Bug #3 (wrong path) ────┬──► Bug #14 (duplicate files)
                        │
                        └──► Bug #2 (track discovery)

Bug #10 (monolithic) ───┬──► Bug #2 (tracks not showing)
                        ├──► Bug #11 (db rebuild empty)
                        └──► Bug #12 (new tracks missing)

Bug #4 (validation) ────────► Track loading broken

Bug #5 (db sync) ───────────► Database stale
Bug #9 (is_dirty) ──────────► Pre-commit broken
Bug #11 (rebuild) ──────────► Database empty
```

---

## Root Cause Analysis

### Core Issue: ULID Migration Incomplete

The ULID flat directory migration was data-focused but didn't update:
1. CLI path resolution (Bug #3)
2. YAML loader to read ULID files (Bug #10)
3. Model validation for ULID IDs (Bug #4)
4. Database sync mechanisms (Bugs #5, #9, #11)

### Blocking Chain

1. **Level 0 (Blocks Everything):**
   - Bug #6: SQLAlchemy import → CLI won't start
   - Bug #8: blocked field → YAML won't load

2. **Level 1 (Blocks Data Access):**
   - Bug #3: Wrong path → Can't find roadmap.yaml
   - Bug #10: Monolithic read → Can't see ULID data
   - Bug #4: Validation → Tracks fail to load

3. **Level 2 (Blocks Features):**
   - Bug #2: Track discovery → Status incomplete
   - Bug #12: Sync missing → New tracks invisible
   - Bug #5, #9, #11: Database issues

4. **Level 3 (Enhancements):**
   - Bug #1: Progress updates
   - Bug #7: Validator patterns
   - Bug #13: Activity log format
   - Bug #15: Create commands

---

## Consolidation Groups

### Group A: CLI Startup Blockers
**Bugs:** #6, #8
**Theme:** Fix imports and schema to allow CLI to start
**Priority:** CRITICAL (P0)
**Must be first**

### Group B: ULID File System Adoption
**Bugs:** #3, #10, #2, #12, #4
**Theme:** Make CLI actually read from ULID files
**Priority:** CRITICAL (P0)
**Depends on:** Group A

### Group C: Database Synchronization
**Bugs:** #5, #9, #11
**Theme:** Fix SQLite backend to match YAML
**Priority:** HIGH (P1)
**Depends on:** Group B

### Group D: Progress System
**Bugs:** #1
**Theme:** Auto-update progress on completion
**Priority:** MEDIUM (P2)
**Depends on:** Group B

### Group E: Tooling Polish
**Bugs:** #7, #14
**Theme:** Validator improvements, cleanup verification
**Priority:** LOW (P3)
**Independent**

### Group F: CLI Create Commands
**Bugs:** #15
**Theme:** Add create track/sprint/task commands
**Priority:** HIGH (P1)
**Depends on:** Group B

### Group G: Activity Log Migration
**Bugs:** #13
**Theme:** Migrate audit-trail.yaml to JSONL
**Priority:** MEDIUM (P2)
**Independent**

---

## Proposed Sprint Structure

### Sprint 1: CLI Startup Unblock (CRITICAL)
**Bugs:** #6, #8
**Tasks:** 9 (4 + 5)
**Goal:** Make CLI commands executable

| Task | Description | Complexity |
|------|-------------|------------|
| 1-1 | Implement lazy imports in orm.py | Medium |
| 1-2 | Move ORM imports behind try/except | Low |
| 1-3 | Add SQLAlchemy to optional deps | Low |
| 1-4 | Test CLI without SQLAlchemy | Medium |
| 1-5 | Update load_roadmap for blocked field | Low |
| 1-6 | Update load_track for blocked field | Low |
| 1-7 | Update load_sprint for blocked field | Low |
| 1-8 | Update load_task for blocked field | Low |
| 1-9 | Add v1→v2 loading migration test | Medium |

### Sprint 2: ULID File Loading System (CRITICAL)
**Bugs:** #3, #10, #2, #12, #4
**Tasks:** 17 (3 + 5 + 3 + 4 + 4 - 2 duplicate)
**Goal:** CLI reads from ULID files correctly
**Depends on:** Sprint 1

| Task | Description | Complexity |
|------|-------------|------------|
| 2-1 | Update get_roadmap_path() for flat structure | Low |
| 2-2 | Update all path callers | Low |
| 2-3 | Add path resolution tests | Low |
| 2-4 | Design ULID file loading strategy | Medium |
| 2-5 | Update load_roadmap for ULID discovery | High |
| 2-6 | Implement lazy track loading | Medium |
| 2-7 | Update query.py for ULID loading | Medium |
| 2-8 | Add ULID loading integration tests | Medium |
| 2-9 | Debug FileSystemManager.list_tracks() | Low |
| 2-10 | Fix track filtering/discovery | Medium |
| 2-11 | Add track listing integration test | Low |
| 2-12 | Implement ULID→roadmap.yaml sync | Medium |
| 2-13 | Add CLI sync command | Medium |
| 2-14 | Add sync discrepancy validation | Medium |
| 2-15 | Update Track validation for ULIDs | Medium |
| 2-16 | Add backward compat for slug IDs | Low |
| 2-17 | Add ID format unit tests | Medium |

### Sprint 3: Database Synchronization (HIGH)
**Bugs:** #5, #9, #11
**Tasks:** 12 (4 + 4 + 4)
**Goal:** SQLite backend works with ULID system
**Depends on:** Sprint 2

| Task | Description | Complexity |
|------|-------------|------------|
| 3-1 | Add db sync to migration script | Medium |
| 3-2 | Implement auto db rebuild on YAML changes | High |
| 3-3 | Add CLI force resync command | Medium |
| 3-4 | Add YAML-DB sync integration test | Medium |
| 3-5 | Investigate is_dirty schema history | Low |
| 3-6 | Update pre-commit for current schema | Medium |
| 3-7 | Add database migration script | Medium |
| 3-8 | Test pre-commit with fresh db | Low |
| 3-9 | Update db_rebuild for ULID files | Medium |
| 3-10 | Update sql_loader for tracks/*.yaml | Medium |
| 3-11 | Add rebuild progress reporting | Low |
| 3-12 | Add rebuild integration test | Medium |

### Sprint 4: Progress Auto-Update (MEDIUM)
**Bugs:** #1
**Tasks:** 5
**Goal:** Progress propagates automatically
**Depends on:** Sprint 2

| Task | Description | Complexity |
|------|-------------|------------|
| 4-1 | Analyze current progress flow | Low |
| 4-2 | Implement auto-progression in update.py | Medium |
| 4-3 | Add post-completion parent update hook | Medium |
| 4-4 | Add progress propagation unit tests | Medium |
| 4-5 | Manual verification with test sprint | Low |

### Sprint 5: CLI Create Commands (HIGH)
**Bugs:** #15
**Tasks:** 6
**Goal:** CLI can create new roadmap objects
**Depends on:** Sprint 2

| Task | Description | Complexity |
|------|-------------|------------|
| 5-1 | Add create track CLI command | Medium |
| 5-2 | Add create sprint CLI command | Medium |
| 5-3 | Add create task CLI command | Medium |
| 5-4 | Update create-from-plan for ULID | High |
| 5-5 | Create ULIDManager utility | Low |
| 5-6 | Add create command integration tests | Medium |

### Sprint 6: Tooling Polish (LOW)
**Bugs:** #7, #14
**Tasks:** 6 (3 + 3)
**Goal:** Clean up validator and verify fixes
**Independent**

| Task | Description | Complexity |
|------|-------------|------------|
| 6-1 | Add VALIDATION_EXCLUDE_PATTERNS | Low |
| 6-2 | Update validator to skip excludes | Low |
| 6-3 | Add exclusion pattern tests | Low |
| 6-4 | Verify single roadmap.yaml location | Low |
| 6-5 | Add startup duplicate warning | Low |
| 6-6 | Document canonical location | Low |

### Sprint 7: Activity Log Migration (MEDIUM)
**Bugs:** #13
**Tasks:** 6
**Goal:** Migrate to JSONL activity log format
**Independent**

| Task | Description | Complexity |
|------|-------------|------------|
| 7-1 | Create activity_log/ directory | Low |
| 7-2 | Write JSONL writer for events | Medium |
| 7-3 | Write JSONL reader for queries | Medium |
| 7-4 | Migrate audit-trail.yaml to JSONL | Medium |
| 7-5 | Update activity log consumers | Medium |
| 7-6 | Add JSONL activity log tests | Medium |

---

## Summary

| Sprint | Theme | Bugs | Tasks | Priority | Depends On |
|--------|-------|------|-------|----------|------------|
| 1 | CLI Startup Unblock | #6, #8 | 9 | CRITICAL | - |
| 2 | ULID File Loading | #3, #10, #2, #12, #4 | 17 | CRITICAL | Sprint 1 |
| 3 | Database Sync | #5, #9, #11 | 12 | HIGH | Sprint 2 |
| 4 | Progress Auto-Update | #1 | 5 | MEDIUM | Sprint 2 |
| 5 | CLI Create Commands | #15 | 6 | HIGH | Sprint 2 |
| 6 | Tooling Polish | #7, #14 | 6 | LOW | - |
| 7 | Activity Log Migration | #13 | 6 | MEDIUM | - |

**Total: 7 sprints, 61 tasks** (vs original 15 sprints, 63 tasks)

---

## Execution Order

```
Sprint 1 (CLI Startup)
    │
    ▼
Sprint 2 (ULID Loading)
    │
    ├───► Sprint 3 (Database Sync)
    │
    ├───► Sprint 4 (Progress Update)
    │
    └───► Sprint 5 (Create Commands)

Sprint 6 (Tooling) ─── Can run anytime
Sprint 7 (Activity Log) ─── Can run anytime
```

Sprints 6 and 7 are independent and can be executed in parallel with others.
