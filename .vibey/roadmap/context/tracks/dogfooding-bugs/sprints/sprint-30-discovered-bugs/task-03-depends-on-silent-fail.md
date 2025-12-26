# Task 03: YAML Loader Fails Silently When depends_on Missing required_status Field

## Bug Description

Tasks with `depends_on` entries that only contain `blocker_type` and `blocker_id` fail to load with `KeyError: 'required_status'`, but the error is not surfaced during db rebuild.

## Impact

- 24 experiment tasks were not loaded into the database
- Silent failure - no indication of which files failed or why
- Users creating tasks manually may not know all required fields

## Current Behavior

The YAML loader expects `depends_on` entries to have all fields:

```yaml
depends_on:
  - blocker_type: task
    blocker_id: 01KC2D0JK325ABWVR9FQD5ZNQY
    required_status: completed        # REQUIRED - causes KeyError if missing
    current_status: pending           # REQUIRED - causes KeyError if missing
    blocks_transition_to: in_progress # REQUIRED - causes KeyError if missing
```

When any of these are missing, the loader throws `KeyError` and the task is silently skipped.

## Root Cause

**File**: `vibey/roadmap/serialization/yaml_loader.py`

```python
def parse_depends_on(data: List[dict]) -> List[DependencyStatus]:
    return [
        DependencyStatus(
            blocker_type=d["blocker_type"],
            blocker_id=d["blocker_id"],
            required_status=d["required_status"],    # KeyError if missing
            current_status=d["current_status"],       # KeyError if missing
            blocks_transition_to=d["blocks_transition_to"],  # KeyError if missing
        )
        for d in data
    ]
```

## Implementation Plan

### Option A: Make Fields Optional with Defaults (Recommended)

This is the most user-friendly approach. Provide sensible defaults:

```python
def parse_depends_on(data: List[dict]) -> List[DependencyStatus]:
    return [
        DependencyStatus(
            blocker_type=d["blocker_type"],
            blocker_id=d["blocker_id"],
            required_status=d.get("required_status", "completed"),
            current_status=d.get("current_status", "pending"),
            blocks_transition_to=d.get("blocks_transition_to", "in_progress"),
        )
        for d in data
    ]
```

### Option B: Validate and Report Missing Fields

If strict validation is preferred:

```python
def parse_depends_on(data: List[dict], file_path: str) -> List[DependencyStatus]:
    REQUIRED_FIELDS = ["blocker_type", "blocker_id", "required_status",
                       "current_status", "blocks_transition_to"]
    results = []

    for i, d in enumerate(data):
        missing = [f for f in REQUIRED_FIELDS if f not in d]
        if missing:
            raise ValueError(
                f"depends_on[{i}] missing required fields: {missing} "
                f"in {file_path}"
            )
        results.append(DependencyStatus(**d))

    return results
```

### Step 1: Update DependencyStatus Model

**File**: `vibey/roadmap/models/common.py` (or wherever DependencyStatus is defined)

```python
@dataclass
class DependencyStatus:
    blocker_type: str
    blocker_id: str
    required_status: str = "completed"      # Default
    current_status: str = "pending"         # Default
    blocks_transition_to: str = "in_progress"  # Default
```

### Step 2: Update YAML Loader

**File**: `vibey/roadmap/serialization/yaml_loader.py`

```python
def parse_depends_on(data: List[dict]) -> List[DependencyStatus]:
    """Parse depends_on entries with sensible defaults for optional fields."""
    if not data:
        return []

    results = []
    for entry in data:
        # Validate required fields
        if "blocker_type" not in entry or "blocker_id" not in entry:
            raise ValueError(
                f"depends_on entry missing blocker_type or blocker_id: {entry}"
            )

        # Use defaults for optional fields
        results.append(DependencyStatus(
            blocker_type=entry["blocker_type"],
            blocker_id=entry["blocker_id"],
            required_status=entry.get("required_status", "completed"),
            current_status=entry.get("current_status", "pending"),
            blocks_transition_to=entry.get("blocks_transition_to", "in_progress"),
        ))

    return results
```

### Step 3: Add Schema Documentation

Create or update documentation for the depends_on schema:

```markdown
## depends_on Schema

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| blocker_type | Yes | - | Entity type: 'task', 'sprint', 'track', 'external' |
| blocker_id | Yes | - | ULID of the blocking entity |
| required_status | No | 'completed' | Status blocker must reach to unblock |
| current_status | No | 'pending' | Current status of the dependency |
| blocks_transition_to | No | 'in_progress' | What transition this blocks |
```

### Step 4: Add Validation on Task Creation

**File**: `vibey/operations/roadmap/create.py`

```python
def validate_depends_on(depends_on: List[dict]) -> List[str]:
    """Validate depends_on entries and return warnings for missing optional fields."""
    warnings = []
    for i, dep in enumerate(depends_on):
        if "required_status" not in dep:
            warnings.append(f"depends_on[{i}]: using default required_status='completed'")
    return warnings
```

## Test Cases

1. **Full depends_on entry** - All fields present, loads correctly
2. **Minimal depends_on** - Only blocker_type and blocker_id, defaults applied
3. **Missing blocker_type** - Raises clear ValueError
4. **Missing blocker_id** - Raises clear ValueError
5. **Empty depends_on array** - Returns empty list
6. **Mixed entries** - Some with all fields, some with defaults

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/models/common.py` | Add defaults to DependencyStatus |
| `vibey/roadmap/serialization/yaml_loader.py` | Use `.get()` with defaults |
| `docs/schema/DEPENDS_ON.md` | Document optional fields |

## Acceptance Criteria

- [ ] depends_on entries with only blocker_type/blocker_id load successfully
- [ ] Default values applied: required_status='completed', current_status='pending', blocks_transition_to='in_progress'
- [ ] Clear error message if blocker_type or blocker_id missing
- [ ] Schema documentation updated
- [ ] Existing tasks with full depends_on entries still work
- [ ] Unit tests cover all cases
