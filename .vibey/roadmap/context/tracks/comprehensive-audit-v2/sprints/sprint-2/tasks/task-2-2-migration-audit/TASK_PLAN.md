# Task 2.2: Audit Completed Migration Tasks Against Database Schema - Detailed Plan

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

Query all completed tasks that claim database migrations or schema changes, then verify those changes actually exist in the database schema. Use PRAGMA commands to validate tables, columns, indices, and views match what was claimed.

## Background

### Problem Statement
Migration tasks may be marked "completed" claiming schema changes (new tables, columns, indices) that were never actually applied to the database. This is especially concerning for the Unified Architecture Migration track.

### Why This Matters
- **Data Integrity:** False schema migrations can cause runtime errors
- **Feature Availability:** Features depending on schema changes will fail
- **Technical Debt:** Incomplete migrations create hidden dependencies

## Investigation Steps

### Step 1: Query Completed Migration Tasks

```sql
-- Find tasks claiming database/schema work
SELECT
  t.id,
  t.title,
  t.status,
  t.completed,
  t.deliverables,
  t.description,
  s.name AS sprint_name,
  tr.name AS track_name
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
  AND (
    t.title LIKE '%migrat%'
    OR t.title LIKE '%schema%'
    OR t.title LIKE '%database%'
    OR t.title LIKE '%table%'
    OR t.title LIKE '%column%'
    OR t.deliverables LIKE '%table%'
    OR t.deliverables LIKE '%column%'
    OR t.deliverables LIKE '%index%'
    OR t.deliverables LIKE '%view%'
    OR t.description LIKE '%CREATE TABLE%'
    OR t.description LIKE '%ALTER TABLE%'
  )
ORDER BY t.completed DESC;
```

### Step 2: Capture Current Database Schema

```sql
-- Get all tables
SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;

-- Get all views
SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name;

-- Get all indices
SELECT name, sql FROM sqlite_master WHERE type='index' ORDER BY name;

-- Get all triggers
SELECT name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name;
```

### Step 3: Document Expected vs Actual Schema

For each migration task, extract claimed changes:

```bash
# Export migration task details
sqlite3 .vibey/roadmap.db "
  SELECT t.id, t.title, t.deliverables, t.description
  FROM tasks t
  WHERE t.status = 'completed'
    AND (t.title LIKE '%migrat%' OR t.title LIKE '%schema%')
" > /tmp/migration_tasks.txt
```

### Step 4: Verify Specific Schema Claims

#### Check for Claimed Tables
```sql
-- List all tables
.tables

-- Check specific table exists
SELECT name FROM sqlite_master
WHERE type='table' AND name='claimed_table_name';
```

#### Check for Claimed Columns
```sql
-- Get columns for a specific table
PRAGMA table_info(tasks);
PRAGMA table_info(sprints);
PRAGMA table_info(tracks);

-- Example: Check for format_version column
PRAGMA table_info(tasks);
-- Look for 'format_version' in output
```

#### Check for Claimed Indices
```sql
-- List indices on a table
PRAGMA index_list(tasks);

-- Get index columns
PRAGMA index_info(index_name);
```

#### Check for Claimed Views
```sql
-- List all views
SELECT name FROM sqlite_master WHERE type='view';

-- Check specific view
SELECT sql FROM sqlite_master
WHERE type='view' AND name='claimed_view_name';
```

### Step 5: Build Verification Matrix

| Task ID | Claimed Change | Type | Exists? | PRAGMA Result | Verdict |
|---------|---------------|------|---------|---------------|---------|
| 01KC... | format_version column | column | NO | Not in table_info | FALSE |
| 01KC... | ticket_history table | table | YES | In .tables | TRUE |
| 01KC... | idx_tasks_status | index | NO | Not in index_list | FALSE |

## SQL Queries Reference

### Query 1: Full Schema Dump
```sql
-- Complete schema export
SELECT
  type,
  name,
  tbl_name,
  sql
FROM sqlite_master
WHERE type IN ('table', 'view', 'index', 'trigger')
ORDER BY type, name;
```

