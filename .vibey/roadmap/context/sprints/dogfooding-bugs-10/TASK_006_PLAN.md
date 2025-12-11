# Task 006: Update/Remove migrate_to_hierarchical.py

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXV`
**Bug Addressed:** #19
**Complexity:** Low
**Priority:** Low
**Type:** Development

## Problem Statement

Two files exist for migrating TO hierarchical structure, which is now obsolete:
- `vibey/operations/migrations/to_hierarchical.py`
- `vibey/cli/migrate-to-hierarchical.py`

These should be removed or repurposed.

## Current State

The `HierarchicalMigrator` class in `to_hierarchical.py`:
- Creates nested `track_slug/sprint_slug/task_slug/` directories
- Moves files from flat structure to nested
- Has CLI command `migrate_to_hierarchical_cmd`

## Implementation Plan

### Option A: Delete (Recommended)

1. Remove `vibey/operations/migrations/to_hierarchical.py`
2. Remove `vibey/cli/migrate-to-hierarchical.py`
3. Remove CLI command registration from `commands.py`
4. Remove any imports referencing these modules

```bash
rm vibey/operations/migrations/to_hierarchical.py
rm vibey/cli/migrate-to-hierarchical.py
```

### Option B: Invert to migrate_to_flat.py

If we need a migration utility in the opposite direction:
1. Rename to `to_flat.py`
2. Rewrite to migrate FROM hierarchical TO flat
3. Update CLI command name

### Step 1: Find and remove CLI command registration

Search for `migrate_to_hierarchical` in:
- `vibey/cli/commands.py`
- `vibey/cli/main.py`

```python
# Remove or comment out:
@cli.command('migrate-to-hierarchical')
def migrate_to_hierarchical_cmd():
    ...
```

### Step 2: Remove imports

Search for imports of:
- `from vibey.operations.migrations.to_hierarchical import`
- `from vibey.cli.migrate-to-hierarchical import`

### Step 3: Delete files

```bash
git rm vibey/operations/migrations/to_hierarchical.py
git rm vibey/cli/migrate-to-hierarchical.py
```

## Files to Modify/Delete

| File | Action |
|------|--------|
| `vibey/operations/migrations/to_hierarchical.py` | DELETE |
| `vibey/cli/migrate-to-hierarchical.py` | DELETE |
| `vibey/cli/commands.py` | Remove command registration |
| `vibey/cli/main.py` | Remove if registered there |

## Testing

1. Verify CLI doesn't crash after removal
2. Verify `vibey --help` doesn't show migrate-to-hierarchical
3. Run test suite to catch any broken imports

## Success Criteria

- [ ] Both migration files deleted
- [ ] CLI command removed
- [ ] No broken imports
- [ ] All tests pass

## Dependencies

- Task 002 (YAMLBackend): Complete migration makes this obsolete
