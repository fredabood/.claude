# Task 1: Audit Completed Migration Tasks Against Database Schema

**Task ID**: `01KDC9293X9AMMB8XRXQ7TJB1K`
**Type**: research
**Priority**: high
**Estimated Tokens**: 3,000

## Objective

Verify that all completed tasks claiming database schema changes (migrations, new tables, columns, indices) actually resulted in those changes existing in the production database.

## Methodology

### Step 1: Query Completed Migration Tasks

```sql
SELECT t.id, t.title, t.description, s.name as sprint_name, tr.name as track_name
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
AND (
    LOWER(t.title) LIKE '%migrat%'
    OR LOWER(t.title) LIKE '%schema%'
    OR LOWER(t.title) LIKE '%database%'
    OR LOWER(t.title) LIKE '%create table%'
    OR LOWER(t.title) LIKE '%add column%'
    OR LOWER(t.title) LIKE '%add table%'
    OR LOWER(t.description) LIKE '%migrat%'
    OR LOWER(t.description) LIKE '%schema%'
    OR LOWER(t.description) LIKE '%create table%'
)
ORDER BY tr.name, s.name;
```

### Step 2: Extract Expected Schema Elements

For each task, parse the title and description to identify:
- Table names expected to exist
- Column names expected to exist
- Index names expected to exist
- Constraint names expected to exist

### Step 3: Query Actual Database Schema

```sql
-- List all tables
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- For each table, get columns
PRAGMA table_info(table_name);

-- List all indices
SELECT name, tbl_name FROM sqlite_master WHERE type='index';
```

### Step 4: Cross-Reference and Flag Discrepancies

For each completed migration task:
1. Check if claimed tables exist
2. Check if claimed columns exist on correct tables
3. Check if claimed indices exist
4. Flag any missing elements as "phantom completion"

## Expected Output

A structured report with:

```markdown
## Migration Task Audit Results

### Verified Completions (N tasks)
| Task ID | Title | Verified Elements |
|---------|-------|-------------------|
| ... | ... | tables: X, columns: Y |

### Phantom Completions (N tasks)
| Task ID | Title | Missing Elements | Recommendation |
|---------|-------|------------------|----------------|
| ... | ... | table: completables | Revert to not_started |
```

## Key Tables to Verify

Based on preliminary analysis, focus on:
- `completables` - claimed by Unified Architecture Migration
- `criteria` - claimed by Unified Architecture Migration
- `artifacts` - claimed by multiple tracks
- `tickets` - claimed by schema v2 migration

## Success Criteria

- [ ] All completed migration tasks queried
- [ ] Each task's claimed schema changes extracted
- [ ] Actual database schema captured
- [ ] Discrepancies identified and documented
- [ ] Recommendations generated for each phantom completion

## Tools

- SQLite CLI (`sqlite3`)
- Python script for parsing task descriptions
- Database: `.vibey/roadmap.db`

## Deliverables

1. `migration-audit-results.json` - Structured audit data
2. Summary section for final audit report
