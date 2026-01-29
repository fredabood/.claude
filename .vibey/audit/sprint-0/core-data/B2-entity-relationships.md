# B2: Entity Relationships Audit

**Task ID:** 01KFXF5B3HGQD72EQQAXM7P91Z
**Phase:** B2: Core Data Model
**Date:** 2026-01-29

## Executive Summary

Complete documentation of entity relationships in the Vibey data model, covering hierarchical parent-child relationships, cross-entity references, and the Triangle Model (Ticket-Commit-Artifact). The system uses a 4-level hierarchy (Roadmap → Track → Sprint → Task) with foreign keys in SQLite and embedded IDs in YAML. Key finding: the model supports complex relationship types including blocking relationships, soft dependencies, and artifact tracking, with denormalized caching in `depends_on` fields for performance.

## Methodology

**Files Analyzed:**
- `vibey/roadmap/database/schema.py:60-400` - SQLite schema definitions (33 tables)
- `vibey/roadmap/models/relationships.py:1-411` - Triangle Model implementation
- `vibey/operations/roadmap/query.py:1-1598` - Hierarchy traversal operations
- `.vibey/roadmap/tracks/*.yaml` - Track YAML storage example
- `.vibey/roadmap/tasks/*.yaml` - Task YAML storage example

## Findings

### 2. Hierarchical Relationships Table

| Parent | Child | FK Field | Cascade Behavior | Cardinality |
|--------|-------|----------|------------------|-------------|
| - | Roadmap | - | Root entity | 1 per repository |
| Roadmap | Track | `roadmap_id` | ON DELETE CASCADE | 1:N |
| Track | Sprint | `track_id` | ON DELETE CASCADE | 1:N |
| Sprint | Task | `sprint_id` | ON DELETE CASCADE | 1:N |
| Track | Sprint | `roadmap_id` | Denormalized copy | 1:N (redundant) |
| Sprint | Task | `track_id` | Denormalized copy | 1:N (redundant) |
| Sprint | Task | `roadmap_id` | Denormalized copy | 1:N (redundant) |

**Notes:**
- Tasks store `sprint_id`, `track_id`, and `roadmap_id` for efficient queries without joins
- Sprints store both `track_id` and `roadmap_id` for the same reason
- All cascade deletes propagate down the hierarchy

### 3. Cross-Entity References Table

| Reference Type | Source Entity | Target Entity | Field Name | Purpose |
|----------------|---------------|---------------|------------|---------|
| Blocking | Any | Any | `entity_blocks` | "This entity blocks these others" |
| Blocked By | Any | Any | `entity_blocked_by` | Inverse of blocking (deprecated) |
| Depends On | Sibling | Sibling | `entity_depends_on` | Soft dependencies between siblings |
| External Dependency | Any | External | `external_dependencies` | Non-roadmap prerequisites |
| Quality Gate | Track/Sprint | Gate Task | `quality_gates` | Gate task execution tracking |
| Development Gate | Sprint | External | `development_gates` | Sprint-level external dependencies |
| Commit Link | Task | GitCommit | `ticket_commit_links` | Triangle Model: Task ↔ Commit |
| Artifact Association | Task | Artifact | `ticket_artifact_associations` | Triangle Model: Task ↔ Artifact |
| Commit Change | GitCommit | Artifact | `commit_artifact_changes` | Triangle Model: Commit ↔ Artifact |
| Agent Assignment | Task | Agent | `assigned_agents` | Task worker assignment |
| Deliverable | Task/Sprint | Deliverable | `entity_deliverables` | Work output tracking |

### 4. Relationship Diagram (ASCII)

