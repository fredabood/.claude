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

**Next Steps:**
1. ✅ Fix progress calculation manually for unified-arch-migration
2. Fix FileSystemManager.get_roadmap_path() to use new location
3. File GitHub issues for all documented bugs
4. Add integration tests for flat structure progress updates
