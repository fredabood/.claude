# B5: Progress Rollup Logic Audit

**Task ID:** 01KFXFAQBPQARFTKCJYYR7QXZF
**Phase:** B5: Core Data Model
**Date:** 2026-01-29

## Executive Summary

Complete documentation of the Vibey progress rollup system, which tracks completion percentage across four hierarchy levels (Roadmap, Track, Sprint, Task). The system uses a count-based approach where progress is calculated as `completed / total * 100`. Progress is stored in denormalized fields in YAML/SQLite and recalculated on status changes. Key finding: tasks are equally weighted (no complexity weighting), and Sprint progress separates development, completion_gate, and production_gate tasks for fine-grained tracking.

## Methodology

**Files Analyzed:**
- `vibey/roadmap/models/roadmap.py:24-45` - Roadmap Progress dataclass
- `vibey/roadmap/models/track.py:17-34` - TrackProgress dataclass
- `vibey/roadmap/models/sprint.py:17-60` - SprintProgress dataclass
- `vibey/roadmap/models/ticket/support.py:56-94` - Unified Progress model
- `vibey/roadmap/models/ticket/completable.py:170-196` - Progress computation from criteria

## Findings

### 2. Progress Calculation Table

| Level | Formula | Fields | Example |
|-------|---------|--------|---------|
| Task | Binary: 0% or 100% | N/A (leaf node) | completed → 100%, not_started → 0% |
| Sprint | `tasks_completed / tasks_total * 100` | development_tasks, completion_gate_tasks, production_gate_tasks | 8/10 tasks → 80% |
| Track | `tasks_completed / tasks_total * 100` | sprints_total, sprints_completed, tasks_total, tasks_completed | 45/60 tasks → 75% |
| Roadmap | `tasks_completed / tasks_total * 100` | tracks_total, tracks_completed, sprints_total, sprints_completed, tasks_total, tasks_completed | 150/200 tasks → 75% |

**Note:** Completion percentage is calculated from **task counts**, not sprint/track counts. This gives more granular progress indication.

### 3. Weighting Factors Table

| Factor | Applied To | Weight Impact | Configuration |
|--------|------------|---------------|---------------|
| Estimated Tokens | Task | Not used in progress | Could be used for weighted progress |
| Task Complexity | Task | Not used in progress | simple/medium/complex enum |
| Task Priority | Task | Not used in progress | critical/high/medium/low enum |
| Task Type | Sprint | Separate tracking | development vs completion_gate vs production_gate |
| Sprint Status | Track | Binary (0 or 1) | completed sprints counted |
| Track Status | Roadmap | Binary (0 or 1) | completed tracks counted |

**Current Implementation:** All tasks are **equally weighted** regardless of complexity, priority, or estimated tokens.

### 4. Recalculation Triggers Table

| Trigger | Event | Scope | Timing |
|---------|-------|-------|--------|
| Task completion | `status → completed` | Sprint, Track, Roadmap | Immediate (on save) |
| Task creation | New task added to sprint | Sprint, Track, Roadmap | On save |
| Task deletion | Task removed from sprint | Sprint, Track, Roadmap | On save |
| Task moved | Task moved to different sprint | Source sprint, Dest sprint, Track, Roadmap | On save |
| Sprint completion | `status → completed` | Track, Roadmap | Immediate (on save) |
| Track completion | `status → completed` | Roadmap | Immediate (on save) |
| Database rebuild | `vibey roadmap db rebuild` | All levels | Manual trigger |
| YAML sync | External YAML modification | Affected level + parents | On `db rebuild` |

### 5. Progress Storage Table

| Level | Storage Location | Cache Strategy | Staleness Handling |
|-------|------------------|----------------|-------------------|
| Task | N/A (computed from status) | No caching | Always current |
| Sprint | `sprint.progress` field in YAML + SQLite | Stored on save | Recompute on db rebuild |
| Track | `track.progress` field in YAML + SQLite | Stored on save | Recompute on db rebuild |
| Roadmap | `roadmap.progress` field in YAML + SQLite | Stored on save | Recompute on db rebuild |

