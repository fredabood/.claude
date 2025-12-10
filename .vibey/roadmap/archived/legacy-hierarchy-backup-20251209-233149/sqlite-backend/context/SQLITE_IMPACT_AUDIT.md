# SQLite Backend Impact Audit

**Track:** sqlite-backend
**Sprint:** sqlite-backend-1 (Core Implementation)
**Date:** 2025-11-26
**Purpose:** Comprehensive codebase audit identifying all areas impacted by SQLite architecture

---

## Executive Summary

The SQLite backend migration will touch **~15,000 lines of code** across **50+ files** in 6 major subsystems. The primary integration point is the **serialization layer** (`vibey/roadmap/serialization/`), which can be extended to support SQL operations alongside YAML.

### Impact Overview

| Subsystem | Files | Lines | Impact Level | Migration Strategy |
|-----------|-------|-------|--------------|-------------------|
| Models | 6 | ~2,000 | Low | No changes needed |
| Serialization | 2 | ~1,500 | **HIGH** | Add SQL variants |
| Operations | 17 | ~7,910 | Medium | Use new serialization |
| CLI | 8 | ~3,000 | Low | No changes needed |
| MCP Server | 10 | ~2,500 | Low | No changes needed |
| Git Hooks | 6 | ~1,500 | Medium | Add DB validation |

---

## 1. Models Layer (NO CHANGES NEEDED)

**Location:** `vibey/roadmap/models/`

The models are **pure dataclasses** that represent roadmap entities. They are already well-structured and map directly to SQLite tables.

### Files
| File | Lines | Classes | Status |
|------|-------|---------|--------|
| `common.py` | ~280 | 11 enums + DependencyStatus | ✅ Ready |
| `task.py` | ~427 | Task + 8 supporting classes | ✅ Ready |
| `sprint.py` | ~299 | Sprint + 5 supporting classes | ✅ Ready |
| `track.py` | ~257 | Track + 6 supporting classes | ✅ Ready |
| `roadmap.py` | ~260 | Roadmap + 7 supporting classes | ✅ Ready |
| `standard.py` | ~277 | Standard + 2 supporting classes | ✅ Ready |

### Why No Changes
- Models are **already normalized** (1:1 with designed SQLite tables)
- Field names match schema design
- Validation in `__post_init__` methods transfers directly to SQLite constraints
- Enums can be stored as TEXT with CHECK constraints

---

## 2. Serialization Layer (PRIMARY MIGRATION TARGET)

**Location:** `vibey/roadmap/serialization/`

This is the **single source of truth** for all YAML I/O. The SQLite implementation should be added here as an alternative backend.

### Current Files
| File | Lines | Functions | Purpose |
|------|-------|-----------|---------|
| `yaml_loader.py` | ~1,089 | 5 | Load YAML → Model objects |
| `yaml_dumper.py` | ~400+ | 4 | Save Model objects → YAML |

### Migration Strategy

**Option A: Parallel Implementation (Recommended)**
```python
# New files to add
vibey/roadmap/serialization/
├── yaml_loader.py      # Existing
├── yaml_dumper.py      # Existing
├── sql_loader.py       # NEW: Load from SQLite
├── sql_dumper.py       # NEW: Save to SQLite
└── backend.py          # NEW: Backend abstraction
```

**Option B: Abstract Backend**
```python
class RoadmapBackend(Protocol):
    def load_roadmap(self) -> Roadmap: ...
    def load_track(self, track_id: str) -> Track: ...
    def load_sprint(self, sprint_id: str) -> Sprint: ...
    def load_task(self, task_id: str) -> Task: ...
    def save_roadmap(self, roadmap: Roadmap): ...
    # etc.

class YAMLBackend(RoadmapBackend): ...  # Existing logic
class SQLiteBackend(RoadmapBackend): ...  # New implementation
```