### Query 2: Table Column Details
```sql
-- For each core table
PRAGMA table_info(tracks);
PRAGMA table_info(sprints);
PRAGMA table_info(tasks);
PRAGMA table_info(tickets);
PRAGMA table_info(handoffs);
```

### Query 3: Foreign Key Verification
```sql
-- Check foreign keys are defined
PRAGMA foreign_key_list(tasks);
PRAGMA foreign_key_list(sprints);
```

### Query 4: Count Schema Objects
```sql
SELECT
  type,
  COUNT(*) as count
FROM sqlite_master
WHERE type IN ('table', 'view', 'index', 'trigger')
GROUP BY type;
```

## Verification Steps

1. **Task Identification:** Find all completed migration-related tasks
2. **Claim Extraction:** Parse deliverables for specific schema changes
3. **Schema Capture:** Document current database schema state
4. **Element-by-Element Check:** Verify each claimed change exists
5. **Discrepancy Documentation:** Record mismatches with evidence
6. **Impact Assessment:** Identify features affected by missing migrations

## Deliverables

### 1. MIGRATION_AUDIT.md

```markdown
# Database Migration Task Audit Results

## Executive Summary
- Total migration tasks analyzed: X
- Schema changes claimed: Y
- Schema changes verified: Z
- Missing migrations: W
- **Migration Integrity Score:** Z/Y (percentage)

## Current Schema State
- Tables: X
- Views: Y
- Indices: Z
- Triggers: W

## Findings

### Verified Migrations (Z tasks)
| Task ID | Title | Claimed Change | Verification |
|---------|-------|----------------|--------------|
| ... | ... | Added X table | EXISTS |

### Missing Migrations (W tasks)
| Task ID | Title | Claimed Change | Expected | Actual |
|---------|-------|----------------|----------|--------|
| ... | ... | format_version column | In tasks table | Not found |

## Schema Discrepancy Details
[Detailed PRAGMA output for each missing element]

## Recommendations
1. [Migrations that need to be applied]
2. [Status corrections needed]
```

### 2. SCHEMA_STATE.sql

```sql
-- Current schema snapshot
-- Generated: [timestamp]
-- Purpose: Baseline for audit comparison

-- Tables
CREATE TABLE tracks (...);
CREATE TABLE sprints (...);
...

-- Views
CREATE VIEW active_tasks AS ...;
...

-- Indices
CREATE INDEX idx_tasks_status ON tasks(status);
...
```

### 3. STATUS_CORRECTIONS.yaml

```yaml
# Migration tasks requiring status correction
corrections:
  - task_id: 01KC...
    old_status: completed
    new_status: not_started
    reason: "Schema changes not applied"
    missing_changes:
      - type: column
        table: tasks
        name: format_version
      - type: index
        name: idx_tasks_format
```

## Acceptance Criteria

- [ ] All completed migration tasks have been identified
- [ ] Current database schema has been fully documented
- [ ] Each claimed schema change has been verified via PRAGMA
- [ ] Missing migrations are documented with expected vs actual state
- [ ] STATUS_CORRECTIONS.yaml identifies tasks needing status changes
- [ ] MIGRATION_AUDIT.md provides clear audit trail

## Estimated Time

- Task identification and parsing: 30 minutes
- Schema capture and documentation: 30 minutes
- Element-by-element verification: 45 minutes
- Report generation: 30 minutes
- **Total: ~2.5 hours**

## PRAGMA Commands Reference

```sql
-- Table information
PRAGMA table_info(table_name);

-- Index list for a table
PRAGMA index_list(table_name);

-- Index details
PRAGMA index_info(index_name);

-- Foreign keys for a table
PRAGMA foreign_key_list(table_name);

-- Check foreign key integrity
PRAGMA foreign_key_check;

-- Database integrity check
PRAGMA integrity_check;
```

## Notes

- Focus on `.vibey/roadmap.db` as the primary database
- Check for v2 schema elements mentioned in Unified Architecture Migration
- Document any tables that exist but weren't claimed by any task
- Consider partial migrations where some columns exist but not all
