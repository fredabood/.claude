# Task 2.1: Audit Completed File Creation Tasks Against Filesystem - Detailed Plan

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

Query all completed tasks that claim to have created files or directories, then verify those artifacts actually exist in the filesystem. Flag any tasks marked complete where the referenced files do not exist.

## Background

### Problem Statement
Tasks can be marked as "completed" with deliverables claiming file or directory creation, but without verification that those files were actually created. This creates false confidence in roadmap progress.

### Why This Matters
- **Roadmap Integrity:** Progress percentages become meaningless if completed tasks didn't deliver
- **Future Planning:** Teams may depend on artifacts that don't exist
- **Audit Trail:** Discrepancies indicate process failures that should be addressed

## Investigation Steps

### Step 1: Query Completed Tasks With File Creation Claims

```sql
-- Find tasks claiming file/directory creation
SELECT
  t.id,
  t.title,
  t.status,
  t.completed,
  t.deliverables,
  s.name AS sprint_name,
  tr.name AS track_name
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
  AND (
    t.deliverables LIKE '%create%'
    OR t.deliverables LIKE '%file%'
    OR t.deliverables LIKE '%.py%'
    OR t.deliverables LIKE '%.yaml%'
    OR t.deliverables LIKE '%.md%'
    OR t.deliverables LIKE '%directory%'
    OR t.deliverables LIKE '%folder%'
    OR t.title LIKE '%create%'
    OR t.title LIKE '%add%file%'
  )
ORDER BY t.completed DESC;
```

### Step 2: Extract File Paths From Deliverables

Parse deliverables for:
- Explicit file paths (e.g., `vibey/cli/commands.py`)
- Relative paths (e.g., `./docs/SETUP.md`)
- Glob patterns (e.g., `tests/*.py`)
- Directory references (e.g., `vibey/operations/`)

```bash
# Export deliverables for analysis
sqlite3 .vibey/roadmap.db "
  SELECT t.id, t.deliverables
  FROM tasks t
  WHERE t.status = 'completed'
    AND t.deliverables IS NOT NULL
    AND t.deliverables != ''
" > /tmp/task_deliverables.txt
```

### Step 3: Verify Each File's Existence

```bash
#!/bin/bash
# Verification script for claimed files

AUDIT_OUTPUT="FILE_CREATION_AUDIT.md"

while IFS='|' read -r task_id file_path; do
  if [ -e "$file_path" ]; then
    echo "| $task_id | $file_path | EXISTS |" >> $AUDIT_OUTPUT
  else
    echo "| $task_id | $file_path | MISSING |" >> $AUDIT_OUTPUT
  fi
done < claimed_files.txt
```

### Step 4: Cross-Reference With Git History

```bash
# For missing files, check if they were ever created then deleted
for file in $(cat missing_files.txt); do
  echo "=== $file ==="
  git log --all --full-history -- "$file"
done
```

### Step 5: Build Verification Matrix

For each completed task with file claims:

| Task ID | Claimed File | Exists? | Git History | Verdict |
|---------|--------------|---------|-------------|---------|
| 01KC... | vibey/new_feature.py | NO | Never existed | FALSE |
| 01KC... | docs/guide.md | YES | Created in abc123 | TRUE |
| 01KC... | tests/test_x.py | NO | Deleted in def456 | STALE |

## SQL Queries Reference

### Query 1: All Completed Tasks With Deliverables
```sql
SELECT
  t.id,
  t.title,
  t.completed,
  t.deliverables
FROM tasks t
WHERE t.status = 'completed'
  AND t.deliverables IS NOT NULL
  AND LENGTH(t.deliverables) > 0
ORDER BY t.completed;
```

### Query 2: Count Completed Tasks By Track
```sql
SELECT
  tr.name AS track_name,
  COUNT(t.id) AS completed_tasks
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
GROUP BY tr.id
ORDER BY completed_tasks DESC;
```

### Query 3: Tasks With Specific File Extensions
```sql
SELECT id, title, deliverables
FROM tasks
WHERE status = 'completed'
  AND (
    deliverables LIKE '%.py%'
    OR deliverables LIKE '%.yaml%'
    OR deliverables LIKE '%.md%'
    OR deliverables LIKE '%.json%'
  );
```

## Verification Steps

1. **Data Extraction:** Export all completed tasks with deliverables
2. **Path Parsing:** Extract file/directory paths from deliverable text
3. **Filesystem Check:** Test existence of each claimed path
4. **Git Verification:** Check history for missing files
5. **Matrix Population:** Document findings in structured format
6. **False Positive Check:** Ensure deliverables are file claims, not descriptions

## Deliverables

### 1. FILE_CREATION_AUDIT.md

```markdown
# File Creation Task Audit Results

## Executive Summary
- Total completed tasks analyzed: X
- Tasks with file creation claims: Y
- Files verified as existing: Z
- Files missing: W
- **Integrity Score:** Z/Y (percentage)

## Methodology
[Description of verification approach]

## Findings

### Verified File Creations (Z tasks)
| Task ID | Title | File(s) Created | Verification |
|---------|-------|-----------------|--------------|
| ... | ... | ... | EXISTS |

### Missing Files (W tasks)
| Task ID | Title | Claimed File | Last Known State |
|---------|-------|--------------|------------------|
| ... | ... | ... | Never existed |

### Recommendations
1. [Status corrections needed]
2. [Process improvements]
```

### 2. STATUS_CORRECTIONS.yaml

```yaml
# Tasks requiring status correction
corrections:
  - task_id: 01KC...
    old_status: completed
    new_status: not_started
    reason: "Claimed file does not exist"
    missing_file: "path/to/file.py"

  - task_id: 01KC...
    old_status: completed
    new_status: in_progress
    reason: "Partial deliverables - 2 of 5 files exist"
    missing_files:
      - "path/to/missing1.py"
      - "path/to/missing2.py"
```

## Acceptance Criteria

- [ ] All completed tasks with file claims have been audited
- [ ] Each claimed file path has been tested for existence
- [ ] Missing files have been documented with git history context
- [ ] STATUS_CORRECTIONS.yaml identifies tasks needing status changes
- [ ] FILE_CREATION_AUDIT.md provides executive summary and detailed findings
- [ ] No false positives (descriptions mistaken for file claims)

## Estimated Time

- Data extraction and parsing: 30 minutes
- Filesystem verification: 45 minutes
- Git history analysis: 30 minutes
- Report generation: 30 minutes
- **Total: ~2.5 hours**

## Notes

- Focus on `.vibey/roadmap/` directory for roadmap-related file claims
- Check `vibey/` package for code file claims
- Include `docs/` directory for documentation claims
- Consider that some files may have been moved/renamed rather than deleted
