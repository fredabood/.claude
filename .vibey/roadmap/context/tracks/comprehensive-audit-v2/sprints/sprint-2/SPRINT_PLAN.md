# Sprint 2: Data Integrity Validation - Detailed Plan

## Sprint Overview

| Field | Value |
|-------|-------|
| Sprint ID | 01KDC9293X9AMMB8XRXQ7TJB1J |
| Track | Comprehensive Repository Audit V2 |
| Status | not_started |
| Tasks | 8 |
| Estimated Tokens | ~25,000 |
| Dependencies | None (can run parallel with Sprint 1) |

## Goal

Validate that all "completed" tasks in the roadmap actually correspond to completed work. This sprint was triggered by discovering that "Unified Architecture Migration" tasks were marked complete but the schema changes were never executed.

## Context

### The Problem
During routine roadmap review, we discovered:
- Tasks marked "completed" with no corresponding code changes
- Database schema v2 migration claimed complete but tables don't exist
- False completion percentages inflating track progress

### Audit Scope
- All tracks marked `completed` or `production_ready`
- All sprints with 100% completion
- All tasks with `status: completed` since Dec 1, 2024

---

## Task Details

### Task 2.1: Audit Completed Migration Tasks Against Database Schema

**Task ID:** `01KDC9293X9AMMB8XRXQ7TJB1K`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Cross-reference tasks that claim database schema changes with the actual schema. Verify tables, views, and triggers exist.

#### Implementation Steps

1. **Query all completed tasks mentioning "schema" or "database"**
   ```sql
   SELECT id, title, description, completed
   FROM tasks
   WHERE status = 'completed'
     AND (title LIKE '%schema%' OR title LIKE '%database%'
          OR title LIKE '%table%' OR title LIKE '%migration%')
   ORDER BY completed DESC;
   ```

2. **Extract claimed schema changes from task descriptions**
   - Look for table names mentioned
   - Look for column additions
   - Look for view creations

3. **Verify against actual schema**
   ```sql
   -- List all tables
   SELECT name FROM sqlite_master WHERE type='table';

   -- List all views
   SELECT name FROM sqlite_master WHERE type='view';

   -- Check if specific table exists
   SELECT sql FROM sqlite_master WHERE name='claimed_table_name';
   ```

4. **Generate discrepancy report**

#### Deliverables
- `SCHEMA_VALIDATION_REPORT.md` - Tasks vs actual schema
- List of false completions found
- List of legitimate completions verified

#### Acceptance Criteria
- [ ] All schema-related completed tasks checked
- [ ] Discrepancies documented with evidence
- [ ] False completions flagged for remediation

---

### Task 2.2: Audit Completed File Creation Tasks Against Filesystem

**Task ID:** `01KDC9293X9AMMB8XRXQ7TJB1M`
**Type:** research | **Complexity:** medium | **Priority:** high

#### Description
Verify that tasks claiming to create files actually resulted in those files existing.

#### Implementation Steps

1. **Query tasks with file creation deliverables**
   ```sql
   SELECT id, title, deliverables
   FROM tasks
   WHERE status = 'completed'
     AND deliverables LIKE '%create%'
   ORDER BY completed DESC;
   ```

2. **Extract claimed file paths from deliverables**
   - Parse deliverables YAML/JSON
   - Extract file paths mentioned

3. **Verify files exist**
   ```bash
   for file in $(cat claimed_files.txt); do
     if [ -f "$file" ]; then
       echo "EXISTS: $file"
     else
       echo "MISSING: $file"
     fi
   done
   ```

4. **Check git history for file creation**
   ```bash
   git log --diff-filter=A --name-only --format="" -- "$filepath"
   ```

#### Deliverables
- `FILE_CREATION_VALIDATION_REPORT.md`
- List of missing files claimed as created
- Verification of existing files

---

### Task 2.3: Cross-reference Unified Architecture Migration Track Status

