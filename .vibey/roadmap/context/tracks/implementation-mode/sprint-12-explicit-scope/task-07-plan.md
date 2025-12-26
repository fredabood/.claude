# Task 07: Update CLI help and documentation

**Task ID**: `01KDC7N5Z5KZACV9SBDBM4ZNPJ`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2500

## Description

Update vibey implement --help output to reflect new options. Update CLI_REFERENCE.md with new usage patterns. Add examples for --ticket with different ticket types.

## Current State

- `vibey implement --help` shows existing options (--track, --sprint, --max-tasks, etc.)
- CLI_REFERENCE.md does not have an `implement` command section
- No usage examples for the new explicit scope workflow

## Target State

- `--help` output reflects new options (--all-tickets, --ticket, --yes)
- Deprecated options clearly marked in help text
- CLI_REFERENCE.md includes complete `implement` command documentation
- Clear examples for each scope type

## Implementation Steps

### Step 1: Update implement() docstring (implement.py)

```python
@click.group(invoke_without_command=True)
@click.option('--all-tickets', is_flag=True, help='Execute all planned tasks (requires confirmation)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.option('--ticket', help='Execute specific ticket by ULID (track/sprint/task)')
@click.option('--track', help='[DEPRECATED] Use --ticket <track-ulid> instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket <sprint-ulid> instead')
@click.option('--max-tasks', type=int, help='Stop after N tasks')
@click.option('--max-tokens', type=int, help='Stop after N tokens')
@click.option('--dry-run', is_flag=True, help='Show what would run without executing')
@click.option('--background', is_flag=True, help='Run as background process')
@click.pass_context
def implement(ctx, all_tickets, yes, ticket, track, sprint, max_tasks, max_tokens, dry_run, background):
    """
    Run implementation mode to execute planned tasks.

    REQUIRES explicit scope specification to prevent accidental execution.

    \b
    SCOPE OPTIONS (one required):
      --all-tickets         Execute entire roadmap (with confirmation)
      --ticket ULID         Execute specific track, sprint, or task

    \b
    EXAMPLES:
      vibey implement --ticket 01KC...     # Execute specific ticket
      vibey implement --all-tickets        # Execute all (with confirmation)
      vibey implement --all-tickets --yes  # Execute all (no confirmation)
      vibey implement --dry-run            # Preview what would run

    \b
    DEPRECATED (still work):
      --track ULID   → Use --ticket ULID instead
      --sprint ULID  → Use --ticket ULID instead
    """
```

### Step 2: Update _show_scope_required_help() message

```python
def _show_scope_required_help():
    """Show help when no scope is specified."""
    console.print(
        Panel(
            "[bold]Explicit Scope Required[/bold]\n\n"
            "The implement command requires explicit scope to prevent accidental execution.\n\n"
            "[bold cyan]Options:[/bold cyan]\n"
            "  --all-tickets       Execute entire roadmap (with confirmation)\n"
            "  --ticket ULID       Execute specific track, sprint, or task\n\n"
            "[bold cyan]Examples:[/bold cyan]\n"
            "  vibey implement --ticket 01KC2D0JK9...   [dim]# Execute track[/dim]\n"
            "  vibey implement --ticket 01KC2D0JKVT... [dim]# Execute sprint[/dim]\n"
            "  vibey implement --ticket 01KC2D0JK7R... [dim]# Execute task[/dim]\n"
            "  vibey implement --all-tickets           [dim]# Execute all[/dim]\n"
            "  vibey implement --dry-run               [dim]# Preview only[/dim]",
            title="[bold yellow]vibey implement[/bold yellow]",
            border_style="yellow",
        )
    )
```

### Step 3: Add implement section to CLI_REFERENCE.md

Add new section to `docs/reference/CLI_REFERENCE.md`:

```markdown
## implement

Run implementation mode for autonomous task execution.

**Usage:**
```bash
vibey implement [OPTIONS] [COMMAND]
```

**Description:**
Implementation mode executes planned tasks autonomously. Requires explicit scope
specification to prevent accidental full-roadmap execution.

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--all-tickets` | Flag | Execute all planned tasks across roadmap (requires confirmation) |
| `--yes, -y` | Flag | Skip confirmation prompts |
| `--ticket` | ULID | Execute specific ticket (auto-detects track/sprint/task) |
| `--track` | ULID | **[DEPRECATED]** Use --ticket instead |
| `--sprint` | ULID | **[DEPRECATED]** Use --ticket instead |
| `--max-tasks` | Integer | Stop after N tasks |
| `--max-tokens` | Integer | Stop after N tokens consumed |
| `--dry-run` | Flag | Preview tasks without executing |
| `--background` | Flag | Run as background process |

**Examples:**

```bash
# Execute specific track
vibey implement --ticket 01KC2D0JK9JKQXGQW6MQEB0JZP

# Execute specific sprint
vibey implement --ticket 01KC2D0JKVT80AFQ6C1PA8CKJD

# Execute specific task
vibey implement --ticket 01KC2D0JK7READW9KAK1HBX4B8

# Execute all with confirmation
vibey implement --all-tickets

# Execute all without confirmation (for scripts)
vibey implement --all-tickets --yes

# Preview without executing
vibey implement --ticket 01KC... --dry-run

# Limit execution
vibey implement --ticket 01KC... --max-tasks 10 --max-tokens 50000
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `pause` | Pause current implementation session |
| `resume` | Resume paused session |
| `status` | Show current session status |
| `stop` | Stop implementation session |

**Notes:**
- Running bare `vibey implement` without scope shows help
- `--ticket` auto-detects ticket type from ULID
- Track ULIDs execute all tasks in all sprints
- Sprint ULIDs execute all tasks in that sprint
- Task ULIDs execute just that single task
- Parent tickets are auto-completed when all children finish
```

### Step 4: Run docs generator to regenerate CLI_REFERENCE.md

After implementing changes:

```bash
vibey docs generate-cli
```

This regenerates the reference from actual command introspection, so Step 3
content will be auto-generated from the docstring and option definitions.

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/implement.py` | Update docstring, help texts, scope help message |
| `docs/reference/CLI_REFERENCE.md` | Auto-generated after code changes |

## Test Cases

1. `vibey implement --help` → Shows new options and examples
2. `vibey implement` (bare) → Shows scope required help with examples
3. Check deprecated options show `[DEPRECATED]` in help
4. `vibey docs generate-cli` → Regenerates reference with implement section
5. `vibey docs check-drift` → No drift after regeneration

## Acceptance Criteria

- [ ] Docstring has clear examples section
- [ ] Help text shows deprecated status for --track/--sprint
- [ ] Bare command shows helpful scope required message
- [ ] CLI_REFERENCE.md includes implement section after regeneration
- [ ] No documentation drift after changes
