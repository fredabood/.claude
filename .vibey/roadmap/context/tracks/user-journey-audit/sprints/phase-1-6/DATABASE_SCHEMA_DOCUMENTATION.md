# Database Schema Documentation

**Generated:** 2025-12-12
**Sprint:** Phase 1.6 - Database Artifact Audit
**Database:** SQLite 3.x

---

## Overview

| Component | Count |
|-----------|-------|
| Tables | 27 |
| Views | 21 |
| Triggers | 40 |
| Indexes | (system-generated on PKs) |

---

## Entity Relationship Diagram (ASCII)

```
                              roadmaps
                                 │
                                 │ 1:N
                                 ▼
                              tracks ──────────────────────────┐
                                 │                             │
                                 │ 1:N                    (polymorphic)
                                 ▼                             │
                              sprints ───────────────────┐     │
                                 │                       │     │
                                 │ 1:N              (polymorphic)
                                 ▼                       │     │
                              tasks ─────────────────────┼─────┤
                                                         │     │
    ┌────────────────────────────────────────────────────┼─────┘
    │                                                    │
    ▼                                                    ▼
entity_blocks          entity_blocked_by          entity_depends_on
entity_commits         entity_deliverables        assigned_agents
external_dependencies  quality_gates              standards
                       development_gates          deliverables
                       commits                    strategic_value

Summary Tables:                 Operational Tables:
├── track_summaries            ├── activity_log
├── sprint_summaries           ├── audit_trail
└── task_summaries             ├── sync_conflicts
                               ├── yaml_checksums
                               ├── database_state
                               └── version_history
```

---

## Core Entity Tables

### roadmaps

**Purpose:** Root container for all roadmap data. Single source of truth for the entire roadmap.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID identifier |
| name | TEXT | NOT NULL | Roadmap name |
| version | TEXT | NOT NULL | Semantic version (e.g., "2.5.0") |
| status | TEXT | NOT NULL, CHECK | Lifecycle status (10 values) |
| blocked | INTEGER | NOT NULL DEFAULT 0 | Is roadmap blocked |
| created | TEXT | NOT NULL | ISO 8601 timestamp |
| started | TEXT | | When work began |
| target_completion | TEXT | | Target completion date |
| completed | TEXT | | When completed |
| deployed | TEXT | | When deployed |
| version_strategy | TEXT | | JSON blob for version strategy |
| metadata | TEXT | | JSON metadata |

**Status Values:** `not_started`, `in_progress`, `paused`, `completion_gate_check`, `completed`, `production_gate_check`, `production_ready`, `deployed`, `wont_do`, `superseded`

**Relationships:**
- Parent of: `tracks`

**Triggers:**
- `trg_roadmap_started` - Auto-set started timestamp
- `trg_roadmap_completed` - Auto-set completed timestamp
- `trg_roadmap_deployed` - Auto-set deployed timestamp

---

### tracks

**Purpose:** Work stream container. Groups related sprints into a coherent work effort.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID identifier |
| roadmap_id | TEXT | NOT NULL, FK | Parent roadmap |
| name | TEXT | NOT NULL | Track name |
| status | TEXT | NOT NULL, CHECK | Lifecycle status (10 values) |
| blocked | INTEGER | NOT NULL DEFAULT 0 | Is track blocked |
| priority | TEXT | CHECK | Priority level (4 values) |
| created | TEXT | NOT NULL | ISO 8601 timestamp |
| started | TEXT | | When work began |
| completed | TEXT | | When completed |
| estimated_duration | TEXT | | Human-readable duration |
| dependencies_json | TEXT | | JSON array of dependencies |
| standards_json | TEXT | | JSON array of standards |
| strategic_value_json | TEXT | | JSON array of strategic value items |
| metadata | TEXT | | JSON metadata |

**Priority Values:** `critical`, `high`, `medium`, `low`

