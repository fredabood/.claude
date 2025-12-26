# Task 04: recalculate_all Auto-Completes Tracks with Incomplete Tasks

## Bug Description

The `recalculate_all` function (called during `vibey roadmap db rebuild`) automatically sets track/sprint statuses to `production_ready` based on some completion logic, even when tasks are incomplete. This causes manual status corrections to be reverted.

## Impact

- Manual status corrections are reverted after db rebuild
- Tracks with 50-90% completion incorrectly show as `production_ready`
- Status audit fixes don't persist
- Data integrity audit work is undone by the progress sync

## Observed Behavior

```bash
# 1. Fix track status via SQL
sqlite3 .vibey/roadmap.db "UPDATE tracks SET status='in_progress' WHERE id='...'"

# 2. Also update YAML
sed -i '' 's/status: production_ready/status: in_progress/' .vibey/roadmap/tracks/....yaml

# 3. Rebuild database
vibey roadmap db rebuild

# 4. Status is reverted!
sqlite3 .vibey/roadmap.db "SELECT status FROM tracks WHERE id='...'"
# Returns: production_ready
```

## Root Cause

**File**: `vibey/operations/roadmap/__init__.py`

The `recalculate_all` function contains auto-completion logic:

```python
def recalculate_all(root_dir: Path, verify: bool = False) -> int:
    # ... recalculates progress counters
    # ... AND auto-sets status based on completion logic
```

This is called at the end of `db_rebuild_cmd`:

```python
# vibey/cli/commands_legacy.py line 3713-3715
print("\n🔄 Synchronizing progress counters in YAML files...")
from vibey.operations.roadmap import recalculate_all
sync_result = recalculate_all(root_dir, verify=False)
```

## Implementation Plan

### Option A: Remove Auto-Completion Logic (Recommended)

The `recalculate_all` function should ONLY update progress counters, not statuses.

```python
def recalculate_all(root_dir: Path, verify: bool = False) -> int:
    """Recalculate progress counters for all tracks and sprints.

    NOTE: This function updates progress counters only.
    Status changes should only be made via explicit CLI commands.
    """
    # Update progress counters
    for track in tracks:
        track.progress.tasks_total = count_tasks(track)
        track.progress.tasks_completed = count_completed_tasks(track)
        track.progress.completion_percent = calculate_percent(track)
        # DO NOT change track.status
```

### Option B: Add --no-auto-complete Flag

```python
@roadmap_db.command('rebuild')
@click.option('--force', '-f', is_flag=True)
@click.option('--no-auto-complete', is_flag=True, help='Skip status auto-completion')
def db_rebuild(ctx, force: bool, no_auto_complete: bool):
    ...
    sync_result = recalculate_all(root_dir, verify=False, auto_complete=not no_auto_complete)
```

### Option C: Only Auto-Progress, Never Auto-Complete

Status should only advance in one direction based on work:
- `not_started` → `in_progress` when first task starts
- Never auto-set to `completed` or `production_ready`

```python
def maybe_auto_progress(entity):
    """Only auto-progress, never auto-complete."""
    if entity.status == 'not_started' and entity.has_started_tasks():
        entity.status = 'in_progress'
        entity.started = datetime.now()
    # Never auto-complete
```

## Step-by-Step Fix

### Step 1: Find the Auto-Completion Logic

```bash
grep -n "production_ready\|completed" vibey/operations/roadmap/__init__.py
```

### Step 2: Identify Status-Setting Code

Look for patterns like:
- `track.status = Status.PRODUCTION_READY`
- `sprint.status = 'completed'`
- Auto-completion based on task counts

### Step 3: Remove or Guard Auto-Completion

```python
# Before
if all_tasks_complete(track):
    track.status = Status.PRODUCTION_READY

# After
# Status changes require explicit CLI commands
# Only update progress counters here
```

### Step 4: Update db_rebuild to Not Revert Status

The db_rebuild should:
1. Load YAML (preserving status from YAML)
2. Load to DB (preserving status from YAML)
3. Recalculate progress counters ONLY
4. Write back progress counters to YAML (not status)

### Step 5: Add Test

```python
def test_recalculate_preserves_status():
    """Verify recalculate_all doesn't change explicit status."""
    # Set track to in_progress with 50% completion
    track.status = 'in_progress'
    track.progress.completion_percent = 50

    # Run recalculate
    recalculate_all(root_dir)

    # Status should be preserved
    assert track.status == 'in_progress'
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/__init__.py` | Remove auto-completion from recalculate_all |
| `vibey/cli/commands_legacy.py` | Optional: add --no-auto-complete flag |
| `tests/operations/roadmap/test_recalculate.py` | Add status preservation test |

## Acceptance Criteria

- [ ] `recalculate_all` only updates progress counters, not status
- [ ] Manual status changes persist after db rebuild
- [ ] Tracks with incomplete tasks stay `in_progress`
- [ ] Only explicit CLI commands can change status to `completed`/`production_ready`
- [ ] Test verifies status is preserved during recalculation

## Priority

**CRITICAL** - This bug blocks all status accuracy work. Must be fixed before other Sprint 30 tasks can be effectively tested.
