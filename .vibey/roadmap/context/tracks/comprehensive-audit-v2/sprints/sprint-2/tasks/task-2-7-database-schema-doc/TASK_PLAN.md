# Task 2.7: Update DATABASE_SCHEMA_DOCUMENTATION.md - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | TBD (assign during execution) |
| Sprint | Sprint 2: Data Integrity Validation |
| Type | documentation |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 3,000 |
| Dependencies | Task 2.2 (Migration Audit) recommended first |

## Objective

Update the DATABASE_SCHEMA_DOCUMENTATION.md to reflect the current state of the database schema, documenting the growth from 27 to 39 tables, 21 to 25 views, and any trigger changes that have occurred.

## Background

### Problem Statement
The database schema has evolved significantly but documentation may not reflect:
- New tables added during various development efforts
- New views created for reporting/queries
- Trigger additions or modifications
- Column changes in existing tables
- Index additions for performance

### Why This Matters
- **Onboarding:** New developers need accurate schema documentation
- **Maintenance:** Schema changes need to be understood before modifications
- **Auditing:** Knowing what exists is prerequisite for validating task claims

## Investigation Steps

### Step 1: Capture Current Schema State

```sql
-- Get all tables with creation SQL
SELECT name, sql
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- Get all views with definition SQL
SELECT name, sql
FROM sqlite_master
WHERE type = 'view'
ORDER BY name;

-- Get all triggers
SELECT name, sql
FROM sqlite_master
WHERE type = 'trigger'
ORDER BY name;

-- Get all indices
SELECT name, sql, tbl_name
FROM sqlite_master
WHERE type = 'index'
  AND name NOT LIKE 'sqlite_%'
ORDER BY tbl_name, name;
```

### Step 2: Document Table Details

For each table, capture:

```sql
-- Example for tasks table
PRAGMA table_info(tasks);
PRAGMA foreign_key_list(tasks);
PRAGMA index_list(tasks);

-- Repeat for all tables
```

### Step 3: Compare Against Existing Documentation

```bash
# Find existing schema documentation
find . -name "*SCHEMA*" -o -name "*schema*" | grep -i doc

# Check existing documentation
cat docs/architecture/DATABASE_SCHEMA_DOCUMENTATION.md
# or wherever it exists
```

### Step 4: Identify New/Changed Elements

Create comparison lists:
- Tables in database but not in docs (NEW)
- Tables in docs but not in database (REMOVED/RENAMED)
- Tables with column changes (MODIFIED)
- New views
- New triggers
- New indices

### Step 5: Categorize Tables by Domain

Group tables logically:
1. **Core Roadmap:** tracks, sprints, tasks
2. **Ticket System:** tickets, ticket_history, ticket_comments
3. **Context System:** contexts, context_files, context_snapshots
4. **Handoff System:** handoffs, handoff_artifacts
5. **Configuration:** settings, adapters, platforms
6. **Audit/History:** audit_log, change_history

## SQL Queries Reference

### Query 1: Complete Schema Inventory
```sql
SELECT
  type,
  name,
  CASE type
    WHEN 'table' THEN 'Table'
    WHEN 'view' THEN 'View'
    WHEN 'trigger' THEN 'Trigger'
    WHEN 'index' THEN 'Index'
  END AS category
FROM sqlite_master
WHERE name NOT LIKE 'sqlite_%'
ORDER BY type, name;
```

### Query 2: Table Statistics
```sql
SELECT
  name,
  (SELECT COUNT(*) FROM pragma_table_info(name)) AS column_count
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name;
```

### Query 3: Row Counts Per Table
```sql
-- Generate row count queries (run separately)
SELECT 'SELECT ''' || name || ''' AS tbl, COUNT(*) AS rows FROM ' || name || ' UNION ALL'
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%';
```

### Query 4: Foreign Key Relationships
```sql
SELECT
  m.name AS table_name,
  p."table" AS references_table,
  p."from" AS from_column,
  p."to" AS to_column
FROM sqlite_master m
JOIN pragma_foreign_key_list(m.name) p
WHERE m.type = 'table'
ORDER BY m.name;
```

