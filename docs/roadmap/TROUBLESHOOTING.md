# Roadmap Validation Troubleshooting Guide

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Status:** ✅ Production Ready

---

## Overview

This guide provides solutions to common validation errors and issues encountered when using the Vibey roadmap validation system. Issues are organized by category with clear steps to diagnose and resolve each problem.

---

## Quick Diagnostic Commands

```bash
# Check validation system status
vibey roadmap validate-fast --profile standard

# Check advanced integrity
vibey roadmap validate-advanced

# Check for auto-repairable issues
vibey roadmap repair --all --dry-run

# Check pre-commit hook status
vibey roadmap check-hooks

# Check recent audit trail
vibey roadmap audit log

# Check for suspicious changes
vibey roadmap audit suspicious
```

---

## Common Validation Errors

### Error 1: YAML Syntax Error

**Symptom:**
```
❌ Validation errors found in track.yaml:
  Line 42: mapping values are not allowed here
```

**Cause:** Invalid YAML syntax (indentation, quotes, special characters)

**Diagnosis:**
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/track-1/track.yaml'))"
```

**Solutions:**

**Solution 1: Fix indentation**
```yaml
# ❌ BAD
track:
  id: example
 name: Wrong indentation  # Misaligned!

# ✅ GOOD
track:
  id: example
  name: Correct indentation
```

**Solution 2: Quote special characters**
```yaml
# ❌ BAD
track:
  name: Example: Track  # Colon breaks parsing!

# ✅ GOOD
track:
  name: "Example: Track"  # Quoted
```

**Solution 3: Use YAML linter**
```bash
# Install yamllint
pip install yamllint

# Lint file
yamllint .vibey/roadmap/track-1/track.yaml
```

---

### Error 2: Missing Required Field

**Symptom:**
```
❌ Missing required field 'status' in task example-task-001
```

**Cause:** Task/sprint/track YAML missing required fields

**Diagnosis:**
```bash
# Check what fields exist
cat .vibey/roadmap/track-1/task-001/task.yaml | grep -E "^  (id|status|title):"
```

**Solution:**

Add missing required fields:
```yaml
task:
  id: example-task-001
  sprint_id: sprint-1      # Required
  track_id: track-1        # Required
  roadmap_id: my-roadmap   # Required
  task_type: development   # Required
  title: "Example Task"    # Required
  description: "..."       # Required
  status: not_started      # Required (was missing!)
  blocked: false           # Required
  created: '2025-11-21T00:00:00+00:00'  # Required
```

**Reference:** See [schema documentation](./VALIDATION_RULES.md#rule-21-required-track-fields) for complete field list

---

### Error 3: Invalid Status Value

**Symptom:**
```
❌ Invalid status value 'done' in task example-task-001
  Valid values: not_started, in_progress, completed, blocked, on_hold, cancelled
```

**Cause:** Status field contains invalid enum value

**Diagnosis:**
```bash
# Check current status
grep "status:" .vibey/roadmap/track-1/task-001/task.yaml
```

**Solution:**

Use valid status enum:
```yaml
# ❌ BAD
task:
  status: done       # Invalid!
  status: finished   # Invalid!
  status: complete   # Invalid!

# ✅ GOOD
task:
  status: completed  # Valid enum value
```

**Valid values:**
- `not_started`
- `in_progress`
- `completed`
- `blocked`
- `on_hold`
- `cancelled`
- `production_ready` (tracks/sprints only)
- `deployed` (tracks/sprints only)

---

### Error 4: Progress Counter Mismatch

**Symptom:**
```
❌ Progress mismatch in sprint example-sprint:
  Claimed: 5 completed
  Actual:  3 completed
```

**Cause:** Progress counters don't match actual completed tasks

**Diagnosis:**
```bash
# Run auto-repair dry-run to see mismatches
vibey roadmap repair --all --dry-run
```

**Solution 1: Auto-repair (recommended)**
```bash
# Preview repairs
vibey roadmap repair --progress --dry-run

# Apply repairs
vibey roadmap repair --progress
```

**Solution 2: Manual fix**
```yaml
# Count actual completed tasks
tasks:
  - status: completed  # 1
  - status: completed  # 2
  - status: completed  # 3
  - status: in_progress
  - status: not_started

# Update progress to match
progress:
  tasks_total: 5
  tasks_completed: 3  # Match actual count!
  completion_percent: 60
