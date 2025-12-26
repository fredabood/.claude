# Task 04: Update TaskSelector for HierarchicalTicket scope

**Task ID**: `01KDC7N5Z3QS3JTJGT536ZWSD3`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 4000

## Description

Modify TaskSelector to accept a HierarchicalTicket as scope, not type-specific track_id/sprint_id parameters. Use HierarchicalTicket properties to navigate hierarchy and find executable work items.

## Architecture Context

TaskSelector operates at Layer 2/3 - it should work with HierarchicalTicket objects, not raw IDs or type-specific parameters.

```
ImplementationLoop
    │
    ▼
TaskSelector.get_next_task(scope: HierarchicalTicket)
    │
    ├── scope.is_ultimate_child → Return this ticket if executable
    ├── scope.descendants → Search descendant work items
    └── Use HierarchicalTicket.is_planned, criteria, status
```

## Current Behavior

```python
class TaskSelector:
    def get_next_task(
        self,
        track_id: Optional[str] = None,  # Type-specific
        sprint_id: Optional[str] = None,  # Type-specific
    ) -> Optional[HierarchicalTicket]:
        # Filters by track_id or sprint_id using SQL queries
```

## Target Behavior

```python
class TaskSelector:
    def get_next_task(
        self,
        scope: Optional[HierarchicalTicket] = None,  # Unified scope
    ) -> Optional[HierarchicalTicket]:
        # Uses HierarchicalTicket properties for hierarchy navigation
```

## Implementation Steps

### Step 1: Update get_next_task() signature and logic

```python
class TaskSelector:
    """
    Selects executable work items using HierarchicalTicket properties.

    Works entirely through the HierarchicalTicket abstraction:
    - Uses is_ultimate_child to identify executable work items
    - Uses descendants to find work within scope
    - Uses is_planned, status, criteria for executability checks
    """

    def __init__(self, ticket_service: TicketService):
        """
        Initialize with TicketService (not db_path).

        Args:
            ticket_service: Service for loading tickets
        """
        self.ticket_service = ticket_service

    def get_next_task(
        self,
        scope: Optional[HierarchicalTicket] = None,
    ) -> Optional[HierarchicalTicket]:
        """
        Find the next executable work item within scope.

        Args:
            scope: Optional HierarchicalTicket defining execution scope.
                  If None, searches entire roadmap.
                  If is_ultimate_child, returns it if executable.
                  If is_parent, searches descendants.

        Returns:
            HierarchicalTicket for the next executable work item, or None
        """
        if scope is None:
            # No scope = all work items
            return self._find_next_executable_global()

        if scope.is_ultimate_child:
            # Single work item - return if executable
            return scope if self._is_executable(scope) else None

        # Parent ticket - search descendants
        return self._find_next_executable_in_scope(scope)

    def _find_next_executable_in_scope(
        self,
        scope: HierarchicalTicket,
    ) -> Optional[HierarchicalTicket]:
        """
        Find next executable work item among scope's descendants.

        Uses HierarchicalTicket.descendants to navigate hierarchy.
        """
        for descendant in scope.descendants:
            # Only consider ultimate children (work items)
            if not descendant.is_ultimate_child:
                continue

            if self._is_executable(descendant):
                return descendant

        return None

    def _is_executable(self, ticket: HierarchicalTicket) -> bool:
        """
        Check if a work item is executable.

        Uses HierarchicalTicket properties:
        - status == NOT_STARTED
        - is_planned == True
        - can_transition_to(IN_PROGRESS) passes
        """
        from vibey.roadmap.models.ticket.enums import TicketStatus

        # Must be not started
        if ticket.status != TicketStatus.NOT_STARTED:
            return False

        # Must be planned
        if not ticket.is_planned:
            return False

        # Must be able to start (dependencies met)
        can_start, _ = ticket.can_transition_to(TicketStatus.IN_PROGRESS)
        return can_start
```

### Step 2: Update get_all_executable() for scope

```python
def get_all_executable(
    self,
    scope: Optional[HierarchicalTicket] = None,
    limit: int = 100,
) -> List[HierarchicalTicket]:
    """
    Get all currently executable work items within scope.

    Args:
        scope: Optional scope ticket. None = entire roadmap.
        limit: Maximum results to return.

    Returns:
        List of executable HierarchicalTickets.
    """
    if scope is None:
        return self._find_all_executable_global(limit)

    if scope.is_ultimate_child:
        return [scope] if self._is_executable(scope) else []

    # Parent - filter descendants
    executable = []
    for descendant in scope.descendants:
        if len(executable) >= limit:
            break

        if descendant.is_ultimate_child and self._is_executable(descendant):
            executable.append(descendant)

    return executable
```

### Step 3: Update count_remaining() for scope

```python
def count_remaining(
    self,
    scope: Optional[HierarchicalTicket] = None,
) -> int:
    """
    Count executable work items within scope.

    Args:
        scope: Optional scope ticket. None = entire roadmap.

    Returns:
        Count of executable work items.
    """
    if scope is None:
        return self._count_executable_global()

    if scope.is_ultimate_child:
        return 1 if self._is_executable(scope) else 0

    # Parent - count descendant work items
    return sum(
        1 for d in scope.descendants
        if d.is_ultimate_child and self._is_executable(d)
    )
```

### Step 4: Remove deprecated methods

Remove or deprecate:
- `_query_candidate_tasks()` with track_id/sprint_id SQL
- Any direct database queries that bypass HierarchicalTicket

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/services/implementation/selector.py` | Replace track_id/sprint_id with scope: HierarchicalTicket |

## Test Cases

1. `get_next_task(scope=parent_ticket)` → Returns first executable descendant
2. `get_next_task(scope=child_ticket)` → Returns that ticket if executable
3. `get_next_task(scope=completed_ticket)` → Returns None
4. `get_all_executable(scope=parent)` → Returns all executable descendants
5. `count_remaining(scope=parent)` → Returns correct count

## Acceptance Criteria

- [ ] `scope: HierarchicalTicket` replaces `track_id`/`sprint_id` parameters
- [ ] Uses `is_ultimate_child` to identify work items
- [ ] Uses `descendants` for hierarchy traversal
- [ ] Uses `is_planned`, `status`, `can_transition_to()` for executability
- [ ] No direct SQL queries with type-specific filters
- [ ] Existing behavior preserved through HierarchicalTicket abstraction