**Storage Format (YAML):**
```yaml
progress:
  tasks_total: 34
  tasks_completed: 12
  sprints_total: 5
  sprints_completed: 1
  completion_percent: 35
```

**Storage Format (SQLite):**
```sql
-- Progress stored as JSON blob
SELECT progress_json FROM sprints WHERE id = ?;
-- Returns: {"tasks_total": 34, "tasks_completed": 12, ...}
```

### 6. Rollup Algorithm

```
ALGORITHM: Update Progress After Task Status Change
INPUT: task, old_status, new_status
OUTPUT: Updated progress at sprint, track, and roadmap levels

1. COMPUTE delta:
   IF new_status = 'completed' AND old_status != 'completed':
       completed_delta = +1
   ELIF old_status = 'completed' AND new_status != 'completed':
       completed_delta = -1
   ELSE:
       completed_delta = 0

2. IF completed_delta = 0: RETURN (no change)

3. UPDATE sprint progress:
   sprint = LOAD(task.sprint_id)

   # Determine task type category
   IF task.task_type IN ['completion_gate']:
       sprint.progress.completion_gate_tasks_completed += completed_delta
   ELIF task.task_type IN ['production_gate']:
       sprint.progress.production_gate_tasks_completed += completed_delta
   ELSE:
       sprint.progress.development_tasks_completed += completed_delta

   sprint.progress.tasks_completed += completed_delta
   sprint.progress.completion_percent = ROUND(
       sprint.progress.tasks_completed / sprint.progress.tasks_total * 100
   )
   SAVE(sprint)

4. UPDATE track progress:
   track = LOAD(sprint.track_id)
   track.progress.tasks_completed += completed_delta

   # Check if sprint became completed
   IF sprint.progress.tasks_completed = sprint.progress.tasks_total:
       track.progress.sprints_completed += 1

   track.progress.completion_percent = ROUND(
       track.progress.tasks_completed / track.progress.tasks_total * 100
   )
   SAVE(track)

5. UPDATE roadmap progress:
   roadmap = LOAD(track.roadmap_id)
   roadmap.progress.tasks_completed += completed_delta

   # Cascade sprint completion
   IF sprint_became_completed:
       roadmap.progress.sprints_completed += 1

   # Check if track became completed
   IF track.progress.sprints_completed = track.progress.sprints_total:
       roadmap.progress.tracks_completed += 1

   roadmap.progress.completion_percent = ROUND(
       roadmap.progress.tasks_completed / roadmap.progress.tasks_total * 100
   )
   SAVE(roadmap)


ALGORITHM: Recompute Progress From Scratch
INPUT: entity_id, entity_type
OUTPUT: Recomputed progress

1. IF entity_type = 'sprint':
   tasks = LOAD_TASKS(entity_id)
   progress = {
       development_tasks_total: COUNT(tasks WHERE type NOT IN gates),
       development_tasks_completed: COUNT(tasks WHERE type NOT IN gates AND status = completed),
       completion_gate_tasks_total: COUNT(tasks WHERE type = completion_gate),
       completion_gate_tasks_completed: COUNT(tasks WHERE type = completion_gate AND status = completed),
       production_gate_tasks_total: COUNT(tasks WHERE type = production_gate),
       production_gate_tasks_completed: COUNT(tasks WHERE type = production_gate AND status = completed),
   }
   progress.tasks_total = SUM of totals
   progress.tasks_completed = SUM of completed
   progress.completion_percent = tasks_completed / tasks_total * 100

2. IF entity_type = 'track':
   sprints = LOAD_SPRINTS(entity_id)
   progress = {
       sprints_total: COUNT(sprints),
       sprints_completed: COUNT(sprints WHERE status = completed),
       tasks_total: SUM(sprint.progress.tasks_total FOR sprint IN sprints),
       tasks_completed: SUM(sprint.progress.tasks_completed FOR sprint IN sprints),
   }
   progress.completion_percent = tasks_completed / tasks_total * 100

3. IF entity_type = 'roadmap':
   tracks = LOAD_TRACKS(entity_id)
   progress = {
       tracks_total: COUNT(tracks),
       tracks_completed: COUNT(tracks WHERE status = completed),
       sprints_total: SUM(track.progress.sprints_total FOR track IN tracks),
       sprints_completed: SUM(track.progress.sprints_completed FOR track IN tracks),
       tasks_total: SUM(track.progress.tasks_total FOR track IN tracks),
       tasks_completed: SUM(track.progress.tasks_completed FOR track IN tracks),
   }
   progress.completion_percent = tasks_completed / tasks_total * 100
```

