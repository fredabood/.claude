# Hierarchical Path Usage Audit

**Task:** Sprint 10 Task 001 - Codebase Audit
**Date:** 2025-12-11
**Status:** Complete

## Executive Summary

This audit identifies all code locations that create, read, or expect hierarchical ULID directory structures instead of the flat structure (`tracks/`, `sprints/`, `tasks/`).

**Total Issues Found:** 15 files with hierarchical path patterns requiring migration

## Critical Files (Must Fix)

### 1. backend.py - PRIMARY CULPRIT
**File:** `vibey/roadmap/serialization/backend.py`
**Priority:** CRITICAL - This is the main source of hierarchical directory creation

| Line | Function | Pattern | Action |
|------|----------|---------|--------|
| 160 | `load_track()` | `roadmap_dir / track_id / "track.yaml"` | Migrate to `tracks/{id}.yaml` |
| 170-172 | `load_sprint()` | `track_dir / sprint_id / "sprint.yaml"` | Migrate to `sprints/{id}.yaml` |
| 202-206 | `load_tasks_by_sprint()` | `track_dir / sprint_id` nested search | Migrate to flat task query |
| 212-220 | `load_tasks_by_track()` | nested `track_dir` iteration | Migrate to flat task query |
| 245 | `save_track()` | `roadmap_dir / track.id / "track.yaml"` | **CREATES ULID DIRS** |
| 253-255 | `save_sprint()` | `track_dir / sprint.id` mkdir | **CREATES NESTED ULID DIRS** |
| 276-278 | `save_tasks()` | `track_id / sprint_id` mkdir | **CREATES NESTED ULID DIRS** |

### 2. round_trip_validation.py
**File:** `vibey/roadmap/database/round_trip_validation.py`
**Priority:** HIGH - Creates hierarchical structure during validation

| Line | Function | Pattern | Action |
|------|----------|---------|--------|
| 135 | `dump_database_to_yaml()` | `output_dir.mkdir()` | OK - creates temp dir |
| 146 | `dump_database_to_yaml()` | `track_dir.mkdir()` | **CREATES ULID DIRS** |
| 149 | `dump_database_to_yaml()` | `save_track(track, track_dir / "track.yaml")` | Migrate |
| 156-157 | `dump_database_to_yaml()` | `sprint_dir = track_dir / sprint_id; sprint_dir.mkdir()` | **CREATES NESTED DIRS** |
| 160 | `dump_database_to_yaml()` | `save_sprint(sprint, sprint_dir / "sprint.yaml")` | Migrate |

### 3. integrity_audit.py
**File:** `vibey/roadmap/database/integrity_audit.py`
**Priority:** HIGH - Expects hierarchical structure for reading

| Line | Function | Pattern | Action |
|------|----------|---------|--------|
| 211 | `audit_*` | `track_yaml = track_dir / "track.yaml"` | Migrate to flat read |
| 232 | `audit_*` | `sprint_yaml = sprint_dir / "sprint.yaml"` | Migrate to flat read |
| 363 | `audit_*` | `track_yaml = track_dir / "track.yaml"` | Migrate to flat read |
| 392 | `audit_*` | `sprint_yaml = sprint_dir / "sprint.yaml"` | Migrate to flat read |
| 714-757 | `_load_track_from_yaml()` | Multiple hierarchical patterns | Full rewrite needed |
| 857 | `audit_*` | `track_yaml = track_dir / "track.yaml"` | Migrate to flat read |

### 4. recalculator.py
**File:** `vibey/roadmap/recalculator.py`
**Priority:** MEDIUM - Creates task directories

| Line | Function | Pattern | Action |
|------|----------|---------|--------|
| 363 | `apply_recalculation_plan()` | `task_dir.mkdir(parents=True)` | Migrate to flat task save |
| 370 | `apply_recalculation_plan()` | `sprint_file = sprint_dir / "sprint.yaml"` | Migrate to flat read |

### 5. directory_migration.py
**File:** `vibey/roadmap/serialization/directory_migration.py`
**Priority:** MEDIUM - Migration utilities (may be obsolete)

| Line | Function | Pattern | Action |
|------|----------|---------|--------|
| 97 | `HierarchicalPathResolver.track_path()` | `roadmap_dir / track_id / 'track.yaml'` | Consider deprecation |
| 113 | `HierarchicalPathResolver.sprint_path()` | `track_id / sprint_id / 'sprint.yaml'` | Consider deprecation |
| 131 | `HierarchicalPathResolver.task_path()` | `track_id / sprint_id / task_id / 'task.yaml'` | Consider deprecation |
| 148-152 | `HierarchicalPathResolver.context_path()` | Nested context paths | Consider deprecation |

## Secondary Files (Update References)

### 6. commands.py
**File:** `vibey/cli/commands.py`

| Line | Pattern | Action |
|------|---------|--------|
| 2677 | `track_dir = roadmap_dir / track_summary.id` | Migrate to flat read |
| 2678 | `track_yaml = track_dir / "track.yaml"` | Migrate |
| 2708 | `sprint_dir = track_dir / sprint_summary.id` | Migrate |
| 2709 | `sprint_yaml = sprint_dir / "sprint.yaml"` | Migrate |
| 3023 | `sprint_dir = roadmap_dir / track_id / sprint_id` | Migrate |

