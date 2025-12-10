# Flat Directory Structure Specification

**Version:** 2.0
**Date:** 2025-12-09
**Status:** Design Specification
**Track:** unified-architecture-migration
**Sprint:** unified-arch-1
**Task:** unified-arch-1-task-001

---

## Executive Summary

This document specifies the exact directory structure and file naming conventions for the unified ticket architecture's flat organization. The migration will reduce directories from **1,300+ to ~30** (98% reduction) and simplify navigation from **10+ levels to 4 levels maximum**.

---

## Design Decisions

### 1. File Naming Convention

**Decision:** Use **ULID-based** file names with `.id` mapping files for human-readable slugs.

**Format:**
```
{ulid}.yaml        # Actual file
.id                # Mapping file (slug ↔ ULID)
```

**Rationale:**
- ULIDs provide immutable identity across renames
- `.id` files enable slug-based lookups for backward compatibility
- Git history tracks files by ULID (stable across renames)
- Avoids name conflicts and simplifies uniqueness guarantees

**Example:**
```
tracks/01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml
tracks/.id  # Contains: sqlite-backend → 01JB3QVDZ8TRK9XN1FJFHGWPRM
```

---

### 2. Directory Structure

**End-State Structure:**
```
.vibey/
├── roadmap.db                          # SQLite database (derived state)
└── roadmap/
    ├── roadmap.yaml                    # RoadmapTicket (1 file)
    │
    ├── tracks/                         # FLAT - all TrackTicket files
    │   ├── .id                         # slug ↔ ULID mapping
    │   ├── 01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml
    │   ├── 01JB3QVDZ9URP8YN2GKGIYHQSN.yaml
    │   └── ...                         # ~36 track files
    │
    ├── sprints/                        # FLAT - all SprintTicket files
    │   ├── .id                         # slug ↔ ULID mapping
    │   ├── 01JB3QVE2CVSL0ZO3HMHJZIRTO.yaml
    │   ├── 01JB3QVE3DWUM1AP4INJKAZLUP.yaml
    │   └── ...                         # ~180 sprint files
    │
    ├── tasks/                          # FLAT - all TaskTicket files
    │   ├── .id                         # slug ↔ ULID mapping
    │   ├── 01JB3QVE5NEXVW2BR5KOLBCNWQ.yaml
    │   ├── 01JB3QVE6OFYWX3CS6LPMCDOXR.yaml
    │   └── ...                         # ~945 task files
    │
    ├── artifacts/                      # First-class artifact definitions
    │   ├── .id                         # slug ↔ ULID mapping
    │   ├── 01JB3QVGMNEFGH4IJ6KLMNOPQR.yaml
    │   └── ...                         # ~500+ artifact files
    │
    ├── activity_log/                   # Time-bucketed JSONL logs
    │   ├── 2025-11.jsonl
    │   ├── 2025-12.jsonl
    │   └── ...
    │
    └── context/                        # Human/AI documentation
        ├── tracks/
        │   ├── sqlite-backend/         # Track-specific context (by slug)
        │   │   ├── AUDIT_2025-11-30T1420Z_SCHEMA_REVIEW.md
        │   │   └── IMPLEMENTATION_AUDIT_2025-12-07.md
        │   └── ...
        │
        ├── sprints/
        │   ├── sqlite-backend-6/       # Sprint-specific context (by slug)
        │   │   ├── GAP_ANALYSIS.md
        │   │   └── architecture/       # Sprint-specific subdirectories allowed
        │   │       ├── 00-INDEX.md
        │   │       ├── 01-DESIGN-PRINCIPLES.md
        │   │       └── ...
        │   └── ...
        │
        └── tasks/
            ├── sqlite-backend-6-task-001/  # Task-specific context (by slug)
            │   └── IMPLEMENTATION_NOTES.md
            └── ...
```

---

### 3. Metrics Comparison

| Metric | Current (v1) | End-State (v2) | Improvement |
|--------|--------------|----------------|-------------|
| **Max Depth** | 10 levels | 4 levels | **60% reduction** |
| **Total Directories** | 1,347 | ~30 | **98% reduction** |
| **Context Directories** | 77 scattered | 3 top-level | **Consolidated** |
| **File Lookup** | Nested walk | Flat iteration | **O(n) → O(1)** |
| **Git Operations** | Slow (deep trees) | Fast (flat lists) | **~10x faster** |

---

### 4. Context File Organization

**Principle:** Context files use **slug-based** subdirectories for human readability, while ticket/artifact files use **ULID-based** names.

**Structure:**
```
context/
├── tracks/{track-slug}/
├── sprints/{sprint-slug}/
└── tasks/{task-slug}/
```

**Naming Convention:**
```
<TYPE>_<TIMESTAMP>Z_<DETAIL>.md
```

**Examples:**
- `AUDIT_2025-11-30T1420Z_SCHEMA_REVIEW.md`
- `DESIGN_2025-12-07T0900Z_DIRECTORY_STRUCTURE.md`
- `IMPLEMENTATION_AUDIT_2025-12-07.md` (legacy, no timestamp)

