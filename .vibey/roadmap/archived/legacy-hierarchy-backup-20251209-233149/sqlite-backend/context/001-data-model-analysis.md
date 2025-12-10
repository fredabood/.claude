# Data Model Analysis

**Task:** sqlite-backend-0-task-001
**Status:** In Progress
**Date:** 2025-11-26

## Current YAML Schema Overview

The Vibey roadmap system uses a hierarchical data model with 4 entity types:

```
Roadmap (1)
    └── Track (N)
            └── Sprint (N)
                    └── Task (N)
```

## Entity Definitions

### 1. Roadmap (`roadmap.yaml`)

**Location:** `.vibey/roadmap.yaml`

| Field | Type | Computed? | Description |
|-------|------|-----------|-------------|
| id | string | No | Unique identifier |
| name | string | No | Human-readable name |
| version | string | No | Semantic version |
| version_strategy | object | No | When to bump versions |
| status | enum | No | Current status |
| blocked | boolean | **Yes** | True if blocked_by not empty |
| created | datetime | No | Creation timestamp |
| started | datetime | No | When work started |
| target_completion | datetime | No | Target date |
| completed | datetime | No | Completion timestamp |
| deployed | datetime | No | Deployment timestamp |
| **progress.tracks_total** | integer | **Yes** | Count of tracks |
| **progress.tracks_completed** | integer | **Yes** | Count of completed tracks |
| **progress.sprints_total** | integer | **Yes** | Sum of sprints across tracks |
| **progress.sprints_completed** | integer | **Yes** | Sum of completed sprints |
| **progress.tasks_total** | integer | **Yes** | Sum of tasks across all sprints |
| **progress.tasks_completed** | integer | **Yes** | Sum of completed tasks |
| **progress.completion_percent** | integer | **Yes** | tasks_completed / tasks_total * 100 |
| tracks | array | No | Track summaries (denormalized) |
| dependencies | array | No | External dependencies |
| blocked_by | array | No | Current blockers |
| version_history | array | No | Version changelog |
| activity_log | array | No | Event log |
| metadata | object | No | Metadata fields |

**Computed Fields:** 7 (progress fields + blocked)

---

### 2. Track (`track.yaml`)

**Location:** `.vibey/roadmap/{track-id}/track.yaml`

| Field | Type | Computed? | Description |
|-------|------|-----------|-------------|
| id | string | No | Unique identifier |
| name | string | No | Human-readable name |
| roadmap_id | string | No | Parent roadmap reference |
| status | enum | No | Current status |
| blocked | boolean | **Yes** | True if blocked_by not empty |
| priority | enum | No | Priority level |
| created | datetime | No | Creation timestamp |
| started | datetime | No | When work started |
| completed | datetime | No | Completion timestamp |
| estimated_duration | string | No | Duration estimate |
| **progress.sprints_total** | integer | **Yes** | Count of sprints |
| **progress.sprints_completed** | integer | **Yes** | Count of completed sprints |
| **progress.tasks_total** | integer | **Yes** | Sum of tasks across sprints |
| **progress.tasks_completed** | integer | **Yes** | Sum of completed tasks |
| **progress.completion_percent** | integer | **Yes** | tasks_completed / tasks_total * 100 |
| sprints | array | No | Sprint summaries (denormalized) |
| dependencies | array | No | Track dependencies |
| blocks | array | No | What this track blocks |
| blocked_by | array | No | Current blockers |
| depends_on | array | No | What this track depends on |
| depended_on_by | array | No | What depends on this track |
| quality_gates | array | No | Track-level quality gates |
| assigned_agents | array | No | Assigned agents |
| deliverables | array | No | Expected deliverables |
| strategic_value | array | No | Strategic justification |
| commits | array | No | Related commits |
| standards | array | No | Applied standards |
| metadata | object | No | Metadata fields |

**Computed Fields:** 6 (progress fields + blocked)

---

### 3. Sprint (`sprint.yaml`)

**Location:** `.vibey/roadmap/{track-id}/{sprint-id}/sprint.yaml`

| Field | Type | Computed? | Description |
|-------|------|-----------|-------------|
| id | string | No | Unique identifier |
| name | string | No | Human-readable name |
| track_id | string | No | Parent track reference |
| roadmap_id | string | No | Parent roadmap reference |
| status | enum | No | Current status |
| blocked | boolean | **Yes** | True if blocked_by not empty |
| created | datetime | No | Creation timestamp |
| started | datetime | No | When work started |
| completion_gate_check_at | datetime | No | When entered completion check |
| completed | datetime | No | Completion timestamp |
| production_gate_check_at | datetime | No | When entered production check |
| production_ready_at | datetime | No | When became production ready |
| deployed_at | datetime | No | Deployment timestamp |
| **progress.development_tasks_total** | integer | **Yes** | Count of dev tasks |
| **progress.development_tasks_completed** | integer | **Yes** | Count of completed dev tasks |
| **progress.completion_gate_tasks_total** | integer | **Yes** | Count of completion gate tasks |
| **progress.completion_gate_tasks_completed** | integer | **Yes** | Count of completed completion gates |
| **progress.production_gate_tasks_total** | integer | **Yes** | Count of production gate tasks |
| **progress.production_gate_tasks_completed** | integer | **Yes** | Count of completed production gates |
| **progress.tasks_total** | integer | **Yes** | Total tasks (sum of above) |
| **progress.tasks_completed** | integer | **Yes** | Completed tasks (sum of above) |
| **progress.completion_percent** | integer | **Yes** | tasks_completed / tasks_total * 100 |
| tasks | array | No | Task summaries (denormalized) |
| development_gates | array | No | External dev dependencies |
| blocks | array | No | What this sprint blocks |
| blocked_by | array | No | Current blockers |
| depends_on | array | No | What this sprint depends on |
| depended_on_by | array | No | What depends on this sprint |
| plan_file | string | No | Path to sprint plan |
| deliverables | array | No | Expected deliverables |
| commits | array | No | Related commits |
| standards | array | No | Applied standards |
| metadata | object | No | Metadata fields |

