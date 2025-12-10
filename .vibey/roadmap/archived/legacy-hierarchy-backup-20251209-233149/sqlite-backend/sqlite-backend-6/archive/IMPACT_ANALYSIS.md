# Sprint 6a Impact Analysis: Unified Ticket Architecture

## Executive Summary

The unified ticket architecture introduces hierarchy attributes (`is_parent`, `is_child`, `is_ultimate_parent`, `is_ultimate_child`, `is_intermediate`) and smart accessors that fundamentally change how the vibey roadmap system accesses commits, deliverables, standards, and progress data.

**Impact Severity**: HIGH
**Files Affected**: 50+ files across 5 major subsystems
**Estimated Migration Effort**: 280-380 hours (7-9.5 weeks)

---

## 1. Current Model Inventory

### Existing Models (vibey/roadmap/models/)

| Model | File | Key Fields | Line Count |
|-------|------|------------|------------|
| Roadmap | roadmap.py | version, progress, tracks, standards, activity_log | ~260 |
| Track | track.py | roadmap_id, sprints, quality_gates, strategic_value | ~257 |
| Sprint | sprint.py | track_id, tasks, development_gates, success_criteria | ~313 |
| Task | task.py | sprint_id, commits, deliverables, gate_info | ~427 |
| Standard | standard.py | type, enforcement, overrides | ~277 |
| Common | common.py | Status, Priority, TaskType, etc. (enums) | ~150 |

### Commit Type Variations (Current)

| Type | Location | Purpose |
|------|----------|---------|
| `GitCommit` | task.py | Individual git commits on tasks |
| `TaskCompletionCommit` | sprint.py | Commits that completed tasks |
| `SprintCompletionCommit` | track.py | Commits that completed sprints |

---

## 2. Breaking Changes

### Category 1: Field Renaming (CRITICAL)

All direct field access patterns must change:

| Current | New (Local) | New (Smart Accessor) |
|---------|-------------|---------------------|
| `task.commits` | `task.commits_local` | `task.commits` → returns local |
| `sprint.commits` | `sprint.commits_local` | `sprint.commits` → aggregated |
| `track.commits` | `track.commits_local` | `track.commits` → aggregated |
| `task.deliverables` | `task.deliverables_local` | `task.deliverables` → returns local |
| `sprint.deliverables` | `sprint.deliverables_local` | `sprint.deliverables` → aggregated |
| `roadmap.standards` | `roadmap.standards_local` | `roadmap.standards` → returns local |
| `track.standards` | `track.standards_local` | `track.standards` → effective |
| `sprint.standards` | `sprint.standards_local` | `sprint.standards` → effective |

### Category 2: Hierarchy Attributes (NEW)

All ticket types must implement:

```python
# Computed from local state (L1)
is_parent: bool           # len(children) > 0
is_child: bool            # parent_id is not None
is_ultimate_parent: bool  # is_parent and not is_child
is_ultimate_child: bool   # is_child and not is_parent
is_intermediate: bool     # is_parent and is_child

# Stored references (L2)
parent_id: Optional[str]
children: list[Ticket]    # lazy loaded
```

### Category 3: Smart Accessor Behavior

| Ticket Type | commits | standards | progress |
|-------------|---------|-----------|----------|
| Roadmap | aggregated | local | computed |
| Track | aggregated | effective | computed |
| Sprint | aggregated | effective | computed |
| Task | **local** | effective | **None** |

### Category 4: Commit Type Unification

Three commit types → single unified `GitCommit`:

```python
# NEW: Single commit type with context
class GitCommit:
    sha: str
    message: str
    author: Optional[str]
    timestamp: Optional[datetime]
    files_changed: Optional[int]
    # Context preserved via relationship, not type
```

### Category 5: Database Schema Changes

New columns required on all entity tables:

```sql
ALTER TABLE tasks ADD COLUMN parent_id TEXT;
ALTER TABLE tasks ADD COLUMN is_parent BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN is_child BOOLEAN DEFAULT TRUE;
ALTER TABLE tasks ADD COLUMN is_ultimate_child BOOLEAN DEFAULT TRUE;
-- Similar for sprints, tracks, roadmaps
```

---

## 3. Affected Files Inventory

### Serialization Layer (10 files) - CRITICAL

| File | Impact | Changes Required |
|------|--------|------------------|
| `yaml_loader.py` | CRITICAL | Complete rewrite for hierarchy fields |
| `yaml_dumper.py` | CRITICAL | Must serialize hierarchy attributes |
| `sql_loader.py` | CRITICAL | Schema changes, hierarchy loading |
| `sql_dumper.py` | CRITICAL | Schema changes, hierarchy saving |
| `backend.py` | HIGH | Abstraction layer updates |

### Database Layer (6 files) - CRITICAL