### 7. DirectoryManager
**File:** `vibey/roadmap/directory_manager.py`
**Priority:** LOW - Used for slug-based hierarchical (not ULID)

This class creates hierarchical structures using **slugs**, not ULIDs:
- Line 119: `track_dir.mkdir()` - uses slug
- Line 156: `sprint_dir.mkdir()` - uses slug
- Line 193: `task_dir.mkdir()` - uses slug

**Note:** DirectoryManager may still be needed for legacy slug-based context directories. Review for potential removal after ULID migration is complete.

### 8. Git Integration Files
**Files with hierarchical expectations:**

| File | Lines | Pattern |
|------|-------|---------|
| `git_sync.py` | 264, 300, 505, 515 | `sprint_dir / "sprint.yaml"` |
| `ci_integration.py` | 239, 507 | `track_id / "track.yaml"` |
| `commit_evidence.py` | 120, 174 | `track_dir / sprint_id` |
| `blocker_enforcer.py` | 277, 283 | `sprint_dir / "sprint.yaml"` |
| `error_handler.py` | 235, 250, 267, 372 | Multiple patterns |
| `merge_ordering.py` | 179, 216 | `track_dir / "track.yaml"` |
| `sprint_tagger.py` | 144 | `sprint_dir / "sprint.yaml"` |
| `state_reconstructor.py` | 207 | Reference to `track.yaml` |

### 9. Migration Scripts (Consider Removal)
**Files:**
- `vibey/operations/migrations/to_hierarchical.py`
- `vibey/cli/migrate-to-hierarchical.py`

These files exist specifically to create hierarchical structure from flat. After migration to flat-only, they should be **deleted or inverted**.

### 10. Other Files with Patterns

| File | Lines | Notes |
|------|-------|-------|
| `migration.py` (operations/roadmap) | 103, 110, 230, 255, 322, 325, 376, 386, 580 | Multiple hierarchical patterns |
| `yaml_remediation.py` | 145, 155, 241 | `track_dir / "track.yaml"` |
| `toc_generator.py` | 201, 219, 240, 293, 297 | Hierarchical path generation |
| `migrate_to_criteria.py` | 39, 46, 209, 259 | Hierarchical detection |
| `summarize.py` | 168 | `sprint_dir / 'sprint.yaml'` |
| `filesystem.py` (cli/roadmap_lib) | 259, 279 | Hierarchical path construction |
| `compatibility.py` | 232, 234 | Hierarchical fallback detection |
| `yaml_dumper.py` | 55 | `task_dir.mkdir()` |

## Test Files (Update Expectations)

These test files create hierarchical structures for testing:

| File | Notes |
|------|-------|
| `test_hierarchical_integration.py` | Tests hierarchical DirectoryManager |
| `test_toc_generator.py` | Creates temp hierarchical structures |
| `test_directory_manager.py` | Tests DirectoryManager (slug-based) |

## Untracked Legacy Directories

The following 35 ULID directories exist locally but are **not tracked in git**:

```
.vibey/roadmap/01KC2D0JK06MN77ZHAGAHF5VKB/
.vibey/roadmap/01KC2D0JK06MN77ZHAGAHF5VKN/
.vibey/roadmap/01KC2D0JK1877YN6T0673VB24T/
... (32 more)
.vibey/roadmap/01KC39XSXJ39N12HWJ93F77KQ9/
```

These were created by `YAMLBackend.save_*()` methods during `db dump` operations. They contain duplicate data already present in the flat structure.

**Action:** Delete after confirming no unique data (Task 007).

## Migration Priority Order

1. **backend.py** - Stop creating ULID directories (Task 002)
2. **round_trip_validation.py** - Update dump function (Task 003)
3. **integrity_audit.py** - Update audit functions (Task 004)
4. **recalculator.py** - Update task creation (Task 005)
5. **to_hierarchical.py** - Delete or invert (Task 006)
6. **Legacy directories** - Delete 35 ULID dirs (Task 007)
7. **Validation command** - Add structure check (Task 008)
8. **Git integration files** - Lower priority, may auto-fix with backend change
9. **Test files** - Update after production code

## Flat Structure Target

After migration, all YAML I/O should use:

```
.vibey/roadmap/
├── roadmap.yaml           # Root roadmap
├── tracks/
│   └── {ulid}.yaml        # One file per track
├── sprints/
│   └── {ulid}.yaml        # One file per sprint
├── tasks/
│   └── {ulid}.yaml        # One file per task
└── context/
    ├── tracks/{slug}/     # Context by slug (human-readable)
    ├── sprints/{slug}/
    └── tasks/{slug}/
```

## Verification Checklist

After all migrations complete:
- [ ] No code creates `roadmap_dir / track.id /` paths
- [ ] No code creates `track_dir / sprint.id /` paths
- [ ] No code creates `sprint_dir / task.id /` paths
- [ ] `vibey roadmap db dump` writes to flat structure
- [ ] `vibey roadmap db rebuild` reads from flat structure
- [ ] No untracked `01KC*/` directories exist
- [ ] All tests pass
- [ ] `vibey roadmap validate-structure` command exists and passes
