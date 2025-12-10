# YAML Synchronization Strategy

**Task:** sqlite-backend-0-task-005
**Status:** In Progress
**Date:** 2025-11-26

## Architecture Context

**Key Decision - Source of Truth Hierarchy:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  REMOTE YAML (git repo)  =  Ultimate source of truth                   │
│                              Shared state across all collaborators      │
├─────────────────────────────────────────────────────────────────────────┤
│  LOCAL SQLite DB         =  Working state for current session          │
│                              Derived from YAML, synced back on commit   │
├─────────────────────────────────────────────────────────────────────────┤
│  Conflict Resolution     =  Git's merge process                        │
│                              After DB→YAML dump, standard git workflow  │
└─────────────────────────────────────────────────────────────────────────┘
```

**Implications:**
- **YAML in git is authoritative** - When conflicts arise, git merge determines the resolution
- **SQLite is session-local** - Each developer has their own DB derived from YAML
- **DB→YAML dump** converts local work into git-trackable format
- **YAML→DB rebuild** synchronizes local DB with authoritative YAML state

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           NORMAL WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   vibey CLI ──▶ SQLite DB ──▶ (pre-commit) ──▶ YAML files ──▶ git       │
│                    ▲                                                     │
│                    │                                                     │
│              All writes                                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          GIT PULL WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   git pull ──▶ YAML files ──▶ (post-merge) ──▶ SQLite DB (rebuilt)      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## DB → YAML Dump Strategy

### When to Dump

1. **Pre-commit hook** - Automatically dump before every commit
2. **Manual command** - `vibey roadmap dump` for explicit sync
3. **After batch operations** - CLI commands that modify multiple entities

### Pre-Dump Safety Checks

Before dumping, verify YAML hasn't been modified outside the database:

```python
def pre_dump_safety_check():
    """
    Detect manual YAML edits that would be overwritten.

    This catches:
    - AI accidentally editing YAML directly
    - Human manually editing YAML
    - Any external modification
    """
    modified_files = []

    for row in query("SELECT file_path, checksum FROM yaml_checksums"):
        current_checksum = compute_sha256(row['file_path'])
        if current_checksum != row['checksum']:
            modified_files.append(row['file_path'])

    if modified_files:
        raise YAMLModifiedError(
            f"YAML files modified outside database:\n"
            f"{chr(10).join('  - ' + f for f in modified_files)}\n\n"
            f"Options:\n"
            f"  vibey roadmap rebuild    # Load YAML changes into DB\n"
            f"  vibey roadmap dump --force  # Overwrite YAML with DB state"
        )
```

### Checksum Tracking

On YAML load (rebuild), store checksums:

```python
def store_yaml_checksums():
    """Store checksums of all YAML files at load time."""
    for yaml_file in find_all_yaml_files():
        checksum = compute_sha256(yaml_file)
        execute("""
            INSERT OR REPLACE INTO yaml_checksums
            (file_path, checksum, loaded_at, file_size, last_modified)
            VALUES (?, ?, datetime('now'), ?, ?)
        """, yaml_file, checksum, os.path.getsize(yaml_file),
            os.path.getmtime(yaml_file))
```

### Dump Process

```python
def dump_db_to_yaml():
    """Dump entire database to YAML files."""

    # 1. Query all entities with computed values
    roadmap = get_roadmap_with_progress()
    tracks = get_all_tracks_with_progress()
    sprints = get_all_sprints_with_progress()
    tasks = get_all_tasks()

    # 2. Build YAML structure for each file
    # 3. Write files with deterministic output

    write_roadmap_yaml(roadmap)
    for track in tracks:
        write_track_yaml(track)
        for sprint in track.sprints:
            write_sprint_yaml(sprint)
            for task in sprint.tasks:
                write_task_yaml(task)
```

### Deterministic Output Requirements

YAML output must be **100% deterministic** to avoid noisy git diffs.

#### 1. Key Ordering

Always output keys in a fixed order defined by schema:

```python
# Task field order (matches schema)
TASK_FIELD_ORDER = [
    'id', 'sprint_id', 'track_id', 'roadmap_id',
    'task_type', 'title', 'description',
    'status', 'blocked', 'blocked_reason',
    'created', 'started', 'completed',
    'assigned_agent', 'priority', 'phase_label',
    'estimated_tokens', 'actual_tokens', 'complexity',
    'gate_info', 'audit_results',
    'dependencies', 'blocks', 'blocked_by',
    'deliverables', 'commits',
    'metadata'
]

