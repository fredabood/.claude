# Roadmap System

**Version:** 2.1 (Gate Model)
**Status:** Sprint 1 Complete (Core Data Model & YAML Schema)

## Overview

The Roadmap System is a comprehensive project management framework for Vibey projects. It provides:

- **4-tier hierarchy:** Roadmap → Track → Sprint → Task
- **Three-tier gate system:** Development gates, Completion gates, Production gates
- **Automatic versioning:** Semantic versioning tied to roadmap progress
- **Dependency tracking:** Complex dependency graphs with blocker detection
- **Activity logging:** Unified activity log at roadmap level
- **Quality gates:** Automated quality validation before completion/production

## Directory Structure

```
framework/roadmap/
├── schema/                    # YAML schemas for all objects
│   ├── roadmap.schema.yaml
│   ├── track.schema.yaml
│   ├── sprint.schema.yaml
│   └── task.schema.yaml
├── models/                    # Python dataclasses
│   ├── __init__.py
│   ├── common.py             # Enums and common types
│   ├── roadmap.py            # Roadmap model
│   ├── track.py              # Track model
│   ├── sprint.py             # Sprint model
│   └── task.py               # Task model
├── validation/                # YAML validation
│   ├── __init__.py
│   └── validator.py          # Validation logic
├── serialization/             # YAML I/O
│   ├── __init__.py
│   ├── yaml_loader.py        # Load YAML → Python objects
│   └── yaml_dumper.py        # Save Python objects → YAML
├── examples/                  # Example roadmaps
│   └── sample-roadmap/       # Complete example project
│       ├── roadmap.yaml
│       ├── tracks/
│       ├── sprints/
│       └── tasks/
└── README.md                  # This file
```

## Quick Start

### Load a Roadmap

```python
from framework.roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks

# Load roadmap
roadmap = load_roadmap('.vibey/roadmap.yaml')
print(f"Roadmap: {roadmap.name} (v{roadmap.version})")
print(f"Progress: {roadmap.progress.completion_percent}%")

# Load track
track = load_track('.vibey/tracks/backend.yaml')
print(f"Track: {track.name} ({track.status.value})")

# Load sprint
sprint = load_sprint('.vibey/sprints/backend-1.yaml')
print(f"Sprint: {sprint.name} - {sprint.progress.tasks_completed}/{sprint.progress.tasks_total} tasks")

# Load tasks
tasks = load_tasks('.vibey/tasks/backend-1-tasks.yaml')
print(f"Loaded {len(tasks)} tasks")
```

### Validate a Roadmap

```python
from framework.roadmap.validation import validate_roadmap, validate_track

# Validate roadmap
result = validate_roadmap('.vibey/roadmap.yaml')
if result.valid:
    print("✅ Roadmap is valid")
else:
    print(f"❌ Validation failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Save a Roadmap

```python
from framework.roadmap.serialization import save_roadmap, save_track
from framework.roadmap.models import Roadmap, Status
from datetime import datetime

# Modify and save
roadmap.add_activity(
    ActivityType.TASK_COMPLETED,
    "Completed task backend-1-task-003",
    {"task_id": "backend-1-task-003"}
)

save_roadmap(roadmap, '.vibey/roadmap.yaml')
```

## Object Hierarchy

### Roadmap
- Top-level container
- Unified activity log
- Version management
- Track summaries
- Global dependencies

**File:** `.vibey/roadmap.yaml`

### Track
- Parallelization boundary
- Contains related sprints
- Track-scoped sprint IDs (e.g., `backend-1`, `frontend-2`)
- Track-level quality gates

**Files:** `.vibey/tracks/{track-id}.yaml`

### Sprint
- **Logical unit of work pushable to production**
- Contains development tasks + quality gate tasks
- Has completion_gate_check and production_gate_check statuses
- Can reach production_ready and deployed statuses

**Files:** `.vibey/sprints/{sprint-id}.yaml`

### Task
- **Context-window sized work unit**
- Three types:
  - **Development tasks:** Build functionality, can serve as dev gates for external sprints
  - **Completion gate tasks:** Hygiene checks (docs, CI/CD), highly isolated
  - **Production gate tasks:** Production readiness (security, testing), highly isolated
- No production statuses (tasks are not production units)

**Files:** `.vibey/tasks/{sprint-id}-tasks.yaml`

## Gate System

### Development Gates
External dependencies (development tasks or sprints) that must complete before current sprint can progress.

**Key Principle:** Only development tasks can serve as development gates. Quality gate tasks cannot.

### Completion Gates
Hygiene checks that must pass before sprint can be "completed":
- Documentation review
- Git/CI/CD hygiene
- Code quality checks

### Production Gates
Production readiness checks that must pass before sprint can be "production_ready":
- Security audits
- Test coverage
- Performance benchmarks

## Status System

### Sprint/Track Statuses (Full Set)
```
not_started → in_progress → completion_gate_check → completed →
                                                         ↓
                             production_gate_check → production_ready → deployed
```

### Task Statuses (Restricted Set)
```
not_started → in_progress → completion_gate_check → completed
```

**Note:** Tasks cannot be `production_ready` or `deployed` - these are sprint-level statuses.

## Validation

All objects are validated against:
1. **Schema rules:** Required fields, types, formats
2. **Business rules:** Date ordering, progress consistency, ID scoping
3. **Relationship rules:** Dependencies, blockers, task types

## Example Project

See `examples/sample-roadmap/` for a complete working example showing:
- Multi-track structure (backend, frontend)
- Sprint planning with tasks
- Quality gates (completion and production)
- Dependency tracking
- Activity logging
- Progress tracking

## Implementation Status

**Sprint 1: Core Data Model & YAML Schema (COMPLETE)**
- ✅ 4 YAML schemas designed
- ✅ Python data models implemented (dataclasses)
- ✅ Validation logic complete
- ✅ Serialization/deserialization complete
- ✅ Example roadmap created
- ⏳ Unit tests pending

**Next:** Sprint 2 - State Management Scripts

## References

- [Design Document](../../docs/development/ROADMAP_OBJECT_HIERARCHY.md)
- [Implementation Plan](../../docs/development/ROADMAP_IMPLEMENTATION_PLAN.md)
- [Framework Roadmap](../../docs/FRAMEWORK_ROADMAP.md)
