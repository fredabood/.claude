# Directory Structure Analysis

**Task:** sqlite-backend-6-task-001
**Date:** 2025-11-30
**Status:** In Progress

## Current Structure Analysis

### Statistics
| Metric | Count |
|--------|-------|
| Total directories | 1,347 |
| Total YAML files | 1,171 |
| Track files (track.yaml) | 36 |
| Sprint files (sprint.yaml) | 180 |
| Task files (task.yaml) | 945 |
| Context directories | 77 |
| Context files | 253 |
| Markdown files | 343 |
| Max directory depth | 10 levels |

### Current Hierarchy
```
.vibey/
├── roadmap.yaml              # Root roadmap definition
├── roadmap.db                # SQLite database
└── roadmap/
    └── <track-id>/           # 36 track folders
        ├── track.yaml
        ├── context/          # Optional context files
        └── <sprint-id>/      # ~5 sprint folders per track
            ├── sprint.yaml
            ├── context/      # Optional context files
            └── <task-id>/    # ~5 task folders per sprint
                ├── task.yaml
                └── context/  # Optional context files
```

### Problems with Current Structure
1. **Deep nesting** - 10 levels deep for task context files
2. **1,347 directories** - Massive directory count for ~1,161 entities
3. **Scattered context** - 77 context directories, hard to find related files
4. **Complex traversal** - Dump/init must recursively walk tree
5. **Name redundancy** - Track ID repeated in sprint ID, sprint ID in task ID
6. **Git noise** - Many directory changes for simple operations

### SQLite Tables to Mirror (End-State from UNIFIED_TICKET_ARCHITECTURE.md)

**Core Tables (High-Volume, Ticket Hierarchy):**
| Table | Rows | Notes | YAML Files? |
|-------|------|-------|-------------|
| tickets | ~1,162 | Unified ticket table (roadmap + tracks + sprints + tasks via single-table inheritance) | Yes - split by ticket_type |
| criteria | ~2,000+ | Completion criteria for all tickets | Embedded in ticket YAML |
| artifacts | ~500+ | First-class artifact entities | Yes |

**Activity/Audit Tables (Append-Heavy, Not Human-Edited):**
| Table | Rows | Notes | YAML Files? |
|-------|------|-------|-------------|
| activity_log | ~10,000+ | Unified activity log (replaces audit_trail) | **No** - SQLite only |

**Relationship/Junction Tables (Database-Only):**
| Table | Notes | YAML Files? |
|-------|-------|-------------|
| artifact_dependencies | Artifact → Artifact dependencies | No - computed |
| criteria_artifacts | Criterion → Artifact references | Embedded in criteria |

**Key Design Decisions from UNIFIED_TICKET_ARCHITECTURE.md:**
1. **Single `tickets` table** - Uses single-table inheritance with `ticket_type` discriminator
2. **`activity_log` replaces `audit_trail`** - High-volume, append-only, stays in SQLite only
3. **`artifacts` is first-class** - Independent entity, tracked via provenance
4. **`criteria` embedded** - Stored in tickets table as JSON, not separate files
5. **No separate standards/deliverables/quality_gates tables** - Converted to criteria

---

## Proposed Structure Options

### Option A: Table-Based Folders
```
.vibey/
├── roadmap.db
└── roadmap/
    ├── roadmaps/
    │   └── vibey-framework-v2.yaml
    ├── tracks/
    │   ├── sqlite-backend.yaml
    │   ├── git-integration.yaml
    │   └── ... (36 files)
    ├── sprints/
    │   ├── sqlite-backend-0.yaml
    │   ├── sqlite-backend-1.yaml
    │   └── ... (180 files)
    ├── tasks/
    │   ├── sqlite-backend-0-task-001.yaml
    │   ├── sqlite-backend-0-task-002.yaml
    │   └── ... (945 files)
    ├── commits/
    │   └── ... (commit reference files)
    ├── deliverables/
    │   └── ... (deliverable files)
    ├── quality_gates/
    │   └── ... (gate files)
    ├── audit_trail/
    │   └── ... (audit entry files)
    └── context/
        ├── tracks/
        │   └── <track-id>/
        ├── sprints/
        │   └── <sprint-id>/
        └── tasks/
            └── <task-id>/
```

