# Sprint 10: Hierarchical to Flat Structure Migration

**Sprint ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXN`
**Bug Addressed:** #19 (YAMLBackend and other modules create hierarchical ULID directories)
**Priority:** High
**Complexity:** High (codebase-wide changes)

## Problem Statement

The codebase has an architectural inconsistency where multiple modules still expect
or create hierarchical directory structures with ULID names:

```
# WRONG - Hierarchical structure (created by YAMLBackend, round_trip_validation, etc.)
.vibey/roadmap/{track_ulid}/track.yaml
.vibey/roadmap/{track_ulid}/{sprint_ulid}/sprint.yaml
.vibey/roadmap/{track_ulid}/{sprint_ulid}/{task_ulid}/task.yaml

# CORRECT - Flat structure (intended architecture)
.vibey/roadmap/tracks/{ulid}.yaml
.vibey/roadmap/sprints/{ulid}.yaml
.vibey/roadmap/tasks/{ulid}.yaml
```

This causes:
1. Duplicate data (same content in both structures)
2. Confusion about which is authoritative
3. Wasted disk space
4. Potential data sync issues

## Root Cause Analysis

### Primary Culprit: `YAMLBackend` class
**File:** `vibey/roadmap/serialization/backend.py:242-278`
```python
def save_track(self, track: Track) -> None:
    save_track(track, self.roadmap_dir / track.id / "track.yaml")  # Creates ULID dir!

def save_sprint(self, sprint: Sprint) -> None:
    track_dir = self.roadmap_dir / sprint.track_id
    sprint_dir = track_dir / sprint.id
    sprint_dir.mkdir(parents=True, exist_ok=True)  # Creates nested dirs!
