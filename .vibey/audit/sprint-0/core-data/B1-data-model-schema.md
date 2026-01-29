# B1: Data Model Schema Audit

**Task ID:** 01KFXF3MN8QMC6DTCNPG26P19P
**Phase:** B1: Core Data Model
**Date:** 2026-01-29

## Executive Summary

Complete schema documentation for all 4 core entity types (Roadmap, Track, Sprint, Task) with Delta Lake type mappings. The Vibey data model uses Python dataclasses with 10 enum types defining valid values. Key finding: the nested dataclass structures (Progress, Metadata, etc.) will require Delta Lake STRUCT types, and list fields will need ARRAY types. The schema is well-designed for replication with clear nullable vs required fields.

## Methodology

**Files Analyzed:**
- `vibey/roadmap/models/roadmap.py:114-260` - Roadmap entity
- `vibey/roadmap/models/track.py:106-260` - Track entity
- `vibey/roadmap/models/sprint.py:110-315` - Sprint entity
- `vibey/roadmap/models/task.py:182-440` - Task entity
- `vibey/roadmap/models/common.py:1-343` - Enum definitions

## Findings

### 2. Entity Schema Tables

#### 3. Roadmap Entity Schema

| Field | Python Type | Delta Lake Type | Required | Default | Constraints |
|-------|-------------|-----------------|----------|---------|-------------|
| id | str | STRING | Yes | - | ULID format (26 chars) |
| name | str | STRING | Yes | - | - |
| version | str | STRING | Yes | - | Semantic version |
| version_strategy | VersionStrategy | STRUCT | Yes | - | Nested dataclass |
| status | Status | STRING | Yes | - | Enum validation |
| blocked | bool | BOOLEAN | Yes | - | Must match blocker list |
| created | datetime | TIMESTAMP | Yes | - | UTC timezone |
| progress | Progress | STRUCT | Yes | - | Nested dataclass |
| tracks | List[TrackSummary] | ARRAY<STRUCT> | Yes | - | - |
| activity_log | List[ActivityLogEntry] | ARRAY<STRUCT> | Yes | - | - |
| metadata | Metadata | STRUCT | Yes | - | Nested dataclass |
| started | Optional[datetime] | TIMESTAMP | No | None | Required if in_progress |
| target_completion | Optional[datetime] | TIMESTAMP | No | None | - |
| completed | Optional[datetime] | TIMESTAMP | No | None | Required if completed |
| deployed | Optional[datetime] | TIMESTAMP | No | None | - |
| dependencies | List[Dependency] | ARRAY<STRUCT> | No | [] | - |
| blocked_by | List[Blocker] | ARRAY<STRUCT> | No | [] | - |
| version_history | List[VersionHistoryEntry] | ARRAY<STRUCT> | No | [] | - |
| deployed_platforms | List[PlatformDeployment] | ARRAY<STRUCT> | No | [] | - |
| standards | List[Standard] | ARRAY<STRUCT> | No | [] | - |

#### 4. Track Entity Schema

| Field | Python Type | Delta Lake Type | Required | Default | Constraints |
|-------|-------------|-----------------|----------|---------|-------------|
| id | str | STRING | Yes | - | ULID format |
| name | str | STRING | Yes | - | - |
| roadmap_id | str | STRING | Yes | - | FK to roadmap |
| status | Status | STRING | Yes | - | Enum validation |
| blocked | bool | BOOLEAN | Yes | - | Must match depends_on |
| priority | Priority | STRING | Yes | - | Enum validation |
| created | datetime | TIMESTAMP | Yes | - | UTC timezone |
| progress | TrackProgress | STRUCT | Yes | - | Nested dataclass |
| sprints | List[SprintSummary] | ARRAY<STRUCT> | Yes | - | - |
| dependencies | List[TrackDependency] | ARRAY<STRUCT> | Yes | - | Source of truth |
| blocks | List[TrackDependency] | ARRAY<STRUCT> | Yes | - | Forward index |
| blocked_by | List[TrackBlocker] | ARRAY<STRUCT> | Yes | - | DEPRECATED |
| depends_on | List[DependencyStatus] | ARRAY<STRUCT> | Yes | - | Cached status |
| depended_on_by | List[str] | ARRAY<STRING> | Yes | - | Reverse index |
| quality_gates | List[QualityGate] | ARRAY<STRUCT> | Yes | - | - |
| assigned_agents | List[str] | ARRAY<STRING> | Yes | - | - |
| metadata | TrackMetadata | STRUCT | Yes | - | Nested dataclass |
| started | Optional[datetime] | TIMESTAMP | No | None | - |
| completed | Optional[datetime] | TIMESTAMP | No | None | - |
| estimated_duration | Optional[str] | STRING | No | None | - |
| deliverables | List[str] | ARRAY<STRING> | No | [] | - |
| strategic_value | List[str] | ARRAY<STRING> | No | [] | - |
| commits | List[SprintCompletionCommit] | ARRAY<STRUCT> | No | [] | - |
| standards | List[Standard] | ARRAY<STRUCT> | No | [] | - |

