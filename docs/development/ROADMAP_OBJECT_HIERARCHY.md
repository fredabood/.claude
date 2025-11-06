# Roadmap Object Hierarchy Design

**Version:** 2.1 (Gate Model)
**Date:** 2025-11-06
**Status:** Design Proposal
**Author:** Vibey Framework Team

---

## Executive Summary

This document defines an optimal roadmap object hierarchy for the Vibey Agent Framework, designed from first principles without legacy constraints. The hierarchy enables structured project management from roadmap to individual tasks, with tracks enabling parallel execution and a sophisticated three-tier gate system for quality and dependency management.

**Key Features:**
- 4-tier hierarchy: Roadmap → Track → Sprint → Task
- Sprint redefined as **logical unit of work pushable to production**
- Task redefined as **context-window sized work unit** (no production concerns)
- Three-tier gate system:
  - **Development Gates**: External dependencies (other sprints/tasks)
  - **Completion Gates**: Quality checks blocking completion (docs, CI/CD)
  - **Production Gates**: Quality checks blocking production (security, testing)
- Quality gates are task objects within the sprint
- Gate-check statuses: `completion_gate_check`, `production_gate_check`
- Unified activity log at roadmap level
- Semantic versioning tied to roadmap progress
- Clean, purpose-built data structures