**Computed Fields:** 10 (progress fields + blocked)

---

### 4. Task (`task.yaml`)

**Location:** `.vibey/roadmap/{track-id}/{sprint-id}/{task-id}/task.yaml`

| Field | Type | Computed? | Description |
|-------|------|-----------|-------------|
| id | string | No | Unique identifier |
| sprint_id | string | No | Parent sprint reference |
| track_id | string | No | Parent track reference |
| roadmap_id | string | No | Parent roadmap reference |
| task_type | enum | No | development/completion_gate/production_gate |
| title | string | No | Task title |
| description | string | No | Task description |
| status | enum | No | Current status |
| blocked | boolean | **Yes** | True if blocked_by not empty |
| created | datetime | No | Creation timestamp |
| started | datetime | No | When work started |
| completed | datetime | No | Completion timestamp |
| assigned_agent | string | No | Assigned agent |
| priority | enum | No | Priority level |
| phase_label | string | No | Optional phase label |
| estimated_tokens | integer | No | Token estimate |
| actual_tokens | integer | No | Actual tokens used |
| complexity | enum | No | Complexity rating |
| gate_info | object | No | Quality gate info (for gate tasks) |
| audit_results | object | No | Audit results (for gate tasks) |
| dependencies | array | No | Task dependencies |
| blocks | array | No | What this task blocks |
| blocked_by | array | No | Current blockers |
| deliverables | array | No | Task deliverables |
| commits | array | No | Related commits |
| metadata | object | No | Metadata fields |

**Computed Fields:** 1 (blocked only - tasks are the leaf nodes)

---

## Relationship Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         ROADMAP                                  │
│  progress.tracks_total = COUNT(tracks)                          │
│  progress.tracks_completed = COUNT(tracks WHERE completed)       │
│  progress.sprints_total = SUM(track.sprints_total)              │
│  progress.sprints_completed = SUM(track.sprints_completed)      │
│  progress.tasks_total = SUM(track.tasks_total)                  │
│  progress.tasks_completed = SUM(track.tasks_completed)          │
│  progress.completion_percent = tasks_completed/tasks_total*100  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          TRACK                                   │
│  progress.sprints_total = COUNT(sprints)                        │
│  progress.sprints_completed = COUNT(sprints WHERE completed)    │
│  progress.tasks_total = SUM(sprint.tasks_total)                 │
│  progress.tasks_completed = SUM(sprint.tasks_completed)         │
│  progress.completion_percent = tasks_completed/tasks_total*100  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          SPRINT                                  │
│  progress.dev_tasks_total = COUNT(tasks WHERE type=development) │
│  progress.dev_tasks_completed = COUNT(above WHERE completed)    │
│  progress.completion_gate_total = COUNT(tasks WHERE type=c_gate)│
│  progress.completion_gate_completed = COUNT(above WHERE done)   │
│  progress.production_gate_total = COUNT(tasks WHERE type=p_gate)│
│  progress.production_gate_completed = COUNT(above WHERE done)   │
│  progress.tasks_total = dev + completion + production           │
│  progress.tasks_completed = completed dev + c_gate + p_gate     │
│  progress.completion_percent = tasks_completed/tasks_total*100  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           TASK                                   │
│  (Source of truth - no computed aggregations)                   │
│  blocked = len(blocked_by) > 0                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Status Enums

### Task Status
- `not_started`
- `in_progress`
- `paused`
- `completion_gate_check`
- `completed`
- `won't_do`

### Sprint/Track/Roadmap Status
- `not_started`
- `in_progress`
- `paused`
- `completion_gate_check`
- `completed`
- `production_gate_check`
- `production_ready`
- `deployed`
- `won't_do`

### Task Types
- `development`
- `completion_gate`
- `production_gate`

### Priority Levels
- `critical`
- `high`
- `medium`
- `low`

### Complexity Levels
- `simple`
- `medium`
- `complex`

## Denormalized Data (Duplicated Across Files)

1. **Track summaries in roadmap.yaml** - id, name, status, priority
2. **Sprint summaries in track.yaml** - id, name, status, estimated_duration, tasks_count, started
3. **Task summaries in sprint.yaml** - id, title, status, task_type, gate_info

This denormalization is for quick reads but causes **consistency issues** when not updated together.

## Computed Fields Summary

| Entity | Computed Fields | Source of Computation |
|--------|-----------------|----------------------|
| Roadmap | 7 | Aggregations from tracks |
| Track | 6 | Aggregations from sprints |
| Sprint | 10 | Aggregations from tasks |
| Task | 1 | blocked_by array length |
| **Total** | **24** | |

## Key Findings

1. **Tasks are the source of truth** - All aggregations flow up from task status
2. **24 computed fields** must be manually synchronized currently
3. **Denormalized summaries** in parent files cause drift
4. **Status progression** has strict rules (can't skip states)
5. **Blocked flag** is computed from blocked_by array

## SQLite Design Implications

1. **Tasks table** is the primary source of truth
2. **Views** should compute all progress aggregations
3. **Triggers** should update blocked flag automatically
4. **No need to store** progress counters - compute them
5. **Foreign keys** can enforce referential integrity
6. **Denormalized summaries** can be generated at YAML dump time

---

**Next Step:** Design SQLite database schema (Task 2)
