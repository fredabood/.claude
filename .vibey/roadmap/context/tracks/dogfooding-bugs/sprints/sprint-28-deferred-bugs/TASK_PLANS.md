# Sprint 28: Comprehensive Task Plans

**Sprint ID:** 01KD43809NC3FPJJ179MAZRKCK
**Track:** CLI Dogfooding Bug Fixes

---

## Task 1: Bug - roadmap show treats ULID as track ID

**Task ID:** `01KD6RCYSJV1EGCF8W1VPXSK11`
**Priority:** High
**Complexity:** Simple
**Estimated Tokens:** 500

### Description

The `vibey roadmap show <ULID>` command fails when given a task or sprint ULID because it defaults to treating the ID as a track ID when `_detect_ulid_type()` returns `None`. Even though the detection function checks all entity types, the fallback at line 819 defaults to "track" instead of returning an appropriate error.

### Reproduction Steps

1. Get a task ULID: `01KCYA0G5135Z8B8ENFD841B10`
2. Run: `vibey roadmap show 01KCYA0G5135Z8B8ENFD841B10`
3. **Actual:** Error: "Track '01KCYA0G5135Z8B8ENFD841B10' not found"
4. **Expected:** Shows task details or searches all entity types

### Root Cause

In `vibey/cli/commands_legacy.py:814-822`:

```python
# For ULID IDs (no hyphens, 26 chars), look up type from .id files
if item_type is None and len(item_id) == 26 and item_id.isalnum():
    item_type = _detect_ulid_type(item_id, root_dir)
    if item_type is None:
        # Default to track for ULIDs not found in .id files  <-- BUG
        item_type = "track"
```

The `_detect_ulid_type` function (lines 771-795) correctly checks:
1. `.id` files for slug→ULID mappings
2. Direct YAML file existence

But if both fail (e.g., ULID exists in database but not in flat files), it returns `None`, and the caller defaults to "track".

### Implementation Plan

**File:** `vibey/cli/commands_legacy.py`

1. **Remove the fallback to "track"** (line 819):
   ```python
   if item_type is None:
       # Don't default - try database lookup or error
       pass
   ```

2. **Add database lookup as fallback** before defaulting:
   ```python
   if item_type is None:
       # Try database lookup
       from vibey.roadmap.database.queries import detect_entity_type
       item_type = detect_entity_type(item_id)

   if item_type is None:
       print(format_error(f"Entity not found: {item_id}"))
       return 1
   ```

3. **Create helper function** in `vibey/roadmap/database/queries.py`:
   ```python
   def detect_entity_type(entity_id: str) -> Optional[str]:
       """Check database for entity type by ID."""
       db_path = get_db_path()
       conn = sqlite3.connect(db_path)

       for table, entity_type in [("tasks", "task"), ("sprints", "sprint"), ("tracks", "track")]:
           row = conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (entity_id,)).fetchone()
           if row:
               return entity_type
       return None
   ```

### Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands_legacy.py:814-822` | Remove track fallback, add database lookup |
| `vibey/roadmap/database/queries.py` | Add `detect_entity_type()` function |

### Verification

```bash
# Test with task ULID
vibey roadmap show 01KD99P0CK180MYKD4DRP72NM2
# Should show task details

# Test with sprint ULID
vibey roadmap show 01KD43809NC3FPJJ179MAZRKCK
# Should show sprint details

# Test with non-existent ID
vibey roadmap show 01XXXXXXXXXXXXXXXXXXX
# Should show "Entity not found" error
```

---

## Task 2: Sprint auto-progress should skip deferred tasks

**Task ID:** `01KD438MN86VRXS70K6BPZNB52`
**Priority:** Medium
**Complexity:** Medium
**Estimated Tokens:** 300
**Status:** Likely already fixed - needs verification

### Description

Sprints with only deferred incomplete tasks should auto-progress to completed status. A sprint should not remain `in_progress` when all non-deferred tasks are complete.

### Reproduction Steps

1. Find a sprint where all incomplete tasks are marked `deferred: true`
2. Run: `vibey roadmap auto-progress --check`
3. **Expected:** Sprint shows as ready to progress
4. **Actual (if bug exists):** Sprint remains in_progress

### Root Cause Analysis

**Current code** in `vibey/operations/roadmap/update.py:1658-1683` already excludes deferred tasks:

```python
# Helper to check if task is deferred
def is_deferred(t):
    return getattr(t, 'deferred', False)

# Development tasks (exclude deferred from totals)
dev_tasks = [t for t in tasks if t.task_type == TaskType.DEVELOPMENT and not is_deferred(t)]
```

