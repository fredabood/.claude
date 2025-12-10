# CLI Bugs Discovered During Validation

## Bug #1: Track and Sprint Progress Not Auto-Updated After Task Completion

**Date:** 2025-12-09
**Severity:** Medium
**Status:** Documented

**Description:**
After completing all 5 tasks in unified-arch-1 sprint, the track and sprint progress fields were not automatically updated to reflect completion.

**Expected Behavior:**
- Sprint status should auto-update to "completed" when all tasks are completed
- Track progress should reflect completed tasks (5/29) and sprints (1/5)
- Track completion_percent should calculate to ~17%

**Actual Behavior:**
- Sprint status remains "not_started"
- Track shows 0/29 tasks completed, 0/5 sprints completed
- Track completion_percent shows 0%

**Root Cause:**
Progress update logic not integrated with flat directory structure migration. The CLI likely expects nested structure or doesn't have auto-progression logic for the new flat format.

**Workaround:**
Manual YAML file editing to correct progress fields.

**Fix Required:**
1. Implement auto-progression logic in operations/roadmap/update.py
2. Add post-task-completion hook to update parent sprint/track progress
3. Integrate with FileSystemManager's dual-format support

**Files Affected:**
- `.vibey/roadmap/tracks/01KC2D0JKTE7Z4HCNHST8ZVW4R.yaml` (unified-architecture-migration track)
- `.vibey/roadmap/sprints/01KC2D0JKTE7Z4HCNHST8ZVW4S.yaml` (unified-arch-1 sprint)

---

## Bug #2: unified-architecture-migration Track Not Showing in `roadmap status`

**Date:** 2025-12-09
**Severity:** Low
**Status:** Documented

**Description:**
The `vibey roadmap status` command does not display the unified-architecture-migration track in its output, even though the track file exists and is valid.

**Expected Behavior:**
All tracks should be listed in `roadmap status` output

**Actual Behavior:**
unified-architecture-migration track is missing from the list (only 37 tracks shown when there should be 38)

**Root Cause:**
Possibly related to:
- Track status being "not_started" (may be filtered)
- Track loading issue with new flat structure
- FileSystemManager list_tracks() method not finding all tracks

**Files Affected:**
- `vibey/operations/roadmap/query.py` (status query logic)
- `vibey/cli/roadmap_lib/filesystem.py` (track discovery)

**Investigation Needed:**
Check track discovery logic in flat structure implementation

---

## Bug #3: CLI Looks for roadmap.yaml in Wrong Location After Migration

**Date:** 2025-12-09
**Severity:** High
**Status:** Documented

**Description:**
After migrating to flat structure, the CLI commands look for `roadmap.yaml` at `.vibey/roadmap.yaml` (old location) instead of `.vibey/roadmap/roadmap.yaml` (new location per flat structure spec).

**Expected Behavior:**
CLI should look for roadmap.yaml at `.vibey/roadmap/roadmap.yaml`

**Actual Behavior:**
CLI returns "Error: Roadmap not found" even though roadmap.yaml exists at the correct new location

**Root Cause:**
FileSystemManager.get_roadmap_path() returns `.vibey/roadmap.yaml` instead of `.vibey/roadmap/roadmap.yaml`

**Files Affected:**
- `vibey/cli/roadmap_lib/filesystem.py` (line 197-199)

**Fix Required:**
```python
def get_roadmap_path(self) -> Path:
    """Get path to roadmap.yaml."""
    # OLD: return self.vibey_dir / self.ROADMAP_FILE
    # NEW: return self.roadmap_root / self.ROADMAP_FILE
    return self.roadmap_root / self.ROADMAP_FILE
```

**Workaround:**
Keep both roadmap.yaml files in sync or symlink old location to new

---

## Bug #4: Track Model Validation Fails for Flat Structure Sprint IDs

**Date:** 2025-12-09
**Severity:** Critical
**Status:** Fixing

**Description:**
After flat structure migration, the Track model's `__post_init__` validation fails because sprint IDs in track files don't match the expected format `{track_id}-{suffix}`.

**Expected Behavior:**
Sprint IDs should be either:
1. Hierarchical: `{track_ulid}-{sprint_suffix}` (e.g., `01KC2D0JK1877YN6T0673VB254-sprint-1`)
2. Independent ULIDs without validation

**Actual Behavior:**
- Track IDs are ULIDs: `01KC2D0JK1877YN6T0673VB254`
- Sprint IDs in track files are old slugs or ULIDs: `cody-port-1` or `01KC2D0JKTE7Z4HCNHST8ZVW4S`
- Validation at `track.py:179-180` rejects all tracks: `ValueError: Sprint ID cody-port-1 must start with track ID 01KC2D0JK1877YN6T0673VB254`

**Root Cause:**
Migration script (`directory_migration_v2.py`) assigned ULIDs to tracks and sprints but didn't update sprint ID references in track.yaml files to match the hierarchical format expected by Track model validation.

**Impact:**
- NO tracks can load from flat structure
- CLI status shows 37 tracks instead of 38 (all tracks with validation errors are filtered out)
- Affects all roadmap operations

