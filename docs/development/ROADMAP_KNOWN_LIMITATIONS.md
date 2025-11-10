# Roadmap System Known Limitations

**Last Updated:** 2025-11-10
**Roadmap Version:** v2.1 (Hierarchical Structure)

This document tracks known limitations and issues in the Vibey roadmap system that have been identified but not yet fixed. These are typically discovered during production use and prioritized for future sprints.

---

## Cascade Update Limitations

**Discovered:** 2025-11-10 (infrastructure-fixes-1 sprint completion)
**Severity:** Medium
**Impact:** Status updates work, but aggregate metrics and dependency tracking require manual updates
**Status:** Documented, not yet scheduled for fix

### Description

When completing tasks and sprints, certain hierarchical updates do not cascade automatically as expected. While the core status progression (task → sprint → track) works correctly, several aggregate fields and relationship updates are not being calculated or propagated.

### Specific Issues

#### 1. Track Progress Fields Not Cascading

**Problem:** When a sprint completes, the parent track's progress fields are not automatically updated.

**Missing Fields:**
- `progress.sprints_total` - Total number of sprints in track
- `progress.sprints_completed` - Number of completed sprints
- `progress.tasks_total` - Total number of tasks across all sprints
- `progress.tasks_completed` - Total completed tasks
- `progress.completion_percent` - Overall track completion percentage

**Current Behavior:**
```yaml
# .vibey/roadmap/infrastructure-fixes/track.yaml
track:
  id: infrastructure-fixes
  status: completed
  progress:
    sprints_total: 1      # ❌ Not auto-calculated
    sprints_completed: 1  # ❌ Not auto-calculated
    tasks_total: 13       # ❌ Not auto-calculated
    tasks_completed: 13   # ❌ Not auto-calculated
    completion_percent: 100  # ❌ Not auto-calculated
```

**Expected Behavior:** These fields should be automatically calculated by aggregating child sprint data when:
- A sprint status changes
- A task is completed
- Sprint completion triggers track update

**Workaround:** Manually calculate and update these fields using:
```bash
python3 framework/scripts/roadmap-update.py --recalculate-track infrastructure-fixes
```
*(Note: This command may not exist yet - manual YAML editing required)*

**Root Cause:** The `roadmap-update.py` script focuses on status transitions but doesn't implement aggregate field calculation. The track model defines these fields but no code populates them.

**Files Affected:**
- `framework/scripts/roadmap-update.py` - Missing aggregate calculation logic
- `.vibey/roadmap/*/track.yaml` - Progress fields remain empty or stale

---

#### 2. Activity Log Entries Showing as "Unknown"

**Problem:** When status updates occur, the activity log captures the event but the `activity_type` field shows as "unknown" instead of proper values.

**Current Behavior:**
```yaml
# .vibey/roadmap/infrastructure-fixes/track.yaml
activity_log:
  - timestamp: '2025-11-10T21:40:45.963791+00:00'
    activity_type: unknown  # ❌ Should be "sprint_completed" or similar
    description: Sprint infrastructure-fixes-1 completed
    actor: system
    metadata:
      sprint_id: infrastructure-fixes-1
```

**Expected Behavior:**
```yaml
activity_log:
  - timestamp: '2025-11-10T21:40:45.963791+00:00'
    activity_type: sprint_completed  # ✅ Proper type
    description: Sprint infrastructure-fixes-1 completed
    actor: system
    metadata:
      sprint_id: infrastructure-fixes-1
```

**Impact:**
- Activity logs are harder to filter and query
- Analytics and reporting can't distinguish event types
- Historical audit trail lacks semantic meaning

**Workaround:** None - entries are written as "unknown" and remain that way

**Root Cause:** The activity logging code doesn't map status change events to proper activity type constants. It defaults to "unknown" for unrecognized events.

**Files Affected:**
- `framework/scripts/roadmap-update.py` - Activity log creation logic
- All track/sprint/task YAML files - Activity log entries

**Suggested Activity Types:**
- `task_started`
- `task_completed`
- `sprint_started`
- `sprint_entered_completion_gate`
- `sprint_completed`
- `track_started`
- `track_completed`
- `dependency_added`
- `blocker_added`
- `blocker_resolved`

---

#### 3. Dependency Status Not Auto-Updating