**Task ID:** `01KDC9293X9AMMB8XRXQ7TJB1N`
**Type:** research | **Complexity:** complex | **Priority:** critical

**See:** `sprints/sprint-2/tasks/task-2-3-unified-arch/TASK_PLAN.md`

#### Description
Deep dive into the Unified Architecture Migration track that triggered this audit. Determine what was actually done vs what was claimed.

#### Background
The Unified Architecture Migration track claimed to:
- Migrate YAML format from v1 to v2
- Add new database tables for format_version
- Implement parent_ref relationship system

Investigation showed many of these changes weren't actually implemented.

#### Implementation Steps

1. **Get full track details**
   ```bash
   vibey roadmap show 01KC39XSXJ39N12HWJ93F77KQ9
   ```

2. **List all sprints and their status**

3. **For each "completed" task:**
   - Check git commits referenced
   - Verify code changes exist
   - Test claimed functionality

4. **Document findings**

#### Deliverables
- `UNIFIED_ARCH_MIGRATION_AUDIT.md`
- Task-by-task validation results
- Recommended status corrections

---

### Task 2.4: Audit Git History Against Roadmap Task Claims

**Task ID:** `01KDDE9NEKAH3BM9PRFPHNNCN8`
**Type:** research | **Complexity:** medium | **Priority:** medium

#### Description
Cross-reference git commits with roadmap task completions. Verify commits exist and contain relevant changes.

#### Implementation Steps

1. **Get all tasks with commit references**
   ```sql
   SELECT id, title, commits
   FROM tasks
   WHERE commits IS NOT NULL
     AND commits != '[]'
   ORDER BY completed DESC;
   ```

2. **For each commit hash:**
   ```bash
   # Verify commit exists
   git cat-file -t $commit_hash

   # Check commit message
   git log -1 --format="%s" $commit_hash

   # Check files changed
   git show --name-only --format="" $commit_hash
   ```

3. **Flag discrepancies:**
   - Non-existent commits
   - Commits unrelated to task
   - Commits by wrong author

#### Deliverables
- `GIT_COMMIT_VALIDATION_REPORT.md`
- Invalid commit references list
- Commit-to-task mapping verification

---

### Task 2.5: Audit Roadmap State for Orphans and Broken References

**Task ID:** `01KDDE9NEKAH3BM9PRFPHNNCNC`
**Type:** development | **Complexity:** medium | **Priority:** medium

#### Description
Find orphaned tasks (no sprint), orphaned sprints (no track), and broken dependency references.

#### Implementation Steps

1. **Find orphaned tasks**
   ```sql
   SELECT t.id, t.title
   FROM tasks t
   LEFT JOIN sprints s ON t.sprint_id = s.id
   WHERE s.id IS NULL;
   ```

2. **Find orphaned sprints**
   ```sql
   SELECT s.id, s.name
   FROM sprints s
   LEFT JOIN tracks tr ON s.track_id = tr.id
   WHERE tr.id IS NULL;
   ```

3. **Find broken depends_on references**
   ```sql
   -- Tasks depending on non-existent tasks
   SELECT t.id, t.title, d.value as depends_on
   FROM tasks t, json_each(t.depends_on) d
   WHERE d.value NOT IN (SELECT id FROM tasks);
   ```

4. **Find broken blocker references**
   ```sql
   -- Similar query for blocked_by field
   ```

5. **Generate cleanup recommendations**

#### Deliverables
- `ORPHAN_AUDIT_REPORT.md`
- List of orphaned entities
- Broken reference list
- Cleanup SQL/commands

---

### Task 2.6: Audit Track/Sprint Completion Status Accuracy

**Task ID:** `01KDDE9NEKAH3BM9PRFPHNNCND`
**Type:** research | **Complexity:** medium | **Priority:** medium

#### Description
Verify that track and sprint completion percentages match actual task completion counts.

#### Implementation Steps

