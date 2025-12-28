# Task 6.5: Validate Progress Tracking Accuracy

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QTB |
| Sprint | 6 - Friction & Progress Tracking |
| Type | testing |
| Complexity | medium |
| Priority | high |
| Estimated Tokens | ~2,000 |
| Dependencies | Sprint 5 (Remediation complete) |

---

## Objective

Validate that the roadmap progress tracking system (track/sprint/task completion percentages) accurately reflects the actual state of the repository after all remediation work. Compare CLI-reported progress with manual verification, document any discrepancies, identify root causes, and ensure the progress tracking system can be trusted for ongoing monitoring.

---

## Analysis Approach

### Phase 1: Rebuild Clean State

Ensure database reflects current YAML state before validation.

### Phase 2: Collect CLI-Reported Progress

Capture all progress metrics as reported by the CLI.

### Phase 3: Manual Verification

Independently calculate progress from raw data sources.

### Phase 4: Compare and Document Discrepancies

Identify mismatches, investigate causes, and document findings.

### Phase 5: Validate Edge Cases

Test progress calculation with various scenarios.

---

## Implementation Steps

### Step 1: Rebuild Database

Ensure a clean, synchronized state before testing.

```bash
# Backup current database
cp .vibey/roadmap.db .vibey/roadmap.db.pre-validation

# Rebuild from YAML sources
vibey roadmap db rebuild --force

# Verify rebuild success
vibey roadmap db status
```

**Validation:**
- Rebuild completes without errors
- db status shows "synchronized"
- No orphaned records reported

### Step 2: Capture CLI Progress Output

```bash
# Full roadmap status
vibey roadmap status > /tmp/cli_progress_full.txt

# Track-level progress
vibey roadmap status --tracks > /tmp/cli_tracks.txt

# Sprint-level progress (for each active track)
vibey roadmap status --sprints > /tmp/cli_sprints.txt

# Task-level status counts
vibey roadmap status --tasks > /tmp/cli_tasks.txt

# JSON output for programmatic comparison
vibey roadmap status --json > /tmp/cli_progress.json
```

### Step 3: Manual Database Verification

Execute raw SQL queries against the database to independently calculate progress.

#### Track Progress Query

```sql
-- Calculate track progress manually
SELECT
  t.id AS track_id,
  t.name AS track_name,
  t.status AS track_status,
  COUNT(task.id) AS total_tasks,
  COUNT(CASE WHEN task.status = 'completed' THEN 1 END) AS completed_tasks,
  ROUND(
    COUNT(CASE WHEN task.status = 'completed' THEN 1 END) * 100.0 /
    NULLIF(COUNT(task.id), 0),
    2
  ) AS calculated_progress
FROM tracks t
LEFT JOIN sprints s ON s.track_id = t.id
LEFT JOIN tasks task ON task.sprint_id = s.id
GROUP BY t.id
ORDER BY t.name;
```

#### Sprint Progress Query

```sql
-- Calculate sprint progress manually
SELECT
  s.id AS sprint_id,
  s.name AS sprint_name,
  s.status AS sprint_status,
  t.name AS track_name,
  COUNT(task.id) AS total_tasks,
  COUNT(CASE WHEN task.status = 'completed' THEN 1 END) AS completed_tasks,
  COUNT(CASE WHEN task.status = 'in_progress' THEN 1 END) AS in_progress_tasks,
  COUNT(CASE WHEN task.status = 'not_started' THEN 1 END) AS not_started_tasks,
  ROUND(
    COUNT(CASE WHEN task.status = 'completed' THEN 1 END) * 100.0 /
    NULLIF(COUNT(task.id), 0),
    2
  ) AS calculated_progress
FROM sprints s
LEFT JOIN tracks t ON s.track_id = t.id
LEFT JOIN tasks task ON task.sprint_id = s.id
GROUP BY s.id
ORDER BY t.name, s.name;
```

#### Task Status Distribution Query

```sql
-- Overall task status distribution
SELECT
  status,
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 2) AS percentage
FROM tasks
GROUP BY status
ORDER BY count DESC;
```

#### Orphan Detection Query