**Pros:**
- Direct 1:1 mapping with SQLite tables
- Simple dump: `SELECT * FROM tracks` → write to `tracks/`
- Simple init: read `tracks/` → `INSERT INTO tracks`
- Max depth: 4 levels (vs current 10)
- ~15 directories (vs current 1,347)

**Cons:**
- Large folders (945 files in tasks/)
- Loses visual hierarchy (can't see sprint's tasks at glance)
- File names must encode hierarchy (sqlite-backend-0-task-001)

### Option B: Entity-Type Folders (Flatter)
```
.vibey/
├── roadmap.db
└── roadmap/
    ├── roadmaps.d/
    │   └── vibey-framework-v2.yaml
    ├── tracks.d/
    │   └── ... (36 files)
    ├── sprints.d/
    │   └── ... (180 files)
    ├── tasks.d/
    │   └── ... (945 files)
    └── context.d/
        └── ... (all context files with prefixed names)
```

**Pros:**
- Even flatter (3 levels max)
- `.d` convention signals "directory of items"
- Single context folder

**Cons:**
- Same large folder issue
- Less intuitive than Option A
- Non-standard naming convention

### Option C: Single Folder with Prefixes
```
.vibey/
├── roadmap.db
└── roadmap/
    ├── entities/
    │   ├── roadmap_vibey-framework-v2.yaml
    │   ├── track_sqlite-backend.yaml
    │   ├── sprint_sqlite-backend-0.yaml
    │   ├── task_sqlite-backend-0-task-001.yaml
    │   └── ... (~1,161 files)
    └── context/
        └── ... (all context files)
```

**Pros:**
- Simplest structure (2 folders)
- All entities in one place
- Easy glob: `entities/track_*.yaml`

**Cons:**
- 1,161 files in one folder (performance concern)
- Type prefix adds redundancy
- Hard to browse in file manager

### Option D: Hybrid (Recommended) - UPDATED FOR END-STATE
```
.vibey/
├── roadmap.db                    # SQLite database (derived from YAML/JSONL)
└── roadmap/
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # TICKET HIERARCHY (maps to unified `tickets` table)
    │ # ═══════════════════════════════════════════════════════════════
    ├── roadmap.yaml              # Single RoadmapTicket
    ├── tracks/
    │   └── <track-id>.yaml       # TrackTicket files (36)
    ├── sprints/
    │   └── <sprint-id>.yaml      # SprintTicket files (180)
    ├── tasks/
    │   └── <task-id>.yaml        # TaskTicket files (945)
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # ARTIFACTS (first-class entities, maps to `artifacts` table)
    │ # ═══════════════════════════════════════════════════════════════
    ├── artifacts/
    │   └── <artifact-id>.yaml    # Artifact definitions (~500+)
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # ACTIVITY LOG (time-bucketed JSONL, maps to `activity_log` table)
    │ # ═══════════════════════════════════════════════════════════════
    ├── activity_log/
    │   ├── 2025-11.jsonl         # November 2025 entries
    │   ├── 2025-12.jsonl         # December 2025 entries
    │   └── ...                   # Monthly buckets
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # CONTEXT (markdown files for human/AI consumption)
    │ # ═══════════════════════════════════════════════════════════════
    └── context/
        ├── tracks/
        │   └── <track-id>/       # Context per track
        ├── sprints/
        │   └── <sprint-id>/      # Context per sprint
        └── tasks/
            └── <task-id>/        # Context per task
```

**Design Principle: SQLite is derived state; Git is source of truth**

The entire SQLite database must be rebuildable from the git repo via `db rebuild`.

**What's in SQLite ONLY (not in files):**
- Computed views (v_ticket_progress, v_reverse_dependencies, etc.)
- Indexes and foreign key constraints
- Cached/derived data

**What's in version-controlled files:**
- All tickets (YAML) - roadmap, tracks, sprints, tasks with embedded criteria
- All artifacts (YAML) - first-class entities with provenance
- Activity log (JSONL) - time-bucketed, append-friendly
- Context files (Markdown) - human/AI documentation

