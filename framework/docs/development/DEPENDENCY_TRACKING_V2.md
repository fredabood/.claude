# Dependency Tracking Design (v2.0)

## Problem

The original dependency tracking system had a critical flaw: **blocked status was never updated**.

- Task `blocked` fields were static (never auto-updated)
- When a dependency completed, dependent tasks weren't notified
- `BlockerComputer` computed blockers on-demand but didn't persist them
- No reverse index to find what needs updating

## Solution: Denormalized Dependency Cache

We added three fields to Task, Sprint, and Track models:

### 1. `depends_on: List[DependencyStatus]`

**Cached status of dependencies for O(1) blocking checks**

```yaml
depends_on:
  - blocker_id: backend-1-task-001
    blocker_type: task
    required_status: completed
    current_status: completed      # ← Cached!
    last_checked: 2025-11-08T15:30:00Z

  - blocker_id: frontend-2-sprint-001
    blocker_type: sprint
    required_status: completed
    current_status: in_progress    # ← Cached!
    last_checked: 2025-11-08T15:30:00Z
```

**Benefits:**
- Check if blocked without loading dependencies: `any(not dep.is_satisfied() for dep in depends_on)`
- See WHY something is blocked (current vs required status)
- Track freshness with `last_checked` timestamp

### 2. `depended_on_by: List[str]`

**Reverse dependency index for O(1) update propagation**

```yaml
# In backend-1-task-001
depended_on_by:
  - backend-1-task-002    # ← These need updating when I complete
  - backend-1-task-005
  - frontend-2-task-010
```

**Benefits:**
- When task completes, instantly know what to update
- No need to scan all tasks to find dependents
- Enables efficient cascade updates

### 3. `blocked: bool`

**Computed from `depends_on` (not `blocked_by`)**

```python
task.blocked = any(not dep.is_satisfied() for dep in task.depends_on)
```

**Model validation enforces consistency:**
- Task initialization fails if `blocked` doesn't match `depends_on`
- Prevents stale data

## Data Model

### DependencyStatus (common.py)

```python
@dataclass
class DependencyStatus:
    """Cached dependency status for fast blocking computation."""

    blocker_id: str          # e.g., "backend-1-task-005"
    blocker_type: str        # task/sprint/track/external
    required_status: str     # e.g., "completed"
    current_status: str      # Cached current status
    last_checked: datetime   # When status was synced

    def is_satisfied(self) -> bool:
        """Check if dependency is satisfied using status progression."""
        status_order = [
            "not_started", "in_progress", "paused",
            "completion_gate_check", "completed",
            "production_gate_check", "production_ready", "deployed"
        ]
        current_idx = status_order.index(self.current_status)
        required_idx = status_order.index(self.required_status)
        return current_idx >= required_idx
```

## Update Flow

### When Task Completes

```
./framework/scripts/roadmap complete backend-1-task-001
│
├─► 1. Update task status
│   └── task.status = COMPLETED
│
├─► 2. Look at depended_on_by
│   └── ["backend-1-task-002", "backend-1-task-005", "frontend-2-task-010"]
│
├─► 3. Update each dependent's depends_on cache
│   For each dependent_id in depended_on_by:
│   ├── Load dependent task/sprint/track
│   ├── Find matching entry in depends_on array
│   ├── Update current_status: "in_progress" → "completed"
│   ├── Update last_checked: now
│   ├── Recompute blocked: any(not d.is_satisfied() for d in depends_on)
│   └── Save dependent
│
└─► 4. Continue cascade (update sprint, track, roadmap)
```

## Migration Strategy

### Phase 1: Add Fields (✅ Done)

- Added `depends_on` and `depended_on_by` to Task, Sprint, Track
- Kept `blocked_by` (deprecated but maintained for compatibility)
- Updated validation to use `depends_on`

### Phase 2: Build Indexes (Next)

Create migration script to populate new fields from existing data:

```python
def migrate_to_cached_dependencies():
    """Populate depends_on and depended_on_by from dependencies."""

    # For each object (task/sprint/track):
    for obj in all_objects:
        # 1. Build depends_on from dependencies
        obj.depends_on = []
        for dep in obj.dependencies:
            status = get_current_status(dep.target_id, dep.type)
            obj.depends_on.append(DependencyStatus(
                blocker_id=dep.target_id,
                blocker_type=dep.type.value,
                required_status=dep.target_status,
                current_status=status,
                last_checked=datetime.now(timezone.utc)
            ))

        # 2. Recompute blocked
        obj.blocked = any(not d.is_satisfied() for d in obj.depends_on)

    # Build reverse index (depended_on_by)
    reverse_index = defaultdict(list)
    for obj in all_objects:
        for dep_status in obj.depends_on:
            reverse_index[dep_status.blocker_id].append(obj.id)

    # Apply reverse index
    for obj in all_objects:
        obj.depended_on_by = reverse_index[obj.id]
```