```
                                    ┌─────────────────┐
                                    │    ROADMAP      │
                                    │ (root entity)   │
                                    └────────┬────────┘
                                             │ 1:N
                     ┌───────────────────────┼───────────────────────┐
                     │                       │                       │
              ┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
              │   TRACK A   │◄───────►│   TRACK B   │◄───────►│   TRACK C   │
              │             │ depends │             │ blocks  │             │
              └──────┬──────┘   on    └──────┬──────┘         └──────┬──────┘
                     │ 1:N                   │ 1:N                   │ 1:N
         ┌───────────┼───────────┐           │                       │
         │           │           │           │                       │
  ┌──────▼─────┐┌────▼────┐┌─────▼────┐┌─────▼─────┐          ┌──────▼─────┐
  │  SPRINT 1  ││SPRINT 2 ││ SPRINT 3 ││ SPRINT 4  │          │  SPRINT 5  │
  └──────┬─────┘└─────────┘└──────────┘└───────────┘          └──────┬─────┘
         │ 1:N                                                       │ 1:N
    ┌────┴────┐                                                 ┌────┴────┐
    │         │                                                 │         │
┌───▼───┐ ┌───▼───┐                                        ┌───▼───┐ ┌───▼───┐
│TASK 1 │ │TASK 2 │                                        │TASK 5 │ │TASK 6 │
└───┬───┘ └───────┘                                        └───────┘ └───────┘
    │
    │ Triangle Model
    │
┌───▼────────────────────────────────────────────────────────────────────────┐
│                           TRIANGLE MODEL                                    │
│                                                                            │
│     ┌────────────┐                                                         │
│     │   TICKET   │ (Task)                                                  │
│     └──────┬─────┘                                                         │
│           /│\                                                              │
│          / │ \                                                             │
│    TicketCommitLink  TicketArtifactAssociation                             │
│        /   │   \                                                           │
│       /    │    \                                                          │
│ ┌────▼───┐ │  ┌──▼───────┐                                                 │
│ │GITCOMMIT│ │  │ ARTIFACT │                                                 │
│ └────┬────┘ │  └────┬─────┘                                                │
│      │      │       │                                                       │
│      └──────┴───────┘                                                       │
│      CommitArtifactChange                                                   │
└────────────────────────────────────────────────────────────────────────────┘
```

### 5. YAML Storage Patterns Table

| Relationship | Storage Method | Example | Pros/Cons |
|--------------|----------------|---------|-----------|
| Hierarchical (parent-child) | Embedded ID field | `track_id: 01KFW4F7KN9E7GTQTXEQXE8AKB` | Pro: Simple lookup; Con: Orphan risk |
| Sibling summaries | Embedded array of summary objects | `sprints: [{id: X, name: Y, status: Z}]` | Pro: Fast display; Con: Sync overhead |
| Dependencies | Embedded array of objects | `dependencies: [{target_id: X, type: Y}]` | Pro: Self-contained; Con: Duplication |
| Blocking | Embedded array (deprecated) | `blocked_by: [{blocker_id: X}]` | Pro: Simple; Con: Deprecated |
| Depends On | Embedded array with cache | `depends_on: [{blocker_id: X, current_status: Y}]` | Pro: No lookups; Con: Stale cache |
| Commits | Embedded array of commit objects | `commits: [{sha: X, message: Y}]` | Pro: Complete history; Con: Size growth |
| Progress | Embedded rollup object | `progress: {tasks_completed: 5}` | Pro: Fast read; Con: Recompute needed |

### 6. SQLite Storage Patterns Table

| Relationship | Table/Column | Constraint | Index |
|--------------|--------------|------------|-------|
| Roadmap→Track | `tracks.roadmap_id` | REFERENCES roadmaps(id) ON DELETE CASCADE | Auto (FK) |
| Track→Sprint | `sprints.track_id` | REFERENCES tracks(id) ON DELETE CASCADE | Auto (FK) |
| Sprint→Task | `tasks.sprint_id` | REFERENCES sprints(id) ON DELETE CASCADE | Auto (FK) |
| Entity Blocking | `entity_blocks` | UNIQUE(blocker_type, blocker_id, blocked_type, blocked_id) | Composite |
| Entity Blocked By | `entity_blocked_by` | UNIQUE(blocked_type, blocked_id, blocker_type, blocker_id) | Composite |
| Entity Depends On | `entity_depends_on` | UNIQUE(dependent_type, dependent_id, dependency_type, dependency_id) | Composite |
| Ticket↔Commit | `ticket_commit_links` | FOREIGN KEY (ticket_id) REFERENCES tasks(id) ON DELETE CASCADE | ticket_id |
| Ticket↔Artifact | `ticket_artifact_associations` | FOREIGN KEY (ticket_id, artifact_id) | Composite |
| Commit↔Artifact | `commit_artifact_changes` | FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE | artifact_id |
| Deliverables | `entity_deliverables` | UNIQUE(owner_type, owner_id, deliverable_id) | Junction table |
| Commits | `entity_commits` | UNIQUE(owner_type, owner_id, commit_id) | Junction table |

### 7. Traversal Operations Table

