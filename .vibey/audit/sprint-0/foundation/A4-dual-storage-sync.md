# A4: Dual Storage Sync Audit

**Task ID:** 01KFXK7YSK51M9WCRV2RAA44J0
**Phase:** A4: Foundation
**Date:** 2026-01-29

## Executive Summary

The Vibey dual storage system maintains YAML files as the git-versioned source of truth and SQLite as the working state for fast queries. The `SyncManager` class handles bidirectional synchronization with checksums for conflict detection and dirty state tracking. Key finding: The sync architecture translates cleanly to remote mode - YAML becomes Delta Lake as the source of truth, with local SQLite cache for offline work and conflict resolution via checksum comparison.

**Key Statistics:**
- 2 sync directions: dump (DB→YAML) and rebuild (YAML→DB)
- 4 sync states: IN_SYNC, DB_AHEAD, YAML_AHEAD, CONFLICT
- SHA-256 checksums for file tracking
- Dirty flag for uncommitted changes

## Dual Storage Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DUAL STORAGE ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

  GIT REPOSITORY                         WORKING STATE
  ──────────────                         ─────────────

┌─────────────────┐                    ┌─────────────────┐
│ .vibey/roadmap/ │                    │ .vibey/roadmap.db│
│ ────────────────│                    │ ────────────────│
│ roadmap.yaml    │◀───── rebuild ─────│ roadmaps table  │
│ tracks/*.yaml   │      (YAML→DB)     │ tracks table    │
│ sprints/*.yaml  │                    │ sprints table   │
│ tasks/*.yaml    │────── dump ───────▶│ tasks table     │
│                 │      (DB→YAML)     │ + 29 more       │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │ git commit                           │ fast queries
         │ git push                             │ transactions
         │ code review                          │ computed views
         │                                      │
         ▼                                      ▼
┌─────────────────┐                    ┌─────────────────┐
│ VERSION CONTROL │                    │ RUNTIME STATE   │
│ - Human readable│                    │ - Fast lookups  │
│ - Diff-friendly │                    │ - Aggregations  │
│ - Audit trail   │                    │ - Relationships │
└─────────────────┘                    └─────────────────┘
```

## SyncManager Class

| Component | Implementation | Location |
|-----------|----------------|----------|
| **Class** | `SyncManager` | `backend.py:349-670` |
| **YAML Backend** | `YAMLBackend` | `backend.py` |
| **SQLite Backend** | `SQLiteBackend` | `backend.py` |
| **Checksum Storage** | `yaml_checksums` table | `schema.py` |
| **State Tracking** | `database_state` table | `schema.py` |

## Sync Operations Table

| Operation | Method | Direction | Trigger | Side Effects |
|-----------|--------|-----------|---------|--------------|
| **Dump** | `SyncManager.dump()` | DB → YAML | Pre-commit hook, manual | Updates checksums, marks clean |
| **Rebuild** | `SyncManager.rebuild()` | YAML → DB | Post-merge hook, manual | Drops/recreates schema, marks clean |
| **Check Modified** | `SyncManager.check_yaml_modified()` | Read-only | Status check | None |
| **Mark Dirty** | `SyncManager.mark_db_dirty()` | DB state | On DB write | Sets is_dirty=1 |
| **Mark Clean** | `SyncManager.mark_db_clean()` | DB state | After sync | Sets is_dirty=0 |

## Sync State Transitions

| Current State | Trigger | New State | Action Required |
|---------------|---------|-----------|-----------------|
| IN_SYNC | DB write | DB_AHEAD | dump before commit |
| IN_SYNC | YAML edit | YAML_AHEAD | rebuild |
| DB_AHEAD | dump | IN_SYNC | None |
| DB_AHEAD | YAML edit | CONFLICT | resolve manually |
| YAML_AHEAD | rebuild | IN_SYNC | None |
| YAML_AHEAD | DB write | CONFLICT | resolve manually |
| CONFLICT | dump --force | IN_SYNC | YAML changes lost |
| CONFLICT | rebuild --force | IN_SYNC | DB changes lost |

## Checksum Tracking Table

| Table | Column | Type | Purpose |
|-------|--------|------|---------|
| `yaml_checksums` | `file_path` | TEXT PK | Full path to YAML file |
| `yaml_checksums` | `checksum` | TEXT | SHA-256 hash of file content |
| `yaml_checksums` | `loaded_at` | TEXT | When file was loaded into DB |
| `yaml_checksums` | `file_size` | INTEGER | File size at load time |
| `yaml_checksums` | `last_modified` | TEXT | File mtime at load time |

## Database State Table

| Table | Column | Type | Purpose |
|-------|--------|------|---------|
| `database_state` | `id` | INTEGER | Singleton (always 1) |
| `database_state` | `last_yaml_load` | TEXT | When DB was rebuilt from YAML |
| `database_state` | `last_yaml_dump` | TEXT | When DB was dumped to YAML |
| `database_state` | `is_dirty` | INTEGER | 1 if uncommitted changes |
| `database_state` | `source_commit` | TEXT | Git commit DB was built from |
| `database_state` | `source_branch` | TEXT | Git branch at time of load |
| `database_state` | `schema_version` | TEXT | Schema version (1.0.0) |

## Dump Operation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DUMP FLOW (DB → YAML)                         │
└─────────────────────────────────────────────────────────────────────┘

1. Pre-dump Check
   └── check_yaml_modified() → modified_files[]
       └── If modified and !force → raise YAMLModifiedError

2. Load from SQLite
   ├── load_roadmap()
   ├── load_all_tasks()
   ├── For each task → load_track(task.track_id)
   └── For each task → load_sprint(task.sprint_id)

3. Save to YAML
   ├── save_roadmap(roadmap)
   ├── For each track → save_track(track)
   ├── For each sprint → save_sprint(sprint)
   └── save_tasks(tasks)

4. Post-dump Update
   ├── store_yaml_checksums()  # Update checksums
   └── mark_db_clean()         # Set is_dirty=0
```

## Rebuild Operation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REBUILD FLOW (YAML → DB)                         │
└─────────────────────────────────────────────────────────────────────┘

1. Pre-rebuild Check
   └── is_db_dirty() → bool
       └── If dirty and !force → raise DirtyDatabaseError

2. Load from YAML (flat structure)
   ├── load_roadmap() from roadmap.yaml
   ├── For each tracks/*.yaml → load_track(file)
   ├── For each sprints/*.yaml → load_sprint(file)
   └── For each tasks/*.yaml → load_task(file)

3. Rebuild Database
   ├── drop_triggers()
   ├── drop_views()
   ├── drop_all_tables()
   ├── create_schema()
   ├── create_views()
   ├── create_triggers()
   └── disable_triggers_for_bulk_operations()

4. Bulk Insert
   └── save_full_roadmap(roadmap, tracks, sprints, tasks)

5. Post-rebuild Update
   ├── store_yaml_checksums()  # Record file hashes
   └── mark_db_clean()         # Set is_dirty=0
```

## Auto-Sync Operations

| Function | File | Purpose |
|----------|------|---------|
| `check_sync_needed()` | `auto_sync.py` | Compare YAML mtime vs DB mtime |
| `ensure_synced()` | `auto_sync.py` | Trigger rebuild if needed |
| `get_sync_status()` | `auto_sync.py` | Return detailed sync status dict |

### Lazy Sync Logic

```python
def check_sync_needed(root_dir: Path) -> bool:
    db_mtime = db_path.stat().st_mtime
    for yaml_file in yaml_dir.glob("**/*.yaml"):
        if yaml_file.stat().st_mtime > db_mtime:
            return True  # YAML newer than DB
    return False
