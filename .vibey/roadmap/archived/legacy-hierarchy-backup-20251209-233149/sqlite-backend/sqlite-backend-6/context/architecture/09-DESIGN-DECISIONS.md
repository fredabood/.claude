# Design Decisions (Tasks 001-003)

This document consolidates the design decisions from Sprint 6's design phase tasks.

---

## Directory Structure Analysis (Task 001)

### Current State Problems
- Deep nesting (10 levels for task context files)
- 1,347 directories for ~1,161 entities
- 77 scattered context directories
- Name redundancy (track ID repeated in sprint/task IDs)

### Recommended Structure
```
.vibey/
├── roadmap.db                    # SQLite database (derived)
└── roadmap/
    ├── roadmap.yaml              # RoadmapTicket (1)
    ├── tracks/                   # TrackTicket files (36)
    ├── sprints/                  # SprintTicket files (180)
    ├── tasks/                    # TaskTicket files (945)
    ├── artifacts/                # Artifact definitions (~500+)
    ├── activity_log/             # Time-bucketed JSONL
    └── context/                  # Human/AI documentation
        ├── tracks/<track-id>/
        ├── sprints/<sprint-id>/
        └── tasks/<task-id>/
```

### Improvements

| Metric | Current | End-State | Improvement |
|--------|---------|-----------|-------------|
| Max depth | 10 levels | 4 levels | 60% reduction |
| Total directories | 1,347 | ~30 | 98% reduction |
| Context directories | 77 scattered | 3 top-level | Consolidated |

---

## File Format Evaluation (Task 002)

### Recommendation: Keep YAML for all roadmap files

### Benchmark Results

| Format | Parse Time (1000 iter) | Size |
|--------|------------------------|------|
| YAML | 749.84 ms | 1,276 bytes |
| JSON | 3.18 ms | 1,530 bytes |

Despite JSON being 100-200x faster to parse, YAML's benefits outweigh the performance difference:
1. Human readability is critical for AI context and manual editing
2. Parse time difference (708ms vs 3ms for 945 tasks) is negligible in practice
3. Git diffs are significantly more readable with YAML
4. Existing tooling and codebase is YAML-based

### Mitigations for YAML

| Con | Mitigation |
|-----|------------|
| Slow parsing | SQLite is hot path; YAML only on dump/init |
| Indentation errors | Pydantic validation on load |
| Parser variations | Use `ruamel.yaml` exclusively |
| No native schema | Pydantic models as schema |

---

## Context Consolidation Strategy (Task 003)

### Recommendation: Hierarchical by Scope (aligned with Directory Structure)

### Current Context Statistics
- 77 context directories
- 248 markdown files
- 31% audit files, 45% miscellaneous

### Context Naming Convention
```
<TYPE>_<TIMESTAMP>Z_<DETAIL>.md
```
Example: `AUDIT_2025-11-30T1420Z_SCHEMA_REVIEW.md`

---

## Key Design Decisions Summary

| Decision | Recommendation | Impact |
|----------|---------------|--------|
| **Directory Structure** | Hybrid (Option D) | 98% directory reduction |
| **File Format** | YAML for tickets/artifacts | Maintained readability |
| **Activity Log** | Time-bucketed JSONL | `activity_log/YYYY-MM.jsonl` |
| **Artifacts** | First-class YAML files | `artifacts/<ulid>.yaml` |
| **Context Naming** | UTC timestamps | Timezone-unambiguous |

---

## Design Principle

**SQLite is derived state; Git is source of truth.**

The entire SQLite database must be rebuildable from the git repo via `db rebuild`.