## Documentation Structure

### DATABASE_SCHEMA_DOCUMENTATION.md Template

```markdown
# Vibey Database Schema Documentation

## Overview
- **Database:** .vibey/roadmap/roadmap.db
- **Engine:** SQLite 3.x
- **Tables:** 39
- **Views:** 25
- **Triggers:** X
- **Indices:** Y
- **Last Updated:** [date]

## Schema Diagram
[ASCII or Mermaid diagram of key relationships]

## Tables by Domain

### Core Roadmap (X tables)

#### tracks
Primary table for development tracks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | ULID identifier |
| name | TEXT | NOT NULL | Track name |
| ... | ... | ... | ... |

**Indices:**
- idx_tracks_status (status)
- idx_tracks_name (name)

**Foreign Keys:** None

---

#### sprints
Sprint definitions within tracks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| ... | ... | ... | ... |

---

### Ticket System (X tables)

#### tickets
[Documentation]

---

### Views

#### active_tasks
Returns tasks with in_progress status.

```sql
CREATE VIEW active_tasks AS
SELECT ...
```

---

### Triggers

#### trg_task_updated
Fires on task update to maintain audit trail.

```sql
CREATE TRIGGER trg_task_updated ...
```

---

## Schema Evolution

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 2.5.0 | 2024-12-XX | Added X tables, Y views |
| 2.4.0 | ... | ... |

### Migration Notes
[Notes on significant migrations]

## Appendices

### A: Complete CREATE Statements
[Full SQL for all tables]

### B: ER Diagram
[Entity-relationship diagram]
```

## Verification Steps

1. **Schema Extraction:** Run PRAGMA commands for all tables
2. **Existing Doc Review:** Find and read current documentation
3. **Gap Analysis:** Identify what's missing from docs
4. **Structure Design:** Organize by logical domain
5. **Content Generation:** Write documentation for each element
6. **Validation:** Verify documentation matches actual schema

## Deliverables

### 1. DATABASE_SCHEMA_DOCUMENTATION.md (Updated)

Complete documentation covering:
- All 39 tables with column definitions
- All 25 views with SQL definitions
- All triggers with descriptions
- All significant indices
- Relationship diagram
- Version history

### 2. SCHEMA_CHANGES_LOG.md

```markdown
# Schema Changes Since Last Documentation

## New Tables (X added)
| Table Name | Purpose | Added In |
|------------|---------|----------|
| ... | ... | ... |

## New Views (X added)
| View Name | Purpose | Added In |
|-----------|---------|----------|
| ... | ... | ... |

## Modified Tables (X changed)
| Table | Change | Reason |
|-------|--------|--------|
| ... | Added column X | ... |

## Removed Elements
| Type | Name | Removed In |
|------|------|------------|
| ... | ... | ... |
```

### 3. SCHEMA_SNAPSHOT.sql

```sql
-- Complete schema snapshot
-- Generated: [timestamp]

-- Tables
CREATE TABLE tracks (...);
...

-- Views
CREATE VIEW active_tasks AS ...;
...

-- Triggers
CREATE TRIGGER trg_task_updated ...;
...

-- Indices
CREATE INDEX idx_tasks_status ON tasks(status);
...
```

## Acceptance Criteria

- [ ] All 39 tables are documented with columns, types, constraints
- [ ] All 25 views are documented with SQL definitions
- [ ] All triggers are documented with behavior descriptions
- [ ] Tables are organized by logical domain
- [ ] Foreign key relationships are documented
- [ ] Schema version history is included
- [ ] Documentation matches actual database state

## Estimated Time

- Schema extraction: 30 minutes
- Existing documentation review: 20 minutes
- Documentation writing: 90 minutes
- Validation and formatting: 30 minutes
- **Total: ~3 hours**

## Notes

- Use PRAGMA commands as the source of truth
- Document column purposes based on naming and usage patterns
- Include example values where helpful
- Note any columns that appear unused
- Consider generating schema from documentation for validation
- Coordinate with Task 2.2 (Migration Audit) for context
