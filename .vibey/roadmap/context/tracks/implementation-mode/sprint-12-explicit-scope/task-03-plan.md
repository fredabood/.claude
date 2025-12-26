# Task 03: Implement --ticket ULID option for targeted execution

**Task ID**: `01KDC7N5Z2FQZEH01CCXKXQZ91`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 5000

## Description

Add `--ticket` option accepting a ULID. Use TicketService to load the ticket as a HierarchicalTicket, then execute all descendant work items until the ticket can be marked complete.

## Architecture Context

**Critical**: This task demonstrates proper Layer 3/4 integration.

The CLI (Layer 4) MUST interact through TicketService (Layer 3):
- NO direct filesystem access to `tracks/`, `sprints/`, `tasks/` directories
- NO type detection logic (`target_ticket_type == "track"`)
- Use `TicketService.get_ticket(ulid)` to load any ticket
- Use `HierarchicalTicket` properties for hierarchy navigation

```
CLI (Layer 4)
    │
    ▼
TicketService.get_ticket(ulid) → HierarchicalTicket (Layer 3)
    │
    ├── ticket.is_parent → Has children to execute
    ├── ticket.is_ultimate_child → Single work item
    ├── ticket.descendants → All descendant tickets
    └── ticket.can_transition_to() → Completion check
```

## Current Behavior

- `--track <ULID>` filters by track_id (leaks storage implementation)
- `--sprint <ULID>` filters by sprint_id (leaks storage implementation)
- Two separate options, type-aware

## Target Behavior

- Single `--ticket <ULID>` option
- TicketService loads ticket (type-agnostic)
- HierarchicalTicket properties determine behavior:
  - `is_ultimate_child` → Execute just this work item
  - `is_parent` → Execute all descendant work items
- No knowledge of track/sprint/task at CLI level

## Implementation Steps

### Step 1: Resolve --ticket using TicketService

```python
from vibey.services.ticket_service import TicketService, TicketNotFoundError
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

def implement(ctx, all_tickets, yes, ticket, track, sprint, ...):
    # ... scope check from Task 01 ...

    # Resolve --ticket to HierarchicalTicket via TicketService
    scope_ticket: Optional[HierarchicalTicket] = None

    if ticket:
        try:
            service = TicketService()
            scope_ticket = service.get_ticket(ticket)
        except TicketNotFoundError:
            console.print(f"[red]Error:[/red] Ticket not found: {ticket}")
            sys.exit(1)

    # Handle deprecated --track/--sprint (Task 06 will add warnings)
    elif track:
        try:
            service = TicketService()
            scope_ticket = service.get_ticket(track)
        except TicketNotFoundError:
            console.print(f"[red]Error:[/red] Ticket not found: {track}")
            sys.exit(1)

    elif sprint:
        try:
            service = TicketService()
            scope_ticket = service.get_ticket(sprint)
        except TicketNotFoundError:
            console.print(f"[red]Error:[/red] Ticket not found: {sprint}")
            sys.exit(1)

    # Pass HierarchicalTicket to implementation
    exit_code = run_implementation_cmd(
        scope_ticket=scope_ticket,  # HierarchicalTicket or None
        all_tickets=all_tickets,
        max_tasks=max_tasks,
        max_tokens=max_tokens,
        dry_run=dry_run,
        background=background,
    )
    sys.exit(exit_code)
```

### Step 2: Update run_implementation_cmd() to use HierarchicalTicket

```python
def run_implementation_cmd(
    scope_ticket: Optional[HierarchicalTicket] = None,
    all_tickets: bool = False,
    max_tasks: Optional[int] = None,
    max_tokens: Optional[int] = None,
    dry_run: bool = False,
    background: bool = False,
) -> int:
    """
    Run implementation mode.

    Args:
        scope_ticket: Optional HierarchicalTicket defining execution scope.
                     If None and all_tickets=True, executes entire roadmap.
                     If provided, executes this ticket and its descendants.
        all_tickets: Execute all tickets (requires scope_ticket=None)
        ...
    """
    # ... existing setup ...

    # Create configuration with scope ticket
    config = ImplementConfig(
        max_tasks=max_tasks,
        max_tokens=max_tokens,
        state_path=state_path,
        scope_ticket=scope_ticket,  # HierarchicalTicket, not track_id/sprint_id
        auto_save=True,
    )
```

### Step 3: Update ImplementConfig to use HierarchicalTicket

```python
# vibey/services/implementation/config.py

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

@dataclass
class ImplementConfig:
    """Configuration for implementation mode."""

    # Token/task limits
    max_tasks: Optional[int] = None
    max_tokens: Optional[int] = None

    # State management
    state_path: Optional[Path] = None
    auto_save: bool = True

    # Scope definition - unified approach
    scope_ticket: Optional[HierarchicalTicket] = None
    """
    The ticket defining execution scope.

    - None: Execute all tickets (requires explicit --all-tickets flag)
    - is_ultimate_child: Execute just this work item
    - is_parent: Execute all descendant work items

    The loop uses scope_ticket.descendants to find executable work.
    """

    # DEPRECATED: Remove in future version
    # track_id: Optional[str] = None
    # sprint_id: Optional[str] = None
```

### Step 4: Display scope information

```python
def _show_scope_info(scope_ticket: Optional[HierarchicalTicket], all_tickets: bool) -> None:
    """Display what scope will be executed."""
    if all_tickets:
        console.print("[bold]Scope:[/bold] Entire roadmap")
        return

    if scope_ticket is None:
        return

    # Use HierarchicalTicket properties (type-agnostic)
    if scope_ticket.is_ultimate_child:
        console.print(f"[bold]Scope:[/bold] Single work item: {scope_ticket.name}")
    elif scope_ticket.is_parent:
        descendant_count = len([d for d in scope_ticket.descendants if d.is_ultimate_child])
        console.print(
            f"[bold]Scope:[/bold] {scope_ticket.name}\n"
            f"       {descendant_count} work items in scope"
        )
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Use TicketService for --ticket resolution |
| `vibey/services/implementation/config.py` | Replace track_id/sprint_id with scope_ticket |

## Test Cases

1. `vibey implement --ticket <parent-ulid>` → Executes all descendants
2. `vibey implement --ticket <child-ulid>` → Executes just that work item
3. `vibey implement --ticket <invalid-ulid>` → Error: "Ticket not found"
4. `vibey implement --ticket <ulid> --dry-run` → Shows scope without executing

## Acceptance Criteria

- [ ] `--ticket` loads ticket via TicketService (not filesystem)
- [ ] No type detection code (no "track"/"sprint"/"task" strings in CLI)
- [ ] HierarchicalTicket properties used for behavior:
  - [ ] `is_ultimate_child` → Single work item execution
  - [ ] `is_parent` → Descendant work items execution
  - [ ] `descendants` → Finding executable work
- [ ] Invalid ULID shows clear error via TicketNotFoundError
- [ ] ImplementConfig uses `scope_ticket: HierarchicalTicket`