### Key Functions to Implement
| Function | YAML Current | SQLite Equivalent |
|----------|--------------|-------------------|
| `load_roadmap()` | Parse roadmap.yaml | `SELECT * FROM roadmaps` |
| `load_track()` | Parse track.yaml | `SELECT * FROM tracks WHERE id = ?` |
| `load_sprint()` | Parse sprint.yaml | `SELECT * FROM sprints WHERE id = ?` |
| `load_tasks()` | Parse task files | `SELECT * FROM tasks WHERE sprint_id = ?` |
| `save_roadmap()` | Write roadmap.yaml | `INSERT/UPDATE roadmaps` |
| `save_track()` | Write track.yaml | `INSERT/UPDATE tracks` |
| `save_sprint()` | Write sprint.yaml | `INSERT/UPDATE sprints` |
| `save_tasks()` | Write task files | `INSERT/UPDATE tasks` |

---

## 3. Operations Layer (MEDIUM IMPACT)

**Location:** `vibey/operations/roadmap/`

Operations call serialization functions. Once serialization supports SQLite, operations automatically benefit.

### Files by Category

#### Query Operations (Read-Heavy)
| File | Lines | Impact | Notes |
|------|-------|--------|-------|
| `query.py` | 437 | Medium | Replace cascading file reads with SQL JOINs |
| `context.py` | 463 | Medium | BFS dependency traversal → recursive CTE |

**Performance Gains:**
- Current: 5+ YAML reads per query
- With SQLite: 1-2 SQL queries

#### Update Operations (Write-Heavy)
| File | Lines | Impact | Notes |
|------|-------|--------|-------|
| `update.py` | 1,086 | **HIGH** | Cascading progress updates → triggers |
| `add_commit.py` | 250 | Low | Single task update |

**Current Pain Point:** `complete_task()` triggers 4+ file writes:
1. Task file (status update)
2. Sprint file (progress recalc)
3. Track file (progress recalc)
4. Roadmap file (progress recalc)

**With SQLite:** Single `UPDATE tasks SET status = 'completed'` + triggers handle cascades.

#### Validation Operations
| File | Lines | Impact | Notes |
|------|-------|--------|-------|
| `validate.py` | 331 | Low | Schema validation moves to DB constraints |
| `advanced_validator.py` | 603 | Medium | Graph queries become SQL |
| `auto_repair.py` | 237 | Medium | Progress repair → view comparison |

**Validation Improvements:**
- Circular dependencies: Recursive CTE
- Orphaned tasks: FK constraint violations
- Progress mismatches: Compare computed views vs stored values

#### Maintenance Operations
| File | Lines | Impact | Notes |
|------|-------|--------|-------|
| `safe_yaml_editor.py` | 775 | Medium | Transaction safety built into SQLite |
| `checkpoint_verifier.py` | 384 | Medium | Checksums can include DB state |
| `audit_trail.py` | 400 | Low | Activity log → activity_log table |
| `commit_mapper.py` | 733 | Low | Link commits to tasks |
| `summarize.py` | 534 | Low | Store summaries in DB |

### Operations Summary
```
Total Operations Files: 17
Total Lines: ~7,910
High Impact: 2 files (update.py, safe_yaml_editor.py)
Medium Impact: 8 files
Low Impact: 7 files
```

---

## 4. CLI Commands (LOW IMPACT)

**Location:** `vibey/cli/`

CLI commands call operations. No direct YAML manipulation.

### Files
| File | Lines | Purpose | Impact |
|------|-------|---------|--------|
| `main.py` | ~800 | Click command definitions | None |
| `commands.py` | ~600 | Command implementations | None |
| `roadmap_commands/*.py` | ~1,600 | Roadmap subcommands | None |

### New Commands to Add
| Command | Purpose |
|---------|---------|
| `vibey roadmap db init` | Initialize SQLite database |
| `vibey roadmap db rebuild` | Rebuild DB from YAML |
| `vibey roadmap dump` | Export DB to YAML |
| `vibey roadmap validate` | Validate DB vs YAML |

