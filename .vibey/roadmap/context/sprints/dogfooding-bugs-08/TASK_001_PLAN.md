# Task 001: Fix complete command slug-to-ULID lookup

**Task ID:** dogfooding-bugs-08-task-001
**Bug Addressed:** #16 (complete command compares slug to ULID)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The `vibey roadmap complete <slug>` command fails to find tasks when using slug identifiers (e.g., `dogfooding-bugs-08-task-001`) because the code compares the slug against task ULIDs (e.g., `01KC4P92GRAHA428M96MTXWP5T`).

---

## Root Cause

In `vibey/cli/roadmap-update.py:complete_task()`:

```python
for t in tasks:
    if t.id == task_id:  # t.id is ULID, task_id is slug
        task = t
        break
```

The comparison `t.id == task_id` fails because:
- `t.id` = `01KC4P92GRAHA428M96MTXWP5T` (ULID)
- `task_id` = `dogfooding-bugs-08-task-001` (slug)

---

## Fix

Compare against both `t.id` (ULID) and `t.slug` (human-readable):

```python
for t in tasks:
    if t.id == task_id or t.slug == task_id:
        task = t
        break
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/roadmap-update.py` | Update `complete_task()` to match on both id and slug |

---

## Implementation

### In `vibey/cli/roadmap-update.py`:

```python
def complete_task(
    fs: FileSystemManager,
    task_id: str,
    completed_by: str = "system",
    skip_commit_check: bool = False
) -> bool:
    """Mark a task as completed."""
    # Find task - support both ULID and slug lookup
    task = None
    for t in tasks:
        if t.id == task_id or getattr(t, 'slug', None) == task_id:
            task = t
            break
```

---

## Testing

```bash
# Should work with slug
vibey roadmap complete dogfooding-bugs-08-task-001

# Should work with ULID
vibey roadmap complete 01KC4P92GRAHA428M96MTXWP5T
```

---

## Success Criteria

- [ ] `complete_task()` finds tasks by slug
- [ ] `complete_task()` still finds tasks by ULID
- [ ] No regression in existing functionality