| Operation | Direction | Query Pattern | Use Case |
|-----------|-----------|---------------|----------|
| Get Parent | Up | `SELECT * FROM tracks WHERE id = (SELECT track_id FROM sprints WHERE id = ?)` | Context display |
| Get Children | Down | `SELECT * FROM sprints WHERE track_id = ?` | Sprint listing |
| Get Siblings | Lateral | `SELECT * FROM sprints WHERE track_id = ? AND id != ?` | Dependency checking |
| Get All Tasks in Track | Down (recursive) | `SELECT t.* FROM tasks t JOIN sprints s ON t.sprint_id = s.id WHERE s.track_id = ?` | Track progress |
| Get Blocking Chain | Graph | Recursive CTE on `entity_blocks` | Blocker analysis |
| Get Hierarchy Path | Up (recursive) | `QueryTicketLoader.get_path()` | Breadcrumb display |
| Aggregate Commits | Down (recursive) | `HierarchicalTicket.commits_aggregated` | Track commit history |
| Get Effective Requirements | Up (inherited) | `HierarchicalTicket.requirements_effective` | Requirement enforcement |

### 8. Delta Lake Relationship Strategy Table

| Relationship | Delta Pattern | JOIN Strategy | Denormalization |
|--------------|---------------|---------------|-----------------|
| Hierarchical FK | Store FK as STRING column | Standard equi-join | Include parent fields in child tables |
| Cross-entity blocking | Separate `entity_blocks` table | Self-join with type filter | Pre-compute blocked status as column |
| Depends On (cached) | Store as ARRAY<STRUCT> in parent | Explode array for analysis | Keep denormalized for read performance |
| Triangle Model | 3 separate tables | Multi-table joins | Consider materialized views |
| Progress rollup | Store as STRUCT column | N/A (denormalized) | Store in parent, refresh on change |
| Commit aggregation | Store commits in task only | Aggregate via parent FK | Consider materialized view per track |
| Summaries | Store as ARRAY<STRUCT> | Explode for filtering | Keep for list operations |

**Delta Lake Specific Considerations:**

1. **No Foreign Key Constraints**: Delta Lake doesn't enforce FKs; use application-level validation
2. **Denormalization Preferred**: JOIN operations in Databricks can be expensive; denormalize frequently accessed relationships
3. **ARRAY Types**: Use for embedded lists (summaries, commits, dependencies)
4. **STRUCT Types**: Use for nested objects (progress, metadata)
5. **Partitioning**: Consider partitioning by `roadmap_id` or `track_id` for query performance
6. **Z-Ordering**: Use Z-ORDER on frequently filtered columns (`status`, `track_id`)

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Hierarchical FKs are strings | Use same IDs in Delta Lake (direct mapping) | S | High |
| Progress is denormalized cache | Replicate cache pattern; trigger recompute on child update | M | Critical |
| depends_on caches blocker status | Maintain same cache in Delta Lake; refresh on sync | M | Critical |
| Triangle Model uses 3 tables | Replicate as 3 Delta tables with same schema | M | High |
| Summary arrays embedded in YAML | Flatten to separate tables OR keep as ARRAY<STRUCT> | L | Medium |
| CASCADE deletes in SQLite | Implement soft deletes in Delta Lake (no physical CASCADE) | M | High |
| Junction tables for many-to-many | Use ARRAY columns instead (Delta Lake pattern) | M | Medium |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Hierarchical table shows all 4 entity levels: PASS (Roadmap, Track, Sprint, Task)
- [x] Cross-entity table has >= 5 reference types: PASS (11 reference types documented)
- [x] ASCII relationship diagram included: PASS (includes hierarchy + Triangle Model)
- [x] Delta Lake strategy addresses JOINs and denormalization: PASS (8 strategies documented)

## References

- `vibey/roadmap/database/schema.py:60-400` - SQLite CREATE TABLE statements
- `vibey/roadmap/models/relationships.py:217-411` - TicketCommitLink, TicketArtifactAssociation, CommitArtifactChange
- `vibey/operations/roadmap/query.py:746-1249` - QueryTicketLoader hierarchy traversal
- `vibey/operations/roadmap/query.py:1251-1428` - Smart accessor functions (get_hierarchy_path, get_aggregated_commits)
- `.vibey/roadmap/tracks/01KFW4F7KN9E7GTQTXEQXE8AKB.yaml` - Track YAML example with embedded arrays
