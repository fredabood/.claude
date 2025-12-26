# Task 06: Deprecate --track and --sprint options

**Task ID**: `01KDC7N5Z4HSMXG430A6WA831Z`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2000

## Description

Mark `--track` and `--sprint` as deprecated with warning messages. They internally resolve to the same TicketService lookup as `--ticket`. Update help text to recommend `--ticket` instead.

## Architecture Context

Both `--track` and `--sprint` will use the same `TicketService.get_ticket(ulid)` call as `--ticket`. The unified architecture means there's no difference in how these ULIDs are handled - TicketService loads any ticket regardless of type.

## Current Behavior

```bash
vibey implement --track 01KC...   # Works without warning
vibey implement --sprint 01KC...  # Works without warning
```

## Target Behavior

```bash
vibey implement --track 01KC...
# ⚠️ Warning: --track is deprecated. Use --ticket 01KC... instead.
# (still executes)

vibey implement --sprint 01KC...
# ⚠️ Warning: --sprint is deprecated. Use --ticket 01KC... instead.
# (still executes)
```

## Implementation Steps

### Step 1: Update option help text

```python
@click.option('--track', help='[DEPRECATED] Use --ticket instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket instead')
```

### Step 2: Add deprecation warnings in implement() function

```python
def implement(ctx, all_tickets, yes, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is not None:
        return

    # Deprecation warnings
    if track:
        console.print(
            f"[yellow]Warning:[/yellow] --track is deprecated. "
            f"Use [bold]--ticket {track}[/bold] instead.\n"
        )

    if sprint:
        console.print(
            f"[yellow]Warning:[/yellow] --sprint is deprecated. "
            f"Use [bold]--ticket {sprint}[/bold] instead.\n"
        )

    # Resolve to scope_ticket (same code path for all three options)
    scope_ticket: Optional[HierarchicalTicket] = None
    ulid_to_resolve = ticket or track or sprint  # --ticket takes precedence

    if ulid_to_resolve:
        try:
            service = TicketService()
            scope_ticket = service.get_ticket(ulid_to_resolve)
        except TicketNotFoundError:
            console.print(f"[red]Error:[/red] Ticket not found: {ulid_to_resolve}")
            sys.exit(1)

    # Check for explicit scope
    has_scope = all_tickets or scope_ticket is not None

    if not has_scope:
        _show_scope_required_help()
        sys.exit(0)

    # Continue with execution...
```

### Step 3: Update docstring to mention deprecation

```python
def implement(ctx, all_tickets, yes, ticket, track, sprint, ...):
    """
    Run implementation mode to execute planned tickets.

    REQUIRES explicit scope specification to prevent accidental execution.

    \b
    SCOPE OPTIONS (one required):
      --all-tickets         Execute entire roadmap (with confirmation)
      --ticket ULID         Execute specific ticket and its descendants

    \b
    EXAMPLES:
      vibey implement --ticket 01KC...     # Execute specific ticket
      vibey implement --all-tickets        # Execute all (with confirmation)
      vibey implement --dry-run            # Preview what would run

    \b
    DEPRECATED OPTIONS (still work, will be removed):
      --track <ULID>   → Use --ticket <ULID> instead
      --sprint <ULID>  → Use --ticket <ULID> instead
    """
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Update help text, add warnings, unified ULID resolution |

## Test Cases

1. `vibey implement --track 01KC...` → Shows deprecation warning, executes
2. `vibey implement --sprint 01KC...` → Shows deprecation warning, executes
3. `vibey implement --ticket 01KC...` → No warning, executes
4. `vibey implement --track X --ticket Y` → Uses --ticket, shows warning for --track
5. `vibey implement --help` → Shows [DEPRECATED] in help

## Acceptance Criteria

- [ ] Help text shows [DEPRECATED] for --track and --sprint
- [ ] Deprecation warning printed when using --track
- [ ] Deprecation warning printed when using --sprint
- [ ] Warning suggests using --ticket with same ULID
- [ ] Deprecated options still work (backward compatible)
- [ ] All three options use same TicketService.get_ticket() code path
- [ ] --ticket takes precedence if multiple provided
