# Context File Consolidation Strategy

**Task:** sqlite-backend-6-task-003
**Date:** 2025-11-30
**Status:** Complete

## Executive Summary

**Recommendation: Option B (Hierarchical by Scope) aligned with Directory Structure Option D**

The context consolidation should mirror the new directory structure from Task 001, organizing files by entity type (tracks/sprints/tasks) while preserving per-entity subdirectories for grouping related context files.

---

## Current State Inventory

### Context File Statistics
| Metric | Count |
|--------|-------|
| Total context directories | 77 |
| Total markdown files | 248 |
| Track-level context dirs | 33 |
| Sprint-level context dirs | 45 |
| Task-level context dirs | 0 |

### File Categories
| Category | Count | % of Total |
|----------|-------|------------|
| Audit files (*AUDIT*) | 78 | 31% |
| Other/miscellaneous | 111 | 45% |
| Session/summary files | 24 | 10% |
| Remediation files | 18 | 7% |
| Implementation plans | 13 | 5% |
| Test-related files | 10 | 4% |
| **Total** | **248** | **100%** |

### Most Common File Names
| File Name | Count |
|-----------|-------|
| AUDIT_REPORT.md | 28 |
| TRACK_AUDIT_REPORT_2025-11-16.md | 20 |
| REMEDIATION_REPORT_2025-11-15.md | 11 |
| IMPLEMENTATION_PLAN.md | 9 |
| REMEDIATION_REPORT_2025-11-16.md | 5 |

### Current Directory Pattern
```
.vibey/roadmap/
└── <track>/
    ├── track.yaml
    ├── context/                    # 33 track-level context dirs
    │   ├── TRACK_AUDIT_REPORT.md
    │   └── IMPLEMENTATION_PLAN.md
    └── <sprint>/
        ├── sprint.yaml
        ├── context/                # 45 sprint-level context dirs
        │   └── AUDIT_REPORT.md
        └── <task>/
            └── task.yaml           # 0 task-level context dirs
```

---

## Consolidation Options

### Option A: Flat with Naming Convention
```
.vibey/roadmap/context/
├── sqlite-backend_TRACK_AUDIT.md
├── sqlite-backend-6_SPRINT_AUDIT.md
├── sqlite-backend-6-task-001_DIRECTORY_STRUCTURE_ANALYSIS.md
└── ...
```

**Pros:**
- Single folder (simplest structure)
- All context immediately visible
- Easy glob: `context/*.md`

**Cons:**
- 248+ files in one directory (unmanageable)
- Long file names (entity ID + type + name)
- Name collisions possible
- Poor organization for browsing

**Score: 45/100**

### Option B: Hierarchical by Scope (RECOMMENDED)
```
.vibey/roadmap/context/
├── tracks/
│   ├── sqlite-backend/
│   │   ├── TRACK_AUDIT_REPORT.md
│   │   ├── IMPLEMENTATION_PLAN.md
│   │   └── REMEDIATION_2025-11-26.md
│   └── git-integration/
│       └── TRACK_AUDIT_REPORT.md
├── sprints/
│   ├── sqlite-backend-6/
│   │   ├── UNIFIED_TICKET_ARCHITECTURE.md
│   │   └── SPRINT_PLAN.md
│   └── sqlite-backend-4/
│       └── SOURCE_OF_TRUTH.md
└── tasks/
    ├── sqlite-backend-6-task-001/
    │   └── DIRECTORY_STRUCTURE_ANALYSIS.md
    └── sqlite-backend-6-task-002/
        └── FILE_FORMAT_EVALUATION.md
```

**Pros:**
- Mirrors directory structure from Task 001 (Option D)
- Clear scope hierarchy (track → sprint → task)
- Subdirectories keep related files together
- Easy navigation by entity
- Scalable to 10K+ tasks
- Clean glob patterns: `context/tracks/**/*.md`

**Cons:**
- More directories than Option A
- Need to know entity ID to find context

**Score: 89/100**

### Option C: Hierarchical by Type
```
.vibey/roadmap/context/
├── audits/
│   ├── track_sqlite-backend_2025-11-16.md
│   └── sprint_sqlite-backend-6_2025-11-30.md
├── plans/
│   └── sprint_sqlite-backend-6_IMPLEMENTATION.md
├── remediation/
│   └── track_sqlite-backend_2025-11-26.md
└── sessions/
    └── sqlite-backend-6-task-001_2025-11-30.md
```

**Pros:**
- Easy to find all files of one type
- Logical grouping for specific queries
- Works well for some tooling

**Cons:**
- Hard to find all context for one entity
- File names must encode entity hierarchy
- Mixed entity types in same folder
- Breaks mental model of "entity context"

**Score: 62/100**

---

## Comparison Matrix

