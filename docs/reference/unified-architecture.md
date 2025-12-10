# Unified Architecture Reference

This document describes the unified ticket architecture implemented in Sprint 5 of the unified-architecture-migration track.

## Overview

The unified architecture provides:
1. **Pydantic-based ticket models** - Immutable, type-safe data models
2. **Criteria-based blocking** - Centralized transition validation
3. **Artifact management** - First-class file tracking entities
4. **Unified transitions** - Single source of truth for status changes

## Core Concepts

### Ticket Model Hierarchy

```
RoadmapTicket
    └── TrackTicket[]
            └── SprintTicket[]
                    └── TaskTicket[]
```

Each ticket type inherits from `HierarchicalTicket` and supports:
- Status tracking with lifecycle methods (`start()`, `complete()`)
- Criteria-based transition validation (`can_transition_to()`)
- Parent/child relationships via `parent_ref` and `child_ids`
- Activity logging

### Ticket Status Lifecycle

```
NOT_STARTED → IN_PROGRESS → COMPLETED
                    ↓
               BLOCKED/DEFERRED
```

Status transitions are validated through:
1. `can_transition_to(target_status)` - Check if transition is allowed
2. `start()` / `complete()` - Apply transition (immutable - returns new instance)

### Criteria System

Criteria define conditions that must be met before transitions:

```yaml
criteria:
  - id: dep-001
    description: "Dependency task must complete"
    required: true
    blocks_transition_to: in_progress
    target:
      type: completable
      completable_id: other-task-001
      required_status: completed
```

Target types:
- `completable` - Reference to another ticket
- `file_exists` - File/directory must exist
- `artifact` - Artifact must meet verification requirements

## Module Reference

### vibey.operations.roadmap.transitions

Centralized status transition logic.

```python
from vibey.operations.roadmap.transitions import (
    TransitionBlockedError,
    transition_task,
    transition_sprint,
    transition_track,
    transition_roadmap,
    can_transition,
)

# Transition a task
try:
    updated_task = transition_task(task_id, TicketStatus.COMPLETED, root_dir)
except TransitionBlockedError as e:
    print(f"Blocked: {e.reasons}")

# Check if transition is possible (read-only)
can, reasons = can_transition(task_id, 'task', TicketStatus.COMPLETED, root_dir)
```

### vibey.operations.roadmap.artifacts

Artifact management operations.

```python
from vibey.operations.roadmap.artifacts import (
    list_artifacts,
    show_artifact,
    adopt_artifact,
    orphan_artifacts,
    stale_artifacts,
    impact_analysis,
)

# List all artifacts
artifacts = list_artifacts(root_dir)

# Adopt a file as artifact
artifact = adopt_artifact("docs/README.md", ArtifactType.DOCUMENTATION, root_dir)

# Find orphan artifacts
orphans = orphan_artifacts(root_dir)

# Impact analysis
affected = impact_analysis(["src/api.py"], root_dir)
```

### vibey.operations.roadmap.query

Query operations for loading tickets.

```python
from vibey.operations.roadmap.query import (
    load_task_ticket,
    load_sprint_ticket,
    load_track_ticket,
    load_roadmap_ticket,
)

# Load entities as ticket models
task = load_task_ticket(root_dir, "unified-arch-5-task-001")
sprint = load_sprint_ticket(root_dir, "unified-arch-5")
```

### vibey.operations.roadmap.update

Update operations with ticket-based transitions.

```python
from vibey.operations.roadmap.update import (
    complete_task,
    start_task,
    start_sprint,
    complete_sprint,
    complete_track,
)

# Complete a task (validates criteria first)
exit_code = complete_task(root_dir, "unified-arch-5-task-001")
```

## CLI Commands

### Artifact Management

```bash
# List all artifacts
vibey artifact list

# Show artifact details
vibey artifact show <artifact_id>

# Register file as artifact
vibey artifact adopt <path> --type documentation

# Find orphan artifacts
vibey artifact orphans

# Check for stale documentation
vibey artifact stale

# Impact analysis
vibey artifact impact src/api.py src/models.py
```

### Roadmap Operations

```bash
# Show status with criteria progress
vibey roadmap status

# Show task/sprint/track details
vibey roadmap show <id>

# Start/complete with criteria validation
vibey roadmap start <id>
vibey roadmap complete <id>
```

## YAML Format (v2)

The v2 YAML format uses a unified `criteria` array instead of separate `blocked_by` and `depends_on` fields:

```yaml
task:
  id: unified-arch-5-task-001
  name: "Migrate query operations"
  status: completed
  ticket_type: task
  parent_ref: unified-arch-5

  # Unified criteria array (v2)
  criteria:
    - id: dep-001
      description: "Sprint 4 must complete"
      required: true
      blocks_transition_to: in_progress
      target:
        type: completable
        completable_id: unified-arch-4
        required_status: completed
      is_met: true
      last_checked: '2025-12-10T02:05:00+00:00'

    - id: del-001
      description: "Implementation file exists"
      required: true
      blocks_transition_to: completed
      target:
        type: file_exists
        paths:
          - vibey/operations/roadmap/query.py
        all_required: true
        deliverable_type: code
```

## Key Principles

### Immutability

Ticket models use immutable patterns:
```python
# start() returns a NEW instance
started_task = task.start()

# Original task unchanged
assert task.status == TicketStatus.NOT_STARTED
assert started_task.status == TicketStatus.IN_PROGRESS
```

### Single Source of Truth

All transitions go through `transitions.py`:
```python
# DON'T modify status directly
task.status = TicketStatus.COMPLETED  # Wrong!

# DO use transition functions
updated = transition_task(task_id, TicketStatus.COMPLETED, root_dir)
```

### Criteria-Based Validation

Always use `can_transition_to()` before transitions:
```python
can, reasons = task.can_transition_to(TicketStatus.COMPLETED)
if not can:
    print(f"Blocked: {reasons}")
```

## Migration from v1

### Key Changes

1. **`blocked` field removed** - Now computed from criteria
2. **`blocked_by` → `criteria`** - Unified criteria array
3. **`depends_on` → `criteria`** - Dependencies are criteria
4. **`deliverables` → `criteria`** - File existence as criteria

### Backward Compatibility

The yaml_loader handles both formats:
```python
# v1: blocked was explicit
blocked = roadmap_data['blocked']

# v2: blocked computed from criteria
blocked = roadmap_data.get('blocked', False)
```

## Architecture Decisions

### Why Pydantic?

1. **Type safety** - Catch errors at parse time
2. **Validation** - Built-in field validation
3. **Immutability** - `frozen=True` by default
4. **Serialization** - Easy JSON/dict conversion

### Why Centralized Transitions?

1. **Single source of truth** - One place for transition logic
2. **Consistent validation** - All transitions validated equally
3. **Easier testing** - Mock one module, not many
4. **Audit trail** - Centralized logging

### Why Criteria-Based Blocking?

1. **Explicit dependencies** - All blockers visible in YAML
2. **Computable status** - `blocked` derived from criteria
3. **Extensible** - New criteria types without code changes
4. **Self-documenting** - YAML describes what blocks what
