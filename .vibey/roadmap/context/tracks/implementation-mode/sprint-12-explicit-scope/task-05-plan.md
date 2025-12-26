# Task 05: Add completion detection using HierarchicalTicket

**Task ID**: `01KDC7N5Z4HSMXG430A6WA831Y`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 4000

## Description

Implement completion detection using HierarchicalTicket's built-in methods: `can_transition_to()`, `progress_for_transition()`, and `auto_progress()`. Stop the loop when the scope ticket can be marked complete.

## Architecture Context

**Critical**: HierarchicalTicket already has all the completion logic built in.

The Unified Ticket Architecture provides:
- `can_transition_to(TicketStatus.COMPLETED)` → Checks all criteria
- `progress_for_transition(TicketStatus.COMPLETED)` → Returns Progress(total, completed)
- `auto_progress(context)` → Automatically transitions when criteria met
- Criteria include `CompletableTarget` for child completion tracking

**DO NOT** create separate track/sprint/task completion methods. The HierarchicalTicket abstraction handles this through criteria.

```
HierarchicalTicket.can_transition_to(COMPLETED)
    │
    ├── Checks all criteria in all_criteria
    ├── CompletableTarget criteria check child status
    ├── Excludes deferred children automatically
    └── Returns (can_complete: bool, blocking_reasons: List[str])
```

## Current Behavior (Wrong Approach)

The original plan had type-specific methods:
```python
class TicketCompletionChecker:
    def _check_track_complete(self, track_id: str)   # WRONG
    def _check_sprint_complete(self, sprint_id: str) # WRONG
    def _check_task_complete(self, task_id: str)     # WRONG
```

## Target Behavior (Correct Approach)

Use HierarchicalTicket's built-in methods:
```python
# Check if scope ticket can complete
can_complete, reasons = scope_ticket.can_transition_to(TicketStatus.COMPLETED)

# Get progress toward completion
progress = scope_ticket.progress_for_transition(TicketStatus.COMPLETED)

# Auto-progress the ticket (and log transitions)
transitions = scope_ticket.auto_progress(context)
```

## Implementation Steps

### Step 1: Create ScopeCompletionChecker using HierarchicalTicket methods

```python
# vibey/services/implementation/completion.py

from typing import Tuple, Optional, List
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.enums import TicketStatus
from vibey.roadmap.models.ticket.support import RefreshContext


class ScopeCompletionChecker:
    """
    Check and update completion status using HierarchicalTicket methods.

    Uses the unified ticket architecture's built-in completion logic:
    - can_transition_to() for checking if completion is possible
    - progress_for_transition() for progress tracking
    - auto_progress() for automatic status transitions

    NO type-specific logic (track/sprint/task) - all handled by criteria.
    """

    def __init__(self, ticket_service: "TicketService"):
        """
        Initialize with TicketService for persisting updates.

        Args:
            ticket_service: Service for updating ticket status
        """
        self.ticket_service = ticket_service

    def check_scope_completion(
        self,
        scope_ticket: HierarchicalTicket,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if scope ticket can be completed.

        Uses HierarchicalTicket.can_transition_to() which:
        - Checks all criteria (including child completion via CompletableTarget)
        - Excludes deferred children automatically
        - Handles all hierarchy levels uniformly

        Args:
            scope_ticket: The ticket defining execution scope

        Returns:
            Tuple of (is_complete, message)
        """
        can_complete, blocking_reasons = scope_ticket.can_transition_to(
            TicketStatus.COMPLETED
        )

        if can_complete:
            return True, f"Ticket {scope_ticket.id} ready to complete"

        # Get progress for informative message
        progress = scope_ticket.progress_for_transition(TicketStatus.COMPLETED)
        remaining = progress.total - progress.completed

        return False, f"{remaining} criteria remaining for completion"

    def try_complete_scope(
        self,
        scope_ticket: HierarchicalTicket,
        context: RefreshContext,
    ) -> Tuple[bool, List[str]]:
        """
        Attempt to complete the scope ticket using auto_progress.

        Uses HierarchicalTicket.auto_progress() which:
        - Refreshes automatic criteria
        - Transitions status when all criteria met
        - Logs transitions to the activity log

        Args:
            scope_ticket: The ticket to complete
            context: RefreshContext with activity log

        Returns:
            Tuple of (completed, transitions)
        """
        # Refresh ticket state from service
        refreshed = self.ticket_service.get_ticket(scope_ticket.id)

        # Use auto_progress to attempt transitions
        transitions = refreshed.auto_progress(context)

        # Check if we reached COMPLETED or beyond
        is_completed = refreshed.status in (
            TicketStatus.COMPLETED,
            TicketStatus.PRODUCTION_READY,
            TicketStatus.DEPLOYED,
        )

        if is_completed:
            # Persist the updated status
            self.ticket_service.update(refreshed)

        return is_completed, transitions

    def get_completion_progress(
        self,
        scope_ticket: HierarchicalTicket,
    ) -> dict:
        """
        Get detailed progress toward scope completion.

        Returns:
            Dict with progress details
        """
        progress = scope_ticket.progress_for_transition(TicketStatus.COMPLETED)

        return {
            "total_criteria": progress.total,
            "completed_criteria": progress.completed,
            "remaining": progress.total - progress.completed,
            "percentage": (
                (progress.completed / progress.total * 100)
                if progress.total > 0 else 100
            ),
            "can_complete": progress.completed >= progress.total,
        }
```