```

---

### Error 5: Broken Reference

**Symptom:**
```
❌ Broken reference: Task task-001 references non-existent sprint 'sprint-999'
```

**Cause:** Task/sprint/track references an ID that doesn't exist

**Diagnosis:**
```bash
# Check if referenced sprint exists
ls .vibey/roadmap/track-1/sprint-999/
# No such file or directory
```

**Solution 1: Fix reference**
```yaml
# ❌ BAD
task:
  sprint_id: sprint-999  # Doesn't exist!

# ✅ GOOD
task:
  sprint_id: sprint-1    # Exists
```

**Solution 2: Create missing object**
```bash
# If sprint should exist, create it
mkdir -p .vibey/roadmap/track-1/sprint-999
# ... create sprint.yaml ...
```

---

### Error 6: Circular Dependency

**Symptom:**
```
❌ Circular dependency detected:
  task-a → task-b → task-c → task-a
```

**Cause:** Dependency graph has a cycle

**Diagnosis:**
```bash
# Run advanced validation
vibey roadmap validate-advanced --verbose

# Check dependency chain
vibey roadmap show task-a | grep "depends_on"
vibey roadmap show task-b | grep "depends_on"
vibey roadmap show task-c | grep "depends_on"
```

**Solution:**

Break the circular dependency:
```yaml
# Before: task-a → task-b → task-c → task-a (circular!)

# Option 1: Remove one dependency
# task-c no longer depends on task-a
task-c:
  depends_on: []  # Removed circular link

# Option 2: Restructure dependencies
# Make all depend on a common parent
parent-task:
  depends_on: []

task-a:
  depends_on:
    - blocker_id: parent-task

task-b:
  depends_on:
    - blocker_id: parent-task

task-c:
  depends_on:
    - blocker_id: parent-task
```

---

### Error 7: Orphaned Task

**Symptom:**
```
⚠️  Orphaned task detected: task-999
  Task claims sprint sprint-1 but sprint doesn't list it
```

**Cause:** Task exists but parent sprint doesn't reference it

**Diagnosis:**
```bash
# Check if sprint lists this task
cat .vibey/roadmap/track-1/sprint-1/sprint.yaml | grep "task-999"
# (no output = not listed)
```

**Solution 1: Auto-repair**
```bash
# Auto-repair can add task to sprint
vibey roadmap repair --all
```

**Solution 2: Manual fix**
```yaml
# In sprint.yaml
sprint:
  tasks:
    - id: task-001
      title: ...
    - id: task-999  # Add orphaned task!
      title: ...
```

---

## Pre-Commit Hook Issues

### Issue 1: Hook Not Running

**Symptom:** Commits succeed without validation

**Diagnosis:**
```bash
# Check hook installation
vibey roadmap check-hooks

# Check hook file exists
ls -la .git/hooks/pre-commit

# Check hook is executable
ls -la .git/hooks/pre-commit | grep -E "^-rwx"
```

**Solutions:**

**Solution 1: Install hook**
```bash
vibey roadmap install-hooks
```

**Solution 2: Make hook executable**
```bash
chmod +x .git/hooks/pre-commit
```

**Solution 3: Verify hook content**
```bash
# Hook should contain Vibey validation code
head -20 .git/hooks/pre-commit
```

---

### Issue 2: Hook Runs But Doesn't Block

**Symptom:** Validation fails but commit still succeeds

**Diagnosis:**
```bash
# Check hook exit code behavior
# Hook should exit 1 on validation failure

# Test manually
.git/hooks/pre-commit
echo $?  # Should be 0 (success) or 1 (failure)
```

**Solution:**

Ensure hook exits with non-zero on failure:
```bash
# In .git/hooks/pre-commit
if python3 -m vibey.cli.main roadmap validate-fast --profile quick; then
    echo "✅ Validation passed"
    exit 0
else
    echo "❌ Validation failed"
    exit 1  # Critical: Must exit 1 to block commit!
fi
```

---

### Issue 3: Hook Too Slow

**Symptom:** Pre-commit validation takes >10 seconds

**Diagnosis:**
```bash
# Time the validation
time vibey roadmap validate-fast --profile quick
# Should be <1s for 470 files
```

**Solutions:**

**Solution 1: Use quick profile**
```bash
# Edit .git/hooks/pre-commit
python3 -m vibey.cli.main roadmap validate-fast --profile quick  # Fastest
```

**Solution 2: Disable advanced validation in hook**
```bash
# Remove or comment out advanced validation
# if [ "$VIBEY_HOOK_ADVANCED" = "true" ]; then
#     python3 -m vibey.cli.main roadmap validate-advanced
# fi
```

**Solution 3: Use incremental validation (future)**
```bash
# Once available
python3 -m vibey.cli.main roadmap validate-fast --incremental
```

---

## CI/CD Issues

### Issue 1: Workflow Not Triggering

**Symptom:** Push doesn't trigger GitHub Actions workflow

**Diagnosis:**
```bash
# Check if roadmap files changed
git diff HEAD~1 --name-only | grep ".vibey/roadmap"

