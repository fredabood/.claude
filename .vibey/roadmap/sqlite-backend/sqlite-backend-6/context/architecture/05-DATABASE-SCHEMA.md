# Database Schema

## Tables

| Class | Table | Notes |
|-------|-------|-------|
| Completable + subtypes | `completables` | Single-table inheritance via `completable_type` (ticket/artifact) |
| Ticket subtypes | `completables` | ticket_type discriminator for roadmap/track/sprint/task |
| Criterion | `criteria` | Polymorphic target via `target_type` + `target_data` JSON |
| ActivityLogEntry | `activity_log` | Context stored as JSON |

### Unified Completables Table

Since both `Ticket` and `Artifact` extend `Completable`, they share a single table with type discriminators:

```sql
CREATE TABLE completables (
    -- Completable fields (shared by all)
    id TEXT PRIMARY KEY,           -- ULID
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,          -- TicketStatus enum
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    -- Type discriminator
    completable_type TEXT NOT NULL,  -- 'ticket' or 'artifact'

    -- Ticket-specific fields (NULL for artifacts)
    ticket_type TEXT,              -- 'roadmap', 'track', 'sprint', 'task'
    parent_id TEXT,
    sequence INTEGER,
    slug TEXT,
    started_at TEXT,
    completed_at TEXT,
    assigned_agents TEXT,          -- JSON array
    commits TEXT,                  -- JSON array
    priority TEXT,
    deferred INTEGER,
    estimated_duration TEXT,
    estimated_tokens INTEGER,      -- Direct estimate (any ticket level, not just tasks)
    complexity TEXT,               -- TaskTicket only
    task_type TEXT,                -- TaskTicket only
    plan_file TEXT,                -- SprintTicket only

    -- Artifact-specific fields (NULL for tickets)
    paths TEXT,                    -- JSON array
    content_hash TEXT,
    artifact_type TEXT,
    artifact_subtype TEXT,
    provenance TEXT,               -- JSON object
    documents_artifact_id TEXT,
    depends_on_artifact_ids TEXT,  -- JSON array

    FOREIGN KEY (parent_id) REFERENCES completables(id),
    FOREIGN KEY (documents_artifact_id) REFERENCES completables(id)
);
```

---

## Core Tables

### completables

**Code:** [`sample_code/sql/table_completables.sql`](../sample_code/sql/table_completables.sql)

Uses single-table inheritance with two levels of discrimination:

**Level 1 - completable_type:**
- `ticket` → Ticket subtypes (work items)
- `artifact` → Artifact (file entities)

**Level 2 - ticket_type (for tickets only):**
- `roadmap` → RoadmapTicket
- `track` → TrackTicket
- `sprint` → SprintTicket
- `task` → TaskTicket

### activity_log

**Code:** [`sample_code/sql/table_activity_log.sql`](../sample_code/sql/table_activity_log.sql)

---

## Key Views

| View | Purpose | Code |
|------|---------|------|
| `v_ticket_progress` | Progress calculation per transition type | - |
| `v_reverse_dependencies` | "Who depends on ticket X?" | [`view_v_reverse_dependencies.sql`](../sample_code/sql/view_v_reverse_dependencies.sql) |
| `v_required_children` | Non-deferred children for completion | [`view_v_required_children.sql`](../sample_code/sql/view_v_required_children.sql) |
| `v_effective_tokens` | Aggregated tokens (direct OR sum of children) | - |
| `v_orphan_artifacts` | Artifacts not referenced by any criterion | - |
| `v_documentation_graph` | What documents what | - |
| `v_stale_documentation` | Docs needing update | - |
| `v_ticket_siblings` | Sibling navigation with prev/next | [`view_v_ticket_siblings.sql`](../sample_code/sql/view_v_ticket_siblings.sql) |
| `v_ticket_artifacts` | All artifacts by ticket | - |

### v_effective_tokens

Computes effective tokens using COALESCE: if `estimated_tokens` is set, use it; otherwise aggregate children.

```sql
CREATE VIEW v_effective_tokens AS
WITH RECURSIVE token_tree AS (
    -- Base case: leaf tickets with direct estimates
    SELECT id, estimated_tokens as effective_tokens
    FROM completables
    WHERE completable_type = 'ticket'
      AND estimated_tokens IS NOT NULL

    UNION ALL

    -- Recursive case: parent aggregates from children
    SELECT p.id, SUM(c.effective_tokens) as effective_tokens
    FROM completables p
    JOIN token_tree c ON c.parent_id = p.id
    WHERE p.completable_type = 'ticket'
      AND p.estimated_tokens IS NULL
    GROUP BY p.id
)
SELECT * FROM token_tree;
```

---

## Entity Mapping

### Completable Hierarchy

```
completables (single table)
│
├── completable_type = 'ticket'
│   ├── ticket_type = 'roadmap' → RoadmapTicket fields
│   ├── ticket_type = 'track'   → TrackTicket fields
│   ├── ticket_type = 'sprint'  → SprintTicket fields
│   └── ticket_type = 'task'    → TaskTicket fields
│
└── completable_type = 'artifact'
    └── Artifact fields (paths, content_hash, provenance, etc.)
```

### Criterion Storage

```
criteria
├── id (ULID)
├── completable_id (FK → completables)  # References Ticket OR Artifact
├── blocks_transition_to (enum)
├── target_type (discriminator)
└── target_data (JSON) → polymorphic target fields
```

### CompletableTarget (Unified Reference)

```
When target_type = 'completable':
target_data = {
    "completable_id": "01HXYZ..."  # Can be Ticket OR Artifact ULID
}
```

This allows both Tickets and Artifacts to depend on each other uniformly.

---

## What's in SQLite Only (NOT in files)

- Computed views (`v_ticket_progress`, `v_reverse_dependencies`, etc.)
- Indexes and foreign key constraints
- Cached/derived data

---

## What's in Version-Controlled Files

| Entity | Format | Notes |
|--------|--------|-------|
| Tickets | YAML | Human-editable, AI-readable |
| Artifacts | YAML | First-class entities with provenance |
| Activity Log | **JSONL** | Time-bucketed, append-friendly |
| Context | Markdown | Human/AI documentation |
| Criteria | Embedded YAML | Part of ticket, not separate |

---

## Design Principle

**SQLite is derived state; Git is source of truth.**

The entire SQLite database must be rebuildable from the git repo via `db rebuild`.