### 7. Remote Aggregation Strategy Table

| Pattern | Consistency | Latency | Trade-offs |
|---------|-------------|---------|------------|
| Eager update | Strong | High | Update parent on every child change; network overhead |
| Lazy recompute | Eventual | Low | Recompute on read; may show stale progress |
| Batch update | Eventual | Medium | Periodic batch job; predictable staleness window |
| Event-driven | Eventual | Medium | Message queue for updates; at-least-once delivery |
| Hybrid | Tunable | Tunable | Eager for active entities, lazy for historical |

**Recommended Strategy for Remote Mode:**

1. **Event-driven updates** with Delta Lake change data capture (CDC)
2. **Staleness tolerance**: Progress can be 1-5 minutes stale without user impact
3. **On-demand refresh**: CLI command to force recalculation
4. **Materialized views**: Pre-compute progress aggregations for common queries

**Implementation:**
```sql
-- Delta Lake materialized view for sprint progress
CREATE OR REPLACE VIEW sprint_progress_live AS
SELECT
    s.id AS sprint_id,
    COUNT(CASE WHEN t.task_type NOT IN ('completion_gate', 'production_gate') THEN 1 END) AS dev_total,
    COUNT(CASE WHEN t.task_type NOT IN ('completion_gate', 'production_gate') AND t.status = 'completed' THEN 1 END) AS dev_completed,
    COUNT(CASE WHEN t.task_type = 'completion_gate' THEN 1 END) AS cg_total,
    COUNT(CASE WHEN t.task_type = 'completion_gate' AND t.status = 'completed' THEN 1 END) AS cg_completed,
    COUNT(CASE WHEN t.task_type = 'production_gate' THEN 1 END) AS pg_total,
    COUNT(CASE WHEN t.task_type = 'production_gate' AND t.status = 'completed' THEN 1 END) AS pg_completed
FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY s.id;
```

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| Progress stored as denormalized fields | Replicate same pattern in Delta Lake | S | High |
| No weighting factors | Consider adding estimated_tokens weighting in remote mode | M | Low |
| Sprint separates task types | Maintain same separation in Delta Lake progress | S | High |
| Recompute on every save | Use event-driven updates in remote mode | M | Critical |
| Progress can become stale | Accept eventual consistency (1-5 min window) | S | Medium |
| Full recompute on db rebuild | Implement periodic reconciliation job | M | Medium |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Progress formula documented for all 4 levels: PASS (Task, Sprint, Track, Roadmap)
- [x] >= 4 recalculation triggers identified: PASS (8 triggers documented)
- [x] Rollup algorithm includes pseudocode or flowchart: PASS (2 algorithms)
- [x] Remote aggregation strategy addresses eventual consistency: PASS (5 patterns with trade-offs)

## References

- `vibey/roadmap/models/roadmap.py:24-45` - Roadmap Progress dataclass definition
- `vibey/roadmap/models/track.py:17-34` - TrackProgress dataclass definition
- `vibey/roadmap/models/sprint.py:17-60` - SprintProgress dataclass with task type separation
- `vibey/roadmap/models/ticket/support.py:56-94` - Unified Progress model
- `vibey/roadmap/models/ticket/completable.py:170-196` - Criteria-based progress computation