**Pros:**
- Aligns with UNIFIED_TICKET_ARCHITECTURE.md end-state
- Ticket hierarchy clearly visible (tracks → sprints → tasks)
- Artifacts as first-class entities (not buried in metadata)
- No audit_trail in YAML (activity_log stays in SQLite)
- Context organized by entity type
- Max depth: 4 levels

**Cons:**
- Large folders (945 tasks, 500+ artifacts)
- Criteria embedded in ticket YAML (not separate files)

---

## Comparison Matrix

| Criterion | Current | Option A | Option B | Option C | Option D |
|-----------|---------|----------|----------|----------|----------|
| **Max depth** | 10 | 4 | 3 | 3 | 4 |
| **Total dirs** | 1,347 | ~15 | ~6 | ~3 | ~20 |
| **Dump simplicity** | Complex | Simple | Simple | Simple | Simple |
| **Init simplicity** | Complex | Simple | Simple | Simple | Simple |
| **SQLite 1:1 mapping** | No | Yes | Yes | Partial | Yes |
| **File navigation** | Poor | Good | Fair | Poor | Good |
| **Git diff clarity** | Poor | Good | Good | Fair | Good |
| **Glob patterns** | Complex | Simple | Simple | Simple | Simple |
| **Context organization** | Scattered | Organized | Flat | Flat | Organized |
| **Scalability (10K tasks)** | Poor | Good | Good | Poor | Good |

**Scoring (1-5, higher is better):**
| Criterion | Weight | Current | A | B | C | D |
|-----------|--------|---------|---|---|---|---|
| Dump/init simplicity | 5 | 1 | 5 | 5 | 5 | 5 |
| File navigation | 3 | 2 | 4 | 3 | 2 | 4 |
| Git diff readability | 3 | 2 | 4 | 4 | 3 | 4 |
| Tool compatibility | 2 | 3 | 5 | 5 | 4 | 5 |
| Scalability | 4 | 1 | 4 | 4 | 2 | 4 |
| Context organization | 3 | 2 | 4 | 2 | 2 | 5 |
| **Weighted Total** | | **29** | **85** | **77** | **61** | **89** |

---

## Recommendation

**Recommended: Option D (Hybrid)**

### Rationale
1. **Best balance** - Separates high-volume entities from metadata
2. **Context preserved** - Maintains entity-specific context organization
3. **SQLite mapping** - Direct correspondence with database tables
4. **Scalability** - Handles 10K+ tasks without single-folder issues
5. **Navigation** - Easy to find files by type

### File Naming Convention (End-State)
```
# Ticket files (by ticket_type, ID is filename)
roadmap.yaml                           # Single RoadmapTicket
tracks/<track-id>.yaml                 # TrackTicket
sprints/<sprint-id>.yaml               # SprintTicket
tasks/<task-id>.yaml                   # TaskTicket

# Artifact files (ULID is filename)
artifacts/<ulid>.yaml                  # Artifact entity

# Context files (organized by ticket, with timestamps)
context/tracks/<track-id>/<TYPE>_<TIMESTAMP>_<DETAIL>.md
context/sprints/<sprint-id>/<TYPE>_<TIMESTAMP>_<DETAIL>.md
context/tasks/<task-id>/<TYPE>_<TIMESTAMP>_<DETAIL>.md
```

**File Formats by Entity Type:**
| Entity | Format | Rationale |
|--------|--------|-----------|
| Tickets | YAML | Human-editable, AI-readable |
| Artifacts | YAML | Human-editable, AI-readable |
| Activity Log | **JSONL** | Append-heavy, fast parse, not human-edited |
| Context | Markdown | Human/AI documentation |
| Criteria | Embedded YAML | Part of ticket, not separate |

**What's NOT in files (SQLite-only):**
- Computed views (v_ticket_progress, v_reverse_dependencies)
- Indexes and foreign key constraints
- Cached/derived data

