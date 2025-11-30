# System Design Recommendations from Tasks 1-3

**Sprint:** sqlite-backend-6 (Unified Ticket Architecture & Criteria-Based Completion)
**Date:** 2025-11-30
**Author:** Claude Code
**Status:** Design Phase Complete
**Updated:** Aligned with UNIFIED_TICKET_ARCHITECTURE.md end-state

---

## Executive Summary

The three design tasks (001-003) have analyzed the current system and produced actionable recommendations for the directory restructure and file organization. This document consolidates those findings into a unified system design recommendation **aligned with the end-state from UNIFIED_TICKET_ARCHITECTURE.md**.

### Key Decisions Made

| Decision | Recommendation | Impact |
|----------|---------------|--------|
| **Directory Structure** | Option D (Hybrid) + Artifacts + Activity Log | 1,347 dirs → ~30 dirs (98% reduction) |
| **File Format** | YAML for tickets/artifacts, JSONL for activity log | Format matches use case |
| **Context Naming** | UTC timestamps (YYYY-MM-DDTHHMMZ) | Timezone-unambiguous ordering |
| **Activity Log** | Time-bucketed JSONL files | `activity_log/YYYY-MM.jsonl` |
| **Artifacts** | First-class YAML files | `artifacts/<ulid>.yaml` |

---

## Recommended Directory Structure (End-State)

### Final Architecture
```
.vibey/
├── roadmap.db                    # SQLite database (derived from files)
└── roadmap/
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # TICKET HIERARCHY (YAML - maps to `tickets` table)
    │ # ═══════════════════════════════════════════════════════════════
    ├── roadmap.yaml              # RoadmapTicket (1)
    ├── tracks/
    │   └── <track-id>.yaml       # TrackTicket files (36)
    ├── sprints/
    │   └── <sprint-id>.yaml      # SprintTicket files (180)
    ├── tasks/
    │   └── <task-id>.yaml        # TaskTicket files (945)
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # ARTIFACTS (YAML - maps to `artifacts` table)
    │ # ═══════════════════════════════════════════════════════════════
    ├── artifacts/
    │   └── <ulid>.yaml           # Artifact definitions (~500+)
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # ACTIVITY LOG (JSONL - maps to `activity_log` table)
    │ # ═══════════════════════════════════════════════════════════════
    ├── activity_log/
    │   └── <YYYY-MM>.jsonl       # Time-bucketed entries
    │
    │ # ═══════════════════════════════════════════════════════════════
    │ # CONTEXT (Markdown - human/AI documentation)
    │ # ═══════════════════════════════════════════════════════════════
    └── context/
        ├── tracks/
        │   └── <track-id>/
        │       └── <TYPE>_<TIMESTAMP>Z_<DETAIL>.md
        ├── sprints/
        │   └── <sprint-id>/
        │       └── <TYPE>_<TIMESTAMP>Z_<DETAIL>.md
        └── tasks/
            └── <task-id>/
                └── <TYPE>_<TIMESTAMP>Z_<DETAIL>.md
```

### Design Principle: SQLite is derived state; Git is source of truth

The entire SQLite database must be rebuildable from the git repo via `db rebuild`.

### What's in SQLite Only (NOT in files)
- Computed views (`v_ticket_progress`, `v_reverse_dependencies`, etc.)
- Indexes and foreign key constraints
- Cached/derived data

### What's in Version-Controlled Files
| Entity | Format | Notes |
|--------|--------|-------|
| Tickets | YAML | Human-editable, AI-readable |
| Artifacts | YAML | First-class entities with provenance |
| Activity Log | **JSONL** | Time-bucketed, append-friendly |
| Context | Markdown | Human/AI documentation |
| Criteria | Embedded YAML | Part of ticket, not separate |

### Comparison with Current Structure

| Metric | Current | End-State | Improvement |
|--------|---------|-----------|-------------|
| Max depth | 10 levels | 4 levels | 60% reduction |
| Total directories | 1,347 | ~30 | 98% reduction |
| Context directories | 77 scattered | 3 top-level | Consolidated |
| Artifact tracking | Embedded in tasks | First-class YAML files | Explicit |
| Audit trail | YAML files | JSONL files (time-bucketed) | Append-friendly |
| SQLite rebuildable | Partial | **100%** | Full git-based recovery |

---

## File Format Decision

### Recommendation: Keep YAML with Mitigations

**YAML Cons and Mitigations:**

