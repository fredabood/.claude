# Task 2.4: Audit Git History Against Roadmap Task Claims - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | TBD (assign during execution) |
| Sprint | Sprint 2: Data Integrity Validation |
| Type | audit |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 3,500 |
| Dependencies | Sprint 1.5 completion (baseline data) |

## Objective

Cross-reference git commit history with completed roadmap tasks to verify work was actually performed. Check commit messages for task ID references and identify tasks marked complete that have no associated commits.

## Background

### Problem Statement
Tasks can be marked "completed" without any actual code being committed. By analyzing git history, we can identify:
- Tasks with legitimate commit evidence
- Tasks with no commits at all
- Tasks with unrelated or insufficient commits

### Why This Matters
- **Accountability:** Completed tasks should have traceable work
- **Audit Trail:** Git commits provide objective evidence of work performed
- **Process Validation:** Helps identify if completion is being rubber-stamped

## Investigation Steps

### Step 1: Export Completed Tasks With Timestamps

```sql
-- Get all completed tasks with completion dates
SELECT
  t.id,
  t.title,
  t.completed,
  t.commits,
  s.name AS sprint_name,
  tr.name AS track_name
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
ORDER BY t.completed;
```

### Step 2: Search Git History for Task References

```bash
# Search for commits mentioning task IDs (ULID format)
git log --all --oneline --grep="01K" | head -100

# Search for commits with specific task IDs
for task_id in $(sqlite3 .vibey/roadmap.db "SELECT id FROM tasks WHERE status='completed'"); do
  echo "=== Task: $task_id ==="
  git log --all --oneline --grep="$task_id"
done

# Search for commits mentioning task titles
git log --all --oneline --grep="migration"
git log --all --oneline --grep="schema"
git log --all --oneline --grep="audit"
```

### Step 3: Analyze Commits Around Completion Dates

```bash
# For each completed task, find commits around its completion date
# Example: Task completed on 2024-12-15
git log --all --oneline --after="2024-12-14" --before="2024-12-16"

# Script to automate this
#!/bin/bash
while IFS='|' read -r task_id completion_date title; do
  echo "=== Task: $task_id ($title) ==="
  echo "Completed: $completion_date"

  # Get commits in 3-day window around completion
  start_date=$(date -d "$completion_date - 1 day" +%Y-%m-%d)
  end_date=$(date -d "$completion_date + 1 day" +%Y-%m-%d)

  git log --all --oneline --after="$start_date" --before="$end_date"
  echo ""
done < completed_tasks.txt
```

### Step 4: Check Commits Field in Tasks

```sql
-- Tasks with commits listed
SELECT id, title, commits
FROM tasks
WHERE status = 'completed'
  AND commits IS NOT NULL
  AND commits != '';

-- Tasks without commits listed
SELECT id, title
FROM tasks
WHERE status = 'completed'
  AND (commits IS NULL OR commits = '');
```

### Step 5: Verify Referenced Commits Exist

```bash
# For tasks that list commits, verify they exist
for commit_hash in $(cat task_commits.txt); do
  if git rev-parse --verify "$commit_hash^{commit}" >/dev/null 2>&1; then
    echo "$commit_hash: EXISTS"
    git show --stat "$commit_hash"
  else
    echo "$commit_hash: NOT FOUND"
  fi
done
```

### Step 6: Build Evidence Matrix

| Task ID | Title | Completion Date | Listed Commits | Found Commits | Evidence Level |
|---------|-------|-----------------|----------------|---------------|----------------|
| 01KC... | Add X feature | 2024-12-15 | abc123 | Verified | STRONG |
| 01KC... | Create Y file | 2024-12-16 | None | 0 near date | NONE |
| 01KC... | Update Z | 2024-12-17 | def456 | Not found | INVALID |

## Git Commands Reference

### Find All Commits in Date Range
```bash
git log --all --oneline --after="2024-12-01" --before="2024-12-31"
```

### Find Commits Touching Specific Files
```bash
git log --all --oneline -- "vibey/*.py"
git log --all --oneline -- ".vibey/roadmap/*.yaml"
```

