# V2 YAML Schema Specification

**Date:** 2025-12-10
**Sprint:** unified-arch-4 (v2 YAML Format Migration)
**Task:** unified-arch-4-task-001
**Status:** Final Design

---

## Overview

This document defines the **v2 YAML format** for roadmap entities. The v2 format introduces:

1. **ULID-only identifiers** - IDs are immutable ULIDs, slugs are separate
2. **Unified criteria** - Replaces blocked_by, depends_on, deliverables
3. **Computed blocked field** - No longer stored (derived from criteria)
4. **Polymorphic targets** - Different criterion types with specific schemas

---

## V2 Format Summary

| Entity | Root Key | Required Fields |
|--------|----------|-----------------|
| Roadmap | `roadmap` | id, name, version, status |
| Track | `track` | id, name, roadmap_id, status, slug, parent_ref |
| Sprint | `sprint` | id, name, track_id, status, slug, parent_ref |
| Task | `task` | id, title, sprint_id, status, slug, parent_ref |

---

## V1 vs V2 Format Comparison

### V1 Format (Current)

```yaml
task:
  id: 01KC2D0JK06MN77ZHAGAHF5VKD
  sprint_id: aider-port-1
  track_id: aider-port
  roadmap_id: vibey-framework-v2
  title: Create AiderAdapter class
  status: completed
  blocked: false                    # Stored (v1)
  blocked_by:                       # Separate array (v1)
    - target_id: aider-port-1-task-001
      reason: Must complete first
  depends_on:                       # Separate array (v1)
    - blocker_id: aider-port-1-task-002
      required_status: completed
  deliverables:                     # Separate array (v1)
    - path: vibey/adapters/aider.py
      type: code
  slug: aider-port-1-task-001
  parent_ref: 01KC2D0JK06MN77ZHAGAHF5VKC
```

### V2 Format (Target)

```yaml
task:
  id: 01KC2D0JK06MN77ZHAGAHF5VKD
  slug: aider-port-1-task-001
  sequence: 1                       # Ordering within parent
  parent_ref: 01KC2D0JK06MN77ZHAGAHF5VKC
  title: Create AiderAdapter class
  status: completed
  # blocked: <removed - computed from criteria>
  criteria:                         # Unified criteria array (v2)
    - id: dep-task-002
      description: Must complete prerequisite task first
      required: true
      blocks_transition_to: in_progress
      target:
        type: completable
        completable_id: 01KC2D0JK06MN77ZHAGAHF5VKE
        required_status: completed
    - id: del-adapter-py
      description: Adapter implementation must exist
      required: true
      blocks_transition_to: completed
      target:
        type: file_exists
        paths:
          - vibey/adapters/aider.py
        deliverable_type: code
```

---

## V2 Schema: Roadmap

```yaml
roadmap:
  # Identity (required)
  id: <ULID>                        # Immutable identifier
  name: <string>                    # Human-readable name
  version: <string>                 # Semantic version (e.g., "1.0.0")

  # State (required)
  status: <enum>                    # not_started|in_progress|completed|on_hold|cancelled

  # Timestamps (auto-managed)
  created: <ISO8601>
  started: <ISO8601 | null>
  completed: <ISO8601 | null>

  # Children (summary only - actual data in tracks/)
  tracks:
    - id: <ULID>
      name: <string>
      slug: <string>
      status: <enum>

  # Unified criteria
  criteria:
    - id: <string>
      description: <string>
      required: <boolean>           # true = blocking, false = warning
      blocks_transition_to: <enum>  # in_progress|completed|production_ready|deployed
      target: <TargetSchema>        # Polymorphic target

  # Standards (now as criteria templates)
  requirements_local: []
  requirements_inherited: []

  # Metadata
  metadata:
    created_by: <string>
    last_updated: <ISO8601 | null>
```

---

## V2 Schema: Track

