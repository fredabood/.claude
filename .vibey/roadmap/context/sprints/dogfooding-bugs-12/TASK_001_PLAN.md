# Task Plan: Database does not auto-sync when YAML files are edited directly

## Bug ID
01KC8NA7RJTJKPRFABDZ2N4R9N

## Problem Statement
When YAML files in `.vibey/roadmap/` are edited directly (not via CLI), the SQLite database does not automatically update. User must manually run `vibey roadmap db rebuild` to sync changes.

## Root Cause Analysis
The SQLite database is a cache/query layer on top of the YAML source of truth. There is no file watcher or automatic sync mechanism. This is a design decision, not a bug.

## Design Decision Analysis

### Option A: Add file watcher for auto-sync
**Pros:**
- Seamless experience for direct YAML editors
- Database always reflects YAML state

**Cons:**
- Performance overhead (watching 1000+ files)
- Complexity (handling file events, debouncing)
- Race conditions with concurrent edits
- Background process required

### Option B: Sync on CLI command execution
**Pros:**
- No background process needed
- Sync happens when user interacts with CLI
- Simple implementation

**Cons:**
- Slight delay on first command after edits
- May miss changes if only using direct queries

### Option C: Enforce CLI-only modifications (current design)
**Pros:**
- Clear data flow
- Activity log always complete
- No sync issues

**Cons:**
- Less flexible for power users
- Pre-commit hook blocks direct edits

## Recommended Implementation: Option B (Lazy Sync)

## Files to Modify

### Primary Files
1. `vibey/cli/roadmap_lib/filesystem.py` - Add freshness check
2. `vibey/operations/roadmap/query.py` - Add sync-on-read
3. `vibey/roadmap/serialization/sql_loader.py` - Add modification time tracking

## Implementation Steps

1. **Add modification time tracking to database**
   ```sql
   CREATE TABLE sync_metadata (
       yaml_path TEXT PRIMARY KEY,
       last_modified_time REAL,
       last_synced_time REAL
   );
   ```

2. **Check freshness before queries**
   ```python
   def check_sync_needed(root_dir: Path) -> bool:
       """Check if any YAML files are newer than last sync."""
       db_path = root_dir / ".vibey" / "roadmap.db"
       yaml_dir = root_dir / ".vibey" / "roadmap"

       db_mtime = db_path.stat().st_mtime if db_path.exists() else 0

       for yaml_file in yaml_dir.glob("**/*.yaml"):
           if yaml_file.stat().st_mtime > db_mtime:
               return True
       return False
   ```

3. **Add auto-sync to CLI entry point**
   ```python
   def ensure_synced(root_dir: Path):
       """Ensure database is synced before operations."""
       if check_sync_needed(root_dir):
           click.echo("🔄 Syncing database with YAML changes...")
           rebuild_database(root_dir)
   ```

4. **Add --no-sync flag for performance**
   - Allow skipping sync check for batch operations

## Test Requirements
- Edit YAML file directly, run query command - should auto-sync
- Run with --no-sync - should skip check
- Large roadmap - verify sync check is fast (<100ms)

## Estimated Complexity
Complex - requires modification tracking and rebuild integration