### Find Commits by Author Pattern
```bash
git log --all --oneline --author="name"
```

### Get Commit Details
```bash
git show --stat <commit-hash>
git show --name-only <commit-hash>
git diff <commit-hash>^..<commit-hash>
```

### Find Commits Mentioning Keywords
```bash
git log --all --oneline --grep="feat"
git log --all --oneline --grep="fix"
git log --all --oneline --grep="task"
```

### List All Commits With Stats
```bash
git log --all --oneline --shortstat
```

## Verification Steps

1. **Export Tasks:** Get all completed tasks with dates and commit refs
2. **Git Search:** Search for task IDs and related terms in commit messages
3. **Date Correlation:** Find commits around each task's completion date
4. **Commit Verification:** Verify listed commits actually exist
5. **Content Analysis:** Check if commit content relates to task claims
6. **Evidence Scoring:** Rate each task's evidence level

## Deliverables

### 1. GIT_HISTORY_AUDIT.md

```markdown
# Git History Cross-Reference Audit Results

## Executive Summary
- Total completed tasks analyzed: X
- Tasks with strong commit evidence: Y
- Tasks with weak evidence: Z
- Tasks with no evidence: W
- **Evidence Coverage:** Y/X (percentage)

## Methodology
1. Searched git history for task ID references
2. Analyzed commits within 3-day window of completion dates
3. Verified commits listed in task metadata
4. Scored evidence level for each task

## Evidence Categories
- **STRONG:** Direct commit reference, verified, content matches
- **MODERATE:** Commits near date, content possibly related
- **WEAK:** Commits near date, content unclear relation
- **NONE:** No commits found around completion date
- **INVALID:** Listed commits do not exist

## Findings

### Strong Evidence Tasks (Y tasks)
| Task ID | Title | Commit | Verified |
|---------|-------|--------|----------|
| ... | ... | abc123 | Files match claims |

### No Evidence Tasks (W tasks)
| Task ID | Title | Completed | Last Commit Before |
|---------|-------|-----------|-------------------|
| ... | ... | 2024-12-15 | 2024-12-10 (unrelated) |

### Suspicious Patterns
[Description of any concerning patterns discovered]

## Recommendations
1. [Tasks needing status review]
2. [Process improvements for commit tracking]
```

### 2. COMMIT_TASK_MAPPING.yaml

```yaml
# Mapping of commits to tasks
mappings:
  - task_id: 01KC...
    commits:
      - hash: abc123
        message: "feat: add migration support"
        date: "2024-12-15"
        files_changed: 5
        relevance: high
    evidence_level: strong

  - task_id: 01KC...
    commits: []
    evidence_level: none
    notes: "No commits found within 7 days of completion"
```

### 3. STATUS_CORRECTIONS.yaml

```yaml
# Tasks requiring investigation/correction
corrections:
  - task_id: 01KC...
    old_status: completed
    recommended_action: investigate
    reason: "No commit evidence for claimed work"
    evidence_level: none

  - task_id: 01KC...
    old_status: completed
    recommended_action: update_commits
    reason: "Listed commit does not exist"
    invalid_commit: xyz789
```

## Acceptance Criteria

- [ ] All completed tasks have been cross-referenced with git history
- [ ] Commits within +/- 3 days of each completion date have been analyzed
- [ ] Task-listed commits have been verified for existence
- [ ] Each task has an assigned evidence level
- [ ] Tasks with no evidence are flagged for review
- [ ] GIT_HISTORY_AUDIT.md provides clear findings and recommendations

## Estimated Time

- Task export and preparation: 20 minutes
- Git history analysis: 60 minutes
- Commit verification: 30 minutes
- Evidence scoring: 30 minutes
- Report generation: 30 minutes
- **Total: ~3 hours**

## Notes

- Consider that some work may be in branches not yet merged
- Check for squashed commits that may contain multiple tasks
- Document any commits that appear to do task work without references
- Flag tasks completed on dates with no repository activity
- Be aware of commit message conventions used in the repository