| File | Impact | Changes Required |
|------|--------|------------------|
| `schema.py` | CRITICAL | Add 6+ columns per entity table |
| `views.py` | CRITICAL | Aggregation views for commits/deliverables |
| `triggers.py` | HIGH | Hierarchy consistency triggers |
| `connection.py` | LOW | No changes expected |

### Operations Layer (17 files) - HIGH

| File | Impact | Changes Required |
|------|--------|------------------|
| `update.py` | CRITICAL | Commit sync, standards enforcement |
| `query.py` | CRITICAL | Hierarchy traversal queries |
| `standards_enforcement.py` | CRITICAL | Inheritance pattern |
| `add_commit.py` | HIGH | Commit type unification |
| `validate.py` | HIGH | Hierarchy validation |
| `summarize.py` | HIGH | Aggregation logic |
| `context.py` | HIGH | Aggregated field access |
| `commit_mapper.py` | HIGH | Commit type changes |
| `auto_repair.py` | MEDIUM | Hierarchy repair |
| `audit_trail.py` | MEDIUM | Track hierarchy changes |

### CLI Layer (15 files) - MEDIUM-HIGH

| File | Impact | Changes Required |
|------|--------|------------------|
| `commands.py` | HIGH | Model operation calls |
| `show.py` | HIGH | Display aggregated vs local |
| `add_standard.py` | HIGH | Inheritance awareness |
| `standards_formatter.py` | HIGH | Show inheritance |
| `status.py` | MEDIUM | Progress aggregation |
| `batch.py` | MEDIUM | Batch operations |

### MCP Layer (12 files) - MEDIUM-HIGH

| File | Impact | Changes Required |
|------|--------|------------------|
| `task_tools.py` | CRITICAL | commits, deliverables access |
| `sprint_tools.py` | HIGH | Aggregation handling |
| `query_tools.py` | HIGH | Hierarchy queries |
| `roadmap_adapter.py` | HIGH | Model conversion |

---

## 4. Migration Strategy

### Phase 1: Foundation (Sprint 6a Tasks 009, 010, 001, 002)

**Goal**: Implement new model classes without breaking existing code

1. Create `vibey/roadmap/models/ticket/` package with:
   - `enums.py` (Task 010)
   - `support.py` (Task 009)
   - `base.py` (Task 001 - Ticket with hierarchy attributes)
   - `hierarchical.py` (Task 002 - smart accessors)

2. **No changes to existing models yet** - new package runs parallel

### Phase 2: Domain Models (Sprint 6a Tasks 003-006)

**Goal**: Create new domain classes that extend HierarchicalTicket

1. Create `domain.py` with:
   - `RoadmapTicket` (Task 003)
   - `TrackTicket` (Task 004)
   - `SprintTicket` (Task 005)
   - `TaskTicket` (Task 006)

2. **No changes to existing models yet** - validate new classes work

### Phase 3: ORM Layer (Sprint 6a Task 007)

**Goal**: Create SQLAlchemy mapping for new models

1. Create `orm.py` with single-table inheritance
2. Create `repository.py` with CRUD operations
3. **Database migration script** for schema changes

### Phase 4: Adapter Layer (Sprint 6a Task 008)

**Goal**: Bridge old and new models during transition

```python
class ModelAdapter:
    @staticmethod
    def task_to_ticket(old: Task) -> TaskTicket:
        """Convert existing Task to new TaskTicket"""
        return TaskTicket(
            id=old.id,
            name=old.title,
            commits_local=old.commits,
            deliverables_local=[d.path for d in old.deliverables],
            # ... field mapping
        )

    @staticmethod
    def ticket_to_task(new: TaskTicket) -> Task:
        """Convert new TaskTicket back to Task for compatibility"""
        # ... reverse mapping
```

### Phase 5: Serialization Migration (New Sprint Required)

**Goal**: Update loaders/dumpers to use new models

1. Update `yaml_loader.py` to construct new Pydantic models
2. Update `yaml_dumper.py` to serialize new models
3. **Backward compatibility**: Read old format, write new format
4. Migration tool: `vibey roadmap migrate-format`

### Phase 6: Operations Migration (New Sprint Required)

**Goal**: Update all operations to use new models

1. Update imports across operations layer
2. Replace direct field access with smart accessors
3. Update hierarchy traversal logic

### Phase 7: CLI/MCP Migration (New Sprint Required)

**Goal**: Update interfaces to display correct information

1. Update CLI commands for inheritance display
2. Update MCP tools for aggregation
3. User documentation updates

---

## 5. Backward Compatibility Plan

### Strategy: Dual-Mode During Transition

```python
# In vibey/roadmap/models/__init__.py

# Old imports still work
from .task import Task
from .sprint import Sprint
from .track import Track
from .roadmap import Roadmap

# New imports available
from .ticket import (
    Ticket,
    HierarchicalTicket,
    RoadmapTicket,
    TrackTicket,
    SprintTicket,
    TaskTicket,
)
```

