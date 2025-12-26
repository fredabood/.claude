# Task 5: Remediate False Completion Statuses

**Task ID**: `01KDC9293X9AMMB8XRXQ7TJB1Q`
**Type**: development
**Priority**: high
**Estimated Tokens**: 4,000
**Blocked By**: Task 4 (Report Generation)

## Objective

Based on the audit report, revert falsely-completed tasks to appropriate status. Update affected sprint and track statuses. Document root cause and implement prevention measures.

## Prerequisites

- Task 4 (Report Generation) complete
- `DATA_INTEGRITY_AUDIT_REPORT.md` available
- `remediation-priority-list.md` available

## Methodology

### Step 1: Review Critical Issues

From the audit report, extract all critical issues requiring immediate remediation:

```bash
# Parse critical issues from report
grep -A 10 "### 9.1 Critical" DATA_INTEGRITY_AUDIT_REPORT.md
```

### Step 2: Create Backup

Before making any changes:

```bash
# Backup current state
cp -r .vibey/roadmap .vibey/roadmap.backup.$(date +%Y%m%d_%H%M%S)

# Backup database
cp .vibey/roadmap.db .vibey/roadmap.db.backup.$(date +%Y%m%d_%H%M%S)

# Create git tag for rollback
git tag -a "pre-remediation-$(date +%Y%m%d)" -m "State before data integrity remediation"
```

### Step 3: Remediate False Task Completions

For each falsely-completed task:

```bash
# Update task status via CLI
vibey roadmap update task $TASK_ID --status not_started

# Or directly update YAML
yq -i '.task.status = "not_started"' .vibey/roadmap/tasks/$TASK_ID.yaml
yq -i '.task.completed = null' .vibey/roadmap/tasks/$TASK_ID.yaml
yq -i '.task.started = null' .vibey/roadmap/tasks/$TASK_ID.yaml
```

### Step 4: Remediate False Sprint Completions

For each falsely-completed sprint:

```bash
# Update sprint status
vibey roadmap update sprint $SPRINT_ID --status in_progress

# Or directly update YAML
yq -i '.sprint.status = "in_progress"' .vibey/roadmap/sprints/$SPRINT_ID.yaml
yq -i '.sprint.completed = null' .vibey/roadmap/sprints/$SPRINT_ID.yaml
```

### Step 5: Remediate False Track Completions

For each falsely-completed track:

```bash
# Update track status
vibey roadmap update track $TRACK_ID --status in_progress

# Or directly update YAML
yq -i '.track.status = "in_progress"' .vibey/roadmap/tracks/$TRACK_ID.yaml
yq -i '.track.completed = null' .vibey/roadmap/tracks/$TRACK_ID.yaml
```

### Step 6: Rebuild Database

After YAML updates:

```bash
vibey roadmap db rebuild
```

### Step 7: Validate Remediations

```sql
-- Verify no false completions remain
SELECT COUNT(*) as remaining_issues
FROM tracks t
LEFT JOIN sprints s ON s.track_id = t.id
WHERE t.status IN ('completed', 'production_ready')
GROUP BY t.id
HAVING COUNT(CASE WHEN s.status NOT IN ('completed', 'production_ready') THEN 1 END) > 0;
```

### Step 8: Document Changes

Create a remediation log:

```markdown
# Remediation Log - {date}

## Tasks Reverted
| Task ID | Title | Old Status | New Status | Reason |
|---------|-------|------------|------------|--------|
| 01K... | ... | completed | not_started | No evidence of completion |

## Sprints Reverted
| Sprint ID | Name | Old Status | New Status | Reason |
|-----------|------|------------|------------|--------|
| 01K... | ... | production_ready | in_progress | Has incomplete tasks |

## Tracks Reverted
| Track ID | Name | Old Status | New Status | Reason |
|----------|------|------------|------------|--------|
| 01K... | ... | production_ready | in_progress | Has incomplete sprints |

## Backup References
- YAML backup: .vibey/roadmap.backup.{timestamp}
- Database backup: .vibey/roadmap.db.backup.{timestamp}
- Git tag: pre-remediation-{date}
```

### Step 9: Fix Auto-Completion Bug

If auto-completion bug was identified:

```python
# In vibey/operations/roadmap/status_manager.py or similar

def update_track_status(track_id, new_status):
    # Before setting to complete, verify all children are complete
    incomplete_sprints = get_incomplete_sprints(track_id)
    if new_status in ('completed', 'production_ready') and incomplete_sprints:
        raise ValidationError(
            f"Cannot mark track complete: {len(incomplete_sprints)} sprints incomplete"
        )
    # ... rest of update logic
```

### Step 10: Add Validation Gate

Create pre-completion validation:

```python
def validate_completion(entity_type, entity_id):
    """Validate all children are complete before allowing completion."""
    if entity_type == 'track':
        sprints = get_sprints_for_track(entity_id)
        incomplete = [s for s in sprints if s.status not in ('completed', 'production_ready')]
        if incomplete:
            return False, f"{len(incomplete)} sprints incomplete"

    elif entity_type == 'sprint':
        tasks = get_tasks_for_sprint(entity_id)
        incomplete = [t for t in tasks if t.status != 'completed']
        if incomplete:
            return False, f"{len(incomplete)} tasks incomplete"

    return True, None
```

## Remediation Checklist

### Unified Architecture Migration Track
- [ ] Revert "Execute migration and validate" task to not_started
- [ ] Revert "Database Schema Migration" sprint to in_progress
- [ ] Revert entire track to in_progress
- [ ] Add blocking note: "Schema v2 migration never executed"

### CLI Dogfooding Bug Fixes Track
- [ ] Revert track from production_ready to in_progress
- [ ] Add note: "Sprint 29 added for data integrity audit"

### Other Tracks (from audit)
- [ ] Review each track in audit report
- [ ] Revert as needed based on findings

## Success Criteria

- [ ] All false completions reverted
- [ ] Database rebuilt successfully
- [ ] Validation queries return 0 issues
- [ ] Remediation log created
- [ ] Auto-completion bug fixed (if applicable)
- [ ] Validation gates added
- [ ] Changes committed with detailed message

## Deliverables

1. `REMEDIATION_LOG.md` - Record of all changes
2. Updated YAML files with correct statuses
3. Bug fixes for auto-completion logic
4. Validation gate implementation
5. Git commit with all remediations

## Rollback Plan

If remediation causes issues:

```bash
# Restore from backup
rm -rf .vibey/roadmap
cp -r .vibey/roadmap.backup.{timestamp} .vibey/roadmap

# Or use git
git checkout pre-remediation-{date} -- .vibey/roadmap/

# Rebuild database
vibey roadmap db rebuild
```