**Design Philosophy:**
- ✅ Optimize for clarity over compatibility
- ✅ Single source of truth for each concern
- ✅ Sprints are production-deployable units
- ✅ Tasks are context-window sized units
- ✅ Quality gates are highly isolated task objects
- ✅ External dependencies are development gates
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
7. [Gate System](#gate-system)
   - [Development Gates](#development-gates)
   - [Quality Gates](#quality-gates)
   - [Completion Gates](#completion-gates)
   - [Production Gates](#production-gates)
8. [Dependency & Blocker Model](#dependency--blocker-model)
9. [Versioning Strategy](#versioning-strategy)
10. [Developer Workflow](#developer-workflow)
11. [State Management & Persistence](#state-management--persistence)
12. [Documentation Structure & Context Management](#documentation-structure--context-management)
    - [Context Self-Containment Goal](#context-self-containment-goal)
    - [Current Design Assessment](#current-design-assessment)
    - [Context Budget Guidelines](#context-budget-guidelines)
    - [Mandatory Documentation Sections](#mandatory-documentation-sections)
    - [Dependency Summary Requirements](#dependency-summary-requirements)
    - [Context Inheritance Rules](#context-inheritance-rules)
13. [Implementation Considerations](#implementation-considerations)
14. [Design Decisions & Rationale](#design-decisions--rationale)
15. [Examples](#examples)

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
3. **Sprint**: **Logical unit of work pushable to production** (track-scoped ID: `backend-1`, `frontend-2`)
   - Has completion gates and production gates
   - Can reach `production_ready` and `deployed` statuses
   - Contains development tasks and quality gate tasks
4. **Task**: **Context-window sized work unit** (sprint-scoped ID)
   - Sized to fit within model's context window
   - No production concerns (`production_ready`/`deployed` statuses not applicable)
   - Can be a development task OR a quality gate task (completion/production)

**Key Simplifications:**
- ❌ No "phases" as separate structures (just optional labels on tasks)
- ❌ No "current_phase" tracking (not needed)
- ❌ No sprint-level activity logs (unified at roadmap level)
- ❌ No global sprint numbering (track-scoped instead)
- ✅ Single source of truth for each concern
- ✅ Clean, flat structures where possible
- ✅ Quality gates are task objects (not separate structure)
- ✅ Sprint is production-deployable unit

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

A **Sprint** is a **logical unit of work pushable to production** within a track.

**Key Characteristics:**
- Production-deployable unit
- Contains development tasks AND quality gate tasks
- Has `completion_gate_check` and `production_gate_check` statuses
- Can reach `production_ready` and `deployed` statuses
- Quality gates are tasks, not separate structures

### Structure

```yaml
sprint:
  # Identity
  id: "backend-1"                    # Track-scoped ID
  name: "User Authentication System"
  track_id: "backend"
  roadmap_id: "vibey-framework-v1"

  # Status (sprint has all statuses)
  status: "production_ready"  # not_started | in_progress | paused | completion_gate_check | completed | production_gate_check | production_ready | deployed | won't_do
  blocked: false

  # Timing
  created: "2025-01-15T10:00:00Z"
  started: "2025-01-21T10:00:00Z"
  completion_gate_check_at: "2025-01-25T12:00:00Z"
  completed: "2025-01-25T16:00:00Z"
  production_gate_check_at: "2025-01-25T18:00:00Z"
  production_ready_at: "2025-01-26T09:00:00Z"

  # Progress
  progress:
    development_tasks_total: 5
    development_tasks_completed: 5
    completion_gate_tasks_total: 2
    completion_gate_tasks_completed: 2
    production_gate_tasks_total: 3
    production_gate_tasks_completed: 3
    tasks_total: 10
    tasks_completed: 10
    completion_percent: 100

  # Tasks (flat list: development tasks + quality gate tasks)
  tasks:
    # DEVELOPMENT TASKS (build functionality)
    - id: "backend-1-task-001"
      title: "Create User database schema"
      status: "completed"
      task_type: "development"

    - id: "backend-1-task-002"
      title: "Implement registration endpoint"
      status: "completed"
      task_type: "development"

    - id: "backend-1-task-003"
      title: "Implement login endpoint"
      status: "completed"
      task_type: "development"

    - id: "backend-1-task-004"
      title: "Add JWT token generation"
      status: "completed"
      task_type: "development"

    - id: "backend-1-task-005"
      title: "Add password hashing"
      status: "completed"
      task_type: "development"

    # COMPLETION GATE TASKS (hygiene for completion)
    - id: "backend-1-gate-c001"
      title: "Documentation Review"
      status: "completed"
      task_type: "completion_gate"
      gate_info:
        blocks_status: "completed"
        threshold: 90
        score: 95

    - id: "backend-1-gate-c002"
      title: "Git/CI/CD Hygiene Check"
      status: "completed"
      task_type: "completion_gate"
      gate_info:
        blocks_status: "completed"
        threshold: 85
        score: 92

    # PRODUCTION GATE TASKS (production readiness)
    - id: "backend-1-gate-p001"
      title: "Security Audit"
      status: "completed"
      task_type: "production_gate"
      gate_info:
        blocks_status: "production_ready"
        threshold: 85
        score: 92

    - id: "backend-1-gate-p002"
      title: "Unit Test Coverage"
      status: "completed"
      task_type: "production_gate"
      gate_info:
        blocks_status: "production_ready"
        threshold: 80
        score: 95

    - id: "backend-1-gate-p003"
      title: "Integration Testing"
      status: "completed"
      task_type: "production_gate"
      gate_info:
        blocks_status: "production_ready"
        threshold: 80
        score: 88

  # Development Gates (external dependencies)
  development_gates:
    - type: "sprint"
      target_id: "infrastructure-1"
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
    agents_used: ["web-developer", "security-auditor", "test-writer", "docs-writer"]
    last_updated: "2025-01-26T09:00:00Z"
```

### Key Design Decisions

**Sprint as Production-Deployable Unit:**
- Sprint is the smallest unit that can be pushed to production
- Has both completion and production gates
- Can reach `production_ready` and `deployed` statuses

**Quality Gates are Tasks:**
- No separate quality_gates structure
- Gates are task objects with `task_type: completion_gate | production_gate`
- Completion gates block `completed` status
- Production gates block `production_ready` status
- Highly isolated: only depend on sprint being in gate_check status

**Development Gates vs Quality Gates:**
- `development_gates`: External dependencies (other sprints/tasks)
- Quality gates: Internal task objects for quality validation
- Clear separation of concerns

**Track-Scoped Sprint IDs:**
- Format: `backend-1`, `frontend-1`, etc.
- Clear ownership
- Natural parallelization

---

## Task Object

A **Task** is a **context-window sized work unit** - the smallest unit of work in the framework.

**Key Characteristics:**
- Sized to fit within model's context window
- No production concerns (no `production_ready` or `deployed` statuses)
- Can be a **development task** OR a **quality gate task**
- Quality gate tasks are highly isolated (only depend on sprint gate_check status)

### Task Types

**1. Development Task** (`task_type: development`)
   - Builds functionality
   - **Can serve as development gates for external sprints**
   - Can depend on external development tasks

**2. Completion Gate Task** (`task_type: completion_gate`)
   - Hygiene checks (docs, CI/CD)
   - **Cannot be depended on by external sprints**
   - Highly isolated

**3. Production Gate Task** (`task_type: production_gate`)
   - Production readiness checks (security, testing)
   - **Cannot be depended on by external sprints**
   - Highly isolated

### Status Options for Tasks

**Tasks have restricted status set (no production statuses):**
- `not_started`
- `in_progress`
- `paused`
- `completion_gate_check`
- `completed`
- `won't_do`

### Structure: Development Task

```yaml
task:
  # Identity
  id: "backend-1-task-002"           # Sprint-scoped ID
  sprint_id: "backend-1"
  track_id: "backend"
  roadmap_id: "vibey-framework-v1"

  # Task Type
  task_type: "development"           # development | completion_gate | production_gate

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

  # Status (no production_ready or deployed)
  status: "completed"  # not_started | in_progress | paused | completion_gate_check | completed | won't_do
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

  # Dependencies (can depend on other tasks, even outside sprint)
  dependencies:
    - type: "task"
      target_id: "backend-1-task-001"  # Database schema
      target_status: "completed"
      reason: "Need User table created"

    - type: "task"
      target_id: "infrastructure-1-task-003"  # Database connection (external sprint)
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

  # Metadata
  metadata:
    token_efficiency: 0.975  # actual / estimated
    duration_hours: 4.5
    last_updated: "2025-01-21T15:30:00Z"
```

### Structure: Quality Gate Task

```yaml
task:
  # Identity
  id: "backend-1-gate-p001"          # Sprint-scoped ID
  sprint_id: "backend-1"
  track_id: "backend"
  roadmap_id: "vibey-framework-v1"

  # Task Type
  task_type: "production_gate"       # completion_gate | production_gate

  # Description
  title: "Security Audit"
  description: |
    Run security audit on authentication system:
    - SQL injection vulnerability check
    - XSS vulnerability check
    - CSRF protection verification
    - Password security audit
    - JWT security review

  # Status
  status: "completed"
  blocked: false

  # Gate Information
  gate_info:
    blocks_status: "production_ready"  # What status this gate blocks
    threshold: 85                       # Minimum score to pass
    score: 92                           # Actual score achieved
    is_blocking: true                   # Is this a blocking gate?

  # Timing
  created: "2025-01-25T10:00:00Z"
  started: "2025-01-25T18:00:00Z"
  completed: "2025-01-25T19:30:00Z"

  # Assignment
  assigned_agent: "security-auditor"
  priority: "critical"

  # Complexity & Size
  estimated_tokens: 6000
  actual_tokens: 5500
  complexity: "medium"

  # Dependencies (HIGHLY ISOLATED - only depends on sprint status)
  dependencies:
    - type: "sprint"
      target_id: "backend-1"
      target_status: "production_gate_check"
      reason: "Sprint must be ready for production gates"

  # Audit results
  audit_results:
    issues_found: 0
    issues_fixed: 0
    recommendations:
      - "Consider adding rate limiting to prevent brute force"
      - "Implement password rotation policy"

  # Metadata
  metadata:
    token_efficiency: 0.92
    duration_hours: 1.5
    last_updated: "2025-01-25T19:30:00Z"
```

### Key Design Decisions

**Task as Context-Window Unit:**
- Sized to fit within model's context window
- No production concerns at task level
- Sprint handles production readiness

**Flat Structure:**
- Tasks are not nested in phases
- Optional `phase_label` for organization
- Single source of truth for task state

**Quality Gates are Tasks:**
- No separate structure
- Just tasks with `task_type: completion_gate | production_gate`
- Have `gate_info` object with threshold/score
- Highly isolated: only depend on sprint gate_check status

**Development Tasks vs Gate Tasks:**
- Development tasks: Build functionality, can depend on external tasks, **can serve as development gates for external sprints**
- Gate tasks: Quality validation, highly isolated, depend only on sprint status, **cannot be depended on by external sprints**

**Restricted Status Set:**
- Tasks cannot be `production_ready` or `deployed`
- These are sprint-level statuses
- Tasks are context-window units, not production units

---

## Status System

### Status Sets by Object Type

**Different objects have different available statuses:**

**Sprints and Tracks (Full Status Set):**
- `not_started`
- `in_progress`
- `paused`
- `completion_gate_check` **(NEW)**
- `completed`
- `production_gate_check` **(NEW)**
- `production_ready`
- `deployed`
- `won't_do`

**Tasks (Restricted Status Set):**
- `not_started`
- `in_progress`
- `paused`
- `completion_gate_check` **(NEW)**
- `completed`
- `won't_do`

**Roadmap (Full Status Set):**
- `not_started`
- `in_progress`
- `paused`
- `completion_gate_check`
- `completed`
- `production_gate_check`
- `production_ready`
- `deployed`
- `won't_do`

### Status Descriptions

| Status | Description | Applicable To |
|--------|-------------|---------------|
| `not_started` | Work not yet begun | All |
| `in_progress` | Active development | All |
| `paused` | Temporarily halted | All |
| `completion_gate_check` | Ready for completion gates to run | All |
| `completed` | Development finished, completion gates passed | All |
| `production_gate_check` | Ready for production gates to run | Sprint, Track, Roadmap |
| `production_ready` | Passed all production gates | Sprint, Track, Roadmap |
| `deployed` | Live in production | Sprint, Track, Roadmap |
| `won't_do` | Cancelled/deprioritized | All |

### Status Progression: Sprints/Tracks

```
not_started → in_progress → completion_gate_check → completed →
                ↓     ↑                                  ↓
              paused  ┘                                  ↓
                ↓                                        ↓
            won't_do                                     ↓
                                                         ↓
                                    production_gate_check → production_ready → deployed
                                             ↓
                                         won't_do
```

### Status Progression: Tasks

```
not_started → in_progress → completion_gate_check → completed
                ↓     ↑
              paused  ┘
                ↓
            won't_do
```

### Status Semantics by Level

**Task:**
- `completion_gate_check`: Task ready for gate checks (if it's a development task)
- `completed`: Task finished
- No `production_ready` or `deployed` (tasks are not production units)

**Sprint:**
- `completion_gate_check`: All development tasks complete, ready for completion gates
- `completed`: All development tasks + all completion gate tasks complete
- `production_gate_check`: Ready for production gates to run
- `production_ready`: All production gate tasks complete (sprint can be deployed)
- `deployed`: Sprint deployed to production

**Track:**
- `completion_gate_check`: All sprints in completion_gate_check or beyond
- `completed`: All sprints completed
- `production_gate_check`: All sprints production_ready, track ready for track-level gates
- `production_ready`: Track quality gates passed
- `deployed`: All track sprints deployed

**Roadmap:**
- `completed`: All tracks completed
- `production_ready`: All tracks production_ready
- `deployed`: Entire roadmap deployed

### Automatic Status Progression

**When all development tasks in sprint complete:**
```python
if all_development_tasks_completed(sprint):
    sprint.status = 'completion_gate_check'
    # Trigger completion gate tasks to run
```

**When all completion gate tasks pass:**
```python
if all_completion_gates_passed(sprint):
    sprint.status = 'completed'
    sprint.status = 'production_gate_check'  # Move immediately to production gate check
    # Trigger production gate tasks to run
```

**When all production gate tasks pass:**
```python
if all_production_gates_passed(sprint):
    sprint.status = 'production_ready'
    # Trigger version bump (PATCH)
```

**When all sprints in track reach production_ready:**
```python
if all_sprints_production_ready(track):
    track.status = 'production_ready'
    # Trigger version bump (MINOR)
```

**When all tracks complete:**
```python
if all_tracks_completed(roadmap):
    roadmap.status = 'completed'
```

---

## Gate System

The Vibey framework uses a sophisticated three-tier gate system to manage dependencies and quality.

### Key Distinction: Development Tasks vs Quality Gates

**Development Tasks** (`task_type: development`):
- Build functionality
- ✅ **Can serve as development gates for external sprints**
- External sprints CAN depend on these
- Example: Sprint B depends on "registration endpoint" task from Sprint A

**Quality Gate Tasks** (`task_type: completion_gate | production_gate`):
- Validate quality
- ❌ **Cannot be depended on by external sprints**
- Highly isolated
- Example: Sprint B CANNOT depend on "security audit" task from Sprint A

### Gate Types Overview

| Gate Type | Purpose | Scope | Can Be Depended On? |
|-----------|---------|-------|---------------------|
| **Development Gates** | External dependencies (dev tasks/sprints) | Cross-sprint/track | ✅ Yes (if dev task) |
| **Completion Gates** | Hygiene checks | Within sprint | ❌ No |
| **Production Gates** | Production readiness | Within sprint | ❌ No |

### Development Gates

**Development Gates** are external dependencies - development tasks or sprints outside the current sprint that must complete before the current sprint can progress.

**Key Principle:** All tasks with `task_type: development` can serve as development gates for external sprints.

**Characteristics:**
- External to the current sprint
- Can be **development tasks** from other sprints (task_type: development)
- Can be entire sprints
- Required for functionality
- **Development tasks can be depended on by other sprints**
- **Quality gate tasks CANNOT be depended on by other sprints**

**What Can Be a Development Gate:**
- ✅ Development tasks (task_type: development) from any sprint
- ✅ Entire sprints (which include dev tasks + quality gates internally)
- ❌ Quality gate tasks (task_type: completion_gate | production_gate)

**Example:**
```yaml
# Sprint backend-2 depends on sprint backend-1 (entire sprint)
development_gates:
  - type: "sprint"
    target_id: "backend-1"
    target_status: "completed"
    reason: "Order system needs authentication functionality"

# Sprint backend-2 depends on specific DEVELOPMENT task from another sprint
development_gates:
  - type: "task"
    target_id: "infrastructure-1-task-003"  # This is a development task
    target_status: "completed"
    reason: "Need database connection configured"

# ❌ INVALID: Cannot depend on quality gate task
development_gates:
  - type: "task"
    target_id: "infrastructure-1-gate-p001"  # This is a quality gate task
    target_status: "completed"
    reason: "WRONG! Cannot depend on quality gates"
```

**Rules:**
1. ✅ Can depend on **development tasks** from OTHER sprints
2. ✅ Can depend on completion of entire sprints
3. ❌ CANNOT depend on **quality gate tasks** of other sprints
4. ✅ Development tasks from any sprint can serve as development gates
5. ✅ Blocks sprint from progressing if not satisfied
6. ✅ External sprints depend on WHAT (development tasks/sprint completion), not HOW (quality gates)

---

### Quality Gates

**Quality Gates** are internal validation tasks that ensure the work product is high quality. They exist solely within the context of the current sprint.

**Key Principle:** Quality gates are **task objects**, not separate structures.

**Characteristics:**
- Exist within the sprint as tasks
- Highly isolated (minimal dependencies)
- Only depend on sprint being in correct gate_check status
- **Cannot be depended on by external sprints**
- Are themselves tasks with `task_type: completion_gate | production_gate`

**Rules:**
1. ✅ Quality gates are task objects within the sprint
2. ✅ Only dependency: sprint being in gate_check status
3. ❌ CANNOT depend on external tasks/sprints
4. ❌ CANNOT be depended on by external sprints
5. ✅ External sprints CAN depend on sprint completion (which internally waits for gates)
6. ✅ Highly isolated and self-contained

**Why Quality Gates Can't Be External Dependencies:**
This prevents the anti-pattern of Sprint B depending on "Sprint A's security audit". Instead:
- ✅ Sprint B depends on "Sprint A completion"
- ✅ Sprint A's completion internally depends on its security audit
- ✅ Clear boundary: quality is internal concern

---

### Completion Gates

**Completion Gates** are quality gates that block the sprint from reaching `completed` status.

**Purpose:** Hygiene checks - ensuring code quality, documentation, and CI/CD practices.

**Typical Completion Gates:**
- Documentation review
- Code style/linting
- Git commit hygiene
- CI/CD pipeline success
- Code review completion
- Basic functionality validation

**Example:**
```yaml
task:
  id: "backend-1-gate-c001"
  title: "Documentation Review"
  task_type: "completion_gate"

  gate_info:
    blocks_status: "completed"   # Blocks sprint from completing
    threshold: 90
    score: 95
    is_blocking: true

  # HIGHLY ISOLATED - only depends on sprint status
  dependencies:
    - type: "sprint"
      target_id: "backend-1"
      target_status: "completion_gate_check"
      reason: "Sprint must be ready for completion gates"
```

**Workflow:**
1. All development tasks in sprint complete
2. Sprint moves to `completion_gate_check` status
3. Completion gate tasks triggered
4. Completion gates run their checks
5. If all pass → sprint moves to `completed`
6. If any fail → sprint stays in `completion_gate_check`, gates must be re-run

---

### Production Gates

**Production Gates** are quality gates that block the sprint from reaching `production_ready` status.

**Purpose:** Production readiness checks - ensuring the code is safe and ready for production deployment.

**Typical Production Gates:**
- Security audit
- Unit test coverage (with thresholds)
- Integration testing
- Performance benchmarking
- Load testing
- Logging audit
- Data validation
- Error handling audit
- API documentation completeness

**Example:**
```yaml
task:
  id: "backend-1-gate-p001"
  title: "Security Audit"
  task_type: "production_gate"

  gate_info:
    blocks_status: "production_ready"   # Blocks sprint from production_ready
    threshold: 85
    score: 92
    is_blocking: true

  # HIGHLY ISOLATED - only depends on sprint status
  dependencies:
    - type: "sprint"
      target_id: "backend-1"
      target_status: "production_gate_check"
      reason: "Sprint must be ready for production gates"

  audit_results:
    issues_found: 0
    issues_fixed: 0
    recommendations:
      - "Consider adding rate limiting"
```

**Workflow:**
1. Sprint reaches `completed` status (all dev tasks + completion gates done)
2. Sprint moves to `production_gate_check` status
3. Production gate tasks triggered
4. Production gates run their checks
5. If all pass → sprint moves to `production_ready`
6. If any fail → sprint stays in `production_gate_check`, gates must be re-run

---

### Gate Isolation Rules

**Quality gates (completion + production) must be highly isolated:**

✅ **Allowed Dependencies:**
- Sprint being in correct gate_check status
- Nothing else

❌ **Prohibited Dependencies:**
- Other tasks (internal or external)
- Other sprints
- External systems (beyond what's needed for the check itself)

**Rationale:**
- Quality gates should validate the sprint's work, not depend on external work
- Isolation ensures gates can run whenever sprint is ready
- Prevents complex dependency chains through quality checks

---

### Gate vs. Development Dependency: Decision Tree

```
Does Sprint B need something from Sprint A?
│
├─ Need Sprint A's FUNCTIONALITY (entire sprint)?
│  └─ ✅ Development Gate: Sprint B depends on Sprint A completion
│
├─ Need Sprint A to be PRODUCTION READY?
│  └─ ✅ Development Gate: Sprint B depends on Sprint A production_ready
│
├─ Need a specific DEVELOPMENT TASK from Sprint A?
│  └─ ✅ Development Gate: Sprint B depends on specific development task
│      (e.g., backend-1-task-002 - implements registration endpoint)
│
├─ Need Sprint A's SECURITY AUDIT to pass?
│  └─ ❌ WRONG! Sprint B depends on Sprint A completion
│      (Sprint A's security audit is internal quality gate, cannot be depended on)
│
├─ Need Sprint A's TESTS to pass?
│  └─ ❌ WRONG! Sprint B depends on Sprint A completion
│      (Sprint A's tests are internal quality gates, cannot be depended on)
│
└─ Need Sprint A's QUALITY GATE TASK?
   └─ ❌ WRONG! Quality gate tasks cannot be depended on by external sprints
       (Only development tasks can serve as development gates)
```

**Key Principles:**
1. External sprints depend on **WHAT** was built (development tasks/completion), not **HOW** it was validated (quality gates)
2. **Development tasks** (task_type: development) can serve as development gates
3. **Quality gate tasks** (task_type: completion_gate | production_gate) cannot be depended on by external sprints

---

### Complete Example: Sprint with All Gate Types

```yaml
sprint:
  id: "backend-1"
  name: "User Authentication System"
  status: "production_ready"

  tasks:
    # DEVELOPMENT TASKS
    - id: "backend-1-task-001"
      title: "Create User schema"
      task_type: "development"
      status: "completed"

    - id: "backend-1-task-002"
      title: "Implement registration"
      task_type: "development"
      status: "completed"

    # COMPLETION GATE TASKS
    - id: "backend-1-gate-c001"
      title: "Documentation Review"
      task_type: "completion_gate"
      status: "completed"
      gate_info:
        blocks_status: "completed"
        threshold: 90
        score: 95

    - id: "backend-1-gate-c002"
      title: "Git/CI/CD Hygiene"
      task_type: "completion_gate"
      status: "completed"
      gate_info:
        blocks_status: "completed"
        threshold: 85
        score: 92

    # PRODUCTION GATE TASKS
    - id: "backend-1-gate-p001"
      title: "Security Audit"
      task_type: "production_gate"
      status: "completed"
      gate_info:
        blocks_status: "production_ready"
        threshold: 85
        score: 92

    - id: "backend-1-gate-p002"
      title: "Unit Test Coverage"
      task_type: "production_gate"
      status: "completed"
      gate_info:
        blocks_status: "production_ready"
        threshold: 80
        score: 95

  # DEVELOPMENT GATES (external dependencies)
  development_gates:
    - type: "sprint"
      target_id: "infrastructure-1"
      target_status: "completed"
      reason: "Need database setup"
```

**Status Progression for this Sprint:**
1. `not_started` → `in_progress` (development work begins)
2. `in_progress` → `completion_gate_check` (all dev tasks done)
3. `completion_gate_check` → `completed` (completion gates pass)
4. `completed` → `production_gate_check` (automatically transition)
5. `production_gate_check` → `production_ready` (production gates pass)
6. `production_ready` → `deployed` (manual deployment)

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

## Documentation Structure & Context Management

### Context Self-Containment Goal

**Fundamental Vibey Goal**: Provide framework for project state-management in AI coding workflows that gives the model sufficient context awareness without overwhelming the context window.

**Core Principle**: When working on `track-1, sprint-B, task-4`, the model should have sufficient context by reading ONLY:
1. `CLAUDE.md` (project context)
2. `ROADMAP.md` (roadmap overview)
3. `track-1.md` (track documentation)
4. `sprint-B.md` (sprint documentation)
5. `task-4.md` (task documentation)

**These 5 documents must be self-contained.** The model should NOT be required to read other track/sprint/task docs to execute the task.

**Hierarchy as Context Container:**
- Roadmap provides context for tracks
- Track provides context for sprints
- Sprint provides context for tasks
- Each object doc serves as table of contents for objects below it

---

### Current Design Assessment

#### ✅ Strengths (Supports Context Management)

**1. Clear Hierarchical Structure**
- 4-tier hierarchy: Roadmap → Track → Sprint → Task
- Each level naturally narrows scope
- Progression is explicit and predictable

**2. ID Scoping Enables Context Inference**
- Track-scoped sprint IDs: `backend-1` (clear ownership)
- Sprint-scoped task IDs: `backend-1-task-002` (clear location)
- Model can infer hierarchy from ID alone

**3. Quality Gates as Tasks (Excellent Design)**
- No separate structure to track
- Gates are just tasks within sprint
- No external gate references
- **Perfect self-containment** ✓

**4. Tracks as Parallelization Boundaries**
- Tracks designed to be independent
- Working on one track shouldn't require reading others
- Good isolation principle

**5. Flat Task Structure**
- No phase nesting = simpler context model
- All tasks at same level within sprint
- Easy to list in sprint doc

**Overall Structure Score**: 9/10

---

#### ❌ Weaknesses (Context Leakage)

**1. CRITICAL: Development Gates Create Context Leakage**

Current design allows cross-sprint task dependencies:

```yaml
# Task in backend-2
task:
  id: "backend-2-task-005"
  dependencies:
    - type: "task"
      target_id: "infrastructure-1-task-003"  # EXTERNAL SPRINT!
      reason: "Need database connection configured"
```

**Problem**: To work on `backend-2-task-005`, must the model read:
- ❌ `track-infrastructure.md`?
- ❌ `sprint-infrastructure-1.md`?
- ❌ `task-infrastructure-1-task-003.md`?

**This is 8 documents instead of 5. Context explosion!**

**2. Sprint-Level Development Gates Also Leak**

```yaml
sprint:
  id: "backend-2"
  development_gates:
    - type: "sprint"
      target_id: "backend-1"
      target_status: "completed"
```

**Problem**: To work on `backend-2`, must the model read `sprint-backend-1.md`?

**3. Track-Level Dependencies Leak**

```yaml
track:
  id: "backend"
  dependencies:
    - type: "track"
      target_id: "infrastructure"
```

**Problem**: Working on backend track, must the model read `track-infrastructure.md`?

**4. No Documentation Structure Specification**

Current design defines:
- ✅ Data structures (YAML schema)
- ❌ Documentation structure (what's IN the markdown docs)
- ❌ Context inheritance rules (what child inherits from parent)
- ❌ Dependency summary requirements

**5. No Token Budget Guidance**

- How large should each doc be?
- What's the context budget for: CLAUDE.md + ROADMAP + track + sprint + task?
- Is there room for dependency summaries?

**6. Cascading Dependencies**

If `infrastructure-1-task-003` itself has dependencies:
```
infrastructure-1-task-003 depends on:
  → infrastructure-1-task-001
    → infrastructure-1-task-000
```

Now you need even MORE docs to understand the full dependency chain.

**7. No "What" vs "How" Boundary**

When depending on external task, need to know:
- ✅ **What** it provides (interface, deliverables)
- ❌ **How** it's implemented (internal details)

Current design doesn't distinguish these.

**Overall Context Management Score**: 3/10

---

### Context Budget Guidelines

**Total Context Budget**: ~10,000 tokens for all documentation
- Leaves room for code, examples, system prompts

**Token Allocation per Document:**

| Document | Target Tokens | Max Tokens | Purpose |
|----------|---------------|------------|---------|
| `CLAUDE.md` | 500 | 1000 | Project overview, tech stack, conventions |
| `ROADMAP.md` | 800 | 1500 | Roadmap status, track summaries |
| `track-{id}.md` | 1200 | 2000 | Track scope, external deps, sprint TOC |
| `sprint-{id}.md` | 2000 | 3000 | Sprint goal, dev gates, task TOC |
| `task-{id}.md` | 1500 | 2500 | Task objective, dep summaries, guidance |
| **Total** | **6000** | **10000** | Full context hierarchy |

**Remaining Budget**: 4,000 - 14,000 tokens for:
- Code files
- Error messages
- Test output
- System prompts

**Design Principle**: Each document must stay within its token budget while providing complete context for its level.

---

### Mandatory Documentation Sections

#### ROADMAP.md

**Required Sections:**

```markdown
# Project Roadmap: {Project Name}

## Overview
- Project vision (2-3 sentences)
- Current version and status
- Target completion date

## Tracks (Table of Contents)

### Track: {track-id} - {Track Name}
**Status**: {status}
**Purpose**: One sentence description
**Deliverables**:
- Key deliverable 1
- Key deliverable 2

(Repeat for each track)

## Version History
- v1.0.0 - Initial release
- v1.1.0 - Track X completed

## Key Metrics
- Tracks: X/Y completed
- Sprints: X/Y production ready
- Overall progress: X%
```

**Token Target**: 800 tokens

---

#### track-{id}.md

**Required Sections:**

```markdown
# Track: {Track Name}

## Scope
- Track purpose (2-3 sentences)
- What's included in this track
- What's NOT included (out of scope)

## External Track Dependencies

(For each external track dependency)

### Dependency: Track {track-id}
**Status**: {status} ✓/→/○
**Provides**:
- Key deliverable 1
- Key deliverable 2

**Integration Points**:
- How we consume their work
- APIs/interfaces we use
- Configuration dependencies

**Why Needed**: One sentence rationale

## Sprints (Table of Contents)

### Sprint {track-id}-1: {Sprint Name}
**Status**: {status}
**Goal**: One sentence
**Deliverables**:
- Key deliverable 1
- Key deliverable 2

(Repeat for each sprint in track)

## Track Deliverables
- Overall what this track delivers
- Public APIs/interfaces
- Integration points for other tracks

## Progress
- Sprints: X/Y completed
- Tasks: X/Y completed
```

**Token Target**: 1200 tokens

**Key Principle**: External track dependencies MUST include "Provides" and "Integration Points" summaries. Model should NOT need to read external track docs.

---

#### sprint-{id}.md

**Required Sections:**

```markdown
# Sprint: {Sprint Name}

## Goal
- Sprint objective (2-3 sentences)
- Success criteria
- Target completion date

## Context from Track
- Track: {track-name}
- Track scope: One sentence reminder
- How this sprint fits in track

## Development Gates (External Dependencies)

(For each development gate)

### Gate: {dependency-type} {dependency-id}
**Status**: {status} ✓/→/○
**Provides**:
- Specific deliverable 1
- Specific deliverable 2

**Interface/API**:
```typescript
// Code showing how to use this dependency
import { thing } from '@/external';
```

**Why Needed**: One sentence rationale

## Tasks (Table of Contents)

### Development Tasks
- [ ] {task-id}: {Task title} ({status})
- [x] {task-id}: {Task title} (completed)

### Completion Gate Tasks
- [x] {gate-id}: Documentation Review (completed, score: 95)

### Production Gate Tasks
- [x] {gate-id}: Security Audit (completed, score: 92)
- [x] {gate-id}: Unit Test Coverage (completed, score: 95)

## Sprint Deliverables
- API endpoint: POST /api/auth/register
- Middleware: JWT authentication
- Database: User table with secure password hashing

## Progress
- Development tasks: X/Y completed
- Completion gates: X/Y passed
- Production gates: X/Y passed
```

**Token Target**: 2000 tokens

**Key Principle**: Development gates MUST include "Provides" and "Interface" summaries. Model should NOT need to read external sprint/task docs.

---

#### task-{id}.md

**Required Sections:**

```markdown
# Task: {Task Title}

## Context
- Sprint: {sprint-name}
- Sprint goal: One sentence reminder
- How this task contributes to sprint

## Objective
- What this task accomplishes (2-3 sentences)
- Success criteria
- Estimated complexity: simple/medium/complex

## Dependencies

(For each dependency - MUST include summary)

### Dependency: {dependency-id}
**Status**: {status} ✓/→
**Provides**:
- Specific thing 1
- Specific thing 2

**How to Use**:
```typescript
// Code showing interface
import { thing } from '@/path';
const result = thing.method();
```

**Why Needed**: One sentence

## Deliverables

### Code
- `src/path/file.ts` - Description
- `src/path/other.ts` - Description

### Tests
- `tests/path/file.test.ts` - Unit tests
- `tests/path/integration.test.ts` - Integration tests

### Documentation
- Update `docs/api.md` with new endpoint

## Implementation Guidance

### Approach
- Suggested implementation strategy
- Key considerations
- Edge cases to handle

### Code Structure
```typescript
// Rough structure/interface
export class Thing {
  method(): Result {
    // Implementation here
  }
}
```

### Testing Strategy
- What to test
- Test cases to cover

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests written and passing
- [ ] Code committed and pushed
```

**Token Target**: 1500 tokens

**Key Principle**: Dependencies MUST include "Provides" and "How to Use" summaries with code examples. Model should NOT need to read external task docs.

---

### Dependency Summary Requirements

**Core Rule**: Any development gate (external dependency) MUST be summarized in the dependent object's documentation.

#### For Task Dependencies

**When task A depends on task B (external sprint):**

```markdown
### Dependency: infrastructure-1-task-003 (Database Connection)
**Status**: Completed ✓
**Provides**:
- PostgreSQL connection pool configured
- Environment variable: `DATABASE_URL` set
- Connection available via `@/lib/database`

**How to Use**:
```typescript
import { db } from '@/lib/database';

// Connection pool ready to use
const result = await db.query('SELECT * FROM users');
```

**Why Needed**: Order processing requires database access to store orders
```

**Model should NOT read**: `task-infrastructure-1-task-003.md`

#### For Sprint Dependencies

**When sprint A depends on sprint B:**

```markdown
### Dependency: Sprint backend-1 (User Authentication)
**Status**: Production Ready ✓
**Provides**:
- POST /api/auth/register - User registration
- POST /api/auth/login - User login
- Middleware: `requireAuth` for protected routes
- JWT token validation

**How to Use**:
```typescript
import { requireAuth } from '@/middleware/auth';

app.post('/api/orders', requireAuth, async (req, res) => {
  // req.user is populated by requireAuth
  const userId = req.user.id;
});
```

**Why Needed**: Orders must be tied to authenticated users
```

**Model should NOT read**: `sprint-backend-1.md`

#### For Track Dependencies

**When track A depends on track B:**

```markdown
### Dependency: Track infrastructure
**Status**: Production Ready ✓
**Provides**:
- PostgreSQL database (connection string in env)
- Redis cache (connection string in env)
- Kubernetes cluster (deployment configs in /k8s)
- CI/CD pipelines (GitLab CI configured)

**Integration Points**:
- Database: Use `DATABASE_URL` environment variable
- Redis: Use `REDIS_URL` environment variable
- Deployment: Run `kubectl apply -f k8s/`

**Why Needed**: Backend services need database, cache, and deployment infrastructure
```

**Model should NOT read**: `track-infrastructure.md`

---

### Dependency Summary Template

**Standard template for all dependency summaries:**

```markdown
### Dependency: {type} {id} ({human-name})
**Status**: {status} {icon}
**Provides**:
- Concrete deliverable 1
- Concrete deliverable 2
- Concrete deliverable 3

**How to Use** / **Interface** / **Integration Points**:
```{language}
// Code example showing interface
// Should be copy-pasteable
```

**Why Needed**: One sentence rationale connecting to current object's goal
```

**Requirements**:
1. **Status**: Current status with visual indicator (✓ completed, → in progress, ○ not started)
2. **Provides**: Concrete, specific deliverables (not vague)
3. **Interface**: Code example showing HOW to use it
4. **Rationale**: Why this dependency exists

---

### Context Inheritance Rules

**What each level inherits from parent:**

#### Task Inherits from Sprint

**Automatic Context** (model can infer):
- Sprint goal
- Sprint deliverables
- Why this task exists (contributes to sprint)

**Must Be Repeated** (in task doc):
- Development gate summaries (from sprint, filtered to relevant ones)
- Specific guidance for this task

**Example**:
```markdown
# Task: Implement Registration Endpoint

## Context
- **Sprint**: backend-1 (User Authentication)
- **Sprint Goal**: Provide secure user authentication system
- **Task Contribution**: Registration is first step in auth flow
```

#### Sprint Inherits from Track

**Automatic Context**:
- Track scope
- Track purpose
- Overall track deliverables

**Must Be Repeated**:
- Track-level dependencies (if relevant to sprint)
- How sprint fits in track progression

**Example**:
```markdown
# Sprint: backend-1 (User Authentication)

## Context from Track
- **Track**: backend (Backend Services Development)
- **Track Scope**: Build all server-side APIs and business logic
- **Sprint Position**: First sprint in track, provides foundation for all backend features
```

#### Track Inherits from Roadmap

**Automatic Context**:
- Project vision
- Overall roadmap progress
- Version/release timeline

**Must Be Repeated**:
- Roadmap-level dependencies (if relevant to track)
- How track fits in overall project

**Example**:
```markdown
# Track: backend (Backend Services)

## Context from Roadmap
- **Project**: E-commerce Platform v2.0
- **Roadmap Vision**: Rebuild platform with modern architecture
- **Track Role**: Provide all server-side functionality for e-commerce operations
```

---

### Reference vs. Embed Guidelines

**When to EMBED (include full summary):**
- ✅ External dependencies (development gates)
- ✅ What dependency provides
- ✅ How to use/integrate with dependency
- ✅ Interface/API examples
- ✅ Parent context (sprint goal in task, track scope in sprint)

**When to REFERENCE (just link, model can read if needed):**
- ✅ Internal project documentation (architecture docs, conventions)
- ✅ External API documentation (third-party services)
- ✅ General knowledge resources

**NEVER reference (must embed or avoid):**
- ❌ Other task implementation details
- ❌ Other sprint internal structure
- ❌ Other track internal organization

**Example of Good Reference**:
```markdown
## Implementation Guidance
- Follow project conventions in `docs/CONVENTIONS.md`
- See database schema in `docs/DATABASE.md`
- API design principles in `docs/API_DESIGN.md`
```

Model CAN read these if needed, but they're project-wide docs, not context-window critical.

**Example of Bad Reference (missing summary)**:
```markdown
## Dependencies
- Depends on `infrastructure-1-task-003` (see that task doc for details)
```

❌ This forces model to read external task doc!

**Correct (with embedded summary)**:
```markdown
## Dependencies

### infrastructure-1-task-003: Database Connection Setup
**Provides**: PostgreSQL connection pool via `@/lib/database`
```

✅ Model has everything it needs!

---

### Context Leakage: Anti-Patterns

**Anti-Pattern 1: Bare Dependency References**

❌ **Bad**:
```yaml
dependencies:
  - type: "task"
    target_id: "infrastructure-1-task-003"
    reason: "Need database"
```

No summary = model must read external doc!

✅ **Good**:
```markdown
### Dependency: infrastructure-1-task-003
**Provides**: PostgreSQL connection via `@/lib/database`
**Interface**: `import { db } from '@/lib/database'`
```

---

**Anti-Pattern 2: Implementation Details in Dependencies**

❌ **Bad**:
```markdown
### Dependency: backend-1-task-002
**Provides**: User registration implementation using bcrypt hashing with 10 rounds, storing salted hashes in users table with email uniqueness constraint...
```

Too much "how", not enough "what"!

✅ **Good**:
```markdown
### Dependency: backend-1-task-002
**Provides**: User registration endpoint
**Interface**: `POST /api/auth/register` accepts email/password, returns JWT token
```

---

**Anti-Pattern 3: Cascading Dependency Chains**

❌ **Bad**:
```
Task A depends on Task B
Task B depends on Task C
Task C depends on Task D
```

To work on Task A, must understand B, C, and D!

✅ **Good**: Flatten dependencies at sprint planning. If Task A needs result of Task D, either:
1. Make Task D part of same sprint
2. Make sprint (not individual task) the dependency
3. Embed summary of what Task D provides

---

### Practical Examples

#### Example 1: Self-Contained Task Doc

```markdown
# Task: Implement Order Creation Endpoint

## Context
- **Sprint**: backend-2 (Order Management)
- **Sprint Goal**: Enable users to create and manage orders
- **Task Contribution**: Core functionality for order creation

## Objective
Create POST /api/orders endpoint that:
- Validates user authentication
- Validates product availability
- Creates order in database
- Returns order confirmation

## Dependencies

### Dependency: backend-1-task-002 (User Authentication)
**Status**: Completed ✓
**Provides**: JWT authentication middleware
**How to Use**:
```typescript
import { requireAuth } from '@/middleware/auth';

app.post('/api/orders', requireAuth, async (req, res) => {
  const userId = req.user.id; // Populated by middleware
});
```
**Why Needed**: Orders must be tied to authenticated users

### Dependency: backend-1-task-005 (Product Catalog API)
**Status**: Completed ✓
**Provides**: Product validation service
**How to Use**:
```typescript
import { ProductService } from '@/services/product';

const product = await ProductService.getById(productId);
if (!product || product.stock < quantity) {
  throw new Error('Product unavailable');
}
```
**Why Needed**: Must validate products exist and are in stock

### Dependency: infrastructure-1-task-003 (Database Connection)
**Status**: Completed ✓
**Provides**: PostgreSQL connection pool
**How to Use**:
```typescript
import { db } from '@/lib/database';

const order = await db.insert('orders', {
  user_id: userId,
  product_id: productId,
  quantity,
  total_price: product.price * quantity
});
```
**Why Needed**: Orders stored in database

## Deliverables
- `src/api/orders/create.ts` - Order creation endpoint
- `src/services/order.ts` - Order business logic
- `tests/api/orders/create.test.ts` - Endpoint tests
- `tests/services/order.test.ts` - Service tests

## Implementation Guidance
1. Use transaction for order creation (atomicity)
2. Validate product stock before creating order
3. Calculate total price server-side (don't trust client)
4. Return full order object with ID

## Acceptance Criteria
- [ ] Endpoint validates JWT authentication
- [ ] Endpoint validates product exists and has stock
- [ ] Order created in database with transaction
- [ ] Returns order object with ID
- [ ] Unit tests pass (90%+ coverage)
- [ ] Integration tests pass
```

**Analysis**: Model has EVERYTHING needed to implement this task without reading any external task docs. Total tokens: ~1800.

---

#### Example 2: Self-Contained Sprint Doc

```markdown
# Sprint: backend-2 (Order Management)

## Goal
Build complete order management system including order creation, retrieval, and status updates.

## Context from Track
- **Track**: backend (Backend Services)
- **Track Goal**: Provide all server-side APIs
- **Sprint Position**: Second sprint, builds on authentication from backend-1

## Development Gates

### Gate: Sprint backend-1 (User Authentication)
**Status**: Production Ready ✓
**Provides**:
- JWT authentication middleware (`requireAuth`)
- User session management
- User registration/login endpoints

**Integration**:
```typescript
import { requireAuth } from '@/middleware/auth';

// Use in protected routes
app.post('/api/orders', requireAuth, handler);
// req.user.id available in handler
```

**Why Needed**: Orders must be associated with authenticated users

### Gate: Sprint backend-1 (Product Catalog)
**Status**: Production Ready ✓
**Provides**:
- Product CRUD APIs
- Product validation service
- Product availability checks

**Integration**:
```typescript
import { ProductService } from '@/services/product';

const product = await ProductService.getById(id);
```

**Why Needed**: Orders reference products, must validate they exist

### Gate: Sprint infrastructure-1 (Database)
**Status**: Completed ✓
**Provides**:
- PostgreSQL connection pool
- Database migrations system
- Connection via environment variable

**Integration**:
```typescript
import { db } from '@/lib/database';

// Connection pool ready
const result = await db.query('SELECT...');
```

**Why Needed**: Orders stored in database

## Tasks

### Development Tasks
- [x] backend-2-task-001: Design order database schema (completed)
- [ ] backend-2-task-002: Implement order creation endpoint (in progress)
- [ ] backend-2-task-003: Implement order retrieval endpoints (not started)
- [ ] backend-2-task-004: Implement order status updates (not started)

### Completion Gate Tasks
- [ ] backend-2-gate-c001: Documentation review
- [ ] backend-2-gate-c002: API documentation complete

### Production Gate Tasks
- [ ] backend-2-gate-p001: Security audit
- [ ] backend-2-gate-p002: Unit test coverage (80%+)
- [ ] backend-2-gate-p003: Integration tests

## Sprint Deliverables
- POST /api/orders - Create order
- GET /api/orders/:id - Get order details
- GET /api/orders - List user's orders
- PATCH /api/orders/:id/status - Update order status
- Order database tables with proper relations
- Comprehensive test suite

## Progress
- Development tasks: 1/4 completed
- Completion gates: 0/2 passed
- Production gates: 0/3 passed
```

**Analysis**: Model has EVERYTHING needed to understand this sprint and work on any task within it, without reading backend-1 or infrastructure-1 docs. Total tokens: ~2100.

---

### Assessment Summary

| Aspect | Current State | With Improvements |
|--------|---------------|-------------------|
| **Structural Design** | ✅ Excellent (9/10) | ✅ Excellent (9/10) |
| **ID Scoping** | ✅ Excellent (10/10) | ✅ Excellent (10/10) |
| **Quality Gates** | ✅ Excellent (10/10) | ✅ Excellent (10/10) |
| **Development Gate Context** | ❌ Poor (3/10) | ✅ Good (8/10) |
| **Doc Structure Spec** | ❌ Missing (0/10) | ✅ Complete (10/10) |
| **Context Inheritance** | ❌ Undefined (0/10) | ✅ Defined (9/10) |
| **Token Budget** | ❌ No guidance (0/10) | ✅ Specified (10/10) |
| **Dependency Summaries** | ❌ Not required (0/10) | ✅ Required (10/10) |
| **Overall** | ⚠️ 4/10 | ✅ 9/10 |

**Conclusion**: The roadmap object hierarchy STRUCTURE is excellent for context management, but the design lacked SPECIFICATION of how to achieve context self-containment. With these documentation requirements, the design now fully supports the goal of self-contained, context-aware development.

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
