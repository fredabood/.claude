# Task 008: Add Structure Validation to CLI

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXX`
**Bug Addressed:** #19
**Complexity:** Medium
**Priority:** Medium
**Type:** Development

## Problem Statement

After migration, we need a CLI command to validate that no hierarchical ULID directories exist and that the flat structure is correct.

## Implementation Plan

### Step 1: Create validate-structure command

Add new CLI command in `vibey/cli/commands.py`:

```python
@roadmap.command('validate-structure')
@click.option('--fix', is_flag=True, help='Automatically fix issues')
def validate_structure_cmd(fix: bool):
    """Validate roadmap directory structure is flat (no ULID directories)."""
    roadmap_dir = Path('.vibey/roadmap')
    issues = []

    # Check for hierarchical ULID directories
    for item in roadmap_dir.iterdir():
        if item.is_dir() and item.name.startswith('01'):
            # ULID directories start with '01' (timestamp prefix)
            issues.append(f"Hierarchical directory found: {item}")

    # Verify flat structure exists
    required_dirs = ['tracks', 'sprints', 'tasks']
    for dir_name in required_dirs:
        dir_path = roadmap_dir / dir_name
        if not dir_path.exists():
            issues.append(f"Missing required directory: {dir_path}")

    # Report results
    if issues:
        click.echo("Structure validation FAILED:")
        for issue in issues:
            click.echo(f"  - {issue}")

        if fix:
            # Optionally auto-fix by deleting ULID dirs
            for item in roadmap_dir.iterdir():
                if item.is_dir() and item.name.startswith('01'):
                    shutil.rmtree(item)
                    click.echo(f"  Deleted: {item}")

        return 1
    else:
        click.echo("Structure validation PASSED")
        click.echo("  - No hierarchical ULID directories")
        click.echo("  - Flat structure verified: tracks/, sprints/, tasks/")
        return 0
```

### Step 2: Register command in CLI

Ensure command is registered in `vibey/cli/main.py` if using Click groups.

### Step 3: Integrate with db init/rebuild

Add structure validation as a post-step in:
- `vibey roadmap db init`
- `vibey roadmap db rebuild`

```python
def db_init_cmd():
    # ... existing init logic

    # Post-init validation
    click.echo("Validating structure...")
    validate_structure_cmd.callback(fix=False)
```

### Step 4: Add warning to db dump

After `db dump`, warn if hierarchical directories were created (shouldn't happen after Task 002):

```python
def db_dump_cmd():
    # ... existing dump logic

    # Check for accidental hierarchical creation
    ulid_dirs = list(roadmap_dir.glob('01*'))
    if ulid_dirs:
        click.echo("WARNING: Hierarchical directories created. Run 'vibey roadmap validate-structure --fix'")
```

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands.py` | Add validate-structure command |
| `vibey/cli/main.py` | Register command if needed |

## Testing

1. Run `vibey roadmap validate-structure` with clean flat structure - PASS
2. Create dummy ULID directory, run again - FAIL
3. Run with `--fix` - should delete and PASS
4. Test integration with `db init` and `db rebuild`

## Success Criteria

- [ ] `vibey roadmap validate-structure` command exists
- [ ] Detects hierarchical ULID directories
- [ ] Verifies flat structure exists
- [ ] `--fix` option deletes ULID directories
- [ ] Integrated with db init/rebuild

## Dependencies

- Tasks 002-007: Complete before validation is meaningful
