# Task Plan: Fix YAML progress counters not synced with database

**Task ID:** 01KCY39YJW8A3YDNTFJY5KMDGT
**Priority:** Low
**Complexity:** Medium

## Problem Statement

Track YAML files show stale progress counters (e.g., `tasks_total: 0`) while the database shows actual counts (e.g., 239 tasks). This causes confusion when inspecting YAML files directly.

### Example

```yaml
# Track YAML shows:
progress:
  tasks_total: 0
  tasks_completed: 0
  completion_percent: 0

# But database shows:
# tasks_total: 239, tasks_completed: 127, completion_percent: 53
```

### Root Cause

The YAML sync process (`vibey roadmap db rebuild`) either:
1. Doesn't update progress fields in track/sprint YAML files
2. Gets stuck/times out before completing the sync
3. Only updates database, not YAML files (single source of truth confusion)

### Affected Code Locations

| File | Lines | Description |
|------|-------|-------------|
| `vibey/roadmap/serialization/yaml_dumper.py` | 169-197 | save_track() with progress |
| `vibey/operations/roadmap/update.py` | 1683-1752 | _update_track_progress() |
| CLI commands | Various | rebuild/sync commands |

## Implementation Plan

### Step 1: Understand Current Sync Flow
- [ ] Trace what happens during `vibey roadmap db rebuild`
- [ ] Identify where YAML progress should be updated
- [ ] Find why sync times out or doesn't complete

### Step 2: Decision Point

**Option A: Database as Single Source of Truth**
- Remove progress fields from YAML files entirely
- Always compute progress from database
- Simplifies sync, removes duplication
- **Recommended if progress is always computed**

**Option B: Keep YAML Progress, Fix Sync**
- Ensure sync always updates YAML after DB load
- Add timeout handling to prevent hangs
- Add progress bar for long syncs

### Step 3: Implement Fix (Option A)

If removing progress from YAML:
1. Update yaml_dumper.py to not write progress fields
2. Update yaml_loader.py to not require progress fields
3. Always compute progress from child entities
4. Update display code to query database

### Step 3 Alt: Implement Fix (Option B)

If keeping YAML progress:
1. Add explicit YAML update step after DB rebuild
2. Add timeout with graceful recovery
3. Show clear message if sync incomplete
4. Add `--skip-yaml-sync` flag for speed

### Step 4: Add Tests
- [ ] Test that progress is computed correctly
- [ ] Test that sync completes within timeout
- [ ] Test that displayed progress matches actual counts

### Step 5: Verify Fix
- [ ] Run `vibey roadmap db rebuild`
- [ ] Check YAML files have correct progress (or no progress fields)
- [ ] Verify `vibey roadmap status` shows correct counts

## Acceptance Criteria

- [ ] Progress shown to user matches actual task counts
- [ ] No stale data in YAML files OR no progress in YAML (single source of truth)
- [ ] Sync completes without timeout
- [ ] Tests added and passing

## Design Considerations

### Recommendation: Option A (Database as Source of Truth)

Storing progress in both YAML and SQLite creates synchronization problems. The database should be the single source of truth for computed values like progress. Benefits:
- No sync needed for progress
- Always accurate
- Simpler code
- Faster operations

Keep in YAML only: status, dates, metadata (things that are directly set, not computed)

## Estimated Effort

- Analysis: 30 minutes
- Implementation: 1 hour
- Testing: 30 minutes
- **Total: ~2 hours**