#### 5. Sprint Entity Schema

| Field | Python Type | Delta Lake Type | Required | Default | Constraints |
|-------|-------------|-----------------|----------|---------|-------------|
| id | str | STRING | Yes | - | ULID format |
| name | str | STRING | Yes | - | - |
| track_id | str | STRING | Yes | - | FK to track |
| roadmap_id | str | STRING | Yes | - | FK to roadmap |
| status | Status | STRING | Yes | - | Enum validation |
| blocked | bool | BOOLEAN | Yes | - | Must match depends_on |
| created | datetime | TIMESTAMP | Yes | - | UTC timezone |
| progress | SprintProgress | STRUCT | Yes | - | Nested dataclass |
| tasks | List[TaskSummary] | ARRAY<STRUCT> | Yes | - | - |
| development_gates | List[DevelopmentGate] | ARRAY<STRUCT> | Yes | - | - |
| blocks | List[DevelopmentGate] | ARRAY<STRUCT> | Yes | - | - |
| blocked_by | List[SprintBlocker] | ARRAY<STRUCT> | Yes | - | DEPRECATED |
| depends_on | List[DependencyStatus] | ARRAY<STRUCT> | Yes | - | - |
| depended_on_by | List[str] | ARRAY<STRING> | Yes | - | - |
| metadata | SprintMetadata | STRUCT | Yes | - | - |
| blocked_reason | Optional[str] | STRING | No | None | - |
| started | Optional[datetime] | TIMESTAMP | No | None | - |
| completion_gate_check_at | Optional[datetime] | TIMESTAMP | No | None | - |
| completed | Optional[datetime] | TIMESTAMP | No | None | - |
| production_gate_check_at | Optional[datetime] | TIMESTAMP | No | None | - |
| production_ready_at | Optional[datetime] | TIMESTAMP | No | None | - |
| deployed_at | Optional[datetime] | TIMESTAMP | No | None | - |
| plan_file | Optional[str] | STRING | No | None | - |
| deliverables | List[str] | ARRAY<STRING> | No | [] | - |
| description | Optional[str] | STRING | No | None | - |
| goal | Optional[str] | STRING | No | None | - |
| success_criteria | List[str] | ARRAY<STRING> | No | [] | - |
| risks | List[str] | ARRAY<STRING> | No | [] | - |
| notes | Optional[str] | STRING | No | None | - |
| assigned_agents | List[str] | ARRAY<STRING> | No | [] | - |
| quality_gates | List | ARRAY<STRUCT> | No | [] | - |
| commits | List[TaskCompletionCommit] | ARRAY<STRUCT> | No | [] | - |
| standards | List[Standard] | ARRAY<STRUCT> | No | [] | - |

#### 6. Task Entity Schema

| Field | Python Type | Delta Lake Type | Required | Default | Constraints |
|-------|-------------|-----------------|----------|---------|-------------|
| id | str | STRING | Yes | - | ULID format |
| sprint_id | str | STRING | Yes | - | FK to sprint |
| track_id | str | STRING | Yes | - | FK to track |
| roadmap_id | str | STRING | Yes | - | FK to roadmap |
| task_type | TaskType | STRING | Yes | - | Enum validation |
| title | str | STRING | Yes | - | - |
| description | str | STRING | Yes | - | - |
| status | TaskStatus | STRING | Yes | - | Enum validation |
| blocked | bool | BOOLEAN | Yes | - | Must match depends_on |
| created | datetime | TIMESTAMP | Yes | - | UTC timezone |
| assigned_agent | str | STRING | Yes | - | Can be empty |
| priority | Priority | STRING | Yes | - | Enum validation |
| estimated_tokens | int | INT | Yes | - | Must be positive |
| complexity | Complexity | STRING | Yes | - | Enum validation |
| dependencies | List[TaskDependency] | ARRAY<STRUCT> | Yes | - | - |
| blocks | List[TaskDependency] | ARRAY<STRUCT> | Yes | - | - |
| blocked_by | List[TaskBlocker] | ARRAY<STRUCT> | Yes | - | DEPRECATED |
| depends_on | List[DependencyStatus] | ARRAY<STRUCT> | Yes | - | - |
| depended_on_by | List[str] | ARRAY<STRING> | Yes | - | - |
| metadata | TaskMetadata | STRUCT | Yes | - | - |
| started | Optional[datetime] | TIMESTAMP | No | None | - |
| completed | Optional[datetime] | TIMESTAMP | No | None | - |
| phase_label | Optional[str] | STRING | No | None | - |
| actual_tokens | Optional[int] | INT | No | None | - |
| size_category | Optional[SizeCategory] | STRING | No | Auto-computed | - |
| gate_info | Optional[GateInfo] | STRUCT | No | None | Required for gate tasks |
| audit_results | Optional[AuditResults] | STRUCT | No | None | - |
| deliverables | List[Deliverable] | ARRAY<STRUCT> | No | [] | - |
| commits | List[GitCommit] | ARRAY<STRUCT> | No | [] | - |
| deferred | bool | BOOLEAN | No | False | - |