### CLI Helpers (May Need Updates)
| File | Lines | Notes |
|------|-------|-------|
| `roadmap_lib/filesystem.py` | 337 | Add DB path methods |
| `roadmap_lib/cache.py` | 600+ | May be replaced by SQLite |

---

## 5. MCP Server (LOW IMPACT)

**Location:** `vibey/mcp/`

MCP tools delegate to operations via `RoadmapAdapter`. No direct YAML access.

### Files
| File | Lines | Purpose | Impact |
|------|-------|---------|--------|
| `server.py` | 530 | FastMCP server | None |
| `tools/task_tools.py` | 340 | Task operations | None |
| `tools/sprint_tools.py` | 382 | Sprint operations | None |
| `tools/query_tools.py` | 414 | Query operations | None |
| `adapters/roadmap_adapter.py` | ~200 | Delegates to operations | None |

### Architecture Preserved
```
MCP Server → RoadmapAdapter → operations/roadmap → serialization → SQLite/YAML
```

No changes needed to MCP layer.

---

## 6. Git Hooks (MEDIUM IMPACT)

**Location:** `vibey/operations/git/hooks/`

Hooks validate YAML before commits. Need to add DB validation.

### Current Hook Flow
```
Pre-commit:
1. Check for YAML syntax errors
2. Validate YAML schema
3. Check for manual YAML edits (warn/block)

Post-commit:
1. Extract task references from commit message
2. Update task status in YAML
```

### SQLite Integration Points

#### Pre-commit Hook Updates
```python
# Current: YAML validation only
def pre_commit_validate():
    validate_yaml_files()

# New: Add DB consistency check
def pre_commit_validate():
    validate_yaml_files()
    if db_exists():
        check_db_yaml_sync()  # Warn if out of sync
```

#### New Hook: Pre-commit DB Dump
```python
# Automatically dump DB to YAML before commit
def pre_commit_dump():
    if db_is_dirty():
        run_db_dump()  # vibey roadmap dump
```

#### Post-merge Hook
```python
# Rebuild DB from YAML after pull
def post_merge_rebuild():
    run_db_rebuild()  # vibey roadmap db rebuild
```

### Files to Update
| File | Lines | Changes |
|------|-------|---------|
| `pre_commit.py` | ~200 | Add DB sync check |
| `hooks/installer.py` | ~80 | Add post-merge hook |

---

## 7. Test Suite (MEDIUM IMPACT)

**Location:** `tests/`

Tests need SQLite variants and roundtrip testing.

### Current Test Files
| File | Lines | Purpose |
|------|-------|---------|
| `test_roadmap_models.py` | ~500 | Model validation |
| `test_yaml_serialization.py` | ~400 | YAML load/save |
| `test_roadmap_operations.py` | ~600 | Operation logic |
| `test_git_hooks.py` | 549 | Hook validation |

### New Tests Needed
| Test File | Purpose |
|-----------|---------|
| `test_sql_serialization.py` | SQLite load/save |
| `test_yaml_sql_roundtrip.py` | DB → YAML → DB consistency |
| `test_triggers.py` | Trigger behavior |
| `test_computed_views.py` | View accuracy |

---

## 8. Database Module Structure

**Proposed Location:** `vibey/roadmap/database/`

### Recommended Structure
```
vibey/roadmap/database/
├── __init__.py           # Module exports
├── connection.py         # Connection management, WAL mode
├── schema.py             # CREATE TABLE statements (from design)
├── migrations.py         # Schema versioning
├── crud/
│   ├── __init__.py
│   ├── roadmap.py        # Roadmap CRUD
│   ├── track.py          # Track CRUD
│   ├── sprint.py         # Sprint CRUD
│   └── task.py           # Task CRUD
├── views.py              # Computed views (from design)
├── triggers.py           # Trigger definitions (from design)
├── sync/
│   ├── __init__.py
│   ├── dump.py           # DB → YAML
│   ├── rebuild.py        # YAML → DB
│   └── checksum.py       # File change detection
└── validation.py         # DB-based validation
```

---

## 9. Integration Order (Recommended)

