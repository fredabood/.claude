# Roadmap Audit Trail System

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Task:** roadmap-integrity-fixes-6-task-007
**Status:** ✅ Production Ready

---

## Overview

The audit trail system provides comprehensive tracking of all roadmap status changes with full accountability. Every status change to tracks, sprints, and tasks is automatically logged with who made the change, when, why, and what commit it's associated with.

### Key Features

- ✅ **Automatic Logging** - All CLI operations log changes automatically
- ✅ **Complete Context** - Who/when/why/commit for every change
- ✅ **Suspicious Change Detection** - Identifies rollbacks and anomalies
- ✅ **Rich Querying** - View by object, date range, or recent changes
- ✅ **Report Generation** - Detailed audit reports with filters
- ✅ **Git Integration** - Links changes to git commits

---

## Architecture

### Storage

**Location:** `.vibey/roadmap/audit-trail.yaml`

**Format:**
```yaml
audit_log:
  - timestamp: '2025-11-21T03:54:34.878635+00:00'
    object_type: task
    object_id: roadmap-integrity-fixes-6-task-007
    field: status
    old_value: not_started
    new_value: completed
    changed_by: system
    reason: Task completed via CLI by system
    commit: 087f906
    source: cli

metadata:
  last_updated: '2025-11-21T03:54:34.885278+00:00'
  total_entries: 1
```

### Fields

- **timestamp**: ISO 8601 timestamp with timezone
- **object_type**: `track`, `sprint`, or `task`
- **object_id**: Full ID of the object
- **field**: Field that changed (usually `status`)
- **old_value**: Previous value
- **new_value**: New value
- **changed_by**: Username who made the change
- **reason**: Human-readable reason for change
- **commit**: Git commit SHA (short form, 7 chars)
- **source**: Source of change (`cli`, `manual`, `automated`, `system`)

---

## Usage

### View Recent Changes

```bash
# Last 20 changes
vibey roadmap audit log

# Last 50 changes
vibey roadmap audit log --limit 50
```

**Output:**
```
📋 Recent Audit Trail Entries (last 20)
================================================================================

2025-11-21 03:54:34 - TASK: roadmap-integrity-fixes-6-task-007
  Field: status
  Change: not_started → completed
  By: system (cli)
  Reason: Task completed via CLI by system
  Commit: 087f906

================================================================================
Total entries shown: 1
```

### View Object History

```bash
# Track history
vibey roadmap audit show roadmap-integrity-fixes

# Sprint history
vibey roadmap audit show roadmap-integrity-fixes-6

# Task history
vibey roadmap audit show roadmap-integrity-fixes-6-task-007
```

**Output:**
```
📋 Audit Trail for roadmap-integrity-fixes-6-task-007
================================================================================

2025-11-21 03:54:34
  Field: status
  Change: not_started → completed
  By: system (cli)
  Reason: Task completed via CLI by system
  Commit: 087f906

================================================================================
Total changes: 1
```

### Detect Suspicious Changes

```bash
vibey roadmap audit suspicious
```

**Detects:**
- Status rollbacks (e.g., `completed` → `not_started`)
- Progress decreases (e.g., 75% → 50%)
- Manual YAML edits without git commits
- Unexpected status transitions

**Output:**
```
⚠️  Suspicious Changes Detected: 3
================================================================================

⚠️  Status rollback: completed → in_progress
  Object: TASK roadmap-system-1-task-003
  Field: status
  Change: completed → in_progress
  When: 2025-11-20 15:30:00
  By: user (manual)
  Reason: Reopening task due to bug found
  Commit: abc1234

================================================================================
Total suspicious changes: 3
```

### Generate Reports

```bash
# Full audit report
vibey roadmap audit report

# Report for specific object
vibey roadmap audit report --object-id roadmap-integrity-fixes

# Report for date range
vibey roadmap audit report --start 2025-01-01 --end 2025-01-31

# Combined filters
vibey roadmap audit report --object-id roadmap-system --start 2025-01-01
```

**Output:**
```
================================================================================
Audit Trail Report
================================================================================
Total entries: 50
Filtered to object: roadmap-integrity-fixes
Date range: 2025-01-01 to now

Recent Changes:
--------------------------------------------------------------------------------

2025-11-21 03:54:34 - TASK: roadmap-integrity-fixes-6-task-007
  Field: status
  Change: not_started → completed
  By: system (cli)
  Reason: Task completed via CLI by system
  Commit: 087f906

...

================================================================================
```

---

## Automatic Logging

### CLI Operations

The following CLI commands automatically log to the audit trail:

**Task Operations:**
- `vibey roadmap start <task-id>` - Logs status change to `in_progress`
- `vibey roadmap complete <task-id>` - Logs status change to `completed`

**Sprint Operations:**
- `vibey roadmap start <sprint-id>` - Logs status change to `in_progress`
- `vibey roadmap complete <sprint-id>` - Logs status change to `completed`

**Auto-logging includes:**
- Current user (via `getpass.getuser()`)
- Git commit SHA (via `git rev-parse HEAD`)
- Automatic reason generation
- Source marked as `cli`

---

## Integration Points

### In Update Operations

The audit trail integrates with `vibey/operations/roadmap/update.py`:

```python
from vibey.operations.roadmap.audit_trail import log_status_change

# In complete_task function:
old_status = task.status.value
task.status = TaskStatus.COMPLETED

log_status_change(
    root_dir=root_dir,
    object_type="task",
    object_id=task_id,
    old_status=old_status,
    new_status="completed",
    reason=f"Task completed via CLI by {completed_by}",
    changed_by=completed_by
)
```