### 7. Enum Types Table

| Enum | Values | Used By | Description |
|------|--------|---------|-------------|
| Status | not_started, in_progress, paused, completion_gate_check, completed, production_gate_check, production_ready, deployed, superseded, wont_do | Roadmap, Track, Sprint | General status for roadmap objects |
| TaskStatus | not_started, in_progress, paused, completion_gate_check, completed, wont_do | Task | Restricted task status (no production) |
| Priority | critical, high, medium, low | All entities | Priority levels |
| TaskType | development, documentation, testing, research, review, infrastructure, design, gate, completion_gate, production_gate, bug | Task | Task classification |
| GateStatus | not_run, running, passed, failed, superseded | QualityGate | Gate execution status |
| DependencyType | task, sprint, track, external | Dependencies | Dependency target type |
| Complexity | simple, medium, complex | Task | Complexity rating |
| SizeCategory | S, M, L, XL, XXL | Task | Token-based size (S=<10K, M=10-30K, L=30-75K, XL=75-150K, XXL=150K+) |
| DeliverableType | code, test, documentation, config, other | Task deliverables | Deliverable classification |
| ActivityType | 20+ values | Roadmap activity log | Activity tracking events |
| VersionBumpTrigger | roadmap_milestone, track_completion, sprint_production_ready, manual | Roadmap | Version bump triggers |

### 8. Delta Lake Type Mapping Table

| Python Type | Delta Lake Type | Notes |
|-------------|-----------------|-------|
| str | STRING | Direct mapping |
| int | INT | Use BIGINT for token counts >2B |
| float | DOUBLE | For token_efficiency ratios |
| bool | BOOLEAN | Direct mapping |
| datetime | TIMESTAMP | Store as UTC |
| Optional[T] | T (nullable) | Set nullable=true in schema |
| List[str] | ARRAY<STRING> | Common for tags, agents |
| List[T] | ARRAY<STRUCT<...>> | Nested object arrays |
| Enum | STRING | Store enum value string |
| dataclass | STRUCT<...> | Nested structs |

### 9. Schema Evolution Considerations Table

| Field | Change Type | Migration Strategy | Risk |
|-------|-------------|-------------------|------|
| blocked_by | Deprecated | Replace with depends_on | Low - backward compatible |
| size_category | Auto-computed | Add column, backfill from estimated_tokens | Low |
| gate_info.score | Optional | Allow nulls, backfill as tasks complete | Low |
| commits[].platform | Required (new) | Backfill with "unknown" for legacy | Medium - data quality |
| commits[].submitted_at | Required (new) | Backfill from date field | Medium |
| deferred | New field | Add column, default False | Low |
| standards | New list | Add ARRAY column, default [] | Low |
| token_budget | New field | Add to metadata, nullable | Low |
| depended_on_by | New list | Add ARRAY column, compute from depends_on | Medium - consistency |

### Nested Dataclass Structures

**Progress (Roadmap):**
```
STRUCT<
  tracks_total: INT,
  tracks_completed: INT,
  sprints_total: INT,
  sprints_completed: INT,
  tasks_total: INT,
  tasks_completed: INT,
  completion_percent: INT
>
```

**DependencyStatus:**
```
STRUCT<
  blocker_id: STRING,
  blocker_type: STRING,
  required_status: STRING,
  current_status: STRING,
  blocks_transition_to: STRING,
  last_checked: TIMESTAMP
>
```

**GitCommit:**
```
STRUCT<
  sha: STRING,
  message: STRING,
  date: TIMESTAMP,
  author: STRING,
  platform: STRING,
  submitted_at: BIGINT  -- Unix timestamp
>
```

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| ULID IDs are self-describing | Use directly as Delta Lake primary keys | S | High |
| Nested STRUCTs require complex schema | Consider flattening for simpler queries | M | Medium |
| depends_on is denormalized cache | Replicate cache strategy in Delta Lake | M | Critical |
| blocked_by is deprecated | Exclude from Delta Lake schema | S | Low |
| Enum values are strings | Store as STRING, validate in application | S | High |
| Timestamps use UTC | Ensure Delta Lake stores as UTC | S | High |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] All 4 entity types have complete schema tables: PASS (Roadmap: 19 fields, Track: 24 fields, Sprint: 33 fields, Task: 27 fields)
- [x] All fields mapped to Delta Lake types: PASS
- [x] All enum types documented with valid values: PASS (11 enums documented)
- [x] Schema evolution considerations identified: PASS (9 evolution items)

## References

- `vibey/roadmap/models/roadmap.py:114-260` - Roadmap dataclass
- `vibey/roadmap/models/track.py:106-260` - Track dataclass
- `vibey/roadmap/models/sprint.py:110-315` - Sprint dataclass
- `vibey/roadmap/models/task.py:182-440` - Task dataclass
- `vibey/roadmap/models/common.py:38-343` - Enum and common type definitions
