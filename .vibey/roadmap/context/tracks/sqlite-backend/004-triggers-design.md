# Triggers Design

**Task:** sqlite-backend-0-task-004
**Status:** In Progress
**Date:** 2025-11-26

## Architecture Context

**Key Decision:** SQLite is the source of truth. All writes go through the database.
YAML files are read-only artifacts generated for git versioning.

This means triggers must handle:
1. **Automatic state transitions** (sprint/track completion)
2. **Blocked flag computation**
3. **Timestamp management**
4. **Summary table synchronization**
5. **Activity logging**

---

## Timestamp Triggers

### Auto-update metadata.last_updated

```sql
-- Tasks
CREATE TRIGGER trg_tasks_updated
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks
    SET metadata = json_set(
        COALESCE(metadata, '{}'),
        '$.last_updated',
        datetime('now')
    )
    WHERE id = NEW.id
      AND metadata != json_set(COALESCE(OLD.metadata, '{}'), '$.last_updated', datetime('now'));
END;

-- Sprints
CREATE TRIGGER trg_sprints_updated
AFTER UPDATE ON sprints
BEGIN
    UPDATE sprints
    SET metadata = json_set(
        COALESCE(metadata, '{}'),
        '$.last_updated',
        datetime('now')
    )
    WHERE id = NEW.id
      AND metadata != json_set(COALESCE(OLD.metadata, '{}'), '$.last_updated', datetime('now'));
END;

-- Tracks
CREATE TRIGGER trg_tracks_updated
AFTER UPDATE ON tracks
BEGIN
    UPDATE tracks
    SET metadata = json_set(
        COALESCE(metadata, '{}'),
        '$.last_updated',
        datetime('now')
    )
    WHERE id = NEW.id
      AND metadata != json_set(COALESCE(OLD.metadata, '{}'), '$.last_updated', datetime('now'));
END;
```

### Auto-set started timestamp

```sql
-- When task changes from not_started to in_progress
CREATE TRIGGER trg_task_started
AFTER UPDATE OF status ON tasks
WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
BEGIN
    UPDATE tasks SET started = datetime('now') WHERE id = NEW.id;
END;

-- When sprint changes from not_started to in_progress
CREATE TRIGGER trg_sprint_started
AFTER UPDATE OF status ON sprints
WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
BEGIN
    UPDATE sprints SET started = datetime('now') WHERE id = NEW.id;
END;

-- When track changes from not_started to in_progress
CREATE TRIGGER trg_track_started
AFTER UPDATE OF status ON tracks
WHEN OLD.status = 'not_started' AND NEW.status = 'in_progress' AND NEW.started IS NULL
BEGIN
    UPDATE tracks SET started = datetime('now') WHERE id = NEW.id;
END;
```

### Auto-set completed timestamp

```sql
-- When task changes to completed
CREATE TRIGGER trg_task_completed
AFTER UPDATE OF status ON tasks
WHEN NEW.status = 'completed' AND NEW.completed IS NULL
BEGIN
    UPDATE tasks SET completed = datetime('now') WHERE id = NEW.id;
END;

-- When sprint changes to completed
CREATE TRIGGER trg_sprint_completed
AFTER UPDATE OF status ON sprints
WHEN NEW.status = 'completed' AND NEW.completed IS NULL
BEGIN
    UPDATE sprints SET completed = datetime('now') WHERE id = NEW.id;
END;

-- When track changes to completed
CREATE TRIGGER trg_track_completed
AFTER UPDATE OF status ON tracks
WHEN NEW.status = 'completed' AND NEW.completed IS NULL
BEGIN
    UPDATE tracks SET completed = datetime('now') WHERE id = NEW.id;
END;
```

---

## Blocked Flag Triggers

### Update task blocked flag

```sql
-- When blocked_by entries change for a task
CREATE TRIGGER trg_task_blocked_by_insert
AFTER INSERT ON entity_blocked_by
WHEN NEW.blocked_type = 'task'
BEGIN
    UPDATE tasks SET blocked = 1 WHERE id = NEW.blocked_id;
END;

CREATE TRIGGER trg_task_blocked_by_delete
AFTER DELETE ON entity_blocked_by
WHEN OLD.blocked_type = 'task'
BEGIN
    UPDATE tasks
    SET blocked = (
        SELECT COUNT(*) > 0
        FROM entity_blocked_by
        WHERE blocked_type = 'task' AND blocked_id = OLD.blocked_id
    )
    WHERE id = OLD.blocked_id;
END;
```

### Update sprint blocked flag

