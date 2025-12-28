# Task 2.5: Audit Roadmap State for Orphans and Broken References - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | TBD (assign during execution) |
| Sprint | Sprint 2: Data Integrity Validation |
| Type | audit |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 3,000 |
| Dependencies | Sprint 1.5 completion (baseline data) |

## Objective

Find orphaned entities and broken references in the roadmap system, including:
- Tasks with invalid sprint_id (orphan tasks)
- Sprints with invalid track_id (orphan sprints)
- Broken blocked_by/depends_on references between tasks
- Invalid .id file mappings in YAML structure

## Background

### Problem Statement
The dual storage system (YAML + SQLite) and hierarchical entity structure can develop inconsistencies:
- Tasks may reference non-existent sprints
- Sprints may reference non-existent tracks
- Task dependencies may point to deleted tasks
- .id files may be stale or point to moved entities

### Why This Matters
- **Data Integrity:** Orphans indicate failed operations or manual edits
- **Query Accuracy:** Orphaned entities may not appear in reports correctly
- **Dependency Tracking:** Broken references cause incorrect blocking logic
- **Navigation:** Invalid .id mappings break directory-based lookups

## Investigation Steps

### Step 1: Find Orphan Tasks

```sql
-- Tasks with no valid sprint
SELECT
  t.id,
  t.title,
  t.sprint_id,
  t.status
FROM tasks t
LEFT JOIN sprints s ON t.sprint_id = s.id
WHERE s.id IS NULL;

-- Tasks with empty/null sprint_id
SELECT id, title, sprint_id
FROM tasks
WHERE sprint_id IS NULL OR sprint_id = '';
```

### Step 2: Find Orphan Sprints

```sql
-- Sprints with no valid track
SELECT
  s.id,
  s.name,
  s.track_id,
  s.status
FROM sprints s
LEFT JOIN tracks tr ON s.track_id = tr.id
WHERE tr.id IS NULL;

-- Sprints with empty/null track_id
SELECT id, name, track_id
FROM sprints
WHERE track_id IS NULL OR track_id = '';
```

### Step 3: Find Broken Dependency References

```sql
-- Tasks with blocked_by pointing to non-existent tasks
SELECT
  t.id AS task_id,
  t.title,
  t.blocked_by
FROM tasks t
WHERE t.blocked_by IS NOT NULL
  AND t.blocked_by != ''
  AND NOT EXISTS (
    SELECT 1 FROM tasks t2 WHERE t2.id = t.blocked_by
  );

-- Parse multi-value blocked_by fields (if stored as comma-separated)
-- Note: This requires application-level parsing
```

### Step 4: Verify Reference Integrity Across Tables

```sql
-- Count tasks per sprint (to find sprints with orphaned task counts)
SELECT
  s.id,
  s.name,
  s.task_count AS recorded_count,
  COUNT(t.id) AS actual_count
FROM sprints s
LEFT JOIN tasks t ON t.sprint_id = s.id
GROUP BY s.id
HAVING recorded_count != actual_count;

-- Count sprints per track
SELECT
  tr.id,
  tr.name,
  tr.sprint_count AS recorded_count,
  COUNT(s.id) AS actual_count
FROM tracks tr
LEFT JOIN sprints s ON s.track_id = tr.id
GROUP BY tr.id
HAVING recorded_count != actual_count;
```

### Step 5: Audit .id File Mappings

```bash
# Find all .id files
find .vibey/roadmap -name ".id" -type f

# Check each .id file points to valid YAML
for id_file in $(find .vibey/roadmap -name ".id" -type f); do
  id_content=$(cat "$id_file")
  dir=$(dirname "$id_file")

  echo "=== $id_file ==="
  echo "ID: $id_content"

  # Check if corresponding YAML exists
  if [ -f "$dir/$id_content.yaml" ]; then
    echo "Status: VALID"
  else
    echo "Status: BROKEN - YAML not found"
  fi
done
```

### Step 6: Verify YAML-Database Sync

```bash
# Count YAML files
tracks_yaml=$(ls -1 .vibey/roadmap/tracks/*.yaml 2>/dev/null | wc -l)
sprints_yaml=$(ls -1 .vibey/roadmap/sprints/*.yaml 2>/dev/null | wc -l)
tasks_yaml=$(ls -1 .vibey/roadmap/tasks/*.yaml 2>/dev/null | wc -l)

# Count database records
tracks_db=$(sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM tracks")
sprints_db=$(sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM sprints")
tasks_db=$(sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM tasks")

echo "Tracks: YAML=$tracks_yaml, DB=$tracks_db"
echo "Sprints: YAML=$sprints_yaml, DB=$sprints_db"
echo "Tasks: YAML=$tasks_yaml, DB=$tasks_db"
```

## SQL Queries Reference

### Query 1: Full Orphan Report
```sql
SELECT 'orphan_task' AS type, t.id, t.title, t.sprint_id AS invalid_ref
FROM tasks t
LEFT JOIN sprints s ON t.sprint_id = s.id
WHERE s.id IS NULL

UNION ALL

SELECT 'orphan_sprint' AS type, s.id, s.name, s.track_id AS invalid_ref
FROM sprints s
LEFT JOIN tracks tr ON s.track_id = tr.id
WHERE tr.id IS NULL;
```