### Step 2: Integrate into ImplementationLoop

```python
# In ImplementationLoop class

async def run(self) -> LoopResult:
    """Run the implementation loop."""
    # Create completion checker
    completion_checker = ScopeCompletionChecker(self.ticket_service)

    # Create refresh context for activity logging
    context = RefreshContext(activity_log=[])

    while True:
        # Execute next work item...
        work_item = self.selector.get_next_task(scope=self.config.scope_ticket)

        if work_item is None:
            self.state.stop_reason = "no_more_tasks"
            break

        # Execute the work item...
        await self._execute_work_item(work_item)

        # Check scope completion using HierarchicalTicket methods
        if self.config.scope_ticket:
            is_complete, transitions = completion_checker.try_complete_scope(
                self.config.scope_ticket,
                context,
            )

            if is_complete:
                logger.info(f"Scope completed: {transitions}")
                self.state.stop_reason = "scope_complete"
                break

        # Check limits...
```

### Step 3: Update LoopResult with scope_complete reason

```python
# In state.py or result.py

class StopReason(str, Enum):
    """Reasons the implementation loop stopped."""

    NO_MORE_TASKS = "no_more_tasks"
    SCOPE_COMPLETE = "scope_complete"  # Scope ticket reached COMPLETED
    MAX_TASKS = "max_tasks"
    MAX_TOKENS = "max_tokens"
    USER_INTERRUPT = "user_interrupt"
    ERROR = "error"
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/services/implementation/completion.py` | New ScopeCompletionChecker using HierarchicalTicket methods |
| `vibey/services/implementation/loop.py` | Integrate completion checking |
| `vibey/services/implementation/state.py` | Add SCOPE_COMPLETE stop reason |

## Test Cases

1. Scope with all criteria met → auto_progress transitions to COMPLETED
2. Scope with incomplete children → can_transition_to returns False
3. Single work item scope → Completes when that work item completes
4. Deferred children excluded → Parent can complete with deferred incomplete
5. Progress tracking → Accurate criteria counts

## Acceptance Criteria

- [ ] Uses `can_transition_to()` for completion checking (not type-specific methods)
- [ ] Uses `progress_for_transition()` for progress tracking
- [ ] Uses `auto_progress()` for automatic status transitions
- [ ] NO separate track/sprint/task completion methods
- [ ] Deferred children handled automatically (via HierarchicalTicket)
- [ ] Loop stops with "scope_complete" reason when scope ticket completes
- [ ] Transitions logged via RefreshContext activity_log
