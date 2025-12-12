# ADR-0003: SQLite + YAML Dual Storage

## Status

Accepted

## Context

Roadmap data needs to satisfy competing requirements:

1. **Version control**: Collaborative editing, merge, history tracking
2. **Fast queries**: Efficient filtering, searching, aggregation
3. **Human readability**: Debugging, manual inspection
4. **Relationship integrity**: Foreign key constraints, cascading updates
5. **Offline capability**: Work without network

Single-format options had significant drawbacks:

**YAML only:**
- Slow queries (must load all files)
- No relationship enforcement
- Complex aggregations require loading entire dataset

**SQLite only:**
- Binary format, poor git diffs
- Merge conflicts hard to resolve
- Not human-editable for quick fixes

## Decision

Maintain both SQLite and YAML representations:

- **YAML files** are the source of truth (version controlled)
- **SQLite database** is a query cache (regenerable, gitignored)
- **Sync** happens on CLI operations, git hooks, or explicit rebuild

```
.vibey/roadmap/
├── tracks/              # YAML source of truth
├── sprints/
├── tasks/
└── roadmap.db          # SQLite cache (gitignored)
```

**Sync strategy:**
1. CLI write operations update both YAML and SQLite
2. External YAML changes detected via modification timestamps
3. `vibey roadmap db rebuild` forces full sync
4. Git hooks can trigger sync on pull/checkout

## Consequences

### Positive

- **Git-friendly**: YAML for collaboration, history, PRs
- **Fast queries**: SQLite for complex operations
- **Human-readable**: Can inspect/edit YAML directly
- **Recoverable**: Can rebuild database from YAML
- **Hybrid access**: Choose format per use case

### Negative

- **Sync complexity**: Must keep two representations aligned
- **Potential drift**: External YAML edits may miss database
- **Storage duplication**: Same data in two formats
- **Write overhead**: Every write touches two stores

### Neutral

- Database is gitignored (regenerated locally)
- Database schema can evolve independently of YAML structure
- Different tools can prefer different backends

## Implementation Details

### Database Schema

26 tables including:
- `tracks`, `sprints`, `tasks`
- `audit_trail` for change history
- `activity_log` for detailed events

### Sync Operations

```python
# Read: prefer SQLite, fallback to YAML
def load_task(task_id: str) -> Task:
    try:
        return sql_loader.load_task(task_id)
    except DatabaseError:
        return yaml_loader.load_task(task_id)

# Write: update both
def save_task(task: Task) -> None:
    yaml_dumper.dump_task(task)
    sql_dumper.dump_task(task)
```

### CLI Backend Selection

```bash
vibey roadmap status                    # auto (SQLite if available)
vibey roadmap status --backend sqlite   # force SQLite
vibey roadmap status --backend yaml     # force YAML
vibey roadmap db rebuild                # rebuild from YAML
```

## Alternatives Considered

### YAML-only with Caching

**Pros:**
- Simpler architecture
- Single source of truth

**Cons:**
- Cache invalidation complexity
- Still need query capabilities

### SQLite-only with Export

**Pros:**
- Single authoritative store
- Full SQL capabilities

**Cons:**
- Version control limitations
- Merge resolution complexity

### JSON instead of YAML

**Pros:**
- Faster parsing
- More precise data types

**Cons:**
- Less human-readable
- Worse git diffs (no comments)

## References

- SQLite backend implementation in sqlite-backend track
- Round-trip validation tests in `tests/roadmap/serialization/`
- Database schema in `vibey/roadmap/serialization/schema.sql`