# Check workflow paths configuration
cat .github/workflows/roadmap-validation.yml | grep -A5 "paths:"
```

**Solutions:**

**Solution 1: Ensure roadmap files changed**
```bash
# Workflow only runs if .vibey/roadmap/** files changed
git add .vibey/roadmap/
git commit -m "Update roadmap"
```

**Solution 2: Check branch name**
```yaml
# Workflow triggers on main/develop only
on:
  push:
    branches: [main, develop]

# If on feature branch, create PR to trigger
gh pr create --base main
```

---

### Issue 2: Validation Passes Locally But Fails in CI

**Symptom:** Local validation succeeds, CI validation fails

**Diagnosis:**
```bash
# Check Python version
python --version  # Local
# vs
# Python version in CI (check workflow file)

# Check installed dependencies
pip list | grep vibey
```

**Solutions:**

**Solution 1: Match Python version**
```bash
# Use same Python version as CI
pyenv install 3.12
pyenv local 3.12
python --version
```

**Solution 2: Fresh install**
```bash
# Reinstall Vibey in clean environment
pip uninstall vibey
pip install -e .
```

**Solution 3: Check for local cache**
```bash
# Clear validation cache
rm -rf ~/.vibey-validation-cache
vibey roadmap validate-fast
```

---

### Issue 3: CI Timeout

**Symptom:** Validation job exceeds timeout (5-10 min)

**Diagnosis:**
```bash
# Check job duration in GitHub Actions
# Navigate to: Actions → Roadmap Validation → Job

# Test validation time locally
time vibey roadmap validate-fast --profile standard
time vibey roadmap validate-advanced
```

**Solutions:**

**Solution 1: Increase timeout**
```yaml
# In .github/workflows/roadmap-validation.yml
jobs:
  fast-validation:
    timeout-minutes: 10  # Increase from 5
```

**Solution 2: Optimize roadmap**
- Reduce number of tasks
- Archive completed tracks
- Split large tracks

**Solution 3: Use faster profile**
```yaml
# Change to quick profile
run: python -m vibey.cli.main roadmap validate-fast --profile quick
```

---

## Audit Trail Issues

### Issue 1: No Audit Entries

**Symptom:** `vibey roadmap audit log` shows no entries

**Diagnosis:**
```bash
# Check if audit file exists
ls -la .vibey/roadmap/audit-trail.yaml

# Check file contents
cat .vibey/roadmap/audit-trail.yaml
```

**Solutions:**

**Solution 1: Perform status change**
```bash
# Audit file created on first status change
vibey roadmap start <any-task-id>

# Check again
vibey roadmap audit log
```

**Solution 2: Check file permissions**
```bash
# Ensure writable
chmod 644 .vibey/roadmap/audit-trail.yaml
```

---

### Issue 2: Audit File Corrupted

**Symptom:** YAML parsing error when reading audit trail

**Diagnosis:**
```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('.vibey/roadmap/audit-trail.yaml'))"
```

**Solutions:**

**Solution 1: Restore from git**
```bash
# Check git history
git log --oneline .vibey/roadmap/audit-trail.yaml

# Restore previous version
git checkout HEAD~1 .vibey/roadmap/audit-trail.yaml
```

**Solution 2: Rebuild from scratch**
```bash
# Backup current file
mv .vibey/roadmap/audit-trail.yaml .vibey/roadmap/audit-trail.yaml.backup

# New file created on next status change
vibey roadmap complete <task-id>
```

---

### Issue 3: Suspicious Changes Not Detected

**Symptom:** Manual YAML edit not flagged as suspicious

**Diagnosis:**
```bash
# Check audit trail for the change
vibey roadmap audit show <object-id>

# Check source field
cat .vibey/roadmap/audit-trail.yaml | grep "source:"
```

**Solution:**

Manual edits won't be in audit trail (that's why they're suspicious!):
```bash
# Look for git commits without audit entries
git log --oneline .vibey/roadmap/