| Criterion | Weight | Option A | Option B | Option C |
|-----------|--------|----------|----------|----------|
| **SQLite mapping alignment** | 5 | 2 | 5 | 3 |
| **File navigation ease** | 4 | 2 | 5 | 3 |
| **Entity context grouping** | 4 | 1 | 5 | 2 |
| **Scalability (10K+ tasks)** | 4 | 1 | 4 | 3 |
| **Naming simplicity** | 3 | 3 | 4 | 2 |
| **Git diff readability** | 3 | 3 | 4 | 3 |
| **Glob pattern simplicity** | 2 | 5 | 4 | 4 |
| **Weighted Total** | | **45** | **89** | **62** |

---

## Recommendation: Option B

### Rationale
1. **Consistency with Task 001** - Same structure as proposed directory hierarchy
2. **Entity-centric** - Find all context for one entity in one place
3. **Scalable** - Subdirectories prevent single-folder bloat
4. **Clear mapping** - `context/<entity-type>/<entity-id>/` is intuitive
5. **Historical context** - Preserves file organization within each entity

### Proposed Structure
```
.vibey/roadmap/context/
├── tracks/
│   └── <track-id>/
│       └── *.md
├── sprints/
│   └── <sprint-id>/
│       └── *.md
└── tasks/
    └── <task-id>/
        └── *.md
```

---

## Naming Convention Specification

### Entity Context Files
| Level | Path Pattern |
|-------|-------------|
| Track | `context/tracks/<track-id>/<FILENAME>.md` |
| Sprint | `context/sprints/<sprint-id>/<FILENAME>.md` |
| Task | `context/tasks/<task-id>/<FILENAME>.md` |

### File Name Format
```
<TYPE>_<TIMESTAMP>_<OPTIONAL_DETAIL>.md
```

**Timestamp Format:** ISO 8601 UTC with minute precision: `YYYY-MM-DDTHHMMZ`
- **Z suffix** indicates UTC timezone (unambiguous across timezones)
- Enables temporal context within a day (multiple files created same day)
- Sortable alphabetically = chronological order
- Human-readable without parsing
- Correlates with activity_log timestamps (also UTC)

**Types (standardized):**
| Type | Purpose | Example |
|------|---------|---------|
| `AUDIT_REPORT` | Validation/audit results | `AUDIT_REPORT_2025-11-30T1420Z.md` |
| `IMPLEMENTATION_PLAN` | Implementation details | `IMPLEMENTATION_PLAN_2025-11-30T0900Z.md` |
| `REMEDIATION` | Fix/remediation docs | `REMEDIATION_2025-11-26T1530Z.md` |
| `SESSION` | Work session notes | `SESSION_2025-11-30T2045Z.md` |
| `ANALYSIS` | Analysis documents | `ANALYSIS_2025-11-30T2012Z_DIRECTORY_STRUCTURE.md` |
| `DESIGN` | Design documents | `DESIGN_2025-11-30T2000Z_UNIFIED_TICKET.md` |

### Naming Rules
1. **UPPERCASE** for file names (visibility)
2. **Underscores** to separate words
3. **ISO UTC timestamps** with minute precision and Z suffix (`YYYY-MM-DDTHHMMZ`)
4. **No entity ID prefix** (already in path)
5. **Descriptive suffix** after timestamp if multiple of same type

### Examples
```
# Good - with UTC timestamps for temporal ordering
context/tracks/sqlite-backend/AUDIT_REPORT_2025-11-16T1030Z.md
context/tracks/sqlite-backend/AUDIT_REPORT_2025-11-16T1545Z.md  # Second audit same day
context/tracks/sqlite-backend/REMEDIATION_2025-11-26T0900Z.md
context/sprints/sqlite-backend-6/IMPLEMENTATION_PLAN_2025-11-30T2000Z.md
context/tasks/sqlite-backend-6-task-001/ANALYSIS_2025-11-30T2012Z_DIRECTORY_STRUCTURE.md

# Bad (avoid)
context/tracks/sqlite-backend/AUDIT_REPORT.md              # No timestamp
context/tracks/sqlite-backend/REMEDIATION_2025-11-26.md    # Date only, no time
context/tracks/sqlite-backend/audit_2025-11-30T1030Z.md    # Lowercase
context/tracks/sqlite-backend/AUDIT_2025-11-30T1030.md     # Missing Z suffix
```

### Why Timestamps Over Dates?

| Scenario | Date-Only | Timestamp |
|----------|-----------|-----------|
| Multiple audits same day | `AUDIT_REPORT.md`, `AUDIT_REPORT_2.md` | `AUDIT_REPORT_2025-11-30T1030.md`, `AUDIT_REPORT_2025-11-30T1545.md` |
| Session continuity | Ambiguous ordering | Clear sequence within day |
| Cross-referencing activity log | Must open file to find time | Filename matches activity_log timestamp |
| Git blame | File shows date only | Can correlate with exact commit time |

---

## Migration Script Design

