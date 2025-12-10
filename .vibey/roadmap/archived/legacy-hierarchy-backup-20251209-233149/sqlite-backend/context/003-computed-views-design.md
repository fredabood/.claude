# Computed Views Design

**Task:** sqlite-backend-0-task-003
**Status:** In Progress
**Date:** 2025-11-26

## Overview

These views compute all progress aggregations automatically from task data.
They replace the 24 manually-maintained counter fields identified in Task 1.

---

## Sprint-Level Views

### v_sprint_progress

Computes all sprint progress metrics from tasks.

```sql
CREATE VIEW v_sprint_progress AS
SELECT
    s.id AS sprint_id,
    s.track_id,
    s.roadmap_id,
    s.name AS sprint_name,
    s.status AS sprint_status,

    -- Development tasks
    COUNT(CASE WHEN t.task_type = 'development' THEN 1 END)
        AS development_tasks_total,
    COUNT(CASE WHEN t.task_type = 'development' AND t.status = 'completed' THEN 1 END)
        AS development_tasks_completed,

    -- Completion gate tasks
    COUNT(CASE WHEN t.task_type = 'completion_gate' THEN 1 END)
        AS completion_gate_tasks_total,
    COUNT(CASE WHEN t.task_type = 'completion_gate' AND t.status = 'completed' THEN 1 END)
        AS completion_gate_tasks_completed,

    -- Production gate tasks
    COUNT(CASE WHEN t.task_type = 'production_gate' THEN 1 END)
        AS production_gate_tasks_total,
    COUNT(CASE WHEN t.task_type = 'production_gate' AND t.status = 'completed' THEN 1 END)
        AS production_gate_tasks_completed,

    -- Total tasks
    COUNT(t.id) AS tasks_total,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS tasks_completed,

    -- Completion percentage (avoid division by zero)
    CASE
        WHEN COUNT(t.id) = 0 THEN 0
        ELSE ROUND(
            (COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0) / COUNT(t.id)
        )
    END AS completion_percent,

    -- Blocked calculation
    CASE
        WHEN EXISTS (
            SELECT 1 FROM entity_blocked_by eb
            WHERE eb.blocked_type = 'sprint' AND eb.blocked_id = s.id
        ) THEN 1
        ELSE 0
    END AS is_blocked

FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY s.id, s.track_id, s.roadmap_id, s.name, s.status;
```

**Replaces:** 9 computed fields in sprint.yaml:
- progress.development_tasks_total
- progress.development_tasks_completed
- progress.completion_gate_tasks_total
- progress.completion_gate_tasks_completed
- progress.production_gate_tasks_total
- progress.production_gate_tasks_completed
- progress.tasks_total
- progress.tasks_completed
- progress.completion_percent

---

## Track-Level Views

### v_track_progress

Computes all track progress metrics from sprints.

```sql
CREATE VIEW v_track_progress AS
SELECT
    tr.id AS track_id,
    tr.roadmap_id,
    tr.name AS track_name,
    tr.status AS track_status,

    -- Sprint counts
    COUNT(DISTINCT s.id) AS sprints_total,
    COUNT(DISTINCT CASE WHEN s.status = 'completed' THEN s.id END) AS sprints_completed,

    -- Task aggregations (sum from sprint progress)
    COALESCE(SUM(sp.tasks_total), 0) AS tasks_total,
    COALESCE(SUM(sp.tasks_completed), 0) AS tasks_completed,

    -- Completion percentage
    CASE
        WHEN COALESCE(SUM(sp.tasks_total), 0) = 0 THEN 0
        ELSE ROUND(
            (COALESCE(SUM(sp.tasks_completed), 0) * 100.0) / COALESCE(SUM(sp.tasks_total), 0)
        )
    END AS completion_percent,

    -- Blocked calculation
    CASE
        WHEN EXISTS (
            SELECT 1 FROM entity_blocked_by eb
            WHERE eb.blocked_type = 'track' AND eb.blocked_id = tr.id
        ) THEN 1
        ELSE 0
    END AS is_blocked

FROM tracks tr
LEFT JOIN sprints s ON s.track_id = tr.id
LEFT JOIN v_sprint_progress sp ON sp.sprint_id = s.id
GROUP BY tr.id, tr.roadmap_id, tr.name, tr.status;
```

