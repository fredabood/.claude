# Task 001: Analyze Current Progress Update Flow

**Task ID:** dogfooding-bugs-04-task-001
**Bug Addressed:** #1 (Track and Sprint Progress Not Auto-Updated After Task Completion)
**Complexity:** Low
**Type:** Research

---

## Problem Statement

After completing all tasks in a sprint, the track and sprint progress fields are not automatically updated. The investigation needs to determine:

1. Why progress propagation isn't working with ULID structure
2. Where the chain breaks between task completion → sprint progress → track progress
3. What needs to change to support flat directory structure

---

## Current Architecture Analysis

### Progress Update Chain (Expected)

```
Task Completed
    ↓
complete_task() in update.py:343
    ↓
_update_sprint_progress() at line 480
    ↓
_update_track_progress() at line 1439 (from inside _update_sprint_progress)
    ↓
_update_roadmap_progress() at line 1511 (from inside _update_track_progress)
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `complete_task()` | `update.py:343` | Entry point for task completion |
| `_update_sprint_progress()` | `update.py:1346` | Updates sprint based on task completion |
| `_update_track_progress()` | `update.py:1442` | Updates track based on sprint completion |
| `_update_roadmap_progress()` | `update.py:1514` | Updates roadmap based on track completion |
| `StatusManager` | `status.py:24` | Auto-progression logic |
| `FileSystemManager` | `filesystem.py` | Flat/nested structure support |

---

## Investigation Steps

### 1. Trace the Call Chain

```python
# In complete_task() at line 480:
_update_sprint_progress(fs, sprint_id)

# In _update_sprint_progress() at line 1438:
track_id = sprint_id.rsplit('-', 1)[0]  # ⚠️ ISSUE: Assumes hierarchical ID
_update_track_progress(fs, track_id)
```

**Issue Identified:** The code extracts `track_id` from `sprint_id` by splitting on `-`:
- Hierarchical: `sqlite-backend-1` → track_id = `sqlite-backend`
- ULID: `01KC2D0JKVT80AFQ6C1PA8CKJD` → track_id = `01KC2D0JKVT80AFQ6C1PA8CKJ` (WRONG!)

### 2. Verify Sprint Model Has track_id

```python
# Sprint model (sprint.py:124):
track_id: str  # ✓ Field exists

# But update.py doesn't use it!
```

### 3. Check FileSystemManager Structure Detection

```python
# filesystem.py:256
if self.structure_format == "flat":
    return self.roadmap_root / "tasks"  # ✓ Correct for flat
```

---

## Root Cause Analysis

### Primary Issue: track_id Extraction

```python
# Current code (update.py:1438):
track_id = sprint_id.rsplit('-', 1)[0]  # Extract track ID

# Should be:
sprint = load_sprint(sprint_path)
track_id = sprint.track_id  # Get from model
```

### Secondary Issues

1. **Sprint summaries in track.yaml**: Track files may have stale sprint summaries
2. **Progress not saved**: Changes may not be persisted correctly
3. **Auto-progression not triggered**: StatusManager may not be called

---

## Verification Commands

```bash
# Check if sprint has track_id field
cat .vibey/roadmap/sprints/01KC2D0JKTE7Z4HCNHST8ZVW4S.yaml | grep track_id

# Check track progress before/after task completion
vibey roadmap show track unified-architecture-migration --progress

# Manually trigger progress refresh
vibey roadmap refresh-progress
```

---

## Expected Findings Summary

| Finding | Evidence | Impact |
|---------|----------|--------|
| track_id extraction fails with ULIDs | `rsplit('-', 1)[0]` produces garbage | **Critical** - breaks entire chain |
| Sprint model has track_id | `sprint.py:124` | Can be used as fix |
| FileSystemManager supports flat | `filesystem.py:256` | No issue here |
| StatusManager logic is sound | `status.py` | No issue here |

---

## Recommended Fix Approach

1. **Immediate**: Load sprint to get `track_id` instead of parsing ID
2. **Robust**: Add `track_id` parameter to `_update_sprint_progress()` and pass it down
3. **Future**: Consider storing parent IDs in a lookup table for performance

---

## Success Criteria

- [ ] Root cause identified and documented
- [ ] Call chain traced with breakpoints/logging
- [ ] Fix approach validated with prototype
- [ ] All affected files documented

---

## Dependencies

None - this is a research task.

---

## Files to Examine

| File | Lines | Purpose |
|------|-------|---------|
| `vibey/operations/roadmap/update.py` | 343, 480, 1346, 1438, 1442 | Progress update chain |
| `vibey/cli/roadmap_lib/status.py` | 91, 177, 206 | Auto-progression |
| `vibey/cli/roadmap_lib/filesystem.py` | 241, 330, 351 | Structure detection |
| `vibey/roadmap/models/sprint.py` | 124 | track_id field |

---

## Notes

This investigation will inform Tasks 002-003. The fix is likely straightforward once the root cause is confirmed - just use `sprint.track_id` instead of parsing the sprint ID string.
