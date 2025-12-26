# Task 02: Add --all-tickets flag for full roadmap execution

**Task ID**: `01KDC7N5Z2FQZEH01CCXKXQZ90`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2000

## Description

Implement `--all-tickets` flag that explicitly enables full-roadmap execution. This flag replaces the current default behavior. Add confirmation prompt with ticket count.

## Architecture Context

This task uses TicketService to get the count of executable tickets for the confirmation message. The CLI interacts through the service layer, not directly with the database.

## Current Behavior

Running `vibey implement` without filters executes ALL planned tasks without warning.

## Target Behavior

1. `--all-tickets` flag required for full roadmap execution
2. When `--all-tickets` is provided, show confirmation prompt with count
3. User must type 'y' or 'yes' to proceed
4. `--yes` or `-y` flag can skip confirmation (for scripting)
5. `--dry-run` skips confirmation (safe operation)

## Implementation Steps

### Step 1: Add `--all-tickets` and `--yes` options

```python
@click.group(invoke_without_command=True)
@click.option('--all-tickets', is_flag=True, help='Execute all planned tickets (requires confirmation)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.option('--ticket', help='Execute specific ticket by ULID')
@click.option('--track', help='[DEPRECATED] Use --ticket instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket instead')
@click.option('--max-tasks', type=int, help='Stop after N tasks')
@click.option('--max-tokens', type=int, help='Stop after N tokens')
@click.option('--dry-run', is_flag=True, help='Show what would run without executing')
@click.option('--background', is_flag=True, help='Run as background process')
@click.pass_context
def implement(ctx, all_tickets, yes, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
```

### Step 2: Add confirmation logic

```python
def implement(ctx, all_tickets, yes, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is not None:
        return

    # Check for explicit scope (from Task 01)
    has_scope = all_tickets or ticket or track or sprint

    if not has_scope:
        _show_scope_required_help()
        sys.exit(0)

    # Handle --all-tickets confirmation
    if all_tickets and not yes and not dry_run:
        if not _confirm_full_execution():
            console.print("[yellow]Aborted.[/yellow]")
            sys.exit(0)

    # Continue with execution...
```

### Step 3: Add confirmation helper using TicketService

```python
def _confirm_full_execution() -> bool:
    """
    Prompt user to confirm full roadmap execution.

    Uses TicketService to get ticket count (Layer 3 interaction).

    Returns:
        True if user confirms, False otherwise.
    """
    from vibey.services.ticket_service import TicketService, TicketServiceError
    from vibey.roadmap.models.ticket.enums import TicketStatus

    try:
        service = TicketService()
        # Search for executable work items (ultimate children that are not_started)
        work_items = service.search(
            status=TicketStatus.NOT_STARTED,
            limit=1000,
        )
        # Filter to ultimate children (work items without children)
        executable = [t for t in work_items if not t.children]
        ticket_count = len(executable)
    except TicketServiceError:
        ticket_count = "unknown number of"

    console.print(
        Panel(
            f"[bold yellow]WARNING: Full Roadmap Execution[/bold yellow]\n\n"
            f"This will execute [bold]{ticket_count}[/bold] planned tickets.\n\n"
            f"[dim]This may take a long time and consume significant tokens.[/dim]",
            border_style="yellow",
        )
    )

    response = click.prompt(
        "Continue with full roadmap execution?",
        type=click.Choice(['y', 'n'], case_sensitive=False),
        default='n',
    )

    return response.lower() == 'y'
```

### Step 4: Update `run_implementation_cmd()` signature

```python
def run_implementation_cmd(
    scope_ticket: Optional[HierarchicalTicket] = None,  # Unified scope
    all_tickets: bool = False,
    max_tasks: Optional[int] = None,
    max_tokens: Optional[int] = None,
    dry_run: bool = False,
    background: bool = False,
) -> int:
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Add --all-tickets, --yes options, confirmation logic |

## Test Cases

1. `vibey implement --all-tickets` → Shows confirmation with ticket count
2. `vibey implement --all-tickets --yes` → Skips confirmation, executes
3. `vibey implement --all-tickets --dry-run` → Skips confirmation (safe)
4. Confirm 'n' → Aborts with message "Aborted."
5. Confirm 'y' → Proceeds with execution

## Acceptance Criteria

- [ ] `--all-tickets` flag available
- [ ] `--yes` flag skips confirmation
- [ ] Confirmation shows ticket count via TicketService
- [ ] 'n' response aborts cleanly
- [ ] 'y' response proceeds with execution
- [ ] `--dry-run` skips confirmation (safe operation)