```sql
-- Find orphaned tasks (no sprint)
SELECT id, title, status
FROM tasks
WHERE sprint_id IS NULL;

-- Find orphaned sprints (no track)
SELECT id, name, status
FROM sprints
WHERE track_id IS NULL;
```

### Step 4: Compare Results

Create comparison script or manually compare:

```bash
# Export manual calculations
sqlite3 .vibey/roadmap.db < manual_queries.sql > /tmp/manual_progress.txt

# Compare files
diff /tmp/cli_progress_full.txt /tmp/manual_progress.txt

# Or use Python for structured comparison
python compare_progress.py
```

#### Comparison Script (compare_progress.py)

```python
#!/usr/bin/env python3
"""Compare CLI-reported progress with manual calculations."""

import json
import sqlite3
from pathlib import Path

def load_cli_progress():
    """Load CLI JSON output."""
    with open('/tmp/cli_progress.json') as f:
        return json.load(f)

def calculate_manual_progress(db_path: str = '.vibey/roadmap.db'):
    """Calculate progress directly from database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Track progress
    tracks = conn.execute("""
        SELECT
          t.id, t.name,
          COUNT(task.id) AS total,
          COUNT(CASE WHEN task.status = 'completed' THEN 1 END) AS completed
        FROM tracks t
        LEFT JOIN sprints s ON s.track_id = t.id
        LEFT JOIN tasks task ON task.sprint_id = s.id
        GROUP BY t.id
    """).fetchall()

    conn.close()
    return {
        'tracks': [dict(t) for t in tracks]
    }

def compare_progress():
    """Compare and report discrepancies."""
    cli = load_cli_progress()
    manual = calculate_manual_progress()

    discrepancies = []

    for cli_track in cli.get('tracks', []):
        manual_track = next(
            (t for t in manual['tracks'] if t['id'] == cli_track['id']),
            None
        )

        if manual_track:
            cli_pct = cli_track.get('progress', 0)
            manual_pct = (
                manual_track['completed'] / manual_track['total'] * 100
                if manual_track['total'] > 0 else 0
            )

            if abs(cli_pct - manual_pct) > 0.1:  # Allow 0.1% tolerance
                discrepancies.append({
                    'track': cli_track['name'],
                    'cli_progress': cli_pct,
                    'manual_progress': manual_pct,
                    'difference': cli_pct - manual_pct
                })

    return discrepancies

if __name__ == '__main__':
    discrepancies = compare_progress()
    if discrepancies:
        print("DISCREPANCIES FOUND:")
        for d in discrepancies:
            print(f"  {d['track']}: CLI={d['cli_progress']:.2f}%, "
                  f"Manual={d['manual_progress']:.2f}%, "
                  f"Diff={d['difference']:.2f}%")
    else:
        print("No discrepancies found. Progress tracking is accurate.")
```

### Step 5: Test Edge Cases

#### Edge Case 1: Empty Sprint

```bash
# Create a sprint with no tasks
vibey roadmap create sprint --track <track-id> --name "Empty Test Sprint"

# Check progress calculation
vibey roadmap status
# Expected: Sprint shows 0% or N/A, doesn't affect track average incorrectly
```

#### Edge Case 2: All Completed Sprint

```bash
# Verify 100% completion displays correctly
# Check that completed sprint doesn't show 100.0000001% (float precision)
```

#### Edge Case 3: Mixed Status Distribution

```sql
-- Verify correct counting with all statuses
SELECT
  COUNT(CASE WHEN status = 'not_started' THEN 1 END) AS not_started,
  COUNT(CASE WHEN status = 'in_progress' THEN 1 END) AS in_progress,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) AS completed,
  COUNT(CASE WHEN status = 'blocked' THEN 1 END) AS blocked,
  COUNT(*) AS total
FROM tasks;
```

#### Edge Case 4: Progress After Status Change

```bash
# Change a task status
vibey roadmap update task <task-id> --status completed

# Verify progress updates correctly
vibey roadmap status

# Change it back
vibey roadmap update task <task-id> --status in_progress

# Verify progress decreases correctly
vibey roadmap status
```

### Step 6: YAML-Database Consistency Check