```sql
CREATE TRIGGER trg_sprint_blocked_by_insert
AFTER INSERT ON entity_blocked_by
WHEN NEW.blocked_type = 'sprint'
BEGIN
    UPDATE sprints SET blocked = 1 WHERE id = NEW.blocked_id;
END;

CREATE TRIGGER trg_sprint_blocked_by_delete
AFTER DELETE ON entity_blocked_by
WHEN OLD.blocked_type = 'sprint'
BEGIN
    UPDATE sprints
    SET blocked = (
        SELECT COUNT(*) > 0
        FROM entity_blocked_by
        WHERE blocked_type = 'sprint' AND blocked_id = OLD.blocked_id
    )
    WHERE id = OLD.blocked_id;
END;
```

### Update track blocked flag

```sql
CREATE TRIGGER trg_track_blocked_by_insert
AFTER INSERT ON entity_blocked_by
WHEN NEW.blocked_type = 'track'
BEGIN
    UPDATE tracks SET blocked = 1 WHERE id = NEW.blocked_id;
END;

CREATE TRIGGER trg_track_blocked_by_delete
AFTER DELETE ON entity_blocked_by
WHEN OLD.blocked_type = 'track'
BEGIN
    UPDATE tracks
    SET blocked = (
        SELECT COUNT(*) > 0
        FROM entity_blocked_by
        WHERE blocked_type = 'track' AND blocked_id = OLD.blocked_id
    )
    WHERE id = OLD.blocked_id;
END;
```

---

## Auto-Completion Triggers

### Clear blocking relationships when blocker completes

```sql
-- When a task completes, remove it as a blocker
CREATE TRIGGER trg_clear_task_blocker
AFTER UPDATE OF status ON tasks
WHEN NEW.status = 'completed'
BEGIN
    -- Remove this task from all blocked_by entries
    DELETE FROM entity_blocked_by
    WHERE blocker_type = 'task' AND blocker_id = NEW.id;

    -- Remove corresponding blocks entries
    DELETE FROM entity_blocks
    WHERE blocker_type = 'task' AND blocker_id = NEW.id;
END;

-- When a sprint completes, remove it as a blocker
CREATE TRIGGER trg_clear_sprint_blocker
AFTER UPDATE OF status ON sprints
WHEN NEW.status = 'completed'
BEGIN
    DELETE FROM entity_blocked_by
    WHERE blocker_type = 'sprint' AND blocker_id = NEW.id;

    DELETE FROM entity_blocks
    WHERE blocker_type = 'sprint' AND blocker_id = NEW.id;
END;

-- When a track completes, remove it as a blocker
CREATE TRIGGER trg_clear_track_blocker
AFTER UPDATE OF status ON tracks
WHEN NEW.status = 'completed'
BEGIN
    DELETE FROM entity_blocked_by
    WHERE blocker_type = 'track' AND blocker_id = NEW.id;

    DELETE FROM entity_blocks
    WHERE blocker_type = 'track' AND blocker_id = NEW.id;
END;
```

### Auto-start sprint when first task starts

```sql
CREATE TRIGGER trg_auto_start_sprint
AFTER UPDATE OF status ON tasks
WHEN NEW.status = 'in_progress'
BEGIN
    UPDATE sprints
    SET status = 'in_progress',
        started = COALESCE(started, datetime('now'))
    WHERE id = NEW.sprint_id
      AND status = 'not_started';
END;
```

### Auto-start track when first sprint starts

```sql
CREATE TRIGGER trg_auto_start_track
AFTER UPDATE OF status ON sprints
WHEN NEW.status = 'in_progress'
BEGIN
    UPDATE tracks
    SET status = 'in_progress',
        started = COALESCE(started, datetime('now'))
    WHERE id = NEW.track_id
      AND status = 'not_started';
END;
```

---

## Summary Table Synchronization Triggers

### Keep task_summaries in sync

```sql
-- Insert summary when task created
CREATE TRIGGER trg_task_summary_insert
AFTER INSERT ON tasks
BEGIN
    INSERT INTO task_summaries (sprint_id, task_id, title, status, task_type, gate_info)
    VALUES (NEW.sprint_id, NEW.id, NEW.title, NEW.status, NEW.task_type, NEW.gate_info);
END;

-- Update summary when task updated
CREATE TRIGGER trg_task_summary_update
AFTER UPDATE ON tasks
BEGIN
    UPDATE task_summaries
    SET title = NEW.title,
        status = NEW.status,
        task_type = NEW.task_type,
        gate_info = NEW.gate_info
    WHERE task_id = NEW.id;
END;

-- Delete summary when task deleted
CREATE TRIGGER trg_task_summary_delete
AFTER DELETE ON tasks
BEGIN
    DELETE FROM task_summaries WHERE task_id = OLD.id;
END;
```

