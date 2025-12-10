# Task 013: Add CLI Command to Sync roadmap.yaml

**Task ID:** dogfooding-bugs-02-task-013
**Bug Addressed:** #12 (New tracks not syncing to roadmap.yaml)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

Users need a CLI command to trigger the sync from ULID files to roadmap.yaml. This makes the sync operation discoverable and controllable.

---

## Implementation

### CLI Command Design

```python
# vibey/cli/commands.py

@roadmap.command()
@click.option('--dry-run', is_flag=True, help='Show what would be synced without applying')
@click.pass_context
def sync(ctx, dry_run: bool):
    """
    Sync roadmap.yaml with ULID track files.

    Updates roadmap.yaml to match the source of truth in tracks/*.yaml files.
    Use --dry-run to preview changes without applying them.
    """
    from vibey.operations.roadmap.sync import sync_roadmap_yaml, sync_progress_counters

    root_dir = ctx.obj.get('root_dir', Path.cwd())
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        click.echo("Error: No roadmap found. Run 'vibey roadmap init' first.", err=True)
        ctx.exit(1)

    # Sync tracks
    click.echo("Syncing tracks..." if not dry_run else "Checking for track changes...")
    report = sync_roadmap_yaml(roadmap_dir, dry_run=dry_run)

    # Display results
    if report['added']:
        click.echo(f"\n  Added tracks ({len(report['added'])}):")
        for track in report['added']:
            click.echo(f"    + {track['id']}: {track['name']}")

    if report['updated']:
        click.echo(f"\n  Updated tracks ({len(report['updated'])}):")
        for track in report['updated']:
            click.echo(f"    ~ {track['id']}: {track['name']}")

    if report['removed']:
        click.echo(f"\n  Removed tracks ({len(report['removed'])}):")
        for track in report['removed']:
            click.echo(f"    - {track['id']}: {track['name']}")

    if not (report['added'] or report['updated'] or report['removed']):
        click.echo("\n  ✓ roadmap.yaml is in sync with ULID files")
    elif dry_run:
        click.echo(f"\n  Would sync: +{len(report['added'])} -{len(report['removed'])} ~{len(report['updated'])}")
        click.echo("  Run without --dry-run to apply changes.")
    else:
        click.echo(f"\n  ✓ Synced: +{len(report['added'])} -{len(report['removed'])} ~{len(report['updated'])}")

    # Sync progress counters
    if not dry_run:
        click.echo("\nUpdating progress counters...")
        progress = sync_progress_counters(roadmap_dir)
        click.echo(f"  Tracks: {progress['tracks_completed']}/{progress['tracks_total']}")
        click.echo(f"  Sprints: {progress['sprints_completed']}/{progress['sprints_total']}")
        click.echo(f"  Tasks: {progress['tasks_completed']}/{progress['tasks_total']}")
        click.echo(f"  Completion: {progress['completion_percent']}%")
```

### Alternative: Subcommand Structure

```python
# If sync is too generic, use subcommand:
# vibey roadmap sync tracks
# vibey roadmap sync progress
# vibey roadmap sync all

@roadmap.group()
def sync():
    """Sync roadmap.yaml with ULID files."""
    pass

@sync.command()
@click.option('--dry-run', is_flag=True)
@click.pass_context
def tracks(ctx, dry_run):
    """Sync track list with tracks/*.yaml files."""
    ...

@sync.command()
@click.pass_context
def progress(ctx):
    """Recalculate progress counters from ULID files."""
    ...

@sync.command()
@click.option('--dry-run', is_flag=True)
@click.pass_context
def all(ctx, dry_run):
    """Sync everything (tracks + progress)."""
    ...
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands.py` | Add `sync` command |
| `vibey/operations/roadmap/__init__.py` | Export sync functions |

---

## Usage Examples

```bash
# Preview sync changes
vibey roadmap sync --dry-run

# Apply sync
vibey roadmap sync

# Example output
$ vibey roadmap sync --dry-run
Checking for track changes...

  Added tracks (2):
    + 01KC2D0JKTE7Z4HCNHST8ZVW4R: unified-architecture-migration
    + 01KC2D0JKVT80AFQ6C1PA8CKJD: dogfooding-bugs

  Would sync: +2 -0 ~0
  Run without --dry-run to apply changes.
```

---

## Testing Strategy

```python
def test_sync_command_dry_run(tmp_path, cli_runner):
    """Dry run shows changes without applying."""
    # Setup with discrepancy
    ...

    result = cli_runner.invoke(cli, ['roadmap', 'sync', '--dry-run'])

    assert result.exit_code == 0
    assert "Would sync" in result.output
    # Verify roadmap.yaml unchanged


def test_sync_command_applies_changes(tmp_path, cli_runner):
    """Sync command applies changes."""
    # Setup with discrepancy
    ...

    result = cli_runner.invoke(cli, ['roadmap', 'sync'])

    assert result.exit_code == 0
    assert "Synced" in result.output
    # Verify roadmap.yaml updated


def test_sync_command_no_roadmap(tmp_path, cli_runner):
    """Error when no roadmap exists."""
    result = cli_runner.invoke(cli, ['roadmap', 'sync'])

    assert result.exit_code == 1
    assert "No roadmap found" in result.output
```

---

## Success Criteria

- [ ] `vibey roadmap sync` command exists
- [ ] `--dry-run` flag works correctly
- [ ] Output is clear and informative
- [ ] Progress counters updated after sync
- [ ] Error handling for missing roadmap

---

## Dependencies

- Task 012 (sync functions implemented)

---

## Notes

This command gives users explicit control over sync timing. Consider adding:
- `--force` to overwrite without confirmation
- `--verbose` for detailed output
- Integration with git hooks for automatic sync on commit