**Problem:** When a blocking track completes, tracks that depend on it still show stale `current_status` values in their `blocked_by` fields.

**Current Behavior:**
```yaml
# .vibey/roadmap/goose-port/track.yaml
blocked_by:
  - dependency_id: infrastructure-fixes
    dependency_type: track
    at_status: not_started
    current_status: not_started  # ❌ Stale - infrastructure-fixes is actually completed
    reason: Must fix roadmap integration first
```

**Expected Behavior:**
```yaml
blocked_by:
  - dependency_id: infrastructure-fixes
    dependency_type: track
    at_status: not_started
    current_status: completed  # ✅ Auto-updated when blocker completes
    blocking: false  # ✅ Auto-calculated: current_status has passed at_status
    reason: Must fix roadmap integration first
```

**Impact:**
- Dependency queries show false positives (tracks appear blocked when they're not)
- Users must manually check if blockers are resolved
- `framework/scripts/roadmap-update.py --unblock` may be needed to force refresh

**Workaround:**
```bash
# Manually refresh all dependency statuses
python3 framework/scripts/roadmap-update.py --refresh-dependencies
```
*(Note: This command may not exist yet)*

**Root Cause:** The system doesn't implement reverse dependency updates. When track A completes, it doesn't notify tracks B, C, D that depend on it to update their `current_status` fields.

**Files Affected:**
- All track YAML files with `blocked_by` entries
- `framework/scripts/roadmap-update.py` - No reverse dependency update logic

**Design Questions:**
- Should every status change trigger a scan of all dependents?
- Should there be a periodic "refresh dependencies" background job?
- Should dependencies be bidirectional (track knows its dependents)?

---

### Why These Limitations Exist

These issues were discovered during the **infrastructure-fixes-1 sprint completion** (2025-11-10) - the first real-world test of the hierarchical roadmap system's cascade update logic.

The system was designed with:
1. ✅ **Core status progression** - Task → Sprint → Track (works correctly)
2. ✅ **Timestamp tracking** - Started, completed dates (works correctly)
3. ❌ **Aggregate calculations** - Not implemented yet
4. ❌ **Activity type classification** - Not implemented yet
5. ❌ **Reverse dependency updates** - Not implemented yet

This is a classic MVP trade-off: the core functionality works (status progression), but the "nice-to-have" features (metrics, detailed logging, auto-unblocking) were deferred.

---

### Prioritization

**Should Fix Soon (P1):**
- Track progress field calculation - Critical for roadmap visibility
- Activity type classification - Important for analytics

**Can Defer (P2):**
- Dependency auto-update - Workaround exists (manual check)

**Design Work Needed:**
- How should aggregate calculations be triggered? (On-demand vs. automatic)
- Should dependencies be bidirectional for efficiency?
- What's the performance impact of cascade updates at scale?

---

### Proposed Fixes

#### Fix 1: Implement Track Progress Calculation

**Location:** `framework/scripts/roadmap-update.py`

**New Function:**
```python
def recalculate_track_progress(track_id: str):
    """Recalculate aggregate progress fields for a track."""
    track_path = find_track_path(track_id)
    track = load_yaml(track_path)

    # Find all sprints in this track
    sprints = find_all_sprints(track_id)

    # Calculate aggregates
    sprints_total = len(sprints)
    sprints_completed = sum(1 for s in sprints if s['status'] == 'completed')

    tasks_total = sum(s['progress']['tasks_total'] for s in sprints)
    tasks_completed = sum(s['progress']['tasks_completed'] for s in sprints)

    completion_percent = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0

    # Update track
    track['progress'] = {
        'sprints_total': sprints_total,
        'sprints_completed': sprints_completed,
        'tasks_total': tasks_total,
        'tasks_completed': tasks_completed,
        'completion_percent': round(completion_percent)
    }

    save_yaml(track_path, track)
```

**Trigger Points:**
- After completing any task in the track
- After completing any sprint in the track
- On-demand via CLI: `roadmap-update.py --recalculate-track <track_id>`

---

#### Fix 2: Activity Type Classification

**Location:** `framework/scripts/roadmap-update.py`

**Implementation:**
```python
ACTIVITY_TYPES = {
    'task_started': 'Task started',
    'task_completed': 'Task completed',
    'sprint_started': 'Sprint started',
    'sprint_completion_gate': 'Sprint entered completion gate',
    'sprint_completed': 'Sprint completed',
    'track_started': 'Track started',
    'track_completed': 'Track completed',
}

def log_activity(obj: dict, activity_type: str, description: str, metadata: dict = None):
    """Add properly typed activity log entry."""
    if activity_type not in ACTIVITY_TYPES:
        raise ValueError(f"Unknown activity type: {activity_type}")

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'activity_type': activity_type,  # ✅ Proper type
        'description': description,
        'actor': 'system',
        'metadata': metadata or {}
    }

    if 'activity_log' not in obj:
        obj['activity_log'] = []
    obj['activity_log'].append(entry)
```

**Changes Required:**
- Replace all `activity_type: unknown` with proper constants
- Update `complete_task()`, `start_task()`, `complete_sprint()` to use constants

---

#### Fix 3: Dependency Auto-Update

**Location:** `framework/scripts/roadmap-update.py`

**New Function:**
```python
def refresh_dependencies(track_id: str = None):
    """Update current_status for all dependencies.

    If track_id provided, only update tracks that depend on it.
    Otherwise, refresh all dependencies system-wide.
    """
    if track_id:
        # Find all tracks that have track_id in their blocked_by
        dependents = find_dependent_tracks(track_id)
    else:
        # Refresh all tracks
        dependents = find_all_tracks()

    for dependent_track_path in dependents:
        track = load_yaml(dependent_track_path)

        for blocker in track.get('blocked_by', []):
            # Fetch current status of blocker
            blocker_track = load_track(blocker['dependency_id'])
            blocker['current_status'] = blocker_track['status']

            # Calculate if still blocking
            blocker['blocking'] = is_status_before(
                blocker['current_status'],
                blocker['at_status']
            )

        save_yaml(dependent_track_path, track)
```

**Trigger Points:**
- After any track status change: `refresh_dependencies(track_id)`
- Periodic refresh: `roadmap-update.py --refresh-all-dependencies`
- On-demand: `roadmap-update.py --refresh-dependencies <track_id>`

---

### Testing Recommendations

When implementing fixes, test with:

1. **Multi-sprint track** - Complete tasks/sprints and verify aggregates cascade
2. **Cross-track dependencies** - Complete blocker and verify dependents update
3. **Activity log queries** - Ensure activity types are filterable
4. **Performance** - Time cascade updates with large roadmaps (100+ tracks)

**Test Data:**
- Use `documentation-system` track (3 sprints, 32 tasks)
- Use `goose-port` → `infrastructure-fixes` dependency chain

---

### Related Documentation

- [ROADMAP_OBJECT_HIERARCHY.md](ROADMAP_OBJECT_HIERARCHY.md) - Data model design
- [ROADMAP_IMPLEMENTATION_PLAN.md](ROADMAP_IMPLEMENTATION_PLAN.md) - Implementation sprints
- [ROADMAP_STATE_UPDATE.md](ROADMAP_STATE_UPDATE.md) - Status update flows
- [ROADMAP_DATA_MODEL_FIX.md](ROADMAP_DATA_MODEL_FIX.md) - Previous data model issues

---

## Future Limitations (Anticipated)

These are potential limitations we anticipate but haven't encountered yet:

### Performance at Scale

**Concern:** With 50+ tracks, 200+ sprints, 1000+ tasks, will cascade updates become slow?

**Mitigation Options:**
- Lazy calculation (only calculate on read)
- Caching layer
- Async background jobs

### Concurrent Updates

**Concern:** What if two agents try to update the same track simultaneously?

**Current Behavior:** File-based YAML locking is not implemented
**Risk:** Last-write-wins, potential data loss

**Mitigation Options:**
- File locking mechanisms
- Transaction log
- Optimistic locking with version numbers

---

## How to Report New Limitations

If you discover new limitations:

1. **Document the issue** - What doesn't work as expected?
2. **Show current vs. expected behavior** - With YAML examples
3. **Identify impact** - Who is affected? How severe?
4. **Suggest workarounds** - Is there a manual fix?
5. **Add to this file** - Keep this document current

**File Location:** `docs/development/ROADMAP_KNOWN_LIMITATIONS.md`

---

**Document Version:** 1.0
**Roadmap System Version:** v2.1 (Hierarchical Structure)
