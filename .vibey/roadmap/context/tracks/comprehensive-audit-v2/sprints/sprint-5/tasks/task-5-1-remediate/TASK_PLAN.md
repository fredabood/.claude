# Task 5.1: Remediate False Completion Statuses - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDC9293X9AMMB8XRXQ7TJB1Q |
| Sprint | Sprint 5: Remediation & Reporting |
| Type | development |
| Complexity | **complex** |
| Priority | critical |
| Estimated Tokens | 5,000 |
| Dependencies | Sprint 2 (provides false completion list) |

## Objective

Fix all tasks, sprints, and tracks that are incorrectly marked as completed. This is the most critical remediation task as it directly affects roadmap integrity and progress reporting accuracy.

## Input Requirements

From Sprint 2 findings, we need:
1. List of falsely completed tasks (from Task 2.1-2.6)
2. Recommended new status for each
3. Evidence documentation for each change

## Remediation Process

### Step 1: Compile Master Correction List

Gather all findings into a single list:

```yaml
# corrections_master.yaml
false_completions:
  tasks:
    - id: 01KC...ABC
      title: "Create v2 schema tables"
      current_status: completed
      new_status: not_started
      reason: "No database tables exist"
      evidence: "PRAGMA table_info shows no v2 tables"
      sprint_id: 01KC...XYZ

    - id: 01KC...DEF
      title: "Migrate YAML format"
      current_status: completed
      new_status: in_progress
      reason: "Partially complete - 30% of files migrated"
      evidence: "grep shows 70% still use old format"
      sprint_id: 01KC...XYZ

  sprints:
    - id: 01KC...XYZ
      name: "Sprint 2: Schema Migration"
      current_status: completed
      new_status: in_progress
      reason: "3 of 8 tasks falsely marked complete"

  tracks:
    - id: 01KC39XSXJ39N12HWJ93F77KQ9
      name: "Unified Architecture Migration"
      current_status: completed
      new_status: in_progress
      reason: "Track contains false completions"
```

### Step 2: Backup Current State

```bash
# Create backup before any changes
cp .vibey/roadmap.db .vibey/roadmap.db.pre-remediation

# Export current status snapshot
sqlite3 .vibey/roadmap.db "
  SELECT id, title, status, completed
  FROM tasks
  WHERE status = 'completed'
" > pre_remediation_snapshot.csv

# Git commit current state
git add .vibey/roadmap/
git commit -m "chore: snapshot before false completion remediation"
```

### Step 3: Execute Task Status Corrections

For each false completion:

```bash
# Method 1: Using CLI
vibey roadmap update task 01KC...ABC --status not_started

# Method 2: Direct YAML edit (if CLI doesn't support)
# Edit the task YAML file directly

# Method 3: Database update (last resort)
sqlite3 .vibey/roadmap.db "
  UPDATE tasks
  SET status = 'not_started',
      completed = NULL
  WHERE id = '01KC...ABC';
"
```

#### Batch Processing Script

```python
#!/usr/bin/env python3
"""Remediate false completions from corrections file."""

import yaml
import subprocess
from pathlib import Path

def remediate_tasks(corrections_file: str):
    """Apply all task status corrections."""

    with open(corrections_file) as f:
        corrections = yaml.safe_load(f)

    results = []

    for task in corrections['false_completions']['tasks']:
        task_id = task['id']
        new_status = task['new_status']

        print(f"Fixing: {task['title']}")
        print(f"  {task['current_status']} -> {new_status}")

        # Execute correction
        result = subprocess.run(
            ['vibey', 'roadmap', 'update', 'task', task_id,
             '--status', new_status],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  ✅ Success")
            results.append({
                'task_id': task_id,
                'status': 'success',
                'new_status': new_status
            })
        else:
            print(f"  ❌ Failed: {result.stderr}")
            results.append({
                'task_id': task_id,
                'status': 'failed',
                'error': result.stderr
            })

    return results

if __name__ == '__main__':
    results = remediate_tasks('corrections_master.yaml')
    # Save results
    with open('remediation_results.yaml', 'w') as f:
        yaml.dump(results, f)
```

### Step 4: Clear Completion Dates

For tasks reverted to `not_started`:

```python
# Clear completed timestamp
for task_file in Path('.vibey/roadmap/tasks/').glob('*.yaml'):
    with open(task_file) as f:
        task = yaml.safe_load(f)

    if task['task']['id'] in reverted_task_ids:
        task['task']['completed'] = None
        task['task']['started'] = None  # Also clear if never started

        with open(task_file, 'w') as f:
            yaml.dump(task, f)
```

### Step 5: Rebuild Database

```bash
# Rebuild to recalculate all progress counters
vibey roadmap db rebuild --force

# Verify rebuild success
vibey roadmap db status
```

### Step 6: Verify Corrections

```bash
# Check corrected tasks
for task_id in $(cat corrected_task_ids.txt); do
  vibey roadmap show $task_id | grep -E "Status:|Completed:"
done

# Verify progress recalculation
vibey roadmap status | grep -E "Progress:|Completion:"

# Compare with pre-remediation
diff pre_remediation_progress.txt post_remediation_progress.txt
```

### Step 7: Document All Changes

Create detailed remediation log:

```markdown
# Remediation Log

## Execution Summary
- **Date:** Dec 28, 2024
- **Tasks Remediated:** X
- **Sprints Affected:** Y
- **Tracks Affected:** Z

## Individual Corrections

### Task Corrections (X total)

| Task ID | Title | Old Status | New Status | Reason |
|---------|-------|------------|------------|--------|
| 01KC... | Create v2 schema | completed | not_started | No tables exist |
| 01KC... | Migrate YAML | completed | in_progress | 30% complete |

### Sprint Recalculations (Y total)

| Sprint | Before | After |
|--------|--------|-------|
| Sprint 2 | 100% | 62.5% |

### Track Recalculations (Z total)

| Track | Before | After |
|-------|--------|-------|
| Unified Arch Migration | 100% | 45% |

## Commands Executed
```bash
[List all commands run]
```

## Backup Information
- Pre-remediation DB: .vibey/roadmap.db.pre-remediation
- Pre-remediation commit: [hash]
- Post-remediation commit: [hash]
```

## Validation Checklist

- [ ] All false completions identified in Sprint 2 addressed
- [ ] No task marked completed without evidence
- [ ] Sprint progress accurately reflects task statuses
- [ ] Track progress accurately reflects sprint statuses
- [ ] Database integrity verified
- [ ] YAML files consistent with database
- [ ] Remediation log complete

## Rollback Plan

If issues discovered:

```bash
# Restore database
cp .vibey/roadmap.db.pre-remediation .vibey/roadmap.db

# Or git revert
git revert HEAD  # If changes committed
```

## Deliverables

1. **REMEDIATION_LOG.md**
   - Complete record of all changes
   - Before/after comparison

2. **remediation_results.yaml**
   - Machine-readable results

3. **PROGRESS_COMPARISON.md**
   - Track/sprint progress before vs after

## Estimated Time

- Compile correction list: 15 minutes
- Backup creation: 5 minutes
- Execute corrections: 30 minutes (depends on count)
- Database rebuild: 5 minutes
- Verification: 20 minutes
- Documentation: 30 minutes
- **Total: ~2 hours**

## Risk Mitigation

1. **Data Loss:** Full backup before any changes
2. **Wrong Corrections:** Review list with human before executing
3. **Cascade Effects:** Rebuild database to ensure consistency
4. **Rollback:** Keep backup until verified stable