### YAML Format Compatibility

```yaml
# OLD FORMAT (still readable)
task:
  id: task-001
  commits:
    - sha: abc123
      message: "feat: add feature"

# NEW FORMAT (preferred)
task:
  id: task-001
  commits_local:
    - sha: abc123
      message: "feat: add feature"
  # Hierarchy attributes computed on load
```

### Database Compatibility

```sql
-- Migration adds columns with defaults
ALTER TABLE tasks ADD COLUMN commits_local_json TEXT;
-- Copy data
UPDATE tasks SET commits_local_json = commits_json;
-- Keep old column during transition
```

---

## 6. Risk Assessment

### High Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during migration | CRITICAL | Comprehensive backup, rollback plan |
| Test suite breakage | HIGH | Parallel test suites during transition |
| Performance regression | MEDIUM | Benchmark aggregation queries |
| User confusion | MEDIUM | Clear documentation, migration guide |

### Dependencies on External Systems

| System | Risk | Notes |
|--------|------|-------|
| Git hooks | LOW | Pre-commit hooks may need updates |
| CI/CD | MEDIUM | Test pipelines need new models |
| MCP clients | HIGH | Breaking API changes possible |

---

## 7. Recommended Sprint Additions

Based on this analysis, Sprint 6a (Task 008) is insufficient for full migration. Recommend adding:

### Sprint 6b: Serialization Migration
- Task 1: Update yaml_loader.py for new models
- Task 2: Update yaml_dumper.py for new models
- Task 3: Update sql_loader.py with ORM
- Task 4: Update sql_dumper.py with ORM
- Task 5: Database schema migration script
- Task 6: Backward compatibility testing
- Task 7: Migration CLI command

### Sprint 6c: Operations Migration
- Task 1: Update query.py operations
- Task 2: Update update.py operations
- Task 3: Update standards_enforcement.py
- Task 4: Update remaining operations files
- Task 5: Integration testing

### Sprint 6d: Interface Migration
- Task 1: Update CLI commands
- Task 2: Update MCP tools
- Task 3: Update documentation
- Task 4: User migration guide
- Task 5: End-to-end testing

---

## 8. Success Criteria

### Sprint 6a Exit Criteria
- [ ] All 10 tasks completed
- [ ] New model classes pass unit tests
- [ ] ORM mapping verified with test database
- [ ] Adapter layer converts models correctly
- [ ] No changes to existing functionality yet

### Full Migration Exit Criteria
- [ ] All YAML files load into new models
- [ ] Database schema migrated
- [ ] All operations use new models
- [ ] CLI displays inheritance correctly
- [ ] MCP tools return aggregated data
- [ ] 100% backward compatibility for existing YAML
- [ ] Performance benchmarks pass
- [ ] All 389 tests passing

---

## 9. Appendix: File-by-File Change List

### Models Package (6 files)
```
vibey/roadmap/models/
├── roadmap.py      # Keep, add import aliases
├── track.py        # Keep, add import aliases
├── sprint.py       # Keep, add import aliases
├── task.py         # Keep, add import aliases
├── standard.py     # Keep, referenced by new models
├── common.py       # Keep, enums used by both
└── ticket/         # NEW PACKAGE
    ├── __init__.py
    ├── enums.py
    ├── support.py
    ├── base.py
    ├── hierarchical.py
    ├── domain.py
    ├── orm.py
    ├── repository.py
    └── adapters.py
```

### Serialization Package (5 files to modify)
```
vibey/roadmap/serialization/
├── yaml_loader.py  # MAJOR CHANGES
├── yaml_dumper.py  # MAJOR CHANGES
├── sql_loader.py   # MAJOR CHANGES
├── sql_dumper.py   # MAJOR CHANGES
└── backend.py      # MODERATE CHANGES
```

### Database Package (4 files to modify)
```
vibey/roadmap/database/
├── schema.py       # MAJOR CHANGES (new columns)
├── views.py        # MAJOR CHANGES (aggregation views)
├── triggers.py     # MODERATE CHANGES
└── connection.py   # MINOR CHANGES
```

---

## 10. Conclusion

The unified ticket architecture is a significant but valuable refactoring that will:

1. **Simplify field access** - Smart accessors handle aggregation/inheritance automatically
2. **Reduce bugs** - No manual tracking of which fields aggregate vs inherit
3. **Improve type safety** - Pydantic validation replaces manual checks
4. **Enable better queries** - Hierarchy attributes allow efficient filtering

**Recommendation**: Proceed with Sprint 6a as designed, but plan for Sprints 6b-6d to complete the full migration. The adapter pattern in Task 008 provides a safe migration path without breaking existing functionality.

**Next Steps**:
1. Complete Sprint 6a (new model classes)
2. Create Sprint 6b plan (serialization migration)
3. Establish backward compatibility tests
4. Document migration guide for users