**Replaces:** 5 computed fields in track.yaml:
- progress.sprints_total
- progress.sprints_completed
- progress.tasks_total
- progress.tasks_completed
- progress.completion_percent

---

## Roadmap-Level Views

### v_roadmap_progress

Computes all roadmap progress metrics from tracks.

```sql
CREATE VIEW v_roadmap_progress AS
SELECT
    r.id AS roadmap_id,
    r.name AS roadmap_name,
    r.status AS roadmap_status,

    -- Track counts
    COUNT(DISTINCT tr.id) AS tracks_total,
    COUNT(DISTINCT CASE WHEN tr.status = 'completed' THEN tr.id END) AS tracks_completed,

    -- Sprint aggregations
    COALESCE(SUM(tp.sprints_total), 0) AS sprints_total,
    COALESCE(SUM(tp.sprints_completed), 0) AS sprints_completed,

    -- Task aggregations
    COALESCE(SUM(tp.tasks_total), 0) AS tasks_total,
    COALESCE(SUM(tp.tasks_completed), 0) AS tasks_completed,

    -- Completion percentage
    CASE
        WHEN COALESCE(SUM(tp.tasks_total), 0) = 0 THEN 0
        ELSE ROUND(
            (COALESCE(SUM(tp.tasks_completed), 0) * 100.0) / COALESCE(SUM(tp.tasks_total), 0)
        )
    END AS completion_percent,

    -- Blocked calculation
    CASE
        WHEN EXISTS (
            SELECT 1 FROM entity_blocked_by eb
            WHERE eb.blocked_type = 'roadmap' AND eb.blocked_id = r.id
        ) THEN 1
        ELSE 0
    END AS is_blocked

FROM roadmaps r
LEFT JOIN tracks tr ON tr.roadmap_id = r.id
LEFT JOIN v_track_progress tp ON tp.track_id = tr.id
GROUP BY r.id, r.name, r.status;
```

**Replaces:** 7 computed fields in roadmap.yaml:
- progress.tracks_total
- progress.tracks_completed
- progress.sprints_total
- progress.sprints_completed
- progress.tasks_total
- progress.tasks_completed
- progress.completion_percent

---

## Blocking & Dependency Views

### v_blocked_entities

Shows all currently blocked entities with their blockers.

```sql
CREATE VIEW v_blocked_entities AS
SELECT
    eb.blocked_type,
    eb.blocked_id,
    eb.blocker_type,
    eb.blocker_id,
    eb.reason,

    -- Blocker status (is the blocker resolved?)
    CASE eb.blocker_type
        WHEN 'task' THEN (SELECT status FROM tasks WHERE id = eb.blocker_id)
        WHEN 'sprint' THEN (SELECT status FROM sprints WHERE id = eb.blocker_id)
        WHEN 'track' THEN (SELECT status FROM tracks WHERE id = eb.blocker_id)
    END AS blocker_status,

    -- Is blocker completed?
    CASE eb.blocker_type
        WHEN 'task' THEN (SELECT status = 'completed' FROM tasks WHERE id = eb.blocker_id)
        WHEN 'sprint' THEN (SELECT status = 'completed' FROM sprints WHERE id = eb.blocker_id)
        WHEN 'track' THEN (SELECT status = 'completed' FROM tracks WHERE id = eb.blocker_id)
    END AS blocker_completed

FROM entity_blocked_by eb;
```

### v_unblocked_tasks

Tasks that are ready to start (no unresolved blockers).

```sql
CREATE VIEW v_unblocked_tasks AS
SELECT t.*
FROM tasks t
WHERE t.status = 'not_started'
  AND NOT EXISTS (
    SELECT 1
    FROM entity_blocked_by eb
    WHERE eb.blocked_type = 'task'
      AND eb.blocked_id = t.id
      AND (
        SELECT status FROM tasks WHERE id = eb.blocker_id
      ) != 'completed'
  )
  AND NOT EXISTS (
    SELECT 1
    FROM v_blocked_entities vb
    WHERE vb.blocked_type = 'sprint'
      AND vb.blocked_id = t.sprint_id
      AND vb.blocker_completed = 0
  );
```