**Relationships:**
- Child of: `roadmaps`
- Parent of: `sprints`

**Triggers:**
- `trg_track_started` - Auto-set started timestamp
- `trg_track_completed` - Auto-set completed timestamp
- `trg_track_blocked_by_insert/delete` - Update blocked flag
- `trg_clear_track_blocker` - Clear blockers on completion
- `trg_track_summary_insert/update/delete` - Maintain denormalized summary
- `trg_activity_track_created/status` - Log activity

---

### sprints

**Purpose:** Time-boxed iteration within a track. Contains tasks to be completed.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID identifier |
| track_id | TEXT | NOT NULL, FK | Parent track |
| roadmap_id | TEXT | NOT NULL, FK | Ancestor roadmap |
| name | TEXT | NOT NULL | Sprint name |
| status | TEXT | NOT NULL, CHECK | Lifecycle status (10 values) |
| blocked | INTEGER | NOT NULL DEFAULT 0 | Is sprint blocked |
| blocked_reason | TEXT | | Explanation of blocking |
| created | TEXT | NOT NULL | ISO 8601 timestamp |
| started | TEXT | | When work began |
| completion_gate_check_at | TEXT | | Gate check timestamp |
| completed | TEXT | | When completed |
| production_gate_check_at | TEXT | | Production gate timestamp |
| production_ready_at | TEXT | | Production ready timestamp |
| deployed_at | TEXT | | When deployed |
| plan_file | TEXT | | Path to sprint plan file |
| description | TEXT | | Sprint description |
| goal | TEXT | | Sprint goal |
| estimated_duration | TEXT | | Duration estimate |
| notes | TEXT | | Additional notes |
| dependencies_json | TEXT | | JSON array |
| standards_json | TEXT | | JSON array |
| development_gates_json | TEXT | | JSON array |
| success_criteria_json | TEXT | | JSON array |
| risks_json | TEXT | | JSON array |
| deliverables_json | TEXT | | JSON array |
| quality_gates_json | TEXT | | JSON array |
| progress_json | TEXT | | JSON object for progress |
| tasks_json | TEXT | | JSON array of task summaries |
| metadata | TEXT | | JSON metadata |

**Relationships:**
- Child of: `tracks`
- Parent of: `tasks`

**Triggers:**
- `trg_sprint_started` - Auto-set started timestamp
- `trg_sprint_completed` - Auto-set completed timestamp
- `trg_sprint_blocked_by_insert/delete` - Update blocked flag
- `trg_clear_sprint_blocker` - Clear blockers on completion
- `trg_auto_start_sprint` - Start when first task starts
- `trg_sprint_summary_*` - Maintain denormalized summary
- `trg_activity_sprint_*` - Log activity
- `trg_prevent_complete_sprint_incomplete` - Block completion if tasks incomplete

---

### tasks

**Purpose:** Individual work item. The atomic unit of work tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID identifier |
| sprint_id | TEXT | NOT NULL, FK | Parent sprint |
| track_id | TEXT | NOT NULL, FK | Ancestor track |
| roadmap_id | TEXT | NOT NULL, FK | Ancestor roadmap |
| task_type | TEXT | NOT NULL, CHECK | Task type (10 values) |
| title | TEXT | NOT NULL | Task title |
| description | TEXT | | Task description |
| status | TEXT | NOT NULL, CHECK | Lifecycle status (7 values) |
| blocked | INTEGER | NOT NULL DEFAULT 0 | Is task blocked |
| created | TEXT | NOT NULL | ISO 8601 timestamp |
| started | TEXT | | When work began |
| completed | TEXT | | When completed |
| assigned_agent | TEXT | | Assigned agent name |
| priority | TEXT | CHECK | Priority level |
| phase_label | TEXT | | Phase label |
| estimated_tokens | INTEGER | | Token estimate |
| actual_tokens | INTEGER | | Actual tokens used |
| complexity | TEXT | CHECK | Complexity level |
| gate_info | TEXT | | JSON for gate tasks |
| audit_results | TEXT | | JSON audit results |
| commits_json | TEXT | | JSON array of commits |
| deliverables_json | TEXT | | JSON array of deliverables |
| dependencies_json | TEXT | | JSON array |
| standards_json | TEXT | | JSON array |
| assigned_agents_json | TEXT | | JSON array of agents |
| estimated_duration | TEXT | | Duration estimate |
| metadata | TEXT | | JSON metadata |