```bash
# Count tasks in YAML files
find .vibey/roadmap/tasks -name '*.yaml' | wc -l

# Count tasks in database
sqlite3 .vibey/roadmap.db "SELECT COUNT(*) FROM tasks"

# Compare counts
# If mismatch, investigate missing/extra records
```

---

## Known Potential Discrepancy Causes

| Cause | Symptom | Resolution |
|-------|---------|------------|
| Stale database | Progress doesn't match YAML | `vibey roadmap db rebuild` |
| Float precision | 99.99999% instead of 100% | Round to 2 decimal places |
| Division by zero | NaN or error on empty sprint | Handle empty case |
| Status enum mismatch | Tasks not counted | Verify status values |
| Orphaned records | Incorrect totals | Clean orphans |
| Cache invalidation | Old progress shown | Force refresh |
| Concurrent modification | Race condition | Use transactions |

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `PROGRESS_TRACKING_VALIDATION_REPORT.md` | `sprint-6/outputs/` | Full validation results |
| `cli_progress.json` | `sprint-6/outputs/` | CLI output snapshot |
| `manual_progress.csv` | `sprint-6/outputs/` | Manual calculation results |
| `discrepancy_analysis.md` | `sprint-6/outputs/` | Root cause analysis (if any) |
| `edge_case_results.md` | `sprint-6/outputs/` | Edge case test results |

---

## Validation Report Template

```markdown
# Progress Tracking Validation Report

## Executive Summary

- **Validation Date:** Dec 28, 2024
- **Database Version:** post-remediation
- **Overall Result:** [PASS/FAIL]
- **Discrepancies Found:** [count]

## Methodology

1. Rebuilt database from YAML sources
2. Captured CLI progress output
3. Executed manual SQL verification queries
4. Compared results with 0.1% tolerance
5. Tested edge cases

## Results

### Track Progress Comparison

| Track | CLI Progress | Manual Calc | Match |
|-------|--------------|-------------|-------|
| Comprehensive Audit V2 | 85% | 85% | YES |
| Context System V2 | 45% | 45% | YES |

### Sprint Progress Comparison

| Sprint | CLI Progress | Manual Calc | Match |
|--------|--------------|-------------|-------|
| Sprint 1 | 100% | 100% | YES |
| Sprint 2 | 100% | 100% | YES |
| ...     | ...  | ...  | ... |

### Task Status Distribution

| Status | CLI Count | DB Count | Match |
|--------|-----------|----------|-------|
| completed | X | X | YES |
| in_progress | Y | Y | YES |
| not_started | Z | Z | YES |

## Discrepancies

[If any discrepancies found, document each one:]

### Discrepancy #1: [Title]

- **Location:** [Track/Sprint/Task]
- **CLI Value:** X%
- **Manual Value:** Y%
- **Difference:** Z%
- **Root Cause:** [Analysis]
- **Resolution:** [Fix applied or recommended]

## Edge Case Results

| Edge Case | Expected | Actual | Pass |
|-----------|----------|--------|------|
| Empty sprint | 0% or N/A | [result] | [Y/N] |
| 100% completion | 100.00% | [result] | [Y/N] |
| Status change | Updates immediately | [result] | [Y/N] |
| YAML-DB sync | Counts match | [result] | [Y/N] |

## Recommendations

1. [Recommendation based on findings]
2. [...]

## Conclusion

[Summary statement about progress tracking reliability]
```

---

## Acceptance Criteria

- [ ] Database rebuilt successfully before validation
- [ ] CLI progress output captured in all formats (text, JSON)
- [ ] Manual SQL queries executed and results documented
- [ ] Track progress comparison completed
- [ ] Sprint progress comparison completed
- [ ] Task status distribution verified
- [ ] YAML-DB count consistency verified
- [ ] At least 4 edge cases tested
- [ ] All discrepancies documented with root causes
- [ ] Validation report completed
- [ ] Progress tracking system trustworthiness determined

---

## Notes

- Run validation after Sprint 5 remediation is complete
- If discrepancies found, coordinate with Task 6.2 (automation) to add checks
- Consider adding progress validation to CI pipeline
- Document any floating-point precision issues for future reference