```yaml
track:
  # Identity (required)
  id: <ULID>
  slug: <string>                    # Human-readable path segment
  parent_ref: <ULID>                # Roadmap ULID
  name: <string>
  roadmap_id: <string>              # Retained for backward compatibility queries

  # State (required)
  status: <enum>                    # not_started|in_progress|completed|on_hold|cancelled
  priority: <enum>                  # critical|high|medium|low

  # Timestamps
  created: <ISO8601>
  started: <ISO8601 | null>
  completed: <ISO8601 | null>
  estimated_duration: <string | null>

  # Progress (computed, may be cached)
  progress:
    sprints_total: <int>
    sprints_completed: <int>
    tasks_total: <int>
    tasks_completed: <int>
    completion_percent: <int>

  # Children (summary only)
  sprints:
    - id: <ULID>
      name: <string>
      slug: <string>
      status: <enum>
      sequence: <int>               # Order within track

  # Unified criteria
  criteria:
    - id: <string>
      description: <string>
      required: <boolean>
      blocks_transition_to: <enum>
      target: <TargetSchema>

  # Legacy arrays (v2 migration: convert to criteria)
  # blocked_by: []                  # REMOVED - use criteria
  # depends_on: []                  # REMOVED - use criteria
  # deliverables: []                # REMOVED - use criteria

  # Retained fields
  strategic_value: []
  assigned_agents: []
  commits: []
  standards: []

  # Metadata
  metadata:
    created_by: <string>
    design_doc: <path | null>
    notes: <string | null>
```

---

## V2 Schema: Sprint

```yaml
sprint:
  # Identity (required)
  id: <ULID>
  slug: <string>
  sequence: <int>                   # Order within track (1, 2, 3...)
  parent_ref: <ULID>                # Track ULID
  track_id: <string>                # Retained for compatibility
  roadmap_id: <string>
  name: <string>

  # Content
  description: <string | null>
  goal: <string | null>
  success_criteria: []              # Human-readable goals

  # State
  status: <enum>

  # Timestamps
  created: <ISO8601>
  started: <ISO8601 | null>
  completed: <ISO8601 | null>

  # Children (summary only)
  tasks:
    - id: <ULID>
      title: <string>
      slug: <string>
      status: <enum>
      sequence: <int>

  # Unified criteria
  criteria:
    - id: <string>
      description: <string>
      required: <boolean>
      blocks_transition_to: <enum>
      target: <TargetSchema>

  # Legacy arrays (v2 migration: convert to criteria)
  # blocked_by: []                  # REMOVED
  # depends_on: []                  # REMOVED
  # deliverables: []                # REMOVED
  # development_gates: []           # REMOVED

  # Retained
  risks: []

  # Metadata
  metadata:
    design_reference: <path | null>
```

---

## V2 Schema: Task

```yaml
task:
  # Identity (required)
  id: <ULID>
  slug: <string>
  sequence: <int>                   # Order within sprint
  parent_ref: <ULID>                # Sprint ULID
  sprint_id: <string>               # Retained for compatibility
  track_id: <string>
  roadmap_id: <string>

  # Content
  title: <string>
  description: <string | null>
  task_type: <enum>                 # development|documentation|research|review|testing

  # State
  status: <enum>                    # not_started|in_progress|completed|blocked|deferred

  # Timestamps
  created: <ISO8601>
  started: <ISO8601 | null>
  completed: <ISO8601 | null>

  # Estimation
  priority: <enum>
  complexity: <enum>                # simple|medium|complex
  estimated_tokens: <int>
  actual_tokens: <int | null>

  # Assignment
  assigned_agent: <string | null>

  # Unified criteria
  criteria:
    - id: <string>
      description: <string>
      required: <boolean>
      blocks_transition_to: <enum>
      target: <TargetSchema>

  # Legacy arrays (v2 migration: convert to criteria)
  # blocked_by: []                  # REMOVED
  # depends_on: []                  # REMOVED
  # deliverables: []                # REMOVED

  # Retained
  commits: []
  audit_results: <object | null>

  # Metadata
  metadata:
    last_updated: <ISO8601 | null>
    token_efficiency: <float | null>
    duration_hours: <float | null>
```

---

## Criterion Target Schemas

### CompletableTarget (Dependencies)

```yaml
target:
  type: completable
  completable_id: <ULID>            # What we depend on
  required_status: completed        # Status it must reach
  cascade_deferred: false           # Waive if target is deferred?
```

### FileExistsTarget (Deliverables)

```yaml
target:
  type: file_exists
  paths:
    - path/to/file.py
    - path/to/another.py
  all_required: true                # All must exist (true) or any (false)
  deliverable_type: code            # code|docs|test|config
```