### Phase 1: Core Database (Sprint 1)
1. Create `database/` module structure
2. Implement schema creation (`schema.py`)
3. Implement connection management (`connection.py`)
4. Implement basic CRUD operations
5. Unit tests for database layer

### Phase 2: Serialization Bridge (Sprint 1-2)
1. Create `sql_loader.py` in serialization
2. Create `sql_dumper.py` in serialization
3. Add backend abstraction
4. Roundtrip tests

### Phase 3: CLI Integration (Sprint 2)
1. Add `vibey roadmap db init`
2. Add `vibey roadmap db rebuild`
3. Add `vibey roadmap dump`
4. Add `vibey roadmap validate`

### Phase 4: Hook Integration (Sprint 3)
1. Update pre-commit for DB awareness
2. Add post-merge hook
3. Implement dirty detection
4. Conflict resolution

### Phase 5: Full Migration (Sprint 4)
1. Update operations to prefer SQLite
2. Add computed views
3. Implement triggers
4. Performance benchmarking

---

## 10. Risk Assessment

### Low Risk
- Models: Already normalized, no changes needed
- CLI: Calls operations, abstracted from storage
- MCP: Calls operations via adapter

### Medium Risk
- Operations: Need to update import paths
- Git Hooks: New validation logic
- Tests: Need comprehensive roundtrip testing

### High Risk
- Serialization: Core migration point, must be backward compatible
- Update cascades: Trigger logic must match current behavior exactly

---

## 11. Backward Compatibility

### Must Maintain
1. **YAML as version control format** - Human-readable diffs in git
2. **CLI command interface** - No breaking changes to user commands
3. **MCP tool signatures** - No breaking changes to AI integrations
4. **Git hook behavior** - Validation still works

### Migration Path
```
Phase 1: SQLite optional (YAML primary)
Phase 2: SQLite default, YAML on commit
Phase 3: YAML deprecated (SQLite only + git hooks dump)
```

---

## 12. Files Changed Summary

### New Files (~15 files)
```
vibey/roadmap/database/
├── __init__.py
├── connection.py
├── schema.py
├── migrations.py
├── crud/__init__.py
├── crud/roadmap.py
├── crud/track.py
├── crud/sprint.py
├── crud/task.py
├── views.py
├── triggers.py
├── sync/__init__.py
├── sync/dump.py
├── sync/rebuild.py
└── sync/checksum.py

vibey/roadmap/serialization/
├── sql_loader.py
├── sql_dumper.py
└── backend.py

vibey/cli/roadmap_commands/
└── db.py  # New subcommand group
```

### Modified Files (~10 files)
```
vibey/roadmap/serialization/__init__.py  # Export new functions
vibey/operations/roadmap/update.py       # Use SQLite for cascades
vibey/operations/roadmap/query.py        # Use SQLite for queries
vibey/cli/roadmap_lib/filesystem.py      # Add DB path methods
vibey/operations/git/hooks/pre_commit.py # Add DB validation
vibey/operations/git/hooks/installer.py  # Add post-merge hook
```

### New Test Files (~5 files)
```
tests/test_sql_serialization.py
tests/test_yaml_sql_roundtrip.py
tests/test_database_triggers.py
tests/test_computed_views.py
tests/test_sync_operations.py
```

---

## Conclusion

The SQLite migration is **well-scoped** due to the existing architecture:

1. **Clean separation of concerns** - Models, serialization, operations, CLI, MCP are decoupled
2. **Single serialization point** - All YAML I/O goes through `vibey/roadmap/serialization/`
3. **Operations abstraction** - CLI and MCP don't know about storage format
4. **Well-designed schema** - Sprint 0 design maps directly to existing models

**Primary work:**
- ~15 new files in `database/` module
- ~3 new files in `serialization/`
- ~10 modified files across operations and hooks
- ~5 new test files

**Expected outcome:**
- 10-50x performance improvement for cascading updates
- Automatic progress aggregation via triggers
- Referential integrity via foreign keys
- YAML remains for git versioning (deterministic dump)
