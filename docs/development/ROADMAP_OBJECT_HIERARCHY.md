# Roadmap Object Hierarchy Design

**Version:** 1.0
**Date:** 2025-11-06
**Status:** Design Proposal
**Author:** Vibey Framework Team

---

## Executive Summary

This document defines a comprehensive roadmap object hierarchy for the Vibey Agent Framework that enables structured project management from the highest level (Roadmap) down to the smallest unit of work (Task). The hierarchy introduces **Tracks** as parallel execution groups and a robust **dependency/blocker system** that allows fine-grained control over what needs to be completed before work can progress.

**Key Features:**
- 4-tier hierarchy: Roadmap → Track → Sprint → Task
- Unified status system with 7 states across all levels
- Explicit dependency and blocker management
- Version management tied to roadmap progress
- Backward compatible with existing sprint state system

---

## Table of Contents

1. [Object Hierarchy Overview](#object-hierarchy-overview)
2. [Roadmap Object](#roadmap-object)
3. [Track Object](#track-object)
4. [Sprint Object](#sprint-object)
5. [Task Object](#task-object)
6. [Status System](#status-system)
7. [Dependency & Blocker Model](#dependency--blocker-model)
8. [Versioning Strategy](#versioning-strategy)
9. [Developer Workflow](#developer-workflow)
10. [State Management & Persistence](#state-management--persistence)
11. [Implementation Considerations](#implementation-considerations)
12. [Trade-offs & Design Decisions](#trade-offs--design-decisions)
13. [Migration Path](#migration-path)

---

## Object Hierarchy Overview

```
┌─────────────────────────────────────────────────────────────┐
│                          ROADMAP                             │
│  Comprehensive view of entire project                        │
│  Version: 1.2.0                                              │
└─────────────────────────────────────────────────────────────┘
           │
           ├─────────────────┬─────────────────┬────────────
           │                 │                 │
┌──────────▼─────────┐ ┌────▼────────────┐ ┌──▼─────────────┐
│   TRACK: Backend   │ │ TRACK: Frontend │ │ TRACK: Infra   │
│   (Parallel Exec)  │ │ (Parallel Exec) │ │ (Parallel Exec)│
└──────────┬─────────┘ └────┬────────────┘ └──┬─────────────┘
           │                 │                 │
     ┌─────┴─────┐     ┌────┴────┐      ┌────┴────┐
     │           │     │         │      │         │
┌────▼────┐ ┌───▼─────▼──┐ ┌───▼─────▼──┐ ┌───▼────┐
│Sprint 1 │ │ Sprint 2   │ │ Sprint 3   │ │Sprint 4│
│ (Auth)  │ │ (Dashboard)│ │ (API Docs) │ │(Deploy)│
└────┬────┘ └───┬────────┘ └───┬────────┘ └───┬────┘
     │          │              │              │
  ┌──┴──┐    ┌──┴──┐       ┌──┴──┐        ┌──┴──┐
  │     │    │     │       │     │        │     │
┌─▼─┐ ┌─▼─┐ ┌▼──┐ ┌▼──┐  ┌▼──┐ ┌▼──┐   ┌▼──┐ ┌▼──┐
│T1 │ │T2 │ │T1 │ │T2 │  │T1 │ │T2 │   │T1 │ │T2 │
└───┘ └───┘ └───┘ └───┘  └───┘ └───┘   └───┘ └───┘
```

**Hierarchy Levels:**
1. **Roadmap**: Entire project scope (completed + planned)
2. **Track**: Parallel execution group of related sprints
3. **Sprint**: Group of highly related tasks
4. **Task**: Smallest unit of work (single context window)

---

## Roadmap Object

The **Roadmap** is the top-level object representing the complete project view.

### Structure

```yaml
roadmap:
  id: "vibey-framework-v1"
  name: "Vibey Framework Production Release"
  version: "1.2.0"
  status: "in_progress"
  blocked: false

  # Metadata
  created: "2025-01-15T10:00:00Z"
  started: "2025-01-20T09:00:00Z"
  target_completion: "2025-12-31T23:59:59Z"
  completed: null

  # Progress tracking
  tracks_total: 5
  tracks_completed: 2
  sprints_total: 18
  sprints_completed: 8
  tasks_total: 156
  tasks_completed: 89

  # Version history
  version_history:
    - version: "1.0.0"
      date: "2025-06-01T00:00:00Z"
      milestone: "Initial Production Release"
    - version: "1.1.0"
      date: "2025-09-15T00:00:00Z"
      milestone: "Multi-platform Support"
    - version: "1.2.0"
      date: "2025-11-01T00:00:00Z"
      milestone: "Advanced Orchestration"

  # Tracks
  tracks:
    - track_id: "track-core-framework"
    - track_id: "track-agent-development"
    - track_id: "track-workflow-system"
    - track_id: "track-platform-ports"
    - track_id: "track-documentation"

  # Dependencies (roadmap-level external dependencies)
  dependencies: []

  # Blockers
  blocked_by: []
```

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique identifier for the roadmap |
| `name` | string | Human-readable roadmap name |
| `version` | string | Current semantic version |
| `status` | enum | Current status (see Status System) |
| `blocked` | boolean | Is roadmap blocked by dependencies? |
| `tracks` | array | List of track IDs in this roadmap |
| `version_history` | array | History of version milestones |
| `dependencies` | array | External dependencies (e.g., third-party tools) |

### Responsibilities

- Track overall project progress
- Manage version numbering and milestones
- Coordinate track-level parallelization
- Maintain historical record of progress
- Surface critical blockers

---

## Track Object

A **Track** is a group of sprints that can be developed in parallel with other tracks.

### Structure

```yaml
track:
  id: "track-core-framework"
  name: "Core Framework Development"
  roadmap_id: "vibey-framework-v1"

  status: "in_progress"
  blocked: false

  # Metadata
  priority: "critical"        # critical, high, medium, low
  started: "2025-01-20T09:00:00Z"
  completed: null
  estimated_duration: "90 days"

  # Progress
  sprints_total: 4
  sprints_completed: 2
  tasks_total: 45
  tasks_completed: 28
  progress_percent: 62

  # Sprints in this track
  sprints:
    - sprint_id: "sprint-001"
    - sprint_id: "sprint-002"
    - sprint_id: "sprint-003"
    - sprint_id: "sprint-004"

  # Dependencies
  dependencies:
    - type: "track"
      target_id: "track-infrastructure"
      target_status: "production_ready"
      reason: "Requires deployment infrastructure"

  # What this track blocks
  blocks:
    - type: "track"
      target_id: "track-platform-ports"
      at_status: "completed"

  # Current blockers
  blocked_by:
    - dependency_id: "track-infrastructure"
      current_status: "in_progress"
      required_status: "production_ready"
      blocking_since: "2025-10-15T10:00:00Z"

  # Specialized agents assigned to this track
  assigned_agents:
    - "coordinator"
    - "architecture-reviewer"
    - "security-auditor"

  # Track-level quality gates
  quality_gates:
    - name: "Architecture Review"
      status: "passed"
      threshold: 90
      blocking: true
```

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique track identifier |
| `name` | string | Human-readable track name |
| `sprints` | array | Sprints belonging to this track |
| `dependencies` | array | What must complete before this track |
| `blocks` | array | What this track blocks |
| `blocked_by` | array | Current active blockers |
| `assigned_agents` | array | Specialized agents for this track |

### Responsibilities

- Group related sprints for parallel execution
- Manage track-level dependencies
- Track aggregate progress across sprints
- Enable parallelization opportunities
- Surface track-level blockers

### Parallelization Strategy

**Tracks can run in parallel when:**
- No direct dependencies between them
- No shared blocking resources
- Independent deliverables

**Example:**
```yaml
# These can run in parallel
Track A: Backend API Development
Track B: Frontend UI Development
Track C: Documentation Updates

# Track D must wait for Track A
Track D: Integration Testing (depends on Track A completion)
```

---

## Sprint Object

A **Sprint** is a group of highly related tasks. This is the existing concept, enhanced with dependency management.

### Structure (Enhanced)

```yaml
sprint:
  id: "sprint-001"
  number: 1
  name: "User Authentication System"
  track_id: "track-core-framework"

  status: "in_progress"
  blocked: false

  # Metadata (existing)
  started: "2025-01-20T09:00:00Z"
  paused: null
  completed: null
  plan_file: "docs/sprints/sprint-1-plan.md"

  # Progress (existing)
  phases: [...]  # Existing phase structure
  current_phase: {...}

  # NEW: Dependencies
  dependencies:
    - type: "sprint"
      target_id: "sprint-000"  # Infrastructure setup
      target_status: "completed"
      reason: "Requires database and auth scaffolding"

  # NEW: What this sprint blocks
  blocks:
    - type: "sprint"
      target_id: "sprint-002"
      at_status: "production_ready"

  # NEW: Current blockers
  blocked_by: []

  # Tasks (enhanced from phases)
  tasks:
    - task_id: "sprint-001-task-001"
    - task_id: "sprint-001-task-002"
    - task_id: "sprint-001-task-003"

  # Existing structures
  activity_log: [...]
  metadata: {...}
```

### Key Enhancements

1. **Track Association**: Each sprint belongs to exactly one track
2. **Dependencies**: Explicit dependencies on other sprints
3. **Blocking State**: Clear visibility into what's blocking the sprint
4. **Task References**: Flat task list in addition to phase structure

### Backward Compatibility

**Existing sprint state files remain valid.** New fields are additive:
- Old: Sprint with phases (nested tasks)
- New: Sprint with phases AND flat task list + dependencies

---

## Task Object

A **Task** is the smallest unit of work, designed to fit within a single model context window.

### Structure

```yaml
task:
  id: "sprint-001-task-001"
  sprint_id: "sprint-001"

  # Identification
  title: "Implement user registration endpoint"
  description: "Create POST /api/auth/register endpoint with email/password validation"

  # Status
  status: "in_progress"
  blocked: false

  # Metadata
  created: "2025-01-20T09:00:00Z"
  started: "2025-01-21T10:30:00Z"
  completed: null

  # Assignment
  assigned_agent: "web-developer"
  estimated_tokens: 8000
  actual_tokens: null

  # Context
  phase: 1  # Optional: which phase this belongs to
  priority: "high"

  # Dependencies
  dependencies:
    - type: "task"
      target_id: "sprint-001-task-000"  # Database schema task
      target_status: "completed"
      reason: "Need User table created first"

  # What this task blocks
  blocks:
    - type: "task"
      target_id: "sprint-001-task-002"  # Login endpoint
      at_status: "completed"

  # Current blockers
  blocked_by:
    - dependency_id: "sprint-001-task-000"
      current_status: "in_progress"
      required_status: "completed"
      blocking_since: "2025-01-21T10:30:00Z"

  # Deliverables
  deliverables:
    - type: "code"
      paths:
        - "src/api/auth/register.ts"
        - "src/api/auth/validation.ts"
    - type: "test"
      paths:
        - "tests/api/auth/register.test.ts"

  # Quality requirements (non-blocking for task completion)
  quality_requirements:
    - "Unit tests written"
    - "Type safety verified"
    - "Error handling implemented"

  # Git commits associated with this task
  commits:
    - sha: "a1b2c3d"
      message: "feat: add user registration endpoint"
      date: "2025-01-21T14:00:00Z"
```

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique task identifier |
| `title` | string | Short task description |
| `description` | string | Detailed task description |
| `status` | enum | Current status |
| `blocked` | boolean | Is task blocked? |
| `assigned_agent` | string | Which agent should handle this |
| `estimated_tokens` | int | Expected token usage |
| `dependencies` | array | What must complete first |
| `deliverables` | array | Expected outputs |
| `commits` | array | Git commits for this task |

### Task Completion Criteria

**A task is complete when:**
1. All code changes committed
2. Basic quality requirements met (not full quality gates)
3. Documentation updated
4. Changes pushed to git

**Quality gates are NOT required for task completion.** They're enforced at sprint level.

---

## Status System

### Unified Status Values

All objects (Roadmap, Track, Sprint, Task) use the same status enum:

| Status | Description | Transition From | Transition To |
|--------|-------------|-----------------|---------------|
| `not_started` | Work not yet begun | - | `in_progress`, `won't_do` |
| `in_progress` | Active development | `not_started`, `paused` | `paused`, `completed`, `won't_do` |
| `paused` | Temporarily halted | `in_progress` | `in_progress`, `won't_do` |
| `completed` | Development finished | `in_progress` | `production_ready` |
| `production_ready` | Passed all quality gates | `completed` | `deployed` |
| `deployed` | Live in production | `production_ready` | - |
| `won't_do` | Cancelled/deprioritized | any | - |

### Status Progression

```
not_started → in_progress → paused → in_progress → completed → production_ready → deployed
                                      ↓                            ↓
                                   won't_do ←───────────────────────
```

### Status Semantics by Object Type

**Task Level:**
- `completed`: Code written, committed, pushed
- `production_ready`: N/A (quality gates at sprint level)
- `deployed`: N/A (deployment at sprint/track level)

**Sprint Level:**
- `completed`: All tasks complete, all code written
- `production_ready`: All quality gates passed
- `deployed`: Deployed to production environment

**Track Level:**
- `completed`: All sprints complete
- `production_ready`: All track sprints are production ready
- `deployed`: All track features deployed

**Roadmap Level:**
- `completed`: All tracks complete
- `production_ready`: All tracks production ready
- `deployed`: Entire roadmap deployed

---

## Dependency & Blocker Model

### Dependency Structure

```yaml
dependencies:
  - type: "task" | "sprint" | "track" | "external"
    target_id: "sprint-001-task-005"
    target_status: "completed"         # What status target must reach
    reason: "Requires auth system"     # Human explanation
    optional: false                    # Is this a hard dependency?
```

### Blocker Structure

```yaml
blocked_by:
  - dependency_id: "sprint-001-task-005"
    dependency_type: "task"
    current_status: "in_progress"
    required_status: "completed"
    blocking_since: "2025-01-21T10:30:00Z"
    estimated_resolution: "2025-01-22T16:00:00Z"  # Optional
```

### Block Tracking

Each object tracks what it blocks:

```yaml
blocks:
  - type: "sprint"
    target_id: "sprint-003"
    at_status: "production_ready"     # Sprint 3 blocked until THIS reaches production_ready
```

### Dependency Types

1. **task**: Depends on another task
2. **sprint**: Depends on a sprint
3. **track**: Depends on a track
4. **external**: Depends on external system/tool

### Dependency Resolution

**Status Check Algorithm:**
```python
def is_blocked(object):
    for dep in object.dependencies:
        target = get_object(dep.target_id)
        if target.status < dep.target_status:
            return True
    return False
```

**Automatic Blocking Updates:**
- When a dependency changes status, all objects that depend on it are re-evaluated
- `blocked` flag automatically updated
- `blocked_by` array automatically updated

### Cascading Dependencies

Dependencies can cascade:
```
Track A → Sprint 1 → Task 1
   ↓         ↓          ↓
Track B → Sprint 3 → Task 7
```

If Task 1 is blocked, Sprint 1 is blocked, and Track A may be blocked.

---

## Versioning Strategy

### Semantic Versioning: MAJOR.MINOR.PATCH

**Version Component Mapping:**

| Component | Triggered By | Example |
|-----------|--------------|---------|
| **MAJOR** | Roadmap milestone completed | 1.0.0 → 2.0.0 |
| **MINOR** | Track completed | 1.2.0 → 1.3.0 |
| **PATCH** | Sprint completed | 1.2.3 → 1.2.4 |

### Version Progression Rules

**MAJOR Version Bump:**
- Complete a major roadmap milestone
- Breaking changes to project architecture
- Major feature set completions
- Requires explicit approval

**MINOR Version Bump:**
- Track completion (all sprints in track completed + production ready)
- New feature track added and completed
- Significant enhancements
- Automated on track completion

**PATCH Version Bump:**
- Sprint completion (sprint reaches production_ready)
- Bug fixes
- Minor improvements
- Automated on sprint production readiness

### Version Naming Convention

**Format**: `{major}.{minor}.{patch}-{stage}.{build}`

**Examples:**
- `1.2.0` - Production release
- `1.2.0-rc.1` - Release candidate 1
- `1.2.0-beta.3` - Beta version 3
- `1.2.0-alpha.5` - Alpha version 5
- `1.3.0-dev` - Development version

**Stage Values:**
- `dev` - Active development
- `alpha` - Feature complete, not tested
- `beta` - Testing phase
- `rc` - Release candidate
- (none) - Production release

### Version Calculation Algorithm

```python
def calculate_version(roadmap):
    major = roadmap.major_version
    minor = count_completed_tracks(roadmap)
    patch = count_production_ready_sprints(current_track)

    if roadmap.status == 'in_progress':
        stage = 'dev'
    elif roadmap.status == 'completed':
        stage = 'rc'
    elif roadmap.status == 'production_ready':
        stage = None  # Production

    return format_version(major, minor, patch, stage)
```

### Roadmap-Version Alignment

```yaml
roadmap:
  version: "1.2.3"
  major_version: 1

  # Version triggers
  version_triggers:
    major:
      - milestone: "Multi-platform Production Release"
        tracks_required: ["track-core", "track-goose", "track-cursor"]

    minor:
      track_completion: true

    patch:
      sprint_production_ready: true
```

### Git Tag Strategy

**Automatic Tagging:**
- MAJOR bumps: `v1.0.0` with annotated tag
- MINOR bumps: `v1.2.0` with annotated tag
- PATCH bumps: `v1.2.3` with lightweight tag

**Tag Format:**
```bash
git tag -a v1.2.0 -m "Track: Core Framework complete"
```

---

## Developer Workflow

### Typical Development Flow

```
1. Query roadmap status
   ├─ See current tracks and progress
   └─ Identify available work

2. Select track to work on
   ├─ Check track is not blocked
   └─ View sprints in track

3. Select sprint to work on
   ├─ Check sprint dependencies met
   ├─ Check sprint is not blocked
   └─ View tasks in sprint

4. Select task to work on
   ├─ Check task dependencies met
   ├─ Check task not blocked
   ├─ Start task
   └─ Launch appropriate agent

5. Complete task
   ├─ Write code
   ├─ Commit changes
   ├─ Push to git
   ├─ Mark task complete
   └─ Update task status

6. Complete sprint
   ├─ All tasks complete
   ├─ Run quality gates
   ├─ Pass all blocking gates
   ├─ Mark sprint production_ready
   └─ Version bump (PATCH)

7. Complete track
   ├─ All sprints production_ready
   ├─ Track-level quality gates pass
   ├─ Mark track complete
   └─ Version bump (MINOR)

8. Complete roadmap
   ├─ All tracks complete
   ├─ Roadmap-level gates pass
   ├─ Mark roadmap production_ready
   └─ Version bump (MAJOR)
```

### CLI Commands (Proposed)

```bash
# Roadmap operations
vibey roadmap status
vibey roadmap version
vibey roadmap list-tracks
vibey roadmap blockers

# Track operations
vibey track list
vibey track status <track-id>
vibey track start <track-id>
vibey track complete <track-id>
vibey track blockers <track-id>

# Sprint operations (enhanced)
vibey sprint list [--track <track-id>]
vibey sprint status <sprint-id>
vibey sprint start <sprint-id>
vibey sprint complete <sprint-id>
vibey sprint blockers <sprint-id>

# Task operations (new)
vibey task list [--sprint <sprint-id>]
vibey task status <task-id>
vibey task start <task-id>
vibey task complete <task-id>
vibey task blockers <task-id>
vibey task assign <task-id> <agent-name>

# Dependency operations
vibey deps check <object-id>
vibey deps graph [--track <track-id>]
vibey deps what-blocks <object-id>
vibey deps what-is-blocked-by <object-id>

# Version operations
vibey version current
vibey version bump <major|minor|patch>
vibey version history
```

### Agent Workflow Integration

**When agent is launched:**
1. Query current task
2. Check task dependencies
3. If blocked, report blockers
4. If not blocked, proceed with work
5. On completion, update task status
6. Check if sprint can advance

**Example:**
```bash
# Agent queries what to work on
vibey task next --agent web-developer
# Returns: sprint-001-task-003

# Agent starts task
vibey task start sprint-001-task-003

# Agent does work...

# Agent completes task
vibey task complete sprint-001-task-003 \
  --commit a1b2c3d \
  --deliverables src/api/auth/login.ts

# Check if more work in sprint
vibey task next --sprint sprint-001
```

---

## State Management & Persistence

### File Structure

```
.vibey/
├── roadmap.yaml                    # Roadmap state
├── tracks/
│   ├── track-core-framework.yaml   # Track state
│   ├── track-agent-dev.yaml
│   └── track-platform-ports.yaml
├── sprints/
│   ├── sprint-001-state.yaml       # Sprint state (existing format + enhancements)
│   ├── sprint-002-state.yaml
│   └── sprint-003-state.yaml
├── tasks/
│   ├── sprint-001-tasks.yaml       # All tasks for sprint 001
│   ├── sprint-002-tasks.yaml
│   └── sprint-003-tasks.yaml
└── dependencies/
    └── dependency-graph.yaml       # Full dependency graph
```

### Roadmap State File

**Location**: `.vibey/roadmap.yaml`

```yaml
# Roadmap state structure (as defined in Roadmap Object section)
roadmap:
  id: "vibey-framework-v1"
  name: "Vibey Framework Production Release"
  version: "1.2.0"
  # ... (full structure from Roadmap Object section)
```

### Track State File

**Location**: `.vibey/tracks/track-{id}.yaml`

```yaml
# Track state structure (as defined in Track Object section)
track:
  id: "track-core-framework"
  name: "Core Framework Development"
  # ... (full structure from Track Object section)
```

### Sprint State File (Enhanced)

**Location**: `.vibey/sprints/sprint-{number}-state.yaml`

Existing sprint state files enhanced with:
```yaml
sprint:
  # Existing fields...
  number: 1
  name: "User Authentication"
  status: "in_progress"

  # NEW fields
  track_id: "track-core-framework"
  blocked: false
  dependencies: [...]
  blocks: [...]
  blocked_by: [...]
```

### Task State File

**Location**: `.vibey/tasks/sprint-{number}-tasks.yaml`

```yaml
tasks:
  - id: "sprint-001-task-001"
    title: "Implement registration endpoint"
    # ... (full structure from Task Object section)

  - id: "sprint-001-task-002"
    title: "Implement login endpoint"
    # ...
```

### Dependency Graph File

**Location**: `.vibey/dependencies/dependency-graph.yaml`

```yaml
# Computed dependency graph for visualization and analysis
dependency_graph:
  version: "1.0"
  generated: "2025-11-06T10:00:00Z"

  nodes:
    - id: "track-core-framework"
      type: "track"
      status: "in_progress"

    - id: "sprint-001"
      type: "sprint"
      status: "completed"

    - id: "sprint-001-task-001"
      type: "task"
      status: "completed"

  edges:
    - from: "sprint-002"
      to: "sprint-001"
      type: "depends_on"
      required_status: "completed"

    - from: "sprint-001-task-002"
      to: "sprint-001-task-001"
      type: "depends_on"
      required_status: "completed"
```

### State Synchronization

**When state changes:**
1. Update primary state file (e.g., task file)
2. Update parent aggregate (e.g., sprint progress)
3. Update dependency graph
4. Update blockers for dependent objects
5. Trigger version calculation if needed

**Consistency Guarantees:**
- Atomic writes using temp files + rename
- Validation before write
- Rollback on error
- Activity log for audit trail

---

## Implementation Considerations

### Python Scripts

**New Scripts Needed:**

1. **`create-roadmap.py`**
   - Initialize roadmap structure
   - Create tracks
   - Set version strategy

2. **`create-track.py`**
   - Create new track
   - Add to roadmap
   - Set up track state file

3. **`update-track-state.py`**
   - Update track status
   - Manage track dependencies
   - Track completion

4. **`create-task.py`**
   - Create task from template
   - Add to sprint
   - Set dependencies

5. **`update-task-state.py`**
   - Update task status
   - Log completion
   - Update deliverables

6. **`query-roadmap.py`**
   - Roadmap status
   - Track progress
   - Overall metrics

7. **`query-dependencies.py`**
   - Check if object blocked
   - List blockers
   - Show dependency graph

8. **`calculate-version.py`**
   - Compute current version
   - Check version bump triggers
   - Update version

9. **`generate-dependency-graph.py`**
   - Build full dependency graph
   - Validate no cycles
   - Export for visualization

**Enhanced Existing Scripts:**

1. **`create-sprint-state.py`**
   - Add track_id field
   - Initialize dependencies
   - Set blocked state

2. **`update-sprint-state.py`**
   - Check dependencies before status change
   - Update blocked state
   - Trigger version bump on production_ready

3. **`query-sprint-state.py`**
   - Show blocker info
   - Display dependencies
   - Track-level context

### Schema Updates

**New Schema Files:**

1. **`roadmap-schema.yaml`** - Roadmap state schema
2. **`track-schema.yaml`** - Track state schema
3. **`task-schema.yaml`** - Task state schema
4. **`dependency-schema.yaml`** - Dependency structure schema

**Updated Schema:**

1. **`sprint-state-schema.yaml`** - Add new fields

### Validation Rules

**Dependency Validation:**
- No circular dependencies
- target_id must exist
- target_status must be valid
- Dependency type matches target type

**Status Validation:**
- Only valid status transitions allowed
- Cannot mark complete if blocked
- Cannot mark production_ready without quality gates

**Version Validation:**
- Version must be valid semantic version
- Version bumps must follow rules
- Version history must be chronological

---

## Trade-offs & Design Decisions

### Design Decision 1: Flat Task List vs. Phase Nesting

**Decision**: Support BOTH phase nesting (existing) AND flat task list (new)

**Rationale:**
- Backward compatibility with existing sprint plans
- Phases provide organizational structure
- Flat task list enables cross-phase dependencies
- Both have value

**Trade-offs:**
- ✅ Maintains existing workflows
- ✅ Enables advanced dependency management
- ❌ Slightly more complex data model
- ❌ Potential for inconsistency if not careful

**Mitigation:**
- Tasks reference their phase
- Scripts validate phase/task consistency
- Clear documentation on when to use each

---

### Design Decision 2: Automatic vs. Manual Version Bumps

**Decision**: Automatic MINOR/PATCH, Manual MAJOR

**Rationale:**
- Track/sprint completion is objective milestone
- MAJOR versions are strategic decisions
- Automation reduces human error
- Manual control for breaking changes

**Trade-offs:**
- ✅ Reduces version management burden
- ✅ Consistent version progression
- ❌ Less control over version timing
- ❌ May bump when not desired

**Mitigation:**
- `--no-version-bump` flag for manual control
- Version bump triggers configurable
- Clear documentation on version strategy

---

### Design Decision 3: Explicit Blocked State vs. Computed

**Decision**: Explicit `blocked: true/false` flag, automatically computed

**Rationale:**
- Performance: don't recompute on every query
- Visibility: easy to see blocked objects
- Consistency: computed from dependencies

**Trade-offs:**
- ✅ Fast queries
- ✅ Clear API
- ❌ Must keep in sync
- ❌ Potential for stale data

**Mitigation:**
- Update blocked state on every dependency change
- Validation scripts check consistency
- Rebuild command to recompute all blocked states

---

### Design Decision 4: Centralized vs. Distributed State Files

**Decision**: Distributed (one file per object type per instance)

**Rationale:**
- Scalability: large roadmaps don't create huge files
- Concurrency: multiple agents can work simultaneously
- Git-friendly: smaller diffs, less merge conflicts
- Modularity: easy to archive completed sprints

**Trade-offs:**
- ✅ Scales to large projects
- ✅ Better concurrent access
- ✅ Cleaner git history
- ❌ More complex to query entire state
- ❌ More file management

**Mitigation:**
- Provide aggregate query scripts
- Cache computed state (dependency graph)
- Clear file naming conventions

---

### Design Decision 5: Dependency Types (Limited Set vs. Extensible)

**Decision**: Limited set of 4 types (task, sprint, track, external)

**Rationale:**
- Simplicity: easy to understand and implement
- Type safety: can validate references
- Sufficient: covers 95% of use cases
- Future: can extend if needed

**Trade-offs:**
- ✅ Simple mental model
- ✅ Easy validation
- ✅ Clear semantics
- ❌ Limited flexibility
- ❌ May need custom handling for edge cases

**Mitigation:**
- "external" type for special cases
- "reason" field for human context
- Can extend in future versions

---

### Design Decision 6: Task Size Constraint (Context Window)

**Decision**: Tasks must fit in single context window (estimated tokens)

**Rationale:**
- Aligns with AI coding assistant limitations
- Forces good task breakdown
- Manageable units of work
- Predictable execution time

**Trade-offs:**
- ✅ Realistic task planning
- ✅ Predictable token usage
- ✅ Natural parallelization
- ❌ Requires upfront estimation
- ❌ May need to split tasks mid-work

**Mitigation:**
- Token estimation guidelines
- Tools to split tasks
- Flexibility to adjust estimates
- actual_tokens tracking for learning

---

### Design Decision 7: Quality Gates at Sprint Level (Not Task)

**Decision**: Quality gates enforce at sprint completion, not task completion

**Rationale:**
- Tasks are development units, sprints are quality units
- Allows iterative development within sprint
- Reduces overhead for small tasks
- Maintains existing quality gate system

**Trade-offs:**
- ✅ Faster task completion
- ✅ More flexible development
- ✅ Batch quality checks
- ❌ Issues found later
- ❌ May accumulate technical debt

**Mitigation:**
- Optional task-level quality requirements (non-blocking)
- CI/CD checks on every commit
- Agent best practices encourage quality
- Security gates always run

---

## Migration Path

### Phase 1: Foundation (Weeks 1-2)

**Goals**: Implement core data structures, no breaking changes

**Tasks:**
1. Create schema files for roadmap, track, task
2. Implement `create-roadmap.py`
3. Implement `create-track.py`
4. Add new fields to sprint state (backward compatible)
5. Implement `create-task.py` and `update-task-state.py`
6. Write tests

**Validation**: Existing sprint states load correctly

---

### Phase 2: Dependency System (Weeks 3-4)

**Goals**: Implement dependency and blocker tracking

**Tasks:**
1. Implement dependency validation
2. Create `query-dependencies.py`
3. Update `update-sprint-state.py` with dependency checks
4. Implement automatic blocked state updates
5. Create `generate-dependency-graph.py`
6. Write tests for dependency cycles, validation

**Validation**: Can create dependencies, detect blockers

---

### Phase 3: Versioning (Week 5)

**Goals**: Implement semantic versioning system

**Tasks:**
1. Create `calculate-version.py`
2. Implement version bump triggers
3. Update sprint/track completion to trigger bumps
4. Create version history tracking
5. Git tag integration
6. Write tests

**Validation**: Versions bump correctly on completions

---

### Phase 4: Query & CLI (Week 6)

**Goals**: Developer-facing query and management tools

**Tasks:**
1. Implement `query-roadmap.py`
2. Create CLI wrapper script (`vibey` command)
3. Implement all CLI commands
4. Add output formatting (text, JSON, YAML)
5. Write CLI tests
6. Documentation

**Validation**: Can manage roadmap via CLI

---

### Phase 5: Integration & Polish (Weeks 7-8)

**Goals**: Integrate with existing framework, documentation

**Tasks:**
1. Update `/vibey` command to use roadmap
2. Update sprint planning workflow
3. Update agents to query task assignments
4. Create migration tool for existing projects
5. Write comprehensive documentation
6. Create examples and tutorials
7. Update CLAUDE.md template

**Validation**: Full end-to-end workflow works

---

### Phase 6: Testing & Release (Weeks 9-10)

**Goals**: Production-ready release

**Tasks:**
1. Comprehensive testing with real projects
2. Performance optimization
3. Bug fixes
4. Documentation review
5. Release preparation
6. Version 2.0.0 release

**Validation**: Production-ready roadmap system

---

## Backward Compatibility Plan

### Existing Sprint States

**Current Format:**
```yaml
sprint:
  number: 1
  status: "in_progress"
  phases: [...]
```

**Enhanced Format:**
```yaml
sprint:
  number: 1
  status: "in_progress"
  track_id: "default-track"  # Auto-assigned if missing
  blocked: false              # Computed if missing
  dependencies: []            # Empty if missing
  phases: [...]              # Preserved
```

**Loading Strategy:**
1. Detect schema version
2. If old version, apply defaults
3. Migrate on first save
4. Log migration in activity log

### Gradual Adoption

**Projects can adopt incrementally:**
1. **Level 0**: No changes (existing sprint system)
2. **Level 1**: Add track structure (no dependencies)
3. **Level 2**: Add dependencies (no tasks)
4. **Level 3**: Add tasks (flat structure)
5. **Level 4**: Full roadmap with versioning

**Each level is production-ready**, just with fewer features.

---

## Example: Complete Roadmap

### Sample Project: "E-commerce Platform"

```yaml
roadmap:
  id: "ecommerce-v2"
  name: "E-commerce Platform v2.0"
  version: "2.3.5"
  status: "in_progress"
  blocked: false

  tracks:
    - track_id: "track-backend"
    - track_id: "track-frontend"
    - track_id: "track-mobile"
    - track_id: "track-infrastructure"

  version_history:
    - version: "2.0.0"
      date: "2025-01-15"
      milestone: "Platform Redesign Launch"
    - version: "2.1.0"
      date: "2025-03-01"
      milestone: "Backend Optimization Complete"
    - version: "2.2.0"
      date: "2025-05-15"
      milestone: "Frontend Redesign Complete"
    - version: "2.3.0"
      date: "2025-08-01"
      milestone: "Mobile App Launch"
```

### Sample Track: "Backend"

```yaml
track:
  id: "track-backend"
  name: "Backend Services"
  roadmap_id: "ecommerce-v2"
  status: "in_progress"
  blocked: false

  sprints:
    - sprint_id: "sprint-001"  # User Auth (completed)
    - sprint_id: "sprint-002"  # Product Catalog (completed)
    - sprint_id: "sprint-003"  # Shopping Cart (in progress)
    - sprint_id: "sprint-004"  # Payment Gateway (not started)

  dependencies:
    - type: "track"
      target_id: "track-infrastructure"
      target_status: "production_ready"
      reason: "Need Kubernetes cluster ready"
```

### Sample Sprint: "Shopping Cart"

```yaml
sprint:
  id: "sprint-003"
  number: 3
  name: "Shopping Cart Implementation"
  track_id: "track-backend"
  status: "in_progress"
  blocked: false

  dependencies:
    - type: "sprint"
      target_id: "sprint-002"
      target_status: "production_ready"
      reason: "Cart depends on product catalog"

  tasks:
    - task_id: "sprint-003-task-001"
    - task_id: "sprint-003-task-002"
    - task_id: "sprint-003-task-003"
```

### Sample Task: "Add to Cart Endpoint"

```yaml
task:
  id: "sprint-003-task-001"
  sprint_id: "sprint-003"
  title: "Implement add-to-cart endpoint"
  status: "completed"
  blocked: false

  assigned_agent: "web-developer"
  estimated_tokens: 6000
  actual_tokens: 5800

  dependencies:
    - type: "task"
      target_id: "sprint-002-task-005"  # Product validation utils
      target_status: "completed"
      reason: "Need product validation"

  deliverables:
    - type: "code"
      paths: ["src/api/cart/add.ts"]
    - type: "test"
      paths: ["tests/api/cart/add.test.ts"]

  commits:
    - sha: "a1b2c3d"
      message: "feat: add shopping cart endpoint"
      date: "2025-09-15T14:30:00Z"
```

---

## Visualization Examples

### Roadmap Dashboard View

```
┌─────────────────────────────────────────────────────────────┐
│ E-commerce Platform v2.0                     Version: 2.3.5  │
│ Status: in_progress                    Progress: 73% (3/4)   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ TRACKS                                                        │
│   ✓ Backend           [████████████░░] 85%   (3/4 sprints)  │
│   ✓ Frontend          [██████████████] 100%  (4/4 sprints)  │
│   → Mobile            [██████░░░░░░░░] 50%   (2/4 sprints)  │
│   ○ Infrastructure    [░░░░░░░░░░░░░░] 0%    (0/3 sprints)  │
│                                                               │
│ CURRENT WORK                                                  │
│   Track: Backend → Sprint 3: Shopping Cart                   │
│   Tasks: 5/8 completed                                        │
│   Blockers: None                                              │
│                                                               │
│ NEXT UP                                                       │
│   • Sprint 4: Payment Gateway (Backend track)                │
│   • Sprint 3: iOS App (Mobile track)                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Graph View

```
track-backend ────┐
    │             │
    ├─ sprint-001 │
    │     │       │
    │     └─ task-001                    track-infrastructure
    │     └─ task-002                          │
    │                                          │
    ├─ sprint-002 ◄──(depends on)──────────────┘
    │     │
    │     └─ task-001
    │     └─ task-002
    │     └─ task-003
    │
    ├─ sprint-003 ◄──(depends on sprint-002)
    │     │
    │     └─ task-001 ◄──(depends on sprint-002-task-003)
    │     └─ task-002
    │     └─ task-003
    │
    └─ sprint-004 ◄──(depends on sprint-003)
```

---

## Conclusion

This roadmap object hierarchy design provides:

1. **Comprehensive Project View**: Roadmap → Track → Sprint → Task
2. **Parallel Execution**: Tracks enable parallelization
3. **Explicit Dependencies**: Clear blockers and dependencies
4. **Unified Status System**: Consistent across all levels
5. **Semantic Versioning**: Tied to project progress
6. **Developer Workflow**: Clear process from roadmap to task
7. **Backward Compatibility**: Existing sprint states preserved
8. **Scalability**: Distributed file structure
9. **Extensibility**: Room for future enhancements

**Key Benefits:**
- ✅ Better project visibility
- ✅ Clear parallelization opportunities
- ✅ Explicit dependency management
- ✅ Automated version tracking
- ✅ Enhanced developer experience
- ✅ Scalable to large projects

**Next Steps:**
1. Review and approve design
2. Begin Phase 1 implementation
3. Iterate based on feedback
4. Release as Vibey Framework 2.0

---

**Document Status**: Ready for Review
**Target Implementation**: Q1 2025
**Estimated Effort**: 10 weeks (2 developers)
**Risk Level**: Low (backward compatible, incremental adoption)