**Task Types:** `development`, `documentation`, `testing`, `research`, `review`, `infrastructure`, `design`, `gate`, `completion_gate`, `production_gate`

**Complexity Values:** `simple`, `medium`, `complex`

**Relationships:**
- Child of: `sprints`

**Triggers:**
- `trg_task_started` - Auto-set started timestamp
- `trg_task_completed` - Auto-set completed timestamp
- `trg_task_blocked_by_insert/delete` - Update blocked flag
- `trg_clear_task_blocker` - Clear blockers on completion
- `trg_auto_start_sprint` - Start sprint when task starts
- `trg_task_summary_*` - Maintain denormalized summary
- `trg_activity_task_*` - Log activity
- `trg_prevent_complete_blocked_task` - Block completion if blockers exist

---

## Supporting Entity Tables

### artifacts

**Purpose:** Generic artifact storage for files and assets.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID identifier |
| name | TEXT | NOT NULL | Artifact name |
| description | TEXT | | Artifact description |
| paths | TEXT | NOT NULL | JSON array of file paths |
| content_hash | TEXT | | Hash for verification |
| last_verified | TEXT | | Last verification timestamp |
| artifact_type | TEXT | NOT NULL, CHECK | Type classification |

**Artifact Types:** `code`, `test`, `config`, `documentation`, `context`, `agent`, `workflow`, `template`, `data`, `asset`, `schema`, `other`

---

### commits

**Purpose:** Git commit references linked to work items.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| commit_hash | TEXT | NOT NULL, UNIQUE | Git commit SHA |
| commit_message | TEXT | | Commit message |
| author | TEXT | | Commit author |
| committed_at | TEXT | | Timestamp |
| branch | TEXT | | Branch name |
| pr_number | INTEGER | | Pull request number |
| pr_url | TEXT | | Pull request URL |

---

### deliverables

**Purpose:** Output artifacts from completed work.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| description | TEXT | NOT NULL | Deliverable description |
| status | TEXT | CHECK | Status (pending/in_progress/completed) |
| completed_at | TEXT | | Completion timestamp |
| artifact_path | TEXT | | File path |
| artifact_url | TEXT | | URL reference |

---

### quality_gates

**Purpose:** Quality checkpoints for tracks and sprints.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| owner_type | TEXT | NOT NULL, CHECK | Entity type (track/sprint) |
| owner_id | TEXT | NOT NULL | Entity ID |
| name | TEXT | NOT NULL | Gate name |
| description | TEXT | | Gate description |
| threshold | INTEGER | NOT NULL DEFAULT 100 | Pass threshold % |
| blocking | INTEGER | NOT NULL DEFAULT 1 | Is gate blocking |
| status | TEXT | NOT NULL DEFAULT 'not_run', CHECK | Gate status |
| score | INTEGER | | Achieved score |
| last_run_at | TEXT | | Last run timestamp |
| last_run_by | TEXT | | Who ran the gate |
| metadata | TEXT | | JSON metadata |

**Status Values:** `not_run`, `running`, `passed`, `failed`, `superseded`

---

### development_gates

**Purpose:** Development checkpoints for sprints.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| sprint_id | TEXT | NOT NULL, FK | Sprint reference |
| name | TEXT | NOT NULL | Gate name |
| description | TEXT | | Gate description |
| status | TEXT | CHECK | Status (pending/resolved/blocked) |
| resolved_at | TEXT | | Resolution timestamp |