| Con | Mitigation | Implementation |
|-----|------------|----------------|
| **Slow parsing** | SQLite is hot path; YAML only on dump/init | Already designed |
| **Indentation errors** | Pydantic validation on load | Catches malformed immediately |
| **Parser variations** | Use `ruamel.yaml` exclusively | Consistent round-trip |
| **No native schema** | Pydantic models as schema | Full validation on deserialize |

**Additional Design Considerations:**
1. **Strict mode parsing** - `ruamel.yaml` with `typ='safe'`
2. **Schema-first loading** - Always deserialize into Pydantic models
3. **Validation errors** - Clear messages with line numbers
4. **IDE support** - Generate JSON Schema from Pydantic models

---

## Context File Naming Convention

### Updated: UTC Timestamps with Z Suffix

**Format:** `<TYPE>_<TIMESTAMP>Z_<OPTIONAL_DETAIL>.md`

**Timestamp:** ISO 8601 UTC with minute precision: `YYYY-MM-DDTHHMMZ`

**Examples:**
```
AUDIT_REPORT_2025-11-30T1420Z.md
REMEDIATION_2025-11-26T1530Z.md
ANALYSIS_2025-11-30T2012Z_DIRECTORY_STRUCTURE.md
```

**Why UTC Timestamps with Z Suffix:**
- **Timezone-unambiguous** - Z suffix indicates UTC
- Multiple files created same day get distinct names
- Alphabetical sorting = chronological ordering
- Correlates with activity_log timestamps (also UTC)
- Enables precise cross-referencing across timezones

---

## Alignment with UNIFIED_TICKET_ARCHITECTURE.md

### Ticket Model (Parts 1-3)

The directory structure maps directly to the layer architecture:

| Layer | Model | Directory |
|-------|-------|-----------|
| Layer 3 | RoadmapTicket | `roadmap.yaml` |
| Layer 3 | TrackTicket | `tracks/<id>.yaml` |
| Layer 3 | SprintTicket | `sprints/<id>.yaml` |
| Layer 3 | TaskTicket | `tasks/<id>.yaml` |

**Criteria are EMBEDDED** in ticket YAML (not separate files):
```yaml
ticket:
  id: sqlite-backend-6-task-001
  criteria:
    - id: crit-001
      description: Analysis document created
      target:
        type: artifact
        artifact_id: 01JDK9A2B3...
```

### Artifact Model (Part 13)

Artifacts are **first-class entities** with their own files:

| Entity | Directory |
|--------|-----------|
| Artifact | `artifacts/<ulid>.yaml` |

This enables:
- Pre-existing file tracking (provenance_type: PRE_EXISTING)
- Generated documentation links (documents_artifact_id)
- Impact analysis across the artifact graph
- Staleness detection for documentation

### Activity Log (Part 11.3)

**Critical Design Decision:** `activity_log` stored as time-bucketed JSONL files.

| Before | After |
|--------|-------|
| `audit_trail/` YAML files | `activity_log/YYYY-MM.jsonl` files |

**Why JSONL (not YAML, not SQLite-only):**
- **Git is source of truth** - SQLite must be rebuildable from git
- **Append-friendly** - New entries added to end of file
- **Fast parse** - JSON, not YAML (important for 10K+ entries)
- **Time-bucketed** - Monthly files keep size manageable
- **Not human-edited** - Machine-generated, no need for YAML readability

**Sample JSONL entry:**
```json
{"timestamp":"2025-11-30T20:10:46Z","type":"task_started","entity_type":"task","entity_id":"sqlite-backend-6-task-001","changed_by":"claude-code"}
```

### Database Tables (Parts 7, Appendix D, Part 13)

| Table | File Format | Notes |
|-------|-------------|-------|
| `tickets` | YAML (split by type) | Roadmap + Tracks + Sprints + Tasks |
| `criteria` | Embedded in ticket YAML | Not separate files |
| `artifacts` | YAML | `artifacts/<ulid>.yaml` |
| `activity_log` | **JSONL** | `activity_log/YYYY-MM.jsonl` |

---

## Migration Transformations

| Before | After | Notes |
|--------|-------|-------|
| `track.yaml` (nested) | `tracks/<id>.yaml` | Flat structure |
| `sprint.yaml` (nested) | `sprints/<id>.yaml` | Flat structure |
| `task.yaml` (nested) | `tasks/<id>.yaml` | Flat structure |
| `deliverables` array | `Artifact` files + `ArtifactTarget` | First-class entities |
| `quality_gates` array | `Criterion` with `ThresholdTarget` | Embedded in ticket |
| `blocked_by`/`depends_on` | `Criterion` with `CompletableTarget` | Unified blocking |
| `audit_trail/` YAML files | `activity_log/` JSONL files | Time-bucketed, append-friendly |
| `metadata/commits/` | Embedded in ticket `commits_local` | JSON array |
| `metadata/standards/` | Requirements → Criteria | Converted |