### Keep sprint_summaries in sync

```sql
-- Insert summary when sprint created
CREATE TRIGGER trg_sprint_summary_insert
AFTER INSERT ON sprints
BEGIN
    INSERT INTO sprint_summaries (track_id, sprint_id, name, status, estimated_duration, tasks_count, started)
    VALUES (
        NEW.track_id,
        NEW.id,
        NEW.name,
        NEW.status,
        json_extract(NEW.metadata, '$.estimated_duration'),
        0,
        NEW.started
    );
END;

-- Update summary when sprint updated
CREATE TRIGGER trg_sprint_summary_update
AFTER UPDATE ON sprints
BEGIN
    UPDATE sprint_summaries
    SET name = NEW.name,
        status = NEW.status,
        estimated_duration = json_extract(NEW.metadata, '$.estimated_duration'),
        started = NEW.started
    WHERE sprint_id = NEW.id;
END;

-- Update task count when tasks change
CREATE TRIGGER trg_sprint_summary_task_count_insert
AFTER INSERT ON tasks
BEGIN
    UPDATE sprint_summaries
    SET tasks_count = (SELECT COUNT(*) FROM tasks WHERE sprint_id = NEW.sprint_id)
    WHERE sprint_id = NEW.sprint_id;
END;

CREATE TRIGGER trg_sprint_summary_task_count_delete
AFTER DELETE ON tasks
BEGIN
    UPDATE sprint_summaries
    SET tasks_count = (SELECT COUNT(*) FROM tasks WHERE sprint_id = OLD.sprint_id)
    WHERE sprint_id = OLD.sprint_id;
END;

-- Delete summary when sprint deleted
CREATE TRIGGER trg_sprint_summary_delete
AFTER DELETE ON sprints
BEGIN
    DELETE FROM sprint_summaries WHERE sprint_id = OLD.id;
END;
```

### Keep track_summaries in sync

```sql
-- Insert summary when track created
CREATE TRIGGER trg_track_summary_insert
AFTER INSERT ON tracks
BEGIN
    INSERT INTO track_summaries (roadmap_id, track_id, name, status, priority)
    VALUES (NEW.roadmap_id, NEW.id, NEW.name, NEW.status, NEW.priority);
END;

-- Update summary when track updated
CREATE TRIGGER trg_track_summary_update
AFTER UPDATE ON tracks
BEGIN
    UPDATE track_summaries
    SET name = NEW.name,
        status = NEW.status,
        priority = NEW.priority
    WHERE track_id = NEW.id;
END;

-- Delete summary when track deleted
CREATE TRIGGER trg_track_summary_delete
AFTER DELETE ON tracks
BEGIN
    DELETE FROM track_summaries WHERE track_id = OLD.id;
END;
```

---

## Activity Logging Triggers

### Log significant events

```sql
-- Task status changes
CREATE TRIGGER trg_activity_task_status
AFTER UPDATE OF status ON tasks
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id, actor)
    VALUES (
        NEW.roadmap_id,
        'task_status_change',
        'Task "' || NEW.title || '" changed from ' || OLD.status || ' to ' || NEW.status,
        datetime('now'),
        'task',
        NEW.id,
        NEW.assigned_agent
    );
END;

-- Sprint status changes
CREATE TRIGGER trg_activity_sprint_status
AFTER UPDATE OF status ON sprints
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
    VALUES (
        NEW.roadmap_id,
        'sprint_status_change',
        'Sprint "' || NEW.name || '" changed from ' || OLD.status || ' to ' || NEW.status,
        datetime('now'),
        'sprint',
        NEW.id
    );
END;

-- Track status changes
CREATE TRIGGER trg_activity_track_status
AFTER UPDATE OF status ON tracks
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
    VALUES (
        NEW.roadmap_id,
        'track_status_change',
        'Track "' || NEW.name || '" changed from ' || OLD.status || ' to ' || NEW.status,
        datetime('now'),
        'track',
        NEW.id
    );
END;

-- New entities created
CREATE TRIGGER trg_activity_task_created
AFTER INSERT ON tasks
BEGIN
    INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
    VALUES (
        NEW.roadmap_id,
        'task_created',
        'Task "' || NEW.title || '" created in sprint ' || NEW.sprint_id,
        datetime('now'),
        'task',
        NEW.id
    );
END;

CREATE TRIGGER trg_activity_sprint_created
AFTER INSERT ON sprints
BEGIN
    INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
    VALUES (
        NEW.roadmap_id,
        'sprint_created',
        'Sprint "' || NEW.name || '" created in track ' || NEW.track_id,
        datetime('now'),
        'sprint',
        NEW.id
    );
END;

CREATE TRIGGER trg_activity_track_created
AFTER INSERT ON tracks
BEGIN
    INSERT INTO activity_log (roadmap_id, event_type, event_description, occurred_at, entity_type, entity_id)
    VALUES (
        NEW.roadmap_id,
        'track_created',
        'Track "' || NEW.name || '" created',
        datetime('now'),
        'track',
        NEW.id
    );
END;
```