---

### standards

**Purpose:** Coding/documentation standards for tracks and sprints.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| owner_type | TEXT | NOT NULL, CHECK | Entity type (track/sprint) |
| owner_id | TEXT | NOT NULL | Entity ID |
| standard_name | TEXT | NOT NULL | Standard name |
| standard_url | TEXT | | Reference URL |
| description | TEXT | | Description |

---

### strategic_value

**Purpose:** Strategic value statements for tracks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| track_id | TEXT | NOT NULL, FK | Track reference |
| value_statement | TEXT | NOT NULL | Value statement |
| sort_order | INTEGER | DEFAULT 0 | Display order |

---

### assigned_agents

**Purpose:** Agent assignments to entities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| owner_type | TEXT | NOT NULL, CHECK | Entity type |
| owner_id | TEXT | NOT NULL | Entity ID |
| agent_name | TEXT | NOT NULL | Agent name |
| role | TEXT | | Agent role |
| assigned_at | TEXT | | Assignment timestamp |

---

### external_dependencies

**Purpose:** External resources that entities depend on.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| owner_type | TEXT | NOT NULL, CHECK | Entity type |
| owner_id | TEXT | NOT NULL | Entity ID |
| name | TEXT | NOT NULL | Dependency name |
| description | TEXT | | Description |
| status | TEXT | CHECK | Status (pending/resolved/blocked) |
| resolved_at | TEXT | | Resolution timestamp |
| metadata | TEXT | | JSON metadata |

---

## Relationship Tables

### entity_blocks

**Purpose:** "A blocks B" relationships between entities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| blocker_type | TEXT | NOT NULL, CHECK | Blocker entity type |
| blocker_id | TEXT | NOT NULL | Blocker entity ID |
| blocked_type | TEXT | NOT NULL, CHECK | Blocked entity type |
| blocked_id | TEXT | NOT NULL | Blocked entity ID |
| reason | TEXT | | Blocking reason |

**Entity Types:** `track`, `sprint`, `task`

---

### entity_blocked_by

**Purpose:** "A is blocked by B" relationships with status tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| blocked_type | TEXT | NOT NULL, CHECK | Blocked entity type |
| blocked_id | TEXT | NOT NULL | Blocked entity ID |
| blocker_type | TEXT | NOT NULL, CHECK | Blocker entity type |
| blocker_id | TEXT | NOT NULL | Blocker entity ID |
| required_status | TEXT | DEFAULT 'completed' | Status blocker must reach |
| blocks_transition_to | TEXT | DEFAULT 'in_progress' | Blocked transition |
| reason | TEXT | | Blocking reason |

---

### entity_depends_on

**Purpose:** Dependency relationships between entities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| dependent_type | TEXT | NOT NULL, CHECK | Dependent entity type |
| dependent_id | TEXT | NOT NULL | Dependent entity ID |
| dependency_type | TEXT | NOT NULL, CHECK | Dependency entity type |
| dependency_id | TEXT | NOT NULL | Dependency entity ID |
| reason | TEXT | | Dependency reason |

---

### entity_commits

**Purpose:** Many-to-many relationship between entities and commits.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| owner_type | TEXT | NOT NULL, CHECK | Entity type |
| owner_id | TEXT | NOT NULL | Entity ID |
| commit_id | INTEGER | NOT NULL, FK | Commit reference |

---

### entity_deliverables

**Purpose:** Many-to-many relationship between entities and deliverables.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| owner_type | TEXT | NOT NULL, CHECK | Entity type |
| owner_id | TEXT | NOT NULL | Entity ID |
| deliverable_id | INTEGER | NOT NULL, FK | Deliverable reference |

---

## Summary/Cache Tables

### track_summaries