---

## Implementation Order

1. **Sprint 6** (Current) - Core model implementation
   - Pydantic models with embedded criteria
   - SQLAlchemy ORM with single-table inheritance
   - CRUD operations using new models

2. **Sprint 7** - Artifact System Architecture
   - First-class Artifact entity
   - ArtifactTarget for criteria
   - Provenance tracking

3. **Sprint 8** - Serialization Migration
   - Task 011: Directory restructure
   - New YAML loader/dumper patterns
   - Artifact file generation

4. **Sprint 12** - Production Cutover
   - Tasks 008-009: Migration execution
   - Context file consolidation
   - Final validation

---

## Path Patterns (End-State)

### YAML Files (Tickets + Artifacts)
```bash
# Ticket hierarchy
.vibey/roadmap.yaml
.vibey/roadmap/tracks/<track-id>.yaml
.vibey/roadmap/sprints/<sprint-id>.yaml
.vibey/roadmap/tasks/<task-id>.yaml

# Artifacts
.vibey/roadmap/artifacts/<ulid>.yaml
```

### JSONL Files (Activity Log)
```bash
# Time-bucketed activity log
.vibey/roadmap/activity_log/2025-11.jsonl
.vibey/roadmap/activity_log/2025-12.jsonl
```

### Context Files (Markdown with UTC timestamps)
```bash
.vibey/roadmap/context/tracks/<track-id>/<TYPE>_<TIMESTAMP>Z.md
.vibey/roadmap/context/sprints/<sprint-id>/<TYPE>_<TIMESTAMP>Z.md
.vibey/roadmap/context/tasks/<task-id>/<TYPE>_<TIMESTAMP>Z.md
```

### Glob Examples
```bash
# All track definitions
.vibey/roadmap/tracks/*.yaml

# All tasks for a sprint
.vibey/roadmap/tasks/sqlite-backend-6-*.yaml

# All artifacts
.vibey/roadmap/artifacts/*.yaml

# All activity log entries
.vibey/roadmap/activity_log/*.jsonl

# All context for a track
.vibey/roadmap/context/tracks/sqlite-backend/*.md

# All audit reports (with Z suffix)
.vibey/roadmap/context/**/*AUDIT_REPORT_*Z*.md
```

---

## Summary of Design Decisions

### Confirmed
1. **Directory Structure:** Option D + Artifacts + Activity Log folders
2. **File Format:** YAML for tickets/artifacts, JSONL for activity log
3. **Context Naming:** UTC timestamps with Z suffix (YYYY-MM-DDTHHMMZ)
4. **Artifacts:** First-class YAML files
5. **Activity Log:** Time-bucketed JSONL files (rebuildable)
6. **Criteria:** Embedded in ticket YAML
7. **SQLite:** 100% rebuildable from git

### YAML Cons Mitigated
1. Slow parsing → SQLite is hot path
2. Indentation errors → Pydantic validation
3. Parser variations → ruamel.yaml exclusively
4. No schema → Pydantic models as schema

### Key Architecture Alignment
- Directory structure reflects Ticket hierarchy
- Artifacts are first-class (Part 13)
- Activity log as JSONL replaces audit_trail (Part 11.3)
- Criteria embedded, not separate files
- **Git is source of truth** - SQLite fully rebuildable

---

## Next Steps

1. ✅ Task 001-003 complete - Design decisions finalized
2. → Continue with Task 004 - Core models: Entity IDs and Types
3. → Proceed through Sprint 6 with current structure
4. → Implement artifacts in Sprint 7
5. → Restructure directory in Sprint 8 Task 011
6. → Complete cutover in Sprint 12 Tasks 008-009

---

## Document References

| Document | Location | Purpose |
|----------|----------|---------|
| UNIFIED_TICKET_ARCHITECTURE.md | Sprint 6 root | Master architecture |
| DIRECTORY_STRUCTURE_ANALYSIS.md | context/tasks/001 | Options analysis |
| FILE_FORMAT_EVALUATION.md | context/tasks/002 | Format benchmarks |
| CONTEXT_CONSOLIDATION_STRATEGY.md | context/tasks/003 | Naming convention |