```

### Secondary Culprits

| File | Function | Lines | Issue |
|------|----------|-------|-------|
| `round_trip_validation.py` | `dump_database_to_yaml()` | 145-166 | Creates `track_dir / track_id` structure |
| `integrity_audit.py` | Multiple functions | 211, 363, 714+ | Expects `track_dir / "track.yaml"` pattern |
| `recalculator.py` | `apply_recalculation_plan()` | 300-370 | Creates `sprint_dir / subtask.id` directories |
| `to_hierarchical.py` | `HierarchicalMigrator` | 25-389 | Entire module for wrong direction |

## Tasks

### Task 001: Codebase Audit (Research)
- Comprehensive grep/search of entire vibey/ directory
- Find ALL occurrences of:
  - `track_id / "track.yaml"` or `/ track.id /`
  - `sprint_id / "sprint.yaml"` or `/ sprint.id /`
  - `task_dir.mkdir` or `sprint_dir.mkdir`
  - DirectoryManager usage
- Output: `HIERARCHICAL_AUDIT.md` with file:line inventory

### Task 002: Migrate YAMLBackend
- Update `save_track()` → `tracks/{id}.yaml`
- Update `save_sprint()` → `sprints/{id}.yaml`
- Update `save_tasks()` → `tasks/{id}.yaml`
- Update corresponding `load_*()` methods
- Remove all `mkdir` calls for nested directories

### Task 003: Migrate round_trip_validation.py
- Update `dump_database_to_yaml()` to use flat structure
- Update `compare_yaml_directories()` for flat comparison
- Ensure round-trip still validates correctly

### Task 004: Migrate integrity_audit.py
- Update all `track_dir / "track.yaml"` patterns
- Update all `sprint_dir / "sprint.yaml"` patterns
- Update orphan detection logic
- Update task counting logic

### Task 005: Migrate recalculator.py
- Update task creation to use `tasks/{ulid}.yaml`
- Remove nested directory creation
- Update sprint references

### Task 006: Update/Remove migrate_to_hierarchical.py
- Option A: Delete obsolete module
- Option B: Rename to `migrate_to_flat.py` (inverse direction)
- Remove `migrate_to_hierarchical_cmd` from CLI

### Task 007: Clean Up Legacy Directories
- Delete 35+ untracked `01KC*/` directories
- Verify no unique data lost
- Add `.gitignore` rule

### Task 008: Add Structure Validation
- New CLI command: `vibey roadmap validate-structure`
- Detect orphaned hierarchical directories
- Warn if both structures exist
- Integrate with `db init/rebuild`

### Task 009: Migrate commands.py Hierarchical Paths
- Update lines 2677-2709 and 3023 in vibey/cli/commands.py
- Convert `track_dir = roadmap_dir / track_summary.id` to flat paths
- Convert `sprint_dir = track_dir / sprint_summary.id` to flat paths

### Task 010: Migrate Git Integration Files
- Update 8 files: git_sync.py, ci_integration.py, commit_evidence.py,
  blocker_enforcer.py, error_handler.py, merge_ordering.py,
  sprint_tagger.py, state_reconstructor.py
- Convert all `sprint_dir / "sprint.yaml"` patterns
- Convert all `track_id / "track.yaml"` patterns

### Task 011: Migrate Roadmap Operations Files
- Update migration.py (operations/roadmap) - 9 patterns
- Update yaml_remediation.py - 3 patterns
- Update toc_generator.py - 5 patterns
- Update migrate_to_criteria.py - 4 patterns
- Update summarize.py - 1 pattern

### Task 012: Migrate CLI Roadmap Lib Files
- Update filesystem.py (cli/roadmap_lib) - lines 259, 279
- Update compatibility.py - lines 232, 234
- Update yaml_dumper.py - line 55

### Task 013: Deprecate directory_migration.py HierarchicalPathResolver
- Review HierarchicalPathResolver class
- Either delete or add deprecation warnings
- Consider creating FlatPathResolver if needed

### Task 014: Update Test Files for Flat Structure
- Update test_hierarchical_integration.py
- Update test_toc_generator.py
- Update test_directory_manager.py
- Ensure all tests pass after migration

## Success Criteria

1. No code paths create hierarchical ULID directories
2. All YAML I/O uses flat `tracks/`, `sprints/`, `tasks/` structure
3. No untracked `01KC*/` directories in `.vibey/roadmap/`
4. `vibey roadmap db dump` writes to flat structure
5. `vibey roadmap db rebuild` reads from flat structure
6. All existing tests pass
7. New validation command exists and works

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/serialization/backend.py` | Rewrite save_*/load_* methods |
| `vibey/roadmap/database/round_trip_validation.py` | Update dump and compare |
| `vibey/roadmap/database/integrity_audit.py` | Update path patterns |
| `vibey/roadmap/recalculator.py` | Update task creation |
| `vibey/operations/migrations/to_hierarchical.py` | Delete or invert |
| `vibey/cli/commands.py` | Remove migrate_to_hierarchical_cmd |
| `vibey/cli/main.py` | Add validate-structure command |
| `.gitignore` | Add rule for ULID directories |

## Dependencies

```
Task 001 (Audit) ─┬─► Task 002 (YAMLBackend) ─┬─► Task 009 (commands.py)
                  │                           ├─► Task 010 (git files)
                  │                           ├─► Task 011 (roadmap ops)
                  │                           └─► Task 012 (cli lib)
                  ├─► Task 003 (round_trip)
                  ├─► Task 004 (integrity_audit)
                  └─► Task 005 (recalculator)
                           │
Task 002 ─────────────────►├─► Task 006 (migrate module)
                           │
Tasks 002-012 ────────────►├─► Task 007 (cleanup)
                           │
Tasks 009-012 ────────────►├─► Task 013 (deprecate resolver)
                           │
Task 007 ─────────────────►├─► Task 008 (validation)
                           │
Tasks 002-012 ────────────►└─► Task 014 (tests)
```

## Estimated Effort

| Task | Complexity | Estimated Tokens |
|------|------------|------------------|
| 001 | Medium | 2,000 | COMPLETE |
| 002 | Medium | 3,000 |
| 003 | Medium | 2,500 |
| 004 | High | 3,500 |
| 005 | Medium | 2,000 |
| 006 | Low | 1,500 |
| 007 | Low | 500 |
| 008 | Medium | 2,000 |
| 009 | Medium | 2,000 |
| 010 | High | 4,000 |
| 011 | High | 3,500 |
| 012 | Medium | 2,000 |
| 013 | Low | 1,500 |
| 014 | Medium | 2,500 |
| **Total** | **High** | **31,500** |
