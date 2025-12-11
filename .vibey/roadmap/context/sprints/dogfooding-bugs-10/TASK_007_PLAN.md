# Task 007: Clean Up Legacy ULID Directories

**Task ID:** `01KC4ZWAGDKBH0NK3X0SDN6YXW`
**Bug Addressed:** #19
**Complexity:** Low
**Priority:** Medium
**Type:** Cleanup

## Problem Statement

35 untracked ULID directories exist in `.vibey/roadmap/` that were created by the old `YAMLBackend.save_*()` methods during `db dump` operations. These contain duplicate data.

## Current State

```bash
$ git status .vibey/roadmap/01KC*
?? .vibey/roadmap/01KC2D0JK06MN77ZHAGAHF5VKB/
?? .vibey/roadmap/01KC2D0JK06MN77ZHAGAHF5VKN/
... (33 more)
?? .vibey/roadmap/01KC39XSXJ39N12HWJ93F77KQ9/
```

These directories are:
- NOT tracked in git (untracked)
- Created during `vibey roadmap db dump` operations
- Contain same data as flat structure (`tracks/`, `sprints/`, `tasks/`)

## Implementation Plan

### Step 1: Verify no unique data

Before deletion, verify all data exists in flat structure:

```bash
# Count tracks in flat vs hierarchical
ls .vibey/roadmap/tracks/*.yaml | wc -l
find .vibey/roadmap/01KC* -name "track.yaml" | wc -l

# Count sprints
ls .vibey/roadmap/sprints/*.yaml | wc -l
find .vibey/roadmap/01KC* -name "sprint.yaml" | wc -l

# Count tasks
ls .vibey/roadmap/tasks/*.yaml | wc -l
find .vibey/roadmap/01KC* -name "task.yaml" | wc -l
```

### Step 2: Delete untracked ULID directories

```bash
# List what will be deleted
find .vibey/roadmap -maxdepth 1 -type d -name "01KC*"

# Delete them
rm -rf .vibey/roadmap/01KC*/
```

### Step 3: Add .gitignore rule

Add to `.vibey/roadmap/.gitignore` or root `.gitignore`:

```gitignore
# Prevent hierarchical ULID directories from being tracked
.vibey/roadmap/01*/
```

### Step 4: Verify cleanup

```bash
# Should show no ULID directories
ls -d .vibey/roadmap/01KC*/ 2>/dev/null || echo "No ULID directories found"

# Database should still work
vibey roadmap db rebuild --force
vibey roadmap status
```

## Files to Modify

| File | Action |
|------|--------|
| `.vibey/roadmap/01KC*/` | DELETE (35 directories) |
| `.gitignore` | ADD rule to prevent future tracking |

## Testing

1. Backup current state (optional)
2. Delete directories
3. Run `vibey roadmap db rebuild`
4. Run `vibey roadmap status` - should show same data
5. Verify no data loss

## Success Criteria

- [ ] All 35 `01KC*/` directories deleted
- [ ] `.gitignore` rule added
- [ ] Database still loads correctly
- [ ] `vibey roadmap status` shows same data
- [ ] No unique data lost

## Dependencies

- Tasks 002-005: Should complete migration BEFORE cleanup
- Ensures no new ULID directories will be created