### Sample Directory Tree (End-State)
```
.vibey/
├── roadmap.db                         # SQLite: derived state, computed views, indexes
└── roadmap/
    │
    │ # TICKET HIERARCHY (YAML)
    ├── roadmap.yaml                   # RoadmapTicket (1 file)
    ├── tracks/
    │   ├── sqlite-backend.yaml        # TrackTicket with embedded criteria
    │   ├── git-integration.yaml
    │   └── ... (36 total)
    ├── sprints/
    │   ├── sqlite-backend-0.yaml      # SprintTicket with embedded criteria
    │   ├── sqlite-backend-6.yaml
    │   └── ... (180 total)
    ├── tasks/
    │   ├── sqlite-backend-0-task-001.yaml  # TaskTicket with embedded criteria
    │   ├── sqlite-backend-6-task-001.yaml
    │   └── ... (945 total)
    │
    │ # ARTIFACTS (YAML - first-class entities)
    ├── artifacts/
    │   ├── 01JDK9A2B3C4D5E6F7G8H9J0.yaml  # Code artifact
    │   ├── 01JDK9A2B3C4D5E6F7G8H9J1.yaml  # Documentation artifact
    │   └── ... (~500+ total)
    │
    │ # ACTIVITY LOG (JSONL - time-bucketed, append-friendly)
    ├── activity_log/
    │   ├── 2025-11.jsonl              # November 2025 (~1000 entries)
    │   └── 2025-12.jsonl              # December 2025
    │
    │ # CONTEXT (Markdown - human/AI readable)
    └── context/
        ├── tracks/
        │   ├── sqlite-backend/
        │   │   ├── AUDIT_REPORT_2025-11-16T1030Z.md
        │   │   └── REMEDIATION_2025-11-26T0900Z.md
        │   └── git-integration/
        ├── sprints/
        │   ├── sqlite-backend-4/
        │   │   └── SOURCE_OF_TRUTH_2025-11-28T1600Z.md
        │   └── sqlite-backend-6/
        │       ├── UNIFIED_TICKET_ARCHITECTURE.md  # Main design doc
        │       └── SYSTEM_DESIGN_RECOMMENDATIONS.md
        └── tasks/
            └── sqlite-backend-6-task-001/
                └── ANALYSIS_2025-11-30T2012Z_DIRECTORY_STRUCTURE.md
```

### Sample Ticket YAML (with embedded criteria)
```yaml
# tasks/sqlite-backend-6-task-001.yaml
ticket:
  id: sqlite-backend-6-task-001
  ticket_type: task
  name: Analyze optimal directory structure
  description: |
    Design the new .vibey directory structure that mirrors SQLite database.
  status: completed
  parent_ref: sqlite-backend-6  # Links to sprint

  # Criteria are EMBEDDED, not separate files
  criteria:
    - id: crit-001
      description: Directory structure comparison matrix created
      blocks_transition_to: completed
      required: true
      target:
        type: artifact
        artifact_id: 01JDK9A2B3C4D5E6F7G8H9J0
        verification: file_exists

    - id: crit-002
      description: Recommendation document with rationale
      blocks_transition_to: completed
      required: true
      target:
        type: artifact
        artifact_id: 01JDK9A2B3C4D5E6F7G8H9J1

  # Task-specific semantic fields
  semantic_fields:
    task_type: development
    estimated_tokens: 2000
    complexity: medium
    phase_label: design
```

### Sample Artifact YAML
```yaml
# artifacts/01JDK9A2B3C4D5E6F7G8H9J0.yaml
artifact:
  id: 01JDK9A2B3C4D5E6F7G8H9J0
  name: Directory Structure Analysis
  description: Comparison matrix of directory structure options
  artifact_type: documentation
  artifact_subtype: analysis

  paths:
    - .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/DIRECTORY_STRUCTURE_ANALYSIS.md

  provenance:
    provenance_type: ticket_created
    created_by_ticket_id: sqlite-backend-6-task-001
    created_by_criterion_id: crit-001

  # State
  exists: true
  is_stale: false

  created_at: '2025-11-30T20:12:00+00:00'
  updated_at: '2025-11-30T20:12:00+00:00'
```