This was implemented per the SPRINT_PLAN.md (completed 2025-12-23).

### Implementation Plan

1. **Verify fix is working** by testing with a known deferred sprint
2. **If still broken**, check if the `deferred` attribute is being loaded correctly from YAML/DB
3. **Possible remaining issue:** The `MockTask` class may not properly expose `deferred`

### Files to Check

| File | Purpose |
|------|---------|
| `vibey/operations/roadmap/update.py:1645` | MockTask.deferred assignment |
| `vibey/roadmap/serialization/yaml_loader.py` | YAML loading of deferred field |
| `vibey/roadmap/serialization/sql_loader.py` | DB loading of deferred field |

### Verification

```bash
# Check if Sprint 10 (has deferred tasks) auto-progresses correctly
vibey roadmap auto-progress --check

# Manually verify deferred field is in database
sqlite3 .vibey/roadmap.db "SELECT id, title, deferred FROM tasks WHERE deferred = 1 LIMIT 5"
```

---

## Task 3: CLI db rebuild fails with missing SQLAlchemy

**Task ID:** `01KD69HEQEFV87R8JTTSJ1VSR6`
**Priority:** High
**Complexity:** Simple
**Estimated Tokens:** 400

### Description

Running `vibey roadmap db rebuild` fails with `ModuleNotFoundError: No module named 'sqlalchemy'` after a standard `pip install vibey`.

### Reproduction Steps

1. Create fresh virtual environment: `python -m venv test_venv`
2. Activate: `source test_venv/bin/activate`
3. Install: `pip install -e .`
4. Run: `vibey roadmap db rebuild`
5. **Actual:** `ModuleNotFoundError: No module named 'sqlalchemy'`
6. **Expected:** Command succeeds

### Root Cause

In `pyproject.toml`, SQLAlchemy is an **optional dependency**:

```toml
[project.optional-dependencies]
db = [
    "sqlalchemy>=2.0.0",
]
```

Standard `pip install vibey` doesn't include it. Users must run:
- `pip install vibey[db]`, or
- `pip install vibey[all]`

However, the `roadmap db` commands require SQLAlchemy and fail without it.

### Implementation Plan

**Option A: Make SQLAlchemy a required dependency** (Recommended)

```toml
# pyproject.toml
dependencies = [
    ...
    "sqlalchemy>=2.0.0",  # Move from optional to required
]
```

**Option B: Graceful error handling**

In `vibey/cli/main.py` for db commands:
```python
@db.command('rebuild')
def db_rebuild():
    try:
        import sqlalchemy
    except ImportError:
        print(format_error(
            "SQLAlchemy is required for database operations.\n"
            "Install with: pip install vibey[db]"
        ))
        sys.exit(1)
    # ... rest of command
```

### Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml:32-39` | Move sqlalchemy to required dependencies |
| OR `vibey/cli/main.py` | Add import guards to db commands |

### Verification

```bash
# Create fresh venv and test
python -m venv /tmp/test_vibey
source /tmp/test_vibey/bin/activate
pip install -e .
vibey roadmap db rebuild
# Should work without additional pip install
```

---

## Task 4: TaskType enum missing 'bug' value

**Task ID:** `01KD6TE4AWJZS92X9CRQPFX5M9`
**Priority:** Medium
**Complexity:** Simple
**Estimated Tokens:** 300

### Description

Tasks with `task_type: bug` fail validation because 'bug' is not a valid TaskType enum value. This prevents creating bug-tracking tasks in the roadmap.

### Reproduction Steps

1. Create a task YAML with `task_type: bug`
2. Run: `vibey roadmap db rebuild`
3. **Actual:** Validation error: "'bug' is not a valid TaskType"
4. **Expected:** Task imports successfully

### Root Cause

There are two `TaskType` enum definitions, neither includes 'bug':

**File 1:** `vibey/roadmap/models/ticket/enums.py:129-142`
```python
class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    INFRASTRUCTURE = "infrastructure"
    GATE = "gate"
    # Missing: BUG = "bug"
```

**File 2:** `vibey/roadmap/models/common.py:73-85`
```python
class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    INFRASTRUCTURE = "infrastructure"
    DESIGN = "design"
    GATE = "gate"
    COMPLETION_GATE = "completion_gate"
    PRODUCTION_GATE = "production_gate"
    # Missing: BUG = "bug"
```

### Implementation Plan

1. **Add BUG to both enum definitions:**

**File:** `vibey/roadmap/models/ticket/enums.py`
```python
class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    INFRASTRUCTURE = "infrastructure"
    GATE = "gate"
    BUG = "bug"  # Add this
```