### Query 2: Reference Chain Validation
```sql
-- Full chain: Track -> Sprint -> Task
SELECT
  tr.id AS track_id,
  tr.name AS track_name,
  s.id AS sprint_id,
  s.name AS sprint_name,
  t.id AS task_id,
  t.title AS task_title
FROM tracks tr
LEFT JOIN sprints s ON s.track_id = tr.id
LEFT JOIN tasks t ON t.sprint_id = s.id
ORDER BY tr.name, s.name, t.title;
```

### Query 3: Dependency Graph Validation
```sql
-- All task dependencies
SELECT
  t1.id AS task_id,
  t1.title AS task_title,
  t1.blocked_by,
  t2.id AS blocker_id,
  t2.title AS blocker_title,
  CASE WHEN t2.id IS NULL THEN 'BROKEN' ELSE 'VALID' END AS status
FROM tasks t1
LEFT JOIN tasks t2 ON t1.blocked_by = t2.id
WHERE t1.blocked_by IS NOT NULL AND t1.blocked_by != '';
```

### Query 4: ULID Format Validation
```sql
-- Check for invalid ULID formats (should be 26 chars)
SELECT 'task' AS type, id, LENGTH(id) AS len
FROM tasks WHERE LENGTH(id) != 26

UNION ALL

SELECT 'sprint' AS type, id, LENGTH(id) AS len
FROM sprints WHERE LENGTH(id) != 26

UNION ALL

SELECT 'track' AS type, id, LENGTH(id) AS len
FROM tracks WHERE LENGTH(id) != 26;
```

## Verification Steps

1. **Orphan Detection:** Query for tasks/sprints with invalid parent references
2. **Dependency Check:** Validate all blocked_by/depends_on references
3. **Count Reconciliation:** Compare recorded vs actual entity counts
4. **ID File Audit:** Verify .id files point to existing YAMLs
5. **YAML-DB Sync:** Ensure file counts match database counts
6. **Format Validation:** Check ULID format compliance

## Deliverables

### 1. ORPHAN_AUDIT.md

```markdown
# Orphan and Broken Reference Audit Results

## Executive Summary
- Orphan tasks found: X
- Orphan sprints found: Y
- Broken dependencies: Z
- Invalid .id mappings: W
- Count mismatches: V
- **Referential Integrity Score:** (calculated)

## Findings

### Orphan Tasks (X found)
| Task ID | Title | Invalid Sprint ID |
|---------|-------|-------------------|
| ... | ... | ... |

### Orphan Sprints (Y found)
| Sprint ID | Name | Invalid Track ID |
|-----------|------|------------------|
| ... | ... | ... |

### Broken Dependencies (Z found)
| Task ID | Title | References | Status |
|---------|-------|------------|--------|
| ... | ... | 01KC... (missing) | BROKEN |

### Invalid .id Mappings (W found)
| .id File Path | Points To | Status |
|---------------|-----------|--------|
| ... | ... | YAML missing |

### Count Mismatches (V found)
| Entity | Recorded | Actual | Discrepancy |
|--------|----------|--------|-------------|
| Sprint X tasks | 5 | 3 | -2 |

## Root Cause Analysis
[Analysis of why orphans/broken refs occurred]

## Recommendations
1. [Cleanup actions]
2. [Prevention measures]
```

### 2. ORPHAN_CLEANUP.yaml

```yaml
# Entities requiring cleanup
orphan_tasks:
  - id: 01KC...
    title: "..."
    invalid_sprint_id: 01KC...
    action: delete | reassign
    reassign_to: # if reassign

orphan_sprints:
  - id: 01KC...
    name: "..."
    invalid_track_id: 01KC...
    action: delete | reassign

broken_dependencies:
  - task_id: 01KC...
    field: blocked_by
    invalid_value: 01KC...
    action: clear | update
```

### 3. INTEGRITY_CHECKS.sql

```sql
-- Reusable integrity check queries
-- Run periodically to detect new orphans

-- Check 1: Orphan tasks
SELECT ... ;

-- Check 2: Orphan sprints
SELECT ... ;

-- Check 3: Broken dependencies
SELECT ... ;

-- Check 4: Count integrity
SELECT ... ;
```

## Acceptance Criteria

- [ ] All orphan tasks have been identified and documented
- [ ] All orphan sprints have been identified and documented
- [ ] All broken dependency references have been found
- [ ] .id file mappings have been audited
- [ ] YAML-Database entity counts have been reconciled
- [ ] ORPHAN_CLEANUP.yaml provides actionable remediation steps
- [ ] INTEGRITY_CHECKS.sql can be reused for ongoing monitoring

## Estimated Time

- Orphan queries: 20 minutes
- Dependency validation: 30 minutes
- .id file audit: 20 minutes
- Count reconciliation: 15 minutes
- Report generation: 30 minutes
- **Total: ~2 hours**

## Notes

- Orphans may be legitimate if entities were intentionally archived
- Some broken references may be due to incomplete migrations
- .id files are used for backward compatibility with nested structure
- Consider implementing foreign key constraints to prevent future orphans
- Document any orphans that should NOT be cleaned up
