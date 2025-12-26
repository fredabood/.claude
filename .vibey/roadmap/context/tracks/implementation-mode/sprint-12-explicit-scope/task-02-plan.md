# Task 02: Add --all-tickets flag for full roadmap execution

**Task ID**: `01KDC7N5Z2FQZEH01CCXKXQZ90`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2000

## Description

Implement `--all-tickets` flag that explicitly enables full-roadmap execution. This flag replaces the current default behavior. Add confirmation prompt: 'This will execute all planned tasks across the entire roadmap. Continue? [y/N]'

## Current Behavior

Running `vibey implement` without filters executes ALL planned tasks without warning.

## Target Behavior

1. `--all-tickets` flag required for full roadmap execution
2. When `--all-tickets` is provided, show confirmation prompt
3. User must type 'y' or 'yes' to proceed
4. `--yes` or `-y` flag can skip confirmation (for scripting)

## Implementation Steps

### Step 1: Add `--all-tickets` and `--yes` options (implement.py:217-224)

```python
@click.group(invoke_without_command=True)
@click.option('--all-tickets', is_flag=True, help='Execute all planned tasks (requires confirmation)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.option('--ticket', help='Execute specific ticket by ULID (track/sprint/task)')
@click.option('--track', help='[DEPRECATED] Use --ticket instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket instead')
@click.option('--max-tasks', type=int, help='Stop after N tasks')
@click.option('--max-tokens', type=int, help='Stop after N tokens')
@click.option('--dry-run', is_flag=True, help='Show what would run without executing')
@click.option('--background', is_flag=True, help='Run as background process')
@click.pass_context
def implement(ctx, all_tickets, yes, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
```

### Step 2: Add confirmation logic in `implement()` function

```python
def implement(ctx, all_tickets, yes, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is not None:
        return

    # Check for explicit scope
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
    exit_code = run_implementation_cmd(
        track=track,
        sprint=sprint,
        ticket=ticket,
        all_tickets=all_tickets,
        max_tasks=max_tasks,
        max_tokens=max_tokens,
        dry_run=dry_run,
        background=background,
    )
    sys.exit(exit_code)
```

### Step 3: Add confirmation helper function (after line 210)

```python
def _confirm_full_execution() -> bool:
    """
    Prompt user to confirm full roadmap execution.

    Returns:
        True if user confirms, False otherwise.
    """
    from vibey.services.implementation import TaskSelector

    project_root = Path.cwd()
    roadmap_root = project_root / ".vibey" / "roadmap"

    try:
        selector = TaskSelector(roadmap_root)
        task_count = selector.count_remaining()
    except Exception:
        task_count = "unknown number of"

    console.print(
        Panel(
            f"[bold yellow]WARNING: Full Roadmap Execution[/bold yellow]\n\n"
            f"This will execute [bold]{task_count}[/bold] planned tasks.\n\n"
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

### Step 4: Update `run_implementation_cmd()` signature (line 273)

```python
def run_implementation_cmd(
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    ticket: Optional[str] = None,       # NEW
    all_tickets: bool = False,           # NEW
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

1. `vibey implement --all-tickets` → Shows confirmation, waits for input
2. `vibey implement --all-tickets --yes` → Skips confirmation, executes
3. `vibey implement --all-tickets --dry-run` → Skips confirmation (dry-run is safe)
4. Confirm 'n' → Aborts with message "Aborted."
5. Confirm 'y' → Proceeds with execution

## Acceptance Criteria

- [ ] `--all-tickets` flag available
- [ ] `--yes` flag skips confirmation
- [ ] Confirmation shows task count
- [ ] 'n' response aborts cleanly
- [ ] 'y' response proceeds with execution
- [ ] `--dry-run` skips confirmation (safe operation)