**Types:**
- `AUDIT` - Audit reports
- `DESIGN` - Design documents
- `IMPLEMENTATION` - Implementation notes
- `ANALYSIS` - Analysis documents
- `GAP_ANALYSIS` - Gap identification
- `REFERENCE` - Reference documentation

---

### 5. Artifact File Organization

**Structure:**
```
artifacts/
├── .id                                 # slug ↔ ULID mapping
├── 01JB3QVGMNEFGH4IJ6KLMNOPQR.yaml    # Artifact definition
└── ...
```

**Artifact YAML Format:**
```yaml
artifact:
  id: 01JB3QVGMNEFGH4IJ6KLMNOPQR
  name: "SQLite Backend Schema"
  slug: sqlite-backend-schema          # For .id mapping
  paths:
    - vibey/roadmap/database/schema.py
  content_hash: sha256:abc123...
  artifact_type: code
  artifact_subtype: module
  provenance: ticket_created
  documents_artifact_id: null
  status: completed
  criteria: []
```

---

### 6. Activity Log Organization

**Structure:**
```
activity_log/
├── 2025-11.jsonl    # November 2025 events
├── 2025-12.jsonl    # December 2025 events
└── ...
```

**Format:** JSONL (JSON Lines) - one event per line

**Benefits:**
- Append-friendly (concurrent writes safe)
- Time-bucketed (one file per month)
- Easy to parse and filter
- Git-friendly (line-based diffs)

**Example Entry:**
```json
{"timestamp": "2025-12-09T14:55:00Z", "event_type": "status_transition", "entity_id": "task_01JB3QVE5N", "from_status": "in_progress", "to_status": "completed", "actor": "claude-code", "context": {"criteria_met": true, "blockers": []}}
```

---

### 7. .id Mapping File Format

**Purpose:** Bidirectional slug ↔ ULID lookup

**Format:**
```
# Vibey Roadmap ID Mapping File
# Format: slug=ulid
# Generated: 2025-12-09T15:00:00Z

sqlite-backend=01JB3QVDZ8TRK9XN1FJFHGWPRM
roadmap-system=01JB3QVDZ9URP8YN2GKGIYHQSN
mcp-server=01JB3QVDZAMNWQZO4JOSKAZMUP
...
```

**Parser:**
- Read all lines
- Skip lines starting with `#`
- Split on `=` to get `slug` and `ulid`
- Build both `slug → ulid` and `ulid → slug` dictionaries

**Operations:**
- `get_ulid(slug: str) → str`
- `get_slug(ulid: str) → str`
- `register(slug: str, ulid: str)`
- `rename_slug(old_slug: str, new_slug: str)` - updates mapping only, file name unchanged

---

## Migration Path

### Current → Target Mapping

**Tracks:**
```
Current:  .vibey/roadmap/sqlite-backend/track.yaml
Target:   .vibey/roadmap/tracks/01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml
Mapping:  tracks/.id contains: sqlite-backend=01JB3QVDZ8TRK9XN1FJFHGWPRM
```

**Sprints:**
```
Current:  .vibey/roadmap/sqlite-backend/sqlite-backend-6/sprint.yaml
Target:   .vibey/roadmap/sprints/01JB3QVE2CVSL0ZO3HMHJZIRTO.yaml
Mapping:  sprints/.id contains: sqlite-backend-6=01JB3QVE2CVSL0ZO3HMHJZIRTO
```

**Tasks:**
```
Current:  .vibey/roadmap/sqlite-backend/sqlite-backend-6/sqlite-backend-6-task-001/task.yaml
Target:   .vibey/roadmap/tasks/01JB3QVE5NEXVW2BR5KOLBCNWQ.yaml
Mapping:  tasks/.id contains: sqlite-backend-6-task-001=01JB3QVE5NEXVW2BR5KOLBCNWQ
```

**Context:**
```
Current:  .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/02-CLASS-MODEL.md
Target:   .vibey/roadmap/context/sprints/sqlite-backend-6/architecture/02-CLASS-MODEL.md
Note:     Uses slug-based path for human readability
```

---

### Migration Algorithm

```python
def migrate_directory_structure():
    """Migrate nested structure to flat structure."""

    # Phase 1: Generate ULIDs for all entities
    for track_dir in find_tracks():
        track_yaml = load_yaml(track_dir / "track.yaml")
        ulid = generate_ulid()
        track_yaml["track"]["id"] = ulid
        track_yaml["track"]["slug"] = track_dir.name

        # Store mapping
        track_mappings[track_dir.name] = ulid

    # Phase 2: Create .id files
    write_id_file("tracks/.id", track_mappings)
    write_id_file("sprints/.id", sprint_mappings)
    write_id_file("tasks/.id", task_mappings)
    write_id_file("artifacts/.id", artifact_mappings)

    # Phase 3: Move files to flat structure
    for slug, ulid in track_mappings.items():
        source = f".vibey/roadmap/{slug}/track.yaml"
        target = f".vibey/roadmap/tracks/{ulid}.yaml"
        git_mv(source, target)

    # Phase 4: Move context files (preserve slug-based paths)
    for sprint_dir in find_sprint_context():
        slug = sprint_dir.parent.parent.name + "/" + sprint_dir.parent.name
        source = sprint_dir
        target = f".vibey/roadmap/context/sprints/{slug}/"
        git_mv(source, target)

    # Phase 5: Update all parent_ref fields to use ULIDs
    for file in all_yaml_files():
        update_parent_refs_to_ulid(file)

    # Phase 6: Cleanup old directory structure
    for track_dir in old_track_dirs():
        if track_dir.is_empty():
            rmdir(track_dir)
```