```

## Conflict Detection

| Conflict Type | Detection Method | Resolution |
|---------------|------------------|------------|
| **YAML_MODIFIED** | checksum mismatch | `rebuild --force` (lose DB changes) |
| **DB_MODIFIED** | `is_dirty=1` | `dump --force` (lose YAML changes) |
| **BOTH_MODIFIED** | checksum + dirty | Manual merge required |
| **FILE_DELETED** | file not found | Remove from checksums |

## Sync Conflict Table (schema.py)

| Column | Type | Purpose |
|--------|------|---------|
| `file_path` | TEXT | YAML file with conflict |
| `conflict_type` | TEXT | yaml_modified, db_modified, both_modified, file_deleted |
| `detected_at` | TEXT | When conflict was detected |
| `resolved_at` | TEXT | When conflict was resolved |
| `resolution` | TEXT | use_db, use_yaml, merged, ignored |
| `db_value` | TEXT | JSON of DB state |
| `yaml_value` | TEXT | JSON of YAML state |

## Git Hook Integration

| Hook | Trigger | Action |
|------|---------|--------|
| **pre-commit** | `git commit` | `vibey roadmap db dump` (DB→YAML) |
| **post-merge** | `git merge`, `git pull` | `vibey roadmap db rebuild` (YAML→DB) |
| **post-checkout** | `git checkout` | `vibey roadmap db rebuild --force` |

## CLI Commands Table

| Command | Operation | Options |
|---------|-----------|---------|
| `vibey roadmap db status` | Show sync state | None |
| `vibey roadmap db rebuild` | YAML → DB | `--force` to discard DB changes |
| `vibey roadmap db dump` | DB → YAML | `--force` to overwrite YAML |
| `vibey roadmap db validate` | Check integrity | None |

## Remote Mode Translation Table

| Local Concept | Remote Equivalent | Transformation |
|---------------|-------------------|----------------|
| YAML files (source of truth) | Delta Lake tables | YAML → Delta tables |
| SQLite (working cache) | Local SQLite cache | Keep for offline |
| SHA-256 checksums | Delta Lake version/timestamp | Use Delta versioning |
| is_dirty flag | Offline change queue | Queue pending changes |
| dump operation | Push to Delta Lake | Write to remote |
| rebuild operation | Pull from Delta Lake | Read from remote |
| Conflict detection | Delta Lake merge conflicts | Use optimistic locking |
| pre-commit hook | Pre-push hook | Sync before push |
| post-merge hook | Post-pull hook | Sync after pull |

## Remote Sync Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REMOTE SYNC ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────┘

  LOCAL MACHINE                          DATABRICKS PLATFORM
  ─────────────                          ───────────────────

┌─────────────────┐                    ┌─────────────────┐
│ Local SQLite    │                    │ Delta Lake      │
│ (Offline Cache) │                    │ (Source of Truth)│
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │ When online:                         │
         │ ┌──────────┐                         │
         ├─┤ Pull     ├────────────────────────▶│
         │ │ (Read)   │                         │
         │ └──────────┘                         │
         │                                      │
         │ When offline:                        │
         │ ┌──────────────┐                     │
         ├─┤ Queue Changes│                     │
         │ │ (Write)      │                     │
         │ └──────────────┘                     │
         │                                      │
         │ On reconnect:                        │
         │ ┌──────────┐                         │
         └─┤ Push     ├────────────────────────▶│
           │ (Sync)   │  Conflict Resolution    │
           └──────────┘                         │

  ┌─────────────────────────────────────────────────────────────────┐
  │ OFFLINE QUEUE (local SQLite table):                              │
  │ - operation: CREATE/UPDATE/DELETE                                │
  │ - entity_type: roadmap/track/sprint/task                        │
  │ - entity_id: ULID                                               │
  │ - payload: JSON                                                 │
  │ - created_at: timestamp                                         │
  │ - synced_at: NULL until pushed                                  │
  └─────────────────────────────────────────────────────────────────┘
```

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Sync direction diagram (DB↔YAML): PASS
- [x] Sync operations documented: PASS (5 operations)
- [x] Checksum mechanism documented: PASS
- [x] Conflict detection documented: PASS (4 conflict types)
- [x] Git hook integration documented: PASS (3 hooks)
- [x] Remote mode translation table: PASS

## References

- `vibey/roadmap/serialization/backend.py:349-670` - SyncManager class
- `vibey/operations/roadmap/auto_sync.py` - Lazy sync operations
- `vibey/roadmap/database/schema.py` - yaml_checksums, database_state tables
- `docs/architecture/adr/0003-dual-storage-sqlite-yaml.md` - ADR for dual storage