### Overview
```python
def migrate_context_files():
    """
    Migrate context files from scattered locations to consolidated structure.

    Source: .vibey/roadmap/<track>/context/
            .vibey/roadmap/<track>/<sprint>/context/
            .vibey/roadmap/<track>/<sprint>/<task>/context/

    Target: .vibey/roadmap/context/tracks/<track-id>/
            .vibey/roadmap/context/sprints/<sprint-id>/
            .vibey/roadmap/context/tasks/<task-id>/
    """
```

### Steps
1. **Inventory Phase**
   - Walk existing directory tree
   - Build mapping: old_path → new_path
   - Detect naming conflicts

2. **Validation Phase**
   - Check for duplicate file names per entity
   - Verify no data loss (file counts match)
   - Generate migration report

3. **Migration Phase**
   - Create new directory structure
   - Use `git mv` for each file (preserve history)
   - Remove empty context directories

4. **Verification Phase**
   - Count files before/after
   - Verify all files accessible
   - Run tests

### Path Mapping Logic
```python
def map_old_to_new(old_path: str) -> str:
    """
    Map old scattered path to new consolidated path.

    Examples:
    .vibey/roadmap/sqlite-backend/context/AUDIT.md
      → .vibey/roadmap/context/tracks/sqlite-backend/AUDIT.md

    .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/PLAN.md
      → .vibey/roadmap/context/sprints/sqlite-backend-6/PLAN.md
    """
    parts = old_path.split('/')

    # Find context/ position
    ctx_idx = parts.index('context')

    # Determine level by position
    if ctx_idx == 3:  # roadmap/<track>/context
        entity_type = 'tracks'
        entity_id = parts[2]
    elif ctx_idx == 4:  # roadmap/<track>/<sprint>/context
        entity_type = 'sprints'
        entity_id = parts[3]
    elif ctx_idx == 5:  # roadmap/<track>/<sprint>/<task>/context
        entity_type = 'tasks'
        entity_id = parts[4]

    filename = parts[-1]
    return f".vibey/roadmap/context/{entity_type}/{entity_id}/{filename}"
```

### Conflict Resolution
1. **Same filename, same entity** - Manual review required
2. **Same filename, different entities** - OK (different directories)
3. **Uppercase vs lowercase** - Normalize to uppercase

### Migration Commands
```bash
# Dry run
python migrate_context.py --dry-run

# Execute migration
python migrate_context.py --execute

# With git mv
python migrate_context.py --execute --git-mv
```

---

## Impact Assessment

### Before Migration
- **77 context directories** scattered across tree
- **10 levels deep** maximum
- **No standard naming** convention

### After Migration
- **3 top-level directories** (tracks/, sprints/, tasks/)
- **4 levels maximum** (context/<type>/<entity>/<file>)
- **Standardized naming** convention

### Migration Statistics
| Entity Type | Directories | Files | New Location |
|-------------|-------------|-------|--------------|
| Tracks | 33 | ~60 | `context/tracks/` |
| Sprints | 45 | ~188 | `context/sprints/` |
| Tasks | 0 | 0 | `context/tasks/` |
| **Total** | **78** | **248** | **context/** |

---

## Integration with Task 001 (Directory Structure)

The context consolidation aligns with Directory Structure Option D:

```
.vibey/
├── roadmap.db
└── roadmap/
    ├── roadmap.yaml
    ├── tracks/           # Entity YAML files
    ├── sprints/          # Entity YAML files
    ├── tasks/            # Entity YAML files
    ├── metadata/         # Lower-volume tables
    └── context/          # ← CONTEXT CONSOLIDATION
        ├── tracks/       # Track context files
        ├── sprints/      # Sprint context files
        └── tasks/        # Task context files
```

### Key Benefits
1. **Parallel structure** - `tracks/` for YAML, `context/tracks/` for markdown
2. **Clear separation** - Entity definitions vs entity context
3. **Same navigation** - Find task definition, find task context
4. **Unified glob patterns** - `tracks/*.yaml` and `context/tracks/**/*.md`

---

## Next Steps

1. ✅ Task 001 complete - Directory structure analysis (Option D recommended)
2. ✅ Task 002 complete - File format evaluation (Keep YAML)
3. ✅ Task 003 complete - Context consolidation (Option B recommended)
4. → Implement in Sprint 8 Task 011 - Actual directory restructure
5. → Migrate in Sprint 12 - Production cutover

---

## Appendix: Sample Migration Output

```
=== Context File Migration Plan ===
Total files to migrate: 248

Track context files (60):
  sqlite-backend/TRACK_AUDIT_REPORT.md
    → context/tracks/sqlite-backend/TRACK_AUDIT_REPORT.md
  sqlite-backend/REMEDIATION_2025-11-26.md
    → context/tracks/sqlite-backend/REMEDIATION_2025-11-26.md
  ...

Sprint context files (188):
  sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md
    → context/sprints/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md
  sqlite-backend-4/SOURCE_OF_TRUTH.md
    → context/sprints/sqlite-backend-4/SOURCE_OF_TRUTH.md
  ...

Task context files (0):
  (none currently)

Directories to create: 81 (3 top + 78 entity)
Directories to remove: 77 (empty after migration)
```
