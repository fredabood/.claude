# Roadmap Object Hierarchy Design

**Version:** 2.0 (Optimal Design)
**Date:** 2025-11-06
**Status:** Design Proposal
**Author:** Vibey Framework Team

---

## Executive Summary

This document defines an optimal roadmap object hierarchy for the Vibey Agent Framework, designed from first principles without legacy constraints. The hierarchy enables structured project management from roadmap to individual tasks, with tracks enabling parallel execution and explicit dependency management.

**Key Features:**
- 4-tier hierarchy: Roadmap → Track → Sprint → Task
- Unified status system with 7 states across all levels
- Explicit dependency and blocker management with auto-computation
- Semantic versioning tied to roadmap progress
- Unified activity log at roadmap level
- Clean, purpose-built data structures

**Design Philosophy:**
- ✅ Optimize for clarity over compatibility
- ✅ Single source of truth for each concern
- ✅ Eliminate redundancy and duplication
- ✅ Make common operations simple
- ✅ Make parallelization explicit

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
12. [Design Decisions & Rationale](#design-decisions--rationale)
13. [Examples](#examples)

---

## Object Hierarchy Overview

```
┌─────────────────────────────────────────────────────────────┐
│                          ROADMAP                             │
│  Unified activity log, version management, global state      │
│  Version: 1.2.0                                              │
└─────────────────────────────────────────────────────────────┘
           │
           ├──────────────────┬──────────────────┬─────────────
           │                  │                  │
┌──────────▼──────────┐ ┌────▼─────────────┐ ┌──▼──────────────┐
│ TRACK: backend      │ │ TRACK: frontend  │ │ TRACK: infra    │
│ (Parallel Capable)  │ │ (Parallel)       │ │ (Foundation)    │
└──────────┬──────────┘ └────┬─────────────┘ └──┬──────────────┘
           │                  │                  │
    ┌──────┴──────┐      ┌───┴────┐        ┌───┴────┐
    │             │      │        │        │        │
┌───▼────┐  ┌────▼────┐ ┌▼────┐ ┌▼─────┐ ┌▼────┐ ┌▼────┐
│backend │  │backend  │ │front│ │front │ │infra│ │infra│
│-1      │  │-2       │ │-1   │ │-2    │ │-1   │ │-2   │
│(Auth)  │  │(Orders) │ │(UI) │ │(Nav) │ │(K8s)│ │(CI) │
└───┬────┘  └────┬────┘ └┬────┘ └┬─────┘ └┬────┘ └┬────┘
    │            │       │       │        │       │
  Tasks        Tasks   Tasks   Tasks    Tasks   Tasks
  (Flat)       (Flat)  (Flat)  (Flat)   (Flat)  (Flat)
```

**Hierarchy Levels:**
1. **Roadmap**: Entire project (unified log, version, global dependencies)
2. **Track**: Parallelization boundary (backend, frontend, infra, etc.)
3. **Sprint**: Work batch within track (track-scoped ID: `backend-1`, `frontend-2`)
4. **Task**: Atomic work unit (context-window sized, sprint-scoped ID)

**Key Simplifications:**
- ❌ No "phases" as separate structures (just optional labels on tasks)
- ❌ No "current_phase" tracking (not needed)
- ❌ No sprint-level activity logs (unified at roadmap level)
- ❌ No global sprint numbering (track-scoped instead)
- ✅ Single source of truth for each concern
- ✅ Clean, flat structures where possible

---

## Roadmap Object

The **Roadmap** is the top-level object with unified state management.

### Structure

```yaml
roadmap:
  # Identity
  id: "vibey-framework-v1"
  name: "Vibey Framework Production Release"

  # Version Management
  version: "1.2.0"
  version_strategy:
    major_on: "roadmap_milestone"      # Manual trigger
    minor_on: "track_completion"        # Automatic
    patch_on: "sprint_production_ready" # Automatic

  # Status
  status: "in_progress"  # not_started | in_progress | paused | completed | production_ready | deployed | won't_do
  blocked: false

  # Timing
  created: "2025-01-15T10:00:00Z"
  started: "2025-01-20T09:00:00Z"
  target_completion: "2025-12-31T23:59:59Z"
  completed: null
  deployed: null

  # Aggregate Progress
  progress:
    tracks_total: 5
    tracks_completed: 2
    sprints_total: 18
    sprints_completed: 8
    tasks_total: 156
    tasks_completed: 89
    completion_percent: 57

  # Tracks
  tracks:
    - id: "backend"
    - id: "frontend"
    - id: "mobile"
    - id: "infrastructure"
    - id: "documentation"

  # Roadmap-level dependencies (external systems)
  dependencies:
    - type: "external"
      name: "AWS Account Setup"
      status: "completed"
      required_for: "infrastructure track"

  # What's blocking the roadmap
  blocked_by: []

  # Version History
  version_history:
    - version: "1.0.0"
      date: "2025-06-01T00:00:00Z"
      milestone: "Initial Production Release"
      git_tag: "v1.0.0"
    - version: "1.1.0"
      date: "2025-09-15T00:00:00Z"
      milestone: "Multi-platform Support"
      git_tag: "v1.1.0"
    - version: "1.2.0"
      date: "2025-11-01T00:00:00Z"
      milestone: "Advanced Orchestration"
      git_tag: "v1.2.0"

  # UNIFIED ACTIVITY LOG (All roadmap events)
  activity_log:
    - timestamp: "2025-01-20T09:00:00Z"
      type: "roadmap_started"
      description: "Started roadmap: Vibey Framework Production Release"

    - timestamp: "2025-01-21T10:30:00Z"
      type: "sprint_started"
      description: "Started sprint backend-1: User Authentication"
      context:
        track_id: "backend"
        sprint_id: "backend-1"

    - timestamp: "2025-01-21T14:00:00Z"
      type: "task_completed"
      description: "Completed task: Implement registration endpoint"
      context:
        track_id: "backend"
        sprint_id: "backend-1"
        task_id: "backend-1-task-001"
        agent: "web-developer"

    - timestamp: "2025-01-25T16:00:00Z"
      type: "quality_gate"
      description: "Security Audit passed (92/85)"
      context:
        track_id: "backend"
        sprint_id: "backend-1"
        gate: "Security Audit"
        score: 92
        threshold: 85

    - timestamp: "2025-01-26T09:00:00Z"
      type: "sprint_completed"
      description: "Sprint backend-1 production ready"
      context:
        track_id: "backend"
        sprint_id: "backend-1"

    - timestamp: "2025-01-26T09:01:00Z"
      type: "version_bump"
      description: "Version bumped to 1.2.1"
      context:
        old_version: "1.2.0"
        new_version: "1.2.1"
        trigger: "sprint_production_ready"

  # Metadata
  metadata:
    created_by: "vibey-init"
    framework_version: "2.0"
    schema_version: "2.0"
    last_updated: "2025-01-26T09:01:00Z"
```

### Key Design Decisions

**Unified Activity Log:**
- ALL events logged at roadmap level (no sprint-level logs)
- Provides complete project history
- Easy to query across tracks/sprints
- Context field provides drill-down info

**Version Management:**
- Explicit strategy configuration
- Automatic bumps on triggers
- History with git tags
- Manual major version control

**Aggregate Progress:**
- Real-time computed metrics
- Cached for performance
- Single source of truth

---

## Track Object

A **Track** is a parallelization boundary containing related sprints.

### Structure

```yaml
track:
  # Identity
  id: "backend"
  name: "Backend Services Development"
  roadmap_id: "vibey-framework-v1"

  # Status
  status: "in_progress"
  blocked: false
  priority: "critical"  # critical | high | medium | low

  # Timing
  created: "2025-01-15T10:00:00Z"
  started: "2025-01-20T09:00:00Z"
  completed: null
  estimated_duration: "90 days"

  # Progress
  progress:
    sprints_total: 4
    sprints_completed: 2
    tasks_total: 45
    tasks_completed: 28
    completion_percent: 62

  # Sprints in this track (track-scoped IDs)
  sprints:
    - id: "backend-1"  # Track-scoped ID
      name: "User Authentication"
      status: "production_ready"

    - id: "backend-2"
      name: "Order Management API"
      status: "in_progress"

    - id: "backend-3"
      name: "Payment Integration"
      status: "not_started"

    - id: "backend-4"
      name: "Analytics Pipeline"
      status: "not_started"

  # Dependencies
  dependencies:
    - type: "track"
      target_id: "infrastructure"
      target_status: "production_ready"
      reason: "Requires Kubernetes cluster and databases"
      optional: false

  # What this track blocks
  blocks:
    - type: "track"
      target_id: "frontend"
      at_status: "completed"
      reason: "Frontend needs backend APIs"

  # Current blockers (auto-computed)
  blocked_by:
    - dependency_id: "infrastructure"
      dependency_type: "track"
      current_status: "in_progress"
      required_status: "production_ready"
      blocking_since: "2025-01-20T09:00:00Z"
      estimated_resolution: "2025-02-15T00:00:00Z"

  # Track-level quality gates (run after all sprints complete)
  quality_gates:
    - name: "Integration Testing"
      threshold: 90
      blocking: true
      status: "not_run"

    - name: "Load Testing"
      threshold: 85
      blocking: true
      status: "not_run"

    - name: "API Documentation"
      threshold: 95
      blocking: false
      status: "not_run"

  # Recommended agents for this track
  assigned_agents:
    - "web-developer"
    - "security-auditor"
    - "performance-engineer"

  # Metadata
  metadata:
    created_by: "sprint-planning"
    last_updated: "2025-01-26T09:00:00Z"
```

### Key Design Decisions

**Track-Scoped Sprint IDs:**
- Format: `{track-id}-{number}` (e.g., `backend-1`, `frontend-2`)
- Makes ownership clear
- Enables track-parallel numbering
- No global sprint numbering confusion

**Track as Parallelization Boundary:**
- Tracks with no dependencies can run in parallel
- Clear separation of concerns
- Natural team/feature alignment

---

## Sprint Object

A **Sprint** is a group of related tasks within a track. **Simplified** - no phases, no nested structures.

### Structure

```yaml
sprint:
  # Identity
  id: "backend-1"                    # Track-scoped ID
  name: "User Authentication System"
  track_id: "backend"
  roadmap_id: "vibey-framework-v1"

  # Status
  status: "production_ready"
  blocked: false

  # Timing
  created: "2025-01-15T10:00:00Z"
  started: "2025-01-21T10:00:00Z"
  completed: "2025-01-25T16:00:00Z"
  production_ready_at: "2025-01-26T09:00:00Z"

  # Progress
  progress:
    tasks_total: 8
    tasks_completed: 8
    completion_percent: 100

  # Tasks (flat list, no phase nesting)
  tasks:
    - id: "backend-1-task-001"
      title: "Create User database schema"
      status: "completed"

    - id: "backend-1-task-002"
      title: "Implement registration endpoint"
      status: "completed"

    - id: "backend-1-task-003"
      title: "Implement login endpoint"
      status: "completed"

    - id: "backend-1-task-004"
      title: "Add JWT token generation"
      status: "completed"

    - id: "backend-1-task-005"
      title: "Add password hashing"
      status: "completed"

    - id: "backend-1-task-006"
      title: "Write unit tests"
      status: "completed"

    - id: "backend-1-task-007"
      title: "Write integration tests"
      status: "completed"

    - id: "backend-1-task-008"
      title: "Update API documentation"
      status: "completed"

  # Dependencies
  dependencies:
    - type: "sprint"
      target_id: "infrastructure-1"  # Needs infra sprint
      target_status: "completed"
      reason: "Requires database setup"

  # What this sprint blocks
  blocks:
    - type: "sprint"
      target_id: "backend-2"
      at_status: "completed"
      reason: "Order system needs auth"

  # Current blockers (auto-computed)
  blocked_by: []

  # Quality Gates (sprint-level, not nested in phases)
  quality_gates:
    - name: "Unit Tests"
      threshold: 80
      blocking: true
      status: "passed"
      score: 95
      checked_at: "2025-01-25T14:00:00Z"

    - name: "Integration Tests"
      threshold: 80
      blocking: true
      status: "passed"
      score: 88
      checked_at: "2025-01-25T15:00:00Z"

    - name: "Security Audit"
      threshold: 85
      blocking: true
      status: "passed"
      score: 92
      checked_at: "2025-01-25T16:00:00Z"
      issues: []

    - name: "Performance Benchmark"
      threshold: 75
      blocking: false
      status: "passed"
      score: 82
      checked_at: "2025-01-25T17:00:00Z"

  # Documentation
  plan_file: "docs/sprints/backend-1-plan.md"
  deliverables:
    - "User registration API endpoint"
    - "User login API endpoint"
    - "JWT authentication middleware"
    - "Comprehensive test suite"
    - "API documentation"

  # Metadata
  metadata:
    estimated_duration: "5 days"
    actual_duration: "5 days"
    estimated_tokens: 50000
    actual_tokens: 48500
    agents_used: ["web-developer", "security-auditor", "test-writer"]
    last_updated: "2025-01-26T09:00:00Z"
```

### Key Design Decisions

**No Phases Structure:**
- Tasks are flat, not nested in phases
- Optional `phase` label on tasks for organization
- Eliminates complexity and duplication
- Single source of truth for task state

**Sprint-Level Quality Gates:**
- Quality gates directly on sprint (not nested in phases)
- Flat array, easy to query
- Clear blocking vs. non-blocking distinction

**Track-Scoped Sprint IDs:**
- `backend-1`, `frontend-1`, etc.
- Clear ownership
- Natural parallelization

---

## Task Object

A **Task** is the smallest unit of work, sized for a single model context window.

### Structure

```yaml
task:
  # Identity
  id: "backend-1-task-002"           # Sprint-scoped ID
  sprint_id: "backend-1"
  track_id: "backend"
  roadmap_id: "vibey-framework-v1"

  # Description
  title: "Implement user registration endpoint"
  description: |
    Create POST /api/auth/register endpoint with:
    - Email validation
    - Password strength validation
    - Duplicate email check
    - User creation
    - JWT token generation
    - Error handling

  # Status
  status: "completed"
  blocked: false

  # Timing
  created: "2025-01-21T10:00:00Z"
  started: "2025-01-21T11:00:00Z"
  completed: "2025-01-21T15:30:00Z"

  # Assignment
  assigned_agent: "web-developer"
  priority: "high"  # critical | high | medium | low

  # Optional: Phase label (organizational only, not structural)
  phase_label: "API Development"

  # Complexity & Size
  estimated_tokens: 8000
  actual_tokens: 7800
  complexity: "medium"  # simple | medium | complex

  # Dependencies
  dependencies:
    - type: "task"
      target_id: "backend-1-task-001"  # Database schema
      target_status: "completed"
      reason: "Need User table created"

    - type: "task"
      target_id: "infrastructure-1-task-003"  # Database connection
      target_status: "completed"
      reason: "Need database connection configured"

  # What this task blocks
  blocks:
    - type: "task"
      target_id: "backend-1-task-003"  # Login endpoint
      at_status: "completed"
      reason: "Login needs registration logic"

  # Current blockers (auto-computed)
  blocked_by: []

  # Deliverables
  deliverables:
    - type: "code"
      paths:
        - "src/api/auth/register.ts"
        - "src/api/auth/validation.ts"
        - "src/models/user.ts"

    - type: "test"
      paths:
        - "tests/api/auth/register.test.ts"
        - "tests/api/auth/validation.test.ts"

    - type: "documentation"
      paths:
        - "docs/api/auth.md"

  # Git commits
  commits:
    - sha: "a1b2c3d4"
      message: "feat: add user registration endpoint"
      date: "2025-01-21T14:00:00Z"
      author: "web-developer-agent"

    - sha: "e5f6g7h8"
      message: "test: add registration endpoint tests"
      date: "2025-01-21T15:00:00Z"
      author: "web-developer-agent"

  # Quality notes (non-blocking for task completion)
  quality_notes:
    - "Unit tests written ✓"
    - "Type safety verified ✓"
    - "Error handling implemented ✓"
    - "Input validation complete ✓"

  # Metadata
  metadata:
    token_efficiency: 0.975  # actual / estimated
    duration_hours: 4.5
    last_updated: "2025-01-21T15:30:00Z"
```

### Key Design Decisions

**Flat Structure:**
- Tasks are not nested in phases
- Optional `phase_label` for organization
- Single source of truth for task state

**Context Window Sizing:**
- Explicit token estimation and tracking
- Learn from actual_tokens for future estimates
- Forces reasonable task breakdown

**Task Completion Criteria:**
- Code written and committed
- Basic quality checks (non-blocking)
- Documentation updated
- Changes pushed
- **Quality gates enforced at sprint level, not task level**

---

## Status System

### Unified Status Values

**All objects** (Roadmap, Track, Sprint, Task) use the same status enum:

| Status | Description | Can Transition To |
|--------|-------------|-------------------|
| `not_started` | Work not yet begun | `in_progress`, `won't_do` |
| `in_progress` | Active development | `paused`, `completed`, `won't_do` |
| `paused` | Temporarily halted | `in_progress`, `won't_do` |
| `completed` | Development finished | `production_ready` |
| `production_ready` | Passed all quality gates | `deployed` |
| `deployed` | Live in production | *(terminal state)* |
| `won't_do` | Cancelled/deprioritized | *(terminal state)* |

### Status Progression

```
not_started → in_progress → completed → production_ready → deployed
                ↓     ↑
              paused  ┘
                ↓
            won't_do
```

### Status Semantics by Level

**Task:**
- `completed`: Code written, committed, pushed, basic quality checks done
- `production_ready`: N/A (tasks don't have quality gates)
- `deployed`: N/A (deployment is sprint/track level)

**Sprint:**
- `completed`: All tasks complete
- `production_ready`: All blocking quality gates passed
- `deployed`: Deployed to production

**Track:**
- `completed`: All sprints completed
- `production_ready`: All sprints production_ready + track quality gates passed
- `deployed`: All track features deployed

**Roadmap:**
- `completed`: All tracks completed
- `production_ready`: All tracks production_ready
- `deployed`: Entire roadmap deployed

### Automatic Status Propagation

**When task completes:**
```python
if all_tasks_in_sprint_completed(sprint):
    sprint.status = 'completed'
    # Trigger quality gate checks
```

**When sprint reaches production_ready:**
```python
if all_sprints_in_track_production_ready(track):
    track.status = 'completed'
    # Trigger track quality gates
    # Trigger version bump (PATCH)
```

**When track completes:**
```python
if all_tracks_completed(roadmap):
    roadmap.status = 'completed'
    # Trigger version bump (MINOR)
```

---

## Dependency & Blocker Model

### Dependency Structure

```yaml
dependencies:
  - type: "task" | "sprint" | "track" | "external"
    target_id: "backend-1-task-005"   # What we depend on
    target_status: "completed"         # Status it must reach
    reason: "Requires auth system"     # Human explanation
    optional: false                    # Hard vs. soft dependency
```

### Blocker Structure (Auto-Computed)

```yaml
blocked_by:
  - dependency_id: "backend-1-task-005"
    dependency_type: "task"
    current_status: "in_progress"
    required_status: "completed"
    blocking_since: "2025-01-21T10:30:00Z"
    estimated_resolution: "2025-01-21T16:00:00Z"
```

### Automatic Blocked State

**The `blocked` flag is automatically computed:**

```python
def is_blocked(obj):
    """Check if object is blocked by dependencies."""
    for dep in obj.dependencies:
        if dep.optional:
            continue  # Optional dependencies don't block

        target = get_object(dep.target_id)
        if not has_reached_status(target.status, dep.target_status):
            return True

    return False
```

**Status Comparison:**
```python
STATUS_ORDER = [
    'not_started',
    'in_progress',
    'paused',
    'completed',
    'production_ready',
    'deployed',
    'won't_do'
]

def has_reached_status(current, required):
    """Check if current status >= required status."""
    if current == 'won't_do' or required == 'won't_do':
        return current == required

    return STATUS_ORDER.index(current) >= STATUS_ORDER.index(required)
```

### Dependency Types

| Type | Description | Example |
|------|-------------|---------|
| `task` | Depends on another task | Task B needs Task A's code |
| `sprint` | Depends on a sprint | Sprint 2 needs Sprint 1's API |
| `track` | Depends on a track | Frontend needs Backend APIs |
| `external` | Depends on external system | Infrastructure needs AWS account |

### Dependency Validation

**Validation Rules:**
1. No circular dependencies (enforced at creation time)
2. `target_id` must exist
3. `target_status` must be valid status
4. `type` must match target object type
5. Cannot depend on an object at a higher level (e.g., task can't depend on track)

**Circular Dependency Check:**
```python
def has_circular_dependency(obj_id, dep_id, graph):
    """Check if adding dependency would create a cycle."""
    visited = set()

    def visit(node):
        if node in visited:
            return True  # Cycle detected
        visited.add(node)

        for dep in graph.get(node, []):
            if visit(dep):
                return True

        visited.remove(node)
        return False

    # Simulate adding edge
    temp_graph = graph.copy()
    temp_graph[obj_id] = temp_graph.get(obj_id, []) + [dep_id]

    return visit(obj_id)
```

### Block Tracking

**What this object blocks:**
```yaml
blocks:
  - type: "sprint"
    target_id: "backend-3"
    at_status: "production_ready"
    reason: "Payment system needs auth"
```

This is the inverse relationship - "If I reach `production_ready`, then `backend-3` is no longer blocked by me."

### Dependency Resolution Workflow

**When dependency changes status:**
1. Identify all objects that depend on it
2. Re-compute their `blocked` status
3. Update their `blocked_by` arrays
4. Log activity if blocking status changed
5. Notify if object became unblocked

---

## Versioning Strategy

### Semantic Versioning: MAJOR.MINOR.PATCH

**Mapping to Hierarchy:**

| Component | Triggered By | Automation | Example |
|-----------|--------------|------------|---------|
| **MAJOR** | Roadmap milestone | Manual | 1.0.0 → 2.0.0 |
| **MINOR** | Track completion | Automatic | 1.2.0 → 1.3.0 |
| **PATCH** | Sprint production_ready | Automatic | 1.2.3 → 1.2.4 |

### Version Bump Rules

**PATCH Bump (Automatic):**
- Triggered when sprint reaches `production_ready`
- Happens immediately
- Git tag: `v1.2.4` (lightweight)
- Activity log entry created

**MINOR Bump (Automatic):**
- Triggered when track reaches `production_ready`
- All sprints in track must be production_ready
- Git tag: `v1.3.0` (annotated)
- Activity log entry created

**MAJOR Bump (Manual):**
- Requires explicit command: `vibey version bump major`
- Used for roadmap milestones
- Breaking changes
- Major feature completions
- Git tag: `v2.0.0` (annotated with message)
- Activity log entry created

### Version Naming Convention

**Format:** `{major}.{minor}.{patch}[-{stage}[.{build}]]`

**Stage Values:**
- *(none)* - Production release
- `rc` - Release candidate
- `beta` - Beta testing
- `alpha` - Alpha testing
- `dev` - Active development

**Examples:**
- `1.2.3` - Production
- `1.3.0-rc.1` - Release candidate 1
- `1.3.0-beta.2` - Beta 2
- `2.0.0-alpha` - Alpha
- `1.2.4-dev` - Development

**Stage Determination:**
```python
def determine_stage(roadmap):
    if roadmap.status == 'deployed':
        return None  # Production
    elif roadmap.status == 'production_ready':
        return 'rc'
    elif roadmap.status == 'completed':
        return 'beta'
    elif roadmap.status == 'in_progress':
        return 'dev'
    else:
        return 'dev'
```

### Version Calculation

```python
def calculate_version(roadmap):
    major = roadmap.major_version

    # Minor = number of tracks that are production_ready
    minor = count_production_ready_tracks(roadmap)

    # Patch = number of sprints in current track that are production_ready
    current_track = get_current_track(roadmap)
    patch = count_production_ready_sprints(current_track) if current_track else 0

    stage = determine_stage(roadmap)

    return format_version(major, minor, patch, stage)
```

### Git Integration

**Automatic Tagging:**
```python
def on_version_bump(old_version, new_version, trigger):
    # Create git tag
    if is_major_bump(new_version):
        # Annotated tag for major versions
        git_tag(f"v{new_version}", f"Major release: {roadmap.name}", annotated=True)
    elif is_minor_bump(new_version):
        # Annotated tag for minor versions
        git_tag(f"v{new_version}", f"Track completion: {track.name}", annotated=True)
    else:
        # Lightweight tag for patches
        git_tag(f"v{new_version}", annotated=False)

    # Update roadmap version history
    roadmap.version_history.append({
        'version': new_version,
        'date': now(),
        'trigger': trigger,
        'git_tag': f"v{new_version}"
    })

    # Log activity
    log_activity('version_bump', f"Version bumped to {new_version}", {
        'old_version': old_version,
        'new_version': new_version,
        'trigger': trigger
    })
```

### Version Control

**Preventing unwanted bumps:**
```bash
# Disable automatic version bumps
vibey config set version.auto_bump false

# Re-enable
vibey config set version.auto_bump true

# Manual bump
vibey version bump patch
vibey version bump minor
vibey version bump major --message "Breaking API changes"
```

---

## Developer Workflow

### Typical Development Flow

```
1. Query roadmap status
   $ vibey roadmap status
   → See current tracks, progress, blockers

2. Select available work
   $ vibey task next --track backend
   → Returns: backend-1-task-003 (no blockers)

3. Start task
   $ vibey task start backend-1-task-003
   → Updates status to in_progress
   → Logs activity
   → Launches appropriate agent

4. Do work
   → Write code
   → Run tests
   → Commit changes

5. Complete task
   $ vibey task complete backend-1-task-003 \
       --commits a1b2c3d,e5f6g7h \
       --deliverables src/api/auth/login.ts,tests/api/auth/login.test.ts
   → Updates task status
   → Checks if sprint complete
   → Updates sprint progress
   → Logs activity

6. Sprint automatically completes when all tasks done
   → Status: completed
   → Quality gates triggered

7. Sprint reaches production_ready after gates pass
   → Status: production_ready
   → Version bumps automatically (PATCH)
   → Git tag created
   → Activity logged

8. Track completes when all sprints production_ready
   → Status: completed
   → Track quality gates triggered
   → Version bumps (MINOR)

9. Roadmap completes when all tracks done
   → Status: completed
   → Ready for deployment
```

### CLI Commands

**Roadmap:**
```bash
vibey roadmap status
vibey roadmap version
vibey roadmap tracks
vibey roadmap activity [--limit 20]
vibey roadmap blockers
vibey roadmap export --format json
```

**Track:**
```bash
vibey track list
vibey track status <track-id>
vibey track sprints <track-id>
vibey track progress <track-id>
vibey track blockers <track-id>
```

**Sprint:**
```bash
vibey sprint list [--track <track-id>]
vibey sprint status <sprint-id>
vibey sprint tasks <sprint-id>
vibey sprint start <sprint-id>
vibey sprint quality-gates <sprint-id>
vibey sprint complete <sprint-id>  # Manual if needed
```

**Task:**
```bash
vibey task list [--sprint <sprint-id>]
vibey task status <task-id>
vibey task next [--track <track-id>] [--agent <agent-name>]
vibey task start <task-id>
vibey task complete <task-id> --commits <sha> --deliverables <paths>
vibey task assign <task-id> <agent-name>
vibey task blockers <task-id>
```

**Dependencies:**
```bash
vibey deps check <object-id>
vibey deps graph [--track <track-id>]
vibey deps what-blocks <object-id>
vibey deps blocked-by <object-id>
vibey deps validate  # Check for circular deps
```

**Version:**
```bash
vibey version current
vibey version bump <major|minor|patch> [--message "..."]
vibey version history
vibey version strategy
```

### Agent Integration

**Agent queries available work:**
```python
# Agent asks: "What should I work on?"
task = query_next_task(agent_name="web-developer", track="backend")

if task.blocked:
    print(f"Task {task.id} is blocked by: {task.blocked_by}")
    # Suggest working on blocker or different task
else:
    start_task(task.id)
    # Agent does work
    complete_task(task.id, commits=[...], deliverables=[...])
```

**Automatic agent routing:**
```python
def recommend_agent_for_task(task):
    """Recommend agent based on task characteristics."""

    # Check task.assigned_agent first
    if task.assigned_agent:
        return task.assigned_agent

    # Check sprint's recommended agents
    sprint = get_sprint(task.sprint_id)
    track = get_track(sprint.track_id)

    # Use track's assigned agents
    if track.assigned_agents:
        # Pick based on task type, complexity, etc.
        return select_best_agent(track.assigned_agents, task)

    # Fall back to coordinator
    return "coordinator"
```

---

## State Management & Persistence

### File Structure

```
.vibey/
├── roadmap.yaml                     # Roadmap state (unified log, version, global state)
├── tracks/
│   ├── backend.yaml                 # Track state
│   ├── frontend.yaml
│   ├── mobile.yaml
│   ├── infrastructure.yaml
│   └── documentation.yaml
├── sprints/
│   ├── backend-1.yaml               # Sprint state (flat structure)
│   ├── backend-2.yaml
│   ├── frontend-1.yaml
│   ├── frontend-2.yaml
│   └── infrastructure-1.yaml
├── tasks/
│   ├── backend-1-tasks.yaml         # All tasks for sprint
│   ├── backend-2-tasks.yaml
│   ├── frontend-1-tasks.yaml
│   └── ...
└── cache/
    ├── dependency-graph.yaml        # Computed dependency graph
    ├── progress-snapshot.yaml       # Cached aggregate progress
    └── blocker-index.yaml           # Index of all current blockers
```

### Schema Versions

**All state files include schema version:**
```yaml
metadata:
  schema_version: "2.0"
  framework_version: "2.0"
```

This enables future migrations if needed.

### State Synchronization

**When state changes:**
1. Update primary object (e.g., task file)
2. Update parent aggregates (sprint progress, track progress, roadmap progress)
3. Recompute blocked states for dependent objects
4. Update dependency graph cache
5. Log activity to unified roadmap log
6. Trigger version bump if applicable

**Atomic Updates:**
```python
def update_task_status(task_id, new_status):
    with atomic_transaction():
        # 1. Update task
        task = load_task(task_id)
        task.status = new_status
        save_task(task)

        # 2. Update sprint progress
        sprint = load_sprint(task.sprint_id)
        sprint.progress = calculate_progress(sprint)
        save_sprint(sprint)

        # 3. Check if sprint completes
        if all_tasks_complete(sprint):
            sprint.status = 'completed'
            trigger_quality_gates(sprint)

        # 4. Update track progress
        track = load_track(sprint.track_id)
        track.progress = calculate_progress(track)
        save_track(track)

        # 5. Update roadmap progress
        roadmap = load_roadmap(track.roadmap_id)
        roadmap.progress = calculate_progress(roadmap)
        save_roadmap(roadmap)

        # 6. Recompute blockers
        update_blockers_for_dependencies(task_id)

        # 7. Update cache
        invalidate_cache(['dependency-graph', 'progress-snapshot'])

        # 8. Log activity
        log_activity('task_completed', f"Completed task: {task.title}", {
            'task_id': task_id,
            'sprint_id': task.sprint_id,
            'track_id': task.track_id
        })
```

### Caching Strategy

**Computed values cached:**
- Dependency graph (full graph computation)
- Progress percentages (aggregate rollups)
- Blocker index (all blocked objects)

**Cache invalidation:**
- On any status change
- On dependency add/remove
- On demand via `vibey cache rebuild`

**Cache rebuild:**
```bash
vibey cache rebuild [--graph] [--progress] [--blockers]
```

---

## Implementation Considerations

### Python Scripts Required

**Core Scripts:**

1. **`vibey-roadmap.py`**
   - Create roadmap
   - Query roadmap status
   - Manage roadmap-level state
   - ~400 lines

2. **`vibey-track.py`**
   - Create track
   - Update track state
   - Query track status
   - ~350 lines

3. **`vibey-sprint.py`**
   - Create sprint (from plan)
   - Update sprint state
   - Query sprint status
   - Quality gate management
   - ~500 lines

4. **`vibey-task.py`**
   - Create task
   - Update task state
   - Query task status
   - Task assignment
   - ~400 lines

5. **`vibey-deps.py`**
   - Add dependency
   - Remove dependency
   - Validate dependencies (no cycles)
   - Query dependency graph
   - Update blocked states
   - ~600 lines

6. **`vibey-version.py`**
   - Calculate version
   - Bump version
   - Version history
   - Git tag management
   - ~300 lines

7. **`vibey-query.py`**
   - Cross-object queries
   - Next available task
   - Blocker analysis
   - Progress reports
   - ~400 lines

8. **`vibey-cache.py`**
   - Build dependency graph
   - Compute progress rollups
   - Build blocker index
   - Cache management
   - ~300 lines

9. **`vibey-validate.py`**
   - Validate state consistency
   - Check for circular dependencies
   - Verify schema compliance
   - Detect orphaned objects
   - ~250 lines

10. **`vibey-export.py`**
    - Export roadmap (JSON, YAML, Markdown)
    - Generate reports
    - Dashboard data
    - ~200 lines

**Total Estimated LOC:** ~3,700 lines

### Schema Files Required

1. **`roadmap-schema.yaml`** - Roadmap state schema
2. **`track-schema.yaml`** - Track state schema
3. **`sprint-schema.yaml`** - Sprint state schema (simplified, no phases)
4. **`task-schema.yaml`** - Task state schema
5. **`dependency-schema.yaml`** - Dependency structure schema

### Dependencies

**Python Packages:**
```
pyyaml>=6.0
jsonschema>=4.0  # Schema validation
networkx>=3.0    # Dependency graph analysis
click>=8.0       # CLI framework
```

### Performance Considerations

**For large roadmaps (1000+ tasks):**

1. **Lazy Loading**: Load objects on-demand, not all at once
2. **Caching**: Cache computed values (dependency graph, progress)
3. **Indexing**: Build indices for fast lookups (blocker index)
4. **Batch Updates**: Update multiple objects in single transaction
5. **Incremental Computation**: Update only affected objects

**Optimization Targets:**
- `vibey task next`: <100ms (even with 1000+ tasks)
- `vibey roadmap status`: <200ms (with caching)
- `vibey deps graph`: <500ms (from cache)
- State update: <50ms per object

---

## Design Decisions & Rationale

### 1. No Phases as Structural Objects

**Decision**: Tasks are flat, phases are optional labels

**Rationale:**
- Phases added complexity without clear benefit
- Tasks are the atomic unit of work
- Labels provide organization without structure
- Eliminates duplication (task state in phase, task state in flat list)
- Simpler queries and updates

**Trade-offs:**
- ✅ Simpler data model
- ✅ Single source of truth for tasks
- ✅ Easier to query and update
- ✅ No nested iteration required
- ❌ Less visual organization (mitigated by labels)
- ❌ Phase-level progress tracking removed (can compute from labels)

---

### 2. Track-Scoped Sprint IDs

**Decision**: Sprint IDs are `{track-id}-{number}` (e.g., `backend-1`)

**Rationale:**
- Makes ownership immediately clear
- Enables parallel numbering across tracks
- No global sprint numbering confusion
- Natural fit with track-based parallelization
- Easier to understand dependencies

**Trade-offs:**
- ✅ Clear ownership and organization
- ✅ Enables track-parallel development
- ✅ Human-readable and meaningful
- ✅ No numbering conflicts
- ❌ Slightly longer IDs (minimal impact)

---

### 3. Unified Activity Log at Roadmap Level

**Decision**: Single activity log for entire roadmap

**Rationale:**
- Complete project history in one place
- Easy to query across tracks/sprints
- Simplifies state management
- Better for analytics and reporting
- Context field provides drill-down

**Trade-offs:**
- ✅ Complete project visibility
- ✅ Simpler state management
- ✅ Better for reporting and analytics
- ✅ Single source of truth for history
- ❌ Log can grow large (mitigate with archiving)
- ❌ More entries per file (mitigate with pagination)

---

### 4. Automatic Version Bumps

**Decision**: Automatic MINOR/PATCH, manual MAJOR

**Rationale:**
- Sprint/track completion is objective milestone
- Reduces manual version management
- Consistent progression
- MAJOR versions are strategic decisions
- Can disable if needed

**Trade-offs:**
- ✅ Reduces management overhead
- ✅ Consistent version progression
- ✅ Objective triggers
- ❌ Less control over timing (mitigate with disable flag)
- ❌ May bump when not desired (mitigate with manual mode)

---

### 5. Explicit `blocked` Flag with Auto-Computation

**Decision**: `blocked: true/false` automatically computed from dependencies

**Rationale:**
- Performance: Don't recompute on every query
- Visibility: Easy to see blocked objects
- Consistency: Computed from dependencies
- Simple API: Just check the flag

**Trade-offs:**
- ✅ Fast queries (no computation)
- ✅ Simple API
- ✅ Clear visibility
- ❌ Must keep in sync (mitigate with update triggers)
- ❌ Potential for staleness (mitigate with validation)

---

### 6. Distributed File Structure

**Decision**: One file per object (roadmap, each track, each sprint, task batch)

**Rationale:**
- Scalability: Large roadmaps don't create huge files
- Concurrency: Multiple agents can work simultaneously
- Git-friendly: Smaller diffs, fewer conflicts
- Modularity: Easy to archive completed work
- Performance: Load only what's needed

**Trade-offs:**
- ✅ Scales to large projects
- ✅ Better concurrent access
- ✅ Cleaner git history
- ✅ Faster loads (lazy loading)
- ❌ More file management (mitigate with scripts)
- ❌ More complex queries (mitigate with caching)

---

### 7. Quality Gates at Sprint Level Only

**Decision**: Quality gates enforced at sprint completion, not task completion

**Rationale:**
- Tasks are development units, sprints are quality units
- Reduces overhead for individual tasks
- Allows iterative development
- Batch quality checks are more efficient
- Maintains existing quality gate philosophy

**Trade-offs:**
- ✅ Faster task completion
- ✅ More flexible development workflow
- ✅ Batch quality checks
- ✅ Reduces overhead
- ❌ Issues found later (mitigate with CI/CD)
- ❌ May accumulate debt (mitigate with optional task quality notes)

---

### 8. Task Size Constraint (Context Window)

**Decision**: Tasks must fit in single context window

**Rationale:**
- Aligns with AI assistant limitations
- Forces good task decomposition
- Predictable execution
- Manageable units of work
- Realistic planning

**Trade-offs:**
- ✅ Realistic task sizes
- ✅ Predictable token usage
- ✅ Forces good planning
- ✅ Natural parallelization boundaries
- ❌ Requires upfront estimation (mitigate with guidelines)
- ❌ May need task splitting (mitigate with split tool)

---

## Examples

### Complete Example: E-commerce Platform

#### Roadmap

```yaml
roadmap:
  id: "ecommerce-v2"
  name: "E-commerce Platform v2.0"
  version: "2.1.3"
  status: "in_progress"
  blocked: false

  progress:
    tracks_total: 4
    tracks_completed: 1
    sprints_total: 12
    sprints_completed: 5
    tasks_total: 89
    tasks_completed: 67
    completion_percent: 75

  tracks:
    - id: "backend"
    - id: "frontend"
    - id: "mobile"
    - id: "infrastructure"

  activity_log:
    - timestamp: "2025-09-15T14:00:00Z"
      type: "track_completed"
      description: "Backend track production ready"
      context:
        track_id: "backend"

    - timestamp: "2025-09-15T14:01:00Z"
      type: "version_bump"
      description: "Version bumped to 2.1.0"
      context:
        trigger: "track_completion"
```

#### Track: Backend

```yaml
track:
  id: "backend"
  name: "Backend Services"
  roadmap_id: "ecommerce-v2"
  status: "production_ready"
  blocked: false

  sprints:
    - id: "backend-1"
      name: "User Authentication"
      status: "production_ready"

    - id: "backend-2"
      name: "Product Catalog API"
      status: "production_ready"

    - id: "backend-3"
      name: "Shopping Cart"
      status: "production_ready"

    - id: "backend-4"
      name: "Payment Integration"
      status: "production_ready"

  dependencies: []
  blocks:
    - type: "track"
      target_id: "frontend"
      at_status: "completed"
```

#### Sprint: Shopping Cart

```yaml
sprint:
  id: "backend-3"
  name: "Shopping Cart Implementation"
  track_id: "backend"
  status: "production_ready"
  blocked: false

  tasks:
    - id: "backend-3-task-001"
      title: "Create Cart database schema"
      status: "completed"

    - id: "backend-3-task-002"
      title: "Implement add-to-cart endpoint"
      status: "completed"

    - id: "backend-3-task-003"
      title: "Implement update cart endpoint"
      status: "completed"

    - id: "backend-3-task-004"
      title: "Implement remove from cart endpoint"
      status: "completed"

    - id: "backend-3-task-005"
      title: "Write cart tests"
      status: "completed"

  dependencies:
    - type: "sprint"
      target_id: "backend-2"
      target_status: "production_ready"
      reason: "Cart depends on product catalog"

  quality_gates:
    - name: "Unit Tests"
      threshold: 80
      blocking: true
      status: "passed"
      score: 95

    - name: "Security Audit"
      threshold: 85
      blocking: true
      status: "passed"
      score: 88
```

#### Task: Add to Cart Endpoint

```yaml
task:
  id: "backend-3-task-002"
  sprint_id: "backend-3"
  track_id: "backend"
  title: "Implement add-to-cart endpoint"
  status: "completed"
  blocked: false

  assigned_agent: "web-developer"
  phase_label: "API Development"

  estimated_tokens: 6000
  actual_tokens: 5800

  dependencies:
    - type: "task"
      target_id: "backend-3-task-001"
      target_status: "completed"
      reason: "Need cart schema"

    - type: "task"
      target_id: "backend-2-task-003"
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
      date: "2025-08-15T14:30:00Z"
```

---

## Summary

This optimized design eliminates backward compatibility constraints to create a cleaner, more maintainable system:

**Key Improvements:**
1. ✅ **Flat task structure** - No phase nesting, optional labels
2. ✅ **Track-scoped sprint IDs** - Clear ownership (`backend-1`, not `sprint-1`)
3. ✅ **Unified activity log** - All events at roadmap level
4. ✅ **Simplified sprint structure** - No current_phase, no phase objects
5. ✅ **Direct quality gates** - Sprint-level array, not nested in phases
6. ✅ **Clean file structure** - Purpose-built schemas from scratch
7. ✅ **Auto-computed blockers** - Explicit flag, automatically maintained

**Eliminated Complexity:**
- ❌ Dual phase/task structures
- ❌ Phase-level progress tracking
- ❌ Current phase pointers
- ❌ Sprint-level activity logs
- ❌ Global sprint numbering
- ❌ Backward compatibility code
- ❌ Migration paths

**Result:**
A cleaner, more maintainable system that's easier to understand, implement, and use. Perfect for a greenfield project with no legacy constraints.

---

**Document Status**: Ready for Implementation
**Target**: Vibey Framework 2.0
**Estimated Effort**: 8 weeks (2 developers)
**Risk Level**: Low (clean slate design)