---

## Backward Compatibility

### Slug-Based Lookups

**Supported:** CLI commands can accept either slug or ULID

```bash
# Both work:
vibey roadmap query task sqlite-backend-6-task-001
vibey roadmap query task 01JB3QVE5NEXVW2BR5KOLBCNWQ
```

**Implementation:**
```python
def resolve_id(entity_type: str, id_or_slug: str) -> str:
    """Resolve slug or ULID to ULID."""
    # If already ULID, return as-is
    if is_ulid(id_or_slug):
        return id_or_slug

    # Lookup in .id file
    id_file = f".vibey/roadmap/{entity_type}s/.id"
    ulid = lookup_ulid(id_file, id_or_slug)

    if ulid is None:
        raise ValueError(f"{entity_type} not found: {id_or_slug}")

    return ulid
```

### Path Redirects

**Not Supported:** Old file paths will not redirect.

**Rationale:**
- Migration is one-time, not gradual
- All code updated atomically in Sprint 1
- No partial migration state

---

## Validation Criteria

### Structural Validation

- [ ] All tracks in `tracks/` directory (36 files)
- [ ] All sprints in `sprints/` directory (~180 files)
- [ ] All tasks in `tasks/` directory (~945 files)
- [ ] All artifacts in `artifacts/` directory (~500+ files)
- [ ] Context files organized by scope (tracks/, sprints/, tasks/)
- [ ] Activity log in time-bucketed JSONL format
- [ ] `.id` mapping files exist for tracks, sprints, tasks, artifacts
- [ ] Max directory depth is 4 levels
- [ ] Total directory count is ≤ 50

### Content Validation

- [ ] All YAML files have valid ULID in `id` field
- [ ] All YAML files have valid slug in `slug` field (where applicable)
- [ ] All `parent_ref` fields use ULIDs (not slugs)
- [ ] All `.id` files have valid `slug=ulid` format
- [ ] All context files follow `<TYPE>_<TIMESTAMP>Z_<DETAIL>.md` naming
- [ ] No duplicate ULIDs across any entity type
- [ ] No duplicate slugs within same entity type

### Round-Trip Validation

- [ ] Load all YAML files → no parse errors
- [ ] Resolve all parent_ref references → no broken links
- [ ] Lookup all slugs via `.id` files → all resolve
- [ ] Reverse lookup all ULIDs via `.id` files → all resolve
- [ ] Database rebuild from YAML → matches pre-migration state
- [ ] All context files accessible via slug-based paths

---

## Rollback Plan

### Backup Strategy

Before migration:
1. Create full backup of `.vibey/roadmap/` directory
2. Create git tag `pre-flat-structure-migration`
3. Create database dump `roadmap-pre-migration.db`

### Rollback Procedure

```bash
# Option 1: Git reset (if migration committed)
git reset --hard pre-flat-structure-migration

# Option 2: Restore from backup (if migration not committed)
rm -rf .vibey/roadmap/
cp -r .vibey/roadmap-backup/ .vibey/roadmap/

# Option 3: Database rollback
cp roadmap-pre-migration.db .vibey/roadmap.db
vibey roadmap db dump  # Regenerate YAML from DB
```

---

## Implementation Notes

### Performance Considerations

- **File I/O:** Flat structure reduces directory traversal from O(d^n) to O(n)
- **Git Operations:** Significantly faster (10x) for status, diff, log
- **Slug Lookup:** Add in-memory LRU cache for `.id` file parsing
- **Parallel Processing:** Can process tracks, sprints, tasks in parallel (no dependencies)

### Migration Time Estimate

- **ULID Generation:** ~1 second (1,161 entities)
- **File Moves:** ~5-10 minutes (git mv for 1,161 files + context)
- **YAML Updates:** ~2-3 minutes (update parent_ref fields)
- **Validation:** ~1 minute (load all YAML, check references)
- **Total:** ~10-15 minutes

---

## References

- **Original Design:** `.vibey/roadmap/sqlite-backend/sqlite-backend-6/context/architecture/09-DESIGN-DECISIONS.md`
- **ULID Spec:** https://github.com/ulid/spec
- **YAML Spec:** https://yaml.org/spec/1.2.2/
- **Git mv:** https://git-scm.com/docs/git-mv

---

**Status:** Design Complete
**Next Task:** unified-arch-1-task-002 (Create directory migration script)