### TestPassesTarget (Quality Gates)

```yaml
target:
  type: test_passes
  test_command: pytest tests/unit/
  pass_threshold: 100               # Percentage
  timeout_seconds: 300
```

### ThresholdTarget (Metrics)

```yaml
target:
  type: threshold
  metric_name: bundle_size_kb
  threshold: 500
  comparison: less_than             # less_than|greater_than|equals
  evaluation_command: du -sk dist/
```

### ManualTarget (Human Verification)

```yaml
target:
  type: manual
  assessor: product-owner
  instructions: Review and approve the design
  assessed: false
  met: false
```

---

## Migration Field Mapping

### Fields Removed (Computed from Criteria)

| V1 Field | V2 Replacement |
|----------|----------------|
| `blocked` | Computed: any unmet required criteria |
| `blocked_by[]` | `criteria[]` with `type: completable` |
| `depends_on[]` | `criteria[]` with `type: completable` |
| `deliverables[]` | `criteria[]` with `type: file_exists` |
| `development_gates[]` | `criteria[]` with `type: test_passes` |
| `quality_gates[]` | `criteria[]` with `type: test_passes` |
| `blocks[]` | Computed via reverse lookup |
| `depended_on_by[]` | Computed via reverse lookup |

### Fields Renamed

| V1 Field | V2 Field |
|----------|----------|
| `track.sprints[].tasks_count` | Computed from tasks[] length |
| `dependencies` | Merged into `criteria` |

### Fields Added

| V2 Field | Purpose |
|----------|---------|
| `sequence` | Ordering within parent |
| `criteria[]` | Unified requirements |
| `criteria[].target` | Polymorphic target |

---

## V2 Detection

A YAML file is v2 format if:

1. Has `criteria` array at entity level, OR
2. Does NOT have `blocked_by` OR `depends_on` OR `deliverables` arrays

```python
def is_v2_format(data: dict) -> bool:
    """Detect if YAML uses v2 format."""
    entity = next(iter(data.values()))  # roadmap|track|sprint|task

    # V2 indicator: has criteria
    if 'criteria' in entity:
        return True

    # V1 indicator: has legacy arrays
    v1_fields = {'blocked_by', 'depends_on', 'deliverables', 'development_gates'}
    if any(f in entity for f in v1_fields):
        return False

    # Ambiguous (no dependencies) - treat as v2
    return True
```

---

## Validation Rules

### Required for All Entities

1. `id` must be valid ULID (26 uppercase alphanumeric chars)
2. `slug` must be non-empty string
3. `status` must be valid enum value
4. `parent_ref` must be valid ULID (except roadmap)

### Criteria Validation

1. Each criterion must have unique `id` within entity
2. `target.type` must be valid enum
3. `target` schema must match `target.type`
4. `blocks_transition_to` must be valid status enum

### Cross-Reference Validation

1. `criteria[].target.completable_id` must reference existing ULID
2. `parent_ref` must reference existing parent entity
3. Circular dependencies not allowed

---

## Implementation Notes

### Backward Compatibility

- V1 files can still be loaded (converted in memory)
- `track_id`, `sprint_id`, `roadmap_id` retained for queries
- Migration script converts v1 → v2 format

### File Naming

- Files named by ULID: `01KC2D0JK06MN77ZHAGAHF5VKD.yaml`
- `.id` mapping files: slug ↔ ULID lookup

### Storage Location

```
.vibey/roadmap/
├── roadmap.yaml              # Single roadmap file
├── tracks/
│   ├── .id                   # slug ↔ ULID mappings
│   └── 01KC2D0JK....yaml     # Track files
├── sprints/
│   ├── .id
│   └── 01KC2D0JK....yaml     # Sprint files
└── tasks/
    ├── .id
    └── 01KC2D0JK....yaml     # Task files
```

---

## Next Steps

1. **Task 002:** Create v1 to v2 migration script
2. **Task 003:** Update yaml_loader for v2 format only
3. **Task 004:** Update yaml_dumper for v2 format only
4. **Task 005:** Execute migration on all YAML files

---

**Design Status:** Complete
**Approved:** 2025-12-10