# Compare to audit trail
vibey roadmap audit log --limit 100
```

**Prevention:** Always use CLI commands instead of manual edits

---

## Auto-Repair Issues

### Issue 1: Repair Doesn't Fix Issue

**Symptom:** `vibey roadmap repair --all` runs but issue persists

**Diagnosis:**
```bash
# Check which repairs were attempted
vibey roadmap repair --all --dry-run

# Check if issue is auto-repairable
# See VALIDATION_RULES.md for auto-repair capabilities
```

**Solutions:**

**Solution 1: Check if issue is auto-repairable**

Not all issues can be auto-repaired:
- ✅ Progress counter mismatches - YES
- ✅ Orphaned tasks - YES
- ❌ YAML syntax errors - NO
- ❌ Missing required fields - NO
- ❌ Circular dependencies - NO

**Solution 2: Manual fix required**
```bash
# For non-repairable issues, fix manually
# Then verify
vibey roadmap validate-advanced
```

---

### Issue 2: Repair Changes Wrong Values

**Symptom:** Auto-repair corrects progress but uses wrong values

**Diagnosis:**
```bash
# Review what repair did
git diff .vibey/roadmap/

# Check audit trail
vibey roadmap audit log --limit 5
```

**Solution:**

**Revert and fix manually:**
```bash
# Revert repair
git checkout -- .vibey/roadmap/

# Fix manually
# ... edit files ...

# Verify
vibey roadmap validate-advanced
```

**Report bug:**
```bash
gh issue create --title "Auto-repair incorrect: ..." --body "..."
```

---

## Performance Issues

### Issue 1: Validation Very Slow

**Symptom:** Validation takes >30 seconds for small roadmap

**Diagnosis:**
```bash
# Time each profile
time vibey roadmap validate-fast --profile quick
time vibey roadmap validate-fast --profile standard
time vibey roadmap validate-fast --profile thorough
```

**Solutions:**

**Solution 1: Use quick profile**
```bash
vibey roadmap validate-fast --profile quick  # Fastest
```

**Solution 2: Check file count**
```bash
# Count roadmap files
find .vibey/roadmap -name "*.yaml" | wc -l

# If >1000 files, consider archiving
```

**Solution 3: Check for large files**
```bash
# Find large YAML files
find .vibey/roadmap -name "*.yaml" -size +100k
```

---

## Getting Help

### Before Asking for Help

**Gather diagnostic information:**
```bash
# 1. System information
python --version
vibey --version
git --version

# 2. Validation results
vibey roadmap validate-fast --profile standard --verbose > validation.log 2>&1

# 3. Audit trail
vibey roadmap audit log --limit 50 > audit.log

# 4. File structure
tree .vibey/roadmap/ -L 3 > structure.txt

# 5. Git status
git status > git-status.txt
git log --oneline -20 > git-log.txt
```

### Where to Get Help

**1. Documentation:**
- [Validation System](./VALIDATION_SYSTEM.md)
- [Validation Rules](./VALIDATION_RULES.md)
- [Best Practices](./BEST_PRACTICES.md)
- This troubleshooting guide

**2. GitHub Issues:**
```bash
# Search existing issues
gh issue list --label "validation"

# Create new issue
gh issue create --title "Validation error: ..." --body "..."
```

**3. Team Chat:**
- Slack: #vibey-help
- Discord: #roadmap-validation

### What to Include in Bug Reports

**Minimum information:**
1. **Error message** - Complete error output
2. **Steps to reproduce** - How to trigger the error
3. **Expected behavior** - What should happen
4. **Actual behavior** - What actually happens
5. **Environment** - Python version, OS, Vibey version
6. **Diagnostic logs** - Output from diagnostic commands above

**Template:**
```markdown
## Error Description
Brief description of the issue

## Steps to Reproduce
1. Run `vibey roadmap validate-fast`
2. Observe error: ...

## Expected Behavior
Should validate successfully

## Actual Behavior
Error: ...

## Environment
- Python: 3.12
- Vibey: 2.5.0
- OS: Ubuntu 22.04

## Diagnostic Logs
See attached files
```

---

## Related Documentation

- [Validation System Overview](./VALIDATION_SYSTEM.md) - Architecture and components
- [Validation Rules](./VALIDATION_RULES.md) - Complete rule reference
- [Best Practices](./BEST_PRACTICES.md) - Recommended workflows
- [Pre-Commit Hooks](./PRE_COMMIT_HOOKS.md) - Local validation
- [CI/CD Validation](./CI_CD_VALIDATION.md) - GitHub Actions
- [Audit Trail](./AUDIT_TRAIL.md) - Change tracking

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