### v_dependency_chain

Shows the full dependency graph for any entity.

```sql
-- Recursive CTE for dependency chains
CREATE VIEW v_dependency_chain AS
WITH RECURSIVE deps AS (
    -- Base case: direct dependencies
    SELECT
        dependent_type,
        dependent_id,
        dependency_type,
        dependency_id,
        1 AS depth,
        dependent_id || ' -> ' || dependency_id AS chain
    FROM entity_depends_on

    UNION ALL

    -- Recursive case: transitive dependencies
    SELECT
        d.dependent_type,
        d.dependent_id,
        edo.dependency_type,
        edo.dependency_id,
        d.depth + 1,
        d.chain || ' -> ' || edo.dependency_id
    FROM deps d
    JOIN entity_depends_on edo
        ON edo.dependent_type = d.dependency_type
        AND edo.dependent_id = d.dependency_id
    WHERE d.depth < 10  -- Prevent infinite loops
)
SELECT * FROM deps;
```

---

## Quality Gate Views (Track and Sprint Level)

### v_quality_gate_summary

Summary of quality gate status by owner (track or sprint).

```sql
CREATE VIEW v_quality_gate_summary AS
SELECT
    qg.owner_type,
    qg.owner_id,

    -- Entity name for context
    CASE qg.owner_type
        WHEN 'track' THEN (SELECT name FROM tracks WHERE id = qg.owner_id)
        WHEN 'sprint' THEN (SELECT name FROM sprints WHERE id = qg.owner_id)
    END AS owner_name,

    -- Counts by status
    COUNT(*) AS gates_total,
    COUNT(CASE WHEN qg.status = 'passed' THEN 1 END) AS gates_passed,
    COUNT(CASE WHEN qg.status = 'failed' THEN 1 END) AS gates_failed,
    COUNT(CASE WHEN qg.status = 'not_run' THEN 1 END) AS gates_pending,

    -- Any blocking gates failed?
    COUNT(CASE WHEN qg.blocking = 1 AND qg.status = 'failed' THEN 1 END) AS blocking_failures,

    -- Overall pass rate
    CASE
        WHEN COUNT(*) = 0 THEN 100
        ELSE ROUND(
            (COUNT(CASE WHEN qg.status = 'passed' THEN 1 END) * 100.0) / COUNT(*)
        )
    END AS pass_rate

FROM quality_gates qg
GROUP BY qg.owner_type, qg.owner_id;
```

### v_failing_quality_gates

Quality gates that are currently failing (track or sprint level).

```sql
CREATE VIEW v_failing_quality_gates AS
SELECT
    qg.owner_type,
    qg.owner_id,
    CASE qg.owner_type
        WHEN 'track' THEN (SELECT name FROM tracks WHERE id = qg.owner_id)
        WHEN 'sprint' THEN (SELECT name FROM sprints WHERE id = qg.owner_id)
    END AS owner_name,
    qg.name AS gate_name,
    qg.description,
    qg.threshold,
    qg.score,
    qg.blocking,
    qg.last_run_at

FROM quality_gates qg
WHERE qg.status = 'failed'
ORDER BY qg.blocking DESC, qg.owner_type, qg.last_run_at DESC;
```

---

## Activity & Reporting Views

### v_recent_activity

Recent activity across the roadmap.

```sql
CREATE VIEW v_recent_activity AS
SELECT
    al.id,
    al.roadmap_id,
    al.event_type,
    al.event_description,
    al.occurred_at,
    al.entity_type,
    al.entity_id,
    al.actor,

    -- Entity name for context
    CASE al.entity_type
        WHEN 'task' THEN (SELECT title FROM tasks WHERE id = al.entity_id)
        WHEN 'sprint' THEN (SELECT name FROM sprints WHERE id = al.entity_id)
        WHEN 'track' THEN (SELECT name FROM tracks WHERE id = al.entity_id)
        ELSE NULL
    END AS entity_name

FROM activity_log al
ORDER BY al.occurred_at DESC;
```

### v_velocity_metrics

Tracks completion velocity over time.