def ordered_dict(data: dict, field_order: list) -> OrderedDict:
    """Return dict with keys in specified order."""
    result = OrderedDict()
    for key in field_order:
        if key in data:
            result[key] = data[key]
    # Include any extra keys at the end (alphabetically)
    for key in sorted(data.keys()):
        if key not in result:
            result[key] = data[key]
    return result
```

#### 2. Array Sorting

Always sort arrays by their natural key:

```python
# Sort arrays by their identifying field
ARRAY_SORT_KEYS = {
    'tracks': 'id',
    'sprints': 'id',
    'tasks': 'id',
    'deliverables': 'description',  # No id, sort by content
    'commits': 'commit_hash',
    'dependencies': 'name',
    'blocks': lambda x: (x.get('type', ''), x.get('target_id', '')),
    'blocked_by': lambda x: (x.get('type', ''), x.get('target_id', '')),
    'quality_gates': 'name',
    'assigned_agents': 'agent_name',
}
```

#### 3. Timestamp Formatting

Use consistent ISO 8601 format:

```python
def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO 8601 with timezone."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
```

#### 4. Null Handling

Use explicit `null` for optional fields (don't omit):

```yaml
# Consistent (always include):
completed: null
actual_tokens: null

# Not this (sometimes missing):
# completed:  <-- omitted
```

#### 5. String Formatting

Multiline strings use literal block scalar `|`:

```yaml
description: |
  This is a multiline
  description.

# Not this:
description: "This is a multiline\ndescription."
```

### YAML Writer Implementation

```python
import yaml
from collections import OrderedDict

class DeterministicDumper(yaml.SafeDumper):
    """YAML dumper that produces deterministic output."""
    pass

