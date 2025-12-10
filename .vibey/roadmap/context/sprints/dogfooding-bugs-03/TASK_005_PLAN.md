# Task 005: Investigate is_dirty Column in Schema History

**Task ID:** dogfooding-bugs-03-task-005
**Bug Addressed:** #9 (Pre-commit Hook Database Error - Missing is_dirty Column)
**Complexity:** Low
**Type:** Research

---

## Problem Statement

The pre-commit hook fails with `no such column: is_dirty` error. This suggests either:
1. Database was created with old schema lacking `is_dirty`
2. `database_state` table doesn't exist
3. Schema migration never ran

---

## Investigation Steps

### 1. Verify Schema Definition

```sql
-- Check current schema.py definition
-- File: vibey/roadmap/database/schema.py:556-575

CREATE TABLE IF NOT EXISTS database_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_yaml_load TEXT,
    last_yaml_dump TEXT,
    is_dirty INTEGER NOT NULL DEFAULT 0,  -- <-- Column exists
    source_commit TEXT,
    source_branch TEXT,
    schema_version TEXT NOT NULL DEFAULT '1.0.0'
);
```

The column **IS defined** in the current schema.

### 2. Check Actual Database

```bash
# Inspect actual database schema
sqlite3 .vibey/roadmap.db ".schema database_state"

# Check if table exists
sqlite3 .vibey/roadmap.db "SELECT name FROM sqlite_master WHERE type='table' AND name='database_state'"

# Check columns
sqlite3 .vibey/roadmap.db "PRAGMA table_info(database_state)"
```

### 3. Possible Root Causes

| Cause | Likelihood | Evidence | Fix |
|-------|------------|----------|-----|
| Database created before is_dirty added | High | Old database file | Recreate or migrate |
| Schema migration failed | Medium | Partial schema | Re-run create_schema |
| database_state table missing | Medium | No table | Run schema init |
| Wrong database file | Low | Different .db file | Check db_path |

### 4. Check Pre-commit Hook Query

```python
# vibey/operations/git/hooks/pre_commit.py:497-501

conn = get_connection(db_path=self.db_path)
row = conn.execute("""
    SELECT is_dirty FROM database_state WHERE id = 1
""").fetchone()
```

The hook queries `is_dirty` directly. If column doesn't exist, it fails.

---

## Debug Script

```python
#!/usr/bin/env python3
"""Debug script for is_dirty column issue."""

import sqlite3
from pathlib import Path

def main():
    db_path = Path.cwd() / ".vibey" / "roadmap.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print("=== Database State Table ===\n")

    # Check if table exists
    result = conn.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='database_state'
    """).fetchone()

    if not result:
        print("❌ database_state table does NOT exist")
        print("\nFix: Run schema creation or migration")
        return

    print("✓ database_state table exists")

    # Check columns
    columns = conn.execute("PRAGMA table_info(database_state)").fetchall()
    print("\nColumns:")
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")

    # Check for is_dirty
    col_names = [col['name'] for col in columns]
    if 'is_dirty' in col_names:
        print("\n✓ is_dirty column exists")

        # Check current value
        row = conn.execute("SELECT * FROM database_state WHERE id = 1").fetchone()
        if row:
            print(f"\nCurrent state:")
            print(f"  is_dirty: {row['is_dirty']}")
            print(f"  schema_version: {row['schema_version']}")
            print(f"  last_yaml_load: {row['last_yaml_load']}")
        else:
            print("\n⚠ No data in database_state (id=1 missing)")
    else:
        print("\n❌ is_dirty column MISSING")
        print("\nExpected columns:")
        print("  id, last_yaml_load, last_yaml_dump, is_dirty,")
        print("  source_commit, source_branch, schema_version")
        print("\nFix: Database schema needs migration")


if __name__ == "__main__":
    main()
```

---

## Expected Findings

Based on the error message, likely scenarios:

1. **Schema Version Mismatch**: Database was created with v1.0.0 schema that lacked `is_dirty`. Current schema is v1.0.0 but includes `is_dirty`, suggesting the table was created before this column was added to the schema definition.

2. **Partial Schema**: `create_schema()` ran but `database_state` initialization failed partway through.

3. **Manual Database Creation**: Database was created manually or by older code.

---

## Recommended Fix

Based on findings, one of:

| Finding | Fix |
|---------|-----|
| Table missing | Run `create_schema()` |
| Column missing | Run schema migration (Task 007) |
| Row missing | Insert singleton row |
| Wrong db file | Update hook to use correct path |

---

## Success Criteria

- [ ] Root cause of is_dirty error identified
- [ ] Debug script created and run
- [ ] Specific fix recommendation documented
- [ ] Evidence collected (sqlite3 output)

---

## Dependencies

None - this is an investigation task.

---

## Notes

This investigation informs Tasks 006-008. The fix depends on what we find:
- If schema outdated: need migration (Task 007)
- If table missing: need schema init (Task 006)
- If hook wrong: need hook update (Task 006)