**Purpose:** Denormalized track data for fast queries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| roadmap_id | TEXT | Roadmap reference |
| track_id | TEXT | Track reference |
| name | TEXT | Track name |
| status | TEXT | Track status |
| priority | TEXT | Track priority |

**Maintained by triggers:** `trg_track_summary_*`

---

### sprint_summaries

**Purpose:** Denormalized sprint data for fast queries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| track_id | TEXT | Track reference |
| sprint_id | TEXT | Sprint reference |
| name | TEXT | Sprint name |
| status | TEXT | Sprint status |
| estimated_duration | TEXT | Duration estimate |
| tasks_count | INTEGER | Number of tasks |
| started | TEXT | Start timestamp |

**Maintained by triggers:** `trg_sprint_summary_*`

---

### task_summaries

**Purpose:** Denormalized task data for fast queries.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| sprint_id | TEXT | Sprint reference |
| task_id | TEXT | Task reference |
| title | TEXT | Task title |
| status | TEXT | Task status |
| task_type | TEXT | Task type |
| gate_info | TEXT | Gate info JSON |

**Maintained by triggers:** `trg_task_summary_*`

---

## Operational Tables

### activity_log

**Purpose:** Event log for all roadmap activity.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| roadmap_id | TEXT | Roadmap reference |
| event_type | TEXT | Event type |
| event_description | TEXT | Event description |
| occurred_at | TEXT | Timestamp |
| entity_type | TEXT | Affected entity type |
| entity_id | TEXT | Affected entity ID |
| actor | TEXT | Who caused the event |
| old_state | TEXT | JSON snapshot before |
| new_state | TEXT | JSON snapshot after |
| metadata | TEXT | Additional data |

---

### audit_trail

**Purpose:** Field-level change audit for compliance.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| timestamp | TEXT | When changed |
| object_type | TEXT | Entity type |
| object_id | TEXT | Entity ID |
| field | TEXT | Changed field |
| old_value | TEXT | Previous value |
| new_value | TEXT | New value |
| changed_by | TEXT | Who made change |
| reason | TEXT | Why changed |
| commit_sha | TEXT | Git commit SHA |
| source | TEXT | Change source (cli/mcp/manual/automated/system) |

---

### yaml_checksums

**Purpose:** File change detection for sync.

| Column | Type | Description |
|--------|------|-------------|
| file_path | TEXT | PRIMARY KEY - File path |
| checksum | TEXT | SHA256 hash |
| loaded_at | TEXT | When loaded |
| file_size | INTEGER | File size |
| last_modified | TEXT | File modification time |

---

### database_state

**Purpose:** Singleton row for DB metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Always 1 |
| last_yaml_load | TEXT | Last rebuild timestamp |
| last_yaml_dump | TEXT | Last dump timestamp |
| is_dirty | INTEGER | Has uncommitted changes |
| source_commit | TEXT | Git commit at load |
| source_branch | TEXT | Git branch at load |
| schema_version | TEXT | Schema version |

---

### sync_conflicts

**Purpose:** Track YAML/DB sync conflicts.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| file_path | TEXT | Affected file |
| conflict_type | TEXT | Type of conflict |
| detected_at | TEXT | When detected |
| resolved_at | TEXT | When resolved |
| resolution | TEXT | How resolved |
| db_value | TEXT | Database value |
| yaml_value | TEXT | YAML value |
| description | TEXT | Conflict description |

**Conflict Types:** `yaml_modified`, `db_modified`, `both_modified`, `file_deleted`, `integrity_error`

**Resolution Types:** `use_db`, `use_yaml`, `merged`, `ignored`

---

### version_history

**Purpose:** Track roadmap version releases.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| roadmap_id | TEXT | Roadmap reference |
| version | TEXT | Version string |
| released_at | TEXT | Release timestamp |
| description | TEXT | Release description |
| changes | TEXT | JSON array of changes |

---

## Views (21 total)

### Progress Views

