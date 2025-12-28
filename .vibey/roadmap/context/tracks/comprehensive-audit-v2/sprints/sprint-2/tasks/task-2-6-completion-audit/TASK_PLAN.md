# Task 2.6: Audit Track/Sprint Completion Status Accuracy - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | TBD (assign during execution) |
| Sprint | Sprint 2: Data Integrity Validation |
| Type | audit |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 2,500 |
| Dependencies | Sprint 1.5 completion (baseline data) |

## Objective

Verify that track and sprint completion statuses accurately reflect the state of their child entities:
- Completed tracks should have all sprints completed
- Completed sprints should have all tasks completed
- Identify any auto-completion logic bugs causing premature status changes

## Background

### Problem Statement
Tracks and sprints can be marked "completed" even when child entities remain incomplete. This can happen due to:
- Manual status overrides without validation
- Auto-completion logic triggering incorrectly
- Race conditions in status update operations
- Status not rolling up properly from children

### Why This Matters
- **Progress Accuracy:** Rollup metrics become unreliable
- **Planning Impact:** Dependencies on "completed" work may fail
- **Trust Erosion:** Users lose confidence in status indicators

## Investigation Steps

### Step 1: Find Tracks Marked Complete With Incomplete Sprints

```sql
-- Tracks marked completed but have non-completed sprints
SELECT
  tr.id AS track_id,
  tr.name AS track_name,
  tr.status AS track_status,
  s.id AS sprint_id,
  s.name AS sprint_name,
  s.status AS sprint_status
FROM tracks tr
JOIN sprints s ON s.track_id = tr.id
WHERE tr.status = 'completed'
  AND s.status != 'completed'
ORDER BY tr.name, s.name;
```

### Step 2: Find Sprints Marked Complete With Incomplete Tasks

```sql
-- Sprints marked completed but have non-completed tasks
SELECT
  s.id AS sprint_id,
  s.name AS sprint_name,
  s.status AS sprint_status,
  t.id AS task_id,
  t.title AS task_title,
  t.status AS task_status
FROM sprints s
JOIN tasks t ON t.sprint_id = s.id
WHERE s.status = 'completed'
  AND t.status NOT IN ('completed', 'wont_do', 'cancelled')
ORDER BY s.name, t.title;
```

### Step 3: Verify Completion Rollup Logic

```sql
-- Calculate expected status based on children
-- Track should be complete only if all sprints are complete
SELECT
  tr.id,
  tr.name,
  tr.status AS current_status,
  CASE
    WHEN COUNT(s.id) = 0 THEN 'not_started'
    WHEN SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) = COUNT(s.id) THEN 'completed'
    WHEN SUM(CASE WHEN s.status IN ('in_progress', 'completed') THEN 1 ELSE 0 END) > 0 THEN 'in_progress'
    ELSE 'not_started'
  END AS expected_status
FROM tracks tr
LEFT JOIN sprints s ON s.track_id = tr.id
GROUP BY tr.id
HAVING current_status != expected_status;
```

### Step 4: Sprint Completion Verification

```sql
-- Sprint should be complete only if all tasks are complete/wont_do/cancelled
SELECT
  s.id,
  s.name,
  s.status AS current_status,
  COUNT(t.id) AS total_tasks,
  SUM(CASE WHEN t.status IN ('completed', 'wont_do', 'cancelled') THEN 1 ELSE 0 END) AS done_tasks,
  CASE
    WHEN COUNT(t.id) = 0 THEN 'not_started'
    WHEN SUM(CASE WHEN t.status IN ('completed', 'wont_do', 'cancelled') THEN 1 ELSE 0 END) = COUNT(t.id) THEN 'completed'
    WHEN SUM(CASE WHEN t.status IN ('in_progress', 'completed') THEN 1 ELSE 0 END) > 0 THEN 'in_progress'
    ELSE 'not_started'
  END AS expected_status
FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY s.id
HAVING current_status != expected_status;
```

### Step 5: Check Progress Percentage Accuracy

```sql
-- Verify progress percentages match task completion rates
SELECT
  s.id,
  s.name,
  s.progress AS recorded_progress,
  CAST(
    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) * 100.0 /
    NULLIF(COUNT(t.id), 0) AS INTEGER
  ) AS calculated_progress
FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY s.id
HAVING ABS(recorded_progress - calculated_progress) > 5;  -- Allow 5% tolerance
```

### Step 6: Timeline Consistency Check

```sql
-- Completed entities should have completion dates
SELECT 'track' AS type, id, name, status, completed
FROM tracks
WHERE status = 'completed' AND completed IS NULL

UNION ALL

SELECT 'sprint' AS type, id, name, status, completed
FROM sprints
WHERE status = 'completed' AND completed IS NULL

UNION ALL

SELECT 'task' AS type, id, title, status, completed
FROM tasks
WHERE status = 'completed' AND completed IS NULL;
```

## SQL Queries Reference