**File:** `vibey/roadmap/models/common.py`
```python
class TaskType(str, Enum):
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    REVIEW = "review"
    INFRASTRUCTURE = "infrastructure"
    DESIGN = "design"
    GATE = "gate"
    COMPLETION_GATE = "completion_gate"
    PRODUCTION_GATE = "production_gate"
    BUG = "bug"  # Add this
```

2. **Update database schema CHECK constraint** (if exists):

Check `vibey/roadmap/database/schema.py` for any CHECK constraint on task_type column.

### Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/models/ticket/enums.py:142` | Add `BUG = "bug"` |
| `vibey/roadmap/models/common.py:85` | Add `BUG = "bug"` |
| `vibey/roadmap/database/schema.py` | Update CHECK constraint if exists |

### Verification

```bash
# Create test task with task_type: bug
echo 'task:
  id: TEST123
  task_type: bug
  title: Test bug task
  status: not_started
' > /tmp/test_bug_task.yaml

# Validate (should not error)
vibey roadmap db rebuild
```

---

## Task 5: Fix add-artifact command: no such column: id

**Task ID:** `01KD6XHBETCEADT66HFQQ6CWNW`
**Priority:** High
**Complexity:** Simple
**Estimated Tokens:** 400

### Description

The `vibey roadmap task add-artifact` command fails with "no such column: id" error. The artifact is created but fails to associate with the task.

### Reproduction Steps

1. Run: `vibey roadmap task add-artifact 01KC2D0JK7READW9KAK1HBX4B8 vibey/cli/main.py`
2. **Actual:** Error: "Failed to add artifact: no such column: id"
3. **Expected:** Artifact successfully associated with task

### Root Cause

**Schema mismatch** between code expectations and actual database schema.

The code in `vibey/cli/commands/relationship.py:279-282` queries:
```python
existing = conn.execute("""
    SELECT id FROM ticket_artifact_associations
    WHERE ticket_id = ? AND artifact_id = ?
""", (task_id, artifact_id)).fetchone()
```

But the actual `ticket_artifact_associations` table schema (from `schema.py`) uses a **composite primary key**:
```sql
CREATE TABLE ticket_artifact_associations (
    ticket_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    ...
    PRIMARY KEY (ticket_id, artifact_id),  -- No 'id' column!
    ...
);
```

The table has no `id` column - it uses `(ticket_id, artifact_id)` as the primary key.

### Implementation Plan

**File:** `vibey/cli/commands/relationship.py`

1. **Fix the duplicate check query** (line 279):
   ```python
   # Before (broken)
   existing = conn.execute("""
       SELECT id FROM ticket_artifact_associations
       WHERE ticket_id = ? AND artifact_id = ?
   """, (task_id, artifact_id)).fetchone()

   # After (fixed)
   existing = conn.execute("""
       SELECT 1 FROM ticket_artifact_associations
       WHERE ticket_id = ? AND artifact_id = ?
   """, (task_id, artifact_id)).fetchone()
   ```

2. **Also check `_ensure_tables_exist`** function (lines 43-58):
   The function creates a DIFFERENT schema than what `schema.py` creates. Align them:
   ```python
   # Current (inconsistent with main schema)
   conn.execute("""
       CREATE TABLE IF NOT EXISTS ticket_artifact_associations (
           id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Wrong!
           ...
       )
   """)

   # Should be removed or aligned with main schema
   ```

3. **Remove `_ensure_tables_exist`** or make it a no-op for existing tables:
   The main schema is created by `vibey roadmap db rebuild`. The relationship commands should not create their own incompatible schema.

### Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/commands/relationship.py:279` | Change `SELECT id` to `SELECT 1` |
| `vibey/cli/commands/relationship.py:43-93` | Remove or fix `_ensure_tables_exist` |

### Verification

```bash
# Test add-artifact command
vibey roadmap task add-artifact 01KD99P0CK180MYKD4DRP72NM2 vibey/cli/main.py

# Verify association created
sqlite3 .vibey/roadmap.db "SELECT * FROM ticket_artifact_associations LIMIT 5"
```

---

## Summary

| Task | Bug | Root Cause | Fix Complexity |
|------|-----|------------|----------------|
| 1 | roadmap show entity detection | Fallback to "track" instead of error | Simple |
| 2 | Sprint auto-progress deferred | Likely already fixed - verify | Verification |
| 3 | SQLAlchemy missing | Optional dependency | Simple |
| 4 | TaskType missing 'bug' | Enum incomplete | Simple |
| 5 | add-artifact no column: id | Schema mismatch | Simple |

**Recommended execution order:** 5 → 4 → 3 → 1 → 2 (fix blocking issues first)
