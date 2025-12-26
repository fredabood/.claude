# Task 01: Remove default full-roadmap execution

**Task ID**: `01KDC7N5Z1G71B3E111RJT4S8V`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2000

## Description

Change `vibey implement` without arguments to show usage help instead of executing all tasks. Display available options and prompt user to specify scope explicitly.

## Architecture Context

This task follows the Unified Ticket Architecture principle that the CLI (Layer 4) should interact through the TicketService (Layer 3), not directly with storage. The scope check itself doesn't need TicketService - it just validates that the user provided explicit scope before proceeding.

## Current Behavior

```python
# vibey/cli/implement.py
@click.group(invoke_without_command=True)
@click.option('--track', help='Only tasks in this track (ULID)')
@click.option('--sprint', help='Only tasks in this sprint (ULID)')
def implement(ctx, track, sprint, max_tasks, max_tokens, dry_run, background):
    if ctx.invoked_subcommand is not None:
        return

    # PROBLEM: This runs ALL tasks by default when no scope specified
    exit_code = run_implementation_cmd(...)
```

## Target Behavior

When `vibey implement` is called without `--all-tickets` or `--ticket`:
1. Show a help message explaining the explicit scope requirement
2. List available options with examples
3. Exit with code 0 (informational, not an error)

## Implementation Steps

### Step 1: Add scope check in `implement()` function

```python
@click.group(invoke_without_command=True)
@click.option('--all-tickets', is_flag=True, help='Execute all planned tickets (requires confirmation)')
@click.option('--ticket', help='Execute specific ticket by ULID')
@click.option('--track', help='[DEPRECATED] Use --ticket instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket instead')
@click.option('--max-tasks', type=int, help='Stop after N tasks')
@click.option('--max-tokens', type=int, help='Stop after N tokens')
@click.option('--dry-run', is_flag=True, help='Show what would run without executing')
@click.option('--background', is_flag=True, help='Run as background process')
@click.pass_context
def implement(ctx, all_tickets, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
    """
    Run implementation mode to execute planned tickets.

    REQUIRES explicit scope specification to prevent accidental execution.
    """
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is not None:
        return

    # Check for explicit scope
    has_scope = all_tickets or ticket or track or sprint

    if not has_scope:
        _show_scope_required_help()
        sys.exit(0)

    # Continue with execution...
```

### Step 2: Add helper function `_show_scope_required_help()`

```python
def _show_scope_required_help() -> None:
    """Display help message when no scope is specified."""
    console.print(
        Panel(
            "[bold cyan]Implementation Mode[/bold cyan]\n\n"
            "[yellow]Explicit scope required.[/yellow]\n\n"
            "To prevent accidental execution, you must specify what to run:\n\n"
            "  [bold]vibey implement --ticket <ULID>[/bold]\n"
            "    Execute a specific ticket and its descendants\n\n"
            "  [bold]vibey implement --all-tickets[/bold]\n"
            "    Execute all planned tickets (will prompt for confirmation)\n\n"
            "  [bold]vibey implement --dry-run[/bold]\n"
            "    Preview what would be executed\n\n"
            "[dim]Use 'vibey implement --help' for all options[/dim]",
            title="Scope Required",
            border_style="yellow",
        )
    )
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Add scope check, add `_show_scope_required_help()` helper |

## Test Cases

1. `vibey implement` → Shows scope required help, exits 0
2. `vibey implement --help` → Shows full help with new options
3. `vibey implement --ticket 01KC...` → Proceeds to execution
4. `vibey implement --all-tickets` → Proceeds to confirmation
5. `vibey implement --dry-run` without scope → Still shows scope required

## Acceptance Criteria

- [ ] `vibey implement` without args shows helpful message
- [ ] Exit code is 0 (not an error)
- [ ] Message explains how to specify scope
- [ ] Message uses unified terminology ("ticket" not "track/sprint/task")
- [ ] Existing scope options (`--track`, `--sprint`) still work (for now)