| View | Purpose |
|------|---------|
| v_roadmap_progress | Aggregate progress across all tracks |
| v_track_progress | Calculate track completion percentage |
| v_sprint_progress | Calculate sprint completion percentage |

### Summary Data Views

| View | Purpose |
|------|---------|
| v_track_summary_data | Track data for summary tables |
| v_sprint_summary_data | Sprint data with task counts |
| v_task_summary_data | Task data for summary tables |

### Aggregation Views

| View | Purpose |
|------|---------|
| v_track_sprint_summaries | Sprint summaries by track |
| v_sprint_commits | Commits aggregated by sprint |
| v_sprint_deliverables | Deliverables aggregated by sprint |
| v_sprint_assigned_agents | Agents by sprint |
| v_sprint_estimated_duration | Duration estimates by sprint |
| v_track_commits | Commits aggregated by track |
| v_track_deliverables | Deliverables aggregated by track |
| v_track_assigned_agents | Agents by track |

### Status Views

| View | Purpose |
|------|---------|
| v_blocked_entities | All blocked entities with details |
| v_unblocked_tasks | Tasks ready to work on |
| v_dependency_chain | Full dependency graph |
| v_failing_quality_gates | Gates below threshold |
| v_quality_gate_summary | Gate status aggregation |

### Activity Views

| View | Purpose |
|------|---------|
| v_recent_activity | Recent activity log entries |
| v_velocity_metrics | Work velocity calculations |

---

## Triggers (40 total)

### Timestamp Auto-Fill (9)
- `trg_roadmap_started`, `trg_roadmap_completed`, `trg_roadmap_deployed`
- `trg_track_started`, `trg_track_completed`
- `trg_sprint_started`, `trg_sprint_completed`
- `trg_task_started`, `trg_task_completed`

### Blocking System (9)
- `trg_task_blocked_by_insert`, `trg_task_blocked_by_delete`
- `trg_sprint_blocked_by_insert`, `trg_sprint_blocked_by_delete`
- `trg_track_blocked_by_insert`, `trg_track_blocked_by_delete`
- `trg_clear_task_blocker`, `trg_clear_sprint_blocker`, `trg_clear_track_blocker`

### Auto-Start Propagation (2)
- `trg_auto_start_sprint` - Start sprint when task starts
- `trg_auto_start_track` - Start track when sprint starts

### Summary Table Maintenance (12)
- `trg_task_summary_insert`, `trg_task_summary_update`, `trg_task_summary_delete`
- `trg_sprint_summary_insert`, `trg_sprint_summary_update`, `trg_sprint_summary_delete`
- `trg_sprint_summary_task_count_insert`, `trg_sprint_summary_task_count_delete`
- `trg_track_summary_insert`, `trg_track_summary_update`, `trg_track_summary_delete`

### Activity Logging (6)
- `trg_activity_task_created`, `trg_activity_task_status`
- `trg_activity_sprint_created`, `trg_activity_sprint_status`
- `trg_activity_track_created`, `trg_activity_track_status`

### Constraint Enforcement (3)
- `trg_prevent_complete_blocked_task`
- `trg_prevent_complete_sprint_incomplete`
- `trg_prevent_complete_track_incomplete`

---

## Schema Statistics

```sql
-- Record counts
SELECT 'roadmaps' as table_name, COUNT(*) as count FROM roadmaps
UNION ALL SELECT 'tracks', COUNT(*) FROM tracks
UNION ALL SELECT 'sprints', COUNT(*) FROM sprints
UNION ALL SELECT 'tasks', COUNT(*) FROM tasks;

-- Results (as of 2025-12-12):
-- roadmaps: 1
-- tracks: 41
-- sprints: 206
-- tasks: 1549
```

---

## Acceptance Criteria Checklist

- [x] All 27 tables documented
- [x] All 21 views documented
- [x] All 40 triggers documented
- [x] Column-level detail for each table
- [x] Relationships mapped
- [x] ERD diagram provided