**Fix Required:**
Option 1 (Quick): Comment out sprint ID validation in Track model for flat structure
Option 2 (Proper): Update migration script to use hierarchical IDs or update all track files

**Files Affected:**
- `vibey/roadmap/models/track.py` (line 179-180)
- All `.vibey/roadmap/tracks/*.yaml` files

---

## Bug #5: SQLite Database Out of Sync with YAML After Migration

**Date:** 2025-12-09
**Severity:** Critical
**Status:** Documented

**Description:**
The SQLite database (.vibey/roadmap.db) is out of sync with the YAML files after flat structure migration. The database contains 37 tracks while the YAML files contain 38 tracks.

**Root Cause:**
The flat structure migration updated YAML files but did not update the SQLite database. When SQLite backend is detected (database file exists), query operations read from the database instead of YAML, missing the newly created unified-architecture-migration track.

**Impact:**
- CLI shows 37 tracks instead of 38
- unified-architecture-migration track invisible to all CLI commands
- Database queries return stale data

**Fix Required:**
- Rebuild SQLite database from YAML files after migration
- OR: Add database sync step to migration script
- OR: Disable SQLite backend until database is updated

**Files Affected:**
- `.vibey/roadmap.db` (stale - 37 tracks)
- `.vibey/roadmap/*.yaml` (current - 38 tracks)

---

## Bug #6: Missing SQLAlchemy Dependency Breaks All CLI Commands

**Date:** 2025-12-09
**Severity:** Critical
**Status:** Documented

**Description:**
All CLI commands fail with `ModuleNotFoundError: No module named 'sqlalchemy'` when attempting to import roadmap serialization modules.

**Error:**
```
File "/Users/fredabood/Repositories/vibey/vibey/roadmap/models/ticket/orm.py", line 23, in <module>
    from sqlalchemy import (
ModuleNotFoundError: No module named 'sqlalchemy'
```

**Root Cause:**
The ORM module (`vibey/roadmap/models/ticket/orm.py`) unconditionally imports SQLAlchemy, even when the YAML backend is being used. This import happens at module load time, making it a hard dependency.

**Impact:**
- **ALL** CLI commands are broken (`vibey roadmap status`, `vibey roadmap show`, etc.)
- Cannot validate roadmap state
- Cannot update task status
- Cannot query roadmap data
- Forces users to install SQLAlchemy even if they only use YAML backend

**Expected Behavior:**
- SQLAlchemy should be an **optional** dependency
- ORM module should use lazy imports or conditional imports
- YAML-only users should not need SQLAlchemy installed

**Fix Required:**
Option 1: Lazy imports in orm.py
```python
# In orm.py
def get_orm_models():
    try:
        from sqlalchemy import ...
        return models
    except ImportError:
        raise ImportError("SQLAlchemy required for database operations")
```

Option 2: Split orm.py into separate module
- Move ORM code to vibey/roadmap/database/orm.py
- Only import when using SQLite backend

Option 3: Make SQLAlchemy required dependency
- Add to requirements.txt / pyproject.toml
- Document as required for all installations

**Files Affected:**
- `vibey/roadmap/models/ticket/__init__.py` (line 129 - imports orm)
- `vibey/roadmap/models/ticket/orm.py` (line 23 - unconditional SQLAlchemy import)
- All CLI commands (all fail on import)

**Workaround:**
Install SQLAlchemy: `pip install sqlalchemy`

---

## Bug #7: Validator Doesn't Exclude context/sample_code Directories

**Date:** 2025-12-09
**Severity:** Low
**Status:** Documented

**Description:**
The `vibey roadmap validate-fast` command validates files in `context/sample_code` directories, which contain example YAML snippets that are NOT valid roadmap objects. These are documentation samples, not roadmap data.

**Error:**
```
❌ .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/sample_code/yaml/block_044.yaml
   • YAML root must be a dictionary
```

**Expected Behavior:**
Validator should skip files in `context/sample_code/` directories, similar to how it might skip test fixtures or documentation examples.

**Actual Behavior:**
Validator includes all YAML files, causing false positives for sample code files.

**Files Affected:**
- `vibey/cli/roadmap_lib/validation.py` (or wherever validate-fast is implemented)

**Fix Required:**
Add exclusion pattern for `context/sample_code/` directories:
```python
VALIDATION_EXCLUDE_PATTERNS = [
    "**/context/sample_code/**",
    "**/test_fixtures/**",
]
```

---

**Next Steps:**
1. ✅ Fix progress calculation manually for unified-arch-migration
2. ✅ Fix FileSystemManager.get_roadmap_path() to use new location
3. ✅ Fix Track model validation for flat structure
4. ✅ Fix query.py SQLite backend parameter passing
5. ✅ Disabled SQLite database (renamed to .db.disabled)
6. 🔧 Fix SQLAlchemy optional dependency issue (Bug #6)
7. 🔧 Fix validator exclusion patterns (Bug #7)
8. File GitHub issues for all documented bugs
9. Add integration tests for flat structure progress updates