### Sample Activity Log JSONL
```jsonl
# activity_log/2025-11.jsonl (one JSON object per line)
{"timestamp":"2025-11-30T20:10:46Z","type":"sprint_started","description":"Sprint sqlite-backend-6 started","entity_type":"sprint","entity_id":"sqlite-backend-6","changed_by":"claude-code"}
{"timestamp":"2025-11-30T20:10:50Z","type":"task_started","description":"Task sqlite-backend-6-task-001 started","entity_type":"task","entity_id":"sqlite-backend-6-task-001","changed_by":"claude-code"}
{"timestamp":"2025-11-30T20:12:46Z","type":"task_completed","description":"Task sqlite-backend-6-task-001 completed","entity_type":"task","entity_id":"sqlite-backend-6-task-001","changed_by":"claude-code"}
{"timestamp":"2025-11-30T20:12:46Z","type":"criterion_met","description":"Directory structure analysis created","entity_type":"criterion","entity_id":"crit-001","context":{"artifact_id":"01JDK9A2B3C4D5E6F7G8H9J0"}}
```

**Why JSONL for Activity Log:**
- **Append-friendly** - New entries added to end of file
- **Fast parse** - JSON, not YAML (important for 10K+ entries)
- **Git-friendly** - Each line is independent, clean diffs
- **Time-bucketed** - Monthly files keep size manageable
- **Not human-edited** - Machine-generated, no need for YAML readability

### Migration Impact
- **Directory reduction**: 1,347 → ~30 directories (98% reduction)
- **File moves**: All YAML files move to new locations
- **Context moves**: 253 context files to consolidated structure
- **New files created**: ~500+ artifact YAML files (from embedded deliverables)
- **Format change**: audit_trail YAML → activity_log JSONL (time-bucketed)
- **Git history**: Use `git mv` to preserve history

### Key Migration Transformations

| Before | After | Notes |
|--------|-------|-------|
| `track.yaml` (nested) | `tracks/<id>.yaml` | Flat structure |
| `sprint.yaml` (nested) | `sprints/<id>.yaml` | Flat structure |
| `task.yaml` (nested) | `tasks/<id>.yaml` | Flat structure |
| `deliverables` array | `Artifact` files + `ArtifactTarget` criteria | First-class entities |
| `quality_gates` array | `Criterion` with `ThresholdTarget` | Embedded in ticket |
| `audit_trail/` YAML files | `activity_log/` JSONL files | Time-bucketed, append-friendly |
| `blocked_by`/`depends_on` | `Criterion` with `CompletableTarget` | Unified blocking model |

---

## Next Steps
1. ✅ Task 001 complete - Directory structure analysis (this document)
2. ✅ Task 002 complete - File format evaluation (keep YAML)
3. ✅ Task 003 complete - Context file consolidation
4. → Continue with Sprint 6 Tasks 004-018 (core model implementation)
5. → Implement in Sprint 7 (Artifact System Architecture)
6. → Implement in Sprint 8 Task 011 (actual directory restructure)
7. → Migrate in Sprint 12 (production cutover)

---

## Appendix: End-State Alignment with UNIFIED_TICKET_ARCHITECTURE.md

### Ticket Model (Part 3)
| Layer | Model | Directory |
|-------|-------|-----------|
| Layer 3 | RoadmapTicket | `roadmap.yaml` |
| Layer 3 | TrackTicket | `tracks/<id>.yaml` |
| Layer 3 | SprintTicket | `sprints/<id>.yaml` |
| Layer 3 | TaskTicket | `tasks/<id>.yaml` |

### Artifact Model (Part 13)
| Entity | Directory |
|--------|-----------|
| Artifact | `artifacts/<ulid>.yaml` |

### Activity Log (Part 11.3)
| Entity | Storage |
|--------|---------|
| ActivityLogEntry | **JSONL files** (`activity_log/YYYY-MM.jsonl`) + SQLite |

Activity log is stored in time-bucketed JSONL files for version control, then loaded into SQLite for queries.

### Database Tables (Part 7 + Appendix D)
| Table | File Format | Notes |
|-------|-------------|-------|
| `tickets` | YAML (split by type) | Roadmap + Tracks + Sprints + Tasks |
| `criteria` | Embedded in ticket YAML | Not separate files |
| `artifacts` | YAML | First-class entity files |
| `activity_log` | **JSONL** (time-bucketed) | `activity_log/YYYY-MM.jsonl` |

This directory structure is optimized for the **complete end-state** after sqlite-backend track completion.