1. **For each sprint, calculate actual completion:**
   ```sql
   SELECT
     s.id,
     s.name,
     s.progress->>'completion_percent' as claimed_percent,
     ROUND(
       SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) * 100.0 /
       NULLIF(COUNT(t.id), 0)
     ) as actual_percent
   FROM sprints s
   LEFT JOIN tasks t ON t.sprint_id = s.id
   GROUP BY s.id
   HAVING claimed_percent != actual_percent;
   ```

2. **For each track, calculate actual completion:**
   ```sql
   SELECT
     tr.id,
     tr.name,
     tr.progress->>'completion_percent' as claimed_percent,
     -- Calculate from sprints
   FROM tracks tr
   ...
   ```

3. **Document discrepancies**

#### Deliverables
- `PROGRESS_ACCURACY_REPORT.md`
- Tracks with incorrect percentages
- Sprints with incorrect percentages
- Recommended corrections

---

### Task 2.7: Update DATABASE_SCHEMA_DOCUMENTATION.md

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QSW`
**Type:** documentation | **Complexity:** medium | **Priority:** high

#### Description
The database schema has grown from 27 tables to 39 tables and from 21 views to 25 views since Dec 12. Update documentation to reflect current schema.

#### Source
Original documentation (if exists):
```
.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-*/DATABASE_SCHEMA_DOCUMENTATION.md
```

#### Implementation Steps

1. **Extract current schema**
   ```sql
   .schema  -- All CREATE statements
   ```

2. **Document each new table:**
   - Table name
   - Purpose
   - Columns with types
   - Foreign keys
   - Triggers

3. **Document each new view:**
   - View name
   - Purpose
   - Underlying query

4. **Create schema diagram** (optional)

#### Deliverables
- Updated `DATABASE_SCHEMA_DOCUMENTATION.md`
- Schema comparison (Dec 12 vs Dec 28)
- New table/view explanations

---

### Task 2.8: Update FILE_TO_ARTIFACT_MAPPING.yaml

**Task ID:** `01KDJNKE2B2W5NJRTSRZWN4QSX`
**Type:** documentation | **Complexity:** medium | **Priority:** medium

#### Description
Update the file-to-artifact mapping to reflect new database tables and views. Map new Python files to the database artifacts they create, query, or modify.

#### Implementation Steps

1. **Identify new database-related files**
   ```bash
   find vibey -name "*.py" -newer <dec12_marker> | \
     xargs grep -l "CREATE TABLE\|INSERT INTO\|SELECT.*FROM"
   ```

2. **Map each file to artifacts:**
   ```yaml
   vibey/roadmap/database/schema.py:
     creates:
       - tasks table
       - sprints table
       - tracks table
     modifies: []
     queries: []

   vibey/roadmap/database/crud/task.py:
     creates: []
     modifies:
       - tasks table
     queries:
       - tasks table
       - sprints table
   ```

3. **Update ARTIFACT_RELATIONSHIP_MODEL.md if needed**

#### Deliverables
- Updated `FILE_TO_ARTIFACT_MAPPING.yaml`
- Updated `ARTIFACT_RELATIONSHIP_MODEL.md` if needed

---

## Sprint Execution Order

```
Task 2.1 (schema) ──┬──> Task 2.7 (schema docs)
Task 2.2 (files)   ─┤
Task 2.3 (unified) ─┤
Task 2.4 (git)     ─┼──> Task 2.5 (orphans)
Task 2.6 (progress)─┤
                    └──> Task 2.8 (artifact mapping)
```

## Output Location

All deliverables should be placed in:
```
.vibey/roadmap/context/tracks/comprehensive-audit-v2/sprints/sprint-2/outputs/
```

## Success Criteria

- [ ] All 8 tasks completed
- [ ] All false completions identified
- [ ] All orphaned entities documented
- [ ] Schema documentation updated (27→39 tables)
- [ ] Artifact mappings current
- [ ] Data integrity issues catalogued for Sprint 5 remediation