### Phase 3: Update roadmap-update.py (Next)

```python
def complete_task(fs, task_id, completed_by):
    # ... existing code ...

    # NEW: Update depended_on_by cascade
    for dependent_id in task.depended_on_by:
        update_dependent_cache(fs, dependent_id, task_id, "completed")

def update_dependent_cache(fs, dependent_id, blocker_id, new_status):
    """Update cached dependency status in a dependent."""
    dependent = load_object(fs, dependent_id)

    # Find and update matching dependency
    for dep_status in dependent.depends_on:
        if dep_status.blocker_id == blocker_id:
            dep_status.current_status = new_status
            dep_status.last_checked = datetime.now(timezone.utc)
            break

    # Recompute blocked
    dependent.blocked = any(not d.is_satisfied() for d in dependent.depends_on)

    save_object(fs, dependent)
```

### Phase 4: Remove Deprecated Fields (Future)

- Remove `blocked_by` (replaced by `depends_on`)
- Remove `BlockerComputer.compute_task_blockers()` (no longer needed)
- Update all code to use new system

## Performance Benefits

| Operation | Old System | New System |
|-----------|------------|------------|
| Check if blocked | O(D) file loads | O(1) array scan |
| Complete task | O(1) update | O(R) updates (R = dependents) |
| Find dependents | O(N) full scan | O(1) lookup |
| Memory overhead | 0 | ~100 bytes/dependency |

Where:
- D = number of dependencies
- R = number of reverse dependencies (depended_on_by)
- N = total number of tasks

## Example YAML

```yaml
tasks:
- id: backend-1-task-002
  title: Implement API endpoint
  status: not_started
  blocked: true                    # Computed from depends_on

  # Source of truth (static config)
  dependencies:
    - type: task
      target_id: backend-1-task-001
      target_status: completed
      reason: Need database schema first

  # NEW: Cached dependency status (for fast blocking check)
  depends_on:
    - blocker_id: backend-1-task-001
      blocker_type: task
      required_status: completed
      current_status: in_progress   # ← Currently blocking!
      last_checked: 2025-11-08T15:30:00Z

  # NEW: Reverse index (who depends on me)
  depended_on_by:
    - backend-1-task-003
    - backend-1-task-005

  # DEPRECATED (kept for migration compatibility)
  blocked_by:
    - dependency_id: backend-1-task-001
      dependency_type: task
      current_status: in_progress
      required_status: completed
      blocking_since: 2025-11-08T10:00:00Z
```

## API Usage

```python
from roadmap.models import Task, DependencyStatus

# Check if task is blocked (O(1))
if task.is_blocked():
    print(f"Task is blocked by {len(task.get_unsatisfied_dependencies())} dependencies")

# See what's blocking
for dep in task.get_unsatisfied_dependencies():
    print(f"  - {dep.blocker_id}: {dep.current_status} (need {dep.required_status})")

# Update dependent when completing
for dependent_id in task.depended_on_by:
    update_dependent_cache(dependent_id, task.id, "completed")

# Compute fresh blocked status
task.blocked = task.compute_blocked_status()
```

## Validation

Models enforce these invariants:

1. **`blocked` matches `depends_on`:**
   ```python
   has_unsatisfied = any(not d.is_satisfied() for d in depends_on)
   assert blocked == has_unsatisfied
   ```

2. **`dependencies` is source of truth:**
   - `depends_on` is a cache of `dependencies` + current status
   - Changes to `dependencies` require rebuilding `depends_on`

3. **Bidirectional consistency:**
   - If A depends on B, then B.depended_on_by contains A
   - Enforced by migration script, maintained by update logic

## Future Enhancements

1. **Stale detection:** Flag entries where `last_checked` is old
2. **Lazy refresh:** Only update caches when queried
3. **Batch updates:** Update multiple dependents in one pass
4. **Conflict resolution:** Handle concurrent updates
5. **Audit logging:** Track when dependencies change

## Files Modified

- `framework/roadmap/models/common.py` - Added `DependencyStatus`
- `framework/roadmap/models/task.py` - Added fields, updated validation
- `framework/roadmap/models/sprint.py` - Added fields, updated validation
- `framework/roadmap/models/track.py` - Added fields, updated validation
- `framework/roadmap/models/__init__.py` - Export `DependencyStatus`