### Query 1: Full Status Hierarchy Report
```sql
SELECT
  tr.name AS track_name,
  tr.status AS track_status,
  s.name AS sprint_name,
  s.status AS sprint_status,
  COUNT(t.id) AS total_tasks,
  SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) AS completed_tasks,
  SUM(CASE WHEN t.status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_tasks
FROM tracks tr
LEFT JOIN sprints s ON s.track_id = tr.id
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY tr.id, s.id
ORDER BY tr.name, s.name;
```

### Query 2: Premature Completion Detection
```sql
-- Find entities marked complete before their children
SELECT
  tr.id AS track_id,
  tr.name AS track_name,
  tr.completed AS track_completed,
  s.id AS sprint_id,
  s.name AS sprint_name,
  s.completed AS sprint_completed
FROM tracks tr
JOIN sprints s ON s.track_id = tr.id
WHERE tr.status = 'completed'
  AND s.status = 'completed'
  AND tr.completed < s.completed;  -- Track completed before sprint
```

### Query 3: Auto-Completion Candidates
```sql
-- Sprints that would auto-complete if logic ran
SELECT
  s.id,
  s.name,
  s.status,
  COUNT(t.id) AS total_tasks,
  SUM(CASE WHEN t.status IN ('completed', 'wont_do') THEN 1 ELSE 0 END) AS done_tasks
FROM sprints s
JOIN tasks t ON t.sprint_id = s.id
WHERE s.status != 'completed'
GROUP BY s.id
HAVING done_tasks = total_tasks AND total_tasks > 0;
```

## Verification Steps

1. **Track-Sprint Check:** Find completed tracks with incomplete sprints
2. **Sprint-Task Check:** Find completed sprints with incomplete tasks
3. **Status Rollup Validation:** Calculate expected status, compare to actual
4. **Progress Accuracy:** Verify percentage calculations
5. **Timeline Consistency:** Check completion dates exist for completed entities
6. **Auto-Completion Analysis:** Identify potential logic bugs

## Deliverables

### 1. COMPLETION_STATUS_AUDIT.md

```markdown
# Track/Sprint Completion Status Audit Results

## Executive Summary
- Tracks with status mismatch: X
- Sprints with status mismatch: Y
- Progress percentage errors: Z
- Missing completion dates: W
- **Status Accuracy Score:** (calculated)

## Status Validation Rules
1. Track = completed IFF all sprints completed/cancelled
2. Sprint = completed IFF all tasks completed/wont_do/cancelled
3. Progress = (completed_tasks / total_tasks) * 100

## Findings

### Falsely Completed Tracks (X found)
| Track ID | Track Name | Status | Incomplete Sprints |
|----------|------------|--------|-------------------|
| ... | ... | completed | 2 of 5 not done |

### Falsely Completed Sprints (Y found)
| Sprint ID | Sprint Name | Status | Incomplete Tasks |
|-----------|-------------|--------|------------------|
| ... | ... | completed | 3 tasks pending |

### Progress Percentage Errors (Z found)
| Entity | Recorded | Calculated | Discrepancy |
|--------|----------|------------|-------------|
| ... | 100% | 75% | -25% |

### Missing Completion Dates (W found)
| Type | ID | Name | Status |
|------|-----|------|--------|
| track | ... | ... | completed (no date) |

## Auto-Completion Logic Analysis
[Analysis of when/how auto-completion triggers]

## Recommendations
1. [Status corrections needed]
2. [Logic fixes required]
```

### 2. STATUS_CORRECTIONS.yaml

```yaml
# Entities requiring status correction
tracks:
  - id: 01KC...
    name: "..."
    current_status: completed
    correct_status: in_progress
    reason: "2 sprints not completed"
    incomplete_sprints:
      - 01KC...
      - 01KC...

sprints:
  - id: 01KC...
    name: "..."
    current_status: completed
    correct_status: in_progress
    reason: "3 tasks not completed"
    incomplete_tasks:
      - 01KC...
      - 01KC...
      - 01KC...

progress_corrections:
  - id: 01KC...
    type: sprint
    current_progress: 100
    correct_progress: 75
```

### 3. COMPLETION_LOGIC_REVIEW.md

```markdown
# Completion Logic Review

## Current Implementation
[Description of how status rollup currently works]

## Identified Issues
1. [Issue 1]
2. [Issue 2]

## Recommended Logic
[Pseudocode for correct completion logic]

## Implementation Location
- File: vibey/operations/roadmap/...
- Function: ...
```

## Acceptance Criteria

- [ ] All completed tracks have been verified against sprint statuses
- [ ] All completed sprints have been verified against task statuses
- [ ] Progress percentages have been validated
- [ ] Completion dates presence has been verified
- [ ] STATUS_CORRECTIONS.yaml documents all required fixes
- [ ] Any auto-completion logic bugs have been identified

## Estimated Time

- Track-sprint verification: 20 minutes
- Sprint-task verification: 30 minutes
- Progress calculation check: 20 minutes
- Timeline verification: 15 minutes
- Report generation: 30 minutes
- **Total: ~2 hours**

## Notes

- Consider that `wont_do` and `cancelled` count as "done" for completion purposes
- Empty sprints (0 tasks) should have special handling
- Progress percentages may have rounding differences (allow tolerance)
- Check both YAML files and database for status consistency
- Auto-completion may be intentionally disabled in some configurations