def _represent_ordered_dict(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def _represent_none(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:null', 'null')

def _represent_str(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

DeterministicDumper.add_representer(OrderedDict, _represent_ordered_dict)
DeterministicDumper.add_representer(type(None), _represent_none)
DeterministicDumper.add_representer(str, _represent_str)

def dump_yaml(data: dict) -> str:
    """Dump dict to deterministic YAML string."""
    return yaml.dump(
        data,
        Dumper=DeterministicDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,  # We handle ordering ourselves
        width=120,
    )
```

---

## YAML → DB Rebuild Strategy

### When to Rebuild

1. **Post-merge hook** - After git pull/merge brings in YAML changes
2. **Post-checkout hook** - After switching branches
3. **Manual command** - `vibey roadmap rebuild` for explicit rebuild
4. **Initial setup** - When setting up DB from existing YAML

### Pre-Rebuild Safety Checks

**Critical:** Prevent data loss when pulling changes overwrites local DB work.

```python
def pre_rebuild_safety_check():
    """
    Prevent rebuild if database has uncommitted changes.

    Scenario this prevents:
    1. Developer does work, DB is updated
    2. Developer runs 'git pull' (triggers post-merge hook)
    3. Hook rebuilds DB from incoming YAML
    4. Local work is LOST

    Safe workflow:
    1. vibey roadmap dump   # Dump local changes to YAML
    2. git add .vibey/      # Stage YAML
    3. git commit           # Commit
    4. git pull             # Now safe (hook rebuilds DB)
    """
    state = query("SELECT is_dirty, last_yaml_dump FROM database_state WHERE id = 1")

    if state['is_dirty']:
        raise DirtyDatabaseError(
            "Database has uncommitted changes that would be lost.\n\n"
            "Options:\n"
            "  vibey roadmap dump       # Save changes to YAML first\n"
            "  vibey roadmap rebuild --force  # Discard local changes\n\n"
            "Safe workflow:\n"
            "  1. vibey roadmap dump\n"
            "  2. git add .vibey/ && git commit\n"
            "  3. git pull"
        )

def mark_db_dirty():
    """Called by triggers after any data modification."""
    execute("UPDATE database_state SET is_dirty = 1 WHERE id = 1")

def mark_db_clean():
    """Called after successful dump to YAML."""
    execute("""
        UPDATE database_state
        SET is_dirty = 0, last_yaml_dump = datetime('now')
        WHERE id = 1
    """)
```

### Dirty Tracking via Triggers

```sql
-- Set dirty flag on any data modification
CREATE TRIGGER trg_mark_dirty_tasks
AFTER INSERT OR UPDATE OR DELETE ON tasks
BEGIN
    UPDATE database_state SET is_dirty = 1 WHERE id = 1;
END;

-- Similar triggers for: tracks, sprints, roadmaps,
-- quality_gates, deliverables, commits, etc.
```

### Rebuild Process

```python
def rebuild_db_from_yaml():
    """Rebuild entire database from YAML files."""

    # 1. Clear existing data (in transaction)
    clear_all_tables()

    # 2. Disable triggers during bulk load
    disable_activity_triggers()

    # 3. Load entities in order (parents before children)
    roadmap = parse_roadmap_yaml()
    insert_roadmap(roadmap)

    for track_dir in get_track_directories():
        track = parse_track_yaml(track_dir)
        insert_track(track)

        for sprint_dir in get_sprint_directories(track_dir):
            sprint = parse_sprint_yaml(sprint_dir)
            insert_sprint(sprint)

            for task_dir in get_task_directories(sprint_dir):
                task = parse_task_yaml(task_dir)
                insert_task(task)

    # 4. Re-enable triggers
    enable_activity_triggers()

    # 5. Validate referential integrity
    validate_db_integrity()
```

### Loading Order

Must respect foreign key constraints:

```
1. roadmaps
2. tracks
3. sprints
4. tasks
5. All relationship tables (external_dependencies, entity_blocks, etc.)
6. All supporting tables (deliverables, commits, quality_gates, etc.)
```

### Handling Computed Values

During rebuild:
- **Ignore computed values from YAML** (progress counters, blocked flags)
- **Let views compute fresh values** from source data
- **Use triggers to populate summary tables**

```python
def insert_task(task_data: dict):
    """Insert task, ignoring computed values."""
    # These are computed by views/triggers, skip them:
    skip_fields = ['blocked']  # Computed from blocked_by

    filtered_data = {k: v for k, v in task_data.items() if k not in skip_fields}
    execute_insert('tasks', filtered_data)
```

---

## Git Hook Integration

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Dump database to YAML before commit
vibey roadmap dump --quiet

# Stage the updated YAML files
git add .vibey/roadmap/
git add .vibey/roadmap.yaml

exit 0
```

### Post-merge Hook

```bash
#!/bin/bash
# .git/hooks/post-merge

# Check if any roadmap YAML files changed
if git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD | grep -q "^\.vibey/roadmap"; then
    echo "Roadmap files changed, rebuilding database..."
    vibey roadmap rebuild --quiet
fi

exit 0
```

### Post-checkout Hook

```bash
#!/bin/bash
# .git/hooks/post-checkout

# $3 is 1 for branch checkout, 0 for file checkout
if [ "$3" = "1" ]; then
    # Branch changed, rebuild DB from YAML
    vibey roadmap rebuild --quiet
fi

exit 0
```

---

## CLI Commands

### `vibey roadmap dump`

Dump database to YAML files.

```
Usage: vibey roadmap dump [OPTIONS]

Options:
  --quiet       Suppress output
  --dry-run     Show what would be written without writing
  --diff        Show diff between current YAML and what would be written
  --entity ID   Only dump specific entity and its children
```

### `vibey roadmap rebuild`

Rebuild database from YAML files.

```
Usage: vibey roadmap rebuild [OPTIONS]

Options:
  --quiet       Suppress output
  --validate    Only validate YAML, don't rebuild
  --backup      Backup current DB before rebuild
  --force       Discard local DB changes and rebuild
```

### `vibey roadmap validate`

Validate YAML integrity with multiple validation levels.

```
Usage: vibey roadmap validate [OPTIONS]

Options:
  --level LEVEL   Validation level: schema, references, computed, full
                  Default: references

Validation Levels:
  schema      - Validate YAML syntax and schema compliance (fast)
  references  - + Check all references point to existing entities
  computed    - + Verify computed fields match actual values
  full        - All validations + generate detailed audit report
```

**Validation Implementation:**

```python
def validate_yaml(level: str = 'references'):
    """
    Validate YAML integrity at specified level.

    Levels:
    - schema: YAML syntax + field types + required fields
    - references: + foreign key validity (task.sprint_id exists, etc.)
    - computed: + compare declared counters vs computed values
    - full: + generate audit report for Sprint 4 dogfooding
    """
    errors = []

    # Level 1: Schema validation (always runs)
    errors.extend(validate_schema())

    if level in ('references', 'computed', 'full'):
        # Level 2: Referential integrity
        errors.extend(validate_references())

    if level in ('computed', 'full'):
        # Level 3: Computed field validation
        # Build two databases and compare
        computed_db = build_db_from_tasks_only()  # Compute all aggregations
        declared_db = build_db_from_yaml_counters()  # Use YAML values as-is

        discrepancies = compare_databases(computed_db, declared_db)
        errors.extend(discrepancies)

    if level == 'full':
        # Level 4: Full audit report
        generate_audit_report(errors)

    return errors


def validate_schema():
    """Validate YAML files against schema definitions."""
    errors = []
    for yaml_file in find_all_yaml_files():
        try:
            data = load_yaml(yaml_file)
            schema = get_schema_for_file(yaml_file)
            validate_against_schema(data, schema)
        except ValidationError as e:
            errors.append(SchemaError(yaml_file, str(e)))
    return errors


def validate_references():
    """Check all references point to existing entities."""
    errors = []

    # Load all entity IDs
    roadmap_ids = {r['id'] for r in load_all_roadmaps()}
    track_ids = {t['id'] for t in load_all_tracks()}
    sprint_ids = {s['id'] for s in load_all_sprints()}
    task_ids = {t['id'] for t in load_all_tasks()}

    # Check task references
    for task in load_all_tasks():
        if task['sprint_id'] not in sprint_ids:
            errors.append(ReferenceError('task', task['id'],
                f"sprint_id '{task['sprint_id']}' does not exist"))
        if task['track_id'] not in track_ids:
            errors.append(ReferenceError('task', task['id'],
                f"track_id '{task['track_id']}' does not exist"))

    # Check sprint references
    for sprint in load_all_sprints():
        if sprint['track_id'] not in track_ids:
            errors.append(ReferenceError('sprint', sprint['id'],
                f"track_id '{sprint['track_id']}' does not exist"))

    # Check blocking references
    for task in load_all_tasks():
        for blocked_by in task.get('blocked_by', []):
            if blocked_by['target_id'] not in task_ids | sprint_ids | track_ids:
                errors.append(ReferenceError('task', task['id'],
                    f"blocked_by target '{blocked_by['target_id']}' does not exist"))

    return errors


def compare_databases(computed_db, declared_db):
    """
    Compare computed values vs declared values in YAML.

    This is the core validation for Sprint 4 (Data Validation & Integrity Audit).
    """
    discrepancies = []

    # Compare sprint progress
    for sprint_id in computed_db.sprint_ids():
        computed = computed_db.get_sprint_progress(sprint_id)
        declared = declared_db.get_sprint_progress(sprint_id)

        for field in ['tasks_total', 'tasks_completed', 'completion_percent']:
            if computed[field] != declared[field]:
                discrepancies.append(ComputedFieldError(
                    'sprint', sprint_id, field,
                    computed=computed[field],
                    declared=declared[field]
                ))

    # Compare track progress
    for track_id in computed_db.track_ids():
        computed = computed_db.get_track_progress(track_id)
        declared = declared_db.get_track_progress(track_id)

        for field in ['sprints_total', 'sprints_completed', 'tasks_total',
                      'tasks_completed', 'completion_percent']:
            if computed[field] != declared[field]:
                discrepancies.append(ComputedFieldError(
                    'track', track_id, field,
                    computed=computed[field],
                    declared=declared[field]
                ))

    # Compare roadmap progress
    computed = computed_db.get_roadmap_progress()
    declared = declared_db.get_roadmap_progress()

    for field in ['tracks_total', 'tracks_completed', 'sprints_total',
                  'sprints_completed', 'tasks_total', 'tasks_completed',
                  'completion_percent']:
        if computed[field] != declared[field]:
            discrepancies.append(ComputedFieldError(
                'roadmap', computed_db.roadmap_id, field,
                computed=computed[field],
                declared=declared[field]
            ))

    return discrepancies
```

### `vibey roadmap status`

Show sync status between DB and YAML.

```
Usage: vibey roadmap status

Output:
  Database: .vibey/roadmap.db (last modified: 2025-11-26T17:30:00)
  YAML files: 150 files (last git commit: abc123)
  Status: IN_SYNC | OUT_OF_SYNC | DB_AHEAD | YAML_AHEAD
```

---

## Error Handling

### YAML Parse Errors

```python
class YAMLParseError(Exception):
    def __init__(self, file_path: str, message: str, line: int = None):
        self.file_path = file_path
        self.message = message
        self.line = line
        super().__init__(f"{file_path}:{line}: {message}" if line else f"{file_path}: {message}")

def parse_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise YAMLParseError(file_path, str(e), getattr(e, 'problem_mark', {}).get('line'))
```

### Referential Integrity Errors

```python
class IntegrityError(Exception):
    def __init__(self, entity_type: str, entity_id: str, message: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = message
        super().__init__(f"{entity_type} '{entity_id}': {message}")

def validate_db_integrity():
    """Check all foreign key constraints."""
    errors = []

    # Check all sprints have valid track_id
    orphan_sprints = query("""
        SELECT id FROM sprints
        WHERE track_id NOT IN (SELECT id FROM tracks)
    """)
    for sprint_id in orphan_sprints:
        errors.append(IntegrityError('sprint', sprint_id, 'track_id references non-existent track'))

    # ... similar checks for other relationships

    if errors:
        raise IntegrityErrors(errors)
```

---

## Handling Edge Cases

### 1. Manual YAML Edits

**Policy:** YAML is read-only. Manual edits are overwritten on next dump.

**Mitigation:**
- Document this clearly in CONTRIBUTING.md
- Pre-commit hook always dumps DB → YAML
- If someone edits YAML manually and commits, the next person's dump will overwrite

**Warning Message:**
```
WARNING: Manual YAML edits detected. These will be overwritten by database state.
Files modified outside of database:
  - .vibey/roadmap/core-framework/track.yaml

To preserve manual changes, use 'vibey roadmap' commands instead.
```

### 2. Database Doesn't Exist

On `dump` when no DB exists:
```
ERROR: Database not found at .vibey/roadmap.db
Run 'vibey roadmap rebuild' to create database from YAML files.
```

### 3. YAML Files Missing

On `rebuild` when YAML directory is empty:
```
ERROR: No roadmap YAML files found in .vibey/roadmap/
Initialize with 'vibey roadmap init' or restore from git history.
```

### 4. Schema Version Mismatch

Include schema version in database:
```python
def check_schema_version():
    db_version = query("SELECT version FROM schema_version")
    if db_version != CURRENT_SCHEMA_VERSION:
        raise SchemaMismatchError(f"DB schema {db_version}, expected {CURRENT_SCHEMA_VERSION}")
```

On mismatch:
```
ERROR: Database schema version mismatch.
Database version: 1.0.0
Expected version: 1.1.0

Run 'vibey roadmap migrate' to upgrade database schema.
```

### 5. Concurrent Access

SQLite handles concurrent reads well but writes are serialized.

**Mitigation:**
- Use WAL mode for better concurrency
- Use short transactions
- CLI commands should be atomic

```python
def init_db():
    conn = sqlite3.connect('.vibey/roadmap.db')
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

---

## Testing Strategy

### Roundtrip Tests

```python
def test_yaml_roundtrip():
    """DB → YAML → DB should produce identical state."""

    # Setup: Create known DB state
    create_test_entities()

    # Dump to YAML
    dump_db_to_yaml()

    # Clear DB
    clear_all_tables()

    # Rebuild from YAML
    rebuild_db_from_yaml()

    # Compare: Should be identical
    assert get_all_tasks() == original_tasks
    assert get_roadmap_progress() == original_progress
```

### Determinism Tests

```python
def test_dump_determinism():
    """Multiple dumps should produce identical YAML."""

    dump_db_to_yaml()
    yaml_1 = read_all_yaml_files()

    dump_db_to_yaml()
    yaml_2 = read_all_yaml_files()

    assert yaml_1 == yaml_2
```

### Integrity Tests

```python
def test_computed_values_match():
    """Computed values in YAML should match DB views."""

    dump_db_to_yaml()

    # Read dumped progress values
    yaml_progress = parse_roadmap_yaml()['progress']

    # Query computed view
    db_progress = query("SELECT * FROM v_roadmap_progress WHERE roadmap_id = ?")

    assert yaml_progress['tasks_completed'] == db_progress['tasks_completed']
    assert yaml_progress['completion_percent'] == db_progress['completion_percent']
```

---

## Summary

| Aspect | Strategy |
|--------|----------|
| **Source of Truth** | Remote YAML (git) is ultimate; local SQLite is session working state |
| **Direction** | Bidirectional: DB → YAML (dump), YAML → DB (rebuild) |
| **Conflict Resolution** | Git merge process after DB→YAML dump |
| **Dump Safety** | Checksum tracking detects manual YAML edits before overwriting |
| **Rebuild Safety** | Dirty flag prevents data loss on git pull |
| **Determinism** | Fixed key order, sorted arrays, consistent null/timestamp formatting |
| **Validation** | 4 levels: schema, references, computed, full audit |
| **Error Handling** | Parse errors, integrity errors, schema version checks, conflict detection |

---

## Next Steps

1. **Task 6:** Create consolidated design document for review
2. **Sprint 1:** Begin core implementation

---

**Document Version:** 1.0.0
