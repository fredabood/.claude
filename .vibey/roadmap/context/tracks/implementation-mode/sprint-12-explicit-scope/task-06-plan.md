# Task 06: Deprecate --track and --sprint options

**Task ID**: `01KDC7N5Z4HSMXG430A6WA831Z`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2000

## Description

Mark `--track` and `--sprint` as deprecated with warning messages. Map them internally to `--ticket` for backward compatibility. Update help text to recommend `--ticket` instead.

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

### Step 1: Update option help text (implement.py:218-219)

```python
@click.option('--track', help='[DEPRECATED] Use --ticket <track-ulid> instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket <sprint-ulid> instead')
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

    # Map deprecated options to --ticket
    effective_ticket = ticket
    if not effective_ticket:
        if track:
            effective_ticket = track
        elif sprint:
            effective_ticket = sprint

    # Check for explicit scope (using effective_ticket)
    has_scope = all_tickets or effective_ticket

    if not has_scope:
        _show_scope_required_help()
        sys.exit(0)

    # Continue with resolved ticket...
```

### Step 3: Update docstring to mention deprecation

```python
def implement(ctx, all_tickets, yes, ticket, track, sprint, ...):
    """
    Run implementation mode to execute planned tasks.

    REQUIRES explicit scope specification to prevent accidental execution.

    Examples:

      vibey implement --ticket 01KC...     # Execute specific ticket
      vibey implement --all-tickets        # Execute all (with confirmation)
      vibey implement --dry-run            # Preview what would run

    Deprecated options (still work but will be removed):

      --track <ULID>   → Use --ticket <ULID> instead
      --sprint <ULID>  → Use --ticket <ULID> instead
    """
```

### Step 4: Update run_implementation_cmd() to not need track/sprint

Since track/sprint are mapped to ticket before calling, we can simplify:

```python
# Old signature
def run_implementation_cmd(
    track: Optional[str] = None,
    sprint: Optional[str] = None,
    ...
)

# Keep for now but mark as deprecated internally
# Will be removed in future version
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Update help text, add warnings, map to --ticket |

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
- [ ] --ticket takes precedence if both provided