```sql
CREATE VIEW v_velocity_metrics AS
SELECT
    t.track_id,
    DATE(t.completed) AS completion_date,
    COUNT(*) AS tasks_completed,
    SUM(t.actual_tokens) AS tokens_used,
    AVG(
        JULIANDAY(t.completed) - JULIANDAY(t.started)
    ) * 24 AS avg_hours_per_task

FROM tasks t
WHERE t.status = 'completed'
  AND t.completed IS NOT NULL
GROUP BY t.track_id, DATE(t.completed)
ORDER BY completion_date DESC;
```

---

## Summary Tables Update Views

These views prepare data for the denormalized summary tables.

### v_track_summary_data

Data for track_summaries table.

```sql
CREATE VIEW v_track_summary_data AS
SELECT
    tr.roadmap_id,
    tr.id AS track_id,
    tr.name,
    tr.status,
    tr.priority
FROM tracks tr;
```

### v_sprint_summary_data

Data for sprint_summaries table.

```sql
CREATE VIEW v_sprint_summary_data AS
SELECT
    s.track_id,
    s.id AS sprint_id,
    s.name,
    s.status,
    s.metadata AS estimated_duration,  -- Extract from metadata
    (SELECT COUNT(*) FROM tasks t WHERE t.sprint_id = s.id) AS tasks_count,
    s.started
FROM sprints s;
```

### v_task_summary_data

Data for task_summaries table.

```sql
CREATE VIEW v_task_summary_data AS
SELECT
    t.sprint_id,
    t.id AS task_id,
    t.title,
    t.status,
    t.task_type,
    t.gate_info
FROM tasks t;
```

---

## View Summary

| View | Purpose | Replaces |
|------|---------|----------|
| v_sprint_progress | Sprint-level progress metrics | 9 computed fields |
| v_track_progress | Track-level progress metrics | 5 computed fields |
| v_roadmap_progress | Roadmap-level progress metrics | 7 computed fields |
| v_blocked_entities | All blocked entities with blockers | blocked flag computation |
| v_unblocked_tasks | Tasks ready to start | - |
| v_dependency_chain | Transitive dependency graph | - |
| v_quality_gate_summary | Gate status by entity | - |
| v_failing_quality_gates | Currently failing gates | - |
| v_recent_activity | Activity log with context | - |
| v_velocity_metrics | Completion velocity over time | - |
| v_track_summary_data | For track_summaries sync | - |
| v_sprint_summary_data | For sprint_summaries sync | - |
| v_task_summary_data | For task_summaries sync | - |

**Total computed fields replaced:** 21 (plus blocked flag at each level = 24)

---

## Performance Considerations

### Indexing Strategy

Critical indexes for view performance:

```sql
-- Task queries (most frequent)
CREATE INDEX idx_tasks_sprint ON tasks(sprint_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_type_status ON tasks(task_type, status);
CREATE INDEX idx_tasks_completed ON tasks(completed);

-- Sprint queries
CREATE INDEX idx_sprints_track ON sprints(track_id);
CREATE INDEX idx_sprints_status ON sprints(status);

-- Track queries
CREATE INDEX idx_tracks_roadmap ON tracks(roadmap_id);
CREATE INDEX idx_tracks_status ON tracks(status);

-- Blocking queries
CREATE INDEX idx_blocked_by_blocked ON entity_blocked_by(blocked_type, blocked_id);
CREATE INDEX idx_blocked_by_blocker ON entity_blocked_by(blocker_type, blocker_id);
```

### Query Optimization Notes

1. **Avoid nested view calls** - v_track_progress uses v_sprint_progress; for very large datasets, consider materialized tables updated by triggers instead.

2. **Limit recursive depth** - v_dependency_chain limits to 10 levels to prevent infinite loops.

3. **Use covering indexes** - Include frequently-selected columns in indexes.

4. **Partial indexes** - For filtered queries like "completed tasks", consider:
   ```sql
   CREATE INDEX idx_tasks_completed_only ON tasks(completed)
   WHERE status = 'completed';
   ```

---

## Next Steps

1. **Task 4:** Design triggers for automatic updates (summary tables, blocked flags)
2. **Task 5:** Design YAML synchronization strategy

---

**Document Version:** 1.0.0
**Views Defined:** 13
**Computed Fields Replaced:** 24
