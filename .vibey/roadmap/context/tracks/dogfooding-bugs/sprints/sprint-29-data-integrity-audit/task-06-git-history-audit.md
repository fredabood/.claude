# Task 6: Audit Git History Against Roadmap Task Claims

**Task ID**: `01KDDE9NEKAH3BM9PRFPHNNCN8`
**Type**: research
**Priority**: high
**Estimated Tokens**: 4,000

## Objective

Cross-reference git commit history with completed task claims. Identify tasks marked complete that have no corresponding commits, and commits that reference tasks not marked complete.

## Methodology

### Step 1: Extract All Completed Development Tasks

```sql
SELECT t.id, t.title, t.description, t.completed,
       s.name as sprint_name, tr.name as track_name
FROM tasks t
JOIN sprints s ON t.sprint_id = s.id
JOIN tracks tr ON s.track_id = tr.id
WHERE t.status = 'completed'
AND t.task_type IN ('development', 'bug', 'infrastructure')
ORDER BY t.completed DESC;
```

### Step 2: Search Git History for Task References

For each completed task, search for commits that reference it:

```bash
# Search by task ULID
git log --all --oneline --grep="$TASK_ID"

# Search by task title keywords
git log --all --oneline --grep="$KEYWORD"

# Search commit messages for task patterns
git log --all --oneline | grep -i "$PATTERN"
```

### Step 3: Analyze Commit-Task Associations

Check existing `task_commit_links` and `commits` tables:

```sql
-- Tasks with linked commits
SELECT t.id, t.title, COUNT(tcl.commit_hash) as commit_count
FROM tasks t
LEFT JOIN ticket_commit_links tcl ON t.id = tcl.ticket_id
WHERE t.status = 'completed'
GROUP BY t.id
HAVING commit_count = 0;

-- Commits in database
SELECT hash, message, author_date
FROM commits
ORDER BY author_date DESC
LIMIT 50;
```

### Step 4: Identify Orphan Commits

Find commits that mention task IDs not in the roadmap:

```bash
# Extract all task IDs mentioned in commits
git log --all --oneline | grep -oE '01K[A-Z0-9]{23}' | sort -u > commit_task_ids.txt

# Compare with actual task IDs
sqlite3 .vibey/roadmap.db "SELECT id FROM tasks" | sort > actual_task_ids.txt

# Find orphan references
comm -23 commit_task_ids.txt actual_task_ids.txt
```

### Step 5: Timeline Analysis

For tasks with commits, verify timeline consistency:
- Task `completed` date should be after or near commit date
- Large gaps suggest status manipulation

```sql
SELECT t.id, t.title, t.completed as task_completed,
       c.author_date as commit_date,
       julianday(t.completed) - julianday(c.author_date) as days_diff
FROM tasks t
JOIN ticket_commit_links tcl ON t.id = tcl.ticket_id
JOIN commits c ON tcl.commit_hash = c.hash
WHERE t.status = 'completed'
ORDER BY days_diff DESC;
```

## Expected Output

```markdown
## Git History Audit Results

### Tasks with Verified Commits (N tasks)
| Task ID | Title | Commits | Files Changed |
|---------|-------|---------|---------------|
| 01K... | Add feature X | 3 | foo.py, bar.py |

### Tasks with No Commits (N tasks) - SUSPICIOUS
| Task ID | Title | Claimed Complete | Investigation |
|---------|-------|------------------|---------------|
| 01K... | Implement Y | 2025-12-15 | No matching commits found |

### Orphan Commit References (N commits)
| Commit | Referenced ID | Status |
|--------|---------------|--------|
| abc123 | 01KXXX... | ID not found in roadmap |

### Timeline Anomalies (N tasks)
| Task ID | Completed | Last Commit | Gap (days) |
|---------|-----------|-------------|------------|
| 01K... | 2025-12-20 | 2025-11-01 | 49 |
```

## Red Flags to Watch For

1. **No commits for development task**: Task marked complete but no code changes
2. **Commit before task created**: Timeline inconsistency
3. **Large completion-commit gap**: Status may have been manually set
4. **Orphan task references**: Commits mention deleted/renamed tasks
5. **Bulk completion dates**: Many tasks completed same minute (automation issue)

## Success Criteria

- [ ] All completed development tasks queried
- [ ] Git history searched for each task
- [ ] Commit-task associations analyzed
- [ ] Orphan references identified
- [ ] Timeline anomalies flagged
- [ ] Recommendations generated

## Tools

- Git CLI for history searches
- SQLite for task queries
- Bash for cross-referencing
- Python for timeline analysis

## Deliverables

1. `git-history-audit-results.json` - Structured findings
2. List of tasks needing status review
3. Summary section for final report