---

## Validation Triggers (Blocker Enforcement)

### Prevent completing blocked tasks

```sql
CREATE TRIGGER trg_prevent_complete_blocked_task
BEFORE UPDATE OF status ON tasks
WHEN NEW.status = 'completed'
  AND EXISTS (
    SELECT 1 FROM entity_blocked_by eb
    JOIN tasks t ON t.id = eb.blocker_id AND eb.blocker_type = 'task'
    WHERE eb.blocked_type = 'task'
      AND eb.blocked_id = NEW.id
      AND t.status != 'completed'
  )
BEGIN
    SELECT RAISE(ABORT, 'Cannot complete task: unresolved blockers exist');
END;
```

### Prevent completing sprints with incomplete tasks

```sql
CREATE TRIGGER trg_prevent_complete_sprint_with_incomplete_tasks
BEFORE UPDATE OF status ON sprints
WHEN NEW.status = 'completed'
  AND EXISTS (
    SELECT 1 FROM tasks
    WHERE sprint_id = NEW.id
      AND status NOT IN ('completed', 'wont_do')
  )
BEGIN
    SELECT RAISE(ABORT, 'Cannot complete sprint: incomplete tasks exist');
END;
```

### Prevent completing tracks with incomplete sprints

```sql
CREATE TRIGGER trg_prevent_complete_track_with_incomplete_sprints
BEFORE UPDATE OF status ON tracks
WHEN NEW.status = 'completed'
  AND EXISTS (
    SELECT 1 FROM sprints
    WHERE track_id = NEW.id
      AND status NOT IN ('completed', 'wont_do')
  )
BEGIN
    SELECT RAISE(ABORT, 'Cannot complete track: incomplete sprints exist');
END;
```

---

## Trigger Summary

| Category | Triggers | Purpose |
|----------|----------|---------|
| Timestamp | 9 | Auto-set updated, started, completed timestamps |
| Blocked Flag | 6 | Keep blocked flag in sync with blocked_by entries |
| Auto-Completion | 5 | Clear blockers, auto-start parent entities |
| Summary Tables | 11 | Keep denormalized summaries in sync |
| Activity Log | 6 | Log significant events for audit trail |
| Validation | 3 | Enforce business rules (prevent invalid states) |
| **Total** | **40** | |

---

## Edge Cases & Considerations

### 1. Trigger Order

SQLite executes BEFORE triggers before AFTER triggers. Order within the same timing is undefined.

**Mitigation:** Design triggers to be independent where possible. Use BEFORE only for validation.

### 2. Circular Updates

Triggers updating the same table can cause infinite loops.

**Mitigation:** Use WHEN clauses to prevent re-triggering:
```sql
WHEN OLD.status != NEW.status  -- Only fire on actual change
```

### 3. Bulk Operations

Triggers fire for each row in bulk INSERT/UPDATE/DELETE.

**Consideration:** For bulk imports (YAML → DB rebuild), consider:
- Temporarily disabling triggers: `DROP TRIGGER trg_name; ... CREATE TRIGGER trg_name;`
- Using a flag column to skip logging during bulk ops

### 4. Blocker Cascade

When a blocker completes, we delete from entity_blocked_by, which fires the blocked flag triggers.

**This is intentional:** The cascade ensures blocked flags stay accurate.

### 5. Summary Table Consistency

Summary tables must stay in sync. We use INSERT/UPDATE/DELETE triggers on all source tables.

**Testing:** Comprehensive tests should verify summary tables match source queries.

---

## Next Steps

1. **Task 5:** Design YAML synchronization strategy (DB → YAML dump, YAML → DB rebuild)
2. **Task 6:** Consolidate into design document for review

---

**Document Version:** 1.0.0
**Triggers Defined:** 40
