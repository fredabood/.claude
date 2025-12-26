# Task 04: Update TaskSelector for hierarchical ticket scope

**Task ID**: `01KDC7N5Z3QS3JTJGT536ZWSD3`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 4000

## Description

Modify TaskSelector to filter tasks based on parent ticket ULID. Implement hierarchy traversal: if ULID is a track, include all sprints/tasks; if sprint, include all tasks; if task, include only that task and its criteria.

## Current Behavior (selector.py)

```python
class TaskSelector:
    def get_next_task(
        self,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
    ) -> Optional[HierarchicalTicket]:
        # Filters by track_id or sprint_id only
```

## Target Behavior

```python
class TaskSelector:
    def get_next_task(
        self,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        task_id: Optional[str] = None,  # NEW: Single task execution
    ) -> Optional[HierarchicalTicket]:
```

## Implementation Steps

### Step 1: Add task_id parameter to all query methods (selector.py)

```python
def get_next_task(
    self,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    task_id: Optional[str] = None,  # NEW
) -> Optional[HierarchicalTicket]:
    """
    Find the next planned and unblocked task.

    Args:
        track_id: Optional track ULID to filter by
        sprint_id: Optional sprint ULID to filter by
        task_id: Optional specific task ULID to execute (single task mode)

    Returns:
        HierarchicalTicket for the next executable task, or None
    """
    # If specific task requested, just return that one
    if task_id:
        return self._get_specific_task(task_id)

    # Existing logic for track/sprint filtering
    candidates = self._query_candidate_tasks(...)
```

### Step 2: Add _get_specific_task() method

```python
def _get_specific_task(self, task_id: str) -> Optional[HierarchicalTicket]:
    """
    Get a specific task by ULID if it's executable.

    Args:
        task_id: Task ULID

    Returns:
        HierarchicalTicket if task exists and is executable, None otherwise
    """
    conn = get_connection(db_path=self.db_path)

    query = """
        SELECT
            t.id, t.title, t.description, t.sprint_id, t.track_id,
            t.roadmap_id, t.task_type, t.status, t.blocked, t.created,
            t.started, t.completed, t.priority, t.estimated_tokens, t.complexity
        FROM tasks t
        WHERE t.id = ?
          AND t.status = 'not_started'
          AND t.blocked = 0
    """

    try:
        cursor = conn.execute(query, [task_id])
        row = cursor.fetchone()

        if row is None:
            return None

        task_data = dict(row)

        # Check if planned
        if self._is_task_planned(task_id):
            return self._load_task_as_ticket(task_data)

        return None

    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        return None
```

### Step 3: Update get_all_executable() for single task mode

```python
def get_all_executable(
    self,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    task_id: Optional[str] = None,  # NEW
    limit: int = 100,
) -> List[HierarchicalTicket]:
    """
    Get all currently executable tasks.

    If task_id is provided, returns only that task (if executable).
    """
    # Single task mode
    if task_id:
        task = self._get_specific_task(task_id)
        return [task] if task else []

    # Existing track/sprint filtering
    candidates = self._query_candidate_tasks(...)
```

### Step 4: Update count_remaining() for single task mode

```python
def count_remaining(
    self,
    track_id: Optional[str] = None,
    sprint_id: Optional[str] = None,
    task_id: Optional[str] = None,  # NEW
) -> int:
    """Count tasks that could be executed."""
    if task_id:
        task = self._get_specific_task(task_id)
        return 1 if task else 0

    # Existing logic
    candidates = self._query_candidate_tasks(...)
    return len(candidates)
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/services/implementation/selector.py` | Add task_id param, _get_specific_task() |

## Test Cases

1. `get_next_task(task_id="01KC...")` → Returns only that task
2. `get_next_task(task_id="completed-task")` → Returns None
3. `get_next_task(task_id="blocked-task")` → Returns None
4. `get_all_executable(task_id="01KC...")` → Returns list with 1 task
5. `count_remaining(task_id="01KC...")` → Returns 1 or 0

## Acceptance Criteria

- [ ] task_id parameter added to all query methods
- [ ] Single task mode returns only that specific task
- [ ] Blocked/completed tasks correctly filtered
- [ ] count_remaining returns accurate count for single task
- [ ] Existing track_id/sprint_id filtering unchanged
