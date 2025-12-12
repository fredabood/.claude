# ADR-0002: Flat Directory Structure for Roadmap Files

## Status

Accepted

## Context

The original roadmap system used a hierarchical directory structure:

```
.vibey/roadmap/
└── track-name/
    └── track.yaml
    └── sprint-name/
        └── sprint.yaml
        └── task-name/
            └── task.yaml
```

This created problems at scale:
- 40 tracks × 10 sprints × 10 tasks = 4,000+ directories
- Expensive `git status` operations (full directory traversal)
- Complex path resolution for ID lookups
- Difficult to rename tracks/sprints (path changes)
- Deep nesting made shell navigation tedious

## Decision

Use a flat directory structure with ULID-based filenames:

```
.vibey/roadmap/
├── tracks/
│   └── 01KC2D0JK9JKQXGQW6MQEB0JZP.yaml
├── sprints/
│   └── 01KC2D0JKVT80AFQ6C1PA8CKJD.yaml
└── tasks/
    └── 01KC2D0JK7READW9KAK1HBX4B8.yaml
```

Each entity type has its own directory, with files named by ULID.

**Entity relationships** are stored in file contents:
```yaml
task:
  id: 01KC2D0JK7READW9KAK1HBX4B8
  sprint_id: 01KC2D0JKVT80AFQ6C1PA8CKJD
  track_id: 01KC2D0JK9JKQXGQW6MQEB0JZP
```

## Consequences

### Positive

- **98% directory reduction**: 3 directories vs 4,000+
- **Fast git operations**: Minimal directory traversal
- **Simple file lookup**: `tracks/{id}.yaml` directly
- **Easy rename/restructure**: Update content, not paths
- **Glob-friendly**: Easy to iterate all entities of a type
- **Parallel-safe**: No directory contention

### Negative

- **Lost visual hierarchy**: Can't browse tracks→sprints→tasks in file explorer
- **ID lookup required**: Need ID-to-name lookup for humans
- **Migration complexity**: One-time conversion of existing data
- **Less intuitive for new users**: Must use CLI, not file browsing

### Neutral

- Files still contain hierarchical relationships via ID references
- SQLite database provides query interface for hierarchy navigation
- Context files remain hierarchical (`.vibey/roadmap/context/sprints/name/`)

## Alternatives Considered

### Keep Hierarchical Structure

**Pros:**
- Intuitive browsing
- Self-documenting paths

**Cons:**
- Performance issues at scale
- Rename complexity

### Hybrid Structure

**Pros:**
- Some browsability
- Some performance benefit

**Cons:**
- Complexity of two patterns
- Unclear boundaries

### Single File (All in roadmap.yaml)

**Pros:**
- Simplest possible structure
- Single file to manage

**Cons:**
- Merge conflicts in collaborative environments
- Can't selectively load entities
- File grows unbounded

## References

- [Git performance with many directories](https://github.blog/2022-06-29-improve-git-monorepo-performance-with-a-file-system-monitor/)
- Migration implementation in sqlite-backend track Sprint 5