### API Reference

**Module:** `vibey.operations.roadmap.audit_trail`

**Classes:**
- `AuditEntry` - Single audit trail entry
- `AuditTrail` - Complete audit trail with metadata
- `AuditTrailManager` - Manages storage and operations

**Functions:**
- `log_status_change()` - Log a status change
- `log_progress_change()` - Log a progress change

**Manager Methods:**
- `load_trail()` - Load audit trail from disk
- `log_change()` - Log any change
- `get_recent_changes(limit)` - Get recent entries
- `get_object_history(object_id)` - Get object history
- `get_field_history(object_id, field)` - Get field history
- `detect_suspicious_changes()` - Find anomalies
- `generate_report()` - Generate detailed report

---

## Suspicious Change Detection

### Detected Patterns

**Status Rollbacks:**
- `completed` → `in_progress` or `not_started`
- `production_ready` → any earlier status

**Progress Decreases:**
- `tasks_completed` decreases
- `sprints_completed` decreases
- `completion_percent` decreases

**Manual Edits:**
- Changes with source=`manual` and no git commit

### Use Cases

1. **Debugging** - Find when a task was incorrectly marked complete
2. **Accountability** - Track who made manual YAML edits
3. **Quality** - Detect retroactive status changes
4. **Auditing** - Ensure changes follow proper workflow

---

## Best Practices

### Do's ✅

- ✅ Use CLI commands for all status changes
- ✅ Review audit trail regularly (`vibey roadmap audit log`)
- ✅ Investigate suspicious changes immediately
- ✅ Use audit trail for debugging status issues
- ✅ Generate reports for retrospectives
- ✅ Check audit trail before critical releases

### Don'ts ❌

- ❌ Don't manually edit YAML without documenting why
- ❌ Don't ignore suspicious change warnings
- ❌ Don't roll back statuses without good reason
- ❌ Don't bypass audit trail (no way to do this anyway)
- ❌ Don't assume audit trail = git history (it's complementary)

---

## Troubleshooting

### No Audit Entries Shown

**Problem:** `vibey roadmap audit log` shows "No audit trail entries found"

**Cause:** Audit trail file doesn't exist or is empty

**Solution:**
```bash
# Check if file exists
ls -la .vibey/roadmap/audit-trail.yaml

# If missing, it will be created on next status change
vibey roadmap start <any-task-id>
```

### Audit File Corrupted

**Problem:** YAML parsing error when reading audit trail

**Cause:** Manual edit introduced syntax error

**Solution:**
```bash
# Backup current file
cp .vibey/roadmap/audit-trail.yaml .vibey/roadmap/audit-trail.yaml.backup

# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/audit-trail.yaml'))"

# If invalid, check backup or restore from git
git checkout .vibey/roadmap/audit-trail.yaml
```

### Missing Commit SHAs

**Problem:** Audit entries show `commit: null`

**Cause:** Not in a git repository or git not in PATH

**Solution:**
```bash
# Verify git is available
git --version

# Verify in git repository
git rev-parse HEAD

# Audit trail will work without git, but won't link to commits
```

### Wrong User Showing

**Problem:** Audit trail shows wrong username

**Cause:** `getpass.getuser()` returns system username, not git config

**Solution:**
- This is expected behavior
- User is OS-level username, not git user
- Commit SHA links to git user info
- Can cross-reference via: `git show <commit> --format="%an %ae"`

---

## Performance Considerations

### File Size

- Each audit entry: ~200-300 bytes
- 1000 entries: ~250 KB
- 10,000 entries: ~2.5 MB

**Recommendation:** Archive or rotate audit trail yearly for large projects

### Read Performance

- Loading audit trail: O(n) where n = number of entries
- Recent queries: O(1) - just slice last N
- Object history: O(n) - scan all entries
- Suspicious detection: O(n) - scan all entries

**Optimization:** Keep audit trail under 10,000 entries for sub-100ms queries

---

## Future Enhancements

### Planned Features

1. **Rotation** - Auto-archive audit trail by year/quarter
2. **Compression** - Gzip old audit files
3. **Revert** - `vibey roadmap audit revert <entry-id>`
4. **Diff** - Show detailed field diffs for complex changes
5. **Export** - Export audit trail to JSON/CSV
6. **Filtering** - More granular filters (by user, by source, etc.)
7. **Webhooks** - Trigger notifications on suspicious changes
8. **Dashboard** - Web UI for audit trail visualization

---

## Security Considerations

### Audit Trail Integrity

**Threat:** Malicious user edits audit trail to hide changes

**Mitigation:**
- Audit trail is in git (tamper evident)
- Manual edits are suspicious (detection)
- Consider signing audit entries (future)

**Recommendation:** Review audit trail in git history alongside code changes

### Sensitive Data

**Threat:** Audit trail exposes sensitive information

**Current:** Only logs status changes, not data values

**Recommendation:** Don't put secrets in status reasons

---

## Related Documentation

- [Validation System](./ADVANCED_VALIDATION_AND_REPAIR.md) - Data integrity checks
- [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md) - Local validation
- [CI/CD Validation](./CI_CD_VALIDATION.md) - Automated checks
- [Branch Protection](./BRANCH_PROTECTION_SETUP.md) - Merge requirements

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
